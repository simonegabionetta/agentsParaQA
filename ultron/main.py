#!/usr/bin/env python3
"""
Ultron — Analisa PR(s) do GitHub + card do gerenciador de tarefas
e posta casos de teste organizados diretamente no card.

Uso:
    python main.py analyze --card PROJ-42 --pr 87
    python main.py analyze --card PROJ-42 --prs 87,88
    python main.py analyze --card PROJ-42 --pr 87 --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from github_client import GitHubClient
from local_git_client import LocalGitClient
from pm_client import build_pm_client
from analyzer import build_comment
from test_runner import execute, resolve_area
from report_reader import read_report, all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Ultron QA — Analisa PR e comenta casos de teste no card",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Analisa PR 87, comenta no card PROJ-42
  python ultron/main.py analyze --card PROJ-42 --pr 87

  # Múltiplos PRs (front + back)
  python ultron/main.py analyze --card PROJ-42 --prs 87,88

  # Visualizar sem postar
  python ultron/main.py analyze --card PROJ-42 --pr 87 --dry-run

  # Diff contra branch específica
  python ultron/main.py analyze --card PROJ-42 --pr 87 --base develop
        """,
    )

    sub = parser.add_subparsers(dest="command")
    cmd = sub.add_parser("analyze", help="Analisa PR(s) e posta testes no card")

    cmd.add_argument("--card", required=True, help="ID do card (ex: PROJ-42, #15)")
    cmd.add_argument("--pr",  type=int, default=0, help="Número do PR")
    cmd.add_argument("--prs", default="", help="Múltiplos PRs separados por vírgula (ex: 87,88)")
    cmd.add_argument("--base", default="", help="Branch base para o diff (padrão: base do PR)")
    cmd.add_argument("--perfil", choices=["MANUAL", "TECNICO"], default="MANUAL",
                     help="Perfil dos casos de teste (padrão: MANUAL)")
    cmd.add_argument("--dry-run", action="store_true", help="Exibe o comentário sem postar")

    cmd.add_argument("--area", choices=["auto", "frontend", "backend"], default="auto",
                     help="Area do card; auto usa o texto do card")
    cmd.add_argument("--execute", action="store_true",
                     help="Executa a suite configurada para a area apos gerar os casos")
    cmd.add_argument("--repo", choices=["frontend", "bi", "agents", "backend"], default="",
                     help="Repositorio local a analisar; obrigatorio para Backend")

    cmd_pub = sub.add_parser("publicar", help="Publica a tabela de veredito no card, se a bateria fechou 100% PASSOU")
    cmd_pub.add_argument("--card", required=True, help="ID do card (ex: ATD-142)")
    cmd_pub.add_argument("--relatorio", default="", help="Caminho do RELATORIO.md (padrão: C:/Users/Simone/qa/<CARD>/RELATORIO.md)")
    cmd_pub.add_argument("--dry-run", action="store_true", help="Mostra o que seria postado sem publicar")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "publicar":
        relatorio_path = Path(args.relatorio) if args.relatorio else Path(f"C:/Users/Simone/qa/{args.card}/RELATORIO.md")
        sys.exit(run_publicar(args.card, relatorio_path, args.dry_run))

    # ── Resolve lista de PRs ─────────────────────────────────────────────────
    pr_numbers: list[int] = []
    if args.pr:
        pr_numbers.append(args.pr)
    if args.prs:
        pr_numbers += [int(n.strip()) for n in args.prs.split(",") if n.strip()]
    if not pr_numbers:
        print("ERRO: informe ao menos um PR com --pr ou --prs")
        sys.exit(1)

    # ── Carrega config ───────────────────────────────────────────────────────
    config = load_config()
    env = os.environ

    github_token = env.get("GITHUB_TOKEN", "").strip()
    github_repo  = env.get("GITHUB_REPO", "").strip()
    if False and (not github_token or not github_repo):
        print("ERRO: GITHUB_TOKEN e GITHUB_REPO são obrigatórios no .env")
        sys.exit(1)

    _header(args.card, pr_numbers, args.dry_run)

    # ── Busca card ───────────────────────────────────────────────────────────
    _step("Buscando card no gerenciador de projetos...")
    try:
        pm = build_pm_client(dict(env))
        card = pm.get_card(args.card)
    except Exception as e:
        _error(f"Erro ao buscar card: {e}")
        sys.exit(1)
    _ok(f"Card: {card.title}")
    area = resolve_area(card, args.area)
    if area == "unknown":
        _error("Nao foi possivel identificar Frontend ou Backend. Use --area frontend ou --area backend.")
        sys.exit(1)
    _ok(f"Fluxo QA: {area}")

    # ── Busca PRs ────────────────────────────────────────────────────────────
    repos = {
        "frontend": r"C:\Users\Simone\Atendas\atendas-frontend",
        "bi": r"C:\Users\Simone\Atendas\atendas-bi",
        "agents": r"C:\Users\Simone\Atendas\atendas-agents",
        "backend": r"C:\Users\Simone\Atendas\atendas-backend",
    }
    repo_key = args.repo or ("frontend" if area == "frontend" else "")
    if not repo_key:
        _error("Para um card Backend informe: --repo bi, --repo agents ou --repo backend.")
        sys.exit(1)
    source = LocalGitClient(repos[repo_key])
    _ok(f"Fonte do diff: repositorio local {repos[repo_key]}")
    prs = []
    for pr_num in pr_numbers:
        _step(f"Buscando PR #{pr_num}...")
        try:
            pr = source.get_pr(pr_num, base_branch=args.base)
            prs.append(pr)
            files_count = len(pr.files_changed)
            _ok(f"PR #{pr_num}: {pr.title} ({files_count} arquivo(s) alterado(s))")
        except Exception as e:
            _error(f"Erro ao buscar PR #{pr_num}: {e}")
            sys.exit(1)

    # ── Analisa com LLM ──────────────────────────────────────────────────────
    _step(f"Analisando com {config.llm_provider} / {config.resolved_model} (perfil: {args.perfil})...")
    try:
        comment = build_comment(
            card=card,
            prs=prs,
            model=config.resolved_model,
            api_key=config.api_key,
            perfil=args.perfil,
        )
    except Exception as e:
        _error(f"Erro na análise LLM: {e}")
        sys.exit(1)
    _ok("Análise concluída")

    if args.execute:
        _step(f"Executando testes de {area}...")
        try:
            run = execute(area, repo_key)
        except Exception as e:
            _error(f"Erro ao executar testes: {e}")
            sys.exit(1)
        _ok(f"Execucao: {run.status}")

    # ── Dry-run ou posta ─────────────────────────────────────────────────────
    if args.dry_run:
        print("\n" + "=" * 70)
        print(comment)
        print("=" * 70)
        _ok("Dry-run concluído. Nada foi postado.")
        return

    _step("Postando comentário no card...")
    try:
        url = pm.post_comment(args.card, comment)
    except Exception as e:
        _error(f"Erro ao postar comentário: {e}")
        sys.exit(1)

    _ok(f"Comentário postado: {url}")


# ── Helpers de output ────────────────────────────────────────────────────────

def _header(card_id: str, prs: list[int], dry_run: bool):
    mode = " [DRY-RUN]" if dry_run else ""
    pr_str = ", ".join(f"#{n}" for n in prs)
    print(f"\n{'='*60}")
    print(f"  Ultron QA{mode}")
    print(f"  Card: {card_id}")
    print(f"  PR(s): {pr_str}")
    print(f"{'='*60}\n")


def _step(msg: str):
    print(f">> {msg}")


def _ok(msg: str):
    print(f"   {msg}")


def _error(msg: str):
    print(f"\nERRO: {msg}\n")


def run_publicar(card: str, relatorio_path: Path, dry_run: bool) -> int:
    if not relatorio_path.exists():
        print(f"ERRO: relatório não encontrado em {relatorio_path}")
        return 1

    texto = relatorio_path.read_text(encoding="utf-8")
    report = read_report(texto)

    if not report.cases:
        print(f"ERRO: nenhum caso com veredito encontrado em {relatorio_path}")
        return 1

    if not all_passed(report.cases):
        print(f"\nBateria não fechou 100% PASSOU — nada foi postado no card {card}.\n")
        for caso in report.cases:
            if caso.veredito != "PASSOU":
                print(f"  {caso.id}: {caso.veredito} (critério: {caso.criterio or '—'})")
        return 1

    print(f"\nTodos os {len(report.cases)} casos passaram. Tabela que seria postada em {card}:\n")
    print(report.table_markdown)

    if dry_run:
        print("\n[DRY-RUN] Nada foi postado.")
        return 0

    resposta = input("\nConfirma publicar esta tabela como comentário no card? (sim/não): ")
    if resposta.strip().lower() not in ("sim", "s"):
        print("Cancelado. Nada foi postado.")
        return 1

    pm = build_pm_client(dict(os.environ))
    url = pm.post_comment(card, report.table_markdown)
    print(f"Comentário postado: {url}")
    return 0


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
RoboCop QA — Percorre o front-end de um site com Playwright e gera casos de teste em .docx.
Compatível com Claude, OpenAI, Gemini, Groq e Ollama via LiteLLM.

Uso:
    python main.py crawl https://exemplo.com
    python main.py crawl https://exemplo.com --email user@site.com --senha abc123
    python main.py crawl https://exemplo.com --email user@site.com --senha abc123 --perfil TECNICO
    python main.py crawl https://exemplo.com --max-paginas 20 --dry-run
"""

import argparse
import sys
from agent import RoboCop
from config import load_config, ConfigError


def main():
    parser = argparse.ArgumentParser(
        description="RoboCop QA — Gera casos de teste a partir do front-end de um site",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Site público
  python main.py crawl https://exemplo.com

  # Site com login
  python main.py crawl https://app.exemplo.com --email qa@empresa.com --senha minhasenha

  # Perfil técnico, máx 30 páginas
  python main.py crawl https://app.exemplo.com --email qa@empresa.com --senha s3cr3t --perfil TECNICO --max-paginas 30

  # Apenas exibe no terminal, sem gerar .docx
  python main.py crawl https://exemplo.com --dry-run
        """
    )

    subparsers = parser.add_subparsers(dest="command")
    crawl = subparsers.add_parser("crawl", help="Percorre o site e gera casos de teste")

    crawl.add_argument("url", help="URL inicial do site (ex: https://app.empresa.com)")
    crawl.add_argument("--email", default="", help="E-mail para login (opcional)")
    crawl.add_argument("--senha", default="", help="Senha para login (opcional)")
    crawl.add_argument(
        "--login-click",
        default="",
        help="Texto do elemento a clicar para login (ex: 'Admin')",
    )
    crawl.add_argument(
        "--login-clicks",
        default="",
        help="Lista de perfis separados por vírgula para rodar em sequência (ex: 'Admin,Cliente,Motorista,Funcionario')",
    )
    crawl.add_argument(
        "--perfil",
        choices=["MANUAL", "TECNICO"],
        default="MANUAL",
        help="Perfil dos casos de teste (padrão: MANUAL)",
    )
    crawl.add_argument(
        "--max-paginas",
        type=int,
        default=15,
        help="Máximo de páginas/rotas a explorar (padrão: 15)",
    )
    crawl.add_argument(
        "--output",
        default="",
        help="Nome do arquivo de saída (padrão: casos_de_teste_<dominio>.docx)",
    )
    crawl.add_argument(
        "--dry-run",
        action="store_true",
        help="Exibe análise no terminal sem gerar .docx",
    )
    crawl.add_argument("--verbose", action="store_true", help="Logs detalhados")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        config = load_config()
    except ConfigError as e:
        print(f"\n❌ Erro de configuração: {e}")
        print("💡 Verifique o arquivo .env (copie de .env.example)\n")
        sys.exit(1)

    if args.command == "crawl":
        agent = RoboCop(config, verbose=args.verbose)

        # Múltiplos perfis de clique
        if args.login_clicks:
            perfis = [p.strip() for p in args.login_clicks.split(",") if p.strip()]
            for perfil_click in perfis:
                print(f"\n{'='*60}")
                print(f"  Perfil: {perfil_click}")
                print(f"{'='*60}")
                safe_name = perfil_click.lower().replace(" ", "_")
                out = args.output or f"casos_de_teste_{safe_name}.docx"
                agent.run(
                    url=args.url,
                    email=args.email,
                    senha=args.senha,
                    login_click_text=perfil_click,
                    perfil=args.perfil,
                    max_pages=args.max_paginas,
                    output_file=out,
                    dry_run=args.dry_run,
                )
        else:
            agent.run(
                url=args.url,
                email=args.email,
                senha=args.senha,
                login_click_text=args.login_click,
                perfil=args.perfil,
                max_pages=args.max_paginas,
                output_file=args.output,
                dry_run=args.dry_run,
            )


if __name__ == "__main__":
    main()

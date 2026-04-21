#!/usr/bin/env python3
"""
Ultron QA — entrada em linguagem natural.

Exemplos de chamada:
    python run.py "Rode o Ultron no card PROJ-42, pr 87, MANUAL"
    python run.py "Rode o Ultron no card PROJ-42, pr 87, 88, TECNICO"
    python run.py "Ultron card #42 pr 15"
    python run.py "card PROJ-42 pr 87 tecnico --dry-run"
"""

import re
import subprocess
import sys
from pathlib import Path

# Garante imports locais
sys.path.insert(0, str(Path(__file__).parent))


def parse(text: str) -> dict:
    t = text.strip()

    # ── Card ────────────────────────────────────────────────────────────────
    # Aceita: PROJ-42  |  ABC-123  |  #42
    card_match = re.search(r"\bcard\s+([A-Z][A-Z0-9]*-\d+|#\d+)", t, re.IGNORECASE)
    if not card_match:
        # Tenta encontrar o padrão diretamente sem a palavra "card"
        card_match = re.search(r"\b([A-Z][A-Z0-9]*-\d+|#\d+)\b", t)
    if not card_match:
        _die('Não encontrei o card. Use: "card PROJ-42" ou "card #42"')
    card = card_match.group(1)

    # ── PRs ─────────────────────────────────────────────────────────────────
    # Pega todos os números que aparecem após a palavra "pr"
    pr_section = re.search(r"\bprs?\b(.+?)(?:manual|tecnico|--|\Z)", t, re.IGNORECASE)
    if not pr_section:
        _die('Não encontrei o PR. Use: "pr 87" ou "pr 87, 88"')
    raw_numbers = re.findall(r"\d+", pr_section.group(1))
    if not raw_numbers:
        _die('Informe ao menos um número de PR. Ex: "pr 87"')
    prs = [int(n) for n in raw_numbers]

    # ── Perfil ───────────────────────────────────────────────────────────────
    if re.search(r"\btecnico\b", t, re.IGNORECASE):
        perfil = "TECNICO"
    else:
        perfil = "MANUAL"

    # ── Dry-run ──────────────────────────────────────────────────────────────
    dry_run = "--dry-run" in t or "dry run" in t.lower() or "dry-run" in t.lower()

    return {"card": card, "prs": prs, "perfil": perfil, "dry_run": dry_run}


def build_args(parsed: dict) -> list[str]:
    args = ["analyze", "--card", parsed["card"]]

    if len(parsed["prs"]) == 1:
        args += ["--pr", str(parsed["prs"][0])]
    else:
        args += ["--prs", ",".join(str(p) for p in parsed["prs"])]

    args += ["--perfil", parsed["perfil"]]

    if parsed["dry_run"]:
        args.append("--dry-run")

    return args


def _die(msg: str):
    print(f"\nERRO: {msg}\n")
    print("Exemplos válidos:")
    print('  "Rode o Ultron no card PROJ-42, pr 87, MANUAL"')
    print('  "card PROJ-42, pr 87, 88, TECNICO"')
    print('  "card #42 pr 15"')
    print()
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    # Junta tudo como uma frase (permite chamar sem aspas)
    text = " ".join(sys.argv[1:])

    parsed = parse(text)

    print(f"\n>> Ultron QA")
    print(f"   Card   : {parsed['card']}")
    print(f"   PR(s)  : {', '.join('#' + str(p) for p in parsed['prs'])}")
    print(f"   Perfil : {parsed['perfil']}")
    if parsed["dry_run"]:
        print("   Modo   : DRY-RUN")
    print()

    args = build_args(parsed)

    # Chama main.py com os argumentos resolvidos
    script = Path(__file__).parent / "main.py"
    result = subprocess.run([sys.executable, str(script)] + args)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

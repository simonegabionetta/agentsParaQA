#!/usr/bin/env bash
# Ultron QA
#
# Linguagem natural (recomendado):
#   ./ultron.sh Rode o Ultron no card PROJ-42, pr 87, MANUAL
#   ./ultron.sh card PROJ-42 pr 87 88 TECNICO
#   ./ultron.sh card PROJ-42 pr 87 --dry-run
#
# Posicional (alternativa):
#   ./ultron.sh PROJ-42 87
#   ./ultron.sh PROJ-42 87,88 TECNICO

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -z "$1" ]; then
  echo ""
  echo "Uso: ./ultron.sh Rode o Ultron no card PROJ-42, pr 87, MANUAL"
  echo "  ou: ./ultron.sh card PROJ-42 pr 87 88 TECNICO"
  echo ""
  exit 1
fi

# ── Setup automático na primeira vez ─────────────────────────────────────────
if [ ! -d ".venv" ]; then
  echo ">> Primeira execução — configurando ambiente..."
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
  echo "   Ambiente pronto."
fi

if [ ! -f ".env" ]; then
  echo ""
  echo "ERRO: arquivo .env não encontrado."
  echo "Execute: cp .env.example .env  e preencha as chaves."
  echo ""
  exit 1
fi

# Passa todos os argumentos como frase para o run.py
exec .venv/bin/python run.py "$@"

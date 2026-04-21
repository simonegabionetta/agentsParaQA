#!/usr/bin/env bash
# RoboCop QA — script de ativação
# Uso: ./robocop.sh crawl https://app.com [opções]
#      ./robocop.sh crawl https://app.com --email qa@empresa.com --senha s3cr3t

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Cria o ambiente virtual na primeira vez
if [ ! -d ".venv" ]; then
  echo ">> Criando ambiente virtual..."
  python3 -m venv .venv

  echo ">> Instalando dependências..."
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt

  echo ">> Instalando browser Playwright..."
  .venv/bin/playwright install chromium
fi

# Verifica se o .env existe
if [ ! -f ".env" ]; then
  echo ""
  echo "ERRO: arquivo .env não encontrado."
  echo "Execute: cp .env.example .env  e preencha com sua chave de API."
  echo ""
  exit 1
fi

exec .venv/bin/python main.py "$@"

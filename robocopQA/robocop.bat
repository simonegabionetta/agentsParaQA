@echo off
REM RoboCop QA — script de ativação (Windows)
REM Uso: robocop.bat crawl https://app.com [opcoes]

cd /d "%~dp0"

IF NOT EXIST ".venv" (
    echo ^>^> Criando ambiente virtual...
    python -m venv .venv

    echo ^>^> Instalando dependencias...
    .venv\Scripts\pip install -q --upgrade pip
    .venv\Scripts\pip install -q -r requirements.txt

    echo ^>^> Instalando browser Playwright...
    .venv\Scripts\playwright install chromium
)

IF NOT EXIST ".env" (
    echo.
    echo ERRO: arquivo .env nao encontrado.
    echo Execute: copy .env.example .env  e preencha com sua chave de API.
    echo.
    exit /b 1
)

.venv\Scripts\python main.py %*

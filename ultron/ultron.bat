@echo off
REM Ultron QA (Windows)
REM
REM Linguagem natural:
REM   ultron.bat Rode o Ultron no card PROJ-42, pr 87, MANUAL
REM   ultron.bat card PROJ-42 pr 87 88 TECNICO
REM
REM Posicional:
REM   ultron.bat PROJ-42 87
REM   ultron.bat PROJ-42 87,88 TECNICO

cd /d "%~dp0"

IF "%~1"=="" (
    echo.
    echo Uso: ultron.bat Rode o Ultron no card PROJ-42, pr 87, MANUAL
    echo  ou: ultron.bat card PROJ-42 pr 87 88 TECNICO
    echo.
    exit /b 1
)

IF NOT EXIST ".venv" (
    echo ^>^> Primeira execucao - configurando ambiente...
    python -m venv .venv
    .venv\Scripts\pip install -q --upgrade pip
    .venv\Scripts\pip install -q -r requirements.txt
    echo    Ambiente pronto.
)

IF NOT EXIST ".env" (
    echo.
    echo ERRO: arquivo .env nao encontrado.
    echo Execute: copy .env.example .env  e preencha as chaves.
    echo.
    exit /b 1
)

.venv\Scripts\python run.py %*

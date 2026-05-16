@echo off
title PDV Pizzaria

cd /d "%~dp0"

echo ==========================================
echo        INICIANDO PDV PIZZARIA
echo ==========================================
echo.

if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

echo Ativando ambiente virtual...
call ".venv\Scripts\activate.bat"

echo Verificando dependencias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Abrindo servidor em segundo plano...
start "Servidor PDV Pizzaria" /min cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && python app.py"

echo Aguardando servidor iniciar...
timeout /t 3 >nul

echo Abrindo sistema no navegador...
start http://127.0.0.1:5000

exit
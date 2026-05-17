@echo off
title PDV Pizzaria

cd /d "%~dp0"

echo ==========================================
echo        INICIANDO PDV PIZZARIA
echo ==========================================
echo.

echo [%date% %time%] BAT iniciado > tray_pdv_erro.log
echo Pasta do projeto: %~dp0 >> tray_pdv_erro.log

if not exist ".venv" (
    echo Criando ambiente virtual...
    echo Criando ambiente virtual... >> tray_pdv_erro.log
    python -m venv .venv
)

echo Ativando ambiente virtual...
echo Ativando ambiente virtual... >> tray_pdv_erro.log
call ".venv\Scripts\activate.bat"

echo Verificando dependencias...
echo Verificando dependencias... >> tray_pdv_erro.log
python -m pip install --upgrade pip >> tray_pdv_erro.log 2>&1
python -m pip install -r requirements.txt >> tray_pdv_erro.log 2>&1

echo.
echo Iniciando PDV na bandeja do sistema...
echo Chamando tray_pdv.py... >> tray_pdv_erro.log

if not exist ".venv\Scripts\pythonw.exe" (
    echo ERRO: pythonw.exe nao encontrado >> tray_pdv_erro.log
    echo ERRO: pythonw.exe nao encontrado
    pause
    exit
)

if not exist "tray_pdv.py" (
    echo ERRO: tray_pdv.py nao encontrado >> tray_pdv_erro.log
    echo ERRO: tray_pdv.py nao encontrado
    pause
    exit
)

start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0tray_pdv.py"

timeout /t 2 >nul

exit
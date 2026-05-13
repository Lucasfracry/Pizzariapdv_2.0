@echo off
title PDV Pizzaria
echo Iniciando o PDV da Pizzaria...
echo.

python -m pip install -r requirements.txt

echo.
echo Abrindo sistema em http://127.0.0.1:5000
echo.

start http://127.0.0.1:5000

python app.py

pause
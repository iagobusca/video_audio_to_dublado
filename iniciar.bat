@echo off
setlocal
cd /d "%~dp0"

rem Ativa runtime python se existir
set "PYEXE=%~dp0bin\runtime\python\python.exe"
if not exist "%PYEXE%" (
    set "PYEXE=python"
)

echo [iniciar.bat] Iniciando dubbr em http://127.0.0.1:7860 ...
"%PYEXE%" app.py
pause

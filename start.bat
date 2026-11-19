@echo off
setlocal

rem start.bat - launcher do instalador Python do projeto dubbr
rem Acessa a pasta bin e executa install_python.py

cd /d "%~dp0bin"
if not exist "install_python.py" (
    echo [ERRO] install_python.py nao encontrado em "%cd%"
    pause
    exit /b 1
)

rem Detecta interpretador Python disponivel
set "PYEXE="
where python >nul 2>&1 && set "PYEXE=python"
if not defined PYEXE (
    where py >nul 2>&1 && set "PYEXE=py -3"
)
if not defined PYEXE (
    echo [ERRO] Python nao encontrado no PATH.
    echo Instale o Python ou use o bin\install_python.py manualmente.
    pause
    exit /b 1
)

echo [start.bat] Executando install_python.py em "%cd%" ...
%PYEXE% install_python.py %*
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    echo [start.bat] install_python.py terminou com codigo %EXITCODE%.
) else (
    echo [start.bat] Concluido com sucesso.
)

pause
exit /b %EXITCODE%

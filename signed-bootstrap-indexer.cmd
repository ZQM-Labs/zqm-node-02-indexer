@echo off
:: signed-bootstrap-indexer.cmd — signed bootstrap for indexer service auto-start
:: Use this in scheduled tasks for 5000 after signing completes.

setlocal
set "PYTHON=pythonw.exe"
set "SCRIPT=%~dp0app.py"
set "WD=%~dp0"

if not exist "%PYTHON%" (
    set "PYTHON=python.exe"
)

if not exist "%PYTHON%" (
    echo ERROR: Python not found in PATH.
    pause
    exit /b 1
)

cd /d "%WD%"
"%PYTHON%" "%SCRIPT%"
endlocal
exit /b %errorlevel%

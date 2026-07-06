@echo off
:: signed-bootstrap-indexer.cmd — signed bootstrap for indexer service auto-start
:: Use this in scheduled tasks for 5000 after signing completes.

setlocal
set "PYTHON=C:\Users\zqmco\AppData\Local\Programs\Python\Python312\pythonw.exe"
set "SCRIPT=C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer\app.py"
set "WD=C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer"

if not exist "%PYTHON%" (
    echo ERROR: Python not found: %PYTHON%
    pause
    exit /b 1
)

cd /d "%WD%"
"%PYTHON%" "%SCRIPT%"
endlocal
exit /b %errorlevel%

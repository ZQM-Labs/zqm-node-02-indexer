@echo off
title ZQM Node-02 Windows Service Install
echo ========================================
echo  Installing ZQM Node-02 Indexer Service
echo ========================================
echo.

REM Clean up any stale scheduled task with the same name
schtasks /query /fo CSV /v | findstr /i "ZQM-Node-02-Indexer" >nul 2>&1 && (
    echo Removing existing scheduled task...
    powershell -Command "Unregister-ScheduledTask -TaskName 'ZQM-Node-02-Indexer' -Confirm:$false"
)

REM Real daemon path uses project-local venv + service wrapper
set PYTHON_EXE=python.exe
set SERVICE_SCRIPT=%~dp0zqm_node_service.py
set PROJECT_DIR=%~dp0

if not exist "%PYTHON_EXE%" (
    echo ERROR: %PYTHON_EXE% not found
    pause
    exit /b 1
)

REM Install/reinstall
sc stop "ZQM-Node-02-Indexer" >nul 2>&1
timeout /t 2 /nobreak >nul
sc delete "ZQM-Node-02-Indexer" >nul 2>&1

sc create "ZQM-Node-02-Indexer" binPath= "\"%PYTHON_EXE%\" \"%SERVICE_SCRIPT%\"" start= auto obj= "zqmco" password= ""
sc description "ZQM-Node-02-Indexer" "ZQM Node-02 local file search indexer. Flask/Waitress API at http://127.0.0.1:5000."

REM Start the service
echo Starting service...
net start "ZQM-Node-02-Indexer"

timeout /t 4 /nobreak >nul

REM Verify health
curl -s "http://127.0.0.1:5000/api/health" >nul 2>&1 && (
    echo.
    echo ========================================
    echo  Service running, API healthy.
    echo  http://127.0.0.1:5000
    echo ========================================
) || (
    echo.
    echo API not responding yet; check %PROJECT_DIR%logs\service_startup.log
)

pause

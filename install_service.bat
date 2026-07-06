@echo off
echo ========================================
echo Installing ZQM Node 02 Indexer Service
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Installing service...
echo.

REM Create service using sc.exe
sc create "ZQM-Node-02-Indexer" binPath= "python.exe C:\Users\zqmco\Desktop\zqm-node-02-indexer\indexer.py" start= auto depend= "Tcpip/AF" obj= "LocalSystem" password= ""

REM Set service description
sc description "ZQM-Node-02-Indexer" "ZQM Node 02 Local File Indexing Service - Provides fast file search across the entire workstation"

REM Start the service
echo Starting service...
net start "ZQM-Node-02-Indexer"

echo.
echo ========================================
echo Service installed successfully!
echo ========================================
echo.
echo Service Name: ZQM-Node-02-Indexer
echo Status: Running
echo Auto-start: Enabled
echo.
echo To manage the service:
echo   - Start:   net start ZQM-Node-02-Indexer
echo   - Stop:    net stop ZQM-Node-02-Indexer
echo   - Remove:  sc delete ZQM-Node-02-Indexer
echo.
echo Access the web UI at: http://localhost:5000
echo.
pause

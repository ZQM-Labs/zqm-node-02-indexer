@echo off
title ZQM Node-02 Service Control
echo.
if "%1"=="" (
    echo Usage:
    echo   service-ctl.bat start
    echo   service-ctl.bat stop
    echo   service-ctl.bat restart
    echo   service-ctl.bat status
    echo.
    sc query "ZQM-Node-02-Indexer"
    goto :eof
)
if /i "%1"=="start" (
    net start "ZQM-Node-02-Indexer"
    goto :eof
)
if /i "%1"=="stop" (
    net stop "ZQM-Node-02-Indexer"
    goto :eof
)
if /i "%1"=="restart" (
    net stop "ZQM-Node-02-Indexer"
    timeout /t 2 /nobreak >nul
    net start "ZQM-Node-02-Indexer"
    goto :eof
)
if /i "%1"=="status" (
    sc query "ZQM-Node-02-Indexer"
    goto :eof
)
echo Unknown command %1
pause

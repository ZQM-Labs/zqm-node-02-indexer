@echo off
cd /d "C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer"
echo Rebuilding workstation file index...
echo This will scan: C:\PerfLogs, C:\Program Files, C:\Program Files (x86), C:\Users, C:\Windows, C:\inetpub
echo.
"C:\Users\zqmco\AppData\Local\Programs\Python\Python312\python.exe" indexer.py rebuild
echo.
echo Done! Press any key to exit.
pause >nul

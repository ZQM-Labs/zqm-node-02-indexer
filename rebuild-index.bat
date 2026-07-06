@echo off
cd /d "C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer"
echo Rebuilding workstation file index...
echo This will scan: Program Files, Program Files (x86), Users, inetpub
echo.
python indexer.py rebuild
echo.
echo Done! Press any key to exit.
pause >nul

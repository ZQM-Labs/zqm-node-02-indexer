@echo off
title ZQM Node-02 File Indexer
cd /d "C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer"

echo ============================================================
echo   ZQM Node-02 File Indexer
echo   Starting server...
echo ============================================================
echo.

call .venv\Scripts\activate.bat
python app.py

pause

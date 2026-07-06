@echo off
title ZQM Node-02 Rebuild Index
echo Rebuilding index from stable venv context...
echo.
cd /d "C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer"

"C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer\.venv\Scripts\python.exe" indexer.py rebuild
echo.
echo Rebuild complete.
pause

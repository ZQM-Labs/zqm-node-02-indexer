# ZQM Node 01 Indexer — Persistence Notes

## Active service
- Port: 5000
- Path: `C:\Users\zqmco\OneDrive\Desktop\zqm-node-01-indexer\app.py`
- Scheduled task: `ZQM-Node-01-Indexer`
- Task state: Ready/Running
- Triggers: Boot + Logon for `zqmco`

## Signed bootstrap
- `C:\Users\zqmco\OneDrive\Desktop\zqm-node-01-indexer\signed-bootstrap-indexer.cmd`

## Re-registering after signing
If updating the task to use the signed cmd bootstrap later:
```cmd
"C:\Users\zqmco\AppData\Local\hermes\skills\skill-automation-center\scripts\elevate.cmd" "C:\Users\zqmco\AppData\Local\hermes\skills\skill-automation-center\scripts\install-service-admin.ps1"
```

For the indexer specifically, adapt the task XML to call
`C:\Users\zqmco\OneDrive\Desktop\zqm-node-01-indexer\signed-bootstrap-indexer.cmd`
instead of calling pythonw.exe directly.

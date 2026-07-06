# ZQM Node-02 Workstation Indexer

Local full-disk file indexer for Windows workstations. Uses Whoosh for BM25 full-text search and SQLite for metadata exact-match recall fallback.

## Current State

- Index directory: `C:\Users\zqmco\.zqm-node-02-indexer\index`
- Metadata store: `C:\Users\zqmco\.zqm-node-02-indexer\metadata.db`
- Web UI: `http://127.0.0.1:5000`
- Runtime: project-local `.venv` with Flask, Whoosh, MCP, Waitress

## Requirements

- Python 3.11+
- Windows 10/11
- Project-local virtualenv: `.venv`
- No OneDrive-sync corruption: keep `.zqm-node-01-indexer\` outside OneDrive-synced trees

## Setup

```powershell
cd C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer

python -m venv .venv
.venv\Scripts\python -m pip install flask whoosh mcp waitress pywin32
```

## Starting the Indexer

### Recommended: Windows service

Install once as Administrator:

```powershell
service-install.bat
```

Control:

- `service-ctl.bat start`
- `service-ctl.bat stop`
- `service-ctl.bat restart`
- `service-ctl.bat status`

Service requires Admin rights. After install, it auto-starts on boot/login.

### Without elevation: silent VBS launch

```powershell
cscript //nologo service-debug-launch.vbs
```

This suppresses the console window and avoids the observable shell limitation: bash job control is not involved.

### Console run

```powershell
start.bat
```

## Rebuild

```powershell
rebuild-local.bat
```

Or from CLI:

```powershell
.venv\Scripts\python indexer.py rebuild
```

## Configuration

`config.json` in the project root stores the last scan metadata.

Default scan roots:
- `C:\PerfLogs` (skipped by default; unskip via `DEFAULT_SCAN_ROOTS`)
- `C:\Program Files`
- `C:\Program Files (x86)`
- `C:\Users`
- `C:\Windows` content excluded; `C:\Users` is indexed
- `C:\inetpub`

Skip rules:
- Skips system/system-like directories by convention
- Indexes text-extractable files for content search
- Skips very large files above `MAX_FILE_SIZE`

## API

- `GET /` — web UI
- `GET /api/search?q=<query>&limit=<n>` — BM25 search with automatic SQLite metadata fallback
- `GET /api/hybrid_search?q=<query>&limit=<n>` — explicit hybrid search endpoint
- `GET /api/recall_debug?q=<query>&limit=<n>` — Whoosh vs metadata recall comparison
- `GET /api/stats` — index statistics
- `GET /api/auth/status` — auth/path probe
- `GET /api/user/paths` — host path probe
- `GET /api/memory` — indexed memory entries
- `POST /api/index` — trigger incremental index
- `POST /api/index` with body `{"rebuild": true}` — full rebuild
- `POST /api/open` with body `{"path": "<filepath>"}` — open file in Explorer

Results include `source` when coming from metadata fallback:
- `source: index` — Whoosh BM25 result
- `source: metadata` — SQLite exact-match/LIKE fallback

## Windows Notes

- Stored-field corruption on large commits is mitigated with batched writer commits every 500 docs
- Background console sessions in this shell environment can display `bash: no job control in this shell`; use `service-install.bat`, `service-debug-launch.vbs`, or `start.bat` instead of raw background session launches
- Index is stored outside the project tree to avoid OneDrive lock conflicts
- Service logs: `logs\service_startup.log`, `logs\service_shutdown.log`

## Troubleshooting

- Service install blocked: run the `.bat` from an elevated session
- Search returns empty: rebuild from CLI
- Search returns 500: stop app, clear `.zqm-node-02-indexer\index`, rebuild
- Metadata fallback missing: run rebuild; it re-upserts SQLite metadata docs
- Port 5000 busy: use netstat/ps to identify listener, terminate exact PID before restart

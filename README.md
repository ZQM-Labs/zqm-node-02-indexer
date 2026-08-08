# zqm-node-02-indexer

Local full-disk file indexer for Windows workstations. Uses Whoosh for BM25 full-text search and SQLite for metadata exact-match recall fallback.

## About

`zqm-node-02-indexer` indexes file content and metadata on a Windows workstation and exposes a search API and web UI. It is designed for offline use on a single host, with the index and metadata DB kept outside OneDrive-synced trees to avoid lock conflicts.

## Installation

```powershell
cd C:\Users\zqmco\Desktop\enhance-repos\zqm-node-02-indexer
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Usage

```powershell
# recommended: install as Windows service (admin)
service-install.bat

# control
service-ctl.bat start
service-ctl.bat stop
service-ctl.bat restart
service-ctl.bat status

# no elevation: silent launch
cscript //nologo service-debug-launch.vbs

# console run
start.bat

# rebuild index
rebuild-local.bat
```

Web UI: `http://127.0.0.1:5000`

## Features

- Whoosh BM25 full-text search with SQLite metadata fallback
- Flask web UI and REST API
- Incremental and full rebuild indexing
- Windows service install with auto-start
- Silent VBS launch without console window
- Batched Whoosh commits to avoid stored-field corruption
- Configurable scan roots and skip rules
- MCP server integration

## API

- `GET /api/search?q=<query>&limit=<n>` — BM25 search
- `GET /api/hybrid_search?q=<query>&limit=<n>` — hybrid search
- `GET /api/recall_debug?q=<query>&limit=<n>` — Whoosh vs metadata comparison
- `GET /api/stats` — index statistics
- `POST /api/index` — incremental index
- `POST /api/index` with `{"rebuild": true}` — full rebuild
- `POST /api/open` with `{"path": "<filepath>"}` — open in Explorer

## Integration: zqm-intel-platforms

This repo is part of the `zqm-intel-platforms` stack and registers as an MCP server.

## License

MIT — see [LICENSE](LICENSE).

## Contact

zqmcomputing@gmail.com

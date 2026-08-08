# zqm-node-02-indexer

Local full-disk file indexer for Windows workstations. Whoosh BM25 full-text search with SQLite metadata exact-match fallback.

## About

`zqm-node-02-indexer` indexes file content and metadata on a Windows workstation and exposes a search API and web UI. Designed for offline use on a single host, with the index and metadata DB kept outside OneDrive-synced trees.

## Installation

```powershell
cd <repo-root>
python -m venv .venv
.\venv\Scripts\pip install -r requirements.txt
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

## Notes

- Keep the index outside OneDrive-synced directories
- Stop the service before package upgrades
- Use admin shell for service install/control

## Integration: zqm-intel-platforms

This repo integrates with `zqm-intel-platforms` for shared OSINT/CTI/SIEM/Windows-telemetry primitives.

## License

MIT — see LICENSE file.

## Contact

Alex Zelenski — zqmcomputing@gmail.com
Brand: ZQM Computing / ZQM-Labs

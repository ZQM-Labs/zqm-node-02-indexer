# ZQM Node-02 Workstation File Indexer

Containerized full-text search indexer for Windows workstations using Whoosh + SQLite + Flask REST API.

## Quick Start

```bash
# Build and run locally
docker compose up -d

# Access via Bearer token
curl -H "Authorization: Bearer test-secret" http://localhost:5000/api/health

# Or query parameter
curl "http://localhost:5000/api/stats?token=test-secret"

# Change token
API_TOKEN=my-secure-token docker compose up -d
```

## Features

- **Multi-stage Dockerfile**: 340MB production image
- **Full-text search**: Whoosh indexer + SQLite metadata fallback
- **REST API**: All `/api/*` routes require Bearer token or query param
- **Health checks**: Built-in container monitoring
- **GitHub Actions CI/CD**: Auto-builds and pushes to GHCR on commits
- **WSL2 compatible**: Mounts for Windows file systems (requires setup)
- **Persistent volumes**: Index data survives restarts

## API Endpoints

All endpoints require `Authorization: Bearer {API_TOKEN}` header or `?token={API_TOKEN}` query param.

- `GET  /api/health` - Health check
- `GET  /api/stats` - Index statistics
- `GET  /api/search?q=query` - Full-text search
- `POST /api/index` - Rebuild index (POST body: `{"rebuild": true}`)
- `GET  /api/roots` - Configured scan roots
- `/` - Web UI (access at http://localhost:5000)

## Environment Variables

- `API_TOKEN` - Bearer token for API authentication (default: `test-secret`)
- `PORT` - Server port (default: `5000`)
- `ZQM_GPG_KEY` - GPG key identifier (if using GPG auth)

## Registry

Image: `ghcr.io/zqm-computing/zqm-node-02-indexer:latest`

## Notes

- Windows-only dependencies (pywin32) are excluded from Dockerfile
- Health checks use curl instead of Python to avoid token visibility
- WSL2 users: Uncomment volume mounts in docker-compose.yml and set up `wsl --mount` for Windows drive access
- API token appears in query params—use Bearer headers in production

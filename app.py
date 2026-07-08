"""
ZQM Node-02 Workstation File Indexer - Flask Web UI
Provides a web interface for searching and managing the file index across the entire workstation.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from threading import Timer
from datetime import datetime

from flask import Flask, render_template, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indexer import build_index, search_index, search_metadata, get_index_stats, CONFIG_FILE, DEFAULT_SCAN_ROOTS

_BASE = Path(__file__).resolve().parent
_API_TOKEN = os.environ.get("API_TOKEN", "").strip()

def _memory_dir_with_fallback():
    try:
        import hermes_constants
        return Path(hermes_constants.get_hermes_home()) / "memories"
    except Exception:
        return Path(os.path.expanduser("~")) / ".local" / "share" / "hermes" / "memories"

_HERMES_MEMORY_DIR = _memory_dir_with_fallback()

try:
    import zqm_auth
    _AUTH_TOKEN = zqm_auth.current_token()
except Exception:
    _AUTH_TOKEN = os.environ.get("ZQM_SERVICE_TOKEN", "")
    zqm_auth = None

if _BASE not in sys.path:
    sys.path.insert(0, str(_BASE))

_INDEX_FIELDS = {"filename", "filetype", "path", "size", "modified"}
CANONICAL_CONFIG_KEYS = {
    "root_paths",
    "last_indexed",
    "total_files",
    "indexed_files",
    "skipped_files",
}


def _auth_status():
    user = _zqm_user()
    return jsonify({
        "authenticated": bool(user),
        "user": user,
        "token_prefix": (_AUTH_TOKEN[:8] + "...") if _AUTH_TOKEN else "",
        "zqm_user": user,
    })


def _user_paths():
    user = _zqm_user()
    base = Path(os.path.expanduser("~"))
    return jsonify({
        "home": str(base),
        "appdata_local": str(base / "AppData" / "Local"),
        "appdata_roaming": str(base / "AppData" / "Roaming"),
        "desktop": str(base / "Desktop"),
        "documents": str(base / "Documents"),
        "downloads": str(base / "Downloads"),
        "user": user,
        "zqm_user": user,
    })


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()


def _zqm_user():
    if zqm_auth is None:
        return None
    user, _ = zqm_auth.parse_credentials(request.headers)
    return user


def _check_api_token():
    """Verify API token from Authorization header or token query param."""
    if not _API_TOKEN:
        return True  # No token configured, allow all requests
    
    # Check Bearer token in Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        if token == _API_TOKEN:
            return True
    
    # Check token query parameter (fallback)
    token_param = request.args.get('token', '')
    if token_param == _API_TOKEN:
        return True
    
    return False


@app.before_request
def check_auth():
    """Check API token on all /api/* routes."""
    if request.path.startswith('/api/') and not _check_api_token():
        return jsonify({"error": "Unauthorized: invalid or missing API token"}), 401


def canonicalize_fields(raw):
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = [raw]
    return [f for f in raw if f in _INDEX_FIELDS]


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_time(iso_str):
    if not iso_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_str


@app.route("/")
def index():
    stats = get_index_stats()
    user = _zqm_user()
    return render_template("index.html", stats=stats, zqm_user=user)


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error", "details": str(e)}), 500


def _search(query, limit=50, fields=None):
    user = _zqm_user()
    if not query:
        return jsonify({"results": [], "total": 0, "query": query, "zqm_user": user})

    try:
        whoosh_results = search_index(query, limit=limit, field=fields)
    except Exception:
        whoosh_results = []

    if not whoosh_results:
        meta = search_metadata(query, limit=limit)
        if meta:
            for r in meta:
                r.setdefault("source", "metadata")
            whoosh_results = meta

    formatted = []
    for r in whoosh_results:
        source = r.pop("source", "index")
        r["size_formatted"] = format_size(r.get("size") or 0)
        r["modified_formatted"] = format_time(r.get("modified"))
        r["source"] = "metadata" if source == "metadata" else "index"
        r.setdefault("size_formatted", "0 B")
        r.setdefault("modified_formatted", "Unknown")
        formatted.append(r)

    return jsonify({"results": formatted, "total": len(formatted), "query": query, "zqm_user": user})


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    limit = request.args.get("limit", 50, type=int)
    fields = canonicalize_fields(request.args.getlist("fields"))
    return _search(query, limit=limit, fields=fields)


@app.route("/api/stats")
def api_stats():
    stats = get_index_stats()
    user = _zqm_user()
    if stats:
        stats["zqm_user"] = user
        return jsonify(stats)
    return jsonify({"document_count": 0, "config": {}, "zqm_user": user})


@app.route("/api/auth/status")
def api_auth_status():
    return _auth_status()


@app.route("/api/user/paths")
def api_user_paths():
    return _user_paths()


@app.route("/api/hybrid_search")
def api_hybrid_search():
    query = request.args.get("q", "").strip()
    limit = request.args.get("limit", 30, type=int)
    return _search(query, limit=limit)


@app.route("/api/index", methods=["POST"])
def api_index():
    data = request.get_json() or {}
    rebuild = bool(data.get("rebuild", False))
    user = _zqm_user()

    try:
        config = build_index(rebuild=rebuild)
        config = {k: config.get(k) for k in CANONICAL_CONFIG_KEYS if k in config}
        return jsonify({"success": True, "config": config, "zqm_user": user})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "zqm_user": user}), 500


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        data = request.get_json() or {}
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                config = json.load(f)
        config = {k: config[k] for k in CANONICAL_CONFIG_KEYS if k in config}
        for key, value in data.items():
            if key in CANONICAL_CONFIG_KEYS:
                config[key] = value
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return jsonify({"success": True, "config": config})

    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    return jsonify({k: config.get(k) for k in CANONICAL_CONFIG_KEYS})


@app.route("/api/roots")
def api_roots():
    return jsonify({"roots": DEFAULT_SCAN_ROOTS})


@app.route("/api/recall_debug")
def api_recall_debug():
    query = request.args.get("q", "").strip()
    limit = request.args.get("limit", 10, type=int)
    user = _zqm_user()

    if not query:
        return jsonify({"error": "missing q", "zqm_user": user}), 400

    try:
        whoosh = search_index(query, limit=limit)
    except Exception as e:
        whoosh = []
        whoosh_error = str(e)
    else:
        whoosh_error = None

    try:
        meta = search_metadata(query, limit=limit)
    except Exception as e:
        meta = []
        meta_error = str(e)
    else:
        meta_error = None

    return jsonify({
        "query": query,
        "whoosh_count": len(whoosh),
        "metadata_count": len(meta),
        "whoosh_error": whoosh_error,
        "metadata_error": meta_error,
        "whoosh_samples": whoosh[:3],
        "metadata_samples": meta[:3],
        "zqm_user": user,
    })


@app.route("/api/open", methods=["POST"])
def api_open_file():
    """Open a file in Windows Explorer with path traversal protection."""
    try:
        data = request.get_json() or {}
        path = data.get("path", "")
        if not path:
            return jsonify({"success": False, "error": "Invalid or missing path"}), 400

        # Security: Resolve and validate path to prevent traversal attacks
        try:
            p = Path(path).resolve()
            # Ensure path is absolute and exists
            if not p.is_absolute() or not p.exists() or not p.is_file():
                return jsonify({"success": False, "error": "Invalid or missing path"}), 400

            # Additional security: ensure path is under allowed roots
            allowed_roots = [Path(r).resolve() for r in DEFAULT_SCAN_ROOTS]
            user_home = Path.home().resolve()
            allowed_roots.append(user_home)

            is_allowed = any(
                str(p).startswith(str(root))
                for root in allowed_roots
            )

            if not is_allowed:
                return jsonify({
                    "success": False,
                    "error": "Access denied: path outside allowed directories"
                }), 403

        except (OSError, ValueError) as e:
            return jsonify({"success": False, "error": f"Path validation failed: {e}"}), 400

        # os.startfile is Windows-only; skip in containerized/non-Windows environments
        if hasattr(os, 'startfile'):
            os.startfile(str(p))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/memory")
def api_memory():
    """API endpoint exposing Hermes agent memory files for observability."""
    store = {}
    mem_dir = _HERMES_MEMORY_DIR
    for name in ("MEMORY.md", "USER.md", "MEMORY.md.lock"):
        path = mem_dir / name
        if path.is_file():
            try:
                store[name] = path.read_text(encoding="utf-8", errors="ignore")
            except Exception as exc:
                store[name] = f"[error reading {name}: {exc}]"
        else:
            store[name] = ""

    raw = store.get("MEMORY.md", "") or ""
    store["memory_entries"] = [chunk for chunk in raw.split("\n§\n")]
    return jsonify(store)


@app.route("/api/health")
def api_health():
    """Health check for local dashboards."""
    try:
        stats = get_index_stats() or {}
    except Exception:
        stats = {}
    return jsonify({
        "status": "ready",
        "indexed_files": stats.get("indexed_files"),
        "document_count": stats.get("document_count"),
        "last_indexed": stats.get("last_indexed"),
        "memory_dir": str(_HERMES_MEMORY_DIR),
        "memory_ok": (_HERMES_MEMORY_DIR / "MEMORY.md").is_file(),
    })


def open_browser():
    # Only open in interactive console sessions, not under service/pythonw contexts.
    if not sys.stdout or not hasattr(sys.stdout, "isatty"):
        return
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n{'='*60}")
    print(f"  ZQM Node-02 Workstation File Indexer")
    print(f"  Scanning: {DEFAULT_SCAN_ROOTS}")
    print(f"  Hermes memory dir: {_HERMES_MEMORY_DIR}")
    print(f"  Running at: http://0.0.0.0:{port}")
    if _API_TOKEN:
        print(f"  API Token: {_API_TOKEN[:16]}...")
    else:
        print(f"  API Token: (none - all requests allowed)")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*60}\n")

    Timer(1.5, open_browser).start()

    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=port)
    except Exception:
        app.run(host="0.0.0.0", port=port, debug=False)

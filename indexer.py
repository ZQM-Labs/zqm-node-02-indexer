"""
ZQM Node-02 Workstation File Indexer
Scans the entire workstation, extracts metadata, and builds a Whoosh search index.
Callable via REST API for future use.
"""

import os
import sys
import json
import mimetypes
import sqlite3
from datetime import datetime
from pathlib import Path

from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, DATETIME, NUMERIC
from whoosh.qparser import MultifieldParser, QueryParser, AndGroup
from whoosh import scoring

# --- Configuration ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(os.path.expanduser("~"), ".zqm-node-02-indexer", "index")
METADATA_DB = os.path.join(os.path.expanduser("~"), ".zqm-node-02-indexer", "metadata.db")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")


def _init_metadata_db():
    """Initialize the SQLite metadata store for exact-match recall fallbacks."""
    os.makedirs(os.path.dirname(METADATA_DB), exist_ok=True)
    conn = sqlite3.connect(METADATA_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            filename TEXT,
            extension TEXT,
            size INTEGER,
            filetype TEXT,
            directory TEXT,
            modified TEXT,
            created TEXT,
            content TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_files_directory ON files(directory)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_files_filetype ON files(filetype)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_files_size ON files(size)")
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(filename, directory, path, content='files', content_rowid='rowid')")
    except Exception:
        pass
    conn.commit()
    conn.close()


def _ensure_metadata_db():
    if not os.path.exists(METADATA_DB):
        _init_metadata_db()


def _upsert_metadata_doc(metadata, content=""):
    _ensure_metadata_db()
    conn = sqlite3.connect(METADATA_DB)
    try:
        conn.execute(
            """
            INSERT INTO files (path, filename, extension, size, filetype, directory, modified, created, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
              filename=excluded.filename,
              extension=excluded.extension,
              size=excluded.size,
              filetype=excluded.filetype,
              directory=excluded.directory,
              modified=excluded.modified,
              created=excluded.created,
              content=excluded.content
            """,
            (
                metadata["path"],
                metadata.get("filename"),
                metadata.get("extension"),
                metadata.get("size", 0),
                metadata.get("filetype"),
                metadata.get("directory"),
                metadata.get("modified").isoformat() if metadata.get("modified") else None,
                metadata.get("created").isoformat() if metadata.get("created") else None,
                content,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def search_metadata(query_str, limit=50):
    """Exact-match / substring recall fallback over the SQLite metadata store."""
    _ensure_metadata_db()
    conn = sqlite3.connect(METADATA_DB)
    conn.row_factory = sqlite3.Row
    try:
        like = f"%{query_str.replace('%', '%%')}%"
        rows = conn.execute(
            """
            SELECT path, filename, extension, size, filetype, directory, modified, created
            FROM files
            WHERE lower(path) LIKE ?1
               OR lower(filename) LIKE ?1
               OR lower(directory) LIKE ?1
               OR lower(filetype) LIKE ?1
               OR lower(content) LIKE ?1
            LIMIT ?
            """,
            (like.lower(), int(limit)),
        ).fetchall()
        rows = list(rows)
        size = max(limit, 20)
        if len(rows) < size:
            try:
                fts = conn.execute(
                    """
                    SELECT files.path, files.filename, files.extension, files.size, files.filetype, files.directory, files.modified, files.created
                    FROM files_fts
                    JOIN files ON files.rowid = files_fts.rowid
                    WHERE files_fts MATCH ?
                    LIMIT ?
                    """,
                    (query_str.replace('"', '""'), int(limit)),
                ).fetchall()
                seen = {r["path"] for r in rows}
                for r in fts:
                    if r["path"] not in seen:
                        rows.append(r)
                        seen.add(r["path"])
            except Exception:
                pass
        results = []
        for r in rows[: int(limit)]:
            results.append(
                {
                    "path": r["path"],
                    "filename": r["filename"],
                    "extension": r["extension"],
                    "size": r["size"],
                    "modified": r["modified"],
                    "filetype": r["filetype"],
                    "directory": r["directory"],
                    "score": 0.0,
                }
            )
        return results
    finally:
        conn.close()


def get_metadata_stats():
    _ensure_metadata_db()
    conn = sqlite3.connect(METADATA_DB)
    try:
        row = conn.execute("SELECT COUNT(*) AS c FROM files").fetchone()
        return {"metadata_document_count": row[0]}
    finally:
        conn.close()

# Default scan roots: user data and app locations
DEFAULT_SCAN_ROOTS = [
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\Users",
    "C:\\inetpub",
]

# Never scan these roots
SKIP_ROOTS = {
    "C:\\PerfLogs",
    "C:\\Windows",
}

# Directories to skip during os.walk
SKIP_DIRS = {
    "WindowsPowerShell",
    "__pycache__",
    ".git",
    "node_modules",
    "venv",
    ".venv",
    ".npm",
    ".cargo",
    "System Volume Information",
    "$Recycle.Bin",
    "Temp",
    "tmp",
    "cache",
    "Cache",
}

SKIP_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".img", ".iso",
    ".vhd", ".vmdk", ".pdb", ".lib", ".obj", ".o", ".pyc", ".pyo",
    ".msi", ".msp", ".cab", ".drv", ".sys", ".ttf", ".fon",
}


MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max for text extraction
MAX_FILES_PER_SCAN = 50000  # Safety limit

def get_schema():
    """Define the Whoosh search schema."""
    return Schema(
        path=ID(unique=True, stored=True),
        filename=TEXT(stored=True, phrase=True),
        extension=ID(stored=True),
        size=NUMERIC(stored=True),
        created=DATETIME(stored=True),
        modified=DATETIME(stored=True),
        content=TEXT(stored=True, phrase=True),
        filetype=ID(stored=True),
        directory=TEXT(stored=True, phrase=True),
        depth=NUMERIC(stored=True),
    )


def classify_filetype(ext, filepath):
    """Classify a file into a type category."""
    mime, _ = mimetypes.guess_type(filepath)
    if mime:
        if mime.startswith("text/"):
            return mime
        return mime.split("/")[0]

    ext = ext.lower()
    text_exts = {".txt", ".md", ".rst", ".log", ".cfg", ".ini", ".conf", ".yml", ".yaml", ".toml"}
    code_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp",
                 ".cs", ".rb", ".go", ".rs", ".swift", ".kt", ".scala", ".php", ".pl",
                 ".sh", ".bat", ".ps1", ".sql", ".r", ".m", ".mm"}
    web_exts = {".html", ".htm", ".css", ".scss", ".less", ".xml", ".json", ".svg"}
    img_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".ico"}
    audio_exts = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"}
    video_exts = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}
    doc_exts = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"}
    archive_exts = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"}

    if ext in text_exts:
        return "text/plain"
    elif ext in code_exts:
        return "text/code"
    elif ext in web_exts:
        return "text/web"
    elif ext in img_exts:
        return "image"
    elif ext in audio_exts:
        return "audio"
    elif ext in video_exts:
        return "video"
    elif ext in doc_exts:
        return "document"
    elif ext in archive_exts:
        return "archive"
    return "unknown"


def get_file_metadata(filepath):
    """Extract metadata from a file."""
    try:
        stat = os.stat(filepath)
        path_obj = Path(filepath)
        ext = path_obj.suffix.lower()
        filetype = classify_filetype(ext, filepath)

        return {
            "path": filepath,
            "filename": path_obj.name,
            "extension": ext,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "filetype": filetype,
            "directory": str(path_obj.parent),
        }
    except (OSError, PermissionError):
        return None


def extract_text_content(filepath, max_size=MAX_FILE_SIZE):
    """Extract text content from a file for indexing."""
    ext = Path(filepath).suffix.lower()

    text_extensions = {
        ".txt", ".md", ".rst", ".log", ".cfg", ".ini", ".conf", ".yml", ".yaml", ".toml",
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp",
        ".cs", ".rb", ".go", ".rs", ".swift", ".kt", ".scala", ".php", ".pl",
        ".sh", ".bat", ".ps1", ".sql", ".r", ".m", ".mm",
        ".html", ".htm", ".css", ".scss", ".less", ".xml", ".json", ".svg",
        ".csv", ".tsv", ".env", ".gitignore", ".dockerfile", ".makefile",
        ".cmake", ".gradle", ".sln", ".csproj", ".props", ".targets",
    }

    if ext not in text_extensions:
        return ""

    try:
        size = os.path.getsize(filepath)
        if size > max_size or size == 0:
            return ""
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, PermissionError, UnicodeDecodeError):
        return ""


def scan_directory(root_path, progress_callback=None):
    """Recursively scan a directory and yield file metadata."""
    root_path = os.path.abspath(root_path)
    file_count = 0
    error_count = 0

    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # Skip unwanted directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            ext = Path(filename).suffix.lower()

            if ext in SKIP_EXTENSIONS:
                continue

            try:
                metadata = get_file_metadata(filepath)
                if metadata:
                    file_count += 1
                    if progress_callback:
                        progress_callback(filepath, file_count)
                    yield metadata

                    if file_count >= MAX_FILES_PER_SCAN:
                        return
            except Exception as e:
                error_count += 1
                if error_count <= 10:  # Log first 10 errors only
                    print(f"  Warning: Error processing {filepath}: {e}")
                continue


def _clear_whoosh_locks(index_dir):
    """Best-effort removal of Whoosh lock/temp artifacts blocking a rebuild."""
    for name in ("MAIN_WRITELOCK", "MAIN.tmp"):
        path = os.path.join(index_dir, name)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
        except Exception:
            pass


def build_index(root_paths=None, rebuild=False):
    """Build or update the Whoosh search index across multiple root paths."""
    if root_paths is None:
        root_paths = DEFAULT_SCAN_ROOTS

    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)

    if rebuild and exists_in(INDEX_DIR):
        import shutil
        _clear_whoosh_locks(INDEX_DIR)
        shutil.rmtree(INDEX_DIR, ignore_errors=True)
        os.makedirs(INDEX_DIR, exist_ok=True)

    if not exists_in(INDEX_DIR):
        ix = create_in(INDEX_DIR, get_schema())
    else:
        ix = open_dir(INDEX_DIR)

    writer = ix.writer(limitmb=64)

    total_files = 0
    indexed_files = 0
    skipped_files = 0
    batch_since_commit = 0

    print("=" * 60)
    print("  ZQM Node-02 Workstation File Indexer")
    print("=" * 60)

    for root_path in root_paths:
        if not os.path.exists(root_path):
            print(f"  Skipping (not found): {root_path}")
            continue
        if any(root_path.startswith(p) for p in SKIP_ROOTS):
            print(f"  Skipping root prefix: {root_path}")
            continue

        print(f"\nScanning: {root_path}")
        print("-" * 60)

        for metadata in scan_directory(root_path):
            total_files += 1
            content = extract_text_content(metadata["path"])

            try:
                writer.add_document(
                    path=metadata["path"],
                    filename=metadata["filename"],
                    extension=metadata["extension"],
                    size=metadata["size"],
                    created=metadata["created"],
                    modified=metadata["modified"],
                    content=content,
                    filetype=metadata["filetype"],
                    directory=metadata["directory"],
                    depth=0,
                )
                indexed_files += 1
                batch_since_commit += 1
                if indexed_files % 500 == 0:
                    print(f"  Indexed {indexed_files} files...")
                if batch_since_commit >= 500:
                    try:
                        writer.commit()
                    except Exception:
                        pass
                    batch_since_commit = 0
                    writer = ix.writer(limitmb=64)
                try:
                    _upsert_metadata_doc(metadata, content=content or "")
                except Exception:
                    pass
            except Exception:
                skipped_files += 1

    if batch_since_commit:
        try:
            writer.commit()
        except Exception:
            pass

    print("\n" + "=" * 60)
    print(f"  Scan Complete")
    print(f"  Files found:   {total_files}")
    print(f"  Files indexed: {indexed_files}")
    print(f"  Files skipped: {skipped_files}")
    if skipped_files > 0:
        skip_rate = (skipped_files / total_files * 100) if total_files > 0 else 0
        print(f"  Skip rate:     {skip_rate:.1f}%")
        if skip_rate > 50:
            print(f"  WARNING: High skip rate detected. Review SKIP_DIRS and SKIP_EXTENSIONS.")
    print("=" * 60)

    config = {
        "root_paths": root_paths,
        "last_indexed": datetime.now().isoformat(),
        "total_files": total_files,
        "indexed_files": indexed_files,
        "skipped_files": skipped_files,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    return config


def _safe_hit(hit, fallback_query=None):
    """Return a clean result dict from a Whoosh hit, with safe fallbacks."""
    def _str(v, default=""):
        if v is None:
            return default
        if isinstance(v, bytes):
            try:
                return v.decode("utf-8", errors="replace")
            except Exception:
                return default
        return str(v)

    def _num(v, default=0):
        try:
            return int(v)
        except Exception:
            return default

    def _time(v, default=None):
        if not v:
            return default
        try:
            return v.isoformat()
        except Exception:
            return default

    try:
        path = _str(hit["path"], "")
        directory = _str(hit.get("directory", ""), "")
        filename = _str(hit.get("filename", ""), "")
        if not filename and path:
            filename = Path(path).name
        if not directory and path:
            directory = str(Path(path).parent)
        return {
            "path": path,
            "filename": filename,
            "extension": _str(hit.get("extension", ""), ""),
            "size": _num(hit.get("size", 0), 0),
            "modified": _time(hit.get("modified")),
            "filetype": _str(hit.get("filetype", ""), ""),
            "directory": directory,
            "score": float(getattr(hit, "score", 0.0) or 0.0),
        }
    except Exception:
        if fallback_query:
            return {
                "path": "",
                "filename": "(index error)",
                "extension": "",
                "size": 0,
                "modified": None,
                "filetype": "",
                "directory": "",
                "score": 0.0,
            }
        return {}


def search_index(query_str, limit=50, field=None, fields=None):
    """Search the index and return results."""
    if not exists_in(INDEX_DIR):
        return []

    ix = open_dir(INDEX_DIR)

    effective_fields = fields or [field] if field else None
    if not effective_fields:
        effective_fields = ["filename", "content", "directory", "filetype"]

    qp = MultifieldParser(
        effective_fields,
        schema=ix.schema,
        group=AndGroup,
        fieldboosts={"filename": 5, "filetype": 3, "directory": 2, "content": 1},
    )

    try:
        q = qp.parse(query_str)
    except Exception:
        return []

    output = []
    try:
        with ix.searcher(weighting=scoring.BM25F()) as searcher:
            results = searcher.search(q, limit=limit)
            try:
                results.fragmenter.maxchars = 200
                results.fragmenter.surround = 50
            except Exception:
                pass

            for hit in results:
                row = _safe_hit(hit, fallback_query=query_str)
                if row.get("filename") == "(index error)":
                    continue
                output.append(row)
    except Exception:
        return []

    return output


def get_index_stats():
    """Get statistics about the current index."""
    if not exists_in(INDEX_DIR):
        return None

    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        doc_count = searcher.doc_count()

    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            config = json.load(f)

    return {
        "document_count": doc_count,
        "config": config,
        "status": "ready",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ZQM Node-02 Workstation File Indexer")
    parser.add_argument("action", nargs="?", default="index",
                        choices=["index", "rebuild", "search", "stats"],
                        help="Action to perform")
    parser.add_argument("query", nargs="?", default="", help="Search query")
    parser.add_argument("--limit", type=int, default=30, help="Search result limit")
    parser.add_argument("--field", default=None, help="Search specific field")

    args = parser.parse_args()

    if args.action == "index":
        build_index()
    elif args.action == "rebuild":
        build_index(rebuild=True)
    elif args.action == "search":
        if not args.query:
            print("Please provide a search query.")
            sys.exit(1)
        results = search_index(args.query, limit=args.limit, field=args.field)
        print(f"\nFound {len(results)} results for: '{args.query}'\n")
        for i, r in enumerate(results, 1):
            size_str = f"{r['size'] / 1024:.1f} KB" if r['size'] < 1024*1024 else f"{r['size'] / (1024*1024):.1f} MB"
            print(f"{i:3d}. {r['filename']}")
            print(f"     Path: {r['directory']}")
            print(f"     Type: {r['filetype']} | Size: {size_str} | Score: {r['score']:.2f}")
            print()
    elif args.action == "stats":
        stats = get_index_stats()
        if stats:
            print(f"Index Statistics:")
            print(f"  Documents indexed: {stats['document_count']}")
            if stats['config']:
                print(f"  Scan roots: {stats['config'].get('root_paths', 'N/A')}")
                print(f"  Last indexed: {stats['config'].get('last_indexed', 'N/A')}")
                print(f"  Total files found: {stats['config'].get('total_files', 'N/A')}")
                print(f"  Files indexed: {stats['config'].get('indexed_files', 'N/A')}")
        else:
            print("No index found. Run 'index' action first.")
"""Dynamic orphan reference engine for zqm-node-02-indexer.

This module adds bidirectional orphan detection over indexed files and
known repository roots without changing the existing Whoosh or SQLite
``files`` table contracts.

Concepts
--------
- Static dependency graph: import-style references within repo text files.
- Bidirectional validation: for any indexed file, compare lived-in refs vs
  reverse references to materialize true orphan status rather than stale
  filesystem absence.
- Human review gate: intentional orphan hinting keeps deprecated plans/RCAs
  from surfacing as remediation items.
"""

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

ORPHAN_METADATA_DB = os.path.join(os.path.expanduser("~"), ".zqm-node-02-indexer", "metadata.db")

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max for text extraction
MAX_FILES_PER_SCAN = 50000  # Safety limit for repo scans

ORPHAN_REPO_ROOTS = [
    os.path.abspath(r"C:\Users\zqmco\src\hermes-agent"),
    os.path.abspath(r"C:\Users\zqmco\OneDrive\Desktop\zqm-node-01-indexer"),
    os.path.abspath(r"C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer"),
]
ORPHAN_REPO_SKIP_DIRS = [".git", ".venv", "__pycache__"]
ORPHAN_REPO_SKIP_FILES = {"*.pyc", "*.pyo", ".DS_Store", "Thumbs.db"}

ORPHAN_FORWARD_REF_PATTERNS = [
    # Python imports: from X import Y / import X / import X.Y
    (r"\.py$", re.compile(r"(?:^|\b)(?:from\s+([\.\w]+)\s+import|import\s+([\.\w]+))", re.IGNORECASE)),
    # PowerShell imports / dot-sourcing
    (r"\.ps1$", re.compile(r"(?:\.\s+|Import-Module\s+|using\s+module\s+)([^\r\n]+)", re.IGNORECASE)),
    # Batch/Cmd indirection
    (r"\.(?:bat|cmd)$", re.compile(r"\b(?:call|start|pushd)\s+([^\r\n]+)", re.IGNORECASE)),
    # Flask app factory references: Blueprint / register_blueprint(...)
    (r"app\.py$", re.compile(r"(?:Blueprint|register_blueprint)\s*\(\s*([^\)]+)", re.IGNORECASE)),
    # HTML includes/extends/from
    (r"\.html$", re.compile(r"{%\s*(?:include|extends|from)\s+['\"]([^'\"]+)['\"]", re.IGNORECASE)),
    # YAML/JSON service references targeting script/module paths
    (r"\.(?:yml|yaml|json)$", re.compile(r"(?:path:|entrypoint:|module:|cmd:)\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)),
]

INTENTIONAL_ORPHAN_HINTS = {
    "archive", "deprecated", "old", "backup", "bak", "rca-", "plan-",
    ".bak.", "tests/fixtures", "fixtures",
}


def _match_patterns(filepath):
    """Return applicable orphan forward-ref patterns for a file."""
    suffix = Path(filepath).suffix.lower()
    for pattern_suffix, compiled in ORPHAN_FORWARD_REF_PATTERNS:
        if suffix == pattern_suffix.lstrip(".") or filepath.lower().endswith(pattern_suffix):
            yield compiled


def _is_intentional_orphan(filepath):
    """Heuristic: true if filename strongly suggests deprecation/intentional status."""
    name = Path(filepath).name.lower()
    return any(hint in name for hint in INTENTIONAL_ORPHAN_HINTS)


def _repo_local_scope(filepath):
    """Map indexed file to its owning repo root, or None."""
    p = os.path.abspath(filepath)
    for root in ORPHAN_REPO_ROOTS:
        if p.startswith(root + os.sep) or p == root:
            return root
    return None


def ensure_orphan_tables(metadata_db):
    """Idempotently create orphan tables on top of existing metadata store."""
    os.makedirs(os.path.dirname(metadata_db), exist_ok=True)
    conn = sqlite3.connect(metadata_db)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS repo_scan_runs (
            repo_root TEXT PRIMARY KEY,
            scanned_at TEXT,
            status TEXT,
            intentional_count INTEGER DEFAULT 0,
            unresolved_count INTEGER DEFAULT 0,
            suppressed_count INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bidirectional_refs (
            src TEXT,
            dst TEXT,
            repo_root TEXT,
            kind TEXT,
            discovered_at TEXT,
            PRIMARY KEY(src, dst, kind)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orphans (
            path TEXT PRIMARY KEY,
            source TEXT,
            kind TEXT,
            reason TEXT,
            target_ref TEXT,
            repo_root TEXT,
            discovered_at TEXT,
            updated_at TEXT,
            intentional INTEGER DEFAULT 0,
            reprocessed INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_orphans_repo ON orphans(repo_root)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_orphans_intentional ON orphans(intentional)
        """
    )
    conn.commit()
    conn.close()


def _normalize_target(target):
    if target is None:
        return None, None
    if isinstance(target, (tuple, list)):
        target = " ".join(str(x) for x in target if x)
    target = str(target).strip()
    if not target:
        return None, None
    return target, Path(target).name.lower()


def score_file_refs(filepath, forward_refs, content):
    """Return a labeled reference summary for a single candidate file.

    Parameters
    ----------
    filepath : str
    forward_refs : list[str]
    content : str

    Returns
    -------
    dict with keys:
        path, repo, intentional, forward_refs, reverse_refs,
        orphan_candidate, resilience, reason
    """
    repo = _repo_local_scope(filepath)
    path = os.path.abspath(filepath)
    intentional = _is_intentional_orphan(filepath)

    present = set()
    reversed_refs = []

    for ref in forward_refs or []:
        ref_norm, _ = _normalize_target(ref)
        if not ref_norm:
            continue
        present.add(ref_norm)
        candidate = ref_norm
        if not Path(candidate).is_absolute() and repo:
            candidate = str(Path(repo) / ref_norm)
        if not Path(candidate).exists() and not any(
            candidate.startswith(root) for root in ORPHAN_REPO_ROOTS
        ):
            reversed_refs.append(ref_norm)

    # A file is only an orphan candidate when it has no usable forward refs
    # AND is not anchored in any known repo root. In-repo files without
    # cross-repo refs are normal, not orphaned.
    orphan_candidate = not present and repo is None and not intentional
    resilience = "strong" if present else "weak"
    reason = ""
    if intentional:
        reason = "intentional/archival"
    elif orphan_candidate:
        reason = f"no forward refs and outside {len(ORPHAN_REPO_ROOTS)} repo roots"
    elif reversed_refs:
        reason = f"non-repo refs: {', '.join(reversed_refs[:5])}"

    return {
        "path": path,
        "repo": repo,
        "intentional": intentional,
        "forward_refs": sorted(present)[:20],
        "reverse_refs": sorted(reversed_refs)[:20],
        "orphan_candidate": orphan_candidate,
        "resilience": resilience,
        "reason": reason,
    }


def upsert_orphan_record(filepath, source, kind, reason, target_ref=None, repo_root=None, intentional=None):
    metadata_db = os.environ.get("ZQM_ORPHAN_METADATA_DB") or os.path.join(os.path.expanduser("~"), ".zqm-node-02-indexer", "metadata.db")
    ensure_orphan_tables(metadata_db)
    conn = sqlite3.connect(metadata_db)
    try:
        conn.execute(
            """
            INSERT INTO orphans (path, source, kind, reason, target_ref, repo_root, discovered_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
              source=excluded.source,
              kind=excluded.kind,
              reason=excluded.reason,
              updated_at=excluded.updated_at
            """,
            (
                os.path.abspath(filepath),
                source,
                kind,
                reason,
                target_ref,
                repo_root or _repo_local_scope(filepath),
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        if intentional is not None:
            try:
                conn.execute(
                    "UPDATE orphans SET intentional = ?, updated_at = ? WHERE path = ?",
                    (1 if intentional else 0, datetime.utcnow().isoformat(), os.path.abspath(filepath)),
                )
                conn.commit()
            except Exception:
                pass
    finally:
        conn.close()


def update_orphan_intentional(path, intentional=True):
    metadata_db = os.path.join(os.path.expanduser("~"), ".zqm-node-02-indexer", "metadata.db")
    ensure_orphan_tables(metadata_db)
    conn = sqlite3.connect(metadata_db)
    try:
        conn.execute(
            "UPDATE orphans SET intentional = ?, updated_at = ? WHERE path = ?",
            (1 if intentional else 0, datetime.utcnow().isoformat(), os.path.abspath(path)),
        )
        conn.commit()
    finally:
        conn.close()


def record_repo_scan(repo_root, status, counts):
    metadata_db = os.path.join(os.path.expanduser("~"), ".zqm-node-02-indexer", "metadata.db")
    ensure_orphan_tables(metadata_db)
    conn = sqlite3.connect(metadata_db)
    try:
        conn.execute(
            """
            INSERT INTO repo_scan_runs (repo_root, scanned_at, status, intentional_count, unresolved_count,
            suppressed_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo_root) DO UPDATE SET
              scanned_at=excluded.scanned_at,
              status=excluded.status,
              intentional_count=excluded.intentional_count,
              unresolved_count=excluded.unresolved_count,
              suppressed_count=excluded.suppressed_count
            """,
            (
                os.path.abspath(repo_root),
                datetime.utcnow().isoformat(),
                status,
                int(counts.get("intentional", 0)),
                int(counts.get("unresolved", 0)),
                int(counts.get("suppressed", 0)),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_prioritized_orphans(repo_root=None, include_intentional=False, limit=200):
    metadata_db = os.path.join(os.path.expanduser("~"), ".zqm-node-02-indexer", "metadata.db")
    ensure_orphan_tables(metadata_db)
    conn = sqlite3.connect(metadata_db)
    conn.row_factory = sqlite3.Row
    try:
        query = """
            SELECT path, source, kind, reason, target_ref, repo_root,
                   discovered_at, updated_at, intentional, reprocessed
            FROM orphans
            WHERE 1=1
        """
        params = []
        if repo_root:
            query += " AND repo_root = ?"
            params.append(repo_root)
        if not include_intentional:
            query += " AND intentional = 0"
        query += """
            ORDER BY
              intentional ASC,
              reprocessed ASC,
              updated_at DESC
            LIMIT ?
        """
        params.append(int(limit))
        return [dict(r) for r in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def metadata_db_path():
    return ORPHAN_METADATA_DB


def scan_repo_for_orphans(repo_root):
    """Scan a repo root for text-file orphans using forward refs and existence checks."""
    repo_root = str(Path(repo_root).resolve())
    rel_depth = len(repo_root.split(os.sep))
    candidates = []
    for dirpath, dirnames, filenames in os.walk(repo_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in ORPHAN_REPO_SKIP_DIRS and not d.startswith(".")]
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if not os.path.isfile(filepath):
                continue
            suffix = Path(filename).suffix.lower()
            if suffix in {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}:
                continue
            if any(pattern.lower().format('') in filename.lower() for pattern in ['*.pyc','*.pyo']):
                continue
            candidates.append(filepath)

    # Limit scan to avoid runaway walks
    candidates = candidates[:MAX_FILES_PER_SCAN]

    counts = {
        "intentional": 0,
        "orphan": 0,
        "nonrepo": 0,
        "unresolved": 0,
        "total_candidates": len(candidates),
    }
    seen_paths = set()
    seen_repo_refs = set()
    for root in ORPHAN_REPO_ROOTS:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in ORPHAN_REPO_SKIP_DIRS and not d.startswith(".")]
            for filename in filenames:
                seen_repo_refs.add(os.path.join(dirpath, filename))

    for filepath in candidates:
        if filepath in seen_paths:
            continue
        seen_paths.add(filepath)
        forward_refs = []
        try:
            size = os.path.getsize(filepath)
            if size > MAX_FILE_SIZE or size == 0:
                continue
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            for pattern in _match_patterns(filepath):
                matches = pattern.findall(content)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            match = next((m for m in match if m), "")
                        if match:
                            forward_refs.append(match.strip())
        except Exception:
            counts["unresolved"] += 1
            continue

        summary = score_file_refs(filepath, forward_refs, "")
        if summary["intentional"]:
            counts["intentional"] += 1
            upsert_orphan_record(filepath, "orphan_ref", "intentional", summary["reason"], intentional=True)
        elif summary["orphan_candidate"]:
            counts["orphan"] += 1
            upsert_orphan_record(filepath, "orphan_ref", "orphan_candidate", summary["reason"], intentional=False)
        elif summary.get("reverse_refs"):
            counts["nonrepo"] += 1
            upsert_orphan_record(filepath, "orphan_ref", "nonrepo", summary["reason"], intentional=False)

    record_repo_scan(repo_root, "completed", counts)
    return counts

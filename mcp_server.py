"""
ZQM Node-02 MCP Server
Wraps the file indexer functionality for use with Claude/Cline via MCP protocol.

Feature-complete parity with Node-01: filtered search, hybrid search,
and filter/cache telemetry tools. Compatible with mcp SDK >= 1.x
(call_tool handler receives (name, arguments)).
"""

import asyncio
import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add current directory to path for indexer import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indexer import (
    search_index,
    search_index_filtered,
    search_metadata,
    get_index_stats,
    get_metadata_stats,
    build_index,
    DEFAULT_SCAN_ROOTS,
)
import orphan_ref as _orphan_ref
# --- Filter cache (mirrors Node-01 telemetry) ---
_FILTER_CACHE_TTL_SECONDS = 30 * 60
_search_filter_cache: dict = {}
_filter_stats = {
    "hits": 0,
    "misses": 0,
    "evictions": 0,
}


def _normalize_filters(args: dict):
    parts = []
    for key in ("query", "field", "fields", "user", "path_prefix", "filetype", "modified_since"):
        parts.append((key, args.get(key)))
    min_size = args.get("min_size_mb")
    if min_size is not None:
        try:
            parts.append(("min_size_bytes", int(float(min_size) * 1024 * 1024)))
        except Exception:
            parts.append(("min_size_mb", min_size))
    limit = args.get("limit")
    parts.append(("limit", int(limit) if limit is not None else None))
    return tuple(parts)


def _bust_expired_cache_entries():
    now = time.time()
    expired = []
    for key, ts in _search_filter_cache.items():
        if now - ts > _FILTER_CACHE_TTL_SECONDS:
            expired.append(key)
    for key in expired:
        _search_filter_cache.pop(key, None)
        _filter_stats["evictions"] += 1


def cache_filtered_search(args: dict, results):
    try:
        _bust_expired_cache_entries()
    except Exception:
        pass
    key = hash(_normalize_filters(args))
    _search_filter_cache[key] = (time.time(), list(results))


def get_cached_filtered_search(args: dict):
    try:
        _bust_expired_cache_entries()
    except Exception:
        return None
    key = hash(_normalize_filters(args))
    entry = _search_filter_cache.get(key)
    if not entry:
        _filter_stats["misses"] += 1
        return None
    _filter_stats["hits"] += 1
    return list(entry[1])


def get_filter_cache_stats():
    return {
        "ttl_seconds": _FILTER_CACHE_TTL_SECONDS,
        "cached_keys": len(_search_filter_cache),
        "hits": _filter_stats["hits"],
        "misses": _filter_stats["misses"],
        "evictions": _filter_stats["evictions"],
    }


def clear_filter_cache():
    _search_filter_cache.clear()


# Try to import MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolResult,
        ListToolsResult,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not installed. Install with: pip install mcp")


class FileIndexerMCPServer:
    """MCP Server for ZQM Node-02 File Indexer."""

    def __init__(self):
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP SDK is required. Install with: pip install mcp")

        self.server = Server("zqm-node-02-indexer")
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="search_files",
                        description="Search for files across the entire workstation using full-text search. Returns matching files with paths, sizes, and relevance scores. Supports structured filters.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query (e.g., 'python', 'machine learning', 'config')"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return (default: 30)",
                                    "default": 30
                                },
                                "user": {
                                    "type": "string",
                                    "description": "Limit results to files under this local user profile directory name, e.g. zqmco"
                                },
                                "path_prefix": {
                                    "type": "string",
                                    "description": "Limit results to files whose path contains this prefix, e.g. C:/Users/zqmco/Documents"
                                },
                                "modified_since": {
                                    "type": "string",
                                    "description": "Limit results to files modified after this ISO datetime, e.g. 2026-07-01T00:00:00"
                                },
                                "filetype": {
                                    "type": "string",
                                    "description": "Optional file type filter, e.g. code, document, image, video, text, archive"
                                },
                                "min_size_mb": {
                                    "type": "number",
                                    "description": "Minimum file size in MB"
                                }
                            },
                            "required": ["query"]
                        }
                    ),
                    Tool(
                        name="hybrid_search_files",
                        description="Hybrid search using BM25 full-text search with a metadata exact-match fallback. Use when full-text search returns no results.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query (e.g., 'python', 'machine learning', 'config')"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return (default: 30)",
                                    "default": 30
                                }
                            },
                            "required": ["query"]
                        }
                    ),
                    Tool(
                        name="get_index_stats",
                        description="Get statistics about the file index including total files indexed, last update time, and scan coverage.",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="rebuild_index",
                        description="Rebuild the entire file index from scratch. This scans all configured directories and creates a fresh index. Use this if the index is out of date or corrupted.",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="find_files_by_type",
                        description="Find files by their type/category (e.g., 'code', 'document', 'image', 'video', 'text').",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "filetype": {
                                    "type": "string",
                                    "description": "File type to search for (e.g., 'code', 'document', 'image', 'video', 'text', 'archive')"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results (default: 50)",
                                    "default": 50
                                },
                                "user": {
                                    "type": "string",
                                    "description": "Limit results to files under this local user profile directory name"
                                },
                                "path_prefix": {
                                    "type": "string",
                                    "description": "Limit results to files whose path contains this prefix"
                                },
                                "modified_since": {
                                    "type": "string",
                                    "description": "Limit results to files modified after this ISO datetime"
                                }
                            },
                            "required": ["filetype"]
                        }
                    ),
                    Tool(
                        name="find_large_files",
                        description="Find the largest files on the workstation. Useful for identifying files taking up disk space.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "min_size_mb": {
                                    "type": "number",
                                    "description": "Minimum file size in MB (default: 100)",
                                    "default": 100
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results (default: 20)",
                                    "default": 20
                                },
                                "user": {
                                    "type": "string",
                                    "description": "Limit results to files under this local user profile directory name"
                                },
                                "path_prefix": {
                                    "type": "string",
                                    "description": "Limit results to files whose path contains this prefix"
                                }
                            }
                        }
                    ),
                    Tool(
                        name="find_recent_files",
                        description="Find recently modified files on the workstation.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results (default: 30)",
                                    "default": 30
                                },
                                "user": {
                                    "type": "string",
                                    "description": "Limit results to files under this local user profile directory name"
                                },
                                "path_prefix": {
                                    "type": "string",
                                    "description": "Limit results to files whose path contains this prefix"
                                }
                            }
                        }
                    ),
                    Tool(
                        name="list_filters",
                        description="List active search filter inputs and process-level cache hits/misses/evictions.",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="search_stats",
                        description="Get search/statistics related to the indexer pipeline, including index stats, metadata stats, and filter cache telemetry.",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                        }
                    ),
                    Tool(
                        name="get_orphan_candidates",
                        description="List prioritized orphan file candidates from indexed repo roots. Filters by intentional flag and optional repo_root.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "repo_root": {"type": "string", "description": "Optional repo root path to filter orphans"},
                                "include_intentional": {"type": "boolean", "description": "Include flagged intentional/archival orphans", "default": False},
                                "limit": {"type": "integer", "description": "Max rows to return", "default": 50}
                            }
                        }
                    ),
                    Tool(
                        name="mark_orphan_intentional",
                        description="Flip the intentional/archival flag on an orphan record to suppress remediation noise.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "description": "Absolute path to the orphaned file"},
                                "intentional": {"type": "boolean", "description": "True to mark as intentional/archival", "default": True}
                            },
                            "required": ["path"]
                        }
                    ),
                    Tool(
                        name="get_orphan_scan_runs",
                        description="Return recent orphan repo scan run summaries, including status and unresolved/intentional counts.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "limit": {"type": "integer", "description": "Rows to return", "default": 20}
                            }
                        }
                    ),
                ]
            )

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool calls. SDK >=1.x passes (name, arguments)."""
            arguments = arguments or {}

            try:
                if name == "search_files":
                    return await self._search_files(arguments)
                elif name == "hybrid_search_files":
                    return await self._hybrid_search_files(arguments)
                elif name == "get_index_stats":
                    return await self._get_index_stats()
                elif name == "rebuild_index":
                    return await self._rebuild_index()
                elif name == "find_files_by_type":
                    return await self._find_files_by_type(arguments)
                elif name == "find_large_files":
                    return await self._find_large_files(arguments)
                elif name == "find_recent_files":
                    return await self._find_recent_files(arguments)
                elif name == "list_filters":
                    return await self._list_filters(arguments)
                elif name == "search_stats":
                    return await self._search_stats(arguments)
                elif name == "get_orphan_candidates":
                    return await self._get_orphan_candidates(arguments)
                elif name == "mark_orphan_intentional":
                    return await self._mark_orphan_intentional(arguments)
                elif name == "get_orphan_scan_runs":
                    return await self._get_orphan_scan_runs(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"Unknown tool: {name}"
                        )]
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Error executing {name}: {str(e)}"
                    )]
                )

    async def _search_files(self, arguments):
        """Search files with advanced filters."""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 30)
        user = arguments.get("user")
        path_prefix = arguments.get("path_prefix")
        modified_since = arguments.get("modified_since")
        filetype = arguments.get("filetype")
        min_size_mb = arguments.get("min_size_mb")

        if not query:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: query parameter is required"
                )]
            )

        try:
            cached = get_cached_filtered_search(arguments)
            if cached is not None:
                results = cached
            else:
                results = search_index_filtered(
                    query,
                    limit=limit,
                    user=user,
                    path_prefix=path_prefix,
                    modified_since=modified_since,
                    filetype=filetype,
                    min_size_mb=min_size_mb,
                )
                cache_filtered_search(arguments, results)
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error executing search_files: {str(e)}"
                )]
            )

        if not results:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No files found matching: '{query}'"
                )]
            )

        output = [f"Found {len(results)} files matching '{query}':\n"]
        for i, r in enumerate(results, 1):
            size_str = f"{r['size'] / 1024:.1f} KB" if r['size'] < 1024*1024 else f"{r['size'] / (1024*1024):.1f} MB"
            output.append(f"{i}. {r['filename']}")
            output.append(f"   Path: {r['path']}")
            output.append(f"   Type: {r['filetype']} | Size: {size_str} | Score: {r['score']:.2f}")
            output.append("")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(output)
            )]
        )

    async def _hybrid_search_files(self, arguments):
        """Hybrid search using BM25 + metadata exact-match fallback."""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 30)

        if not query:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: query parameter is required"
                )]
            )

        try:
            results = search_index(query, limit=limit)
        except Exception:
            results = []

        if not results:
            results = search_metadata(query, limit=limit)
            if results:
                for r in results:
                    r.setdefault("source", "metadata")
        else:
            for r in results:
                r.setdefault("source", "index")

        if not results:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No files found matching: '{query}'"
                )]
            )

        output = [f"Found {len(results)} files matching '{query}':\n"]
        for i, r in enumerate(results, 1):
            size_str = f"{r['size'] / 1024:.1f} KB" if r['size'] < 1024*1024 else f"{r['size'] / (1024*1024):.1f} MB"
            output.append(f"{i}. {r['filename']}")
            output.append(f"   Path: {r['path']}")
            output.append(f"   Type: {r['filetype']} | Size: {size_str} | Score: {r['score']:.2f}")
            output.append("")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(output)
            )]
        )

    async def _get_index_stats(self):
        """Get index statistics."""
        stats = get_index_stats()

        if not stats:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No index found. Run rebuild_index first."
                )]
            )

        config = stats.get('config', {})
        output = [
            "Index Statistics:",
            f"  Total documents: {stats['document_count']}",
            f"  Last indexed: {config.get('last_indexed', 'Never')}",
            f"  Files found: {config.get('total_files', 'N/A')}",
            f"  Files indexed: {config.get('indexed_files', 'N/A')}",
            f"  Files skipped: {config.get('skipped_files', 'N/A')}",
            "",
            "Scan roots:"
        ]

        for root in config.get('root_paths', []):
            output.append(f"  - {root}")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(output)
            )]
        )

    async def _rebuild_index(self):
        """Rebuild the index."""
        try:
            build_index(rebuild=True)
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Index rebuilt successfully."
                )]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Rebuild failed: {str(e)}"
                )]
            )

    async def _find_files_by_type(self, arguments):
        """Find files by type."""
        filetype = arguments.get("filetype", "")
        limit = arguments.get("limit", 50)
        user = arguments.get("user")
        path_prefix = arguments.get("path_prefix")
        since = arguments.get("modified_since")

        if not filetype:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: filetype parameter is required"
                )]
            )

        try:
            results = search_index_filtered(
                filetype,
                limit=limit,
                field="filetype",
                user=user,
                path_prefix=path_prefix,
                modified_since=since,
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error executing find_files_by_type: {str(e)}")]
            )

        if not results:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No files found of type: '{filetype}'"
                )]
            )

        output = [f"Found {len(results)} {filetype} files:\n"]
        for i, r in enumerate(results, 1):
            size_str = f"{r['size'] / 1024:.1f} KB" if r['size'] < 1024*1024 else f"{r['size'] / (1024*1024):.1f} MB"
            output.append(f"{i}. {r['filename']}")
            output.append(f"   Path: {r['path']}")
            output.append(f"   Size: {size_str}")
            output.append("")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(output)
            )]
        )

    async def _find_large_files(self, arguments):
        """Find large files."""
        min_size_mb = arguments.get("min_size_mb", 100)
        limit = arguments.get("limit", 20)
        user = arguments.get("user")
        path_prefix = arguments.get("path_prefix")

        min_size_bytes = int(min_size_mb) * 1024 * 1024

        try:
            results = search_metadata("", limit=5000)
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error executing find_large_files: {str(e)}"
                )]
            )

        large_files = []
        for r in results:
            path = r.get("path") or ""
            low = path.lower()
            if user and user.lower() not in low:
                continue
            if path_prefix:
                pp = path_prefix.replace("\\", "/").lower()
                if not low.startswith(pp):
                    continue
            size = r.get("size") or 0
            if size >= min_size_bytes:
                large_files.append(r)

        large_files.sort(key=lambda x: x.get("size") or 0, reverse=True)
        large_files = large_files[: int(limit)]

        if not large_files:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No files found larger than {min_size_mb} MB"
                )]
            )

        output = [f"Found {len(large_files)} files larger than {min_size_mb} MB:\n"]
        for i, r in enumerate(large_files, 1):
            size_str = f"{r['size'] / (1024*1024):.1f} MB"
            output.append(f"{i}. {r['filename']}")
            output.append(f"   Path: {r['path']}")
            output.append(f"   Size: {size_str}")
            output.append("")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(output)
            )]
        )

    async def _find_recent_files(self, arguments):
        """Find recently modified files."""
        limit = arguments.get("limit", 30)
        user = arguments.get("user")
        path_prefix = arguments.get("path_prefix")

        try:
            results = search_metadata("", limit=5000)
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error executing find_recent_files: {str(e)}"
                )]
            )

        results_with_dates = []
        for r in results:
            path = r.get("path") or ""
            low = path.lower()
            if user and user.lower() not in low:
                continue
            if path_prefix:
                pp = path_prefix.replace("\\", "/").lower()
                if not low.startswith(pp):
                    continue
            raw = r.get("modified")
            if not raw:
                continue

            try:
                modified = datetime.fromisoformat(raw)
                results_with_dates.append((modified, r))
            except Exception:
                pass

        results_with_dates.sort(key=lambda x: x[0], reverse=True)
        recent_files = [r for _, r in results_with_dates[: int(limit)]]

        if not recent_files:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No recent files found"
                )]
            )

        output = [f"Found {len(recent_files)} recently modified files:\n"]
        for i, r in enumerate(recent_files, 1):
            size_str = f"{r['size'] / 1024:.1f} KB" if r['size'] < 1024*1024 else f"{r['size'] / (1024*1024):.1f} MB"
            output.append(f"{i}. {r['filename']}")
            output.append(f"   Path: {r['path']}")
            output.append(f"   Modified: {r['modified']}")
            output.append(f"   Size: {size_str}")
            output.append("")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(output)
            )]
        )

    async def _list_filters(self, arguments):
        stats = get_filter_cache_stats()
        output = [
            "Filter/cache telemetry:",
            f"  TTL seconds: {stats['ttl_seconds']}",
            f"  Cached keys: {stats['cached_keys']}",
            f"  Hits: {stats['hits']}",
            f"  Misses: {stats['misses']}",
            f"  Evictions: {stats['evictions']}",
        ]
        return CallToolResult(content=[TextContent(type="text", text="\n".join(output))])

    async def _search_stats(self, arguments):
        index_stats = get_index_stats() or {}
        config = index_stats.get("config") or {}
        metadata_stats = get_metadata_stats() or {}
        cache_stats = get_filter_cache_stats()
        output = [
            "Search pipeline stats:",
            f"  Index documents: {index_stats.get('document_count', 'N/A')}",
            f"  Last indexed: {config.get('last_indexed', 'Never')}",
            f"  Files indexed: {config.get('indexed_files', 'N/A')}",
            f"  Total files found: {config.get('total_files', 'N/A')}",
            f"  Metadata docs: {metadata_stats.get('metadata_document_count', 'N/A')}",
            f"  Filter cache TTL: {cache_stats['ttl_seconds']}s",
            f"  Filter cache keys: {cache_stats['cached_keys']}",
            f"  Filter cache hits: {cache_stats['hits']}",
            f"  Filter cache misses: {cache_stats['misses']}",
            f"  Filter cache evictions: {cache_stats['evictions']}",
        ]
        return CallToolResult(content=[TextContent(type="text", text="\n".join(output))])

    async def _get_orphan_candidates(self, arguments):
        repo_root = arguments.get("repo_root")
        include_intentional = bool(arguments.get("include_intentional", False))
        limit = int(arguments.get("limit", 50))
        try:
            results = _orphan_ref.get_prioritized_orphans(
                repo_root=repo_root,
                include_intentional=include_intentional,
                limit=limit,
            )
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Error querying orphans: {e}")])

        if not results:
            return CallToolResult(content=[TextContent(type="text", text="No orphan records found.")])

        lines = [f"Found {len(results)} orphan records:"]
        for i, row in enumerate(results, 1):
            label = "intentional" if row.get("intentional") else "unresolved"
            lines.append(f"{i}. [{label}] {row.get('path')}")
            lines.append(f"   repo={row.get('repo_root')} kind={row.get('kind')} reason={row.get('reason')} target={row.get('target_ref')}")
            lines.append("")
        return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])

    async def _mark_orphan_intentional(self, arguments):
        path = arguments.get("path")
        intentional = bool(arguments.get("intentional", True))
        if not path:
            return CallToolResult(content=[TextContent(type="text", text="Error: path is required")])
        try:
            _orphan_ref.update_orphan_intentional(path, intentional=intentional)
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Error updating orphan record: {e}")])
        return CallToolResult(content=[TextContent(type="text", text=f"Updated orphan flag for {path} -> intentional={intentional}")])

    async def _get_orphan_scan_runs(self, arguments):
        limit = int(arguments.get("limit", 20))
        try:
            conn = sqlite3.connect(_orphan_ref.metadata_db_path())
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT repo_root, scanned_at, status, intentional_count, unresolved_count, suppressed_count FROM repo_scan_runs ORDER BY scanned_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            conn.close()
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Error querying scan runs: {e}")])

        if not rows:
            return CallToolResult(content=[TextContent(type="text", text="No orphan scan runs recorded yet.")])

        lines = ["Recent orphan scan runs:"]
        for row in rows:
            lines.append(f"- {row['repo_root']}")
            lines.append(f"  scanned_at={row['scanned_at']} status={row['status']}")
            lines.append(f"  intentional={row['intentional_count']} unresolved={row['unresolved_count']} suppressed={row['suppressed_count']}")
        return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point."""
    if not MCP_AVAILABLE:
        print("Error: MCP SDK not installed.")
        print("Install with: pip install mcp")
        sys.exit(1)

    server = FileIndexerMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
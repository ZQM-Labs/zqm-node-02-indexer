"""
ZQM Node-02 MCP Server
Wraps the file indexer functionality for use with Claude/Cline via MCP protocol.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add current directory to path for indexer import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indexer import search_index, search_metadata, get_index_stats, get_metadata_stats, build_index, DEFAULT_SCAN_ROOTS

# Try to import MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        ListToolsResult,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not installed. Install with: pip install mcp")


class FileIndexerMCPServer:
    """MCP Server for ZQM Node-01 File Indexer."""
    
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
                        description="Search for files across the entire workstation using full-text search. Returns matching files with paths, sizes, and relevance scores.",
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
                                }
                            }
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls."""
            tool_name = request.params.name
            arguments = request.params.arguments or {}
            
            try:
                if tool_name == "search_files":
                    return await self._search_files(arguments)
                elif tool_name == "hybrid_search_files":
                    return await self._hybrid_search_files(arguments)
                elif tool_name == "get_index_stats":
                    return await self._get_index_stats()
                elif tool_name == "rebuild_index":
                    return await self._rebuild_index()
                elif tool_name == "find_files_by_type":
                    return await self._find_files_by_type(arguments)
                elif tool_name == "find_large_files":
                    return await self._find_large_files(arguments)
                elif tool_name == "find_recent_files":
                    return await self._find_recent_files(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"Unknown tool: {tool_name}"
                        )]
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Error executing {tool_name}: {str(e)}"
                    )]
                )
    
    async def _search_files(self, arguments):
        """Search for files."""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 30)
        
        if not query:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: query parameter is required"
                )]
            )
        
        results = search_index(query, limit=limit)
        
        if not results:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No files found matching: '{query}'"
                )]
            )
        
        # Format results
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
        
        if not filetype:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: filetype parameter is required"
                )]
            )
        
        # Search for the filetype
        results = search_index(filetype, limit=limit, field="filetype")
        
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
        min_size_bytes = min_size_mb * 1024 * 1024
        
        # Fetch enough results to cover large files safely
        results = search_index("*", limit=5000)
        large_files = [r for r in results if r.get('size') and r['size'] >= min_size_bytes]
        large_files.sort(key=lambda x: x.get('size', 0), reverse=True)
        large_files = large_files[:limit]
        
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
        
        # Fetch a larger pool and sort by modified date
        results = search_index("*", limit=5000)
        
        from datetime import datetime
        results_with_dates = []
        for r in results:
            raw = r.get('modified')
            if not raw:
                continue
            try:
                modified = datetime.fromisoformat(raw)
                results_with_dates.append((modified, r))
            except Exception:
                pass
        
        results_with_dates.sort(key=lambda x: x[0], reverse=True)
        recent_files = [r for _, r in results_with_dates[:limit]]
        
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
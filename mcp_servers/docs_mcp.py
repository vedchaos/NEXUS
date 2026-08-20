#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Documentation Server"""

import json
import sys
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS = [
    {"name": "ctz_docs_read", "description": "Read a markdown file from the project", "inputSchema": {"type": "object", "properties": {"file": {"type": "string"}, "max_lines": {"type": "integer", "default": 500}}, "required": ["file"]}},
    {"name": "ctz_docs_search", "description": "Search for content in markdown/docs files", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "directory": {"type": "string", "default": "."}, "file_pattern": {"type": "string", "default": "*.md"}}, "required": ["query"]}},
    {"name": "ctz_docs_list", "description": "List markdown/documentation files", "inputSchema": {"type": "object", "properties": {"directory": {"type": "string", "default": "."}, "recursive": {"type": "boolean", "default": True}}}},
]


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-docs", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_docs_read":
                fpath = PROJECT_ROOT / args["file"] if not os.path.isabs(args["file"]) else Path(args["file"])
                if not fpath.exists():
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": f"File not found: {fpath}"})}], "isError": True}}
                lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
                max_l = args.get("max_lines", 500)
                content = "\n".join(lines[:max_l])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"file": str(fpath.relative_to(PROJECT_ROOT)), "lines": len(lines), "truncated": len(lines) > max_l, "content": content})}]}}
            elif name == "ctz_docs_search":
                query = re.compile(args["query"], re.IGNORECASE)
                base = PROJECT_ROOT / args.get("directory", ".")
                pattern = args.get("file_pattern", "*.md")
                matches = []
                for f in base.rglob(pattern):
                    try:
                        text = f.read_text(encoding="utf-8", errors="replace")
                        for i, line in enumerate(text.splitlines(), 1):
                            if query.search(line):
                                matches.append({"file": str(f.relative_to(PROJECT_ROOT)), "line": i, "text": line.strip()[:200]})
                                if len(matches) >= 50:
                                    break
                    except:
                        pass
                    if len(matches) >= 50:
                        break
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"query": args["query"], "matches": matches, "count": len(matches)}, indent=2)}]}}
            elif name == "ctz_docs_list":
                base = PROJECT_ROOT / args.get("directory", ".")
                recursive = args.get("recursive", True)
                files = sorted(str(f.relative_to(PROJECT_ROOT)) for f in (base.rglob("*.md") if recursive else base.glob("*.md")))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"files": files, "count": len(files)})}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r:
                sys.stdout.write(json.dumps(r) + "\n")
                sys.stdout.flush()
        except:
            pass

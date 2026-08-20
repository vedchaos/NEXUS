#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — File Server (read/write/list/search)"""
import json, os, sys, glob as _glob
from pathlib import Path

TOOLS = [
    {"name": "ctz_file_read", "description": "Read a file's contents", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "encoding": {"type": "string", "default": "utf-8"}}, "required": ["path"]}},
    {"name": "ctz_file_write", "description": "Write content to a file", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "append": {"type": "boolean", "default": false}}, "required": ["path", "content"]}},
    {"name": "ctz_file_list", "description": "List files in a directory", "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "default": "."}, "pattern": {"type": "string", "default": "*"}, "recursive": {"type": "boolean", "default": false}}}},
    {"name": "ctz_file_search", "description": "Search for files by name pattern", "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "default": "."}, "pattern": {"type": "string"}, "max_results": {"type": "integer", "default": 50}}, "required": ["pattern"]}},
    {"name": "ctz_file_grep", "description": "Search file contents by regex pattern", "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "default": "."}, "pattern": {"type": "string"}, "include": {"type": "string", "default": "*"}, "max_results": {"type": "integer", "default": 50}}, "required": ["pattern"]}},
    {"name": "ctz_file_info", "description": "Get file info (size, modified, type)", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "ctz_file_copy", "description": "Copy a file", "inputSchema": {"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}},
    {"name": "ctz_file_delete", "description": "Delete a file", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
]

def handle_request(request):
    method, params, req_id = request.get("method"), request.get("params", {}), request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-file", "version": "1.0.0"}}}
    if method == "notifications/initialized": return None
    if method == "tools/list": return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments", {})
        try:
            if name == "ctz_file_read":
                content = Path(args["path"]).read_text(encoding=args.get("encoding", "utf-8"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": content[:50000]}]}}
            elif name == "ctz_file_write":
                p = Path(args["path"]); p.parent.mkdir(parents=True, exist_ok=True)
                if args.get("append"): p.open("a").write(args["content"])
                else: p.write_text(args["content"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "written", "path": str(p)})}]}}
            elif name == "ctz_file_list":
                p = Path(args.get("path", "."))
                if args.get("recursive"): items = [str(f.relative_to(p)) for f in p.rglob(args.get("pattern", "*")) if f.is_file()][:100]
                else: items = [f.name for f in p.iterdir() if f.is_file()][:100]
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(items)}]}}
            elif name == "ctz_file_search":
                matches = [str(f) for f in Path(args.get("path", ".")).rglob(args["pattern"])][:args.get("max_results", 50)]
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(matches)}]}}
            elif name == "ctz_file_grep":
                import re
                pattern = re.compile(args["pattern"])
                results = []
                include = args.get("include", "*")
                for f in Path(args.get("path", ".")).rglob(include):
                    if f.is_file() and f.stat().st_size < 1000000:
                        try:
                            for i, line in enumerate(f.read_text(errors="ignore").splitlines()):
                                if pattern.search(line):
                                    results.append({"file": str(f), "line": i + 1, "text": line[:200]})
                                    if len(results) >= args.get("max_results", 50): break
                        except: pass
                    if len(results) >= args.get("max_results", 50): break
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}}
            elif name == "ctz_file_info":
                p = Path(args["path"])
                s = p.stat()
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"path": str(p), "size": s.st_size, "modified": s.st_mtime, "is_file": p.is_file(), "is_dir": p.is_dir(), "extension": p.suffix})}]}}
            elif name == "ctz_file_copy":
                import shutil; shutil.copy2(args["src"], args["dst"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "copied"})}]}}
            elif name == "ctz_file_delete":
                os.remove(args["path"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "deleted"})}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r: sys.stdout.write(json.dumps(r) + "\n"); sys.stdout.flush()
        except: pass

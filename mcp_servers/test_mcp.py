#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Test Runner Server"""

import json
import sys
import subprocess
import py_compile
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS = [
    {"name": "ctz_test_run", "description": "Run a Python test file and return output", "inputSchema": {"type": "object", "properties": {"file": {"type": "string"}, "timeout": {"type": "integer", "default": 30}}, "required": ["file"]}},
    {"name": "ctz_test_list", "description": "List Python test files in a directory", "inputSchema": {"type": "object", "properties": {"directory": {"type": "string", "default": "."}}}},
    {"name": "ctz_test_compile", "description": "Check if a Python file compiles without errors", "inputSchema": {"type": "object", "properties": {"file": {"type": "string"}}, "required": ["file"]}},
]


def _find_test_files(directory):
    base = PROJECT_ROOT / directory if not os.path.isabs(directory) else Path(directory)
    if not base.exists():
        return {"error": f"Directory not found: {base}"}
    files = sorted(str(f.relative_to(PROJECT_ROOT)) for f in base.rglob("test_*.py")) + \
            sorted(str(f.relative_to(PROJECT_ROOT)) for f in base.rglob("*_test.py"))
    return {"files": files, "count": len(files)}


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-test", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_test_run":
                fpath = PROJECT_ROOT / args["file"] if not os.path.isabs(args["file"]) else Path(args["file"])
                if not fpath.exists():
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": f"File not found: {fpath}"})}], "isError": True}}
                proc = subprocess.run([sys.executable, str(fpath)], capture_output=True, text=True, timeout=args.get("timeout", 30), cwd=str(PROJECT_ROOT))
                result = {"returncode": proc.returncode, "stdout": proc.stdout[-3000:], "stderr": proc.stderr[-2000:]}
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
            elif name == "ctz_test_list":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(_find_test_files(args.get("directory", ".")), indent=2)}]}}
            elif name == "ctz_test_compile":
                fpath = PROJECT_ROOT / args["file"] if not os.path.isabs(args["file"]) else Path(args["file"])
                if not fpath.exists():
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": f"File not found: {fpath}"})}], "isError": True}}
                try:
                    py_compile.compile(str(fpath), doraise=True)
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"file": str(fpath), "compiles": True, "status": "OK"})}]}}
                except py_compile.PyCompileError as e:
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"file": str(fpath), "compiles": False, "error": str(e)})}], "isError": True}}
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

#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Live System Status Server"""

import json
import sys
import os
import time
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MCP_DIR = Path(__file__).parent
START_TIME = time.time()
TOOLS = [
    {"name": "ctz_status_uptime", "description": "Get system and server uptime", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ctz_status_ctz", "description": "Get CTZ project status", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ctz_status_mcp", "description": "List all MCP server statuses", "inputSchema": {"type": "object", "properties": {}}},
]


def _get_uptime():
    try:
        if platform.system() == "Windows":
            r = subprocess.run(["powershell", "-Command", "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime"], capture_output=True, text=True, timeout=10)
            return r.stdout.strip()
        else:
            with open("/proc/uptime") as f:
                secs = float(f.read().split()[0])
                return str(timedelta(seconds=int(secs)))
    except:
        return "unknown"


def _ctz_project_status():
    data_dir = PROJECT_ROOT / "data"
    return {
        "project_root": str(PROJECT_ROOT),
        "exists": PROJECT_ROOT.exists(),
        "has_bridge_core": (PROJECT_ROOT / "bridge_core").exists(),
        "has_mcp_servers": MCP_DIR.exists(),
        "mcp_count": len(list(MCP_DIR.glob("*_mcp.py"))) if MCP_DIR.exists() else 0,
        "data_dir_exists": data_dir.exists(),
        "platform": platform.system(),
        "python": sys.version.split()[0],
    }


def _mcp_server_statuses():
    servers = []
    for f in sorted(MCP_DIR.glob("*_mcp.py")):
        name = f.stem.replace("_mcp", "")
        try:
            with open(f, encoding="utf-8") as fh:
                content = fh.read()
            tool_count = content.count('"name": "ctz_')
            has_main = 'if __name__' in content
            servers.append({"name": name, "file": f.name, "tools": tool_count, "has_main": has_main, "status": "ok"})
        except Exception as e:
            servers.append({"name": name, "file": f.name, "status": "error", "error": str(e)})
    return servers


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-status", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_status_uptime":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"system_uptime": _get_uptime(), "server_uptime_seconds": round(time.time() - START_TIME, 1), "server_uptime": str(timedelta(seconds=int(time.time() - START_TIME))), "timestamp": datetime.now().isoformat()})}]}}
            elif name == "ctz_status_ctz":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(_ctz_project_status(), indent=2)}]}}
            elif name == "ctz_status_mcp":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(_mcp_server_statuses(), indent=2)}]}}
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

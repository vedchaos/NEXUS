#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Monitor Server (system monitoring)"""
import json, os, sys, platform, time
from pathlib import Path

CTZ_ROOT = Path(__file__).parent.parent

TOOLS = [
    {"name": "ctz_monitor_system", "description": "Get system info (CPU, RAM, disk, platform)", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ctz_monitor_processes", "description": "List top processes by memory/CPU", "inputSchema": {"type": "object", "properties": {"top": {"type": "integer", "default": 10}, "sort_by": {"type": "string", "enum": ["memory", "cpu"], "default": "memory"}}}},
    {"name": "ctz_monitor_disk", "description": "Get disk usage", "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "default": "."}}}},
    {"name": "ctz_monitor_network", "description": "Check network connectivity", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ctz_monitor_db_size", "description": "Check CTZ database sizes", "inputSchema": {"type": "object", "properties": {}}},
]

def handle_request(request):
    method, params, req_id = request.get("method"), request.get("params", {}), request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-monitor", "version": "1.0.0"}}}
    if method == "notifications/initialized": return None
    if method == "tools/list": return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments", {})
        try:
            if name == "ctz_monitor_system":
                info = {"platform": platform.system(), "platform_version": platform.version(), "architecture": platform.machine(), "hostname": platform.node(), "python": platform.python_version()}
                try:
                    import psutil
                    info["cpu_count"] = psutil.cpu_count()
                    info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
                    mem = psutil.virtual_memory()
                    info["ram_total_gb"] = round(mem.total / (1024**3), 1)
                    info["ram_used_gb"] = round(mem.used / (1024**3), 1)
                    info["ram_percent"] = mem.percent
                    disk = psutil.disk_usage("/")
                    info["disk_total_gb"] = round(disk.total / (1024**3), 1)
                    info["disk_used_gb"] = round(disk.used / (1024**3), 1)
                    info["disk_percent"] = round(disk.percent, 1)
                except ImportError:
                    info["note"] = "Install psutil for detailed stats: pip install psutil"
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(info, indent=2)}]}}
            elif name == "ctz_monitor_processes":
                try:
                    import psutil
                    procs = []
                    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
                        procs.append(p.info)
                    sort_key = "memory_percent" if args.get("sort_by", "memory") == "memory" else "cpu_percent"
                    procs.sort(key=lambda x: x.get(sort_key, 0) or 0, reverse=True)
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(procs[:args.get("top", 10)], indent=2)}]}}
                except ImportError:
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "psutil not installed"}], "isError": True}}
            elif name == "ctz_monitor_disk":
                import shutil
                usage = shutil.disk_usage(args.get("path", "."))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"total_gb": round(usage.total / (1024**3), 1), "used_gb": round(usage.used / (1024**3), 1), "free_gb": round(usage.free / (1024**3), 1)})}]}}
            elif name == "ctz_monitor_network":
                import urllib.request
                try:
                    urllib.request.urlopen("https://httpbin.org/get", timeout=5)
                    connected = True
                except:
                    connected = False
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"connected": connected})}]}}
            elif name == "ctz_monitor_db_size":
                dbs = []
                for sub in ["data/memory", "data/context", "data/cache", "data/automation", "data/vault"]:
                    d = CTZ_ROOT / sub
                    if d.exists():
                        for f in d.glob("*.db"):
                            dbs.append({"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)})
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(dbs, indent=2)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r: sys.stdout.write(json.dumps(r) + "\n"); sys.stdout.flush()
        except: pass

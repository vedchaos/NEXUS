#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Backup Server"""
import json, os, shutil, sys, time
from datetime import datetime
from pathlib import Path

CTZ_ROOT = Path(__file__).parent.parent
BACKUP_DIR = CTZ_ROOT / "data" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

TOOLS = [
    {"name": "ctz_backup_create", "description": "Create a backup of a directory", "inputSchema": {"type": "object", "properties": {"source": {"type": "string"}, "name": {"type": "string", "default": ""}, "exclude": {"type": "array", "items": {"type": "string"}, "default": ["__pycache__", ".git", "node_modules"]}}, "required": ["source"]}},
    {"name": "ctz_backup_list", "description": "List all backups", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ctz_backup_restore", "description": "Restore a backup", "inputSchema": {"type": "object", "properties": {"backup_name": {"type": "string"}, "destination": {"type": "string"}}, "required": ["backup_name", "destination"]}},
    {"name": "ctz_backup_delete", "description": "Delete a backup", "inputSchema": {"type": "object", "properties": {"backup_name": {"type": "string"}}, "required": ["backup_name"]}},
    {"name": "ctz_backup_db", "description": "Backup a specific SQLite database", "inputSchema": {"type": "object", "properties": {"db_path": {"type": "string"}}, "required": ["db_path"]}},
]

def handle_request(request):
    method, params, req_id = request.get("method"), request.get("params", {}), request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-backup", "version": "1.0.0"}}}
    if method == "notifications/initialized": return None
    if method == "tools/list": return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments", {})
        try:
            if name == "ctz_backup_create":
                src = Path(args["source"])
                bname = args.get("name") or f"backup_{src.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                dest = BACKUP_DIR / bname
                exclude = args.get("exclude", ["__pycache__", ".git", "node_modules"])
                def _ignore(d, files):
                    return [f for f in files if f in exclude or any(e in str(Path(d) / f) for e in exclude)]
                shutil.copytree(str(src), str(dest), ignore=_ignore, dirs_exist_ok=True)
                size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "created", "name": bname, "size_kb": round(size/1024, 1)})}]}}
            elif name == "ctz_backup_list":
                backups = []
                for d in sorted(BACKUP_DIR.iterdir(), reverse=True):
                    if d.is_dir():
                        size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
                        backups.append({"name": d.name, "size_kb": round(size/1024, 1), "created": datetime.fromtimestamp(d.stat().st_ctime).isoformat()})
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(backups, indent=2)}]}}
            elif name == "ctz_backup_restore":
                src = BACKUP_DIR / args["backup_name"]
                if not src.exists():
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Backup not found: {args['backup_name']}"}], "isError": True}}
                dest = Path(args["destination"])
                shutil.copytree(str(src), str(dest), dirs_exist_ok=True)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "restored", "destination": str(dest)})}]}}
            elif name == "ctz_backup_delete":
                p = BACKUP_DIR / args["backup_name"]
                if p.exists():
                    shutil.rmtree(str(p))
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "deleted"})}]}}
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "Not found"}], "isError": True}}
            elif name == "ctz_backup_db":
                import sqlite3
                src = Path(args["db_path"])
                if not src.exists():
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "DB not found"}], "isError": True}}
                bname = f"db_{src.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                dst = BACKUP_DIR / bname
                conn = sqlite3.connect(str(src))
                conn.execute(f"VACUUM INTO '{str(dst)}'")
                conn.close()
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "backed_up", "name": bname, "size_kb": round(dst.stat().st_size/1024, 1)})}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r: sys.stdout.write(json.dumps(r) + "\n"); sys.stdout.flush()
        except: pass

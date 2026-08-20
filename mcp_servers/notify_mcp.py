#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Notification Server"""

import json
import sys
import subprocess
import platform
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "data" / "notifications"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "notification_log.jsonl"

TOOLS = [
    {"name": "ctz_notify_desktop", "description": "Send a desktop notification", "inputSchema": {"type": "object", "properties": {"message": {"type": "string"}, "title": {"type": "string", "default": "CTZ Notification"}, "urgency": {"type": "string", "default": "normal", "enum": ["low", "normal", "critical"]}}, "required": ["message"]}},
    {"name": "ctz_notify_log", "description": "Log a notification to the history", "inputSchema": {"type": "object", "properties": {"message": {"type": "string"}, "level": {"type": "string", "default": "info"}}, "required": ["message"]}},
]


def _send_desktop(title, message, urgency):
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; $n=New-Object System.Windows.Forms.NotifyIcon; $n.Icon=[System.Drawing.SystemIcons]::Information; $n.Visible=$true; $n.ShowBalloonTip(5000,'{title}','{message}','Info')"], timeout=10, capture_output=True)
        elif system == "Darwin":
            subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'], timeout=10, capture_output=True)
        else:
            subprocess.run(["notify-send", "-u", urgency, title, message], timeout=10, capture_output=True)
        return True
    except Exception as e:
        return str(e)


def _log_notification(message, level="info"):
    entry = {"timestamp": datetime.now().isoformat(), "message": message, "level": level}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-notify", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_notify_desktop":
                result = _send_desktop(args.get("title", "CTZ Notification"), args["message"], args.get("urgency", "normal"))
                _log_notification(args["message"], args.get("urgency", "normal"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"sent": result is True, "detail": str(result) if result is not True else "ok"})}]}}
            elif name == "ctz_notify_log":
                entry = _log_notification(args["message"], args.get("level", "info"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(entry)}]}}
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

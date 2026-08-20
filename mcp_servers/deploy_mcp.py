#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Deployment Server"""

import json
import sys
import subprocess
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS = [
    {"name": "ctz_deploy_check", "description": "Check if project is deployable (requirements, structure)", "inputSchema": {"type": "object", "properties": {"directory": {"type": "string", "default": "."}}}},
    {"name": "ctz_deploy_git_status", "description": "Check git status for deployment readiness", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ctz_deploy_packages", "description": "List installed pip packages", "inputSchema": {"type": "object", "properties": {"filter": {"type": "string", "default": ""}}}},
]


def _run(cmd, cwd=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd or str(PROJECT_ROOT))
        return {"stdout": p.stdout.strip(), "stderr": p.stderr.strip(), "code": p.returncode}
    except Exception as e:
        return {"error": str(e)}


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-deploy", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_deploy_check":
                base = PROJECT_ROOT / args.get("directory", ".")
                checks = {
                    "has_requirements": (base / "requirements.txt").exists(),
                    "has_setup_py": (base / "setup.py").exists(),
                    "has_pyproject": (base / "pyproject.toml").exists(),
                    "has_main": any((base / m).exists() for m in ["main.py", "app.py", "manage.py", "__main__.py"]),
                    "has_docker": (base / "Dockerfile").exists(),
                    "has_gitignore": (base / ".gitignore").exists(),
                    "python_version": sys.version.split()[0],
                }
                checks["deployable"] = checks["has_requirements"] and (checks["has_main"] or checks["has_setup_py"] or checks["has_pyproject"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(checks, indent=2)}]}}
            elif name == "ctz_deploy_git_status":
                result = _run(["git", "status", "--porcelain"])
                branch = _run(["git", "branch", "--show-current"])
                ahead = _run(["git", "rev-list", "--count", f"origin/{branch.get('stdout', 'main')}..HEAD" if branch.get("stdout") else "HEAD"])
                changes = result.get("stdout", "").strip().split("\n") if result.get("stdout") else []
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"branch": branch.get("stdout", "unknown"), "uncommitted_changes": len([c for c in changes if c.strip()]), "clean": not result.get("stdout", "").strip(), "ahead_by": int(ahead.get("stdout", "0") or 0)}, indent=2)}]}}
            elif name == "ctz_deploy_packages":
                filt = args.get("filter", "")
                cmd = [sys.executable, "-m", "pip", "list", "--format=json"]
                result = _run(cmd)
                try:
                    pkgs = json.loads(result.get("stdout", "[]"))
                except:
                    pkgs = []
                if filt:
                    pkgs = [p for p in pkgs if filt.lower() in p.get("name", "").lower()]
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"packages": pkgs, "count": len(pkgs)}, indent=2)}]}}
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

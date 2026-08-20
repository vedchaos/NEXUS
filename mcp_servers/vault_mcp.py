#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Vault Server"""
import json, sys, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge_core.vault import get_vault

TOOLS = [
    {"name": "ctz_vault_set", "description": "Store a secret (API key, token, password) securely", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "value": {"type": "string"}, "category": {"type": "string", "default": "general"}, "description": {"type": "string", "default": ""}}, "required": ["name", "value"]}},
    {"name": "ctz_vault_get", "description": "Retrieve a secret by name", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "ctz_vault_delete", "description": "Delete a secret", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "ctz_vault_list", "description": "List all stored secrets (names only, not values)", "inputSchema": {"type": "object", "properties": {"category": {"type": "string"}}}},
    {"name": "ctz_vault_stats", "description": "Vault statistics", "inputSchema": {"type": "object", "properties": {}}},
]

def handle_request(request):
    method, params, req_id = request.get("method"), request.get("params", {}), request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-vault", "version": "1.0.0"}}}
    if method == "notifications/initialized": return None
    if method == "tools/list": return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments", {})
        vault = get_vault()
        try:
            if name == "ctz_vault_set": r = vault.set(args["name"], args["value"], args.get("category", "general"), args.get("description", ""))
            elif name == "ctz_vault_get": r = vault.get(args["name"])
            elif name == "ctz_vault_delete": r = vault.delete(args["name"])
            elif name == "ctz_vault_list": r = vault.list_all(args.get("category"))
            elif name == "ctz_vault_stats": r = vault.stats()
            else: return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown tool"}}
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r: sys.stdout.write(json.dumps(r) + "\n"); sys.stdout.flush()
        except: pass

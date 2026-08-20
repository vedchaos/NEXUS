#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — API Server (REST testing)"""
import json, sys
try:
    import requests
except ImportError:
    requests = None

TOOLS = [
    {"name": "ctz_api_get", "description": "GET request to an API endpoint", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}, "headers": {"type": "object", "default": {}}, "timeout": {"type": "integer", "default": 30}}, "required": ["url"]}},
    {"name": "ctz_api_post", "description": "POST request to an API endpoint", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}, "data": {"type": "object", "default": {}}, "headers": {"type": "object", "default": {}}, "json_body": {"type": "boolean", "default": true}}, "required": ["url"]}},
    {"name": "ctz_api_put", "description": "PUT request to an API endpoint", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}, "data": {"type": "object", "default": {}}, "headers": {"type": "object", "default": {}}, "json_body": {"type": "boolean", "default": true}}, "required": ["url"]}},
    {"name": "ctz_api_delete", "description": "DELETE request to an API endpoint", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}, "headers": {"type": "object", "default": {}}}, "required": ["url"]}},
    {"name": "ctz_api_test", "description": "Test an API endpoint (GET + measure response time)", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}, "expected_status": {"type": "integer", "default": 200}}, "required": ["url"]}},
]

def handle_request(request):
    method, params, req_id = request.get("method"), request.get("params", {}), request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-api", "version": "1.0.0"}}}
    if method == "notifications/initialized": return None
    if method == "tools/list": return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments", {})
        try:
            if not requests:
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "Error: requests not installed"}], "isError": True}}
            import time as _t
            h = args.get("headers", {})
            t0 = _t.time()
            if name == "ctz_api_get":
                r = requests.get(args["url"], headers=h, timeout=args.get("timeout", 30))
            elif name == "ctz_api_post":
                r = requests.post(args["url"], json=args.get("data") if args.get("json_body", True) else None, data=args.get("data") if not args.get("json_body", True) else None, headers=h, timeout=30)
            elif name == "ctz_api_put":
                r = requests.put(args["url"], json=args.get("data") if args.get("json_body", True) else None, headers=h, timeout=30)
            elif name == "ctz_api_delete":
                r = requests.delete(args["url"], headers=h, timeout=30)
            elif name == "ctz_api_test":
                r = requests.get(args["url"], timeout=30)
                elapsed = round(_t.time() - t0, 3)
                expected = args.get("expected_status", 200)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": r.status_code, "expected": expected, "pass": r.status_code == expected, "time_seconds": elapsed})}]}}
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown tool"}}
            elapsed = round(_t.time() - t0, 3)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": r.status_code, "time_seconds": elapsed, "body": r.text[:5000]})}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r: sys.stdout.write(json.dumps(r) + "\n"); sys.stdout.flush()
        except: pass

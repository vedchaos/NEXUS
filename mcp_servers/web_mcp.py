#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Web Server (fetch, search)"""
import json, sys
try:
    import requests
except ImportError:
    requests = None

TOOLS = [
    {"name": "ctz_web_fetch", "description": "Fetch a URL and return content (text/markdown)", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}, "format": {"type": "string", "enum": ["text", "html", "markdown"], "default": "text"}, "timeout": {"type": "integer", "default": 30}}, "required": ["url"]}},
    {"name": "ctz_web_search", "description": "Search the web using DuckDuckGo", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 5}}, "required": ["query"]}},
    {"name": "ctz_web_headers", "description": "Get HTTP headers from a URL", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
]

def handle_request(request):
    method, params, req_id = request.get("method"), request.get("params", {}), request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-web", "version": "1.0.0"}}}
    if method == "notifications/initialized": return None
    if method == "tools/list": return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments", {})
        try:
            if not requests:
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "Error: requests library not installed. pip install requests"}], "isError": True}}
            if name == "ctz_web_fetch":
                r = requests.get(args["url"], timeout=args.get("timeout", 30), headers={"User-Agent": "CTZ/1.0"})
                content = r.text[:10000] if args.get("format") != "html" else r.text[:20000]
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": r.status_code, "content": content, "length": len(r.text)})}]}}
            elif name == "ctz_web_search":
                r = requests.get(f"https://html.duckduckgo.com/html/", params={"q": args["query"]}, headers={"User-Agent": "CTZ/1.0"}, timeout=15)
                # Simple extraction
                import re
                results = re.findall(r'class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>', r.text)
                output = [{"url": url, "title": title.strip()} for url, title in results[:args.get("limit", 5)]]
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(output, indent=2)}]}}
            elif name == "ctz_web_headers":
                r = requests.head(args["url"], timeout=10, allow_redirects=True)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(dict(r.headers), indent=2)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r: sys.stdout.write(json.dumps(r) + "\n"); sys.stdout.flush()
        except: pass

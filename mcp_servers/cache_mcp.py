#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Cache Server"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge_core.cache import get_cache

TOOLS = [
    {"name": "ctz_cache_get", "description": "Get cached LLM response (returns None if miss)", "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "model": {"type": "string", "default": ""}, "provider": {"type": "string", "default": ""}}, "required": ["prompt"]}},
    {"name": "ctz_cache_set", "description": "Cache an LLM response", "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "response": {"type": "string"}, "model": {"type": "string", "default": ""}, "provider": {"type": "string", "default": ""}, "tokens_used": {"type": "integer", "default": 0}, "cost_saved": {"type": "number", "default": 0.0}, "ttl_hours": {"type": "integer", "default": 24}}, "required": ["prompt", "response"]}},
    {"name": "ctz_cache_stats", "description": "Get cache statistics", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ctz_cache_cleanup", "description": "Remove expired cache entries", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ctz_cache_clear", "description": "Clear all cache", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ctz_cache_search", "description": "Search cached responses by keyword", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}},
]


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-cache", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        cache = get_cache()
        try:
            if name == "ctz_cache_get":
                r = cache.get(args["prompt"], args.get("model", ""), args.get("provider", ""))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r)}]}}
            elif name == "ctz_cache_set":
                k = cache.set(args["prompt"], args["response"], args.get("model", ""), args.get("provider", ""), args.get("tokens_used", 0), args.get("cost_saved", 0.0), args.get("ttl_hours"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"key": k, "status": "cached"})}]}}
            elif name == "ctz_cache_stats":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(cache.stats(), indent=2)}]}}
            elif name == "ctz_cache_cleanup":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(cache.cleanup())}]}}
            elif name == "ctz_cache_clear":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(cache.clear())}]}}
            elif name == "ctz_cache_search":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(cache.search(args["query"], args.get("limit", 10)), indent=2)}]}}
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
        except: pass

#!/usr/bin/env python3
"""
NEXUS MCP — Memory Server
Exposes 3-tier memory as MCP tools
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "bridge_core"))
from memory_3tier import get_memory


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": "nexus-memory", "version": "1.0.0"},
        }}

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
            {
                "name": "memory_save",
                "description": "Save a memory to the 3-tier system (RAM + SQLite + ChromaDB)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "tags": {"type": "string"},
                        "type": {"type": "string", "enum": ["finding", "task", "decision", "note"]},
                        "importance": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "memory_search",
                "description": "Search all memory tiers semantically",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "memory_stats",
                "description": "Get memory system statistics",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "memory_compact",
                "description": "Auto-compact old memories to save space",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "older_than_days": {"type": "integer", "default": 90},
                    },
                },
            },
        ]}}

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        mem = get_memory()

        if tool_name == "memory_save":
            mem_id = mem.save(
                content=args["content"],
                tags=args.get("tags", ""),
                mem_type=args.get("type", "note"),
                importance=args.get("importance", 0.5),
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": f"Memory saved (ID: {mem_id})"}],
            }}

        elif tool_name == "memory_search":
            results = mem.search(args["query"], args.get("limit", 10))
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}],
            }}

        elif tool_name == "memory_stats":
            stats = mem.get_stats()
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps(stats, indent=2)}],
            }}

        elif tool_name == "memory_compact":
            result = mem.compact(args.get("older_than_days", 90))
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": f"Compacted: {result['deleted']} memories removed"}],
            }}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}))
            sys.stdout.flush()

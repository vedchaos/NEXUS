#!/usr/bin/env python3
"""
NEXUS MCP — LLM Fallback Server
Exposes Smart Brain as an MCP tool
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge_core.smart_brain import get_brain


def handle_request(request):
    """Handle MCP JSON-RPC request"""
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": "nexus-brain", "version": "1.0.0"},
        }}

    if method == "notifications/initialized":
        return None  # No response for notifications

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
            {
                "name": "nexus_query",
                "description": "Query LLM with auto provider selection, fallback, and caching",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "The prompt to send"},
                        "task_type": {"type": "string", "enum": ["code", "research", "vision", "pentest", "write", "speed", "quality", "cost", "local", "hinglish", "data", "agent", "ml"], "description": "Task type for routing"},
                        "system_prompt": {"type": "string", "description": "Optional system prompt to set context"},
                    },
                    "required": ["prompt"],
                },
            },
            {
                "name": "nexus_brain_stats",
                "description": "Get brain statistics (providers, cache, usage)",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]}}

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        brain = get_brain()

        if tool_name == "nexus_query":
            prompt = args.get("prompt", "")
            task_type = args.get("task_type", "agent")
            system_prompt = args.get("system_prompt")
            response, provider, model, cached = brain.query(prompt, task_type, system_prompt=system_prompt)
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": response}],
                "metadata": {"provider": provider, "model": model, "cached": cached},
            }}

        elif tool_name == "nexus_brain_stats":
            stats = brain.get_stats()
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps(stats, indent=2)}],
            }}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}


if __name__ == "__main__":
    # Read from stdin, write to stdout (MCP stdio transport)
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}))
            sys.stdout.flush()

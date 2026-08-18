#!/usr/bin/env python3
"""
NEXUS MCP — Task Router Server
Auto classifies and routes tasks to appropriate agents/tools
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge_core.task_classifier import classify_task, get_task_chain


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": "nexus-router", "version": "1.0.0"},
        }}

    if method == "notifications/initialized":
        return None  # No response for notifications

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
            {
                "name": "classify_task",
                "description": "Classify a user request into a task type (code, research, pentest, etc.)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "User request to classify"},
                    },
                    "required": ["input"],
                },
            },
            {
                "name": "get_routing",
                "description": "Get recommended provider chain for a task type",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_type": {"type": "string"},
                    },
                    "required": ["task_type"],
                },
            },
            {
                "name": "list_task_types",
                "description": "List all supported task types",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]}}

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "classify_task":
            task_type, confidence = classify_task(args["input"])
            chain = get_task_chain(task_type)
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps({
                    "task_type": task_type,
                    "confidence": confidence,
                    "recommended_providers": chain.get("preferred", []),
                    "fallback_providers": chain.get("fallback", []),
                }, indent=2)}],
            }}

        elif tool_name == "get_routing":
            chain = get_task_chain(args["task_type"])
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps(chain, indent=2)}],
            }}

        elif tool_name == "list_task_types":
            from bridge_core.task_classifier import TASK_TYPES
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps(list(TASK_TYPES.keys()), indent=2)}],
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

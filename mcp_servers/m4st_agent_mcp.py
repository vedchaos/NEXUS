#!/usr/bin/env python3
"""
NEXUS MCP — Agent Orchestrator Server
6-agent OMO Sisyphus loop
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "bridge_core"))
from agents import get_orchestrator


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": "nexus-orchestrator", "version": "1.0.0"},
        }}

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
            {
                "name": "run_sisyphus",
                "description": "Run the full 6-agent Sisyphus loop on a user request",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "request": {"type": "string", "description": "User request to process"},
                        "context": {"type": "object", "description": "Additional context"},
                        "adaptive": {"type": "boolean", "default": True, "description": "Skip critique for simple tasks"},
                    },
                    "required": ["request"],
                },
            },
            {
                "name": "plan_only",
                "description": "Create an execution plan without running it",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "request": {"type": "string"},
                    },
                    "required": ["request"],
                },
            },
            {
                "name": "memory_save",
                "description": "Save to long-term memory via Memory Agent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "importance": {"type": "number"},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "memory_recall",
                "description": "Search memory via Memory Agent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["query"],
                },
            },
        ]}}

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        orch = get_orchestrator()

        try:
            if tool_name == "run_sisyphus":
                result = orch.run(args["request"], args.get("context"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}],
                }}

            elif tool_name == "plan_only":
                plan = orch.planner.plan(args["request"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {
                    "content": [{"type": "text", "text": json.dumps(plan, indent=2)}],
                }}

            elif tool_name == "memory_save":
                result = orch.memory_agent.remember(
                    args["content"],
                    importance=args.get("importance", 0.7),
                )
                return {"jsonrpc": "2.0", "id": req_id, "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                }}

            elif tool_name == "memory_recall":
                result = orch.memory_agent.recall(args["query"], args.get("limit", 10))
                return {"jsonrpc": "2.0", "id": req_id, "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}],
                }}

        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": f"[ERROR] {str(e)}"}],
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

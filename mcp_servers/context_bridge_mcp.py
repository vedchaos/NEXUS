#!/usr/bin/env python3
"""
CHAOS TYPE ZERO MCP - Context Bridge Server
Cross-session memory persistence via MCP tools.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge_core.context_bridge import get_bridge


TOOLS = [
    {
        "name": "ctz_session_start",
        "description": "Start a new session for cross-session context tracking",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "model": {"type": "string"},
            },
        },
    },
    {
        "name": "ctz_session_end",
        "description": "End a session and save its summary",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "summary": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "ctz_session_list",
        "description": "List recent sessions with metadata",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "ctz_context_save",
        "description": "Save a context entry: decision, fact, task_outcome, preference, note, error, insight",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "entry_type": {"type": "string", "enum": ["decision", "fact", "task_outcome", "preference", "note", "error", "insight"]},
                "content": {"type": "string"},
                "importance": {"type": "number", "default": 0.5},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["session_id", "entry_type", "content"],
        },
    },
    {
        "name": "ctz_context_search",
        "description": "Semantic search across all session context entries",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
                "entry_type": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "ctz_fact_save",
        "description": "Save a key fact that persists across all sessions forever",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fact": {"type": "string"},
                "category": {"type": "string", "default": "general"},
                "confidence": {"type": "number", "default": 0.8},
            },
            "required": ["fact"],
        },
    },
    {
        "name": "ctz_fact_search",
        "description": "Search key facts semantically",
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
        "name": "ctz_fact_list",
        "description": "List all key facts, optionally filtered by category",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "limit": {"type": "integer", "default": 50},
            },
        },
    },
    {
        "name": "ctz_restore_context",
        "description": "Restore context for a new session - finds everything relevant from past sessions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_tokens": {"type": "integer", "default": 2000},
            },
            "required": ["query"],
        },
    },
    {
        "name": "ctz_session_link",
        "description": "Create a link between two related sessions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_session": {"type": "string"},
                "to_session": {"type": "string"},
                "link_type": {"type": "string", "default": "related"},
                "reason": {"type": "string"},
            },
            "required": ["from_session", "to_session"],
        },
    },
    {
        "name": "ctz_compact",
        "description": "Auto-compact old context entries and deactivate unused facts",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days_old": {"type": "integer", "default": 90},
                "min_importance": {"type": "number", "default": 0.3},
            },
        },
    },
    {
        "name": "ctz_bridge_stats",
        "description": "Get context bridge statistics",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": "ctz-context-bridge", "version": "1.0.0"},
        }}

    if method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        bridge = get_bridge()
        result = _dispatch(bridge, tool_name, args)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def _text(content):
    return {"content": [{"type": "text", "text": content}]}


def _error_text(msg):
    return {"content": [{"type": "text", "text": f"Error: {msg}"}], "isError": True}


def _dispatch(bridge, tool_name, args):
    try:
        if tool_name == "ctz_session_start":
            sid = bridge.start_session(
                title=args.get("title", ""),
                tags=args.get("tags", []),
                model=args.get("model", ""),
            )
            return _text(json.dumps({"session_id": sid, "status": "started"}))

        elif tool_name == "ctz_session_end":
            bridge.end_session(
                session_id=args["session_id"],
                summary=args.get("summary", ""),
                tags=args.get("tags", []),
            )
            return _text(json.dumps({"status": "ended", "session_id": args["session_id"]}))

        elif tool_name == "ctz_session_list":
            sessions = bridge.list_sessions(
                limit=args.get("limit", 10),
                tags=args.get("tags"),
            )
            out = []
            for s in sessions:
                out.append({
                    "id": s[0], "title": s[1], "started": s[2],
                    "ended": s[3], "tags": s[4], "summary": s[5],
                    "messages": s[7], "is_active": bool(s[10]),
                })
            return _text(json.dumps(out, indent=2))

        elif tool_name == "ctz_context_save":
            eid = bridge.save_context(
                session_id=args["session_id"],
                entry_type=args["entry_type"],
                content=args["content"],
                importance=args.get("importance", 0.5),
                tags=args.get("tags", []),
            )
            return _text(json.dumps({"entry_id": eid, "status": "saved"}))

        elif tool_name == "ctz_context_search":
            results = bridge.search_context(
                query=args["query"],
                limit=args.get("limit", 10),
                entry_type=args.get("entry_type"),
            )
            return _text(json.dumps(results, indent=2, default=str))

        elif tool_name == "ctz_fact_save":
            fid = bridge.save_fact(
                fact=args["fact"],
                category=args.get("category", "general"),
                confidence=args.get("confidence", 0.8),
            )
            return _text(json.dumps({"fact_id": fid, "status": "saved"}))

        elif tool_name == "ctz_fact_search":
            results = bridge.search_facts(
                query=args["query"],
                limit=args.get("limit", 10),
            )
            return _text(json.dumps(results, indent=2, default=str))

        elif tool_name == "ctz_fact_list":
            facts = bridge.get_facts(
                category=args.get("category"),
                limit=args.get("limit", 50),
            )
            out = []
            for f in facts:
                out.append({
                    "id": f[0], "fact": f[1], "category": f[2],
                    "source_session": f[3], "confidence": f[4],
                    "times_recalled": f[5], "is_active": bool(f[8]),
                })
            return _text(json.dumps(out, indent=2))

        elif tool_name == "ctz_restore_context":
            result = bridge.restore_context(
                query=args["query"],
                max_tokens=args.get("max_tokens", 2000),
            )
            return _text(json.dumps(result, indent=2))

        elif tool_name == "ctz_session_link":
            bridge.link_sessions(
                from_session=args["from_session"],
                to_session=args["to_session"],
                link_type=args.get("link_type", "related"),
                reason=args.get("reason", ""),
            )
            return _text(json.dumps({"status": "linked"}))

        elif tool_name == "ctz_compact":
            result = bridge.compact(
                days_old=args.get("days_old", 90),
                min_importance=args.get("min_importance", 0.3),
            )
            return _text(json.dumps(result))

        elif tool_name == "ctz_bridge_stats":
            return _text(json.dumps(bridge.stats(), indent=2))

        else:
            return _error_text(f"Unknown tool: {tool_name}")

    except Exception as e:
        return _error_text(str(e))


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

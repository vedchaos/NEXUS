#!/usr/bin/env python3
"""
NEXUS MCP — Agent Orchestrator Server
6-agent OMO Sisyphus loop with adaptive critique
Tools: nexus_run, nexus_plan, nexus_execute, nexus_critique,
       nexus_remember, nexus_recall, nexus_summarize, nexus_status
"""

import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge_core.agents import get_orchestrator

# === MCP Protocol ===
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "nexus-orchestrator"
SERVER_VERSION = "1.0.0"

# === Tool Definitions ===
TOOLS = [
    {
        "name": "nexus_run",
        "description": (
            "Run the full NEXUS 6-agent Sisyphus loop: "
            "Plan → Execute → Critique → Refine → Memory → Report. "
            "Use for complex multi-step tasks that need planning and quality review."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": "User request to process through the full Sisyphus loop",
                },
                "context": {
                    "type": "object",
                    "description": "Additional context: files, env vars, prior results",
                },
                "adaptive": {
                    "type": "boolean",
                    "default": True,
                    "description": "Skip critique for low-risk simple tasks (saves time)",
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 3,
                    "description": "Max critique→refine loops before accepting result",
                },
            },
            "required": ["request"],
        },
    },
    {
        "name": "nexus_plan",
        "description": (
            "Create a step-by-step execution plan without running it. "
            "Returns steps, estimated time, risk level, and whether authorization is needed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": "What you want to accomplish",
                },
                "context": {
                    "type": "object",
                    "description": "Additional context for better planning",
                },
            },
            "required": ["request"],
        },
    },
    {
        "name": "nexus_execute",
        "description": (
            "Execute a single planned step. Returns execution status and output. "
            "Use after nexus_plan to run individual steps."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "step": {
                    "type": "object",
                    "description": "Step object from nexus_plan: {id, action, tool, args}",
                },
                "context": {
                    "type": "object",
                    "description": "Execution context (env vars, file paths, etc.)",
                },
            },
            "required": ["step"],
        },
    },
    {
        "name": "nexus_critique",
        "description": (
            "Review any work output for quality, accuracy, security issues. "
            "Returns score (1-10), issues, strengths, and pass/fail."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "work": {
                    "description": "The work to review (string or object)",
                },
                "criteria": {
                    "type": "string",
                    "description": "Review criteria: quality, accuracy, completeness, security (comma-separated)",
                    "default": "quality, accuracy, completeness, security",
                },
            },
            "required": ["work"],
        },
    },
    {
        "name": "nexus_remember",
        "description": (
            "Save information to NEXUS long-term memory (3-tier: RAM→SQLite→ChromaDB). "
            "Auto-promotes based on access frequency and importance."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "What to remember",
                },
                "tags": {
                    "type": "string",
                    "description": "Comma-separated tags for categorization",
                    "default": "",
                },
                "importance": {
                    "type": "number",
                    "description": "Importance score 0.0-1.0",
                    "default": 0.7,
                },
                "mem_type": {
                    "type": "string",
                    "description": "Memory type: note, task, finding, decision, error",
                    "default": "note",
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "nexus_recall",
        "description": (
            "Search NEXUS long-term memory using semantic search. "
            "Returns ranked results from RAM cache, SQLite, and ChromaDB."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in memory",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return",
                    "default": 10,
                },
                "mem_type": {
                    "type": "string",
                    "description": "Filter by type: note, task, finding, decision, error",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "nexus_summarize",
        "description": (
            "Summarize a conversation or session for long-term memory storage. "
            "Extracts decisions, findings, completed tasks, and pending items."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversation": {
                    "type": "array",
                    "description": "Array of {role, content} message objects",
                    "items": {"type": "object"},
                },
            },
            "required": ["conversation"],
        },
    },
    {
        "name": "nexus_status",
        "description": (
            "Get NEXUS orchestrator status: agents available, memory stats, "
            "last task, uptime, provider health."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


# === Request Handler ===
def handle_request(request):
    """Handle MCP JSON-RPC request"""
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")

    # --- Initialize ---
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }

    # --- Initialized notification ---
    if method == "notifications/initialized":
        return None  # No response for notifications

    # --- List Tools ---
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    # --- Call Tool ---
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        return handle_tool_call(tool_name, args, req_id)

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def handle_tool_call(tool_name, args, req_id):
    """Dispatch tool calls to orchestrator"""
    try:
        orch = get_orchestrator()
        result = None

        # --- nexus_run ---
        if tool_name == "nexus_run":
            if "max_iterations" in args:
                orch.max_iterations = args["max_iterations"]
            if "adaptive" in args:
                orch.adaptive = args["adaptive"]
            result = orch.run(args["request"], args.get("context"))
            return format_result(req_id, result)

        # --- nexus_plan ---
        elif tool_name == "nexus_plan":
            plan = orch.planner.plan(args["request"], args.get("context"))
            return format_result(req_id, {
                "plan": plan,
                "message": "Plan created. Use nexus_execute to run steps.",
            })

        # --- nexus_execute ---
        elif tool_name == "nexus_execute":
            step = args["step"]
            result = orch.executor.execute(step, args.get("context"))
            return format_result(req_id, result)

        # --- nexus_critique ---
        elif tool_name == "nexus_critique":
            criteria = args.get("criteria", "quality, accuracy, completeness, security")
            result = orch.critic.review(args["work"], criteria)
            return format_result(req_id, result)

        # --- nexus_remember ---
        elif tool_name == "nexus_remember":
            result = orch.memory_agent.remember(
                content=args["content"],
                tags=args.get("tags", ""),
                importance=args.get("importance", 0.7),
                mem_type=args.get("mem_type", "note"),
            )
            return format_result(req_id, result)

        # --- nexus_recall ---
        elif tool_name == "nexus_recall":
            results = orch.memory_agent.recall(
                query=args["query"],
                limit=args.get("limit", 10),
            )
            return format_result(req_id, results)

        # --- nexus_summarize ---
        elif tool_name == "nexus_summarize":
            summary = orch.memory_agent.summarize_session(args["conversation"])
            # Also save the summary to memory
            orch.memory_agent.remember(
                content=json.dumps(summary),
                tags="session_summary",
                importance=summary.get("importance", 0.7),
                mem_type="task",
            )
            return format_result(req_id, summary)

        # --- nexus_status ---
        elif tool_name == "nexus_status":
            status = {
                "server": SERVER_NAME,
                "version": SERVER_VERSION,
                "uptime_seconds": round(time.time() - _start_time, 2),
                "agents": [
                    "Planner", "Coder", "Researcher",
                    "Critic", "Executor", "Memory",
                ],
                "adaptive": orch.adaptive,
                "max_iterations": orch.max_iterations,
                "memory_stats": get_memory_stats(orch),
                "timestamp": datetime.now().isoformat(),
            }
            return format_result(req_id, status)

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"},
            }

    except Exception as e:
        tb = traceback.format_exc()
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": f"[NEXUS ERROR] {e}\n\n{tb}"}],
                "isError": True,
            },
        }


def format_result(req_id, data):
    """Format a successful result"""
    text = json.dumps(data, indent=2, default=str) if isinstance(data, (dict, list)) else str(data)
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {"content": [{"type": "text", "text": text}]},
    }


def get_memory_stats(orch):
    """Get memory system stats — delegates to ChaosMemory.get_stats()"""
    try:
        mem = orch.memory_agent.memory
        return mem.get_stats()
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


# === Server Entry ===
_start_time = time.time()


def main():
    """Run MCP server over stdio"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                print(json.dumps(response))
                sys.stdout.flush()
        except json.JSONDecodeError as e:
            err = {"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {e}"}}
            print(json.dumps(err))
            sys.stdout.flush()
        except Exception as e:
            err = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
            print(json.dumps(err))
            sys.stdout.flush()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
NEXUS MCP — Vision Server
Tools: vision_screenshot, vision_ocr, vision_analyze, vision_find_text, vision_status
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge_core.vision import get_vision

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "nexus-vision"
SERVER_VERSION = "1.0.0"

TOOLS = [
    {
        "name": "vision_screenshot",
        "description": "Take a screenshot of the screen",
        "inputSchema": {
            "type": "object",
            "properties": {
                "region": {"type": "array", "items": {"type": "integer"}, "description": "Optional region [x,y,w,h]"},
            },
        },
    },
    {
        "name": "vision_ocr",
        "description": "Read text from an image file using OCR",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to image file"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "vision_read_screen",
        "description": "Take screenshot and read all text from it",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vision_analyze",
        "description": "Analyze an image (colors, size, metadata)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to image file"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "vision_find_text",
        "description": "Take screenshot and search for specific text on screen",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to find on screen"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "vision_status",
        "description": "Get vision module status",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }}

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        vision = get_vision()

        if tool_name == "vision_screenshot":
            region = tuple(args["region"]) if "region" in args else None
            result = vision.take_screenshot(region=region)
        elif tool_name == "vision_ocr":
            result = vision.read_image(args["path"])
        elif tool_name == "vision_read_screen":
            result = vision.read_screenshot()
        elif tool_name == "vision_analyze":
            result = vision.analyze_image(args["path"])
        elif tool_name == "vision_find_text":
            result = vision.find_text_on_screen(args["text"])
        elif tool_name == "vision_status":
            result = vision.get_status()
        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}

        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
        }}

    elif method == "notifications/initialized":
        return None

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}), flush=True)

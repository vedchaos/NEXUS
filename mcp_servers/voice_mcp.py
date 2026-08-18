#!/usr/bin/env python3
"""
CHAOS TYPE ZERO MCP — Voice Server
Tools: voice_speak, voice_listen, voice_transcribe, voice_save, voice_status
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge_core.voice import get_voice

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ctz-voice"
SERVER_VERSION = "1.0.0"

TOOLS = [
    {
        "name": "voice_speak",
        "description": "Speak text aloud using TTS",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "rate": {"type": "integer", "description": "Speech rate (default 175)"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "voice_listen",
        "description": "Record from microphone and transcribe (STT)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "duration": {"type": "integer", "description": "Recording duration in seconds (default 5)"},
            },
        },
    },
    {
        "name": "voice_transcribe",
        "description": "Transcribe an audio file to text",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to audio file"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "voice_save",
        "description": "Save text to audio file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to convert to speech"},
                "output_path": {"type": "string", "description": "Output file path"},
            },
            "required": ["text", "output_path"],
        },
    },
    {
        "name": "voice_status",
        "description": "Get voice module status",
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
        voice = get_voice()

        if tool_name == "voice_speak":
            result = voice.speak(args["text"], rate=args.get("rate", 175))
        elif tool_name == "voice_listen":
            result = voice.listen(duration=args.get("duration", 5))
        elif tool_name == "voice_transcribe":
            result = voice.transcribe_file(args["path"])
        elif tool_name == "voice_save":
            result = voice.save_to_file(args["text"], args["output_path"])
        elif tool_name == "voice_status":
            result = voice.get_status()
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

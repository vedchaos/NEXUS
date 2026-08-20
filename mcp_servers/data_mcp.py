#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Data Analysis Server"""

import json
import sys
import csv
import os
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS = [
    {"name": "ctz_data_csv_read", "description": "Read a CSV file and return rows", "inputSchema": {"type": "object", "properties": {"file": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": ["file"]}},
    {"name": "ctz_data_csv_analyze", "description": "Analyze a CSV file (rows, columns, stats)", "inputSchema": {"type": "object", "properties": {"file": {"type": "string"}}, "required": ["file"]}},
    {"name": "ctz_data_json_read", "description": "Read a JSON file", "inputSchema": {"type": "object", "properties": {"file": {"type": "string"}, "max_depth": {"type": "integer", "default": 3}}, "required": ["file"]}},
    {"name": "ctz_data_json_analyze", "description": "Analyze JSON file structure", "inputSchema": {"type": "object", "properties": {"file": {"type": "string"}}, "required": ["file"]}},
]


def _resolve(file):
    p = PROJECT_ROOT / file if not os.path.isabs(file) else Path(file)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return p


def _analyze_structure(data, depth=0, max_depth=3):
    if depth >= max_depth:
        return type(data).__name__
    if isinstance(data, dict):
        return {k: _analyze_structure(v, depth + 1, max_depth) for k, v in list(data.items())[:20]}
    if isinstance(data, list):
        if not data:
            return "empty_list"
        return {"_array_of": _analyze_structure(data[0], depth + 1, max_depth), "_length": len(data)}
    return type(data).__name__


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-data", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_data_csv_read":
                p = _resolve(args["file"])
                limit = args.get("limit", 100)
                with open(p, encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    rows = [r for i, r in enumerate(reader) if i < limit]
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"file": str(p.relative_to(PROJECT_ROOT)), "rows": rows, "count": len(rows)}, indent=2)}]}}
            elif name == "ctz_data_csv_analyze":
                p = _resolve(args["file"])
                with open(p, encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames or []
                    rows = list(reader)
                stats = {}
                for h in headers:
                    vals = [r.get(h, "") for r in rows]
                    numeric = []
                    for v in vals:
                        try:
                            numeric.append(float(v))
                        except:
                            pass
                    col_stat = {"count": len(vals), "non_empty": sum(1 for v in vals if v), "unique": len(set(vals))}
                    if numeric:
                        col_stat["type"] = "numeric"
                        col_stat["min"] = min(numeric)
                        col_stat["max"] = max(numeric)
                        col_stat["mean"] = round(sum(numeric) / len(numeric), 4)
                    else:
                        col_stat["type"] = "text"
                        col_stat["top_values"] = dict(Counter(vals).most_common(5))
                    stats[h] = col_stat
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"file": str(p.relative_to(PROJECT_ROOT)), "total_rows": len(rows), "columns": headers, "column_stats": stats}, indent=2)}]}}
            elif name == "ctz_data_json_read":
                p = _resolve(args["file"])
                with open(p, encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                text = json.dumps(data, indent=2)
                if len(text) > 5000:
                    text = text[:5000] + "\n... (truncated)"
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"file": str(p.relative_to(PROJECT_ROOT)), "content": text})}]}}
            elif name == "ctz_data_json_analyze":
                p = _resolve(args["file"])
                with open(p, encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                structure = _analyze_structure(data)
                size = p.stat().st_size
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"file": str(p.relative_to(PROJECT_ROOT)), "size_bytes": size, "root_type": type(data).__name__, "structure": structure}, indent=2)}]}}
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
        except:
            pass

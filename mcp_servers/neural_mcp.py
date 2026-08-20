#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Neural Network Server"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge_core.neural import get_neural

TOOLS = [
    {"name": "ctz_neural_classify", "description": "Classify text by sentiment, topic, and intent", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "ctz_neural_summarize", "description": "Extractive summarization of text", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}, "max_sentences": {"type": "integer", "default": 3}}, "required": ["text"]}},
    {"name": "ctz_neural_embed", "description": "Generate TF-IDF text embedding vector", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}, "corpus": {"type": "array", "items": {"type": "string"}, "default": []}}, "required": ["text"]}},
    {"name": "ctz_neural_similarity", "description": "Score similarity between two texts (0-1)", "inputSchema": {"type": "object", "properties": {"text1": {"type": "string"}, "text2": {"type": "string"}}, "required": ["text1", "text2"]}},
    {"name": "ctz_neural_patterns", "description": "Detect patterns in a batch of texts", "inputSchema": {"type": "object", "properties": {"texts": {"type": "array", "items": {"type": "string"}}}, "required": ["texts"]}},
    {"name": "ctz_neural_categorize", "description": "Categorize multiple texts by topic", "inputSchema": {"type": "object", "properties": {"texts": {"type": "array", "items": {"type": "string"}}}, "required": ["texts"]}},
]


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-neural", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        neural = get_neural()
        try:
            if name == "ctz_neural_classify":
                r = neural.classify(args["text"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2)}]}}
            elif name == "ctz_neural_summarize":
                r = neural.summarize(args["text"], args.get("max_sentences", 3))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"summary": r})}]}}
            elif name == "ctz_neural_embed":
                corpus = args.get("corpus", [])
                if corpus:
                    r = neural.embed_with_corpus(args["text"], corpus)
                else:
                    r = neural.embed(args["text"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"embedding": r, "dimensions": len(r)})}]}}
            elif name == "ctz_neural_similarity":
                r = neural.similarity(args["text1"], args["text2"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"similarity": r})}]}}
            elif name == "ctz_neural_patterns":
                r = neural.detect_patterns(args["texts"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2)}]}}
            elif name == "ctz_neural_categorize":
                r = neural.categorize_batch(args["texts"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2)}]}}
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

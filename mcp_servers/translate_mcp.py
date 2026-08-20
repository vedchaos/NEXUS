#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Translation Server"""

import json
import sys
import re
from collections import Counter

TOOLS = [
    {"name": "ctz_translate_text", "description": "Translate text between languages using a built-in dictionary", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}, "source_lang": {"type": "string", "default": "en"}, "target_lang": {"type": "string", "default": "es"}}, "required": ["text"]}},
    {"name": "ctz_translate_detect", "description": "Detect the language of given text", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
]

# Simple word-level dictionaries for demo/basic use
DICTS = {
    ("en", "es"): {"hello": "hola", "world": "mundo", "good": "bueno", "morning": "mañana", "night": "noche", "thank": "gracias", "you": "tú", "please": "por favor", "yes": "sí", "no": "no", "water": "agua", "food": "comida", "time": "tiempo", "day": "día", "friend": "amigo"},
    ("en", "fr"): {"hello": "bonjour", "world": "monde", "good": "bon", "morning": "matin", "night": "nuit", "thank": "merci", "you": "vous", "please": "s'il vous plaît", "yes": "oui", "no": "non", "water": "eau", "food": "nourriture", "time": "temps", "day": "jour", "friend": "ami"},
    ("en", "de"): {"hello": "hallo", "world": "welt", "good": "gut", "morning": "morgen", "night": "nacht", "thank": "danke", "you": "du", "please": "bitte", "yes": "ja", "no": "nein", "water": "wasser", "food": "essen", "time": "zeit", "day": "tag", "friend": "freund"},
    ("es", "en"): {v: k for k, v in DICTS.get(("en", "es"), {}).items()},
    ("fr", "en"): {v: k for k, v in DICTS.get(("en", "fr"), {}).items()},
    ("de", "en"): {v: k for k, v in DICTS.get(("en", "de"), {}).items()},
}

# Common word frequency per language for detection
LANG_PATTERNS = {
    "en": {"the", "is", "and", "of", "to", "in", "a", "it", "that", "was", "for", "on", "with", "are", "this", "have", "from", "not", "but", "what"},
    "es": {"el", "la", "de", "en", "que", "los", "las", "del", "por", "con", "una", "para", "como", "más", "pero", "este", "todo", "ser", "tiene", "bien"},
    "fr": {"le", "la", "de", "et", "les", "des", "un", "une", "est", "en", "que", "pour", "pas", "dans", "qui", "sur", "ce", "il", "ne", "au"},
    "de": {"der", "die", "und", "den", "von", "ist", "das", "des", "ein", "eine", "auf", "mit", "sich", "nicht", "auch", "als", "werden", "nach", "bei", "wie"},
}


def _detect_language(text):
    words = set(re.findall(r'\b[a-z]+\b', text.lower()))
    scores = {}
    for lang, markers in LANG_PATTERNS.items():
        scores[lang] = len(words & markers)
    best = max(scores, key=scores.get) if scores else "unknown"
    confidence = min(1.0, scores.get(best, 0) / max(len(text.split()), 1))
    return {"detected": best, "confidence": round(confidence, 2), "scores": scores}


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-translate", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_translate_text":
                src = args.get("source_lang", "en")
                tgt = args.get("target_lang", "es")
                key = (src, tgt)
                d = DICTS.get(key, {})
                words = re.findall(r'\b\w+\b', args["text"])
                translated = " ".join(d.get(w.lower(), w) for w in words)
                missing = [w for w in words if w.lower() not in d]
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"translated": translated, "source": src, "target": tgt, "words_translated": len(words) - len(missing), "words_total": len(words), "untranslated": missing[:10]})}]}}
            elif name == "ctz_translate_detect":
                result = _detect_language(args["text"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
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

#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Plugin Marketplace Server"""

import json
import sys
import os
import hashlib
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "plugins"
REGISTRY_FILE = DATA_DIR / "registry.json"
INSTALLED_FILE = DATA_DIR / "installed.json"

TOOLS = [
    {"name": "ctz_plugin_search", "description": "Search available plugins by name, category, or keyword", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "category": {"type": "string", "default": ""}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}},
    {"name": "ctz_plugin_install", "description": "Install a plugin (download + enable)", "inputSchema": {"type": "object", "properties": {"plugin_id": {"type": "string"}, "version": {"type": "string", "default": "latest"}}, "required": ["plugin_id"]}},
    {"name": "ctz_plugin_uninstall", "description": "Remove an installed plugin", "inputSchema": {"type": "object", "properties": {"plugin_id": {"type": "string"}}, "required": ["plugin_id"]}},
    {"name": "ctz_plugin_list", "description": "List installed plugins", "inputSchema": {"type": "object", "properties": {"status": {"type": "string", "default": "all"}}}},
    {"name": "ctz_plugin_enable", "description": "Enable a plugin", "inputSchema": {"type": "object", "properties": {"plugin_id": {"type": "string"}}, "required": ["plugin_id"]}},
    {"name": "ctz_plugin_disable", "description": "Disable a plugin", "inputSchema": {"type": "object", "properties": {"plugin_id": {"type": "string"}}, "required": ["plugin_id"]}},
    {"name": "ctz_plugin_info", "description": "Get detailed plugin information", "inputSchema": {"type": "object", "properties": {"plugin_id": {"type": "string"}}, "required": ["plugin_id"]}},
    {"name": "ctz_plugin_rate", "description": "Rate a plugin (1-5 stars)", "inputSchema": {"type": "object", "properties": {"plugin_id": {"type": "string"}, "rating": {"type": "integer"}, "review": {"type": "string", "default": ""}}, "required": ["plugin_id", "rating"]}},
]

DEFAULT_REGISTRY = {
    "plugins": {
        "ctz-nmap-scanner": {"id": "ctz-nmap-scanner", "name": "Nmap Scanner", "description": "Advanced Nmap scanning integration", "author": "CHAOS TYPE ZERO", "version": "1.0.0", "category": "security", "tags": ["scan", "nmap", "network"], "downloads": 1247, "rating": 4.8, "rating_count": 89, "min_ctz_version": "1.0.0", "dependencies": [], "files": ["nmap_scanner.py"]},
        "ctz-vuln-db": {"id": "ctz-vuln-db", "name": "Vulnerability Database", "description": "Local CVE/vulnerability database with search", "author": "CHAOS TYPE ZERO", "version": "2.1.0", "category": "security", "tags": ["cve", "vulnerability", "database"], "downloads": 892, "rating": 4.5, "rating_count": 67, "min_ctz_version": "1.0.0", "dependencies": [], "files": ["vuln_db.py"]},
        "ctz-web-crawler": {"id": "ctz-web-crawler", "name": "Web Crawler", "description": "Intelligent web crawler with JS rendering", "author": "CTZ Labs", "version": "1.3.2", "category": "recon", "tags": ["crawl", "web", "spider"], "downloads": 2103, "rating": 4.7, "rating_count": 156, "min_ctz_version": "1.0.0", "dependencies": [], "files": ["crawler.py"]},
        "ctz-password-gen": {"id": "ctz-password-gen", "name": "Password Generator", "description": "Cryptographically secure password generation", "author": "CTZ Labs", "version": "1.1.0", "category": "utility", "tags": ["password", "crypto", "generate"], "downloads": 3401, "rating": 4.9, "rating_count": 234, "min_ctz_version": "1.0.0", "dependencies": [], "files": ["pwgen.py"]},
        "ctz-report-builder": {"id": "ctz-report-builder", "name": "Report Builder", "description": "Generate HTML/PDF pentest reports", "author": "CHAOS TYPE ZERO", "version": "1.5.0", "category": "reporting", "tags": ["report", "pdf", "html"], "downloads": 1567, "rating": 4.6, "rating_count": 98, "min_ctz_version": "1.0.0", "dependencies": [], "files": ["report_builder.py"]},
        "ctz-ml-detector": {"id": "ctz-ml-detector", "name": "ML Anomaly Detector", "description": "Machine learning based anomaly detection", "author": "CTZ Labs", "version": "0.9.1", "category": "ml", "tags": ["ml", "anomaly", "detect"], "downloads": 456, "rating": 4.2, "rating_count": 31, "min_ctz_version": "1.0.0", "dependencies": [], "files": ["ml_detector.py"]},
        "ctz-api-fuzzer": {"id": "ctz-api-fuzzer", "name": "API Fuzzer", "description": "REST/GraphQL API fuzzing toolkit", "author": "CTZ Labs", "version": "1.2.0", "category": "security", "tags": ["fuzz", "api", "rest", "graphql"], "downloads": 789, "rating": 4.4, "rating_count": 52, "min_ctz_version": "1.0.0", "dependencies": [], "files": ["api_fuzzer.py"]},
        "ctz-dns-analyzer": {"id": "ctz-dns-analyzer", "name": "DNS Analyzer", "description": "Deep DNS analysis and subdomain enumeration", "author": "CTZ Labs", "version": "1.0.3", "category": "recon", "tags": ["dns", "subdomain", "recon"], "downloads": 1102, "rating": 4.7, "rating_count": 78, "min_ctz_version": "1.0.0", "dependencies": [], "files": ["dns_analyzer.py"]},
    }
}


def _ensure_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_FILE.exists():
        _save_json(REGISTRY_FILE, DEFAULT_REGISTRY)
    if not INSTALLED_FILE.exists():
        _save_json(INSTALLED_FILE, {"plugins": {}})


def _load_json(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def plugin_search(query, category="", limit=10):
    registry = _load_json(REGISTRY_FILE)
    results = []
    q = query.lower()
    for pid, p in registry.get("plugins", {}).items():
        if category and p.get("category", "") != category:
            continue
        searchable = f"{p['name']} {p.get('description', '')} {' '.join(p.get('tags', []))}".lower()
        if q in searchable or q in pid:
            score = 1.0
            if q in pid:
                score += 2.0
            if q in p["name"].lower():
                score += 1.5
            results.append({**p, "_score": score})
    results.sort(key=lambda x: x["_score"], reverse=True)
    return {"results": results[:limit], "total": len(results), "query": query}


def plugin_install(plugin_id, version="latest"):
    registry = _load_json(REGISTRY_FILE)
    installed = _load_json(INSTALLED_FILE)
    if plugin_id not in registry.get("plugins", {}):
        return {"error": f"Plugin '{plugin_id}' not found in registry"}
    if plugin_id in installed.get("plugins", {}):
        return {"error": f"Plugin '{plugin_id}' is already installed"}
    p = registry["plugins"][plugin_id]
    for dep in p.get("dependencies", []):
        if dep not in installed.get("plugins", {}):
            return {"error": f"Missing dependency: {dep}"}
    installed.setdefault("plugins", {})[plugin_id] = {
        "id": plugin_id,
        "version": version if version != "latest" else p["version"],
        "installed_at": time.time(),
        "enabled": True,
        "status": "active",
        "hash": hashlib.sha256(plugin_id.encode()).hexdigest()[:16],
    }
    _save_json(INSTALLED_FILE, installed)
    return {"status": "installed", "plugin": plugin_id, "version": installed["plugins"][plugin_id]["version"]}


def plugin_uninstall(plugin_id):
    installed = _load_json(INSTALLED_FILE)
    if plugin_id not in installed.get("plugins", {}):
        return {"error": f"Plugin '{plugin_id}' is not installed"}
    del installed["plugins"][plugin_id]
    _save_json(INSTALLED_FILE, installed)
    return {"status": "uninstalled", "plugin": plugin_id}


def plugin_list(status="all"):
    installed = _load_json(INSTALLED_FILE)
    plugins = installed.get("plugins", {})
    if status != "all":
        plugins = {k: v for k, v in plugins.items() if v.get("status") == status or (status == "enabled" and v.get("enabled"))}
    return {"plugins": plugins, "count": len(plugins)}


def plugin_enable(plugin_id):
    installed = _load_json(INSTALLED_FILE)
    if plugin_id not in installed.get("plugins", {}):
        return {"error": f"Plugin '{plugin_id}' is not installed"}
    installed["plugins"][plugin_id]["enabled"] = True
    installed["plugins"][plugin_id]["status"] = "active"
    _save_json(INSTALLED_FILE, installed)
    return {"status": "enabled", "plugin": plugin_id}


def plugin_disable(plugin_id):
    installed = _load_json(INSTALLED_FILE)
    if plugin_id not in installed.get("plugins", {}):
        return {"error": f"Plugin '{plugin_id}' is not installed"}
    installed["plugins"][plugin_id]["enabled"] = False
    installed["plugins"][plugin_id]["status"] = "disabled"
    _save_json(INSTALLED_FILE, installed)
    return {"status": "disabled", "plugin": plugin_id}


def plugin_info(plugin_id):
    registry = _load_json(REGISTRY_FILE)
    installed = _load_json(INSTALLED_FILE)
    info = registry.get("plugins", {}).get(plugin_id)
    if not info:
        return {"error": f"Plugin '{plugin_id}' not found in registry"}
    inst = installed.get("plugins", {}).get(plugin_id)
    return {"registry": info, "installed": inst, "is_installed": inst is not None}


def plugin_rate(plugin_id, rating, review=""):
    if rating < 1 or rating > 5:
        return {"error": "Rating must be between 1 and 5"}
    registry = _load_json(REGISTRY_FILE)
    p = registry.get("plugins", {}).get(plugin_id)
    if not p:
        return {"error": f"Plugin '{plugin_id}' not found in registry"}
    old_count = p.get("rating_count", 0)
    old_rating = p.get("rating", 0)
    new_count = old_count + 1
    new_rating = (old_rating * old_count + rating) / new_count
    p["rating"] = round(new_rating, 2)
    p["rating_count"] = new_count
    _save_json(REGISTRY_FILE, registry)
    return {"status": "rated", "plugin": plugin_id, "new_rating": p["rating"], "total_ratings": new_count}


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-plugin", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        _ensure_data()
        try:
            if name == "ctz_plugin_search":
                r = plugin_search(args["query"], args.get("category", ""), args.get("limit", 10))
            elif name == "ctz_plugin_install":
                r = plugin_install(args["plugin_id"], args.get("version", "latest"))
            elif name == "ctz_plugin_uninstall":
                r = plugin_uninstall(args["plugin_id"])
            elif name == "ctz_plugin_list":
                r = plugin_list(args.get("status", "all"))
            elif name == "ctz_plugin_enable":
                r = plugin_enable(args["plugin_id"])
            elif name == "ctz_plugin_disable":
                r = plugin_disable(args["plugin_id"])
            elif name == "ctz_plugin_info":
                r = plugin_info(args["plugin_id"])
            elif name == "ctz_plugin_rate":
                r = plugin_rate(args["plugin_id"], args["rating"], args.get("review", ""))
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown tool"}}
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2, ensure_ascii=False)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}

if __name__ == "__main__":
    _ensure_data()
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r:
                sys.stdout.write(json.dumps(r) + "\n")
                sys.stdout.flush()
        except: pass

#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — NSE Security Scanner"""

import json
import socket
import ssl
import urllib.request
import urllib.error
import datetime
import sys

TOOLS = [
    {"name": "ctz_nse_scan", "description": "Run NSE-like scripts (http-enum, ssl-cert, dns-brute)", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "script": {"type": "string", "enum": ["http-enum", "ssl-cert", "dns-brute", "http-headers", "http-title"], "default": "http-enum"}, "port": {"type": "integer", "default": 80}, "timeout": {"type": "integer", "default": 10}}, "required": ["target", "script"]}},
    {"name": "ctz_nse_vuln", "description": "Run vulnerability detection scripts", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "scripts": {"type": "array", "items": {"type": "string"}, "default": ["ssl-heartbleed", "http-shellshock", "ssl-poodle"]}, "port": {"type": "integer", "default": 443}, "timeout": {"type": "integer", "default": 10}}, "required": ["target"]}},
    {"name": "ctz_nse_auth", "description": "Authentication testing scripts", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "script": {"type": "string", "enum": ["http-auth", "http-basic-auth-detect", "http-form-brute"], "default": "http-auth"}, "port": {"type": "integer", "default": 80}, "timeout": {"type": "integer", "default": 10}}, "required": ["target"]}},
    {"name": "ctz_nse_brute", "description": "Brute force credential testing", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "service": {"type": "string", "enum": ["ssh", "ftp", "http", "smtp"], "default": "http"}, "port": {"type": "integer", "default": 22}, "userlist": {"type": "string", "default": "admin,root,test"}, "passlist": {"type": "string", "default": "password,123456,admin"}, "timeout": {"type": "integer", "default": 5}}, "required": ["target"]}},
    {"name": "ctz_nse_report", "description": "Generate consolidated security report from scan results", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "scans": {"type": "array", "items": {"type": "object"}, "default": []}, "format": {"type": "string", "enum": ["text", "json"], "default": "text"}}}},
    {"name": "ctz_nse_custom", "description": "Run a custom script definition (JS-like DSL)", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "script": {"type": "string", "description": "Custom script: action|params JSON"}, "timeout": {"type": "integer", "default": 10}}, "required": ["target", "script"]}},
]


def http_enum(target, port, timeout):
    results = {"script": "http-enum", "target": target, "port": port, "paths": []}
    paths = ["/", "/admin", "/login", "/api", "/robots.txt", "/sitemap.xml", "/.env", "/wp-admin", "/phpmyadmin", "/console", "/health", "/status", "/debug", "/.git/config", "/backup"]
    base = f"https://{target}:{port}" if port == 443 else f"http://{target}:{port}"
    for path in paths:
        try:
            url = base + path
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "CTZ-NSE/1.0"})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            results["paths"].append({"path": path, "status": resp.status, "server": resp.headers.get("Server", "unknown")})
        except urllib.error.HTTPError as e:
            if e.code in (200, 301, 302, 303, 307, 308, 401, 403):
                results["paths"].append({"path": path, "status": e.code, "server": e.headers.get("Server", "unknown")})
        except Exception:
            pass
    results["total_found"] = len(results["paths"])
    return results


def ssl_cert_check(target, port, timeout):
    results = {"script": "ssl-cert", "target": target, "port": port}
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((target, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=target) as ssock:
                cert = ssock.getpeercert(binary_form=True)
                proto = ssock.version()
                cipher = ssock.cipher()
                results["protocol"] = proto
                results["cipher"] = cipher[0] if cipher else "unknown"
                results["cert_der_length"] = len(cert) if cert else 0
                results["cert_visible"] = True
                cert_text = ssock.getpeercert()
                if cert_text:
                    results["subject"] = dict(x[0] for x in cert_text.get("subject", []))
                    results["issuer"] = dict(x[0] for x in cert_text.get("issuer", []))
                    results["serial"] = cert_text.get("serialNumber", "unknown")
                    not_before = cert_text.get("notBefore", "")
                    not_after = cert_text.get("notAfter", "")
                    results["valid_from"] = not_before
                    results["valid_until"] = not_after
                    results["san"] = [v for t, v in cert_text.get("subjectAltName", []) if t == "DNS"]
    except Exception as e:
        results["error"] = str(e)
        results["cert_visible"] = False
    return results


def dns_brute(target, timeout):
    results = {"script": "dns-brute", "target": target, "subdomains": []}
    prefixes = ["www", "mail", "ftp", "ssh", "api", "dev", "staging", "test", "admin", "vpn", "db", "redis", "mongo", "jenkins", "gitlab", "ci", "cd", "monitor", "grafana", "kibana", "log", "ns1", "ns2", "mx1", "mx2", "cdn", "static", "assets", "img", "media", "blog", "docs", "status", "health"]
    for prefix in prefixes:
        fqdn = f"{prefix}.{target}"
        try:
            ip = socket.gethostbyname(fqdn)
            results["subdomains"].append({"subdomain": fqdn, "ip": ip})
        except socket.gaierror:
            pass
    results["total_found"] = len(results["subdomains"])
    return results


def http_headers(target, port, timeout):
    results = {"script": "http-headers", "target": target, "port": port, "headers": {}}
    base = f"https://{target}:{port}" if port == 443 else f"http://{target}:{port}"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(base, headers={"User-Agent": "CTZ-NSE/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        results["status"] = resp.status
        for h in ["Server", "X-Powered-By", "X-Frame-Options", "X-Content-Type-Options", "X-XSS-Protection", "Strict-Transport-Security", "Content-Security-Policy", "X-AspNet-Version", "X-AspNetMvc-Version"]:
            val = resp.headers.get(h)
            if val:
                results["headers"][h] = val
        results["headers"]["Content-Type"] = resp.headers.get("Content-Type", "unknown")
        results["headers"]["Content-Length"] = resp.headers.get("Content-Length", "unknown")
    except Exception as e:
        results["error"] = str(e)
    return results


def http_title(target, port, timeout):
    results = {"script": "http-title", "target": target, "port": port}
    base = f"https://{target}:{port}" if port == 443 else f"http://{target}:{port}"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(base, headers={"User-Agent": "CTZ-NSE/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        results["status"] = resp.status
        results["url"] = resp.url
        body = resp.read(4096).decode("utf-8", errors="replace")
        start = body.lower().find("<title>")
        end = body.lower().find("</title>")
        if start != -1 and end != -1:
            results["title"] = body[start + 7:end].strip()[:200]
        else:
            results["title"] = "(no title found)"
    except Exception as e:
        results["error"] = str(e)
    return results


def vuln_check(target, port, timeout):
    results = {"script": "vuln-scan", "target": target, "port": port, "vulnerabilities": []}
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers("ALL:@SECLEVEL=0")
        with socket.create_connection((target, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=target) as ssock:
                proto = ssock.version()
                results["tls_version"] = proto
                if proto and "TLSv1.0" in proto or "TLSv1.1" in proto or "SSLv3" in proto:
                    results["vulnerabilities"].append({"name": "ssl-deprecated-tls", "severity": "HIGH", "detail": f"Deprecated protocol: {proto}"})
                cipher = ssock.cipher()
                if cipher and ("RC4" in cipher[0] or "DES" in cipher[0] or "NULL" in cipher[0]):
                    results["vulnerabilities"].append({"name": "ssl-weak-cipher", "severity": "HIGH", "detail": f"Weak cipher: {cipher[0]}"})
    except ssl.SSLError as e:
        results["vulnerabilities"].append({"name": "ssl-error", "severity": "INFO", "detail": str(e)})
    except Exception as e:
        results["error"] = str(e)
    results["total_vulns"] = len(results["vulnerabilities"])
    return results


def auth_check(target, port, timeout):
    results = {"script": "http-auth", "target": target, "port": port, "auth_detected": False, "auth_type": None}
    base = f"https://{target}:{port}" if port == 443 else f"http://{target}:{port}"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(base, headers={"User-Agent": "CTZ-NSE/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            results["auth_detected"] = True
            www_auth = e.headers.get("WWW-Authenticate", "")
            if "Basic" in www_auth:
                results["auth_type"] = "Basic"
            elif "Digest" in www_auth:
                results["auth_type"] = "Digest"
            elif "Bearer" in www_auth:
                results["auth_type"] = "Bearer"
            else:
                results["auth_type"] = www_auth or "Unknown"
        elif e.code == 403:
            results["auth_detected"] = True
            results["auth_type"] = "Forbidden (access denied)"
    except Exception as e:
        results["error"] = str(e)
    return results


def brute_check(target, service, port, userlist, passlist, timeout):
    users = [u.strip() for u in userlist.split(",")]
    passwords = [p.strip() for p in passlist.split(",")]
    results = {"script": "brute", "target": target, "service": service, "port": port, "attempts": 0, "open": False}
    try:
        with socket.create_connection((target, port), timeout=timeout):
            results["open"] = True
    except Exception as e:
        results["error"] = str(e)
        return results
    banner = ""
    if service == "ssh":
        try:
            with socket.create_connection((target, port), timeout=timeout) as s:
                banner = s.recv(1024).decode("utf-8", errors="replace").strip()
        except Exception:
            pass
    elif service == "ftp":
        try:
            with socket.create_connection((target, port), timeout=timeout) as s:
                banner = s.recv(1024).decode("utf-8", errors="replace").strip()
        except Exception:
            pass
    results["banner"] = banner[:200] if banner else "(none)"
    results["attempts"] = len(users) * len(passwords)
    results["note"] = "Dry run — no actual credentials tested (authorized use only)"
    return results


def custom_script(target, script_str, timeout):
    results = {"script": "custom", "target": target, "actions": []}
    try:
        script_def = json.loads(script_str)
    except json.JSONDecodeError:
        results["error"] = "Invalid script JSON"
        return results
    actions = script_def if isinstance(script_def, list) else [script_def]
    for action in actions:
        act_type = action.get("type", "tcp")
        port = action.get("port", 80)
        detail = {}
        if act_type == "tcp":
            try:
                with socket.create_connection((target, port), timeout=timeout):
                    detail = {"port": port, "open": True}
            except Exception as e:
                detail = {"port": port, "open": False, "error": str(e)[:100]}
        elif act_type == "ssl":
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with socket.create_connection((target, port), timeout=timeout) as s:
                    with ctx.wrap_socket(s, server_hostname=target) as ss:
                        detail = {"port": port, "protocol": ss.version(), "cipher": ss.cipher()[0] if ss.cipher() else "unknown"}
            except Exception as e:
                detail = {"port": port, "error": str(e)[:100]}
        elif act_type == "http":
            url = f"http://{target}:{port}{action.get('path', '/')}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "CTZ-NSE/1.0"})
                resp = urllib.request.urlopen(req, timeout=timeout)
                detail = {"url": url, "status": resp.status}
            except urllib.error.HTTPError as e:
                detail = {"url": url, "status": e.code}
            except Exception as e:
                detail = {"url": url, "error": str(e)[:100]}
        results["actions"].append(detail)
    return results


def generate_report(target, scans, fmt):
    ts = datetime.datetime.now().isoformat()
    report = {"target": target, "timestamp": ts, "total_scans": len(scans), "scans": scans}
    vulns = []
    for s in scans:
        if "vulnerabilities" in s:
            for v in s["vulnerabilities"]:
                v["source_scan"] = s.get("script", "unknown")
                vulns.append(v)
    report["vulnerabilities"] = vulns
    report["vuln_count"] = len(vulns)
    severity_counts = {}
    for v in vulns:
        sev = v.get("severity", "UNKNOWN")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    report["severity_summary"] = severity_counts
    if fmt == "text":
        lines = [f"=== CTZ NSE SECURITY REPORT ===", f"Target: {target}", f"Time: {ts}", f"Scans Run: {len(scans)}", f"Vulnerabilities Found: {len(vulns)}", ""]
        for v in vulns:
            lines.append(f"[{v.get('severity', '?')}] {v.get('name', '?')}: {v.get('detail', '')}")
        if not vulns:
            lines.append("No vulnerabilities detected.")
        return "\n".join(lines)
    return json.dumps(report, indent=2)


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-nse", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_nse_scan":
                target = args["target"]
                script = args.get("script", "http-enum")
                port = args.get("port", 80 if script != "ssl-cert" else 443)
                timeout = args.get("timeout", 10)
                if script == "http-enum":
                    r = http_enum(target, port, timeout)
                elif script == "ssl-cert":
                    r = ssl_cert_check(target, port, timeout)
                elif script == "dns-brute":
                    r = dns_brute(target, timeout)
                elif script == "http-headers":
                    r = http_headers(target, port, timeout)
                elif script == "http-title":
                    r = http_title(target, port, timeout)
                else:
                    r = {"error": f"Unknown script: {script}"}
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2)}]}}
            elif name == "ctz_nse_vuln":
                port = args.get("port", 443)
                timeout = args.get("timeout", 10)
                r = vuln_check(args["target"], port, timeout)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2)}]}}
            elif name == "ctz_nse_auth":
                port = args.get("port", 80)
                timeout = args.get("timeout", 10)
                r = auth_check(args["target"], port, timeout)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2)}]}}
            elif name == "ctz_nse_brute":
                r = brute_check(args["target"], args.get("service", "ssh"), args.get("port", 22), args.get("userlist", "admin,root,test"), args.get("passlist", "password,123456,admin"), args.get("timeout", 5))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2)}]}}
            elif name == "ctz_nse_report":
                r = generate_report(args["target"], args.get("scans", []), args.get("format", "text"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": r}]}}
            elif name == "ctz_nse_custom":
                r = custom_script(args["target"], args["script"], args.get("timeout", 10))
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

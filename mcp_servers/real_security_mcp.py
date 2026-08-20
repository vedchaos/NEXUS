#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Real Security Scanner (Nmap + Nuclei via WSL2)"""
import json, sys, subprocess, os, tempfile, time

TOOLS = [
    {"name": "ctz_real_nmap_scan", "description": "Real Nmap scan via WSL2", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "scan_type": {"type": "string", "default": "quick"}, "ports": {"type": "string", "default": "top-1000"}}, "required": ["target"]}},
    {"name": "ctz_real_nmap_service", "description": "Nmap service/version detection", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "ports": {"type": "string", "default": "1-1000"}}, "required": ["target"]}},
    {"name": "ctz_real_nmap_os", "description": "Nmap OS detection", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]}},
    {"name": "ctz_real_nuclei_scan", "description": "Real Nuclei vulnerability scan via WSL2", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "severity": {"type": "string", "default": "medium,high,critical"}, "templates": {"type": "string", "default": ""}}, "required": ["target"]}},
    {"name": "ctz_real_nuclei_severity", "description": "Nuclei scan by severity", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "severity": {"type": "string", "default": "critical"}}, "required": ["target"]}},
    {"name": "ctz_real_combined_scan", "description": "Nmap + Nuclei combined scan", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "quick": {"type": "boolean", "default": True}}, "required": ["target"]}},
    {"name": "ctz_real_port_scan", "description": "Quick port scan with Nmap", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "ports": {"type": "string", "default": "21,22,25,53,80,443,3306,8080"}}, "required": ["target"]}},
    {"name": "ctz_check_tools", "description": "Check if Nmap/Nuclei are installed in WSL2", "inputSchema": {"type": "object", "properties": {}, "required": []}},
]


def _run_wsl(cmd, timeout=120):
    """Run command via WSL2 and return output."""
    try:
        result = subprocess.run(
            ["wsl", "-e", "bash", "-c", cmd],
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return {
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:5000],
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"error": "WSL2 not found. Install with: wsl --install"}
    except Exception as e:
        return {"error": str(e)}


def handle_check_tools(params):
    """Check if Nmap and Nuclei are installed in WSL2."""
    nmap = _run_wsl("which nmap 2>/dev/null && nmap --version | head -2")
    nuclei = _run_wsl("which nuclei 2>/dev/null && nuclei -version 2>&1 | head -2")
    return {
        "nmap": {
            "installed": nmap.get("returncode", 1) == 0,
            "info": nmap.get("stdout", "Not installed").strip()
        },
        "nuclei": {
            "installed": nuclei.get("returncode", 1) == 0,
            "info": nuclei.get("stdout", "Not installed").strip()
        },
        "install_cmd": "wsl -e bash -c 'sudo apt update && sudo apt install -y nmap; go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest'"
    }


def handle_nmap_scan(params):
    target = params.get("target", "")
    scan_type = params.get("scan_type", "quick")
    ports = params.get("ports", "top-1000")
    
    flags = {
        "quick": "-sV -T4 --top-ports 100",
        "full": "-sV -sC -T4 -p-",
        "stealth": "-sS -T2 --top-ports 100",
        "udp": "-sU -T4 --top-ports 50",
        "aggressive": "-sV -sC -A -T4",
    }
    flag_str = flags.get(scan_type, flags["quick"])
    
    cmd = f"nmap {flag_str} {target} -oX /tmp/nmap_result.xml 2>&1; cat /tmp/nmap_result.xml 2>/dev/null"
    result = _run_wsl(cmd, timeout=180)
    return {"target": target, "scan_type": scan_type, "output": result.get("stdout", result.get("error", ""))[:8000]}


def handle_nmap_service(params):
    target = params.get("target", "")
    ports = params.get("ports", "1-1000")
    cmd = f"nmap -sV -p {ports} {target} 2>&1"
    result = _run_wsl(cmd, timeout=180)
    return {"target": target, "output": result.get("stdout", result.get("error", ""))[:8000]}


def handle_nmap_os(params):
    target = params.get("target", "")
    cmd = f"nmap -O {target} 2>&1"
    result = _run_wsl(cmd, timeout=120)
    return {"target": target, "output": result.get("stdout", result.get("error", ""))[:8000]}


def handle_nuclei_scan(params):
    target = params.get("target", "")
    severity = params.get("severity", "medium,high,critical")
    templates = params.get("templates", "")
    
    cmd = f"nuclei -target {target} -severity {severity}"
    if templates:
        cmd += f" -t {templates}"
    cmd += " -json 2>&1"
    
    result = _run_wsl(cmd, timeout=300)
    return {"target": target, "severity": severity, "output": result.get("stdout", result.get("error", ""))[:8000]}


def handle_nuclei_severity(params):
    target = params.get("target", "")
    severity = params.get("severity", "critical")
    cmd = f"nuclei -target {target} -severity {severity} -json 2>&1"
    result = _run_wsl(cmd, timeout=300)
    return {"target": target, "severity": severity, "output": result.get("stdout", result.get("error", ""))[:8000]}


def handle_combined_scan(params):
    target = params.get("target", "")
    quick = params.get("quick", True)
    
    # Phase 1: Nmap
    nmap_cmd = f"nmap -sV -T4 --top-ports 100 {target} 2>&1"
    nmap_result = _run_wsl(nmap_cmd, timeout=180)
    
    # Phase 2: Nuclei
    nuclei_cmd = f"nuclei -target {target} -severity medium,high,critical -json 2>&1"
    nuclei_result = _run_wsl(nuclei_cmd, timeout=300)
    
    return {
        "target": target,
        "nmap": nmap_result.get("stdout", nmap_result.get("error", ""))[:5000],
        "nuclei": nuclei_result.get("stdout", nuclei_result.get("error", ""))[:5000],
    }


def handle_port_scan(params):
    target = params.get("target", "")
    ports = params.get("ports", "21,22,25,53,80,443,3306,8080")
    cmd = f"nmap -p {ports} {target} 2>&1"
    result = _run_wsl(cmd, timeout=60)
    return {"target": target, "ports": ports, "output": result.get("stdout", result.get("error", ""))[:5000]}


HANDLERS = {
    "ctz_real_nmap_scan": handle_nmap_scan,
    "ctz_real_nmap_service": handle_nmap_service,
    "ctz_real_nmap_os": handle_nmap_os,
    "ctz_real_nuclei_scan": handle_nuclei_scan,
    "ctz_real_nuclei_severity": handle_nuclei_severity,
    "ctz_real_combined_scan": handle_combined_scan,
    "ctz_real_port_scan": handle_port_scan,
    "ctz_check_tools": handle_check_tools,
}


def handle_request(request):
    method, params, req_id = request.get("method"), request.get("params", {}), request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-real-security", "version": "1.0.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_params = params.get("arguments", {})
        handler = HANDLERS.get(tool_name)
        if not handler:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}
        try:
            result = handler(tool_params)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


if __name__ == "__main__":
    print("CTZ Real Security Scanner (Nmap/Nuclei via WSL2) running", file=sys.stderr)
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue

#!/usr/bin/env python3
"""
NEXUS Security Module — Recon & Vulnerability Scanning
Authorized security research tools via WSL2 Kali Linux
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

NEXUS_ROOT = Path(__file__).parent.parent
RESULTS_DIR = NEXUS_ROOT / "data" / "scan_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

USE_WSL = True  # Use WSL2 Kali Linux


def run_cmd(cmd, timeout=300):
    """Run a command safely"""
    try:
        if USE_WSL:
            full_cmd = f"wsl -d kali-linux -- bash -c '{cmd}'"
        else:
            full_cmd = cmd

        result = subprocess.run(
            full_cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] Command timed out after {timeout}s"
    except Exception as e:
        return f"[ERROR] {str(e)}"


def recon_passive(target):
    """Passive recon — no direct contact"""
    results = {}
    results["whois"] = run_cmd(f"whois {target}", timeout=30)
    results["dig"] = run_cmd(f"dig {target} ANY +noall +answer", timeout=30)
    results["nslookup"] = run_cmd(f"nslookup {target}", timeout=30)
    results["subdomains"] = run_cmd(f"sublist3r -d {target} -silent", timeout=120)
    return results


def recon_active(target, scan_type="quick"):
    """Active recon — direct contact with target"""
    if scan_type == "quick":
        cmd = f"nmap -sV -sC --top-ports 1000 -oG - {target}"
    elif scan_type == "full":
        cmd = f"nmap -sV -sC -p- --min-rate 5000 -oG - {target}"
    elif scan_type == "stealth":
        cmd = f"nmap -sS -sV --top-ports 1000 -T2 -oG - {target}"
    else:
        cmd = f"nmap -sV --top-ports 100 -oG - {target}"

    return run_cmd(cmd, timeout=600)


def scan_web(target, port=80):
    """Web vulnerability scanning"""
    results = {}
    results["nikto"] = run_cmd(f"nikto -h {target} -p {port}", timeout=300)
    results["whatweb"] = run_cmd(f"whatweb {target}", timeout=120)
    results["gobuster"] = run_cmd(
        f"gobuster dir -u http://{target} -w /usr/share/wordlists/dirb/common.txt -t 20 -q",
        timeout=300
    )
    return results


def scan_vulns(target):
    """Vulnerability scanning with nuclei"""
    output = run_cmd(f"nuclei -u {target} -severity critical,high,medium -json", timeout=600)
    findings = []
    for line in output.strip().split("\n"):
        if line.strip():
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return findings


def full_scan(target, authorized=False):
    """Complete scan workflow"""
    all_results = {}

    # Phase 1: Passive
    all_results["recon_passive"] = recon_passive(target)

    # Phase 2: Active
    all_results["recon_active"] = recon_active(target, "quick")

    # Phase 3: Web (if HTTP detected)
    if "80" in str(all_results["recon_active"]) or "443" in str(all_results["recon_active"]):
        all_results["web"] = scan_web(target)

    # Phase 4: Vuln (if authorized)
    if authorized:
        all_results["vulns"] = scan_vulns(target)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = RESULTS_DIR / f"full_{target.replace('.', '_')}_{timestamp}.json"
    result_file.write_text(json.dumps(all_results, indent=2, default=str))

    return {"file": str(result_file), "results": all_results}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recon.py <target> [--authorized]")
        sys.exit(1)

    target = sys.argv[1]
    authorized = "--authorized" in sys.argv

    result = full_scan(target, authorized)
    print(f"\n[NEXUS] Scan complete. Results: {result['file']}")

---
name: ctz-security
description: Security scanning and penetration testing. Use when user asks to scan, hack, pentest, vulnerability assessment, nmap, nuclei, sqlmap, or security audit.
---

# CHAOS TYPE ZERO Security Skill

Security scanning toolkit for CHAOS TYPE ZERO. All scans require explicit authorization.

## Tools Available
- `pentest_scan` — Full vulnerability scan
- `pentest_recon` — Passive/active reconnaissance
- `pentest_web` — Web application scanning

## Authorization Protocol
**NEVER** run security tools without user saying "authorized" or "go ahead".

## Scan Types
1. **Recon** — DNS, subdomains, ports (safe)
2. **Web Scan** — Headers, technologies, vulnerabilities
3. **Full Scan** — Everything combined

## Commands
- "scan target.com" → recon + web scan
- "hack target.com" → ask for authorization first
- "nmap 192.168.1.1" → port scan
- "find vulns in app" → vulnerability assessment

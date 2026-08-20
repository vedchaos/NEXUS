---
name: ctz-status
description: Live status dashboard using ctz_status_uptime/ctz/mcp tools
---

# CTZ Status Skill

## When to Use
- Monitoring system uptime
- Checking CTZ service status
- Verifying MCP server connections

## Available Tools
- ctz_status_uptime: Get system uptime and availability
- ctz_status_ctz: Check CTZ core service status
- ctz_status_mcp: Verify MCP server connections

## Workflow
1. Check system uptime with ctz_status_uptime
2. Verify CTZ services with ctz_status_ctz
3. Test MCP connections with ctz_status_mcp
4. Address any issues found

## Examples
- "user request" → "How long has system been up?" → ctz_status_uptime
- "user request" → "Is CTZ running?" → ctz_status_ctz
- "user request" → "MCP servers connected?" → ctz_status_mcp
- "user request" → "Full status check" → all three tools

## Notes
- Status checks are lightweight
- Can be automated with ctz-scheduler skill
- Alerts available for downtime
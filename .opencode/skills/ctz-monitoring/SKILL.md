---
name: ctz-monitoring
description: System monitoring using ctz_monitor_system/processes/disk tools
---

# CTZ Monitoring Skill

## When to Use
- Monitoring system performance metrics
- Tracking running processes
- Checking disk usage and health

## Available Tools
- ctz_monitor_system: Get CPU, memory, network stats
- ctz_monitor_processes: List and monitor running processes
- ctz_monitor_disk: Check disk usage and health

## Workflow
1. Use ctz_monitor_system for overall performance
2. Check specific processes with ctz_monitor_processes
3. Verify disk space with ctz_monitor_disk
4. Set up alerts for thresholds if needed

## Examples
- "user request" → "System performance?" → ctz_monitor_system
- "user request" → "What's running?" → ctz_monitor_processes
- "user request" → "Disk space left?" → ctz_monitor_disk
- "user request" → "Is server overloaded?" → ctz_monitor_system + ctz_monitor_processes

## Notes
- Real-time monitoring may impact performance
- Historical data available for trends
- Alerts can be configured via automation skill
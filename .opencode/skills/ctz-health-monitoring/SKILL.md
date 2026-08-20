---
name: ctz-health-monitoring
description: System health checks using ctz_health_check/db/memory tools
---

# CTZ Health Monitoring Skill

## When to Use
- Performing system health checks
- Monitoring database performance
- Checking memory usage

## Available Tools
- ctz_health_check: Run comprehensive system health check
- ctz_health_db: Check database connectivity and performance
- ctz_health_memory: Monitor memory usage and availability

## Workflow
1. Run ctz_health_check for overall system status
2. If issues detected, drill down with specific tools
3. Check database with ctz_health_db
4. Monitor memory with ctz_health_memory
5. Take corrective action if needed

## Examples
- "user request" → "How's the system?" → ctz_health_check
- "user request" → "Is database up?" → ctz_health_db
- "user request" → "Memory usage?" → ctz_health_memory
- "user request" → "Full diagnostic" → ctz_health_check + ctz_health_db + ctz_health_memory

## Notes
- Health checks may require permissions
- Some checks are real-time, others cached
- Alerts can be configured for critical issues
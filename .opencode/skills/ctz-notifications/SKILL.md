---
name: ctz-notifications
description: Desktop notifications using ctz_notify_desktop/log tools
---

# CTZ Notifications Skill

## When to Use
- Sending desktop notifications for important events
- Logging messages for audit trail
- Alerting user about completed tasks

## Available Tools
- ctz_notify_desktop: Send Windows toast notification
- ctz_notify_log: Write message to notification log

## Workflow
1. Determine notification urgency and content
2. Use ctz_notify_desktop for immediate alert
3. Log message with ctz_notify_log for history
4. Combine with voice if needed (via ctz-voice skill)

## Examples
- "user request" → "Alert me when done" → ctz_notify_desktop after task
- "user request" → "Log this event" → ctz_notify_log with message
- "user request" → "Notify with voice" → ctz_notify_desktop + ctz-voice skill

## Notes
- Desktop notifications require Windows notification permission
- Log files stored in designated directory
- Can be triggered by automation skill
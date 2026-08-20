---
name: ctz-comms
description: CHAOS TYPE ZERO communication hub — email, Slack, Discord, Telegram, webhooks
version: 1.0.0
---

# CTZ Comms — Communication MCP Skill

Multi-channel communication server for CHAOS TYPE ZERO.

## Channels

| Tool | Protocol | Config Key |
|---|---|---|
| `ctz_email_send` | SMTP | `smtp.*` |
| `ctz_email_read` | IMAP | `imap.*` |
| `ctz_email_list` | IMAP | `imap.*` |
| `ctz_slack_send` | Webhook POST | `slack_webhook` |
| `ctz_discord_send` | Webhook POST | `discord_webhook` |
| `ctz_telegram_send` | Bot API | `telegram_token` |
| `ctz_webhook_send` | Generic POST | per-call URL |
| `ctz_comms_log` | Local DB | — |
| `ctz_comms_history` | Local DB | — |

## Configuration

Edit `data/comms/config.json`:

```json
{
  "smtp": { "host": "smtp.example.com", "port": 587, "user": "...", "pass": "...", "tls": true },
  "imap": { "host": "imap.example.com", "port": 993, "user": "...", "pass": "...", "ssl": true },
  "slack_webhook": "https://hooks.slack.com/services/...",
  "discord_webhook": "https://discord.com/api/webhooks/...",
  "telegram_token": "123456:ABC..."
}
```

Credentials are stored locally in `data/comms/config.json` — never committed to git.

## Communication History

All outbound/inbound communications are logged to `data/comms/history.db` (SQLite).

Query with `ctz_comms_history`:
- Filter by `channel` (email, slack, discord, telegram, webhook)
- Filter by `direction` (inbound, outbound)
- Filter by `since` (ISO date)
- Limit results

## Workflows

### Send email
```
ctz_email_send(to="user@example.com", subject="Alert", body="System breach detected.")
```

### Read inbox
```
ctz_email_list(limit=5, search="UNSEEN")
ctz_email_read(uid="12345")
```

### Multi-channel alert
1. `ctz_slack_send(text="⚠ ALERT: ...")`
2. `ctz_discord_send(content="⚠ ALERT: ...")`
3. `ctz_telegram_send(chat_id="@ops", text="⚠ ALERT: ...")`
4. `ctz_email_send(to="admin@company.com", subject="ALERT", body="...")`
5. `ctz_comms_log(channel="alert", direction="outbound", recipient="multi", subject="System Alert", body="...", status="sent")`

### Generic webhook
```
ctz_webhook_send(url="https://target.com/api/notify", data={"event": "breach", "severity": "critical"})
```

## Notes

- All tools gracefully error when credentials are not configured
- History is persisted across restarts
- Supports HTML email via `html` parameter on `ctz_email_send`
- IMAP search uses standard IMAP search syntax (UNSEEN, SINCE, FROM, SUBJECT, etc.)

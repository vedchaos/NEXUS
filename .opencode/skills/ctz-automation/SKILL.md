# CHAOS TYPE ZERO Automation Skill

## What it does
Full automation engine — triggers, actions, chains, presets. Runs automations in background with SQLite persistence and run history.

## Trigger types
| Type | Config | Example |
|------|--------|---------|
| `interval` | `{seconds: N}` | Run every 60 seconds |
| `cron` | `{expression: "M H DoM Mon DoW"}` | Full 5-field cron: `0 22 * * *` = 10 PM daily |
| `file_change` | `{directory, pattern, check_interval}` | Watch folder for changes |
| `url_change` | `{url, check_interval}` | Monitor webpage for content changes |

## Action types
| Type | Params | What it does |
|------|--------|--------------|
| `shell` | `{command, timeout}` | Run shell command |
| `file_copy` | `{src, dst}` | Copy file |
| `file_cleanup` | `{directory, max_age_days, pattern}` | Delete old files |
| `api_call` | `{url, method, headers, body}` | HTTP request |
| `notify` | `{title, message, voice}` | Windows toast + optional voice |
| `llm_query` | `{prompt, task_type}` | Query LLM brain |
| `backup` | `{src, dst_dir}` | Backup file/dir with timestamp |
| `log` | `{message}` | Write to daily log |

## Presets (one-command setup)
| Preset | What it does | Params |
|--------|-------------|--------|
| `auto_backup` | Backup a path on schedule | `{src_path, interval_hours}` |
| `file_cleanup` | Delete old files daily | `{directory, max_age_days, pattern}` |
| `url_monitor` | Watch URL for changes | `{url}` |
| `daily_report` | LLM summary at 10 PM | `{}` |
| `health_check` | System health every N min | `{interval_minutes}` |

## MCP Tools (9 tools)
- `ctz_auto_create` — Create automation with trigger + actions
- `ctz_auto_list` — List all automations
- `ctz_auto_get` — Get automation by ID
- `ctz_auto_delete` — Delete automation
- `ctz_auto_enable` / `ctz_auto_disable` — Toggle
- `ctz_auto_run` — Trigger immediately
- `ctz_auto_preset` — Create from preset
- `ctz_auto_history` — Run history
- `ctz_auto_stats` — Engine stats

## Quick examples

### Auto-backup every 6 hours
```json
{"preset": "auto_backup", "params": {"src_path": "C:\\Projects\\myapp", "interval_hours": 6}}
```

### Custom: notify when URL changes
```json
{
  "name": "Price Monitor",
  "trigger_type": "url_change",
  "trigger_config": {"url": "https://example.com/prices", "check_interval": 300},
  "actions": [
    {"type": "notify", "params": {"title": "Price Alert", "message": "Prices changed!", "voice": true}}
  ]
}
```

### Custom: daily backup + cleanup + report chain
```json
{
  "name": "Daily Ops",
  "trigger_type": "cron",
  "trigger_config": {"expression": "0 23 * * *"},
  "actions": [
    {"type": "backup", "params": {"src": "C:\\Projects"}},
    {"type": "file_cleanup", "params": {"directory": "C:\\temp", "max_age_days": 3}},
    {"type": "llm_query", "params": {"prompt": "Summarize today's work", "task_type": "write"}},
    {"type": "notify", "params": {"title": "CHAOS TYPE ZERO", "message": "Daily ops done", "voice": true}}
  ]
}
```

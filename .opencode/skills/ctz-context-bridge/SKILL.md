---
name: ctz-context-bridge
description: Cross-session memory persistence — remember everything across sessions. Save context, restore context, manage key facts, link sessions.
---

# CTZ Context Bridge

Cross-session memory persistence. Never lose context between sessions.

## When to Use
- Starting a new session → restore relevant context
- Making a decision → save to context
- Learning a fact → save as key fact
- Finishing a session → end session with summary
- Related sessions → link them together

## MCP Tools

### Session Management
- `ctz_session_start` — Start tracking a new session
- `ctz_session_end` — End session with summary
- `ctz_session_list` — List recent sessions
- `ctz_session_link` — Link two related sessions

### Context Entries
- `ctz_context_save` — Save a decision, fact, outcome, preference, note, error, or insight
- `ctz_context_search` — Semantic search across all session context

### Key Facts
- `ctz_fact_save` — Save a fact that persists forever across all sessions
- `ctz_fact_search` — Search key facts semantically
- `ctz_fact_list` — List all key facts

### Context Restore
- `ctz_restore_context` — Restore everything relevant from past sessions for a new session

### Maintenance
- `ctz_compact` — Auto-compact old context and deactivate unused facts
- `ctz_bridge_stats` — Get statistics

## Workflow

### New Session
```
1. ctz_restore_context(query="what I'm working on") → get relevant past context
2. Start working with restored context
3. ctz_session_start(title="Session Title") → begin tracking
```

### During Session
```
ctz_context_save(session_id, "decision", "Chose X over Y because Z", importance=0.8)
ctz_fact_save(fact="User prefers dark mode", category="preference")
```

### End Session
```
ctz_session_end(session_id, summary="Built context bridge, tested successfully")
```

## Entry Types
| Type | When to save |
|------|-------------|
| decision | You made a choice |
| fact | You learned something |
| task_outcome | A task completed |
| preference | User preference |
| note | General note |
| error | Something failed |
| insight | Important realization |

## Categories for Facts
`project`, `config`, `preference`, `tool`, `person`, `location`, `general`

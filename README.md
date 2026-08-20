# CHAOS TYPE ZERO

> **C**omprehensive **H**ybrid **A**utonomous **O**perating **S**ystem — **Type Zero**

An autonomous AI operating system for independent developers, security researchers, and ML engineers. Self-healing, multi-provider, memory-aware, with full automation.

---

## What is CHAOS TYPE ZERO?

CHAOS TYPE ZERO (CTZ) is a personal AI agent that thinks, remembers, automates, and evolves. Built for devs who want an AI that actually works — not a chatbot.

### Core Powers

| Feature | What it does |
|---------|-------------|
| **14 LLM Providers** | Free-first with auto-fallback — NVIDIA, Groq, Mistral, Gemini, Ollama, and more |
| **3-Tier Memory** | RAM (instant) → SQLite (structured) → ChromaDB (semantic search) |
| **6-Agent Orchestrator** | Plan → Execute → Critique → Refine → Memory → Report |
| **9 MCP Servers** | Brain, Memory, Router, Security, Orchestrator, Voice, Vision, ML, Automation |
| **Automation Engine** | Triggers, actions, presets — backup, monitor, report, health check |
| **Security Module** | Kali Linux tools via WSL2 — Nmap, Nuclei, Nikto, SQLMap |
| **ML Pipeline** | Train, evaluate, deploy models locally with scikit-learn |
| **Voice & Vision** | Whisper STT, pyttsx3 TTS, Tesseract OCR, screenshot analysis |
| **Task Classifier** | Auto-routes 12 task types to optimal providers |
| **Hinglish Support** | Understands Hindi+English mixed input — "agle 5 minute mein backup lelo" |

---

## Quick Start

```bash
# Clone
git clone https://github.com/vedchaos/chaos-type-zero.git
cd NEXUS

# Install dependencies
pip install -r requirements.txt

# Copy env template and add API keys
cp config/.env.example config/.env
notepad config/.env

# Run full system test
python test_ctz.py

# Run v2 verification (voice, vision, ML, all 9 MCP servers)
python test_v2.py

# Run automation test
python test_automation.py
```

---

## Architecture

```
CHAOS TYPE ZERO/
├── SOUL_CTZ.md                    ← Agent identity (hot-reload)
├── bridge_core/                   ← Python modules (the brain)
│   ├── smart_brain.py            ← 14 LLM providers, 12 task chains, provider-specific adapters
│   ├── memory_3tier.py           ← RAM + SQLite + ChromaDB with deduplication
│   ├── agents.py                 ← 6-agent Sisyphus orchestrator (actually executes)
│   ├── task_classifier.py        ← 12 task types with Hinglish support
│   ├── scheduler.py              ← Full 5-field cron + Hinglish time parser
│   ├── recon.py                  ← Security scanning (sanitized inputs)
│   ├── voice.py                  ← Whisper STT + pyttsx3 TTS
│   ├── vision.py                 ← Screenshot + Tesseract OCR + auto-cleanup
│   ├── ml_pipeline.py            ← Train/Evaluate/Predict with scikit-learn
│   └── automation.py             ← Triggers, actions, chains, persistence
├── mcp_servers/                   ← 9 MCP tool servers
│   ├── llm_fallback.py          ← Brain MCP (ctz_query, ctz_brain_stats)
│   ├── memory_mcp.py            ← Memory MCP (ctz_memory_save/search/stats)
│   ├── task_router_mcp.py       ← Router MCP (ctz_route)
│   ├── pentest_mcp.py           ← Security MCP (ctz_scan_*)
│   ├── ctz_orchestrator_mcp.py  ← Orchestrator MCP (ctz_run/plan/execute/critique)
│   ├── voice_mcp.py             ← Voice MCP (ctz_voice_listen/speak/transcribe)
│   ├── vision_mcp.py            ← Vision MCP (ctz_vision_screenshot/ocr/analyze)
│   ├── ml_mcp.py                ← ML MCP (ctz_ml_train/evaluate/predict)
│   └── automation_mcp.py        ← Automation MCP (ctz_auto_create/list/run/preset)
├── .opencode/                     ← OpenCode integration
│   ├── agent/ctz.md             ← Agent identity
│   └── skills/                  ← 12 skill modules
│       ├── ctz-automation/      ← Automation workflows
│       ├── ctz-security/        ← Security scanning
│       ├── ctz-voice/           ← Voice interaction
│       ├── ctz-vision/          ← Visual perception
│       ├── ctz-ml/              ← Machine learning
│       ├── ctz-memory/          ← Memory management
│       ├── ctz-code-review/     ← Code review
│       ├── ctz-recon/           ← Reconnaissance
│       ├── ctz-scheduler/       ← Task scheduling
│       ├── ctz-git/             ← Git automation
│       ├── ctz-web/             ← Web interaction
│       └── ctz-deploy/          ← Deployment
├── config/
│   ├── .env.example             ← API key template (SMART_KEY auto-detect)
│   └── .env                     ← Your keys (gitignored)
├── data/                         ← Runtime data (gitignored)
│   ├── memory/                  ← SQLite + ChromaDB
│   ├── automation/              ← Automation DB + logs
│   └── screenshots/             ← Vision captures
├── test_ctz.py                   ← Core system test (5/5)
├── test_v2.py                    ← Full verification (9/9 MCP)
├── test_automation.py            ← Automation engine test
├── opencode.json                 ← OpenCode config (6 agents, 9 MCPs)
├── requirements.txt              ← Python dependencies (lean)
└── .gitignore                    ← Git exclusions
```

---

## LLM Providers (14)

| Provider | Free | Rate Limit | Use Case |
|----------|------|-----------|----------|
| NVIDIA NIM | Yes | 100/day | General |
| Groq | Yes | 1000/day | Speed |
| Mistral | Yes | 500/day | French, Code |
| Google Gemini | Yes | 1500/day | Multimodal |
| Together AI | Yes | 200/day | Open source |
| OpenRouter | Yes | 200/day | Multi-model |
| Cloudflare Workers AI | Yes | 10000/day | Edge |
| Cohere | Yes | 1000/day | Enterprise |
| HuggingFace Inference | Yes | 300/day | Open source |
| SambaNova | Yes | 100/day | Fast inference |
| Ollama | Yes | Unlimited | Local |
| DeepSeek | Cheap | 500/day | Code |
| OpenAI | Paid | 5000/day | GPT-4 |
| Anthropic | Paid | 1000/day | Claude |

**Free-first strategy**: CTZ tries free providers before paid. Ollama as last resort. API keys auto-detected from environment.

---

## Task Types (12)

| Type | Description | Preferred Providers |
|------|-------------|-------------------|
| code | Writing, debugging, reviewing | NVIDIA, Groq, DeepSeek |
| research | Information gathering | Gemini, Groq, Cohere |
| pentest | Security scanning | Groq, NVIDIA, Mistral |
| vision | Screenshot analysis, OCR | Gemini, OpenAI |
| hinglish | Hindi+English mixed input | Groq, NVIDIA, Ollama |
| write | Essays, articles, docs | Cohere, Gemini, Mistral |
| ml | Machine learning | Groq, NVIDIA, DeepSeek |
| data | Data analysis, SQL | Groq, NVIDIA, DeepSeek |
| voice | Speech-to-text | Groq, NVIDIA, Ollama |
| agent | Task automation | Groq, NVIDIA, Ollama |
| speed | Fastest response | Groq, NVIDIA, SambaNova |
| general | Default fallback | Ollama |

---

## Memory System

### 3-Tier Architecture

```
Tier 1: RAM (200 entries, <1ms)
├── LRU cache
├── Last 10 conversations
└── Current task context

Tier 2: SQLite (~5ms)
├── Task history
├── Structured queries
└── Scan results

Tier 3: ChromaDB (~50ms)
├── Semantic embeddings (all-MiniLM-L6-v2)
├── Natural language search
└── Long-term recall
```

### Smart Features
- **Deduplication**: Same memory stored in multiple tiers appears once in search results
- **Auto-compaction**: Memories older than 90 days with low importance auto-archived
- **Disk budget**: 1.5GB max for all memory data

---

## Automation Engine

### Triggers
| Type | Config | Example |
|------|--------|---------|
| `interval` | `{seconds: N}` | Run every 60 seconds |
| `cron` | `{expression: "M H DoM Mon DoW"}` | `0 22 * * *` = 10 PM daily |
| `file_change` | `{directory, pattern}` | Watch folder for changes |
| `url_change` | `{url, check_interval}` | Monitor webpage content |

### Actions (8 types)
`shell` · `file_copy` · `file_cleanup` · `api_call` · `notify` · `llm_query` · `backup` · `log`

### Presets (one-click)
| Preset | What it does |
|--------|-------------|
| `auto_backup` | Backup a path on schedule |
| `file_cleanup` | Delete old files daily |
| `url_monitor` | Watch URL for changes |
| `daily_report` | LLM summary at 10 PM |
| `health_check` | System health every N min |

---

## Security Module

### Tool Tiers

| Tier | Tools | Authorization |
|------|-------|--------------|
| Passive Recon | WHOIS, Dig, Sublist3r | Always safe |
| Active Scan | Nmap, Nikto, Gobuster | Auto-approved |
| Vuln Scan | Nuclei, WhatWeb | Auto-approved |
| Exploitation | SQLMap, Hydra, Metasploit | **Requires "authorized"** |

All user inputs sanitized with `sanitize_target()` + `shlex.quote()`. No `shell=True` on subprocess calls.

---

## Voice & Vision

### Voice
- **STT**: OpenAI Whisper (local, 4 model sizes)
- **TTS**: pyttsx3 (offline, instant)
- **Hinglish**: Understands mixed Hindi+English commands

### Vision
- **Screenshots**: Full screen or region capture via Pillow
- **OCR**: Tesseract for text extraction
- **Auto-cleanup**: Screenshots older than 7 days auto-deleted

---

## Usage with OpenCode

```bash
cd NEXUS
opencode
```

### Available Agents
| Agent | Role |
|-------|------|
| `ctz` | Primary agent (default) |
| `ctz-recon` | Reconnaissance specialist |
| `ctz-scan` | Vulnerability scanner |
| `ctz-exploit` | Exploitation (authorized only) |
| `ctz-ml` | Machine learning |
| `ctz-code` | Code review |

---

## Hardware Requirements

- **OS**: Windows 11 (ReviOS) / Linux (Kali WSL2)
- **CPU**: Intel i5 or better
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: NVIDIA (optional, for local LLM via Ollama)
- **Disk**: 2GB for CTZ + 1.5GB memory budget

---

## License

Personal use. Built by Ved for Ved.

---

*"The only way to deal with an unfree world is to become so absolutely free that your very existence is an act of rebellion." — Albert Camus*

# NEXUS

**N**eural **E**ngine for **X**enolithic **U**nified **S**ystems

> An autonomous AI operating system for independent developers, security researchers, and ML engineers.

---

## What is NEXUS?

NEXUS is a personal AI agent that combines:

- **14 LLM Providers** — Free-first with auto-fallback (NVIDIA, Groq, Mistral, Gemini, Ollama...)
- **3-Tier Memory** — RAM (instant) → SQLite (structured) → ChromaDB (semantic)
- **6-Agent Orchestrator** — Plan → Execute → Critique → Refine → Memory → Report
- **Security Module** — Kali Linux tools via WSL2 (Nmap, Nuclei, Nikto...)
- **ML Pipeline** — Train, evaluate, deploy models locally
- **Voice & Vision** — Whisper STT, OCR, screen reading
- **Task Classifier** — Auto-routes 12 task types to optimal providers
- **Hinglish Support** — understands Hindi+English mixed input

---

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/nexus.git
cd nexus

# Install dependencies
pip install -r requirements.txt

# Copy env template
cp config/.env.example config/.env

# Add your API keys
notepad config/.env

# Initialize memory
python bridge_core/memory_3tier.py

# Check system health
python bridge_core/smart_brain.py
```

---

## Architecture

```
NEXUS/
├── SOUL_NEXUS.md                 ← Agent identity (hot-reload)
├── bridge_core/                  ← Python modules (the brain)
│   ├── smart_brain.py           ← 14 LLM providers, 12 task chains
│   ├── memory_3tier.py          ← RAM + SQLite + ChromaDB
│   ├── agents.py                ← 6-agent Sisyphus orchestrator
│   ├── task_classifier.py       ← 12 task types
│   ├── recon.py                 ← Security scanning
│   └── scheduler.py             ← Hinglish time parser
├── mcp_servers/                  ← MCP tool servers
│   ├── llm_fallback.py         ← Brain MCP
│   ├── memory_mcp.py           ← Memory MCP
│   ├── task_router_mcp.py      ← Router MCP
│   ├── pentest_mcp.py          ← Security MCP
│   └── m4st_agent_mcp.py       ← Orchestrator MCP
├── .opencode/                    ← OpenCode integration
│   ├── agents/                  ← Agent definitions
│   ├── skills/                  ← Skill modules
│   ├── plugins/                 ← Auto-logging plugins
│   └── commands/                ← Quick commands
├── config/                       ← Configuration
│   ├── opencode.json            ← OpenCode config
│   └── .env.example             ← API key template
├── data/                         ← Runtime data (gitignored)
│   ├── cache/                   ← LLM response cache
│   ├── memory/                  ← SQLite + ChromaDB
│   └── logs/                    ← Execution logs
├── requirements.txt              ← Python dependencies
└── .gitignore                    ← Git exclusions
```

---

## LLM Providers (14)

| Provider | Free | Rate Limit | Use Case |
|---|---|---|---|
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

---

## Task Types (12)

| Type | Description | Preferred Provider |
|---|---|---|
| code | Writing, debugging, reviewing code | NVIDIA, Groq, DeepSeek |
| research | Information gathering, web search | Gemini, Groq, Cohere |
| pentest | Security scanning, vulnerability assessment | Groq, NVIDIA, Mistral |
| vision | Screenshot analysis, OCR | Gemini, OpenAI |
| hinglish | Hindi+English mixed input | Groq, NVIDIA, Ollama |
| write | Essays, articles, documentation | Cohere, Gemini, Mistral |
| ml | Machine learning, model training | Groq, NVIDIA, DeepSeek |
| data | Data analysis, SQL, visualization | Groq, NVIDIA, DeepSeek |
| voice | Speech-to-text, audio processing | Groq, NVIDIA, Ollama |
| agent | Task automation, orchestration | Groq, NVIDIA, Ollama |
| speed | Fastest possible response | Groq, NVIDIA, SambaNova |
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
├── Semantic embeddings
├── Natural language search
└── Long-term recall
```

### Auto-Compaction
- Memories older than 90 days with low importance: auto-archived
- High-access memories: promoted from RAM to SQLite
- Disk budget: 1.5GB max for all memory data

---

## Security Module

### Tool Tiers

| Tier | Tools | Authorization |
|---|---|---|
| Passive Recon | WHOIS, Dig, Sublist3r | Always safe |
| Active Scan | Nmap, Nikto, Gobuster | Auto-approved |
| Vuln Scan | Nuclei, WhatWeb | Auto-approved |
| Exploitation | SQLMap, Hydra, Metasploit | **Requires "authorized"** |

### WSL2 Kali Linux
All tools available via WSL2:
```bash
wsl -d kali-linux -- nmap -sV target.com
wsl -d kali-linux -- nuclei -u target.com
```

---

## Voice & Vision

### Whisper Models
| Model | VRAM | Speed | Accuracy |
|---|---|---|---|
| tiny | ~1GB | Fastest | Low |
| base | ~1GB | Fast | Good |
| small | ~2GB | Medium | Better |
| medium | ~5GB | Slow | High |

### Screen Reading
- Full screen OCR via Tesseract
- Region capture and analysis
- Screenshot-to-text pipeline

---

## Usage with OpenCode

```bash
cd nexus
opencode
```

### Available Agents
- `nexus` — Primary agent (default)
- `nexus-recon` — Reconnaissance specialist
- `nexus-scan` — Vulnerability scanner
- `nexus-exploit` — Exploitation (authorized only)
- `nexus-ml` — Machine learning
- `nexus-code` — Code review

---

## License

Personal use. Built by Ved for Ved.

---

*"The only way to deal with an unfree world is to become so absolutely free that your very existence is an act of rebellion." — Albert Camus*

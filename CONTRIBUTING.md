# 🤝 Contributing to CHAOS TYPE ZERO

> Thanks for wanting to contribute! Here's how to get started.

## 🚀 Quick Start

```bash
# 1. Fork the repo
# 2. Clone your fork
git clone https://github.com/vedchaos/chaos-type-zero.git

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a branch
git checkout -b feature/your-feature

# 5. Make your changes

# 6. Run tests
pytest tests/ -v

# 7. Commit
git commit -m "feat: your feature description"

# 8. Push
git push origin feature/your-feature

# 9. Create PR on GitHub
```

---

## 📁 Project Structure

```
chaos-type-zero/
├── bridge_core/          # Core AI modules (18 modules)
│   ├── smart_brain.py    # Multi-provider LLM orchestration
│   ├── memory_3tier.py   # RAM + SQLite + ChromaDB memory
│   ├── heuristics.py     # Risk scoring, pattern learning
│   ├── meta_reasoner.py  # Adaptive routing, strategy selection
│   └── ...
├── mcp_servers/          # MCP tool servers (40 servers)
│   ├── browser_mcp.py    # Browser automation
│   ├── nse_mcp.py        # Security scanning
│   └── ...
├── skills/               # Agent skills (31 skills)
├── agents/               # Agent configurations
├── tests/                # Unit tests
├── dashboard/            # Web dashboard
├── docker/               # Docker deployment
└── opencode.json         # Main config
```

---

## 🎯 Ways to Contribute

### 1. 🐛 Bug Fixes
- Found a bug? Open an issue first
- Then fix it and submit a PR

### 2. ✨ New Features
- New MCP server? Great!
- New skill? Awesome!
- New provider? Perfect!

### 3. 📚 Documentation
- Fix typos
- Add examples
- Improve guides

### 4. 🧪 Tests
- Add missing tests
- Improve test coverage
- Integration tests

---

## 📝 Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new MCP server for Discord
fix: memory leak in context bridge
docs: update README with new features
test: add tests for heuristics engine
refactor: simplify smart brain logic
```

---

## 🔧 Development Setup

### Prerequisites
- Python 3.10+
- Ollama (optional, for local LLMs)
- Git

### Install
```bash
# Clone
git clone https://github.com/vedchaos/chaos-type-zero.git
cd chaos-type-zero

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start dashboard
python dashboard/server.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_smart_brain.py -v

# Run with coverage
pytest tests/ --cov=bridge_core

# Run tests matching pattern
pytest tests/ -k "memory"
```

---

## 📋 Pull Request Checklist

- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Works on Windows + Linux
- [ ] Commit messages follow convention

---

## 🎨 Style Guide

- **Python:** PEP 8 compliant
- **Naming:** snake_case for functions, PascalCase for classes
- **Docstrings:** Google style
- **Type hints:** Always use them

```python
def smart_brain(task: str, context: dict) -> dict:
    """Process task through smart brain.
    
    Args:
        task: The task to process
        context: Additional context
        
    Returns:
        dict with response and metadata
    """
    pass
```

---

## 🔐 Security

**DO NOT** commit:
- API keys
- Passwords
- Tokens
- Personal information

If you find a security vulnerability, email: [your-email]

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 💬 Questions?

- Open an issue
- Start a discussion
- DM on Twitter: @vedchaos

---

**Jai Hind! 🇮🇳**

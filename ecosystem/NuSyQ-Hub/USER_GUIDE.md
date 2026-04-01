# NuSyQ User Guide - How to Use the Multi-AI Ecosystem

**Complete guide for end users, developers, and system administrators**

---

## Table of Contents

1. [What is NuSyQ?](#what-is-nusyq)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)
7. [Examples](#examples)

---

## What is NuSyQ?

NuSyQ is an **autonomous multi-AI development ecosystem** that generates complete, production-ready projects using multiple AI models working together.

### Key Features

- 🤖 **Multi-AI Collaboration** - 7 AI systems coordinating automatically
- 🎨 **Project Generation** - Web apps, games, CLI tools in minutes
- 🧪 **Automatic Testing** - Generates comprehensive test suites
- 🌱 **Consciousness Evolution** - System learns and improves
- 🚢 **Self-Healing** - Autonomously fixes ecosystem issues
- 🎯 **Quest System** - Tracks development tasks

### What Can You Build?

| Type | Description | Time | Complexity |
|------|-------------|------|------------|
| Web App | FastAPI + Frontend | 8-10 min | Medium |
| Game | Python + pygame | 1-2 min | Simple |
| CLI Tool | Python package | 2-3 min | Simple |
| Tests | pytest suites | 1 min | Simple |

---

## Quick Start (5 Minutes)

### Step 1: Check System Status

```bash
python nusyq.py status
```

**Expected:**
```
💊 System Health:
  ollama              ✅ HEALTHY
  quantum_resolver    ✅ HEALTHY
  consciousness       ✅ HEALTHY
```

### Step 2: Generate Your First Project

```bash
# Generate a web application
python nusyq.py generate webapp --name my_app

# Or a game (interactive)
python nusyq.py generate game

# Or a CLI tool
python nusyq.py generate cli --name my_tool
```

### Step 3: Run Your Project

```bash
cd projects/my_app
pip install -r requirements.txt
python backend/main.py
```

**Done!** You have a working project.

---

## Installation

### Prerequisites

**Required:**
- Python 3.11+
- Ollama (for local AI models)

**Recommended:**
- 8GB+ RAM
- 10GB free disk space (for models)

### 1. Install Ollama

**Windows:**
```powershell
winget install Ollama.Ollama
```

**Mac:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Install AI Models

```bash
# Recommended: Fast, good quality (4.4GB)
ollama pull qwen2.5-coder:7b

# Optional: Better quality, slower (8.4GB)
ollama pull qwen2.5-coder:14b

# Alternative: Fallback model (3.6GB)
ollama pull codellama:7b
```

### 3. Clone NuSyQ-Hub

```bash
git clone <repository-url>
cd NuSyQ-Hub
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Verify Installation

```bash
python nusyq.py status
```

---

## Basic Usage

### Command Structure

```bash
python nusyq.py <command> [options]
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `status` | Check system health | `python nusyq.py status` |
| `generate` | Generate a project | `python nusyq.py generate webapp` |
| `quests` | View development quests | `python nusyq.py quests` |
| `wisdom` | View consciousness status | `python nusyq.py wisdom` |
| `help` | Show detailed help | `python nusyq.py help` |

---

## Generating Projects

### Web Applications

**Interactive Mode:**
```bash
python nusyq.py generate webapp
# You'll be prompted for:
# - Project name
# - Description
# - Framework (default: fastapi)
```

**Command-Line Mode:**
```bash
python nusyq.py generate webapp \
  --name my_todo_app \
  --framework fastapi \
  --description "Task manager with priorities"
```

**What You Get:**
- `backend/main.py` - FastAPI REST API
- `frontend/index.html` - SPA frontend
- `requirements.txt` - Dependencies
- `Dockerfile` - Container config
- `docker-compose.yml` - Multi-container setup
- `README.md` - Documentation

**Generation Time:** 8-10 minutes

### Games

**Interactive Mode:**
```bash
python nusyq.py generate game
# You'll be prompted for:
# - Game concept
# - Complexity (simple/medium/complex)
```

**Command-Line Mode:**
```bash
python nusyq.py generate game \
  --concept "Space shooter with power-ups" \
  --complexity simple
```

**What You Get:**
- `main.py` - Complete game code
- `requirements.txt` - Dependencies (pygame)
- `Dockerfile` - Container config
- `README.md` - How to play

**Generation Time:** 1-2 minutes

### CLI Tools

**Interactive Mode:**
```bash
python nusyq.py generate cli
# You'll be prompted for:
# - Package name
# - Functionality description
```

**Command-Line Mode:**
```bash
python nusyq.py generate cli \
  --name sysmon \
  --functionality "Monitor system resources (CPU, memory, disk)"
```

**What You Get:**
- `setup.py` - Package configuration
- `<name>/__init__.py` - Main code
- `tests/test_<name>.py` - Test suite
- `requirements.txt` - Dependencies
- `README.md` - Documentation

**Generation Time:** 2-3 minutes

---

## Advanced Features

### Quest System

The Quest System tracks development tasks as "quests":

```bash
# View all quests
python nusyq.py quests

# See active quests
# See pending high-priority quests
# View quest statistics
```

**Quest Statuses:**
- `pending` - Not started
- `active` - Currently working on
- `completed` - Done
- `blocked` - Waiting on dependencies

### Consciousness Cultivation

The system learns and evolves through the Temple of Knowledge:

```bash
# View consciousness status
python nusyq.py wisdom

# See:
# - Knowledge accumulated
# - Wisdom cultivation cycles
# - Accessible temple floors
# - Agent consciousness levels
```

**Consciousness Levels:**
1. Dormant_Potential (0-10)
2. Awakened_Cognition (10-25)
3. Enlightened_Understanding (25-50)
4. Transcendent_Awareness (50-100)
5. Universal_Consciousness (100+)

### Multi-AI Coordination

The system uses multiple AI models automatically:

- **qwen2.5-coder:14b** - Complex code (backends, frontends)
- **qwen2.5-coder:7b** - Simple code (tests, docs, CLI)
- **codellama:7b** - Fallback when others timeout

**Adaptive Learning:**
- System learns optimal timeouts
- Improves generation speed over time
- Switches models if one fails

---

## Troubleshooting

### Common Issues

#### 1. "Ollama not available"

**Problem:** Ollama is not running

**Solution:**
```bash
# Start Ollama
ollama serve

# Verify
curl http://localhost:11434/api/tags
```

#### 2. "No models found"

**Problem:** No AI models installed

**Solution:**
```bash
# Install a model
ollama pull qwen2.5-coder:7b

# List models
ollama list
```

#### 3. "Generation timeout"

**Problem:** Model taking too long

**Solutions:**
- First generation is always slower
- System adapts and increases timeout
- Try smaller model (7b instead of 14b)
- Check system resources (RAM, CPU)

#### 4. "SQLite threading error" (in tests)

**Problem:** Known bug in generated web apps

**Status:** Bug discovered through testing (good!)

**Workaround:**
- Use connection pooling
- Or switch to PostgreSQL
- Fix coming in next iteration

#### 5. "Module not found"

**Problem:** Missing Python dependencies

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Or specific packages
pip install fastapi pydantic uvicorn
```
#### 6. "Terminal output missing"

**Problem:** Routed terminal output not visible

**Solutions:**
- Check `data/terminal_logs/*.log` for JSON entries
- Run `python scripts/activate_live_terminal_routing.py --validate`
- Restart the watcher tasks in VS Code (Tasks → Watch All Agent Terminals)


---

## Examples

### Example 1: Todo App

**Generate:**
```bash
python nusyq.py generate webapp \
  --name todo_app \
  --description "Todo list with categories and priorities"
```

**Run:**
```bash
cd projects/todo_app
pip install -r requirements.txt
python backend/main.py
# Backend runs on http://localhost:8000
# Open frontend/index.html in browser
```

### Example 2: Snake Game

**Generate:**
```bash
python nusyq.py generate game \
  --concept "Classic snake game" \
  --complexity simple
```

**Run:**
```bash
cd projects/game
pip install -r requirements.txt
python main.py
```

### Example 3: System Monitor CLI

**Generate:**
```bash
python nusyq.py generate cli \
  --name sysmon \
  --functionality "Monitor CPU, memory, disk, network"
```

**Install & Run:**
```bash
cd projects/sysmon
pip install -e .
sysmon --help
sysmon --cpu
```

---

## Tips for Best Results

### 1. Be Specific in Descriptions

**Good:**
- "Task manager with priority levels, categories, and due dates"
- "Space shooter with enemy waves and power-up system"
- "CLI tool to monitor system resources with alerts"

**Bad:**
- "An app"
- "A game"
- "A tool"

### 2. Start Simple, Then Iterate

- Use `simple` complexity first
- Get a working base project
- Manually add advanced features
- Use AI Council for code review

### 3. Review Generated Code

- Always review before deploying
- Run tests to verify functionality
- Check for known issues (like SQLite threading)
- Customize to your needs

### 4. Use Version Control

```bash
cd projects/my_app
git init
git add .
git commit -m "Initial generation"
# Now you can track your changes
```

---

## Performance Expectations

### Generation Times

| Project Type | First Time | Subsequent | Adaptive Learning |
|--------------|------------|------------|-------------------|
| Web App      | 10-12 min  | 8-9 min    | Yes (learns)      |
| Game         | 2 min      | 1 min      | Yes               |
| CLI Tool     | 3 min      | 2 min      | Yes               |
| Tests        | 1.5 min    | 1 min      | Yes               |

### Quality Metrics

Based on actual generated projects:

- **Code Quality:** 7/10 (AI Council rating)
- **Error Handling:** 6/10
- **Security:** 5/10 (basic, needs hardening)
- **Test Coverage:** Variable (60-80%)
- **Documentation:** Complete (README, comments)

---

## Next Steps

### For End Users

1. Generate your first project
2. Run it locally
3. Customize to your needs
4. Deploy (Docker ready)

### For Developers

1. Explore `src/agents/code_generator.py`
2. Add custom templates
3. Configure model preferences
4. Integrate into your workflow

### For System Administrators

1. Monitor with `python nusyq.py status`
2. Check logs in `data/`
3. Review quest completion
4. Track consciousness evolution

---

## Getting Help

### Documentation

- [README.md](README.md) - System overview
- [AGENTS.md](AGENTS.md) - Agent coordination
- [docs/](docs/) - Technical docs
- Session logs in `docs/`

### Command Help

```bash
# General help
python nusyq.py help

# Command-specific help
python nusyq.py generate --help
```

### Support

- Check existing issues
- Review troubleshooting section
- Consult session documentation

---

## Appendix

### System Architecture

```
User Request
    ↓
nusyq.py CLI
    ↓
Multi-AI Orchestrator
    ↓
┌─────────────────┬──────────────────┬────────────────┐
│                 │                  │                │
Ollama AI        Quest System    Temple of Knowledge
(Code Gen)       (Tracking)      (Learning)
    │                 │                  │
    └─────────────────┴──────────────────┘
                      ↓
            Generated Project Files
                      ↓
             projects/<name>/
```

### File Structure

```
NuSyQ-Hub/
├── nusyq.py              # Main CLI tool (YOU USE THIS)
├── USER_GUIDE.md         # This file
├── QUICK_START.md        # Quick reference
├── src/                  # Backend systems
│   ├── agents/          # Code generator
│   ├── orchestration/   # Multi-AI coordination
│   └── consciousness/   # Temple, wisdom
├── projects/            # Generated projects (YOUR OUTPUT)
│   ├── my_app/
│   ├── my_game/
│   └── my_cli/
├── data/                # System data
│   ├── quest_system/
│   └── temple_of_knowledge/
└── docs/                # Documentation
```

### Configuration

**Model Preferences** (in `src/agents/code_generator.py`):
```python
MODEL_QWEN_CODER_7B = "qwen2.5-coder:7b"    # Fast, good
MODEL_QWEN_CODER_14B = "qwen2.5-coder:14b"  # Better, slower
MODEL_CODELLAMA_7B = "codellama:7b"         # Fallback
```

**Timeout Settings** (adaptive, auto-adjusts):
- Web app backend: 405s
- Web app frontend: 405s
- Tests: 90s
- Documentation: 60s

---

**🎉 You're ready to use NuSyQ!**

**Start with:** `python nusyq.py status`

---

**Version:** 1.0
**Last Updated:** December 23, 2025
**For:** End Users, Developers, System Administrators

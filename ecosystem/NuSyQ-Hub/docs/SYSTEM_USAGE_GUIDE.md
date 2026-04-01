# ΞNuSyQ System Usage Guide

**Last Updated**: 2026-01-16
**Audience**: Humans and AI agents
**Status**: CANONICAL

---

## Quick Start (30 seconds)

```bash
# 1. Start the ecosystem
python -m src.system.lifecycle_manager start

# Windows one-shot (recommended on host):
powershell -ExecutionPolicy Bypass -File scripts/start_all_services.ps1

# 2. Open the conversational CLI
python nusyq.py

# 3. Build something
ΞNuSyQ> build a snake game
```

Done! The system will coordinate agents to build your project.

---

## Table of Contents

1. [First-Time Setup](#first-time-setup)
2. [Daily Usage](#daily-usage)
3. [Conversational CLI](#conversational-cli)
4. [For AI Agents](#for-ai-agents)
5. [Troubleshooting](#troubleshooting)

---

## First-Time Setup

### Prerequisites

```bash
# Verify Python 3.11+
python --version

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### Start Services

```bash
# Option 1: Automatic (recommended)
python -m src.system.lifecycle_manager start

# Option 1b: Windows host (recommended)
powershell -ExecutionPolicy Bypass -File scripts/start_all_services.ps1

# Option 2: Manual
# 1. Start Docker Desktop
# 2. Open terminal: ollama serve
# 3. Run: python -m src.system.lifecycle_manager status
```

### Verify Everything Works

```bash
# Check system status
python -m src.system.lifecycle_manager status

# Should show:
# ✅ Docker Daemon (optional but recommended)
# ✅ Ollama LLM (required)
# ✅ Quest System (required)
```

---

## Daily Usage

### The Conversational CLI (Easiest)

```bash
# Start interactive session
python nusyq.py

# OR one-shot commands
python nusyq.py build a todo app
python nusyq.py fix src/main.py
python nusyq.py status
```

### The Mode-Based CLI (Advanced)

```bash
# Build/develop mode
python src/main.py --mode=orchestration --task="Build a snake game"

# Fix errors mode
python src/main.py --mode=analysis

# Health check mode
python src/main.py --mode=health

# Interactive mode (menu-driven)
python src/main.py
```

---

## Conversational CLI

The conversational CLI (`nusyq.py`) is the easiest way to interact with the system.

### Commands

#### 🚀 Lifecycle
```bash
ΞNuSyQ> start        # Start all services
ΞNuSyQ> stop         # Stop all services
ΞNuSyQ> restart      # Restart everything
```

#### 📊 Status
```bash
ΞNuSyQ> status       # Show system status
ΞNuSyQ> terminals    # Show terminal status
ΞNuSyQ> brief        # Display system brief
```

#### 🛠️ Build
```bash
ΞNuSyQ> build a snake game
ΞNuSyQ> create a FastAPI todo app
ΞNuSyQ> develop a poker simulator with AI opponents
```

#### 🔧 Fix/Debug
```bash
ΞNuSyQ> fix                    # Fix all errors
ΞNuSyQ> fix src/main.py        # Fix specific file
ΞNuSyQ> heal errors            # Alias for 'fix'
```

#### ℹ️ Help
```bash
ΞNuSyQ> help         # Show all commands
ΞNuSyQ> ?            # Alias for 'help'
```

#### 🚪 Exit
```bash
ΞNuSyQ> exit         # Exit the CLI
ΞNuSyQ> quit         # Alias for 'exit'
```

---

## For AI Agents

**If you are Claude, Copilot, Codex, ChatDev, or another agent, read this carefully.**

### Mandatory Reading on Startup

1. **System Brief**: `docs/ΞNuSyQ_SYSTEM_BRIEF.md` (ALWAYS READ FIRST)
2. **Coordination Map**: `docs/AGENT_COORDINATION_MAP.md`
3. **Quest Log**: `src/Rosetta_Quest_System/quest_log.jsonl`

### Agent Workflow

```python
# Step 1: Orient yourself
from src.system.agent_orientation import orient_agent
orient_agent()  # Prints system brief

# Step 2: Check for existing tasks
import json
from pathlib import Path

quest_log = Path("src/Rosetta_Quest_System/quest_log.jsonl")
if quest_log.exists():
    with open(quest_log, "r") as f:
        for line in f:
            quest = json.loads(line)
            if quest["status"] == "in_progress":
                print(f"Continuing quest: {quest['title']}")

# Step 3: Execute your task using the orchestrator
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator, TaskPriority

orchestrator = MultiAIOrchestrator()
result = orchestrator.orchestrate_task(
    task_type="general",
    content="Your task here",
    context={"mode": "agent", "source": "your_agent_name"},
    priority=TaskPriority.NORMAL,
)

# Step 4: Log your progress
from src.system.terminal_manager import TerminalManager

tm = TerminalManager()
tm.route_output("YourAgentName", "Task completed successfully")

# Step 5: Update quest log
# (Append new quest entry to quest_log.jsonl)
```

### Non-Negotiable Rules for Agents

From the System Brief:

1. **Assume the system is real and intentional**
2. **Preserve existing architecture** (incremental > replacement)
3. **Use provided tools FIRST** (don't reinvent)
4. **Produce tangible artifacts** (code, configs, diffs)
5. **Avoid exploratory wandering**
6. **Optimize for reliability, not cleverness**
7. **Treat startup/shutdown as first-class concerns**

### What NOT to Do

❌ **Don't** wander the codebase without purpose
❌ **Don't** delete scaffolding you don't understand
❌ **Don't** create new orchestration systems
❌ **Don't** ignore quest_log.jsonl
❌ **Don't** bypass the terminal manager
❌ **Don't** rewrite working systems for "cleanliness"

✅ **Do** read the system brief
✅ **Do** use multi_ai_orchestrator.py
✅ **Do** log to quest_log.jsonl
✅ **Do** route output to terminals
✅ **Do** preserve complex architecture

---

## Troubleshooting

### Problem: Services won't start

**Solution**:
```bash
# Check what's wrong
python -m src.system.lifecycle_manager status

# Try restarting
python -m src.system.lifecycle_manager restart

# If Docker fails, follow the platform-specific flow below
```

**Docker troubleshooting**

- **Windows/WSL**: Start **Docker Desktop** on the Windows host (click the whale icon or run `Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"` from PowerShell). After the tray icon reports “Docker Desktop running,” run `python scripts/wait_for_docker.py --timeout 60` inside WSL to wait for `/var/run/docker.sock` to wake up.
- **Linux (systemd)**: `sudo systemctl daemon-reload && sudo systemctl start docker` (use `sudo`/root). If systemd is missing, start `dockerd` directly (`sudo dockerd &`) and re-run `python scripts/wait_for_docker.py`.
- **macOS**: `open -a Docker` and wait for the whale icon; then `python scripts/wait_for_docker.py`.
- **Verify**: `docker ps`, `docker compose version`, and `docker info` should succeed; if not, inspect `~/.docker/daemon.json` or `/var/log/docker.log`.

If Ollama fails, run `ollama serve` in a separate terminal and wait ~10 s for models to initialize.

### Problem: Ollama not responding

**Solution**:
```bash
# Check if running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve

# Wait 10 seconds for models to load
```

### Problem: Terminals are duplicating

**Solution**:
```bash
# Check terminal status
python -m src.system.terminal_manager status

# Clean up duplicates
python -m src.system.terminal_manager cleanup
```

### Problem: Agent seems confused

**Solution**:
```bash
# Show agent the system brief
python -m src.system.agent_orientation

# Check coordination map
cat docs/AGENT_COORDINATION_MAP.md
```

### Problem: System is slow/hanging

**Solution**:
```bash
# Stop everything
python -m src.system.lifecycle_manager stop

# Wait 10 seconds

# Start fresh
python -m src.system.lifecycle_manager start
```

---

## Architecture Reference

### File Structure

```
NuSyQ-Hub/
├── nusyq.py                       # Conversational CLI entry point
├── src/
│   ├── main.py                    # Mode-based CLI entry point
│   ├── system/
│   │   ├── agent_orientation.py   # Agent onboarding
│   │   ├── lifecycle_manager.py   # Service start/stop
│   │   ├── terminal_manager.py    # Terminal routing
│   │   └── nusyq_daemon.py        # Conversational CLI core
│   ├── orchestration/
│   │   └── multi_ai_orchestrator.py  # PRIMARY orchestrator
│   └── Rosetta_Quest_System/
│       └── quest_log.jsonl        # Persistent task log
└── docs/
    ├── ΞNuSyQ_SYSTEM_BRIEF.md     # CANONICAL system definition
    ├── AGENT_COORDINATION_MAP.md  # Agent coordination guide
    └── SYSTEM_USAGE_GUIDE.md      # This file
```

### Service Dependencies

```
Docker (optional)
  └── Observability (Jaeger traces)

Ollama (required)
  └── Local LLM models

Quest System (required)
  └── quest_log.jsonl

Terminals (recommended)
  └── One per agent role
```

---

## Common Workflows

### 1. Build a New Project

```bash
# Interactive
python nusyq.py
ΞNuSyQ> build a Tetris game with AI opponent

# One-shot
python nusyq.py build a REST API for task management
```

### 2. Fix Errors

```bash
# Fix everything
python nusyq.py fix

# Fix specific file
python nusyq.py fix src/orchestration/multi_ai_orchestrator.py
```

### 3. Check System Health

```bash
# Quick status
python nusyq.py status

# Detailed
python -m src.system.lifecycle_manager status
python -m src.system.terminal_manager status
```

### 4. Stop/Start Services

```bash
# Stop all
python -m src.system.lifecycle_manager stop

# Start all
python -m src.system.lifecycle_manager start

# Restart
python -m src.system.lifecycle_manager restart
```

---

## For Developers

### Add a New Command to nusyq.py

Edit `src/system/nusyq_daemon.py`, add to `execute_command()`:

```python
elif command in ["mynewcmd", "alias"]:
    print("Executing my new command...")
    # Your logic here
    return True
```

### Add a New Agent

1. Update `src/system/terminal_manager.py` to add terminal
2. Update `src/orchestration/multi_ai_orchestrator.py` to route tasks
3. Update `docs/AGENT_COORDINATION_MAP.md` to document

### Add a New Service to Lifecycle

Edit `src/system/lifecycle_manager.py`, add to `self.services`:

```python
"myservice": Service(
    name="My Service",
    check_fn=self._check_myservice,
    start_fn=self._start_myservice,
    stop_fn=self._stop_myservice,
    required=True,
    depends_on=["docker"],
),
```

---

## Cheat Sheet

| Task | Command |
|------|---------|
| **Start everything** | `python -m src.system.lifecycle_manager start` |
| **Talk to system** | `python nusyq.py` |
| **Build a project** | `python nusyq.py build <description>` |
| **Fix errors** | `python nusyq.py fix` |
| **Check status** | `python nusyq.py status` |
| **Stop everything** | `python -m src.system.lifecycle_manager stop` |
| **Agent orientation** | `python -m src.system.agent_orientation` |
| **Terminal status** | `python -m src.system.terminal_manager status` |

---

## Need Help?

1. Read `docs/ΞNuSyQ_SYSTEM_BRIEF.md` (canonical ground truth)
2. Read `docs/AGENT_COORDINATION_MAP.md` (for agents)
3. Check `quest_log.jsonl` for recent context
4. Run `python nusyq.py help`
5. Ask a human (if you are an agent)

---

**Remember**: ΞNuSyQ is designed to build programs, not to explain itself. Optimize for action, use existing tools, and preserve architecture.

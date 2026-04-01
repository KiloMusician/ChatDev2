# 🎯 Terminal Routing Guide - Using Your 16 Specialized Terminals

## Overview

You have **16 themed terminals** that are currently underutilized. Each terminal
has specific routing keywords and purposes. By routing commands to the right
terminal, you get:

- ✅ **Clean separation** of concerns (errors vs tests vs metrics)
- ✅ **Persistent sessions** (terminals stay open across restarts)
- ✅ **Visual organization** (emoji icons make scanning easy)
- ✅ **Contextual output** (error logs in Error terminal, test results in Tests
  terminal)

## Your 16 Terminals

### 🤖 AI Agent Terminals (6 terminals)

| Terminal            | Purpose                | Route Keywords                                               | Example                         |
| ------------------- | ---------------------- | ------------------------------------------------------------ | ------------------------------- |
| **🤖 Claude**       | Claude agent execution | `claude`, `anthropic`, `sonnet`, `claude_code`               | Code generation, analysis       |
| **🧩 Copilot**      | GitHub Copilot         | `copilot`, `github_copilot`, `gh_copilot`                    | Suggestions, completions        |
| **🧠 Codex**        | OpenAI Codex           | `codex`, `openai_codex`, `gpt_code`, `gpt`                   | Transformations, migrations     |
| **🏗️ ChatDev**      | Multi-agent team       | `chatdev`, `chat dev`, `multi_agent`, `software_company`     | CEO, CTO, Designer, Coder teams |
| **🏛️ AI Council**   | Consensus voting       | `council`, `ai_council`, `consensus`, `deliberation`, `vote` | Multi-model decisions           |
| **🔗 Intermediary** | Cross-agent comms      | `intermediary`, `router`, `bridge`, `coordinator`, `handoff` | Agent-to-agent messaging        |

### 🛠️ Operational Terminals (10 terminals)

| Terminal           | Purpose             | Route Keywords                                             | Example                   |
| ------------------ | ------------------- | ---------------------------------------------------------- | ------------------------- |
| **🔥 Errors**      | Error monitoring    | `error`, `exception`, `failed`, `stderr`, `traceback`      | All exceptions, failures  |
| **💡 Suggestions** | Next steps          | `suggest`, `recommend`, `next_steps`, `hint`, `todo`       | AI recommendations        |
| **✅ Tasks**       | Work queue          | `task`, `pu_queue`, `work_queue`, `processing`, `job`      | PU processing, jobs       |
| **🧪 Tests**       | Test execution      | `pytest`, `tests/`, `test suite`, `coverage`, `xfailed`    | All test runs             |
| **🎯 Zeta**        | Autonomous ops      | `zeta`, `autonomous`, `orchestrat`, `cycle`, `meta`        | Zeta orchestration        |
| **🤖 Agents**      | Multi-agent coord   | `agent`, `ai_`, `ollama`, `multi-agent`                    | Agent coordination        |
| **📊 Metrics**     | Health monitoring   | `metric`, `health`, `dashboard`, `monitor`, `stats`        | System health, dashboards |
| **⚡ Anomalies**   | Unusual events      | `anomaly`, `orphan`, `unexpected`, `zombie`, `leak`        | Orphaned processes        |
| **🔮 Future**      | Development roadmap | `future`, `planned`, `roadmap`, `upcoming`, `vision`       | Future features           |
| **🏠 Main**        | General operations  | `main`, `default`, `general`, `snapshot`, `status`, `info` | Default terminal          |

---

## How Routing Works

### Automatic Routing (Via Scripts)

Scripts can emit routing hints using `terminal_router.py`:

```python
from src.output.terminal_router import emit_route, Channel

emit_route(Channel.METRICS, "CPU: 45%, RAM: 2.1GB")
# Output goes to 📊 Metrics terminal

emit_route(Channel.ERRORS, "ImportError: No module named 'src'")
# Output goes to 🔥 Errors terminal
```

### Manual Terminal Selection (You)

When running commands manually, **open the appropriate terminal** first:

1. **Click the terminal dropdown** in VS Code
2. **Select the themed terminal** (e.g., "🧪 Tests")
3. **Run your command** → output stays in that terminal

### Smart Command Routing (Agent-Driven)

Agents can route commands to terminals by detecting keywords:

- Command contains `pytest` → route to **🧪 Tests**
- Command contains `error_report` → route to **🔥 Errors**
- Command contains `ai_status` → route to **🤖 Agents**
- Command contains `brief` → route to **🏠 Main**

---

## Practical Examples

### Example 1: Running Tests

**Current (Bad):**

```bash
# Generic pwsh terminal
python -m pytest tests/test_guild_board.py
# Output mixes with other stuff, hard to find
```

**Better (Manual Terminal Selection):**

```bash
# Click dropdown → "🧪 Tests"
python -m pytest tests/test_guild_board.py
# Output stays in Tests terminal forever
```

**Best (Agent-Routed):**

```bash
# Tell agent: "Run tests and show results in Tests terminal"
# Agent emits: emit_route(Channel.TESTS)
# Then runs: python -m pytest tests/test_guild_board.py
```

### Example 2: Health Checks

**Current (Bad):**

```bash
# Generic pwsh terminal
pwsh -NoProfile -File scripts/start_system.ps1
# Mixes with everything else
```

**Better (Manual Terminal Selection):**

```bash
# Click dropdown → "📊 Metrics"
pwsh -NoProfile -File scripts/start_system.ps1
# Health report stays in Metrics terminal
```

**Best (Agent-Routed with Parsing):**

```python
# Agent script routes different parts to different terminals
emit_route(Channel.METRICS, "Overall: 5/8 services active")
emit_route(Channel.ERRORS, "Docker daemon not responding")
emit_route(Channel.AGENTS, "Ollama: ✅ 9 models loaded")
```

### Example 3: Multi-Agent Collaboration

**Current (Bad):**

```bash
# Everything in one pwsh terminal
python nusyq_chatdev.py --task "Create REST API"
# CEO, CTO, Coder outputs all mixed together
```

**Best (Multi-Terminal Routing):**

```python
# ChatDev wrapper emits routes for each agent role
emit_route(Channel.CHATDEV, "[CEO] Starting project analysis...")
emit_route(Channel.AGENTS, "[Coder] Generating Python Flask API...")
emit_route(Channel.TESTS, "[Tester] Running unit tests...")
emit_route(Channel.ERRORS, "[Reviewer] Found 3 issues...")
```

### Example 4: Error Hunting

**Current (Bad):**

```bash
# Generic terminal
python scripts/start_nusyq.py error_report
# 1,228 errors scroll past, can't review
```

**Best (Error Terminal + Persistent Session):**

```bash
# Click dropdown → "🔥 Errors"
python scripts/start_nusyq.py error_report
# All errors stay in Error terminal
# Scroll up anytime to review
# Terminal persists across VS Code restarts
```

---

## Agent Integration Patterns

### Pattern 1: Terminal-Aware Task Execution

```python
# In scripts/start_nusyq.py or similar
from src.output.terminal_router import emit_route, Channel

def run_tests():
    emit_route(Channel.TESTS)  # Signal: output goes to Tests terminal
    subprocess.run(["python", "-m", "pytest", "tests/"])

def show_metrics():
    emit_route(Channel.METRICS)  # Signal: output goes to Metrics terminal
    subprocess.run(["pwsh", "-File", "scripts/start_system.ps1"])

def analyze_with_ollama(file):
    emit_route(Channel.AGENTS)  # Signal: output goes to Agents terminal
    subprocess.run(["python", "src/tools/agent_task_router.py", "analyze", file])
```

### Pattern 2: Multi-Terminal Splitting

```python
# Complex workflow that uses 3 terminals
def full_ecosystem_check():
    # Health metrics → Metrics terminal
    emit_route(Channel.METRICS)
    check_docker()
    check_ollama()

    # Errors → Errors terminal
    emit_route(Channel.ERRORS)
    run_error_scan()

    # Next steps → Suggestions terminal
    emit_route(Channel.SUGGESTIONS)
    generate_recommendations()
```

### Pattern 3: Agent-Specific Routing

```python
# Route based on which AI system is handling the task
def route_to_agent(agent_name: str, task: str):
    routes = {
        "claude": Channel.CLAUDE,
        "copilot": Channel.COPILOT,
        "ollama": Channel.AGENTS,
        "chatdev": Channel.CHATDEV,
    }

    emit_route(routes.get(agent_name, Channel.MAIN))
    execute_task(task)
```

---

## Quick Reference Card

**When to use which terminal:**

- 🤖 **Claude** → When Claude agent is actively coding/analyzing
- 🧩 **Copilot** → When Copilot is giving suggestions/completions
- 🧠 **Codex** → When running code transformations (migrations, refactors)
- 🏗️ **ChatDev** → When ChatDev multi-agent team is working
- 🏛️ **AI Council** → When running consensus experiments (multiple models
  voting)
- 🔗 **Intermediary** → When agents are passing context/results to each other
- 🔥 **Errors** → When running error scans, debugging, exception tracking
- 💡 **Suggestions** → When getting AI recommendations, next steps, hints
- ✅ **Tasks** → When running PU queue, work queue, background jobs
- 🧪 **Tests** → When running pytest, test suites, coverage reports
- 🎯 **Zeta** → When running autonomous cycles, Zeta orchestration
- 🤖 **Agents** → When checking AI system health, Ollama status, agent
  coordination
- 📊 **Metrics** → When running health checks, system briefs, dashboards
- ⚡ **Anomalies** → When detecting orphaned processes, unexpected behaviors
- 🔮 **Future** → When planning features, reviewing roadmap
- 🏠 **Main** → Default for snapshots, status, general info

---

## Implementation Checklist

To fully utilize your 16 terminals, scripts should:

- [ ] Import `terminal_router.py`
- [ ] Emit routing hints before outputs: `emit_route(Channel.METRICS)`
- [ ] Group related outputs to same terminal
- [ ] Use specific terminals for specific tasks (tests → Tests, errors → Errors)
- [ ] Document routing in docstrings: `# Outputs to: 📊 Metrics terminal`

---

## Example: Modernized `start_system.ps1`

Instead of dumping everything to one terminal, split it:

```powershell
# Health metrics
python -c "from src.output.terminal_router import emit_route, Channel; emit_route(Channel.METRICS)"
pwsh -NoProfile -File scripts/start_system.ps1

# Errors found
python -c "from src.output.terminal_router import emit_route, Channel; emit_route(Channel.ERRORS)"
python scripts/start_nusyq.py error_report --quick

# Next steps
python -c "from src.output.terminal_router import emit_route, Channel; emit_route(Channel.SUGGESTIONS)"
python scripts/start_nusyq.py suggest
```

Each section goes to its themed terminal!

---

## Activation Status

**Currently:** ❌ Terminals exist but routing not used systematically **Goal:**
✅ All scripts emit routes, all outputs cleanly separated **Impact:** 10x easier
debugging, cleaner workflows, persistent context

**Next Step:** Modernize `start_system.ps1`, `start_nusyq.py`, and
`agent_task_router.py` to emit terminal routes.

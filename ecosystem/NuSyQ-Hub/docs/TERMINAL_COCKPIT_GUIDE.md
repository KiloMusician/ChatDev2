# Terminal Cockpit Operations Guide

**Status:** Operational monitoring system for NuSyQ-Hub  
**Purpose:** Real-time visibility into AI agents, error streams, quality
metrics  
**Architecture:** Event bus + tailing terminals (no background jobs)

---

## Quick Start

### Clean up old broken terminals first:

```powershell
# Kill all junk background jobs
Get-Job | Stop-Job -Force
Get-Job | Remove-Job -Force
```

### Launch the cockpit:

```powershell
# Default (Main + Errors + Agents + ChatDev):
.\scripts\launch_terminals.ps1

# All core terminals (Main + Errors + Metrics):
.\scripts\launch_terminals.ps1 -Core

# All AI system terminals (Agents + Council + ChatDev + Culture Ship + Moderator):
.\scripts\launch_terminals.ps1 -AI

# Quality terminals (Tests + Suggestions + Anomalies):
.\scripts\launch_terminals.ps1 -Quality

# Everything:
.\scripts\launch_terminals.ps1 -All
```

### Stop all terminals:

```powershell
Get-Process pwsh | Where-Object {$_.MainWindowTitle -match 'Terminal'} | Stop-Process
```

---

## Terminal Reference

### Core Terminals

#### 🏠 Main Terminal (`scripts/terminals/main.ps1`)

**Purpose:** Operator console  
**Shows:**

- Git status (current branch, uncommitted changes)
- Last 5 commits
- Recent reports (from `state/reports/`)
- Quest log tail (last 8 lines of `quest_log.jsonl`)

**Refresh:** Every 5 seconds

**Use when:** You want a high-level overview of system state

---

#### 🔥 Error Monitor (`scripts/terminals/errors.ps1`)

**Purpose:** Real-time diagnostic stream  
**Tails:**

- `state/reports/unified_error_report_latest.md` (if exists)
- `state/logs/errors.log` (fallback)

**Shows:** All errors logged by the system  
**Use when:** Debugging, watching for new errors during development

---

#### 📊 Metrics & Health (`scripts/terminals/metrics.ps1`)

**Purpose:** System health dashboard  
**Shows:**

- Spine health status (GREEN/YELLOW/RED)
- Error count trends (from `unified_error_report_latest.json`)
- Test coverage (if `.coverage` exists)

**Refresh:** Every 10 seconds  
**Use when:** Monitoring system health, tracking error reduction progress

---

### AI System Terminals

#### 🤖 Agent Coordination Hub (`scripts/terminals/agents.ps1`)

**Purpose:** Inter-agent message bus  
**Tails:** `state/logs/agent_bus.log`  
**Events:**

- `task_routed` - Work assigned to agent
- `agent_assigned` - Agent picked up task
- `work_completed` - Task finished
- `proof_validated` - Proof gates passed

**Use when:** Watching multi-agent collaboration, debugging task routing

---

#### 🏛️ AI Council (`scripts/terminals/council.ps1`)

**Purpose:** Consensus decision stream  
**Tails:** `state/logs/council_decisions.log`  
**Events:**

- `vote_started` - New decision needed
- `vote_cast` - Agent voted
- `consensus_reached` - Majority achieved
- `decision_final` - Action approved/rejected

**Use when:** Monitoring governance, understanding why decisions were made

---

#### 🏗️ ChatDev Multi-Agent (`scripts/terminals/chatdev.ps1`)

**Purpose:** CEO/CTO/Coder/Tester coordination  
**Shows:**

- Ollama models (running local LLMs)
- ChatDev transcript (last 150 lines of `state/logs/chatdev_latest.log`)

**Refresh:** Every 5 seconds  
**Use when:** Watching ChatDev multi-agent projects, verifying Ollama
availability

---

#### 🛸 Culture Ship (`scripts/terminals/culture_ship.ps1`)

**Purpose:** Proof gating & theater detection  
**Tails:** `state/logs/culture_ship_audits.log`  
**Events:**

- `proof_submitted` - Work claims to be done
- `audit_started` - Culture Ship reviewing
- `theater_detected` - Fake progress caught
- `proof_validated` - Real progress confirmed

**Use when:** Ensuring work quality, preventing fake progress from entering
canonical systems

---

#### 🔗 Moderator Gate (`scripts/terminals/moderator.ps1`)

**Purpose:** Risk assessment & compliance  
**Tails:** `state/logs/moderator.log`  
**Events:**

- `risk_assessed` - Safety check performed
- `gate_passed` - Work allowed to proceed
- `gate_blocked` - Work rejected (too risky)
- `escalation` - Human review needed

**Use when:** Understanding why work was blocked, reviewing safety decisions

---

### Quality Terminals

#### 🧪 Test Runner Monitor (`scripts/terminals/tests.ps1`)

**Purpose:** Continuous verification  
**Runs:** `pytest -q` every 60 seconds  
**Logs:** `state/logs/test_history.log`  
**Shows:** Pass/fail streaks, exit codes

**Use when:** Watching test suite during development, ensuring changes don't
break tests

---

#### 💡 Suggestion Stream (`scripts/terminals/suggestions.ps1`)

**Purpose:** Linting & type checking trends  
**Runs:**

- `ruff check .` (first 40 issues)
- `mypy .` (first 40 issues)

**Refresh:** Every 90 seconds  
**Use when:** Tracking code quality improvements, watching error count decrease

---

#### ⚡ Anomaly Detection (`scripts/terminals/anomalies.ps1`)

**Purpose:** Unusual pattern detection  
**Tails:** `state/logs/anomalies.log`  
**Events:**

- `spike_detected` - Sudden metric change
- `pattern_break` - Expected behavior violated
- `unexpected_behavior` - Unknown activity

**Use when:** Investigating system misbehavior, catching emergent issues early

---

## Event Bus Architecture

All terminals tail **canonical log files** in `state/logs/`:

```
state/logs/
├── agent_bus.log              (inter-agent messages)
├── council_decisions.log      (votes & consensus)
├── culture_ship_audits.log    (proof gating)
├── chatdev_latest.log         (CEO/CTO/Coder/Tester)
├── moderator.log              (risk gates)
├── errors.log                 (error stream)
├── anomalies.log              (unusual patterns)
└── test_history.log           (test results)
```

### Writing to the bus (from any Python code):

```python
from src.utils.event_bus import emit_event, emit_agent_message

# Generic event
emit_event("agent_bus", "task_routed",
           {"task_id": 42, "agent": "claude"},
           "Assigned refactoring compute_deltas() to Claude")

# Convenience helpers
emit_agent_message("claude", "Starting Phase 3 Task 3.1", task_id=3.1)
emit_council_vote("copilot", "approve", task_id=3.1, reason="passes all tests")
emit_audit("proof_validation", True, proof_id=123, complexity_reduced=68)
emit_error("ERROR", "Import failed", file="start_nusyq.py", line=42)
```

---

## Integration with Existing Systems

### Hook into orchestrator:

```python
# In src/orchestration/multi_ai_orchestrator.py
from src.utils.event_bus import emit_agent_message

def route_task(task, agent):
    emit_agent_message(agent, f"Routing {task.name}", task_id=task.id)
    # ... existing routing logic ...
```

### Hook into quest system:

```python
# In src/Rosetta_Quest_System/quest_engine.py
from src.utils.event_bus import emit_event

def complete_quest(quest_id):
    emit_event("agent_bus", "quest_completed", {"quest_id": quest_id})
    # ... existing completion logic ...
```

### Hook into ChatDev:

```python
# In nusyq_chatdev.py or ChatDev integration
from src.utils.event_bus import emit_event

def run_chatdev_project(description):
    emit_event("chatdev_latest", "project_started", {"desc": description})
    # ... run ChatDev ...
    emit_event("chatdev_latest", "project_completed", {"status": "success"})
```

---

## Terminal Best Practices

### DO:

- ✅ Keep terminals open during development for real-time feedback
- ✅ Use `-Core` for normal work, `-All` for deep debugging
- ✅ Let terminals tail logs (they're read-only, safe)
- ✅ Write events liberally (`emit_event` is cheap)
- ✅ Use `emit_agent_message` for quick agent status updates

### DON'T:

- ❌ Create background jobs manually (use `launch_terminals.ps1`)
- ❌ Edit terminal scripts while they're running
- ❌ Tail non-existent files directly (create them first)
- ❌ Spam events (group similar events into periodic summaries)

---

## Troubleshooting

### Terminal shows "Missing: <file>"

**Solution:** File doesn't exist yet. Either:

1. Wait for system to create it (e.g., run
   `python scripts/start_nusyq.py error_report`)
2. Create manually: `New-Item -ItemType File -Force -Path state/logs/<file>.log`

### Terminal is frozen / not updating

**Solution:**

1. Check if file is being written to:
   `Get-Content state/logs/<file>.log -Tail 5`
2. If empty, emit a test event:
   `python -c "from src.utils.event_bus import emit_event; emit_event('agent_bus', 'test', {})"`
3. If still frozen, restart terminal: `Ctrl+C` then re-run script

### Too many terminals open

**Solution:** Close all at once:

```powershell
Get-Process pwsh | Where-Object {$_.MainWindowTitle -match 'Terminal'} | Stop-Process
```

### Ollama not showing in ChatDev terminal

**Solution:**

1. Verify Ollama installed: `ollama list`
2. If not in PATH, add to environment or use full path
3. If Ollama not running, start service: `ollama serve`

---

## Next Steps

1. **Wire existing systems to event bus:**

   - Add `emit_agent_message` calls to orchestrator
   - Add `emit_council_vote` to guild/council logic
   - Add `emit_audit` to Culture Ship proof gating
   - Add `emit_event` to ChatDev integration

2. **Test the bus:**

   ```powershell
   # Open agent terminal
   .\scripts\terminals\agents.ps1

   # In another window, emit test event
   python -c "from src.utils.event_bus import emit_agent_message; emit_agent_message('test', 'Hello from event bus!')"

   # Verify message appears in agent terminal
   ```

3. **Use terminals during Phase 3:**
   - Launch `-Core` terminals before starting refactoring
   - Watch error count decrease in Metrics terminal
   - Monitor test results in Test Runner terminal
   - Track agent coordination in Agent Coordination Hub

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│  OPERATIONAL TERMINALS (PowerShell windows)                 │
│                                                              │
│  🏠 Main   🔥 Errors   📊 Metrics   🤖 Agents   🏛️ Council  │
│  🏗️ ChatDev   🛸 Culture Ship   🔗 Moderator               │
│  🧪 Tests   💡 Suggestions   ⚡ Anomalies                   │
│                                                              │
│  (Each terminal: Get-Content -Wait -Tail N on a log file)   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ tail
                              │
┌─────────────────────────────────────────────────────────────┐
│  EVENT BUS (state/logs/*.log files)                         │
│                                                              │
│  agent_bus.log  council_decisions.log  culture_ship_audits  │
│  chatdev_latest.log  moderator.log  errors.log  anomalies   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ emit_event()
                              │
┌─────────────────────────────────────────────────────────────┐
│  SYSTEM COMPONENTS (Python)                                 │
│                                                              │
│  Orchestrator → Agent Bus                                   │
│  Quest System → Agent Bus                                   │
│  ChatDev Integration → ChatDev Log                          │
│  Culture Ship → Audit Log                                   │
│  Council → Decision Log                                     │
│  Error Reporter → Error Log                                 │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** Terminals are **views**, not **controllers**. They passively
observe; system components actively emit.

**Zero-token technique:** Each terminal shows real signal (not narrative),
leaving receipts (auditable logs), with minimal overhead (append-only writes).

---

**Status:** ✅ Fully operational, ready for Phase 3 integration

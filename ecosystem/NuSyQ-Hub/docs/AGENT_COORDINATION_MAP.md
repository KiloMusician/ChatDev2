# ΞNuSyQ Agent Coordination Map

**Purpose**: This document maps all agent orchestration systems and their relationships to prevent confusion and ensure agents use the correct coordination mechanisms.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  - python nusyq.py (conversational CLI)                         │
│  - python src/main.py (mode-based CLI)                          │
│  - VS Code extensions (Copilot, Codex, Claude)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│  src/orchestration/multi_ai_orchestrator.py (PRIMARY)           │
│  src/orchestration/unified_ai_orchestrator.py (LEGACY)          │
│  src/agents/agent_orchestration_hub.py (AGENT ROUTING)          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT LAYER                                 │
│  - Claude (via terminal)                                        │
│  - Copilot (via extension)                                      │
│  - Codex (via API)                                              │
│  - ChatDev (via python subprocess)                              │
│  - Ollama (via HTTP API)                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  COORDINATION SYSTEMS                           │
│  - Quest System (src/Rosetta_Quest_System/quest_log.jsonl)     │
│  - Guild Board (docs/GUILD_BOARD.md)                            │
│  - Terminal Manager (src/system/terminal_manager.py)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Primary Orchestrators (USE THESE)

### 1. **multi_ai_orchestrator.py** ✅ PRIMARY
**Location**: `src/orchestration/multi_ai_orchestrator.py`

**Purpose**: Main coordination hub for all AI agents (Claude, Copilot, Codex, ChatDev, Ollama)

**When to use**:
- Building new projects
- Complex multi-step tasks
- Agent coordination needed
- Task routing

**Methods**:
- `orchestrate_task(task_type, content, context, priority)` - Submit task
- `get_task_status(task_id)` - Check task progress

**Example**:
```python
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator, TaskPriority

orchestrator = MultiAIOrchestrator()
result = orchestrator.orchestrate_task(
    task_type="general",
    content="Build a snake game",
    context={"mode": "cli"},
    priority=TaskPriority.HIGH,
)
```

---

### 2. **agent_orchestration_hub.py** ✅ AGENT ROUTING
**Location**: `src/agents/agent_orchestration_hub.py`

**Purpose**: Routes tasks to specific agents based on task type

**When to use**:
- Need to target a specific agent (e.g., "use Claude for this")
- Agent specialization needed
- Inter-agent communication

**Methods**:
- `route_task(task, preferred_agent)` - Route to specific agent
- `coordinate_agents(tasks)` - Parallel coordination

---

## Quest & Guild System (TASK TRACKING)

### Quest System ✅ ACTIVE
**Location**: `src/Rosetta_Quest_System/quest_log.jsonl`

**Purpose**: Persistent task logging across sessions

**Format**:
```json
{
  "quest_id": "Q-20260116-1234",
  "title": "Fix import errors",
  "status": "in_progress",
  "assigned_to": "Claude",
  "created_at": "2026-01-16T12:34:56",
  "steps": [...],
  "artifacts": [...]
}
```

**How agents should use it**:
1. Read quest_log.jsonl on startup
2. Update quest status as work progresses
3. Append new quests when starting new work
4. Mark quests complete when done

---

### Guild Board ✅ ACTIVE
**Location**: `docs/GUILD_BOARD.md`

**Purpose**: Human-readable task board

**Structure**:
- **Quests In Progress**: Active work
- **Quests Completed**: Done
- **Quests Blocked**: Waiting on external factors
- **Quests Planned**: Backlog

**How agents should use it**:
1. Check Guild Board for context on system priorities
2. Update Guild Board when completing major milestones
3. Don't micro-manage (quest_log.jsonl is for fine-grained tracking)

---

## Terminal Routing

### Terminal Manager ✅ NEW
**Location**: `src/system/terminal_manager.py`

**Purpose**: Enforces "one terminal per role" for agent output

**Canonical Terminals**:
- Claude, Copilot, Codex, ChatDev, AI-Council, Intermediary
- Errors, Suggestions, Tasks, Zeta, Agents, Metrics, Anomalies, Future, Main

**How agents should use it**:
```python
from src.system.terminal_manager import TerminalManager

tm = TerminalManager()
tm.route_output("Claude", "Starting task X...")
```

---

## Legacy/Deprecated Orchestrators (DO NOT USE)

⚠️ The following orchestrators exist but should NOT be used by new code:

### ❌ unified_ai_orchestrator.py (LEGACY)
- **Status**: Superseded by `multi_ai_orchestrator.py`
- **Why**: Older architecture, less capable
- **What to do**: Use `multi_ai_orchestrator.py` instead

### ❌ autonomous_quest_orchestrator.py (EXPERIMENTAL)
- **Status**: Experimental, incomplete
- **Why**: Not production-ready
- **What to do**: Use Quest System + multi_ai_orchestrator instead

### ❌ chatdev_development_orchestrator.py (SPECIFIC)
- **Status**: Too specific (ChatDev only)
- **Why**: Should use multi_ai_orchestrator which handles all agents
- **What to do**: Use multi_ai_orchestrator, which routes to ChatDev when appropriate

---

## How Agents Should Coordinate

### **Scenario 1: User Requests a Task**

1. **User** → `python nusyq.py build a snake game`
2. **nusyq_daemon.py** → Parses command
3. **multi_ai_orchestrator.py** → Routes to appropriate agent(s)
4. **Agent** (e.g., Claude) → Executes task
5. **Quest System** → Logs progress
6. **Terminal Manager** → Routes output to "Claude" terminal
7. **User** → Sees results

---

### **Scenario 2: Agent Needs Help from Another Agent**

1. **Agent A** (e.g., Copilot) → Encounters complex task
2. **agent_orchestration_hub.py** → `coordinate_agents([task])`
3. **multi_ai_orchestrator.py** → Routes sub-tasks to Agent B (e.g., Claude)
4. **Agent B** → Completes sub-task
5. **Agent A** → Receives result, continues
6. **Quest System** → Logs collaboration

---

### **Scenario 3: Agent Discovers Errors**

1. **Agent** → Runs code, detects error
2. **Terminal Manager** → Routes error to "Errors" terminal
3. **Agent** → Logs error in quest_log.jsonl
4. **Agent** → (Optional) Invokes `ComprehensiveErrorResolver`
5. **Guild Board** → Updates with "Quest Blocked" if unresolvable

---

## Decision Tree for Agents

```
┌─────────────────────────────────────────┐
│ Need to execute a task?                 │
└────────────┬────────────────────────────┘
             │
             ▼
      ┌──────────────┐
      │ Single agent │
      │ task?        │
      └──┬────────┬──┘
         │ Yes    │ No
         │        │
         ▼        ▼
    Use Agent   Use multi_ai_orchestrator
    directly    (coordinates multiple agents)
         │        │
         └────┬───┘
              │
              ▼
      ┌──────────────┐
      │ Log to       │
      │ quest_log.   │
      │ jsonl        │
      └──────┬───────┘
             │
             ▼
      ┌──────────────┐
      │ Route output │
      │ to correct   │
      │ terminal     │
      └──────────────┘
```

---

## Key Principles for Agents

1. **Use multi_ai_orchestrator.py** - It's the canonical entry point
2. **Always log to quest_log.jsonl** - Preserves context across sessions
3. **Route output to correct terminal** - Prevents chaos
4. **Update Guild Board** - Keep humans informed
5. **Don't invent new orchestrators** - Use existing infrastructure
6. **Coordinate via agent_orchestration_hub.py** - Don't call agents directly

---

## File Locations Reference

| Component | Path | Purpose |
|-----------|------|---------|
| **Primary Orchestrator** | `src/orchestration/multi_ai_orchestrator.py` | Main coordination hub |
| **Agent Router** | `src/agents/agent_orchestration_hub.py` | Routes tasks to agents |
| **Quest System** | `src/Rosetta_Quest_System/quest_log.jsonl` | Persistent task log |
| **Guild Board** | `docs/GUILD_BOARD.md` | Human-readable task board |
| **Terminal Manager** | `src/system/terminal_manager.py` | Terminal routing |
| **Lifecycle Manager** | `src/system/lifecycle_manager.py` | Service start/stop |
| **System Voice** | `src/system/nusyq_daemon.py` | Conversational CLI |
| **Agent Orientation** | `src/system/agent_orientation.py` | Agent onboarding |

---

## Emergency Contacts (For Agents)

If you (an agent) are confused about what to do:

1. Read `docs/ΞNuSyQ_SYSTEM_BRIEF.md` (canonical ground truth)
2. Read this file (`docs/AGENT_COORDINATION_MAP.md`)
3. Check `quest_log.jsonl` for recent context
4. Check `docs/GUILD_BOARD.md` for priorities
5. Use `multi_ai_orchestrator.py` when in doubt

**DO NOT**:
- Wander aimlessly through the codebase
- Create new orchestration systems
- Ignore existing infrastructure
- Delete scaffolding you don't understand

---

**Last Updated**: 2026-01-16
**Maintained By**: ΞNuSyQ Core Team
**Status**: CANONICAL (agents must follow this)

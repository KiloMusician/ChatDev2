# 🧠 Multi-Agent Orchestration System - Complete Architecture

*Build Date: December 26, 2025*

## Overview

We've built a **complete multi-agent orchestration system** that spans:
1. **Terminal Infrastructure** - Dedicated terminals for each agent (Claude, Copilot, Codex, ChatDev, AI Council, Intermediary)
2. **Coordination Layer** - Prevents agent collision via task locking and request/grant patterns
3. **Guild Board** - Living coordination substrate where agents claim, work, and post progress
4. **Terminal Router** - Routes agent output to appropriate terminals with full tracing

Together, these form a **coherent orchestration platform** where 6+ AI agents can work in parallel without stepping on each other.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Multi-Agent Ecosystem                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐                │
│  │   Claude    │  │   Copilot    │  │  Codex   │  ...           │
│  │   🤖 Agent  │  │  🔷 Agent    │  │📘 Agent  │                │
│  └──────┬──────┘  └────────┬─────┘  └────┬─────┘                │
│         │                  │              │                      │
│         └──────────────────┼──────────────┘                      │
│                            │                                      │
│                   ┌────────▼────────┐                           │
│                   │  Agent Terminal  │                          │
│                   │     Router       │                          │
│                   │ (src/system/    │                          │
│                   │  agent_terminal │                          │
│                   │  _router.py)    │                          │
│                   └────────┬────────┘                           │
│                            │                                      │
│         ┌──────────────────┼──────────────────┐                │
│         │                  │                  │                │
│    ┌────▼─────┐      ┌────▼──────┐    ┌─────▼─────┐         │
│    │ Guild     │      │ Terminal   │    │Coordination│         │
│    │ Board     │      │Orchestrator│    │ Layer      │         │
│    │(Queues,  │      │ (9+        │    │ (Locks,    │         │
│    │Claiming, │      │ terminals) │    │  Requests) │         │
│    │Progress) │      │            │    │            │         │
│    └────┬─────┘      └────┬───────┘    └─────┬──────┘         │
│         │                  │                  │                │
│         └──────────────────┼──────────────────┘                │
│                            │                                      │
│              ┌─────────────▼────────────┐                      │
│              │    .vscode/sessions.json │                      │
│              │  (Terminal Keeper UI)    │                      │
│              │  - 🤖 Claude Terminal    │                      │
│              │  - 🔷 Copilot Terminal   │                      │
│              │  - 📘 Codex Terminal     │                      │
│              │  - 💻 ChatDev Terminal   │                      │
│              │  - 🏛️ AI Council        │                      │
│              │  - 🔗 Intermediary       │                      │
│              │  - 🔥 Errors             │                      │
│              │  - 💡 Suggestions        │                      │
│              │  - ✓ Tasks               │                      │
│              │  ... (9 total)           │                      │
│              └──────────────────────────┘                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Multi-Agent Terminal Orchestrator

**File:** `src/system/multi_agent_terminal_orchestrator.py`

Manages isolated I/O streams for each agent:
- One stream per (agent, terminal) pair
- Async-safe writes with message serialization
- Full tracing with IDs and parent relationships
- Pub/Sub for cross-agent visibility
- Persistent message logging to disk

**Key Classes:**
- `TerminalStream` - Isolated I/O channel
- `MultiAgentTerminalOrchestrator` - Central manager
- `AgentContext` - Exclusive execution context for agent

**Usage:**
```python
orchestrator = await get_orchestrator()

# Create/get stream
stream = await orchestrator.get_or_create_stream(
    AgentType.CLAUDE, TerminalType.CLAUDE
)

# Write message
await orchestrator.write_to_terminal(
    AgentType.CLAUDE,
    TerminalType.CLAUDE,
    "Analysis complete: 47 files refactored"
)
```

### 2. Agent Terminal Router

**File:** `src/system/agent_terminal_router.py`

Routes agent output to correct terminals based on event type:
- Agent heartbeats → 🤖 Agents terminal
- Task completion → ✓ Tasks + 📊 Metrics terminals
- Errors → 🔥 Errors + ⚡ Anomalies terminals
- Inter-agent messages → 🔗 Intermediary terminal
- Consensus votes → 🏛️ AI Council terminal

**Key Methods:**
- `route_agent_output()` - Route single agent message
- `route_event()` - Multicast event to interested terminals
- `route_task_update()` - Standardized task status
- `route_error()` - Error routing with context
- `route_inter_agent_message()` - Agent-to-agent comms

**Usage:**
```python
router = await get_router()

await router.route_task_update(
    task_id="q-123",
    agent=AgentType.CLAUDE,
    status="completed",
    message="Refactoring complete",
    context={"files_changed": 47}
)
```

### 3. Agent Coordination Layer

**File:** `src/system/agent_coordination_layer.py`

Prevents task collision and manages handoffs:
- Atomic task locks (only one agent at a time)
- Request/grant patterns (agent asking permission)
- Waitlist management (queue if task locked)
- Timeout handling (reclaim expired locks)
- Cross-agent communication tracking

**Key Classes:**
- `TaskLock` - Lock on specific task
- `AgentRequest` - Inter-agent request
- `AgentCoordinationLayer` - Central coordinator

**Usage:**
```python
coord = await get_coordination_layer()

# Try to lock task
status, lock = await coord.request_task_lock(
    task_id="q-123",
    agent=AgentType.CLAUDE,
    timeout_seconds=300
)

if status == TaskLockStatus.GRANTED:
    # Do work...
    await coord.release_task_lock("q-123", AgentType.CLAUDE)
```

### 4. Guild Board System

**File:** `src/guild/guild_board.py`

Living coordination substrate where agents claim and report work:
- Atomic quest claiming
- Progress posting (heartbeats, notes, blockers)
- Quest state transitions (open → claimed → active → done)
- System signals (errors, drift detection)
- Event logging for audit trail

**Key Classes:**
- `AgentHeartbeat` - Agent status message
- `QuestEntry` - Quest definition
- `BoardPost` - Agent communication
- `GuildBoard` - Central board manager

**Usage:**
```python
board = await get_board()

# Heartbeat
await board.agent_heartbeat(
    agent_id="copilot",
    status=AgentStatus.WORKING,
    current_quest="q-123",
    capabilities=["code", "refactoring"]
)

# Claim quest
success, msg = await board.claim_quest("q-123", "copilot")

# Post progress
await board.post_on_board(
    agent_id="copilot",
    message="Completed 47 refactors",
    quest_id="q-123",
    artifacts=["logs/run_47.jsonl"]
)

# Complete
await board.complete_quest("q-123", "copilot", artifacts=[...])
```

### 5. Guild Board Renderer

**File:** `src/guild/guild_board_renderer.py`

Produces human-readable views of board state:
- Markdown rendering for Obsidian/GitHub
- JSON export for machine consumption
- Stable filename (`docs/GUILD_BOARD.md`) - no churn
- Summary sections (agents, quests, signals, posts)

**Usage:**
```python
renderer = GuildBoardRenderer(board)

# Render to string
md = await renderer.render_markdown()

# Save to disk
await renderer.save_markdown()  # → docs/GUILD_BOARD.md
await renderer.save_json()      # → docs/guild_board.json
```

### 6. Agent Guild Protocols

**File:** `src/guild/agent_guild_protocols.py`

Simple async methods agents call to use the board:
- `agent_heartbeat()` - Show I'm alive
- `agent_claim()` - Reserve task atomically
- `agent_start()` - Begin work
- `agent_post()` - Share updates
- `agent_complete()` - Mark done
- `agent_yield()` - Abandon task
- `agent_swarm()` - Request team help

These are the **handshake protocol** agents use without internal coordination knowledge.

---

## Information Flow

### Agent Lifecycle (Minimal)

```
┌─────────────────┐
│  Agent Starts   │
└────────┬────────┘
         │
         ▼
  ┌──────────────┐     await agent_heartbeat(
  │  Heartbeat   │     agent="copilot",
  │  (show alive)│     status="idle"
  └────────┬─────┘     )
           │
           ▼
  ┌──────────────┐     quests = await
  │Get Available │     agent_available_quests(
  │   Quests     │     "copilot", capabilities
  └────────┬─────┘     )
           │
           ▼
  ┌──────────────┐     ok, msg = await
  │   Claim      │     agent_claim(
  │    Quest     │     "copilot", quest_id
  └────────┬─────┘     )
           │ (success)
           ▼
  ┌──────────────┐     await agent_start(
  │   Start      │     "copilot", quest_id
  │    Work      │     )
  └────────┬─────┘
           │
           ▼ (do actual work)

  ┌──────────────┐     await agent_post(
  │    Post      │     "copilot",
  │  Progress    │     "Completed step 5",
  └────────┬─────┘     quest_id=quest_id
           │           )
           ▼
  ┌──────────────┐     ok, msg = await
  │  Complete    │     agent_complete(
  │   Quest      │     "copilot",
  └────────┬─────┘     quest_id,
           │           artifacts=[...]
           ▼           )
  ┌──────────────┐
  │    Loop →    │
  │   Heartbeat  │
  └──────────────┘
```

### Collision Prevention

```
Agent A                      Board                      Agent B
   │                            │                          │
   ├─ claim("q-123") ──────────→│                          │
   │                            │  (acquires lock)         │
   │                        ✓ GRANTED                      │
   │                            │← claim("q-123")
   │                            │  (lock held by A)
   │                        ✗ DENIED
   │                            │  "Already claimed"
   │                            │
   │─ (work on q-123) ──────────→│
   │                            │  (still locked)
   │                            │
   │─ complete("q-123") ────────→│
   │                            │  (releases lock)
   │                            │← claim("q-123") [B retries]
   │                            │  ✓ GRANTED
```

### Terminal Routing

```
Agent Posts               Router              Terminals
   │                        │                     │
   ├─ heartbeat("idle") ────→│
   │                         │─→ 🤖 Agents
   │                         │
   ├─ claim("q-123") ───────→│
   │                         │─→ ✓ Tasks
   │                         │
   ├─ post("Progress:..") ──→│
   │                         │─→ 💡 Suggestions
   │                         │
   ├─ error detected ────────→│
   │                         │─→ 🔥 Errors
   │                         │─→ ⚡ Anomalies
   │                         │
   ├─ complete("q-123") ─────→│
   │                         │─→ ✓ Tasks
   │                         │─→ 📊 Metrics
```

---

## File Organization

```
src/
├── system/
│   ├── multi_agent_terminal_orchestrator.py    (Terminals)
│   ├── agent_terminal_router.py                (Routing)
│   └── agent_coordination_layer.py             (Locking)
│
└── guild/
    ├── __init__.py                             (Exports)
    ├── guild_board.py                          (Core)
    ├── guild_board_renderer.py                 (Rendering)
    ├── agent_guild_protocols.py                (Protocol)
    └── guild_cli.py                            (CLI)

.vscode/
└── sessions.json                               (Terminal Keeper)

state/guild/
├── guild_board.json                            (State)
└── guild_events.jsonl                          (Events)

data/
├── agent_registry.json                         (Agent capabilities)
├── ecosystem/quest_assignments.json            (Assignments)
└── unified_pu_queue.json                       (Task backlog)

docs/
├── GUILD_BOARD_SYSTEM.md                       (Guild docs)
├── GUILD_BOARD.md                              (Rendered view)
└── RECEIPTS/GUILD_BOARD_ACTIVATION.md          (Receipt)
```

---

## Integration Points

### ↔️ Terminal Keeper Extension
- `.vscode/sessions.json` defines 15+ terminals
- Each agent has dedicated terminal
- Shared visibility terminals (AI Council, Intermediary)
- Real-time UI updates via Terminal Keeper API

### ↔️ Quest System (Rosetta)
- Reads `src/Rosetta_Quest_System/quests.json`
- Syncs with `quest_log.jsonl`
- Quest state transitions logged

### ↔️ Agent Ecosystem
- Reads `data/agent_registry.json` for capabilities
- Updates agent progression via board completion events
- Skill-based quest matching

### ↔️ Task Orchestration
- Reads `data/unified_pu_queue.json` for backlog
- Converts PUs to boardquests
- Tracks assignments bidirectionally

---

## Concurrency Guarantees

### 1. Atomic Claiming
- Only ONE agent can successfully claim a quest
- Lock-based synchronization
- Immediate feedback on claim status

### 2. Crash Safety
- Append-only event log never corrupted
- Board state reconstructible from events
- Locks timeout if agent crashes

### 3. Terminal Ordering
- Messages serialized per terminal
- No interleaving across terminals
- Each agent stream atomic

### 4. Coordination Ordering
- Task lock acquisition is ordered
- Request queues prevent starvation
- Waitlist prevents indefinite blocking

---

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Claim quest | O(1) | Dict lookup + lock update |
| Post message | O(1) | Append to stream + board |
| Get available | O(n) | Filter by capability |
| Complete quest | O(1) | Dict update |
| Heartbeat | O(1) | Dict upsert |
| Get status | O(n) | Scan all agents/quests |

**Scaling:** System designed for 10-20 agents, 100-500 quests. Can scale to 1000s with database backend.

---

## Next Phase (Future)

When ready to enhance:

1. **Database Backend** - SQLite/PostgreSQL for true persistence
2. **Web Dashboard** - Real-time board visualization
3. **Skill Progression** - Agents level up, unlock capabilities
4. **Automatic Parties** - Form teams for complex multi-quest chains
5. **Culture Ship Integration** - Board posts become emergence lore
6. **Cross-Repo Sync** - SimVerse/Root agents on same guild board
7. **Quest Templates** - Reusable patterns for refactors, fixes, etc.

---

## Status

✅ **Foundation Complete** - Core multi-agent orchestration ready
✅ **Terminal Infrastructure** - 15+ dedicated/shared terminals defined
✅ **Coordination Layer** - Atomic claiming, collision prevention
✅ **Guild Board** - Living state, full audit trail
✅ **Agent Protocols** - Simple handshake for agents
✅ **Rendering** - Markdown views with stable filenames
✅ **Documentation** - Complete with examples

🚀 **Ready for Agent Use**

Agents can now claim quests, coordinate work, and self-manage as a coherent party instead of isolated processes.

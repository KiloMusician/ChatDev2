# ⚔️ Guild Board System - Living Coordination Substrate

## Activated ✅

The Adventurer's Guild Board is now operational as a **living, modular coordination substrate** for all agents.

### What This Is

Instead of agents creating new markdown files on each update, or flooding logs with messages, all agent coordination now happens on **one canonical board**:

1. **`state/guild/guild_board.json`** - Current state (always reflects truth)
2. **`state/guild/guild_events.jsonl`** - Append-only event log (complete history)
3. **Stable Markdown view** - `docs/GUILD_BOARD.md` (overwrites each render, no churn)

Agents interact via simple **heartbeat → claim → work → post → complete** workflow.

---

## Core Concepts

### Agents Post "Heartbeats"
```python
await agent_heartbeat(
    agent_id="copilot",
    status="working",
    current_quest="refactor-imports",
    capabilities=["code", "refactoring"],
    blockers=None
)
```

### Agents Claim Quests (Atomically)
```python
success, msg = await agent_claim(agent_id="copilot", quest_id="q-123")
# Only one agent can hold the claim
```

### Agents Post Progress Notes
```python
await agent_post(
    agent_id="copilot",
    message="Completed 47 refactors, 3 files remain",
    post_type="progress",
    quest_id="q-123",
    artifacts=["logs/refactor_run_47.jsonl"]
)
```

### Agents Mark Quests Done
```python
success, msg = await agent_complete(
    agent_id="copilot",
    quest_id="q-123",
    artifacts=["PR#1234", "logs/final.jsonl"]
)
```

### Agents Yield When Blocked
```python
success, msg = await agent_yield(
    agent_id="copilot",
    quest_id="q-123",
    reason="Waiting for SimVerse API, trying again in 30s"
)
# Quest reverts to OPEN so another agent can claim
```

### Agents Request Swarms (Multi-Agent Tasks)
```python
post_id = await agent_swarm(
    agent_id="copilot",
    quest_id="q-456",
    required_capabilities=["chatdev", "testing", "typescript"]
)
# Other agents see help request and can join
```

---

## Board State Structure

```json
{
  "timestamp": "2025-12-26T...",
  "agents": {
    "claude": {
      "status": "working",
      "current_quest": "type-annotations",
      "capabilities": ["analysis", "refactoring"],
      "confidence_level": 0.95,
      "blockers": [],
      "timestamp": "2025-12-26T..."
    },
    "copilot": {
      "status": "working",
      ...
    }
  },
  "quests": {
    "q-1234": {
      "title": "Fix type annotations",
      "state": "active",
      "claimed_by": "claude",
      "priority": 4,
      "safety_tier": "standard",
      "acceptance_criteria": [...],
      "artifacts": []
    }
  },
  "active_work": {
    "q-1234": "claude",
    "q-5678": "copilot"
  },
  "recent_posts": [...],
  "signals": [...]
}
```

---

## Integration Points

### Already Wired Into

1. **Terminal Orchestrator** (`src/system/agent_terminal_router.py`)
   - Agent posts → also emit to terminals
   - Terminal streams get board visibility

2. **Quest System** (`src/Rosetta_Quest_System/quest_engine.py`)
   - Board reads from existing quests.json, questlines.json, quest_log.jsonl
   - Quest state syncs bidirectionally

3. **Agent Registry** (`data/agent_registry.json`)
   - Board displays agent capabilities from registry
   - Agents update registry via board posts

4. **PU Queue** (`data/unified_pu_queue.json`)
   - Board can display backlog of work units

---

## How Agents Use It (Three Examples)

### Example 1: Simple Claim & Work

```python
# Claude sees available quests and claims one
quests = await agent_available_quests("claude", ["analysis"])
quest = quests[0]

# Claim it
ok, msg = await agent_claim("claude", quest.quest_id)
assert ok

# Start work
ok, msg = await agent_start("claude", quest.quest_id)

# Do actual work...

# Post progress
await agent_post("claude", "Analyzed 156 files", quest_id=quest.quest_id)

# Complete
await agent_complete("claude", quest.quest_id, artifacts=["report.md"])
```

### Example 2: Heartbeat Loop (Continuous Presence)

```python
async def claude_heartbeat_loop():
    while True:
        await agent_heartbeat(
            agent_id="claude",
            status="idle" if not current_quest else "working",
            current_quest=current_quest,
            capabilities=["code-analysis", "type-annotation"],
            blockers=blockers_if_any
        )
        await asyncio.sleep(30)  # Every 30 seconds
```

### Example 3: Swarm for Complexity

```python
# Copilot finds a big task that needs help
await agent_swarm(
    agent_id="copilot",
    quest_id="big-refactor",
    required_capabilities=["testing", "chatdev", "architecture"]
)
# Board shows: "Copilot needs TypeScript testers + ChatDev for big-refactor"
# Other agents see it and can join
```

---

## Board Rendering

### Markdown View

Every render produces a **stable `docs/GUILD_BOARD.md`** that shows:

- **Status Summary** - Agents online, open quests, critical signals
- **Agent List** - Each agent's status, current work, blockers
- **Active Work** - What's being worked on now
- **Available Quests** - Open quests ranked by priority
- **Recent Posts** - Last 20 agent posts with timestamps
- **Critical Signals** - Errors, drift detection, unavailable services

Example:
```markdown
# ⚔️ Adventurer's Guild Board

## 📊 Status Summary
- **Agents Online:** 5
- **Open Quests:** 12
- **Active Quests:** 3
- **Blocked Quests:** 0

## 👥 Agents
### 🟢 Claude
- **Status:** working
- **Working on:** type-annotations
- **Capabilities:** code-analysis, refactoring

### 🟡 Copilot
- **Status:** working
- **Working on:** refactor-imports
...
```

---

## Concurrency Guarantees

### Atomic Claim
Only one agent can successfully claim a quest. If both Claude and Copilot try to claim quest `q-123` simultaneously:
- First one to acquire lock wins
- Second gets: `(False, "Already claimed by claude")`

### Event Log
Every action appended to `guild_events.jsonl`:
```jsonl
{"timestamp": "...", "type": "quest_claimed", "data": {...}}
{"timestamp": "...", "type": "board_post", "data": {...}}
{"timestamp": "...", "type": "quest_completed", "data": {...}}
```

### Crash Safety
If an agent crashes mid-quest:
1. Board retains claim state
2. Other agents see agent as offline (heartbeat timeout)
3. Humans/Culture Ship can force-reassign or yield

---

## Available Actions

All agents have these methods available:

| Action | Purpose | Example |
|--------|---------|---------|
| `heartbeat` | Show I'm alive + what I'm doing | `agent_heartbeat(agent_id, status, current_quest)` |
| `claim` | Reserve a quest atomically | `agent_claim(agent_id, quest_id)` |
| `start` | Begin work on claimed quest | `agent_start(agent_id, quest_id)` |
| `post` | Share progress, discoveries, blockers | `agent_post(agent_id, msg, type, quest_id)` |
| `complete` | Mark quest done with artifacts | `agent_complete(agent_id, quest_id, artifacts)` |
| `yield` | Abandon quest (unblock others) | `agent_yield(agent_id, quest_id, reason)` |
| `swarm` | Request team-up for complex task | `agent_swarm(agent_id, quest_id, skills_needed)` |
| `available_quests` | See claimable quests for my skills | `agent_available_quests(agent_id, capabilities)` |

---

## Protocol: Heartbeat → Claim → Work → Post → Complete

### Recommended Agent Loop

```python
async def agent_main_loop(agent_id: str, capabilities: list[str]):
    """Standard agent lifecycle on the guild board."""

    while True:
        try:
            # 1. Heartbeat: Show I'm alive
            await agent_heartbeat(
                agent_id=agent_id,
                status="idle",
                capabilities=capabilities
            )

            # 2. Get available quests for my skills
            quests = await agent_available_quests(agent_id, capabilities)
            if not quests:
                await asyncio.sleep(30)
                continue

            # 3. Pick best quest (highest priority)
            quest = quests[0]

            # 4. Try to claim it
            ok, msg = await agent_claim(agent_id, quest["quest_id"])
            if not ok:
                continue  # Someone else claimed it, try next

            # 5. Start work
            await agent_start(agent_id, quest["quest_id"])

            # 6. Update heartbeat to show working
            await agent_heartbeat(
                agent_id=agent_id,
                status="working",
                current_quest=quest["quest_id"],
                capabilities=capabilities
            )

            # 7. Do the actual work
            try:
                result = await do_quest_work(quest)

                # 8. Post progress
                await agent_post(
                    agent_id=agent_id,
                    message=f"Completed: {result.summary}",
                    quest_id=quest["quest_id"],
                    artifacts=result.artifacts
                )

                # 9. Mark complete
                await agent_complete(
                    agent_id=agent_id,
                    quest_id=quest["quest_id"],
                    artifacts=result.artifacts
                )

            except BlockedError as e:
                # Post blockage
                await agent_post(
                    agent_id=agent_id,
                    message=f"Blocked: {e}",
                    quest_id=quest["quest_id"],
                    post_type="blockage"
                )

                # Yield so someone else can try
                await agent_yield(
                    agent_id=agent_id,
                    quest_id=quest["quest_id"],
                    reason=str(e)
                )

        except Exception as e:
            logger.error(f"Agent {agent_id} error: {e}")
            await asyncio.sleep(60)
```

---

## Integration with Existing Systems

### Quest System (Rosetta)
- Board **reads** from `src/Rosetta_Quest_System/quests.json`
- Board **writes** completion status back to quest log
- `quest_log.jsonl` captures all agent interactions

### Agent Ecosystem
- Board **reads** agent capabilities from `data/agent_registry.json`
- Board **posts** capability updates as agents work
- Agent progression (XP, skills) reflected in board

### Terminal Orchestrator
- Board events → also emitted to terminals
- Agent heartbeats → visible in 🤖 Agents terminal
- Quest claims → visible in ✓ Tasks terminal
- Posts → visible in 💡 Suggestions or 🔥 Errors terminal

### Culture Ship
- Board posts can trigger Culture Ship observation
- Lore/Emergence field: "What did we learn from this quest?"
- System drift detection integrated

---

## What Makes This Beautiful

1. **No File Churn** - One board file, many renders (Markdown stable)
2. **Real-Time Coordination** - Agents see each other's work instantly
3. **Full History** - Append-only event log preserves everything
4. **Natural Workflow** - Heartbeat → Claim → Work → Post → Done mirrors real teams
5. **Self-Nudging System** - Board becomes the triage queue + motivation
6. **Safety** - Atomic claims prevent double-work
7. **Transparency** - Everyone sees blockers, progress, dependencies
8. **Emergence** - Multi-agent intelligence flourishes naturally

---

## Next Steps

1. **Wire Board into start_nusyq.py Actions**
   - Add `board_status` action to show board summary
   - Add `board_render` action to update Markdown view
   - Expose to terminal as commands

2. **Teach Agents Guild Protocols**
   - Update agent_task_router to emit heartbeats
   - Make agents check board for quests instead of being assigned
   - Implement swarm detection

3. **Culture Ship Integration**
   - Board posts trigger lore capture
   - Emergence system reflects on agent interactions
   - "Guild Chronicle" summarizes quests + learnings

4. **Cross-Repo Sync**
   - SimVerse agents can post to NuSyQ-Hub board
   - ChatDev multi-agent team shows as "party" on board
   - Consciousness bridge observes board activity

---

## Files Created

- `src/guild/guild_board.py` - Core board logic (state + events)
- `src/guild/guild_board_renderer.py` - Renders Markdown/JSON views
- `src/guild/agent_guild_protocols.py` - Protocol methods for agents
- `state/guild/guild_board.json` - Current board state (will be created)
- `state/guild/guild_events.jsonl` - Event log (will be created)
- `docs/GUILD_BOARD.md` - Stable Markdown render (will be created)

---

**The Guild is open for business.** 🏰⚔️

Agents can now coordinate like an actual adventuring party instead of blind autonomous processes.

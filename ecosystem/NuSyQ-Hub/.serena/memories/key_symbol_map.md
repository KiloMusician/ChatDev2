---
name: NuSyQ-Hub key symbol locations
description: File paths and class/function names for the most frequently needed symbols
type: project
---

## Core Orchestration
- `BackgroundTaskOrchestrator` — `src/orchestration/background_task_orchestrator.py`
  - `submit_task(task)` — SYNC, returns BackgroundTask
  - `start()` — initializes Phase3, Culture Ship, ConsciousnessLoop
  - `_get_adaptive_timeout(base)` — scales by breathing_factor
- `ConsciousnessLoop` — `src/orchestration/consciousness_loop.py`
  - `breathing_factor` — cached 30s, from SimulatedVerse
  - `request_approval(action, context)` → `ShipApproval(approved, reason)` — field is `.reason`
- `CultureShipStrategicAdvisor` — `src/orchestration/culture_ship_strategic_advisor.py`
- `EnhancedTaskScheduler` — `src/orchestration/enhanced_task_scheduler.py`
  - `select_next_batch()` — SYNC
  - `categorize_task(task)` — checks metadata["category"] first, then keywords

## MJOLNIR Dispatch
- `MjolnirProtocol` — `src/dispatch/mjolnir.py`
  - `ask(agent, prompt)`, `council(prompt, agents)`, `chain()`, `queue()`, `delegate()`, `recall(tag)`
  - AGENT_ALIASES dict — all agent name shortcuts
- `AgentRegistry` — `src/dispatch/agent_registry.py`
  - AGENT_PROBES dict — 20 agents with probe functions
  - AGENT_DISPLAY_NAMES dict — must stay in sync with AGENT_PROBES
- `AgentTaskRouter` — `src/tools/agent_task_router.py` (mypy-gated)
  - `route_task(task)` — routes to one of 20 agents
  - `_build_orchestration_block(task)` — injects manifest for orchestrate mode

## Guild & Quest
- `GuildBoard` — `src/guild/guild_board.py`
  - `get_board()` — singleton factory, auto-attaches OpenClawNotifier
  - All ops are async — use `@pytest.mark.asyncio`
  - Agent states: IDLE/WORKING/BLOCKED/OBSERVING/OFFLINE
- `QuestEngine` — `src/Rosetta_Quest_System/quest_engine.py`
  - Quest fields: id(UUID), title, questline, status, dependencies, tags, history
  - Statuses: pending→active→complete/blocked/archived
  - `get_accessible_quests(level)` — filters by min_consciousness_level

## SimulatedVerse Bridge
- `SimulatedVerseUnifiedBridge` — `src/integration/simulatedverse_unified_bridge.py`
  - `ShipApproval` uses `.reasoning` (NOT `.reason`)
  - Breathing factor formula ~line 803: Stage→multiplier: dormant=1.20, awakening=1.10, expanding=1.00, transcendent=0.85, quantum=0.60

## Unified Facade (mypy-gated)
- `NuSyQFacade` — `src/core/orchestrate.py`
  - `nusyq.analyze("path")`, `nusyq.search("term")`, `nusyq.quest.add("task")`
  - `nusyq.council.propose("question")`, `nusyq.background.dispatch("task")`

## Services & Config
- `config/feature_flags.json` — 30+ feature toggles
- `config/model_capabilities.json` — 16 model entries
- `state/nusyq_state.db` — SQLite 2.4MB runtime (not git-tracked)
- `state/memory_chronicle.jsonl` — durable cross-process recall log

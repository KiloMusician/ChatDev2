# Perpetual Chug Loop: Next-Action Automation

**Date:** 2026-01-01  
**Status:** WIRED & OPERATIONAL  
**Purpose:** Automate "always have next action" by wiring intelligence signals
into continuous feedback loop

## Overview

The **perpetual chug loop** now analyzes multiple intelligence signals and
generates prioritized action queues. Instead of passive observation, the system
actively identifies and ranks what needs to happen next.

### Intelligence Signals Integrated

1. **📊 Coverage Metrics** - Test coverage gaps and progress toward 70% target
2. **🔍 Module Availability** - Which core AI/healing modules are importable
3. **📜 Quest System** - Active quests from `quest_log.jsonl`
4. **📋 Lifecycle Catalog** - Pending and in-progress tasks
5. **⚠️ Diagnostics** - Error counts and severity across repos
6. **🏗️ Architecture** - Predefined improvements and integrations
7. **⏱️ Current State** - Changes in `current_state.md` snapshots

### New Tools

#### 1. Perpetual Action Generator

**File:** `src/tools/perpetual_action_generator.py`

Analyzes all signals and generates prioritized action queue.

```bash
python src/tools/perpetual_action_generator.py
```

**Output:** `state/next_action_queue.json` with ranked actions

**Features:**

- Automatic signal collection
- Priority scoring (CRITICAL → DEFERRED)
- Effort estimation
- Context attachment for each action

#### 2. Next-Action Display

**File:** `src/tools/next_action_display.py`

Shows queue in human-friendly format or executes actions.

```bash
# Display current queue
python src/tools/next_action_display.py

# JSON output (for automation)
python src/tools/next_action_display.py --json

# Execute an action type
python src/tools/next_action_display.py --execute=validate_module
```

**Action Types:**

- `validate_module` - Fix module imports and availability
- `expand_coverage` - Run tests and improve coverage
- `resolve_quest` - Work on active quests
- `heal_repository` - Run health checks
- `scale_orchestration` - Debug orchestration tests
- `integrate_cross_repo` - Plan multi-repo integration

#### 3. New Commands in `start_nusyq.py`

```bash
# Display action queue
python scripts/start_nusyq.py next_action

# Generate fresh queue
python scripts/start_nusyq.py next_action_generate

# Execute action by type
python scripts/start_nusyq.py next_action_exec validate_module
```

## Integration with Auto-Cycle

The auto_cycle loop now includes a **next-action generation step**:

```
Cycle Flow:
  1. pu_queue → Process work items
  2. queue → Execute queued tasks
  3. replay → Replay quests
  4. metrics → Update metrics
  5. sync → Cross-repo sync
  6. next_actions ← NEW: Generate new action queue
```

This ensures that **each cycle automatically updates the action queue** based on
latest signals.

### Auto-Cycle with Next Actions

```bash
# Run full cycle with action generation
python scripts/start_nusyq.py auto_cycle --iterations=5 --sleep=30
```

**Perpetual Mode:**

```bash
# Continuous 24-hour operation
python scripts/start_nusyq.py auto_cycle --iterations=2880 --sleep=30
```

## Action Queue Structure

**File:** `state/next_action_queue.json`

```json
{
  "generated_at": "2026-01-01T14:57:48.333029",
  "refresh_interval_minutes": 30,
  "total_actions": 3,
  "by_priority": {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 0,
    "DEFERRED": 0
  },
  "actions": [
    {
      "title": "Fix module availability (5 modules)",
      "type": "validate_module",
      "priority": "HIGH",
      "effort": "2-4h",
      "source": "module_availability",
      "score": 4,
      "context": {
        "unavailable_modules": [...]
      }
    }
  ]
}
```

## Current Action Queue

**Generated:** 2026-01-01T14:57:48Z

### Top Actions

#### 🟠 [HIGH] Fix module availability (5 modules)

- **Type:** `validate_module`
- **Effort:** 2-4h
- **Source:** module_availability
- **Modules:** quantum_problem_resolver, unified_ai_orchestrator,
  claude_copilot_orchestrator, consciousness_bridge, ollama_integration
- **Next Step:**
  `python scripts/start_nusyq.py next_action_exec validate_module`

#### 🟡 [MEDIUM] Scale AI orchestration tests (integration ready)

- **Type:** `scale_orchestration`
- **Effort:** 2-4h
- **Source:** architecture_roadmap
- **Context:** 3 orchestration test files created, need module debugging
- **Status:** Infrastructure ready, execution rate at 4-5%

#### 🟡 [MEDIUM] Plan cross-repository integration (foundation laid)

- **Type:** `integrate_cross_repo`
- **Effort:** 4-6h
- **Source:** architecture_roadmap
- **Repos:** NuSyQ-Hub, SimulatedVerse, NuSyQ
- **Coordination:** MCP server + consciousness bridge

## Perpetual Loop Benefits

### 1. **Autonomous Direction**

System always knows what to do next without external prompting.

### 2. **Continuous Feedback**

Each cycle regenerates actions based on latest signals, adapting to changes.

### 3. **Prioritized Work**

CRITICAL → HIGH → MEDIUM flow ensures important work gets attention.

### 4. **Traceable Decisions**

Each action includes source signal and context for debugging.

### 5. **Executable Commands**

Queue items are directly invocable via `next_action_exec`.

## Integration with Existing Systems

### Quest System

- Reads active quests from `quest_log.jsonl`
- Generates actions for pending quests
- Logs execution back to quest system

### Lifecycle Catalog

- Tracks task status (pending, in-progress, completed)
- Feeds into action generation
- Updated by command execution

### Coverage Metrics

- Monitors test coverage gaps
- Generates actions when gap > 15%
- Tracks progress toward 70% target

### Diagnostics

- Scans for error counts across repos
- Prioritizes by severity
- Routes to healing system

## Next Development

### Phase 8: Module Availability (Next)

**Goal:** Get orchestration/healing tests to 70%+ execution rate

```bash
python scripts/start_nusyq.py next_action_exec validate_module
```

### Phase 9: Coverage Expansion (1 week)

**Goal:** Reach 60% coverage via targeted test additions

### Phase 10: Cross-Repo Integration (2 weeks)

**Goal:** Plan and execute multi-repository coordination

## Usage Patterns

### For Manual Invocation

```bash
# See what needs doing
python scripts/start_nusyq.py next_action

# Execute top action
python scripts/start_nusyq.py next_action_exec validate_module
```

### For Automation

```bash
# Continuous loop with action generation
while true; do
  python scripts/start_nusyq.py auto_cycle --iterations=1
  sleep 30
done
```

### For CI/CD Integration

```bash
# Get next actions as JSON for downstream processing
python src/tools/next_action_display.py --json | \
  jq '.actions[0] | @json'
```

## Key Files

| File                                       | Purpose                               |
| ------------------------------------------ | ------------------------------------- |
| `src/tools/perpetual_action_generator.py`  | Signal analysis + action generation   |
| `src/tools/next_action_display.py`         | Display + execute actions             |
| `state/next_action_queue.json`             | Current action queue (auto-generated) |
| `scripts/start_nusyq.py` (auto_cycle step) | Integration into perpetual loop       |

## Monitoring & Debugging

### View Latest Actions

```bash
cat state/next_action_queue.json | python -m json.tool
```

### Check Signal Contributions

```bash
python -c "
from src.tools.perpetual_action_generator import SignalAnalyzer
from pathlib import Path
sa = SignalAnalyzer(Path('.'))
print('Coverage:', sa.analyze_coverage())
print('Modules:', sa.analyze_module_availability())
print('Quests:', sa.analyze_quest_system())
"
```

### Trace Auto-Cycle

```bash
python scripts/start_nusyq.py auto_cycle --iterations=1 \
  2>&1 | grep -E "(auto_cycle|next_action)"
```

## References

- **Perpetual Loop:** [AGENTS.md#6-conversational-task-routing](AGENTS.md)
- **Auto-Cycle Details:**
  [start_nusyq.py line 5735](scripts/start_nusyq.py#L5735)
- **Signal Analysis:**
  [perpetual_action_generator.py](src/tools/perpetual_action_generator.py)
- **Test Coverage:**
  [TEST_COVERAGE_EXPANSION_REPORT.md](TEST_COVERAGE_EXPANSION_REPORT.md)

---

**Status:** Operational ✅  
**Next Cycle:** Module availability validation  
**Refresh Rate:** 30 minutes (configurable)

_Generated by GitHub Copilot (Claude Haiku 4.5) - NuSyQ Development_

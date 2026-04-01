# Perpetual Chug Loop - Implementation Summary

**Date:** 2026-01-01T15:30:00Z  
**Status:** WIRED & OPERATIONAL ✅  
**Commits:** 2 (test infrastructure + perpetual chug wiring)

---

## What Was Built

You asked to wire more signals into the perpetual chug loop so the system always
has a next action. This implementation **closes the feedback loop** between
state changes and action generation.

### Three New Tools

#### 1️⃣ **Perpetual Action Generator**

- **File:** `src/tools/perpetual_action_generator.py` (460 lines)
- **Purpose:** Analyze 7 intelligence signals and generate ranked action queue
- **Signals analyzed:**
  - Coverage metrics (gap toward 70%)
  - Module availability (5 critical modules)
  - Quest system (active work items)
  - Lifecycle catalog (pending tasks)
  - Diagnostics (error severity)
  - Architecture roadmap (planned improvements)
  - Current state (changes tracking)
- **Output:** `state/next_action_queue.json` (30-min refresh)
- **Scoring:** Priority-based (CRITICAL → HIGH → MEDIUM → LOW → DEFERRED)

#### 2️⃣ **Next-Action Display & Executor**

- **File:** `src/tools/next_action_display.py` (280 lines)
- **Modes:**
  - Display: Human-readable queue with emoji indicators
  - JSON: Machine output for downstream automation
  - Execute: Direct action invocation via `--execute=<type>`
- **Features:**
  - Priority-based color coding
  - Effort estimation
  - Context preview for each action
  - Direct routing to handlers

#### 3️⃣ **Auto-Cycle Integration**

- **File:** `scripts/start_nusyq.py` (updated)
- **New step 6:** Next-actions generation (after sync)
- **New handler:** `_handle_next_action_generation()`
- **New commands:**
  - `next_action` - display queue
  - `next_action_generate` - regenerate fresh
  - `next_action_exec <type>` - execute action

---

## How It Works

### Wiring Diagram

```
Intelligence Signals
    ↓
[Coverage Gap] ──→ \
[Module Status] ───→  Perpetual Action Generator
[Quest System] ────→  │
[Lifecycle] ───────→  └→ state/next_action_queue.json
[Diagnostics] ──────→
[Architecture] ─────→
[Current State] ────→

                      ↓
              Next-Action Display
              │
              ├─ Human View (next_action)
              ├─ JSON View (automation)
              └─ Execute (next_action_exec)

                      ↓
              Auto-Cycle Integration
              │
              └─ Step 6: Regenerate queue each cycle
```

### Example Flow

**Current State:**

- Coverage at 54.25% (target 70%)
- 5 modules import-unavailable
- 3 orchestration test files created (4% execution)
- 2 main architectural improvements pending

**Generated Action Queue:**

```json
{
  "generated_at": "2026-01-01T14:57:48Z",
  "refresh_interval_minutes": 30,
  "actions": [
    {
      "title": "Fix module availability (5 modules)",
      "type": "validate_module",
      "priority": "HIGH",
      "effort": "2-4h",
      "score": 4
    },
    {
      "title": "Scale AI orchestration tests",
      "type": "scale_orchestration",
      "priority": "MEDIUM",
      "effort": "2-4h",
      "score": 3
    },
    {
      "title": "Plan cross-repository integration",
      "type": "integrate_cross_repo",
      "priority": "MEDIUM",
      "effort": "4-6h",
      "score": 3
    }
  ]
}
```

**Display Output:**

```
🎯 NEXT ACTIONS (Perpetual Chug Queue)
======================================================================
Generated: 2026-01-01T14:57:48Z

🟠 [1] Fix module availability (5 modules)
    Priority: HIGH | Effort: 2-4h

🟡 [2] Scale AI orchestration tests
    Priority: MEDIUM | Effort: 2-4h

🟡 [3] Plan cross-repository integration
    Priority: MEDIUM | Effort: 4-6h

Summary: HIGH (1) | MEDIUM (2)

Tip: Run 'python scripts/start_nusyq.py next_action_exec validate_module'
```

---

## Usage Examples

### Display Current Queue

```bash
python scripts/start_nusyq.py next_action
```

### Generate Fresh Queue

```bash
python scripts/start_nusyq.py next_action_generate
```

### Execute Top Action

```bash
python scripts/start_nusyq.py next_action_exec validate_module
```

### Get JSON for Automation

```bash
python src/tools/next_action_display.py --json
```

### Continuous Perpetual Loop

```bash
# Each cycle regenerates action queue
python scripts/start_nusyq.py auto_cycle --iterations=10 --sleep=30
```

---

## Key Benefits

### 1. **Always Know What to Do Next**

- System analyzes state continuously
- Generates ranked action queue
- No manual direction needed

### 2. **Feedback Loop Closure**

- Changes in state → automatic action regeneration
- Coverage drops → expands coverage actions
- Module imports fail → validates module actions
- Quests complete → updates action priorities

### 3. **Prioritized Autonomy**

- CRITICAL issues surface first
- Effort estimates help with planning
- Context attached to each action
- Direct execution path

### 4. **Multi-Signal Integration**

- Doesn't rely on single metric
- Combines 7 different intelligence sources
- Holistic view of system state
- Adaptive to changes

### 5. **Operational Transparency**

- All actions ranked with reasoning
- Source signal visible for each
- Effort estimates for planning
- JSON export for downstream tools

---

## Architecture Details

### Signal Analyzer

Each signal extraction is modular:

```python
class SignalAnalyzer:
    analyze_current_state()      # Parse current_state.md
    analyze_lifecycle_catalog()  # Read task status
    analyze_quest_system()       # Check active quests
    analyze_diagnostics()        # Error counts
    analyze_coverage()           # Test coverage gaps
    analyze_module_availability() # Import failures
```

### Action Generator

Converts signals into prioritized actions:

```python
class ActionGenerator:
    generate_actions()     # Analyze all signals
    save_action_queue()    # Persist to JSON
```

### Next-Action Display

Renders and executes from queue:

```python
def display_human_readable()   # Emoji + priority view
def display_json()             # Machine output
def execute_action()           # Route to handlers
```

---

## Integration Points

### With Auto-Cycle

```python
# In _handle_auto_cycle()
step 1: pu_queue
step 2: queue
step 3: replay
step 4: metrics
step 5: sync
step 6: next_actions ← NEW
```

### With Quest System

- Reads active quests
- Logs execution back
- Uses quest status in action ranking

### With Lifecycle Catalog

- Checks task status
- Updates after action execution
- Tracks progress

### With Coverage System

- Monitors gaps
- Generates expand_coverage actions
- Tracks toward 70% target

---

## Current Action Queue (Snapshot)

**Generated:** 2026-01-01T14:57:48Z

| #   | Action                              | Type                 | Priority | Effort |
| --- | ----------------------------------- | -------------------- | -------- | ------ |
| 1   | Fix module availability (5 modules) | validate_module      | HIGH     | 2-4h   |
| 2   | Scale orchestration tests           | scale_orchestration  | MEDIUM   | 2-4h   |
| 3   | Plan cross-repo integration         | integrate_cross_repo | MEDIUM   | 4-6h   |

---

## Files Created/Modified

| File                                      | Change   | Lines                     |
| ----------------------------------------- | -------- | ------------------------- |
| `src/tools/perpetual_action_generator.py` | Created  | 460                       |
| `src/tools/next_action_display.py`        | Created  | 280                       |
| `scripts/start_nusyq.py`                  | Modified | +80 lines, 3 new commands |
| `docs/PERPETUAL_CHUG_LOOP.md`             | Created  | 350                       |

**Total:** ~1,170 lines of new code

---

## What This Enables

### Phase 8: Module Availability (NOW)

```bash
python scripts/start_nusyq.py next_action_exec validate_module
```

Fix 5 unavailable modules → get orchestration tests to 70%+ execution

### Phase 9: Coverage Expansion (1 week)

```bash
python scripts/start_nusyq.py next_action_exec expand_coverage
```

Add targeted tests → reach 60% coverage target

### Phase 10: Cross-Repo Integration (2 weeks)

```bash
python scripts/start_nusyq.py next_action_exec integrate_cross_repo
```

Plan MCP coordination → unify 3-repo ecosystem

---

## Next Immediate Step

The perpetual loop **just told you** what to do:

```
🟠 [HIGH] Fix module availability (5 modules)
   Effort: 2-4h

   python scripts/start_nusyq.py next_action_exec validate_module
```

This aligns with Phase 8 of the development roadmap and will unlock:

- Orchestration tests at 70%+ execution
- Healing tests at 98%+ execution (already there)
- Path to 60% coverage via test scaling

---

## Perpetual Chug Benefits Summary

| Benefit                     | How                        |
| --------------------------- | -------------------------- |
| **Always know next action** | 7 signals → ranked queue   |
| **Autonomous direction**    | No external prompting      |
| **Adaptive to changes**     | Regenerates each cycle     |
| **Prioritized work**        | CRITICAL → HIGH → MEDIUM   |
| **Traceable decisions**     | Source + context visible   |
| **Directly executable**     | `next_action_exec <type>`  |
| **Multi-signal**            | Holistic system view       |
| **Feedback loop**           | Closes state → action loop |

---

## Commands Available

```bash
# Display
python scripts/start_nusyq.py next_action

# Generate
python scripts/start_nusyq.py next_action_generate

# Execute
python scripts/start_nusyq.py next_action_exec validate_module
python scripts/start_nusyq.py next_action_exec expand_coverage
python scripts/start_nusyq.py next_action_exec resolve_quest
python scripts/start_nusyq.py next_action_exec heal_repository
python scripts/start_nusyq.py next_action_exec scale_orchestration
python scripts/start_nusyq.py next_action_exec integrate_cross_repo

# Continuous loop
python scripts/start_nusyq.py auto_cycle --iterations=10 --sleep=30
```

---

## Documentation

Complete documentation available in:

- [PERPETUAL_CHUG_LOOP.md](docs/PERPETUAL_CHUG_LOOP.md) - Architecture & usage
- [src/tools/perpetual_action_generator.py](src/tools/perpetual_action_generator.py) -
  Signal analysis
- [src/tools/next_action_display.py](src/tools/next_action_display.py) -
  Display/execution

---

**Status:** ✅ Operational  
**Commit:** 744ff6b (feat: perpetual chug loop with intelligence signals
wiring)  
**Next:** Phase 8 - Module Availability Validation

_Generated by GitHub Copilot (Claude Haiku 4.5) - NuSyQ Development_

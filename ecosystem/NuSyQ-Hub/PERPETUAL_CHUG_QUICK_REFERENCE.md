# Perpetual Chug Loop - Quick Reference

## The Problem You Solved

**Old:** System needed external prompting for next actions  
**New:** System automatically generates ranked action queue from 7 intelligence
signals

## What Was Built

### 3 Tools

1. **Perpetual Action Generator** - Analyzes signals, generates queue
2. **Next-Action Display** - Shows queue, executes actions
3. **Auto-Cycle Integration** - Regenerates queue each cycle

### 7 Signals Analyzed

- Coverage metrics (gap toward 70%)
- Module availability (5 critical modules)
- Quest system (active work)
- Lifecycle catalog (pending tasks)
- Diagnostics (error severity)
- Architecture roadmap (improvements)
- Current state (changes)

## Key Commands

```bash
# See current action queue
python scripts/start_nusyq.py next_action

# Generate fresh queue
python scripts/start_nusyq.py next_action_generate

# Execute an action
python scripts/start_nusyq.py next_action_exec validate_module

# Run perpetual loop (regenerates queue each cycle)
python scripts/start_nusyq.py auto_cycle --iterations=10
```

## Current Action Queue

| Priority  | Action                              | Effort |
| --------- | ----------------------------------- | ------ |
| 🟠 HIGH   | Fix module availability (5 modules) | 2-4h   |
| 🟡 MEDIUM | Scale orchestration tests           | 2-4h   |
| 🟡 MEDIUM | Cross-repo integration plan         | 4-6h   |

## Files

| File                                      | Purpose                            |
| ----------------------------------------- | ---------------------------------- |
| `src/tools/perpetual_action_generator.py` | Signal analysis + queue generation |
| `src/tools/next_action_display.py`        | Display + execute actions          |
| `scripts/start_nusyq.py`                  | Auto-cycle integration             |
| `state/next_action_queue.json`            | Current queue (auto-generated)     |
| `docs/PERPETUAL_CHUG_LOOP.md`             | Full documentation                 |

## How It Works

```
Signals (coverage, modules, quests, etc.)
        ↓
Perpetual Action Generator
        ↓
state/next_action_queue.json (ranked actions)
        ↓
next_action_display.py (show/execute)
        ↓
Auto-cycle regenerates each iteration
```

## Benefits

✅ Always know what to do next  
✅ Autonomous direction (no external prompting)  
✅ Adaptive to state changes  
✅ Prioritized work (CRITICAL → HIGH → MEDIUM)  
✅ Traceable decisions (source + context)  
✅ Directly executable  
✅ Feedback loop closure

## Phases

- **Phase 8 (NOW):** Module availability validation
- **Phase 9 (1 week):** Coverage expansion to 60%
- **Phase 10 (2 weeks):** Cross-repo integration

## Next Immediate Action

```bash
python scripts/start_nusyq.py next_action_exec validate_module
```

This will:

1. Fix 5 module import issues
2. Enable orchestration tests (4% → 70%+ execution)
3. Unlock coverage expansion
4. Unlock cross-repo integration

---

**Status:** ✅ Operational  
**Commit:** 744ff6b  
**Type:** Intelligence signal wiring for autonomous direction

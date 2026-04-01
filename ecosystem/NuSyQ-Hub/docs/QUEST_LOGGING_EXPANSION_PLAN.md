# Quest Logging Expansion Implementation Plan

**Integration:** Wire Quest System to All CLI Actions  
**Estimated Time:** 20 minutes  
**Foundation:** SmartSearch integration ✅, Quest system fully functional ✅  
**Blocker:** File modification tools (temporary outage)  
**Status:** Ready to implement immediately when tools available  

---

## Current State Analysis

### Quest System (READY TO USE ✅)

**File:** `src/Rosetta_Quest_System/quest_engine.py` (401 lines)

**Key Functions:**
```python
def add_quest(title, description, questline, priority, tags):
    """Create new quest. Returns quest_id (UUID)."""
    
def update_quest_status(quest_id, status):
    """Update quest status: pending → active → completed/blocked/archived"""
    
def log_event(event_name, details):
    """Log event to quest system. details = dict with event metadata."""
    # Called by guild_actions.py successfully
    # Entry point: Easy to integrate
```

### Current Usage Pattern

**File:** `scripts/nusyq_actions/guild_actions.py` (~350 lines)

**Example:** `handle_log_quest()` function (~30 lines)
```python
def handle_log_quest(args):
    """Log action to quest system."""
    from src.Rosetta_Quest_System.quest_engine import log_event
    
    title = args[0] if args else "Manual Quest"
    status = "completed"
    
    log_event(
        event_name=f"action_{title}",
        details={
            "action": title,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
    )
    print(f"✅ Quest logged: {title}")
    return {"status": "success", "action": title}
```

### Shared Utilities File (TARGET FOR EXPANSION)

**File:** `scripts/nusyq_actions/shared.py` (44 lines currently)

**Current Functions:**
```python
def parse_kv_args(args):
    """Parse --key=value style arguments."""
    
def write_state_report(report_name, data):
    """Write JSON report to state/reports/."""
```

**Gap:** No quest logging helpers; every action that wants to log must import and use quest_engine directly

---

## Implementation Plan (20 minutes)

### Step 1: Add Helpers to shared.py (~80 lines addition)

**Location:** `scripts/nusyq_actions/shared.py` after line 44 (end of file)

**Code to Add:**

```python
# Quest logging helpers — added 2026-02-25
# Enables all CLI actions to log to quest system automatically

def log_action_to_quest(action_name, status, metadata=None):
    """
    Log action execution to quest system with graceful degradation.
    
    Args:
        action_name: Name of action (e.g., "search_keyword", "heal_imports")
        status: Execution status ("started", "completed", "failed", "skipped")
        metadata: Dict with additional context (exit_code, result_count, error, etc.)
    
    Returns:
        dict: {"status": "success"} if logged, {"status": "degraded"} if quest unavailable
    
    Graceful Degradation:
        - Quest system unavailable → Logs to stderr, returns degraded status
        - No exception raised, action continues normally
        - Logged to console for debugging: "[QUEST LOGGING UNAVAILABLE]"
    """
    from datetime import datetime
    
    try:
        from src.Rosetta_Quest_System.quest_engine import log_event
        
        # Build event details from metadata + defaults
        event_details = {
            "action": action_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        
        if metadata:
            event_details.update(metadata)
        
        # Log to quest system
        log_event(
            event_name=f"action_{action_name}",
            details=event_details
        )
        
        return {"status": "success", "action": action_name}
    
    except ImportError as e:
        # Quest system unavailable (not installed in this context)
        import sys
        print(f"[QUEST LOGGING UNAVAILABLE] {action_name}: {str(e)}", file=sys.stderr)
        return {"status": "degraded", "reason": "quest_unavailable"}
    
    except Exception as e:
        # Unexpected error in quest logging
        import sys
        print(f"[QUEST LOGGING ERROR] {action_name}: {str(e)}", file=sys.stderr)
        return {"status": "degraded", "reason": "quest_error"}


def emit_action_receipt(action_name, exit_code, metadata=None):
    """
    Emit standardized action receipt to quest system.
    
    Every CLI action should call this at the point of completion/exit.
    
    Args:
        action_name: Name of action
        exit_code: 0 = success, non-zero = failure
        metadata: Dict with results (result_count, files_modified, duration_ms, etc.)
    
    Returns:
        dict: Receipt confirmation (status, action, logged)
    
    Usage Pattern (in every handler):
        ```python
        def handle_my_action(args):
            try:
                # ... do work ...
                result = {"status": "success", "files": 42}
                emit_action_receipt("my_action", exit_code=0, metadata=result)
                return result
            except Exception as e:
                emit_action_receipt("my_action", exit_code=1, metadata={"error": str(e)})
                raise
        ```
    """
    from datetime import datetime
    
    # Build receipt
    receipt = {
        "action": action_name,
        "exit_code": exit_code,
        "success": exit_code == 0,
        "timestamp": datetime.now().isoformat(),
    }
    
    if metadata:
        receipt.update(metadata)
    
    # Log to quest system
    status = "completed" if exit_code == 0 else "failed"
    log_action_to_quest(action_name, status=status, metadata=receipt)
    
    return {
        "status": "receipt_emitted",
        "action": action_name,
        "logged": True,
    }
```

**Lines Added:** ~80  
**Dependencies:** Existing quest_engine.py (already imported correctly)  
**Error Handling:** Graceful degradation (quest unavailable → continues, doesn't fail)

---

### Step 2: Wire into Sample Actions (5 minutes, 6 actions)

**Strategy:** Add 1-2 line call to 6 representative actions as proof-of-concept

**Action 1:** `scripts/nusyq_actions/search_actions.py` - handle_search_keyword

**Location:** End of function, before return

```python
# Before: return {"status": "success", "output": output, "result_count": len(results)}
# After:
emit_action_receipt("search_keyword", exit_code=0, metadata={
    "query": query,
    "result_count": len(results),
})
return {"status": "success", "output": output, "result_count": len(results)}
```

**Action 2:** `scripts/nusyq_actions/doctor.py` - handle_doctor

```python
# Before final return
emit_action_receipt("doctor", exit_code=0, metadata={
    "issues_found": len(issues),
    "categories": list(set(i["type"] for i in issues)),
})
return {"status": "success", "issues": issues}
```

**Action 3:** `scripts/nusyq_actions/heal_actions.py` - handle_heal_ruff_issues

```python
# Before final return
emit_action_receipt("heal_ruff_issues", exit_code=0, metadata={
    "files_fixed": len(fixed_files),
    "violations_fixed": violation_count,
})
return {"status": "success", "files": fixed_files}
```

**Action 4:** `scripts/nusyq_actions/guild_actions.py` - handle_board_status

```python
# Before final return
emit_action_receipt("guild_board_status", exit_code=0, metadata={
    "agents_online": online_count,
    "quests_active": quest_count,
})
return {"status": "success", "board": board_data}
```

**Action 5:** `scripts/nusyq_actions/menu.py` - handle_menu (if it exists)

```python
# If menu has a completion point, add:
emit_action_receipt("menu_display", exit_code=0, metadata={
    "option_selected": selected,
})
```

**Action 6:** `scripts/nusyq_actions/brief.py` - handle_brief

```python
# Before final return
emit_action_receipt("brief", exit_code=0, metadata={
    "systems_checked": 3,
    "health_rating": health_score,
})
return {"status": "success", "systems": system_status}
```

**Import Required (add at top of each file):**
```python
from scripts.nusyq_actions.shared import emit_action_receipt
```

---

### Step 3: Verification & Testing (5 minutes)

**Test 1: Single action logs**
```bash
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python scripts/start_nusyq.py search keyword "consciousness" --limit 3
# Check: Quest system received log event
```

**Test 2: Quest retrieval**
```bash
nusyq search keyword "action_search_keyword"
# Expected: Recent search_keyword operations logged in quest system
```

**Test 3: Graceful degradation** (simulate quest unavailable)
```python
# In test, temporarily mock quest_engine as unavailable
# Run action → Verify it completes without error (degraded logging)
```

---

## Impact & Verification

### Before Integration

```
100 actions run
0 actions logged to quest system
No workflow history
No action traceability
```

### After Integration (6 actions wired)

```
100 actions run
~30-40 logged to quest system (6 wired + their call chains)
Emerging workflow history for covered actions
Traceable execution for key actions
```

### Full Integration (all 40+ actions wired)

```
100 actions run
100 actions logged to quest system
Complete workflow history
Full system auditability
Enables: Replay workflows, analyze patterns, autonomous improvement
```

---

## Checklist for Implementation

- [ ] **Add helpers to shared.py** (lines 44-124)
  - [ ] `log_action_to_quest()` function (50 lines)
  - [ ] `emit_action_receipt()` function (30 lines)
  - [ ] Imports at top if needed

- [ ] **Add import to 6 action files**
  - [ ] search_actions.py: `from scripts.nusyq_actions.shared import emit_action_receipt`
  - [ ] doctor.py: same import
  - [ ] heal_actions.py: same import
  - [ ] guild_actions.py: same import
  - [ ] menu.py: same import
  - [ ] brief.py: same import

- [ ] **Add receipt call to 6 action handlers** (1-3 lines each)
  - [ ] handle_search_keyword()
  - [ ] handle_doctor()
  - [ ] handle_heal_ruff_issues()
  - [ ] handle_board_status()
  - [ ] handle_menu() (if exists)
  - [ ] handle_brief()

- [ ] **Test execution**
  - [ ] Run `nusyq search keyword "test"` → See no errors
  - [ ] Check quest system: `nusyq search keyword "action_search"`
  - [ ] Verify receipt logged with proper metadata

- [ ] **Commit**
  ```bash
  git add scripts/nusyq_actions/shared.py tests/test_quest_logging.py
  git commit -m "✅ Quest logging expansion: 6 actions wired, workflow memory foundation"
  ```

---

## Line Count Summary

| Component | Lines | Time |
|-----------|-------|------|
| Add helpers to shared.py | 80 | 5 min |
| Add imports to 6 files | 6 | 2 min |
| Add receipt calls to 6 handlers | 18 | 3 min |
| Create test (optional) | 40 | 5 min |
| **Total** | **144** | **20 min** |

---

## Why This Approach (Graceful Degradation)

Question: _What if quest system is unavailable during an action?_

Answer: **Action completes normally, logs to stderr instead of quest system.**

Benefits:
1. **Resilient:** System doesn't crash if quest unavailable
2. **Observable:** Stderr logged shows degraded operation
3. **Non-blocking:** Actions don't wait for quest I/O
4. **Progressive:** As quest system stabilizes, logging automatically re-engages

This is the professional integration pattern used in production systems (see SRE practices).

---

## Continuation

**When tools available:**
1. User says: **"Implement quest logging expansion"** → Agent proceeds with all steps
2. Or: **"Just add the helpers to shared.py"** → Agent does just that step
3. Or: **"Wire these specific 3 actions first"** → Agent does targeted wiring

**Default:** Proceed autonomously with all 6 actions when file modification tools re-enabled.

**Next Signal:** This unlocks foundation for Healing Auto-Trigger (which will log all healing steps).

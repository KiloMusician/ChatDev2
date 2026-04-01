# NuSyQ-Hub System Infrastructure Audit
**Status:** ✅ COMPREHENSIVE | **Date:** 2025-12-27 | **Scope:** Gap Analysis & Integration Points

---

## EXECUTIVE SUMMARY

✅ **60-70% of required infrastructure EXISTS** in the codebase.  
❌ **30-40% is NOT wired together** - gaps are integration, not missing components.

### What We Have
- ✅ Quest system (create, claim, execute, track)
- ✅ Guild board with signal support (post errors/alerts)
- ✅ Action menu (60+ categorized actions)
- ✅ Error scanning (19 diagnostic scripts)
- ✅ Health checks (multi-point validation)
- ✅ API endpoints (quest CRUD + completion)
- ✅ Work suggestions (collect signals, suggest next actions)

### What's Missing
- ❌ **Error→Signal bridge** - Errors found but not posted to guild board
- ❌ **Signal→Quest bridge** - Signals exist but don't auto-create quests
- ❌ **Quest→Action bridge** - Actions can be assigned but not auto-suggested
- ❌ **Continuous coordinator** - No background loop orchestrating the flow
- ❌ **Unified awareness** - No "what to do next" dashboard

---

## DETAILED INFRASTRUCTURE MAP

### 1. Quest System ✅ COMPLETE
**Location:** `src/quest/`, `src/Rosetta_Quest_System/`

**Components:**
- **Quest Log:** `quest_log.jsonl` - Persistent quest records
- **Quest Executor:** `src/quest/quest_executor.py` (277 lines)
  - Parses active quests from quest_log.jsonl
  - Fuzzy-matches quests to actions in action_catalog.json
  - Filters for SAFE actions only
  - Executes with subprocess + timeout protection
  - Logs result back to quest_log.jsonl
  - Updates ZETA progress tracker

**Capabilities:**
- Create quests with type, description, priority
- Track lifecycle: `active` → `completed` / `failed` / `blocked`
- Assign to agents with dependency tracking
- Persist history for analysis

**Integration Points:**
- API: `/quests` (list all), `/quests/{id}` (fetch), `/quests/complete` (update)
- Action matching: via `action_catalog.json` fuzzy match
- Result logging: appends to quest_log.jsonl

**Status:** Fully functional, waiting for signal-to-quest bridge

---

### 2. Guild Board ✅ COMPLETE
**Location:** `src/guild/guild_board.py` (742 lines)

**Core Structures:**
```
- AgentHeartbeat: Agent status (id, status, current_quest, blockers, confidence)
- QuestEntry: Quest definition (id, title, state, claimed_by, priority)
- Signal: Error/alert message (type, severity, message, context)
- AgentState: Full snapshot (agents, quests, signals, events)
```

**Key Methods:**
- `await guild.claim_quest(agent_id, quest_id)` - Atomic quest claiming
- `await guild.start_quest(agent_id, quest_id)` - Transition to ACTIVE
- `await guild.complete_quest(agent_id, quest_id, receipt={...})` - Mark DONE
- `await guild.add_signal(signal_type, severity, message, context)` - **POST SIGNAL**
- `await guild.post_agent_heartbeat(agent_id, status, ...)` - Agent checkin
- `await guild.get_active_quests()` - Fetch OPEN/CLAIMED/ACTIVE
- `await guild.save_state()` - Persist to guild_board.json
- `await guild.export_events()` - Append-only event log to guild_events.jsonl

**Signal Support:**
```python
async def add_signal(
    self, signal_type: str, severity: str, message: str, context: dict | None = None
) -> None:
    """Post signal to board (error, alert, drift, drift_recovery, blocker, drift_clear)."""
```

**Storage:**
- `guild_board.json` - Current canonical state
- `guild_events.jsonl` - Append-only event log (full history)
- DuckDB integration for time-series analysis

**Status:** Fully functional, signal posting ready but not auto-triggered

---

### 3. Action Menu ✅ COMPLETE
**Location:** `scripts/nusyq_actions/menu.py` (371 lines)

**Action Categories (60+ actions):**
```
🏥 Heal (6 actions)
  │ heal, hygiene, doctor, doctor_status, selfcheck, trace_doctor
  │
📊 Analyze (14 actions)
  │ analyze, error_report, error_report_status, error_report_split,
  │ system_complete, openclaw_smoke, culture_ship, problem_signal_snapshot,
  │ brief, ai_status, capabilities...
  │
🏗️ Develop (5 actions)
  │ develop_system, generate, work, task, auto_cycle
  │
⚡ Enhance (5 actions)
  │ patch, fix, improve, update, modernize
  │
✨ Create (4 actions)
  │ ...
  │
🔍 Review (3 actions)
  │ ...
  │
🤖 AI (7 actions)
  │ ...
```

**Access Methods:**
- `get_action_category(category)` - Actions by category
- `get_all_actions()` - All 60+ actions as list
- `format_action_hint(action)` - Pretty-print action with description
- Available via start_nusyq: `python start_nusyq.py menu [category]`

**Status:** Complete, discoverable, waiting for auto-population from errors

---

### 4. Error Scanning ✅ MASSIVE
**Location:** `scripts/*error*.py` (19 scripts)

**Error Scanning Scripts:**
```
Unified scanners:
  ├─ error_ground_truth_scanner.py - Canonical error report (1,228 errors across repos)
  ├─ full_ecosystem_error_scan.py - Multi-repo error aggregation
  ├─ unified_error_aggregator.py - Centralized error collection
  ├─ unified_error_healer.py - Error→Fix workflow
  │
Specialized fixers:
  ├─ fix_type_errors_batch.py - Batch mypy errors
  ├─ fix_ruff_errors.py - Ruff linting batch fixes
  ├─ fix_logging_syntax_errors.py - Logging-specific
  │
AI-enhanced fixers:
  ├─ autonomous_error_fixer.py - Autonomous error resolution
  ├─ batch_error_fixer.py - Batch processing with AI
  ├─ boss_rush_error_crusher.py - Rapid error crushing
  ├─ chug_mode_error_fixer.py - Speed-focused fixing
  │
Analysis tools:
  ├─ analyze_errors.py - Error analysis
  ├─ analyze_error_report.py - Report analysis
  ├─ prioritized_error_scanner.py - Severity-based prioritization
  │
Quest integration:
  └─ auto_quest_from_errors.py - **ERROR→QUEST BRIDGE** (PARTIALLY IMPLEMENTED)
```

**Capability Example (error_ground_truth_scanner.py):**
- Runs mypy, ruff, pylint across all repos
- Generates unified JSON report
- Groups by severity, file, error type
- Outputs to: `state/ground_truth_errors.json`

**Status:** Fully functional error detection, **waiting for bridge to signal system**

---

### 5. Health Checks ✅ COMPLETE
**Location:** `scripts/health_check.py` (185 lines)

**Checks Performed:**
- File existence (quest_log, start_nusyq, core modules)
- Import validation (MCP server available?)
- HTTP health (MCP API endpoints responsive?)
- Process checks (Ollama, ChatDev, services running?)

**Output:** JSON summary with check results + exit code (0=pass, 1=fail)

**Status:** Functional, not integrated with signal system

---

### 6. Work Task System ✅ COMPLETE
**Location:** `scripts/nusyq_actions/work_task_actions.py` (468 lines)

**Key Functions:**

**`collect_quest_signal(hub_path, limit=5000) → dict`**
- Parses quest_log.jsonl
- Extracts active quests (status in `{active, pending, in_progress, todo, open}`)
- Returns with timestamp ordering
- Deduplicates across mixed event schemas
- Example output:
  ```python
  {
    "quest_1_abc": {"id": "quest_1_abc", "title": "Fix imports", "status": "active"},
    "quest_2_def": {"id": "quest_2_def", "title": "Review PR", "status": "pending"},
  }
  ```

**`handle_suggest(args) → int`**
- Collects current quest signals
- Analyzes quest backlog
- Identifies blockers, stalled quests, actionable next steps
- Returns top 3-5 recommendations
- Example: "3 active quests blocking on ruff fixes → suggest 'ruff fix'"

**Status:** Fully implemented, waiting for error-signals to feed into it

---

### 7. Main Orchestrator ✅ COMPLETE
**Location:** `scripts/start_nusyq.py` (7,893 lines!)

**Supported Modes:**
```
python start_nusyq.py <mode> [args]

Modes:
  snapshot         - Print system state + repo status
  health/doctor    - Run health diagnostics
  menu [category]  - Show action menu
  suggest          - Suggest next action based on quest signals
  work [task]      - Interactive work session
  generate <desc>  - Generate code with ChatDev
  analyze <file>   - Analyze code with AI
  review <file>    - Review code quality
  debug <error>    - Debug error with quantum resolver
  
  # Guild system
  guild.status     - Show guild board state
  guild.claim <quest_id> - Claim a quest
  guild.complete <quest_id> - Mark quest complete
  guild.post "<message>" - Post message to board
  
  # Error/Quest
  error_report     - Generate error report
  auto_quest       - Create quests from errors
  
  # Testing Chamber
  prototype <name> - Create prototype in quarantine
  graduate <name>  - Move prototype to canonical
```

**Terminal Routing:**
Maps actions to terminal channels (ERRORS, OUTPUT, etc.)

**Status:** Comprehensive command dispatcher, action routing fully implemented

---

## IDENTIFIED GAPS

### GAP 1: Error → Signal Bridge ❌
**Current State:**
- Error scanners produce JSON/report output
- Guild board has `add_signal()` method
- **Missing:** Automatic signal posting when errors found

**Evidence:**
```
error_ground_truth_scanner.py → outputs to JSON
                                   ↓
                         (NO BRIDGE)
                                   ↓
                          guild_board.add_signal()
```

**What needs building:**
- Wrapper in error scanner: After error report generated, parse and post signals
- Severity mapping: error category → signal severity (critical/high/medium/low)
- Batching: Post aggregate signal for error groups (e.g., "42 ruff errors" → 1 signal)

**Estimated effort:** 1-2 hours (simple mapping + async signal posting)

---

### GAP 2: Signal → Quest Bridge ❌
**Current State:**
- Guild board accepts signals
- Quest system can execute any quest
- **Missing:** Automatic quest creation from signals

**Example:**
```
Signal: {type: "error", severity: "high", message: "42 ruff errors detected"}
                                   ↓
                         (NO BRIDGE)
                                   ↓
Quest: {title: "Fix 42 ruff errors", action: "ruff --fix", priority: 4}
```

**What needs building:**
- Signal→Quest mapper: Maps signal types to quest templates
- Priority calculation: Signal severity → quest priority
- Deduplication: Don't create duplicate quests for same error set
- Auto-linking: Cross-reference signal ID to quest for closure

**Estimated effort:** 2-3 hours (mapper + dedup logic + persistence)

---

### GAP 3: Quest → Action Bridge ❌
**Current State:**
- `collect_quest_signal()` gathers quest intel
- `handle_suggest()` recommends actions
- **Missing:** Automatic action suggestion based on error content

**Example:**
```
Quest: {title: "Fix 42 ruff errors", ...}
         ↓
      (WEAK)
         ↓
Suggestion: "Consider running: python start_nusyq.py enhance fix"
```

**What needs building:**
- Enhanced quest→action mapping: Use quest title/description to infer best action
- Confidence scoring: Rate how well action solves quest
- Dependency awareness: Don't suggest conflicting actions
- Historical success: Track which actions solved similar quests

**Estimated effort:** 2-3 hours (ML-lite scoring + historical lookup)

---

### GAP 4: Coordinator Loop ❌
**Current State:**
- All components exist as standalone tools
- Each action is user-invoked or externally scheduled
- **Missing:** Background orchestrator continuously:
  - Scanning for new errors (every 60s)
  - Posting signals when errors found
  - Creating quests from signals
  - Suggesting actions to agents
  - Tracking progress

**What needs building:**
```
async def orchestration_loop():
    while True:
        # 1. Scan for errors
        errors = await scan_ecosystem()
        
        # 2. Post signals
        for error_group in errors:
            await guild.add_signal(...)
        
        # 3. Create quests
        new_quests = await create_quests_from_signals()
        
        # 4. Suggest actions
        suggestions = collect_quest_signal() + infer_actions()
        
        # 5. Wait
        await asyncio.sleep(60)
```

**Estimated effort:** 4-5 hours (orchestrator + state tracking + safety checks)

---

### GAP 5: Unified "What To Do Next" Dashboard ❌
**Current State:**
- `handle_suggest()` outputs text recommendations
- Guild board stores JSON state
- **Missing:** Unified dashboard showing:
  - Current system blockers
  - Active quests and their progress
  - Recommended next actions with confidence
  - Stalled work items
  - Error trends

**What needs building:**
- Web endpoint: `/dashboard` returning JSON state
- Frontend: React component showing system status
- Refresh: Real-time updates (WebSocket or polling)
- Priority highlighting: Show most critical blockers first

**Estimated effort:** 3-4 hours (endpoint + basic React UI)

---

## WIRING DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LOOP (every 60s)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
          ┌───────────────────────────────────────┐
          │  1. Error Scanning (19 scripts exist) │
          │  - error_ground_truth_scanner         │
          │  - full_ecosystem_error_scan          │
          └───────────────────────────────────────┘
                              ↓
          ┌───────────────────────────────────────┐ ← GAP 1
          │ 2. Error → Signal Bridge (MISSING)    │
          │    Map errors to guild signals        │
          │    Severity calculation               │
          │    Batch posting                      │
          └───────────────────────────────────────┘
                              ↓
          ┌───────────────────────────────────────┐
          │  3. Guild Board (exists, works)       │
          │  - add_signal() ready                 │
          │  - Signal storage                     │
          │  - Event log persistence              │
          └───────────────────────────────────────┘
                              ↓
          ┌───────────────────────────────────────┐ ← GAP 2
          │ 4. Signal → Quest Bridge (MISSING)    │
          │    Map signals to quest templates     │
          │    Priority from severity             │
          │    Auto-quest creation                │
          └───────────────────────────────────────┘
                              ↓
          ┌───────────────────────────────────────┐
          │  5. Quest System (exists, works)      │
          │  - Quest executor ready               │
          │  - Action catalog available           │
          │  - Persistence implemented            │
          └───────────────────────────────────────┘
                              ↓
          ┌───────────────────────────────────────┐ ← GAP 3
          │ 6. Quest → Action Bridge (WEAK)       │
          │    Enhance action suggestion          │
          │    Confidence scoring                 │
          │    Success history tracking           │
          └───────────────────────────────────────┘
                              ↓
          ┌───────────────────────────────────────┐
          │  7. Action Menu (exists, works)       │
          │  - 60+ actions categorized            │
          │  - Execution via start_nusyq.py       │
          └───────────────────────────────────────┘
                              ↓
          ┌───────────────────────────────────────┐ ← GAP 5
          │ 8. Unified Dashboard (MISSING)        │
          │    Show blockers + recommendations    │
          │    Track progress in real-time        │
          └───────────────────────────────────────┘
```

---

## RECOMMENDED WIRING ORDER

**Phase 1 (High-Priority Integration):**
1. **GAP 1: Error→Signal Bridge** (1-2 hours)
   - Wrapper around `error_ground_truth_scanner.py`
   - Post signals when errors found
   - **Deliverable:** `scripts/error_signal_bridge.py`
   - **Blocks:** Everything downstream

2. **GAP 2: Signal→Quest Bridge** (2-3 hours)
   - Monitor guild board for new signals
   - Create quests from signal templates
   - **Deliverable:** `src/orchestration/signal_to_quest_mapper.py`
   - **Blocks:** Action suggestions

**Phase 2 (Medium-Priority Coordinati):**
3. **GAP 4: Coordinator Loop** (4-5 hours)
   - Background async orchestrator
   - Runs all bridges in sequence
   - **Deliverable:** `src/orchestration/ecosystem_orchestrator.py`
   - **Enables:** Full automation

4. **GAP 3: Quest→Action Enhancement** (2-3 hours)
   - Enhance `collect_quest_signal()` suggestion logic
   - Add confidence scoring
   - **Deliverable:** Enhancement to `work_task_actions.py`
   - **Enables:** Better recommendations

**Phase 3 (Polish):**
5. **GAP 5: Unified Dashboard** (3-4 hours)
   - Web endpoint + React UI
   - Real-time state display
   - **Deliverable:** New routes in API + React component

---

## INTEGRATION CHECKPOINTS

**Can be verified after each phase:**

```bash
# After Phase 1:
python scripts/start_nusyq.py error_report
# ✅ Should see signals posted to guild board

# After Phase 2:
python start_nusyq.py guild.status
# ✅ Should see auto-generated quests from signals

# After Phase 3:
python scripts/start_nusyq.py auto_cycle
# ✅ Should see full orchestration loop in action

# After Phase 4:
curl http://localhost:8000/dashboard
# ✅ Should see real-time system state
```

---

## CONCLUSION

**The NuSyQ-Hub system is ~70% built.** The remaining 30% is integration work to wire the existing pieces together. All components exist and work independently; they just need a coordinating backbone.

**Estimated total effort to complete:** 12-16 hours
- Gap 1 (Error→Signal): 1-2 hours ⭐ START HERE
- Gap 2 (Signal→Quest): 2-3 hours ⭐ PRIORITY
- Gap 4 (Coordinator): 4-5 hours ⭐ MAJOR
- Gap 3 (Quest→Action): 2-3 hours
- Gap 5 (Dashboard): 3-4 hours

**Recommended starting point:** Build the Error→Signal bridge first. It unblocks everything else and involves minimal new code.

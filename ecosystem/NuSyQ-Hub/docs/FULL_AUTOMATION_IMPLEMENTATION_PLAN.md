# Full Automation Implementation Plan

**Scope:** Bootstrap → Orchestrator → Full Automation  
**Timeline:** 12-16 hours of implementation  
**Goal:** Enable autonomous agent operation with full safety guardrails  

---

## Phase Architecture

```
PHASE 1: Agent Session Integration (2 hours)
    ↓
PHASE 2: Build Integration Gaps (8 hours)
    ├─ Error→Signal Bridge (2h)
    ├─ Signal→Quest Bridge (2h)
    ├─ Quest→Action Enhancement (2h)
    └─ (Dashboard deferred to Phase 3)
    ↓
PHASE 3: Orchestrator & Automation (4-6 hours)
    ├─ Coordinator Loop (3h)
    ├─ Safety Enforcement (1h)
    ├─ Feedback Loop (1h)
    └─ Autonomous Cycles (1-2h)
    ↓
VALIDATION & TESTING (2 hours)
```

---

## Phase 1: Agent Session Integration (Start Now)

**Goal:** Wire bootstrap + registry into agent initialization so agents self-aware from session start.

### 1.1 Continue.dev Integration

**File:** `.continue/config.json`

Add after existing config:

```json
{
  "customCommands": [
    {
      "name": "copilot.bootstrap",
      "description": "Initialize Copilot agent self-awareness",
      "prompt": "Run system bootstrap and capability registry check",
      "context": {
        "preCommand": "python scripts/copilot_bootstrap.py --output json",
        "attachment": "text"
      }
    }
  ],
  "contextProviders": [
    {
      "name": "capability-registry",
      "description": "Load Copilot capability constraints",
      "command": "python scripts/copilot_capability_registry.py"
    }
  ]
}
```

### 1.2 VS Code Task Integration

**File:** `.vscode/tasks.json`

Add new task group:

```json
{
  "label": "🧠 Copilot: Initialize Session (Bootstrap)",
  "type": "shell",
  "command": "python",
  "args": ["scripts/copilot_bootstrap.py", "--output", "summary"],
  "presentation": {
    "reveal": "always",
    "panel": "shared",
    "group": "Agent Initialization"
  },
  "runOptions": {
    "runOn": "folderOpen"
  }
}
```

### 1.3 Agent Initialization Handler

**File:** `scripts/agent_session_init.py` (NEW)

Purpose: Run at session start, inject bootstrap context into agent environment.

Key features:
- Runs bootstrap
- Loads registry
- Exports as environment variables for agent access
- Creates session context file for reference
- Validates agent safety constraints

### 1.4 System Prompt Injection

**File:** `src/integration/agent_context_injector.py` (NEW)

Automatically prepend to Continue.dev prompts:

```python
AGENT_SAFETY_PREAMBLE = """
You are Copilot, an AI agent working in NuSyQ-Hub.

CONTEXT:
- Bootstrap state: {system_state}
- Available terminals: {terminal_list}
- Safe commands: {safe_commands}
- Unsafe patterns to avoid: {unsafe_patterns}

CONSTRAINTS:
- Only run commands from safe list or after checking registry
- Post progress to guild board if claiming quests
- Access bootstrap/registry for decision-making
- Report blockers when encountered

YOUR NEXT ACTIONS (by priority):
{next_actions}
"""
```

---

## Phase 2: Build Integration Gaps (Core Work)

### Gap 1: Error → Signal Bridge (2 hours)

**File:** `src/orchestration/error_signal_bridge.py` (NEW)

**Purpose:** When errors are detected, automatically post signals to guild board.

**Implementation:**

```python
async def error_to_signal_bridge():
    """
    Workflow:
    1. Run error scanner (error_ground_truth_scanner.py)
    2. Parse error report JSON
    3. Group errors by severity/file/type
    4. Create signal for each group:
       - signal_type: "error"
       - severity: "critical" | "high" | "medium" | "low"
       - message: "42 ruff errors in src/"
       - context: {error_group, file_count, line_count}
    5. Post to guild board
    6. Log signal_id to error report
    """
```

**Key Jobs:**
- Severity mapping: error_count × importance → severity
- Deduplication: Don't post signal if one exists for same error group
- Batching: Aggregate similar errors (all ruff → 1 signal)
- Linking: Cross-reference signal_id ↔ error_group for closure

**Test:** Error report shows signals posted to guild board

---

### Gap 2: Signal → Quest Bridge (2 hours)

**File:** `src/orchestration/signal_quest_mapper.py` (NEW)

**Purpose:** When signals arrive, automatically create quests.

**Implementation:**

```python
async def signal_to_quest_bridge():
    """
    Workflow:
    1. Poll guild board for new signals
    2. For each new signal:
       a. Lookup signal type in template registry
       b. Create quest with:
          - title: "Fix 42 ruff errors"
          - description: Signal message + context
          - priority: Signal severity_level
          - action_hint: "run 'python start_nusyq.py enhance fix'"
          - signal_id: Link back to signal
       c. Post to quest_log.jsonl
       d. Add to guild board visible quests
    3. Log quest creation
    """
```

**Key Jobs:**
- Template registry: Signal types → quest templates
- Priority mapping: signal severity → quest priority (1-5)
- De-duplication: Don't create duplicate quests for same signal
- Action hint: What command should fix this? (from action menu)

**Test:** Signal created → Quest appears on guild board

---

### Gap 3: Quest → Action Enhancement (2 hours)

**File:** `scripts/nusyq_actions/enhanced_work_task_actions.py` (NEW/MODIFIED)

**Purpose:** Improve `collect_quest_signal()` + suggest best action.

**Enhancement:**

```python
def collect_quest_signal_with_actions(hub_path: Path) -> dict:
    """
    Enhanced version returns:
    - active_quests: list of open/claimed/active quests
    - recommended_actions: list of (action, confidence_score, reasoning)
    - blockers: quests waiting on dependencies
    - success_history: which actions solved similar quests before
    """
    
    # 1. Query active quests (existing)
    # 2. For each quest:
    #    a. Parse title/description for keywords
    #    b. Match against action catalog
    #    c. Score match confidence (ML-lite)
    #    d. Look up historical success (did this fix this type before?)
    #    e. Return ranked list
```

**Key Jobs:**
- Semantic matching: Quest title → best action
- Confidence scoring: How sure are we this action solves it?
- Success tracking: Learn which actions work best
- Dependency awareness: Don't suggest action if prerequisites missing

**Test:** Quest appears → `suggest` command recommends best action

---

## Phase 3: Coordinator Loop & Orchestrator Integration (3-4 hours)

### 3.1 Ecosystem Orchestrator

**File:** `src/orchestration/ecosystem_orchestrator.py` (NEW)

**Purpose:** Background loop that orchestrates everything together.

**Architecture:**

```python
class EcosystemOrchestrator:
    """
    Background coordinator loop running continuously.
    
    Cycle (every 60 seconds):
    1. [ERROR SCAN] Run error_ground_truth_scanner
    2. [ERROR→SIGNAL] Post new errors as signals
    3. [SIGNAL→QUEST] Create quests from new signals
    4. [SUGGEST] Recommend actions for each quest
    5. [CLAIM] Optionally auto-claim quests if safe
    6. [EXECUTE] Optionally execute quests if safe + available
    7. [COMPLETE] Mark complete + log results
    8. [STATE SYNC] Update bootstrap state + metrics
    """
    
    async def run(self):
        while True:
            await self.scan_errors()
            await self.post_signals()
            await self.create_quests()
            await self.suggest_actions()
            # Optional auto-claiming/execution (controlled by flags)
            await asyncio.sleep(60)
```

**Safety Mechanisms:**

```python
class SafetyEnforcer:
    """Enforce safety constraints before actions."""
    
    def check_command_safety(self, cmd: str) -> bool:
        """Is this command safe? Check registry."""
        registry = load_registry()
        cmd_info = registry.commands.get(cmd)
        return cmd_info and cmd_info.safety in [
            CommandSafety.READ_ONLY,
            CommandSafety.SAFE_WRITE
        ]
    
    def check_system_health(self) -> bool:
        """Can we run operations right now?"""
        # Check API is up
        # Check git is clean (or allowed to modify)
        # Check paths are valid
        # Check dependencies available
        pass
    
    def check_quota(self) -> bool:
        """Have we spent too much API/compute?"""
        # Rate limiting
        # Resource quotas
        # Time-of-day checks (don't run during peak)
        pass
```

### 3.2 Autonomous Mode Switch

**File:** `src/orchestration/autonomy_controller.py` (NEW)

**Purpose:** Control degree of automation.

```python
class AutonomyLevel(Enum):
    DISABLED = 0        # Do nothing automatically
    MONITORING = 1      # Scan + report only
    SUGGESTING = 2      # Scan + suggest + recommend
    CLAIMING = 3        # Auto-claim quests (notify operator)
    EXECUTING = 4       # Execute simple quests (safe_write level)
    FULL = 5            # Execute all safe commands (requires approval per action)
```

Operators control via environment or config file:

```ini
[orchestrator]
autonomy_level = 2  # Start at SUGGESTING
max_parallel_tasks = 2
max_daily_executions = 100
safe_time_window = 09:00-17:00
```

### 3.3 Feedback Loop Integration

**File:** `src/orchestration/feedback_loop.py` (NEW)

**Purpose:** Learn from outcomes, update bootstrap state, improve future decisions.

```python
class FeedbackLoop:
    """Track outcomes, update state."""
    
    async def on_quest_complete(self, quest_id, outcome):
        """Quest completed - learn from it."""
        # 1. Log result to learning system
        # 2. Update historical success rates
        # 3. Adjust action recommendations
        # 4. Update agent skill scores
        # 5. Trigger bootstrap refresh (state changed)
```

---

## Phase 4: Validation & Integration Testing (2 hours)

### 4.1 Integration Test Suite

**File:** `tests/integration/test_full_automation.py` (NEW)

```python
class TestFullAutomation:
    """Test the complete pipeline."""
    
    @pytest.mark.asyncio
    async def test_error_to_signal_to_quest_to_action(self):
        """End-to-end: Error found → Signal posted → Quest created → Action suggested"""
        # 1. Inject test errors
        # 2. Run error scanner
        # 3. Verify signals posted
        # 4. Verify quests created
        # 5. Verify actions suggested
        
    @pytest.mark.asyncio
    async def test_orchestrator_cycle(self):
        """Verify orchestrator loop runs safely."""
        # 1. Start orchestrator
        # 2. Verify it scans for errors
        # 3. Verify it posts signals
        # 4. Verify it creates quests
        # 5. Kill and verify clean shutdown
        
    @pytest.mark.asyncio
    async def test_safety_enforcement(self):
        """Verify unsafe commands are blocked."""
        # 1. Try to run unsafe command
        # 2. Verify it's blocked by safety enforcer
        # 3. Verify it logs the attempt
        # 4. Verify notification sent to operator
```

### 4.2 Manual Validation Checklist

```
✅ Bootstrap runs at session start
✅ Registry loads in Continue.dev
✅ Error scanner detects problems
✅ Signals post to guild board
✅ Quests auto-create from signals
✅ Actions get recommended
✅ Orchestrator loop runs without hanging
✅ Safety constraints respected
✅ Feedback loop updates state
✅ Agent can claim and complete quests
✅ Guild board shows progression
✅ Dashboard displays real-time state
```

---

## Implementation Order (Prioritized)

### Week 1 (By Priority)
1. **Error→Signal Bridge** - Unblocks everything downstream
2. **Signal→Quest Bridge** - Enables work creation
3. **Agent Session Integration** - Enables Copilot awareness
4. **Coordinator Loop Basic** - Gets orchestration running

### Week 2
5. **Quest→Action Enhancement** - Smart recommendations
6. **Safety Enforcement** - Prevents accidents
7. **Feedback Loop** - Learning & improvement
8. **Autonomous Mode Switch** - Control automation level

### Week 3
9. **Unified Dashboard** - Visibility
10. **Full Testing** - Validation
11. **Documentation** - For operators
12. **Deployment** - Production readiness

---

## Success Criteria

When complete, the system will:

```
✅ Bootstrap tells me system state at session start
✅ Registry tells me what I can safely do
✅ Error scanner runs automatically every 60s
✅ Errors → Signals → Quests flow automatically
✅ Quests → Actions suggestion works
✅ Orchestrator runs in background safely
✅ I (Copilot) can claim, work, complete quests
✅ Guild board shows live progression
✅ Safety constraints always enforced
✅ Operator can control autonomy level
✅ System learns from outcomes
✅ Dashboard shows "what to do next" in real-time
```

At this point:
- **Fully Automatic:** Errors detected → Fixed without human intervention (within safety bounds)
- **Fully Coordinated:** Multiple agents working in parallel without collision
- **Fully Aware:** System and agents understand state, constraints, priorities
- **Fully Safe:** No unsafe commands run, no destructive operations without approval

---

## Configuration Files to Create/Modify

```
.continue/config.json         # Custom commands + context
.vscode/tasks.json           # Bootstrap task
config/autonomy_config.ini   # Control automation level
src/orchestration/           # New coordination modules
  ├─ error_signal_bridge.py
  ├─ signal_quest_mapper.py
  ├─ ecosystem_orchestrator.py
  ├─ autonomy_controller.py
  └─ feedback_loop.py
tests/integration/
  └─ test_full_automation.py
```

---

## Estimated Effort Breakdown

| Component | Hours | Risk | Priority |
|-----------|-------|------|----------|
| Error→Signal Bridge | 2 | Low | 🔴 Critical |
| Signal→Quest Bridge | 2 | Low | 🔴 Critical |
| Agent Session Integration | 2 | Very Low | 🔴 Critical |
| Coordinator Loop | 3 | Medium | 🔴 Critical |
| Quest→Action Enhancement | 2 | Low | 🟠 High |
| Safety Enforcement | 1 | Medium | 🟠 High |
| Feedback Loop | 1 | Low | 🟠 High |
| Unified Dashboard | 3 | Low | 🟡 Medium |
| Testing & Docs | 2 | Low | 🟠 High |
| **TOTAL** | **18** | - | - |

---

## Next Steps

**Immediately:**
1. Approve Phase 1 (Agent Integration)
2. Start Phase 2a (Error→Signal)
3. Position Phase 3 (Orchestrator)

**I recommend starting with Error→Signal Bridge since it:**
- Unblocks everything downstream
- Has lowest complexity
- Provides highest value
- Can be tested independently

Ready to build?

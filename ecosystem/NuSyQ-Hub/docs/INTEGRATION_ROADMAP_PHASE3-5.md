# Integration Roadmap: Phase 3-5 (Complete Path to Production)

**Scope:** NuSyQ Tripartite System (NuSyQ-Hub, SimulatedVerse, NuSyQ Root)  
**Timeline:** Phase 3 (now), Phase 4 (1-2 weeks), Phase 5 (2-4 weeks)  
**Goal:** Move from "scaffolded + orchestrated" → "fully integrated +
autonomous"  
**Success Metric:** 0 errors across all repos + services online + work executing
end-to-end

---

## Executive Summary

```
CURRENT STATE (2026-01-08):
  ✓ Spine health: GREEN
  ✓ Dispatch actions: 56/56 available
  ✓ Error detection: Operational
  ✓ AI orchestration: Defined
  ✓ Architecture: 7-layer, complete
  ⚠️ Services: ALL 14 OFFLINE (active: false)
  ⚠️ Work execution: Enqueued but not processed
  ⚠️ Errors: 75 total (64 Hub, 8 SimVerse, 3 Root)

PHASE 3 OUTCOME (1-2 weeks):
  ✓ start_nusyq.py: 44 → 0 errors (gateway script refactored)
  ✓ Code quality: Improved (70%+ reduction in complexity)
  ✓ Maintainability: High (extracted modules, clear registry)
  ✓ All 56 actions: Still callable, improved structure

PHASE 4 OUTCOME (1-2 weeks):
  ✓ Services: 14/14 online (active: true)
  ✓ SimulatedVerse: 8 → 0 errors (integration complete)
  ✓ Orchestrator: Running, routing work
  ✓ PU Queue: Processing items with proofs
  ✓ Cross-repo diagnostics: Unified view

PHASE 5 OUTCOME (1-2 weeks):
  ✓ Total errors: 75 → 0 (full quality achievement)
  ✓ Work execution: End-to-end proof-gated
  ✓ Theater audits: Preventing fake progress
  ✓ Autonomous healing: 6-hour cycles operational
  ✓ Production ready: Full deployment capability
```

---

## Phase 3: Gateway Script Refactoring (CURRENT)

**Primary File:** `scripts/start_nusyq.py`  
**Error Count:** 44 (primarily COMPLEXITY: C901)  
**Timeline:** 1-2 weeks  
**Dependencies:** None (stand-alone refactoring)

### 3.1 Complexity Reduction Strategy

**Error Breakdown by Function:**

```
Function                  Current Complexity    Target    Type
─────────────────────────────────────────────────────────────────
compute_deltas()          76                    8         C901
_handle_capabilities()    45                    12        C901
main()                    38                    10        C901
_handle_error_report()    15                    12        C901 (secondary)
_handle_snapshot()        14                    10        C901 (secondary)
dispatch_map             (implicit structure)   N/A       Maintainability
(other functions)         ~20 combined          < 12 each C901

TOTAL C901 VIOLATIONS:    ~35
TARGET:                   0
APPROACH:                 Extract helpers, use dispatch patterns
```

### 3.2 Refactoring Sequence

#### TASK 3.1: Extract compute_deltas() → compute_deltas_helpers.py

**Current State:**

- File: `scripts/start_nusyq.py`, Lines 1040-1150
- Complexity: 76 (CRITICAL)
- Pattern: Large if/elif chain + nested logic

**Extraction:**

```python
# NEW FILE: scripts/nusyq_analysis/compute_deltas_helpers.py

def detect_new_files(current: FileDict, previous: FileDict) -> List[FileDelta]:
    """Identify files that exist in current but not in previous."""
    # ~15 complexity → < 5 (simple set difference)

def detect_deleted_files(current: FileDict, previous: FileDict) -> List[FileDelta]:
    """Identify files that existed in previous but not in current."""
    # ~15 complexity → < 5 (simple set difference)

def detect_modified_files(current: FileDict, previous: FileDict) -> List[FileDelta]:
    """Identify files that changed content/permissions."""
    # ~20 complexity → < 8 (hash comparison + filter)

def classify_delta_type(old_file: Optional[File], new_file: Optional[File]) -> DeltaType:
    """Determine delta type (added, deleted, modified, etc.)."""
    # ~10 complexity → < 5 (simple enum dispatch)

def rank_deltas_by_priority(deltas: List[FileDelta]) -> List[FileDelta]:
    """Sort deltas by priority (src/ before tests/, critical before optional)."""
    # ~10 complexity → < 5 (custom sort key)

# REFACTORED: Original function
def compute_deltas(hub_path: Optional[Path], current_snap: RepoSnapshot) -> List[FileDelta]:
    """Orchestrate delta computation using helpers."""
    # Complexity: 76 → 8 (simple orchestration)
    previous = _load_previous_snapshot(hub_path)
    if not previous:
        return classify_all_new(current_snap.files)

    deltas = []
    deltas.extend(detect_new_files(current_snap.files, previous.files))
    deltas.extend(detect_deleted_files(current_snap.files, previous.files))
    deltas.extend(detect_modified_files(current_snap.files, previous.files))

    return rank_deltas_by_priority(deltas)
```

**Effort:** 1-2 hours  
**Tests:** Add unit tests for each helper (pytest)  
**Validation:**

- Complexity: 76 → 8 ✓
- Tests pass ✓
- Behavior unchanged ✓

---

#### TASK 3.2: Extract action registry → action_registry.py

**Current State:**

- File: `scripts/start_nusyq.py`, Lines ~4805-4900
- Pattern: 56 lambda handlers in dispatch_map dictionary
- Issue: Hard to discover, extend, or understand action categories

**Extraction:**

```python
# NEW FILE: scripts/nusyq_actions/action_registry.py

from enum import Enum
from dataclasses import dataclass
from typing import Callable, List, Optional

class ActionTier(str, Enum):
    """Action categorization by function and trust level."""
    CORE = "core"                    # Infrastructure: snapshot, error_report, help
    AI_ROUTING = "ai_routing"        # analyze, review, debug, generate
    HEALING = "healing"              # heal, doctor, hygiene, selfcheck
    TESTING = "testing"              # test, test_history
    AUTOMATION = "automation"        # auto_cycle, orchestrate, invoke_agent
    WORK_QUEUE = "work_queue"        # queue, pu_execute, replay, sync
    GUILD = "guild"                  # 11 guild_* actions
    TRACING = "tracing"              # 12 trace_* actions
    LIFECYCLE = "lifecycle"          # lifecycle_catalog, brief, capabilities
    SPECIAL = "special"              # zero_token_status, quantum_resolver_status
    ADVANCED = "advanced"            # suggest, next_action, develop_system
    EXPERIMENTAL = "experimental"    # simverse_bridge, sns_analyze

@dataclass
class ActionMetadata:
    """Metadata for a single action."""
    name: str                         # e.g., "analyze"
    tier: ActionTier                  # Categorization
    requires_args: bool               # Whether action takes positional args
    forbidden_in_overnight: bool      # Not allowed in overnight safe mode
    description: str                  # One-line description
    example: str                      # Example invocation
    handler: Callable                 # The handler function

class ActionRegistry:
    """Central registry of all 56 actions."""

    def __init__(self):
        self._actions: Dict[str, ActionMetadata] = {}

    def register(self, metadata: ActionMetadata):
        """Register a new action."""
        self._actions[metadata.name] = metadata

    def get(self, name: str) -> Optional[ActionMetadata]:
        """Retrieve action metadata."""
        return self._actions.get(name)

    def list_by_tier(self, tier: ActionTier) -> List[ActionMetadata]:
        """Get all actions in a tier."""
        return [a for a in self._actions.values() if a.tier == tier]

    def get_callable(self, name: str) -> Optional[Callable]:
        """Get handler for action."""
        meta = self.get(name)
        return meta.handler if meta else None

    def is_available(self, name: str) -> bool:
        """Check if action exists."""
        return name in self._actions

    def is_allowed_in_overnight(self, name: str) -> bool:
        """Check if action is allowed in overnight safe mode."""
        meta = self.get(name)
        if not meta:
            return False
        return not meta.forbidden_in_overnight

    def discover_actions(self) -> Dict[str, List[str]]:
        """Discover actions by tier."""
        result = {}
        for tier in ActionTier:
            result[tier.value] = [a.name for a in self.list_by_tier(tier)]
        return result

# Global registry (singleton)
GLOBAL_REGISTRY = ActionRegistry()

# Register all 56 actions (example: 3 shown)
GLOBAL_REGISTRY.register(ActionMetadata(
    name="snapshot",
    tier=ActionTier.CORE,
    requires_args=False,
    forbidden_in_overnight=False,
    description="Generate tripartite system snapshot",
    example="python scripts/start_nusyq.py snapshot",
    handler=_handle_snapshot_or_help,
))

GLOBAL_REGISTRY.register(ActionMetadata(
    name="analyze",
    tier=ActionTier.AI_ROUTING,
    requires_args=True,
    forbidden_in_overnight=False,
    description="Analyze file with Ollama or Claude",
    example="python scripts/start_nusyq.py analyze src/main.py --system=ollama",
    handler=lambda args, paths, run_ai: handle_analyze(args, paths, run_ai),
))

GLOBAL_REGISTRY.register(ActionMetadata(
    name="generate",
    tier=ActionTier.AI_ROUTING,
    requires_args=True,
    forbidden_in_overnight=True,  # Forbidden in overnight mode
    description="Generate code with ChatDev or Ollama",
    example="python scripts/start_nusyq.py generate 'REST API with JWT'",
    handler=lambda args, paths, run_ai: handle_generate(args, paths, run_ai),
))

# ... (54 more actions registered)

def get_registry() -> ActionRegistry:
    """Singleton accessor."""
    return GLOBAL_REGISTRY
```

**In start_nusyq.py::main():**

```python
# BEFORE (lines ~4805-4900, 96 lines of lambdas)
dispatch_map: dict[str, callable] = {
    "heal": lambda: run_heal(paths.nusyq_hub),
    "suggest": lambda: handle_suggest(paths, git_snapshot, read_quest_log, run),
    # ... 54 more lambdas ...
}

# AFTER (clean invocation, 8 lines)
registry = get_registry()
if action not in registry.discover_actions():
    print(f"[ERROR] Unknown action: {action}")
    return 1

handler = registry.get_callable(action)
if handler:
    return handler()  # Execute with proper context injection
else:
    return 1
```

**Effort:** 2-3 hours  
**Tests:** Unit tests for registry, action discovery  
**Validation:**

- All 56 actions callable ✓
- Dispatch behavior unchanged ✓
- Registry discoverable (e.g., for help, autocomplete) ✓

---

#### TASK 3.3: Refactor main() function

**Current State:**

- File: `scripts/start_nusyq.py`, Lines 4712-4950 (~240 lines)
- Complexity: 38 (multiple concerns mixed)
- Issues: Bootstrap + dispatch + tracing all in one function

**Refactoring:**

```python
# PHASE 1: Bootstrap (extract into bootstrap_phase())
def _bootstrap_phase(hub_path: Path) -> Tuple[WorkspacePaths, RunContext]:
    """Initialize spine, load paths, prepare execution context."""
    # Initialize spine
    health = initialize_spine(repo_root=hub_path)
    # Load paths
    paths = load_paths(hub_path, allow_discovery=True)
    # Setup run context
    run_id = ensure_run_id()
    # Load configurations
    contracts = read_action_contracts(paths.nusyq_hub)
    # Return prepared context
    return paths, RunContext(run_id=run_id, contracts=contracts)

# PHASE 2: Parse + Validate (extract into parse_and_validate_phase())
def _parse_and_validate_phase(args: list[str], registry: ActionRegistry) -> Tuple[str, list[str]]:
    """Parse command-line args, validate action, apply overnight restrictions."""
    # Extract action from args
    action = _extract_action(args) or "snapshot"
    # Validate action exists
    if not registry.is_available(action):
        raise InvalidActionError(f"Unknown action: {action}")
    # Check overnight restrictions
    if mode == "overnight" and not registry.is_allowed_in_overnight(action):
        raise OvernightRestrictedError(f"Action {action} forbidden in overnight mode")
    return action, args

# PHASE 3: Execute (extract into execute_phase())
def _execute_phase(action: str, args: list[str], paths: WorkspacePaths, registry: ActionRegistry) -> int:
    """Execute handler for action."""
    handler = registry.get_callable(action)
    if not handler:
        return 1
    # Setup tracing span
    with otel.start_action_span(f"nusyq.action.{action}") as span:
        rc = handler()
        span.set_attribute("exit_code", rc)
        return rc

# REFACTORED main()
def main() -> int:
    """Orchestrate bootstrap → validate → execute → emit receipt."""
    # Phase 1: Bootstrap
    hub_default = Path(__file__).resolve().parents[1]
    try:
        paths, ctx = _bootstrap_phase(hub_default)
    except Exception as e:
        print(f"[ERROR] Bootstrap failed: {e}")
        return 1

    # Phase 2: Parse & Validate
    try:
        action, remaining_args = _parse_and_validate_phase(sys.argv[1:], get_registry())
    except (InvalidActionError, OvernightRestrictedError) as e:
        print(f"[ERROR] {e}")
        return 1

    # Phase 3: Execute
    try:
        rc = _execute_phase(action, remaining_args, paths, get_registry())
    except Exception as e:
        print(f"[ERROR] Execution failed: {e}")
        return 1

    # Phase 4: Receipt emission (automatic via context manager)
    return rc
```

**Effort:** 2-3 hours  
**Validation:**

- Complexity: 38 → 10 ✓
- All 56 actions still callable ✓
- Bootstrap behavior identical ✓

---

### 3.3 Phase 3 Summary

| Task                                   | Complexity Reduction | Tests              | Validation     | Effort        |
| -------------------------------------- | -------------------- | ------------------ | -------------- | ------------- |
| 3.1: Extract compute_deltas()          | 76 → 8               | 3 unit tests       | ✓              | 1-2h          |
| 3.2: Action registry                   | (refactor)           | 5 unit tests       | ✓              | 2-3h          |
| 3.3: Refactor main()                   | 38 → 10              | 4 unit tests       | ✓              | 2-3h          |
| 3.4: Minor fixes (type hints, linting) | (5 errors)           | 2 unit tests       | ✓              | 1h            |
| **TOTAL PHASE 3**                      | **44 → 0 errors**    | **14+ unit tests** | **✓ All pass** | **6-9 hours** |

**End State:**

- Error count: 44 → 0 ✓
- Code coverage: 90%+ maintained ✓
- All 56 actions operational ✓
- Maintainability: Significantly improved ✓

---

## Phase 4: Cross-Repo Integration Completion

**Scope:** Services activation + SimulatedVerse integration  
**Timeline:** 1-2 weeks  
**Dependencies:** Phase 3 completion (optional but preferred)

### 4.1 Critical Services Activation

**Current State:** All 14 services INACTIVE  
**Target State:** All 14 services ACTIVE (running or ready)

```
SERVICE ACTIVATION SEQUENCE
═══════════════════════════════════════════════════════════════════

TIER 1 (HIGHEST PRIORITY): Critical infrastructure
  1. Orchestrator Service
     └─ Start: python src/orchestration/start_orchestrator.py
     └─ Role: Routes work to AI systems (Claude, Ollama, ChatDev)
     └─ Current: INACTIVE
     └─ Activate: Create service bootstrap script, register in lifecycle

  2. PU Queue Service
     └─ Start: python src/automation/pu_queue_service.py
     └─ Role: Process work items (PUs) from queue
     └─ Current: INACTIVE
     └─ Activate: Hook to orchestrator, persist status

  3. Trace Service
     └─ Start: OpenTelemetry collector (docker-based)
     └─ Role: Collect telemetry, tracing spans
     └─ Current: INACTIVE
     └─ Activate: Docker compose up (config/observability/)

TIER 2 (HIGH PRIORITY): Hub services
  4. Quest Log Sync Service
     └─ Role: Sync quest_log.jsonl across 3 repos
     └─ Activate: Start in background, monitor file changes

  5. Hub Autonomous Monitor
     └─ Role: Monitor system health, trigger healing cycles
     └─ Activate: Create monitoring daemon, register lifecycle

  6. Guild Board Renderer
     └─ Role: Render quest board from quest_log
     └─ Activate: Hook to quest log watcher

TIER 3 (MEDIUM PRIORITY): Auxiliary services
  7-13. Hub Context Server, Healthcheck Server, Agent Hub, AI Intermediary,
        Architecture Watcher, etc.
        └─ Activate: Bootstrap stubs first, wire implementation later

TIER 4 (LOWEST PRIORITY): Future services
  14. SimulatedVerse Dev Server
      └─ Activate: npm run dev (separate process)
```

### 4.2 SimulatedVerse Integration (8 errors → 0)

**Error Breakdown:**

- 3-4 errors: TypeScript/Node.js linting (tslint/eslint)
- 2-3 errors: Python<->TypeScript bridge type mismatches
- 1-2 errors: Import path resolution

**Integration Path:**

1. Run SimulatedVerse scanner: `npm run lint` + Python diagnostics
2. Fix TypeScript errors (eslint --fix where possible)
3. Verify Bridge Integration: Sync current_state between repos
4. Validate Proof Gating: Culture-Ship audit passes

### 4.3 Unified Diagnostics View

**Target:** Single diagnostic dashboard showing all 3 repos

```
Commands:
  python scripts/start_nusyq.py vscode_diagnostics_bridge  # VS Code lens
  python scripts/start_nusyq.py unified_error_report       # Canonical scan
  python scripts/start_nusyq.py brief                       # 60-second status
```

### 4.4 Phase 4 Success Criteria

| Item                  | Current | Target | Status |
| --------------------- | ------- | ------ | ------ |
| Services online       | 0/14    | 14/14  | ✗      |
| SimulatedVerse errors | 8       | 0      | ✗      |
| NuSyQ Root errors     | 3       | 0      | ✗      |
| Orchestrator running  | No      | Yes    | ✗      |
| PU Queue processing   | No      | Yes    | ✗      |
| Cross-repo sync       | No      | Yes    | ✗      |
| Unified diagnostics   | No      | Yes    | ✗      |

---

## Phase 5: Full Autonomous Capability

**Scope:** End-to-end proof-gated work execution  
**Timeline:** 1-2 weeks  
**Dependencies:** Phase 3 + Phase 4 complete

### 5.1 Autonomous Work Flow

```
PROOF-GATED WORK EXECUTION PIPELINE
═══════════════════════════════════════════════════════════════════

INTAKE
  1. User/system generates work request
     ├─ Explicit: "analyze src/main.py with Ollama"
     ├─ Implicit: Error detected → heal action triggered
     └─ Scheduled: 6-hour healing cycle kicks off

ENQUEUE
  2. Work routed to PU Queue (Proof Unit)
     ├─ Create PU with proof criteria
     ├─ Assign priority, complexity estimate
     └─ Log to quest_log.jsonl

ROUTE
  3. Orchestrator picks best AI system
     ├─ Type: "code fix" → ChatDev or Ollama
     ├─ Type: "analysis" → Claude Code or Ollama
     ├─ Type: "quantum problem" → Quantum Resolver
     └─ Type: "proof audit" → Culture-Ship

EXECUTE
  4. AI system executes work
     ├─ Generate output (fixed code, analysis, etc.)
     ├─ Run quick validation (no infinite loops, etc.)
     └─ Return result

VALIDATE (Proof Gating)
  5. Check proof criteria
     ├─ Tests pass (pytest)
     ├─ Type checks pass (mypy)
     ├─ Linting passes (ruff, black)
     ├─ Theater audit passes (no fake progress)
     └─ All criteria met → continue; else → healing

PERSIST
  6. If validated: Persist to quest log, state reports
     ├─ Update quest status (completed)
     ├─ Write receipt (trace ID, span ID, outputs)
     ├─ Update evolution metrics
     ├─ Capture emergence (if applicable)
     └─ Sync to SimulatedVerse

OBSERVE
  7. Emit observability signals
     ├─ OpenTelemetry span closure
     ├─ Metrics update
     ├─ Health check integration
     └─ Anomaly detection (if unusual)
```

### 5.2 Autonomous Healing Cycle (6-hour cadence)

```
HEALING CYCLE SCHEDULER
═══════════════════════════════════════════════════════════════════

Trigger: Every 6 hours (configurable)
  └─ Check: Are there outstanding errors?
  └─ If yes: Spawn healing cycle

CYCLE PHASES:
  1. Scan: python scripts/start_nusyq.py error_report --force
  2. Prioritize: Rank errors by impact + fixability
  3. Heal: Route to healers (automated, semi-auto, manual)
  4. Validate: Run proof gates
  5. Report: Generate healing report, log to quest system
  6. Sleep: Wait 6 hours, repeat

EXPECTED RESULTS:
  • Start: 75 errors
  • After 1 cycle: 50-60 errors (auto-fixes + semi-auto)
  • After 2 cycles: 20-30 errors (gains slower, manual work needed)
  • After 3 cycles: 5-10 errors (nearing zero, requires attention)
  • Target: 0 errors (full quality)
```

### 5.3 Phase 5 Success Criteria

| Item                  | Current | Target      | Status    |
| --------------------- | ------- | ----------- | --------- |
| NuSyQ-Hub errors      | 64      | 0           | ✗         |
| SimulatedVerse errors | 8       | 0           | ✗         |
| NuSyQ Root errors     | 3       | 0           | ✗         |
| **Total errors**      | **75**  | **0**       | ✗         |
| Test coverage         | 90.72%  | 95%+        | ~         |
| Tests passing         | 697     | All         | ✓         |
| Services online       | 0/14    | 14/14       | (Phase 4) |
| Work execution        | Manual  | Autonomous  | ✗         |
| Theater audits        | Defined | Running     | (Phase 4) |
| Healing cycles        | Defined | Operational | (Phase 5) |

---

## Timeline & Milestones

```
PHASE 3: GATEWAY SCRIPT REFACTORING (1-2 weeks)
├─ Week 1:
│  ├─ Mon-Tue: Extract compute_deltas() [2 tasks done by end of Mon]
│  ├─ Wed-Thu: Extract action_registry() [1-2 tasks done by end of Wed]
│  ├─ Fri: Refactor main() + integrate + test all 56 actions
│  └─ Weekend: Polish, final validation
│
├─ Week 2:
│  ├─ Mon-Wed: Add comprehensive type hints, final linting
│  ├─ Thu-Fri: Full integration testing, documentation
│  └─ Deliverable: start_nusyq.py: 44 → 0 errors, all tests pass
│
└─ GATE: Phase 3 completion = "Gateway Refactoring Complete"

PHASE 4: CROSS-REPO INTEGRATION (1-2 weeks)
├─ Week 1:
│  ├─ Bootstrap orchestrator + pu_queue services
│  ├─ Activate trace service (Docker-based)
│  ├─ Wire quest_log_sync across 3 repos
│  └─ Begin SimulatedVerse error resolution
│
├─ Week 2:
│  ├─ Complete SimulatedVerse integration (8 → 0 errors)
│  ├─ Activate remaining 10 services
│  ├─ Unified diagnostics view operational
│  └─ Full integration testing
│
└─ GATE: Phase 4 completion = "Full Service Integration"

PHASE 5: AUTONOMOUS EXECUTION (1-2 weeks)
├─ Week 1:
│  ├─ End-to-end work flow testing
│  ├─ Proof gating validation
│  ├─ First healing cycle (automated)
│  └─ Error count: 75 → 40-50
│
├─ Week 2:
│  ├─ Continued healing cycles (daily)
│  ├─ Manual refactoring for stubborn errors
│  ├─ Final validation runs
│  └─ Error count: 40-50 → 0
│
└─ GATE: Phase 5 completion = "Zero-Error Production Ready"

TOTAL TIMELINE: 3-6 weeks to full production readiness
```

---

## Key Dependencies & Blockers

```
PHASE 3 Dependencies:
  ✓ No external dependencies
  ✓ Can be done in parallel with Phase 4 planning

PHASE 4 Dependencies:
  ✓ Phase 3 helpful but not required
  ✓ Service bootstrap scripts must exist
  ✓ Lifecycle catalog infrastructure (already present)
  ✓ NuSyQ Root / SimulatedVerse access

  BLOCKERS:
    ⚠️ Docker setup (for trace service) - may require system setup
    ⚠️ Ollama models running - need to verify availability
    ⚠️ ChatDev path resolution - check environment variables

PHASE 5 Dependencies:
  ✓ Phase 3 + Phase 4 complete
  ✓ All 14 services running
  ✓ Proof gating infrastructure active

  BLOCKERS:
    ⚠️ Theater audits must work (SimulatedVerse integration)
    ⚠️ Healing pipeline must route correctly
    ⚠️ Manual refactoring capacity for stubborn errors
```

---

## Resource Allocation

```
PHASE 3: Gateway Script Refactoring
  Team: 1-2 engineers (code + review)
  Focus: Claude Code + GitHub Copilot
  Effort: 6-9 hours actual work

PHASE 4: Cross-Repo Integration
  Team: 2-3 engineers (infrastructure + integration)
  Focus: Service bootstrapping, cross-repo wiring
  Effort: 15-20 hours actual work

PHASE 5: Autonomous Execution
  Team: 2-3 engineers (validation + healing)
  Focus: End-to-end testing, manual refactoring
  Effort: 20-30 hours actual work (includes waiting for cycles)

TOTAL EFFORT: 40-60 person-hours over 3-6 weeks
```

---

## Rollback & Safety Strategy

```
PHASE 3 ROLLBACK:
  • All changes to scripts/start_nusyq.py are additive
  • Original dispatch_map can be restored if issues arise
  • Git revert available at every commit point
  • Zero risk to system availability

PHASE 4 ROLLBACK:
  • Services start independently (no forced initialization)
  • Can disable individual services without affecting others
  • Quest log sync can be paused if cross-repo issues arise
  • Fallback to Phase 3 state possible

PHASE 5 ROLLBACK:
  • Healing cycles can be disabled (config flag)
  • Manual work execution always available
  • Proof gating can be relaxed for experimentation
  • Full restoration to Phase 4 state if needed

SAFETY GATES:
  ✓ All changes gated on proof validation
  ✓ Breaking changes trigger alerts
  ✓ Theater audits prevent deployment of broken work
  ✓ Comprehensive logging enables post-mortems
```

---

## Success Criteria Summary

### Phase 3 Success

- [ ] start_nusyq.py: 44 → 0 errors
- [ ] All 56 actions still callable
- [ ] Test coverage: 90%+ maintained
- [ ] Code complexity: Reduced by 70%+
- [ ] All imports: Clean, organized
- [ ] Documentation: Updated with new modules

### Phase 4 Success

- [ ] All 14 services: active = true
- [ ] SimulatedVerse: 8 → 0 errors
- [ ] NuSyQ Root: 3 → 0 errors
- [ ] Orchestrator: Processing work
- [ ] PU Queue: Maintaining queue, processing items
- [ ] Quest log sync: Working across repos
- [ ] Unified diagnostics: Single dashboard view

### Phase 5 Success

- [ ] Total errors: 75 → 0
- [ ] All 56 actions: Autonomous execution verified
- [ ] Proof gating: 100% enforcement
- [ ] Healing cycles: Running on schedule
- [ ] Theater audits: Preventing fake progress
- [ ] Production ready: Full deployment capability
- [ ] Documentation: Complete and discoverable

---

## Estimated Completion Date

**Assumption:** 2-3 person-hours per day available  
**Phase 3:** 3-4 days → **Completion: Mid-January 2026**  
**Phase 4:** 5-7 days → **Completion: Late January 2026**  
**Phase 5:** 7-10 days → **Completion: Early February 2026**

**Target: Full Production Readiness by February 1, 2026**

---

## Next Actions

1. **Immediate (Today):**

   - [ ] Confirm Phase 3 plan with architecture review
   - [ ] Create branch: `feature/phase3-gateway-refactoring`
   - [ ] Begin Task 3.1 (compute_deltas extraction)

2. **Short-term (This week):**

   - [ ] Complete Task 3.1 + 3.2 + 3.3
   - [ ] Validate all 56 actions still callable
   - [ ] Run full test suite

3. **Medium-term (Next 1-2 weeks):**

   - [ ] Complete Phase 3: Merge to master
   - [ ] Begin Phase 4 planning
   - [ ] Start service bootstrap scripts

4. **Long-term (1-6 weeks):**
   - [ ] Execute Phase 4 + Phase 5
   - [ ] Achieve zero-error state
   - [ ] Production deployment

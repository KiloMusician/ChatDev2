# Epistemic-Operational Lattice (EOL)
## Continuous Fusion Architecture for Multi-Agent Orchestration

**Version:** 0.1 (Foundation)  
**Status:** Generative Design + Minimal Viable Implementation  
**Last Updated:** 2026-02-28  

---

## Conceptual Foundation

The **Epistemic-Operational Lattice (EOL)** is a decision-making substrate that continuously fuses all observable signals (code, runtime, agent state, policy, objectives) into a **unified world state**, then executes actions under **explicit policy gating** rather than implicit heuristics.

### Core Model

```
WorldState_t = f(Context_t, RepoGraph_t, Runtime_t, Telemetry_t, Memory_t, Policy_t, Objective_t)

Action_t = argmax_a U(a | WorldState_t, Risk_t, Budget_t, Time_t)
```

Where `U` (utility) is evaluated under safety/risk constraints, not raw task completion.

---

## Seven Planes of the Lattice

### 1. **Observation Plane**
**Purpose:** Ingest all signal streams into normalized, attributed facts.

**Inputs:**
- Chat stream (user messages)
- Filesystem deltas (git diffs, file changes)
- Process table (running agents, services)
- Git graph (commit history, branches)
- Event logs (quest_log.jsonl, action receipts)
- Telemetry (latency, error rates, resource use)
- Diagnostics (linters, type checkers, security scanners)
- Environment (secrets, config, feature flags)

**Outputs:**
- Normalized fact stream (timestamp, source, confidence, provenance)
- Attribution metadata (update source, validation method)

**Current Implementation:** Scattered across quest_log.jsonl, state.py, and direct file reads.

**Need:** `build_world_state.py` with fact normalization pipeline.

---

### 2. **Coherence Plane**
**Purpose:** Detect contradictions and maintain canonical signal precedence.

**Responsibilities:**
- Compare multiple signal sources (e.g., VS Code error count vs. tool ground truth)
- Detect stale/conflicting information
- Establish precedence rules (tool output > config assumptions > cached state)
- Flag signal drift with reasoning

**Example Contradiction:**
```
Signal 1: VS Code problems view reports 209 errors
Signal 2: start_nusyq.py error_report shows 28 diagnostics
Signal 3: Config docs cite 1,228 errors (timestamp: 2025-12-25)

Resolution: Signal 2 + 1 are current; Signal 3 is stale. 
Precedence: Tool ground truth (Signal 2) > UI view (Signal 1) > docs (Signal 3)
```

**Current Implementation:** Implicit in conversation/human interpretation.

**Need:** `coherence_evaluator.py` with signal-priority matrix and drift alerts.

---

### 3. **Intent/Policy Plane**
**Purpose:** Encode doctrine, constraints, and safety rules as executable policy.

**Domains:**
- **Doctrine:** `.github/instructions/` files, AGENTS.md, CLAUDE.md
- **Safety:** No destructive ops without approval; all mutations logged
- **Capacity:** Budget constraints (token, time, CPU), risk thresholds
- **Ethical:** Culture alignment (non-coercion, consent, transparency)

**Structure:**
```python
@dataclass
class Policy:
    allow_mutations: bool = False  # Can this operation modify state?
    risk_threshold: float = 0.7    # Max acceptable risk score
    requires_approval: bool = False # Does Culture Ship need to review?
    category: str = "FEATURE"      # SECURITY, BUGFIX, FEATURE, REFACTOR, etc.
    time_budget_s: int = 300       # Wall-clock budget
    token_budget: int = 5000       # Token consumption limit
    doctrine_refs: list[str] = field(default_factory=list)  # Which instruction files govern this?
```

**Current Implementation:** Encoded in task.metadata, enforce_policy() scattered.

**Need:** `policy_compiler.py` that synthesizes policy from multiple instruction files and evaluates against world state.

---

### 4. **Capability Plane**
**Purpose:** Maintain live registry of agent/system affordances and failure modes.

**Registry entries:**
```python
@dataclass
class Capability:
    agent: str  # "ollama", "chatdev", "copilot", "consciousness", etc.
    capability: str  # "code_review", "generation", "analysis", "healing"
    latency_ms: float  # Observed mean response time
    success_rate: float  # Historical success (0.0-1.0)
    cost: str  # "low", "medium", "high" (token/time/resources)
    constraints: list[str]  # ["max_context_2M", "no_streaming", ...]
    last_probe: float  # Timestamp of last health check
    is_online: bool  # Current availability
    failure_mode: str | None  # Last observed failure type
```

**Routing Logic:**
```python
best_agent = argmax(Capability[agent] for agent in available_agents
                    where agent.capability in required_capabilities
                    and risk(agent, task) < policy.risk_threshold
                    and cost(agent, task) < policy.budget
                    order_by agent.success_rate desc)
```

**Current Implementation:** agent_registry.py (probes only); no capability-to-task matching.

**Need:** `capability_registry.py` with live updates + `route_by_capability.py` for intelligent delegation.

---

### 5. **Planning Plane**
**Purpose:** Build reversible, preconditioned execution plans before mutation.

**Plan Structure:**
```python
@dataclass
class ExecutionPlan:
    plan_id: str  # UUID
    steps: list[Step]
    dependencies: dict[str, list[str]]  # step_id -> [prerequisite_step_ids]
    checkpoints: list[Checkpoint]  # Safe rollback points
    preconditions: list[Predicate]  # Must all be true before execution
    postconditions: list[Predicate]  # Verify success after execution
    estimated_cost: Cost  # Token, time, resources
    dry_run_result: Optional[DryRunResult]  # Simulation result before commitment

@dataclass
class Step:
    step_id: str
    action: str  # Human-readable action description
    agent: str  # Which agent executes this
    params: dict[str, Any]
    timeout_s: int
    retryable: bool
    rollback_action: Optional[str]  # How to undo if this step fails
```

**Current Implementation:** Tasks execute immediately in queues; no DAG/reversibility.

**Need:** `plan_from_world_state.py` with DAG builder + `execution_plan_validator.py`.

---

### 6. **Execution Plane**
**Purpose:** Run actions with full traceability, receipts, and postconditional validation.

**Receipt Structure:**
```python
@dataclass
class ActionReceipt:
    action_id: str  # UUID
    timestamp: str  # ISO 8601
    agent: str  # Who executed?
    action_type: str  # What was done?
    params: dict[str, Any]  # With what inputs?
    status: ("success" | "failed" | "partial")
    exit_code: int
    duration_s: float
    token_used: int
    stdout: str
    stderr: str
    artifacts: list[str]  # Output files, logs, etc.
    postcondition_result: dict[str, bool]  # Which postconditions passed?
    next_steps: list[str]  # Linked quests/actions
```

**Ledger:** Append-only JSON Lines file, never mutated.

**Current Implementation:** Task status in memory + quest_log.jsonl (quest-specific); no unified receipt ledger.

**Need:** `action_receipt_ledger.py` + integration with quest system + postconditional validators.

---

### 7. **Memory Plane**
**Purpose:** Persist all durable episodic traces for replay, drift analysis, recovery.

**Substrate:**
- **quest_log.jsonl:** Append-only quest event stream ✅ (existing)
- **action_receipt_ledger.jsonl:** Append-only action receipt stream (new)
- **world_state_snapshot.json:** Periodic full state snapshots (new)
- **event_index.jsonl:** Cross-linked event references (new)
- **policy_decisions.jsonl:** Policy evaluations + their outcomes (new)

**Access Pattern:**
```python
# Replay execution from timestamp
state = restore_state_at_timestamp("2026-02-28T14:30:00Z")

# Find all drift events since last known-good
drift = fetch_signal_drift_since_timestamp("2026-02-27T00:00:00Z")

# Audit which policy decided which action
audit_trail = fetch_policy_decisions_for_action(action_id)
```

**Current Implementation:** quest_log.jsonl only.

**Need:** Unified event sourcing substrate + querying/replay tools.

---

### 8. **Evolution Plane** (Future)
**Purpose:** Use evaluation feedback to tune routing, timeouts, risk thresholds.

**Feedback Loop:**
```
Execution_t → Observe Outcome → Evaluate Policy Efficacy → Adapt Policy
        ↑__________________________________________________________________|
```

**Metrics:**
- Agent success rates (historical)
- Policy approval rate (% tasks that pass initial gates)
- Drift detection rate (% contradictions caught before action)
- Cost vs. benefit (token spent vs. value generated)
- Mean time to resolution (for healed issues)

**Adaptation:**
```python
if agent_failure_rate[agent] > threshold:
    capability_registry[agent].success_rate *= decay_factor
    route_by_capability() will deprioritize that agent
    
if policy_rejects_good_tasks > threshold:
    policy_compiler().lower_risk_threshold(category)
    more tasks will pass gates next time
```

**Current Implementation:** None.

**Need:** `evaluation_loop.py` + `adaptive_policy_tuner.py` (future-phase).

---

## Unified Typed Interface

**Core methods** that all planes implement:

```python
# Observation: Ingest signal
def sense() -> WorldState:
    """Fuse all signals into typed world state."""
    
# Planning: Generate proposals
def propose(world_state: WorldState) -> list[Action]:
    """Generate candidate next actions."""

# Coherence: Validate soundness
def critique(action: Action, world_state: WorldState) -> CritiqueResult:
    """Score risk, check policy, predict outcomes."""

# Execution: Controlled mutation
def act(action: Action, world_state: WorldState) -> ActionReceipt:
    """Execute action with full tracing."""

# Evolution: Learn from feedback
def learn(receipt: ActionReceipt, world_state: WorldState) -> PolicyUpdate:
    """Adapt routing/thresholds based on outcomes."""
```

---

## Minimal Viable Implementation (v0.1)

### What's Included:
1. **world_state.schema.json** — Typed definition of WorldState
2. **build_world_state.py** — Observation + Coherence planes (ingestion + signal reconciliation)
3. **plan_from_world_state.py** — Planning plane stub (capability routing + action generation)
4. **Integration with existing** quest_log.jsonl, task orchestrator, agent registry

### What's Deferred (v0.2+):
- Executable policy compiler (v0.2)
- Full DAG planning with reversibility (v0.2)
- Postconditional validation framework (v0.2)
- Adaptive policy tuning (v0.3)
- Cross-repo digital twin sync (v1.0)

---

## Operational Model

### Per-Decision Cycle:

1. **Sense:** Observe current world state by fusing all available signals
   - File system (git status, config, workspace structure)
   - Runtime (agent probes, queue state, memory, resources)
   - Telemetry (latency, error counts, diagnostic reports)
   - Memory (replay quest log, state snapshots, receipts)

2. **Propose:** Generate candidate next actions
   - Which task is most urgent by policy category + priority?
   - Which agent can execute it best (by capability match)?
   - What is the estimated cost (token, time, risk)?

3. **Critique:** Evaluate against policy + risk thresholds
   - Does this action pass safety gates?
   - Do we have sufficient budget?
   - Are preconditions satisfied?
   - What could go wrong?

4. **Act:** Execute the approved action with full tracing
   - Capture input, output, duration, errors
   - Validate postconditions
   - Log receipt to append-only ledger
   - Emit quest update if applicable

5. **Learn:** Adapt based on outcome (future phase)
   - Did the action succeed? Why/why not?
   - Should we rank that agent higher/lower next time?
   - Should we adjust risk thresholds for that category?

---

## Integration Points with Existing NuSyQ-Hub

| **NuSyQ Component** | **Integration** |
|---|---|
| `quest_log.jsonl` | Memory plane substrate; read-only during sense() |
| `quest_engine.py` | Quest status updates on action completion |
| `background_task_orchestrator.py` | Execution plane; receives actions from plan_from_world_state.py |
| `enhanced_task_scheduler.py` | Planning plane; feeds ordered task list |
| `agent_registry.py` | Capability plane; probes live agent availability |
| `src/core/orchestrate.py` | Public API; sense() -> propose() -> critique() -> act() |
| `.github/instructions/` | Policy plane; parsed by policy_compiler.py |
| `src/integration/consciousness_bridge.py` | Policy evaluation (Culture Ship approval gating) |

---

## Deployment Strategy

### Phase 1 (Now): Foundation
- ✅ Create world_state.schema.json (data contract)
- ✅ Implement build_world_state.py (sense + coherence)
- ✅ Implement plan_from_world_state.py (capability routing)
- ✅ Add action_receipt_ledger.py (execution tracing)
- ⚠️ Integrate with orchestrate.py facade

### Phase 2 (Next): Policy Gating
- Policy compiler from instruction files
- Risk classifiers (security, mutation, resource)
- Postconditional validators
- Integration with Culture Ship approval loop

### Phase 3 (Future): Adaptive Evolution
- Evaluation metrics + feedback loops
- Dynamic policy tuning
- Agent ranking based on outcomes
- Cross-repo state synchronization

---

## References

- **Architectural Inspiration:** Culture Minds (Iain M. Banks), decision-making under uncertainty, event sourcing
- **Implementation Basis:** Existing quest_log.jsonl, background_task_orchestrator.py, agent_registry.py
- **Policy Source:** `.github/copilot-instructions.md`, `.github/instructions/*.md`, AGENTS.md, CLAUDE.md
- **Safety Reference:** Culture ethics (consent, non-coercion, transparency, reversibility)

---


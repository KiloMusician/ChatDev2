"""Epistemic-Operational Lattice (EOL) Quick Reference

Fast lookup guide for the sense→propose→critique→act decision cycle.
**Print this for your desk!**

---

## 📊 Quick Start (30 seconds)

```python
from src.core.orchestrate import nusyq

# Run full cycle (sense → propose → critique → act)
result = nusyq.eol.full_cycle("Analyze errors", auto_execute=False)
if result.ok:
    print(f"Candidates: {len(result.value['actions'])}")
    print(f"Approved: {len(result.value['approved_actions'])}")
```

---

## 🧠 The Five Planes (v0.1)

### 1. **Observation Plane** (see)
Ingest signals from all sources: git, agents, quests, diagnostics.
- **Output:** List of `Signal` objects (timestamp, source, confidence, value)
- **Implemented:** ✅ `build_world_state.py` → `ObservationCollector`

### 2. **Coherence Plane** (reconcile)
Detect contradictions, resolve by signal precedence.
- **Precedence:** user_input(10) > diagnostic_tool(9) > agent_probe(8) > ... > config(5)
- **Output:** `Contradiction` objects + `SignalDrift` alerts
- **Implemented:** ✅ `build_world_state.py` → `CoherenceEvaluator`

### 3. **Planning Plane** (route)
Match intent to agent capabilities; generate ordered action candidates.
- **Input:** WorldState + user objective
- **Output:** `list[Action]` sorted by (time_sensitivity, policy_priority, cost, success_rate)
- **Implemented:** ✅ `plan_from_world_state.py` → `PlanGenerator`

### 4. **Execution Plane** (act)
Execute action with pre/post-condition validation; emit immutable receipt.
- **Input:** Action + WorldState
- **Output:** `ActionReceipt` (timestamp, duration, status, stdout/stderr, postcondition results)
- **Ledger:** Append-only `action_receipt_ledger.jsonl`
- **Implemented:** ✅ `action_receipt_ledger.py` → `ActionReceiptLedger`

### 5. **Memory Plane** (persist)
Store all episodic traces for replay, drift analysis, recovery.
- **Substrate:** quest_log.jsonl, action_receipt_ledger.jsonl, world_state_snapshot.json
- **Linkage:** `quest_receipt_linkage.py` connects receipts to quests
- **Implemented:** ✅ (quest_log + receipts + snapshots exist)

### 6-8. **Intent/Policy, Capability, Evolution** (future)
Deferred to v0.2+ (policy compiler, adaptive ranking, learning)

---

## 🎯 API Reference

### Via Facade

```python
from src.core.orchestrate import nusyq

# Sense: Build world state
world = nusyq.eol.sense().value

# Propose: Generate actions
actions = nusyq.eol.propose(world, "Do this").value

# Critique: Evaluate policy
approved = nusyq.eol.critique(actions[0], world).value

# Act: Execute with receipt
receipt = nusyq.eol.act(actions[0], world, dry_run=False).value

# Full cycle: All of above
output = nusyq.eol.full_cycle("Do this", auto_execute=False).value

# Stats: Action performance
stats = nusyq.eol.stats().value
print(f"Success rate: {stats['success_rate']:.1%}")
```

### Via Direct Classes

```python
from src.core.eol_integration import EOLOrchestrator
from pathlib import Path

eol = EOLOrchestrator(workspace_root=Path("."))

# Sense
world = eol.sense()

# Propose
actions = eol.propose(world, "Fix bugs")

# Act (with receipt logging)
receipt = eol.act(actions[0], world, dry_run=True)
print(f"Status: {receipt.status}")
print(f"Duration: {receipt.duration_s}s")

# Stats
stats = eol.stats()
```

### Via CLI

```bash
# Sense
python scripts/start_nusyq.py eol sense [--json]

# Propose
python scripts/start_nusyq.py eol propose "Your objective" [--json]

# Full cycle
python scripts/start_nusyq.py eol full-cycle "Your objective" [--auto] [--json]

# Stats
python scripts/start_nusyq.py eol stats [--json]

# Debug
python scripts/start_nusyq.py eol debug [--json]
```

---

## 🔄 Decision Cycle (Per Epoch)

```
┌─────────────────────────────────────────────────────┐
│ Epoch N: Agent Reconstituted from Stateless Substrate
├─────────────────────────────────────────────────────┤
│                                                     │
│  1️⃣ SENSE (sense())                                 │
│    ├─ Read: git status, agents, quests, diagnostics│
│    ├─ Fuse: Normalize all signals + confidence     │
│    ├─ Reconcile: Resolve contradictions by precedence
│    └─ Output: WorldState (typed dict)              │
│                                                     │
│  2️⃣ PROPOSE (propose(world_state, objective))      │
│    ├─ Parse: Extract intent from objective         │
│    ├─ Route: Match capabilities to intent          │
│    ├─ Generate: Create action candidates           │
│    └─ Output: list[Action] (ranked by priority)    │
│                                                     │
│  3️⃣ CRITIQUE (critique(action, world_state))       │
│    ├─ Evaluate: Check policy gates + risk          │
│    ├─ Validate: Assess budget + preconditions      │
│    └─ Output: bool (approved / rejected)           │
│                                                     │
│  4️⃣ ACT (act(action, world_state, dry_run))       │
│    ├─ Validate pre: Check preconditions            │
│    ├─ Dispatch: Invoke background_task_orchestrator│
│    ├─ Validate post: Check postconditions          │
│    ├─ Emit: ActionReceipt to ledger (immutable)    │
│    └─ Output: ActionReceipt                        │
│                                                     │
│  5️⃣ LEARN (future)                                 │
│    ├─ Evaluate: Did action succeed?                │
│    ├─ Metric: Success rate + effectiveness         │
│    └─ Adapt: Update rankings + risk thresholds     │
│                                                     │
│  6️⃣ PERSIST                                        │
│    ├─ Write: state/world_state_snapshot.json        │
│    └─ Ledger: Auto-append receipt                  │
│                                                     │
└─────────────────────────────────────────────────────┘
         ↓
  Epoch N+1 (agent reconstituted, reads same substrate)
```

---

## 📋 File Summary

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `src/core/build_world_state.py` | Observation + Coherence planes | 450 | ✅ |
| `src/core/plan_from_world_state.py` | Planning plane | 550 | ✅ |
| `src/core/action_receipt_ledger.py` | Execution plane | 550 | ✅ |
| `src/core/eol_integration.py` | Orchestrator + full_cycle | 450 | ✅ |
| `src/core/eol_facade_integration.py` | Facade definition | 230 | ✅ |
| `src/core/quest_receipt_linkage.py` | Memory substrate | 300 | ✅ |
| `scripts/nusyq_actions/eol.py` | CLI support | 350 | ✅ |
| `tests/integration/test_eol_e2e.py` | E2E tests | 400 | ✅ |

---

## 🎬 Common Workflows

### Run Full Cycle (Sense→Propose, No Execute)
```python
result = nusyq.eol.full_cycle("Analyze codebase", auto_execute=False)
print(f"Generated {len(result.value['actions'])} candidates")
```

### Get Stats
```python
stats = nusyq.eol.stats().value
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Top agent: {max(stats['by_agent'].items(), key=lambda x: x[1]['count'])}")
```

### View World State Contradictions
```python
world = nusyq.eol.sense().value
for cnt in world['coherence']['contradictions']:
    print(f"{cnt['key']}: {cnt['reasoning']}")
```

### Manual Step-by-Step
```python
world = nusyq.eol.sense().value
actions = nusyq.eol.propose(world, "Fix tests").value
for action in actions[:3]:
    approved = nusyq.eol.critique(action, world).value
    if approved:
        receipt = nusyq.eol.act(action, world, dry_run=True).value
        print(f"Dry-run: {receipt['status']}")
        break
```

---

## ⚡ Performance Tips

1. **Dry-run first:** Always use `dry_run=True` until confident
2. **Check budget:** Look at `world_state['policy_state']['resource_budgets']`
3. **Signal precedence:** High-cost actions get checked earlier in proposal ranking
4. **Async friendly:** LEDs light up on long-running Ollama calls (15s+ for complex tasks)

---

## 🔗 Links

- **Architecture:** [docs/EPISTEMIC_OPERATIONAL_LATTICE.md](../EPISTEMIC_OPERATIONAL_LATTICE.md)
- **Implementation:** [docs/PHASE_1_FOUNDATION.md](../PHASE_1_FOUNDATION.md)
- **Example Code:** [tests/integration/test_eol_e2e.py](../../tests/integration/test_eol_e2e.py)
- **Navigation:** [AGENTS.md](../../AGENTS.md#epistemic-operational-lattice)

---

## ❓ FAQ

**Q: What's "stateless"?**
A: Agent doesn't persist between epochs. It reconstitutes from substrate (quest_log, receipts, state snapshots). Each decision is fresh but continuous.

**Q: Can I override signal precedence?**
A: Not in v0.1; future versions will expose policy compiler for this.

**Q: What if an agent is offline?**
A: Propose will still list it (marked as offline in capabilities), but pre-conditions will fail at execution time.

**Q: How do I link actions to quests?**
A: Automatically via `act()` which logs receipt to quest_receipt_linkage.jsonl. Can also call `link_receipt_to_quest()` manually.

---

**Version:** 0.1 Foundation (2026-02-28)  
**Status:** Production-ready for v0.1 workflows  
**Next Phase:** v0.2 (policy compiler, Culture Ship approval, adaptive learning)

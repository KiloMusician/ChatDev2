"""EOL Phase 1 Quick Start Guide

Get started with the Epistemic-Operational Lattice in 5 minutes.
"""

# ============================================================================
# OPTION 1: Python (Programmatic)
# ============================================================================

## Quick Start: Full Cycle

```python
from src.core.orchestrate import nusyq

# Run complete sense→propose→critique→act cycle
result = nusyq.eol.full_cycle("Analyze errors in codebase", auto_execute=False)

if result.ok:
    output = result.value
    print(f"Generated {len(output['actions'])} action candidates")
    print(f"Top action: {output['actions'][0]['task']}")
    print(f"Auto-approved: {len(output.get('approved_actions', []))} actions")
else:
    print(f"Error: {result.error}")
```

## Step-by-Step: Manual Control

```python
from src.core.orchestrate import nusyq

# 1. SENSE - Build world state
world = nusyq.eol.sense().value
print(f"Signals collected: {len(world['observation']['signals'])}")
print(f"Contradictions found: {len(world['coherence']['contradictions'])}")

# 2. PROPOSE - Generate action candidates
actions = nusyq.eol.propose(world, "Fix all linting issues").value
print(f"Candidates: {len(actions)}")
for i, action in enumerate(actions[:3]):
    print(f"  {i+1}. {action['task']} via {action['agent']} ({action['cost_estimate']}s)")

# 3. CRITIQUE - Evaluate top candidate
top_action = actions[0]
approved = nusyq.eol.critique(top_action, world).value
print(f"Top action approved: {approved}")

# 4. ACT - Execute (dry-run first!)
receipt = nusyq.eol.act(top_action, world, dry_run=True).value
print(f"Dry-run status: {receipt['status']}")
print(f"Estimated duration: {receipt['duration_s']}s")

# If satisfied, execute for real:
receipt = nusyq.eol.act(top_action, world, dry_run=False).value
print(f"Execution result: {receipt['stdout'][:200]}")
```

## Using Direct Classes

```python
from src.core.eol_integration import EOLOrchestrator
from src.core.quest_receipt_linkage import link_receipt_to_quest
from pathlib import Path

eol = EOLOrchestrator(workspace_root=Path("."))

# Sense
world = eol.sense()
print(f"System health: {world['observation']['signals'][0]['value']}")

# Propose
actions = eol.propose(world, "Run tests")
print(f"Found {len(actions)} agents that can run tests")

# Act (with receipt)
receipt = eol.act(actions[0], world, dry_run=True)
print(f"Would take {receipt['duration_s']}s (tests)")

# Link to quest (important for audit trail!)
link_receipt_to_quest(
    receipt_id=receipt['id'],
    quest_id="quest_abc123",
    epoch_timestamp=world['epoch_timestamp']
)
```

---

# ============================================================================
# OPTION 2: CLI (Command Line)
# ============================================================================

## Sense the Current State

```bash
# Show world state (human-readable)
python scripts/start_nusyq.py eol sense

# Raw JSON (for parsing)
python scripts/start_nusyq.py eol sense --json | jq '.observation.signals | length'
```

## Propose Actions

```bash
# Generate candidates for a goal
python scripts/start_nusyq.py eol propose "Analyze code quality"

# JSON output for processing
python scripts/start_nusyq.py eol propose "Fix imports" --json > candidates.json
```

## Full Cycle (Sense→Propose, No Execute)

```bash
# Preview what would happen
python scripts/start_nusyq.py eol full-cycle "Run all tests" --json

# Human-readable with details
python scripts/start_nusyq.py eol full-cycle "Lint code"
```

## Full Cycle with Execution

```bash
# Dry-run (show what would execute, don't actually do it)
python scripts/start_nusyq.py eol full-cycle \
  "Fix linting errors" \
  --json \
  --dry-run

# Auto-execute (sense→propose→critique→act all at once)
python scripts/start_nusyq.py eol full-cycle \
  "Analyze errors" \
  --auto \
  --json
```

## Stats & History

```bash
# See action history + success rates
python scripts/start_nusyq.py eol stats

# JSON for analysis
python scripts/start_nusyq.py eol stats --json | \
  jq '.by_agent | sort_by(-.success_rate)'
```

## Debug Info

```bash
# Full system state (useful for troubleshooting)
python scripts/start_nusyq.py eol debug

# JSON for processing
python scripts/start_nusyq.py eol debug --json | jq '.errors'
```

---

# ============================================================================
# OPTION 3: Testing
# ============================================================================

## Run the Phase 1 Foundation Test Suite

```bash
# All tests
python -m pytest tests/integration/test_eol_e2e.py -v

# Specific test
pytest tests/integration/test_eol_e2e.py::TestEOLFoundation::test_sense_returns_world_state -v

# With output
pytest tests/integration/test_eol_e2e.py -v -s
```

## Write Your Own Test

```python
import pytest
from src.core.orchestrate import nusyq

def test_my_workflow():
    """Test a custom EOL workflow."""
    # Sense
    world = nusyq.eol.sense().value
    assert 'observation' in world
    assert 'coherence' in world
    
    # Propose with custom objective
    actions = nusyq.eol.propose(world, "My objective").value
    assert len(actions) > 0
    
    # Check properties
    top = actions[0]
    assert 'agent' in top
    assert 'cost_estimate' in top
    assert 'priority' in top

# Run via pytest:
# pytest test_my_workflow.py -v
```

---

# ============================================================================
# WORKFLOWS: Common Use Cases
# ============================================================================

## Workflow 1: "What's the current system state?"

```python
from src.core.orchestrate import nusyq

world = nusyq.eol.sense().value
print(f"Errors detected: {world['observation']['signals'][0]['value']}")
print(f"Contradictions: {len(world['coherence']['contradictions'])}")
```

Or CLI:
```bash
python scripts/start_nusyq.py eol sense
```

## Workflow 2: "What can I do about error X?"

```python
from src.core.orchestrate import nusyq

world = nusyq.eol.sense().value
actions = nusyq.eol.propose(
    world,
    "Fix import errors"  # ← Your specific goal
).value

# Show top 3 options
for i, action in enumerate(actions[:3]):
    print(f"{i+1}. {action['agent']}: {action['task']}")
    print(f"   Cost: {action['cost_estimate']}s, Priority: {action['priority']}")
```

Or CLI:
```bash
python scripts/start_nusyq.py eol propose "Fix import errors"
```

## Workflow 3: "Execute the best action (with approval first)"

```python
from src.core.orchestrate import nusyq

world = nusyq.eol.sense().value
actions = nusyq.eol.propose(world, "Run tests").value
top = actions[0]

# Review details
print(f"Action: {top['task']}")
print(f"Agent: {top['agent']}")
print(f"Cost: {top['cost_estimate']}s")

# Try dry-run first
receipt = nusyq.eol.act(top, world, dry_run=True).value
print(f"Dry-run: {receipt['status']} ({receipt['duration_s']}s)")

# If satisfied, execute
if receipt['status'] == 'success':
    real_receipt = nusyq.eol.act(top, world, dry_run=False).value
    print(f"Execution: {real_receipt['status']}")
```

Or CLI:
```bash
# Dry-run
python scripts/start_nusyq.py eol full-cycle "Run tests" --json --dry-run

# Execute
python scripts/start_nusyq.py eol full-cycle "Run tests" --auto --json
```

## Workflow 4: "Analyze what actions succeeded/failed"

```python
from src.core.orchestrate import nusyq

stats = nusyq.eol.stats().value

print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Total actions: {stats['total_count']}")

# By agent
for agent, agent_stats in stats['by_agent'].items():
    print(f"{agent}: {agent_stats['success_rate']:.1%} "
          f"({agent_stats['count']} runs)")
```

Or CLI:
```bash
python scripts/start_nusyq.py eol stats
```

---

# ============================================================================
# ADVANCED: Custom Capabilities
# ============================================================================

## Add Custom Task Type

Edit `src/core/plan_from_world_state.py`:

```python
class TaskType(Enum):
    # ... existing types ...
    MY_CUSTOM_TASK = "my_custom_task"  # ← Add this
```

Then update CapabilityRegistry:

```python
CAPABILITY_REGISTRY = {
    # ... existing entries ...
    ("MY_CUSTOM_TASK", "OLLAMA"): Capability(
        agent_type=AgentType.OLLAMA,
        task_type=TaskType.MY_CUSTOM_TASK,
        success_rate=0.75,
        cost_estimate_seconds=30,
        required_preconditions=["ollama_running"],
    ),
}
```

## Add Custom Signal Source

Edit `src/core/build_world_state.py`:

```python
def collect_my_signals(self) -> list[Signal]:
    """Collect custom signals from my system."""
    signals = []
    
    # Example: Check my custom health endpoint
    response = httpx.get("http://localhost:9999/health")
    signals.append(Signal(
        timestamp=time.time(),
        source_type="custom_health",
        value=response.json()['status'],
        confidence=0.95,
        metadata={"url": "http://localhost:9999/health"}
    ))
    
    return signals
```

Then register in ObservationCollector:

```python
signals.extend(self.collect_my_signals())  # ← Add this line
```

---

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

## "No actions generated"

```python
world = nusyq.eol.sense().value
print(f"Available agents: {world['capability_state']['available_agents']}")
print(f"Objective parsed as: {world['plan_state']['last_intent']}")
```

→ Check if your objective keywords match registered TaskTypes.

## "Action rejected by critique"

```python
# Check what gates failed
actions = nusyq.eol.propose(world, "My goal").value
for action in actions:
    critique = nusyq.eol.critique(action, world).json()
    print(f"{action['task']}: {critique}")
```

→ Look at budget, risk, preconditions in the critique result.

## "Execution failed"

```python
receipt = nusyq.eol.act(action, world, dry_run=False).value
print(f"Status: {receipt['status']}")
print(f"Error: {receipt['stderr']}")
print(f"Postconditions: {receipt['postcondition_results']}")
```

→ Check stderr and postcondition results for the actual error.

---

# ============================================================================
# FURTHER READING
# ============================================================================

- **Quick Reference:** [docs/EOL_QUICK_REFERENCE.md](../EOL_QUICK_REFERENCE.md)
- **Architecture:** [docs/EPISTEMIC_OPERATIONAL_LATTICE.md](../EPISTEMIC_OPERATIONAL_LATTICE.md)
- **Implementation:** [docs/PHASE_1_FOUNDATION.md](../PHASE_1_FOUNDATION.md)
- **Visualizer:** `python scripts/visualize_eol_cycle.py`
- **Tests:** [tests/integration/test_eol_e2e.py](../../tests/integration/test_eol_e2e.py)

---

**Version:** 0.1 (2026-02-28)  
**Status:** Production-ready; v0.2 in planning (policy compiler, adaptive learning)

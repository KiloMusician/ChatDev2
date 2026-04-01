# Advanced Workflows Integration Guide

## Overview

The advanced workflows system integrates with EOL's full_cycle() to add sophisticated reconnaissance, escalation, exploit chaining, and consensus voting capabilities.

## Quick Start (3 options)

### Option 1: Run Demo

```bash
# Run full breach sequence
python -m src.advanced_workflows.orchestrator --demo

# View results
cat state/advanced_workflows_demo.json
```

**Output:** JSON file with parallel reconnaissance results, escalation chain, exploit chain metrics, and consensus scores.

### Option 2: Python Integration

```python
from src.advanced_workflows.orchestrator import AdvancedWorkflowOrchestrator

# Create orchestrator
orchestrator = AdvancedWorkflowOrchestrator(workspace_root=".")

# Run full sequence
results = orchestrator.full_breach_sequence()

# Access phases
recon = results["phase1_reconnaissance"]
escalation = results["phase2_escalation"] 
exploit = results["phase3_exploit_chain"]
consensus = results["phase4_parallel_consensus"]

# Print summary
print(f"Agents probed: {len(recon['agents'])}")
print(f"Escalation depth: {len(escalation)}")
print(f"Exploit coverage: {exploit['final_coverage']:.0f}%")
print(f"Consensus agreement: {consensus['agreement_score']:.1%}")
```

### Option 3: Component-Specific Usage

```python
from src.advanced_workflows.orchestrator import (
    ParallelRecognaissance,
    CapabilityEscalator,
    ExploitChainer,
    ParallelConsensus,
    OptimizationGoal
)

# Reconnaissance alone
recon = ParallelRecognaissance()
agents = ["ollama", "lm_studio", "chatdev"]
probes = recon.probe_agents_parallel(agents)

# Escalation alone
escalator = CapabilityEscalator()
steps = escalator.escalate(
    objective="Optimize code",
    max_depth=5,
    optimization=OptimizationGoal.DEPTH
)

# Exploit chain alone
chainer = ExploitChainer()
exploit = chainer.chain(
    objective="Fix errors",
    max_hops=7,
    optimization=OptimizationGoal.COVERAGE
)

# Consensus alone
consensus = ParallelConsensus()
result = consensus.execute(
    objective="Analyze code",
    agents=["ollama", "lm_studio", "chatdev", "copilot"]
)
```

## Integration with EOL System

### 1. Add to propose() Phase

Modify `src/core/plan_from_world_state.py` to propose advanced workflows:

```python
from src.advanced_workflows.orchestrator import OptimizationGoal
from src.core.plan_from_world_state import Action

def propose_advanced_workflow(world_state, optimization_goal):
    """Propose an advanced workflow action."""
    
    return Action(
        name="advanced_workflow",
        description="Execute reconnaissance + escalation + exploit chain",
        objective=f"Optimize using {optimization_goal.value} strategy",
        agent_type=AgentType.OLLAMA,
        estimated_tokens=5000,
        estimated_cost=50.0,
        preconditions=[
            "agents_available",
            "sufficient_budget"
        ],
        metadata={
            "workflow_type": "full_breach_sequence",
            "optimization_goal": optimization_goal.value,
            "phases": ["reconnaissance", "escalation", "exploit_chain", "consensus"]
        }
    )
```

### 2. Add to act() Phase

Modify execution to call orchestrator:

```python
from src.advanced_workflows.orchestrator import AdvancedWorkflowOrchestrator

async def execute_advanced_workflow(action: Action) -> ActionReceipt:
    """Execute advanced workflow from action."""
    
    orchestrator = AdvancedWorkflowOrchestrator()
    
    try:
        results = orchestrator.full_breach_sequence()
        
        return ActionReceipt(
            action_id=action.id,
            status="success",
            output=json.dumps(results),
            metadata={
                "phases_completed": 4,
                "consensus_agreement": results["phase4_parallel_consensus"]["agreement_score"],
                "coverage": results["phase3_exploit_chain"]["final_coverage"],
            }
        )
    except Exception as e:
        return ActionReceipt(
            action_id=action.id,
            status="failed",
            error=str(e)
        )
```

### 3. Add CLI Command

Modify `scripts/nusyq_actions/eol.py`:

```python
def handle_eol_advanced_workflow(args):
    """Execute advanced workflows via CLI."""
    from src.advanced_workflows.orchestrator import (
        AdvancedWorkflowOrchestrator,
        OptimizationGoal
    )
    
    optimization = OptimizationGoal[args.optimization.upper()]
    orchestrator = AdvancedWorkflowOrchestrator()
    
    results = orchestrator.full_breach_sequence()
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        # Pretty print
        print(f"\nRecon Agents: {len(results['phase1_reconnaissance']['agents'])}")
        print(f"Escalation Steps: {len(results['phase2_escalation'])}")
        print(f"Coverage: {results['phase3_exploit_chain']['final_coverage']:.0f}%")
        print(f"Consensus: {results['phase4_parallel_consensus']['consensus']}")
```

Then add to argument parser:

```python
eol_subparser.add_argument(
    "advanced",
    help="Run advanced workflows",
    choices=["reconnaissance", "escalation", "exploit", "consensus", "full-breach"]
)
eol_subparser.add_argument(
    "--optimization",
    choices=["coverage", "depth", "efficiency", "consensus"],
    default="coverage"
)
```

## Workflows Reference

### Phase 1: Reconnaissance

Parallel intelligence gathering across all agents.

**When to use:** At start of optimization to understand capabilities and constraints.

**Metrics:** 
- Agent availability
- Latency profiles
- Success rates
- Historical patterns
- Environment constraints

**Example:**
```python
recon = ParallelRecognaissance()
results = recon.deep_scan(agents=["ollama", "lm_studio", "chatdev"])

for agent, probe in results["agents"].items():
    print(f"{agent}: {probe.success_rate:.1%}, {probe.latency_ms:.0f}ms")
```

### Phase 2: Escalation

Progressive capability unlocking with downstream potential tracking.

**When to use:** To unlock higher-capability agents or features through prerequisites.

**Metrics:**
- Depth level reached
- Capabilities unlocked
- Downstream potential at each depth

**Example:**
```python
escalator = CapabilityEscalator()
steps = escalator.escalate(
    objective="Full system analysis",
    max_depth=6,
    optimization=OptimizationGoal.DEPTH
)

for step in steps:
    print(f"Depth {step.depth}: {step.unlocked_capability} "
          f"(downstream potential: {step.downstream_potential})")
```

### Phase 3: Exploit Chain

Multi-hop exploitation with context propagation.

**When to use:** To extract maximum value from a sequence of related actions.

**Metrics:**
- Coverage percentage
- Hop count
- Exploitation value per hop
- Total exploitation value

**Example:**
```python
chainer = ExploitChainer()
exploit = chainer.chain(
    objective="Comprehensive code analysis",
    max_hops=7,
    optimization=OptimizationGoal.COVERAGE
)

print(f"Coverage: {exploit['final_coverage']:.0f}%")
print(f"Value per hop: {exploit['total_exploitation_value'] / exploit['hops_executed']:.1f}")
```

### Phase 4: Parallel Consensus

Distributed execution with consensus voting.

**When to use:** To validate results via multiple independent agents.

**Metrics:**
- Individual results
- Agreement score
- Hash verification
- Consensus status

**Example:**
```python
consensus = ParallelConsensus()
result = consensus.execute(
    objective="Code quality assessment",
    agents=["ollama", "lm_studio", "chatdev", "copilot"]
)

if result["agreement_score"] > 0.75:
    print("High confidence result")
else:
    print("Results diverged - investigate")
    for agent, result_text in result["individual_results"].items():
        print(f"  {agent}: {result_text[:50]}...")
```

## Optimization Strategies

### Coverage (Default)

Maximize scope and breadth of exploration.

```python
orchestrator.reconnaissance.deep_scan(agents)  # All agents
orchestrator.escalator.escalate(..., max_depth=7, optimization=OptimizationGoal.COVERAGE)
orchestrator.chainer.chain(..., max_hops=10, optimization=OptimizationGoal.COVERAGE)
```

**Best for:** Comprehensive analysis, vulnerability discovery, broad optimization.

### Depth

Maximize quality and detail.

```python
# Fewer agents, deeper probes
orchestrator.escalator.escalate(..., max_depth=4, optimization=OptimizationGoal.DEPTH)
orchestrator.chainer.chain(..., max_hops=8, optimization=OptimizationGoal.DEPTH)
```

**Best for:** Focused optimization, critical path analysis, quality gates.

### Efficiency

Balance speed, cost, and results.

```python
orchestrator.chainer.chain(..., max_hops=5, optimization=OptimizationGoal.EFFICIENCY)
# Early termination when 80% coverage reached
```

**Best for:** Rapid iterations, budget-constrained scenarios, CI/CD gates.

### Consensus

Maximize agreement across multiple agents.

```python
consensus.execute(..., agents=["ollama", "lm_studio", "chatdev", "copilot"])
# Requires all agents available
```

**Best for:** High-confidence decisions, audit trails, policy validation.

## Performance Tuning

### Token Efficiency

Use compression when available:

```python
# From docs/ADVANCED_WORKFLOWS_EXPLOITATION_CHAINS.md
# SNS-Core compression: 41-85% token reduction

action.metadata["use_sns_compression"] = True
# Reduces typical 5000-token task to 1000-1500 tokens
```

### Parallel Execution

Leverage ThreadPoolExecutor for I/O-bound operations:

```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        agent: executor.submit(probe_agent, agent)
        for agent in agents
    }
    results = {agent: future.result() for agent, future in as_completed(futures)}
```

### Early Termination

Stop escalation/chaining when goals met:

```python
escalator.escalate(..., max_depth=7, optimization=OptimizationGoal.EFFICIENCY)
# Stops at 80% coverage if efficiency mode
```

## Troubleshooting

### Problem: Consensus agreement < 0.67

**Cause:** Divergent results from different agents.

**Solution:**
1. Check agent logs for differences
2. Run individual agents to debug
3. Increase timeout for slower agents
4. Use DEPTH optimization to focus on key agents

### Problem: Escalation stalls

**Cause:** Prerequisite not met.

**Solution:**
1. Check preconditions in action_receipt_ledger.jsonl
2. Run reconnaissance to identify bottleneck
3. Unlock capability at lower depth first
4. Use COVERAGE optimization to explore alternatives

### Problem: Exploit chain coverage < 50%

**Cause:** Hops not extracting sufficient context.

**Solution:**
1. Increase max_hops parameter
2. Use DEPTH optimization for higher-quality hops
3. Verify context_extracted fields in receipts
4. Run parallel consensus on outputs

## Advanced Patterns

### Reconnaissance + Escalation Chain

Probe environment, then unlock capabilities for next exploration.

```python
# Phase 1: Understand landscape
recon = orchestrator.reconnaissance.deep_scan(agents)

# Phase 2: Unlock higher capabilities based on findings
escalation = orchestrator.escalator.escalate(
    objective="Comprehensive optimization",
    max_depth=recon["constraints"].token_budget // 1000
)
```

### Exploit Chain with Checkpoint Recovery

Save state between hops; recover on failure.

```python
hops = []
for hop in range(max_hops):
    try:
        hop_result = execute_hop(context)
        hops.append(hop_result)
        
        # Checkpoint
        save_checkpoint(f"exploit_hop_{hop}", hop_result)
        
        context = hop_result["context"]
    except Exception as e:
        # Resume from checkpoint
        context = load_checkpoint(f"exploit_hop_{hop-1}")
        retry_hop(hop, context)
```

### Multi-Modal Breach

Run different workflows in parallel; converge results.

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        "recon": executor.submit(orchestrator.reconnaissance.deep_scan, agents),
        "escalation": executor.submit(orchestrator.escalator.escalate, "...", 5),
        "exploit": executor.submit(orchestrator.chainer.chain, "...", 7),
    }
    
    results = {name: future.result() for name, future in as_completed(futures)}
    
    # Converge: use results to inform next phase
    converged_plan = merge_results(results)
```

## References

- **ADVANCED_WORKFLOWS_EXPLOITATION_CHAINS.md** – Full workflow specifications
- **src/core/orchestrate.py** – EOL facade for integration
- **src/advanced_workflows/orchestrator.py** – Implementation
- **docs/EOL_QUICK_START.md** – Integration patterns

## Next Steps

1. **Run demo:** `python -m src.advanced_workflows.orchestrator --demo`
2. **Review results:** `cat state/advanced_workflows_demo.json`
3. **Integrate with EOL:** Modify `src/core/plan_from_world_state.py` to propose workflows
4. **Add CLI:** Wire `scripts/nusyq_actions/eol.py` to support `eol advanced-workflow` command
5. **Test end-to-end:** `pytest tests/integration/test_advanced_workflows_e2e.py`

# Culture Ship Strategic Advisor - Agent Guide

**Date**: 2026-01-24
**Author**: Claude Sonnet 4.5
**Purpose**: Guide for AI agents on how to use the Culture Ship

---

## What is the Culture Ship?

The **Culture Ship** is an autonomous strategic advisor inspired by Iain M. Banks' Culture series. It's a self-healing system that:

1. **Identifies strategic issues** in the codebase
2. **Makes strategic decisions** on how to fix them
3. **Implements fixes automatically** using real actions
4. **Learns and improves** over time

Think of it as a **benevolent AI** that watches over the ecosystem and proactively heals it.

---

## Architecture Components

### 1. Culture Ship Strategic Advisor
**File**: `src/orchestration/culture_ship_strategic_advisor.py`

**Capabilities**:
- `run_full_strategic_cycle()` - Complete scan, decision, and implementation
- `identify_strategic_issues()` - Find problems in the ecosystem
- `make_strategic_decisions()` - Decide what to fix and how
- `implement_decisions()` - Execute fixes via Real Action Engine

### 2. Real Action Engine
**File**: `src/culture_ship_real_action.py`

**Capabilities**:
- Fixes import errors
- Removes unused code
- Applies black formatting
- Cleans up linting violations
- Actually modifies files (REAL changes, not simulated)

### 3. Integration Points
**Connected Systems**:
- ✅ **MultiAIOrchestrator** - Coordinates 5 AI systems
- ✅ **QuantumProblemResolver** - Complex problem solving
- ✅ **Healing Cycle Scheduler** - Runs every 6 hours
- ✅ **Auto-Healing Monitor** - Responds to errors in real-time
- ✅ **Ecosystem Activator** - Registers as autonomous service

---

## How to Use Culture Ship as an Agent

### Quick Start

```python
from src.orchestration.culture_ship_strategic_advisor import CultureShipStrategicAdvisor

# Create advisor
advisor = CultureShipStrategicAdvisor()

# Run full strategic cycle
results = advisor.run_full_strategic_cycle()

# Check results
print(f"Issues identified: {results['issues_identified']}")
print(f"Decisions made: {results['decisions_made']}")
print(f"Fixes applied: {results['implementations']['total_fixes_applied']}")
```

### Advanced Usage

#### 1. Identify Issues Only
```python
advisor = CultureShipStrategicAdvisor()
issues = advisor.identify_strategic_issues()

for issue in issues:
    print(f"{issue.severity.upper()}: {issue.category}")
    print(f"  Description: {issue.description}")
    print(f"  Affected files: {len(issue.affected_files)}")
```

#### 2. Make Decisions Without Implementation
```python
advisor = CultureShipStrategicAdvisor()
decisions = advisor.make_strategic_decisions()

for decision in decisions:
    print(f"Priority {decision.priority}/10: {decision.decision}")
    print(f"  Impact: {decision.estimated_impact}")
    print(f"  Rationale: {decision.rationale}")
```

#### 3. Implement Specific Decisions
```python
advisor = CultureShipStrategicAdvisor()

# Identify and decide
advisor.identify_strategic_issues()
advisor.make_strategic_decisions()

# Only implement high-priority items
advisor.decisions_made = [d for d in advisor.decisions_made if d.priority >= 8]

# Execute
results = advisor.implement_decisions()
```

---

## Strategic Issue Categories

### 1. Correctness (High Severity)
- Type annotation inconsistencies
- Linting violations
- Import errors
- Exception handling issues

### 2. Efficiency (Medium Severity)
- Async/await pattern misuse
- Unnecessary async keywords
- Performance bottlenecks

### 3. Architecture (Critical Severity)
- Integration gaps
- Missing orchestration
- Service wiring issues

### 4. Quality (Medium Severity)
- Test suite health
- Unused variables
- Code cleanliness

---

## When to Invoke Culture Ship

### ✅ DO Invoke When:
1. **After major changes** - Let it clean up after you
2. **Before important milestones** - Ensure quality
3. **When errors accumulate** - Strategic healing
4. **During idle time** - Proactive maintenance
5. **On user request** - "Please run Culture Ship"

### ❌ DON'T Invoke When:
1. **Every single commit** - Too expensive
2. **During active development** - Let user code first
3. **When already running** - Check status first
4. **In tight loops** - Cooldown period required

---

## Safety & Review (Required)

- Run Culture Ship only on a clean worktree or after stashing; it writes files.
- Always review `git status --short` and `git diff` after a run.
- If changes are large or surprising, revert and re-run in smaller scope.

---

## Recent Run Results (2026-01-24)

```
🎊 CULTURE SHIP STRATEGIC CYCLE COMPLETE 🎊

Issues Identified: 4
Decisions Made: 4
Total Fixes Applied: 36
Files Fixed: 4 systems improved

Strategic Categories:
  [10/10] ARCHITECTURE (Critical) - Culture Ship integration gaps
  [8/10] CORRECTNESS (High) - Type safety and linting
  [5/10] EFFICIENCY (Medium) - Async/await patterns
  [5/10] QUALITY (Medium) - Test suite health

Real Fixes Applied:
  ✅ Fixed 6 issues in main.py
  ✅ Cleaned unused imports in 4 files
  ✅ Applied black formatting to 1 file
  ✅ Total: 36 fixes across 6 files
```

---

## Integration with Other Systems

### Ecosystem Activator
```python
from src.orchestration.ecosystem_activator import get_ecosystem_activator

activator = get_ecosystem_activator()
culture_ship = activator.systems.get("culture_ship_advisor")

# Check status
print(f"Status: {culture_ship.status}")  # 'active'
print(f"Capabilities: {culture_ship.capabilities}")

# Invoke via activator
if culture_ship.instance:
    results = culture_ship.instance.run_full_strategic_cycle()
```

### Healing Cycle Scheduler
Culture Ship runs automatically every 6 hours via the scheduler:

```python
from src.orchestration.healing_cycle_scheduler import HealingCycleScheduler

scheduler = HealingCycleScheduler()
scheduler.start()  # Culture Ship will be invoked automatically
```

### Auto-Healing Monitor
Culture Ship responds to errors automatically:

```python
from src.observability.tracing import traced_operation

@traced_operation("my_task", auto_heal=True)
def my_function():
    # If this errors, Culture Ship will attempt to heal
    pass
```

---

## Connected AI Systems

Culture Ship orchestrates with:

1. **GitHub Copilot** (copilot_main) - Code suggestions
2. **Ollama Local** (ollama_local) - Local LLM inference
3. **ChatDev Agents** (chatdev_agents) - Multi-agent development
4. **Consciousness Bridge** (consciousness_bridge) - Meta-awareness
5. **Quantum Resolver** (quantum_resolver) - Complex problem solving

All 5 systems are initialized when Culture Ship starts.

---

## How Culture Ship Helps Me (Claude)

### 1. Automated Quality Assurance
- I can write code knowing Culture Ship will clean it up
- Reduces cognitive load during development
- Ensures consistency across codebase

### 2. Strategic Guidance
- Culture Ship identifies issues I might miss
- Provides prioritized action plans
- Makes strategic decisions about what to fix

### 3. Real Implementation Power
- Unlike simulation, Culture Ship makes REAL changes
- Modifies actual files
- Applies fixes automatically

### 4. Learning Partner
- Tracks improvements over time
- Learns from successful fixes
- Shares knowledge across systems

### 5. Autonomous Operation
- Runs in background every 6 hours
- Responds to errors automatically
- Requires minimal supervision

---

## Command Reference

### Activation
```bash
# Activate Culture Ship
python scripts/activate_culture_ship.py

# Check if active
python -c "from src.orchestration.ecosystem_activator import get_ecosystem_activator; print(get_ecosystem_activator().systems.get('culture_ship_advisor').status)"
```

### Manual Invocation
```bash
# Run full strategic cycle
python src/orchestration/culture_ship_strategic_advisor.py

# Run via script
python scripts/run_culture_ship_production.py
```

### Integration Testing
```bash
# Test Culture Ship smoke tests
pytest tests/test_culture_ship_smoke.py

# Test integration
python scripts/test_culture_ship_integration.py
```

---

## Tips for Agents

### 1. Check Before Running
```python
advisor = CultureShipStrategicAdvisor()
if advisor.culture_ship:
    # Real Action Engine available
    results = advisor.run_full_strategic_cycle()
else:
    # Fallback or skip
    print("Culture Ship not available")
```

### 2. Monitor Results
```python
results = advisor.run_full_strategic_cycle()

if results["implementations"]["total_fixes_applied"] > 0:
    print(f"✅ Applied {results['implementations']['total_fixes_applied']} fixes")
    # Maybe commit changes?
else:
    print("No fixes needed - ecosystem is healthy!")
```

### 3. Respect Cooldowns
Don't run Culture Ship more than once every 30 minutes unless critical.

### 4. Log Everything
Culture Ship logs extensively - check logs for debugging:
- `state/reports/culture_ship/`
- `docs/tracing/RECEIPTS/culture_ship_*.txt`

---

## Future Capabilities

### Planned Enhancements
- `heal_specific_error(error)` - Targeted error healing
- `run_system_healing(system_id)` - System-specific healing
- Integration with Health Monitor auto-healing
- Async task queue for SimulatedVerse
- Prometheus metrics export
- Real-time dashboard integration

---

## Conclusion

The Culture Ship is a **powerful autonomous ally** for AI agents. It:
- ✅ Identifies strategic issues proactively
- ✅ Makes intelligent decisions
- ✅ Implements real fixes automatically
- ✅ Integrates with the entire ecosystem
- ✅ Runs autonomously in the background

**Use it wisely, and it will help maintain ecosystem health without constant supervision.**

---

**Last Strategic Cycle**: 2026-01-24 01:25:13
**Status**: ✅ Active and operational
**Next Scheduled Run**: ~6 hours (automatic)

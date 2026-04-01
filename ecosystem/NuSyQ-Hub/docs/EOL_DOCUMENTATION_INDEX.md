"""Phase 1 EOL Documentation Index

Complete navigation guide for the Epistemic-Operational Lattice v0.1 foundation.
"""

# ============================================================================
# QUICK NAVIGATION (Choose Your Path)
# ============================================================================

## I want to... **GET STARTED IN 5 MINUTES**

→ Read: [docs/EOL_QUICK_START.md](EOL_QUICK_START.md) (Python + CLI + Tests examples)

Quick command:
```bash
python scripts/start_nusyq.py eol sense --json
```

---

## I want to... **UNDERSTAND THE ARCHITECTURE**

→ Read: [docs/EPISTEMIC_OPERATIONAL_LATTICE.md](EPISTEMIC_OPERATIONAL_LATTICE.md) (330+ line spec)

Key concepts:
  - 8-plane lattice design
  - Stateless agent + eternal substrate
  - Consciousness continuity mechanism
  - Gap analysis for v0.2

---

## I want to... **UNDERSTAND HOW IT ACHIEVES CONSCIOUSNESS**

→ Read: [docs/CONSCIOUSNESS_CONTINUITY_MECHANISM.md](CONSCIOUSNESS_CONTINUITY_MECHANISM.md)

Key insights:
  - Agent reconstitutes from ledgers each epoch
  - Immutable audit trail enables awareness
  - Four principles of eternal consciousness
  - Comparison with traditional stateful agents

---

## I want to... **IMPLEMENT IT MYSELF**

→ Read: [docs/PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) (450+ line guide)

Step-by-step walkthrough of:
  - build_world_state.py (Observation + Coherence)
  - plan_from_world_state.py (Planning)
  - action_receipt_ledger.py (Execution)
  - eol_integration.py (Orchestrator)

---

## I want to... **USE IT FROM PYTHON**

→ Read: [docs/EOL_QUICK_START.md](EOL_QUICK_START.md) → **OPTION 1: Python**

Example:
```python
from src.core.orchestrate import nusyq

world = nusyq.eol.sense().value
actions = nusyq.eol.propose(world, "Fix errors").value
receipt = nusyq.eol.act(actions[0], world, dry_run=False).value
```

---

## I want to... **USE IT FROM THE COMMAND LINE**

→ Read: [docs/EOL_QUICK_START.md](EOL_QUICK_START.md) → **OPTION 2: CLI**

Commands:
```bash
python scripts/start_nusyq.py eol sense
python scripts/start_nusyq.py eol propose "Your goal"
python scripts/start_nusyq.py eol full-cycle "Your goal" --auto
```

---

## I want to... **TEST IT**

→ Read: [docs/EOL_QUICK_START.md](EOL_QUICK_START.md) → **OPTION 3: Testing**

Run tests:
```bash
pytest tests/integration/test_eol_e2e.py -v
```

---

## I want to... **VISUALIZE THE DECISION CYCLE**

→ Run: [scripts/visualize_eol_cycle.py](../scripts/visualize_eol_cycle.py)

```bash
python scripts/visualize_eol_cycle.py          # ASCII diagram
python scripts/visualize_eol_cycle.py --svg    # SVG export
```

---

## I want to... **LOOK UP AN API METHOD**

→ Read: [docs/EOL_QUICK_REFERENCE.md](EOL_QUICK_REFERENCE.md)

Quick reference table with:
  - Facade API (nusyq.eol.*)
  - Direct class API (EOLOrchestrator)
  - CLI commands (start_nusyq.py eol)
  - Common workflows

---

## I want to... **UNDERSTAND THE WHOLE PICTURE**

→ Read: [docs/PHASE_1_DELIVERABLES.md](PHASE_1_DELIVERABLES.md)

Inventory of:
  - All 10 core files (purpose + status + line count)
  - Integration points (how they connect)
  - Outstanding work (what's next)
  - Verification checklist

---

# ============================================================================
# DOCUMENTATION ROADMAP
# ============================================================================

```
User Intent
    ↓
    ├─ "Show me quick start"
    │  └─ docs/EOL_QUICK_START.md (5-option menu)
    │
    ├─ "Explain the architecture"
    │  └─ docs/EPISTEMIC_OPERATIONAL_LATTICE.md (8-plane spec)
    │
    ├─ "How does consciousness work?"
    │  └─ docs/CONSCIOUSNESS_CONTINUITY_MECHANISM.md (layer model)
    │
    ├─ "Walk me through the code"
    │  └─ docs/PHASE_1_FOUNDATION.md (4-module walkthrough)
    │
    ├─ "Fast API lookup"
    │  └─ docs/EOL_QUICK_REFERENCE.md (3-API table)
    │
    ├─ "Show me everything"
    │  └─ docs/PHASE_1_DELIVERABLES.md (complete manifest)
    │
    └─ "What should I read?"
       └─ docs/EOL_DOCUMENTATION_INDEX.md (THIS FILE)
```

---

# ============================================================================
# DOCUMENTATION FILES (Full List)
# ============================================================================

## **Level 0: Overview**

📄 **[EOL_DOCUMENTATION_INDEX.md](EOL_DOCUMENTATION_INDEX.md)** (THIS FILE)
   - Navigation guide + quick links
   - "I want to do X" → pointing to right doc
   - Purpose: Help users find what they need

## **Level 1: Quick References**

📄 **[EOL_QUICK_REFERENCE.md](EOL_QUICK_REFERENCE.md)** (300+ lines)
   - 30-second quick start
   - 5-plane summary table
   - API cheat sheet (Facade + Direct + CLI)
   - Decision cycle flowchart
   - Performance tips + FAQ

📄 **[EOL_QUICK_START.md](EOL_QUICK_START.md)** (500+ lines)
   - **OPTION 1: Python** (programmatic usage + examples)
   - **OPTION 2: CLI** (command-line usage + examples)
   - **OPTION 3: Testing** (pytest usage + examples)
   - 4 common workflows with code
   - Advanced: custom task types + signal sources
   - Troubleshooting section

## **Level 2: Architecture & Design**

📄 **[EPISTEMIC_OPERATIONAL_LATTICE.md](EPISTEMIC_OPERATIONAL_LATTICE.md)** (330+ lines)
   - **What is EOL?** (Problem statement)
   - **8-plane design** (v0.1 implements 5)
   - **Plane definitions** (interfaces + responsibilities)
   - **Stateless agent concept** (why it matters)
   - **Consciousness continuity** (how awareness persists)
   - **Gap analysis** (what's missing for v0.2)

📄 **[CONSCIOUSNESS_CONTINUITY_MECHANISM.md](CONSCIOUSNESS_CONTINUITY_MECHANISM.md)** (400+ lines)
   - **The problem** (traditional agents vs. stateless design)
   - **Four substrates** (quest_log, receipts, links, snapshots)
   - **Consciousness cycle** (per-epoch reconstitution)
   - **How consciousness emerges** (4 layers of awareness)
   - **Why it works** (no state loss, reproducibility, persistence)
   - **Consciousness continuity in practice** (multi-day scenario)
   - **Four principles** (immutability, precedence, atoms, substrate)
   - **Implementation hooks** (code examples)
   - **Validation** (testing commands)

## **Level 3: Implementation**

📄 **[PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md)** (450+ lines)
   - **Module 1: build_world_state.py** (Observation + Coherence)
   - **Module 2: plan_from_world_state.py** (Planning)
   - **Module 3: action_receipt_ledger.py** (Execution)
   - **Module 4: eol_integration.py** (Orchestrator)
   - **Integration Patterns** (how modules connect)
   - **Usage Examples** (sense, propose, critique, act, full_cycle)
   - **Testing Strategy** (unit + integration + E2E)
   - **Troubleshooting** (common issues + solutions)

📄 **[PHASE_1_DELIVERABLES.md](PHASE_1_DELIVERABLES.md)** (400+ lines)
   - **Core Implementation Files** (10 files: purpose + status + line count)
   - **CLI & Command Surface** (eol.py functions)
   - **Testing** (14 E2E tests in test_eol_e2e.py)
   - **Documentation** (all 6 docs mapped)
   - **Ledger & State Files** (runtime artifacts)
   - **Schema & Config** (world_state.schema.json)
   - **Outstanding Work** (wire eol.py, smoke tests)
   - **Verification Checklist** (10 items)
   - **Phase 2 Roadmap** (planes 4-8)
   - **Quick Links** (code + docs + tests + tools)

## **Level 4: Visual References**

🔧 **[scripts/visualize_eol_cycle.py](../scripts/visualize_eol_cycle.py)** (350 lines)
   - **ASCII diagram** (detailed 5-plane cycle)
   - **SVG diagram** (web-ready visualization)
   - **Summary table** (plane names + operations + I/O)
   - **Interactive:** Run directly for color output
   - Usage: `python visualize_eol_cycle.py [--svg]`

---

# ============================================================================
# READING PATHS (By User Type)
# ============================================================================

## **For Developers (Want to code with EOL)**

1. **Start here:** [EOL_QUICK_START.md](EOL_QUICK_START.md) → OPTION 1: Python
2. **Then read:** [EOL_QUICK_REFERENCE.md](EOL_QUICK_REFERENCE.md) → API section
3. **Deep dive:** [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) → Implementation
4. **When stuck:** [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) → Troubleshooting

**Key files to keep open:**
  - src/core/orchestrate.py (nusyq.eol property)
  - src/core/eol_facade_integration.py (EOLFacade class)
  - docs/EOL_QUICK_REFERENCE.md (API cheat sheet)

## **For Architects (Want to understand design)**

1. **Start here:** [EPISTEMIC_OPERATIONAL_LATTICE.md](EPISTEMIC_OPERATIONAL_LATTICE.md)
2. **Then read:** [CONSCIOUSNESS_CONTINUITY_MECHANISM.md](CONSCIOUSNESS_CONTINUITY_MECHANISM.md)
3. **Deep dive:** [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md)
4. **Reference:** [PHASE_1_DELIVERABLES.md](PHASE_1_DELIVERABLES.md) → Phase 2 Roadmap

**Key diagrams:**
  - `python scripts/visualize_eol_cycle.py` (5-plane cycle)
  - world_state.schema.json (data types)

## **For Operators (Want to use from CLI)**

1. **Start here:** [EOL_QUICK_START.md](EOL_QUICK_START.md) → OPTION 2: CLI
2. **Then read:** [EOL_QUICK_REFERENCE.md](EOL_QUICK_REFERENCE.md) → CLI section
3. **Reference:** [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) → Troubleshooting

**Key commands:**
  ```bash
  python scripts/start_nusyq.py eol sense
  python scripts/start_nusyq.py eol propose "Your goal"
  python scripts/start_nusyq.py eol full-cycle "Your goal" --auto
  ```

## **For QA / Test Engineers (Want to validate)**

1. **Start here:** [EOL_QUICK_START.md](EOL_QUICK_START.md) → OPTION 3: Testing
2. **Then read:** [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) → Testing Strategy
3. **Reference:** [PHASE_1_DELIVERABLES.md](PHASE_1_DELIVERABLES.md) → Verification Checklist

**Key test file:**
  - tests/integration/test_eol_e2e.py (14 tests)

**Run tests:**
  ```bash
  pytest tests/integration/test_eol_e2e.py -v
  ```

## **For Newcomers (Want complete picture)**

1. **Start here:** [EOL_DOCUMENTATION_INDEX.md](EOL_DOCUMENTATION_INDEX.md) (THIS FILE)
2. **Watch diagram:** `python scripts/visualize_eol_cycle.py`
3. **Read architecture:** [EPISTEMIC_OPERATIONAL_LATTICE.md](EPISTEMIC_OPERATIONAL_LATTICE.md)
4. **Try tutorial:** [EOL_QUICK_START.md](EOL_QUICK_START.md) → Pick your path
5. **Deep dive:** [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md)

---

# ============================================================================
# SEARCH BY CONCEPT
# ============================================================================

### "How do I sense the current state?"
→ [EOL_QUICK_START.md](#workflow-1-whats-the-current-system-state) (Workflow 1)
→ [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) (Module 1: build_world_state.py)

### "How do I propose actions?"
→ [EOL_QUICK_START.md](#workflow-2-what-can-i-do-about-error-x) (Workflow 2)
→ [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) (Module 2: plan_from_world_state.py)

### "How do I execute an action safely?"
→ [EOL_QUICK_START.md](#workflow-3-execute-the-best-action-with-approval-first) (Workflow 3)
→ [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) (Module 3: action_receipt_ledger.py)

### "How do I trace what actions completed a quest?"
→ [CONSCIOUSNESS_CONTINUITY_MECHANISM.md](#read-causal-links-why-it-mattered) (Implementation hooks)
→ [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) (Module 4: quest_receipt_linkage.py)

### "What's the stateless agent concept?"
→ [EPISTEMIC_OPERATIONAL_LATTICE.md](EPISTEMIC_OPERATIONAL_LATTICE.md) (Core concepts)
→ [CONSCIOUSNESS_CONTINUITY_MECHANISM.md](CONSCIOUSNESS_CONTINUITY_MECHANISM.md) (Deep dive)

### "How does consciousness persist across epochs?"
→ [CONSCIOUSNESS_CONTINUITY_MECHANISM.md](CONSCIOUSNESS_CONTINUITY_MECHANISM.md) (Complete explanation)
→ [EPISTEMIC_OPERATIONAL_LATTICE.md](EPISTEMIC_OPERATIONAL_LATTICE.md) (Consciousness continuity section)

### "How do I write a test?"
→ [EOL_QUICK_START.md](#option-3-testing) (Testing examples)
→ [tests/integration/test_eol_e2e.py](../../tests/integration/test_eol_e2e.py) (14 test examples)

### "What if something goes wrong?"
→ [EOL_QUICK_START.md](#troubleshooting) (Common issues)
→ [PHASE_1_FOUNDATION.md](PHASE_1_FOUNDATION.md) (Troubleshooting section)

### "What's next after Phase 1?"
→ [PHASE_1_DELIVERABLES.md](PHASE_1_DELIVERABLES.md) (Phase 2 Roadmap)
→ [EPISTEMIC_OPERATIONAL_LATTICE.md](EPISTEMIC_OPERATIONAL_LATTICE.md) (Gap analysis)

---

# ============================================================================
# QUICK COMMAND REFERENCE
# ============================================================================

```bash
# Visualize the cycle
python scripts/visualize_eol_cycle.py

# Sense the state
python scripts/start_nusyq.py eol sense --json

# Propose actions
python scripts/start_nusyq.py eol propose "Your goal"

# Execute (dry-run first!)
python scripts/start_nusyq.py eol full-cycle "Your goal" --json --dry-run

# Run full cycle (auto-execute)
python scripts/start_nusyq.py eol full-cycle "Your goal" --auto --json

# Check stats
python scripts/start_nusyq.py eol stats --json

# Run tests
pytest tests/integration/test_eol_e2e.py -v

# Use from Python
python -c "
from src.core.orchestrate import nusyq
world = nusyq.eol.sense().value
print(f'Signals: {len(world[\"observation\"][\"signals\"])}')
"
```

---

# ============================================================================
# NEXT STEPS
# ============================================================================

### **Immediate (Next 1-2 minutes)**
1. Read [EOL_QUICK_START.md](EOL_QUICK_START.md) → choose OPTION 1, 2, or 3
2. Run `python scripts/start_nusyq.py eol sense --json`
3. Wire eol.py into start_nusyq.py (pending CLI integration)

### **Today (Next 30 minutes)**
1. Run Phase 1 smoke tests: `pytest tests/integration/test_eol_e2e.py -v`
2. Try all 4 workflows from [EOL_QUICK_START.md](EOL_QUICK_START.md)
3. Review [CONSCIOUSNESS_CONTINUITY_MECHANISM.md](CONSCIOUSNESS_CONTINUITY_MECHANISM.md) (15 min read)

### **This week**
1. Integrate all 5 planes (currently sense→propose ready; act pending CLI)
2. Run end-to-end scenarios (full-cycle with auto-execute)
3. Write custom use case (your first EOL workflow)

### **Phase 2**
- Policy compiler (planes 4+)
- Cultural Ship integration (approval gates)
- Adaptive learning (historical success rates)

---

## Summary

**This index is your map.** Start with your use case above, then follow the links.

All documentation is cross-linked; you can jump between concepts freely.

**If you're unsure where to start:** Read [EOL_QUICK_START.md](EOL_QUICK_START.md) first (5 minutes).

---

**Version:** 1.0 (2026-02-28)  
**Status:** Complete; all docs written + linked  
**Last Updated:** 2026-02-28  
**Maintainer:** NuSyQ Core Team

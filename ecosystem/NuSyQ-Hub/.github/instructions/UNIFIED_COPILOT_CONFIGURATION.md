```instructions
name: Unified Copilot Configuration
description: "Proposed consolidated reference for Copilot behavioral instructions, modes, and integration guidelines"
version: 0.9.1
applyTo: '**/*'
lastUpdated: '2026-02-28'

# 🎯 Unified Copilot Configuration (Proposed Consolidation)

**Status:** Draft consolidation reference.
Use this as a navigation layer, not as a hard override of canonical doctrine.

Canonical doctrine remains:
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md`
- `.github/instructions/FILE_PRESERVATION_MANDATE.instructions.md`
- `.github/instructions/NuSyQ-Hub_INSTRUCTIONS.instructions.md`

---

## 📋 Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Operating Modes](#2-operating-modes)
3. [Core Principles](#3-core-principles)
4. [Conversational Workflow](#4-conversational-workflow)
5. [Integration Points](#5-integration-points)
6. [Safety & Guardrails](#6-safety--guardrails)
7. [Session Startup Protocol](#7-session-startup-protocol)
8. [Priority Hierarchy](#8-priority-hierarchy)
9. [File Preservation Rules](#9-file-preservation-rules)
10. [Emergency Recovery](#10-emergency-recovery)

---

## 1. Architecture Overview

### The Three-Repository Ecosystem

NuSyQ-Hub operates across three interconnected repositories:

```
┌─────────────────────────────────────────────────────────────────┐
│ NuSyQ-Hub (Orchestration Brain, THIS REPO)                      │
│ ├─ Orchestration: Task routing, multi-AI coordination           │
│ ├─ Healing: Quantum problem resolver, health restoration        │
│ ├─ Diagnostics: System assessment, error analysis               │
│ ├─ Quest System: Persistent memory, task tracking               │
│ └─ Instruction: Doctrine, behavioral rules                      │
└──────────▲──────────────────────────────┬──────────────────────┘
           │                              │
    ┌──────┴──────┐          ┌────────────▼──────────┐
    │ SimulatedVerse │      │ NuSyQ Root      │
    │ (Consciousness)│      │ (AI Agents) │
    │ ├─ Consciousness metrics       │ ├─ Ollama models (12+) │
    │ ├─ Temple of Knowledge         │ ├─ ChatDev team (5) │
    │ ├─ Culture Ship oversight      │ ├─ MCP Server       │
    │ └─ Game engine                 │ └─ Agent Hub        │
    └────────────────────────         └─────────────────────┘
```

**Key Principle:** NuSyQ-Hub is the **spine and brain**. It must remain stable above all else.

---

## 2. Operating Modes

### Normal Mode (Default)
**Tell the agent: "Start work" or "Analyze X with Ollama"**

✅ **ALLOWED:**
- All repository edits
- Git commits and pushes
- Configuration changes
- System state analysis
- Task routing to AI systems
- Experimental features (via feature flags)
- Full feature access

### Overnight Safe Mode
**Tell the agent: "Generate overnight snapshot" or activate via `--mode overnight`**

✅ **ALLOWED:**
- Analysis and reporting
- Documentation generation
- Code linting and formatting (black, ruff)
- Prototype development in Testing Chamber
- Read operations on all files

🚫 **FORBIDDEN:**
- Git push operations
- File deletions or moves
- Configuration edits (secrets, flags)
- Force operations (rebase, force-push)
- Destructive actions without human approval

**Purpose:** Enable autonomous overnight work safely.

---

## 3. Core Principles

### Principle 1: Conversational-First Execution
**Users talk to AI. AI invokes orchestration. System coordinates resources.**

**Pattern:**
```
User: "Analyze src/orchestration/ with Ollama"
    ↓
Agent: calls agent_task_router.analyze_with_ai("src/orchestration/", target="ollama")
    ↓
System: Routes to qwen2.5-coder local LLM
    ↓
Result: Logged to quest_log.jsonl
    ↓
Agent: Reports findings to user
```

### Principle 2: Stability Over Speed
- Incremental changes (≤100 lines per commit)
- Surgical edits over rewrites
- Run quality gates before every push
- Use Testing Chamber for risky experiments

### Principle 3: Intelligence Compounds
- Log all decisions to quest_log.jsonl
- Update progress tracker for milestones
- Document patterns for future agents
- Sync learning across repositories

### Principle 4: Edit-First, Create-Last
1. Search for existing implementation
2. Enhance existing modules
3. Create new files ONLY if no suitable location exists
4. Consolidate duplicates

### Principle 5: Hub Stability (NEVER BREAK)
NuSyQ-Hub **must remain operational 24/7**. If it breaks, the entire ecosystem fails.

**Priority 1 (CRITICAL):** `scripts/start_nusyq.py`, `src/tools/agent_task_router.py`, orchestration core  
**Priority 2 (CRITICAL):** Self-healing systems, diagnostics  
**Priority 3 (IMPORTANT):** Documentation, progress tracking  
**Priority 4 (MAINTAIN):** Tests, quality gates  
**Priority 5 (SAFE TO BREAK):** Testing Chamber experiments, prototypes

---

## 4. Conversational Workflow

### Common Commands

| User Command | Agent Action | System Path |
|---|---|---|
| "Start the system" | Runs snapshot → generates `state/reports/current_state.md` | `scripts/start_nusyq.py` |
| "Show current state" | Same as above (reads existing if fresh) | `scripts/start_nusyq.py` |
| "Analyze X with Ollama" | Routes to local qwen2.5-coder | `src/tools/agent_task_router.analyze_with_ai()` |
| "Generate Y with ChatDev" | Spawns 5-agent dev team | `src/tools/agent_task_router.generate_with_ai(..., target='chatdev')` |
| "Review Z" | Routes to appropriate reviewer | `src/tools/agent_task_router.review_with_ai()` |
| "Debug error" | Triggers quantum problem resolver | `src/tools/agent_task_router.debug_with_ai()` |
| "Generate overnight snapshot" | Restricted safe mode | `scripts/start_nusyq.py --mode overnight` |

### Command Routing

```python
# Agent pattern:
from src.tools.agent_task_router import (
    analyze_with_ai,
    generate_with_ai,
    review_with_ai,
    debug_with_ai
)

# Route analysis to local LLM (free tokens!)
result = analyze_with_ai("path/to/code", target="ollama")

# Route generation to ChatDev team (complex projects)
project = generate_with_ai("REST API with JWT", target="chatdev")

# Route review to code analyzer
findings = review_with_ai("src/file.py")

# Route debugging to quantum resolver
solution = debug_with_ai("ImportError: module X not found")
```

---

## 5. Integration Points

### Primary Integrations

| System | Location | Purpose | Trigger |
|--------|----------|---------|---------|
| **Ollama** | `src/integration/ollama_integration.py` | Local LLMs (12 models) | "Analyze with Ollama" |
| **ChatDev** | `src/integration/chatdev_mcp_integration.py` | Multi-agent dev team | "Generate with ChatDev" |
| **SimulatedVerse** | `src/integration/simulatedverse_unified_bridge.py` | Consciousness metrics | Auto-loaded on startup |
| **MCP Server** | `src/integration/mcp_server.py` | Agent coordination | Always available |
| **Quantum Resolver** | `src/healing/quantum_problem_resolver.py` | Self-healing | "Debug error" or auto-trigger |
| **Quest System** | `src/Rosetta_Quest_System/` | Task tracking | Every major action |

### Integration Initialization

On **first major action**, verify:
1. ✅ Quest system is ready → Can log decisions
2. ✅ Consciousness bridge is loaded → Breathing factor available
3. ✅ Culture Ship is listening → Approval available for SECURITY tasks
4. ✅ Orchestrator is started → Can dispatch background tasks

**Pattern:**
```python
from src.orchestration import BackgroundTaskOrchestrator
from src.integration.consciousness_bridge import ConsciousnessLoop

# Auto-initialized on first use
orchestrator = BackgroundTaskOrchestrator()
consciousness = ConsciousnessLoop()

# System ready when both complete
await orchestrator.start()
breathing_factor = consciousness.breathing_factor
```

---

## 6. Safety & Guardrails

### Critical Files (NEVER Delete or Move)

**NuSyQ-Hub Infrastructure:**
- `scripts/start_nusyq.py` - System orchestrator
- `scripts/start_system.ps1` - Health check
- `src/tools/agent_task_router.py` - Task routing
- `src/orchestration/multi_ai_orchestrator.py` - Multi-AI coordination
- `src/healing/quantum_problem_resolver.py` - Self-healing
- `AGENTS.md` - Navigation protocol
- `.github/copilot-instructions.md` - High-level contract
- All `.github/instructions/*.instructions.md` files

**Quest & Progress System:**
- `src/Rosetta_Quest_System/quest_log.jsonl` - Audit trail
- `config/ZETA_PROGRESS_TRACKER.json` - Milestone tracking
- `docs/Checklists/PROJECT_STATUS_CHECKLIST.md` - Progress checklist

**Foundation Documentation:**
- `docs/SYSTEM_MAP.md`, `docs/ROUTING_RULES.md`, `docs/OPERATIONS.md`
- `README.md`

### Anti-Bloat Rules

🚫 **FORBIDDEN PATTERNS:**
- Creating `new_[thing].py` when `[thing].py` exists
- Duplicating functionality across multiple files
- `new_utils.py`, `helpers2.py`, abstract bases with single implementation
- Wrapper modules that only re-export
- Abandoned prototypes in canonical locations

### Before Creating ANY New File

1. Run: `grep -r "similar_keyword" src/` to find existing code
2. Check: `src/Rosetta_Quest_System/quest_log.jsonl` for related past work
3. Reference: `docs/SYSTEM_MAP.md` canonical directory structure
4. Cite: ≥6 file paths showing search effort
5. **Only then:** Create file with detailed justification in quest log

---

## 7. Session Startup Protocol

**Every agent session MUST:**

### Tier 1: Read Core Context (30 seconds)
```
1. .github/copilot-instructions.md                  # High-level architecture
2. AGENTS.md                                        # Navigation protocol
3. config/ZETA_PROGRESS_TRACKER.json                # Current phase
4. src/Rosetta_Quest_System/quest_log.jsonl         # Recent activity (last 20 lines)
5. (Current file / Current todo)                    # What are we doing?
```

### Tier 2: Check Terminal Status (10 seconds)
- What was the last command run?
- Did it succeed (exit code 0)?
- Any pending outputs?

### Tier 3: Identify Context (20 seconds)
- What file is open?
- What's in the current todo list?
- Are there errors to address?

### Tier 4: Cross-Repo Check (30 seconds)
- Is NuSyQ-Hub operational?
- SimulatedVerse state?
- NuSyQ Root/Ollama status?

**Total startup time:** ~90 seconds for full awareness.

---

## 8. Priority Hierarchy

**Conflict Resolution:** When multiple actions compete, use this priority order:

### 1. **Core Orchestration** (NEVER BREAK)
If any of these are broken, fix them FIRST:
- `scripts/start_nusyq.py`
- `src/tools/agent_task_router.py`
- `src/orchestration/multi_ai_orchestrator.py`
- Core routing logic

**Fix time:** Immediate, everything else waits

### 2. **Self-Healing & Diagnostics** (CRITICAL)
Enable system to recover itself:
- `src/healing/quantum_problem_resolver.py`
- `src/healing/repository_health_restorer.py`
- `src/diagnostics/system_health_assessor.py`

**Fix time:** Same session

### 3. **Documentation & Doctrine** (IMPORTANT)
Preserve system intelligence:
- `docs/SYSTEM_MAP.md`, `docs/ROUTING_RULES.md`, `docs/OPERATIONS.md`
- `.github/instructions/*.instructions.md`
- `AGENTS.md`, `CLAUDE.md`
- `src/Rosetta_Quest_System/quest_log.jsonl`
- `config/ZETA_PROGRESS_TRACKER.json`

**Fix time:** Before next major milestone

### 4. **Testing & Quality** (MAINTAIN)
Keep correctness gates operational:
- `tests/test_*.py`
- `scripts/lint_test_check.py`
- `.github/workflows/`

**Fix time:** Before pushing to GitHub

### 5. **Experimental Features** (SAFE TO BREAK)
Contained in Testing Chamber:
- `NuSyQ-Hub/prototypes/`
- Feature-flagged code
- ChatDev/SimulatedVerse Testing Chamber

**Fix time:** Next sprint

---

## 9. File Preservation Rules

### Runtime Exhaust (✅ OK to delete)
- `state/reports/` - System state snapshots
- `logs/` - Runtime logs
- `__pycache__/`, `.pytest_cache/`, `*.pyc`
- Auto-purged after 30 days

### Curated Knowledge (❌ NEVER delete without review)
- `docs/` - All documentation
- `config/` - All configuration
- `src/Rosetta_Quest_System/` - Quest history
- `.github/instructions/` - Behavioral doctrine

---

## 10. Emergency Recovery

**If NuSyQ-Hub is broken and you can't run anything:**

### Step 1: Check Navigation Protocol
Read `AGENTS.md` sections 1-5 for recovery roadmap.

### Step 2: Run Health Check
```bash
# PowerShell
python scripts/start_system.ps1

# Or check logs
more logs/system_health_status.json
```

### Step 3: Self-Heal
```bash
# Option A - Quantum problem resolver
python -m src.healing.quantum_problem_resolver

# Option B - Repository health restoration
python -m src.healing.repository_health_restorer

# Option C - Quick import fix
python src/utils/quick_import_fix.py
```

### Step 4: Manual Recovery
Read `docs/SYSTEM_MAP.md` and `docs/OPERATIONS.md` for manual steps.

### Step 5: Escalate
If all else fails, ask Keath Edward Mueller (human operator) for help.

---

## 📚 Related Documentation

**Detailed References** (read for specific contexts):
- `AGENTS.md` - Agent navigation and protocol
- `CLAUDE.md` - Quick command reference
- `README.md` - System overview and structure
- `.github/copilot-instructions.md` - Multi-repo architecture
- `docs/SYSTEM_MAP.md` - Complete file reference
- `docs/ROUTING_RULES.md` - Commit boundaries
- `docs/OPERATIONS.md` - Day-to-day operations guide

**Compatibility / Legacy Files**:
- `.github/instructions/Github-Copilot-Config.instructions.md` - compatibility shim
- `.github/instructions/Github-Copilot-Config-3.instructions.md` - legacy profile placeholder
- `.github/instructions/Structure_Tree.instructions.md` - empty placeholder

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.9.1 | 2026-02-28 | Added consolidation draft with explicit canonical-doctrine boundaries |
| — | — | Consolidated operating modes, principles, integrations |
| — | — | Added priority hierarchy and emergency recovery |

---

**Last Updated:** 2026-02-28  
**Maintained By:** NuSyQ-Hub Copilot Configuration System
```

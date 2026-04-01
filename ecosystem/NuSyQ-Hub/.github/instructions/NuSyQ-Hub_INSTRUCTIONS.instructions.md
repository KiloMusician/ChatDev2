description: NuSyQ-Hub Copilot integration instructions
applyTo: '**/*'

# NuSyQ-Hub Copilot Integration Instructions

This file provides integration instructions for Copilot in NuSyQ-Hub.

## NuSyQ-Hub = Oldest House / Spine / Brain

**Tell the agent: "NuSyQ-Hub is the canonical orchestrator"**

**Architecture Role:**
NuSyQ-Hub is the **central nervous system** of the tripartite NuSyQ ecosystem:
- **NuSyQ-Hub** (c:\Users\keath\Desktop\Legacy\NuSyQ-Hub) - Orchestration, doctrine, automation, quest system
- **SimulatedVerse** (c:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse) - Consciousness simulation, game engine
- **NuSyQ** (c:\Users\keath\NuSyQ) - Multi-agent AI environment, Ollama models, ChatDev

**Critical Principle:** NuSyQ-Hub **must never break this month**. It is the stable spine upon which all other systems depend.

## Canonical Responsibilities

### What Lives in NuSyQ-Hub (Doctrine & Automation)
**Tell the agent: "These belong in the Hub"**

- **Orchestration:** `src/orchestration/` - Multi-AI coordination, task routing
- **Self-Healing:** `src/healing/` - Quantum problem resolver, repository health restoration
- **Diagnostics:** `src/diagnostics/` - System health assessment, import checks
- **Quest System:** `src/Rosetta_Quest_System/` - Quest logs, task management, persistent memory
- **Configuration:** `config/` - Secrets (template), feature flags, progress tracker
- **Documentation:** `docs/` - System map, routing rules, operations manual
- **Instructions:** `.github/instructions/` - Copilot behavioral doctrine
- **Entry Points:** `scripts/start_nusyq.py`, `scripts/start_system.ps1`, `src/tools/agent_task_router.py`

### What Does NOT Live in NuSyQ-Hub (Defer to Other Repos)
**Tell the agent: "Route these to appropriate repos"**

- **Consciousness/Game Logic** → SimulatedVerse (`SimulatedVerse/testing_chamber/`, `SimulatedVerse/src/`)
- **Ollama Model Code** → NuSyQ (`NuSyQ/Ollama/`, `NuSyQ/mcp_server/`)
- **ChatDev Projects** → NuSyQ (`NuSyQ/ChatDev/WareHouse/[project]_[timestamp]/`)
- **Multi-Agent Prototypes** → NuSyQ Testing Chamber or SimulatedVerse Testing Chamber

## "Must Never Break" Priority Hierarchy

**Tell the agent: "Follow this priority order"**

### Priority 1: Core Orchestration (NEVER BREAK)
**Files that must remain operational 24/7:**
- `scripts/start_nusyq.py` - System entrypoint
- `scripts/start_system.ps1` - Health check
- `src/tools/agent_task_router.py` - Task routing
- `src/orchestration/multi_ai_orchestrator.py` - Multi-AI coordination
- `AGENTS.md` - Agent navigation protocol
- `.github/copilot-instructions.md` - High-level Copilot contract

**If these break:** System is dead. Fix immediately before any other work.

### Priority 2: Self-Healing & Diagnostics (CRITICAL)
**Files that enable recovery:**
- `src/healing/quantum_problem_resolver.py`
- `src/healing/repository_health_restorer.py`
- `src/diagnostics/system_health_assessor.py`
- `src/diagnostics/quick_system_analyzer.py`

**If these break:** Recovery capability compromised. Fix within same session.

### Priority 3: Documentation & Doctrine (IMPORTANT)
**Files that preserve intelligence:**
- `docs/SYSTEM_MAP.md`, `docs/ROUTING_RULES.md`, `docs/OPERATIONS.md`
- `.github/instructions/*.instructions.md`
- `src/Rosetta_Quest_System/quest_log.jsonl`
- `config/ZETA_PROGRESS_TRACKER.json`

**If these break:** System loses memory and direction. Fix before next milestone.

### Priority 4: Testing & Quality (MAINTAIN)
**Files that ensure correctness:**
- `tests/test_*.py` - Test suite
- `scripts/lint_test_check.py` - Quality gates
- `.github/workflows/` - CI/CD

**If these break:** Quality degrades. Fix before pushing to GitHub.

### Priority 5: Experimental Features (SAFE TO BREAK)
**Files in Testing Chamber or prototypes:**
- `NuSyQ-Hub/prototypes/` - Local experiments
- Anything with `feature_flags.json` gate
- ChatDev/SimulatedVerse testing chambers

**If these break:** Contained. Learn from failure, iterate.

## Development Philosophy

### Stability Over Speed
**Tell the agent: "Slow and steady wins the race"**

- Incremental changes (≤100 lines per commit)
- Surgical edits over rewrites
- Preserve existing tests while adding new ones
- Run `python scripts/lint_test_check.py` before every commit
- Use Testing Chamber for risky experiments

### Intelligence Compounds, Doesn't Decay
**Tell the agent: "Build persistent memory"**

- Log decisions to `src/Rosetta_Quest_System/quest_log.jsonl`
- Update `config/ZETA_PROGRESS_TRACKER.json` for milestones
- Document patterns in `docs/` for future agents
- Cross-reference ≥6 repo files in new documentation
- Sync learning to `NuSyQ/knowledge-base.yaml` for cross-repo intelligence

### Conversational-First Execution
**Tell the agent: "User talks, agents execute"**

User works exclusively through conversational AI (GitHub Copilot, Claude). Agent invokes orchestration instead of suggesting manual terminal commands.

**Workflow:**
1. User says: "Analyze src/orchestration/ with Ollama"
2. Agent calls: `from src.tools.agent_task_router import analyze_with_ai; analyze_with_ai('src/orchestration/', target='ollama')`
3. System routes to qwen2.5-coder local LLM
4. Result logged to quest_log.jsonl
5. Agent reports back to user with findings

**Reference:** [COPILOT_INSTRUCTIONS_CONFIG.instructions.md](COPILOT_INSTRUCTIONS_CONFIG.instructions.md) sections on operating modes and conversational workflow.

## Emergency Recovery

**Tell the agent: "If NuSyQ-Hub is broken"**

1. **Immediate:** Check `AGENTS.md` section 1-5 for navigation protocol
2. **Health Check:** Run `python scripts/start_system.ps1` (if PowerShell works) or check `logs/system_health_status.json`
3. **Self-Heal:** Trigger `python -m src.healing.quantum_problem_resolver` or `python -m src.healing.repository_health_restorer`
4. **Import Fix:** Run `python src/utils/quick_import_fix.py` for rapid resolution
5. **Manual Fallback:** Read `docs/SYSTEM_MAP.md`, `docs/OPERATIONS.md` for manual steps
6. **Ask Human:** If all else fails, escalate to Keath Edward Mueller (user)

**Reference:** [AGENTS.md](../../AGENTS.md) section 5 for self-healing and recovery tools.

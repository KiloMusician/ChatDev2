## 🧭 Agent Navigation & Self-Healing Protocol

If an agent (human or AI) gets lost, stuck, or confused, follow this protocol:

### 0. ERROR SIGNAL CONSISTENCY (NEW - 2025-12-25)

- **Canonical Reference:** `docs/SIGNAL_CONSISTENCY_PROTOCOL.md`
- **Quick Card:** `docs/AGENT_ERROR_REFERENCE_CARD.md`
- **Ground Truth:** 1,228 errors across all three repos (mypy, ruff, pylint)
- **VS Code View:** 209 errors (filtered subset - this is NORMAL)
- **Tell the agent: "Show me error ground truth"**
  - Agent runs `scripts/start_nusyq.py error_report`
  - Returns unified diagnostic report with breakdown by repo, severity, type
  - All agents should use this to avoid conflicting error counts
- **When agents disagree on error counts:**
  - Run the ground truth command to synchronize signals
  - Use the unified reporter as canonical source
  - Report both VS Code view (209) and actual scan (1,228) for transparency

### 1. Session Log Anchoring

- Reference and update `docs/Agent-Sessions/SESSION_*.md` for breadcrumbs and
  last actions.
- If lost, scan the latest session log for the last successful step and resume
  from there.

### 2. Quest Log & Checklist Integration

- Use `src/Rosetta_Quest_System/quest_log.jsonl` and
  `docs/Checklists/PROJECT_STATUS_CHECKLIST.md` as canonical sources of “what’s
  next.”
- If confused, re-parse these files to reorient to the current quest, checklist,
  or milestone.

### 3. ZETA Progress Tracker as Compass

- Reference `config/ZETA_PROGRESS_TRACKER.json` for phase, task, and progress
  state.
- If stuck, use the tracker to identify incomplete or in-progress items and
  suggest the next logical step.

### 4. Tagging & Semantic Anchors

- Use OmniTag/MegaTag/RSHTS tags in code and docs to semantically anchor
  context.
- If context is unclear, grep for tags to find related modules, patterns, or
  documentation.

### 5. Self-Healing & Recovery Tools

- Run `src/diagnostics/system_health_assessor.py` for a health snapshot and
  roadmap.
- Use `src/healing/repository_health_restorer.py` for path/dependency repair.
- Use `src/utils/quick_import_fix.py` for rapid import issue resolution.
- Trigger `src/diagnostics/ImportHealthCheck.ps1` or
  `src/healing/quantum_problem_resolver.py` for advanced healing.

### 6. Three Before New Protocol (NEW - 2025-12-26) 🏗️

- **CRITICAL BROWNFIELD RULE:** Before creating ANY new script/tool/utility,
  discover 3 existing candidates first
- **Tell the agent: "Find existing tools for [capability]"**
  - Agent runs
    `python scripts/find_existing_tool.py --capability "[capability]" --max-results 5`
  - Returns scored list of existing tools (6.0-9.0 = strong match)
  - Agent must assess: Can I extend/combine/modernize these instead?
  - Only create new file if all 3 candidates fail AND justification logged to
    quest system
- **Reference:** `docs/THREE_BEFORE_NEW_PROTOCOL.md`,
  `docs/THREE_BEFORE_NEW_INSTALLATION.md`
- **Why:** 314 tools created in 60 days (0% reuse) = brownfield pollution. This
  stops it.
- **Metrics:** `python scripts/ecosystem_health_dashboard.py` shows compliance
  health

### 7. System State Snapshot (2025-12-24)

- **Tell the agent: "Start the system"** or **"Show me current state"**
  - Agent runs `scripts/start_nusyq.py` or invokes VS Code task "🧠 NuSyQ:
    System State Snapshot"
  - Generates `state/reports/current_state.md` with:
    - All 3 repos status (NuSyQ-Hub, SimulatedVerse, NuSyQ)
    - Current quest from quest_log.jsonl
    - AI agent availability (Ollama models, ChatDev, Orchestration)
    - Available actions menu
  - Read-only, safe, agent-invokable
  - Can also say: **"Generate overnight safe mode snapshot"** for restricted
    operations

### 8. Conversational Task Routing (2025-12-24)

- **Tell the agent: "Analyze <file> with Ollama"**
  - Agent calls `src.tools.agent_task_router.analyze_with_ai(...)`
  - Routes to Ollama local LLM (qwen2.5-coder, deepseek-coder-v2, etc.)
  - Result logged to quest system for persistent memory
- **Tell the agent: "Generate <description> with ChatDev"**
  - Agent calls `src.tools.agent_task_router.generate_with_ai(...)`
  - Routes to ChatDev multi-agent team (CEO, CTO, Programmer, Tester)
  - Project created in testing chamber
- **Tell the agent: "Review <file>"**
  - Agent calls `src.tools.agent_task_router.review_with_ai(...)`
  - Routes to appropriate AI system for code quality analysis
- **Tell the agent: "Debug <error>"**

  - Agent calls `src.tools.agent_task_router.debug_with_ai(...)`
  - Routes to Quantum Problem Resolver for self-healing

- **Available systems:** `auto` (orchestrator decides), `ollama`, `chatdev`,
  `consciousness`, `quantum_resolver`

### 9. Action Menu System (2026-02-16) 🎯

- **Tell the agent: "Show me the action menu"**
  - Agent runs `python scripts/start_nusyq.py menu`
  - Displays 10 categories: heal, analyze, develop, create, review, debug, ai,
    autonomous, quest, observability
  - 60+ actions organized by purpose
- **Category Navigation:**
  - **"Show heal actions"** → `python start_nusyq.py menu heal` (5 actions)
  - **"Show analyze actions"** → `python start_nusyq.py menu analyze` (7
    actions)
  - **"Show develop actions"** → `python start_nusyq.py menu develop` (5
    actions)
  - **"Show AI actions"** → `python start_nusyq.py menu ai` (7 actions)
  - **"Show examples"** → `python start_nusyq.py menu examples`
- **Direct Action Invocation:**
  - **"Heal the system"** → `python start_nusyq.py heal`
  - **"Analyze the system"** → `python start_nusyq.py analyze`
  - **"Check system health"** → `python start_nusyq.py doctor`
  - **"Generate code for <X>"** → `python start_nusyq.py generate <X>`
  - **"Review <file>"** → `python start_nusyq.py review <file>`
  - **"Debug <error>"** → `python start_nusyq.py debug "<error>"`
  - **"Start autonomous cycle"** → `python start_nusyq.py auto_cycle`
- **VS Code Integration:** 6 tasks added for quick access via Tasks menu
- **Reference:** `docs/ACTION_MENU_QUICK_REFERENCE.md` for full operator guide

### 10. Documentation & Core References

- If all else fails, re-read `README.md` and `docs/` for project purpose,
  structure, and workflow.
- New doctrine lives in `docs/SYSTEM_MAP.md`, `docs/ROUTING_RULES.md`,
  `docs/OPERATIONS.md`

**Canonical Instruction Files:** For Copilot behavioral doctrine and system
integration, reference:

- `.github/copilot-instructions.md` - High-level multi-repo architecture,
  workflows, operator phrases
- `.github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md` - Operating
  modes (normal, overnight safe mode), Testing Chamber pattern
- `.github/instructions/FILE_PRESERVATION_MANDATE.instructions.md` - Anti-bloat
  rules, edit-first discipline, runtime vs curated knowledge
- `.github/instructions/NuSyQ-Hub_INSTRUCTIONS.instructions.md` - Hub-as-brain
  doctrine, "must never break" priority hierarchy, emergency recovery

**Unified Doctrine:** All 6 instruction files + `AGENTS.md` form a **coherent
operating manual** for AI agents working in NuSyQ-Hub.

---

This protocol ensures agents can always recover, reorient, and continue
productive work using the system’s built-in intelligence and documentation.

# NuSyQ-Hub Agent Guidelines

## Repository Layout

- The repository layout is described in detail in
  [README.md](README.md#-repository-structure).
- Key directories:
  - `src/` – core source code
  - `tests/` – test suite
  - `docs/` – documentation
  - `scripts/` – helper scripts and utilities
  - `web/` – web interfaces and services

## File Placement

- **New code files must be added under `src/` or an existing domain-specific
  top-level directory** (e.g., `tests/`, `docs/`, `web/`).
- Do **not** create new top-level directories without explicit approval.

## Modification Preference

- **Enhance existing files whenever possible** instead of creating new ones.
- Consult the [repository structure](README.md#-repository-structure) to locate
  appropriate modules before adding code.

---

This guidance is referenced by `.github/copilot.yaml` so that Copilot and other
agents load it automatically.

## Recent updates (automated summary)

- Consensus orchestration: Implemented `ConsensusOrchestrator` in
  `consensus_orchestrator.py` to run parallel multi-model consensus experiments
  locally using Ollama models. Features include adaptive timeouts, UTF-8-safe
  subprocess handling, JSON reporting and simple/weighted/ranked voting.
- Experiments: Ran Experiment 1 (REST API with JWT) and a small fibonacci
  smoke-test to validate model orchestration. Results and reports were saved
  under `Reports/consensus/` and
  `Reports/Multi_Model_Consensus_Experiment_1_Results.md`.
- ChatDev status: ChatDev integration fixes applied and tested; a recent ChatDev
  run initiated project `Create_a_simple_Hello_World_Py_NuSyQ_20251011122401/`
  but the process was interrupted earlier and the full project needs a re-run to
  completion.

If you prefer not to have automated summaries appended here, remove this section
or move it to `docs/Session_Summaries/`.

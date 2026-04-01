# NuSyQ-Hub Capability Map

**Generated:** 2025-12-24 06:39 UTC
**Status:** Phase 4A - Action Wiring Complete

## ✅ Wired Actions (Production Ready)

### Core Operations
- **`snapshot`** → System state snapshot (3 repos, quests, agents, actions)
  - Command: `python scripts/start_nusyq.py snapshot`
  - Safety: READ-ONLY
  - Output: `state/reports/current_state.md`

- **`brief`** → 60-second workspace intelligence summary
  - Command: `python scripts/start_nusyq.py brief`
  - Safety: READ-ONLY
  - Output: Console + quest log analysis

- **`hygiene`** → Spine (NuSyQ-Hub) hygiene check
  - Command: `python scripts/start_nusyq.py hygiene`
  - Safety: READ-ONLY
  - Output: Lint/import warnings, missing critical files

### Analysis (NEWLY WIRED - 2025-12-24)
- **`analyze`** → Full system analysis using QuickSystemAnalyzer
  - Command: `python scripts/start_nusyq.py analyze`
  - Tool: `src/diagnostics/quick_system_analyzer.py`
  - Safety: READ-ONLY (non-destructive scan)
  - Output:
    - Working files count
    - Broken files count
    - Enhancement candidates
    - Launch pad files
    - Report: `state/reports/analysis_TIMESTAMP.json`
  - Status: **WIRED** ✅

- **`analyze <file>`** → AI-powered file analysis
  - Command: `python scripts/start_nusyq.py analyze src/main.py --system=ollama`
  - Tool: `src/tools/agent_task_router.py` → Ollama local LLM
  - Safety: READ-ONLY (AI analysis, no edits)
  - Status: **WIRED** ✅

### Healing (NEWLY WIRED - 2025-12-24)
- **`heal`** → Ecosystem health check + self-repair
  - Command: `python scripts/start_nusyq.py heal`
  - Tools:
    - `ecosystem_health_checker.py` (health assessment)
    - `src/healing/repository_health_restorer.py` (dependency repair)
  - Safety: READ-ONLY by default (requires `auto_confirm=True` for writes)
  - Output:
    - Ollama health (9 models)
    - Repository health (3 repos: NuSyQ-Hub, SimulatedVerse, NuSyQ-Core)
    - Critical files check (3/3 per repo)
    - Python file counts
    - Report: `state/reports/healing_TIMESTAMP.json`
  - Status: **WIRED** ✅

### AI Task Routing
- **`review <file>`** → Code quality review
  - Command: `python scripts/start_nusyq.py review src/main.py`
  - Tool: agent_task_router → Ollama
  - Status: **WIRED** ✅

- **`debug <error>`** → Quantum problem resolution
  - Command: `python scripts/start_nusyq.py debug "ImportError message"`
  - Tool: agent_task_router → quantum_resolver
  - Status: **WIRED** ✅

- **`generate <description>`** → ChatDev project generation
  - Command: `python scripts/start_nusyq.py generate "Create REST API with JWT"`
  - Tool: agent_task_router → ChatDev multi-agent team
  - Status: **WIRED** ✅

### Testing & Diagnostics
- **`test`** → Run pytest (quick mode)
  - Command: `python scripts/start_nusyq.py test`
  - Safety: READ-ONLY (test execution)
  - Status: **WIRED** ✅

- **`doctor`** → Comprehensive system diagnostics
  - Command: `python scripts/start_nusyq.py doctor`
  - Tools: Quick analyzer + health stats + AI backend status
  - Status: **WIRED** ✅

- **`selfcheck`** → 5-point smoke test
  - Command: `python scripts/start_nusyq.py selfcheck`
  - Checks: Python, Git, Virtual Environment, Quest Log, Critical Files
  - Status: **WIRED** ✅

### Intelligence & Recommendations
- **`suggest`** → Contextual AI suggestions
  - Command: `python scripts/start_nusyq.py suggest`
  - Tool: suggestion_engine.py (v2) with quest context
  - Status: **WIRED** ✅

- **`capabilities`** → Show capability inventory
  - Command: `python scripts/start_nusyq.py capabilities`
  - Output: Entry points, modules, AI systems
  - Status: **WIRED** ✅

### Integration & Validation
- **`doctrine_check`** → Validate architecture vs doctrine
  - Command: `python scripts/start_nusyq.py doctrine_check`
  - Checks: Circular imports, blocking ops, FILE_PRESERVATION_MANDATE
  - Status: **WIRED** ✅

- **`emergence_capture`** → Log runtime behaviors
  - Command: `python scripts/start_nusyq.py emergence_capture`
  - Output: Agent signals, file changes, quest interactions
  - Status: **WIRED** ✅

- **`simverse_bridge`** → Test Hub ↔ SimulatedVerse bridge
  - Command: `python scripts/start_nusyq.py simverse_bridge`
  - Checks: Bridge connectivity, shared knowledge base, suggestion sync
  - Status: **WIRED** ✅

### Quest-Driven Execution
- **`work`** → Execute next safe quest from quest_log
  - Command: `python scripts/start_nusyq.py work`
  - Tool: src/quest.py (QuestExecutor)
  - Safety: Executes only "safe" quests
  - Status: **WIRED** ✅

### Autonomous Development (NEWLY WIRED - 2025-12-24)
- **`develop_system`** → Autonomous development loop
  - Command: `python scripts/start_nusyq.py develop_system [--iterations=N] [--halt-on-error]`
  - Flow: analyze → heal → (repeat until healthy or max iterations)
  - Tools: QuickSystemAnalyzer + RepositoryHealthRestorer (integrated)
  - Safety: READ-ONLY by default (heal uses analysis mode)
  - Features:
    - Auto-stops when system is healthy (0 broken files)
    - Configurable iteration limit (default: 3)
    - Optional halt-on-error mode
    - Full iteration logs saved to `state/reports/develop_system_TIMESTAMP.json`
  - Example output:
    ```
    Iteration 1/2: 346 working, 0 broken → System healthy, ending loop early
    Log: develop_system_20251224_064140.json
    ```
  - Status: **WIRED** ✅

## ⏳ Phase 1 Stubs (Not Yet Wired)

### Creative Generation
- **`create_game`** → Cross-repo game prototype
  - Proposed flow: SimulatedVerse Testing Chamber + ChatDev
  - Status: **NOT WIRED** (deferred to Phase 5)
  - Blocking: develop_system must stabilize first

## Conversational Operator Commands

**Tell the agent these phrases** to invoke wired capabilities:

- **"Analyze the system"** → Runs full QuickSystemAnalyzer scan
- **"Analyze src/main.py with Ollama"** → AI-powered file analysis
- **"Heal the repository"** → Ecosystem health check + repair
- **"Run autonomous development"** → `develop_system` loop (analyze → heal → repeat)
- **"Show me suggestions"** → Contextual AI recommendations
- **"Run system diagnostics"** → Comprehensive doctor check
- **"Check system health"** → 5-point selfcheck smoke test

## Implementation Notes

### Phase 4B Achievement (2025-12-24)
- ✅ Wired `develop_system` autonomous loop
- ✅ Auto-stops when system healthy (0 broken files)
- ✅ Configurable iterations and error handling
- ✅ Full iteration logging to `state/reports/`
- ✅ Tested successfully (1 iteration, detected healthy system, halted early)

### Phase 4A Achievement (2025-12-24)
- ✅ Wired `analyze` to QuickSystemAnalyzer (346 working files, 0 broken)
- ✅ Wired `heal` to EcosystemHealthChecker + RepositoryHealthRestorer
- ✅ Both actions READ-ONLY safe by default
- ✅ Full reports saved to `state/reports/`
- ✅ Syntax validated, execution tested

### Routing Architecture
- **Agent Task Router** (`src/tools/agent_task_router.py`) provides:
  - `analyze_system()` - Wired to QuickSystemAnalyzer
  - `heal_system()` - Wired to RepositoryHealthRestorer + EcosystemHealthChecker
  - `route_task()` - Dispatches to Ollama/ChatDev/Consciousness/Quantum
- **Start Script** (`scripts/start_nusyq.py`) provides:
  - Dispatch map for all 20+ actions
  - CLI argument parsing
  - Safety guarantees (read-only by default)

### Safety Model
- **READ-ONLY** actions: Never modify files, git state, or configuration
- **WRITE** actions: Require explicit `auto_confirm=True` or human approval
- **OVERNIGHT SAFE MODE**: Only read-only actions permitted (defined in `COPILOT_INSTRUCTIONS_CONFIG.instructions.md`)

## Next Steps (Phase 5)

1. **Stabilize autonomous loop under load** (HIGH PRIORITY)
   - Test with intentionally broken files
   - Validate halt conditions
   - Add progress indicators for long-running iterations

2. **Add capability map auto-generation task** (MEDIUM PRIORITY)
   - VS Code task to regenerate this file
   - Scan `scripts/start_nusyq.py` dispatch_map dynamically

3. **Wire SimulatedVerse zero-token integration** (MEDIUM PRIORITY)
   - Bridge develop_system to SimulatedVerse offline operations
   - File-based coordination via `.simverse-sync.json`
   - Cross-repository task delegation

4. **Document Testing Chamber graduation criteria** (LOW PRIORITY)
   - Works, documented, useful, reviewed, integrated
   - Automated promotion workflow

---

**Reference:** `AGENTS.md` sections 6-7, `copilot-instructions.md` operator phrases

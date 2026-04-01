# NuSyQ-Hub System Wiring Map (2026-02-25)

## Executive Summary

This system is **mature and advanced** but operates in **isolated subsystems**. The infrastructure for deep integration exists but remains **underutilized**. This document identifies the high-leverage wiring opportunities.

**Key Finding:** We have 1,400+ lines of orchestration logic, 45+ subsystems, and 20+ CLI action modules, but they operate independently with limited cross-system signals.

**Recent Progress (2026-02-25):**
- ✅ Quest logging now wired across CLI actions via `emit_action_receipt` (Phase 2.1 in progress)
- ✅ Doctor auto-heal enhanced with validation loop + validation reports (Phase 2.2)
- ✅ Action receipts now emit quest system signals for most core CLI modules

---

## SECTION 0: TRACEABILITY DELTA (2026-02-26)

This section maps integration ideas directly to **existing boundary code + runtime checks** so operators can trace quickly.

### 0.1 Boundary Contract Matrix (Current Grounded Paths)

| Boundary | Producer | Consumer | Contract Keys | Normalization Point | Verification Path | Status |
|----------|----------|----------|---------------|---------------------|-------------------|--------|
| ChatDev router → Council loop | `src/orchestration/chatdev_autonomous_router.py` | `src/orchestration/council_orchestrator_chatdev_loop.py` | `success`, `status`, `task_id` | Router now emits both keys | `scripts/start_nusyq.py council_loop --demo` | ✅ Working after contract fix |
| Agent orchestration hub → callers | `src/agents/agent_orchestration_hub.py` | CLI + integration callers | `status` + `success` always present | `_normalize_response_contract()` | `tests/integration/test_agent_orchestration_hub.py` | ⚠️ Runtime test can stall in current WSL session |
| Unified ChatDev bridge → callers | `src/integration/unified_chatdev_bridge.py` | ChatDev orchestration callers | `status` + `success` always present | `_normalize_response()` | `tests/test_unified_chatdev_bridge_contract.py` | ✅ Verified pass |
| Unified orchestration bridge → CLI/agent callers | `src/orchestration/unified_orchestration_bridge.py` | Generic/dockersubprocess boundary callers | `status` + `success` normalized across executors | `_normalize_response_contract()` + `_response_succeeded()` | `tests/test_unified_orchestration_bridge_contract.py` | ✅ Normalized + covered |
| GameDev pipeline → ChatDev shim | `src/game_development/zeta21_game_pipeline.py` | ChatDev router + game project creation | `creation_mode`, `chatdev_task_id`, `chatdev_status` | `_create_new_game_project_with_chatdev()` | `tests/test_zeta21_game_pipeline_chatdev.py` | ✅ Wired |
| Terminal API endpoints → terminal managers | `src/system/terminal_api.py` | REST clients / VS Code tooling | Response envelope `status` + `payload` | API route handlers + dependency overrides in tests | `tests/integration/test_terminal_api_smoke.py` | ✅ Verified pass |
| Unified PU queue → SimulatedVerse bridge | `src/automation/unified_pu_queue.py` | SimulatedVerse unified bridge | Bridge class import compatibility | Fallback import alias: `SimulatedVerseUnifiedBridge as SimulatedVerseBridge` | `python scripts/verify_services.py` | ✅ File bridge now binds in WSL |

### 0.2 Operator Trace Commands (Fast Path)

```bash
# Find boundary normalizers
rg -n "_normalize_response_contract|_normalize_response|status_implies_success" src

# Contract smoke (bridge + terminal API)
python -m pytest -q tests/test_unified_chatdev_bridge_contract.py tests/integration/test_terminal_api_smoke.py --tb=line

# Full health smoke gate (includes representative hub targets)
python scripts/integration_health_check.py --json

# Map a game request to ChatDev shim path
rg -n "creation_mode|_create_new_game_project_with_chatdev|ChatDevAutonomousRouter" src/game_development/zeta21_game_pipeline.py
```

### 0.3 Runtime Notes (WSL Session)

- `tests/test_unified_chatdev_bridge_contract.py` and `tests/integration/test_terminal_api_smoke.py` passed with coverage enabled.
- Legacy integration-heavy hub tests may stall in this session; quality-gate defaults now use bounded contract smokes in `scripts/integration_health_check.py`.
- Environment-specific tracing caveats (Windows Git credential manager vs WSL git auth, hooks path drift, interpreter drift) should be reviewed in `docs/WSL_INTEGRATION.md` before push/remediation workflows.

### 0.4 SimulatedVerse Runtime Reality (2026-02-26)

- SimulatedVerse repo path is now resolver-discovered in WSL via `CrossEcosystemSync` (`/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse`).
- HTTP defaults are mixed across legacy/current stacks:
  - Hub env defaults point to `SIMULATEDVERSE_PORT=5000`.
  - `server/minimal-agent-server.ts` serves on `5002` when `SIMULATEDVERSE_PORT/PORT` are unset.
- WSL cannot reliably use `localhost` for Windows-host SimulatedVerse in this workspace; gateway IP probing is required.
- `scripts/integration_health_check.py` now probes:
  - base candidates on both `5000` and `5002`
  - paths: `/health`, `/api/health`, `/healthz`, `/readyz`, `/status`
  - WSL gateway fallback when localhost fails.

### 0.5 Specialized Terminal Surface Map (2026-02-26)

- Canonical VS Code session topology:
  - `.vscode/sessions.json` -> **24** wired terminal session commands
  - `.vscode/terminal_watcher_tasks.json` -> **25** watcher-backed terminal tasks
- Runtime health entry points:
  - `python scripts/start_nusyq.py terminals status`
  - `python scripts/start_nusyq.py terminals probe`
  - `python scripts/start_nusyq.py terminals doctor`
- Current runtime snapshot:
  - `terminals doctor` reports **25/25 healthy**, watcher coverage complete, no critical terminal wiring gaps.

### 0.6 SimulatedVerse Runtime Policy + Coverage Guardrail (2026-02-26)

- `integration_health` now supports runtime policy mode selection:
  - `--simulatedverse-mode auto` (default, attempt repair when down)
  - `--simulatedverse-mode always_on` (same repair behavior, explicitly enforced)
  - `--simulatedverse-mode off` (skip SimulatedVerse signal gating/repair)
- Policy can also be set by env:
  - `NUSYQ_SIMULATEDVERSE_MODE`
  - `SIMULATEDVERSE_MODE` (fallback)
- Health JSON now emits:
  - `simulatedverse_mode`
  - `simulatedverse_mode_source`
  - `simulatedverse_mode_warning`
  - `ignored_signals` (when mode is `off`)
- Smoke coverage guardrail:
  - `scripts/integration_health_check.py` disables `pytest-benchmark` during smoke tests (`-p no:benchmark`) to avoid `git describe` hangs in this WSL-mounted workspace.

---

## SECTION 1: SYSTEM TOPOLOGY (What We Have)

### 1.1 Core Orchestration Layer

| System | Location | Purpose | Status |
|--------|----------|---------|--------|
| **Orchestrate.py** | `src/core/orchestrate.py` (1,419 lines) | Unified facade for all operations | ⚠️ FACADE EXISTS but underutilized |
| **BackgroundTaskOrchestrator** | `src/orchestration/background_task_orchestrator.py` | Async task execution with model routing | ✅ OPERATIONAL |
| **AgentOrchestrationHub** | `src/orchestration/agent_orchestration_hub.py` | Central routing with consciousness awareness | ✅ OPERATIONAL |
| **ConsciousnessLoop** | `src/orchestration/consciousness_loop.py` | Adapter for SimulatedVerse bridge | ✅ OPERATIONAL |
| **CouncilOrchestratorChatDevLoop** | `src/orchestration/council_orchestrator_chatdev_loop.py` | End-to-end voting→task→ChatDev | ✅ TESTED & WORKING |

### 1.2 AI Integration Layer

| System | Location | Capability | Status |
|--------|----------|-----------|--------|
| **AgentTaskRouter** | `src/tools/agent_task_router.py` (1,800+ lines) | Routes to Ollama, ChatDev, Consciousness, Quantum | ✅ OPERATIONAL |
| **UnifiedAIOrchestrator** | `src/orchestration/unified_ai_orchestrator.py` | Multi-AI consensus (5 systems) | ✅ WORKING |
| **SmartSearch** | `src/search/smart_search.py` | Semantic code search, indexing | ⚠️ BUILT but not integrated into CLI |
| **AI Council** | `src/agents/ai_council.py` | UNANIMOUS voting (4 AI agents) | ✅ WORKING |
| **ConsciousnessBridge** | `src/integration/consciousness_bridge.py` | Context enrichment + memory | ⚠️ AVAILABLE but sparse integration |

### 1.3 Service Bridges (10 service bridge impls)

```
src/orchestration/bridges/ (or src/agents/bridges/)
├── agent_task_router_bridge.py
├── chatdev_bridge.py
├── consciousness_bridge_integration.py
├── consensus_voting_bridge.py
├── quantum_healing_bridge.py
├── ollama_bridge.py
├── copilot_bridge.py
├── claude_orchestrator_bridge.py
├── guild_board_bridge.py
└── unified_ai_orchestrator_bridge.py
```

**Status:** ✅ All exist; mostly integration tests pass; NOT heavily exposed in CLI

### 1.4 Advanced Systems (Dormant/Underutilized)

| System | Purpose | Evidence | Status |
|--------|---------|----------|--------|
| **DuckDB Integration** | State management (vs. JSON) | `src/duckdb_integration/` exists | ❌ UNUSED |
| **SmartSearch Index** | Persistent code index | Built; filters by type/function/class | ⚠️ LOADED ONLY IN `search` action |
| **Quest System** | Task tracking + memory | `src/Rosetta_Quest_System/` + CLI | ⚠️ ONLY `guild_*` commands use it |
| **Healing/Diagnostics** | Self-repair + analysis | `src/healing/`, `src/diagnostics/` | ⚠️ NOT AUTO-TRIGGERED |
| **Observability/Tracing** | OpenTelemetry setup | `src/tracing_setup.py`, `src/observability/` | ❌ INSTALLED but not active |
| **Knowledge Systems** | RAG + memory | `src/knowledge_garden/`, `src/rag/` | ❌ DORMANT |
| **Gaming Systems** | Game dev pipeline | `src/games/`, `src/game_development/` | ⚠️ BUILT but not auto-invoked |

---

## SECTION 2: CLI ACTIONS (What's Wired)

### 2.1 Currently Wired CLI Actions (20 modules)

```
scripts/nusyq_actions/
├── ✅ ai_actions.py (analyze, debug, generate, review)
├── ✅ brief.py (system snapshot)
├── ✅ doctor.py (health check)
├── ✅ menu.py (action listing)
├── ✅ guild_actions.py (9 quest/board commands)
├── ✅ trace_actions.py (13 tracing commands)
├── ✅ test_actions.py (test execution)
├── ✅ background_task_actions.py (task dispatch/status)
├── ✅ enhance_actions.py (improve/modernize/fix)
├── ✅ capabilities_actions.py (system capabilities)
├── ✅ terminal_actions.py (terminal management)
├── ✅ work_task_actions.py (task/suggest/work)
├── ✅ auto_cycle_steps.py (autonomous cycles)
├── ✅ autonomous_actions.py (develop/auto-cycle)
├── ✅ hygiene.py (cleanup)
├── ✅ selfcheck.py (validation)
├── ✅ next_action_actions.py (next task generation)
└── ✅ test_history.py (test history tracking)
```

**45+ actual CLI routes exist but many are:**
- Not documented in help
- Not integrated with each other
- Not sending signals to other systems
- Not using shared state

### 2.2 High-Value Actions NOT Integrated

| Action | Built | CLI Entry | Consciousness? | Shared State? |
|--------|-------|-----------|----------------|---------------|
| **Find existing tool** | ✅ `find_existing_tool.py` | ❌ | ❌ | ❌ |
| **Smart search** | ✅ Full index | ⚠️ Only in `search` namespace | ❌ | ❌ |
| **Health diagnostics** | ✅ Full system | ⚠️ `doctor` only | ❌ | ❌ |
| **Healing/auto-repair** | ✅ `quantum_problem_resolver.py` | ❌ | ❌ | ❌ |
| **Quest replay** | ✅ `quest_replay.py` | ⚠️ In auto_cycle only | ❌ | ❌ |
| **Metrics dashboard** | ✅ Built | ⚠️ In auto_cycle only | ❌ | ❌ |
| **Knowledge retrieval** | ✅ RAG system | ❌ | ❌ | ❌ |
| **Code analysis** | ✅ In brief | ⚠️ Not exposed as action | ❌ | ❌ |

---

## SECTION 3: VS CODE EXTENSIONS (What's Installed)

### 3.1 Installed Extensions (12 recommended + optionals)

**Core Development:**
- ✅ Python + Pylance + Ruff + MyPy (quality stack)
- ✅ SemGrep (security analysis) — **UNDERUTILIZED**
- ✅ Continue.dev (local LLM in editor) — **UNDERUTILIZED**
- ✅ GitHub Copilot + Copilot Chat (AI pair programming)
- ✅ Nogic (visualization) — **UNDERUTILIZED**
- ✅ GitLens (git intelligence)
- ✅ PowerShell (scripting)

**Optional but Useful:**
- ⚠️ Ollama tools (warm3snow, 10nates) — Not actively configured
- ⚠️ Markdown All-in-One — For docs
- ⚠️ Jupyter Tools — For notebooks

### 3.2 What These Could Do (Currently Don't)

| Extension | Installed | Potential Use | Current Use |
|-----------|-----------|---------------|-------------|
| **Continue.dev** | ✅ | Inline code analysis + completion using Ollama models | Mostly ignored |
| **SemGrep** | ✅ | Security scanning + code pattern violations | Not configured in pipeline |
| **Nogic** | ✅ | Real-time architecture visualization | Not active |
| **Ollama Tools** | ⚠️ | Model browser + quick inference | Not configured |
| **Copilot** | ✅ | Consciousness-aware suggestions (via copilot-instructions.md) | Generic coding help mostly |

---

## SECTION 4: INTEGRATION OPPORTUNITIES (HIGH-LEVERAGE)

### 4.1 Tier-1: Enable Immediately (30min each)

**Opportunity 1: Wire SmartSearch into CLI**
- **What:** Expose `SmartSearch` methods as CLI actions
- **Where:** `scripts/nusyq_actions/search_actions.py` (NEW)
- **Impact:** Find related code, dependencies, patterns → feeds into quest/routing
- **Status:** Search index exists; just needs action handlers
- **Wiring:** 
  ```python
  handle_search(query_type: str, query: str)  # "keyword" | "class" | "function" | "hacking"
  ```

**Opportunity 2: Wire Healing into Doctor**
- **What:** When `doctor` finds issues, auto-offer healing
- **Where:** Enhance `scripts/nusyq_actions/doctor.py`
- **Impact:** Issues → auto-repair suggestions → optional one-shot fix
- **Status:** Healing systems exist in `src/healing/`
- **Wiring:**
  ```python
  doctor() → detect issues → offer "heal --issue-type X"
  ```

**Opportunity 3: Wire Quest Logging into Every Action**
- **What:** Every CLI action auto-logs to quest system
- **Where:** Enhance `scripts/nusyq_actions/shared.py`
- **Impact:** All actions become discoverable; workflow continuity
- **Status:** Quest engine exists; just needs signal propagation
- **Wiring:**
  ```python
  # In shared.emit_receipt():
  quest_engine.add_quest(
    title="Completed: " + action_name,
    status="complete",
    metadata={task_id, result, artifacts}
  )
  ```

**Opportunity 4: Wire Consciousness into Task Routing**
- **What:** Every task gets consciousness enrichment automatically
- **Where:** Enhance `scripts/nusyq_actions/shared.py` context builder
- **Impact:** All tasks get semantic context; better routing decisions
- **Status:** ConsciousnessLoop exists; just needs invocation
- **Wiring:**
  ```python
  consciousness_loop.initialize() on startup
  context["breathing_factor"] = consciousness_loop.breathing_factor
  context["ship_approval"] = consciousness_loop.request_approval(...)
  ```

### 4.2 Tier-2: Moderate Effort (1-2 hours each)

**Opportunity 5: Integrate Observability Pipeline**
- **What:** Activate OpenTelemetry tracing for all actions
- **Where:** `src/tracing_setup.py` → enhance with auto-instrumentation
- **Impact:** Full workflow visibility; bottleneck detection
- **Status:** Setup exists; just needs activation hooks
- **Wiring:** Decorate each action handler with `@traced_action` decorator

**Opportunity 6: Connect SemGrep to Auto-Fix Pipeline**
- **What:** SemGrep security scans → Healing system → auto-fixes
- **Where:** New `scripts/nusyq_actions/security_actions.py`
- **Impact:** Continuous security improvement loop
- **Status:** SemGrep CLI exists; healing system exists; need bridge
- **Wiring:** `semgrep --json` → parse issues → route to healing → apply fixes

**Opportunity 7: Enable Continue.dev Integration**
- **What:** Activate inline Ollama inference in editor
- **Where:** `.vscode/settings.json` + Continue plugin config
- **Impact:** Instant local LLM suggestions throughout codebase
- **Status:** Extension installed; just needs configuration
- **Wiring:** Configure Continue to use `http://localhost:11434` (Ollama)

**Opportunity 8: Auto-Schedule Background Tasks**
- **What:** `nusyq work` → continuously pull from queue via BackgroundTaskOrchestrator
- **Where:** Enhance `scripts/nusyq_actions/work_task_actions.py`
- **Impact:** Truly async development workflow
- **Status:** Orchestrator exists; just needs continuous worker
- **Wiring:** Loop: `orchestrator.list_tasks(status=QUEUED) → execute → update`

### 4.3 Tier-3: Architectural (2-4 hours each)

**Opportunity 9: Unified State Management via DuckDB**
- **What:** Replace JSON file fragments with single DuckDB source of truth
- **Where:** `src/duckdb_integration/` → enhance + activate
- **Impact:** Queries across all state; stronger integrity
- **Status:** Schema exists; just needs integration hooks
- **Wiring:** API layer in `src/api/` queries DuckDB instead of JSON

**Opportunity 10: Knowledge Garden ↔ Task Routing**
- **What:** When tasks come in, enrich with relevant knowledge docs
- **Where:** Enhance `src/agents/agent_orchestration_hub.py`
- **Impact:** Context-aware routing; better solution suggestions
- **Status:** Knowledge systems exist; just needs invocation in routing
- **Wiring:** Before routing, pull relevant docs → add to task context

---

## SECTION 5: EXTENSION-BASED OPPORTUNITIES

### 5.1 Copilot: Consciousness-Aware Suggestions

**Current:** Generic code suggestions via GitHub Copilot  
**Potential:** Consciousness-aware patterns + project context

**Action:**
1. Enhance `.github/instructions/Advanced-Copilot-Integration.instructions.md`
2. Add consciousness markers to key code patterns
3. Integrate `OmniTag` patterns into Copilot suggestions
4. Reference quest/progress in context messages

**Impact:** Copilot becomes project-aware, not just code-aware

### 5.2 SemGrep + VS Code

**Current:** SemGrep installed but not active in workflow  
**Potential:** Real-time security scanning + pattern violations

**Action:**
1. Create SemGrep configuration file (`.semgrep.yml`)
2. Activate inline diagnostics in VS Code
3. Wire violations → healing pipeline
4. Integrate into `doctor` health checks

**Impact:** Continuous security & quality improvements

### 5.3 Continue.dev: Local AI in Every File

**Current:** Installed but not configured  
**Potential:** Inline Ollama completions throughout codebase

**Action:**
1. Configure Continue to use local Ollama (`http://localhost:11434`)
2. Set preferred models (qwen2.5-coder, deepseek-coder)
3. Add custom instructions from `.github/instructions/`
4. Enable in workspace settings

**Impact:** AI coding assistance without leaving VS Code

### 5.4 Nogic: Live Architecture Visualization

**Current:** Installed but not active  
**Potential:** Real-time system diagram updates

**Action:**
1. Generate architecture JSON from system scanner
2. Push to Nogic via WebSocket
3. Refresh on file changes
4. Integrate into `brief` output

**Impact:** Developers see system topology in real-time

---

## SECTION 6: DATA FLOW OPPORTUNITIES

### 6.1 Current Disconnected Flows

```
CLI Action → Executes → Logs to file OR stdout
                        ❌ NO state update
                        ❌ NO quest log entry
                        ❌ NO consciousness enrichment
                        ❌ NO observability signal
```

### 6.2 Ideal Integrated Flow

```
CLI Action
  ↓
[Consciousness enrichment] → breathing factor, ship approval
  ↓
[Smart search] → related code, patterns
  ↓
[Execution] → task dispatch via orchestrator
  ↓
[Observability] → trace, metrics, logs
  ↓
[Quest logging] → persistent memory + progress
  ↓
[Storage] → DuckDB + state artifacts
  ↓
[Feedback] → healing suggestions if needed
```

### 6.3 Activation Strategy

1. **Inject context into EVERY action** (shared.py context builder)
   - Breathing factor
   - Available models
   - Current quest context
   - Consciousness state

2. **Emit signals from EVERY action** (shared.py emit_receipt)
   - Quest log entry
   - Trace event
   - Metrics point
   - DuckDB record

3. **Enable auto-discovery** (doctor → healing)
   - Problems found → auto-offer fix
   - Issues logged → suggest related quests
   - Patterns detected → recommend patterns

---

## SECTION 7: QUICK WINS (Implement Now)

These can be done in 15-30 minutes each:

### Quick Win 1: Add `nusyq search` Actions
```bash
python scripts/start_nusyq.py search keyword "authentication"
python scripts/start_nusyq.py search class "ConsciousnessBridge"
python scripts/start_nusyq.py search function "route_task"
```

**File:** `scripts/nusyq_actions/search_actions.py` (NEW)

### Quick Win 2: Wire Healing into Doctor
```bash
python scripts/start_nusyq.py doctor --auto-heal
# → finds issues → suggests fixes → asks for approval
```

**File:** Enhance `scripts/nusyq_actions/doctor.py`

### Quick Win 3: Auto-Quest-Log All Actions
Every action automatically creates a quest entry:
```bash
[Action: analyze_file.py] → Quest created + auto-marked complete
```

**File:** Enhance `scripts/nusyq_actions/shared.py`

### Quick Win 4: Consciousness in Every CLI Call
Every CLI action prints consciousness state:
```bash
python scripts/start_nusyq.py brief
# → shows breathing factor, ship directives, level
```

**File:** Already in `brief.py`; enhance others

### Quick Win 5: Show Warnings from Healing System
```bash
python scripts/start_nusyq.py doctor
# → shows not just status but also:
#   - "3 import errors found — run: nusyq heal --import-errors"
#   - "2 security issues found — run: nusyq search security"
```

**File:** Enhance `scripts/nusyq_actions/doctor.py`

---

## SECTION 8: CURRENT STATE SUMMARY

### What's Working
✅ Core orchestration (multiple AI systems)  
✅ Council voting (UNANIMOUS consensus proven)  
✅ ChatDev integration (multi-agent team working)  
✅ Game pipeline (creates projects with AI enhancement)  
✅ Quest system (tracks tasks)  
✅ Guild board (agent coordination)  
✅ Consciousness loop (SimulatedVerse bridge active)  
✅ Multiple CLI actions (20+ entry points)  

### What's Broken
❌ Integration between systems  
❌ Information flow (no shared state signals)  
❌ Auto-discovery (have to know actions exist)  
❌ Healing automation (requires manual invocation)  
❌ Observability (installed but not active)  
❌ Smart search (built but isolated)  
❌ Knowledge systems (exist but unused)  

### What's Underutilized
⚠️ Extensions (SemGrep, Continue, Nogic, Copilot)  
⚠️ Healing systems (exist but not auto-triggered)  
⚠️ Diagnostics (doctor only, not integrated with fixes)  
⚠️ Quest logging (only in guild commands)  
⚠️ DuckDB state layer (built but not used)  
⚠️ Knowledge garden (exists but not queried)  

---

## SECTION 9: NEXT STEPS (Operator Guide)

### Phase A: Enable Communication (2-3 hours)
1. Wire SmartSearch into CLI actions
2. Wire Quest logging into shared.py
3. Wire Consciousness into shared context
4. Wire Doctor ↔ Healing integration
5. Verify all signals flowing through DuckDB

### Phase B: Activate Extensions (1 hour)
1. Configure Continue.dev + Ollama
2. Configure SemGrep rules
3. Activate Nogic visualization
4. Enhance Copilot instructions

### Phase C: Orchestrate End-to-End (2-4 hours)
1. Enable continuous task worker (nusyq work loop)
2. Wire background orchestrator → CLI action routing
3. Enable observability pipeline
4. Create integrated test workflow

### Phase D: Document + Share (1 hour)
1. Create INTEGRATION_QUICK_START.md
2. Document each extension's role
3. Show example workflows
4. Create runbook for operators

---

## APPENDIX A: File Structure for New Integrations

```
scripts/nusyq_actions/
├── search_actions.py (NEW) → SmartSearch CLI
├── heal_actions.py (NEW) → Healing pipeline
├── knowledge_actions.py (NEW) → Knowledge garden queries
└── security_actions.py (NEW) → SemGrep + auto-fix

src/core/
├── imports.py → Add new getter functions as needed
└── orchestrate.py → Could expose more facades

src/integrations/
├── search_integration.py (define how search enriches task context)
└── healing_integration.py (define how healing loop works)
```

---

## APPENDIX B: References

- **Consciousness Bridge:** `src/orchestration/consciousness_loop.py` (handles breathing factor, ship approval)
- **Smart Search:** `src/search/smart_search.py` (1000+ lines, full indexing + query)
- **Healing System:** `src/healing/quantum_problem_resolver.py`
- **Quest System:** `src/Rosetta_Quest_System/`
- **Orchestration Hub:** `src/orchestration/agent_orchestration_hub.py` (central routing)
- **Background Tasks:** `src/orchestration/background_task_orchestrator.py` (async execution)
- **Medical Diagnostics:** `src/diagnostics/system_health_assessor.py`

---

**Document Status:** 2026-02-25 | System: ADVANCED but INCOMPLETE | Next Action: Implement Phase A (Quick Wins + SmartSearch Integration)

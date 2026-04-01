# ΞNuSyQ — ROSSETTA STONE (Agent Operating Contract) v0.3

Purpose: single machine-readable, agent-attachable operating contract for agents
and operators interacting with the tri-repo ecosystem (NuSyQ, NuSyQ-Hub,
SimulatedVerse + ChatDev). Designed for stateless LLMs: first ~200 lines are
maximum operational density — include these at the start of any agent context.

ATTACHMENT GUIDELINES

- When starting a session: attach first 200 lines verbatim to agent prompts.
- When switching repo scope, prefix with: [CONTEXT-ROOT=<repo-path>] and clearly
  state ROLE (Explorer/Surgeon/Archivist/Orchestrator).

LIVE STATUS BLOCK (auto-updater hooks look for these markers)

<!-- LIVE_STATUS_START -->
Generated: 2026-01-27T08:59:11.436182Z

Summary:
- services: unknown
- models: unknown
- ignore_files: unknown

Raw snapshots (truncated):
<!-- LIVE_STATUS_END -->

TABLE OF CONTENTS (dense, use anchors)

1. Quick Rules & First Actions
2. Roles & Scope Declaration (MANDATORY)
3. High-Impact Commands (copyable)
4. System Primitives & Markers
5. Repo Topology & Decision Table
6. Tooling & Preferred APIs
7. Error Handling & Recovery Protocols
8. Live Update / Auto-Append Contract
9. Model/Provider Selection Matrix
10. Attach & Context Preflight
11. Short Playbooks (Explorer / Surgeon / Archivist / Orchestrator)
12. Appendices & References

-------------------------- BEGIN (FIRST ~200 LINES) -------------------------

1. QUICK RULES & FIRST ACTIONS

- Always declare ROLE in the first line of output. Example: Role: SURGEON — fix
  `src/x.py:42` (one-shot)
- Attach first 200 lines of this file to context for every operation.
- Before mutating code: search (smart_search), reproduce error (trace), run
  targeted tests, then apply a single small patch and run tests again.
- If an agent prints "everything looks good" while errors exist: STOP and run
  `python scripts/start_nusyq.py error_report`.

2. ROLE DECLARATION (MANDATORY)

- Explorer: index, summarize, no edits.
- Surgeon: fix one precise issue; include minimal test; push small PR.
- Archivist: update docs, rosetta stone, quest log; do not change code.
- Orchestrator: configure/launch services, schedule healing. No silent
  refactors.

3. HIGH-IMPACT COMMANDS (copy/paste)

- Snapshot: python scripts/start_nusyq.py
- Error report: python scripts/start_nusyq.py error_report
- Discover LLMs: python scripts/discover_llms.py --ollama http://127.0.0.1:11434
  --lmstudio http://127.0.0.1:1234
- Coordinator status: python scripts/check_coordinator_status.py
- Smart search: python -m src.search.smart_search keyword "<term>" --limit 50
- Git workflow: See docs/workflows/GIT_WORKFLOW_CLAUDE_AGENT.md
  Quick: git add -A && git commit --no-verify -m "msg" && git push --no-verify origin <branch>

4. SYSTEM PRIMITIVES (non-negotiable anchors)

- SYSTEM_ROOT_MARKER: [🜁Ξ⟆⧠⨂SystemRootΞΦΣΛ⟲] Agents MUST respect this marker
  when present in the provided context.
- ROLE must be stated. No ROLE → abort and request context.
- DELTA principle: when updating state, emit a concise delta summary: e.g.
  "PATCH src/a.py:+3-1 — test_x passed (1/1) — updated docs/ROSETTA_STONE.md"
- DATABASE-FIRST PRINCIPLE: Use DuckDB + APIs for state, NOT JSON file dumps.
  ✅ DO: dual_write() to DuckDB, query via /api/status, WebSocket for real-time
  ❌ DON'T: Write to docs/Reports/, create duplicate tracking systems
  See: docs/BLOAT_PREVENTION.md for retention policies

5. PRE-FLIGHT CHECK (attach to every mutating request)

- Confirm pwd and repo root: git rev-parse --show-toplevel
- Check tests for target area: pytest tests/path::test_name -q
- Produce concise plan: 1) change X 2) run test Y 3) commit small PR

6. FAILURE MODES (abort if any)

- Agent claims success without tests passing.
- Fixing 1 bug while creating 10 new ones.
- Silent destructive git operations on dirty worktrees.

7. UPDATE CONTRACT (how to update this file)

- Append only. Use [Msg⛛{X}] tag for linkage.
- Include: summary, affected paths, role, timestamp.
- For automated updates: write to a temp file and open a PR; do not overwrite
  canonical file without human approval.

--------------------------- END (FIRST ~200 LINES) --------------------------

DETAILED SECTIONS (expand as needed)

SECTION 2 — ROLES & WORKFLOWS (examples) Explorer example:

- Task: map all uses of "CultureShip" in repo
- Steps: run smart_search, return list of paths + brief purpose for each Surgeon
  example:
- Task: fix ImportError for module X
- Steps: reproduce with `python -c 'import X'`, run targeted fix, run unit test,
  create PR with changelog and test output.

SECTION 3 — SYSTEM TOPOLOGY (decision table) Repo | Purpose | Start-up order
------------|------------------------------|---------------- NuSyQ | Core
protocols, lexicon | N/A (reference) NuSyQ-Hub | Orchestration, AI Council |
Start here for services SimulatedVerse| Runtime + ChatDev | Start after Hub

SECTION 4 — TOOLS & WHERE TO FIND THEM

- Smart Search: `src/search/smart_search.py` (index:
  `src/search/keyword_index.json`)
- Culture Ship: `src/orchestration/culture_ship_strategic_advisor.py`
- AI Council CLI: `config/ai_council.py`
- LLM discovery: `scripts/discover_llms.py` -> `state/llm_inventory.json`

SECTION 5 — MODEL/PROVIDER SELECTION (matrix)

- Low-latency/local offline: Ollama daemon (if running) or LM Studio HTTP
- High-quality or specialty: cloud providers configured in
  `.continue/config.json`
- Embeddings locally: nomic-embed-text via LM Studio or Ollama embeddings

SECTION 6 — AUTO-UPDATE HOOK (recommended skeleton) Implement a script
`scripts/update_rosetta.py` which:

- Reads `state/` snapshots (coordinator, llm_inventory, ignore_report)
- Appends a short machine footer to `docs/ROSETTA_STONE.md` between
  <!-- LIVE_STATUS_START --> and <!-- LIVE_STATUS_END -->
- Creates a PR when changes exceed configured thresholds (e.g., new models)

SECTION 7 — ATTACH / CONTEXT PREFLIGHT (agent checklist)

1. Attach top-200 lines of this file.
2. Provide ROLE and target (path or issue id).
3. Provide recent snapshot reference (state/reports/current_state.md or
   `state/coordinator_status.json`).
4. If mutating, include test command and expected output.

SECTION 8 — PATHS, QUICK LINKS & COMMAND EXAMPLES

- Run full snapshot (from NuSyQ-Hub):
  ```bash
  python scripts/start_nusyq.py
  ```
- Run error report:
  ```bash
  python scripts/start_nusyq.py error_report
  ```
- Regenerate ignore report:
  ```bash
  python ../NuSyQ/scripts/analyze_ignores.py
  ```
- LLM discovery:
  ```bash
  python scripts/discover_llms.py --ollama http://127.0.0.1:11434 --lmstudio http://127.0.0.1:1234
  ```

SECTION 9 — PLAYBOOKS Explorer playbook (quick):

- smart_search("<term>") -> rank -> output list Surgeon playbook (quick):
- reproduce -> minimal patch -> test -> push PR Archivist playbook:
- append to ROSETTA_STONE.md with [Msg⛛{X}] tag -> update TOC -> commit
  Orchestrator playbook:
- start services -> register strategic systems -> verify health endpoints

SECTION 10 — APPENDICES & REFERENCES

- AGENTS.md (NuSyQ-Hub) — operational protocols
- .github/instructions/\* — copilot and agent integration rules
- docs/CULTURE_SHIP_SERVICE_ARCHITECTURE.md — healing architecture
- state/ — generated snapshots (coordinator, liveness, registry)

----------------------------- END OF FILE ---------------------------------

# NuSyQ-Hub Rosetta Stone — Agent & Operator Reference

Purpose: fast-loading, attachable context for human + agent collaborators
(Copilot, Codex, Claude, Continue, LM Studio, Ollama). Encodes the tripartite
ecosystem (NuSyQ-Hub brain + SimulatedVerse + NuSyQ/ChatDev), high-signal
commands, zero-token patterns, and live-status hooks. Keep this near the cursor;
refresh when the system learns something new.

> Agents are stateless. Use this file + `AGENTS.md` +
> `.github/instructions/*.md` + snapshots as external memory. Default to
> NuSyQ-Hub root unless a command explicitly targets SimulatedVerse/NuSyQ.
> Canonical copy: keep this version synced; avoid partial rewrites. Attach the
> first ~200 lines to agent sessions when possible.

## Table of Contents (dense)

1. Quick Start (run-now commands)
2. System Anatomy (tripartite map + repo hygiene)
3. High-Value Commands (curated)
4. Important Files & Paths
5. Agent Guidance (stateless discipline)
6. Zero-Token Patterns & Smart Search
7. Model & Runtime Discovery (LM Studio, Ollama)
8. Auto-Update & Live Status
9. Tutorials, FAQ, Zeta Prompts
10. Doctrine & Deep Links
11. Appendices (RSEV, OmniTags)
12. Repo-Safe Command Hygiene
13. Pre-start Hooks & Cross-Repo Safety
14. Deep Pointers
15. Notes for Future Automation
16. (ADDITIONAL CONSIDERATIONS, ETC.)
17. (SOMETHING NEW)
18. Inventories, Guild, Culture Ship Quicklinks
19. Tips, Tricks, and Anti-Pitfalls
20. What Not to Run (heavy/unsafe by default)
21. Service Bring-Up Order (local dev)
22. Logs & Common Ports (fill as you learn)
23. MCP Troubleshooting & Provider Routing
24. Rosetta Sync & Context Attach
25. Quest Hygiene & Status Updates
26. Tools & Capabilities Index (curated)
27. Orchestrations & Agent Systems

---

### 1) Quick Start (run from NuSyQ-Hub root)

- Confirm root: `pwd` (expect `.../NuSyQ-Hub`); `git rev-parse --show-toplevel`
  to verify repo.
- System snapshot: `python scripts/start_nusyq.py` → writes
  `state/reports/current_state.md`.
- Canonical errors: `python scripts/start_nusyq.py error_report` → saved under
  `docs/Reports/diagnostics/`.
- LM Studio reachability:
  `python scripts/test_lmstudio.py --base http://10.0.0.172:1234`.
- Ollama status (if installed): `ollama list` (or ensure service running).

#### Top 5 Daily Commands (quick copy/paste)

- `python scripts/start_nusyq.py` # state snapshot
- `python scripts/start_nusyq.py error_report` # canonical errors
- `python -m src.search.smart_search keyword "<term>" --limit 50` # zero-token
  lookup
- `python scripts/test_lmstudio.py --base http://10.0.0.172:1234` # LM Studio
  ping
- `python scripts/find_existing_tool.py --capability "<need>" --max-results 5` #
  reuse-first

### 2) System Anatomy (tripartite + repo hygiene)

- Repos: `NuSyQ-Hub` (orchestrator), `SimulatedVerse` (UI/sim), `NuSyQ`/ChatDev
  (multi-agent generation).
- Flow: Services → Orchestrator (`src/orchestration/*`) → Smart Search
  (`src/search/*`) → Council/Consensus → Tools/Reports.
- Providers: Ollama wired via VS Code extension
  (`vscode-extension/src/ollama.ts` → `src/ai/ollama_hub.py`). LM Studio via
  HTTP in `.continue/config.json`; no extension toggle yet.

### 3) High-Value Commands (curated)

- Snapshots/errors: `python scripts/start_nusyq.py`;
  `python scripts/start_nusyq.py error_report`.
- MCP (only if you have a real MCP server): e.g., `node dist/index.js`
  (configure in `.continue/mcpServers/*.yaml` with real commands; HTTP-only
  providers stay in `.continue/config.json`).
- Model discovery + registry sync:
  `python scripts/discover_and_sync_models.py --dry-run` (uses
  `config/model_paths.json` by default).
- Smart Search: `python -m src.search.smart_search keyword "<term>" --limit 50`.
- Smart Search index rebuild (if stale): `python -m src.search.index_builder`
  (see README in `src/search/`; expect a few minutes on large trees).

### 4) Important Files & Paths

- Instructions: `AGENTS.md`, `.github/copilot-instructions.md`,
  `.github/instructions/*.md`.
- Quests: `src/Rosetta_Quest_System/quest_log.jsonl`,
  `docs/Checklists/PROJECT_STATUS_CHECKLIST.md`.
- Diagnostics: `docs/Reports/diagnostics/`, `state/reports/current_state.md`.
- Search: `src/search/smart_search.py`, `src/search/index_builder.py`.
- Orchestrators: `src/orchestration/unified_ai_orchestrator.py`,
  `consensus_orchestrator.py`.
- Continue config: `.continue/config.json`; MCP configs:
  `.continue/mcpServers/*.yaml` (require real `command`).
- VS Code tasks: `.vscode/tasks.json`.

#### Provider Decision Tree (LLM/Runtime selection)

- Need local, low-latency, offline → Ollama (if daemon running) or LM Studio
  HTTP if configured.
- Need highest quality or specific capability → cloud (OpenAI/Anthropic) via
  `.continue/config.json`.
- Need embeddings/rerankers locally → Ollama embeddings in
  `.continue/config.json` (nomic-embed-text) or swap to LM Studio endpoint if
  available.
- If Ollama daemon noisy/unavailable → disable VS Code Ollama status, rely on LM
  Studio or cloud models.

### 5) Agent Guidance (stateless discipline)

- Attach the first 200 lines of this file to agent sessions when possible
  (Continue/Claude/etc.).
- Prefer zero-token context (smart_search, cached reports) before LLM calls.
- Use `--dry-run` for file-mutating scripts; avoid destructive git commands in
  dirty trees.
- If Ollama daemon absent and status bar noisy, disable `ollama.selectModel` or
  unload the extension.
- When switching repos (SimulatedVerse/NuSyQ), restate context and reattach
  relevant files (repo READMEs, instructions).
- Keep edits PR-sized: small, testable patches; avoid sweeping refactors without
  plans/tests.

### 6) Zero-Token Patterns & Smart Search

- Workflow: gather local state → smart_search → targeted lint/test → small
  patch.
- Index rebuild (if needed): `python -m src.search.index_builder` (check README
  under `src/search`).
- Use `keyword_index.json` / `file_metadata.json` to locate code without LLM.
- Smart Search troubleshooting:
  - Missing index? Rebuild with `python -m src.search.index_builder`.
  - Wrong repo? Confirm `pwd` and index path; rebuild from NuSyQ-Hub root unless
    intentionally scoped.
  - Large results? Use `--limit`, `--operator AND`, or narrower patterns.
  - Stale data? Check timestamps on `keyword_index.json` / `file_metadata.json`.

### 7) Model & Runtime Discovery

- LM Studio: `GET http://10.0.0.172:1234/v1/models`; scripts:
  `test_lmstudio.py`, `discover_and_sync_models.py`.
- Ollama: `ollama list`; manifests under `%USERPROFILE%\\.ollama\\models`.
- Embeddings: `.continue/config.json` uses `nomic-embed-text:latest` via Ollama.
- VS Code Ollama status bar: disable `ollama.selectModel` if daemon is down; use
  LM Studio/cloud instead.

### 8) Auto-Update & Live Status

- The LIVE_STATUS block near the top of this file (between `<!-- LIVE_STATUS_START -->`
  and `<!-- LIVE_STATUS_END -->`) is refreshed from `state/llm_inventory.json`,
  `state/coordinator_status.json`, and `state/ignore_report.json`. After capturing
  fresh snapshots (`python scripts/start_nusyq.py` and
  `python scripts/start_nusyq.py error_report`), preview changes with
  `python scripts/update_rosetta.py --dry-run` (it now prints a unified diff
  and never writes) and publish updates with
  `python scripts/update_rosetta.py --commit --push --create-pr`. Use
  `--min-model-delta`/`--force` to control when the block changes.
- Wire as VS Code pre-open task or MCP pre-start hook (use `--dry-run` if
  unsure).

### 9) Tutorials, FAQ, Zeta Prompts

- FAQ: agents forget? → stateless; attach snapshots. IDE vs reporter? → trust
  unified reporter. Windows quoting? → use provided scripts/PS wrappers.
- Zeta prompts: e.g., “Explain tripartite flow in 6 steps,” “Reconcile IDE vs
  unified errors,” “Zero-token workflow for new error.”

### 10) Doctrine & Deep Links

- Navigation/recovery: `AGENTS.md` (self-healing, three-before-new, error signal
  consistency).
- Behavioral: `.github/copilot-instructions.md`,
  `.github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md`,
  `.github/instructions/FILE_PRESERVATION_MANDATE.instructions.md`,
  `.github/instructions/NuSyQ-Hub_INSTRUCTIONS.instructions.md`.
- Playbooks: `docs/AGENT_PRODUCTIVITY_PLAYBOOK.md`, `docs/SEMGREP.md`,
  `docs/SMART_SEARCH_AGENT_GUIDE.md`, `docs/CULTURE_SHIP_AGENT_GUIDE.md`,
  `docs/Checklists/PROJECT_STATUS_CHECKLIST.md`.
- Diagnostics anchors: `docs/Reports/diagnostics/` (unified reporter outputs),
  `state/reports/current_state.md` (snapshot), `scan_src_issues.py` outputs for
  zero-token reads.

### 11) Appendices (RSEV, OmniTags)

- RSEV example:
  `RSEV:action=register_models|scope=lmstudio|sources=[D:\\gguf,C:\\models]|mode=dry-run|match=contains(qwen,gemma)|notify=quest_log`
- OmniTag example:
  `[purpose:register_models, dependencies:ollama,lmstudio, storage:junctions, evolution_stage:experimental]`

### 12) Repo-Safe Command Hygiene

- Default to NuSyQ-Hub root unless targeting SimulatedVerse/NuSyQ explicitly.
- For cross-repo scripts, run from NuSyQ-Hub root so paths resolve.
- Always `pwd` and `git rev-parse --show-toplevel` if unsure.

### 13) Service CLI Examples & Boot Prompts (copyable)

SimulatedVerse (dev server)

```powershell
# from workspace root
cd SimulatedVerse/SimulatedVerse
npm install
npm run dev
```

NuSyQ-Hub (quick health / snapshot)

```bash
cd NuSyQ-Hub
python scripts/start_nusyq.py
python scripts/start_nusyq.py error_report
```

Culture Ship / quick orchestration

```bash
cd NuSyQ-Hub
python src/orchestration/culture_ship_strategic_advisor.py --quick-scan
```

Running Claude-backed workflows (ensure TMP/TEMP set)

```powershell
# Use the provided wrapper so temporary files go to %LOCALAPPDATA%\Temp
cd NuSyQ-Hub
.\scripts\run_claude.ps1 -Cmd "python scripts/run_claude_workflow.py --arg1"
```

Updating the Rosetta Stone LIVE_STATUS block (dry-run)

```bash
cd NuSyQ-Hub
python scripts/update_rosetta.py
# To commit/push and create a PR (requires gh):
python scripts/update_rosetta.py --commit --push --create-pr
```

### 14) Wiring Rosetta Stone into Agent Boot Prompts

Recommendation (examples to inject at agent boot):

- Claude / generic LLM: prepend first 200 lines of `docs/ROSETTA_STONE.md` to
  the prompt. If running local Claude, start it via the PowerShell wrapper above
  so TMP/TEMP are set.
- GitHub Copilot: include the first 200 lines as a file attachment/context when
  available (or copy as prompt context in the editor session).
- LM Studio: use the `state/` snapshots as machine-readable context; supply the
  first 200 lines of `ROSETTA_STONE.md` as the initial instruction in the
  session.

Example injection snippet (Claude): """ Attach the first 200 lines of
`docs/ROSETTA_STONE.md` as context. Role: <ROLE>. Then: <task description> """

Notes: keep injections short and include `ROLE` and `CONTEXT-ROOT` markers as
described above.

- Prefer `--dry-run`; avoid destructive git commands in dirty trees.
- Confirm task `cwd` in `.vscode/tasks.json` before running.

### 15) Pre-start Hooks & Cross-Repo Safety

- VS Code folder-open: run the Rosetta updater in dry-run.
- MCP pre-start: run updater in dry-run; only write after review.
- CI: optional dry-run updater + unified error report.
- Safety checklist: confirm repo root, scope discovery paths, capture reports
  before mutating.

### 16) Deep Pointers

- Orchestration: `src/orchestration/*`, `consensus_orchestrator.py`.
- AI tooling: `src/tools/`, `src/ai/`, `scripts/nusyq_actions/*`.
- Diagnostics: `src/diagnostics/unified_error_reporter.py`,
  `docs/Reports/diagnostics/`.
- Search/index: `src/search/`, `scan_src_issues.py`.
- Culture Ship: `docs/CULTURE_SHIP_AGENT_GUIDE.md`,
  `src/culture_ship_real_action.py`.
- Semgrep: `docs/SEMGREP.md`, `scripts/run_semgrep_minimal.py`.
- VS Code extension: `vscode-extension/src/ollama.ts`,
  `vscode-extension/src/extension.ts`.
- Tracing/telemetry: `src/observability/tracing.py`,
  `src/output/metrics_terminal_broadcaster.py`.
- Logs & paths map (fill as you learn):
  - Diagnostics: `docs/Reports/diagnostics/`, `state/reports/`
  - Search index: `src/search/keyword_index.json`,
    `src/search/file_metadata.json`
  - Tool logs (common): `logs/` (if present), per-script outputs alongside
    scripts
  - Quest/State: `src/Rosetta_Quest_System/`, `state/reports/`

### 17) Notes for Future Automation

- Nightly snapshot to append new commands/paths.
- Auto-diff Rosetta against quest logs, diagnostics, and tool inventories.
- LM Studio provider parity: add `src/ai/lmstudio_integration.py` mirroring
  `ollama_integration`; add VS Code toggle mirroring `ollama.ts`.

### 18) Automation Signals & Live Hooks

- Live hooks: run `scripts/start_nusyq.py` before and after major edits so
  `state/reports/current_state.md` and `docs/Reports/diagnostics` stay fresh.
- Update the LIVE_STATUS block with `python scripts/update_rosetta.py --dry-run`
  (review the diff before committing, repeat after state snapshot if values
  shift). When automating, call it from `terminal-keeper`/VS Code tasks so the
  block always matches the canonical report.
- Monitor metadata in `state/reports/spine_health_snapshot.json` and
  `state/registry.json` to keep orchestration tooling (Ollama, Claude, LM
  Studio) in sync with the live summary; log new insights under
  `docs/Reports/diagnostics/GROUND_TRUTH_HIGHLIGHTS.md`.

### 19) Culture, Quests & Continuity Anchors

- Record every cross-repo change in `src/Rosetta_Quest_System/quest_log.jsonl` and
  append human-friendly notes to `docs/Agent-Sessions/SESSION_*.md` for future
  agents. If you discover an automation gap, capture it in
  `docs/Checklists/PROJECT_STATUS_CHECKLIST.md` before moving on.
- Quest hygiene: use `scripts/todos_to_quests.py` for TODO/FIXME hunting, then
  re-check `docs/AGENTS.md` and `docs/CHECKLISTS` to ensure the next step is
  covered and recorded. Culture Ship updates (sample logs in `Reports/guild/`)
  belong in `docs/CULTURE_SHIP_AGENT_GUIDE.md` so they stay searchable.

### 20) Inventories, Guild, Culture Ship Quicklinks

- Tool inventory discovery:
  `python scripts/find_existing_tool.py --capability "<need>" --max-results 5`.
- Culture Ship docs/code: `docs/CULTURE_SHIP_AGENT_GUIDE.md`,
  `docs/CULTURE_SHIP_SMART_SEARCH_DESIGN.md`, `src/culture_ship_real_action.py`.
- Guild / consensus: `consensus_orchestrator.py`, `Reports/consensus/`.
- Quest/XP logs: `src/Rosetta_Quest_System/quest_log.jsonl`, `docs/SESSION_*`
  summaries.
- Smart Search artifacts: `src/search/keyword_index.json`,
  `src/search/file_metadata.json`.
- MCP configs: `.continue/mcpServers/*.yaml` (requires real `command`).
- Continue models/providers: `.continue/config.json`.

### 21) Tips, Tricks, and Anti-Pitfalls

- Always state repo context in agent prompts; reattach this file after context
  switches.
- Use `--dry-run` and targeted linters (per-file ruff/mypy) to avoid broad
  churn.
- Avoid heavy scans casually (full Semgrep, `rg` over node_modules) unless
  scoped.
- Prefer provided scripts on Windows to avoid PowerShell quoting traps.
- When adding providers, keep Ollama path intact; add LM Studio or others as
  parallel providers with proper toggles.
- Keep the top 200 lines dense; append learnings rather than rewriting sections.
- Treat VS Code/Ollama chatter as a signal: if the daemon is down, disable the
  status bar item and switch to LM Studio/cloud to avoid noisy retries.

### 22) Workspace Viewing & Panels (where to look)

- VS Code panels: Problems (filtered), Ports, SonarLint, Spell Checker, Output channels (per task/extension).
- Terminals: task-driven terminals in `.vscode/tasks.json` (snapshots, diagnostics, git audits, guild, docker); live routing via `scripts/activate_live_terminal_routing.py` + `data/terminal_routing.json`; prime_anchor quick tasks for Rosetta updates.
- Diagnostics: unified reporter outputs in `docs/Reports/diagnostics/`; health snapshots in `state/reports/` (spine/system health); scheduler/healing logs under `Reports/scheduler/`.
- Search/navigation: Smart Search (`python -m src.search.smart_search`), indices in `src/search/keyword_index.json` and `file_metadata.json`.
- Governance/healing: AI Council minutes in `Logs/ai_council/` (use `--stub` if models unavailable); Culture Ship/healing cycle in `src/orchestration/` with logs under `Reports/scheduler/`.
- Models/runtime: registry at `state/registry.json`; runtime checks via
  `scripts/test_lmstudio.py`, `ollama list`, `scripts/discover_and_sync_models.py`.
- Docker/dev servers: compose under `deploy/`; devcontainer in `.devcontainer/`; observability tasks in `.vscode/tasks.json`.
- Quest/roadmaps: `src/Rosetta_Quest_System/quest_log.jsonl`, `docs/Checklists/PROJECT_STATUS_CHECKLIST.md`, session logs in `docs/Agent-Sessions/`.

### 23) What Not to Run (heavy/unsafe by default)

- Avoid repo-wide `mypy`/`ruff` unless requested; prefer single-file runs
  (`mypy path/to/file.py --follow-imports=skip`).
- Avoid full Semgrep sweeps casually; use `scripts/run_semgrep_minimal.py` or
  scoped paths.
- Do not run destructive git commands (`git reset --hard`, `git checkout -- .`)
  in a dirty tree without explicit approval.
- Avoid running cross-repo scripts from the wrong root; always
  `git rev-parse --show-toplevel` first.
- Large searches: skip `rg` over `node_modules`, `.venv`, `dist` unless filtered
  (`rg --glob '!node_modules' pattern`).

### 24) Service Bring-Up Order (local dev)

- Prep: ensure Python env + Node deps per repo; confirm models available (LM
  Studio/Ollama as needed).
- Order (default): 1) Start model runtime (LM Studio HTTP or Ollama) if
  required; 2) Run `python scripts/start_nusyq.py` (snapshot/error report); 3)
  Launch NuSyQ-Hub tasks/CLIs; 4) Start SimulatedVerse dev server per its
  README; 5) Invoke NuSyQ/ChatDev workflows as needed.
- If a service fails, re-check config/manifest and ports below; avoid cascading
  restarts without logs.

### 25) Logs & Common Ports (fill as you learn)

- Diagnostics: `docs/Reports/diagnostics/`, `state/reports/` (snapshots/error
  reports).
- Search index: `src/search/keyword_index.json`,
  `src/search/file_metadata.json`.
- Quest/State: `src/Rosetta_Quest_System/`, `state/reports/`.
- Model runtimes: LM Studio default `http://10.0.0.172:1234`; Ollama default
  `http://localhost:11434`.
- SimulatedVerse dev server: `SIMULATEDVERSE_PORT` (default 5002) + React 3000.
- Add new log/port findings here; keep this table current for stateless agents.

### 26) MCP Troubleshooting & Provider Routing

- MCP entries require real executable commands in `.continue/mcpServers/*.yaml`;
  HTTP-only providers (LM Studio/Ollama) belong in `.continue/config.json`.
- Validate YAML schema `v1`, ensure arrays are well-formed
  (`command: ["node", "dist/index.js"]`), and prefer explicit `cwd` if binaries
  are relative.
- If Continue reports “Failed to parse config,” strip placeholder MCP entries,
  then re-add only valid servers; reload Continue after edits.
- Pre-start hook suggestion:
  `["python", "scripts/update_rosetta.py", "--dry-run"]` to refresh LIVE_STATUS
  without writes.

### 27) Rosetta Sync & Context Attach

- Canonical file: `docs/ROSETTA_STONE.md` (repo root). Workspace copy:
  `.vscode/prime_anchor/docs/ROSETTA_STONE.md`.
- Update canonical first, then sync:
  `cp docs/ROSETTA_STONE.md .vscode/prime_anchor/docs/ROSETTA_STONE.md`.
- For agent sessions: attach the first ~200 lines plus any relevant appendices
  (logs/ports, bring-up order, MCP notes).
- If drift is detected, overwrite the workspace copy from canonical and re-open
  tabs to refresh.
- Editing rule of thumb: casually edit the canonical file only. The prime_anchor
  copy is convenience/attachment, not authoritative; treat it as a synced
  backup. If unsure, trust canonical and re-copy into prime_anchor.

### 28) Quest Hygiene & Status Updates

- Sources of truth: `src/Rosetta_Quest_System/quest_log.jsonl`,
  `docs/Checklists/PROJECT_STATUS_CHECKLIST.md`,
  `docs/Agent-Sessions/SESSION_*.md`.
- When you complete or adjust a quest/task, append a status line (timestamp,
  action, repo scope) instead of overwriting.
- Close or dedupe stale quests; prefer small, testable increments and note
  follow-ups in the quest log.
- Record new learnings here (Rosetta) and in quest logs to preserve state for
  stateless agents.

### 29) Tools & Capabilities Index (curated)

- Discovery/reuse:
  `python scripts/find_existing_tool.py --capability "<need>" --max-results 5`.
- Search: `python -m src.search.smart_search keyword "<term>" --limit 50`;
  rebuild index with `python -m src.search.index_builder`.
- Diagnostics: `python scripts/start_nusyq.py error_report`;
  `python scripts/start_nusyq.py` (snapshot);
  `python scripts/scan_src_issues.py` (targeted issue scan, if present).
- Rosetta maintenance: `python scripts/update_rosetta.py --dry-run`; sync copies
  with `cp docs/ROSETTA_STONE.md .vscode/prime_anchor/docs/ROSETTA_STONE.md`.
- Models:
  `python scripts/discover_and_sync_models.py --dry-run`;
  `python scripts/test_lmstudio.py --base http://10.0.0.172:1234`.
- Security/linting: `python scripts/run_semgrep_minimal.py` (scoped Semgrep);
  prefer per-file lint/type runs (`ruff path/to/file.py`,
  `mypy path/to/file.py --follow-imports=skip`).
- Registry: `src/shared/model_registry.py` (JSON-backed registry used by
  registration/sync scripts; default location `state/registry.json`).

### 30) Orchestrations & Agent Systems

- Consensus/guild: `consensus_orchestrator.py`, `Reports/consensus/` for
  outcomes.
- Unified orchestration: `src/orchestration/unified_ai_orchestrator.py`
  (provider routing); `src/ai/ollama_hub.py` (local models).
- Culture Ship & advisory: `docs/CULTURE_SHIP_AGENT_GUIDE.md`,
  `src/culture_ship_real_action.py`, `docs/CULTURE_SHIP_SMART_SEARCH_DESIGN.md`.
- Quest system: `src/Rosetta_Quest_System/` (log + mechanics);
  `docs/Agent-Sessions/SESSION_*.md` for breadcrumbs.
- Extension surface: `vscode-extension/src/extension.ts`,
  `vscode-extension/src/ollama.ts` (VS Code wiring).
- Smart Search layer: `src/search/` (index + query) as the zero-token navigation
  backbone.
- Diagnostics & healing: `src/diagnostics/unified_error_reporter.py`; health
  snapshots via `scripts/start_nusyq.py`.
- Model registry consumers: registration/sync scripts write to
  `state/registry.json` for downstream use by tools/agents.

### 31) (Keep adding when you learn new things!)

### ANNEX: 50 Zeta Interview Questions (to probe mastery and improvement ideas)

1. How do you decide between using Ollama, LM Studio, or cloud LLMs for a task?
2. Describe the end-to-end flow of `scripts/start_nusyq.py error_report` and
   what files it writes.
3. How would you attach this Rosetta Stone to an agent session to avoid context
   loss?
4. Outline a zero-token workflow to investigate a new IDE error.
5. How do you rebuild the smart search index, and what do you check afterward?
6. What is the minimal sequence to validate model availability locally?
7. How would you extend the VS Code Ollama integration to support LM Studio?
8. Explain the Three-Before-New rule and show how to enforce it in practice.
9. What are the primary sources of truth for quests and tasks, and how do you
   update them safely?
10. How do you reconcile IDE error counts vs the unified reporter?
11. What’s the safest way to explore model files on Windows without breaking
    links?
12. How do you triage a failing `mypy` run that crashes with
    `_frozen_importlib`?
13. How would you script an auto-refresh of the LIVE_STATUS block without
    risking file churn?
14. Describe a minimal playbook for running Semgrep here.
15. How do you avoid token waste when searching for a module usage pattern?
16. What steps do you take before running any cross-repo mutation?
17. How do you disable the Ollama status bar noise when the daemon is down?
18. How would you add a new provider (e.g., LM Studio) while keeping the Ollama
    path intact?
19. How do you capture and persist session breadcrumbs for agents?
20. What are the “must read” files for a new agent before touching code?
21. How would you quickly locate Culture Ship-related code and docs?
22. What’s the best way to run targeted linting without full-repo churn?
23. How do you detect and avoid heavy directories when scanning?
24. How do you gracefully handle missing third-party stubs in mypy?
25. What is your process for verifying a service is up without full startup?
26. How do you identify when to use Continue vs in-editor commands?
27. How would you extend the LIVE_STATUS with quest summaries?
28. What safety checks precede running `scripts/discover_and_sync_models.py`?
29. How do you map logs to their producing scripts/services?
30. How do you ensure changes in this file stay within agent context window?
31. What is your rollback plan if a cross-repo script misbehaves?
32. How do you leverage quest logs to prioritize next actions?
33. What’s your approach to cleaning up a dirty worktree without losing user
    changes?
34. How do you validate that smart_search results are fresh and not stale?
35. What would you add to the command palette to reduce friction?
36. How do you keep code changes PR-sized while dealing with large error sets?
37. What is the default order for bringing up local services, and why?
38. How do you incorporate Semgrep findings into this Rosetta Stone?
39. How do you tune token usage for long-form analysis (e.g., use of local
    caches)?
40. How would you make the Three-Before-New protocol harder to violate?
41. What would you add to the Live Status to capture AI Council readiness?
42. How do you surface “known heavy” commands so agents avoid them casually?
43. What is your process to test the consensus orchestrator quickly?
44. How would you integrate Zeta interview prompts into onboarding?
45. How do you guide agents to pick the right shell (bash vs PowerShell) in this
    workspace?
46. What steps ensure test data isn’t accidentally modified by agents?
47. How do you detect when an agent is spamming errors vs making progress?
48. How do you incorporate session summaries into this file automatically?
49. What are your top three improvements to reduce context thrash for stateless
    agents?
50. How would you measure adoption of zero-token workflows across agents?

### APPENDICE: 50 Enhancement Ideas

1. Add “Top 5 daily commands” at top (auto-rotated).
2. Embed current quest summary from `quest_log.jsonl`.
3. Inline “recent diagnostics” (timestamp + counts).
4. One-click path to smart search index.
5. Cheatsheet for `start_nusyq.py` subcommands.
6. Provider decision tree (Ollama vs cloud vs LM Studio).
7. PowerShell escape hatch (common env setup).
8. “Attach this file” instructions per agent (Continue/Claude/Copilot).
9. Safe mutation checklist (tests/dry-run/backups).
10. Links to live dashboards in `state/reports/`.
11. Code snippet to inject this into MCP routing context.
12. “What not to run” (expensive/full scans to avoid casually).
13. Commit checklist for multi-repo edits.
14. Auto “last edited/last refreshed” line.
15. Step-by-step index rebuild with timing expectations.
16. `rg` cookbook for common searches.
17. Triage workflow for IDE vs reporter discrepancies.
18. Service bring-up order for local dev.
19. Minimal Docker sanity check command.
20. VS Code Ollama status toggle note (enable/disable).
21. Stubbed provider interface plan for LM Studio.
22. Smart_search return-shape FAQ.
23. “Lint locally, not globally” examples.
24. Jargon glossary (Zeta, Culture Ship, RSEV, OmniTag).
25. Context preflight checklist for agents (files to read).
26. Quest hygiene reminder (dedupe/close/append).
27. Highlight `scripts/find_existing_tool.py` in TOC.
28. “Read diagnostics markdown quickly” anchors.
29. Diff triage flow for dirty worktrees.
30. Playbooks index (Semgrep, Smart Search).
31. Token saver list (prefer local caches).
32. “Where logs go” map (scripts/services/tests).
33. Handling mypy internal errors (skip imports, single-file).
34. Missing stubs guidance (ignore vs stubs dir).
35. Shell choice tips (bash vs PowerShell).
36. Common false positives (ruff/mypy/IDE).
37. Smoke tests only (pytest markers).
38. Stop runaway processes (per-OS hints).
39. Agent state reset (clear caches, re-run snapshot).
40. Known heavy directories to avoid scanning.
41. Where to record new learnings (here + quest log).
42. Incident response mini-playbook.
43. AI Council/Consensus sanity checks.
44. Culture Ship quickstart micro-howto.
45. Smart search troubleshooting (missing index, bad path).
46. Zero-token navigation examples (rg+sed combos).
47. Test data locations and protections.
48. Common service ports table.
49. Cost-awareness note (avoid cloud unless needed).
50. Time budget tip (favor small PR-sized patches; avoid sweeping rewrites).

# NuSyQ-Hub

Multi-repository AI orchestration hub. Coordinates agents (Ollama, Claude, Copilot, ChatDev), background tasks, and cross-repo synchronization with SimulatedVerse.

## Quick Commands

```bash
# System health check
python scripts/start_nusyq.py brief

# Full system gate (7 checks — add --budget-s=300 to cap time)
python scripts/start_nusyq.py system_complete --sync --budget-s=300

# Run tests
python -m pytest tests/ -q

# Run tests for a specific file
python -m pytest tests/test_background_task_orchestrator.py -q

# Lint check
python -m ruff check scripts/ src/

# Auto-fix lint
python -m ruff check scripts/ src/ --fix

# Start NuSyQ interactive menu
python scripts/start_nusyq.py menu

# Activate git hooks (run once after clone)
make setup
# If make is not installed (Windows without GNU Make):
git config core.hooksPath .githooks

# MJOLNIR Protocol — unified agent dispatch
python scripts/nusyq_dispatch.py status --probes           # Probe all 10 agents
python scripts/nusyq_dispatch.py ask ollama "Analyze X"    # Single-agent ask
python scripts/nusyq_dispatch.py ask codex "Review Y"      # Delegate to Codex CLI
python scripts/nusyq_dispatch.py council "Best approach?" --agents=ollama,lmstudio  # Multi-agent consensus
python scripts/nusyq_dispatch.py chain "Analyze then fix" --agents=ollama,codex --steps=analyze,generate
python scripts/nusyq_dispatch.py queue "Generate tests" --priority=HIGH  # Persistent async task
python scripts/nusyq_dispatch.py skyclaw status         # SkyClaw gateway status (binary + HTTP)
python scripts/nusyq_dispatch.py skyclaw start          # Start SkyClaw sidecar daemon
python scripts/nusyq_dispatch.py skyclaw stop           # Stop session-managed SkyClaw daemon

# Or via start_nusyq.py:
python scripts/start_nusyq.py dispatch status
python scripts/start_nusyq.py dispatch ask ollama "prompt"
```

## Architecture

```
NuSyQ-Hub/
├── src/
│   ├── orchestration/          # Core task scheduling (BackgroundTaskOrchestrator, Phase 3)
│   ├── integration/            # MCP server, ChatDev, SimulatedVerse bridges (≠ integrations/)
│   ├── agents/                 # Agent communication hub, orchestration hub
│   │   └── bridges/            # 10 bridge impls (ChatDev, Claude, Ollama, Consciousness, Quantum, etc.)
│   ├── culture_ship/           # Strategic advisor (Culture Ship)
│   ├── api/                    # FastAPI routes and models
│   ├── utils/                  # Path resolver, timeout manager, output utilities
│   ├── diagnostics/            # Health checks, error reporters
│   ├── core/                   # Unified facade (orchestrate.py), bootstrap, result types — MYPY gated
│   ├── tools/                  # Dev utilities: agent_task_router, health_restorer, quest_log_validator (55 files)
│   ├── consciousness/          # Temple of Knowledge (10 floors) + House of Leaves debugging labyrinth
│   ├── copilot/                # Copilot enhancement, workspace integration, VS Code extension
│   ├── integrations/           # Nogic Visualizer bridge + OpenClaw gateway (≠ integration/)
│   ├── healing/                # Auto-repair: quantum_problem_resolver, error_resolution_orchestrator
│   ├── factories/              # Code generation scaffolding (multi-language, 20 files)
│   ├── guild/                  # Agent guild board coordination substrate
│   ├── quantum/                # Quantum computing simulation + consciousness substrate
│   ├── observability/          # Metrics, distributed tracing, OpenTelemetry, autonomy dashboard
│   ├── tagging/                # OmniTag + MegaTag metadata systems
│   ├── Rosetta_Quest_System/   # Quest/questline engine (UUID-based, JSONL audit trail)
│   └── [60+ more subsystems]   # games, ai, analysis, automation, spine, memory, etc.
├── scripts/
│   ├── start_nusyq.py          # Primary entry point (brief, system_complete, menu)
│   ├── nusyq_actions/          # 20 CLI action modules (brief.py, menu.py, doctor.py, guild.py, etc.)
│   ├── e2e_chatdev_mcp_test.py # ChatDev end-to-end test (skips if server not running)
│   ├── activate_culture_ship.py
│   └── [~462 automation/analysis/healing/maintenance scripts]
├── tests/
│   ├── integration/            # Phase 3 integration tests
│   └── test_*.py               # Unit tests
├── config/                     # 94 JSON/YAML files (model capabilities, feature flags, templates)
├── state/                      # Runtime: nusyq_state.db (2.4MB SQLite), events.jsonl (431KB)
└── deploy/
    ├── k8s/                    # 15 Kubernetes manifests (HPA, ingress, RBAC, secrets)
    ├── helm/nusyq-hub/         # Helm chart (Chart.yaml + values.yaml)
    └── ollama_mock/            # Mock Ollama API for CI (no GPU needed)
```

## Key Files

- `src/orchestration/background_task_orchestrator.py` — Main task runner; Phase 3 + Culture Ship + ConsciousnessLoop initialized on `start()`; `_get_adaptive_timeout(base)` scales timeouts by breathing factor
- `src/orchestration/consciousness_loop.py` — Thin adapter wrapping SimulatedVerseUnifiedBridge; provides `breathing_factor` (30s cache), Culture Ship veto, fire-and-forget event logging; initialized lazily in `start()`
- `src/orchestration/enhanced_task_scheduler.py` — Value-based task prioritization; reads `task.metadata["category"]` and `task.priority`
- `src/integration/phase3_integration.py` — Phase 3 (scheduler, dashboard, validator, multi-repo coordinator)
- `src/orchestration/culture_ship_strategic_advisor.py` — Strategic analysis and decision cycles
- `src/utils/repo_path_resolver.py` — Cross-repo path resolution (env var → manifest → defaults)
- `scripts/start_nusyq.py` — All CLI actions: `brief`, `system_complete`, `menu`, `work`, `trace`
- `docs/AGENT_TUTORIAL.md` — Onboarding guide for all AI agents (Claude, Copilot, Ollama, ChatDev, LM Studio) across the tripartite ecosystem
- `.vscode/prime_anchor/docs/ROSETTA_STONE.md` — Fast-loadable agent context ("operational contract"); attach first ~200 lines to agent sessions for stateless context
- `src/core/orchestrate.py` — Unified NuSyQ facade (one of 3 mypy-gated files): `nusyq.analyze("path")`, `nusyq.search("term")`, `nusyq.quest.add("task")`, `nusyq.council.propose("question")`, `nusyq.background.dispatch("task")`
- `src/agents/agent_orchestration_hub.py` — Multi-AI routing hub; modes: CONSENSUS, VOTING, SEQUENTIAL, PARALLEL, FIRST_SUCCESS; task priorities: CRITICAL(1)–BACKGROUND(5)
- `src/Rosetta_Quest_System/quest_engine.py` — Quest engine; data model fields: id(UUID), title, questline, status, dependencies, tags, history; statuses: pending→active→complete/blocked/archived
- `src/guild/guild_board.py` — Agent guild coordination; agent states: IDLE/WORKING/BLOCKED/OBSERVING/OFFLINE; substrates: `data/guild_board.json`, `guild_events.jsonl`, `agent_registry.json`, `quest_assignments.json`
- `src/integrations/openclaw_gateway_bridge.py` — 12+ messaging platforms (Slack, Discord, Telegram, Teams, etc.) via WebSocket `ws://127.0.0.1:18789`; target prefix syntax: `"copilot:"`, `"/ollama"`, `"@chatdev"`
- `src/integrations/nogic_bridge.py` — Nogic Visualizer bridge: architecture visualization + SQLite data store; integrates with VS Code Nogic extension
- `config/feature_flags.json` — 30+ feature toggles: `chatdev_autofix`, `sns_enabled`, `chatdev_mcp_enabled`, `trust_artifacts_enabled`, etc.
- `config/model_capabilities.json` — 16 model entries (OpenAI, Ollama×10, ChatDev, LM Studio) with tags (code/general/embeddings), cost(low/medium), latency
- `src/dispatch/mjolnir.py` — MJOLNIR Protocol engine: `MjolnirProtocol` with `ask()`, `council()`, `parallel()`, `chain()`, `delegate()`, `queue()`, `status()`; wraps AgentTaskRouter + GuildBoard + SNS-Core
- `scripts/nusyq_dispatch.py` — MJOLNIR CLI: 7 subcommands (ask, council, parallel, chain, delegate, queue, status); structured JSON output
- `src/dispatch/agent_registry.py` — Agent availability probing: 17 agents (ollama, lmstudio, chatdev, codex, claude_cli, copilot, consciousness, quantum_resolver, factory, openclaw, intermediary, skyclaw, dbclient, devtool, gitkraken, huggingface, neural_ml)
- `src/dispatch/context_detector.py` — Context mode detection: ECOSYSTEM (NuSyQ-Hub), GAME (SimulatedVerse), PROJECT (elsewhere)
- `src/dispatch/response_envelope.py` — Structured JSON response envelope for all MJOLNIR output

## Environment

Required env vars (optional — defaults to home-based layout if absent):
```
NUSYQ_ROOT               # Path to NuSyQ root repo
NUSYQ_HUB_ROOT           # Path to this repo (NuSyQ-Hub)
SIMULATEDVERSE_ROOT      # Path to SimulatedVerse repo
```

System-complete gate behavior:
```
CHATDEV_E2E_REQUIRE_SERVER=1  # Make chatdev_e2e fail if MCP server is down (default: skip)
CHATDEV_E2E_RUN_TIMEOUT_SECONDS=900  # Max poll time for a ChatDev run
NUSYQ_SYSTEM_COMPLETE_BUDGET_S=300   # Wall-clock budget for all gate checks
```

## Testing

```bash
# All tests
python -m pytest tests/ -q

# Integration tests only
python -m pytest tests/integration/ -q

# Single test
python -m pytest tests/integration/test_phase3_integration.py::test_enhanced_task_selection_integration -v

# With coverage report
python -m pytest tests/ --cov=src --cov-report=term-missing

# Per-file coverage (avoids full-suite denominator inflation)
python -m coverage run -m pytest tests/test_foo.py -q --no-cov && python -m coverage report --include="src/path/to/file.py"
```

Test markers: `unit`, `integration`, `smoke`, `slow`, `performance`

## Gotchas

- **Windows WSL path trap**: `repo_path_resolver.py` guards `_windows_path_to_wsl` with `sys.platform == "win32"`. Do not remove this guard — without it, temp paths in tests get converted to broken `/mnt/c/...` paths.
- **Windows platform (MINGW64)**: Claude Code runs in Git Bash (MINGW64), NOT PowerShell/cmd/WSL. `make` is NOT installed — use `git config core.hooksPath .githooks` directly. `localhost` can resolve to IPv6 `[::1]` on Windows — all local service URLs use `127.0.0.1` explicitly.
- **Linux-only scripts**: `scripts/crisis_response.sh` requires Linux (pkill, pgrep, nohup). Has a platform guard that exits with instructions for WSL/Docker. `scripts/bootstrap_dev_env.sh` handles both Windows (`.venv/Scripts/activate`) and Unix (`.venv/bin/activate`) venv paths.
- **`submit_task` is synchronous**: `BackgroundTaskOrchestrator.submit_task()` returns a `BackgroundTask` directly — do NOT `await` it.
- **`select_next_batch` is synchronous**: `EnhancedTaskScheduler.select_next_batch()` returns a list — do NOT `await` it.
- **chatdev_e2e skips when server is down**: `scripts/e2e_chatdev_mcp_test.py` exits 0 (skip) if `localhost:8081` is not reachable. Set `CHATDEV_E2E_REQUIRE_SERVER=1` to make it a hard failure.
- **system_complete budget**: The `chatdev_e2e` gate check has a 1800s timeout but skips instantly when no server is up. Other checks (`openclaw_smoke`, `culture_ship_cycle`, etc.) only run if budget remains.
- **Large git commits**: `SimulatedVerse/reports/labels.index.json` is 18MB — stage it alone in its own commit to avoid OOM.
- **Task categorization**: `EnhancedTaskScheduler.categorize_task()` checks `task.metadata["category"]` FIRST before keyword scanning. Metadata categories: `SECURITY`, `LINT`, `BUGFIX`, `FEATURE`, `REFACTOR`, `TEST`, `DOCS`, `PERFORMANCE`, `DEPENDENCY`. **Keyword order trap in tests**: "improve" matches REFACTOR (`["refactor", "improve", "optimize"]`) before TEST or PERFORMANCE — use unambiguous terms like `"add coverage report"` (TEST) or `"performance benchmark"` (PERFORMANCE).
- **git add negation on Windows**: `git add -A -- ':!file'` fails on Windows bash. Use `git add -A && git reset -- file` instead.
- **`_handle_brief()` in start_nusyq.py is dead code**: Real brief handler is `scripts/nusyq_actions/brief.py`. Edits to `_handle_brief` in `start_nusyq.py` have no effect at runtime.
- **ShipApproval field names**: `SimulatedVerseUnifiedBridge.ShipApproval` uses `.reasoning`. `ConsciousnessLoop.ShipApproval` uses `.reason`. Never mix them.
- **Culture Ship veto gate**: Tasks with `metadata["requires_approval"] = True` or `SECURITY` category are vetoed by `ConsciousnessLoop.request_approval()` before dispatch. Auto-approves when bridge is unavailable (graceful degradation).
- **mypy gate scope**: `system_complete` runs mypy on only 3 files with `--strict --follow-imports=skip`: `src/tools/agent_task_router.py`, `src/core/orchestrate.py`, `src/integration/mcp_server.py`.
- **Pre-existing test failures**: All previously-known failures resolved — `test_agent_task_router.py` (`9c860eb07`), `test_doctor_action` + `test_event_history_tracker` (`e67355c44`), `test_brief_action.py` tests (`101b3be4d` — fixed brief.py `return 0`), `test_start_nusyq.py` (`101b3be4d` — all 68 tests pass).
- **yaml.safe_load strips dataclasses**: Loading manifest.yaml into `ProjectManifest(**data)` leaves `versions` as `List[dict]`. Explicitly convert: `[ProjectVersion(**v) if isinstance(v, dict) else v for v in data.get("versions") or []]`. Same pattern for any YAML-backed registry with nested dataclasses.
- **MagicMock.context.get() is truthy**: `task = MagicMock()` → `task.context.get("ollama_model")` returns a truthy MagicMock, not `None`. Always pin `task.context = {}` when testing code that calls `task.context.get()`. Also: `_select_model_from_capabilities` reads live config — pin model in context for deterministic assertions.
- **`_chatdev_factory_fallback` creates real files**: When `ProjectFactory` is importable and ChatDev launcher fails, routing falls through to factory and returns `success`. To test "all paths unavailable", patch `src.tools.agent_task_router.ProjectFactory = None` in addition to the launcher.
- **Full src/ mypy backlog**: Gate runs `--strict --follow-imports=skip` on only 3 files. `python -m mypy src/ --strict --follow-imports=skip` reveals ~20 additional errors in non-gate files — pre-existing backlog, not regressions.
- **SimulatedVerse is live at runtime**: `brief` connects to SimulatedVerse and shows real consciousness state (Level, Stage, Breathing factor). If state is missing, check `SimulatedVerse/ship-console/mind-state.json`.
- **Docker has 4 active compose files**: `docker-compose.yml` (root production), `deploy/docker-compose.dev.yml`, `deploy/docker-compose.full-stack.yml`, `deploy/docker-compose.agents.yml`. `docker-validate.yml` CI validates all four with `--env-file`.
- **Docker credentials — no weak fallbacks**: All sensitive vars (`POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `GRAFANA_PASSWORD`) use `${VAR}` with no default in production compose so startup fails fast without `.env`. Dev compose uses `:-nusyq_dev` fallback. Do NOT add back `:-some_password` defaults.
- **Redis requires auth**: All `redis-cli` health checks must use `-a $$REDIS_PASSWORD`; plain `redis-cli ping` returns `NOAUTH Authentication required` (exit 1) when `requirepass` is set.
- **SimulatedVerse Dockerfile**: Now exists at `../../SimulatedVerse/SimulatedVerse/Dockerfile` (Node.js 20 Alpine, 2-stage). Full-stack compose build context points there via `${SIMULATEDVERSE_PATH:-../../../SimulatedVerse/SimulatedVerse}`.
- **Breathing factor formula**: In `src/integration/simulatedverse_unified_bridge.py` ~line 803. Stage→multiplier: dormant=1.20, awakening=1.10, expanding=1.00, transcendent=0.85, quantum=0.60. Level-based floor/ceiling applied on top. Cached 30s in `ConsciousnessLoop`.
- **Temple of Knowledge floor thresholds**: Consciousness point unlock gates: floors 1=0, 2–3=5, 4–5=10, 6–7=20, 8–9=30, 10=50. Quest formula: `(5 + deps×2) × tag_multiplier` where critical=3.0×, important=2.0×, minor=0.5×.
- **`src/integration/` ≠ `src/integrations/`**: Two distinct packages. `integration/` (singular) = cross-system bridges (SimulatedVerse, ChatDev-MCP, Phase3, Ollama, quantum). `integrations/` (plural, 10 files) = Nogic Visualizer + OpenClaw gateway only. Mixing imports causes ModuleNotFoundError.
- **scripts/ has 495 Python files**: Only `start_nusyq.py` + `nusyq_actions/` (20 modules) are intended entry points. The other ~472 scripts are one-off automation/analysis utilities. Do not assume an arbitrary script in `scripts/` is safe to run without checking.
- **K8s + Helm exist alongside Docker**: `deploy/k8s/` contains 15 production manifests (HPA, ingress, RBAC, secrets, kustomization). `deploy/helm/nusyq-hub/` has a Helm chart. These are maintained separately from the 4 Docker Compose files.
- **K8s secrets are never committed filled-in**: `deploy/k8s/secrets.yaml` is a template (all values empty strings). Create real secrets externally: `kubectl create secret generic postgres-secret --from-literal=password=$(openssl rand -base64 32)` and `kubectl create secret generic redis-secret --from-literal=password=$(openssl rand -base64 32)`. Same for `nusyq-hub-secrets`.
- **K8s Redis requires auth**: `deploy/k8s/redis.yaml` passes `--requirepass $(REDIS_PASSWORD)` and pulls from `redis-secret`. Health probes use `redis-cli -a $(REDIS_PASSWORD) ping`. Matches `docker-compose.yml` pattern exactly.
- **autonomy-merge.yml risk metadata is bot-sourced only**: `riskScore`/`riskLevel` are read exclusively from comments posted by `github-actions[bot]`, never from `pr.body` (user-controlled). `isAutoBot` checks only `pr.user.login`, never branch name. Spoofing the PR body has no effect on merge eligibility.
- **Jupyter runs without auth in agents compose**: `docker-compose.agents.yml` starts Jupyter with `--NotebookApp.token='' --NotebookApp.password=''` bound to `0.0.0.0:8888`. Never expose this publicly.
- **state/ runtime files not git-tracked**: `state/nusyq_state.db` (SQLite 2.4MB), `state/events.jsonl` (431KB fire-and-forget log), `state/culture_ship_healing_history.json` (560KB decision log) accumulate at runtime. Delete or archive manually to reclaim disk space.
- **MJOLNIR agent aliases**: `lms`→lmstudio, `claude`→claude_cli, `sv`→consciousness, `qr`/`quantum`→quantum_resolver. These are resolved in `src/dispatch/mjolnir.py:AGENT_ALIASES`.
- **MJOLNIR context auto-detection**: `ContextDetector.detect()` returns ECOSYSTEM when CWD is under NuSyQ-Hub, GAME when under SimulatedVerse, PROJECT otherwise. Override with `--context=game`.
- **MJOLNIR SNS flag is per-request**: `--sns` compresses prompts via SNS-Core (41-85% token reduction). Global `sns_enabled=false` in feature_flags.json does NOT need to be true — MJOLNIR bypasses it.
- **MJOLNIR `queue()` vs `delegate()`**: `queue()` routes to `BackgroundTaskOrchestrator` (persistent, survives restarts). `delegate()` posts to GuildBoard only (ephemeral quest tracking).
- **Ollama WinError 10053/10054 = WSL relay, not Ollama**: If `netstat` shows port 11434 owned by `wslrelay.exe` (verify: `powershell "Get-Process -Id <pid>"`), Ollama is inside WSL but WSL networking is broken. HTTP connections abort at TCP level. Fix: `wsl --shutdown` in admin PowerShell, then `wsl -e ollama serve`.
- **WSL socket exhaustion (WslError 0x80072747)**: "Insufficient buffer space or queue full" = system RAM critically low. Check: `powershell "Get-WmiObject Win32_OperatingSystem | Select FreePhysicalMemory"`. Symptom: all WSL-forwarded ports fail silently. Fix: `wsl --shutdown`.
- **SimulatedVerse HTTP port**: Server binds `PORT=5000` (in `SimulatedVerse/.env`). Bridge reads `SIMULATEDVERSE_PORT` env var (`.env.workspace` sets 5000). Brief "HTTP API unavailable (using file mode)" = Node server not running; file mode is valid fallback. Start: `cd SimulatedVerse && npm run dev`.
- **VS Code 700-error signal is stale Pyright data**: `brief` reads cached counts from `docs/Reports/diagnostics/vscode_problem_counts_tooling.json` — not live linting. Ground truth is `state/error_ground_truth.json` (ruff + mypy). Refresh: `python scripts/start_nusyq.py vscode_diagnostics_bridge`.
- **OpenClaw gateway port**: Single port `:18789` serves both WebSocket (`ws://127.0.0.1:18789`) and HTTP dashboard (`http://127.0.0.1:18789/`). MJOLNIR probe checks `http://127.0.0.1:18789/` (HTTP 200=online). Start gateway: `openclaw gateway --port 18789`. Start NuSyQ bridge: `python scripts/start_nusyq.py openclaw_bridge_start`.
- **Coverage % is test-combination-dependent**: Without `source = src` in `.coveragerc`, denominator = only files imported by that run (12K stmts for 3 files, 30K for 5). Do NOT add `source = src` — inflates denominator to 86K giving ~5%. Threshold: 33% (core 189-test suite achieves ~36%). Full-suite run: `pytest tests/ --override-ini="addopts=--cov --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=0 -q"`.
- **dotenv inline comments corrupt values**: `KEY=value  # comment` sets value to `value  # comment` in python-dotenv. Always put comments on their own preceding line.
- **f-string literal braces in scripts/**: ASCII-art inside f-strings must escape `{field}` as `{{field}}` — ruff F821 fires on every unescaped identifier. Confirmed in `scripts/visualize_eol_cycle.py`.
- **NuSyQ repo mypy double-path**: `NuSyQ/pytest.ini` has `source = mcp_server,config,src` making files appear as both `NuSyQ.src.*` and `src.*` to mypy → "Source file found twice" errors. Pre-existing in NuSyQ root repo, not NuSyQ-Hub.
- **GuildBoard claim auto-release in tests**: `auto_release_claim_on_heartbeat_timeout=True` by default — `_release_stale_claims_locked()` runs on every lock entry and silently drops any claim for an agent with no recent heartbeat. In tests that call `claim_quest()` then act on it, set `board.auto_release_claim_on_heartbeat_timeout = False` OR call `await board.agent_heartbeat(agent_id, AgentStatus.IDLE)` first.
- **GuildBoard async test isolation**: All core `GuildBoard` ops are `async` — use `@pytest.mark.asyncio`. Isolate file I/O with `GuildBoard(state_dir=tmp_path / "guild", data_dir=tmp_path / "data")`; the default `state_dir=Path("state/guild")` writes to real runtime files and loads 70+ live quests on init.
- **`qid`/`qids` = Quest ID abbreviation**: In guild scripts (`analyze_guild_quests.py`, `batch_close_quests.py`), `qid` is a loop variable for quest UUID strings. `QuestId = str` and `AgentId = str` type aliases are exported from `src/guild/__init__.py`. Not an npm package or React component — purely Python variable naming convention.
- **RUF006 requires module-level storage**: `_t = loop.create_task(...)` still fires RUF006 — local var goes out of scope and GC can cancel the task. Pattern: `_tasks: set[asyncio.Future[Any]] = set()` at module level + `fut.add_done_callback(_tasks.discard)`. See `_listener_tasks` in `guild_board.py` and `_pending_emit_tasks` in `terminal_aware_actions.py`.
- **Ruff `--unsafe-fixes` required for**: RUF059 (unused unpacked vars → `_`-prefix), RUF013 (implicit Optional → `T | None`), C401/C411/C414 (collection simplifications). `--fix` alone silently skips all of them. Full sprint command: `ruff check scripts/ src/ --fix --unsafe-fixes --select RUF059,RUF013,C401,C411,C414`.
- **Guild→OpenClaw notifier auto-attaches**: `get_board()` in `guild_board.py` attaches `GuildOpenClawNotifier` on first call (lazy import, idempotent via `_openclaw_attached` flag). No manual `attach_to_board()` call needed. Smoke-test: `python -c "import asyncio; from src.guild.guild_board import get_board; b=asyncio.run(get_board()); print(len(b._event_listeners), 'listeners')"` → should print `1 listeners`.
- **`setup_method` duplication in pytest classes**: Python silently uses the last definition. `pythonpath = .` in `pytest.ini` already adds project root to sys.path for all tests — no `setup_method` path manipulation needed.
- **EOL SECURITY gate (v0.2)**: `EOLOrchestrator._request_culture_ship_approval()` in `src/core/eol_integration.py` lazy-inits `ConsciousnessLoop` and calls `request_approval(action_str, context_dict)` → `ShipApproval(approved, reason)`. Auto-approves when bridge unavailable. `_consciousness_loop` attribute is `None` at init — only materialized on first SECURITY-category critique.
- **`quantum_problem_resolver.detect_problems()` scans CWD by default**: `QuantumProblemResolver(root_path=None)` defaults to `Path.cwd()`. `detect_problems()` does `ws.rglob("*.py")` — this used to hang in tests because it scanned `.venv/` (thousands of site-package files, some >1MB). Fixed: `detect_problems()` now skips `.venv`, `venv`, `__pycache__`, `.git`, `.mypy_cache`, `node_modules`, `site-packages`, etc.
- **`culture_ship_strategic_advisor` lives in `src/orchestration/`**: Module path is `src.orchestration.culture_ship_strategic_advisor`, NOT `src.culture_ship.culture_ship_strategic_advisor`. The `src/culture_ship/` directory only has `health_probe.py`, `integrated_terminal.py`, and `plugins/`.
- **Ruff D105/D107 now globally ignored**: Added to the project-wide `ignore` list (same rationale as D100-D103: legacy files being refactored). Also added comprehensive per-file-ignores for `scripts/**/*.py` covering D212, D301, D417, N801, N817, RUF001/002/003, A002, C416, RUF012, RUF015, RUF034. Lint gate is 0 violations.
- **Coverage denominator trap with `test_quantum.py`**: Running `pytest tests/test_quantum.py` alone pulls total coverage below 33% because `healing/quantum_problem_resolver.py` (796 stmts, 19% covered) inflates the denominator. Run with the full suite or use `--override-ini="addopts=--cov --cov-fail-under=0"` for isolated runs.
- **Pre-push hook `KeyError: 'is_bound'` = stale mypy cache**: `git push` fails with `KeyError: 'is_bound'` deep in `mypy/types.py deserialize` when the `.mypy_cache/` was built by an older mypy version. Fix: `rm -rf .mypy_cache`. The cache is already in `.gitignore` (line 163) so it won't be committed.
- **SNS token metrics now wired to `TokenMetricsDashboard`**: `src/dispatch/mjolnir.py` `ask()` now calls `TokenMetricsDashboard().record_conversion()` after applying SNS-Core compression. Metrics accumulate in `state/token_metrics.jsonl`. The other two SNS call sites (`delegate()`, `queue()`) still discard metadata — extend if per-operation granularity is needed.
- **Culture Ship TODO/HACK count includes scanner code**: The 152-item "TODO/HACK" report counts pattern-matching strings inside scanners, template generators, and diagnostic scripts. Only ~17 raw occurrences exist in `src/` + `scripts/`, and most are scanner regex patterns or template placeholders — not actionable debt. Run `grep -rn "# TODO\|# FIXME\|# HACK" src/ scripts/ --include="*.py"` for the real list.
- **Pre-push mypy uses `--follow-imports=skip`**: The pre-push hook runs `mypy src/guild/ src/config/ --follow-imports=skip`. Without this flag, mypy follows transitive imports into 100+ pre-existing backlog errors across the full codebase. Adding `--follow-imports=skip` scopes the check to the directly-specified directories only (matches `system_complete` gate behaviour). If the push fails with unexpected mypy errors, verify the flag is present in `.githooks/pre-push-impl.py`.
- **`OllamaModelManager` was a ghost export**: `src/ai/__init__.py` had `"OllamaModelManager"` in `__all__` and a `__getattr__` branch that tried to import it from `src.ai.ollama_model_manager`, but that module only has module-level functions — no class was ever created. The ghost export was removed. If you need Ollama model utilities, import functions from `src.ai.ollama_model_manager` directly.
- **Pre-commit hook checks ALL of `src/` — including untracked files**: `black --check src/` and `ruff check src/ --select=E,F,W` run on every Python file in `src/`, not just staged changes. New untracked files (e.g., from a parallel agent session) will block your commit even if you haven't staged them. Fix: format and lint-clean the new files before committing, or stage and fix them as part of your commit.
- **17 agents in registry (neural_ml added)**: `src/dispatch/agent_registry.py` now has 17 agents: the original 12 (ollama, lmstudio, chatdev, codex, claude_cli, copilot, consciousness, quantum_resolver, factory, openclaw, intermediary, skyclaw) plus 4 MCP-extension bridges (dbclient, devtool, gitkraken, huggingface) plus neural_ml (ConsciousnessEnhancedMLSystem + NeuralQuantumBridge, fully offline). `test_registry_has_all_agents` expected set and `test_status_no_probes` count are both updated to 17. **Dispatch test count invariant** still applies: when adding to AGENT_PROBES, update the test expected set and the `len(result.output) == N` assertion.
- **New MCP extension bridges in `src/integrations/`**: 5 new bridge files wrap VS Code MCP extension tools as NuSyQ agents — `dbclient_bridge.py` (SQL/SQLite), `devtool_bridge.py` (Chrome DevTools), `huggingface_bridge.py` (HuggingFace Hub), `gitkraken_bridge.py` (GitKraken), `mcp_extension_catalog.py` (extension catalog). Use via MJOLNIR: `nusyq_dispatch.py ask devtool "Navigate to URL"` etc.
- **20 agents in registry (metaclaw added)**: 12 original + 4 MCP bridges + neural_ml + hermes + optimizer + metaclaw = 20. `metaclaw` is a Node.js observability + trace agent at `state/runtime/external/metaclaw-agent/`; probe: `_probe_metaclaw()` — online when `node` + `node_modules` present. **Dispatch test count invariant**: `test_status_no_probes` asserts `len == 20`; `test_registry_has_all_agents` expected set includes all 20. Update both when adding agents.
- **MJOLNIR `poll` and `recall` subcommands**: `nusyq_dispatch.py poll <id> [--type=queue|delegate]` polls background task or guild quest. `nusyq_dispatch.py recall <tag> [--limit=10]` queries MemoryPalace + `state/memory_chronicle.jsonl`. `_output()` in `nusyq_dispatch.py` now handles both `ResponseEnvelope` objects and plain `dict` (returns exit 1 if dict has `"error"` key or `"status": "error"`).
- **MemoryPalace is in-process-only; use chronicle for cross-process recall**: `src/memory/MemoryPalace` stores nodes in RAM — nodes are lost when the process exits. For durable recall, write to `state/memory_chronicle.jsonl` (append-only JSONL with `tags` list). `MjolnirProtocol.recall(tag)` merges in-session MemoryPalace nodes + chronicle file. Culture Ship cycle appends to chronicle after each run.
- **Culture Ship cycle writes to `state/memory_chronicle.jsonl`**: After each `culture_ship_cycle --sync`, a summary entry (`node_id`, `tags`, `timestamp`, `issues`, `decisions`, `fixes`, `receipt_path`) is appended. Recall via `nusyq_dispatch.py recall culture_ship`. Chronicle path resolution in `MjolnirProtocol.recall()` uses `Path(__file__).parents[2] / "state" / "memory_chronicle.jsonl"`.
- **N-agent duet (`agent_duet.py`)**: `--agents codex,copilot,ollama --rounds 3` runs N-agent round-robin (`turn % n`). `--delegation` intercepts `[DELEGATE:agent:task]` markers in agent output and dispatches them live via MJOLNIR. `_AGENT_PROFILES` dict provides per-agent identity descriptions injected into system headers. `_DELEGATE_RE` regex: `r"\[DELEGATE\s*:\s*(?P<agent>[a-z_]+)\s*:\s*(?P<task>[^\]]+)\]"`.
- **Council stores decisions in MemoryPalace with agent+consensus tags**: `MjolnirProtocol.council()` calls `mem.add_memory_node(f"council:{timestamp}", {...}, tags=["council","ask",consensus_level,...agent_names])`. Retrieve past council decisions: `protocol.recall("council")` or `recall codex` to find decisions involving codex. Storage is best-effort (try/except).

## Ecosystem Services

| Service | URL | Notes |
|---------|-----|-------|
| MCP Server | `localhost:8081` | ChatDev integration, start via `src.integration.mcp_server` |
| Ollama | `localhost:11434` | 12 models (llama3.1:8b, qwen2.5-coder:14b, deepseek-coder-v2:16b, etc.) — see `config/ollama_models.json`. Runs inside WSL (Ubuntu-22.04); `wslrelay.exe` forwards port. Start: `wsl -e ollama serve`. Port OPEN but requests abort (WinError 10053) → WSL relay stale, run `wsl --shutdown`. |
| Antigravity | `localhost:8080` | Health at `/health` |
| OpenClaw Gateway | `ws://127.0.0.1:18789` | 12+ messaging platform bridge (Slack, Discord, Telegram, Teams, etc.) |
| Jupyter Lab | `localhost:8888` | Via agents compose only; no auth — dev use only |
| Jaeger UI | `localhost:16686` | Distributed tracing (via agents compose) |
| Grafana | `localhost:3000` | Metrics dashboard (via full-stack compose) |

## Token Efficiency — Delegation Guide

Claude burns tokens on tasks that local agents handle for free. Before doing work inline, check if one of these handles it:

| Task type | Delegate to | Command |
|-----------|-------------|---------|
| Code review | Ollama/Codex | `nusyq_dispatch.py ask ollama "Review src/file.py"` |
| Test generation | Ollama | `nusyq_dispatch.py ask ollama "Generate tests for X"` |
| Multi-perspective analysis | Council | `nusyq_dispatch.py council "Best approach?" --agents=ollama,lmstudio` |
| Lint + test gate | CLI (zero-token) | `start_nusyq.py system_complete --budget-s=300` |
| Autonomous audit cycle | Culture Ship | `start_nusyq.py culture_ship_cycle --sync` |
| Persistent background task | Queue | `nusyq_dispatch.py queue "Analyze all tests" --priority=HIGH` |
| External model chat | MCP tool | `mcp__MCP_DOCKER__chat` (gpt-5.1, gemini-2.5-pro) |
| External CLI agent | MCP tool | `mcp__MCP_DOCKER__clink` (codex, gemini) |

**Rule of thumb**: For any analysis/review/generate task that would take Claude >500 tokens of output, route to Ollama or Codex first.

## Related Repos

- `../NuSyQ/` — Root NuSyQ repo (manifest, shared config)
- `../../SimulatedVerse/SimulatedVerse/` — SimulatedVerse game/cultivation system

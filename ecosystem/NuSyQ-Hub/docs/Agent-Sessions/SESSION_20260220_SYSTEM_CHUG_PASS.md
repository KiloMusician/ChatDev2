# Session Log — 2026-02-20 System Chug Pass

## Scope
- Full-system activation and reliability hardening pass.
- Focus areas:
  - error-signal consistency
  - background orchestrator hygiene persistence
  - trace service lifecycle + health semantics
  - async job-status signal truth
  - snapshot git-status reliability
  - antigravity runtime-aware health probing

## Commands Run (selected)
- `python scripts/start_nusyq.py activate_ecosystem`
- `python scripts/start_nusyq.py openclaw_smoke --sync`
- `python scripts/start_nusyq.py error_report --quick --sync --repo=nusyq-hub --repo=simulated-verse --repo=nusyq`
- `python scripts/start_nusyq.py doctor --quick --sync --budget-s=120`
- `python scripts/start_nusyq.py system_complete --sync --budget-s=120`
- `python scripts/start_nusyq.py orchestrator_hygiene --keep-completed=300 --keep-failed=100 --keep-cancelled=100 --stale-running-after-s=1800`
- `python scripts/start_nusyq.py trace_service_start`
- `python scripts/start_nusyq.py trace_service_status`
- `python scripts/start_nusyq.py trace_service_healthcheck`
- `python scripts/start_nusyq.py snapshot`
- `python scripts/start_nusyq.py brief`

## Key Fixes Applied
- `scripts/nusyq_actions/brief.py`
  - Ground-truth-first diagnostics and drift reporting.
- `scripts/nusyq_actions/trace_actions.py`
  - PID-managed trace service start/stop/status.
  - Healthcheck logic now accepts reachable endpoint when tracer backend is unavailable.
- `src/orchestration/background_task_orchestrator.py`
  - Prune/hygiene persistence corrected (`preserve_on_disk=False` for prune writes).
- `scripts/nusyq_actions/background_task_actions.py`
  - `orchestrator_hygiene` handler added.
- `scripts/start_nusyq.py`
  - Snapshot lint metric now prefers unified ground truth.
  - Async job-status inference fixed for checkpoint `generated_at`/`timestamp`.
  - Faster/more reliable git dirty detection via `git diff --quiet` probes + fallback.
- `src/api/systems.py`
  - Antigravity probe now includes marker checks and strict runtime mode.
- `zen_engine/codex/zen.json`
  - Repaired JSON syntax faults; codex loader now parses successfully.

## Outcomes
- `system_complete`: PASS (7/7).
- `ecosystem_status`: 18/18 active.
- `trace_service_status`: OK.
- `openclaw_smoke_status`: completed.
- `brief`: ground truth and aggregate aligned at 0/0/0.
- `snapshot`: lint errors now aligned to ground truth (`0`).
- Orchestrator backlog reduced from 595 to 409 with retained caps.

## Validation
- Targeted/combined suites passed for modified paths:
  - `tests/test_api_systems.py`
  - `tests/test_brief_action.py`
  - `tests/test_trace_actions_smoke.py`
  - `tests/test_background_task_orchestrator.py`
  - `tests/test_start_nusyq_parsing_smoke.py`

## Pass 2 — OpenClaw First, Antigravity Second (2026-02-20 late pass)

### Additions
- `scripts/start_nusyq.py`
  - Added new actions:
    - `openclaw_status`
    - `antigravity_status`
    - `antigravity_health` (alias)
  - Wired into:
    - `KNOWN_ACTIONS`
    - terminal routing (`METRICS`)
    - fast-path dispatch (no heavy startup)
    - dispatch map
    - help output and brief action menu
  - Added OpenClaw operational-readiness probe:
    - checks `config/secrets.json` OpenClaw block
    - checks gateway/API TCP reachability
    - validates enabled channel credentials vs placeholders
    - emits `functional` boolean and detailed notes
    - returns non-zero when not functional (truthful gate signal)
- `scripts/nusyq_actions/menu.py`
  - Analyze category now surfaces:
    - `openclaw_status`
    - `antigravity_status`

### New Tests
- `tests/test_start_nusyq_parsing_smoke.py`
  - `test_openclaw_status_reports_degraded_when_disabled`
  - `test_openclaw_status_reports_online_when_ready`
  - `test_antigravity_status_uses_probe`

### Latest Runtime Results
- `python scripts/start_nusyq.py openclaw_smoke --sync --json`:
  - PASS (`5/5`) for integration wiring smoke.
- `python scripts/start_nusyq.py openclaw_status --json`:
  - `status: degraded`, `functional: false`, RC=1.
  - Reasons: `openclaw.enabled=false`, gateway/API not reachable, no channels enabled.
- `python scripts/start_nusyq.py antigravity_status --json`:
  - `status: degraded`, `functional: false`, RC=1.
  - Detail: strict runtime required; markers present but no runtime process/URL.
- `python scripts/start_nusyq.py system_complete --sync --reuse-recent --json`:
  - PASS (`7/7`).

### Pass 2b Tightening
- `src/api/systems.py`
  - Antigravity `process_keywords` tightened to remove generic false-positive tokens:
    - removed: `npm run dev`, `vite`
    - kept/specialized: `modular-window-server`, `web/modular-window-server`, `modular-window-server/server.js`, `nusyq-modular-window-server`
- `tests/test_api_systems.py`
  - Added `test_antigravity_probe_keywords_are_specific`.

### Operational Check Notes
- `openclaw` CLI binary exists on host path, but invocation currently fails in this shell with:
  - `exec: node: not found`
  - Meaning: OpenClaw gateway cannot be launched from this environment until Node runtime is available on PATH.
- Temporary Antigravity runtime test:
  - Started `web/modular-window-server` (`npm run dev`) and confirmed `antigravity_status` flips to `online`.
  - After shutdown, `antigravity_status` returns `degraded` as expected.

## Pass 3 — OpenClaw Runtime/Bridge Hardening (2026-02-20 late-night)

### Runtime upgrades performed
- Installed Linux Node runtime (`node v22.22.0`) in environment.
- Installed Linux OpenClaw CLI globally (`openclaw 2026.2.19-2`) as additional launcher path.

### New OpenClaw controls added
- `scripts/start_nusyq.py`
  - Added managed gateway lifecycle:
    - `openclaw_gateway_start`
    - `openclaw_gateway_status`
    - `openclaw_gateway_stop`
  - Added managed bridge lifecycle:
    - `openclaw_bridge_start`
    - `openclaw_bridge_status`
    - `openclaw_bridge_stop`
  - Added launcher auto-resolution with fallback hierarchy:
    - OpenClaw binary probe
    - Windows `node.exe + openclaw.mjs` fallback
    - Node+mjs fallback
  - Added CLI-health truth path:
    - gateway status can be `functional=true` using OpenClaw health probe even when raw socket probe is unavailable from WSL loopback.
  - Added WSL-aware bridge routing:
    - when bind=`lan` and config URL is loopback, bridge auto-routes to WSL host gateway URL (example: `ws://172.24.224.1:18789`).
  - Added Windows fallback cleanup in gateway stop:
    - kills lingering unmanaged listener PIDs on target port when needed.
- `scripts/nusyq_actions/menu.py`
  - Added menu entries for gateway/bridge lifecycle actions.
- `config/secrets.json`
  - `openclaw.enabled: true`
  - `openclaw.bind: "lan"`

### Tests added/updated
- `tests/test_start_nusyq_parsing_smoke.py`
  - `test_openclaw_status_uses_cli_health_probe`
  - `test_openclaw_gateway_start_and_stop`
  - `test_openclaw_bridge_start_status_stop`
  - Updated disabled OpenClaw status expectation to `offline`.

### Live validation (end-to-end)
- `python scripts/start_nusyq.py openclaw_gateway_start --json --force`:
  - `status: ok`, `functional: true`.
- `python scripts/start_nusyq.py openclaw_gateway_status --json`:
  - `status: online`, `functional: true` via `probe_source=openclaw_cli_health`.
- `python scripts/start_nusyq.py openclaw_bridge_start --json`:
  - `status: ok`, `functional: true`, `connected: true`.
  - Bridge auto-selected `ws://172.24.224.1:18789` in this environment.
- `python scripts/start_nusyq.py openclaw_bridge_status --json`:
  - `status: online`, `functional: true`.
- `python scripts/start_nusyq.py openclaw_status --json`:
  - `status: degraded`, `functional: true`, `messaging_functional: false`
  - reason: no channels configured with real credentials yet.
- `python scripts/start_nusyq.py openclaw_bridge_stop --json`:
  - `status: stopped`.
- `python scripts/start_nusyq.py openclaw_gateway_stop --json`:
  - `status: stopped`; unmanaged listener cleanup engaged when necessary.

## Pass 4 — Signal Truth Tightening + Live Chug Validation (2026-02-21)

### Reliability fix applied
- `scripts/start_nusyq.py`
  - Hardened `openclaw_bridge_status` to prevent stale log false-positives:
    - `connected` now reflects real runtime connectivity (`running && connected_from_log`).
    - added `connected_from_log` for transparency/breadcrumbs.

### Regression coverage
- `tests/test_start_nusyq_parsing_smoke.py`
  - Added `test_openclaw_bridge_status_masks_stale_connected_marker`.
  - Validates: when process is down but old log has success marker, status remains `offline`, `connected=false`, `connected_from_log=true`.

### Live chug sequence (validated)
- Start:
  - `python scripts/start_nusyq.py openclaw_gateway_start --json --force` -> `status: ok`, `functional: true`.
  - `python scripts/start_nusyq.py openclaw_bridge_start --json` -> `status: ok`, `functional: true`, `connected: true`.
- Runtime checks:
  - `python scripts/start_nusyq.py openclaw_gateway_status --json` -> `online`, probe source `openclaw_cli_health`.
  - `python scripts/start_nusyq.py openclaw_bridge_status --json` -> `online`, `functional: true`.
  - `python scripts/start_nusyq.py openclaw_status --json` -> `degraded`, `functional: true`, `messaging_functional: false` (channels still not configured).
  - `python scripts/start_nusyq.py openclaw_smoke --json` -> `ok`, `5/5` checks passing.
- Stop:
  - `python scripts/start_nusyq.py openclaw_bridge_stop --json` -> `stopped`.
  - `python scripts/start_nusyq.py openclaw_gateway_stop --json` -> `stopped`.
  - Post-stop `openclaw_bridge_status --json` now correctly reports:
    - `status: offline`
    - `running: false`
    - `connected: false`
    - `connected_from_log: true` (historical marker only, not live state).

## Pass 5 — Antigravity Runtime Hardening + Health Crash Fix (2026-02-21)

### Antigravity runtime controls added
- `scripts/start_nusyq.py`
  - Added managed Open Antigravity lifecycle actions:
    - `open_antigravity_start`
    - `open_antigravity_runtime_status`
    - `open_antigravity_stop`
  - Added managed PID/log tracking:
    - `state/runtime/open_antigravity_runtime.pid`
    - `state/runtime/open_antigravity_runtime.log`
  - Added runtime health probe against modular-window-server:
    - `http://127.0.0.1:8080/health` (override with `--port`, `--host`)
  - `antigravity_status` now includes runtime block (`pid/running/health_url/health_ok`) for truth alignment.
- `src/api/systems.py`
  - Antigravity probes now include default health URLs:
    - `http://127.0.0.1:8080/health`
    - `http://127.0.0.1:8080/api/systems/antigravity/status`
  - Added `require_health_url: true` support so online state requires actual health URL success when configured.

### OpenClaw truth tightening
- `scripts/start_nusyq.py`
  - Added conservative credential format validation for OpenClaw channel readiness:
    - Slack (`xoxb-`, `xapp-`)
    - Discord token shape
    - Telegram bot token shape
    - Twilio/Teams field sanity checks
  - `openclaw_status` now emits `invalid_format_fields` per channel and notes invalid-enabled channel formats.

### Health diagnostics repair
- `ecosystem_health_checker.py`
  - Fixed crash in `run_comprehensive_check()` by initializing `self.repos` in constructor.
  - Prior failure (`AttributeError: EcosystemHealthChecker has no attribute 'repos'`) is resolved.

### Jedi restoration step
- Re-enabled Jedi setting in workspace configs:
  - `.vscode/settings.json` -> `"python.jediEnabled": true`
  - `.vscode/Settings/settings.json` -> `"python.jediEnabled": true`

### Tests added/updated
- `tests/test_start_nusyq_parsing_smoke.py`
  - `test_open_antigravity_start_status_stop`
  - `test_openclaw_status_rejects_invalid_channel_format`
  - updated antigravity probe test to include runtime health state
- `tests/test_api_systems.py`
  - `test_antigravity_probe_includes_health_urls_and_requires_health`

### Validation results
- `python -m py_compile scripts/start_nusyq.py src/api/systems.py ecosystem_health_checker.py tests/test_start_nusyq_parsing_smoke.py tests/test_api_systems.py` ✅
- `pytest -q --no-cov tests/test_start_nusyq_parsing_smoke.py tests/test_api_systems.py -k "openclaw or antigravity"` ✅
  - `13 passed, 10 deselected`

### Live runtime validation
- `open_antigravity_start --json` -> `status: ok`, `functional: true`
- `open_antigravity_runtime_status --json` -> `status: online`, `functional: true`
- `antigravity_status --json` -> `status: online`, `functional: true`, health URLs `1/2`
- `open_antigravity_stop --json` -> `status: stopped`
- post-stop `open_antigravity_runtime_status --json` -> `status: degraded`, `functional: false`

### Remaining blocker for OpenClaw "online"
- No real messaging channel credentials discovered in:
  - Linux env vars
  - Windows user env vars
  - `config/secrets.json`
  - local secrets files scanned (`config/secrets.ps1`, `.env`, `.env.local`, `config/.env`)
- Result: OpenClaw remains runtime-functional but messaging-degraded until real channel credentials are provided.

## Pass 6 — Error Signal Reliability Repair (2026-02-21)

### Ground-truth scanner reliability fixes
- `src/diagnostics/unified_error_reporter.py`
  - Fixed scanner subprocess deadlock risk:
    - `_run_with_heartbeat` now uses bounded `subprocess.run(..., capture_output=True, timeout=...)`
    - prevents pipe-buffer blocking on large lint outputs.
  - Added quick-mode style-debt visibility:
    - quick Ruff scan now includes additional isolated `E501` debt scan (`--isolated --select E501`).

### Validation and observed truth
- `python scripts/start_nusyq.py error_report --quick --sync --force --budget-s=120 --json`
  - now reports non-zero quick ground truth (`total_diagnostics: 195`, severity=`error`) instead of previous zero artifacts.
- Direct lint debt baseline:
  - `ruff check src tests scripts --statistics --select E501`
  - current count observed in this run: `894` line-length violations.

### Interpretation
- Quick error report now reflects meaningful error signal and no longer collapses to false-zero due output-capture stalls.
- Remaining gap: quick mode is sampled by design and therefore lower than full direct E501 count.

## Pass 7 — OpenClaw + Ollama Reliability Hotfix (2026-02-21)

### Model discovery ground-truth fix
- `src/integration/Ollama_Integration_Hub.py`
  - Fixed `KILOOllamaHub.discover_models()` to parse modern `ollama.Client.list()` responses (`ListResponse` with `.models` attribute), not only dict/list payloads.
  - Added robust fallback parsing for dict/object model shapes:
    - accepts `name`, `model`, or `id` as model identifier.
    - extracts details from dict or pydantic-style `model_dump()`.
  - Improved `list_ollama_models()`:
    - primary endpoint: `/v1/models`
    - fallback endpoint: `/api/tags`

### Path resolution escape fix
- `src/utils/repo_path_resolver.py`
  - Fixed Windows backslash replacement bug in `$env:USERPROFILE` normalization by switching `re.sub` replacement to lambda.
  - Prevents `re.error: bad escape \\U` class failures.

### OpenClaw bridge hardening
- `src/integrations/openclaw_gateway_bridge.py`
  - Fixed quest logging compatibility:
    - no longer assumes `QuestManager.log_quest()` exists.
    - uses best-effort compatibility (`log_quest` or `add_quest`) and never fails message routing on quest-log API mismatch.
  - Fixed channels API URL derivation:
    - replaced fragile string split logic with URL parsing (`urlparse`).
    - `ws://host:18789` now correctly maps to `http://host:18790/api/channels/send`.
- `scripts/start_nusyq.py`
  - `openclaw_status` now probes runtime channel truth from OpenClaw CLI:
    - `openclaw channels list --json`
    - emits `openclaw_cli_channels_probe_ok`, `openclaw_cli_channels`, `channels_ready_config`, `channels_ready`.
  - Messaging status now aligns with runtime channels, not only static `secrets.json` config.

### Tests added
- `tests/test_ollama_models.py`
  - `test_list_ollama_models_falls_back_to_api_tags`
  - `test_discover_models_handles_listresponse_with_models_attr`
- `tests/test_repo_path_resolver.py`
  - `test_normalize_userprofile_windows_path_does_not_raise_bad_escape`
- `tests/integration/test_openclaw_gateway_bridge.py`
  - `test_build_channels_api_url_uses_gateway_host`
  - `test_handle_inbound_message_allows_quest_manager_without_log_quest`

### Validation results
- Live reproduction resolved:
  - Before: `discover_models_count=0` while Ollama had 10 models.
  - After: `discover_models_count=10`.
- OpenClaw runtime checks:
  - `openclaw_gateway_status --json` => `status: online`, `functional: true`
  - `openclaw_bridge_status --json` => `status: online`, `connected: true`
  - synthetic inbound route (`handle_inbound_message`) now returns success and Ollama output.
- Pytest targeted checks:
  - `pytest -q --no-cov tests/test_ollama_models.py -k "falls_back_to_api_tags or handles_listresponse"` ✅
  - `pytest -q --no-cov tests/test_repo_path_resolver.py -k "bad_escape or normalize_userprofile"` ✅
  - `pytest -q --no-cov tests/integration/test_openclaw_gateway_bridge.py -k "build_channels_api_url_uses_gateway_host or allows_quest_manager_without_log_quest"` ✅

### Remaining constraint
- `openclaw_status` remains `degraded` for messaging because real external channel credentials are still disabled/placeholder (`slack`, `discord`, `telegram`, `whatsapp`, `teams`).

## Pass 8 — Lint/Doctor Closure Sweep (2026-02-24)

### Commands run
- `python scripts/start_nusyq.py error_report --quick --sync --force --repo=nusyq-hub,nusyq,simulated-verse --budget-s=240`
- `python scripts/start_nusyq.py doctor --with-lint --with-system-health --with-analyzer --sync --budget-s=360`
- `python -m black tests/test_consciousness_loop.py src/orchestration/consciousness_loop.py src/factories/artifact_registry.py src/integration/chatdev_mcp_integration.py src/culture_ship/integrated_terminal.py src/orchestration/background_task_orchestrator.py src/integrations/nogic_bridge.py src/tools/agent_task_router.py`
- `python -m ruff check --fix tests/test_consciousness_loop.py`
- `python -m black --check src tests`
- `python -m ruff check src tests`

### Fixes applied
- Resolved `doctor` failing `lint_test_diagnostic` by formatting and import-hygiene cleanup in:
  - `tests/test_consciousness_loop.py`
  - `src/orchestration/consciousness_loop.py`
  - `src/factories/artifact_registry.py`
  - `src/integration/chatdev_mcp_integration.py`
  - `src/culture_ship/integrated_terminal.py`
  - `src/orchestration/background_task_orchestrator.py`
  - `src/integrations/nogic_bridge.py`
  - `src/tools/agent_task_router.py`

### Validation outcomes
- `doctor --with-lint --with-system-health --with-analyzer`: PASS (`3/3`).
- `black --check src tests`: PASS.
- `ruff check src tests`: PASS.
- Forced cross-repo quick ground truth (`error_report`): `0` diagnostics (`0 errors / 0 warnings / 0 infos`).

## Pass 9 — Audit-Driven Integration Contract Patches (2026-02-25)

### Scope addressed
- Applied concrete patches from runtime audit findings:
  - GameDev ↔ ChatDev wiring gap
  - ChatDev router success/status truth contract
  - Council loop top-level success propagation

### Changes applied
- `src/game_development/zeta21_game_pipeline.py`
  - Added `creation_mode` support in `create_new_game_project`:
    - `template` (existing behavior)
    - `chatdev` (new route-through-ChatDev mode)
  - Added lazy ChatDev router bootstrap:
    - `_get_chatdev_router()`
  - Added ChatDev-backed creation path:
    - `_create_new_game_project_with_chatdev(...)`
    - writes `CHATDEV_REQUEST.md`
    - persists ChatDev task metadata in `project.json`
  - Added metadata field: `creation_mode`.
- `src/orchestration/chatdev_autonomous_router.py`
  - `_execute_chatdev_task(...)` now sets:
    - `success = (returncode == 0)`
    - `status = "success" | "failed"` accordingly
  - `route_task_to_chatdev(...)` now sets `task.status` from result success (`completed`/`failed`) instead of unconditional completion.
- `src/orchestration/council_orchestrator_chatdev_loop.py`
  - `propose_and_execute(...)` now propagates real execution outcome:
    - top-level `success` mirrors ChatDev result
    - top-level `status` is `completed` or `failed`
    - decision state updates to `completed` or `failed` with artifacts.
- `scripts/start_nusyq.py`
  - Improved `council_loop` failure rendering:
    - prints ChatDev status/returncode/error when available.

### Tests added
- `tests/test_zeta21_game_pipeline_chatdev.py`
  - chatdev-mode routing + metadata persistence
  - failure path cleanup behavior
  - invalid `creation_mode` guard
- `tests/test_chatdev_autonomous_router_contract.py`
  - task status follows execution success
  - success flag derived from subprocess return code
- `tests/test_council_orchestrator_chatdev_loop_contract.py`
  - closed loop reports failed when ChatDev fails
  - closed loop reports completed when ChatDev succeeds

### Validation outcomes
- Targeted lint/style:
  - `ruff` on patched files: PASS
  - `black --check` on patched files: PASS
- Targeted tests:
  - `pytest -q --no-cov tests/test_zeta21_game_pipeline_chatdev.py tests/test_chatdev_autonomous_router_contract.py tests/test_council_orchestrator_chatdev_loop_contract.py`: PASS (`7 passed`)
- Runtime workflow verification:
  - `python scripts/start_nusyq.py council_loop --demo`
    - now exits non-zero when ChatDev returns failure (truthful status propagation)
    - CLI shows ChatDev status/return code details
- Ecosystem gates:
  - `python scripts/start_nusyq.py system_complete --sync --budget-s=300`: PASS (`7/7`)
  - `python scripts/start_nusyq.py error_report --quick --sync --force --repo=nusyq-hub,nusyq,simulated-verse --budget-s=240`: `0 diagnostics`

## Pass 10 — ChatDev CLI Compatibility Hardening (2026-02-25)

### Scope addressed
- Fixed runtime contract mismatch between NuSyQ router command assumptions and local ChatDev CLI capabilities.
- Removed hard dependency on unsupported ChatDev flags/values.
- Added actionable error normalization for missing ChatDev credentials.

### Changes applied
- `src/orchestration/chatdev_autonomous_router.py`
  - Added ChatDev CLI capability discovery:
    - `_get_supported_chatdev_flags()` probes `run.py --help` and caches supported flags.
  - Added dynamic command construction:
    - `_build_chatdev_command(...)` includes only supported flags (`--name`, `--description`, `--model`, `--auto-mode` when available).
  - Added model-compatibility fallback:
    - `_strip_model_flag(...)`
    - if ChatDev rejects model override (e.g. `KeyError: 'ollama'`), retries once without `--model`.
  - Existing status/success contract remains truthful (`success` from subprocess return code).
- `tests/test_chatdev_autonomous_router_contract.py`
  - Added `test_execute_chatdev_task_uses_only_supported_cli_flags`.
  - Added `test_execute_chatdev_task_retries_without_model_on_model_keyerror`.
  - Added `test_execute_chatdev_task_surfaces_credential_guidance`.

### Validation outcomes
- Lint/style:
  - `black src/orchestration/chatdev_autonomous_router.py tests/test_chatdev_autonomous_router_contract.py`: PASS
  - `ruff check src/orchestration/chatdev_autonomous_router.py tests/test_chatdev_autonomous_router_contract.py`: PASS
- Targeted tests:
  - `pytest -q --no-cov tests/test_chatdev_autonomous_router_contract.py tests/test_council_orchestrator_chatdev_loop_contract.py tests/test_zeta21_game_pipeline_chatdev.py`: PASS (`10 passed`)
- Runtime verification:
  - `python scripts/start_nusyq.py council_loop --demo`
    - no longer fails on unsupported `--description/--auto-mode`
    - no longer hard-fails on `--model ollama` mismatch (auto-retry without model)
    - current remaining blocker is environment-level ChatDev credential requirement (`OpenAI API key not found`), now surfaced as explicit guidance: set `OPENAI_API_KEY` or configure ChatDev local provider/model.

## Pass 11 — Legacy ChatDev Shim Activation (2026-02-25)

### Scope addressed
- Verified existing ecosystem integrations include legacy ChatDev pathways (`run_ollama.py` + launcher/service wrappers).
- Added an in-router compatibility shim so autonomous routing can pivot to the legacy local-LLM entrypoint automatically.

### Changes applied
- `src/orchestration/chatdev_autonomous_router.py`
  - Added legacy shim command builder for `run_ollama.py`:
    - `_build_chatdev_ollama_shim_command(...)`
    - `_to_ollama_root_url(...)`
    - `_sanitize_project_name(...)`
    - `_should_try_legacy_ollama_shim(...)`
  - `_execute_chatdev_task(...)` now:
    - retries via `run_ollama.py` when legacy integration failures are detected (missing OpenAI key, model mismatch, unsupported args).
  - Added subprocess-timeout contract mapping:
    - `subprocess.TimeoutExpired` now returns `{"success": False, "status": "timeout", ...}` instead of generic `error`.
  - Added configurable timeout:
    - `CHATDEV_TASK_TIMEOUT_SECONDS` (default `300`, clamped to `30..3600`)
- `tests/test_chatdev_autonomous_router_contract.py`
  - Added `test_execute_chatdev_task_uses_legacy_ollama_shim_on_credential_failure`.
  - Added `test_execute_chatdev_task_maps_subprocess_timeout_to_timeout_status`.
  - Added `test_chatdev_timeout_seconds_respects_env`.

### Validation outcomes
- Lint/style:
  - `black src/orchestration/chatdev_autonomous_router.py tests/test_chatdev_autonomous_router_contract.py`: PASS
  - `ruff check src/orchestration/chatdev_autonomous_router.py tests/test_chatdev_autonomous_router_contract.py`: PASS
- Targeted tests:
  - `pytest -q --no-cov tests/test_chatdev_autonomous_router_contract.py tests/test_council_orchestrator_chatdev_loop_contract.py tests/test_zeta21_game_pipeline_chatdev.py`: PASS (`13 passed`)
- Runtime verification:
  - `python scripts/start_nusyq.py council_loop --demo`
    - confirmed live fallback from `run.py` to `run_ollama.py` in the real ChatDev install
    - current blocker moved to runtime capacity (`run_ollama.py` timed out at 300s for demo task) rather than contract mismatch.

## Pass 12 — Self-Configuring ChatDev Shim Settings (2026-02-25)

### Scope addressed
- Upgraded shim path from manual env-driven to autonomous config discovery.
- Router now self-configures Ollama URL/model/org from existing ecosystem configs.

### Changes applied
- `src/orchestration/chatdev_autonomous_router.py`
  - Added multi-source settings resolution with precedence:
    - env: `CHATDEV_OLLAMA_URL`, `OLLAMA_BASE_URL`, `BASE_URL`, `CHATDEV_OLLAMA_MODEL`, `CHATDEV_ORG`
    - helper: `src.utils.config_helper.get_ollama_host()`
    - file configs:
      - `config/settings.json` (`ollama.host`)
      - `config/chatdev_ollama_models.json` (`models.primary_coder.name`, `agent_assignments.Programmer`, `ollama_endpoint`)
      - `src/integration/settings.json` (`organization`, `ollama_base_url`)
  - Added `_build_chatdev_env(...)` to auto-populate:
    - `OLLAMA_BASE_URL`, `BASE_URL`, `OPENAI_BASE_URL` (OpenAI-compatible `/v1`)
    - `CHATDEV_MODEL`
    - `CHATDEV_USE_OLLAMA=1` + fallback `OPENAI_API_KEY=ollama-local` for shim mode
  - Added `CHATDEV_TASK_TIMEOUT_SECONDS` runtime knob (clamped `30..3600`).
- `tests/test_chatdev_autonomous_router_contract.py`
  - Added env precedence test for settings resolution.
  - Added shim command auto-settings test.
  - Added environment synthesis test for OpenAI-compatible vars.

### Validation outcomes
- Lint/style:
  - `black src/orchestration/chatdev_autonomous_router.py tests/test_chatdev_autonomous_router_contract.py`: PASS
  - `ruff check src/orchestration/chatdev_autonomous_router.py tests/test_chatdev_autonomous_router_contract.py`: PASS
- Targeted tests:
  - `pytest -q --no-cov tests/test_chatdev_autonomous_router_contract.py tests/test_council_orchestrator_chatdev_loop_contract.py tests/test_zeta21_game_pipeline_chatdev.py`: PASS (`16 passed`)
- Live runtime verification:
  - `CHATDEV_TASK_TIMEOUT_SECONDS=60 python scripts/start_nusyq.py council_loop --demo`
    - confirmed shim auto-populated command values from existing config:
      - `--org KiloFoolish`
      - `--model qwen2.5-coder:7b`
      - `--ollama-url http://localhost:11434`
    - timeout surfaced with truthful status contract:
      - `status: timeout`
      - `error: ChatDev command timed out after 60 seconds`.

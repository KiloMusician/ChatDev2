# ChatDev2 — Sector Card

**Role:** Autonomous multi-agent software development system (ChatDev v2 fork).
Operates as a colony worker — receives tasks from `Dev-Mentor/tasks/queue.json`
and produces code autonomously via its agent pipeline.

**Colony integration:**
- Tasks submitted via `delegation_planner.py chatdev "title"` or direct queue write
- Docker container: `kilocore-chatdev` on port :7338
- Uses `lattice` profile; adapts to LiteLLM :4000 for all model calls

**Key directories:**
- `camel/` — Core CAMEL agent framework
- `assets/`, `attached_assets/` — Task and output assets
- Agent roles: Programmer, Reviewer, Tester, Documenter

**Status:** Live as Docker container. Routes through LiteLLM ecosystem aliases.
Safe-mode tasks only (safe_mode: true in task envelope).

**Fast truth probe:**
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_colony_doctor.ps1
```

**Bounded local workflow smoke:**
```powershell
python .\tools\workflow_smoke_runner.py `
  --repo-root C:\dev\_sandboxes\chatdev-factory-prototype-smoke `
  --yaml-file ChatDev_v1.yaml `
  --task-prompt "Create the smallest possible Python program that prints hello. Keep it one file and minimal." `
  --session-name chatdev_smoke_runner_local `
  --timeout-seconds 360 `
  --poll-interval 2 `
  --grace-seconds 20 `
  --stop-on-first-artifact
```
Expected proof shape:
- `status: artifact_emitted` or `completed`
- output under `WareHouse\<session>_<timestamp>\code_workspace\`
- real generated artifact such as `hello.py`, not bootstrap files under `.venv/` or `attachments/`

**Bounded local GameDev phase-1 smoke:**
```powershell
python .\tools\workflow_smoke_runner.py `
  --repo-root C:\dev\_sandboxes\chatdev-factory-prototype-smoke `
  --yaml-file C:\dev\active\ChatDev2\yaml_instance\GameDev_phase1_smoke.yaml `
  --task-prompt "Create the smallest possible Python game prototype. Keep it to one file and minimal." `
  --session-name gamedev_phase1_smoke_local `
  --timeout-seconds 420 `
  --poll-interval 2 `
  --grace-seconds 20 `
  --stop-on-first-artifact
```
Expected proof shape:
- `status: artifact_emitted` or `completed`
- output under `WareHouse\<session>_<timestamp>\code_workspace\game.py`
- purpose is phase-1 artifact proof, not full `GameDev_v1` polish, QA, or execution coverage

**Bounded local GameDev stub smoke:**
```powershell
python .\tools\workflow_smoke_runner.py `
  --repo-root C:\dev\_sandboxes\chatdev-factory-prototype-smoke `
  --yaml-file C:\dev\active\ChatDev2\yaml_instance\GameDev_stub_smoke.yaml `
  --task-prompt "Create the smallest possible pygame stub. Keep it to one file." `
  --session-name gamedev_stub_smoke_local `
  --timeout-seconds 240 `
  --poll-interval 2 `
  --grace-seconds 20 `
  --stop-on-first-artifact
```
Expected proof shape:
- `status: artifact_emitted` or `completed`
- output under `WareHouse\<session>_<timestamp>\code_workspace\game.py`
- purpose is sandbox artifact proof for the GameDev lane when full game generation is too slow

**Bounded local GameDev mechanic smoke:**
```powershell
python .\tools\workflow_smoke_runner.py `
  --repo-root C:\dev\_sandboxes\chatdev-factory-prototype-smoke `
  --yaml-file C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml `
  --task-prompt "Create the smallest possible playable pygame square-move demo. Keep it to one file." `
  --session-name gamedev_mechanic_smoke_local `
  --timeout-seconds 240 `
  --poll-interval 2 `
  --grace-seconds 20 `
  --stop-on-first-artifact `
  --validate-python-artifacts `
  --run-python-artifacts `
  --runtime-python python `
  --python-run-timeout-seconds 5
```
Expected proof shape:
- `status: artifact_emitted` or `completed`
- `artifact_validation` shows emitted `.py` files as syntactically valid
- `artifact_runtime_validation` shows the emitted `.py` launched without an immediate runtime crash
- `runtime_python` identifies the interpreter used for launch validation
- output under `WareHouse\<session>_<timestamp>\code_workspace\game.py`
- purpose is one-layer-deeper proof beyond window-only stub

**Receipt and status entry points:**
```bash
make latest-gamedev-smoke
make latest-gamedev-smoke-full
make status-gamedev
make status-gamedev-compact
```
Expected proof shape:
- `latest-gamedev-smoke` returns the compact latest receipt summary
- `latest-gamedev-smoke-full` returns the full latest receipt payload
- `status-gamedev` returns the combined live status report
- `status-gamedev-compact` returns only the compact `automation_summary` contract
- the compact contract now reports `preferred_live_model_matches_smoke` and `preferred_live_model_proven_for_smoke` so model-routing preference stays separate from bounded runtime proof
- when that preferred-vs-proven split exists, `advisories` emits machine-readable warnings without collapsing the passing smoke gate
- the full `assessment` block now mirrors that distinction with `preferred_live_model`, `proven_smoke_model`, `preferred_live_model_matches_smoke`, `preferred_live_model_proven_for_smoke`, machine-readable `advisories`, and human-readable `notes`

**Raw LiteLLM latency probe for the same GameDev prompt:**
```powershell
python .\tools\litellm_raw_latency_probe.py `
  --model ecosystem-coder-fast `
  --model ecosystem-qwen `
  --model ecosystem-auto `
  --model ecosystem-qwen35
```
Expected proof shape:
- one JSON line per model
- distinguishes raw completion latency from ChatDev workflow overhead
- useful when GameDev smoke is timing out before `game.py`

**Raw full-vs-stub comparison on the same route:**
```powershell
python .\tools\litellm_raw_latency_probe.py `
  --model ecosystem-coder-fast `
  --preset gamedev-phase1-full

python .\tools\litellm_raw_latency_probe.py `
  --model ecosystem-coder-fast `
  --preset pygame-stub `
  --max-tokens 180
```
Expected proof shape:
- same route, two prompt surfaces
- helps separate “full game generation is too slow” from “backend is generally unhealthy”

**Colony doctor with GameDev Python lane truth:**
```powershell
python .\tools\chatdev_colony_doctor.py --json
```
Expected proof shape:
- one JSON report covering live service health, local route truth, and `gamedev_env`
- `gamedev_env` reports which Python lanes currently have `pygame`
- use this before assuming the active venv is valid for local GameDev smoke/runtime validation

**Bootstrap a repo-local GameDev Python 3.13 lane:**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\bootstrap_gamedev_env.ps1
```
Expected proof shape:
- creates `.venv-gamedev313` using the current `python` command
- installs `requirements.txt`
- final probe shows `pygame` available in the new env
- `chatdev_colony_doctor.py --json` reports `repo_gamedev_venv` when the env exists

**Run the mechanic smoke through the repo-local GameDev lane:**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_gamedev_mechanic_smoke.ps1
```
Expected proof shape:
- `status: artifact_emitted` or `completed`
- `runtime_python` points at `.venv-gamedev313`
- `artifact_validation` is syntactically valid
- `artifact_runtime_validation` shows the generated pygame artifact launched without an immediate crash
- bootstraps `.venv-gamedev313` automatically if it is missing

**Windows-native GameDev lane entry point:**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 doctor -Json
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 local-proof
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 local-proof -Json
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 local-start
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 local-status
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 local-stop
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 bootstrap
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 smoke
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 smoke -Json
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 latest
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 latest-full
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 status-full
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 status-compact
```
Expected proof shape:
- `doctor` returns the same bounded colony report plus `gamedev_env`
- `local-proof` returns the narrow bounded local DevAll app proof:
  - `chatdev_local_health`
  - `local_app_loaded`
  - `local_app_bootable`
  - `local_app_core_routes_ready`
  - `local_app_extended_routes_ready`
  - `local_startup_probe` when used with `-Json`
  - uses an ephemeral localhost startup port by default so concurrent proofs do not fight over a fixed port
- `local-start` starts one managed local DevAll app instance on `:6400` and waits for `/health`
- `local-status` returns the managed-process state plus `/health`
- `local-stop` stops the managed local DevAll app instance
- `bootstrap` creates or verifies `.venv-gamedev313`
- `smoke` runs the proven repo-local mechanic smoke lane end-to-end
- `smoke` also writes a stable JSON receipt by default under `C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\_smoke_receipts\<session>.json`
- `smoke` refreshes `C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\_smoke_receipts\latest.json` as a stable pointer to the newest receipt
- `smoke -Json` returns the final receipt JSON from disk without interleaved workflow logs
- runtime validation now patches `pygame.event.get()` under dummy SDL to inject a synthetic `QUIT`, so well-behaved pygame event loops can reach `artifact_runtime_outcome: completed`
- `latest` returns the newest smoke receipt summary, including `workflow_used`, `provider` / `model`, explicit `proven_smoke_model`, `attempted_model`, any auto-seeded local `env_defaults`, `output_path`, `result_json`, `artifact_runtime_outcome`, `runtime_proof_depth`, `runtime_launch_proven`, and `runtime_completion_proven`; `latest-full` returns the full latest receipt payload
- `status-full` returns doctor summary plus latest smoke summary, the current `yaml_validation` gate result from `uv run python tools/validate_all_yamls.py`, an `assessment` verdict with `next_action` / `recommendation`, and an `automation_summary` block with callable scope (`callable_via`, `full_devall_ready`, `local_app_bootable`, `local_app_core_routes_ready`, `local_app_extended_routes_ready`, `artifact_runtime_outcome`, `runtime_proof_depth`, `runtime_launch_proven`, `runtime_completion_proven`, `current_proof`, `current_proof_blockers`, `runtime_launch_gate_ok`, `runtime_launch_gate_blockers`, `runtime_completion_gate_ok`, `runtime_completion_gate_blockers`, `workflow_gate_ok`, `workflow_gate_blockers`, `proof_scope`), receipt freshness (`proof_generated_at`, `proof_age_seconds`, `proof_freshness`, `proof_stale_after_seconds`), workflow/provider/output facts, `attempted_model`, `env_defaults`, `smoke_attempted_without_model_call`, a compact `operator_commands` block including the cheaper `latest` receipt surfaces, a separate `proxy_health` split, and `backend_requirements` that clarify Ollama is optional for the currently proven LiteLLM lane
- `status-compact` returns only the compact `automation_summary` contract so automations can consume the proven readiness fields, provider/model, output path, and operator commands without the larger nested report
- when a smoke fails before token accounting starts, read `attempted_model`, `env_defaults`, and `smoke_attempted_without_model_call` first; they now expose the intended local route even when `provider`, `model`, and `proven_smoke_model` are still null
- interpret the local DevAll readiness fields narrowly:
  `full_devall_ready` = app currently live on `:6400`
  `local_app_bootable` = checkout can start locally
  `local_app_core_routes_ready` = `/health` and `/api/health` respond during the bounded startup probe
  `local_app_extended_routes_ready` = `/api/bridge/status` and `/api/ecosystem/status` also respond during that startup probe
- `smoke`, `latest`, and `status` accept `-ReceiptDir` for alternate sandbox receipt roots

**Direct Ollama latency probe for the same GameDev prompt:**
```powershell
python .\tools\litellm_raw_latency_probe.py `
  --mode ollama-generate `
  --base-url http://127.0.0.1:11434 `
  --model qwen3:8b `
  --model qwen2.5-coder:14b `
  --model devstral:24b
```
Expected proof shape:
- one JSON line per direct Ollama model
- separates LiteLLM routing effects from backend model behavior

Current verified shape on 2026-06-25:
- Live colony ChatDev `:7338` health is up.
- Dev-Mentor `:7337`, LiteLLM `:4000`, and Ollama `:11434` are reachable.
- Local checkout app imports after `fastmcp` is installed.
- Sandbox smoke venv `C:\dev\_sandboxes\chatdev-factory-prototype-smoke\.venv\Scripts\python.exe` is Python `3.13` and now has `pygame`.
- Repo venv `C:\dev\active\ChatDev2\.venv\Scripts\python.exe` is Python `3.14`; `pygame` currently falls back to a source-build path there instead of the Windows wheel used by Python `3.13`.
- Local checkout exposes bridge/ecosystem routes, but the live `:7338` service does not expose `/api/bridge/status` or `/api/ecosystem/status`; treat that as container/image drift until rebuilt or re-routed.
- Latest bounded startup proof sharpens that split further:
  - `local_app_bootable: true`
  - `local_app_core_routes_ready: true`
  - `local_app_extended_routes_ready: true`
- Avoid broad `rg` over this repo without excluding `ecosystem/`, `logs/`, `WareHouse/`, and generated reports.

**Task envelope format:**
```json
{
  "assigned_to": "chatdev",
  "category": "hardening",
  "issue": "<task description>",
  "repo": "<repo name>",
  "safe_mode": true
}
```

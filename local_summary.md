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
powershell -ExecutionPolicy Bypass -File .\tools\bootstrap_gamedev_env.ps1
```
Expected proof shape:
- creates `.venv-gamedev313` using the current `python` command
- installs `requirements.txt`
- final probe shows `pygame` available in the new env
- `chatdev_colony_doctor.py --json` reports `repo_gamedev_venv` when the env exists

**Run the mechanic smoke through the repo-local GameDev lane:**
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_gamedev_mechanic_smoke.ps1
```
Expected proof shape:
- `status: artifact_emitted` or `completed`
- `runtime_python` points at `.venv-gamedev313`
- `artifact_validation` is syntactically valid
- `artifact_runtime_validation` shows the generated pygame artifact launched without an immediate crash
- bootstraps `.venv-gamedev313` automatically if it is missing

**Windows-native GameDev lane entry point:**
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 doctor -Json
powershell -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 bootstrap
powershell -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 smoke
powershell -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 smoke -Json
powershell -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 latest
powershell -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 status
```
Expected proof shape:
- `doctor` returns the same bounded colony report plus `gamedev_env`
- `bootstrap` creates or verifies `.venv-gamedev313`
- `smoke` runs the proven repo-local mechanic smoke lane end-to-end
- `smoke` also writes a stable JSON receipt by default under `C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\_smoke_receipts\<session>.json`
- `smoke` refreshes `C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\_smoke_receipts\latest.json` as a stable pointer to the newest receipt
- `smoke -Json` returns the final receipt JSON from disk without interleaved workflow logs
- `latest` returns the newest smoke receipt summary; add `-Json` to emit the full payload
- `status` returns doctor summary plus latest smoke summary; add `-Json` to emit the full payload
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

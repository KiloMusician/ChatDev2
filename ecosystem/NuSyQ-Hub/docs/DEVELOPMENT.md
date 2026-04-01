## Developer Setup & Quickstart

This document provides a concise developer onboarding guide for NuSyQ-Hub. It
covers environment setup, required environment variables, common developer
commands (tests, linters, scans), and quick instructions to start the Multi-AI
Orchestrator for local testing.

### 1) Python environment

Windows (PowerShell)

```powershell
# from repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# optional dev extras
pip install -e ".[dev]"
```

Unix/macOS (bash)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 2) Environment variables

Copy `.env.example` to `.env` and populate the values. Key variables used by the
repository:

- `CHATDEV_PATH` (recommended) — Path to a local ChatDev clone used for
  multi-agent experiments. Alternatively set `chatdev.path` in
  `config/secrets.json`.
- `GITHUB_COPILOT_API_KEY` (optional) — If present, Copilot integration will use
  it; otherwise the orchestrator falls back to safe/local providers.
- `OLLAMA_HOST` / `OLLAMA_PORT` — For local Ollama model coordination (only when
  you run Ollama).

Loading .env into PowerShell (helper)

```powershell
# Simple loader (works for KEY=VALUE lines)
Get-Content .env | ForEach-Object {
  if ($_ -and -not ($_ -like '#*')) {
    $pair = ($_ -split '=',2)
    if ($pair.Length -eq 2) { Set-Item -Path Env:\$($pair[0].Trim()) -Value $($pair[1].Trim()) }
  }
}
```

Use the included `scripts/setup_env.ps1` or `scripts/setup_env.sh` helpers where
available.

### 3) Common developer commands

Run quick repo scan (find hotspots, duplicates, and complexity):

```bash
python -m src.tools.maze_solver . --max-depth 6 --progress
```

Run lint / tests / formatting

```bash
python scripts/lint_test_check.py
pytest -q
ruff .
black --check .
```

Run a single test file (recommended when iterating):

```bash
pytest tests/test_kilo_discovery.py -q -o addopts=""
```

Note: The test runner in CI may use coverage addopts that can interfere with
local runs; passing `-o addopts=""` clears that value for a local run.

### 4) Terminal logs

Terminal routing writes JSON lines to `data/terminal_logs/*.log`. Use
`python scripts/activate_live_terminal_routing.py --validate` to verify the
watcher scripts and tasks are aligned with `data/terminal_routing.json`.

### 5) Start Multi-AI Orchestrator (local smoke test)

The repository provides lightweight scripts for local orchestrator testing.

1. Ensure `PYTHONPATH` includes the repository root (or run from the repo root
   and set env variable):

Windows PowerShell:

```powershell
$env:PYTHONPATH = Convert-Path .
python -u scripts/start_multi_ai_orchestrator.py
```

Or run the smoke test (submits a safe task and polls for completion):

```powershell
$env:PYTHONPATH = Convert-Path .
python -u scripts/submit_orchestrator_test_task.py
```

Notes:

- If `GITHUB_COPILOT_API_KEY` is not set, Copilot integration will log a warning
  and the orchestrator will use a local/fallback provider where available. This
  is expected and non-fatal.
- ChatDev / Ollama integrations require local services or the
  `CHATDEV_PATH`/OLLAMA envs to be set; without them the orchestrator uses
  conservative fallbacks.

### 5) Debugging tips & recoverability

- If you get import errors, run `python src/utils/quick_import_fix.py` to
  attempt automated fixes.
- For deep health checks, run `python src/diagnostics/system_health_assessor.py`
  and `python src/healing/repository_health_restorer.py`.
- For PowerShell-specific import audits use
  `src/diagnostics/ImportHealthCheck.ps1`.

### 6) Making changes & submitting PRs

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Run unit tests for affected modules.
3. Run `pre-commit` hooks: `pre-commit run --files <changed_files>`
4. Commit and push. Open a PR against `master`.

### 7) Where to find help

- Session logs: `docs/Agent-Sessions/`
- Orchestration reports: `Reports/consensus/` and
  `data/orchestration_state*.json`
- If something blocks you, run `src/healing/repository_health_restorer.py` and
  attach `logs/healing_report.json` to your issue.

---

If you want, I can also add a short `make` or `invoke` task file to simplify
these commands into `make dev` / `make test`—let me know and I'll scaffold that
next.

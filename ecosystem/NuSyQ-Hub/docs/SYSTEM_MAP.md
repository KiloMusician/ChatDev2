# NuSyQ-Hub — System Map

## Purpose
- Core orchestration and diagnostics hub for the NuSyQ ecosystem.
- Stable home for AI coordination logic, healing/diagnostics tooling, and doctrine/docs.

## Scope & Ownership
- Language: Python (3.12+) with supporting PowerShell tooling.
- Default branch: `master` (CI targets `main`/`master` via workflows).
- CI: `.github/workflows/ci.yml` (ruff, black --check, run_tests.py), plus additional quality/security workflows in `.github/workflows/`.

## Key Directories (path-based)
- `src/` — core orchestration, integration, diagnostics, healing, setup/secrets systems.
- `scripts/` — utility/diagnostic/launch scripts.
- `docs/` — documentation (doctrine, guides, maps).
- `config/` — config and secrets templates (real secrets must stay out of git).
- `logs/` — runtime logs (should be ignored; if you need to keep canonical summaries, move them into `docs/`).
- `tests/` — pytest suite; additional integration tests under `tests/` subfolders.
- `.github/workflows/` — CI/quality/security pipelines.

## Entry Points
- Core test driver: `python run_tests.py` (used in CI).
- Lint: `python -m ruff .`; Format check: `python -m black --check .`.
- Compile sanity: `python -m compileall src` (fast import check).
- Environment setup (example):
  1) `python -m venv .venv` && activate
  2) `python -m pip install --upgrade pip`
  3) `python -m pip install -r dev-requirements.txt`

## Trace Entry Points
- Boundary map: `docs/SYSTEM_WIRING_MAP_2026-02-25.md` (contract normalizers, smoke gates, integration boundaries).
- Map index: `docs/SYSTEM_MAPS_META_INDEX.md` (role-based map routing).
- Windows/WSL runtime split: `docs/WSL_INTEGRATION.md` (auth/hooks/interpreter boundary caveats).
- Terminal intelligence surface: `python scripts/start_nusyq.py terminals status|probe|doctor`.
- SimulatedVerse runtime smoke (Windows-hosted from WSL): use `scripts/integration_health_check.py --mode full` and inspect `simulatedverse_base_candidates` + WSL gateway fields.

## Artifacts to Keep Out of Git
- Real secrets: `config/secrets.*`, `.env*`, `settings.local.*`, API keys/tokens of any form.
- Runtime outputs: `logs/`, `Reports/`, `State/`, `ops/receipts/`, caches (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`).
- Large model files: `models/`, `*.gguf`, `*.safetensors`, etc.

## Promotion / Integration Rules
- Experiments should land here only after they have: (a) a smoke test, (b) CI coverage, (c) documented entry points.
- Cross-repo coordination: document shared contracts in `docs/` and reference paths explicitly.

## Status Checks to Expect
- Ruff lint, Black check, `run_tests.py` in CI.
- Additional security/quality workflows may run (see `.github/workflows/`).

## Contacts / Agents
- Copilot: operator for scoped edits and mechanical changes.
- Claude (architect): plans, decisions, and summaries; must cite paths.
- ChatDev/Ollama: optional for ideation; results get reviewed and ported explicitly.

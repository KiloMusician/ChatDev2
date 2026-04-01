# NuSyQ-Hub — Operations

## Daily Startup (local)
1) Activate env: `python -m venv .venv` → activate.
2) Install deps: `python -m pip install --upgrade pip` and `python -m pip install -r dev-requirements.txt`.
3) Quick health: `python -m compileall src` (import sanity).
4) Lint/format check: `python -m ruff .`; `python -m black --check .`.
5) Tests: `python run_tests.py` (or `pytest -q` if scoped).
6) `git status -sb` to ensure clean working tree before edits.

## Pre-commit Checklist
- Scope confirmed (paths/files).
- No secrets in working tree (`config/secrets.*`, `.env*`, `settings.local.*`, tokens).
- Runtime artifacts not staged (`logs/`, `Reports/`, `State/`, caches).
- Verification run (lint/tests) or noted if intentionally deferred.
- Conventional Commit message with verification note.

## CI Expectations
- `ci.yml`: ruff, black --check, run_tests.py on ubuntu/windows, optional OTEL deps.
- Additional workflows in `.github/workflows/` may run security/quality scans.
- Keep CI fast: prefer smoke-level checks over heavyweight end-to-end runs.

## Secrets Handling
- Real secrets live outside git: use environment variables or local `config/secrets.*` not tracked.
- Templates only: ensure placeholder values that do not resemble real keys (avoid `sk-...`).
- Before sharing logs or configs, scrub tokens/URLs.

## Logging & Artifacts
- Runtime logs and reports should remain untracked. If a log/summary is worth keeping, move it into `docs/` as a curated artifact.
- Avoid committing `logs/`, `Reports/`, `State/`, `ops/receipts/`, caches.

## Branch / PR Safety
- Default branch: `master`. Use feature branches; keep 1–3 commits per change set.
- Respect branch protection (PRs + status checks). Avoid force-push to protected branches without explicit approval.

## Recovery / Troubleshooting
- If imports break: `python -m compileall src` to locate syntax/import issues.
- If deps drift: reinstall from `dev-requirements.txt`.
- If CI fails: reproduce locally using the same commands as workflows; check `.github/workflows/ci.yml` steps.

## Release / Integration Notes
- Promote experimental work only after smoke tests + docs updates.
- Document any new entry point or integration in `SYSTEM_MAP.md` and `ROUTING_RULES.md`.

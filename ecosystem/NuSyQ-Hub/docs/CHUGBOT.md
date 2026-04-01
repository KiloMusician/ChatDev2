# Chug-Bot — Automated Maintenance Runner

Chug-Bot is the repository's automation coordinator. It runs the following tasks (via `scripts/chugbot_runner.py` or the scheduled GitHub Actions workflow `chugbot-ci.yml`):

- Programmatic import checks (`scripts/run_repo_import_checks.py`) — fast in-process checks that skip heavy optional deps.
- `apply_missing_inits.py` dry-run to detect package markers to add.
- `generate_phase1_plan.py` to produce `config/PHASE1_FOCUS_PLAN.json` for ZETA Phase 1 focus.
- `triage_import_failures.py` to convert import failures into PUs (file: `data/unified_pu_queue.json`).

How to run locally

```bash
python scripts/chugbot_runner.py
```

CI

- The workflow `.github/workflows/chugbot-ci.yml` runs unit tests, import checks, dry-run `apply_missing_inits.py`, generates PHASE1 plan, and uploads reports as artifacts.

Notes

- Import checks are conservative: heavy ML modules are skipped by default to make runs fast and reliable in CI.
- The triage step is intentionally conservative and writes queued PUs for manual review.
- Add scheduled runs via GitHub Actions (already configured to run every 6 hours).

Contributions and follow-ups

- If import failures are numerous, consider adding dependency stubs in `stubs/` or adding optional dependency guards.
- Consider automating PR creation for small fixes (e.g., adding package markers) when safe.

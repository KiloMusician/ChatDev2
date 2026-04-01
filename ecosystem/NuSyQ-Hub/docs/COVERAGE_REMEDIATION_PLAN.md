Coverage remediation plan (short-term)

## Goal

Bring the repository CI to a stable, incremental coverage improvement plan
without blocking local development.

## Short-term actions (this file + small scripts)

1. Import-only smoke tests

   - Add lightweight tests that simply import top-level modules/packages to
     catch import-time errors. These tests are fast and increase baseline
     coverage by marking modules as executed.
   - Suggested location: `tests/import_smoke/test_imports_*.py`

2. Coverage omit rules

   - Add `coverage` omit patterns in `pytest.ini` (or `.coveragerc`) for
     third-party, generated, or vendored files that should not count toward
     coverage.
   - Suggested patterns: `*/.venv/*`, `*/.mypy_cache/*`, `**/generated/*`,
     `**/third_party/*`

3. CI job split

   - Create two CI jobs:
     - `quick-smoke`: runs import-smoke tests and unit smoke tests (fast, should
       run on every push and PR) — does NOT enforce full coverage.
     - `full-tests`: runs full pytest + coverage and enforces `fail-under`
       threshold (runs nightly or as a blocking gate on release branches).

4. Metric-driven rollout
   - Lower the `fail-under` coverage threshold temporarily if needed to allow
     PRs to land while increasing test coverage gradually.
   - Track per-package coverage and prioritize writing tests for high-impact
     modules (or modules with recent churn).

## Medium-term actions

- Add a coverage report job that uploads metrics (e.g., to Codecov or a simple
  artifact) to monitor progress over time.
- Add tests that assert critical flows and increase branch/line coverage for
  core orchestration and integration modules.
- Replace broad end-to-end tests with smaller unit tests where practical.

## How you can help now

- I can scaffold an import-smoke test suite and a sample CI job template. Tell
  me if you want me to create `tests/import_smoke/test_imports_core.py` and a
  GitHub Actions workflow file `/.github/workflows/quick-smoke.yml`.

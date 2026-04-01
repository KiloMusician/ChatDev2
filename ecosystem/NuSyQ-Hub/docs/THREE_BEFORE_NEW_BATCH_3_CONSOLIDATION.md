# Three Before New: Batch 3 Consolidation – Test Runners

**Date:** 2025-12-28  
**Target:** Test runners and pytest wrappers  
**Discovery:**
`python scripts/find_existing_tool.py --capability "test runner" --max-results 20`

## Tool Inventory (20 found)

### Tier 1 · Canonical/High-Value (KEEP)

1. `scripts/lint_test_check.py` – End-to-end lint+pytest gate (CI-quality)
2. `scripts/friendly_test_runner.py` – Pytest wrapper with diagnostics and quick
   mode
3. `scripts/run_tests_quick.py` – Coverage-free quick runner for local iteration
4. `tests/test_ml_modules.py` + `scripts/run_tests_ml.py` (if present) –
   domain-specific
5. `src/diagnostics/smoke_test_runner.py` – AST/import/syntax smoke harness for
   files

### Tier 2 · Context/Integration (KEEP)

6. `scripts/fix_pytest_capture.py` – pytest capture helper
7. `scripts/generate_sns_tests.py` – test generator (SNS domain)
8. `scripts/maintenance_runner.py` – maintenance hooks
9. `scripts/run_targeted_tests.py` – targeted subset runner
10. `scripts/run_tests_intelligent.py` – heuristic/intelligent selector
11. `scripts/run_tests_safely.py` – safety wrapper
12. `scripts/wsl_test_runner.ps1` – WSL bridge
13. `src/diagnostics/comprehensive_test_runner.py` – legacy omnibus audit

### Tier 3 · Redundant/Overlapping (CANDIDATES TO MERGE/RETIRE)

14. `scripts/run_tests_quick.py` (overlaps Friendly quick mode) – keep behavior,
    merge into canonical
15. `scripts/friendly_test_runner.py` (main candidate canonical) – expand modes
16. `src/diagnostics/smoke_test_runner.py` (file-level smoke) – expose as
    subcommand instead of standalone
17. `scripts/run_tests_intelligent.py` / `run_targeted_tests.py` – unify as
    "smart selection" mode
18. `src/diagnostics/comprehensive_test_runner.py` – audit-style, likely retire
    after porting any unique checks
19. `scripts/run_tests_safely.py` – wrap into safety mode (fail-fast, cleanup)
20. `scripts/wsl_test_runner.ps1` – integrate as `--backend wsl` option; keep
    script as shim only if needed

## Consolidation Plan

### Phase 1 · Design (this doc)

- Canonical entrypoint: **`scripts/friendly_test_runner.py`** extended to cover
  all modes.
- Provide subcommands/flags instead of multiple files:
  `--mode quick|full|targeted|smart|smoke|ci` and `--backend local|wsl`.
- Preserve quick behavior from `run_tests_quick.py` (override addopts, disable
  coverage) as `--mode quick`.
- Expose smoke runner (`smoke_test_runner.py`) via `--mode smoke <path>`.
- Keep `lint_test_check.py` as the CI/quality pipeline; hook it as `--mode ci`
  passthrough.
- Add `--select` (patterns) and `--list-modes` for discoverability; log runs via
  `src.utils.test_run_registry` if available.

### Phase 2 · Implementation Targets

1. **Unify quick & friendly:** move quick logic into Friendly `--mode quick`;
   deprecate `run_tests_quick.py` (leave shim calling canonical).
2. **Add smoke mode:** call `SmokeTestRunner` for file(s) or glob; return
   non-zero if any fail.
3. **Targeted/Smart mode:** port minimal useful heuristics from
   `run_tests_intelligent.py` / `run_targeted_tests.py` (e.g., changed files →
   tests mapping). If too heavy, keep original files but route via canonical.
4. **CI mode:** thin wrapper that runs `scripts/lint_test_check.py` or
   equivalent pipeline.
5. **Backend flag:** allow `--backend wsl` to shell out to existing PowerShell
   shim; otherwise default local.
6. **Safety:** include `--fail-fast`, `--max-fail`, and timeout passthrough.
7. **Telemetry:** preserve diagnostic hints from Friendly runner; continue
   registry logging when available.

### Phase 3 · Migration & Cleanup

- Update references (tasks, docs, README snippets) to use
  `python scripts/friendly_test_runner.py --mode <...>`.
- Keep small shims (`run_tests_quick.py`, `wsl_test_runner.ps1`) but rewrite to
  delegate; mark deprecated in headers.
- Retire/absorb `src/diagnostics/comprehensive_test_runner.py` after verifying
  no unique checks are lost.
- Keep domain-specific generators/helpers (SNS, maintenance) untouched.
- Log consolidation to quest system; run `scripts/lint_test_check.py` and a
  representative `--mode quick` smoke.

## Expected Impact

- Reduce overlapping runners from ~8 to 1 canonical entrypoint + 1-2 shims.
- Standardize UX (`--mode`), improve discoverability, and ensure quick local
  runs bypass coverage safely.
- Preserve Testing Chamber smoke capability while making it accessible from the
  canonical runner.

## Status

- ✅ Discovery complete; design plan drafted (this document).
- ✅ Canonical runner updated: `scripts/friendly_test_runner.py` now exposes
  modes `full|quick|targeted|smart|smoke|ci`, preserves diagnostics, supports
  fail-fast/max-fail, logs runs, delegates targeted → `run_targeted_tests.py`,
  and can invoke pytest via the WSL backend when requested.
- ✅ Shims created/updated: `run_tests_quick.py`, `run_tests_safely.py`, and
  `src/diagnostics/comprehensive_test_runner.py` now delegate to the canonical
  runner, with deprecation warnings.
- ✅ References migrated: README.md, fix_pytest_capture.py,
  quick_fix_workflow.py all updated to point to canonical friendly_test_runner.
- ✅ Quick-run docs (DEV_QUICK_RUN.md) updated.
- Next: Log quest entry and run validation checks.

Developer Quick Run & Testing

This document explains the project's recommended local testing workflow so you
can iterate quickly without tripping the global coverage enforcement used in CI.

## Quick-run helper

Use `scripts/friendly_test_runner.py --mode quick` for rapid local iteration. It
runs `pytest` in a subprocess while overriding `pytest.ini` addopts and
disabling the coverage plugin so local runs don't fail because of the
repository's coverage gate. The legacy `scripts/run_tests_quick.py` remains as a
shim that delegates to this canonical runner.

Recommended usage (PowerShell / pwsh):

```powershell
# Run the default smoke test
python scripts/friendly_test_runner.py --mode quick -q tests/test_quantum_import.py

# Run quick mode on a specific test file
python scripts/friendly_test_runner.py --mode quick -q tests/test_my_module.py::test_my_case

# Run full local pytest (this will apply coverage settings from pytest.ini)
python -m pytest -q
```

## Friendly test-runner

`scripts/friendly_test_runner.py` provides a human-friendly wrapper that runs
pytest, captures output, and prints actionable diagnostics for common failures
such as:

- Coverage parse warnings ("Couldn't parse Python file ... (couldnt-parse)")
- SyntaxError traces with file+line information
- Coverage fail-under failures

Usage:

```powershell
# Quick mode (no coverage enforcement)
python scripts/friendly_test_runner.py --mode quick tests/test_quantum_import.py

# Full mode (normal pytest behavior)
python scripts/friendly_test_runner.py tests/test_quantum_import.py
```

If a "couldn't parse" warning is detected, the runner will: 1) suggest running
`python -m py_compile <file>` and 2) automatically invoke
`scripts/check_file_encoding.py <file>` to catch null bytes or encoding issues.

## Why this exists

CI enforces a coverage threshold which is valuable for long-term quality, but it
blocks local rapid iteration when you only need to run a single smoke test. The
quick-run helper and friendly runner let you iterate locally while keeping the
stricter gate in CI.

## Notes

- If you need to reproduce the CI run locally, run `python -m pytest` (this will
  use the pytest.ini settings).
- The project's CI should remain the source of truth for coverage gating; local
  runs should prefer quick-mode for development speed.

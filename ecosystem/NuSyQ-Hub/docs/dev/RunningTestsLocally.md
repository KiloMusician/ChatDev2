# Running Tests Locally (fast, focused)

This repo enforces coverage and other strict settings in CI. For quick local
iterations or focused test runs, override pytest options without changing any
tracked config files.

## TL;DR

- Use the PYTEST_ADDOPTS environment variable to override `pytest.ini` addopts.
- Keep CI strict by not editing `pytest.ini`.

## Examples

Run a single test file with minimal flags:

```powershell
# Windows PowerShell
$env:PYTEST_ADDOPTS="-q -x"; pytest tests/system_testing/test_enhanced_placeholders.py
```

Run a specific test and show print output:

```powershell
$env:PYTEST_ADDOPTS="-q -s"; pytest tests/llm_testing/test_ollama_integration.py::test_small_model_responds
```

Restore defaults for the session:

```powershell
Remove-Item Env:PYTEST_ADDOPTS
```

## Why this works

Pytest merges options from multiple sources. Options from the `PYTEST_ADDOPTS`
environment variable are appended and can effectively bypass or override strict
settings like coverage addopts for local developer productivity. In CI, the
variable is not set and the repo-wide defaults apply.

## Notes

- If tests rely on environment services (e.g., Ollama), prefer small local
  models and reasonable timeouts. Tests should skip gracefully when infra isn’t
  available.
- Use `scripts/lint_test_check.py` before pushing to run the full set (Black,
  Ruff, pytest with coverage).

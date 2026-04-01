# PyTest Usage Guide

`pytest` and its async plugin (`pytest-asyncio`) sit at the top of our dependency inventory because they form the primary validation loop for NuSyQ’s agent orchestration, ChatDev bridges, and ML integrations. This guide connects the existing `pytest.ini` configuration with the async-heavy workflows we run, ensuring the plugin is exercised and each capability earns its place.

## Configuration highlights (`pytest.ini`)

- **Discovery patterns:** `test_*.py` and `*_test.py` in `tests/`, collecting classes that begin with `Test` and functions that begin with `test_`.
- **Coverage instrumentation:** `--cov`, `--cov-report` (term/html/xml) plus `--cov-fail-under=30` generate enforcement-friendly reports.
- **Markers:** dozens of markers (`integration`, `chatdev`, `ollama`, `asyncio`, `ml_heavy`, etc.) let us gate suites by subsystem, external dependency, or performance tier.
- **Logging & asyncio:** `log_cli=true`, `asyncio_mode=auto`, and `pythonpath=src` ensure async tests run reliably on Windows/macOS while capturing logs in real time.
- **Async plugin:** `pytest-asyncio` handles the `@pytest.mark.asyncio` decorators used throughout tests (`tests/`, `tests/integration`, and scripts like `scripts/generate_sns_tests.py`), so agent scheduling, ChatDev integrations, and SNS workflows can await/call loops without extra boilerplate.
- **Warnings filter:** Deprecation/Future warnings are suppressed to keep output focused.

## Running pytest

Use the root command:

```bash
python -m pytest
```

Targeted runs:

- Unit path:
  ```bash
  python -m pytest -m unit
  ```
- ChatDev/SimulatedVerse integration:
  ```bash
  python -m pytest -m "chatdev or simulatedverse"
  ```
- ML/external service skip:
  ```bash
  python -m pytest -m "not ml_heavy and not requires_external_service"
  ```
- Explicit async run:
  ```bash
  python -m pytest tests/test_agent_protocol.py -m asyncio
  ```

## Async coverage & plugin hygiene

1. Keep `pytest-asyncio` up to date because dozens of async marks and fixtures rely on it; if a new async marker is added, ensure the plugin version can handle it before gating tests.  
2. Async tests already log cycles via `asyncio_mode=auto`; if we add custom loops (e.g., for agent orchestration), wrap them with `pytest.mark.asyncio` to preserve compatibility.  
3. Coverage reports already run with `--cov-report=term-missing`; add new modules under `tests/` to keep coverage metrics growing.

## Automation hooks & auditor integration

- `python -m pytest` powers automation scripts like `scripts/execute_remaining_pus.py` and the modernization audit; the CLI now accepts `--mode core` from the updated auditor so we can run Hub-centric suites before enabling warehouse projects.  
- When building the user-facing app or VS Code extension, expose “Run pytest” buttons that call this command; they will automatically include `pytest-asyncio` and the async markers we already rely on.
- Document additional async-heavy markers in `pytest.ini` (e.g., `ai_backend_required`, `simulatedverse`) whenever new async tests are added so the plugin stays exercised.

## Next actions

* Keep `pytest`/`pytest-asyncio` at the top of the inventory by exercising async markers in PRs (especially `integration`, `chatdev`, `ollama`).  
* Extend CI to run `python scripts/comprehensive_modernization_audit.py --mode core` before `pytest` so warehouse noise stays muted unless explicitly enabled.  
* Add any new async tests to `tests/` with the correct markers and coverage annotations so the dependency stays justified.

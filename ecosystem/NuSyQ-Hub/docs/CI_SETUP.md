CI Setup recommendations

## Purpose

Short instructions to make Continuous Integration (GitHub Actions or other CI)
run the test-suite reliably.

## Steps

1. Install dev dependencies

Ensure the CI runner installs the developer requirements before running tests.
Example (PowerShell on Windows runners):

```powershell
python -m pip install -U pip
pip install -r dev-requirements.txt
```

On Linux/macOS runners use the same `pip install -r dev-requirements.txt` step.

2. Run tests

Use the repository test runner which ensures PYTHONPATH includes `src/` and
loads necessary pytest plugins:

```powershell
python run_tests.py
```

Or run pytest directly after setting PYTHONPATH:

```powershell
$env:PYTHONPATH = "${PWD}\src"
pytest -q
```

3. Linting and formatting (optional but recommended)

Run `ruff` and `black` as part of CI:

```powershell
# check only
ruff .
black --check .
# or auto-fix where appropriate
ruff . --fix
black .
```

## Notes

- The repository includes a small `conftest.py` shim that will execute async
  test coroutines even if `pytest-asyncio` is not installed; however it's
  recommended to install `pytest-asyncio` in CI for a consistent plugin-driven
  experience.
- For subprocess-based tests that invoke `python -m copilot.bridge_cli`, ensure
  the runner uses the repository root as working directory (the repo includes a
  minimal `copilot` shim to help with such subprocess invocations).
- If you switch to an installable package layout (setup.py/pyproject), prefer
  installing the package into the venv in CI (`pip install -e .`) and run tests
  against the installed package rather than relying on PYTHONPATH.

## Contact

If you want, I can add a GitHub Actions workflow file
(`.github/workflows/ci.yml`) that installs `dev-requirements.txt`, runs `ruff`
and `black --check`, and then runs the test suite. Let me know if you want that
next.

# `pytest-cov` Coverage Practice

`pytest-cov` (the fourth dependency in our inventory list) is what turns `pytest` runs into meaningful metrics. This doc outlines how we already use it and what to do when expanding our test surface.

## Current setup

- `pytest.ini` enables coverage (`--cov`, `--cov-report=term-missing`, `--cov-report=html:htmlcov`, `--cov-report=xml`) so every `python -m pytest` run produces terminal, HTML, and XML artifacts.  
- The `--cov-fail-under=30` flag enforces a minimum coverage baseline, which we raise over time as we add more tests.  
- Coverage files live in `htmlcov/` and `coverage.xml`, making them easy to consume for automation (e.g., `scripts/execute_remaining_pus.py` or external dashboards).

## Recommended workflows

1. **Before pushing** – run `python -m pytest --maxfail=1` to see coverage quickly, then `python -m pytest` to regenerate the HTML/XML reports for the new baseline.  
2. **Selective directories** – if you’re working in a new module (say `src/automation`), run `python -m pytest --cov=src/automation` to highlight its coverage impact.  
3. **Coverage summary** – `coverage.xml` is the artifact used by dashboards or CI; ensure the file gets overwritten every time and is included in release reports if we publish stats.

## Automation hooks

- The auditor and automation scripts already rely on the coverage reports produced by `pytest-cov`. When you run `scripts/comprehensive_modernization_audit.py` after cleaning up placeholders, it assumes the subsequent `python -m pytest` run has updated `coverage.xml`, so keep these files up to date.  
- Our future app/extension’s “Run pytest” command should include `--cov` flags so the coverage status remains live even for GUI-driven runs.

## Next actions

* Use the `coverage` files as part of PR gating; inspect `coverage.xml` or `htmlcov/index.html` before marking modernization tasks as done.  
* Raise `--cov-fail-under=` gradually as `docs/COMPREHENSIVE_MODERNIZATION_AUDIT.md` improves.  
* Keep `pytest-cov` dependencies synchronized with `coverage` itself (via `requirements`/`pyproject`), and rerun `scripts/dependency_inventory.py` whenever we adjust coverage tooling to keep the inventory truthful.

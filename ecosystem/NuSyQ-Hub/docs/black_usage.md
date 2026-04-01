# Black Formatter Usage

`black` (the second dependency on the inventory after `pytest`) is the formatter that keeps NuSyQ-Hub’s Python style consistent. The repo already enforces it through multiple tooling layers, and this document summarizes how we exercise it so the dependency stays indispensable.

## Where black runs

1. **Pre-commit hook** – `.pre-commit-config.yaml` specifies `black==24.3.0` with `--line-length=100`, so the formatter runs automatically during commits on any changed Python files (excluding archives, documentation trees, and node_modules).  
2. **Manual CLI** – `src/main.py` lists `black` under its `quality` mode, executing `black src/ tests/` (see `_quality_resolution_mode`). This lets builds or manual runs apply the formatter programmatically or via the future app extension’s “quality mode” button.  
3. **CI/dev requirements** – `dev-requirements.txt`, `requirements-dev.txt`, and `projects’` templates already pin `black>=24.0.0`, ensuring developer environments can install it easily.

## Operating black

Use the consistent line length:

```bash
black --line-length=100 src/ tests/
```

Or run the full quality flow:

```bash
python src/main.py --mode=quality
```

This mode also chains `black` with `isort`/`autopep8` and logs the results. The CLI branch ensures formatting can be automated across agents anytime we extend the app.

## Advanced flow

- When grading a warehouse project, run the formatter with `--include` to restrict scope: `black --line-length=100 ChatDev/WareHouse/pvz_THUNLPDemo_2024`.  
- After hitting `--mode core` with the auditor, consider running `black src/ tests/` before committing so the Hub files keep consistent style even while warehouse work is gated.

## Next actions

1. Keep `.pre-commit-config.yaml` thresholds aligned with our formatting goals and bump `black` when we need new features (e.g., pattern matching improvements).  
2. Document any formatting exceptions in `docs/pytest_usage.md` or `docs/Black_Exceptions.md` if a file must stay unformatted for downstream compatibility.  
3. When building the user-facing app or extension, add a “run formatter” action that calls `src/main.py --mode=quality` so the same CLI driver controls formatting across environments.

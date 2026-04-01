# Contributing to NuSyQ-Hub

Thank you for helping cultivate this evolving ecosystem! Please follow these guidelines to ensure clarity, maintainability, and continuous improvement.

## Development Setup

```bash
# Option A: Automatic bootstrap (recommended)
./scripts/bootstrap_dev_env.sh

# Option B: Manual setup
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e "[.dev]"  # or at minimum: pip install black ruff flake8 mypy
pre-commit install
pre-commit run --files <changed_files>
```

## Node & SonarLint

If you plan to run SonarLint or Node-based analysis locally, install Node (>=20.12.0).

Preferred (system-wide):

```bash
# Debian/Ubuntu (requires sudo)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

Or use `nvm` for per-user installs:

```bash
# install nvm if not present
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
# reload shell, then:
source ~/.nvm/nvm.sh
nvm install 20

# After Node is installed, copy the template workspace settings and adjust the node path if needed
cp .vscode/settings.template.json .vscode/settings.json
```

After the hooks pass, run tests with `pytest`.

## Workflow
- Fork the repository and create a feature branch for your changes.
- Use atomic, well-documented commits.
- Reference the ZETA_PROGRESS_TRACKER and relevant checklists for task status.
- Run `python scripts/lint_test_check.py` before submitting a PR.
- Ensure all code is formatted (black), linted (ruff/flake8), and tested (pytest).
- Document new features and update CHANGELOG.md.

## Best Practices
- Prefer modular, readable, and well-documented code.
- Use type hints and Google-style docstrings for all public functions and classes.
- Remove dead/commented code and avoid bloat.
- Use pathlib for file operations.
- Parameterize paths/configs; avoid hard-coded values.
- Use environment variables for secrets and API keys.
- Add or update tests for all new/changed functionality.
- Reference and update docs/Checklists and ZETA_PROGRESS_TRACKER.json as needed.

## Navigation & Documentation
- Use scripts/project_navigator.py for directory/context navigation.
- Keep documentation up to date in docs/ and README.md.
- Leverage and enhance Copilot/consciousness bridge integrations.

## Performance & Optimization
- Profile and optimize code for speed and memory where possible.
- Remove or consolidate redundant modules.
- Document performance improvements in PRs and CHANGELOG.md.

## Advanced AI Integration
- Use and extend Copilot/AI orchestration patterns.
- Maintain consciousness-aware tagging and context propagation.
- Reference quest logs and progress trackers for context.

---
For questions, open an issue or consult the docs/ directory.

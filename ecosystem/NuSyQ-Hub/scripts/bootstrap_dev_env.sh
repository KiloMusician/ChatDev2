#!/usr/bin/env bash
set -euo pipefail

echo "🛠️  Bootstrapping NuSyQ-Hub dev environment..."

# Prefer an existing python3 >= 3.11 (on Windows, `python` is often the only command)
PYTHON=""
for py_candidate in python3 python py; do
  if command -v "$py_candidate" >/dev/null 2>&1; then
    if "$py_candidate" -c 'import sys; sys.exit(0) if sys.version_info >= (3,11) else sys.exit(1)' 2>/dev/null; then
      PYTHON="$py_candidate"
      echo "Found suitable python: $($PYTHON --version)"
      break
    fi
  fi
done

# Try pyenv if no suitable system python found
if [ -z "${PYTHON}" ]; then
  if command -v pyenv >/dev/null 2>&1; then
    PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
    echo "pyenv detected at $PYENV_ROOT. Installing/activating Python 3.11.6 (recommended)..."
    pyenv install -s 3.11.6
    pyenv local 3.11.6
    PYTHON=python3
  else
    echo "No suitable Python (>=3.11) found and pyenv is not installed." >&2
    echo "Install pyenv (https://github.com/pyenv/pyenv#installation) or install Python 3.11+ and re-run this script." >&2
    exit 1
  fi
fi

# Create venv
echo "Creating virtual environment in .venv..."
$PYTHON -m venv .venv
# shellcheck source=/dev/null
if [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate  # Windows (Git Bash / MINGW64)
elif [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate      # Linux / macOS
else
  echo "❌ Could not find venv activation script" >&2
  exit 1
fi

echo "Upgrading pip and installing dev dependencies (editable install)..."
python -m pip install --upgrade pip
# Try full dev extras; fallback to minimal recommended tools
if ! python -m pip install -e "[dev]"; then
  echo "Editable dev install failed; installing minimal tools (black, ruff, flake8, mypy)"
  python -m pip install black ruff flake8 mypy
fi

echo "Installing and enabling git hooks..."
if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install || true
else
  echo "pre-commit not found; installing pre-commit"
  python -m pip install pre-commit
  pre-commit install || true
fi

cat <<'DOC'
✅ Bootstrap complete.
Next steps:
  1. Activate the virtualenv:
     Linux/macOS: source .venv/bin/activate
     Windows:     source .venv/Scripts/activate  (Git Bash)
                  .venv\Scripts\activate.bat      (cmd)
                  .venv\Scripts\Activate.ps1      (PowerShell)
  2. Run `pre-commit run --files <changed_files>` to verify
  3. Run `pytest` to check tests
DOC

exit 0

#!/usr/bin/env bash
# Local CI mirror for NuSyQ-Hub — run before agents merge changes
set -euo pipefail
echo "Running local CI mirror: lint -> tests"
echo "1. Run ruff (if installed)"
if command -v ruff >/dev/null 2>&1; then
  ruff check . || true
else
  echo "  ruff not found — skipping"
fi

echo "2. Run pytest (fast filter)"
python -m pytest -q -k 'not e2e and not llm_testing'

echo "Local CI completed"

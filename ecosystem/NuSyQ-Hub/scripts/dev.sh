#!/usr/bin/env bash
TASK=${1:-help}

case "$TASK" in
  install)
    echo "Create venv manually and run: pip install -r requirements.txt"
    ;;
  install-dev)
    pip install -e "[dev]" || true
    ;;
  lint)
    command -v ruff >/dev/null && ruff . || echo "ruff not found, skipping"
    command -v black >/dev/null && black --check . || echo "black not found, skipping"
    ;;
  test)
    pytest -q
    ;;
  scan)
    python -m src.tools.maze_solver . --max-depth 6 --progress
    ;;
  orchestrator)
    export PYTHONPATH="$(pwd)"
    python -u scripts/start_multi_ai_orchestrator.py
    ;;
  smoke)
    export PYTHONPATH="$(pwd)"
    python -u scripts/submit_orchestrator_test_task.py
    ;;
  *)
    echo "Usage: scripts/dev.sh <install|install-dev|lint|test|scan|orchestrator|smoke>"
    ;;
esac

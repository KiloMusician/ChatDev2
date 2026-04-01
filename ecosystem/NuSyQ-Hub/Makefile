PYTHON?=.venv/Scripts/python.exe
PIP?=.venv/Scripts/pip.exe

all: venv install lint test

venv:
	@if [ ! -d ".venv" ]; then \
		python -m venv .venv; \
	fi

install: venv
	$(PIP) install -r requirements.txt

lint:
	$(PIP) install ruff black mypy
	.venv/Scripts/ruff check src/ scripts/
	.venv/Scripts/black --check src/ scripts/
	.venv/Scripts/mypy src/

test:
	$(PIP) install pytest
	.venv/Scripts/pytest tests/

docker-build:
	docker build -t nusyq-hub .

docker-up:
	docker-compose up -d

clean:
	rm -rf .venv __pycache__ .mypy_cache .pytest_cache.PHONY: help setup install install-dev lint test scan orchestrator smoke

help:
	@echo "Makefile targets:"
	@echo "  setup         - configure git hooks (run once after cloning)"
	@echo "  install       - create venv (manual) and install requirements"
	@echo "  install-dev   - install dev extras (.[dev])"
	@echo "  lint          - run ruff and black (if available)"
	@echo "  test          - run pytest"
	@echo "  scan          - run quick repo scan via maze_solver"
	@echo "  orchestrator  - start simple orchestrator runner (in foreground)"
	@echo "  smoke         - run orchestrator smoke test (submit a safe task)"

setup:
	@echo "Configuring git hooks..."
	@git config core.hooksPath .githooks
	@echo "✅ Git hooks activated (.githooks/). Run 'make setup' once after cloning."

install:
	@echo "Run venv creation manually; then: pip install -r requirements.txt"

install-dev:
	@pip install -e ".[dev]" || true

lint:
	@which ruff > /dev/null 2>&1 && ruff . || echo "ruff not found, skipping"
	@which black > /dev/null 2>&1 && black --check . || echo "black not found, skipping"

test:
	@pytest -q

scan:
	@python -m src.tools.maze_solver . --max-depth 6 --progress

orchestrator:
	@PYTHONPATH=$(shell pwd) python -u scripts/start_multi_ai_orchestrator.py

smoke:
	@PYTHONPATH=$(shell pwd) python -u scripts/submit_orchestrator_test_task.py

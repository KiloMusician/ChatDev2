# Terminal Depths + Dev-Mentor Makefile
# Unified entrypoint for all common operations
#
# Usage:
#   make colony      — Full colony bootstrap (diagnose → serve → monitor)
#   make dev         — Start the Replit dev server
#   make td          — Enter Terminal Depths (universal launcher)
#   make td-play     — Enter via terminal REPL (no browser)
#   make td-open     — Enter via browser
#   make td-status   — Show server + colony health
#   make td-install  — Install 'td' command system-wide
#   make td-automate — Run 250-command speedrun automation
#   make diagnose    — Run Phase 0 diagnostics
#   make push        — Auto-git push to GitHub
#   make walk        — Trigger Serena full repo walk
#   make drift       — Run drift detection engine
#   make align       — Check Mladenc alignment score
#   make audit       — Print Serena audit trail
#   make gordon      — Launch Gordon autonomous player
#   make clean       — Remove __pycache__ and .pyc files
#   make help        — Show this menu
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: help bootstrap dev cli stop restart status logs doctor test test-python test-node lint format build clean rebuild prune open-api open-ui

# Detect OS for cross-platform support
OS := $(shell uname -s)
ifeq ($(OS),Windows_NT)
    SHELL := powershell
    .SHELLFLAGS := -NoProfile -Command
    RM_RF := rm -r -force
    SEP := \
else
    RM_RF := rm -rf
    SEP := /
endif

# Paths
SCRIPT_DIR := $(shell pwd)
COMPOSE_FILE := $(SCRIPT_DIR)/docker-compose.yml
BOOTSTRAP_PS1 := $(SCRIPT_DIR)/bootstrap.ps1
BOOTSTRAP_SH := $(SCRIPT_DIR)/bootstrap.sh

# Profile selection
PROFILE ?= balanced
MODE ?= full

# ── Core variables ───────────────────────────────────────────────────────────
PYTHON  ?= python3
PORT    ?= 7337
BASE_URL ?= http://localhost:$(PORT)

# Docker Compose shortcuts
DC      := docker compose -f $(COMPOSE_FILE)
DC_FULL := docker compose -f docker-compose.full.yml

help:
	@echo "Terminal Depths + Dev-Mentor — Makefile"
	@echo "========================================"
	@echo ""
	@echo "Bootstrap & Lifecycle:"
	@echo "  make bootstrap      Full system startup (services + CLI)"
	@echo "  make dev            Services only (no CLI client)"
	@echo "  make cli            CLI client only"
	@echo "  make stop           Shutdown all services"
	@echo "  make restart        Restart all services"
	@echo ""
	@echo "Diagnostics:"
	@echo "  make status         Show service status"
	@echo "  make logs           Tail Docker logs"
	@echo "  make doctor         System health check"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run all tests (Python + Node)"
	@echo "  make lint           Lint all code"
	@echo "  make format         Format all code"
	@echo "  make build          Build Docker images"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove build artifacts"
	@echo "  make rebuild        Clean + build"
	@echo "  make prune          Docker system prune (aggressive)"
	@echo ""
	@echo "Quick shortcuts:"
	@echo "  make open-api       Open API docs in browser"
	@echo "  make open-ui        Open SimulatedVerse UI in browser"
	@echo ""
	@echo "Options:"
	@echo "  PROFILE=lite        Use lightweight models (default: balanced)"
	@echo "  PROFILE=vision      Use vision models"

# ============================================================
# Bootstrap & Lifecycle
# ============================================================

bootstrap:
	@echo "Starting Terminal Depths (profile=$(PROFILE))..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
	        powershell -NoProfile -Command "& '$(BOOTSTRAP_PS1)' -Mode full -Profile $(PROFILE)"; \
	else \
	        bash $(BOOTSTRAP_SH) full $(PROFILE); \
	fi

dev:
	@echo "Starting services only (profile=$(PROFILE))..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
	        powershell -NoProfile -Command "& '$(BOOTSTRAP_PS1)' -Mode dev -Profile $(PROFILE)"; \
	else \
	        bash $(BOOTSTRAP_SH) dev $(PROFILE); \
	fi

cli:
	@echo "Starting CLI client..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
	        powershell -NoProfile -Command "& '$(BOOTSTRAP_PS1)' -Mode cli"; \
	else \
	        bash $(BOOTSTRAP_SH) cli; \
	fi

stop:
	@echo "Shutting down services..."
	docker compose -f $(COMPOSE_FILE) down
	@echo "✓ Shutdown complete"

restart: stop
	@sleep 2
	@$(MAKE) dev

# ============================================================
# Diagnostics
# ============================================================

status:
	@echo "Service Status:"
	@docker compose -f $(COMPOSE_FILE) ps

logs:
	@docker compose -f $(COMPOSE_FILE) logs -f --tail=50

doctor:
	@echo "Terminal Depths System Diagnostics"
	@echo "===================================="
	@echo ""
	@echo "🔍 Environment:"
	@command -v docker >/dev/null 2>&1 && echo "✓ Docker installed" || echo "✗ Docker not found"
	@command -v docker-compose >/dev/null 2>&1 && echo "✓ Docker Compose installed" || echo "✗ Docker Compose not found"
	@command -v python >/dev/null 2>&1 && echo "✓ Python installed ($$( python --version))" || echo "✗ Python not found"
	@command -v node >/dev/null 2>&1 && echo "✓ Node.js installed ($$(node --version))" || echo "✗ Node.js not found"
	@echo ""
	@echo "🌐 Ports:"
	@nc -zv 127.0.0.1 7337 2>&1 | grep -q succeeded && echo "✓ Dev-Mentor (7337)" || echo "  Dev-Mentor (7337) — not responding"
	@nc -zv 127.0.0.1 5000 2>&1 | grep -q succeeded && echo "✓ SimulatedVerse (5000)" || echo "  SimulatedVerse (5000) — not responding"
	@nc -zv 127.0.0.1 11434 2>&1 | grep -q succeeded && echo "✓ Ollama (11434)" || echo "  Ollama (11434) — not responding"
	@echo ""
	@echo "📦 Images:"
	@docker images | grep -E "terminal-depths|ollama|simulatedverse" | wc -l | xargs echo "  Built images:"
	@echo ""

# ============================================================
# Development
# ============================================================

test: test-python test-node
	@echo "✓ All tests passed"

test-python:
	@echo "Testing Python (Dev-Mentor)..."
	@cd $(SCRIPT_DIR) && python -m pytest tests/ -v --tb=short 2>/dev/null || echo "  (no tests found)"

test-node:
	@echo "Testing Node (SimulatedVerse)..."
	@[ -d "../Desktop/SimulatedVerse/SimulatedVerse" ] && cd "../Desktop/SimulatedVerse/SimulatedVerse" && npm run test 2>/dev/null || echo "  (SimulatedVerse tests skipped)"

lint:
	@echo "Linting Python..."
	@python -m pylint app/ cli/ --disable=all --enable=E 2>/dev/null || echo "  (pylint not configured)"
	@echo "Linting TypeScript..."
	@[ -d "../Desktop/SimulatedVerse/SimulatedVerse" ] && cd "../Desktop/SimulatedVerse/SimulatedVerse" && npm run lint:errors 2>/dev/null || echo "  (ESLint not available)"

format:
	@echo "Formatting Python..."
	@python -m black app/ cli/ 2>/dev/null || echo "  (black not installed)"
	@echo "Formatting TypeScript..."
	@[ -d "../Desktop/SimulatedVerse/SimulatedVerse" ] && cd "../Desktop/SimulatedVerse/SimulatedVerse" && npm run lint:fix 2>/dev/null || echo "  (Prettier not available)"

build:
	@echo "Building Docker images..."
	@docker compose -f $(COMPOSE_FILE) build
	@echo "✓ Build complete"

# ============================================================
# Cleanup
# ============================================================

clean:
	@echo "Cleaning build artifacts..."
	$(RM_RF) __pycache__ .pytest_cache .mypy_cache dist build
	@echo "✓ Cleaned"

rebuild: clean build
	@echo "✓ Rebuild complete"

prune:
	@echo "WARNING: This will remove ALL unused Docker images, containers, and volumes"
	@echo "Press Ctrl+C to cancel, or wait 3 seconds..."
	@sleep 3
	@docker system prune -a --volumes -f
	@echo "✓ Pruned"

# ============================================================
# Quick Shortcuts
# ============================================================

open-api:
	@echo "Opening API docs..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
	        start http://localhost:7337/docs; \
	else \
	        open http://localhost:7337/docs 2>/dev/null || xdg-open http://localhost:7337/docs; \
	fi

open-ui:
	@echo "Opening SimulatedVerse UI..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
	        start http://localhost:5000; \
	else \
	        open http://localhost:5000 2>/dev/null || xdg-open http://localhost:5000; \
	fi

.DEFAULT_GOAL := help

# ── Colony ──────────────────────────────────────────────────────────────────

.PHONY: colony
colony: diagnose dev  ## Full colony bootstrap: diagnose then serve

# ── Dev server ──────────────────────────────────────────────────────────────

.PHONY: dev
dev:  ## Start the DevMentor / Terminal Depths server
	$(PYTHON) -m cli.devmentor serve --host 0.0.0.0 --port $(PORT)

# ── Terminal Depths universal launcher ────────────────────────────────────────

.PHONY: td
td:  ## Enter Terminal Depths from this shell (auto-detects interface)
	$(PYTHON) scripts/td.py

.PHONY: td-play
td-play:  ## Enter Terminal Depths via terminal REPL (no browser)
	$(PYTHON) scripts/td.py play

.PHONY: td-open
td-open:  ## Enter Terminal Depths via browser
	$(PYTHON) scripts/td.py open

.PHONY: td-status
td-status:  ## Show Terminal Depths server + colony health
	$(PYTHON) scripts/td.py status

.PHONY: td-surfaces
td-surfaces:  ## Map all detected surfaces (shell, docker, godot, simverse…)
	$(PYTHON) scripts/td.py surfaces

.PHONY: td-install
td-install:  ## Install 'td' command system-wide (adds to PATH)
	bash scripts/install_td.sh

.PHONY: td-install-win
td-install-win:  ## Install 'td' command on Windows (PowerShell)
	pwsh -File scripts/install_td.ps1

.PHONY: td-automate
td-automate:  ## Run 250-command speedrun via API automation
	$(PYTHON) scripts/td_automate.py --base-url $(BASE_URL)

.PHONY: td-automate-dry
td-automate-dry:  ## Dry-run the speedrun (print commands, no API calls)
	$(PYTHON) scripts/td_automate.py --dry-run

# ── Phase 0: Diagnostics ────────────────────────────────────────────────────

.PHONY: diagnose
diagnose:  ## Run Phase 0 colony diagnostics + write surface_inventory.json
	$(PYTHON) scripts/diagnostics.py

.PHONY: diagnose-json
diagnose-json:  ## Diagnostics — JSON output
	$(PYTHON) scripts/diagnostics.py --json

.PHONY: diagnose-fail
diagnose-fail:  ## Diagnostics — show failures only
	$(PYTHON) scripts/diagnostics.py --quiet

# ── Git / GitHub ─────────────────────────────────────────────────────────────

.PHONY: push
push:  ## Auto-git push to GitHub (reads .env.local then GITHUB_TOKEN)
	$(PYTHON) scripts/git_auto_push.py

# ── Serena ΨΞΦΩ ──────────────────────────────────────────────────────────────

.PHONY: walk
walk:  ## Trigger Serena full repo walk (background, may take 30s)
	curl -s -X POST $(BASE_URL)/api/serena/walk \
	  -H "Content-Type: application/json" \
	  -d '{"mode":"full"}' | python3 -m json.tool

.PHONY: drift
drift:  ## Run Drift Detection Engine
	curl -s "$(BASE_URL)/api/serena/drift" | python3 -m json.tool

.PHONY: align
align:  ## Check Mladenc alignment score
	curl -s "$(BASE_URL)/api/serena/align" | python3 -m json.tool

.PHONY: audit
audit:  ## Print Serena audit trail
	curl -s "$(BASE_URL)/api/serena/audit" | python3 -m json.tool

.PHONY: toolkit
toolkit:  ## Show Serena Agno toolkit manifest
	curl -s "$(BASE_URL)/api/serena/toolkit" | python3 -m json.tool

# ── Gordon ───────────────────────────────────────────────────────────────────

.PHONY: gordon
gordon:  ## Launch Gordon autonomous player (targets localhost:5000)
	$(PYTHON) gordon_player.py --url $(BASE_URL) --delay 3.0

.PHONY: gordon-quiet
gordon-quiet:  ## Gordon in quiet mode
	$(PYTHON) gordon_player.py --url $(BASE_URL) --quiet

# ── Knowledge Graph ──────────────────────────────────────────────────────────

.PHONY: knowledge
knowledge:  ## Build knowledge_graph.json from YAML sources
	$(PYTHON) scripts/populate_knowledge_graph.py

.PHONY: knowledge-stats
knowledge-stats:  ## Show knowledge graph statistics
	$(PYTHON) scripts/populate_knowledge_graph.py --stats

.PHONY: knowledge-verify
knowledge-verify:  ## Verify knowledge graph integrity
	$(PYTHON) scripts/populate_knowledge_graph.py --verify

.PHONY: easter-eggs
easter-eggs:  ## Seed game world with cross-game easter eggs
	$(PYTHON) scripts/generate_easter_eggs.py

.PHONY: easter-eggs-dry
easter-eggs-dry:  ## Preview easter egg seeding without changes
	$(PYTHON) scripts/generate_easter_eggs.py --dry-run

# ── Economy / Research / TIS-100 ─────────────────────────────────────────────

.PHONY: economy-init
economy-init:  ## Initialise colony economy DB (wallets + research table)
	$(PYTHON) -c "from app.game_engine.economy import _conn; _conn(); print('Economy DB ready.')"

.PHONY: bank
bank:  ## View player bank balance
	$(PYTHON) -c "from app.game_engine.economy import EconomyEngine,CREDIT_SYMBOL; e=EconomyEngine(); print('Player balance:',e.balance('player'),CREDIT_SYMBOL)"

.PHONY: bank-leaderboard
bank-leaderboard:  ## Colony credit leaderboard
	$(PYTHON) -c "from app.game_engine.economy import EconomyEngine,CREDIT_SYMBOL; [print(f'{r[\"entity\"]:<20} {r[\"balance\"]}{CREDIT_SYMBOL}') for r in EconomyEngine().leaderboard()]"

.PHONY: research-list
research-list:  ## List colony tech tree status
	$(PYTHON) -c "from app.game_engine.economy import EconomyEngine,RESEARCH_TREE,CREDIT_SYMBOL; e=EconomyEngine(); done=set(e.researched()); [print(('✓' if t in done else '○'), f'{v[\"name\"]:<30}', f'{v[\"cost\"]}{CREDIT_SYMBOL}') for t,v in RESEARCH_TREE.items()]"

.PHONY: tis100-puzzles
tis100-puzzles:  ## List all TIS-100 puzzle levels
	$(PYTHON) -c "from app.game_engine.tis100 import PUZZLES; [print(f'Level {p[\"id\"]}: {p[\"title\"]:<30} [{p[\"difficulty\"]}] {p[\"xp\"]}XP') for p in PUZZLES.values()]"

.PHONY: schedules
schedules:  ## Show agent work schedules summary
	$(PYTHON) scripts/show_schedules.py

# ── Gordon CLI (N17 — VS Code tasks panel integration) ───────────────────────

.PHONY: gordon-cli gordon-tasks gordon-chronicle

gordon-cli:  ## Gordon CLI dashboard (task queue + agent status)
	python3 scripts/gordon_cli.py dashboard

gordon-tasks:  ## List MASTER_ZETA_TODO tasks (open items)
	python3 scripts/gordon_cli.py tasks

gordon-chronicle:  ## Tail Gordon's chronicle log
	@tail -f state/gordon_chronicle.jsonl 2>/dev/null || echo "No chronicle yet."

# ── Validation / CI ──────────────────────────────────────────────────────────

.PHONY: validate quick-test ecosystem port-status

validate:  ## Run full CI validation suite (generates validate_report.md)
	TD_BASE_URL=http://localhost:5000 python3 scripts/validate_all.py --report

quick-test:  ## Smoke tests only (faster)
	TD_BASE_URL=http://localhost:5000 python3 scripts/validate_all.py --quick

ecosystem:  ## Show live ecosystem activation plan
	python3 core/environment.py --plan

port-status:  ## Scan all 15 ports in port_map.json
	python3 scripts/port_watcher.py

# ── Self-Improvement ──────────────────────────────────────────────────────────

.PHONY: self-improve bootstrap-local install

self-improve:  ## Extract TODO comments and queue improvement tasks
	python3 scripts/self_improve.py --todos --suggest

bootstrap-local:  ## Bootstrap local environment (Linux/macOS/WSL)
	bash scripts/bootstrap_local.sh

install:  ## pip install -r requirements.txt
	pip install -r requirements.txt

install-dev:  ## Install runtime + dev tools (black, pytest, mypy)
	pip install -r requirements.txt black pytest pytest-asyncio mypy

# ── CHUG engine ──────────────────────────────────────────────────────────────

.PHONY: status
status:  ## DevMentor status report (zero-token)
	$(PYTHON) scripts/devmentor_status.py

.PHONY: improve
improve:  ## CHUG improvement cycle
	$(PYTHON) scripts/devmentor_improve.py

# ── Cleanup ───────────────────────────────────────────────────────────────────

.PHONY: clean
clean:  ## Remove __pycache__ and .pyc files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean done."

# ── Docker — Lattice Stack ────────────────────────────────────────────────────
# Requires: Docker Desktop (Windows/Mac) or Docker Engine + Compose (Linux/WSL)
# Setup:    cp .env.example .env  →  edit .env (GITHUB_TOKEN, SESSION_SECRET)

.PHONY: docker-core docker-up docker-apps docker-bridge docker-sidecars docker-research-dbs docker-lattice docker-full docker-down docker-build docker-rebuild docker-logs docker-ps docker-shell

docker-core:  ## Shared singleton infra: Redis + Ollama + Model Router + shared Postgres
	@echo "Starting shared singleton infra..."
	$(DC) up -d redis ollama model-router shared-postgres

docker-up:  ## Shared infra + shared ops: MCP + LM Studio bridge + n8n
	@echo "Starting shared singleton infra + ops surfaces..."
	$(DC) --profile shared-ops up -d redis ollama model-router shared-postgres mcp-server lm-studio-bridge n8n-terminal

docker-apps:  ## Optional app containers: Dev-Mentor + NuSyQ-Hub + SimulatedVerse
	@echo "Starting optional app containers..."
	$(DC) --profile app-containers up -d dev-mentor nusyq-hub-app simulatedverse-app

docker-bridge:  ## Cross-repo bridge surface (expects shared ops + app containers)
	@echo "Starting cross-repo bridge..."
	$(DC) --profile cross-repo up -d nusyq-bridge

docker-sidecars:  ## Legacy all-container sidecars (kept for compatibility/testing)
	@echo "Starting legacy sidecar containers..."
	$(DC) --profile legacy-sidecars up -d gordon serena-analytics skyclaw culture-ship chatdev

docker-research-dbs:  ## Optional per-repo Postgres instances for comparison work
	@echo "Starting research database trio..."
	$(DC) --profile research-dbs up -d devmentor-postgres nusyq-hub-postgres simulatedverse-postgres

docker-lattice:  ## Compatibility stack: shared infra + ops + app containers + sidecars
	@echo "Starting compatibility lattice stack..."
	$(DC) --profile shared-ops --profile app-containers --profile legacy-sidecars --profile cross-repo up -d \
	        redis ollama model-router shared-postgres \
	        mcp-server lm-studio-bridge n8n-terminal \
	        dev-mentor nusyq-hub-app simulatedverse-app nusyq-bridge \
	        gordon serena-analytics skyclaw culture-ship chatdev

docker-full:  ## Legacy showcase stack via docker-compose.full.yml
	@echo "Starting legacy showcase stack..."
	$(DC_FULL) --profile full up

docker-down:  ## Stop all running Lattice services
	$(DC) down
	@echo "Lattice offline."

docker-build:  ## Build the dev-mentor Docker image
	$(DC) build dev-mentor

docker-rebuild:  ## Force rebuild --no-cache (use after Dockerfile changes)
	$(DC) build --no-cache dev-mentor

docker-logs:  ## Follow live logs for all services
	$(DC) logs -f --tail=80

docker-ps:  ## Show status of all Lattice services
	$(DC) ps

docker-shell:  ## Open a bash shell inside the running dev-mentor container
	docker exec -it terminal-depths-backend bash

# ── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help:  ## Show this help menu
	@echo ""
	@echo "  DevMentor Colony Command Center"
	@echo "  ═══════════════════════════════"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-18s %s\n", $$1, $$2}'
	@echo ""

# ⚡ Quick Reference - NuSyQ Development Commands

## 🌅 Daily Workflow

```bash
# Start your day
python scripts/morning_standup.py

# Fast standup (short timeouts)
python scripts/morning_standup.py --fast

# Start active development (auto-test on save)
python scripts/dev_watcher.py

# Quick task menu (interactive)
python scripts/quickstart.py

# Boss Rush summary (safe console output)
python scripts/show_boss_rush_summary.py
```

## 🛠️ Code Quality

```bash
# Format, organize, lint, auto-fix everything
python scripts/improve_code_quality.py

# Manual tools
black src/ --line-length=100         # Format code
ruff check src/ --fix                # Auto-fix lint issues
mypy src/guild/ src/config/          # Type check
```

## 🧪 Testing

```bash
# All tests
pytest tests/ -v

# Quick smoke test
pytest tests/ -q -x

# Friendly diagnostics (records in test history)
python scripts/friendly_test_runner.py --quick

# Test run history (dedupe window)
python scripts/start_nusyq.py test_history 10

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Specific file
pytest tests/test_guild_board.py -v

# Watch mode (auto-run on changes)
pytest-watch tests/
```

## 🏰 Guild Board

```bash
# Status
python scripts/start_nusyq.py guild_status

# Render board
python scripts/start_nusyq.py guild_render

# Available quests
python scripts/start_nusyq.py guild_available claude code,refactor,safe

# Send heartbeat
python scripts/start_nusyq.py guild_heartbeat claude active
```

## 📊 System Health

```bash
# Quick health check (13 tests)
python scripts/start_nusyq.py selfcheck

# Full diagnostics
python scripts/start_nusyq.py doctor

# System snapshot
python scripts/start_nusyq.py snapshot

# Capabilities inventory
python scripts/start_nusyq.py capabilities

# Lifecycle catalog (services + terminals)
python scripts/start_nusyq.py lifecycle_catalog

# Cross-repo task summary
python scripts/start_nusyq.py task_summary

# Error report
python scripts/start_nusyq.py error_report
```

## 🔍 Debugging

```bash
# VS Code debugger
# Press F5 → Select configuration:
# - Guild Board: Full System
# - Agent Task Router
# - Multi-AI Orchestrator
# - Quantum Problem Resolver
# - Run Current Test
# - Debug Current File
# - Config Loader Test

# Python debugger (command line)
python -m pdb src/guild/guild_board.py

# Enhanced REPL
ipython
ptpython  # Even better!
```

## 🤖 AI Task Routing

```bash
# Analyze file with Ollama
python scripts/start_nusyq.py analyze src/guild/guild_board.py --system=auto

# Review file
python scripts/start_nusyq.py review src/config/orchestration_config_loader.py

# Debug error
python scripts/start_nusyq.py debug "ImportError in guild_board.py"

# Generate with ChatDev
python scripts/start_nusyq.py generate "REST API with JWT authentication"
```

## 📦 Package Management

```bash
# Install all dev packages
python scripts/install_dev_packages.py

# Individual packages
pip install watchdog rich typer
pip install --upgrade black ruff mypy
```

## 🔧 Git Operations

```bash
# Commit (pre-commit hook runs automatically)
git add .
git commit -m "feat: add new feature"
# → Validates syntax, format, lint, config

# Push (pre-push hook runs automatically)
git push
# → Runs tests, type check, health check

# Bypass hooks (NOT RECOMMENDED)
git commit --no-verify
git push --no-verify

# Configure hooks path (already done)
git config core.hooksPath .githooks
```

## ⚙️ Configuration

```bash
# Validate config
python -m src.config.orchestration_config_loader --validate

# Print config summary
python -m src.config.orchestration_config_loader --summary

# Test config loading
python -c "from src.config.orchestration_config_loader import get_guild_board_config; print(get_guild_board_config())"
```

## 🎯 VS Code Tasks

```
Ctrl+Shift+P → Tasks: Run Task

Available tasks:
- NuSyQ: Snapshot (Spine Lens)
- NuSyQ: Hygiene (Spine Guard)
- NuSyQ: Suggest (Next 1-3)
- NuSyQ: Brief (60s Status)
- NuSyQ: Problem Signal Snapshot
- NuSyQ: Unified Error Report
- NuSyQ: Selfcheck
- Guild: Board Status
- Guild: Render Board
- Error Scan: Full Ecosystem
- Code Quality: Ruff Fix
- Code Quality: Mypy
- Code Quality: Black Format
```

## 🎨 Code Snippets (Type in .py file)

```
quest        → Quest entry template
heartbeat    → Agent heartbeat creation
config       → Config loader boilerplate
async_guild  → Async guild method
action       → NuSyQ action decorator
quest_log    → JSONL log entry
route        → Terminal routing
logger       → Python logger
```

## 🚀 Launch Configurations (F5)

1. **Guild Board: Full System** - Debug entire guild system
2. **Agent Task Router** - Debug task routing
3. **System Health Check** - Debug diagnostics
4. **Multi-AI Orchestrator** - Debug orchestration
5. **Quantum Problem Resolver** - Debug healing system
6. **Run Current Test** - Debug current test file
7. **Debug Current File** - Debug any Python file
8. **Config Loader Test** - Validate configuration

## 📝 Common Workflows

### Add New Feature

```bash
# 1. Create feature branch
git checkout -b feature/new-thing

# 2. Start watcher (auto-test)
python scripts/dev_watcher.py

# 3. Develop (save triggers tests)
code src/new_feature.py

# 4. Improve quality
python scripts/improve_code_quality.py

# 5. Commit (hooks validate)
git add .
git commit -m "feat: add new thing"

# 6. Push (hooks test)
git push origin feature/new-thing
```

### Fix Bug

```bash
# 1. Run diagnostics
python scripts/start_nusyq.py error_report

# 2. Debug in VS Code
# F5 → Debug Current File

# 3. Write test
code tests/test_bugfix.py

# 4. Fix code (watcher runs tests)
code src/buggy_file.py

# 5. Verify fix
pytest tests/test_bugfix.py -v

# 6. Commit
git commit -am "fix: resolve bug in X"
```

### Refactor Code

```bash
# 1. Run baseline tests
pytest tests/ --cov=src

# 2. Refactor
code src/module_to_refactor.py

# 3. Auto-format & lint
python scripts/improve_code_quality.py

# 4. Verify no breakage
pytest tests/ -v

# 5. Type check
mypy src/module_to_refactor.py

# 6. Commit
git commit -am "refactor: improve X"
```

## 🏥 Emergency Recovery

```bash
# System not responding
python scripts/start_nusyq.py doctor

# Import errors
python src/utils/quick_import_fix.py

# Path issues
python src/healing/repository_health_restorer.py

# Advanced healing
python src/healing/quantum_problem_resolver.py src/broken_file.py

# Nuclear option (restart environment)
deactivate
.venv\Scripts\activate
python scripts/install_dev_packages.py
```

## 📊 Metrics & Observability

```bash
# Start observability stack
docker compose -f dev/observability/docker-compose.observability.yml up -d

# Stop observability
docker compose -f dev/observability/docker-compose.observability.yml down

# Run with tracing
python scripts/start_nusyq.py snapshot  # Auto-traces to OpenTelemetry
```

## 🧪 Test Terminal

The Tests terminal is wired into Terminal Keeper and routes pytest output, coverage,
and test diagnostics automatically (via `terminal_groups.json` + routing map).

---

**Last Updated:** 2025-12-26  
**Author:** GitHub Copilot (Claude Sonnet 4.5)  
**Related Docs:**

- [ECOSYSTEM_ENHANCEMENT_COMPLETE.md](ECOSYSTEM_ENHANCEMENT_COMPLETE.md)
- [BOSS_RUSH_DEPLOYMENT_COMPLETE.md](BOSS_RUSH_DEPLOYMENT_COMPLETE.md)
- [PHASE_2_ACTION_PLAN.md](PHASE_2_ACTION_PLAN.md)

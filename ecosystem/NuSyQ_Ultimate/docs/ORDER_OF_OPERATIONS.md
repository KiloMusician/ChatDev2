# NuSyQ Ecosystem: Order of Operations & Dependency Modlist

This document tracks the recommended startup, integration, and troubleshooting order for the NuSyQ multi-repo system. It is designed to prevent missed steps and clarify dependencies for future contributors and agents.

## 1. Environment Preparation
- [ ] Ensure Python 3.12+ and Node.js are installed
- [ ] Install PowerShell 7+ (pwsh)
- [ ] Confirm required VS Code extensions (Copilot, AIQuickFix, Continue.dev, SonarQube)
- [ ] Set up virtual environments for each repo

## 2. NuSyQ-Hub Initialization
- [ ] Run orchestrator DryRun: `pwsh NuSyQ.Orchestrator.ps1 -DryRun`
- [ ] Install PowerShell.Yaml module if missing
- [ ] Run full orchestrator: `pwsh NuSyQ.Orchestrator.ps1`
- [ ] Run repo health checks: `python src/diagnostics/system_health_assessor.py`
- [ ] Run import fixer: `python src/utils/quick_import_fix.py`

## 3. NuSyQ Root Startup
- [ ] Activate venv: `source .venv/bin/activate` or `./.venv/Scripts/activate`
- [ ] Start MCP server: `python mcp_server/main.py`
- [ ] Validate MCP health: `curl http://localhost:8000/health` (or correct port)
- [ ] Check Ollama models: `ollama list`
- [ ] Run ChatDev wrapper: `python nusyq_chatdev.py`

## 4. SimulatedVerse Startup
- [ ] Install Node dependencies: `npm install`
- [ ] Start Express backend: `npm run dev` (port 5000)
- [ ] Start React UI: `npm start` (port 3000)
- [ ] Confirm Temple of Knowledge and House of Leaves logs

## 5. Integration & Context Plumbing
- [ ] Register agent contexts: `python scripts/agent_context_cli.py --namespace kilo --path path/to/file.py`
- [ ] Push context to MCP: `python scripts/agent_context_cli.py --namespace kilo --path path/to/file.py --push-mcp http://localhost:8000/mcp`
- [ ] Sync secrets/config: `config/secrets.json` ↔ `nusyq.manifest.yaml`
- [ ] Confirm cross-repo context bridge

## 6. Testing & Validation
- [ ] Run targeted pytest tests with `-o addopts=`
- [ ] Run ruff and black for lint/format
- [ ] Run integration tests in all repos
- [ ] Confirm session logs and progress trackers are updating

## 7. Troubleshooting & Recovery
- [ ] If lost, consult `docs/Agent-Sessions/SESSION_*.md` and quest logs
- [ ] Use self-healing tools: `src/healing/repository_health_restorer.py`, `src/healing/quantum_problem_resolver.py`
- [ ] Check system health and import status

## 8. Shutdown & Maintenance
- [ ] Stop MCP server and background services
- [ ] Archive logs and session summaries
- [ ] Update modlist and order-of-operations docs

---

## Dependency Modlist
- NuSyQ-Hub: PowerShell.Yaml, Python 3.12+, ruff, black, pytest
- NuSyQ Root: FastAPI, uvicorn, Ollama, ChatDev, Continue.dev
- SimulatedVerse: Node.js, Express, React, TouchDesigner (optional)
- Shared: VS Code extensions, config/secrets.json, nusyq.manifest.yaml

---

This file should be updated as new integration points, dependencies, or startup steps are added. See also: `docs/Checklists/PROJECT_STATUS_CHECKLIST.md`, `docs/Agent-Sessions/SESSION_*.md`, and repo-specific README.md files.

# Code Tour Summary — ΞNuSyQ Multi-Repo Guided Tour

This summary accompanies the CodeTour at `.tours/code_tour.tour` and provides a quick reference for maintainers and new contributors.

Repositories covered
- `NuSyQ` (root) — MCP server, agent context plumbing, orchestrator hooks
- `NuSyQ-Hub` (Legacy) — discovery tools, function registries, archival experiments
- `SimulatedVerse` — the simulation engine with Express + React UI

High-value entry points
- `mcp_server/main.py` — FastAPI MCP server and `/health` endpoint
- `scripts/agent_context_cli.py` — register files/notebooks to the AgentContextManager
- `src/tools/agent_context_manager.py` — JSON-backed context manager
- `NuSyQ.Orchestrator.ps1` — environment orchestration script (PowerShell)
- `src/tools/kilo_discovery_system.py` (NuSyQ-Hub) — discovery and indexing helpers
- `docs/ORDER_OF_OPERATIONS.md` — curated startup & dependency steps (new)

Common developer flows
1. Start MCP server (use repo venv python)
2. Register a context item via the CLI
3. Run discovery tests and inspect generated indices
4. Use the orchestrator in DryRun to validate environment changes

Debugging tips
- Use `-o addopts=` when running pytest locally to avoid CI addopts
- If orchestrator fails on YAML operations, check PowerShell.Yaml availability
- Capture full MCP server logs by running `python mcp_server/main.py` from the repo venv

Where to add new content
- New code -> `src/`
- Tests -> `tests/`
- Documentation & playbooks -> `docs/`

This file is intended as a lightweight companion to the full tour. If you want, I can expand each step into detailed checklists or convert this into a set of automated tasks (Makefile / PowerShell task runner) that validate the steps automatically.

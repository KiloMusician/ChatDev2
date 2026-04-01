# Tripartite DEV Bootstrap (NuSyQ / NuSyQ-Hub / SimulatedVerse)

This document contains the canonical, minimal steps to get the Tripartite
development environment up and running on a developer machine.

Prereqs

- pwsh (PowerShell) or compatible shell
- Python 3.12+ (repo uses a local `.venv`)
- Node.js (for SimulatedVerse frontend)
- Docker (optional)
- Ollama (if you use local models)

Quick environment vars (examples)

- `CHATDEV_PATH` — path to ChatDev integration (optional)
- `PYTHONPATH` — add repo `src` if needed

Canonical startup order

1. Repair / create virtualenv pwsh -NoProfile -File .\scripts\venv-repair.ps1

2. Dry-run orchestrator pwsh -NoProfile -File "..\NuSyQ\NuSyQ.Orchestrator.ps1"
   -DryRun

3. Start MCP server (NuSyQ/mcp_server) pwsh -NoProfile -Command "Start-Process
   -FilePath .\.venv\Scripts\python.exe -ArgumentList
   '-m','uvicorn','mcp_server.main:app','--host','127.0.0.1','--port','3000'
   -WorkingDirectory '..\NuSyQ' -PassThru"

4. Start Orchestrator (if DryRun OK) pwsh -NoProfile -File
   "..\NuSyQ\NuSyQ.Orchestrator.ps1"

5. Start SimulatedVerse (frontend) cd SimulatedVerse npm ci npm run dev

Health checks

- MCP: http://127.0.0.1:3000/health
- Ollama: `ollama list`
- Orchestrator logs: `Logs/orchestrator_*.log` or `orchestration_state.json`

Shutdown

- pwsh .\stop-all-servers.ps1

Notes

- Use the scripts in `scripts/` to automate repeated operations.

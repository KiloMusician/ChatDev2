# Copilot Notes

This file records commands, terminal uses, and live notes for the Copilot agent running inside the workspace.

- Date: 2025-10-23
- Purpose: record steps taken to bring up NuSyQ services and debug integration across repos.

## Commands run

- Orchestrator DryRun (NuSyQ): `pwsh -NoProfile -File ./NuSyQ.Orchestrator.ps1 -DryRun`
- Start MCP server (background): `.venv/Scripts/python.exe -m mcp_server.main &`
- Quick repo scan (NuSyQ-Hub): `python -m src.tools.maze_solver . --max-depth 6 --progress`

## Observations

- Orchestrator DryRun succeeded parsing but PowerShell module `PowerShell.Yaml` is not available; ConvertFrom-Yaml missing.
- MCP server binary is at `mcp_server/main.py` and can be launched via repository venv python.

## Next steps

- Start MCP server and tail logs
- If MCP server starts successfully, POST a small health-check request to `/health` and record response
- Start SimulatedVerse dev server
- Wire `AgentContextManager` to MCP via small HTTP POST endpoint

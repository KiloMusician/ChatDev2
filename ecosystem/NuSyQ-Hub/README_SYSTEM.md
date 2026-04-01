NuSyQ System - Quick Start & Runtime Requirements

Purpose

A minimal, human-readable guide that documents how to bring the local NuSyQ ecosystem up in a reproducible order and what runtime dependencies are expected.

Start order (recommended)

1. Ensure required environment variables are set (see `.env.example`).
2. Start the MCP server (NuSyQ repo):
   - Use the workspace task or run `python mcp_server/main.py` from the `NuSyQ/` folder.
3. Start the Unified Orchestrator / Orchestrator tasks in `NuSyQ/` (if applicable).
4. Start local model runtimes (Ollama / LM Studio) if you plan to route tasks to local models.
5. Start SimulatedVerse dev server (optional) using the provided npm tasks.
6. Run `python scripts/start_nusyq.py` to generate a system snapshot and verify state.

Key files & status

- `scripts/start_nusyq.py` - system snapshot and diagnostics
- `src/Rosetta_Quest_System/quest_log.jsonl` - persistent quest and event log
- `NuSyQ/mcp_server/main.py` - MCP server (FastAPI) that exposes tools and health endpoints
- `src/tools/agent_task_router.py` - conversational routing surface
- `src/system/dictionary/consciousness_bridge.py` - repository-aware context enrichment

Important environment variables (see `.env.example`)

- CHATDEV_PATH - Path to ChatDev installation (optional)
- NUSYQ_RUN_ID - Run identifier used in receipts/tracing
- NUSYQ_ECOSYSTEM_EFFICIENCY_FORCE - When set to '1', forces suggested routing targets
- OLLAMA_URL - Base URL for local Ollama API (e.g., http://127.0.0.1:11434)

Quick verification

Run the lightweight health check to validate key runtime artefacts:

```bash
python scripts/health_check.py
```

If you want, I can expand this document with diagrams, a start/stop script, and a small `Makefile` or VS Code tasks to orchestrate the full start sequence.

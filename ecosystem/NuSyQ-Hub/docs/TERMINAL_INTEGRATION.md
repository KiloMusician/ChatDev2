# Terminal Integration Guide

This document describes how to use the enhanced terminal ecosystem implemented
in `src/system/enhanced_terminal_ecosystem.py` and how to hook VS Code terminals
to those logs for a better developer experience.

Usage summary

- The system provides named channels (Errors, Tasks, Tests, Metrics, Agents,
  etc.).
- Messages are stored as newline-delimited JSON under
- `data/terminal_logs/<channel_slug>.log` (channel names are normalized to
- lowercase with underscores, e.g., `errors`, `ai_council`, `tasks`).
- Programs can write to channels by importing TerminalManager or by using the
  CLI wrapper:

```bash
# Send a structured message from any script
python -m src.system.enhanced_terminal_ecosystem send "Errors" error "Something failed" '{"code":123}'

# List channels
python -m src.system.enhanced_terminal_ecosystem list

# Show recent entries
python -m src.system.enhanced_terminal_ecosystem recent "Errors" 50
```

Suggested VS Code setup

1. Create a terminal for each important channel and run a tail command:

   - Windows (PowerShell):

  ```powershell
  Get-Content -Path .\data\terminal_logs\errors.log -Wait -Tail 50
  ```

   - Linux/macOS:
  ```bash
  tail -n 200 -f data/terminal_logs/errors.log
  ```

2. Add tasks to `.vscode/tasks.json` that open the tail commands for quick
   access. Example task for Errors:

```json
{
  "label": "Tail: Errors",
  "type": "process",
  "command": "powershell",
  "args": [
    "-NoExit",
    "-Command",
    "Get-Content -Path .\\data\\terminal_logs\\errors.log -Wait -Tail 200"
  ],
  "presentation": { "panel": "dedicated" }
}
```

3. Use the `TerminalManager` API from Python modules to emit machine-readable
   events. Example:

```py
from src.system.enhanced_terminal_ecosystem import TerminalManager
tm = TerminalManager.get_instance()
tm.send('Tasks','info','started_job', meta={'job_id': 'ZETA-123'})
```

## REST API integration

You can also expose the terminal ecosystem via a lightweight REST webhook so
remote tools (ChatGPT CLI, automation scripts, or other repos) send structured
events without touching the repo files directly.

1. Start the REST server:

```bash
python scripts/run_terminal_api.py
# or, for development with reload:
uvicorn src.system.terminal_api:app --reload
```

2. Call the webhook against `http://localhost:8000`:

   - `POST /api/terminals/send` – body: `{"channel":"Errors","level":"error","message":"text","meta":{"run":"cli"}}`
   - `GET /api/terminals` – list active channels.
   - `GET /api/terminals/{channel}/recent?n=20` – fetch recent entries (max 500).
   - `GET /health` – readiness probe for orchestration and CLI checks.

3. Example `curl` call:

```bash
curl -X POST http://localhost:8000/api/terminals/send \
  -H "Content-Type: application/json" \
  -d '{"channel":"Errors","level":"error","message":"Webhook test","meta":{"source":"cli"}}'
```

Secure the HTTP gateway (JWT/OAuth/mTLS) before exposing it beyond your
development environment.

Design notes and next steps

- Channels are intentionally file-backed for compatibility with editors and
  monitoring tools.
- Future: add socket/HTTP API for live web UIs, add Log rotation, structured
  indexing (SQLite/Elastic), and per-channel retention policies.

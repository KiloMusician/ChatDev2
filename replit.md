# ChatDev 2.0 — DevAll

## Overview

ChatDev 2.0 (DevAll) is a zero-code multi-agent orchestration platform for building complex AI workflows. It supports visual graph-based workflow design, multiple LLM backends (OpenAI, Gemini, Ollama), and produces artifacts via multi-agent collaboration.

## Architecture

- **Frontend**: Vue 3 + Vite, runs on port 5000 (`frontend/`)
- **Backend**: FastAPI + uvicorn, runs on port 6400 (`server/`, `server_main.py`)
- **Proxy**: Vite dev server proxies `/api` and `/ws` requests to the backend on port 6400
- **Agent Runtime**: `runtime/` — node executors, edge logic, memory, tools
- **Workflows**: Defined as YAML in `yaml_instance/`, outputs stored in `WareHouse/`

## Running the App

The single workflow `Start application` runs `bash start.sh` which:
1. Starts the FastAPI backend on `localhost:6400`
2. Starts the Vite frontend on `0.0.0.0:5000`

## Port Design

- Port 5000: Frontend (Vite) — webview-accessible
- Port 6400: Backend (FastAPI) — internal only, proxied through Vite
- Port 8008: Dev-Mentor (Terminal Depths) — ecosystem service
- Port 3003: NuSyQ-Hub Reactive API — ecosystem service (FastAPI, `src/api/main.py`)
- Port 3002: CONCEPT_SAMURAI static docs — ecosystem service

## Key Files

- `start.sh` — Startup script for both services
- `server_main.py` — Backend entry point
- `frontend/vite.config.js` — Vite config with proxy and port settings
- `pyproject.toml` — Python project config (`tool.uv.package = false`)
- `yaml_instance/` — Pre-built workflow YAML definitions

## Dependencies

- **Python**: 3.12 (installed via Replit module system)
- **Python packages**: fastapi, uvicorn, fastmcp, pandas, pyyaml, openai, anthropic, etc. (installed via pip)
- **Node packages**: Vue 3, vue-router, @vue-flow/core, vite (installed via npm in `frontend/`)

## NuSyQ Ecosystem Integration

Six repos cloned to `ecosystem/` and launched via `ecosystem/start_services.sh`:

| Repo | Type | Port | Status |
|------|------|------|--------|
| Dev-Mentor | FastAPI (game engine, CHUG, ML) | 8008 | Auto-started |
| CONCEPT_SAMURAI | Static docs server | 3002 | Auto-started |
| SimulatedVerse | Node/RimWorld sim | 3000 | Heavy — not auto-started |
| NuSyQ-Hub | FastAPI reactive API | 3003 | Auto-started |
| NuSyQ_Ultimate | Python library | — | CLI/library mode |
| awesome-vibe-coding | Docs/resources | — | Static reference |

The **Ecosystem** page (`/ecosystem`) shows live health of all 6 repos plus the Bridge Status panel. The **Orchestrator** page (`/orchestrator`) is the central control panel.

Backend API: `GET /api/ecosystem/status`, `GET /api/ecosystem/repos`, `POST /api/ecosystem/chug`

### Bridge API (`server/routes/bridge.py`)
Routes under `/api/bridge/`:
- `GET /ping` — Quick uptime ping
- `GET /status` — Compact status (repos online/offline, quest counts, sessions)
- `GET /manifest` — Full bridge manifest with capabilities and repo map
- `GET /quests` — All 20 Dev-Mentor CTF quests (live from JSON files)
- `POST /quests/sync` — Sync quest catalogue into shared memory
- `POST /command` — Bridge command router (boot, integrate, quest sync, chug run, etc.)
- `GET /repo/list` — All registered repos
- `GET /repo/status[/{name}]` — Live health probe of repos
- `POST /agent/dispatch` — Dispatch a task to a named agent
- `POST /session/open` + `GET /session/state/{id}` — Session management

### Dev-Mentor Quest Sync
- 20 CTF quests across 5 categories (Crypto, Forensics, Network, Reverse Engineering, Web)
- Auto-synced to shared memory on every `bootstrap()` call (server startup)
- Also synced via `POST /api/bridge/quests/sync` or `POST /api/bridge/command` → `quest sync`
- Stored in shared memory keys: `devmentor.quests.synced`, `devmentor.quests.summary`

### ecoscan (Terminal Health Check)
- `./ecoscan` — Quick health check of all NuSyQ ecosystem services from terminal
- `./ecoscan --json` — Full bridge manifest as JSON
- Probes: ChatDev :6400, Bridge, Orchestrator, Dev-Mentor :8008, CONCEPT_SAMURAI :3002, Quests

## NuSyQ Central Orchestrator (TOTAL SYSTEM ACTIVATION)

The orchestrator wires all 6 repos into a living system:

### Shared Memory Layer (`ecosystem/shared/`)
- `db.py` — SQLite WAL with 6 tables (task_queue, agent_registry, tool_registry, execution_log, shared_memory, chug_cycles)
- `memory.py` — Cross-agent KV store; namespace-aware read/write/snapshot
- `task_queue.py` — Async-safe enqueue/dequeue/complete/fail
- `tool_registry.py` — 20 tools registered across all 6 repos
- `agent_registry.py` — 7 agents registered with capabilities + heartbeat
- `execution_log.py` — Structured timed action log, full audit trail

### Central Orchestrator (`ecosystem/orchestrator.py`)
- CHUG cycle: ASSESS → CULTIVATE → HARVEST → UPGRADE → GROW
- Scans 3 live services on every cycle
- Auto-creates tasks, routes to agents, harvests results, writes upgrades
- Runs cycles #1, #2, ... persisted in `chug_cycles` table

### Orchestrator API (`server/routes/orchestrator.py`)
Routes under `/api/orchestrator/`:
- `GET /status` — Full system snapshot
- `GET /scan` — Quick service scan (no side effects)
- `POST /cycle` — Trigger CHUG cycle in background
- `GET /cycle/last` — Last cycle result
- `GET /cycle/history` — Recent cycles
- `GET /tasks` — Task queue state
- `POST /tasks/enqueue` — Manually add a task
- `GET /agents` — All registered agents
- `GET /tools` — All registered tools (filterable by repo)
- `GET /memory` — Shared memory snapshot
- `POST /memory/write` — Write to shared memory
- `GET /logs` — Execution audit log

### PYTHONPATH Activation (`ecosystem/activate.py`)
- Adds all 6 repo roots to `sys.path` and `PYTHONPATH` env var
- Enables cross-repo imports from any ecosystem module

### Frontend Orchestrator Panel (`/orchestrator`)
- Live CHUG cycle trigger + status polling
- System scan with service health indicators
- Cycle history table (phase → done)
- Task queue with manual enqueue form
- Agent registry with capabilities
- Tool registry with repo filtering
- Execution log + shared memory inspector

## NuSyQ-Hub as Running Service

NuSyQ-Hub (`ecosystem/NuSyQ-Hub/`) now runs as a persistent HTTP service on **port 3003** via `uvicorn src.api.main:app`. Started by `ecosystem/start_services.sh` alongside Dev-Mentor and CONCEPT_SAMURAI.

API surface exposed at `http://localhost:3003`:
- `GET /api/status` — system heartbeat (`status`, `run_id`, `details`)
- `GET /api/agents` — agent registry
- `GET /api/quests` — quest list (12 templates)
- `GET /api/metrics` — system metrics
- `GET /api/systems/*` — per-system status routes

The bridge status endpoint now probes NuSyQ-Hub at `/api/status` and reports it as `online` when healthy. The BridgeHUD shows it as a 4th coloured dot.

## Per-Repo td_bridge.py

Each ecosystem repo has a self-contained `td_bridge.py` at its root. All 6 repos are covered:

| Repo | REPO_ID | File |
|---|---|---|
| Dev-Mentor | `dev_mentor` | `ecosystem/Dev-Mentor/td_bridge.py` |
| CONCEPT_SAMURAI | `concept_samurai` | `ecosystem/CONCEPT_SAMURAI/td_bridge.py` |
| NuSyQ-Hub | `nusyq_hub` | `ecosystem/NuSyQ-Hub/td_bridge.py` |
| NuSyQ_Ultimate | `nusyq_ultimate` | `ecosystem/NuSyQ_Ultimate/td_bridge.py` |
| awesome-vibe-coding | `awesome_vibe_coding` | `ecosystem/awesome-vibe-coding/td_bridge.py` |
| SimulatedVerse | `simulated_verse` | `ecosystem/SimulatedVerse/td_bridge.py` |

Each file is self-contained: auto-resolves the workspace root, provides `td`, `hub` singleton clients, and these helper functions:

```python
from td_bridge import td_ping, td_command, td_task, td_heartbeat, td_hub_status
from td_bridge import td_game_state, td_push_state, td_consciousness
from td_bridge import td_colonists, td_push_colonists, td_dispatch, td_session

td_ping()                       # ChatDev bridge health
td_command("projects")          # run bridge command
td_heartbeat()                  # self-register with bridge + write to shared memory
td_hub_status()                 # NuSyQ-Hub port 3003 status
td_game_state()                 # read persisted game/sim state
td_push_state({"phase": "run"}) # merge-update game state
```

## Bridge HUD (Sidebar)

`frontend/src/components/BridgeHUD.vue` — live ecosystem status strip embedded at the left side of the top nav bar:
- Coloured dots for ChatDev :6400, Dev-Mentor :8008, NuSyQ-Hub :3003, and CONCEPT_SAMURAI :3002
- Live event count badge fed by the SSE stream
- SSE connection pulse indicator
- Hover panel with per-service status, quest count, sessions, uptime, and 5 most-recent events
- Links to Ecosystem and Orchestrator views

## Bridge SSE Event Stream

`GET /api/bridge/events` — long-lived `text/event-stream` response:
- `ping` event every 5 s (keeps connection alive)
- `log` events for new execution log entries
- `health` snapshot every 30 s (probes Dev-Mentor, CONCEPT_SAMURAI, ChatDev)
- `project` events (future: emitted when WareHouse projects complete)

## Persistent Game State (`/api/nusyq/`)

`server/routes/nusyq_bridge.py` — all game/sim state is persisted to the shared SQLite DB via the shared memory KV store (namespace `game_state`, key prefix `nusyq.`):

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/nusyq/game/state` | GET | Read game state (idle defaults) |
| `/api/nusyq/game/state` | POST | Merge-update game state |
| `/api/nusyq/colonist_state` | GET | Read colonist snapshot |
| `/api/nusyq/colonist_state` | POST | Push colonist state from RimWorld |
| `/api/nusyq/consciousness` | GET/POST | Persist consciousness metrics |
| `/api/nusyq/sessions/{id}` | GET/POST | Per-session persistence |

## ChatDev Project Results (`/api/bridge/projects`)

WareHouse scan surface:
- `GET /api/bridge/projects` — lists all 100+ WareHouse projects with file count, size, Python files, prompt preview, `api_key_available` flag
- `GET /api/bridge/projects/{name}` — per-project file list with content previews
- `projects` bridge command — available in `/api/bridge/command` router

## Bridge Command Registry (full list)

All commands available via `POST /api/bridge/command {"command":"..."}`:

| Command | Description |
|---|---|
| `boot` | Bridge boot confirmation + cockpit URL |
| `nusyq status` | Live probe of all 4 services (threaded, no deadlock) |
| `gordon status` | Gordon orchestrator status from Dev-Mentor |
| `gordon run` | Trigger one Gordon `--mode once` cycle in background |
| `serena status` | Serena indexer status (chunks, files, functions) |
| `serena find` | Query Serena semantic search (pass `query` in ctx) |
| `quest sync` | Sync all 20 CTF quests into shared memory |
| `integrate` | Full ecosystem integration snapshot |
| `chug run` | Trigger CHUG orchestrator cycle |
| `agents` | List all registered agents |
| `tools` | List all registered tools |
| `memory snapshot` | Dump shared memory KV store |
| `repo list` | All repos from registry |
| `repo status` | Live probe of all registered repos |
| `projects` | WareHouse project count + first 20 |

## Terminal Depths (`td`) CLI

`ecosystem/Dev-Mentor/td` — universal CLI launcher wired to Dev-Mentor :8008.

- **PATH**: `start.sh` adds `Dev-Mentor/` to `$PATH` and symlinks to `~/.local/bin/td`
- **Env vars**: `TD_SERVER_URL=http://localhost:8008`, `NUSYQ_HUB_URL=http://localhost:3003` set in `start.sh`
- **Usage**: `td status` / `td play` / `td surfaces` / `TD_SERVER_URL=http://localhost:8008 python3 scripts/td.py <cmd>`

### Fixed Broken Links (session)

1. `ecosystem/Dev-Mentor/scripts/td.py` line 121: `DEFAULT_PORTS` now includes `8008` → `[5000, 8008, 7337, 8000]`
2. `ecosystem/Dev-Mentor/app/game_engine/commands.py` line 32847: `NUSYQ_HUB_URL` default now `http://localhost:3003` (was `:8000`)
3. `server/routes/bridge.py` `nusyq status` command: fixed async event-loop deadlock by running external probes in `ThreadPoolExecutor`; ChatDev probes itself as `online:True` directly (no HTTP loop)

## Gordon Orchestrator

`ecosystem/Dev-Mentor/scripts/gordon_orchestrator.py` — god-mode conductor:
- Launched as sidecar by Dev-Mentor on startup (`--mode once`)
- Bridge commands: `gordon status` (live check), `gordon run` (trigger new cycle)
- Health port: 3000; Game API: `POST http://localhost:5000/api/game/command`

## LLM Setup

The app requires API keys to run workflows (OpenAI, Anthropic, Gemini). Set these as environment variables/secrets before use.

# System Architecture — Three-System Overview

> **One repo. Three distinct systems. Zero confusion.**
>
> Read this if you find yourself asking: "Is this a DevMentor thing or a Terminal Depths
> thing? Where does the RimWorld mod fit?" This document answers that permanently.

---

## The Three Systems

```
┌─────────────────────────────────────────────────────────────────────┐
│  DEVMENTOR  (the outer shell — the teaching environment)            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  TERMINAL DEPTHS  (the inner game — the cyberpunk RPG)        │  │
│  │                                                               │  │
│  │   Commands · NPCs · Factions · ARG · Story · Quests          │  │
│  │   534 handlers · 5-layer consciousness · 7 PRIMUS fragments   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Serena · Gordon · CHUG · Lattice · NuSyQ · MCP · RL · ML          │
└─────────────────────────────────────────────────────────────────────┘
         ▲
         │  REST API  (http://localhost:7337/api/game/command)
         │
┌─────────────────────┐
│  TERMINAL KEEPER    │  ← RimWorld mod. Bridge only. C# code.
│  Lattice Colonists  │     Colony IS the training loop.
└─────────────────────┘
```

---

## DevMentor

**What it is:** The VS Code-native mentorship repository. The *outer shell*.
It IS the repo. It IS the development environment. It IS the cognitive exoskeleton.

**What it owns:**
- The FastAPI backend (`app/backend/main.py`) and all REST routes
- The CLI (`cli/devmentor.py` → `python -m cli.devmentor serve`)
- Serena (drift detection, policy enforcement, code walks, Memory Palace)
- Gordon (autonomous player agent, RL training loop)
- The CHUG engine (7-phase continuous improvement cycles)
- The Lattice (SQLite knowledge graph, embeddings, semantic search)
- NuSyQ-Hub integration (manifest publishing, chronicle sync)
- All 71 agent personalities (`agents/`, `config/personalities/`)
- The ML services layer (model registry, feature store, embedder)
- VS Code integration files (`.vscode/`, `.devcontainer/`)
- MCP server (`mcp/server.py` — 16 tools for Claude/Copilot/Continue.dev)
- Health endpoints, port registry, sidecar services

**Port:** 5000 (Replit) / 7337 (Docker, VS Code, local)

**API prefix:** `/api/` — DevMentor routes like `/api/health`, `/api/serena/*`, `/api/mcp/*`

**Database owner:** All 10 SQLite databases in `state/` and `var/`

---

## Terminal Depths

**What it is:** The cyberpunk terminal RPG running *inside* DevMentor. The *game engine*.
It is NOT a separate process. It runs as part of the FastAPI server.

**What it owns:**
- All 534 game command handlers (`app/game_engine/commands.py`)
- Game state, player XP, inventory, narrative (`app/game_engine/state.py`)
- NPCs, factions, districts (`app/game_engine/npcs.py`, `factions.py`)
- The 5-layer consciousness system and 7 PRIMUS fragments
- The ARG layer (signal frequencies, temple floors, Project Emergence)
- The VirtualFS (in-game file system with real directory mounts)
- Terminal UI (`app/frontend/` — xterm.js browser console)
- Ambient sound system (Web Audio API, CRT aesthetic, scan lines)
- Economy system (`state/economy.db`)
- Swarm Ledger (`state/swarm_ledger.db`)

**API prefix:** `/api/game/` — routes like `/api/game/command`, `/api/game/state`

**Game panel:** `http://localhost:7337/game/` (browser xterm console)
**CLI panel:** `http://localhost:7337/game-cli/` (Swarm Console)

**Naming rule:** If it's a player-facing game feature → it belongs in Terminal Depths.
If it's infrastructure, AI, learning, or IDE tooling → it belongs in DevMentor.

---

## Terminal Keeper: Lattice Colonists

**What it is:** A RimWorld mod. A *bridge only*. The colony IS the training loop.
It connects a running RimWorld colony directly to the Terminal Depths ecosystem,
allowing RimWorld pawns to register as persistent agents with memories, skills, and XP.

**What it owns:**
- C# mod source code (`mods/TerminalKeeper/`)
- RimWorld XML defs and patches (`mods/TerminalKeeper/Defs/`)
- The `LatticeTerminal` in-game building (colonists interact with the game here)
- Pawn → Agent registration via Terminal Depths REST API
- Incident relay (colony events → Lattice events)
- Crash detection and alert publishing

**How it connects:**
```
RimWorld colonist
  → builds Lattice Terminal
    → C# calls Terminal Depths REST API
      → /api/game/command (register_agent, send_command, etc.)
        → Serena memory updated
          → Gordon trains on it
```

**RimAPI Bridge** (`services/rimapi_bridge.py`): FastAPI service that relays
RimWorld pawn state, incidents, and crashes to the Lattice via Redis pub/sub.

**Port:** Terminal Keeper calls Terminal Depths on 7337 (local/Docker)

---

## Naming Conventions

| Context | Correct name |
|---------|-------------|
| The repo / project overall | DevMentor (or Dev-Mentor for GitHub) |
| The game the player interacts with | Terminal Depths |
| The RimWorld mod | Terminal Keeper: Lattice Colonists |
| The AI ecosystem | The Lattice |
| The main FastAPI backend | DevMentor backend |
| The main DB container | `terminal-depths-backend` (Docker, historical) |
| The CLI command | `devmentor` |
| The web game panel URL | `/game/` |

> Docker container name `terminal-depths-backend` is a legacy name from the early
> days when Terminal Depths and DevMentor were the same concept. The container runs
> the full DevMentor+Terminal Depths stack.

---

## Port Reference

| Port | What | Where |
|------|------|-------|
| 5000 | DevMentor server | **Replit ONLY** |
| 7337 | DevMentor server | **Docker / VS Code / local ONLY** |
| 9100 | MCP server (HTTP mode) | Any env |
| 11434 | Ollama | Local / Docker host |
| 6379 | Redis | Docker |
| 9001 | Model Router | Docker |
| 1234 | LM Studio bridge | Local (if running) |

> RULE: Never use port 5000 in Docker. Never use port 7337 in Replit.
> Auto-detection: `REPL_ID` env var present → 5000; absent → 7337.

### Ecosystem Port Resolution Shim

`core/port_resolver.py` is the single source of truth for all service URL resolution across the NuSyQ ecosystem. Never write `os.environ.get("TERMINAL_DEPTHS_URL", "http://localhost:5000")` inline.

```python
from core.port_resolver import TD_BASE, td_url, svc_url

# Use the pre-computed constant (fastest, evaluated once at import time)
url = f"{TD_BASE}/api/game/command"

# Or call the function (same logic, safe to call from any context)
url = td_url()

# Named services from port_map.json
gordon  = svc_url("gordon")        # → http://localhost:3000
simverse = svc_url("simulatedverse") # → http://localhost:5100
```

**Resolution order** (highest → lowest priority):
1. `TERMINAL_DEPTHS_URL` env var (explicit override)
2. `TD_URL` env var (short alias)
3. `config.runtime.SELF_PORT` auto-detect (`REPL_ID` → 5000, else → 7337)
4. Port probing via `probe_td_url()` (only needed by health-check scripts)

`mcp/server.py` uses this shim via `_TD_BASE` — the 30 former inline `os.environ.get(...)` calls were replaced in the port-shim sprint.

---

## What Lives Where

```
Dev-Mentor/
├── app/
│   ├── backend/        ← DevMentor: FastAPI routes, startup, middleware
│   ├── game_engine/    ← Terminal Depths: 534 handlers, state, NPCs
│   └── frontend/       ← Terminal Depths: xterm.js UI, game panels
├── agents/
│   ├── serena/         ← DevMentor: drift detection, policy, memory walks
│   ├── gordon/         ← DevMentor: autonomous player, strategic loop
│   ├── chug/           ← DevMentor: continuous improvement engine
│   └── rl/             ← DevMentor: RL environment, PPO trainer
├── cli/                ← DevMentor: `python -m cli.devmentor serve`
├── mcp/                ← DevMentor: MCP server (Claude/Copilot/Continue.dev)
├── mods/
│   └── TerminalKeeper/ ← Terminal Keeper: C# RimWorld mod ONLY
├── services/
│   ├── rimapi_bridge.py  ← Terminal Keeper bridge
│   └── ...             ← DevMentor: sidecar services
├── config/
│   ├── port_map.json   ← DevMentor: health/port registry
│   └── personalities/  ← DevMentor: 71 agent YAML personalities
├── state/              ← All systems: SQLite databases (10 DBs)
├── docs/
│   ├── temple/         ← Terminal Depths: 11-floor ARG temple docs
│   └── ...             ← DevMentor: technical docs
├── TORCH.md            ← DevMentor: agent onboarding (read first)
├── NEXT_ACTIONS.md     ← DevMentor: engineering backlog
├── AGENTS.md           ← DevMentor: universal agent entry point
└── SYSTEM_ARCHITECTURE.md  ← This file
```

---

## Integration Matrix

```
Claude Code + Copilot Chat
  → MCP server (mcp/server.py) via .vscode/mcp.json
    → 16 tools: read/write files, game commands, semantic search, git push
      → needs: python mcp/server.py running (stdio mode, always-on)

Continue.dev (Ollama / LM Studio)
  → .vscode/continue/config.json
    → models: qwen2.5-coder, codestral, etc. via Ollama
      → needs: Ollama running on :11434

GitHub Copilot Inline
  → github.copilot VS Code extension
    → no special config needed; just the extension

RimWorld + Terminal Keeper
  → mods/TerminalKeeper/ C# → REST API calls to :7337/api/game/command
    → RimAPI bridge → Redis pub/sub → Gordon/Serena subscribe
      → needs: docker compose --profile rimworld up
```

---

*Last updated: Sprint 26 (Agent Torch-Passing)*
*Maintained by: Serena (Memory Palace, walk_repo) + human dev*

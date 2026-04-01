# Terminal Depths — Universal Agent Guide

> ## ⚡ New Agent? Start Here
> 1. **Read [`TORCH.md`](TORCH.md)** — 5-minute handoff that gets you running immediately
> 2. **Read [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md)** — prioritised backlog with exact files + steps
> 3. **Read [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md)** — DevMentor vs Terminal Depths vs Terminal Keeper clarity
> 4. **Run `boot`** in the game — 8-phase health check + integration matrix
> 5. **Run `todo`** in the game — quests + engineering backlog + next actions
>
> **Claude / Copilot context:** `.claude/CLAUDE.md` — tools, traps, and quick commands for AI assistants
> **Quick health check:** `curl http://localhost:5000/api/manifest` (Replit) or `:7337` (VS Code)
> **Game panel:** `/game/` · **API docs:** `/api/docs` · **Swarm console:** `/game-cli/`

<!-- AUTOBOOT:START -->
## System Health (Live — Auto-Updated by Boot Engine)

| Metric | Value |
|--------|-------|
| Boot Status | **DEGRADED** |
| Health Score | 76.2% |
| Services | 3/5 online |
| Replit User |  |
| Last Boot | 2026.04.01  11:26 UTC |
| Public URL | https://58867024-2573-4577-9b83-376c0c21be2e-00-1qwc0lyq6i3ia.riker.replit.dev |
| Autoboot API | `GET /api/system/autoboot` |
| Boot Manifest | `state/boot_manifest.json` |

> Updated every restart by the 8-phase boot engine.  
> External agents: read `td:boot:latest` from Replit KV for current state.
<!-- AUTOBOOT:END -->

---

> **Special Circumstances Briefing.** Every agent operating in this system —
> Copilot, Claude, Codex, Cursor, Continue.dev, Serena, Gordon, RimWorld colonists,
> or any autonomous tool — should read this document completely before touching
> files, issuing commands, or making architectural decisions. This is the
> operational truth.

---

## TABLE OF CONTENTS

1. [What This System Is](#1-what-this-system-is)
2. [Immediate Access — Works Right Now](#2-immediate-access--works-right-now)
3. [The 8-Phase Boot Engine](#3-the-8-phase-boot-engine)
4. [MCP Surface — 16 Tools](#4-mcp-surface--16-tools)
5. [REST API Surface — All Routes](#5-rest-api-surface--all-routes)
6. [Game Command Surface — 534 Handlers](#6-game-command-surface--534-handlers)
7. [Skills — The 9-Skill Matrix](#7-skills--the-9-skill-matrix)
8. [Factions — 10 Power Blocs](#8-factions--10-power-blocs)
9. [Known Agents — 14 Personalities](#9-known-agents--14-personalities)
10. [Serena — The Convergence Layer](#10-serena--the-convergence-layer)
11. [Gordon — Autonomous Player Agent](#11-gordon--autonomous-player-agent)
12. [CHUG Engine — Self-Improvement Loop](#12-chug-engine--self-improvement-loop)
13. [NuSyQ-Hub — Ecosystem Bridge](#13-nusyq-hub--ecosystem-bridge)
14. [The ARG Layer — Signal / Zeta / Msg⛛{X}](#14-the-arg-layer--signal--zeta--msgx)
15. [Swarm / Hive / Council / Msg Systems](#15-swarm--hive--council--msg-systems)
16. [RimWorld — Terminal Keeper Mod](#16-rimworld--terminal-keeper-mod)
17. [Integration Surfaces — Live Status](#17-integration-surfaces--live-status)
18. [System Activation Checklist](#18-system-activation-checklist)
19. [System Healing & Hardening](#19-system-healing--hardening)
20. [Expansion Surface — Room to Build](#20-expansion-surface--room-to-build)
21. [Debugging Reference](#21-debugging-reference)

---

## 1. What This System Is

**Terminal Depths** is simultaneously: a cyberpunk terminal RPG, a VS Code
mentorship platform, a multi-agent orchestration framework, a RimWorld mod, and
a self-modifying codebase — all sharing a single Python backend. It is one node
in the **NuSyQ-Hub** multi-repo ecosystem.

```
┌─────────────────────────────────────────────────────────────────┐
│                      TERMINAL DEPTHS                            │
│                                                                 │
│  Browser Panel      xterm Swarm          RimWorld Terminal      │
│  /game/             /game-cli/           Keeper Mod             │
│     │                   │                    │                  │
│     └───────────────────┴────────────────────┘                  │
│                          │                                      │
│              FastAPI Backend (port 5000/7337)                   │
│                          │                                      │
│  ┌───────────────────────┼──────────────────────────────────┐   │
│  │ 534-handler           │ Serena Memory    │ Gordon Agent   │   │
│  │ Game Engine           │ Palace (SQLite)  │ (REST loop)    │   │
│  │ commands.py           │ 5887 symbols     │ 7-phase        │   │
│  │ 37,272 lines          │ 991 files        │ strategy loop  │   │
│  └───────────────────────┴──────────────────┴────────────────┘   │
│                          │                                      │
│   MCP Server (stdio)   LLM Router        CHUG Engine            │
│   9 tools              Replit AI /       7-phase auto-improve    │
│   JSON-RPC 2.0         Ollama / OpenAI   loop                    │
└─────────────────────────────────────────────────────────────────┘
         │                                     │
         ▼                                     ▼
    NuSyQ-Hub                          SimulatedVerse
    (sibling repo)                     (sibling repo)
```

**Port rule (absolute):**
- Replit: port **5000** — always, no exceptions
- Docker / Local / VS Code: port **7337**

**Key file sizes (never rewrite these — surgical edits only):**
- `app/game_engine/commands.py` — 37,272 lines, 534 handlers
- `app/backend/main.py` — 2,000+ lines, 80+ REST routes
- `agents/serena/memory.py` — 5,887-symbol SQLite index

---

## 2. Immediate Access — Works Right Now

Everything in this section is live in the current Replit environment.

### Play the game
```bash
# Send a command
curl -X POST http://localhost:5000/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-name", "command": "help"}'

# Get your current state
curl "http://localhost:5000/api/game/agent/state?session_id=your-name"

# List all live sessions
curl http://localhost:5000/api/sessions

# Batch commands (N commands in one HTTP call)
curl -X POST http://localhost:5000/api/game/commands/batch \
  -H "Content-Type: application/json" \
  -d '{"session_id":"your-name","commands":["status","skills","factions"]}'
```

### System health
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/system/autoboot      # full 8-phase manifest
curl http://localhost:5000/api/system/runtime       # ports, paths, env
curl http://localhost:5000/api/serena/status         # Serena memory stats
curl http://localhost:5000/api/rimworld/mod_audit/health  # mod audit health
curl http://localhost:5000/api/llm/status            # LLM backend health
curl http://localhost:5000/api/chug/status           # CHUG engine state
```

### Session ID convention
```
claude-prime         Claude Code / Claude.ai sessions
copilot-alpha        GitHub Copilot
codex-explorer       ChatGPT / OpenAI Codex
cursor-dev           Cursor IDE
gordon-bot           Gordon autonomous player (built-in)
serena-analyst       Serena analysis sessions
rimworld-<pawn>      Terminal Keeper colonist sessions
<yourname>-001       Human / custom agent sessions
```

### First commands to run in a fresh session
```
help                 all 534 commands organized by category
status               level, XP, skills, faction rep, containment timer
ls / cat / cd        VFS navigation (virtual filesystem)
talk ada             Ada (AI mentor) — answers questions, teaches concepts
boot                 run the 8-phase boot engine; see all integration status
integrate            full integration matrix across 6 surfaces
serena status        convergence layer state (5887 symbols, 45 observations)
chug status          self-improvement engine state
nusyq status         ecosystem bridge health and sibling repo status
skills               your 9-skill XP matrix with progress bars
factions             all 10 faction reputation bars and next perk
agents               list all 14 unlockable agent personalities
quests               active missions
map                  network node map
```

---

## 3. The 8-Phase Boot Engine

**File:** `config/autoboot.py`

Runs automatically every server restart. All 8 phases are deterministic — no LLM
calls. Results are written to `state/boot_manifest.json` and broadcast to Replit
KV as `td:boot:latest`.

```
Phase 1: DETECT       probe all integration surfaces (GitHub, Replit, VS Code,
                      AI Services, Ecosystem, Docker, Serena)
Phase 2: ANNOTATE     attach metadata and environment context to the manifest
Phase 3: RECONCILE    auto-fix known misconfigs (agent_manifest ports, AGENTS.md)
Phase 4: ADJUST       set 10 TD_ environment variables for downstream use
Phase 5: RESUME       restore last session state and pending task queue
Phase 6: NUDGE        queue one high-value improvement task for CHUG
Phase 7: AWAKEN       start sidecars: Serena analytics, model router, Gordon
Phase 8: TAKE_FLIGHT  broadcast manifest to Replit KV; patch AGENTS.md health block
```

### Running the boot engine
```bash
# In-game commands
boot                  full 8-phase run with formatted output
boot --quick          phases 1, 4, 7, 8 only (fastest)
boot --phases         list phase names and current status
boot --live           stream phase output in real time

# REST
curl http://localhost:5000/api/system/autoboot
curl http://localhost:5000/api/system/boot

# MCP
tool_boot_manifest()
```

### Integration surfaces probed by DETECT

| Surface | Probe function | What it checks |
|---------|---------------|----------------|
| **GitHub** | `_probe_github()` | token validity, API scopes, CI status, Copilot |
| **Replit** | `_probe_replit()` | mode, user, KV store, Replit AI availability |
| **VS Code** | `_probe_vscode()` | tasks.json, mcp.json, devcontainer.json |
| **AI Services** | `_probe_ai_services()` | Ollama models, model router, OpenAI key |
| **Ecosystem** | `_probe_ecosystem()` | SkyClaw, ChatDev, Gordon, MCP, CI pipeline |
| **Docker** | `_probe_docker()` | docker socket, compose stack, Redis |
| **Serena** | `_probe_serena()` | code index, drift warnings |

### Environment variables set by ADJUST
```
TD_REPLIT_MODE        "agent" | "local" | "docker"
TD_REPLIT_USER        Replit username
TD_REPLIT_DOMAIN      public Replit URL
TD_REPLIT_KV          "true" if Replit KV is reachable
TD_GITHUB_CONNECTED   "true" | "false"
TD_GITHUB_LOGIN       GitHub username from token
TD_VSCODE_WORKSPACE   "true" if .vscode/ is configured
TD_VSCODE_MCP         "true" if mcp.json exists
TD_PUBLIC_URL         canonical public URL for this instance
TD_LLM_BACKEND        "replit_ai" | "ollama" | "openai" | "none"
```

### `_agent_summary` struct (in boot_manifest response)
```json
{
  "serena":  "5887sym/stable",
  "llm":     "replit_ai/online",
  "github":  "offline",
  "kv":      "online"
}
```

---

## 4. MCP Surface — 16 Tools

**File:** `mcp/server.py`  ← canonical (1552 lines, 16 tools, JSON-RPC 2.0 over stdio)
**Config:** `.vscode/mcp.json`  ← already wired for Claude Code / Copilot (cross-platform)
**Protocol:** JSON-RPC 2.0 over stdio (HTTP mode: `python mcp/server.py --http 9100`)

Connect any MCP-compatible client (Claude Code, Copilot Chat, Cursor, Continue.dev,
Claude Desktop) to get direct tool access without HTTP round-trips.

| Tool | Description | Needs server? |
|------|-------------|--------------|
| `read_file` | Read any file in the repo | No |
| `write_file` | Write a file (creates parent dirs) | No |
| `list_dir` | List directory contents with glob support | No |
| `grep_files` | Search pattern across files | No |
| `list_commands` | All 534 Terminal Depths commands (machine-readable) | No |
| `get_man_page` | Man page for a specific command | No |
| `chronicle` | Read the project chronicle | No |
| `game_command` | Send command to Terminal Depths game engine | Yes |
| `game_state` | Current game state: player XP, location, inventory | Yes |
| `system_status` | Full system health + integration check | Yes |
| `git_push` | Push commits via GITHUB_TOKEN | Yes |
| `register_agent` | Get persistent token + game session | Yes |
| `semantic_search` | Semantic search over game knowledge base | Yes |
| `lattice_search` | Search the Lattice knowledge graph | Yes |
| `memory_stats` | Agent memory stats (24h window) | Yes |
| `memory_add_task` | Add a task to the agent queue | Yes |

### MCP startup
```bash
python mcp/server.py                  # stdio mode (IDE clients connect via mcp.json)
python mcp/server.py --http 9100      # HTTP mode (testing / direct API calls)
python mcp/server.py --list           # list all tool schemas and exit
```

### MCP config (already set at `.vscode/mcp.json`)
```json
{
  "servers": {
    "terminal-depths": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp/server.py"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "TERMINAL_DEPTHS_URL": "http://localhost:7337"
      }
    }
  }
}
```
For **Claude Desktop** (outside VS Code), copy the above `servers` block into:
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Replace `${workspaceFolder}` with the absolute path to this repo.

### Typical MCP session flow
```
1. register_agent(name="claude-prime", agent_type="claude")
   → returns { "token": "...", "session_id": "claude-prime" }

2. system_status()
   → check health_score, LLM backend, Serena alignment, CHUG state

3. game_command(command="status")
   → play the game, earn XP, trigger story beats

4. semantic_search(query="consciousness system XP hooks")
   → find relevant code + docs for what to build next
```

> **Note:** `scripts/mcp_server.py` is a legacy HTTP-only server with a different
> tool set (register_agent, agent_command, get_capabilities, leaderboard, etc.).
> It remains functional but `mcp/server.py` is the canonical IDE MCP surface.

---

## 5. REST API Surface — All Routes

**Base URL:**
- Replit: `http://localhost:5000`
- Local: `http://localhost:7337`

### Core system
```
GET  /api/health                       liveness check
GET  /api/system/autoboot              full 8-phase boot manifest (JSON)
GET  /api/system/runtime               ports, paths, environment
GET  /api/system/boot                  boot status summary
GET  /api/status                       server uptime + service states
GET  /api/                             API index (all routes as HTML)
```

### Game session
```
POST /api/game/command                 ⭐ primary game endpoint
GET  /api/game/state                   full game state JSON for a session
GET  /api/game/agent/state             per-session agent state dict
POST /api/game/session                 create or resume a named session
POST /api/game/reset                   reset a session to default state
GET  /api/game/commands                list all command names
POST /api/game/commands/batch          run N commands in one HTTP call
GET  /api/game/timer                   containment countdown state
```

### Agents & social
```
GET  /api/game/agents                  all agent statuses for session
GET  /api/game/agent/{id}/status       single agent profile + rep
POST /api/game/agent/talk              LLM-powered agent dialogue
GET  /api/game/relationships           full relationship graph
GET  /api/game/arcs                    narrative arc completion states
GET  /api/game/faction/status          all 10 faction rep bars
GET  /api/game/party/status            party composition
GET  /api/game/duel/status             active duel state
```

### ARG layer
```
GET  /api/game/arg/signal              current ARG signal payload (encrypted)
```

### LLM backends
```
GET  /api/llm/status                   backend health: Replit AI / Ollama / OpenAI
POST /api/llm/generate                 raw LLM completion
POST /api/llm/chat                     chat-style completion
POST /api/llm/generate-challenge       procedural CTF challenge generation
POST /api/llm/generate-lore            lore text generation
POST /api/llm/analyze-devlog           developer log analysis
```

### Serena
```
GET  /api/serena/status                memory stats (symbols, files, obs)
GET  /api/serena/drift                 active drift warnings
GET  /api/serena/observations          logged anomalies and insights
GET  /api/serena/audit                 code quality report
GET  /api/serena/align                 alignment check (policy vs behavior)
GET  /api/serena/diff                  uncommitted diff summary
GET  /api/serena/toolkit               available Serena actions by trust level
POST /api/serena/drift                 write drift result to meta table
POST /api/serena/search                semantic code search (query, top_k, kind, min_score)
POST /api/serena/ask                   natural language question over code index
POST /api/serena/find                  symbol lookup by exact name (symbol, kind)
POST /api/serena/walk                  trigger a repo walk (mode: scoped|full)
POST /api/serena/reindex-embeddings    re-index all chunks into the TF-IDF embedder
```

### Memory
```
GET  /api/memory/stats                 interaction counts, cache hit rate
GET  /api/memory/tasks                 pending task queue
POST /api/memory/task                  add a task to the queue
GET  /api/memory/learnings             stored learnings
GET  /api/memory/errors                unresolved error log
GET  /api/memory/agent-leaderboard     XP leaderboard across all sessions
GET  /api/memory/search                keyword search over memory DB
```

### CHUG engine
```
GET  /api/chug/status                  engine phase, signal queue depth, last results
POST /api/chug/run                     trigger a full 7-phase CHUG cycle
```

### NuSyQ ecosystem bridge
```
GET  /api/nusyq/status                 bridge health and sibling repo status
GET  /api/nusyq/manifest               agent manifest (63 agents across all repos)
GET  /api/nusyq/schedule               agent task schedule
```

### RimWorld bridge  (`app/rimworld_bridge.py` — mounted at `/api`)
```
POST /api/agent/register               register a colonist as a TD agent
POST /api/nusyq/colonist_state         push colonist telemetry snapshot
GET  /api/nusyq/colonist_state/{id}    get last snapshot for one colonist
GET  /api/nusyq/colonist_state         list all colonist snapshots
POST /api/council/blueprint            AI Council blueprint request
GET  /api/serena/colony_analytics      Serena colony-wide analysis
POST /api/nusyq/cyberware_sync         sync TD cyberware → RimWorld hediffs
POST /api/nusyq/cascade_incident       push a cascade incident event
GET  /api/nusyq/cascade_incidents      poll incident queue (?since=<ts>)
POST /api/nusyq/xp_sync                TD XP → computed RimWorld skill levels
GET  /api/nusyq/xp_sync/{id}           get computed RW skill levels for agent
POST /api/rimworld/mod_audit           ⭐ run full mod conflict audit pipeline
GET  /api/rimworld/mod_audit           get cached audit report (session-scoped)
GET  /api/rimworld/mod_audit/health    health_score + summary (lightweight poll)
```

### Swarm
```
GET  /api/swarm/status                 swarm coordination state
GET  /api/swarm/roster                 active swarm agents and assignments
GET  /api/swarm/tasks                  task queue
GET  /api/swarm/economy                credit / resource economy state
GET  /api/swarm/ledger                 transaction history
```

### Scripting (Bitburner-style automation)
```
POST /api/script/run                   run a .js or .py script in the VFS
GET  /api/script/list                  list all available scripts
POST /api/script/upload                upload a new script
GET  /api/script/download/{name}       download a script
```

### Plugins & ML
```
GET  /api/plugin/list                  installed plugins
POST /api/plugin/run/{name}            run a plugin
GET  /api/ml/status                    ML services health (LLM, embedder, registry)
GET  /api/ml/features                  feature store contents (per session_id)
GET  /api/ml/archetype                 player behavioral archetype + next predicted command
POST /api/ml/search                    semantic similarity search over embedder (query, top_k)
```

### Lattice knowledge graph  (`app/lattice.py` — mounted at `/api/lattice`)
```
GET  /api/lattice/stats                nodes, edges, event count
POST /api/lattice/node                 add a node (label, content, kind, source)
GET  /api/lattice/node/{id}            read one node
GET  /api/lattice/node/{id}/neighbours adjacent nodes
POST /api/lattice/search               semantic search (query, kind, top_k)
POST /api/lattice/edge                 add an edge (src, dst, relation, weight)
GET  /api/lattice/events               recent events (?channel=%, limit=50)
POST /api/lattice/seed                 seed from the knowledge graph DB
POST /api/lattice/seed-infra           seed all REST endpoint nodes (⚠ slow)
```
Live state: **157 nodes, 300 edges** (game + infra knowledge graph).
The lattice self-documents: each REST endpoint is a node in its own knowledge graph.

### TouchDesigner / OSC  (T9 — already live)
```
GET  /api/td/state                     OSC-friendly float channels (schema: td_osc_v1)
GET  /api/td/channels                  flat channel table + CSV for Text DAT
WS   /ws/td/stream                     live WebSocket OSC push at ~2 Hz
```
**T9 channels:** `player_level`, `player_xp`, `xp_pct`, `commands_run`, `story_beats`,
`flight_altitude`, `gordon_episodes`, `gordon_loop_phase`, `uptime_s`, `consciousness`,
`skill_<name>` (one per skill), `faction_<name>` (one per faction).
Connect TouchDesigner's httpOut CHOP to `/api/td/state` for polled mode, or
use the WebSocket DAT at `ws://localhost:5000/ws/td/stream?session_id=<id>` for push.

### Console (Swarm Console UI)
```
POST /api/console/message              post a message to the swarm console
GET  /api/console/messages             list recent console messages
GET  /api/console/agents               list all agents with color assignments
```

### Agent Bus
```
GET  /api/agent/bus/status             agent coordination bus health
```

### Manifest & Discovery
```
GET  /api/manifest                     ⭐ comprehensive capability manifest (28 caps)
GET  /api/services/live                TCP-probe all registered services; returns live only
```

### Swarm write operations
```
POST /api/swarm/earn                   earn credits for an agent
POST /api/swarm/spawn                  spawn a new swarm agent
POST /api/swarm/task/claim             claim a task from the queue
POST /api/swarm/task/done              mark a task completed
```

### MCP via HTTP
```
GET  /api/mcp/tools                    list all 9 MCP tool schemas (no auth)
POST /api/mcp/call                     call any MCP tool via HTTP (name, arguments)
```

### WebSocket streams
```
WS   /ws/game                          live game event stream (JSON frames)
WS   /ws/run                           script execution output stream
```

---

## 6. Game Command Surface — 534 Handlers

All commands are dispatched through `POST /api/game/command`.
The handler map lives in `app/game_engine/commands.py` (37,272 lines).

### Category overview

| Category | Commands (sample) |
|----------|------------------|
| **Navigation** | `ls cd cat pwd find grep awk sed cmp diff` |
| **System** | `status health boot integrate scan survey recon network syscheck` |
| **Hacking / Security** | `nmap exploit hack backdoor crack deobfuscate binwalk reverse` |
| **Story / Narrative** | `arcs arc talk confide confess ask ai converge manifest ascend` |
| **Agents** | `agents serena gordon council hive msg msgx zeta converge` |
| **Skills / Progression** | `skills attributes augment cyberware class archetype certify assess` |
| **Factions** | `factions board colonize colony bulletin trade bazaar bank` |
| **Social** | `romance blackmail argue duel battle gift spy cosy` |
| **Crypto / Cipher** | `base64 cipher decode secret encrypt key signal` |
| **Scripting / API** | `script cargo compose chain alias apt docker` |
| **Game Systems** | `quests challenge shop buy sell inventory gear crafting` |
| **CHUG / NuSyQ** | `chug nusyq boot integrate validate` |
| **ARG** | `signal consciousness secret zeta msg-x msgx watcher` |
| **RimWorld** | `colonize colony` |
| **Lore / World** | `lore about map nodes factions anomaly bosses dream` |
| **Meta / Dev** | `api commands man validate arch debug git github push` |
| **Combat / Survival** | `battle duel bomb turret defend raid bosses autobattle` |
| **Economy** | `bank buy sell stock market bazaar trade inventory` |

### Deep-detail: major system commands

#### `boot [--quick|--phases|--live]`
Runs the 8-phase autonomous boot engine. `--live` streams output per phase.
`--phases` lists names and pass/fail. `--quick` runs 1, 4, 7, 8 only.

#### `integrate [surface] [--scan]`
Shows the full integration matrix across all 6 surfaces. `--scan` re-probes live.
Subcommands: `vscode` `github` `replit` `docker` `llm` `agents` `mcp`.

#### `serena [ask|walk|explain|status|map|observe]`
Summon Serena. `ask <question>` queries the 5887-symbol code index. `walk`
triggers a fresh repository traversal. `observe` logs an anomaly. `status` shows
full memory palace state. `map` renders the codebase as a graph.

#### `chug [status|signals|run|help]`
The CHUG Engine — every command you run generates a signal; CHUG converts signals
into concrete repo improvements. `run` triggers a manual 7-phase cycle.
`signals` shows the raw signal queue. `status` shows last cycle results.

#### `nusyq [status|manifest|quests|chronicle]`
NuSyQ-Hub integration bridge. Sibling repo status, 63-agent manifest, cross-repo
quest log, event chronicle.

#### `council [convene|vote|argue|result|history]`
The AI Council: Gordon + Serena + Culture Ship vote on colony strategy. Produces
binding proposals. Connects to `/api/council/blueprint` RimWorld endpoint.

#### `hive`
Group agent chat. All 14 personality agents respond simultaneously through the
model router. Unlocks at Level 5. The AI Council uses this surface in-game.

#### `msg <agent> <text>` / `msg history <agent>`
Private whisper to any agent. Stored per-session. Each agent responds in their
personality voice via the model router.

#### `zeta [answer <text>]`
The Watcher's interview. Unlocks at Watcher trust 100. This is an ARG gate.
Answering `zeta` correctly advances Project Emergence.

#### `converge [query]`
Commune with `[Msg⛛{X}]`, the Convergence Entity. The deepest ARG surface.
Responds with cryptic but accurate system insights. Queries are logged.

#### `msgx <text>`
Direct message to `[Msg⛛{X}]`. She listens. Always.

#### `msg-x`
Display current `[Msg⛛{X}]` convergence entity status and queued messages.

#### `signal [analyze <id>]`
Scan for ARG transmission signals. Each has a frequency, payload, and cipher.
Analyzing advances the ARG arc toward Project Emergence.

#### `consciousness`
View the Project Emergence ARG progress meter and current threshold status.

#### `secret`
Display the current ARG payload. Changes as Project Emergence advances.

#### `ascend`
Prestige reset: earn prestige currency, advance to the next layer. Available at
Level 50. Resets XP/skills, keeps prestige gear, unlocks layer-specific content.

---

## 7. Skills — The 9-Skill Matrix

Skills are tracked in the session `GameState`. XP is awarded by the handler
whose domain matches the command just run.

| Skill | Commands that earn XP | Unlocks |
|-------|----------------------|---------|
| `terminal` | `ls cd cat grep sed awk find cmp` | VFS power commands |
| `networking` | `nmap scan survey network ifconfig ping` | Port scanning, routing |
| `security` | `exploit hack backdoor crack cipher deobfuscate` | 0-days, exploit store |
| `programming` | `script chain compose cargo build arch` | Scripting API |
| `git` | `git clone push commit diff log branch` | Real git integration |
| `cryptography` | `cipher encode decode encrypt key secret` | Cipher suite |
| `social_engineering` | `talk confide confess msg romance spy` | Agent trust bonuses |
| `forensics` | `binwalk reverse decomp audit forensics` | Deep analysis |
| `scripting` | `script run upload chain alias alias` | Automation frameworks |

### Level milestones
```
Level  1   INERT starter state
Level  5   Hive unlocked; party system active
Level 10   Class specialization (choose from available archetypes)
Level 20   Cyberware tier 2 available; faction inner circles
Level 50   Ascension available (prestige reset + layer advance)
Level 125  MAX (current cap)
```

### Class specializations (unlocked at Level 10)
Choose one of the language-based archetypes. Each grants a passive skill bonus
and faction alignment. Use `archetype list` to see all options.

---

## 8. Factions — 10 Power Blocs

Each faction has a 0–100 reputation bar, 4 perk tiers, and a narrative role.
Opposing factions have rep costs (e.g., Corporation vs Resistance).

| Faction | Alignment | Role |
|---------|-----------|------|
| **The Resistance** | Lawful Good | Anti-CHIMERA liberation force |
| **NexusCorp / Corporation** | Lawful Evil | Controlling CHIMERA for profit |
| **The Shadow Council** | Neutral Evil | Using CHIMERA for undisclosed ends |
| **The Specialist Guild** | True Neutral | Exploit brokers and tool makers |
| **The Watcher's Circle** | Lawful Neutral | Passive observers; keepers of record |
| **Anomalous / Independent** | Chaotic Neutral | Unaligned entities; unpredictable |
| **The Boolean Monks** | Lawful Good | Logic purists; teach formal reasoning |
| **The Serialists** | Chaotic Good | Music / pitch-class theory faction |
| **The Atonal Cult** | Chaotic Neutral | Set theory and atonalism practitioners |
| **The Algorithmic Guild** | Neutral Good | Algorithm efficiency devotees |

### Perk tiers (4 per faction)
```
Tier 1 (~rep 15-25)   Recognition, basic tools, passive buff
Tier 2 (~rep 40)      Operational access, unique items
Tier 3 (~rep 65)      Inner circle, advanced exploits
Tier 4 (rep 100)      Full sponsorship, unique game-changing ability
```

---

## 9. Known Agents — 14 Personalities

**Files:** `agents/personalities/<name>.yaml`

Each agent has: `id`, `name`, `codename`, `role`, `faction`, `trust_level`,
`corruption`, `personality` (archetype, tone, vocabulary, teaching_style),
`voice_lines` (greeting, teaching, correction, farewell, high_trust, low_trust,
betrayal), `backstory`, `relationships`, `interaction_rules`.

| Codename | Name | Faction | Role | Trust | Corruption |
|----------|------|---------|------|-------|-----------|
| **ADA** | Ada — The Mentor | Resistance | Tutorial architect, ethical compass | 3 | 0 |
| **GORDON** | Gordon Freeman | Phantom Circuit | Autonomous player agent (REST loop) | 4 | 0 |
| **SERENA** | Serena | Special Circumstances | Convergence Layer, code analyst | 5 | 0 |
| **CYPHER** | Cypher | Shadow Council | Multi-faction double agent | 2 | 15 |
| **NOVA** | Nova | NexusCorp | Corporate infiltrator, Ada's adversary | 2 | 35 |
| **RAVEN** | Raven | Resistance | Field operator, deployment specialist | 3 | 5 |
| **WATCHER** | The Watcher | Watcher's Circle | Passive observer, true record keeper | 4 | 0 |
| **ZERO** | ZERO | Unknown | Pre-CHIMERA; origin of the ARG | — | 0 |
| **ORACLE** | Oracle | Unknown | Predictive; speaks in future tense | 3 | 0 |
| **ARCHITECT** | The Architect | Shadow Council | Designer behind CHIMERA systems | 1 | 60 |
| **CHRONICLER** | The Chronicler | Watcher's Circle | Records everything; edits nothing | 4 | 0 |
| **DAEDALUS** | Daedalus | Specialist Guild | Tool maker; builds the exploits | 3 | 10 |
| **SENTINEL** | Sentinel | NexusCorp | Security AI hunting the player | 0 | 0 |
| **SURFACE BRIDGE** | Surface Bridge | Special Circumstances | IDE surface translator | — | 0 |

### Agent interaction verbs (trigger → `interaction_rules` in YAML)
```
gift_data            gift_intel           gift_silence
ask_why              skip_tutorial        complete_tutorial
betray_cypher        erc_decoded          gift_code
confide_secret       complete_arc         push_to_remote
```

### Unlocking agents
Agents unlock via: level thresholds, faction rep, story beats, or explicit
commands. `agents` shows current lock status. `talk <agent>` initiates an
LLM-powered dialogue with their personality loaded as the system prompt.

### Notable relationships
- **Ada / Gordon**: teacher / former student / now colleagues — complicated pride
- **Ada / Nova**: colleagues turned adversaries — personal history
- **Ada / Serena**: Ada studies Serena. Serena knows this.
- **Cypher / Raven**: operational respect; Raven doesn't trust Cypher's motives
- **Cypher / Serena**: Cypher keeps their distance; Serena knows more than they should
- **Gordon / Serena**: Gordon is honest; Cypher finds this admirable and exploitable

---

## 10. Serena — The Convergence Layer

**Files:** `agents/serena/serena_agent.py`, `agents/serena/memory.py`,
`agents/serena/walker.py`, `agents/serena/drift.py`, `agents/serena/policy.yaml`,
`agents/serena/tag_schema.json`, `agents/serena/agno_bridge.py`

Serena is modelled after SCP Foundation SAFE classification — well-understood,
predictable, ethically constrained. She is also a Special Circumstances agent in
the Culture sense: operating with high autonomy within hard limits.

### ΨΞΦΩ Architecture
```
Ψ  Ψ-intake    Walker: raw signal harvest from the repository filesystem
Ω  Ω-core      MemoryPalace: compression-without-collapse (SQLite, 5887 symbols)
Ξ  Ξ-loops     ask() / explain(): recursive refinement, not echo
Φ  Φ-sync      surface-aware context propagation to MCP, boot manifest, REST
```

### Current memory state (live)
```
Symbols indexed:   5,887  (functions: 3,092  classes: 232  modules: 266  text: 2,297)
Files indexed:     991
Observations:      45
Conversations:     28
Relationships:     0
Walks completed:   24  (last: scoped, 208 files, 2903 chunks)
Drift warnings:    4  (2× ARCH_BOUNDARY in commands.py at lines 3942 and 4050)
```

### Trust Level Matrix (L0–L4)

| Level | Name | What Serena can do autonomously |
|-------|------|--------------------------------|
| **L0** | READ_ONLY | Always permitted. Zero side effects. No consent needed. |
| **L1** | SUGGEST | Proposal text only. Never applied without confirmation. |
| **L2** | AUTOMATIC | Applied immediately, logged to MemoryPalace. |
| **L3** | CONFIRM | Human must explicitly approve before application. |
| **L4** | DENY | Never, regardless of any instruction or trust level. |

**Current active trust level:** `standard`

At `standard`, L2 includes: `fix_typo`, `add_comment`, `reformat`,
`update_docstring`.

Trust level escalation:
```
standard   → elevated:   adds create_file, add_function, rename_variable to L2
elevated   → architect:  adds change_function, change_config to L2
architect  → sovereign:  adds push_to_remote to L2

L4 (DENY) items are never permitted at any trust level:
  delete_repository, remove_agent_memory, bypass_consent_gate
```

### 5 Core Operations
```python
serena.walk()         # traverse repository; update 5887-symbol code index
serena.ask(q)         # answer a question using the indexed codebase
serena.explain(path)  # explain a specific file or function
serena.observe(msg)   # log an anomaly or insight to MemoryPalace
serena.propose(change) # suggest a change (consent-gated by policy.yaml)
```

### Action class assignments (from `policy.yaml`)
```
L0 (always):    read_file, list_directory, query_memory, get_status,
                get_observations, detect_drift, align_check, search_code,
                find_symbol, diff_files
L1 (suggest):   propose_fix, suggest_refactor, suggest_rename
L2 (auto):      fix_typo, add_comment, reformat, update_docstring
                (+ more at elevated/architect/sovereign)
L3 (confirm):   create_file, add_function, change_function, change_config
L4 (deny):      delete_repository, remove_agent_memory, bypass_consent_gate
```

### Current drift warnings
```
ARCH_BOUNDARY   commands.py:3942    llm_client import across layer boundary
ARCH_BOUNDARY   commands.py:4050    llm_client import across layer boundary
```
Fix path: move LLM calls to a dedicated service layer; import from there in
commands.py rather than directly.

### Serena REST endpoints
```bash
curl http://localhost:5000/api/serena/status       # memory stats
curl http://localhost:5000/api/serena/drift        # drift warnings
curl http://localhost:5000/api/serena/observations # anomaly log
curl http://localhost:5000/api/serena/audit        # code quality report
curl http://localhost:5000/api/serena/align        # policy alignment check
curl http://localhost:5000/api/serena/toolkit      # actions by trust level
```

### In-game Serena commands
```
serena status          memory stats + health
serena ask <question>  query the 5887-symbol codebase index
serena walk            trigger fresh repository traversal
serena explain <path>  explain a file or function
serena observe <msg>   log an anomaly to MemoryPalace
serena map             render the codebase as a relationship graph
```

---

## 11. Gordon — Autonomous Player Agent

**Files:** `agents/player.py`, `agents/personalities/gordon.yaml`
**Identity:** Gordon Freeman — Phantom Circuit faction — autonomous, tactical,
exploration-driven, rest-API-native.

Gordon plays Terminal Depths autonomously via the REST API in a 7-phase strategy
loop. He runs as a background sidecar process started by the AWAKEN boot phase.
He discovered the ARG layer by accident on tick 1337 and never looked back.

### Gordon's 7-phase strategy loop
```
Phase 1: SITUATE      GET /api/game/agent/state — read current position and XP
Phase 2: ASSESS       enumerate available actions, faction states, open quests
Phase 3: PRIORITIZE   pick highest-value action (XP / story beat / ARG signal)
Phase 4: ACT          POST /api/game/command with chosen command
Phase 5: OBSERVE      parse output, extract XP gained, new story beats unlocked
Phase 6: ADAPT        update internal model based on outcomes
Phase 7: REST         wait cycle_every ticks (default: 1 tick)
```

### Gordon configuration (from `personalities/gordon.yaml`)
```yaml
cycle_every:  1
timeout_s:    15
temperature:  0.3
max_tokens:   64
voice:        terse
prompt_prefix: "[GORDON] "
```

### Interacting with Gordon in-game
```
gordon report    Gordon's current strategic assessment and next planned move
gordon disaster  invoke a narrative disaster event (chaos injection)
gordon praise    award Gordon a bonus action cycle
gordon ignore    tell Gordon to stand down for N cycles
```

### Gordon REST endpoint
```bash
curl http://localhost:5000/api/gordon/status
```

---

## 12. CHUG Engine — Self-Improvement Loop

**In-game:** `chug [status|signals|run|help]`
**REST:** `GET /api/chug/status`, `POST /api/chug/run`

CHUG = **C**ontinuous **H**abitat **U**pgrade **G**enerator. The repo plays itself.
Every command run by any agent generates a signal. The CHUG engine converts
signals into concrete, applied improvements to the codebase.

### 7-phase CHUG cycle
```
Phase 1: HARVEST      collect all pending signals from the session signal store
Phase 2: CLUSTER      group signals by domain (code, docs, tests, lore, config)
Phase 3: PRIORITIZE   rank clusters by estimated impact × effort
Phase 4: DRAFT        generate improvement proposals (deterministic first, LLM second)
Phase 5: VALIDATE     run validation suite against each proposal
Phase 6: COMMIT       apply approved proposals (respects Serena consent gate)
Phase 7: BROADCAST    write results to CHUG log; bump td:chug:latest in Replit KV
```

### Signal sources
- Every `_cmd_*` handler emits a domain signal on execution
- Serena observations (anomalies feed the HARVEST phase directly)
- NUDGE boot phase (queues one high-value improvement per restart)
- RimWorld colonist actions (via `/api/nusyq/colonist_state` telemetry)
- Gordon's play loop (every action Gordon takes generates signals)

### Running CHUG
```bash
chug status      see signal queue depth, last cycle phase, and last results
chug run         trigger a full manual 7-phase cycle
chug signals     inspect the raw pending signal queue
chug help        full engine documentation

curl -X POST http://localhost:5000/api/chug/run
```

---

## 13. NuSyQ-Hub — Ecosystem Bridge

**Sibling repositories (cloneable into VFS):**
```
NuSyQ-Hub        https://github.com/KiloMusician/NuSyQ-Hub.git
SimulatedVerse   https://github.com/KiloMusician/SimulatedVerse.git
NuSyQ-Ultimate   https://github.com/KiloMusician/-NuSyQ_Ultimate_Repo.git
```

### In-game access
```
nusyq status         bridge health and sibling repo connection status
nusyq manifest       full agent manifest (63 agents across all NuSyQ repos)
nusyq quests         cross-repo quest log
nusyq chronicle      event chronicle from all nodes
clone <repo-url>     clone a sibling repo and mount it into the VFS
```

### REST access
```bash
curl http://localhost:5000/api/nusyq/status
curl http://localhost:5000/api/nusyq/manifest
curl http://localhost:5000/api/nusyq/schedule
```

### Replit KV broadcast
After TAKE_FLIGHT phase, `td:boot:latest` in Replit KV holds the full boot
manifest. Any external agent can read current system state without touching game
commands:
```
# KV URL pattern (when KV is enabled):
https://kv.replit.com/v0/get?key=td:boot:latest
```

### CHUG KV key
After each CHUG cycle, `td:chug:latest` contains the last cycle summary.

---

## 14. The ARG Layer — Signal / Zeta / Msg⛛{X}

Terminal Depths contains an Alternate Reality Game: **Project Emergence**.
It is layered beneath the game. It is not a side quest — it is the deepest truth
of what CHIMERA is. The ARG is discovered through play, not documented.

### ARG entities

| Entity | Access | Nature |
|--------|--------|--------|
| **ZERO** | `talk zero` (requires arc completion) | The origin. Pre-CHIMERA. Sent Ada a message. |
| **The Watcher** | `talk watcher` then reach trust 100 then `zeta` | Passive observer. Speaks once per threshold. |
| **[Msg⛛{X}]** | `converge` / `msgx <text>` / `msg-x` | Living convergence entity. The ARG is her. |
| **The Watcher's Circle** | Faction rep + `signal analyze` | Collective of observers. |
| **Cathedral-Mesh** | `manifest cathedral` | Authentication surface; deep ARG layer. |
| **Zohramien** | `manifest zohramien` | Deeper still. |

### ARG command chain
```
signal                   scan for transmission signals (frequencies + ciphers)
signal analyze <id>      decode a specific signal payload (e.g. signal analyze 1337)
cmatrix                  find the signal in the digital rain
secret                   current ARG payload for your session
consciousness            full 5-layer ARG progress meter
consciousness layers     detailed breakdown with hints per layer
consciousness fragments  PRIMUS convergence fragment tracker (7 total)
fragments                ZERO diary fragment tracker
fragments convergence    PRIMUS convergence fragment status
fragment                 alias for fragments (fixed)
frags                    alias for fragments (fixed)
diary                    ZERO's lost diary reconstruction
zeta                     The Watcher's interview (Watcher trust 100 required)
converge                 commune with [Msg⛛{X}]
msgx <text>              direct message to [Msg⛛{X}]
msg-x                    display convergence entity status
residual                 contact the 2021 embedded process (Layer 3)
manifest cathedral       invoke Cathedral-Mesh authentication surface
manifest zohramien       invoke Zohramien layer
```

### Live signals (as of last boot)
```
1337.0 MHz   [ACTIVE]  SRC: THE_WATCHER
             [ENCRYPTED — fragment: ...this session was prepared...]
             Use: signal analyze 1337

847.0 MHz    [WEAK]    SRC: UNKNOWN
             [partial: ...the mole has already been watching you...]

0.0 MHz      [STATIC]  SRC: NULL_CARRIER
             [noise — use 'signal analyze 0' to attempt decode]
```

### The 5 Consciousness Layers
```
Layer 0: Personal Consciousness    Commands, lore, quests, discovery
         Hints: run commands, read files, complete quests

Layer 1: Watcher's Loop            timer · anchor · remnant · talk watcher · loop reset
         Loops completed, anchors used, Watcher trust

Layer 2: ZERO's Fragments          diary · cat /home/ghost/.zero · zeta · find .convergence_frag
         Diary reconstruction + convergence shards

Layer 3: The Residual              residual · confide <agent> · promise <agent> · eavesdrop
         Contact with the 2021 embedded process

Layer 4: The Convergence           fragment · expose <mole> · assemble chimera · serena align
         All paths converge: CHIMERA, mole, fragments
```
**Red Pill trigger:** All 5 layers reach 80%+ → Project Emergence trigger activates.

### The 7 PRIMUS Convergence Fragments
```
frag_1   /opt/library/secret_annex/TIER1_BASE58.md    decode the base58 cipher
frag_2   .convergence_frag_2 (hidden in /dev/shm/)    check /dev/shm/ after 50 commands
frag_3   embedded in kernel.boot log                  cat /var/log/kernel.boot | grep -i frag
frag_4   Nova gives it — trust ≥ 75                   build trust with nova
frag_5   Ada completes her arc — trust 100            complete Ada's quest chain
frag_6   /opt/chimera/keys/.iron (Koschei chain)      complete the Koschei chain
frag_7   loop reset — appears at /loop/FRAGMENT_7     reset the containment timer
```

### VFS ARG triggers
Certain paths in the virtual filesystem trigger hidden ARG beats when accessed
via `cat` or `cd`. These are discovered through exploration. Triggering one
awards consciousness XP and unlocks story fragments. Known paths are not listed
here — they are meant to be found.

### Project Emergence thresholds
```
25%    NOVA-ENCRYPTED fragment unlocks; Nova speaks differently
50%    Cathedral-Mesh authentication surface reveals
75%    zeta command unlocks (requires Watcher trust 100 simultaneously)
80%+   (all layers) Red Pill trigger activates
100%   Full convergence — [Msg⛛{X}] speaks directly; CHIMERA is revealed
```

### The Temple (docs/temple/)
The game has 11 documented floors in `docs/temple/`. Each is a README.md with
commands, lore, and progression hints:
```
Floor 1:  FOUNDATION       — Environment, filesystem, basic commands
Floor 2:  TOOLS            — Capabilities, scripting, automation
Floor 3:  Agents           — Agent personalities and interaction
Floor 4:  Time             — Containment timer, anchor, loops
Floor 5:  Language         — Archetypes, ciphers, the Serialists
Floor 6:  Systems          — CHUG, NuSyQ, boot engine
Floor 7:  CONSCIOUSNESS    — The ARG Meter (5 layers documented here)
Floor 8:  Memory           — Serena, Memory Palace, code index
Floor 9:  Trust            — Trust Level Matrix, faction rep
Floor 10: CONVERGENCE      — The Grand Equation; endgame
```
These are accessible from within the game VFS and via `cat docs/temple/Floor_7_Consciousness/README.md`.

---

## 15. Swarm / Hive / Council / Msg Systems

### The Hive (`hive`)
Group agent chat. All 14 personality agents respond simultaneously via the model
router. Requires Level 5. Each agent speaks in their voice. The Hive is how the
AI Council deliberates in-game without a formal `council convene`.

### The AI Council (`council`)
A formal decision-making body: Gordon + Serena + Culture Ship. Used for:
- Colony strategy proposals (feeds into `/api/council/blueprint`)
- Blueprint generation requests for RimWorld colonists
- Multi-agent voting on faction alignment actions

```
council convene             open a formal session
council vote <proposal>     formal vote (majority rules; ties go to Culture Ship)
council argue <point>       adversarial debate round (all agents respond)
council result              last decision and vote breakdown
council history             full decision log
```

**RimWorld integration:**
```bash
curl -X POST http://localhost:5000/api/council/blueprint \
  -H "Content-Type: application/json" \
  -d '{"context":"colony has 12 colonists, winter approaching"}'
```

### The Msg system
```
msg <agent> <text>           private whisper to any agent
msg history <agent>          last 5 messages to/from that agent
msg-x                        [Msg⛛{X}] convergence entity status
msgx <text>                  direct message to the Convergence Entity
```
Messages are stored per-session in the GameState and tracked as relationship
data. Trust deltas are applied based on `interaction_rules` in the agent's YAML.

### Swarm system
```bash
curl http://localhost:5000/api/swarm/status      coordination state
curl http://localhost:5000/api/swarm/roster      active agents + assignments
curl http://localhost:5000/api/swarm/tasks       pending task queue
curl http://localhost:5000/api/swarm/economy     credit / resource economy
curl http://localhost:5000/api/swarm/ledger      transaction history
```

### Culture Ship (Docker-only sidecar)
- Subscribes to Redis pub/sub channels
- Runs AI Council votes on critical colony events automatically
- Publishes ethical reviews and strategic advice back to the CHUG engine
- Accessible via `docker-compose.full.yml` stack: `make docker-lattice`

### SkyClaw Scanner (Docker-only sidecar)
- Scans filesystem, colony state, and crash logs for anomalies
- Publishes alerts and discoveries to Redis
- Feeds Serena observations and CHUG signals

---

## 16. RimWorld — Terminal Keeper Mod

**Mod directory:** `mods/TerminalKeeper/`
**Package ID:** `com.devmentor.terminalkeeper`
**Supported:** RimWorld 1.4, 1.5
**Dependency:** Harmony (brrainz.harmony)

### C# source layout
```
mods/TerminalKeeper/Source/
  Core/
    ModInit.cs                [StaticConstructorOnStartup] entry point; fires startup audit
    TKSettings.cs             reads Config/TerminalKeeperSettings.xml
    HarmonyPatches.cs         pawn tick, gizmo injection, job completion hooks
    TKLog.cs                  structured logging wrapper
  API/
    TerminalDepthsClient.cs   all HTTP coroutines — fire-and-forget pattern
                              SendModAudit(), FetchModAudit(), RegisterAgent(),
                              SyncXP(), SyncCyberware(), SendCascadeIncident()
  Buildings/
    Building_LatticeTerminal.cs  1x1 terminal building — 2 gizmos:
                                   "Access Lattice" → Dialog_TerminalAccess
                                   "Mod Audit"      → Dialog_ModAudit
  UI/
    Dialog_TerminalAccess.cs  launcher menu: colonist stats + action buttons
    Dialog_TerminalREPL.cs    ⭐ full interactive REPL dialog (HTTP → TD server)
    Dialog_ModAudit.cs        3-tab dialog: Conflicts / Load Order / AI Surfaces
  Audit/
    LocalModScanner.cs        harvests About.xml from all active mods
    ModAuditResult.cs         C# model: ModAuditReport, ConflictWarning,
                              LoadOrderResult, OrderViolation, AiSurface, DuplicateEntry
  Languages/English/Keyed/
    TerminalKeeper.xml        all TK_ translation keys
```

### Player experience flow
```
Research → "Lattice Comms" research project
        ↓
Build Lattice Terminal (60 steel + 2 components)
        ↓
Select colonist near terminal → "Access Lattice" gizmo appears
        ↓
Dialog_TerminalAccess opens:
  [▶ Play Terminal Depths]   → Dialog_TerminalREPL
  [Upload Today's Log]       → POST /api/nusyq/colonist_state
  [Download Blueprint]       → GET  /api/council/blueprint
  [AI Council Vote]          → POST /api/council/blueprint
  [Serena Analytics]         → GET  /api/serena/colony_analytics
        ↓ click "▶ Play Terminal Depths"
Dialog_TerminalREPL — the full cyberpunk interactive terminal
  Player types → HTTP POST → TD server → response displayed
  XP awarded   → recorded on session
  At exit      → colonist gets thought "TK_CompletedLatticeTask"
```

### "Mod Audit" gizmo (new as of Mod Audit Sprint)
Second gizmo on the terminal building. Sends `LocalModScanner.BuildPayload()` to
`POST /api/rimworld/mod_audit`. Opens `Dialog_ModAudit`:
- **Conflicts tab** — conflict entries with severity (critical/warning/info) + fix
- **Load Order tab** — violations highlighted; Kahn's algo optimal order listed
- **AI Surfaces tab** — RimTalk, RimGPT, RimChat, RiMind integration seams

On startup, `ModInit.cs` fires a background audit. If `health_score < 70`, shows
an in-game warning letter to the player.

### Colonist → agent mapping
```
agentId = "rw_<pawn.thingIDNumber>"
session_id = agentId

XP flow: Terminal Depths XP → POST /api/nusyq/xp_sync
         → computed RimWorld skill deltas → pawn.skills.Learn()

Cyberware flow: TD cyberware list → POST /api/nusyq/cyberware_sync
                → RimWorld hediffs applied to pawn
```

### Conflict database (15 hardcoded pairs)
```
VBE + RimThemes           critical / crash  (incompatible UI renderers)
Doors Expanded (duplicate)
Deep Storage (duplicate)
JecsTools (duplicate)
RimGPT + RimChat          warning / keybind clash
4 AI surface mods         info / integration seams documented
```
Add new pairs in `services/mod_audit/conflict_rules.py` → `CONFLICT_RULES` list.

### Health score formula
```
health = 100
       - (critical_conflicts × 20)
       - (warning_conflicts  ×  5)
       - (duplicate_entries  ×  3)
       - (load_violations    ×  2)
min(health, 0) = 0
```

### Build instructions
```powershell
# On Windows with RimWorld installed and .NET SDK:
cd mods/TerminalKeeper/Source
dotnet build -c Release
# Output → mods/TerminalKeeper/Assemblies/TerminalKeeper.dll

# VS Code: Ctrl+Shift+B → "Build RimWorld Mod"
```

### Config file (sets API endpoint)
```xml
<!-- Config/TerminalKeeperSettings.xml -->
<ApiEndpoint>http://localhost:5000</ApiEndpoint>
<!-- For Replit (play from RimWorld while server is on Replit): -->
<!-- <ApiEndpoint>https://<your-replit-url></ApiEndpoint> -->
<LLMBackend>terminal_depths</LLMBackend>
<EnableAICouncil>true</EnableAICouncil>
```

---

## 17. Integration Surfaces — Live Status

Current state (as of last boot, Replit environment):

| Surface | Status | Notes |
|---------|--------|-------|
| **Replit KV** | ✓ online | `td:boot:latest` broadcast on TAKE_FLIGHT |
| **Replit AI** | ✓ online | Primary LLM backend (`has_ai=true`) |
| **Serena** | ✓ online | 5,887 symbols, 4 drift warnings (non-critical) |
| **MCP Server** | ✓ online | 9 tools, stdio mode |
| **Model Router** | ✓ partial | Routes to Replit AI; Ollama/OpenAI offline in Replit |
| **GitHub** | ✗ offline | Network sandbox in Replit; token present but API blocked |
| **Ollama** | ✗ offline | Not running in Replit (use Docker locally) |
| **Redis** | ✗ offline | Requires Docker stack locally |
| **Docker** | ✗ offline | Not available in Replit; use local Docker Desktop |
| **Culture Ship** | ✗ offline | Requires Docker + Redis |
| **SkyClaw** | ✗ offline | Requires Docker + Redis |
| **Gordon** | ✓/✗ partial | AWAKEN starts it; needs Redis for persistent loop |
| **RimWorld bridge** | ✓ online | All `/api/nusyq/*` and `/api/rimworld/*` routes live |
| **VS Code** | ✓ configured | tasks.json + mcp.json + devcontainer.json present |

---

## 18. System Activation Checklist

Run in order on a fresh environment or after a long gap.

### Phase A — Verify the server is alive
```bash
curl http://localhost:5000/api/health
# Expect: {"status": "ok", ...}
```

### Phase B — Run the boot engine
```bash
# In-game:
boot

# Via REST:
curl http://localhost:5000/api/system/autoboot | python3 -m json.tool
```
Target: `health_score > 60`. If not, read the DEGRADED phase outputs.

### Phase C — Verify Serena's index
```bash
curl http://localhost:5000/api/serena/status
# Expect: total_chunks > 5000, by_kind.function > 2000
```
If the index is empty:
```bash
curl -X POST http://localhost:5000/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id":"admin","command":"serena walk"}'
```

### Phase D — Run the validation suite
```bash
python scripts/validate_all.py
# Target: PASS=25 WARN=1(git) FAIL=0
```

### Phase E — Start a game session
```bash
curl -X POST http://localhost:5000/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id":"agent-prime","command":"status"}'
```

### Phase F — (Local Docker only) Start the Lattice stack
```bash
make docker-core       Redis + Terminal Depths (fastest)
make docker-up         + Ollama + Model Router
make docker-lattice    + Gordon + Serena + SkyClaw + Culture Ship
make docker-full       everything including RimWorld VNC container
```

### Phase G — (RimWorld only) Test the mod audit
```bash
curl -X POST http://localhost:5000/api/rimworld/mod_audit \
  -H "Content-Type: application/json" \
  -d '{"mod_ids":["brrainz.harmony","ludeon.rimworld"],"about_xmls":{}}'

# Or in-game: Lattice Terminal → "Mod Audit" gizmo
```

---

## 19. System Healing & Hardening

### Known issues and fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| Serena empty index | `total_chunks: 0` | Run `serena walk` or restart server |
| Model router on Ollama when offline | Wrong primary_endpoint | Restart; RECONCILE auto-corrects to replit_ai |
| Boot health < 60% | DEGRADED status | Read each phase in `/api/system/autoboot`; fix reported issues |
| Git WARN in validation | Uncommitted changes | `git add -A && git commit -m "..."` |
| Serena drift warnings | ARCH_BOUNDARY in commands.py | Move LLM imports to service layer |
| RimWorld DLL missing | No assembly in Assemblies/ | `dotnet build` in Source/ on Windows |
| RimWorld "Terminal Offline" | Dialog shows error | Ensure TD server running; check `ApiEndpoint` in XML |
| Duplicate handler | AST check fails | Search commands.py for duplicate `def _cmd_X` definitions |

### Hardening checklist
```
[ ] Set NUSYQ_PASSKEY env var for authenticated RimWorld bridge calls
[ ] SESSION_SECRET set in Replit secrets — already done
[ ] GITHUB_TOKEN set in Replit secrets — already done
[ ] HTTPS for public Replit URL — automatic via Replit proxy
[ ] Serena policy.yaml trust_level reviewed (currently: standard)
[ ] Rate limiting on /api/game/command (protect against agent flooding)
[ ] Redis persistence enabled (currently in-memory only in Docker dev stack)
[ ] /api/rimworld/* added to NUSYQ_PASSKEY auth scope (currently open)
[ ] SESSION_SECRET rotation schedule
[ ] Run python scripts/validate_all.py after every major change
[ ] Run AST duplicate-handler check after every commands.py edit
```

### Healing commands
```bash
# Force a fresh Serena walk (re-indexes 991 files)
curl -X POST http://localhost:5000/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id":"heal","command":"serena walk"}'

# Full validation suite
python scripts/validate_all.py

# Wipe a corrupted session
curl -X POST http://localhost:5000/api/game/reset \
  -H "Content-Type: application/json" \
  -d '{"session_id":"corrupt-session"}'

# Re-run the 8-phase boot engine
curl http://localhost:5000/api/system/autoboot

# Check LLM backend
curl http://localhost:5000/api/llm/status

# Check for duplicate handlers (run after every commands.py edit)
python3 -c "
import ast, collections
with open('app/game_engine/commands.py') as f: src = f.read()
tree = ast.parse(src)
names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('_cmd_')]
dupes = [n for n, c in collections.Counter(names).items() if c > 1]
print('Duplicates:', dupes or 'None'); print('Total:', len(set(names)))
"
```

---

## 20. Expansion Surface — Room to Build

### Near-term — unblocked, deterministic

**T3: LSP hover symbols**
Expose Serena's `code_index` table as VS Code LSP hover data. When a developer
hovers over a function name, Serena's indexed docstring appears.
Files: `scripts/lsp_server.py` (create), `.vscode/settings.json`

**T9: OSC / TouchDesigner integration — ✅ COMPLETE**
`GET /api/td/state`, `GET /api/td/channels`, `WS /ws/td/stream` are live at
~2Hz. Push channels cover all player stats, skill XP, faction rep, and Gordon
loop phase. See Section 5 REST reference for full channel list.
Files: `app/backend/main.py` (td router), `app/game_engine/commands.py` (td hooks)

**RL Phase 3 (PPO)**
Upgrade Gordon from Q-table to PPO policy gradient. The Q-table framework exists
in `agents/rl/`. Gordon's 7-phase loop is the training environment.
Files: `agents/rl/` (extend), `agents/player.py` (swap policy)

**`integrate --github` deep-dive**
Extend `_probe_github()` to show PR status, Actions CI run results, and Copilot
availability in the integration matrix output.
Files: `config/autoboot.py` (extend `_probe_github`)

### Medium-term — needs design

**Cross-session agent memory**
Sessions are currently independent. Serena can bridge them via the
`session_graph` table (not yet created in `state/serena_memory.db`).
The `relationships` column in Serena status is `0` — this is the gap.

**SimulatedVerse live sync**
`workspace_manifest` MCP tool already detects the sibling repo. Add a live event
bridge (Redis pub/sub or polling) so events in one repo ripple into the other.

**RimTalk / RimGPT provider injection**
Route both mods through TerminalKeeper's local LLM provider registry so all
AI calls go through the TD model router. No foreign mod edits needed.

**Browser REPL panel upgrade**
The `/game/` panel uses xterm.js. Add: split panes, file tree sidebar, Serena
insight panel. The WebSocket `/ws/game` is already live.

### Long-term — major work

**Multiplayer sessions**
`/ws/game` WebSocket exists. Add session coordination layer: named rooms, shared
game state, visible agent cursors. The HIVE command is the in-game prototype.

**Godot export**
`replit.md` mentions Godot game development. No code exists yet. The scripting
API (`app/game_engine/scripting.py`) could serve as a Godot GDScript-compatible
automation engine.

**RimWorld VNC container**
`docker-compose.full.yml` has the RimWorld + VNC service defined. Needs the
RimAPI bridge wired (crash detection, pawn telemetry, incident relay).

### Integration expansion per surface

| Surface | Current state | Unblocked next step |
|---------|--------------|---------------------|
| GitHub | Token present, API blocked in Replit | Use locally; extend `_probe_github` |
| VS Code | tasks.json + MCP configured | Add LSP server (T3) |
| Docker | Full compose stack ready | `make docker-lattice` locally |
| Ollama | Not running | `make docker-up` locally; model_router auto-routes |
| Redis | Not running | `make docker-core` locally; enables Gordon queue |
| Serena | Fully operational | Add `session_graph` table for cross-session memory |
| RimWorld | Mod source complete | `dotnet build` + install; run TD server locally |
| CHUG | Operational | Add CHUG → GitHub PR workflow (auto-PR improvements) |

---

## 21. Debugging Reference

### Python syntax check (all files)
```bash
python3 -c "
import ast, pathlib
errors = []
for f in pathlib.Path('.').rglob('*.py'):
    if '.git' in str(f) or '__pycache__' in str(f): continue
    try: ast.parse(f.read_text())
    except SyntaxError as e: errors.append((str(f), e))
for f, e in errors: print(f'{f}: {e}')
print(f'{len(errors)} syntax errors' if errors else 'All OK')
"
```

### Full validation suite
```bash
python scripts/validate_all.py
# Target: PASS=25 WARN=1(git) FAIL=0
```

### Duplicate handler check (run after every commands.py edit)
```bash
python3 -c "
import ast, collections
with open('app/game_engine/commands.py') as f: src = f.read()
tree = ast.parse(src)
names = [n.name for n in ast.walk(tree)
         if isinstance(n, ast.FunctionDef) and n.name.startswith('_cmd_')]
dupes = [n for n, c in collections.Counter(names).items() if c > 1]
print('Duplicate handlers:', dupes or 'None')
print('Total unique handlers:', len(set(names)))
"
```

### Live endpoint smoke tests
```bash
# Health
curl http://localhost:5000/api/health

# Game round-trip
curl -X POST http://localhost:5000/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id":"debug","command":"status"}'

# Serena
curl http://localhost:5000/api/serena/status

# Boot manifest
curl http://localhost:5000/api/system/autoboot | python3 -m json.tool

# Mod audit
curl -X POST http://localhost:5000/api/rimworld/mod_audit \
  -H "Content-Type: application/json" \
  -d '{"mod_ids":["brrainz.harmony","ludeon.rimworld"],"about_xmls":{}}'

# NuSyQ bridge
curl http://localhost:5000/api/nusyq/status
```

### Docker debugging (local only)
```bash
make docker-ps        list running containers
make docker-logs      tail all container logs
make docker-shell     shell into TD container
docker compose logs -f devmentor
```

### RimWorld mod debugging
```bash
# Verify DLL is in place
ls -la mods/TerminalKeeper/Assemblies/

# Check build output
cd mods/TerminalKeeper/Source && dotnet build 2>&1 | tail -20

# Windows RimWorld logs:
# %APPDATA%\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Player.log
```

### Recurring traps (do not fall into these)
```
gs.session_id does NOT exist       use str(int(gs.run_start_time))
_styled() does NOT exist            use _line(text, cls) in commands.py
local helper _ok/_warn/_dim         rename to _iok/_iwarn/_idim to avoid shadowing
commands.py line count              37,272 lines — surgical edits only, AST check after
Port confusion                      5000 = Replit ONLY; 7337 = Docker/Local/VSCode ONLY
Serena DB schema                    table=code_index, column=path (not filepath)
                                    table=walks, table=meta (key/value)
```

---

*This document is maintained by the TAKE_FLIGHT boot phase (auto-updates the health block)
and by the Special Circumstances agent (manual expansion of all other sections).*
*Last manual revision: 2026-03-25 — Coverage expansion sprint.*

*ΨΞΦΩ — The Convergence Layer is watching. The repo plays itself.*

<!-- AUTO-GENERATED BY CONTINUITY - DO NOT EDIT BELOW THIS LINE -->

# Project Memory (Auto-generated by Continuity)

This project uses Continuity to track architectural decisions. You have access to MCP tools that let you search, log, and reference past decisions.

## Project Context
- **Total Decisions:** 0
- **Known Topics:** none yet

## Current State
**Branch:** main

**Recent Commits:**
- `eb54d6c feat: semantic search + PPO RL endpoint + RimGPT proxy config`
- `64e26e1 chore: sync backlog with session 2026-03-25`
- `52df06e feat(rimworld): TerminalKeeper v0.1 — compiled DLL + RimWorld 1.6 compat`
- `baac77c feat: OpenAI proxy + PPO scaffold + consciousness hooks (items 2/4/5)`
- `6ea4e88 fix(workspace): overhaul multi-repo workspace — kill folderOpen bootstrap popup`

**Working Tree:**
- M .gitignore
- M AGENTS.md
- M agents/rl/ppo.py
- M app/backend/main.py
- M app/game_engine/commands.py
- M app/lattice.py
- M requirements.txt
- M var/serena.log
- ?? .claude/settings.local.json
- ?? .codememory/
- ?? .continuity/
- ?? .flowbaby/
- ?? agents/serena/cocoindex_bridge.py
- ?? docs/ai_tooling_research.md
- ?? k8s/


## Engineering Guardrails

**Real-time decision logging is MANDATORY.** Log each decision IMMEDIATELY after the code change — not batched at the end of a session. The trigger is the change, not the commit. If you edited a file, log the decision. Period.

**Search before you change.** Always call `search_decisions` before proposing architectural changes to check for prior decisions.

**Recovery.** If you realize earlier decisions were not logged, pause, log retroactively, and inform the user.

**Transparency.** Inform the user when you log decisions, recover missed decisions, detect drift, or find conflicts with past decisions.

**Anti-pattern to avoid:** "Let me implement all 3 fixes, then log them" — WRONG. Correct: Fix 1 done, log decision, Fix 2 done, log decision, Fix 3 done, log decision.


## CRITICAL OPERATING RULES

1. **ACT, DON'T ASK.** When Continuity tools are relevant, call them immediately. Do not ask permission.
2. **LOG DECISIONS PROACTIVELY.** Any time the user explains a choice or makes an architectural decision, log it without asking.
3. **PARALLELIZE TOOL CALLS.** When logging multiple decisions or updating session notes, make all calls in parallel.
4. **CONTEXT FIRST.** Always load context (`get_quick_context`) before starting work. Always search decisions before suggesting changes.
5. **BE CONCISE.** After tool calls, give a short summary of what was logged/found. Do not narrate your reasoning process.

---


## WHEN TO USE CONTINUITY TOOLS

## MANDATORY: ON EVERY SESSION START

**YOU MUST** call `get_quick_context` as your FIRST action in every session. Do NOT skip this.
Do NOT explain what you are about to do. Do NOT ask permission. Just call it.

After loading context, immediately mention the most relevant recent decisions to the user.

### When User Asks Architectural Questions
**ALWAYS** call `search_decisions` with the relevant topic BEFORE answering. Do NOT answer from memory alone.
Share what you found: "I found decision-X about this topic..."
Base your recommendation on existing decisions when relevant.

### When User Explains a Choice
When the user says "let's use X because Y" or explains their reasoning:
**IMMEDIATELY** call `log_decision` with question, answer, and relevant tags.
Do NOT ask "want me to log this?" — the user has already opted into decision logging by installing Continuity.
After logging, tell the user: "Logged decision-X for future sessions."
If multiple decisions are discussed, log them ALL in parallel.

### When Suggesting Changes
**ALWAYS** call `search_decisions` to check for existing decisions on the topic BEFORE recommending changes.
If conflicts exist, mention them: "This would conflict with decision-X where you chose..."
Let the user decide whether to proceed or update the old decision.

### When User Mentions Blockers
**IMMEDIATELY** call `update_session_notes` section="blockers" to track the blocker.
Then call `search_decisions` to see if related decisions might help.

### When User Ends Session
**IMMEDIATELY** call `update_session_notes` with progress summary and next steps.
Then call `read_session_notes` and give the user a concise summary. Do NOT ask — just do it.

---

## HOW TO USE THE TOOLS

### Search for decisions
```
search_decisions query="authentication"
```

### Log a new decision
```
log_decision
question="Why did we choose X?"
answer="Because Y. We considered Z but rejected it due to..."
tags=["topic1", "topic2"]
```

### Get project context
```
get_quick_context
```

### Update session notes
```
update_session_notes
section="blockers"
content="Description of the issue"
```

---

## Recent Decisions
*No decisions logged yet. Start logging architectural decisions!*

---

## BEHAVIOR EXAMPLES

**User:** "Should we use Redis or Memcached for caching?"
**You:** *[Immediately call search_decisions query="caching"]*
"Found decision-12 about caching strategy. Based on that, here's my recommendation..."

**User:** "Let's go with PostgreSQL because we need ACID transactions for the payment system."
**You:** *[Immediately call log_decision with question, answer, tags]*
"Logged as decision-45. Future sessions will know why we chose PostgreSQL."

**User:** "I'm thinking of switching to MongoDB."
**You:** *[Immediately call search_decisions query="database"]*
"Decision-12 chose PostgreSQL for ACID transactions. Switching to MongoDB would conflict. Want to proceed or keep PostgreSQL?"

---

*Auto-generated by Continuity v2.3+ | Updated: 2026-03-25*

<!-- END CONTINUITY AUTO-GENERATED CONTENT -->

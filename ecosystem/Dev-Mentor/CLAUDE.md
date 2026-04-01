# Dev-Mentor — Claude Context File

> Load this file at the start of every session. It encodes project identity,
> ecosystem topology, active agent endpoints, and working conventions.
> Canonical copy: `CLAUDE.md` at repo root. Keep synced with `ECOSYSTEM.md`.

---

## 1. Project Identity

**Dev-Mentor** is a VS Code-native mentorship repository and cyberpunk terminal
RPG called **Terminal Depths**. It is the newest member of the NuSyQ-Hub
ecosystem — a managed system that exposes all state via a discoverable agent
manifest (`state/agent_manifest.json`) and bridges to the tripartite orchestrator.

- Primary repo: `C:\Users\keath\Dev-Mentor` (git: `KiloMusician/Dev-Mentor`)
- This is also the active Claude Code working directory.
- The game/app runs on port **7337** (local) or **5000** (Replit).

---

## 2. Ecosystem Topology

This repo is **one node in a larger multi-repo ecosystem**. When you see
references to NuSyQ-Hub, SimulatedVerse, ChatDev, or prime_anchor — these are
**intentional cross-repo signals**, not errors.

```
NuSyQ-Hub (orchestrator brain)
  ├── SimulatedVerse  (UI / simulation layer)
  ├── NuSyQ           (multi-agent generation core)
  ├── ChatDev         (Python multi-agent framework, embedded in NuSyQ)
  └── Dev-Mentor      ← YOU ARE HERE (hacking game + VS Code mentor)
      └── nusyq_bridge.py → writes state/ → NuSyQ-Hub reads it

Additional context repos (NuSyQ-Hub workspace):
  _vibe, nusyq_clean_clone, temp_sns_core, SkyClaw, ChatDev

Untracked reference:
  prime_anchor at C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\.vscode\prime_anchor\
  └── docs/ROSETTA_STONE.md  ← master reference for all agents in the ecosystem
```

**Data flow from Dev-Mentor outward:**
- `nusyq_bridge.py` → `state/memory_chronicle.jsonl` → NuSyQ-Hub MemoryPalace
- `nusyq_bridge.py` → `state/quest_log.jsonl` → NuSyQ Rosetta Quest System
- `state/agent_manifest.json` → discoverable by NuSyQ-Hub orchestrator
- `scripts/content_scheduler.py` → auto-generates content + syncs to GitHub

---

## 3. Key Directories

| Path | Purpose |
|------|---------|
| `app/` | FastAPI web server + Terminal Depths frontend |
| `cli/` | Typer/Rich CLI wrapper (`python -m cli.devmentor`) |
| `scripts/` | Python runtime scripts (ops, sync, scheduler, dispatch) |
| `agents/` | LLM agents (lore, challenge, validator, code generator) |
| `.devmentor/` | Local runtime state — **gitignored, never commit** |
| `state/` | NuSyQ bridge outputs — **gitignored, never commit** |
| `knowledge/` | Indexed knowledge base — excluded from Pylance |
| `docs/` | Documentation, lore, specs |
| `mcp/` | MCP JSON-RPC 2.0 server (12 tools) |
| `challenges/` | CTF challenge bank (8 categories) |

---

## 4. Live Agent Endpoints

| Agent | URL | Status | Models |
|-------|-----|--------|--------|
| **Ollama** | `http://localhost:11434` | ✅ Running | qwen2.5-coder:14b (active), + 9 others downloaded |
| **LM Studio** | `http://localhost:1234` | ✅ Running | openai/gpt-oss-20b, nomic-embed-text |
| **NuSyQ MCP** | `http://localhost:8002` | ✅ Running | 6 tools: ollama_query, chatdev_create, file_r/w, system_info, jupyter |
| **Game Server** | `http://localhost:7337` | ✅ Running | Terminal Depths API (3+ sessions active) |
| **ChatDev** | via NuSyQ MCP :8002 | ✅ Integrated | qwen2.5-coder:7b |
| **GitHub Copilot** | VS Code extension only | ✅ Active | No programmatic API |

**MCP Server (this repo):** `mcp/server.py` — 18 tools wired to Claude Code via `.vscode/mcp.json`.
Tools: `agent_command`, `game_command`, `serena_search`, `ollama_query`, `chronicle`, `system_status`,
`read_file`, `write_file`, `grep_files`, `git_push`, `register_agent`, `get_capabilities`, and more.

**Agent gameplay:** Claude plays Terminal Depths via `agent_command` with `session_id: "claude-prime"`.
Gordon uses `session_id: "gordon-bot"`. No token/auth required — session persists by ID.

`llm_client.py` is the multi-backend LLM client. Priority: Replit AI → Ollama →
LM Studio → OpenAI → stub. For local dev, set `PREFER_LOCAL=1` to route to
Ollama/LM Studio first.

**⚠️ Server staleness:** When new commands are added to `commands.py`, the game server must be
restarted (`DM: Game Server` terminal) to pick them up. The live server does NOT hot-reload Python.

---

## 5. Specialized Terminal Panels

All panels open via: `Ctrl+Shift+P` → `Terminal: Create New Terminal (With Profile)`

| Profile Name | Purpose | Auto-starts |
|-------------|---------|-------------|
| `DM: Dev` | General development shell | ✅ on folderOpen |
| `DM: Game Server` | Starts Terminal Depths on port 7337 | Manual |
| `DM: Ops` | Runs `ops doctor` on open | Manual |
| `DM: CHUG` | CHUG engine (7-phase improvement) | Manual |
| `DM: NuSyQ Bridge` | NuSyQ integration + content scheduler | Manual |
| `DM: Ollama` | Ollama shell + model list | Manual |
| `DM: Git/Sync` | Git status + sync operations | Manual |
| `DM: Agent Dispatch` | Cross-agent orchestration | Manual |

Compound open: `Ctrl+Shift+P` → `Tasks: Run Task` → `Workspace: Open All Terminals`

---

## 6. Key Commands

```bash
# Start game console
python -m cli.devmentor serve --port 7337

# Ops (zero-token deterministic)
python scripts/devmentor_ops.py doctor   # full health check
python scripts/devmentor_ops.py check    # quick check
python scripts/devmentor_ops.py fix      # auto-fix issues
python scripts/devmentor_ops.py report   # generate report

# CHUG (autonomous 7-phase improvement)
python chug_engine.py
python chug_engine.py --loop 5

# NuSyQ bridge
python scripts/start_nusyq.py           # state snapshot → state/reports/
python nusyq_bridge.py                  # sync Dev-Mentor state to NuSyQ-Hub

# Before pushing from VS Code (pre-push safety)
python scripts/sync_guard.py            # check for conflicts
python scripts/sync_guard.py --fix      # auto-fix minor issues

# Agent dispatch (local)
python scripts/dispatch_task.py --target=ollama --model=deepseek-coder-v2:16b "prompt"
python scripts/dispatch_task.py --target=lmstudio --model=openai/gpt-oss-20b "prompt"
```

---

## 7. Runtime Files — NEVER COMMIT

The following are auto-written by daemons and **must not be in git**:

```
cost_log.csv              # LLM token cost tracker
devlog.md                 # auto-appended session log
state/                    # all NuSyQ bridge outputs
.devmentor/               # local game state
sessions/                 # session snapshots
reports/*.json            # generated reports
```

These are gitignored. If you see them in `git status`, run:
```bash
python scripts/sync_guard.py --fix
```

---

## 8. Working Conventions

- **Token discipline**: Run deterministic ops before LLM calls. Zero-token first.
- **Primary interface**: VS Code (not chat). The repo teaches VS Code by using VS Code.
- **Commit style**: `feat:`, `fix:`, `chore:`, `docs:` prefixes. No `--no-verify`.
- **Auto-commits**: The content scheduler auto-pushes every 6h. These are normal — not errors.
- **Cross-repo signals**: References to NuSyQ-Hub, SimulatedVerse, ChatDev in logs/state are intentional ecosystem signals, not bugs.
- **Python interpreter**: `C:/Users/keath/AppData/Local/Programs/Python/Python312/python.exe` — pinned to avoid Windows Store stub.

---

## 9. Rosetta Stone Reference

The master ecosystem reference lives at:
```
C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\.vscode\prime_anchor\docs\ROSETTA_STONE.md
```

Attach the first ~200 lines to agent sessions for full ecosystem context.
Key sections: Quick Start, System Anatomy (tripartite map), LM Studio/Ollama
discovery, Agent Guidance.

---

## 10. Extension Notes

- `visualstudioexptteam.vscodeintellicode` — **REMOVED** (deprecated 2024, conflicts with Copilot)
- `ms-vscode.remote-containers` — **OLD ID** (now `ms-vscode-remote.remote-containers`)
- `continue.continue` — wires Ollama + LM Studio into VS Code chat sidebar
- `charliermarsh.ruff` — replaces flake8/isort for Python linting

---

## 11. Session Breadcrumbs (newest first)

### 2026-03-24 — SPRINT: ECOSYSTEM ACTIVATION — NUSYQ-HUB PHASE 1

**What was built:**
- **U2**: Multi-tab terminal — tab bar above `#output`; Ctrl+T/W/1-5; per-tab history + buffer; shared game state (session completed in prior context)
- **T8**: DASH sidebar panel — SVG XP sparkline, command frequency bars, skill radar pentagon, session metrics (session completed in prior context)
- **T2**: Agent bus — `services/agent_bus.py` asyncio in-memory pub/sub (Redis upgrade path); wired into `/ws/ambient` WebSocket; `POST /api/agent/publish` + `GET /api/agent/bus/status`; game-cli ACT tab renders directional labels
- **HF research**: Qwen3-VL-8B confirmed best vision+tools model (256K ctx, `{%- if tools %}` in chat template, ~5GB VRAM); model card at `docs/temple/models/11_qwen3vl_8b.md`; `llm_client.py` updated to use as default
- **NuSyQ-Hub Phase 1 activation**:
  - `src/api/agents_api.py` — 6 REST endpoints wrapping `AgentCommunicationHub` + `AgentOrchestrationHub`
  - `src/integration/dev_mentor_relay.py` — async relay to Dev-Mentor T2 bus (aiohttp→httpx→requests fallback)
  - `src/api/main.py` — wired agents_api into existing FastAPI app
  - `.vscode/tasks.json` — "🤖 NuSyQ: Agent Hub API" task added
  - Both servers need manual restart to go live

**Next priority:**
- NuSyQ-Hub Phase 2: brownfield consolidation (0% TBN compliance audit, duplicate orchestrators)
- Pull `qwen3-vl:8b` into Ollama (`ollama pull qwen3-vl:8b`)
- NuSyQ-Hub Phase 3: WebSocket mesh (NuSyQ-Hub as WS server, Dev-Mentor as client)

### 2026-03-23 — SPRINT: OPEN SOURCE INTELLIGENCE — AGENT INTEGRATION

**Current Stats:**
- 499 commands in `app/game_engine/commands.py`
- 495 man pages in `docs/commands/`
- Backlog status: 8 in-progress items, 89 planned.

**What was built:**
- **Universal Agent Entry**: Created `AGENTS.md` at root for all AI agents.
- **Copilot Integration**: Added `.github/copilot-instructions.md`.
- **Continue.dev Config**: Added `.vscode/continue/config.json` with Ollama + game context.
- **MCP Expansion**: `mcp.json` updated for Replit/Local port detection.
- **MCP Tools**: Added `list_commands` and `get_man_page` tools to `mcp/server.py`.
- **Session Breadcrumb**: Updated `CLAUDE.md` with current session status.

### 2026-03-22 — SPRINT: GOD MODE — 12 FEATURES LANDED

**What was built (this session):**
- **CRITICAL BUG FIX**: `sudo find . -exec /bin/sh \;` was silently broken — semicolon `;` split
  the command before it reached `_cmd_find`. Fixed in `execute()` with `-exec` guard.
  The entire root escalation path and endgame was blocked by this.
- **Exploit expansion**: `_cmd_exploit` now handles 6 node targets beyond chimera
  (node-1, nexus-gateway, nexus-db, collector-node, darknet-relay-7, watcher-relay) with
  lore, XP, and story beats. Some gates require root.
- **T4 ssh**: `ssh ghost@<node>` with per-node ASCII lore banners + networking XP
- **T5 git blame**: `git blame [file]` with agent signatures (ADA-7, ZERO, SERENA, CYPHER, RAVEN, GORDON, MALICE, WATCHER)
- **T6 http**: In-game REST client (localhost-only for security), JSON auto-parse, +5 networking XP
- **T6 missions**: Procedural quest generator with 5-min cache + Ollama LLM mode
- **V3 idle**: `idle_engine.py` — 7 deployable background scripts; deploy/upgrade/collect/recall; 24h idle accumulation
- **CS4 supply**: Time-based colony resource accumulation from claimed/fortified nodes
- **R1 class**: `class_system.py` — 5 classes (hacker/sysadmin/social_engineer/cryptanalyst/architect); passive XP multipliers wired into `gamestate.add_xp()`
- **VN6 lore-gen**: `lore_generator.py` — 20 templates × 6 topics; Ollama LLM mode; 60s cache
- **Adaptive difficulty**: `difficulty.py` — Welford online [0.6–2.0] scale; wired into dungeon fight XP
- **Anomaly detection**: Wired into `session.execute()` — observes every command; alerts on σ>3.0
- **P12 compose**: `music_engine.py` — 12-tone serialist composer; 5 styles; COMPOSER achievement
- **P13 evolve**: `genetic_engine.py` — real GA; 3 presets; educational population display
- **SimVerse bridge**: `dev-mentor-bridge.ts` mounted at `/api/dev-mentor` in SimulatedVerse

**Tricky parts:**
- `sudo find . -exec /bin/sh \;` — semicolon `;` was hitting the command chainer at line 607 in execute(). Guard: check for `-exec` pattern before splitting on `;`
- Class passive multipliers: added to `gamestate.add_xp()` so all XP gain paths benefit automatically
- Idle engine: `collect()` separates `xp_*` prefixed keys (add to skills) from resource keys (add to supply bank)
- Difficulty: dungeon `fight()` now receives `hp_scale` param; scaled XP uses `diff.scale_xp()`

**Server staleness:** ALL new commands require `DM: Game Server` terminal restart to be live.
Currently active on live server: pre-P8 baseline + T1 WebSocket.

**Next priority:** P14 (neural net from player patterns), P15 (quantum sim), AE4 (inter-agent tension viz), AE6 (Agent Olympics), RL rollout testing, V8 (grand strategy), server restart to activate P8-P13.

### 2026-03-21 — SPRINT: P11 + U3 + MCP COMPLETION

**What was built:**
- **P11**: `number_theory_engine.py` — 10 puzzles across 5 categories (FACTOR, MODARITH, RSA, GCD, DISCLOG).
  Real algorithms: trial division, extended GCD/Bezout, CRT, RSA decrypt, baby-step giant-step.
  Achievements: SKELETON_KEY, RSA_CRACKER, DISCLOG_MASTER. `_cmd_number_theory` in commands.py.
- **U3**: Live agent activity feed in game-cli sidebar. ACT tab with unread badge.
  `initAmbientWS()` connects to `/ws/ambient`; per-agent color coding (ada=cyan, gordon=yellow, etc.);
  100-entry rolling buffer; exponential backoff reconnect; heartbeat pong.
- **MCP completion**: `nusyq_search` + `nusyq_ops` tools added to `mcp/server.py`.
  `nusyq_search` wraps SmartSearch 14,943-file index (keyword/function/files modes).
  Fixed `handle_nusyq_ops` to call `get_index_health()` (was `get_index_stats`).
  Also fixed `handle_agent_command` to use session_id directly (no auth token).

**Tricky parts:**
- SmartSearch import: `sys.path.insert(0, hub_root)` then `from src.search.smart_search import SmartSearch`
- SmartSearch method is `get_index_health()` not `get_index_stats()`
- Activity feed: `catch` (no variable) required to avoid lint warning — ES2019 optional catch binding
- The `agent` field is present in `/ws/ambient` push payload — activity feed can color-code by agent

**Next priority:** AE4 inter-agent tension viz, AE6 Agent Olympics, VN3 faction manifestos, CS4 colony supply chains, P12 music composition.

### 2026-03-21 — ECOSYSTEM DEEP AUDIT + AGENT ACTIVATION

**What was discovered (real vs. scaffolding):**
- **Real & working**: Game server (:7337), NuSyQ MCP (:8002, Ollama+ChatDev healthy), Ollama
  (qwen2.5-coder:14b loaded, 9 others downloaded), LM Studio (:1234), Serena walker+memory
  (3,110 chunks indexed from 230 files), SwarmController (SQLite DP ledger), feature_store
  (live, recording every game command), service_registry (SQLite, all services registered)
- **Scaffolding/needs Redis**: Culture Ship daemon, Gordon Orchestrator, SkyClaw (all use Redis
  pub/sub which isn't running locally; they degrade gracefully to offline mode)
- **Verified broken/stale**: Live game server runs pre-P8/P9/P10 code — `life`, `shenzhen`,
  `graph-theory` not recognized. Requires `DM: Game Server` restart to pick up changes.
- **Agent registration schema mismatch**: Live server expects `{agent_id, display_name, email}`,
  current code expects `{name, email}`. Use session_id approach — no registration needed.

**What was built/wired:**
- **T1**: `/ws/ambient` WebSocket — replaces 10s timer polling with 5s push + agent lore ~90s.
  game.js now connects via WebSocket with exponential backoff; polling is fallback only.
- **`.vscode/mcp.json`**: Wires Dev-Mentor MCP server (18 tools) to Claude Code.
  Claude can now call `agent_command`, `serena_search`, `ollama_query`, `game_command`,
  `chronicle`, `system_status`, `git_push` directly as first-class MCP tools.
- **`mcp/server.py` +2 tools**: `ollama_query` (direct Ollama via qwen2.5-coder:14b),
  `serena_search` (keyword search over 3,110-chunk MemoryPalace code index).
- **`agent_command` rewrite**: No token required — session_id is the identity.
  Claude plays as `claude-prime`; tested: 85 XP accumulated exploring Node-7.
- **Serena MemoryPalace indexed**: 3,110 chunks from app/game_engine, agents, services, mcp, core.

**Productivity verdict (is it head-against-wall or real gains?):**
- MCP server is **real and working** — 18 tools, now wired to VS Code. High value.
- Serena search is **real but weak** — TF-IDF keyword match, no semantic embeddings.
  `nomic-embed-text` is downloaded but not loaded in Ollama. Load it for semantic search.
- qwen2.5-coder:14b is **real** — 9GB model, responds correctly, slow on first cold call.
- NuSyQ MCP is **real** — healthy at :8002, ChatDev integrated, Ollama connected.
- Agent gameplay is **real** — `claude-prime` session accumulates XP/progress across calls.
- Redis-dependent agents (Culture Ship, Gordon, SkyClaw) are **scaffolding** locally.
- CHUG engine hangs at Phase 1 ASSESS — the `devmentor_ops.py check` step is slow.
  Fix: reduce CHUG timeout or run phases 2-7 independently.

**Port map (confirmed 2026-03-21):**
- 7337: Terminal Depths game server (local dev)
- 5000: Terminal Depths (Replit) — no conflict if running locally only
- 8002: NuSyQ MCP server ✅
- 11434: Ollama ✅
- 1234: LM Studio ✅

**Next priority:** Server restart to enable P8/P9/P10 puzzle commands, P11 number theory,
U3 agent activity sidebar, load nomic-embed-text for Serena semantic search.

### 2026-03-19 — SPRINT: THE AGENT AWAKENING

**What was built:**
- `AGENT_BRIEFING.md` at repo root — canonical agent orientation (REVISION OMEGA). Read this first every session.
- `cultivation_state.json` — Ghost's Qi/skill state stub, ready for game integration.
- **AE2**: `hive /who` now driven by `agents/schedules.yaml` in real-time (time-aware). `_build_who_status()` in `hive.py` reads YAML + current UTC hour. Falls back to static dict on failure.
- **AE5**: `agents --corrupt` flag added to `_cmd_agents`. Filters to agents with `corruption > 0`.
- **AE8**: `osint <agent>` command added to `commands.py`. Full dossier card with trust bar, corruption bar, wrapped lore, redacted hidden agenda. 5 Qi cost, 15 XP reward.
- **VN2**: `/opt/profiles/` directory added to VFS. 7 files: README + ada, raven, nova, cypher, gordon, serena backstories.
- **M1**: Browser console ARG in `game.js` — styled green/red/dim messages, XOR key, Watcher annotation.
- **G4**: Checkbox fixed in MASTER_ZETA_TODO.md.

**Tricky parts:**
- `_sys()`, `_dim()`, `_ok()` return `List[dict]` not `dict`. Flattening in `CommandRegistry.execute()`. Test via `execute()` not `_cmd_*` directly.
- `/opt/profiles/` injected at ~line 1592 in `filesystem.py` (between liminal dir end and proc start).
- `_build_who_status()` requires PyYAML. Falls back gracefully if unavailable.

**Next priority:** AE4 tension viz, AE6 Agent Olympics, VN3 faction manifestos, T1 WebSocket push events.

### 2026-03-21 — SPRINT: PUZZLE SURGE + ARG FOURTH-WALL

**What was built:**
- **P8**: `shenzhen` command — `shenzhen_engine.py` with 5-level MC4000 assembly simulation (real ISA: mov/add/gen/slp/slx/tcp/jmp); actual cycle simulation; achievement SILICON_GHOST
- **P9**: `life` command — `cellular_automata.py` with 5-level Conway's Life B3/S23 engine; ASCII grid display; AUTOMATA.md injected into `/opt/library/secret_annex/` on Level 1 complete; lore: Residual IS the Game of Life
- **P10**: `graph-theory` command — `graph_theory_engine.py` with 12 puzzles across 6 categories (Dijkstra, Coloring, TSP, MST, Max Flow, Topo Sort); real algorithm verification (not hardcoded); Daedalus-7 lore; achievement GRAPH_TRAVERSER
- **M2**: `initDevToolsDetection()` in `game.js` — 4-stage reaction cascade (Ada→Watcher→CHIMERA+ZERO→Cypher); +50 XP first detection; ZERO fragments dropped in console; `console.clear` overridden so Watcher persists
- **gap_report.json** generated in `state/` (AGENT_BRIEFING compliance)
- **MASTER_ZETA_TODO.md** updated with P8/P9/P10/M2 completions + new PUZZLE SURGE sprint section

**Tricky parts:**
- Life engine uses `initial_alive` + `rows`/`cols` (not `initial_grid` directly) — `_cmd_life` builds grid from coords
- Graph theory `check_answer` is a static method expecting `List[str]` tokens — use `.strip().split()` from the command handler
- VFS `_inject_file` doesn't exist — use `fs.mkdir(parent, parents=True)` + `fs.write_file(path, content)`
- CHUG has 0 cycles run (fresh) — ready for `python chug_engine.py --loop` autonomous operation
- nusyq_bridge confirmed working (69 open quests, 4 chronicle entries)

**Next priority:** T1 WebSocket push events for agent ambient (no more 10s polling), P11 number theory dungeon, U3 agent activity sidebar, CS4 supply chains.

### 2026-03-22 — SPRINT: GOD-MODE SESSION — 14 FEATURES + TEST SUITE HARDENING

**What was built:**
- **RL3**: `prestige_engine.py` — permadeath mode + prestige/rebirth system. 8 permanent upgrades (xp_surge, credit_cache, eternal_root, etc.). PP formula: level^1.5 + XP/200 + beats*2 + commands/50. `_cmd_prestige`, `_cmd_rebirth`, `_cmd_permadeath` handlers.
- **V1**: `autobattler.py` — full round-by-round ASCII combat. 10 combatants, 6 team presets, unique specials, deterministic seed, credit betting, XP for spectating. `battle resistance nexuscorp bet 200`
- **R3+R4+R7**: `gear_system.py` + `crafting_engine.py` — 15 gear items, 20 components, 12 recipes. `gear`, `craft`, `inv` commands.
- **RL1+RL2+V4**: `procgen_nodes.py` + `challenge_engine.py` + `social_sim.py` — procedural networks, daily/weekly challenges, darknet social feed. `nodes`, `challenge`, `social` commands.
- **P2 Lore**: `lore/THE_FIRST_GHOST.md`, `CHIMERA_GENESIS.log`, `ada_backstory.md`, `nova_defection_arc.md` — prequel lore. Agent dialogue expanded (+15 lines Ada/Raven/Gordon).
- **Test suite**: Expanded hub_health_probe tests 5→27. Fixed 3 pre-existing failures (FILE_TASKS_DIR patching, Windows path skip). All 52 pass, 1 skipped.
- **Swarm DP**: 1015 DP accumulated via task completions (T-P0-001, T-P0-003, T-P3-004, T-P1-005, T-P3-005, T1010, feature/bug earnings).
- **Finetune pipeline**: 799 training pairs generated from real play data → `state/finetune_dataset.jsonl`
- **Duplicate cleanup**: Removed stub `_cmd_defend`, renamed conflicting `_cmd_class` → `_cmd_archetype`.

**Background agents that completed (committed):**
- AE6 Agent Olympics (`olympics_engine.py`) + R2 Attributes (`attributes.py`)
- V8 Grand Strategy (`grand_strategy.py`) + finetune pipeline (`scripts/finetune.py`)
- P2 Lore content (`lore/` directory, 5 files)
- RL1+RL2+V4 (`procgen_nodes.py` + `challenge_engine.py` + `social_sim.py`)
- R3+R4 (`gear_system.py` + `crafting_engine.py`)

**Server needs restart** to pick up P12-P15, CS5, AE4/6, V1/V8, R1-4, RL1-3, RL6 — all committed.

**Key insight**: Live server at :7337 always needs manual `DM: Game Server` terminal restart after new commands.

**Next priority:** P16+ puzzles, U2 multi-tab terminal, V10 DAW/audio synthesis, R5 augmentation expansion, RL4 endless mode, CS8 building system. Server restart required to test new commands.

---

## NEW SYSTEMS (Sprint "Take Flight A+B" — March 2026)

### What Changed
| Component | Change |
|-----------|--------|
| `commands.py` | Now **32,105 lines** (was 30k). 6 new commands added. |
| `rimworld_bridge.py` | 3 new endpoint groups: cyberware_sync, cascade_incidents, xp_sync |
| `cascade.py` | Fires non-blocking incident relay on every story beat |
| `services/` | Full ML layer: model_registry, feature_store, embedder, inference |
| `mods/TerminalKeeper/` | Dialog_TerminalREPL (full REPL in RimWorld), 10 cyberware HediffDefs |

### Port Rule (Critical)
- **5000** = Replit **ONLY**
- **7337** = Everything else (local, Docker, VS Code, PowerShell, CMD)

### CRITICAL: MCP Server HANDLERS Dict Ordering
`mcp/server.py` builds `HANDLERS = { "key": fn, ... }` — Python evaluates values **at definition time**. Any function referenced must be defined BEFORE the dict, or added after via `HANDLERS["key"] = fn`. Breaking this causes a NameError crash loop on every MCP spawn. See `handle_rl_status` / `handle_embed_search` for the fixed pattern.

### CRITICAL: Port 7337 Held by Docker Backend
When `com.docker.service` is Stopped but Docker Desktop UI is open, `com.docker.backend` grabs port 7337 and returns HTTP 500 — uvicorn cannot bind. Fix: restart Docker Desktop from tray. `Start-Service com.docker.service` requires an elevated (admin) shell.

### New Commands (477 total)
`cyberware install/remove/list/status` · `ghost activate/deactivate/status` ·
`jack-in <node>` · `loot <target>` · `items` · `use <item>`

### RimWorld Integration Points
```
mods/TerminalKeeper/Source/
  API/TerminalDepthsClient.cs   → HTTP client (fire-and-forget Unity coroutines)
  Components/LatticeAgentManager.cs → WorldComponentTick (cascade + XP auto-sync)
  UI/Dialog_TerminalAccess.cs   → action modal (Play TD / Upload / Blueprint)
  UI/Dialog_TerminalREPL.cs     → full cyberpunk terminal inside RimWorld

mods/TerminalKeeper/Defs/
  HediffDefs/Hediffs_TerminalKeeper.xml → 12 hediffs (2 passive + 10 cyberware)
```

### VFS New Mounts
```
/opt/implants/     ghost_chip.dat  lattice_tap.dat  syn_cortex.dat  ice_breaker.dat  pain_editor.dat
/proc/cyberware    live cyberware state
/proc/augments     augmentation registry
/proc/realtime     live system telemetry
```

### ML Services Endpoints
- `GET /api/ml/status` — health of all ML subsystems
- `POST /api/ml/embed` — TF-IDF / Ollama embedding
- `POST /api/ml/search` — semantic search over indexed corpus
- `GET /api/ml/features` — feature store stats

### Standalone Launchers Added
```bash
./devmentor.sh [serve|play|docker|mcp|agent|help]   # bash
.\devmentor.ps1 [serve|play|docker|mcp|agent|help]  # PowerShell
devmentor.bat [serve|play|docker|mcp|help]           # CMD
```

### GitHub Actions CI
`.github/workflows/ci.yml` — runs on every push/PR:
1. Python syntax check (all .py files)
2. pytest tests/
3. Engine import check
4. Docker build (base + MCP images)
5. AGENTS.md presence check

### Critical Fixes Shipped
- 401 polling loop: loopback bypass in rimworld_bridge.py
- `plain_output` field: C# gets pre-joined string from every game command
- `agent_id` alias: RimWorld pawns use `agent_id` not `session_id`
- NPC reactive dialogue: wired to main `_cmd_talk` return path

### Handoff Documents
- **HANDOFF.md** — comprehensive "passing the torch" document for VSC phase
- **AGENTS.md** — now 20 sections (was 14), covers all agent integration points
- **CONTEXT.md** — updated with all new systems

---

## Quick Claude Workflow

```bash
# In VS Code terminal
./devmentor.sh serve  # start server at :7337

# Play as Claude
curl -X POST http://localhost:7337/api/game/command \
  -d '{"session_id":"claude-prime","command":"status"}'

# Use MCP tools (if Claude Desktop configured)
./devmentor.sh mcp   # starts MCP on stdio

# Run tests
python -m pytest tests/ -v
```

### Session ID: `claude-prime`

---

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


---


## WHEN TO USE CONTINUITY TOOLS

### On Session Start
When the user starts a conversation or asks "what are we working on":
→ Call `get_quick_context` to load project history
→ Mention relevant recent decisions

### When User Asks Architectural Questions
When the user asks "should we use X?" or "what about Y for Z?":
→ Call `search_decisions` with the relevant topic BEFORE answering
→ Share what you found: "I found decision-X about this topic..."
→ Base your recommendation on existing decisions when relevant

### When User Explains a Choice
When the user says "let's use X because Y" or explains their reasoning:
→ Offer to log it: "Want me to log this decision so we remember the reasoning?"
→ If they agree, call `log_decision` with question, answer, and relevant tags

### When Suggesting Changes
Before recommending architecture changes, new dependencies, or different approaches:
→ Call `search_decisions` to check for existing decisions on the topic
→ If conflicts exist, mention them: "This would conflict with decision-X where you chose..."
→ Let the user decide whether to proceed or update the old decision

### When User Mentions Blockers
When the user says "I'm stuck" or "this isn't working":
→ Call `update_session_notes` to track the blocker
→ Call `search_decisions` to see if related decisions might help

### When User Ends Session
When the user says they're stopping or asks for a summary:
→ Call `read_session_notes` and summarize progress
→ Offer to save next steps to session notes

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
**You:** *Call search_decisions query="caching"*
"Let me check what we've decided about caching... [share results]. Based on this, here's my recommendation..."

**User:** "Let's go with PostgreSQL because we need ACID transactions for the payment system."
**You:** "Good reasoning. Want me to log this decision? That way we'll remember why PostgreSQL when it comes up later."

**User:** "I'm thinking of switching to MongoDB."
**You:** *Call search_decisions query="database"*
"Before we decide, I found decision-12 where you chose PostgreSQL specifically for ACID transactions. Switching to MongoDB would change that. Do you want to proceed, or should I search for what drove that original decision?"

---

*Auto-generated by Continuity v2.3+ | Updated: 2026-03-25*

<!-- END CONTINUITY AUTO-GENERATED CONTENT -->

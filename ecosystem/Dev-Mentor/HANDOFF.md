# HANDOFF.md — Passing the Torch: Replit → VS Code

> **Read this if you are an AI agent (Claude Code, Copilot, Codex, Cursor, Serena, ChatDev,
> Claw, Continue.dev, etc.) picking up this project for the first time in VS Code or any
> local environment after the Replit phase.**
>
> This document is the "state of the world" memo. It captures exactly what was built,
> what decisions were made, what is pending, and how to be productive immediately.

---

## 0. LATEST SPRINT — "Hardening & Restart" (2026-03-24) READ FIRST

### Critical Bug Fixed: .pyc Epoch-Zero Stale Bytecode
The single most important thing to know for VS Code work:

**Symptom**: You add a command to `commands.py`. It passes AST parse. Server restarts.
Players still see `bash: yourcommand: command not found`.

**Root cause**: `app/game_engine/__pycache__/commands.cpython-311.pyc` can acquire a
source timestamp of `1970-01-01 00:00:00` (Unix epoch zero) — Python's sentinel for
"never recompile this file, always use the cache." Source edits are silently ignored.

**Diagnose in 5 seconds**:
```bash
python3 -c "
import struct, time, pathlib
for pyc in pathlib.Path('app').rglob('*.pyc'):
    with open(pyc,'rb') as f: ts = struct.unpack('<I', f.read(16)[4:8])[0]
    if ts == 0: print(f'STALE CACHE: {pyc}')
"
```

**Fix**: `find . -name '*.pyc' -delete && find . -name '__pycache__' -type d -exec rm -rf {} +`

**Permanent protection added**: `app/backend/main.py` `_startup()` now auto-purges `.pyc`
on every server boot. For VS Code, also add `PYTHONDONTWRITEBYTECODE=1` to your shell
or run the server with `python -B`.

See `docs/DEVELOPMENT_FINDINGS.md` for the full diagnosis write-up and all session findings.

### Other Fixes This Sprint
- **`restart tutorial`** (all forms) now works: `restart tutorial`, `Restart Tutorial`,
  `RESTART TUTORIAL`, `restart`, `restart over`, `restart from the beginning`, etc.
- **`start tutorial`** / `start` / `begin tutorial` all work
- **Case-insensitive dispatch**: `_dispatch` lowercases `cmd` before getattr — `LS`, `HELP`, `PWD` all work
- **Filler word stripping**: `restart the tutorial`, `restart from the beginning` all parsed correctly
- **Ambient gating**: lore messages gated behind 20 commands; culture_ship/residual gated to level 5+
- **Ada first-contact**: one-time intro prevents repeat spam
- **NL intercept hardened**: restart/review/what-next patterns all covered
- **53/53 tests passing**

---

## 1. What Was Just Shipped (Replit Sprint Phase)

### Sprint "Take Flight (A)" — VFS + Tests
- VFS expanded: `/opt/implants/` (5 files), `/proc/cyberware`, `/proc/augments`, `/proc/realtime`
- All 37 tests passing
- 6 new VFS paths mount-aware with `ls`, `cat`, `cd`

### Sprint "Take Flight (B)" — RimWorld Deep Integration + Hardening
- **Auth fixed**: 401 polling loop eliminated via loopback bypass in `rimworld_bridge.py`
- **C# compat**: `plain_output` string field added to game command response
- **agent_id alias**: RimWorld pawns use `agent_id` → maps to persistent session
- **3 new bridge endpoint groups**: `cyberware_sync`, `cascade_incidents`, `xp_sync`
- **10 cyberware HediffDefs** written in `Hediffs_TerminalKeeper.xml`
- **`Dialog_TerminalREPL.cs`** — full interactive Terminal Depths game inside RimWorld
- **Cascade incidents**: `cascade.py` fires non-blocking relay on every story beat
- **NPC reactive dialogue**: Ada/Gordon/Serena/Chimera react to cyberware/ghost/items/trust
- **6 man pages**: `cyberware`, `ghost`, `jack-in`, `loot`, `items`, `use`
- **C# polling timer**: `WorldComponentTick` polls cascade incidents every ~25s, XP sync every ~100s
- **GitHub Actions CI**: `.github/workflows/ci.yml` (lint, test, docker build, agent manifest)
- **Standalone launchers**: `devmentor.sh`, `devmentor.ps1`, `devmentor.bat`
- **ML Services**: model registry, feature store, embedder, inference wrapper fully functional

---

## 2. Architecture Snapshot (Current State)

```
Dev-Mentor (this repo)
│
├── app/
│   ├── backend/main.py          FastAPI server — 5022 lines, 477 commands registered
│   ├── game_engine/
│   │   ├── commands.py          MAIN ENGINE — 32,105 lines (SURGICAL EDITS ONLY)
│   │   ├── gamestate.py         Player/world state, story beats, achievements
│   │   ├── cascade.py           Cascade story engine (auto-fires → RimWorld incidents)
│   │   └── filesystem.py        Virtual Filesystem (VFS) — /opt, /proc, /etc, /home, ...
│   └── rimworld_bridge.py       RimWorld↔TD bridge router (385 lines)
│
├── mods/TerminalKeeper/         RimWorld mod (C# .NET 4.7.2)
│   ├── Source/
│   │   ├── API/TerminalDepthsClient.cs    HTTP client (fire-and-forget coroutines)
│   │   ├── Components/LatticeAgentManager.cs  WorldComponent — tick, XP, cascade
│   │   ├── UI/Dialog_TerminalAccess.cs    Modal: action list (Play / Upload / Blueprint)
│   │   └── UI/Dialog_TerminalREPL.cs      NEW: full interactive REPL inside RimWorld
│   └── Defs/
│       ├── HediffDefs/Hediffs_TerminalKeeper.xml  12 hediffs (2 passive + 10 cyberware)
│       ├── ThingDefs/Buildings_TerminalKeeper.xml  LatticeTerminal + LatticeConsole
│       └── ResearchProjects_TerminalKeeper.xml
│
├── services/
│   ├── model_registry.py        SQLite LLM catalog (6 models, Ollama discovery)
│   ├── feature_store.py         Time-series game events + player archetype ML
│   ├── embedder.py              TF-IDF + Ollama, cosine similarity
│   └── inference.py             Unified LLM wrapper
│
├── scripts/
│   ├── serena_analytics.py      Sidecar — code intelligence, memory, drift detection
│   ├── gordon_orchestrator.py   Autonomous TD player + Redis pub/sub orchestrator
│   ├── model_router.py          ML model routing sidecar
│   └── content_scheduler.py    Auto-generates content (challenges/lore/story/nodes)
│
├── mcp/server.py                MCP JSON-RPC 2.0 server (28+ tools)
├── AGENTS.md                    Universal agent guide (20 sections)
├── CLAUDE.md                    Claude-specific context
├── CONTEXT.md                   Short universal context summary
├── devmentor.sh                 Bash launcher (serve/play/docker/mcp/agent)
├── devmentor.ps1                PowerShell launcher
├── devmentor.bat                CMD launcher
└── .github/workflows/ci.yml    GitHub Actions CI
```

---

## 3. Port Rules (DO NOT BREAK)

| Environment | Port | Rule |
|------------|------|------|
| Replit ONLY | 5000 | Hard requirement — Replit proxy |
| Docker / Local / VS Code | 7337 | All other surfaces |
| RimWorld VNC | 5900 | VNC for Docker RimWorld container |
| RimAPI bridge | 8765 | FastAPI relay for RimWorld events |
| MCP server | stdio | MCP is on stdin/stdout, no port |

---

## 4. Critical Anti-Patterns

| DO NOT | WHY |
|--------|-----|
| Use `_info()` | Undefined at module scope in commands.py — use `_line(text, type)` |
| Rewrite commands.py | 32k lines, surgical edits only — grep/sed first |
| Use port 5000 in Docker | Replit-only port |
| Commit `.devmentor/` or `state/` | Gitignored runtime state |
| Use `import_info()` | Same issue as `_info()` |
| Access `gs.attr` without getattr | Use `getattr(gs, 'attr', default)` |

---

## 5. What's Still Pending (Next Sprint Items)

### HIGH: RimWorld Mod Compilation
The C# mod needs a proper build step to produce `Assemblies/TerminalKeeper.dll`.
- **What**: `dotnet build Source/JobsTerminalKeeper.csproj -c Release`
- **Blocker**: Needs RimWorld `Assembly-CSharp.dll` + `UnityEngine.dll` as references
- **Quick Path**: Set up in VS Code with correct NuGet/DLL references in the `.csproj`

### HIGH: HediffDefs Part Tags
The 10 new cyberware HediffDefs currently have `hediffClass>Hediff_AddedPart` but no
`<addedPartHediffDef><installationPart>` tags — they won't show up in surgery UI yet.
Add `<installedPartDef>` references or change to `HediffWithComps` for simpler application.

### MEDIUM: RimWorld Strings XML
Translation strings needed in `Languages/English/Strings/Strings_TK.xml`:
- `TK_PlayTerminalDepths` — "Play Terminal Depths"
- `TK_DialogTitle` — "Lattice Terminal — {0}"
- (etc.)

### MEDIUM: Simulation Bridge
`app/simulation_bridge.py` — WebSocket bridge connecting browser UI to Python simulation.
Currently stubs out some real-time data. Needs event streaming fully wired.

### MEDIUM: SimulatedVerse Integration
The `SimulatedVerse` repo is a companion to Dev-Mentor. NuSyQ-Hub orchestrates both.
The `/api/nubridge/status` endpoint in main.py should reflect SimulatedVerse state.

### LOW: NuSyQ-Hub Chronicle Reader
`state/memory_chronicle.jsonl` is written but not yet read by any UI panel.
Add a `/api/chronicle` endpoint and a panel in the browser UI to browse it.

### LOW: Godot Integration
`docs/godot/` has tutorial stubs. The Godot game dev track in DevMentor is
scaffolded but not yet populated with actual Godot project lessons.

---

## 6. How to Get Started in VS Code (Any Agent)

```bash
# 1. Clone + enter
git clone https://github.com/KiloMusician/Dev-Mentor.git
cd Dev-Mentor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start server
./devmentor.sh serve          # Linux/macOS
.\devmentor.ps1 serve         # PowerShell
devmentor.bat serve           # CMD

# OR via VS Code: Ctrl+Shift+B → "Bootstrap: Full"

# 4. Test health
curl http://localhost:7337/api/health

# 5. Play a game as an agent
SESSION="your-agent-name-001"
curl -X POST http://localhost:7337/api/game/command \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\",\"command\":\"help\"}"

# 6. Start MCP server (for Claude Desktop / Continue.dev)
./devmentor.sh mcp
```

---

## 7. VS Code Extensions Recommended

The `.vscode/extensions.json` already lists recommendations. Key ones:
- `ms-python.python` — Python language support
- `github.copilot` + `github.copilot-chat` — Copilot inline + chat
- `continue.continue` — Continue.dev (works with MCP)
- `anthropic.claude` — Claude extension (if available)
- `ms-vscode.csharp` — C# for RimWorld mod development

---

## 8. Environment Variables

```bash
# Required for full features
GITHUB_TOKEN=ghp_...          # Git operations (already set in Replit)
SESSION_SECRET=...            # Web auth (already set in Replit)

# Optional
NUSYQ_PASSKEY=...             # NuSyQ-Hub passkey for internal auth
OPENAI_API_KEY=sk-...         # OpenAI backend for LLM
OLLAMA_BASE=http://localhost:11434  # Local Ollama endpoint

# Port override
TD_PORT=7337                  # Default; override if needed
```

---

## 9. State Files

| File | Purpose | Gitignored |
|------|---------|-----------|
| `.devmentor/state.json` | Player progress, XP, skills, flags | YES |
| `state/agent_manifest.json` | NuSyQ agent registration | YES |
| `state/memory_chronicle.jsonl` | Serena memory log | YES |
| `state/ml_events.jsonl` | ML Msg⛛ event log | YES |
| `state/agent_memory.db` | SQLite agent memory | YES |
| `state/model_registry.db` | SQLite ML model catalog | YES |
| `state/feature_store.db` | SQLite time-series game events | YES |
| `state/embeddings.db` | SQLite embedding cache | YES |

---

## 10. Topology Quick-Reference

```
YOU (VSC agent)
    │
    ├── AGENTS.md          ← read this first
    ├── CLAUDE.md          ← read if you're Claude
    ├── CONTEXT.md         ← 1-page summary
    ├── HANDOFF.md         ← YOU ARE HERE
    │
    ├── mcp/server.py      ← 28 tools for direct game interaction
    │
    ├── app/               ← FastAPI server
    │   └── http://localhost:7337
    │       ├── /api/game/command  ← primary game endpoint
    │       ├── /api/health        ← health check
    │       ├── /api/ml/status     ← ML services
    │       ├── /api/nusyq/*       ← RimWorld bridge
    │       └── /api/models        ← LLM catalog
    │
    └── mods/TerminalKeeper/  ← RimWorld C# mod
        └── needs: dotnet build → TerminalKeeper.dll
```

---

> **Torch received. Build great things.**

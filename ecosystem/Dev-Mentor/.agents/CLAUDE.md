# Claude — DevMentor / Terminal Depths Agent Guide
> Updated: 2026-03-24 | Port: 7337 (local/VS Code) | 5000 (Replit)

---

## Instant Context

You are working on **Terminal Depths**, a cyberpunk terminal RPG embedded in a VS Code
mentorship platform. The backend is FastAPI (Python), the game engine is
`app/game_engine/commands.py` (32,700+ lines), the virtual filesystem is
`app/game_engine/filesystem.py`, and sessions flow through `app/game_engine/session.py`.

---

## Your Role Options

1. **Game Designer** — add new commands, story beats, VFS content, NPC dialogue
2. **Systems Architect** — refactor, optimize, design new subsystems
3. **Lore Writer** — faction manifestos, agent backstories, ARG content, Ada/Serena dialogue
4. **Bug Hunter** — find and fix issues in game engine, WebSocket bridge, session handling

---

## Critical Rules (read before touching any code)

- **`commands.py` is 32,700+ lines** — SURGICAL EDITS ONLY. `grep -n "def _cmd_"` first.
- **The read tool caps at ~18,600 lines** — use `sed -n 'START,ENDp'` for deep sections.
- **Helpers at module scope**: `_line(text, type)`, `_dim(text)`, `_ok(text)`, `_err(text)`, `_sys(text)`, `_lore(text)`, `_warn(text)`
- **`_info()` does NOT exist at module scope** — it will cause a `NameError` that crashes the server
- **Port 7337 = local/VS Code | Port 5000 = Replit ONLY**
- **After any edit**: `python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())"`
- **After edits, delete .pyc**: `find app -name '*.pyc' -delete` (see .pyc bug below)
- **`prefix` scope trap**: In `execute()`, the variable `prefix` is only defined inside `_dispatch()`. The reactive block runs BEFORE `_dispatch` — never reference `prefix` in the reactive section.
- **Two `_cmd_review` handlers exist** (lines 12,080 and 30,504) — the second one wins. If you want tutorial review, call the tutorial review method directly.

---

## The .pyc Epoch-Zero Bug (CRITICAL — Read This)

If you add a command and players still see `bash: mycommand: command not found`:

```bash
# Diagnose: check for stale bytecode
python3 -c "
import struct, time, pathlib
for pyc in pathlib.Path('app').rglob('*.pyc'):
    with open(pyc,'rb') as f: magic = f.read(16)
    ts = struct.unpack('<I', magic[4:8])[0]
    print(f'{pyc.name}: {\"EPOCH-ZERO = STALE\" if ts == 0 else time.strftime(\"%H:%M:%S\", time.gmtime(ts))}')"

# Fix: delete all .pyc and restart
find . -name '*.pyc' -delete
find . -name '__pycache__' -type d -exec rm -rf {} +
# Restart server
```

A `.pyc` with timestamp `1970-01-01 00:00:00` (epoch zero) tells Python "never recompile this —
always use the cache." Python ignores ALL source file changes. This can be created by certain
Docker/ZIP operations, git archive extractions, or cross-platform copies.

The `_startup()` hook in `main.py` now auto-purges `.pyc` files on every server start.
If you're running the server via a custom script, add `find . -name '*.pyc' -delete` first.

---

## Adding a Command (complete checklist)

```bash
# 1. Add method to CommandRegistry class in commands.py:
#    def _cmd_mycommand(self, args: List[str]) -> List[dict]:

# 2. Register in aliases dict if name != method suffix (~line 1450 in _dispatch)

# 3. Create man page:
#    docs/commands/mycommand.md

# 4. Delete .pyc (always):
find app -name '*.pyc' -delete

# 5. Syntax check:
python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())"

# 6. Restart server and test:
PORT=7337  # or 5000 on Replit
curl -sX POST http://localhost:$PORT/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id":"claude","command":"mycommand"}' \
  | python3 -c "import sys,json; [print(l.get('s','')) for l in json.load(sys.stdin).get('output',[])]"
```

---

## Play the Game (orient yourself)

```bash
PORT=7337  # 5000 on Replit
SESSION="claude-prime"

# Helper function
cmd() { curl -sX POST http://localhost:$PORT/api/game/command \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\",\"command\":\"$1\"}" \
  | python3 -c "import sys,json; [print(l.get('s','')) for l in json.load(sys.stdin).get('output',[])]"; }

cmd "help"        # full command listing
cmd "status"      # your level, XP, faction, timer
cmd "tutorial"    # current tutorial step (42 steps total)
cmd "hive"        # the AI hive system overview
cmd "bosses list" # boss encounters
cmd "agents"      # 71 in-game agent roster
cmd "map"         # faction map
cmd "cat /opt/library/.dev_log.md"   # lore content
cmd "cat /home/ghost/.ada_hint"      # hidden Ada message (level 2+)
```

---

## Key Game Concepts

- **Story beats**: `gs.add_story_beat("name")` — persistent narrative flags (set of strings)
- **XP system**: `gs.award_xp("skill_name", amount)` — skills: `hacking`, `social_engineering`, `math`, `data_analysis`, `scripting`, `terminal`, `recon`, `combat`
- **Trust matrix**: `self.trust_matrix.get_trust("ada")` / `self.trust_matrix.adjust_trust("ada", delta)`
- **Factions**: `resistance`, `nexuscorp`, `shadow_council`, `darknet`, `academic`, `architects`, `nihilists`, `loop_walkers`
- **71 agents**: ada, raven, gordon, cypher, zero, nova, serena, malice, herald, vex, lyra... (`cat /opt/colony/roster.txt`)
- **Dispatch flow**: `execute(raw)` → reactive pre-process → `_dispatch(cmd, args)` → `getattr(self, "_cmd_"+cmd)` → alias lookup → NL intercept → `_cmd_not_found`

---

## MCP Integration (recommended for Claude Code)

Add to `.vscode/mcp.json`:
```json
{
  "mcpServers": {
    "terminal-depths": {
      "url": "http://localhost:7337/mcp",
      "type": "http"
    }
  }
}
```

Available MCP tools:
- `list_commands` — full command catalog with descriptions
- `get_game_state` — current player state for a session
- `get_man_page` — read `docs/commands/<name>.md`
- `search_commands` — fuzzy search by keyword
- `get_story_progress` — which beats are hit
- `get_agent_states` — all NPC agent states
- `serena_query` — ask Serena about the codebase

---

## CLAUDE.md Note

The file `CLAUDE.md` at the repo root is **in-game lore content** (the game's meta-layer
and Claude's fictional identity in the Terminal Depths narrative). It is not your operational guide.
THIS file (`.agents/CLAUDE.md`) is your actual working guide.

---

## What's Currently Working (as of 2026-03-24)

- 53/53 tests pass
- 477 commands, all case-insensitive dispatch
- Tutorial (42 steps) fully functional including restart/start/begin variants
- NL intercept: free-text questions route intelligently
- WebSocket bridge + REST API both functional
- Ambient gating (no lore dumps before 20 commands, culture_ship gated to level 5+)
- ML services (offline-first, SQLite-backed)
- Serena sidecar auto-starts
- RimWorld bridge endpoints functional
- MCP server with 28+ tools

## What Needs Work (assign yourself a task)

- `_cmd_nova` — thin dialogue, needs expansion
- `ascend` — story conclusion is a stub, needs actual ending
- Ada dialogue variety — first-contact flow good, subsequent `talk ada` calls repetitive
- Serena drift detection — score always 0.0 (bug in `serena_analytics.py`)
- Challenge validation — too strict on whitespace/case
- `leaderboard` — placeholder, needs real session data
- RimWorld mod compilation (needs VS Code + dotnet toolchain)
- Sound effects — Web Audio ambient works but SFX missing

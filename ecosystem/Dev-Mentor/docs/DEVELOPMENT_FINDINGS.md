# Development Findings — Session Log
> Maintained by: Replit Agent  
> Last updated: 2026-03-24  
> Purpose: Capture bugs found, fixes applied, and guidance for VS Code phase

---

## Critical Bug: Stale `.pyc` Bytecode (FIXED — but read this)

### What happened
`_cmd_restart` and `_cmd_start` were correctly added to `commands.py` and verified via AST parse,
but the live server responded with `bash: restart: command not found` for every player.

### Root cause
`app/game_engine/__pycache__/commands.cpython-311.pyc` had a **source timestamp of
`1970-01-01 00:00:00` (Unix epoch zero)**. Python interprets this special value as
*"this cache is always valid — never check the source file again."*

Every server restart loaded the stale bytecode, silently ignoring all recent edits to
`commands.py`. The file on disk was correct; the running process was not.

### How it was diagnosed
```python
import struct, time
with open('app/game_engine/__pycache__/commands.cpython-311.pyc', 'rb') as f:
    magic = f.read(16)
    ts = struct.unpack('<I', magic[4:8])[0]
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts)))
# Printed: 1970-01-01 00:00:00   ← the smoking gun
```

The difflib suggestions were also a diagnostic signal: `Did you mean: readlink, realpath, reset?`
instead of `restart` meant `_cmd_restart` was literally not in `dir(self)` at runtime.

### Fix applied
1. **Immediate**: Deleted all `.pyc` files and `__pycache__` directories
2. **Permanent**: Added auto-purge to `app/backend/main.py` `_startup()`:
   ```python
   for _pyc in pathlib.Path(".").rglob("*.pyc"):
       try: _pyc.unlink()
       except Exception: pass
   ```

### If you see this again in VS Code
```bash
# Nuke all bytecode caches
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
# Then restart the server
python -m cli.devmentor serve --host 0.0.0.0 --port 7337
```

### Prevention for local development
Add to your shell profile or VS Code task:
```bash
export PYTHONDONTWRITEBYTECODE=1  # Python never writes .pyc files
```
Or run the server with:
```bash
python -B -m cli.devmentor serve --host 0.0.0.0 --port 7337
```

---

## Critical Bug: Port Conflict on Workflow Restart (FIXED)

### What happened
Restarting the workflow left the old Python process alive on port 5000. The new process
failed with `[Errno 98] address already in use` and exited silently — but the OLD process
(with stale code) kept serving requests. The user appeared to have a working server, but
it was running code from before any recent fixes.

### Fix (Replit-specific)
```bash
fuser -k 5000/tcp 2>/dev/null; sleep 1
# then restart workflow
```

### Fix for VS Code / local
The port is 7337 locally. If the server fails to start:
```bash
# Windows (PowerShell)
netstat -ano | findstr :7337
taskkill /PID <pid> /F
# Linux/Mac
fuser -k 7337/tcp
# Or find and kill:
lsof -ti:7337 | xargs kill -9
```

---

## What Currently Works (as of 2026-03-24)

### Game Engine
- **53/53 tests pass** (`python -m pytest tests/ -q`)
- **477 commands** registered and dispatched
- **42-step tutorial** with variant detection and XP awards
- **NL intercept** — free-text questions route to game responses, not "not found"
- **Reactive pre-processing** — unknown input tries NL before failing
- **`restart tutorial`** — all case/phrasing variants work (11/11 tested):
  - `restart tutorial`, `restart the tutorial`, `Restart Tutorial`, `RESTART TUTORIAL`
  - `restart`, `restart tut`, `restart over`, `restart fresh`, `restart again`
  - `restart from the beginning`, `tutorial restart`
- **`start tutorial`** / `start` / `begin tutorial` — all work
- **Case-insensitive dispatch** — `LS`, `HELP`, `PWD` all dispatch correctly
- **Ambient gating** — lore/ambient messages gated behind command thresholds
- **Ada first-contact** — one-time intro flag prevents spam
- **`help`** — works, no ARG topic leaks (old numbered help system gone)

### Infrastructure
- **WebSocket bridge** (`/ws/game`) — real-time game ↔ browser
- **REST API** (`/api/game/command`) — works for external agents and testing
- **Serena analytics sidecar** (port 3001) — auto-starts
- **Model router sidecar** (port 9001) — auto-starts
- **Auto-git sync** — pushes unpushed commits on startup
- **Session persistence** — sessions saved to `sessions/<id>.json`
- **ML services** — model registry, feature store, embedder all functional offline
- **MCP server** — JSON-RPC 2.0 at `/mcp`, 28+ tools
- **RimWorld bridge** — API endpoints at `/api/nusyq`, `/api/council`, `/api/agent`
- **NuSyQ bridge** — manifest publishing, chronicle management

### Tutorial System
- Step 1–42 all defined and validating
- Variant commands (multiple valid answers per step) work
- Replay bonus (second completion awards XP)
- `tutorial`, `tutorial list`, `tutorial step N` all work
- `review` shows progress, `what next` gives guidance

---

## What Needs Fixing / Finishing

### High Priority

| Issue | File | Notes |
|-------|------|-------|
| VS Code port is 7337, not 5000 — some docs still say 5000 | Multiple `.agents/*.md` | Fix before VS Code phase |
| `.pyc` auto-purge adds ~0.5s to startup (rglob over whole tree) | `app/backend/main.py` | Optimize: only purge `app/` subtree |
| `bootstrap.ps1` / `bootstrap.sh` — need verification they set port 7337 | repo root | Test on fresh VS Code clone |
| `Dialog_TerminalREPL.cs` in RimWorld mod — not tested with live server | `mods/TerminalKeeper/Source/UI/` | Needs integration test |
| RimWorld CI workflow auth — loopback bypass may not work in GH Actions | `.github/workflows/ci.yml` | Check `rimworld_bridge.py` bypass logic |

### Medium Priority

| Issue | File | Notes |
|-------|------|-------|
| `_cmd_talk ada` — Ada dialogue variety pool is small after first contact | `commands.py` ~line 4xxx | Add 10+ more Ada responses |
| `_cmd_nova` — NOVA responses are thin | `commands.py` | Expand NOVA dialogue tree |
| Challenge validation too strict on whitespace/case | `app/game_engine/challenge_engine.py` | Normalize input before compare |
| `duel` system — active duel fires on every command but no clear exit | `app/game_engine/duels.py` | Add `duel surrender` / timeout |
| Gordon autonomous player rate-limit — fires too fast, hits API limits | `scripts/gordon_orchestrator.py` | Add configurable sleep between moves |
| Serena drift detection — drift score always 0.0 | `scripts/serena_analytics.py` | Fix the diff/change detector |

### Low Priority / Polish

| Issue | File | Notes |
|-------|------|-------|
| `tutorial` after completion shows all story beats as ambient dump | `app/game_engine/session.py` | Gate post-complete ambient to 1 item max |
| `ascend` story conclusion — not fully written | `commands.py` | Add actual ending cutscene |
| Sound effects — Web Audio ambient plays but SFX missing | `app/static/js/game.js` | Add key-click and hack-success SFX |
| Mobile layout broken below 600px | `app/static/css/game.css` | Add media queries |
| Command history doesn't persist across browser refresh | `app/static/js/game.js` | Use localStorage |
| `leaderboard` command — registered but shows placeholder | `commands.py` | Connect to real session data |

### Never-Started (backlog)

- Multiplayer node messages (players leave hints for each other)
- LLM-powered NPC responses (API integration ready, just not wired to NPC dialogue)
- `ascend` full story conclusion with real ending
- ARG puzzle chain completion (hints exist, final reveal not written)
- VS Code extension wrapping the web console as a native panel
- `challenges` scoring / time-attack leaderboard

---

## Architectural Landmines (Read Before Editing)

### `commands.py` is 32,700+ lines — read tool caps at ~18,600
When reading with the `read` tool in IDEs, you only see the first ~18,600 lines.
Use `sed -n 'START,ENDp'` or `grep -n "def _cmd_"` to find specific methods.

### Two `_cmd_review` definitions exist
- Line 12,080 — tutorial review handler
- Line 30,504 — pentest peer-review system (overrides the first in Python's MRO)
This means `review` in-game always hits the pentest handler. If you want tutorial review,
call `self._tut_review()` directly or rename one of the handlers.

### `prefix` variable scope trap
In `execute()`, `prefix` (the cascade ambient list) is defined inside `_dispatch()` at ~line 1449.
The reactive block runs **before** `_dispatch` at ~line 719. Never reference `prefix` in the
reactive block — it is not yet defined. The existing code already handles this correctly; don't
break it.

### `_info()` does not exist at module scope
`_line()`, `_dim()`, `_ok()`, `_err()`, `_sys()`, `_lore()`, `_warn()` all exist.
`_info()` is **not defined** at module scope and will raise `NameError` crashing the server.

### Aliases dict vs `getattr` dispatch
Commands are found in two places in `_dispatch()`:
1. `getattr(self, f"_cmd_{cmd.lower()}", None)` — finds any method matching the pattern
2. `aliases` dict — manually maps short names to handler methods

If you add a new `_cmd_foo` method, it is automatically discoverable by getattr. The aliases
dict is only needed for commands whose name differs from the method (e.g., `"ll": "_cmd_ls"`).

### `.pyc` epoch-zero timestamp can be created by certain Docker/ZIP operations
If you see unexplained "command not found" for a command you just added, always check the
.pyc timestamp first before debugging the code.

---

## Testing Reference

```bash
# Full test suite (from repo root)
python -m pytest tests/ -q

# Single command smoke test (Replit port 5000, local port 7337)
PORT=5000  # or 7337
curl -sX POST http://localhost:$PORT/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id":"debug","command":"restart tutorial"}' \
  | python3 -c "import sys,json; [print(l.get('s','')) for l in json.load(sys.stdin).get('output',[])]"

# Check which commands exist on the live class
python3 -c "
from app.game_engine.commands import CommandRegistry
cmds = sorted(n[5:] for n in dir(CommandRegistry) if n.startswith('_cmd_') and not n.startswith('_cmd_not_'))
print(f'{len(cmds)} commands:', cmds[:20], '...')
"

# Diagnose stale .pyc
python3 -c "
import struct, time, pathlib
for pyc in pathlib.Path('app').rglob('*.pyc'):
    with open(pyc,'rb') as f: magic = f.read(16)
    ts = struct.unpack('<I', magic[4:8])[0]
    label = 'EPOCH-ZERO (STALE!)' if ts == 0 else time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))
    print(f'{pyc}: {label}')
"
```

---

## Useful Agent Patterns

### Quick game state read (for any agent)
```python
import requests
BASE = "http://localhost:7337"  # 5000 on Replit
r = requests.get(f"{BASE}/api/game/state", params={"session_id": "my-agent"})
state = r.json()["state"]
print(state["level"], state["xp"], state["commands_run"])
```

### Send a command and read output cleanly
```python
import requests
def cmd(session, command, port=7337):
    r = requests.post(f"http://localhost:{port}/api/game/command",
        json={"session_id": session, "command": command})
    return "\n".join(l["s"] for l in r.json().get("output", []) if l.get("s","").strip())

print(cmd("my-agent", "status"))
print(cmd("my-agent", "tutorial"))
```

### Serena knowledge query
```python
import requests
r = requests.post("http://localhost:7337/api/serena/query",
    json={"query": "how does the hive system work?", "session_id": "external"})
print(r.json().get("answer", r.json()))
```

### Add a new command — 3-step checklist
```
1. Add method to CommandRegistry in commands.py:
       def _cmd_mycommand(self, args: List[str]) -> List[dict]:
2. If the name != method suffix, add to aliases dict (~line 1450)
3. Create docs/commands/mycommand.md
4. Syntax-check: python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())"
5. Delete .pyc: find app -name '*.pyc' -delete
6. Restart server and test
```

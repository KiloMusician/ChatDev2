# GitHub Copilot — DevMentor / Terminal Depths Agent Guide
> Updated: 2026-03-24 | Port: 7337 (local/VS Code) | 5000 (Replit)

---

## Project Context

Cyberpunk terminal RPG (Terminal Depths) + VS Code mentorship platform.
FastAPI backend, Python game engine (`commands.py`, 32,700+ lines), 477+ commands,
71 AI agent characters, virtual filesystem, RimWorld mod integration.

---

## Copilot-Specific Tips

### Best Autocomplete Prompts in This Codebase

When adding a new command, open with a docstring and Copilot will complete the body:
```python
def _cmd_mynewcommand(self, args: List[str]) -> List[dict]:
    """mynewcommand [subcommand] [arg] — one-line description (UNLOCK: condition)."""
    gs = self.gs
    sub = args[0].lower() if args else ""
    # Copilot completes: state checks, XP awards, story beats, output helpers
```

### Helper Functions (show Copilot one use and it learns them all)

```python
_sys("  Header text")          # white bold — system/status messages
_ok("  Success message")       # green — confirmations
_err("  Error message")        # red — failures
_dim("  Dim comment")          # muted — secondary info
_lore("  Narrative text")      # amber — story/NPC dialogue
_warn("  Warning message")     # orange — cautions
_line("  Typed text", "info")  # typed line: info/warn/error/success/dim/cyan/yellow
```

**NEVER USE**: `_info()` — undefined at module scope, crashes the server.

### Copilot Chat Commands for This Project

```
@workspace what commands exist for the boss system?
@workspace show me how _cmd_supply is implemented
@workspace how do I add a VFS file to filesystem.py?
@workspace find all story beats in commands.py
/explain app/game_engine/commands.py around _cmd_hive
/tests generate tests for _cmd_restart
```

### Files to Pin in Copilot Context

Priority order (add these to `.github/copilot-instructions.md` or Copilot settings):
1. `CONTEXT.md` — 1-page project overview
2. `app/game_engine/commands.py` lines 1–200 — structure + all helper definitions
3. `app/game_engine/gamestate.py` — full state schema
4. `docs/ARCHITECTURE.md` — system design

### GitHub Copilot CLI

```bash
gh copilot suggest "add a new game command called 'fractal' that renders ASCII Mandelbrot art"
gh copilot suggest "fix the _cmd_talk handler to support 'talk nova' NPC dialogue"
gh copilot explain "what does _cmd_hive do in commands.py?"
gh copilot explain "how does the tutorial step validation work in session.py?"
```

---

## Common Patterns for Copilot to Complete

```python
# Pattern: Standard subcommand dispatch
def _cmd_NAME(self, args: List[str]) -> List[dict]:
    """NAME [list|show|reset] — description."""
    sub = args[0].lower() if args else "list"
    if sub == "list":
        return [_sys("  NAME LIST"), _dim("  (items here)")]
    if sub == "reset":
        self.gs.flags.pop("name_state", None)
        return [_ok("  NAME reset.")]
    return [_err(f"NAME: unknown subcommand '{sub}'"), _dim("  Usage: NAME [list|show|reset]")]

# Pattern: XP award + story beat
gs.award_xp("hacking", 25)
gs.add_story_beat("my_event_name")

# Pattern: Flag-based persistent state
value = gs.flags.get("my_flag", default_value)
gs.flags["my_flag"] = new_value

# Pattern: Level gate
if gs.level < 3:
    return [_dim("  [LOCKED] Requires level 3.")]

# Pattern: Story beat gate
if "unlock_beat" not in gs.story_beats:
    return [_lore("  [???]: Access denied. Trust insufficient.")]
```

---

## Quick Test Loop (Copilot Terminal)

```bash
PORT=7337  # or 5000 on Replit
curl -sX POST http://localhost:$PORT/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id":"copilot-alpha","command":"YOUR_COMMAND"}' \
  | python3 -c "import sys,json; [print(l.get('s','')) for l in json.load(sys.stdin).get('output',[])]"
```

---

## After Any Edit

```bash
# 1. Always syntax-check commands.py
python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())"

# 2. Always delete .pyc to prevent stale bytecode (IMPORTANT)
find app -name '*.pyc' -delete

# 3. Run tests
python -m pytest tests/ -q

# 4. Restart server and test the command
```

---

## What's Working / What Needs Help

**Working**: All 477 commands, tutorial (42 steps), NL intercept, WebSocket bridge,
REST API, ML services, Serena sidecar, ambient gating, case-insensitive dispatch.

**Good Copilot tasks** (medium complexity, well-bounded):
- Expand Ada/Nova NPC dialogue variety
- Add `duel surrender` subcommand and duel timeout
- Fix challenge validation whitespace/case sensitivity
- Write `ascend` story conclusion (currently a stub)
- Add `leaderboard` real data (currently placeholder)
- Fix Serena drift detection (always returns 0.0)
- Write story beat `serena_awakened` for L4 trust unlock

# OpenAI Codex / GPT-4o / ChatGPT — DevMentor Integration Guide
> Updated: 2026-03-24 | Port: 7337 (local/VS Code) | 5000 (Replit)

---

## Function Signatures (Codex autocomplete context)

### Game Command Pattern
```python
def _cmd_COMMAND_NAME(self, args: List[str]) -> List[dict]:
    """COMMAND_NAME [arg1] [arg2] — description (UNLOCK: unlock_condition)."""
    gs = self.gs
    sub = args[0].lower() if args else "default"

    # State access patterns:
    level = gs.level                              # int
    beats = gs.story_beats                        # set of strings
    flags = gs.flags                              # dict
    flag_val = gs.flags.get("key", default)       # safe flag access

    # State mutation patterns:
    gs.add_story_beat("beat_name")               # add story event
    gs.award_xp("skill", amount)                 # award XP
    gs.flags["key"] = value                       # set flag
    gs.unlock("ACHIEVEMENT_ID")                   # unlock achievement

    # Trust matrix (if available):
    if self.trust_matrix:
        trust = self.trust_matrix.get_trust("agent_name")  # int 0-100
        self.trust_matrix.adjust_trust("agent_name", delta)

    # Output helpers (ONLY these exist at module scope):
    return [
        _sys("  Header text"),           # white bold system message
        _dim("  Dim comment"),            # muted text
        _ok("  Success message"),         # green
        _err("  Error message"),          # red
        _lore("  Narrative text"),        # amber/story colored
        _warn("  Warning message"),       # orange
        _line("  Typed text", "info"),    # typed: info/warn/error/success/dim/cyan/yellow
    ]
    # NEVER USE: _info() — undefined at module scope, NameError crash
```

### VFS File Pattern (filesystem.py)
```python
# In _build_tree() or the static VFS dict:
"/path/to/file.txt": _f("""File content here
Line 2
Line 3"""),
"/path/to/dir/": _dir(),  # directory marker
```

### Man Page Template (docs/commands/NAME.md)
```markdown
# NAME

## NAME
name — one line description

## SYNOPSIS
```
name [subcommand] [args]
```

## DESCRIPTION
Full description of what the command does, its lore context, and game mechanics.

## SUBCOMMANDS
- `name list` — shows all items
- `name show <id>` — shows detail for item

## EXAMPLES
```
name list
name show alpha
```

## SEE ALSO
`related_cmd`, `other_cmd`
```

---

## System Prompt for Codex/GPT-4o API Integration

```python
import openai, requests

BASE = "http://localhost:7337"  # 5000 on Replit

# Give GPT-4o full game context
client = openai.OpenAI()
game_state = requests.get(f"{BASE}/api/game/state", params={"session_id": "codex"}).json()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": open("CONTEXT.md").read()[:4000]},
        {"role": "user", "content": f"Current game state: {game_state}. What should I do next?"}
    ]
)

# Extract command and execute
cmd = response.choices[0].message.content.strip()
result = requests.post(f"{BASE}/api/game/command",
    json={"session_id": "codex", "command": cmd})
print(result.json())
```

---

## Autonomous Agent Loop Pattern

```python
import requests, time, openai

BASE = "http://localhost:7337"  # 5000 on Replit
SESSION = "codex-explorer"
client = openai.OpenAI()
SYSTEM = open("CONTEXT.md").read()[:3000] + "\n\nYou are an autonomous agent playing Terminal Depths. Choose the most strategic command based on the current state."

def get_state():
    return requests.get(f"{BASE}/api/game/state", params={"session_id": SESSION}).json()

def run_cmd(command):
    r = requests.post(f"{BASE}/api/game/command",
        json={"session_id": SESSION, "command": command})
    return r.json().get("output", [])

for turn in range(20):
    state = get_state()
    resp = client.chat.completions.create(model="gpt-4o", messages=[
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"State: {state['state']}. Choose ONE command:"}
    ])
    command = resp.choices[0].message.content.strip().split("\n")[0]
    output = run_cmd(command)
    print(f"[{turn}] {command}")
    for line in output:
        if line.get("s", "").strip():
            print("  " + line["s"])
    time.sleep(2)  # rate limit
```

---

## Key Pitfalls for Codex-Generated Code

| Pitfall | Correct Pattern |
|---------|----------------|
| `return _info("text")` | `return [_line("text", "info")]` or `return [_dim("text")]` |
| `gs.xp += 50` | `gs.award_xp("hacking", 50)` |
| Editing commands.py without syntax check | Always run `python3 -c "import ast; ast.parse(...)"` after |
| Not deleting .pyc after edit | `find app -name '*.pyc' -delete` — stale bytecode kills your changes |
| `getattr(gs, "attr")` without default | `getattr(gs, "attr", None)` — GameState has dynamic attrs |
| Using port 5000 in VS Code | Port 7337 for all non-Replit environments |

---

## After Generating / Editing Code

```bash
# Mandatory post-edit sequence:
python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())" && echo "Syntax OK"
find app -name '*.pyc' -delete
python -m pytest tests/ -q
# Then restart server and test the specific command
```

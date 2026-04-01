# Terminal Depths — Modding API

> This document explains how to extend Terminal Depths with custom commands, challenges, NPCs, story beats, and agent scripting.

---

## Overview

Terminal Depths is designed to be modded. The architecture separates:

| Layer | Location | Language |
|-------|----------|----------|
| **Commands** | `app/game_engine/commands.py` | Python |
| **JS Commands** | `app/frontend/game/commands.js` | JavaScript |
| **Game State** | `app/game_engine/gamestate.py` | Python |
| **NPCs** | `app/game_engine/npcs.py` | Python |
| **Story beats** | `app/game_engine/story.py` | Python |
| **Filesystem** | `app/game_engine/filesystem.py` | Python |
| **LLM** | `llm_client.py` | Python |
| **Memory/Cache** | `memory.py` | Python |

---

## 1. Adding a Custom Command (Python backend)

Commands are methods on the `CommandRegistry` class in `app/game_engine/commands.py`.

### Step-by-step

1. Open `app/game_engine/commands.py`
2. Add a method named `_cmd_<yourcommand>`:

```python
def _cmd_greet(self, args: List[str]) -> List[dict]:
    name = args[0] if args else "stranger"
    self.gs.add_xp(5, "terminal")          # award XP (amount, skill)
    return [
        _line(f"Hello, {name}!", "success"),
        _line("XP awarded for social engineering.", "dim"),
    ]
```

3. The command is automatically available as `greet <name>` in the game.

### Helper functions

```python
_line(text, type="info")   # generic line
_ok(text)                  # green success
_err(text)                 # red error
_sys(text)                 # cyan system
_dim(text)                 # grey dim
_story(text)               # purple story
_xp_line(text)             # yellow XP notification
```

### Line types (the `t` field)

| Type | Color | Use |
|------|-------|-----|
| `info` | white | Default output |
| `success` | green | Positive result |
| `error` | red | Failure |
| `warn` | yellow | Warning |
| `system` | cyan | System messages |
| `story` | purple | Narrative text |
| `npc` | orange | NPC speech |
| `dim` | grey | Meta info |
| `xp` | yellow italic | XP award |
| `ls-row` | — | File listing row (special) |

---

## 2. Adding a JavaScript Command (frontend)

Frontend commands live in `app/frontend/game/commands.js` in the `CommandRegistry` class.

```javascript
_cmd_greet(args) {
    const name = args[0] || 'stranger';
    this.gs.addXp(5, 'terminal');
    return [
        { t: 'success', s: `Hello, ${name}!` },
        { t: 'dim',     s: 'XP awarded.' },
    ];
}
```

The method name becomes the command after removing `_cmd_` and replacing `_` with `-`.

---

## 3. Adding a Challenge

### In JavaScript (frontend)

Challenges are defined in `app/frontend/game/game.js` in the `CHALLENGES` array:

```javascript
{ 
  id:  'c41',
  title: 'My Custom Challenge',
  cat:   'Security',
  xp:    50,
  desc:  'Use the greet command with your name',
  validate: (history) => history.some(c => c.startsWith('greet '))
}
```

Fields:
- `id` — unique string (e.g. `c41`)
- `title` — display name
- `cat` — category (Terminal, Security, Network, Coding, etc.)
- `xp` — XP reward
- `desc` — player-facing description
- `validate(history, gs?)` — function returning `true` when complete

### Via LLM generation (in-game)

```bash
# In the game terminal:
generate challenge --category Security --difficulty hard
```

---

## 4. Adding a Custom NPC

### Step-by-step

1. Open `app/game_engine/npcs.py`
2. Add your NPC to the `NPC_DATA` dict:

```python
"mystic": {
    "name": "MYSTIC",
    "personality": "cryptic prophet",
    "color": "#cc88ff",
    "responses": {
        "default": [
            "The bits speak in riddles.",
            "Seek the zero-day. It finds you.",
        ],
        "hello": ["You found me. Now what?"],
    },
    "unlock_beat": None,    # or a story beat ID required to talk
    "first_meet_xp": 20,
}
```

3. The NPC is accessible via `talk mystic` in the game.

### Dialogue patterns

The `responses` dict supports:
- `"default"` — fallback responses
- Any keyword that appears in the player's message
- `"*<word>"` — exact match

---

## 5. Adding Story Beats

Story beats are triggered events in `app/game_engine/story.py`.

```python
# In StoryEngine._build_beats():
Beat(
    id="met_mystic",
    trigger=lambda cmd, gs: cmd.startswith("talk mystic"),
    message="[MYSTIC]: The signal is between the lines.",
    xp=30,
    title="Mystic Contact",
    once=True,   # triggers only once
)
```

Beat fields:
- `id` — unique string; stored in `gs.storyBeats`
- `trigger(cmd, gs)` — predicate returning True
- `message` — text shown in terminal (purple story style)
- `xp` — XP bonus
- `title` — short label for timeline/toast
- `once` — whether it fires only once (default True)

---

## 6. Extending the Virtual Filesystem

Add files and directories in `app/game_engine/filesystem.py` in the `_DEFAULT_FS` structure.

```python
"home": {
    "type": "dir",
    "children": {
        "ghost": {
            "type": "dir",
            "children": {
                "secret_note.txt": {
                    "type": "file",
                    "content": "The mole's name begins with N...",
                    "perms": "-rw-r--r--",
                    "owner": "ghost",
                    "size": 44,
                }
            }
        }
    }
}
```

---

## 7. Using the LLM API

From any Python file:

```python
from llm_client import get_client, Prompts

llm = get_client()

# Simple generation
response = llm.generate("Describe a new network node in cyberpunk style", max_tokens=100)

# Chat
response = llm.chat([
    {"role": "system", "content": Prompts.SYSTEM_GAME},
    {"role": "user", "content": "I found the mole. What happens next?"}
])

# Cached (deterministic) call
response = llm.generate(prompt, temperature=0.3)  # auto-cached
```

### Prompt templates

```python
Prompts.npc_response(npc_name, personality, player_input)
Prompts.generate_challenge(category, difficulty)
Prompts.generate_lore(node_name, context)
Prompts.generate_command_handler(cmd_name, flags, description)
```

---

## 8. Writing In-Game Scripts (ns API)

Players can write scripts and run them inside the game:

```javascript
// example: auto-recon.td
const result = await ns.run("nmap -sV 10.0.1.254");
const output = await ns.llm("Summarize this nmap output: " + result);
ns.print(output);
await ns.sleep(1000);
await ns.run("hack chimera-control");
```

### ns API surface

| Function | Description |
|----------|-------------|
| `ns.run(cmd)` | Execute a terminal command |
| `ns.print(text)` | Print to terminal |
| `ns.llm(prompt)` | LLM call via game backend |
| `ns.aiChat(msgs)` | Multi-turn chat |
| `ns.getState()` | Get current game state |
| `ns.addXp(n, skill)` | Award XP |
| `ns.sleep(ms)` | Pause |
| `ns.writeFile(path, content)` | Write to VFS |
| `ns.readFile(path)` | Read from VFS |
| `ns.ls(path)` | List directory |

---

## 9. MCP Tool Integration

Terminal Depths exposes a JSON-RPC 2.0 MCP server at `mcp/server.py` with these tools:

| Tool | Description |
|------|-------------|
| `td_run_command` | Execute a game command |
| `td_game_state` | Read full game state |
| `td_write_file` | Write to virtual filesystem |
| `td_read_file` | Read from virtual filesystem |
| `td_list_directory` | List VFS directory |
| `td_memory_store` | Store to agent memory |
| `td_memory_search` | Search agent memory |
| `td_llm_generate` | Generate text via LLM |
| `td_chronicle` | Read game chronicle |
| `td_git_push` | Push to git |
| `td_system_status` | System health status |

---

## 10. Plugin System

Plugins live in `plugins/` and extend DevMentor via `plugins/manager.py`.

```python
# plugins/my_plugin.py

class MyPlugin:
    name = "my-plugin"
    version = "1.0.0"

    def on_command(self, cmd: str, gs) -> list | None:
        """Optional: intercept commands. Return list to override output, None to pass through."""
        if cmd == "myplugin":
            return [{"t": "success", "s": "My plugin works!"}]
        return None

    def on_level_up(self, level: int, gs) -> None:
        """Called when player levels up."""
        pass

    def on_xp(self, amount: int, skill: str, gs) -> None:
        """Called when XP is awarded."""
        pass
```

Register in `plugins/manager.py`:
```python
from plugins.my_plugin import MyPlugin
manager.register(MyPlugin())
```

---

## 11. Creating New World Nodes

World nodes are procedurally generated network servers. Use the batch generator:

```bash
python scripts/generate_node_batch.py --count 5 --theme corporate
```

Themes: `corporate`, `underground`, `resistance`, `academic`, `gov`, `darknet`

Each generated node includes:
- Virtual filesystem with lore files
- A resident challenge
- An NPC type
- Network graph connections

---

## File Locations Quick Reference

```
app/
  game_engine/
    commands.py      — Command handlers (Python)
    gamestate.py     — Game state, XP, levels
    npcs.py          — NPC roster and dialogue
    story.py         — Story beats
    filesystem.py    — Virtual filesystem
    session.py       — HTTP session manager
  frontend/
    game/
      commands.js    — Client-side commands
      game.js        — Main game loop, rendering
      gamestate.js   — Client state
      npcs.js        — Client NPC system
      story.js       — Client story engine
      sound.js       — Audio system
      style.css      — Styles
      index.html     — Entry point

llm_client.py        — Multi-backend LLM client
memory.py            — SQLite agent memory
plugins/             — Plugin system
mcp/server.py        — MCP JSON-RPC server
scripts/             — Content generation scripts
stubs/               — Deterministic LLM stubs (JSON)
```

---

## Testing Your Mod

1. Make your changes
2. Restart the DevMentor Console workflow
3. Open the game at `/game`
4. Test your command in the terminal
5. Check the LOG tab for events and error messages

```bash
# Or run a quick Python test:
python -c "
from app.game_engine.gamestate import GameState
from app.game_engine.filesystem import VirtualFS
from app.game_engine.commands import CommandRegistry
gs = GameState()
fs = VirtualFS()
cmds = CommandRegistry(fs, gs, None, None, None)
print(cmds.execute('greet world'))
"
```

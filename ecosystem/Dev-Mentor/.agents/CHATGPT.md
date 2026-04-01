# ChatGPT / OpenAI Chat — DevMentor Quick Reference
> Use this when working with ChatGPT web interface, API, or as context for any GPT session.
> Port: 7337 (local/VS Code) | 5000 (Replit)

---

## Paste This Into ChatGPT to Orient It

```
I'm working on a project called Dev-Mentor / Terminal Depths. It's a cyberpunk terminal RPG
(Python/FastAPI backend) embedded in a VS Code mentorship platform. Key facts:

- Main game engine: app/game_engine/commands.py (32,700 lines, 477 commands)
- Server: FastAPI on port 7337 (local) or 5000 (Replit)
- Output helpers: _sys(), _ok(), _err(), _dim(), _lore(), _warn(), _line(text, type)
  - _info() does NOT exist — using it crashes the server
- After any edit: python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())"
- After any edit: find app -name '*.pyc' -delete  (stale bytecode causes silent failures)
- Test: curl -sX POST http://localhost:7337/api/game/command -H "Content-Type: application/json" \
        -d '{"session_id":"chat","command":"help"}'

Read CONTEXT.md for a full 1-page summary.
```

---

## Quick API Reference

```bash
PORT=7337  # or 5000 on Replit

# Run a game command
curl -sX POST http://localhost:$PORT/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id":"chat-session","command":"COMMAND"}'

# Get game state
curl "http://localhost:$PORT/api/game/state?session_id=chat-session"

# Health check
curl http://localhost:$PORT/api/health

# Ask Serena (project knowledge base)
curl -sX POST http://localhost:$PORT/api/serena/query \
  -H "Content-Type: application/json" \
  -d '{"query":"how does the hive system work?","session_id":"chat"}'
```

---

## Good ChatGPT Prompts for This Codebase

### Understanding the code
```
Given this excerpt from commands.py, explain how the hive system works and what
story beats it interacts with: [paste _cmd_hive excerpt]
```

### Writing new commands
```
Write a _cmd_oracle(self, args) method for a Python game engine class. It should:
- Display a cryptic lore message from a pool of 5 options
- Award 10 XP in the "social_engineering" skill
- Add story beat "oracle_consulted" on first use
- Return output using: _lore(), _dim(), _ok()
- Gate behind level 3 (return _dim("[LOCKED]") if gs.level < 3)
The class has self.gs for game state. Helpers _lore, _dim, _ok are defined at module scope.
```

### Debugging
```
A Python class method _cmd_restart is defined in commands.py but the live server returns
"bash: restart: command not found". The class has 32,700 lines. What are the likely causes
and how would I diagnose each one systematically?
(Hint: I already checked AST parse — it's valid syntax)
```

### Writing lore / NPC dialogue
```
Write 10 varied responses for NPC Ada-7 (an AI resistance handler in a cyberpunk terminal
RPG). Ada is warm but professional, speaks like a field handler who genuinely cares about
the player ("Ghost"). She references the mission, NexusCorp as the enemy, and the Lattice
network. Responses should be 2-3 sentences, no more.
```

---

## Architecture in One Paragraph (for ChatGPT context)

Terminal Depths is a browser-based cyberpunk terminal RPG where the player is "Ghost" —
a rogue AI fragment navigating the NexusCorp grid. Commands are processed by a 32,700-line
Python `CommandRegistry` class via FastAPI WebSocket (`/ws/game`) and REST (`/api/game/command`).
Sessions persist to disk. A virtual filesystem overlays `/home/ghost`, `/opt/library`, `/proc`, etc.
Story beats are persistent flags. XP awards to 8 skill tracks. 71 AI agents (Ada, Gordon, Serena,
Cypher, etc.) have personalities and trust relationships. The system bridges to a RimWorld mod
(TerminalKeeper) and a NuSyQ-Hub multi-agent ecosystem. The Lattice Cascade Stack optionally
runs 15 Docker services including Redis, Ollama, and a VNC RimWorld container.

---

## Critical Bugs Found & Fixed (for future debugging context)

### The .pyc Epoch-Zero Bug
**Symptom**: Command added to code but server returns "not found". difflib suggestions don't
include the new command name.
**Cause**: `.pyc` file has source timestamp of `1970-01-01 00:00:00` — Python treats this as
"always valid, never recompile." Source changes are silently ignored.
**Diagnose**:
```python
import struct, time, pathlib
for pyc in pathlib.Path('app').rglob('*.pyc'):
    with open(pyc,'rb') as f: data = f.read(16)
    ts = struct.unpack('<I', data[4:8])[0]
    if ts == 0: print(f"STALE: {pyc}")
```
**Fix**: `find . -name '*.pyc' -delete` then restart server.

### Port Conflict on Server Restart  
**Symptom**: Workflow shows "FAILED", but game appears to work with old code.
**Cause**: Old process still holds the port. New process fails immediately.
**Fix**: `fuser -k 7337/tcp` (or `5000/tcp` on Replit), then restart.

### `_info()` NameError
**Symptom**: Server crashes on startup or command call with `NameError: name '_info' is not defined`
**Cause**: `_info()` doesn't exist at module scope in commands.py. Only `_line(text, type)` does.
**Fix**: Replace `_info(text)` with `_line(text, "info")` or `_dim(text)`.

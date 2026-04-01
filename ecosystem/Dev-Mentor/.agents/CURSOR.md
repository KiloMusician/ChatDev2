# Cursor IDE — DevMentor / Terminal Depths Agent Guide

## @ Mentions (most useful)
- `@CONTEXT.md` — full project context
- `@AGENTS.md` — all agent integration docs
- `@app/game_engine/commands.py` — game command engine
- `@docs/ARCHITECTURE.md` — system architecture
- `@docs/API_REFERENCE.md` — REST API docs

## Cursor Rules
Project rules are in `.cursor/rules/project.mdc` — automatically loaded for all .py and .md files.
They define: coding rules, helper functions, key file list, command patterns, test commands.

## Composer Prompts (Ctrl+I)
Great prompts for this codebase:
- "Add a new command `treasure` that reveals a random achievement hint. Follow the pattern in _cmd_fortune."
- "Add VFS file /opt/library/new_file.txt with this content: [content]. Follow the _f() pattern in filesystem.py."
- "Fix the _cmd_rivalry method to also handle `rivalry reset` subcommand."
- "Add story beat 'my_new_beat' to the ambient tick at line ~870 in commands.py."

## Tab Completion Context
Set these files as "always include" in Cursor settings:
1. CONTEXT.md
2. app/game_engine/commands.py (first 100 lines only — model context)
3. app/game_engine/gamestate.py

## Chat Context (@codebase queries)
- "Where is the hive system implemented?"
- "How does the trust matrix work?"
- "What achievements are currently available?"
- "Find all places where story beats are added"

## Quick Test Loop
```bash
# Run from Cursor terminal
curl -sX POST http://localhost:7337/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"session_id":"cursor","command":"YOUR_COMMAND"}' \
  | python3 -c "import sys,json; [print(l.get('s','')) for l in json.load(sys.stdin).get('output',[])]"
```

## Cursor-Specific Workflow
1. Open `app/game_engine/commands.py` — use Ctrl+G to jump to line 1415 (dispatch table)
2. Add your command alias there
3. Jump to end of file (Ctrl+End) — add your `_cmd_` method
4. Run the test loop above
5. Syntax check: `python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())"`

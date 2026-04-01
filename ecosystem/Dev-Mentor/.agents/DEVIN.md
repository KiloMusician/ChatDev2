# Devin — DevMentor / Terminal Depths Agent Guide

## Task Breakdown Strategy
Devin works best with clear, isolated tasks. Here's the optimal task format for this project:

### Task Template
```
TASK: Add [feature name] to Terminal Depths

CONTEXT: Read CONTEXT.md and AGENTS.md first.

FILES TO MODIFY:
  - app/game_engine/commands.py (add method _cmd_[name])
  - [Register in dispatch at line ~1415]
  - docs/commands/[name].md (create man page)

IMPLEMENTATION:
  1. Add method _cmd_[name](self, args: List[str]) -> List[dict] to CommandRegistry class
  2. Use helpers: _sys(), _ok(), _err(), _dim(), _lore(), _line(text, type)
  3. Access game state: gs = self.gs; gs.level; gs.flags; gs.story_beats
  4. Register: add "[name]": "_cmd_[name]" to aliases dict ~line 1415

VALIDATION:
  python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read()); print('OK')"
  curl -sX POST http://localhost:7337/api/game/command -H "Content-Type: application/json" \
    -d '{"session_id":"devin","command":"[name]"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['output']), 'lines')"

SUCCESS CRITERIA:
  - AST parses clean
  - Command returns non-empty output
  - Man page exists at docs/commands/[name].md
  - No duplicate method definitions
```

## Devin-Specific Notes
- Always run the validation step before marking done
- The file is large (30,000+ lines) — use grep/sed to navigate, never read/write the whole file
- If adding to the end of the class, insert BEFORE `def to_dict(self):`
- The dispatch dict is the "routing table" — every new command needs an entry there

## Environment Setup for Devin
```bash
cd /workspace
pip install -r requirements.txt
python -m cli.devmentor serve --host 0.0.0.0 --port 7337 &
sleep 3
curl http://localhost:7337/api/health  # should return {"status": "ok"}
```

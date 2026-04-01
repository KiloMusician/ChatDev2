# Aider — DevMentor / Terminal Depths Agent Guide

## Quick Start
```bash
# Recommended launch command
aider --config .aider.conf.yml \
      --read CONTEXT.md \
      --read AGENTS.md \
      --read docs/ARCHITECTURE.md \
      app/game_engine/commands.py

# Minimal: add a single command
aider --read CONTEXT.md app/game_engine/commands.py docs/commands/
```

## Best Aider Workflows for This Project

### Add a new game command
```
aider --read CONTEXT.md app/game_engine/commands.py
> Add a command called 'treasure' that picks a random achievement from gs.achievements 
> and reveals a hint about how to earn it. Follow the helper patterns in the file.
> Register it in the aliases dict and return a properly formatted output list.
```

### Add VFS content
```
aider --read CONTEXT.md app/game_engine/filesystem.py
> Add a new VFS directory /opt/library/philosophy/ with 3 files:
> truth.txt (Boolean Monk treatise on truth), void.txt (Nihilist view), and time.txt (Loop Walker perspective).
> Each 10 lines. Follow the existing _f() pattern in the file.
```

### Fix a broken command
```
aider app/game_engine/commands.py
> The _cmd_rivalry method returns empty output when called with 'rivalry status'.
> Find the issue and fix it. Do not rewrite the method wholesale.
```

## Critical Flags for This Project
```bash
--lint-cmd "python3 -m py_compile {file}"   # catch syntax errors immediately
--test-cmd "python3 -c \"import ast; ast.parse(open('app/game_engine/commands.py').read())\""
--no-auto-commits                             # review changes before committing
--read CONTEXT.md                             # always include project context
```

## The .aider.conf.yml
A `.aider.conf.yml` is pre-configured at the project root. It sets:
- model: gpt-4o
- reads CONTEXT.md, AGENTS.md, docs/ARCHITECTURE.md on every session
- lint and test commands pre-configured

## Anti-Patterns (Aider commonly falls into these)
- DO NOT ask Aider to "rewrite commands.py" — it will fail (file too large)
- DO NOT use `_info()` — undefined, will crash
- DO make targeted requests: "add this specific method" or "modify lines X-Y"
- DO always include `--read CONTEXT.md` for project context

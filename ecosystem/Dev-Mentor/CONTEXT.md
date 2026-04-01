# Terminal Depths / Dev-Mentor — Universal AI Context
> Last updated: Sprint "Take Flight (B)" — March 2026
> See HANDOFF.md for full "passing the torch" detail.

## Project Summary
Terminal Depths is a VS Code-native cyberpunk terminal RPG and AI mentorship platform. It combines a massive (32k+ line) game engine with a FastAPI backend, MCP server, ML services layer, and a bidirectional RimWorld mod integration — allowing AI agents, human players, and RimWorld colonists to all interact with a persistent world.

## Key Facts
| Fact | Value |
|------|-------|
| Language | Python 3.11+ / C# .NET 4.7.2 (RimWorld mod) |
| Backend | FastAPI (app/backend/main.py — 5022 lines) |
| Ports | **5000 (Replit ONLY)** / **7337 (Docker/Local/VSC)** |
| Database | SQLite × 4 (agent_memory, model_registry, feature_store, embeddings) |
| Game Engine | app/game_engine/commands.py (477+ commands, 32,105 lines) |
| MCP Server | mcp/server.py (28+ tools) |
| RimWorld Mod | mods/TerminalKeeper/ (needs dotnet build → TerminalKeeper.dll) |
| ML Layer | services/ (model_registry, feature_store, embedder, inference) |

## Critical Files
- `app/game_engine/commands.py`: Core game logic (dispatch + commands)
- `app/game_engine/filesystem.py`: Virtual Filesystem (VFS) implementation
- `app/game_engine/gamestate.py`: Player and world state management
- `app/backend/main.py`: API entry point
- `mcp/server.py`: MCP tool definitions and handlers
- `AGENTS.md`: Detailed guide for all agent types
- `docs/commands/`: Man pages for every game command

## Command Cheatsheet (Top 30)
`help`, `status`, `ls`, `cat`, `cd`, `talk`, `hive`, `quests`, `skills`, `map`, `nmap`, `exploit`, `man`, `commands search`, `whoami`, `mail`, `inventory`, `shop`, `build`, `raid`, `escort`, `multiverse`, `profile`, `leaderboard`, `puzzle`, `secret`, `rev`, `turret`, `fifthwall`, `agents`.

## How To
- **Run Server**: `python -m app.backend.main`
- **Run Tests**: `python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())"`
- **Add Command**: Define `_cmd_<name>(self, args)` in `CommandRegistry` class in `commands.py`, then register in `aliases` dict.
- **Add VFS Content**: Edit `VFS` dict in `app/game_engine/filesystem.py`.
- **Call API**: `POST /api/game/command` with `{"session_id": "...", "command": "..."}`.

## Anti-Patterns
- **NO `_info()`**: Use `_line(text, type)`, `_dim()`, `_ok()`, `_err()`, `_sys()`, or `_lore()`.
- **NO Re-writes**: `commands.py` is huge. Use surgical edits only.
- **Ports**: Use 5000 for Replit, 7337 for local/Docker.
- **Direct State**: Always check if attribute exists on `gs` before accessing (`getattr(gs, '...', default)`).

## Launchers (Any Surface)
```bash
./devmentor.sh serve        # Linux/macOS
.\devmentor.ps1 serve       # PowerShell
devmentor.bat serve         # CMD
docker compose up           # Docker base
python -m cli.devmentor serve  # Direct Python
```

## RimWorld Integration (mods/TerminalKeeper/)
| What | How |
|------|-----|
| Colonist plays Terminal Depths | Interact with TK_LatticeTerminal → Dialog_TerminalREPL |
| Cyberware sync | TD install → POST /api/nusyq/cyberware_sync → HediffDef applied |
| Story beat → colony incident | cascade.py fires → polled by WorldComponentTick every ~25s |
| XP sync | TD skill XP → /api/nusyq/xp_sync → RW SkillDef level set |
| Build mod | dotnet build mods/TerminalKeeper/Source/JobsTerminalKeeper.csproj |

## Anti-Patterns (READ BEFORE CODING)
- **NO `_info()`**: Use `_line(text, type)`, `_dim()`, `_ok()`, `_err()`, `_sys()`, `_lore()`
- **NO rewrites of commands.py**: 32k lines — grep/sed/offset reads only
- **Port 5000 = Replit ONLY, port 7337 = everything else**
- **Always `getattr(gs, 'attr', default)`** — never direct attribute access on GameState

## Agent Roles
- **Claude/Copilot/Codex/Cursor**: General development, code completion, game expansion
- **Serena**: Long-term memory, code archaeology, context retrieval (sidecar daemon)
- **Gordon**: Strategic planning, autonomous gameplay (REST-based bot)
- **ChatDev**: NuSyQ-Hub integration, multi-agent generation
- **SkyClaw**: Security auditing, vulnerability scanning, penetration testing
- **Claw(s)**: Advanced exploit research, cascade story triggers

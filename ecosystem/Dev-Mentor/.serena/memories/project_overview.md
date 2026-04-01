# Dev-Mentor — Project Overview

## Purpose
Cyberpunk terminal RPG mentorship tool + VS Code-native coding mentor. Originally from Replit.
- **Terminal Depths**: text-based cyberpunk RPG game (FastAPI backend + HTML/JS frontend)
- **Mentor system**: 10 autonomous agents that review code, generate challenges, write lore
- **CHUG Engine**: 7-phase perpetual self-improvement cycle (ASSESS→PLAN→EXECUTE→VERIFY→CONSOLIDATE→DOCUMENT→EXPORT)
- **NuSyQ integration**: `nusyq_bridge.py` dual-writes game events to NuSyQ-Hub's `state/memory_chronicle.jsonl`

## Location
`C:/Users/keath/Dev-Mentor/`

## Related repos
- NuSyQ-Hub: `C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/` (primary hub, shares chronicle)
- SimulatedVerse: `C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/` (consciousness substrate)
- NuSyQ: `C:/Users/keath/NuSyQ/` (multi-agent generation core)

## Tech Stack
- **Backend**: FastAPI (`app/backend/main.py`) — 60+ API endpoints
- **Frontend**: HTML/JS in `app/frontend/` — game UI + CLI interface
- **Game engine**: Python in `app/game_engine/` — commands, scripting, filesystem, gamestate, session, story, npcs
- **Agents**: 10 Python agents in `agents/` — orchestrator, llm_agent, content_generator, implementer, tester, validator, challenger, documenter, lore_generator, player
- **Language**: Python 3.12 (`C:/Users/keath/AppData/Local/Programs/Python/Python312/python.exe`)
- **Package manager**: uv (`uv.lock` present) — use `uv run` or activate venv
- **Linting**: Biome (`biome.json`) for frontend JS/TS; ruff for Python
- **Memory DB**: SQLite at `.devmentor/agent_memory.db`

## Key Files
- `app/backend/main.py` — FastAPI app: 60+ routes (game, memory, LLM, NuSyQ bridge, git, security)
- `agents/orchestrator.py` — CHUG cycle runner: `cycle()`, `run_agent()`, `generate_status_report()`
- `agents/implementer.py` — coverage report (server must be running for API coverage)
- `chug_engine.py` — CHUG perpetual cycle entry point
- `nusyq_bridge.py` — NuSyQ-Hub integration: `chronicle()`, `report_event()`, `sync_quests()`
- `app/game_engine/commands.py` — **37,360 lines** (~37k LOC); 534 command handlers; surgical edits only

## CRITICAL: Port Rule
- **7337** = Terminal Depths locally (VS Code / Docker / terminal) — ALWAYS use this
- **5000** = Replit compat layer ONLY — NEVER use locally
- **8000** = NuSyQ-Hub Agent API
- **11434** = Ollama
- **1234** = LM Studio

## AST Safety Rule
After EVERY edit to `commands.py`:
```bash
python -c "import ast; ast.parse(open('app/game_engine/commands.py').read()); print('AST OK')"
```

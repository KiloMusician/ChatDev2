# Task Completion Checklist — Dev-Mentor

## After every Python change:
```bash
python -m ruff check .
python -m ruff check . --fix
```

## After every edit to commands.py (MANDATORY):
```bash
python -c "import ast; ast.parse(open('app/game_engine/commands.py').read()); print('AST OK')"
```
commands.py is **37,360 lines** — a syntax error here breaks the entire game engine.

## After every frontend JS change:
```bash
npm run lint:fix
```
Note: 47 pre-existing Biome errors remain in `app/frontend/` — don't count against new work.

## Key invariants to preserve:
- **Port rule**: 7337 = local always. 5000 = Replit ONLY. Never break this.
- `app/backend/main.py` NuSyQ endpoints: `nusyq_status`, `nusyq_manifest`, `nusyq_sync_quests`, `nusyq_chronicle`, `nusyq_schedule`
- `nusyq_bridge.py` dual-writes to both local `.devmentor/chronicle.jsonl` AND `NuSyQ-Hub/state/memory_chronicle.jsonl`
- Game engine: **534 handlers** in commands.py (was 182 handlers + 72 stubs — fully implemented as of 2026-03)
- `agents/implementer.py` is the health check for stub coverage — run it to see progress
- Output primitive in commands.py: `_line(text, cls)` — NOT `_styled()`, NOT `print()`
- Session ID pattern: `str(int(gs.run_start_time))` — NOT `gs.session_id` (doesn't exist)

## When adding a new game command:
1. Add handler `_cmd_<name>` in `app/game_engine/commands.py`
2. Register it in the `CommandRegistry` dispatch table
3. Run the AST check above
4. Run `python agents/implementer.py` to update coverage report
5. Test via `curl -X POST http://localhost:7337/api/game/command -d '{"command":"<name>"}'`

## When adding a new API endpoint:
1. Add to `app/backend/main.py`
2. Run `python agents/implementer.py` to update coverage report

## Workspace files (which to open):
- `Dev-Mentor.code-workspace` — canonical 5-repo ecosystem workspace (Dev-Mentor + NuSyQ-Hub + SimulatedVerse + NuSyQ + prime_anchor); absolute paths, all DM terminal profiles
- `Dev-Mentor-Complete.code-workspace` — same + embedded tasks + launch configs; uses `${workspaceFolder:Dev-Mentor}` variables
- `TerminalKeeper.ecosystem.code-workspace` — focused RimWorld/C# mod work

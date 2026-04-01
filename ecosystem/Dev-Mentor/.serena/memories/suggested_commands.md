# Suggested Commands — Dev-Mentor

## Shell environment
- Platform: Windows 11, Git Bash (MINGW64)
- Python: `C:/Users/keath/AppData/Local/Programs/Python/Python312/python.exe`
- Package manager: `uv` (uv.lock present)

## ⚠️ Port Rule — CRITICAL
**Port 7337 = local/Docker/VS Code. Port 5000 = Replit ONLY.**
Never start the server on 5000 when working locally.

## Run the backend server (local)
```bash
cd /c/Users/keath/Dev-Mentor
python -m cli.devmentor serve --port 7337
# or via uvicorn directly:
uvicorn app.backend.main:app --reload --port 7337
```

## Quick health check
```bash
curl -s http://localhost:7337/api/health | python -m json.tool
```

## AST check after commands.py edit (ALWAYS run this)
```bash
python -c "import ast; ast.parse(open('app/game_engine/commands.py').read()); print('AST OK')"
```

## Agents / CHUG cycle
```bash
python agents/orchestrator.py          # run one CHUG cycle
python chug_engine.py                  # perpetual self-improvement loop
python agents/implementer.py           # coverage report (needs server running)
python agents/tester.py                # run tests via agent
python playtest.py                     # playtest game interactively
```

## Linting & Formatting
```bash
# Python
python -m ruff check .
python -m ruff check . --fix

# Frontend JS (Biome)
npm run lint          # biome check app/frontend/
npm run lint:fix      # biome check --write app/frontend/
npm run format        # biome format --write app/frontend/
```

## Testing
```bash
python -m pytest tests/ -q
```

## NuSyQ bridge
```bash
python -c "from nusyq_bridge import chronicle; chronicle('test', 'hello')"
python -c "from nusyq_bridge import report_event; report_event('test', {})"
```

## Git
```bash
git status
git add -A && git commit -m "feat: ..."
```

## MCP server (for Claude Code integration)
```bash
python mcp/server.py   # stdio mode — Claude Code connects via .vscode/mcp.json
```

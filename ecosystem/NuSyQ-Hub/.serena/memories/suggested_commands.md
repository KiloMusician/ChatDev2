---
name: NuSyQ-Hub development commands
description: All development commands for health checks, testing, linting, MJOLNIR dispatch, and git operations
type: project
---

## Health & Status
```bash
python scripts/start_nusyq.py brief                          # Quick system health
python scripts/start_nusyq.py system_complete --budget-s=300 # Full 7-check gate
python scripts/nusyq_dispatch.py status --probes             # Probe all 20 agents
```

## Testing
```bash
python -m pytest tests/ -q                                   # Full suite (~9,500 tests)
python -m pytest tests/ -q --no-cov                          # No coverage (faster)
python -m pytest tests/test_foo.py -q                        # Single file
python -m pytest tests/ -m "not slow" -q                     # Fast subset
python -m pytest tests/integration/ -q                       # Integration tests
# Coverage (threshold 30%):
python -m coverage run -m pytest tests/test_foo.py -q --no-cov && python -m coverage report --include="src/path/to/file.py"
```

## Linting
```bash
python -m ruff check src/ scripts/ --fix                     # Auto-fix
python -m ruff check src/ scripts/ --fix --unsafe-fixes --select RUF059,RUF013,C401,C411,C414
python -m ruff format src/ scripts/                          # Format
python -m mypy src/core/orchestrate.py src/integration/mcp_server.py src/tools/agent_task_router.py --strict --follow-imports=skip
```

## MJOLNIR Dispatch
```bash
python scripts/nusyq_dispatch.py ask ollama "prompt"
python scripts/nusyq_dispatch.py council "question" --agents=ollama,lmstudio
python scripts/nusyq_dispatch.py chain "analyze then fix" --agents=ollama,codex --steps=analyze,generate
python scripts/nusyq_dispatch.py queue "task" --priority=HIGH
python scripts/nusyq_dispatch.py poll <task_id>
python scripts/nusyq_dispatch.py recall culture_ship --limit=5
python scripts/nusyq_dispatch.py skyclaw status
```

## Git
```bash
git config core.hooksPath .githooks                          # Activate hooks (once after clone)
# Stage specific files (not -A — avoid accidentally staging .env or large files)
git add src/path/to/file.py tests/test_foo.py
# Large JSON files (labels.index.json is 18MB) — always commit ALONE:
git add SimulatedVerse/reports/labels.index.json && git commit -m "data: update labels"
```

## Culture Ship
```bash
python scripts/start_nusyq.py culture_ship_cycle --sync      # Full audit cycle
python scripts/activate_culture_ship.py                      # Direct activation
```

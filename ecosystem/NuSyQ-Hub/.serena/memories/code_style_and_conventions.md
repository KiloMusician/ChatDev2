---
name: NuSyQ-Hub code style and conventions
description: Formatting rules, type hints, naming conventions, async patterns, and import traps
type: project
---

## Formatting
- Ruff formatter + linter (replaces black + isort + flake8)
- Python formatter: `charliermarsh.ruff` in VS Code
- Line length: 88 chars (ruff default)
- `editor.formatOnSave: true` with `source.organizeImports: explicit` and `source.fixAll: explicit`

## Type Hints
- All new code should have type hints
- mypy strict gate on 3 files only: `orchestrate.py`, `agent_task_router.py`, `mcp_server.py`
- Full src/ has ~20 pre-existing mypy errors — do NOT add `source = src` to mypy config
- Use `Optional[X]` or `X | None` (ruff RUF013 auto-fixes `Optional` → `| None` with `--unsafe-fixes`)
- `cast()` needed at JSON load boundaries (json.load returns Any)

## Naming Conventions
- Classes: PascalCase (`BackgroundTaskOrchestrator`)
- Functions/methods: snake_case (`submit_task`, `route_task`)
- Constants: UPPER_SNAKE_CASE (`AGENT_ALIASES`, `AGENT_PROBES`)
- Type aliases: `QuestId = str`, `AgentId = str` (exported from `src/guild/__init__.py`)
- `qid` = quest ID variable (string UUID), NOT a package reference

## Async Patterns
- Guild ops: all `async` — use `@pytest.mark.asyncio` in tests
- `asyncio_mode = auto` in pytest.ini — all async test functions auto-detected
- `_tasks: set[asyncio.Future[Any]] = set()` at module level + `fut.add_done_callback(_tasks.discard)` for RUF006
- Use `asyncio.run()` NOT `loop.run_until_complete()` in non-async contexts (avoids closed-loop errors)

## Import Patterns
- `src/integration/` (singular) for cross-system bridges
- `src/integrations/` (plural) for Nogic + OpenClaw only
- Lazy imports in `__init__.py` via `__getattr__` for optional heavy dependencies
- `# noqa: F401` on `import asyncio` in agent_registry.py (required for monkeypatch.setattr)

## F-strings
- ASCII art inside f-strings: escape `{field}` as `{{field}}` — ruff F821 fires on unescaped identifiers
- dotenv inline comments corrupt values: `KEY=value  # comment` → actual value includes ` # comment`

## Ruff Rules Requiring `--unsafe-fixes`
- RUF059: unused unpacked vars → `_`-prefix
- RUF013: implicit Optional → `T | None`
- C401/C411/C414: collection simplifications

## Globally Ignored Ruff Rules
- D100-D105, D107: missing docstrings (legacy files being refactored)
- Per-file ignores for `scripts/**/*.py`: D212, D301, D417, N801, N817, RUF001-003, A002, C416, RUF012, RUF015, RUF034

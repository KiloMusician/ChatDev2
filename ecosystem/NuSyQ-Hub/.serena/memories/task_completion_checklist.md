---
name: NuSyQ-Hub task completion checklist
description: Steps to verify before marking any code change complete — lint, test, mypy gate, pre-commit scope, coverage rules
type: project
---

Before marking any task complete, run these in order:

## 1. Lint (zero violations required)
```bash
python -m ruff check src/ scripts/ --fix
python -m ruff format src/ scripts/
# For unsafe fixes (RUF059, RUF013, C401/C411/C414):
python -m ruff check src/ scripts/ --fix --unsafe-fixes --select RUF059,RUF013,C401,C411,C414
```

## 2. Tests
```bash
# Affected file tests only (fast):
python -m pytest tests/test_<affected>.py -q
# Full suite if touching dispatch/orchestration/guild:
python -m pytest tests/ -q --no-cov
# Target: 0 failures, 0 errors (40 skips are expected/normal)
```

## 3. Mypy Gate (only if touching the 3 gated files)
```bash
python -m mypy src/core/orchestrate.py src/integration/mcp_server.py src/tools/agent_task_router.py --strict --follow-imports=skip
# Gate fails → must fix before committing
```

## 4. Pre-commit Scope Check
- New untracked files in `src/` will be checked by `black --check src/` and `ruff check src/` even if unstaged
- Format+lint ALL new files before staging, not just the ones you're committing
- `.vscode/settings.json` is gitignored — changes there don't get committed

## 5. Coverage (only if coverage dropped)
```bash
# Per-file coverage (avoids full-suite denominator inflation):
python -m coverage run -m pytest tests/test_foo.py -q --no-cov && python -m coverage report --include="src/path/to/file.py"
# Threshold: 30% for full suite. Do NOT add `source = src` to .coveragerc
```

## 6. Git Safety
- Stage specific files, never `git add -A` (risks committing .env, large binaries)
- Large JSON (labels.index.json 18MB) — commit alone in its own commit
- Pre-push hook runs mypy on `src/guild/` and `src/config/` with `--follow-imports=skip`
- If pre-push fails with `KeyError: 'is_bound'` → stale mypy cache → `rm -rf .mypy_cache`

## Common Task Category Fixes
When writing tests for `EnhancedTaskScheduler`:
- Use `task.metadata["category"] = "TEST"` to force category (not keyword matching)
- "improve" keyword → REFACTOR (not TEST). Use "add coverage report" for TEST.
- SECURITY category → vetoed by ConsciousnessLoop (auto-approves when bridge unavailable)

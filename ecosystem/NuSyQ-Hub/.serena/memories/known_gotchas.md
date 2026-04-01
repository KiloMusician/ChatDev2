---
name: NuSyQ-Hub known gotchas and traps
description: Critical traps for sync/async methods, test isolation, imports, Windows-specific issues, and ShipApproval field names
type: project
---

## Sync/Async Traps
- `BackgroundTaskOrchestrator.submit_task()` — SYNC, returns BackgroundTask directly, do NOT await
- `EnhancedTaskScheduler.select_next_batch()` — SYNC, returns list, do NOT await
- `EcosystemActivator.activate_system()` — SYNC

## Test Isolation
- `task = MagicMock()` → `task.context.get("key")` returns truthy MagicMock, not None. Always pin `task.context = {}`
- `GuildBoard` default `state_dir=Path("state/guild")` loads 70+ live quests. Use `GuildBoard(state_dir=tmp_path/"guild", data_dir=tmp_path/"data")` in tests
- `auto_release_claim_on_heartbeat_timeout=True` by default — set to False or call `await board.agent_heartbeat()` before `claim_quest()` in tests
- `_chatdev_factory_fallback` creates real files — patch `src.tools.agent_task_router.ProjectFactory = None` to truly disable
- `sys.modules.pop()` in teardown causes stale `__globals__` in class instances — don't pop modules that were imported during test

## Import Traps
- `src/integration/` (singular) ≠ `src/integrations/` (plural) — mixing causes ModuleNotFoundError
- `OllamaModelManager` was removed from `src/ai/__init__.py` — use functions from `src.ai.ollama_model_manager` directly
- `culture_ship_strategic_advisor` is in `src/orchestration/`, NOT `src/culture_ship/`
- `QuestSystem` alias = `QuestManager` (in `src/Rosetta_Quest_System/quest_manager.py`)

## Windows-Specific
- Git Bash (MINGW64) — use Unix syntax. `localhost` may resolve to IPv6 `[::1]`; use `127.0.0.1` explicitly
- `make` not installed — use `git config core.hooksPath .githooks` directly
- `_windows_path_to_wsl` in `repo_path_resolver.py` is guarded with `sys.platform == "win32"` — do NOT remove guard
- WSL relay for Ollama: WinError 10053/10054 = stale relay. Fix: `wsl --shutdown` in admin PowerShell
- `git add -A -- ':!file'` fails on Windows bash — use `git add -A && git reset -- file` instead
- Pre-push mypy hook uses `--follow-imports=skip` — required to avoid 100+ transitive backlog errors
- Stale mypy cache `KeyError: 'is_bound'` — fix: `rm -rf .mypy_cache`

## ShipApproval Field Names
- `SimulatedVerseUnifiedBridge.ShipApproval` uses `.reasoning`
- `ConsciousnessLoop.ShipApproval` uses `.reason`
- Never mix them — silent attribute errors

## Coverage
- Do NOT add `source = src` to `.coveragerc` — inflates denominator from 30K to 86K stmts, drops % to ~5%
- Threshold: 30% (core suite achieves ~36%)
- `test_quantum.py` alone pulls below 33% (quantum_problem_resolver.py is 796 stmts, 19% covered)

## Pre-commit Hooks
- `check-yaml` excludes `knowledge-base.yaml` (mixes YAML+markdown sections)
- pytest-fast hook runs offline tests only (not integration/, not live-connection tests)
- `config/agent_router.py` and `src/tools/search_omnitags.py` have pytest guard for sys.stdout replacement

## Task Categorization
- `EnhancedTaskScheduler.categorize_task()` checks `task.metadata["category"]` FIRST before keyword scan
- "improve" keyword matches REFACTOR before TEST — use "add coverage report" for TEST category

## Dispatch Test Count Invariant
- Adding agents to AGENT_PROBES requires updating: `test_registry_has_all_agents` expected set, `test_status_no_probes` count assertion (currently 20), `test_display_names_match_probes`

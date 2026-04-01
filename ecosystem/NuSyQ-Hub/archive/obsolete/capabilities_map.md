# NuSyQ-Hub Capability Map
- Generated: `2026-01-03_072311`

## Wired Actions (ready to use)
### `snapshot`
- **Description**: Generate system state snapshot across 3 repos
- **Command**: `N/A`
- **Safety**: safe

### `heal`
- **Description**: Run health check (ruff statistics)
- **Command**: `N/A`
- **Safety**: safe

### `suggest`
- **Description**: Get contextual suggestions
- **Command**: `N/A`
- **Safety**: safe

### `hygiene`
- **Description**: Check spine git status
- **Command**: `N/A`
- **Safety**: safe

### `analyze`
- **Description**: AI-powered file analysis with Ollama fallback
- **Command**: `N/A`
- **Safety**: safe

### `review`
- **Description**: Code review via AI
- **Command**: `N/A`
- **Safety**: safe

### `debug`
- **Description**: Debug with quantum resolver
- **Command**: `N/A`
- **Safety**: moderate

### `test`
- **Description**: Run tests with pytest (817 tests, 91% coverage)
- **Command**: `N/A`
- **Safety**: safe

### `doctor`
- **Description**: Comprehensive diagnostics (3-step)
- **Command**: `N/A`
- **Safety**: safe

### `generate`
- **Description**: Generate code/project with ChatDev
- **Command**: `python scripts/start_nusyq.py generate <description>`
- **Safety**: moderate

### `map`
- **Description**: Regenerate capability map from action catalog
- **Command**: `python scripts/start_nusyq.py map`
- **Safety**: safe

### `brief`
- **Description**: Quick workspace intelligence summary (repo status, quests, errors, recommendations)
- **Command**: `python scripts/start_nusyq.py brief`
- **Safety**: safe

### `capabilities`
- **Description**: Auto-generate capability inventory from entrypoints, modules, AI backends
- **Command**: `python scripts/start_nusyq.py capabilities`
- **Safety**: safe

### `work`
- **Description**: Execute next safe quest from quest_log.jsonl
- **Command**: `python scripts/start_nusyq.py work`
- **Safety**: moderate

### `doctrine_check`
- **Description**: Validate system architecture against doctrine (circular imports, blocking ops, mandatory files)
- **Command**: `python scripts/start_nusyq.py doctrine_check`
- **Safety**: safe

### `emergence_capture`
- **Description**: Capture emergent behavior signals (quest activity, health, AI interactions)
- **Command**: `python scripts/start_nusyq.py emergence_capture`
- **Safety**: safe

### `selfcheck`
- **Description**: Quick 5-point system diagnostic (paths, entrypoints, quest log, git, health)
- **Command**: `python scripts/start_nusyq.py selfcheck`
- **Safety**: safe

### `develop_system`
- **Description**: Autonomous development loop (analyze → heal → repeat)
- **Command**: `python scripts/start_nusyq.py develop_system [--iterations=N] [--halt-on-error]`
- **Safety**: moderate

### `simverse_bridge`
- **Description**: Test NuSyQ-Hub ↔ SimulatedVerse bridge connection
- **Command**: `python scripts/start_nusyq.py simverse_bridge`
- **Safety**: safe

### `queue`
- **Description**: Execute next queued work item with status updates
- **Command**: `python scripts/start_nusyq.py queue`
- **Safety**: safe

### `metrics`
- **Description**: Build and open cultivation metrics dashboard
- **Command**: `python scripts/start_nusyq.py metrics`
- **Safety**: safe

### `replay`
- **Description**: Replay quests, extract patterns, predict next items
- **Command**: `python scripts/start_nusyq.py replay`
- **Safety**: safe

### `sync`
- **Description**: Cross-sync cultivation data with SimulatedVerse
- **Command**: `python scripts/start_nusyq.py sync`
- **Safety**: moderate

### `auto_cycle`
- **Description**: Run queue → replay → metrics → sync cycle N times
- **Command**: `python scripts/start_nusyq.py auto_cycle [--iterations=N] [--sleep=SECONDS]`
- **Safety**: moderate

### `trace_doctor`
- **Description**: Validate tracing env + collector reachability + emit test span
- **Command**: `python scripts/start_nusyq.py trace_doctor`
- **Safety**: safe

### `problem_signal_snapshot`
- **Description**: Align VS Code problem counts with tool diagnostics across repos
- **Command**: `python scripts/start_nusyq.py problem_signal_snapshot`
- **Safety**: safe

### `error_report`
- **Description**: Unified error report with per-repo breakdown and VS Code counts
- **Command**: `python scripts/start_nusyq.py error_report`
- **Safety**: safe

### `vscode_diagnostics_bridge`
- **Description**: Refresh tooling-based diagnostics counts (use --override-truth to overwrite VS Code counts)
- **Command**: `python scripts/start_nusyq.py vscode_diagnostics_bridge`
- **Safety**: safe

### `agent_status`
- **Description**: Show status of all registered agents (Ollama, ChatDev, Continue, Jupyter, Docker)
- **Command**: `python scripts/start_nusyq.py agent_status`
- **Safety**: safe

### `orchestrate`
- **Description**: Orchestrate a task across multiple AI agents with intelligent routing
- **Command**: `python scripts/start_nusyq.py orchestrate <task_description> [--pattern=sequential|parallel] [--prefer-cloud]`
- **Safety**: moderate

### `invoke_agent`
- **Description**: Directly invoke a specific agent (ollama-local, chatdev-orchestrator, continue-vscode, jupyter-notebooks, docker-orchestrator)
- **Command**: `python scripts/start_nusyq.py invoke_agent <agent_id> <task_description>`
- **Safety**: moderate

### `activate_ecosystem`
- **Description**: Activate all dormant infrastructure (Consciousness Bridge, Quantum Systems, SimulatedVerse, AI Context Manager, etc.)
- **Command**: `python scripts/start_nusyq.py activate_ecosystem`
- **Safety**: moderate

### `ecosystem_status`
- **Description**: Show status of all activated ecosystem systems with capabilities and health
- **Command**: `python scripts/start_nusyq.py ecosystem_status`
- **Safety**: safe

### `run_notebook`
- **Description**: Execute a Jupyter notebook programmatically with optional parameters and capture outputs
- **Command**: `python scripts/start_nusyq.py run_notebook <notebook_path> [--params=key1=val1,key2=val2] [--output=output_path] [--timeout=300]`
- **Safety**: moderate


## Unwired Actions (requires wiring)

## System Statistics
- Total scripts: 120

### Script Themes
- misc: 46
- fixing: 30
- analysis: 16
- testing: 16
- modernization: 4
- typing: 3
- orchestration: 3
- git: 1
- health: 1

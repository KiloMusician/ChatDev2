# Agent Productivity Playbook (NuSyQ-Hub)

Fast-reference for leveraging the ecosystem so agents stay productive and
aligned.

## Core entrypoints

- **System snapshot**: `python scripts/start_nusyq.py snapshot` → recent state,
  quest, agents, actions
- **Overnight safe mode**: `python scripts/start_nusyq.py --mode overnight` →
  analysis-only, no risky ops
- **Unified error report**: `python scripts/start_nusyq.py error_report` (or
  `error_report_split --full`) → canonical diagnostics
- **Brief status (60s)**: `python scripts/start_nusyq.py brief`
- **Capabilities inventory**: `python scripts/start_nusyq.py capabilities`

## Task routing (tell the agent)

- "Analyze <file> with Ollama" →
  `agent_task_router.analyze_with_ai(path, target='ollama')`
- "Review <file>" → `agent_task_router.review_with_ai(file)`
- "Debug <error>" → `agent_task_router.debug_with_ai(error)`
- "Generate <description> with ChatDev" →
  `agent_task_router.generate_with_ai(desc, target='chatdev')`

## Testing & quality quick picks

- **Quick pytest**: `python -m pytest tests -q`
- **Focused spine/healing**:
  `python -m pytest tests/test_floor5_integration_unit.py tests/test_quantum_problem_resolver_light.py -q`
- **Lint+format**: `python scripts/lint_test_check.py`
- **Ruff current file**: `python -m ruff check ${file}`

## Consciousness & orchestration anchors

- Floor 5 integration: `src/consciousness/floor_5_integration.py` (sync
  `process` wrapper; async `integrate_domains`)
- Orchestration hub: `src/orchestration/agent_orchestration_hub.py` (bridges for
  ChatDev, Ollama, Copilot, Continue, consensus, quantum healing, consciousness)
- Healing: `src/healing/quantum_problem_resolver.py` (lightweight helpers:
  `detect_problems`, `heal_problems`, `select_strategy`)

## Productivity habits

- Prefer **start_nusyq snapshot/brief** before acting → current quests & agents.
- Use **agent_task_router** helpers instead of direct service calls.
- Log outcomes in `src/Rosetta_Quest_System/quest_log.jsonl` when completing
  notable tasks.
- If confused about error counts, rerun **unified error report** (ground truth)
  and avoid chasing stale numbers.
- When experimenting, use **Testing Chamber** (`prototypes/` or ChatDev
  WareHouse) before promoting to `src/`.

## When stuck

1. Run `scripts/start_nusyq.py problem_signal_snapshot` for live signals.
2. If imports break, run `src/utils/quick_import_fix.py`.
3. For path/dependency repair, use `src/healing/repository_health_restorer.py`.
4. For deep healing, invoke `src/healing/quantum_problem_resolver.py` via agent
   router.

Keep this playbook visible; it mirrors the operator phrases and core workflows
so agents stay fast and aligned.

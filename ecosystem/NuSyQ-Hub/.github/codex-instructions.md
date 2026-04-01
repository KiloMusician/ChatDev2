# NuSyQ-Hub Codex Instructions

## Big Picture
- NuSyQ-Hub is the orchestration/knowledge hub of a **tripartite system** (NuSyQ-Hub, NuSyQ, SimulatedVerse). Treat this repo as the control plane for multi-agent automation, templates, and system health workflows (see `README.md`).
- Canonical “what’s next” sources: `src/Rosetta_Quest_System/quest_log.jsonl`, `docs/Checklists/PROJECT_STATUS_CHECKLIST.md`, and `config/ZETA_PROGRESS_TRACKER.json` (AGENTS protocol).

## System Health + Ground Truth
- If error counts disagree, **always** run the ground truth report: `scripts/start_nusyq.py error_report` (AGENTS protocol). Report both the VS Code view and actual scan counts.
- For a system state snapshot, run `scripts/start_nusyq.py` to generate `state/reports/current_state.md`.
- Self-healing tools:
  - `src/diagnostics/system_health_assessor.py`
  - `src/healing/repository_health_restorer.py`
  - `src/utils/quick_import_fix.py`
  - `src/diagnostics/ImportHealthCheck.ps1` or `src/healing/quantum_problem_resolver.py`

## Workflow Conventions
- **Three Before New**: before creating any new tool/script, run
  `python scripts/find_existing_tool.py --capability "..." --max-results 5` and reuse/extend top matches. Log justification if you still create a new tool.
- Session breadcrumbs: update the latest `docs/Agent-Sessions/SESSION_*.md` when you complete meaningful work.
- Use tagging systems (OmniTag/MegaTag/RSHTS) when you need semantic anchors across code/docs (see `README.md`).

## AI Routing (Local + Multi-Agent)
- Use the task router in `src.tools.agent_task_router` for agent operations:
  - Analyze: `analyze_with_ai(...)`
  - Generate: `generate_with_ai(...)`
  - Review: `review_with_ai(...)`
  - Debug: `debug_with_ai(...)`
- Supported systems: `auto`, `ollama`, `chatdev`, `consciousness`, `quantum_resolver` (AGENTS protocol).

## Repo Layout & Examples
- Core code lives under `src/`, tests in `tests/`, docs in `docs/`, scripts in `scripts/`, web in `web/` (AGENTS + README).
- For architecture context, start at `README.md` and `docs/SYSTEM_MAP.md`, `docs/ROUTING_RULES.md`, `docs/OPERATIONS.md`.

## Guardrails
- Prefer enhancing existing files over adding new ones; do not add new top-level dirs without approval (AGENTS protocol).
- If stuck, re-run the system snapshot and re-anchor using quest log + ZETA tracker.

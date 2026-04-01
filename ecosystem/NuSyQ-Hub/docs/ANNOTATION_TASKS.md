## Repository Annotation Tasks (assistant-tracked)

Purpose: track systematic addition of developer- and agent-friendly
module docstrings, guidance, troubleshooting notes, and tag updates across
the codebase. This file is maintained by the automated editing agent as a
running checklist and guidance reference for future edits.

Guiding principles
- Small, safe edits first: prefer module-level docstrings and comments.
- No behavioral changes unless a syntax/error fix is required.
- Validate using static checks after each batch.
- Record status and next steps here.

How to use
- The agent will update status markers (TODO / IN-PROGRESS / DONE).
- Human reviewers can follow the checklist and run the validation commands.

Quick validation commands (run locally):
```powershell
# Run the project's test suite (if present)
python -m pytest -q

# Run static error checker used by the workspace
# (tooling may vary; use provided VS Code Problems or CI tasks)
```

---

Batch 1 — Completed (docstrings & small fixes)
- [x] `src/tools/maze_solver.py` — added guidance, safe_print notes, outputs
- [x] `src/tools/run_and_capture.py` — added usage notes (encoding, interrupts)
- [x] `src/tools/log_indexer.py` — added ingestion guidance
- [x] `src/tools/repo_scan.py` — expanded agent tips
- [x] `src/tools/extract_commands.py` — added purpose & integration notes
- [x] `src/tools/ChatDev-Party-System.py` — added guidance and tags
- [x] `src/tools/wizard_navigator.py` — annotated as deprecated shim
- [x] `src/tools/structure_organizer.py` — added guidance
- [x] `src/tools/launch-adventure.py` — added guidance + fixed syntax in `ensure_ollama_running`
- [x] `src/tools/chatdev_testing_chamber.py` — added sandbox guidance
- [x] `src/utils/helpers.py` — added guidance
- [x] `src/utils/quick_import_fix.py` — expanded docstring and warnings
- [x] `src/utils/import_health_checker.py` — added module-level guidance
- [x] `src/utils/repository_analyzer.py` — added guidance
- [x] `src/utils/file_organization_auditor.py` — expanded guidance
- [x] `src/utils/generate_structure_tree.py` — added usage tips

Batch 2 — Next (small/medium utilities)
- [ ] `src/utils/import_health_checker.py` — (follow-up) address lint warnings and logging patterns (separate pass)
- [ ] `src/utils/quick_import_fix.py` — replace broad excepts where safe
- [ ] `src/utils/quick_github_audit.py` — add guidance and outputs
- [ ] `src/utils/import_health_checker.py::tests` — add small unit tests for parsing helpers

Batch 3 — Medium complexity (after approvals)
- [ ] `src/tools/kilo_discovery_system.py` — annotate high-level architecture and integration points
- [ ] `src/tools/kilo_dev_launcher.py` — clarify usage and environment requirements
- [ ] `src/tools/health_restorer.py` — document safety and rollback recommendations

Batch 4 — Large / high-risk modules (careful, multi-step)
- [ ] `src/spine/*` — annotate purpose, high-level design, and public APIs
- [ ] `src/orchestration/*` — add ingest points and examples for agent integration

Validation & QA
- After each batch:
  - Run static checks (Problems pane / get_errors tool).
  - Run a small smoke test (e.g., run `python -m src.tools.maze_solver . --max-depth 2`).
  - Ensure new log or summary artifacts appear in `logs/` when applicable.

Housekeeping & PR notes
- Keep edits in small commits. If a code fix is needed, include a brief
  explanation and reference in the commit message.
- Prefer adding tests for non-trivial behavioral fixes.

Owner: assistant (automated annotation agent)

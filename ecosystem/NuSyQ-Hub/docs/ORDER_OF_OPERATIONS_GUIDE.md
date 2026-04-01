# Order of Operations Guide

This guide captures the **structured workflow agents should follow** across all three repositories (NuSyQ-Hub, SimulatedVerse, NuSyQ) so that the system remains traceable, deterministic, and portable.

## 1. Phase 0 – Zero-Token Preparation (Always Run First)

1. **Activate the workspace**: `python scripts/check_env.py` and `python scripts/activate_ecosystem.py` register the required paths and services across the three repos.  
2. **Sync the project checklist**:
   - `python scripts/checklist_to_quests.py` converts every unchecked entry in `docs/Checklists/PROJECT_STATUS_CHECKLIST.md` into a `add_quest` event inside `src/Rosetta_Quest_System/quest_log.jsonl`.
   - This keeps workspace state aligned with the ZETA tracker (`config/ZETA_PROGRESS_TRACKER.json`), the guild board (`state/guild/guild_board.json`), and the PU queue (`data/unified_pu_queue.json`).
3. **Run deterministic lint/build scripts**:
   - `python scripts/chug_helpers.py` runs the zero-token sequence (ruff, mypy, auto-fix import tests, hygiene target) plus the checklist sync noted above.
   - The same step now also executes `python scripts/copilot_hang_monitor.py --check` to guard Copilot/process hangs and `python scripts/snapshot_delta_report.py` to extend the system-state trace with deltas.
   - If extra inspection is needed, `python scripts/start_nusyq.py hygiene` and `python scripts/start_nusyq.py error_report` provide comprehensive diagnostics.

## 2. Phase 1 – CHUG Cycle (Core Actions)

Repeat these steps inside the CHUG interface (`scripts/chug_helpers.py`, `scripts/start_nusyq.py auto_cycle`, or the VS Code `NuSyQ: Checklist Sync` task plus manual `run` tasks):

1. **Auto-cycle (Perpetual)**:
   - `python scripts/start_nusyq.py auto_cycle --iterations=N --sleep=S` performs Culture Ship audits, PU queue processing, metrics, and next-action generation for the entire tripartite workspace.
   - Reuse the same commands in SimulatedVerse (if available) or NuSyQ root by invoking their `start_nusyq.py` equivalents.
2. **Test & validate**: After each CHUG iteration, run targeted regression suites (`pytest`, `scripts/run_clean_coverage.py tests/`) or module tests (e.g., `scripts/test_culture_ship_cycle.py`) to ensure wiring still holds.
3. **Capture trace artifacts**: The auto-cycle writes receipts to `state/receipts/`, updates `data/terminal_logs/`, and logs PU queue metrics to `Reports/` so the next agent can see what triggered each action.

## 3. Phase 2 – Enablement & Routing

1. **Router wiring**:
   - `scripts/start_nusyq.py guild_status` and `scripts/start_nusyq.py guild_render` expose the guild board; call them after each sprint to sync agent handoffs with quests.
   - The PU queue CLI (`src/automation/unified_pu_queue.py`) is used by Culture Ship, auto-theater audits, and the orchestration layer; invoke `demo`, `status`, or `execute` when debugging routing.
2. **ZETA & checklist coherence**:
   - Run `python src/tools/zeta_progress_updater.py` after mission-critical quests complete to update `config/ZETA_PROGRESS_TRACKER.json`.
   - Keep `docs/Checklists/PROJECT_STATUS_CHECKLIST.md` and `src/Rosetta_Quest_System/quest_log.jsonl` in sync by rerunning `scripts/checklist_to_quests.py` before manual work.
3. **Trace modernization**:
   - Use `src/tools/perpetual_action_generator.py` and `state/next_action_queue.json` to determine prioritized actions for QA, modernization, or documentation work.
   - Run `python scripts/placeholder_playbook.py` to refresh the plugin registry, publish Copilot prompt guidance, capture the System Health Assessor summary, and log the placeholder fix in `reports/placeholder_playbook_report.md`.

## 4. Phase 3 – Documentation & Export

1. **Capture snapshots**:
   - `scripts/start_nusyq.py snapshot`, `python scripts/analyze_current_state.py`, and `state/reports/current_state.md` record the workspace status for future follow-up tasks.
   - Export to portable ZIP via `python scripts/devmentor_portable.py export` and include the “Continue in VS Code” checklist.
2. **Document updates**:
   - Update `docs/PERPETUAL_CHUG_LOOP.md`, `docs/OPERATIONS.md`, and `README.md` whenever you introduce new wiring (e.g., new tasks, commands, autosync flows).
   - Append a short report to `reports/` or the guild board to capture what changed and why.

## 5. Closing the Loop

1. **Guild board**: Post heartbeats (`scripts/start_nusyq.py guild_heartbeat`) and quest completions to keep the board synced with actual work.
2. **Quest lifecycle**: After finishing a placeholder, log it as completed in `src/Rosetta_Quest_System/quest_log.jsonl` (with tags, completion status, and a link to the doc or code change).  
3. **Next sprint**: Refer back to the order-of-operations guide and the ZETA tracker to select the next placeholder (plugin registry, modernization, trace, etc.) and repeat the loop.

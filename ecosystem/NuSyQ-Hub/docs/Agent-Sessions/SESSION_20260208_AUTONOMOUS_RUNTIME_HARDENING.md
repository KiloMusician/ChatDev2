# Session: Autonomous Runtime Hardening (2026-02-08)

## Objective
Stabilize autonomous operation so long-running cycles keep working without queue corruption/truncation and without reprocessing completed work.

## Root Causes Found
1. `UnifiedPUQueue` dataclass loading was brittle:
   - Queue entries with extra fields (`completed_at`, `associated_quest_id`, etc.) caused load failures.
   - On failure, in-memory queue became empty, and later saves truncated `data/unified_pu_queue.json`.
2. `AutonomousLoop` task selection filter was logically wrong:
   - `status != completed OR note != simulated` selected nearly everything, including completed entries.
3. Audit-generated PU schema drift:
   - `_run_audit()` wrote `source` (legacy) instead of `source_repo` and omitted modern queue fields.
4. Runtime resilience:
   - Unhandled exception classes could terminate the loop abruptly.

## Patches Applied

### `src/automation/unified_pu_queue.py`
- Extended `PU` dataclass with compatibility fields:
  - `completed_at`, `failed_at`, `last_error`, `associated_quest_id`, `background_task_id`, `dependencies`.
- Hardened `_load_queue()`:
  - Per-entry normalization (including `source` -> `source_repo` migration).
  - Default filling for required fields.
  - Skip invalid records instead of failing entire queue load.
- Hardened `_save_queue()`:
  - Merge by `id` with existing on-disk records.
  - Preserve unknown/external fields from other writers.
  - Prevent accidental queue truncation when mixed-schema writers are active.

### `src/automation/autonomous_loop.py`
- `start()` and `run_cycle()` now catch/log broad exceptions for operational visibility.
- `_run_audit()` now emits modern queue schema (`source_repo`, `proof_criteria`, `metadata`, etc.).
- `_get_next_tasks()` now selects only active statuses:
  - `approved`, `queued`, `pending`, `in_progress`.
- `_execute_tasks()` now classifies deferred states as `skipped` instead of `failed`:
  - `pending`, `queued`, `in_progress`, `submitted`, `delegated`.
- `_delegate_heavy_tasks_to_background()` now considers:
  - `pending`, `approved`, `queued`.

### `run_autonomous.py`
- Added traceback printing for non-keyboard crashes to make failures visible in logs.

### `nusyq.bat`
- Added persistent service commands using existing service manager:
  - `autosvc-start`, `autosvc-stop`, `autosvc-status`, `autosvc-restart`.

### `scripts/autonomous_monitor.py`
- Added idle-queue recovery:
  - seeds new PUs from canonical sector gaps when no pending work is found.
- Fixed missing import for `PU` in gap-seeding path:
  - eliminated silent seed failure when queue becomes fully completed.
- Tightened gap dedupe to active queue states only (`queued/approved/pending`), so completed history no longer blocks reseeding.
- Added configurable subprocess timeout for `auto_cycle`:
  - `--auto-cycle-timeout` (default `240s`).
- Trace hygiene:
  - monitor now clears in-memory trace entries each cycle so each trace file is one-cycle scoped and easier to audit.

### `scripts/start_autonomous_service.py`
- Added `--auto-cycle-timeout` plumbing and forwarding into monitor process startup.
- Startup log now prints timeout value for operator visibility.
- Enhanced `--status` output with hard runtime evidence:
  - latest trace filename
  - last auto-cycle return code + command
  - three-vantage command return codes
  - PU queue status distribution
  - aggregate execution counters from `data/execution_metrics.json`
- Hardened PID liveness detection:
  - `is_running()` now validates process command line contains the monitor script path, avoiding false positives from PID reuse.

### Python 3.10 compatibility hotfixes
- Replaced direct `from datetime import UTC` imports with fallback (`timezone.utc`) in:
  - `src/system/ai_metrics_tracker.py`
  - `src/tools/vibe_indexer.py`
  - `src/tools/register_lattice.py`
  - `src/orchestration/unified_autonomous_healing_pipeline.py`
- Result:
  - auto-cycle metrics step no longer fails with `cannot import name 'UTC'`.

## Validation
1. Compile checks passed:
   - `run_autonomous.py`
   - `src/automation/autonomous_loop.py`
   - `src/automation/unified_pu_queue.py`
2. Compatibility smoke test:
   - Mixed-schema queue loaded successfully.
   - Unknown fields preserved after save.
   - Legacy `source` migrated to `source_repo`.
3. End-to-end cycle test:
   - `python run_autonomous.py --cycles 1 --tasks 5 --refill-mode audit+gaps --min-pending 10`
   - Completed with queue updates, quest generation, metrics save, and no fatal crash.
4. Persistent service test:
   - `python scripts/start_autonomous_service.py --restart --interval 300 --auto-cycle on-pending --auto-cycle-timeout 60`
   - Confirmed running PID + trace artifact with successful `auto_cycle` (`return_code=0`).

## Operational Note
For unattended Windows-hosted operation, prefer service mode over transient shell sessions:

```bat
nusyq.bat autosvc-start --interval 300 --auto-cycle on-pending
nusyq.bat autosvc-status
```

## Continuation Update (2026-02-10)

### Runtime evidence (live)
- `python scripts/start_autonomous_service.py --status` confirms monitor is running and cycling.
- Queue now reports active throughput directly in live queue counts (`completed` increasing, `approved` decreasing).
- Manual bounded proof run:
  - `python scripts/start_nusyq.py auto_cycle --iterations=1 --max-pus=5 --sleep=1 --real-pus`
  - Observed delta in `data/unified_pu_queue.json`: `completed +5`, `approved -5`.

### Fixes applied in this continuation
- `scripts/start_autonomous_service.py`
  - Added explicit stale-metrics warning in `--status`:
    - compares `data/execution_metrics.json.updated_at` against latest trace timestamp.
    - prints warning when metrics are significantly behind, reducing false "stalled" interpretation.
  - Added robust ISO timestamp parsing with timezone normalization for status diagnostics.
- `docs/SESSION_2026-01-22_DOCKER_MCP_FIXES.md`
  - Replaced raw merge-marker literals with prefixed `[merge marker]` examples inside code block.
  - Prevents conflict scanners from reporting false-positive merge conflicts in documentation examples.
- `scripts/start_nusyq.py` + `src/diagnostics/unified_error_reporter.py`
  - Hardened `error_report --quick` behavior for operator clarity:
    - quick mode now defaults to hub-only unless `--repo` is explicitly provided.
    - quick ruff scan now uses bounded sampling/timeouts for predictable completion.
    - report now marks partial scans and emits explicit timeout warnings instead of silently returning misleading zero totals.
  - Validation command:
    - `python scripts/start_nusyq.py error_report --quick --force`
    - now completes and clearly reports partial status (`ruff timed out for nusyq-hub`) in both console and report artifacts.

## Continuation Update (2026-02-10, later)

### Autonomous loop hardening
- Patched quest-conversion scope in `src/automation/autonomous_loop.py` to stop per-cycle quest churn:
  - `_process_results()` now tracks `quest_candidate_ids` from tasks completed in the current cycle.
  - `_create_quests_from_pu_results()` now accepts optional `pu_ids` and only converts those IDs when provided.
  - Removed quest creation from `in_progress` PUs in the conversion pass; only `completed` PUs are converted.

### Validation
- Runtime proof with synthetic queue entries:
  - Added 2 approved test PUs.
  - Ran `python run_autonomous.py --cycles 1 --tasks 2 --refill-mode none`.
  - Observed bounded behavior in logs:
    - `PU statuses updated: 2`
    - `Quests generated: 2`
  - Confirms quest generation is now cycle-scoped instead of scanning/creating across historical completed PUs.

### Additional run orchestration fix
- `run_autonomous.py` audit refill helper (`_refill_queue_from_audit`) no longer initializes with `max_tasks_per_cycle=0`.
- Updated to `max_tasks_per_cycle=1` for operator clarity (audit-only path still uses `_run_audit()`).
- Validation:
  - `python run_autonomous.py --cycles 1 --tasks 2 --refill-mode audit+gaps`
  - log now shows audit helper with `Max tasks/cycle: 1` and main loop with requested task count.

### Logging signal quality fix
- Reduced startup log bloat from spine status descriptions:
  - `src/spine/spine_manager.py` now truncates both current-state summary and lifecycle-entry text in `SpineHealth.describe()`.
  - `scripts/start_nusyq.py` local spine log no longer duplicates `desc=%s` payload.
- Validation:
  - `initialize_spine(refresh=True).describe()` now returns compact output (~100 chars) instead of multi-KB payload.

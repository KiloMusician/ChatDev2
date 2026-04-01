# Spine Health Integration Plan

## Objective
Provide the rest of the NuSyQ ecosystem (NuSyQ Root and SimulatedVerse) with a machine-readable Spine health signal so they can react to regressions before running heavy tasks. The Spine health snapshot is now emitted in `NuSyQ-Hub/state/reports/spine_health_snapshot.json` every time `start_nusyq.py` or other entry points initialize the spine.

## Signal Format
- `repo_root` – canonical path to NuSyQ-Hub.
- `timestamp` – ISO UTC timestamp of the last snapshot.
- `status` – `GREEN` / `YELLOW` / `RED` indicating whether both `current_state.md` and the lifecycle catalog are available.
- `current_state_excerpt` – list of the first few non-empty lines from `state/reports/current_state.md`.
- `lifecycle_entries` – titles from `lifecycle_catalog_latest.json`.
- `signals` – simple counters (`current_state_lines`, `lifecycle_entries`) for simple guarding logic.

The JSON file is deliberately lightweight so other repos can `cat` or `json.load` it without importing the entire NuSyQ-Hub codebase.

## Cross-Repo Consumption Strategy

### 1. NuSyQ Root
1. Add a lightweight helper (`scripts/consume_spine_health.py`) that:
   - Locates the Hub via `NUSYQ_HUB_PATH` or `../NuSyQ-Hub`.
   - Reads `state/reports/spine_health_snapshot.json`.
   - Emits a brief status report or updates `state/reports/current_state.md` inside the root repo (mirroring hub status).
2. Schedule this helper as part of the Root’s bootstrap (`src/main.py` / `scripts/bootstrap_root.py`) so Root always has the latest spine health before running quantum or Orbit tasks.
3. Optionally wire the helper to update the Root’s orchestration scoreboard (e.g. append to `state/health/spine_health.log`), enabling dashboard traces and alerts.

### 2. SimulatedVerse
1. Extend `SimulatedVerse/scripts/start_simverse.py` (or equivalent) to:
   - Read `NuSyQ-Hub/state/reports/spine_health_snapshot.json` before starting.
   - Raise warnings or fallback modes if `status != "GREEN"`.
   - Pass the JSON contents into a logging/tracing event (for example, via `src/spine/simverse_bridge.py`).
2. Add a `quest` or `heartbeat` entry that records the Spine snapshot contents to `state/heartbeat.jsonl`, so the verse can replay which hub iteration it last observed.
3. Create a symlink or shared volume for `SimulatedVerse/state/feeds/nu_spine_health.json` that simply mirrors the Hub JSON. This allows other scripts to poll a stable file instead of referencing the Hub path directly.

### Monitoring & Alerting
- Run a daily job (e.g. `scripts/monitor_spine_health.py`) that registries both the Hub and the other repos to ensure the snapshot is being read and consumed.
- The job can compare timestamps to confirm no stale data and optionally push to the NuSyQ quest system by logging a `spine_health_check` entry in `src/Rosetta_Quest_System/quest_log.jsonl`.

## Next Actions
1. Add the helper script mentioned above (`scripts/consume_spine_health.py`) in each repo and reference this doc.
2. Update onboarding docs (e.g. `docs/QUICK_REFERENCE_VS_CODE_TASKS.md`) to mention the new `spine_health_snapshot.json` file and how to surface it in dashboards.
3. Gate automated pipelines so the next stage only runs if the latest snapshot exists and has `status == "GREEN"`; otherwise raise a warning in `state/reports/health_warning.log`.

Having a single JSON file means the Spine health signal can also be pushed to external orchestrators simply by copying the file, which keeps automation simple while still honoring the “spine as shared backbone” doctrine.

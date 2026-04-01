# Slice 1 Design: Process Discovery and Registry Sync

Date: 2026-03-20
Status: Draft for user review
Scope: SkyClaw process discovery, registry persistence, and process inventory sync

## Goal

Give the ecosystem a durable, queryable inventory of all visible host processes without disrupting the existing service mesh. SkyClaw should discover live host processes, classify each with an `is_ecosystem` flag, persist the current snapshot into the registry, and prune stale entries when processes disappear.

## Current State

The codebase already has:

- A function-based SQLite service registry in [`app/backend/service_registry.py`](/mnt/c/Users/keath/Dev-Mentor/app/backend/service_registry.py)
- A SkyClaw daemon in [`scripts/skyclaw_scanner.py`](/mnt/c/Users/keath/Dev-Mentor/scripts/skyclaw_scanner.py)
- Existing registry consumers in the API and game command layer that assume rows in `services` are routable network services with `host`, `port`, and `health_endpoint`

SkyClaw currently includes an ad hoc `scan_processes()` implementation, but it only emits discovery events and does not reconcile process state into SQLite.

## Constraints

- The existing `services` table and service mesh behavior must remain intact.
- Process discovery must not break service health, gateway routing, or current game commands that rely on `list_services()`.
- Multiple live processes can share the same name, so process identity cannot be keyed by `name`.
- Process scanning failure must degrade gracefully and must not stop the rest of a SkyClaw scan cycle.

## Chosen Approach

Add a sibling `processes` table to the existing registry instead of overloading the `services` table.

Why this approach:

- It avoids collisions for repeated process names like `Code`, `git`, or `bash`.
- It preserves the contract of `services` as routable endpoints.
- It gives later slices a stable query surface for host runtime visibility.

## Architecture

### 1. Process Discovery Module

Add [`core/process_discovery.py`](/mnt/c/Users/keath/Dev-Mentor/core/process_discovery.py) with these functions:

- `scan_processes() -> list[dict]`
- `is_ecosystem_process(name: str) -> bool`
- `sync_processes_to_registry(processes: list[dict]) -> dict`

`scan_processes()` returns normalized process rows with:

- `pid`
- `name`
- `start_time`
- `is_ecosystem`
- optional `metadata`

Discovery strategy:

- Use `psutil` when available
- Fall back to platform-native process listing commands when `psutil` is unavailable
- Normalize timestamps to stable text values before persistence

`is_ecosystem_process()` is heuristic and keyword-based for Slice 1. It is not authoritative and should remain easy to extend later from configuration.

### 2. Registry Extension

Extend [`app/backend/service_registry.py`](/mnt/c/Users/keath/Dev-Mentor/app/backend/service_registry.py) with a new `processes` table:

```sql
CREATE TABLE IF NOT EXISTS processes (
    pid            INTEGER PRIMARY KEY,
    name           TEXT NOT NULL,
    start_time     TEXT,
    last_seen      REAL,
    is_ecosystem   INTEGER NOT NULL DEFAULT 0,
    metadata       TEXT
);
```

Add additive helpers:

- `upsert_process(pid, name, start_time, is_ecosystem, metadata=None) -> None`
- `list_processes(only_ecosystem=False, stale_threshold_seconds=None) -> list[dict]`
- `prune_stale_processes(age_seconds=300, active_processes=None) -> int`
- `process_stats(stale_threshold_seconds=300) -> dict`

Keep the existing service helpers unchanged:

- `register()`
- `list_services()`
- `gateway_table()`
- `health_check_all()`

This slice does not mix processes into `list_services()` or `gateway_table()`.

### 3. SkyClaw Integration

[`scripts/skyclaw_scanner.py`](/mnt/c/Users/keath/Dev-Mentor/scripts/skyclaw_scanner.py) remains the scheduler.

Each scan cycle will:

1. run normal filesystem, colony, and crash scans
2. collect the current process snapshot through `core.process_discovery.scan_processes()`
3. sync that snapshot into the registry
4. publish a compact process-sync discovery event
5. continue even if process sync fails

The process sync summary should include counts such as:

- `seen`
- `ecosystem`
- `pruned`

SkyClaw should still write its summary file to `state/skyclaw_scan.json`.

## Identity and Pruning Semantics

The primary row identifier is `pid`, but PID reuse is a real edge case. Slice 1 handles this by treating a changed `start_time` for an existing PID as a replacement of the previous row.

Pruning should remove rows that were not seen during the current staleness window. The preferred implementation is:

- upsert every scanned process with a fresh `last_seen`
- prune rows whose `last_seen` is older than the configured threshold

Optional safety improvement:

- allow `prune_stale_processes()` to receive the active snapshot and avoid pruning rows just written in the same cycle

## Error Handling

- If `psutil` import fails, fall back to platform-native commands.
- If process listing fails entirely, return a degraded process-sync result and log the error.
- SkyClaw must continue the rest of the scan cycle even when process sync fails.
- Registry writes should be additive and isolated from the existing service mesh paths.

## Testing and Verification

### Unit-Level Checks

- `scan_processes()` returns normalized rows on the current host
- `is_ecosystem_process()` marks obvious ecosystem tools as expected
- `upsert_process()` stores rows correctly
- `prune_stale_processes()` removes stale rows only

### Integration Checks

- Run `python scripts/skyclaw_scanner.py --scan once`
- Confirm `state/service_registry.db` contains rows in `processes`
- Confirm `registry_stats()` continues to report service counts and now also reports process totals
- Start a visible process such as RimWorld and verify it appears after the next scan
- Stop that process and verify it is pruned after the configured stale interval

## Out of Scope for Slice 1

- Exposing process inventory in the game UI
- Merging processes into the service list UI
- Process control or restart behavior
- Cross-shell `start-system` orchestration
- Doctor command changes

## Follow-On Slices Enabled by This Work

- Slice 2: startup and doctor reliability can validate expected host processes against the registry
- Slice 3: the game can surface live ecosystem processes or a `/proc`-style view from the persisted inventory

## Implementation Notes

- Preserve backward compatibility for all existing service registry consumers.
- Keep `is_ecosystem` heuristic small and explicit for the first pass.
- Prefer simple function-based integration because the registry module is already function-based; do not introduce a new registry class in Slice 1.

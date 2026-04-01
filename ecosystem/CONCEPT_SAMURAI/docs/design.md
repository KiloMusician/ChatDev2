# keeper.ps1 — Design Notes

## Core Philosophy

This tool is a **system state coordinator**, not a performance booster.

The goal is:
- Remove interference before gaming (dev workloads, idle containers, WSL VMs)
- Restore the development environment cleanly after gaming
- Diagnose audio and performance issues with hard evidence
- Never make changes you can't undo

The tool should behave like a **thermostat**, not CCTV — keep current state, record only meaningful changes, never log everything forever.

---

## Architecture

### Thin-router + `lib/` modules

`keeper.ps1` is now a thin entrypoint. It owns:

- parameter parsing
- path/bootstrap state
- module loading order
- command routing

All functional logic lives under `lib/`:

- **`lib/config.ps1`** — JSON loading, defaults + machine.local merge, shared object helpers
- **`lib/state.ps1`** — `current.json`, `rollback.json`, ring buffer, session summaries
- **`lib/actions.ps1`** — process stop, service control, power plan, Game Mode, launcher start
- **`lib/health.ps1`** — health snapshot, WSL/Docker detection, doctor report, audio triage, mode recommendation
- **`lib/automation.ps1`** — idle-aware coding vs balanced automation and scheduled-task install/remove/status
- **`lib/profiles.ps1`** — mode apply + restore orchestration; per-profile CPU priority rules and GPU preference engine
- **`lib/watch.ps1`** — watch loop, rolling state updates, and anomaly auto-capture
- **`lib/listener.ps1`** — Steam library watcher, local appmanifest parser, active-game metadata, and per-game mode rules
- **`lib/updates.ps1`** — winget update detection and opt-in package update application
- **`lib/export.ps1`** — JSON/HTML incident export and pruning
- **`lib/maintenance.ps1`** — disk analysis (`think`), safe cleanup pass (`maintain`): temp/Docker/WSL/npm/downloads; safety-gated by mode, CPU, and disk-busy thresholds
- **`lib/brain.ps1`** — deterministic pressure scoring (`score`), rules-based advisor (`advisor`), Ollama log analysis (`analyze`), and advisory action applier (`optimize`)

UI and integration surfaces intentionally sit above the core:

- **`tools/keeper-bridge.ps1`** — machine-readable JSON bridge for UI shells and future local integrations
- **`godot/keeper-shell`** — offline-first desktop shell with tray-capable Windows UI
- **`index.html` / `server.py`** — optional fallback surface, not the primary app

The public interface did not change. Existing commands, flags, config files, state file locations, and `.cmd` launchers remain valid.

### Profile system

Profiles are defined in `config/profiles.json`. Each profile specifies:

```json
{
  "shutdownWsl": true,
  "stopProcesses": ["Code", "Docker*", "com.docker.*", "dockerd*"],
  "stopServices": ["WSearch"],
  "startServices": [],
  "startLaunchers": [],
  "setPowerPlan": "high_performance",
  "setGameMode": true,
  "notes": ["Human-readable summary of what this mode does."]
}
```

Per-machine overrides go in `config/machine.local.json` (not committed). The settings system deep-merges `defaults.json` → `machine.local.json`.

`balanced` is intentionally separate from `coding`. `coding` means "prefer developer stability"; `balanced` means "leave current apps alone and return to neutral system posture."

`auto` is intentionally separate from `recommend`. `recommend` may still suggest `gaming`; `auto` only manages the safe subset of mode changes (`coding` vs `balanced`) and defers when a game is active.

Steam integration is intentionally local-first:

- `libraryfolders.vdf` discovers Steam libraries
- `appmanifest_*.acf` files provide AppID, title, and install directory
- no Steam Web API key, client plugin, or external dependency is required for mode switching
- per-game rules live in `settings.listener.gameProfiles` inside `machine.local.json`

UI integration is also intentionally local-first:

- the desktop shell talks to the local bridge, not directly to individual modules
- the bridge keeps `keeper.ps1` human-friendly while exposing stable JSON for other local apps
- this gives future projects such as Dev-Mentor, SimulatedVerse, or NuSyQ-Hub a clean local integration seam

---

## State Model

### `state/current.json`

Overwritten in place on every `status`, `watch` sample, and mode change. Contains:

```json
{
  "mode": "gaming",
  "started_at": "2026-03-29T18:42:10Z",
  "status": "ready",
  "power_plan_raw": "High performance",
  "wsl_active": false,
  "docker_active": false,
  "top_offenders": ["msedge", "python"]
}
```

### `state/ringbuffer.json`

Rolling array of health samples, capped at 180 by default. Oldest are dropped automatically. Never grows unbounded.

### `state/rollback.json`

Written immediately before any mode change. Contains:

- Prior power plan GUID
- Prior Game Mode state
- List of processes that were stopped (so they can be noted for restore)
- List of services that were stopped (restarted by `mode restore`)
- Prior mode name

Used by `mode restore` to reverse service changes and power plan.

### `sessions/`

One compact JSON summary per mode switch. Kept up to 30 (configurable). Contains: session ID, mode, duration, before/after CPU%, WSL/Docker state, top offenders, action summary. Never contains per-sample streams.

### `incidents/`

Created by `export` and by anomaly auto-capture in `watch`. HTML and JSON bundles can contain current state, rollback state, recent sessions, doctor data, and trigger reasons. Auto-pruned after 14 days by `prune`.

---

## Dependency Order for Mode Application

```
1. Bootstrap (paths, workspace dirs, privilege check)
2. Load config (defaults + machine.local merge)
3. Snapshot current health state
4. Record rollback state
5. Stop processes (pattern matching, wildcard-safe)
6. Shutdown WSL (if profile requires, after Docker-backed processes are stopped)
7. Stop services (safe, logs if service not found)
8. Set power plan
9. Set Game Mode
10. Start services (if profile requires)
11. Start launchers (if profile requires)
12. Re-snapshot health state
13. Append ring buffer sample
14. Save rollback state to disk
15. Write session summary
16. Update current state to "ready"
```

This order avoids half-applied states. If the script is interrupted, rollback state was already saved.

---

## What is Safe to Automate

Included in default profiles:
- `wsl --shutdown` — clean, reversible
- Stop VS Code, Docker Desktop — restartable
- Stop Node/Python/Jupyter — if explicitly listed
- Switch Balanced ↔ High Performance power plan — fully reversible
- Stop and restart Windows Search (WSearch) — service, not destructive
- Enable/disable Game Mode via registry key — single DWORD, easily reversed

Deliberately excluded from default profiles:
- Disabling drivers
- Modifying GPU mode
- Editing large registry key sets
- Uninstalling Nahimic or Realtek
- Changing service startup types permanently
- Anything requiring a reboot to apply/reverse

Those belong in `docs/safety.md` as guided manual steps, not automated actions.

---

## Diagnostics Design

`doctor` collects a health snapshot and applies rule-based checks:

| Check | Risk Points | Reason |
|-------|-------------|--------|
| Nahimic service/process detected | +2 | Known MSI audio conflict |
| GPU mode is `MSHybrid` | +1 | dGPU-only mode often lowers gaming DPC risk on supported MSI models |
| Docker active | +1 | Background GPU/CPU/RAM |
| WSL active | +1 | VM overhead |
| CPU > 60% | +1 | Contention risk |
| Audio-risk processes active | +1 | Code, node, chrome, etc. |

Risk levels: `low` (0–1), `medium` (2–3), `high` (4+)

Nahimic gets double weight because it is specifically known to cause audio stutter on MSI laptops through conflicts with the Realtek audio stack.

When `doctor -AudioTriage` runs without `-LatencyMonReportPath`, keeper also looks for the newest `LatencyMon*.txt` report on Desktop/Documents and attaches it automatically if one exists.

## Recommendation + Update Design

`recommend` is deliberately conservative:

- If a Steam game is active and dev workloads are also active, prefer `balanced`
- If only game workloads are active, recommend `gaming`
- If dev workloads are active, recommend `coding`
- If neither side is active, recommend `balanced`

When local Steam metadata is available, recommendation and doctor surfaces carry friendly game names and AppIDs instead of only raw process names.

This is meant to avoid surprising shutdowns of Docker, WSL, or editors during active project work.

`updates` uses `winget` for package updates because it is present on the target machine and has a clean command surface for installed applications. Windows Update and driver automation are intentionally kept separate for now.

`auto` uses a stricter policy than `recommend`:

- If a game is running, do nothing and defer to the Steam listener or a manual gaming choice
- If the machine has been idle past the configured threshold, switch to `balanced`
- If dev workloads are active and the machine is not idle, switch to `coding`
- Otherwise keep or move to `balanced`

This keeps scheduled automation safe: it never auto-enters gaming mode and never kills project tools in the background.

`updates -Apply` is also guarded:

- All available upgrades are listed
- Policy-approved upgrades are separated from blocked upgrades
- Deny lists block sensitive tools by default, including Docker Desktop and Visual Studio Code family packages
- Allow lists override deny lists when you explicitly trust a package
- Approved updates are applied one package at a time by exact ID, not via an unrestricted `--all`

---

## Storage Budget

Default retention policy (configurable in `defaults.json`):

| Store | Limit | Behavior |
|-------|-------|----------|
| Ring buffer | 180 samples | Oldest dropped automatically |
| Session summaries | 30 files | Oldest deleted by `prune` |
| Incidents | 14 days | Deleted by `prune` |
| current.json | 1 file | Overwritten in place |
| rollback.json | 1 file | Overwritten in place |

Total footprint is typically well under 1 MB.

---

## Brain Layer

The brain layer is a three-tier pipeline layered above the existing modules:

| Tier | Command | Description |
|------|---------|-------------|
| Hot path | `score` | Deterministic weighted pressure index (0-100). Disk 30%, CPU 25%, RAM 25%, background contention 20%. Persists to `state/performance_score.json`. No LLM, no network. |
| Hot path | `advisor` | Rules-based priority-ordered recommendation. Outputs: `recommended`, `why`, `confidence`, `safe_to_apply`. Persists to `state/advisor_last.json`. No LLM, no network. |
| Hot path | `optimize` | Applies the advisor recommendation if `safe_to_apply` is true (or `-Force`). Dispatches to `Invoke-DockerPrune`, `Invoke-CleanTemp`, or `Invoke-DemoteDevProcesses` as appropriate. |
| Warm path | `analyze` | Ollama-backed log analysis. Reads `state/action_log.jsonl` and the latest score. Returns structured JSON from the model. 30s timeout, graceful fallback if Ollama is unavailable. |

Priority order for advisor: disk >= 90% > gaming + contention >= 38% > CPU/RAM pressure > disk >= 80% > contention >= 50%.

`safe_to_apply` is false when: the overall score status is below "warning", the current mode is `heavy-gaming`, or the recommended action is "none".

The bridge `snapshot` command includes `brain.score` and `brain.advisor` from the last persisted state so UIs can surface them without re-running the scoring pipeline.

---

## Future Extensions

- Richer Godot shell and packaged Windows executable
- Non-Steam game detection
- Richer anomaly rules and cooldown controls
- Direct MSI Center integration beyond registry-based GPU mode detection
- `optimize -Schedule`: run optimizer on a timer via Task Scheduler (same guard policy as `auto`)

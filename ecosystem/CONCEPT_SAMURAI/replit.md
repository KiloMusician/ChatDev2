# keeper.ps1 — Windows Mode Switcher

## Project Overview

A lightweight, safe Windows PowerShell system orchestrator that switches between gaming and coding modes, reduces background interference, and monitors system health in real time.

**Note:** This is a Windows-only CLI tool. It cannot run on Linux/Replit directly. A static web dashboard (`index.html`) is provided to document the project and display its capabilities.

## Architecture

- **keeper.ps1** — Single-entrypoint PowerShell script (Windows only, 1200+ lines)
- **config/defaults.json** — Global defaults (power plans, watch interval, ring buffer, retention, doctor thresholds, launchers)
- **config/profiles.json** — Mode profiles: gaming, coding, audio-safe, quiet, diagnose, restore
- **config/machine.local.example.json** — Per-machine override template (copy to `machine.local.json`)
- **docs/design.md** — Architecture decisions, state model, dependency order, future extensions
- **docs/safety.md** — Safety model, what the tool will never do automatically, rollback behavior, LatencyMon guide
- **index.html** — Web dashboard (documentation/overview, served by Python)
- **server.py** — Python HTTP server for the dashboard (port 5000)

## Profiles

| Mode | Summary |
|------|---------|
| `gaming` | Shuts WSL/Docker/VS Code, high-performance power, Game Mode on |
| `coding` | Balanced power, Game Mode off, restores Windows Search |
| `audio-safe` | Kills all audio-risk processes + browsers, shuts WSL/Docker, high-performance |
| `quiet` | Stops all dev workloads + browsers, balanced power, no Game Mode |
| `diagnose` | Balanced baseline for stutter testing; run doctor after |
| `restore` | Rolls back last reversible mode change |

## Replit Setup

- **Language:** Python 3.11 (for serving the dashboard)
- **Workflow:** "Start application" runs `python3 server.py` on port 5000
- **Deployment:** Autoscale, run command: `python3 server.py`

## Key Commands (Windows only)

```powershell
.\keeper.ps1 status
.\keeper.ps1 mode gaming
.\keeper.ps1 mode coding
.\keeper.ps1 mode audio-safe       # new: kill audio-risk processes
.\keeper.ps1 mode quiet             # new: stop all workloads
.\keeper.ps1 mode restore
.\keeper.ps1 watch
.\keeper.ps1 doctor
.\keeper.ps1 export
.\keeper.ps1 export -Html           # new: HTML report
.\keeper.ps1 prune
```

## Flags

| Flag | Purpose |
|------|---------|
| `-WhatIf` | Dry-run preview |
| `-DebugMode` | Full structured action output |
| `-Quiet` | Suppress INFO logs |
| `-Html` | HTML report (with `export`) |
| `-DurationSec N` | Timed `watch` mode |

## State Files (auto-created on Windows)

- `state/current.json` — Active state snapshot (overwritten in place)
- `state/ringbuffer.json` — 180-sample rolling buffer
- `state/rollback.json` — Last reversible changes
- `sessions/` — Session summaries (max 30)
- `incidents/` — Export bundles (14-day retention)

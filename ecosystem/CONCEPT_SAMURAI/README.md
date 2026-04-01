# keeper.ps1

> Lightweight, safe system orchestrator for Windows laptops that switches between gaming and coding modes, reduces background interference, and monitors system health in real time. Uses profile-based actions, rollback, and compact state tracking — no bloat, no risky tweaks, just predictable performance.

---

## What it does

- Switches between gaming, coding, balanced, quiet, diagnose, audio-safe, and restore workflows with reversible state tracking
- Captures compact health snapshots for CPU, RAM, top processes, WSL, Docker, power plan, and current mode
- Watches for live pressure/anomalies and can export incident bundles as JSON or HTML
- Detects Steam games from local library metadata and can auto-apply per-game mode rules
- Produces machine-readable JSON through `tools/keeper-bridge.ps1` for local shells and desktop integrations
- Recommends or safely automates mode changes for coding vs balanced workloads
- Surfaces audio-triage guidance, Nahimic detection, MSI GPU mode hints, and LatencyMon summaries
- Provides Windows launcher wrappers and shortcut installers for common actions


## What it does NOT do

- It does not overclock hardware, flash firmware, or apply unsafe registry tweaks
- It does not require a cloud backend, Steam login, or always-on internet connectivity
- It does not persist full telemetry/history; it keeps compact state and short session summaries instead
- It does not silently force destructive changes without recording rollback information first
- It does not replace proper driver troubleshooting when diagnostics point at GPU, network, storage, or audio drivers



## Requirements

- Windows with PowerShell 5.1 or newer; PowerShell 7 is recommended for local development and testing
- Optional: `winget` for package update reporting and apply flows
- Optional: Steam installed locally if you want `listen` to auto-detect game launches
- Optional: Godot if you want to run the desktop shell instead of the local HTML fallback
- Optional: Pester for local test runs; CI installs and runs it on Windows automatically



## Quick Start

```powershell
# Launch the offline-first desktop shell (prefers Godot, falls back to the local dashboard)
.\tools\Launch-KeeperShell.ps1

# Return machine-readable JSON for desktop/app integrations
.\tools\keeper-bridge.ps1 snapshot

# See current system state
.\keeper.ps1 status

# Preview gaming mode changes without applying them
.\keeper.ps1 mode gaming -WhatIf

# Switch to gaming mode
.\keeper.ps1 mode gaming

# Switch back to coding mode
.\keeper.ps1 mode coding

# Switch to neutral daily mode
.\keeper.ps1 mode balanced

# Kill all audio-risk processes (for stutter troubleshooting)
.\keeper.ps1 mode audio-safe

# Maximum quiet — all dev workloads stopped, no Game Mode
.\keeper.ps1 mode quiet

# Watch live health (Ctrl+C to stop)
.\keeper.ps1 watch

# Watch for 60 seconds then exit
.\keeper.ps1 watch -DurationSec 60

# Watch Steam libraries for a short test run
.\keeper.ps1 listen -DurationSec 10

# Use local Steam manifests + per-game rules (configured in machine.local.json)
.\keeper.ps1 listen

# Run system health diagnostics
.\keeper.ps1 doctor

# Ask keeper which mode fits the current workload
.\keeper.ps1 recommend

# Apply the recommended mode
.\keeper.ps1 recommend -Apply

# Evaluate safe automation logic for coding vs balanced
.\keeper.ps1 auto

# Apply safe automation logic now
.\keeper.ps1 auto -Apply

# Show scheduled automation status
.\keeper.ps1 schedule

# Preview scheduled automation install/update
.\keeper.ps1 schedule -Apply -WhatIf

# Check available package updates
.\keeper.ps1 updates

# Apply package updates through winget
.\keeper.ps1 updates -Apply

# Export a focused audio triage bundle
.\keeper.ps1 doctor -Export -AudioTriage -Html

# Export a JSON report
.\keeper.ps1 export

# Export an HTML report (saves to incidents/)
.\keeper.ps1 export -Html

# Roll back last mode change
.\keeper.ps1 mode restore

# Clean up old session/incident files
.\keeper.ps1 prune

# Report Docker VHD size before elevated compaction
.\tools\compact-docker-vhd.ps1 -ReportOnly

# Launch elevated Docker VHD compaction helper
.\tools\keeper-compact-vhd-admin.cmd
```

## CI
--

This repository includes a GitHub Actions workflow that runs the Pester test suite on Windows runners (`.github/workflows/pester.yml`). The workflow installs Pester and runs `Invoke-Pester -Path tests -Output Detailed` on pushes and pull requests to `main`.

If you'd rather run CI locally, execute the same command in PowerShell (PowerShell 7+ recommended):

```powershell
pwsh -NoProfile -Command "Install-Module -Name Pester -Force -Scope CurrentUser -SkipPublisherCheck -AllowClobber; Import-Module Pester; Invoke-Pester -Path tests -Output Detailed"
```

## Agent Interfaces

If you want an external coding or orchestration agent to interact with Keeper efficiently, use the structured surfaces instead of scraping terminal output:

- [`tools/keeper-mcp.ps1`](tools/keeper-mcp.ps1) exposes Keeper as an MCP stdio server
- [`tools/keeper-bridge.ps1`](tools/keeper-bridge.ps1) exposes compact JSON commands directly
- [`agent_manifest.json`](agent_manifest.json) describes the agent-facing role, capabilities, and preferred startup flow
- [`GORDON.md`](GORDON.md) is the low-token cockpit guide for Docker Gordon or any comparable agent

The workspace already includes a Keeper MCP server entry in [`.vscode/mcp.json`](.vscode/mcp.json) so agents that honor workspace MCP config can mount it directly.

## Ecosystem Interaction Matrix

`CONCEPT` is the machine-governance layer for the wider local stack. It does not replace the other repos; it stabilizes them.

| From | To | What Flows |
|------|----|------------|
| **CONCEPT** | **Dev-Mentor / TerminalDepths** | Keeper MCP preflight, pressure scoring, advisor, maintenance signals |
| **Dev-Mentor / TerminalDepths** | **CONCEPT** | Agent/operator calls into Keeper before heavy workflows |
| **CONCEPT** | **SimulatedVerse** | Safe-start guidance for Docker, ChatDev, and local simulation surfaces |
| **SimulatedVerse** | **CONCEPT** | Runtime pressure feedback via actual service load and recovery needs |
| **CONCEPT** | **NuSyQ-Hub** | Machine state for healing/orchestration decisions |
| **NuSyQ-Hub** | **CONCEPT** | Higher-order diagnosis, healing, and cross-repo routing |
| **NuSyQ-Hub** | **Nogic** | Real architecture visualization bridge and VS Code bridge |
| **NuSyQ-Hub** | **GitNexus** | Live ecosystem git matrix surface at `/api/gitnexus/*` |

Practical meaning:
- Run Keeper first when starting `Dev-Mentor`, `SimulatedVerse`, or other heavy local services.
- Treat `NuSyQ-Hub` as the orchestration brain above Keeper, not a replacement for it.
- Treat `Nogic` as a live sibling architecture surface.
- Treat `GitNexus` as the live cross-repo git/status matrix for the ecosystem.

## Windows launchers

The repo also includes simple Windows wrappers in `tools/` so you can launch common actions from Explorer, desktop shortcuts, or the Start Menu:

- `tools\keeper-ui.cmd`
- `tools\keeper-web.cmd`
- `tools\keeper-gaming.cmd`
- `tools\keeper-gaming-admin.cmd`
- `tools\keeper-coding.cmd`
- `tools\keeper-balanced.cmd`
- `tools\keeper-auto.cmd`
- `tools\keeper-auto-admin.cmd`
- `tools\keeper-schedule.cmd`
- `tools\keeper-schedule-admin.cmd`
- `tools\keeper-audio-safe.cmd`
- `tools\keeper-audio-safe-admin.cmd`
- `tools\keeper-quiet.cmd`
- `tools\keeper-restore.cmd`
- `tools\keeper-status.cmd`
- `tools\keeper-doctor.cmd`
- `tools\keeper-recommend.cmd`
- `tools\keeper-updates.cmd`
- `tools\keeper-updates-admin.cmd`
- `tools\keeper-updates-apply-admin.cmd`
- `tools\keeper-doctor-audio.cmd`
- `tools\keeper-diagnose.cmd`
- `tools\keeper-export.cmd`
- `tools\keeper-advisor.cmd`
- `tools\keeper-analyze.cmd`
- `tools\keeper-maintain.cmd`
- `tools\keeper-optimize.cmd`
- `tools\keeper-prune.cmd`
- `tools\keeper-score.cmd`
- `tools\keeper-think.cmd`
- `tools\keeper-watch.cmd`
- `tools\keeper-listen.cmd`
- `tools\keeper-listen-admin.cmd`
- `tools\keeper-compact-vhd-admin.cmd`

To generate desktop and Start Menu shortcuts for those wrappers, run:

```powershell
.\tools\install-shortcuts.ps1
```

## Desktop shell

Keeper now has a local desktop shell scaffold in `godot/keeper-shell`.

- Primary surface: Godot desktop app
- System tray support: via Godot `StatusIndicator`
- Integration path: local JSON bridge at `tools\keeper-bridge.ps1`
- Offline behavior: fully local; no internet required
- Fallback: `index.html` can still be opened locally if Godot is unavailable

The PowerShell core stays authoritative. The UI talks to the bridge instead of parsing terminal output.

---

## Modes

| Mode | What it does |
|------|-------------|
| `gaming` | Shuts WSL, stops VS Code & Docker, stops Windows Search, sets High Performance power plan, enables Game Mode |
| `coding` | Balanced power plan, disables Game Mode, restores Windows Search |
| `balanced` | Neutral everyday mode: keeps current apps running, balanced power plan, disables Game Mode, restores Windows Search |
| `audio-safe` | Kills all audio-risk processes (browsers, dev tools, VS Code, Docker, WSL), sets High Performance — use when experiencing audio stutter |
| `quiet` | Stops all dev workloads and browsers, shuts WSL, balanced power, no Game Mode — use for recording or troubleshooting |
| `diagnose` | Balanced baseline with no extra noise — run `doctor` after to capture clean diagnostic state |
| `restore` | Rolls back the last reversible mode change using `state/rollback.json` |

---

## Configuration

### `config/defaults.json`
Global defaults: power plan mappings, watch sample interval, ring buffer size, recommendation heuristics, automation schedule settings, Steam listener settings, update settings, anomaly thresholds, retention policy, doctor thresholds, and launcher commands.

### `config/profiles.json`
Defines the actions for each mode. Edit this to customize which processes are stopped, which services are toggled, and which power plan to use.

### `config/machine.local.json` (not committed)
Per-machine overrides. Copy `config/machine.local.example.json` to `config/machine.local.json` and add your own process names, launcher paths, or profile tweaks. This file is `.gitignore`d so it never gets committed.

Keeper now supports local Steam per-game rules through `settings.listener.gameProfiles`. Rules can match on `appId`, `namePattern`, `processPattern`, `pathPattern`, or `installDirPattern`, then choose a different `onGameStart` / `onGameExit` mode for that game.

---

## State & Storage

```
state/
  current.json      # Overwritten in place — current mode and health snapshot
  ringbuffer.json   # Rolling 180-sample buffer (overwrites oldest)
  rollback.json     # Last reversible changes (power plan, stopped services, etc.)
sessions/           # Tiny per-session summaries (kept up to 30, then pruned)
incidents/          # Export bundles (JSON or HTML) — created manually or on anomaly
```

**Storage philosophy:** This tool behaves like a thermostat, not CCTV. It keeps current state and only records meaningful changes. Run `prune` periodically or add it to a scheduled task.

---

## Safety Model

Every mode change follows this order:
1. Snapshot current state (before health check)
2. Save rollback state (power plan, stopped services/processes)
3. Apply changes in dependency order (processes → WSL → services → power → game mode)
4. Re-check health state after
5. Save compact session summary
6. Rollback state available immediately via `mode restore`

No change is applied without first recording what it was. No change permanently destroys anything. See [`docs/safety.md`](docs/safety.md) for the full safety model.

---

## Doctor Report

`.\keeper.ps1 doctor` checks for:

- **Nahimic** services or processes (common MSI audio stutter source)
- MSI GPU mode detection when the registry exposes `MSHybridEnabled`
- WSL and Docker activity
- High background CPU usage
- Known audio-risk processes (browsers, dev tools, Python, Node, Docker, Jupyter, etc.)
- Non-elevated shell (warns when service control is unavailable)

`.\keeper.ps1 recommend` adds:

- A conservative mode recommendation based on active Steam game processes, dev workloads, WSL/Docker activity, and current CPU pressure
- A mixed-workload guardrail that prefers `balanced` over killing a live coding session by accident
- Friendly active game metadata from local Steam `appmanifest_*.acf` files when available

`.\keeper.ps1 auto` adds:

- Safe automation that only manages `coding` vs `balanced`
- Idle-aware downshift to `balanced`
- Active dev workload upshift to `coding`
- Defers entirely when a game is running so the Steam listener or manual gaming mode stays in control

`.\keeper.ps1 schedule` adds:

- Status, install/update, and removal of the Keeper automation scheduled task
- A repeating task that runs `auto -Apply -Quiet` on a configured interval and at logon

`.\keeper.ps1 updates` adds:

- Available `winget` package upgrades
- `winget` version and update capability
- Whether `PSWindowsUpdate` is installed for future Windows Update automation
- Guarded allow/deny policy
- Optional `-Apply` support for applying only policy-approved `winget` package upgrades

Risk levels: `low` / `medium` / `high`

`.\keeper.ps1 doctor -Export -AudioTriage -Html` adds:

- Nahimic service details and running Nahimic processes
- Audio-driver inventory for Realtek, Nahimic, Intel Smart Sound, and related devices
- Installed audio packages from the Windows uninstall registry
- An explicit recommendation about whether to disable Nahimic first or move on to reinstall/removal
- Optional LatencyMon report attachment via `-LatencyMonReportPath`
- Automatic LatencyMon report discovery from Desktop/Documents when you do not provide a path

`.\keeper.ps1 listen` adds:

- Local Steam library discovery from `libraryfolders.vdf`
- Local game metadata discovery from `appmanifest_*.acf`
- Friendly game names and Steam AppIDs in listener state, doctor output, and exports
- Per-game profile overrides without any external Steam dependency or login

`.\tools\keeper-bridge.ps1` adds:

- A machine-readable local contract for desktop shells and future local projects
- JSON responses for `snapshot`, `status`, `doctor`, `recommend`, `auto`, `games`, `mode`, and `export`
- An offline-first integration layer that does not depend on web services or Steam authentication

---

## Flags

| Flag | Description |
|------|-------------|
| `-WhatIf` | Preview changes without applying them |
| `-DebugMode` | Show full structured action results |
| `-Quiet` | Suppress INFO log lines |
| `-Html` | Output HTML report when used with `export` |
| `-Export` | When used with `doctor`, write an incident bundle instead of only printing to the console |
| `-Apply` | Apply the recommended mode, install/update automation scheduling, or apply policy-approved package updates, depending on the command |
| `-Remove` | Remove the installed automation scheduled task when used with `schedule` |
| `-AudioTriage` | Include focused audio/Nahimic/driver triage data in `doctor` or `export` |
| `-Silent` | Request silent package upgrades when used with `updates -Apply` |
| `-LatencyMonReportPath PATH` | Attach a LatencyMon text or report file path to the audio triage bundle |
| `-DurationSec N` | Stop `watch` after N seconds |

---

## Design

See [`docs/design.md`](docs/design.md) for architecture decisions, the state model, and the safety principles this tool is built around.
The current implementation uses a thin [`keeper.ps1`](keeper.ps1) router that dot-sources focused modules from [`lib/`](lib).

---

## License

MIT

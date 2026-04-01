# keeper.ps1 — lib/ Split + Full Sprint Design

**Date:** 2026-03-29
**Status:** Approved
**Scope:** Full sprint — UX fixes + lib/ module split + features A, B, E, F

---

## Overview

Split the 1,885-line `keeper.ps1` monolith into focused `lib/` modules while delivering four new features and fixing all launcher UX gaps. The public interface (CLI flags, config files, state file locations, `.cmd` launchers) is frozen — no breaking changes.

---

## Architecture

### Module Layout

```
keeper.ps1              ← thin router (~200 lines), dot-sources lib/ on demand
lib/
  config.ps1            ← settings load, defaults + machine.local merge
  state.ps1             ← current.json, rollback.json, ringbuffer.json I/O
  actions.ps1           ← all side-effectful primitives
  health.ps1            ← cheap health snapshot (CPU, RAM, WSL, Docker, top procs)
  doctor.ps1            ← expensive diagnostics (Nahimic, audio risk, LatencyMon, GPU)
  profiles.ps1          ← Invoke-ModeProfile, Invoke-RestoreMode
  watch.ps1             ← watch loop + anomaly auto-capture (Feature B)
  listener.ps1          ← Steam game-watcher daemon (Feature A)
  export.ps1            ← JSON/HTML incident bundle generation
```

### Dependency Graph

```
keeper.ps1 (router)
│
├── lib/config.ps1       ← no deps; loaded first
├── lib/state.ps1        ← deps: config.ps1
├── lib/actions.ps1      ← deps: config.ps1, state.ps1
├── lib/health.ps1       ← deps: config.ps1, state.ps1
├── lib/doctor.ps1       ← deps: health.ps1, config.ps1
├── lib/profiles.ps1     ← deps: actions.ps1, health.ps1, state.ps1, config.ps1
├── lib/watch.ps1        ← deps: health.ps1, state.ps1, export.ps1 (anomaly only)
├── lib/listener.ps1     ← deps: profiles.ps1, config.ps1
└── lib/export.ps1       ← deps: health.ps1, state.ps1, doctor.ps1
```

### Module Responsibilities

| Module | Responsibility | Max Lines |
|--------|---------------|-----------|
| `config.ps1` | Load `defaults.json` + `machine.local.json`, deep-merge, expose `$Settings`/`$Profiles` | 120 |
| `state.ps1` | Read/write `current.json`, `rollback.json`, `ringbuffer.json` | 100 |
| `actions.ps1` | Stop/start process, service, power plan, game mode, WSL, launcher — all side-effectful primitives | 300 |
| `health.ps1` | Cheap health snapshot: CPU%, RAM, WSL active, Docker active, top processes, current mode | 120 |
| `doctor.ps1` | Expensive diagnostics: Nahimic, audio risk, LatencyMon parse (E), GPU mode (F) | 300 |
| `profiles.ps1` | Mode apply + restore orchestration in dependency order | 200 |
| `watch.ps1` | Watch loop with configurable interval + anomaly auto-capture (B) | 150 |
| `listener.ps1` | Steam library discovery + process watcher daemon (A) | 180 |
| `export.ps1` | JSON + HTML incident bundle generation | 350 |
| `keeper.ps1` | Param parsing, dot-source, command router | 200 |

---

## Feature Designs

### Feature A — Steam Game-Watcher (`listener.ps1`)

**New command:** `.\keeper.ps1 listen`

**Behavior:**
1. Parse `libraryfolders.vdf` from the Steam config directory to discover all Steam library root paths (handles multiple drives/libraries)
2. Poll running processes every `listener.pollIntervalSec` seconds (default: 3)
3. When any process whose `.exe` path is under a Steam library folder is detected for the first time → apply `gaming` profile
4. Write detected game info to `state/listener.json` (PID, exe name, path, detected_at)
5. When that PID exits → apply `restore` (rolls back to pre-game state), delete `state/listener.json`
6. Write a session summary as normal

**Config additions to `defaults.json`:**
```json
"listener": {
  "pollIntervalSec": 3,
  "steamVdfPath": null,
  "onGameStart": "gaming",
  "onGameExit": "restore"
}
```

`steamVdfPath: null` → auto-detect from `$env:ProgramFiles(x86)\Steam\config\libraryfolders.vdf`. Override in `machine.local.json` for non-standard installs.

**Edge cases:**
- Multiple Steam libraries on different drives: all paths checked
- Game already running when `listen` starts: detected on first poll, applied immediately
- Keeper already in `gaming` mode: skip re-apply, still track PID for exit detection
- Multiple game processes: track the first detected; subsequent launches ignored until first exits
- Ctrl+C: clean exit, no orphaned `listener.json`

**New `.cmd` launcher:** `tools/keeper-listen.cmd`
**New admin launcher:** `tools/keeper-listen-admin.cmd`
**New shortcut entry:** `Keeper Listen` in `install-shortcuts.ps1`

---

### Feature B — Anomaly Auto-Capture (`watch.ps1`)

**Enhanced watch loop:** After each health sample, applies lightweight rules:

| Rule | Default threshold |
|------|------------------|
| CPU% above threshold for N consecutive samples | `anomaly.cpuSpikePercent` = 80, `anomaly.spikeSustainSamples` = 3 |
| Nahimic process newly detected mid-session | any detection after watch started |
| Audio-risk process count increases by N | `anomaly.audioRiskNewProcesses` = 2 |

**On trigger:**
- Write JSON incident to `incidents/anomaly-<timestamp>.json` (same schema as export bundles)
- Print one-line notice below live display: `[ANOMALY] Captured → incidents/anomaly-<timestamp>.json`
- Do NOT interrupt the watch loop or change mode

**Config additions:**
```json
"anomaly": {
  "enabled": true,
  "cpuSpikePercent": 80,
  "spikeSustainSamples": 3,
  "captureOnNahimicDetected": true,
  "audioRiskNewProcesses": 2
}
```

---

### Feature E — LatencyMon Auto-Parse (`doctor.ps1`)

**Enhanced `-LatencyMonReportPath` behavior:**

1. If no path given: auto-scan `$env:USERPROFILE\Desktop` and `$env:USERPROFILE\Documents` for `LatencyMon*.txt` (newest first). Skip silently if none found.
2. Parse the text report: extract driver name + highest ISR/DPC execution time per driver
3. Map known drivers to human causes:

| Driver | Cause |
|--------|-------|
| `nvlddmkm.sys` | NVIDIA display driver — update via GeForce Experience |
| `ndis.sys` | Network adapter driver — update in Device Manager |
| `HDAudBus.sys` | Audio driver itself — check Realtek/Nahimic stack |
| `ACPI.sys` | Power management / BIOS firmware |
| `dxgkrnl.sys` | DirectX GPU scheduler |
| `storahci.sys` | Storage controller |
| `tcpip.sys` | TCP/IP stack — disable Wi-Fi adapter during gaming |

4. Surface top-3 offenders with times + fix recommendation in `doctor` output and HTML export
5. Add `latencymon_auto_discovered: true` flag in report when path was auto-found

---

### Feature F — MSI Center GPU Mode Detection (`doctor.ps1`)

**Registry read:**
`HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000`
Value: `MSHybridEnabled` (DWORD)

| Value | Mode | Note |
|-------|------|------|
| `1` | MSHybrid | iGPU + dGPU power sharing |
| `0` | Discrete Only | dGPU always active — preferred for gaming |
| absent | Unknown / not MSI | Non-MSI system or GPU switching unsupported |

**Doctor output additions:**
```
gpu_mode            : MSHybrid
gpu_mode_note       : Switch to Discrete Only in MSI Center before gaming for lower DPC latency
```

Included in HTML export's system info panel. No write operations — read-only detection.

---

## UX Fixes

### Launcher Pause Behavior

All `.cmd` launchers that display output add `pause` after the PowerShell call so the terminal stays open when double-clicked from the desktop. Exception: `keeper-watch.cmd` (loop keeps it open), and admin launchers (handled separately).

| Launcher | Change |
|----------|--------|
| `keeper-gaming.cmd` | add `pause` |
| `keeper-coding.cmd` | add `pause` |
| `keeper-audio-safe.cmd` | add `pause` |
| `keeper-quiet.cmd` | add `pause` |
| `keeper-diagnose.cmd` | add `pause` |
| `keeper-restore.cmd` | add `pause` |
| `keeper-status.cmd` | add `pause` |
| `keeper-doctor.cmd` | add `pause` |
| `keeper-doctor-audio.cmd` | add `pause` + auto-open HTML |
| `keeper-export.cmd` | add `-Html` flag + `pause` + auto-open HTML |
| `keeper-watch.cmd` | no change |

### Auto-Open HTML

`keeper-doctor-audio.cmd` and `keeper-export.cmd`: after the PowerShell call completes, find the most-recently modified `.html` in `incidents/` and open it with `start`.

### Admin Elevated Launchers

`Invoke-KeeperElevated.ps1`: switch from `-File` to `-Command "& 'path' @args; Read-Host 'Press Enter to close'"`. Try `pwsh.exe` first (PowerShell 7+), fall back to `powershell.exe`.

### First-Run Setup

New `setup.cmd` in repo root:
```cmd
@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install-shortcuts.ps1"
pause
```

Single double-click installs all desktop + Start Menu shortcuts.

### Shortcut Icons

`install-shortcuts.ps1` uses distinct `shell32.dll` icon indices per shortcut type:

| Type | Icon index |
|------|-----------|
| Gaming / Admin | 16 (game controller-ish) |
| Coding | 71 (monitor) |
| Audio / Doctor | 168 (speaker) |
| Status / Watch | 21 (magnifier) |
| Restore / Setup | 238 (undo-ish) |

### Legacy Gaming-Mode Redirect

`tools/gaming-mode/README.md`: add notice at top pointing to `keeper.ps1` as the primary system. Keep existing content for reference.

---

## Data Flow

```
listen               watch                   mode/doctor/export
   │                    │                          │
   ▼                    ▼                          ▼
lib/listener.ps1   lib/watch.ps1          keeper.ps1 router
   │                    │                          │
   ├── lib/config.ps1   ├── lib/health.ps1    lib/config.ps1
   ├── lib/profiles.ps1 ├── lib/state.ps1     lib/profiles.ps1
   └── lib/actions.ps1  └── lib/export.ps1    lib/doctor.ps1
                           (anomaly only)      lib/export.ps1
                                               lib/actions.ps1
```

State files (`state/*.json`) are the only shared mutable surface — no pipes, no sockets, no shared memory between commands.

---

## Config Changes

### `config/defaults.json` additions

```json
{
  "listener": {
    "pollIntervalSec": 3,
    "steamVdfPath": null,
    "onGameStart": "gaming",
    "onGameExit": "restore"
  },
  "anomaly": {
    "enabled": true,
    "cpuSpikePercent": 80,
    "spikeSustainSamples": 3,
    "captureOnNahimicDetected": true,
    "audioRiskNewProcesses": 2
  }
}
```

All other config keys, file paths, and profile schemas remain unchanged.

---

## New State File

`state/listener.json` — written by `listen` command, deleted on clean exit:
```json
{
  "game_exe": "eldenring.exe",
  "game_path": "C:\\SteamLibrary\\steamapps\\common\\ELDEN RING\\Game\\eldenring.exe",
  "pid": 12345,
  "detected_at": "2026-03-29T18:42:10Z",
  "prior_mode": "coding"
}
```

---

## Implementation Order

1. `lib/config.ps1` — foundation; everything else depends on it
2. `lib/state.ps1` — second dependency tier
3. `lib/health.ps1` — needed by watch, doctor, profiles
4. `lib/actions.ps1` — needed by profiles, listener
5. `lib/doctor.ps1` — includes features E + F
6. `lib/profiles.ps1` — mode apply/restore
7. `lib/export.ps1` — HTML/JSON generation
8. `lib/watch.ps1` — watch loop + feature B
9. `lib/listener.ps1` — feature A
10. `keeper.ps1` refactor — thin router wiring everything
11. UX fixes — .cmd launchers, setup.cmd, Invoke-KeeperElevated.ps1, install-shortcuts.ps1
12. Config updates — defaults.json additions
13. New launchers — keeper-listen.cmd, keeper-listen-admin.cmd
14. Legacy redirect — gaming-mode README
15. Smoke test — verify all commands still work end-to-end

---

## What Does NOT Change

- All existing `.cmd` launcher filenames and behavior (except adding `pause`)
- All config file locations and schemas (only additions, no removals)
- All state file locations (`state/`, `sessions/`, `incidents/`)
- CLI flags and command names
- `katana-keeper/` subdirectory (independent MVP, unaffected)
- `docs/safety.md` safety model

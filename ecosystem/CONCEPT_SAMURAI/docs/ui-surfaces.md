# Keeper UI Surfaces

## Goal

Keeper stays **offline-first** and **local-first**:

- the PowerShell core remains the source of truth
- the Godot shell is the primary desktop UI
- the web dashboard is an optional degraded fallback
- no internet connection is required for normal operation

## Surface hierarchy

### 1. Core CLI

`keeper.ps1` remains the authoritative runtime:

- mode switching
- rollback
- doctor / audio triage
- watch / listen
- export
- updates / automation

### 2. Local JSON bridge

`tools/keeper-bridge.ps1` is the integration seam for UI layers and future local
projects such as Dev-Mentor, SimulatedVerse, or NuSyQ-Hub.

It exposes machine-readable JSON for:

- `snapshot`
- `status`
- `doctor`
- `recommend`
- `auto`
- `games`
- `mode`
- `export`

This avoids scraping human-oriented `Format-List` output and keeps the CLI stable.

### 3. Godot desktop shell

`godot/keeper-shell` is the preferred app surface:

- Windows desktop UI
- system tray via Godot `StatusIndicator`
- no browser required
- local bridge only
- room for richer surfaces later without rewriting keeper core logic

### 4. Web fallback

`index.html` remains the last-resort fallback surface.

It is intentionally secondary:

- useful if Godot is unavailable
- safe offline because it is local static content
- does not replace the desktop shell

## Launch paths

### Main desktop shell

```powershell
.\tools\Launch-KeeperShell.ps1
```

or double-click:

```text
tools\keeper-ui.cmd
```

### Force the fallback dashboard

```powershell
.\tools\Launch-KeeperShell.ps1 -PreferWebFallback
```

or double-click:

```text
tools\keeper-web.cmd
```

## Deployment model

Current state:

- usable from source checkout
- Godot shell runs from the project folder
- launcher resolves Godot locally when installed

Later:

- add Godot export preset
- build a standalone Windows executable
- keep the same bridge and CLI underneath

## Why this split

This keeps the project maintainable:

- no giant monolithic UI script inside `keeper.ps1`
- no internet dependency
- future integrations can call the bridge directly
- the Godot shell can evolve without destabilizing the core orchestration logic

# keeper.ps1 — Safety Model

## Guiding Principles

1. **No permanent destructive changes.** Every action the tool takes can be reversed.
2. **State before action.** The tool snapshots the current state before applying any change.
3. **No blind registry spray.** Only the Game Mode DWORD (`AllowAutoGameMode`) is touched.
4. **No driver changes.** Driver installs, updates, and removals are always manual.
5. **No always-growing logs.** The ring buffer is capped and rolls over automatically.
6. **-WhatIf on everything.** Every mode change can be previewed without applying it.

---

## What the Tool Will Never Do Automatically

These are intentionally out of scope for the automated profiles. They require human judgment and are listed here as guided manual steps:

### Nahimic / Realtek Audio

If `doctor` detects Nahimic and audio stutter is confirmed:

1. Open **MSI Center** → check if Nahimic is installed under "Features"
2. Try **disabling audio enhancements** first:
   - Sound settings → Output device → Device properties → Additional device properties → Enhancements → Disable all
3. If stutter persists, try **stopping the Nahimic service** temporarily:
   ```powershell
   Stop-Service -Name "NahimicService" -Force
   ```
4. This repo's default recommendation is **disable first, do not uninstall first**. Uninstall or reinstall only after:
   - the temporary Nahimic A/B test clearly improves stutter, or
   - LatencyMon still points at the audio path after you remove other likely culprits
5. If stutter resolves, consider a clean reinstall via MSI's support page (not via random GitHub scripts)

### Driver Updates

If `doctor` or LatencyMon points to a specific driver (e.g., `nvlddmkm.sys`, `ndis.sys`):

- Update via **Device Manager** or the manufacturer's official download
- Never use third-party "driver updater" tools
- For NVIDIA: use the official GeForce Experience or nvidia.com installer

### GPU Mode Switching (MSI-specific)

Some MSI Katana SKUs support switching between:
- **MSHybrid** (iGPU + dGPU, better battery)
- **Discrete only** (dGPU always active, better gaming latency)

This requires MSI Center and often a reboot. It is not automated here because:
- Not all Katana SKUs support it
- It requires a restart to take effect
- The wrong setting drains battery significantly

Manual steps: MSI Center → User Scenario → GPU Switch (if available for your model)

### BIOS Updates

MSI's official audio troubleshooting path includes checking for BIOS updates. This is:
- Always manual
- Always done through MSI's support site for your exact model number
- Never automated

### Permanent Service Startup Changes

`keeper.ps1` starts and stops services for a session, but **never changes their startup type**. Services like `WSearch` will return to their configured startup state after a reboot regardless of what keeper does.

If you want to permanently disable a service, do it deliberately through `services.msc`, not through this tool.

### Scheduled Automation

`auto` and `schedule` are intentionally limited:

- They only move between `coding` and `balanced`
- They never auto-enter `gaming`
- If a game is detected, automation defers instead of changing mode
- The goal is to reduce idle/dev friction safely, not to surprise you mid-session

### Guarded Package Updates

`updates -Apply` only upgrades packages that pass the update policy:

- Docker Desktop and Visual Studio Code family packages are blocked by default
- Allow lists override deny lists if you explicitly trust a package
- Updates are applied one package at a time by exact package ID
- Windows Update, drivers, BIOS, and firmware remain manual

---

## Rollback Behavior

`mode restore` reads `state/rollback.json` and applies the inverse of the last mode change:

- Restarts any services that were stopped (e.g., WSearch)
- Restores the prior power plan by GUID
- Restores Game Mode state

Limitations:
- Stopped **processes** are not restarted (VS Code, Docker Desktop, browsers) — those you relaunch manually or via the `coding` profile's `startLaunchers`
- Only the **most recent** rollback is stored — running two mode changes in a row overwrites the first rollback
- If you reboot between mode change and restore, the rollback may be stale

---

## Risk Classification

| Action | Risk | Reversible |
|--------|------|-----------|
| `wsl --shutdown` | Low | Yes (restart WSL) |
| Stop VS Code | Low | Yes (relaunch) |
| Stop Docker Desktop | Low | Yes (relaunch) |
| Stop Node/Python/Jupyter | Low | Yes (relaunch) |
| Stop WSearch service | Low | Yes (restore command) |
| Set High Performance power plan | Low | Yes (restore command) |
| Enable/disable Game Mode | Low | Yes (restore command) |
| Stop Nahimic service (manual) | Medium | Yes (restart service) |
| Disable audio enhancements (manual) | Medium | Yes (re-enable in Sound settings) |
| Update drivers (manual) | Medium | Yes (rollback in Device Manager) |
| GPU mode switch via MSI Center (manual) | Medium | Yes (switch back + reboot) |
| BIOS update (manual) | High | Rarely reversible |
| Uninstall Nahimic/Realtek (manual) | High | Requires reinstall |

---

## LatencyMon Guidance

If audio stutter persists after running `audio-safe` mode, the next step is running **LatencyMon** (resplendence.com/latencymon) while reproducing the stutter.

What to look for:

| Driver | Likely cause |
|--------|-------------|
| `nvlddmkm.sys` | NVIDIA driver DPC latency |
| `ndis.sys` | Wi-Fi/network driver latency |
| `ACPI.sys` | Power management / firmware |
| `dxgkrnl.sys` | GPU scheduling |
| `HDAudBus.sys` | Audio driver itself |
| `storahci.sys` | Storage controller |

Share the LatencyMon output with the driver name highlighted and investigate that specific driver. The fix is almost always a driver update, not a system setting.

`.\keeper.ps1 doctor -Export -AudioTriage -Html -LatencyMonReportPath <path>` will bundle the current doctor state, audio driver inventory, Nahimic process/service state, and the referenced LatencyMon report path into a single incident export.

---

## What "Safe" Means Here

The tool will not touch:
- Registry keys other than the single Game Mode DWORD
- Driver or firmware files
- Windows Update settings
- Startup programs (Autoruns entries)
- GPU configuration
- Network adapter settings
- Scheduled tasks (read-only, never written)
- User data or documents

The tool **will** temporarily modify:
- Active power plan (always restored)
- Game Mode registry key (always restored)
- Running processes (stopped only if listed in profile)
- Service running state (stopped/started, startup type unchanged)
- WSL VM state (`wsl --shutdown` — restart with `wsl` manually)

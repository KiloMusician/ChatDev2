# katana-keeper

Lightweight, safe system orchestrator for Windows laptops that switches between gaming and coding modes, reduces background interference, and monitors system health in real time. Uses profile-based actions, rollback, and compact state tracking—no bloat, no risky tweaks, just predictable behavior.

## Quick start

1. Open PowerShell in the `katana-keeper` folder.
2. Run `status` to see current health:

```powershell
pwsh -ExecutionPolicy Bypass -File .\keeper.ps1 status
```

3. Start watch mode (live):

```powershell
pwsh -ExecutionPolicy Bypass -File .\keeper.ps1 watch
```

4. Switch to gaming mode (dry-run first with -WhatIf):

```powershell
pwsh -ExecutionPolicy Bypass -File .\keeper.ps1 mode gaming -WhatIf
# to actually apply:
pwsh -ExecutionPolicy Bypass -File .\keeper.ps1 mode gaming
```

5. Restore prior state:

```powershell
pwsh -ExecutionPolicy Bypass -File .\keeper.ps1 mode restore
```

## Files

- `keeper.ps1` — single-file CLI (status, watch, mode, doctor, prune)
- `config/defaults.json` — safe defaults (ring buffer size, retention)
- `config/profiles.json` — profile definitions (gaming, coding, diagnose, restore)
- `config/machine.local.json` — machine-specific overrides (not under version control; copy from `machine.local.json.example`)

## Notes

- Config: `config/defaults.json` and `config/profiles.json` control behavior. Edit `config/machine.local.json` (not under version control) to add your machine-specific preferences.
- State files live under `state/` and are intentionally small. `sessions/` keeps tiny session summaries. `incidents/` are only created on explicit export or anomaly.
- This MVP intentionally avoids destructive driver/BIOS changes. Use LatencyMon for deep driver/DPC analysis.

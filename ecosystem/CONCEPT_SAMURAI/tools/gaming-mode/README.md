> **This toolkit predates `keeper.ps1`.**
> For the current system, use `.\keeper.ps1` from the repo root - it covers all gaming, audio-safe, coding, diagnose, quiet, and restore modes with WhatIf support, rollback, Steam game-watcher, and HTML export. Double-click `setup.cmd` to install desktop shortcuts.
> The scripts below are kept for reference.

---

# Gaming Mode toolkit

This small toolkit provides scripts to (safely) switch your Windows laptop into a "Gaming Mode", collect diagnostics, and capture performance logs to help diagnose audio stutter or other issues during gameplay.

Files
- `gaming-mode.ps1` — toggle a custom gaming mode (switch power plan, stop Docker/WSL, lower background process priorities, optionally disable Nahimic)
- `monitor-usage.ps1` — sample CPU/memory/top processes and (if available) NVIDIA GPU stats and write CSV logs
- `diagnostics.ps1` — collect system info (OS, CPU, GPU, audio devices, installed audio drivers, running dev processes)

Quick workflow

1. Run `diagnostics.ps1` and save its output (helps identify obvious misconfigurations).
   - In PowerShell: `pwsh -ExecutionPolicy Bypass -File .\\diagnostics.ps1 | Tee-Object diagnostics-output.txt`

2. Start `monitor-usage.ps1` while reproducing the audio stutter. Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\gaming-mode\monitor-usage.ps1 -DurationSeconds 300 -IntervalSeconds 2 -Output .\gaming-monitor.csv
```

3. Optionally enable Gaming Mode to reduce background noise (this will switch power plan and attempt to stop Docker/WSL by default):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\gaming-mode\gaming-mode.ps1 -Mode on
```

4. Reproduce the audio stutter while the monitor is running. After you collect logs, disable gaming mode:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\gaming-mode\gaming-mode.ps1 -Mode off
```

5. For true root-cause DPC/driver analysis, run LatencyMon while reproducing the stutter and attach the generated report. LatencyMon is the recommended tool for DPC latency analysis: https://www.resplendence.com/latencymon

Notes and cautions
- Some operations in `gaming-mode.ps1` require Administrator privileges (changing service startup type, switching the active power plan). The script will warn if admin access is not available.
- The scripts try to be conservative: they will not kill editors or browsers unless explicitly asked.
- Don’t run these scripts blindly during important work — they stop services and may change system settings.

If you want, I can:

- Walk you through running LatencyMon and interpreting its report (paste the report here and I’ll analyze it).
- Tweak the scripts to more aggressively stop processes you identify as noisy (e.g., specific Python/Jupyter kernels, Docker containers).
- Convert the monitor to a small GUI or system tray tool if you prefer a one-click recorder.

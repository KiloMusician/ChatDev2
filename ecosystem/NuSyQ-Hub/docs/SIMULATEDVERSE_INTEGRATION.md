# SimulatedVerse Integration

This document describes quick steps and scripts to wire the `SimulatedVerse`
repo into the NuSyQ ecosystem.

Files added

- `config/repos.json` — maps repo names to absolute paths on disk.
- `scripts/start_simulatedverse.ps1` — convenience script to run dependency
  check + `npm run dev` in the SimulatedVerse repo.

How to run

1. Ensure `config/repos.json` has the correct path for `SimulatedVerse`.
2. From the NuSyQ-Hub root, start the SimulatedVerse dev server:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_simulatedverse.ps1
```

`config/repos.json` should target the SimulatedVerse repository root (the folder
that contains `package.json`). If your layout is nested, the launcher now
auto-detects `SimulatedVerse/` under that root.

The launcher installs dependencies only when needed:
- `node_modules` is missing, or
- `package-lock.json` is newer than `node_modules/.package-lock.json`.

Use a forced reinstall when required:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_simulatedverse.ps1 -ForceInstall
```

WSL note: if `tsx` fails with `ENOTSUP` on `/mnt/c/.../Temp/...pipe`, set
Linux temp dirs when launching Node scripts:

```bash
TEMP=/tmp TMP=/tmp TMPDIR=/tmp npm run dev:minimal
```

Monitoring

- The Agent Dashboard can monitor files under `tools/agent_dashboard` and will
  refresh when `status.json` changes. To monitor SimulatedVerse, add a small
  script in the `SimulatedVerse` repo that writes status to
  `NuSyQ-Hub/tools/agent_dashboard/status.json` or create a symlink.

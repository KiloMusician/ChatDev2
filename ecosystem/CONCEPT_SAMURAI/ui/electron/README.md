Keeper UI (Electron prototype)

This prototype provides a minimal Electron desktop app (system tray + dashboard) that can start/stop the repo's Steam listener and show a simple dashboard.

Quick start (Windows):

1. Install Node.js (v18+ recommended).
2. cd ui/electron
3. npm install
4. npm run start

Notes
- The tray toggle starts `tools/keeper-listen.cmd` in the repository root. When you stop the listener via the tray app it will kill the child process started by the app (it cannot stop an external listener started outside the app).
- The dashboard reads `state/listener.json` to display the tracked game/process info when available.
- The UI is intentionally minimal. Next steps to improve:
  - Add a proper tray icon (place an .ico at `ui/electron/assets/icon.ico`).
  - Add persistent app settings (autostart, minimize-to-tray)
  - Wire Steam Web API enrichment into the dashboard (use `tools/steam-enrich-example.ps1`).
  - Package with an installer (electron-builder or similar) for Windows distribution.

Offline behavior
- The app is fully local and does not require internet to start or to control the local listener. Remote Steam enrichments are optional and only used if your machine has a Steam Web API key configured.

Security
- The prototype spawns local commands (cmd/pwsh) to interact with the repo scripts. Only run it in trusted environments.

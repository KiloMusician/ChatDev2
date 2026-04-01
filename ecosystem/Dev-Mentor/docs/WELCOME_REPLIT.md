# DevMentor in Replit (Interactive Lab)

This Replit project is **a development & learning lab** for the **VS Code-native DevMentor repository**.

- **Source of truth:** `.devmentor/state.json` (portable; used by VS Code, Replit, anywhere)
- **Core runtime (target):** open the repository in VS Code (`code .`) and use VS Code Tasks
- **Replit adds:** a web dashboard + CLI that wrap the *same* core scripts (zero magic)

## Run modes

### 1) Web Dashboard (default in Replit)
- Click **Run**.
- Open the web preview.
- Use the left sidebar to navigate (Dashboard / Tutorials / Actions / Live Logs).
- Export a portable ZIP any time from the footer link.

### 2) CLI
In the shell:

```bash
python -m cli.devmentor status
python -m cli.devmentor start
python -m cli.devmentor next
python -m cli.devmentor export
```

## Portability: Replit ➜ VS Code

1. In Replit, export:

```bash
python -m cli.devmentor export
```

2. Download `exports/devmentor-portable.zip`
3. Unzip anywhere, open in VS Code
4. Continue via VS Code Tasks

> The Replit UI is optional. The repo must still “just work” in VS Code with no Replit dependencies.

## Architecture (short)

- `scripts/` — core DevMentor operations (bootstrap, validate, export/import)
- `.devmentor/` — portable progress state (gitignored in real use)
- `app/backend/` — FastAPI wrapper with allow-listed commands + websocket logs
- `app/frontend/` — static dashboard UI
- `cli/` — Typer/Rich CLI wrapper

Happy forging. 🚀

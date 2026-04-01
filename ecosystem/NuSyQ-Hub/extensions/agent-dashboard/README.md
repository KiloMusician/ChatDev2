# NuSyQ Agent Dashboard

Legacy VS Code extension that originally provided a lightweight webview showing
real-time agent status, quest progress, and unified error reporting for the
NuSyQ-Hub workspace.

Current status:

- the canonical IDE cockpit is now `src/vscode_mediator_extension`
- the mediator capability cockpit absorbs this package's core behaviors
- this folder remains useful as reference code and a compatibility surface, not
  as the preferred UI entry point

Features

- Agent list (from tools/agent_dashboard/status.json)
- Quest log (from src/Rosetta_Quest_System/quest_log.jsonl)
- Unified errors (from state/unified_errors.json)
- Automatic refresh when those files change

Preferred usage

1. Open the command palette (Ctrl+Shift+P).
2. Run `PowerShell Mediator: Open Capability Cockpit`.
3. Use the `Agent Mesh` and `Unified Error Queue` sections there for the
   integrated view.

Legacy usage

1. Open the command palette (Ctrl+Shift+P) and run "Agent Dashboard: Open".
2. Click Refresh to fetch live data from the workspace.

Notes

- This extension expects to be opened in the NuSyQ-Hub workspace. It looks for
  files under `state/`, `src/Rosetta_Quest_System/`, and
  `tools/agent_dashboard/`.
- For production-grade integration, consider adding IPC/WS hooks to NuSyQ
  services.

A small VS Code extension that provides a live Webview dashboard for:

- ✅ Real-time agent status (reads `tools/agent_dashboard/status.json`)
- ✅ Quest progress (reads `src/Rosetta_Quest_System/quest_log.jsonl`)
- ✅ Unified error reporting (reads `state/unified_errors.json`)

Key features

- Live file watchers and automatic updates for agent/quest/error sources.
- Buttons to run workspace tasks: _Run Unified Error Report_, _Run System
  Snapshot_ (if tasks are present).
- Open the unified error JSON directly in the editor.

Quick install (developer mode)

1. Open this workspace in VS Code.
2. Open the `extensions/agent-dashboard` folder.
3. Run the "Run Extension" debug target (F5) to load the extension in an
   Extension Development Host.

Usage

- Command Palette → **Open Agent Dashboard** to open the webview.
- Use **Refresh** to force a manual reload.
- Click **Run Unified Error Report** to start the `NuSyQ: Unified Error Report`
  task (if configured).

Integration notes

- The extension reads from:
  - `tools/agent_dashboard/status.json` (agent snapshots)
  - `src/Rosetta_Quest_System/quest_log.jsonl` (quest event stream)
  - `state/unified_errors.json` (unified diagnostics)
- Provide tasks in `.vscode/tasks.json` for `NuSyQ: Unified Error Report` and
  the system snapshot tasks so the extension can trigger them.

Suggested next steps

- Keep this package as a compatibility/reference surface while consolidating UI
  effort into the mediator cockpit.
- Avoid adding new dashboard-only features here unless they are first designed
  for the canonical cockpit.

Security & privacy

- The webview runs with scripts enabled and a strict CSP. Files are read from
  the workspace only.

Contributing

- Follow the repository's `Three Before New` rule: search for an existing
  capability before adding new files.
- Keep UI code minimal and prefer the workspace's canonical sources for data.

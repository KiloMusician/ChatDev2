# PowerShell Mediator VS Code extension (minimal)

This is the canonical VS Code control-plane extension for the local NuSyQ
ecosystem. It provides mediator control plus live diagnostics, capability
cockpit workflows, and a single IDE-native place to surface cross-repo
operators like GitNexus, Nogic, Culture Ship, and Keeper.

Structured read precedence:

1. `state/boot/rosetta_bootstrap.json`
2. `state/registry.json`
3. `state/reports/control_plane_snapshot.json`
4. focused feed artifacts
5. docs fallback

Legacy dashboard behavior is now folded into the capability cockpit instead of
living as a separate first-class UI track. That means the cockpit now also
surfaces:

- live `tools/agent_dashboard/status.json` agent roster data
- the Rosetta quest tail from `src/Rosetta_Quest_System/quest_log.jsonl`
- the legacy `state/unified_errors.json` feed when present
- repair queue management through `state/repair_requests.json`
- freshness and ownership for bootstrap, registry, snapshot, deprecations, and the Culture Ship runtime descriptor
- structured IDE surface inventory from the snapshot, including mediator commands, supporting extension commands, and sampled Dev-Mentor VS Code tasks
- structured storage/state inventory from the snapshot, including repo-owned ledgers, cache DBs, memory stores, and legacy archive counts

- `PowerShell Mediator: Start` — launches the repository wrapper
  `scripts/start_powershell_mediator.ps1` which in turn runs the Node-based
  mediator (`scripts/powershell_mediator.js`). The wrapper runs the mediator in
  the background.
- `PowerShell Mediator: Stop` — issues a best-effort stop (the extension
  launches the wrapper; stopping is best done via OS process manager).
- `PowerShell Mediator: Refresh Diagnostics Snapshot` — runs
  `scripts/vscode_diagnostics_bridge.py --quiet` and rewrites the current
  bridge snapshot under `docs/Reports/diagnostics/`.
- `PowerShell Mediator: Open Diagnostics Dashboard` — opens a webview with live
  VS Code diagnostics counts plus the latest bridge snapshot.
- `PowerShell Mediator: Open Capability Cockpit` — opens a webview for local
  AI/runtime probes plus one-click launches for OpenClaw, Intermediary, AI
  status, SkyClaw, AI Council demo loop, Culture Ship, Ollama, LM Studio, and
  the hidden `nusyq.*` / ChatDev local extension commands, including ignition,
  tripartite status, routing, tests/tasks launchers, AI terminal queries, the
  absorbed agent-mesh dashboard, and the repair queue.

Control-plane intent:

- treat this extension as the primary IDE cockpit
- keep GitNexus, Nogic, Culture Ship, Keeper, and local model surfaces visible
- migrate useful dashboard behavior here instead of proliferating more packages
- treat `extensions/agent-dashboard` as a legacy feeder/reference package

How to use during development

1. Open this repository in VS Code.
2. Run the Extension Development Host (F5). In the development host, open the
   Command Palette and run `PowerShell Mediator: Start`.
3. The extension adds a mediator status item and a live diagnostics status item
   in the status bar, plus a live terminal-topology status item.
4. Click the diagnostics status item to refresh the bridge snapshot manually,
   or use the dashboard command for a richer in-editor view.
5. Use `PowerShell Mediator: Open Capability Cockpit` for a VS Code-native
   operator panel over the core NuSyQ local AI systems, direct command entry
   points, absorbed agent-mesh/quest/error dashboard signals, Terminal Keeper
   session grid, repair queue control, and live terminal topology coverage.

Notes & limitations

- This remains a local/workspace-oriented extension, but it is the intended
  spine for the IDE control plane rather than a disposable experiment.
- The mediator runs `scripts/start_powershell_mediator.ps1` which expects `node`
  installed and the mediator script to be present in
  `scripts/powershell_mediator.js`.
- Auto-refresh-on-save is controlled by the `powershellMediator.*` workspace
  settings contributed by the extension.
- The cockpit can detect and launch commands exposed by the bundled
  `../vscode-extension` and `../src/integration/vscode_extension` packages when
  those local extensions are installed in the workspace.

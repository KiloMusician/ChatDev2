# DevMentor Runtime (VS Code-Native)

## Reality check: “auto-run on open”
VS Code does **not** reliably auto-execute arbitrary scripts on folder open without an extension.
DevMentor achieves “open and it works” via:
1) opening a welcome document (README)
2) recommending extensions
3) providing a single boot task: **DevMentor: Start/Resume**

An optional micro-extension can later remove the last click, but this repo is designed to work without it.

## Control surface
- `.vscode/tasks.json` is the runtime control panel
- `.devmentor/state.json` is the canonical local progress (“save game”)
- `exports/devmentor-portable.zip` is the portable snapshot

## Key tasks
- DevMentor: Start/Resume
- DevMentor: Next Step
- DevMentor: Validate Current Challenge
- DevMentor: Diagnose Environment
- 🔍 DevMentor: Boot Status
- 🔗 DevMentor: Integration Matrix
- DevMentor: Export Portable ZIP
- DevMentor: Import Portable ZIP

## Operator notes
- `DevMentor: Boot Status` is the structured autoboot/status view for the current runtime.
- `DevMentor: Integration Matrix` is the quickest way to see Keeper, GitNexus, Nogic, Docker, and agent-surface truth without browsing docs first.


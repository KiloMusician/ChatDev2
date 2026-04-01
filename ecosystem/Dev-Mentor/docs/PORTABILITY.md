# Portability (Replit ↔ ZIP ↔ VS Code)

## Goal
You can develop this repo anywhere (Replit, Codespaces, local).
At any moment you can export a ZIP and resume in VS Code **without losing learning state**.

## Canonical state
`.devmentor/state.json` is the “save game.” It is:
- local by default (gitignored)
- portable via `DevMentor: Export Portable ZIP`

## What the portable ZIP contains
- the minimum scripts needed to import/resume
- tutorials + challenges
- `.vscode/` configuration
- a `manifest.json` including saved state


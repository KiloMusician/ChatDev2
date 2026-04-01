# Nested Workspace Notes — NuSyQ

This repository is often used as part of a larger, multi-repo workspace that
includes `NuSyQ-Hub`, `SimulatedVerse` and `ChatDev`. Some ignore and docker
patterns reference sibling directories when the repos are opened together.

Purpose
- Explain why there are cross-repo ignore entries (e.g., `ChatDev/WareHouse/`).
- Provide guidance for using this repo standalone vs in a nested workspace.

When using NuSyQ as part of a workspace
- Keep sibling-path ignore rules (they prevent huge ephemeral folders from
  being tracked when the workspace is opened at a higher-level root).
- Use `scripts/analyze_ignores.py` to audit ignore rules and detect
  cross-references: `python scripts/analyze_ignores.py` (writes
  `state/ignore_report.json`).

When using NuSyQ standalone
- Consider removing or narrowing sibling-path patterns in `.gitignore` and
  `.dockerignore` so they only target local patterns. Use `.git/info/exclude`
  for private, clone-local ignores.

If you want assistance converting this repo to a standalone build context,
open an issue or ask the AI Council (see `docs/AI_AGENT_INSTRUCTIONS.md`).

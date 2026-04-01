# Testing Chamber — Safe Edit Policy

**Purpose**: allow agents to modify pre-existing files without risking the live game.

## Where Edits Go
- Staging: `/testing-chamber/<module>/<file>`
- Promotion PR merges back to canonical location after smokes pass.

## Guardrails
- Mirror original path under `testing-chamber/` to preserve imports.
- Attach Rosetta header (STABILITY: alpha, HEALTH: unknown).
- Required proof artifacts:
  - `ops/smokes/<module>.<ts>.json` (pass/fail + reason)
  - `ops/diffs/<module>.<ts>.patch` (exact changes)
- Promotion requires:
  - Boot & render smoke pass
  - Duplicate/bloat scan clean
  - Reviewer = OWNER in Rosetta header

## Allowed Edits
- Bugfix, perf tweak, UI polish, incremental feature toggled off by default.
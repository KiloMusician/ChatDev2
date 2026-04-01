# Workspace Rosetta Stone

Last updated: 2026-03-21

## Purpose

This is the canonical guide for repo-root truth in the active workspace.

Use this document whenever SCM counts, status checks, or service ownership are
ambiguous. Do not assume that a folder name shown in VS Code is the real Git
root.

## Canonical Repo Roots

These are the real repos that matter for the current ecosystem work:

- `/mnt/c/CONCEPT`
  - Keeper / Concept_Samurai
  - machine pressure, mode, advisor, maintenance
  - Windows-first executor and preflight layer

- `/mnt/c/Users/keath/Dev-Mentor`
  - Terminal Depths
  - orchestrator
  - Serena integration
  - ChatDev worker
  - Open Router service
  - bridge/probes/cascade scripts

- `/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub`
  - Hub API
  - Hub status and health semantics

- `/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse`
  - SimulatedVerse app/runtime
  - degraded mode and fallback launcher
  - Rosetta content/schemas

- `/mnt/c/Users/keath/NuSyQ`
  - broader NuSyQ system repo
  - RosettaStone normalization, routing, proof gates

- `/mnt/c/Users/keath/NuSyQ/ChatDev`
  - nested ChatDev repo

## Shadow Git Traps

These paths contained `.git` directories that were not reliable repo roots for
the current work and could mislead automation or IDE SCM:

- `/mnt/c/Users/keath/Desktop/SimulatedVerse/.git`
- `/mnt/c/Users/keath/Desktop/Legacy/.git`

These malformed shadow `.git` directories were removed on 2026-03-21.

Do not recreate parent-folder `.git` directories above the canonical repo roots.
Do not trust status counts from parent folders over the canonical repo roots
above.

## Known SCM Failure Modes

### 1. Nested-folder name mismatch

The human label `SimulatedVerse` may refer to either:

- the parent folder `/mnt/c/Users/keath/Desktop/SimulatedVerse`
- or the real repo `/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse`

Always verify which one is active before making claims about pending changes.

### 2. Mode-bit churn on Windows-backed trees

The SimulatedVerse repo can show large false-positive file changes caused by
permission flips like `100644 => 100755` with no content changes.

Local mitigation:

```bash
git -C /mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse config core.filemode false
```

### 3. Stale VS Code SCM badges

After cleanup, the Source Control badge may continue to show old counts.
Refresh the SCM pane or reload the window before assuming the repo is still
dirty.

### 4. SimulatedVerse Git boundary friction

The canonical SimulatedVerse repo on this machine currently has two recurring
Git friction points:

- Git LFS hooks are installed, but `git-lfs` is not always available on PATH in
  the active shell, which can block normal post-checkout/post-merge/pre-push
  flows.
- WSL Git on the Windows-backed worktree can hang or take an unusually long
  time during `git status`, even for small changes, because working-tree scans
  on the mounted filesystem are slow.

Operational rule:

- treat this as a repo hygiene/runtime issue, not a sign that the changes are
  strategically large
- prefer `python scripts/workspace_scm_truth.py --save` or Windows `git.exe`
  when establishing authoritative SimulatedVerse SCM truth
- if a push is blocked only by missing `git-lfs`, either install/fix `git-lfs`
  in that shell or use a narrow temporary hook bypass for the push rather than
  assuming the repo itself is corrupted

### 5. Runtime queue churn in Dev-Mentor

`/mnt/c/Users/keath/Dev-Mentor/tasks/queue.json` can change while the live
worker stack is active. Treat this as runtime task state, not casual editor
noise.

### 6. Task surface split

`/mnt/c/Users/keath/Dev-Mentor/tasks/queue.json` is the canonical swarm queue.

`/mnt/c/Users/keath/Dev-Mentor/tasks/legacy_runtime/` is the old file-based
task lane used by a few legacy scripts. It is not the primary planning surface.

`/mnt/c/Users/keath/Dev-Mentor/tasks/archive/` is historical storage only and
must not be treated as live pending work.

## Current Documentation State

### Accurate but incomplete

- [`TRIPARTITE_WORKSPACE_AUDIT_2026-03-20.md`](/mnt/c/Users/keath/Dev-Mentor/docs/workspace/TRIPARTITE_WORKSPACE_AUDIT_2026-03-20.md)
  - useful operational snapshot
  - does not document the shadow `.git` traps
  - does not clearly distinguish parent folders from actual repo roots

- [`NESTED_WORKSPACE_README.md`](/mnt/c/Users/keath/Desktop/SimulatedVerse/NESTED_WORKSPACE_README.md)
  - useful warning about nested workspace behavior
  - too narrow to serve as the workspace-wide source of truth

## Live Cross-Repo Control Surfaces

These are the current low-token or zero-token control planes that should be
preferred before broad LLM exploration:

- `CONCEPT` / Keeper
  - `C:\CONCEPT\tools\keeper-bridge.ps1`
  - deterministic pressure, advisor, maintenance, and mode decisions

- `NuSyQ-Hub` / GitNexus
  - `http://127.0.0.1:8000/api/gitnexus/health`
  - `http://127.0.0.1:8000/api/gitnexus/matrix`
  - `http://127.0.0.1:8000/api/gitnexus/repos/{repo_id}`
  - use for cross-repo git/state truth instead of rediscovering repo status

- `NuSyQ-Hub` / Nogic
  - bridge exists in `src/integrations/nogic_bridge.py`
  - VS Code bridge exists in `src/integrations/nogic_vscode_bridge.py`
  - treat this as the live architecture visualization surface

- `NuSyQ` / RosettaStone
  - `python scripts/run_rosetta_pipeline.py ...`
  - normalization, routing, artifact persistence, and proof-gate flow
  - `state/boot/rosetta_bootstrap.json`
  - `state/registry.json`
  - `state/reports/control_plane_snapshot.json`

## Control-Plane Read Order

Before broad repo rediscovery, prefer:

1. `NuSyQ/state/boot/rosetta_bootstrap.json`
2. `NuSyQ/state/registry.json`
3. `NuSyQ/state/reports/control_plane_snapshot.json`
4. focused feed artifacts
5. docs fallback

## Canonical Repo Roles

- `CONCEPT`
  - machine-governance and safe-start executor

- `Dev-Mentor / TerminalDepths`
  - interactive MCP, game/task plane, operator-facing workflow surface

- `SimulatedVerse`
  - simulation layer, patch-bay, ChatDev runtime, Culture Ship runtime owner

- `NuSyQ`
  - RosettaStone pipeline, telemetry, proof-gate memory, multi-agent root

- `NuSyQ-Hub`
  - orchestration brain, healing, diagnostics, Nogic visualization, GitNexus matrix, Culture Ship control owner

## Canonical VS Code Workspace

Use this workspace file for normal operation:

- [`TerminalKeeper.ecosystem.code-workspace`](/mnt/c/Users/keath/Dev-Mentor/TerminalKeeper.ecosystem.code-workspace)

It intentionally includes only the primary repo roots:

- `Dev-Mentor`
- `NuSyQ`
- `NuSyQ-Hub`
- `SimulatedVerse`

It intentionally does not include the nested `NuSyQ/ChatDev` repo by default,
to avoid duplicate SCM surfaces unless that repo is being worked directly.

## Canonical SCM Truth Command

For multi-repo status checks, use:

```bash
python scripts/workspace_scm_truth.py --save
```

This command is the authoritative workspace-wide SCM check because it:

- parses the checked-in workspace file
- discovers nested repos under workspace folders
- uses Windows `git.exe` automatically for `/mnt/c/...` repos
- reports ahead/behind plus pending files per repo

This matters on the current machine because WSL Git on Windows-backed trees can
time out or hide pending files that VS Code and Windows Git still surface.

### Not the operational guide

- [`RosettaStone.md`](/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/knowledge/RosettaStone.md)
  - real and important
  - but it is a game/schema/lore system document
  - it is not the SCM or workspace-ownership guide

## Operating Rule

Before claiming a repo is clean, dirty, ahead, behind, or push-ready:

1. verify the exact repo root
2. run `python scripts/workspace_scm_truth.py --save`
3. check tracked changes
4. check untracked changes
5. check upstream ahead/behind
6. only then summarize workspace state

Do not infer workspace truth from folder labels, stale IDE counts, or shallow
directory scans.

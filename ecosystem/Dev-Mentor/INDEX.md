# Dev-Mentor Operator Index

This file is the current entrypoint map for the repo. Older “deployment complete” notes are intentionally retired so operators do not start from stale bootstrap assumptions.

## Start here
- [`START_HERE.md`](/mnt/c/Users/keath/Dev-Mentor/START_HERE.md)
- [`TORCH.md`](/mnt/c/Users/keath/Dev-Mentor/TORCH.md)
- [`BOOTSTRAP.md`](/mnt/c/Users/keath/Dev-Mentor/BOOTSTRAP.md)

## Primary control surfaces
- VS Code tasks in [`.vscode/tasks.json`](/mnt/c/Users/keath/Dev-Mentor/.vscode/tasks.json)
- Workspace SCM truth in [`scripts/workspace_scm_truth.py`](/mnt/c/Users/keath/Dev-Mentor/scripts/workspace_scm_truth.py)
- Runtime CLI in [`cli/devmentor.py`](/mnt/c/Users/keath/Dev-Mentor/cli/devmentor.py)
- Ecosystem map in [`ECOSYSTEM.md`](/mnt/c/Users/keath/Dev-Mentor/ECOSYSTEM.md)

## Recommended operator flow
1. Run Keeper / `CONCEPT` preflight first when the wider stack is under pressure.
2. Use `DevMentor: Start/Resume` to attach to the local runtime.
3. Use `🔍 DevMentor: Boot Status` and `🔗 DevMentor: Integration Matrix` before browsing docs or logs.
4. Use `DevMentor: Diagnose Environment` and `DevMentor: Validate Current Challenge` before assuming the runtime is broken.

## Current runtime facts
- `Dev-Mentor` health: `http://127.0.0.1:7337/api/health`
- `LM Studio` canonical Windows endpoint: `http://127.0.0.1:1234/v1/models`
- `SimulatedVerse` current local runtime: `http://127.0.0.1:5002/api/health`
- `ChatDev` adapter: `http://127.0.0.1:4466/chatdev/agents`

## Avoid
- treating old `Bootstrap Workspace` references as canonical
- assuming older `SimulatedVerse` `5000` docs are still accurate
- assuming WSL Git slowness in sibling repos means repo corruption

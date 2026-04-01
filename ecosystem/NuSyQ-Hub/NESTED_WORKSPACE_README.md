# Nested Workspace Notes — NuSyQ-Hub

NuSyQ-Hub is primarily an orchestration and service layer and is frequently
opened inside larger workspaces that include `NuSyQ` and `SimulatedVerse`. Some
ignore and dockerignore entries intentionally reference sibling folders or
workspace-level artifacts.

Quick guidance

- If you work on NuSyQ-Hub as a standalone repo: review `.gitignore` and
  `.dockerignore` for sibling-path entries (they are harmless but may be
  confusing). Remove or narrow them if you prefer a standalone workflow.
- If you work in the multi-repo workspace: keep these entries. They help prevent
  large ephemeral directories (e.g., `ChatDev/WareHouse/`) from being
  accidentally included in builds or commits.

Tools

- Audit ignore cross-references: `python ../NuSyQ/scripts/analyze_ignores.py`
  (runs from the workspace root and writes `state/ignore_report.json`).
- If you use Claude CLI/extension, set a temp path so it doesn’t emit `tmpclaude-*` folders in the repo root (e.g., launch from a shell with `set TMP=C:\Users\keath\AppData\Local\Temp & set TEMP=%TMP%` on Windows).

Build context note

- Docker builds should use a curated build context (minimal subtree) to avoid
  shipping the entire workspace. See `docs/` for recommended build contexts and
  scripts.

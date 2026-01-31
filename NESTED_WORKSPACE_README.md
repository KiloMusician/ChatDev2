# Nested Workspace Notes — ChatDev

ChatDev is included as a component under the NuSyQ workspace and may be
referenced from other repos via sibling-path ignores (e.g., `ChatDev/WareHouse/`).

Usage guidance
- When working on ChatDev standalone, ensure `.gitignore` entries that
  reference sibling repos are adjusted so local builds are predictable.
- If you rely on submodules (see `.gitmodules`), ensure submodules are
  initialised via `git submodule update --init --recursive`.

Audit
- To see how other repos reference ChatDev, run the workspace ignore audit:
  `python ../scripts/analyze_ignores.py` (from workspace root).

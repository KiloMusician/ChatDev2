Third-party components and vendoring notes

1. GodotProjectZero (TinyTakinTeller/GodotProjectZero)

   - Intended usage: submodule at external/GodotProjectZero (not added in
     branch-only preview)
   - Upstream license: MIT for code; assets may be licensed per-contributor.
     When vendoring, list asset-specific licenses.
   - To add as submodule (run from repository root):

     git submodule add https://github.com/TinyTakinTeller/GodotProjectZero.git
     external/GodotProjectZero git submodule update --init --recursive

2. Branch-only preview performed: a namespaced bridge and CI workflow were added
   to preview integration without adding the upstream submodule.

When we vendor template files, record the upstream commit hash and the specific
files copied into `THIRD_PARTY.md`.

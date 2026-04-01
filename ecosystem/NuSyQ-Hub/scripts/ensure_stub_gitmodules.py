"""Ensure `.gitmodules` contains a safe stub for the `_vibe` submodule to avoid
CI failing when `.gitmodules` is inconsistent or missing that entry.

This script is idempotent and safe to run in CI before any `git submodule`
commands are invoked.
"""

from pathlib import Path

GITMODULES = Path(".gitmodules")
STUB = """[submodule "_vibe"]
    path = _vibe
    url = https://github.com/KiloMusician/placeholder-empty-vibe.git
"""

if not GITMODULES.exists():
    print(".gitmodules not found, creating stub with _vibe entry")
    GITMODULES.write_text(STUB)
else:
    content = GITMODULES.read_text()
    if 'submodule "_vibe"' in content or '[submodule "_vibe"]' in content:
        print("_vibe entry already present in .gitmodules")
    else:
        print("_vibe entry missing; appending safe stub to .gitmodules")
        with GITMODULES.open("a", encoding="utf-8") as f:
            f.write("\n" + STUB)

print("ensure_stub_gitmodules: done")

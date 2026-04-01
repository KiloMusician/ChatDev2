#!/usr/bin/env python3
"""ecosystem_entrypoint.py — Devcontainer post-create hook.

Called by .devcontainer/devcontainer.json postCreateCommand.
Runs a quick system brief to validate the environment is healthy.
Extend this to perform full environment setup as needed.
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).parent.parent
    print("=== NuSyQ-Hub Ecosystem Entrypoint ===")
    print(f"Repo root: {repo_root}")

    result = subprocess.run(
        [sys.executable, "scripts/start_nusyq.py", "brief"],
        cwd=repo_root,
    )
    if result.returncode != 0:
        print("⚠️  Brief check returned non-zero — environment may need attention.")
        # Don't fail the devcontainer post-create; just warn.
    else:
        print("✅ Environment brief passed.")

    print("\nTIP: Run 'python scripts/start_nusyq.py menu' to explore available actions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

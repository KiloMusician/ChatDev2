from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def provide_context(config: dict[str, Any]) -> dict[str, Any]:
    root = Path(config.get("root_dir", "."))
    branch_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    commit_result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    files = list(root.rglob("*"))
    return {
        "branch": branch_result.stdout.strip(),
        "commit_count": commit_result.stdout.strip(),
        "total_files": sum(1 for f in files if f.is_file()),
        "total_directories": sum(1 for f in files if f.is_dir()),
    }

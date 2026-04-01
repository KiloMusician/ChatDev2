from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _git_changed_files(root: Path) -> list[Path]:
    diff = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    files: list[Path] = [root / p for p in diff.stdout.splitlines() if p]
    files.extend([root / p for p in untracked.stdout.splitlines() if p])
    return files


def _git_all_files(root: Path) -> list[Path]:
    cmd = ["git", "ls-files"]
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
    return [root / p for p in result.stdout.splitlines() if p]


def provide_context(config: dict[str, Any]) -> dict[str, Any]:
    root = Path(config.get("root_dir", "."))
    changed_only = config.get("changed_files_only", False)
    files = _git_changed_files(root) if changed_only else _git_all_files(root)

    summaries: list[Any] = []
    for path in files:
        if not path.is_file():
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            summaries.append(
                {
                    "path": str(path.relative_to(root)),
                    "lines": len(lines),
                    "first_line": lines[0].strip() if lines else "",
                }
            )
        except Exception as exc:
            summaries.append({"path": str(path), "error": str(exc)})
    return {"files": summaries}

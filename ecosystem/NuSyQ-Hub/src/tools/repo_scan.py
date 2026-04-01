"""Utility command to scan repository structure and detect simple anomalies.

Provides a summary of directories, files, and potential issues such as
missing ``__init__`` modules or unusually large files. Designed to be
used as a ChatDev command and to return JSON-serialisable data for
GitHub Copilot or other tools.

Agent & developer tips:
- Use `repo_scan` as a fast health-check in CI jobs or when onboarding new
    contributors to understand repo layout.
- The returned dictionary is intentionally JSON-serialisable so agents can
    index and create tasks from anomalies found.
- For broad repository scans, run with `depth=None`; for quick checks use
    `depth=1` or `depth=2` to limit runtime.

Example:
-------
>>> from src.tools.repo_scan import repo_scan
>>> result = repo_scan(path='.', depth=1)
>>> result['total_files'] >= 0
True

"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def repo_scan(
    path: str = ".", depth: int | None = None, max_file_size: int = 1_000_000
) -> dict[str, Any]:
    """Scan a repository and return a structured summary.

    Parameters
    ----------
    path:
        Root directory to start scanning from.
    depth:
        Optional maximum depth to descend relative to ``path``.
        ``None`` scans the entire tree.
    max_file_size:
        Threshold in bytes to flag files as ``large_files`` anomalies.

    Returns:
    -------
    dict
        JSON-serialisable summary containing counts and anomalies.

    """
    root = Path(path).resolve()
    if not root.exists():
        msg = f"Path not found: {root}"
        raise FileNotFoundError(msg)

    summary: dict[str, Any] = {
        "path": str(root),
        "total_dirs": 0,
        "total_files": 0,
        "files_by_extension": {},
        "anomalies": {
            "large_files": [],
            "missing_init": [],
            "suspicious_files": [],
        },
    }

    def _scan(current: Path, current_depth: int) -> None:
        for entry in current.iterdir():
            try:
                if entry.is_dir():
                    summary["total_dirs"] += 1
                    if depth is None or current_depth < depth:
                        py_files = list(entry.glob("*.py"))
                        if py_files and not (entry / "__init__.py").exists():
                            summary["anomalies"]["missing_init"].append(
                                str(entry.relative_to(root))
                            )
                        _scan(entry, current_depth + 1)
                elif entry.is_file():
                    summary["total_files"] += 1
                    ext = entry.suffix or ""
                    summary["files_by_extension"][ext] = (
                        summary["files_by_extension"].get(ext, 0) + 1
                    )
                    size = entry.stat().st_size
                    if size > max_file_size:
                        summary["anomalies"]["large_files"].append(str(entry.relative_to(root)))
                    if not entry.suffix:
                        summary["anomalies"]["suspicious_files"].append(
                            str(entry.relative_to(root))
                        )
            except (PermissionError, OSError):
                # Skip entries we cannot access
                continue

    _scan(root, 0)

    # Sort outputs for consistency
    summary["files_by_extension"] = dict(sorted(summary["files_by_extension"].items()))
    for key in summary["anomalies"]:
        summary["anomalies"][key] = sorted(summary["anomalies"][key])

    return summary


if __name__ == "__main__":  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description="Scan repository structure and report anomalies")
    parser.add_argument("--path", default=".")
    parser.add_argument("--depth", type=int, default=None)
    parser.add_argument("--max-file-size", type=int, default=1_000_000)
    args = parser.parse_args()

    result = repo_scan(path=args.path, depth=args.depth, max_file_size=args.max_file_size)

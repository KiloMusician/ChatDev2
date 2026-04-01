"""Repository structure scanner used by integrated scanner workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def repo_scan(
    path: str = ".",
    depth: int | None = None,
    max_file_size: int = 1_000_000,
) -> dict[str, Any]:
    """Scan a repository tree and return counts + lightweight anomalies."""
    root = Path(path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {root}")

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
                        summary["anomalies"]["large_files"].append(
                            str(entry.relative_to(root))
                        )
                    if not entry.suffix:
                        summary["anomalies"]["suspicious_files"].append(
                            str(entry.relative_to(root))
                        )
            except (PermissionError, OSError):
                continue

    _scan(root, 0)
    summary["files_by_extension"] = dict(sorted(summary["files_by_extension"].items()))
    for key in ("large_files", "missing_init", "suspicious_files"):
        summary["anomalies"][key] = sorted(summary["anomalies"][key])
    return summary


def scan_repository(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    """Backward-compatible alias used by older scripts."""
    return [repo_scan(*args, **kwargs)]

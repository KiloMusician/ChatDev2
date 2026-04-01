#!/usr/bin/env python3
"""Duplicate filename audit report.

Scans the repository for duplicate filenames and proposes a "prime" file for each
duplicate group based on simple heuristics (src/ > scripts/ > tools/ > docs/state).
Writes both Markdown and JSON reports for review.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}

IGNORE_FILES = {
    "__init__.py",
    "README.md",
    "LICENSE",
    "LICENSE.txt",
    ".DS_Store",
}


def _should_skip(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def _score_path(path: Path) -> int:
    parts = set(path.parts)
    score = 0
    if "src" in parts:
        score += 30
    if "scripts" in parts:
        score += 20
    if "tools" in parts:
        score += 10
    if "tests" in parts:
        score += 5
    if "docs" in parts:
        score -= 5
    if "state" in parts or "data" in parts:
        score -= 10
    score -= len(path.parts)  # prefer shallower paths
    return score


def _pick_prime(paths: list[Path]) -> tuple[Path, list[str]]:
    scored = sorted(paths, key=lambda p: (_score_path(p), p.stat().st_mtime), reverse=True)
    prime = scored[0]
    reasons = []
    if "src" in prime.parts:
        reasons.append("prefers src/")
    elif "scripts" in prime.parts:
        reasons.append("prefers scripts/")
    elif "tools" in prime.parts:
        reasons.append("prefers tools/")
    else:
        reasons.append("shorter/more recent path")
    return prime, reasons


def build_report(root: Path) -> dict[str, Any]:
    duplicates: dict[str, list[Path]] = defaultdict(list)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if _should_skip(path):
            continue
        duplicates[path.name].append(path)

    duplicate_groups = {name: paths for name, paths in duplicates.items() if len(paths) > 1}

    ignored = {name: [str(p) for p in paths] for name, paths in duplicate_groups.items() if name in IGNORE_FILES}

    actionable = {name: paths for name, paths in duplicate_groups.items() if name not in IGNORE_FILES}

    analyzed = []
    for name, paths in sorted(actionable.items()):
        prime, reasons = _pick_prime(paths)
        analyzed.append(
            {
                "filename": name,
                "count": len(paths),
                "prime": str(prime),
                "prime_reasons": reasons,
                "paths": [
                    {
                        "path": str(p),
                        "size_bytes": p.stat().st_size,
                        "modified": datetime.fromtimestamp(p.stat().st_mtime, tz=UTC).isoformat(),
                    }
                    for p in sorted(paths)
                ],
            }
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "root": str(root),
        "duplicate_count": len(actionable),
        "ignored_duplicates": ignored,
        "duplicates": analyzed,
    }


def write_reports(report: dict[str, Any], output_dir: Path, prefix: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"{prefix}_{timestamp}.json"
    md_path = output_dir / f"{prefix}_{timestamp}.md"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Duplicate Filename Audit",
        "",
        f"Generated: {report['generated_at']}",
        f"Root: {report['root']}",
        f"Actionable duplicates: {report['duplicate_count']}",
        "",
        "## Ignored (common/expected names)",
    ]
    if report["ignored_duplicates"]:
        for name, paths in sorted(report["ignored_duplicates"].items()):
            lines.append(f"- {name} ({len(paths)} copies)")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Actionable duplicates")
    if not report["duplicates"]:
        lines.append("- None")
    else:
        for item in report["duplicates"]:
            lines.append(f"### {item['filename']} ({item['count']} copies)")
            lines.append(f"- Prime: {item['prime']}")
            lines.append(f"- Prime reasons: {', '.join(item['prime_reasons'])}")
            lines.append("- Paths:")
            for path_info in item["paths"]:
                lines.append(f"  - {path_info['path']} ({path_info['size_bytes']} bytes)")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote JSON report: {json_path}")
    print(f"Wrote Markdown report: {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Duplicate filename audit report")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--output-dir", default="state/reports", help="Output directory for reports")
    parser.add_argument("--prefix", default="duplicate_filename_report", help="Report prefix")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root)
    write_reports(report, Path(args.output_dir), args.prefix)


if __name__ == "__main__":
    main()

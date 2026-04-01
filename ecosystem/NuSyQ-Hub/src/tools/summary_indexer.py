#!/usr/bin/env python3
"""📑 Summary / Report / Analysis Documentation Indexer.

=========================================================

OmniTag: {
    "purpose": "Scan repository for summary, report, and analysis markdown files and build a unified index",
    "dependencies": ["pathlib", "json"],
    "context": "Feeds documentation artifacts into AI orchestration and context engines",
    "evolution_stage": "v1.0"
}

This module discovers markdown documentation artifacts (summary, report, analysis, session logs)
and produces a structured JSON index for downstream AI systems.

Design Goals:
- Zero heavy dependencies
- Fast glob scanning with limited pattern set
- Metadata extraction (title, category, first heading, repo, size, modified timestamp)
- Extensible categorization via simple pattern matching

Output: docs/Auto/SUMMARY_INDEX.json
Structure:
{
  "generated_at": ISO_TIMESTAMP,
  "repository": REPO_NAME,
  "total_files": N,
  "files": [ { ... metadata ... } ],
  "categories": { category: count }
}

Usage:
    python -m src.tools.summary_indexer            # builds index for current repo
    from src.tools.summary_indexer import build_summary_index  # programmatic use
"""

from __future__ import annotations

import contextlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

CATEGORY_MAP = {
    "summary": ["summary"],
    "report": ["report"],
    "analysis": ["analysis"],
    "session": ["session"],
    "investigation": ["investigation"],
}

HEADING_PATTERN = re.compile(r"^#\s+(?P<title>.+)$", re.MULTILINE)


@dataclass
class SummaryDocMeta:
    path: str
    repository: str
    category: str
    size_bytes: int
    modified: str
    title: str | None = None
    first_heading: str | None = None
    omni_tags: list[str] | None = None


def categorize(path: Path) -> str:
    lowered = path.name.lower()
    for cat, tokens in CATEGORY_MAP.items():
        if any(tok in lowered for tok in tokens):
            return cat
    return "other"


def extract_metadata(path: Path, repo_name: str) -> SummaryDocMeta:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    heading_match = HEADING_PATTERN.search(text)
    first_heading = heading_match.group("title").strip() if heading_match else None
    # Simple OmniTag extraction (JSON-like curly block containing "purpose")
    omni_tags: list[str] = []
    if "OmniTag" in text:
        for line in text.splitlines():
            if "OmniTag" in line or "MegaTag" in line or "RSHTS" in line:
                omni_tags.append(line.strip())
    omni_tags_value: list[str] | None = omni_tags or None
    return SummaryDocMeta(
        path=str(path),
        repository=repo_name,
        category=categorize(path),
        size_bytes=path.stat().st_size if path.exists() else 0,
        modified=(
            datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            if path.exists()
            else datetime.now().isoformat()
        ),
        title=first_heading,
        first_heading=first_heading,
        omni_tags=omni_tags_value,
    )


def scan_repository(root: Path) -> list[SummaryDocMeta]:
    excluded_dir_names = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        "dist",
        "build",
    }
    recursive_scan_roots = [
        root / "docs",
        root / "Reports",
        root / "state" / "reports",
    ]

    def _should_skip_directory(path: Path) -> bool:
        path_str = str(path).replace("\\", "/").lower()
        return (
            "/docs/archive/" in path_str
            or "/docs/archive" in path_str
            or "/archive/" in path_str
            or "/nusyq_clean_clone/" in path_str
            or "/docs/tracing/receipts/" in path_str
        )

    def _is_summary_doc(filename: str) -> bool:
        lowered = filename.lower()
        if not lowered.endswith(".md"):
            return False
        return (
            "summary" in lowered
            or "report" in lowered
            or "analysis" in lowered
            or (lowered.startswith("session_") and "summary" in lowered)
        )

    results: list[SummaryDocMeta] = []
    repo_name = root.name
    seen_paths: set[Path] = set()

    # Root-level summaries/reports are common; capture them directly.
    for child in root.iterdir():
        if not child.is_file():
            continue
        if not _is_summary_doc(child.name):
            continue
        if child in seen_paths:
            continue
        seen_paths.add(child)
        results.append(extract_metadata(child, repo_name))

    for scan_root in recursive_scan_roots:
        if not scan_root.exists() or not scan_root.is_dir():
            continue
        if _should_skip_directory(scan_root):
            continue
        for current_root, dirs, files in os.walk(scan_root):
            current_path = Path(current_root)
            dirs[:] = [
                d
                for d in dirs
                if d not in excluded_dir_names and not _should_skip_directory(current_path / d)
            ]
            if _should_skip_directory(current_path):
                continue
            for name in files:
                if not _is_summary_doc(name):
                    continue
                path = current_path / name
                if path in seen_paths:
                    continue
                seen_paths.add(path)
                results.append(extract_metadata(path, repo_name))
    return results


def build_summary_index(root: Path) -> dict[str, Any]:
    files = scan_repository(root)
    categories: dict[str, int] = {}
    for meta in files:
        categories[meta.category] = categories.get(meta.category, 0) + 1
    return {
        "generated_at": datetime.now().isoformat(),
        "repository": root.name,
        "total_files": len(files),
        "categories": categories,
        "files": [asdict(f) for f in files],
    }


def save_summary_index(root: Path) -> Path:
    index = build_summary_index(root)
    out_dir = root / "docs" / "Auto"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "SUMMARY_INDEX.json"
    out_file.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return out_file


def main() -> None:
    root = Path(__file__).resolve().parents[2]  # repository root
    save_summary_index(root)


if __name__ == "__main__":  # pragma: no cover
    with contextlib.suppress(KeyboardInterrupt, SystemExit):
        main()

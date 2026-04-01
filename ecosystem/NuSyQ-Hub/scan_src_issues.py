#!/usr/bin/env python3
"""Focused diagnostic for src/ directory only"""

import re
from pathlib import Path

repo_root = Path("src")
issues: dict[str, list[tuple[Path, int, str]]] = {
    "placeholder": [],
    "deprecated": [],
    "incomplete": [],
    "hardcoded": [],
}

SKIP_DIRS: set[str] = {"legacy", "__pycache__"}
SKIP_PATHS: set[Path] = {
    Path("diagnostics/unified_scanner.py"),
    Path("config/service_config.py"),
}

placeholder_patterns = [
    r"raise NotImplementedError",
    r"TODO[\s:]*implement",
]

deprecated_patterns = [
    r"@deprecated",
    r"# DEPRECATED",
]

incomplete_patterns = [
    r"# TODO:",
    r"# FIXME:",
    r"# WIP:",
]

hardcoded_patterns = [
    r"'C:\\\\Users",
    r'"C:\\\\Users',
    r"localhost:[\d]{4,5}",
]


def _should_skip(path: Path) -> bool:
    """Determine whether a path should be skipped during scanning."""
    rel_path = path.relative_to(repo_root)
    if any(part in SKIP_DIRS for part in rel_path.parts):
        return True
    if rel_path in SKIP_PATHS:
        return True
    return False


def scan_file(fpath: Path) -> None:
    """Scan a file for issues."""
    if _should_skip(fpath):
        return
    try:
        with open(fpath, encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                for pattern in placeholder_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues["placeholder"].append((fpath, i, line.strip()[:60]))
                        break

                for pattern in incomplete_patterns:
                    if re.search(pattern, line):
                        issues["incomplete"].append((fpath, i, line.strip()[:60]))
                        break

                for pattern in hardcoded_patterns:
                    if re.search(pattern, line):
                        issues["hardcoded"].append((fpath, i, line.strip()[:60]))
                        break
    except (OSError, UnicodeDecodeError):
        pass


# Scan src/ Python files
for py_file in sorted(repo_root.rglob("*.py")):
    scan_file(py_file)

print("=" * 90)
print("SRC/ DIRECTORY ISSUES (Core codebase)")
print("=" * 90)

for category, items in issues.items():
    if items:
        print(f"\n{category.upper()}: {len(items)} issues")
        for fpath, line_no, text in sorted(set(items))[:20]:
            rel_path = str(fpath).replace("src\\", "")
            print(f"  {rel_path}:{line_no}")
            print(f"    └─ {text}")

print("\n" + "=" * 90)
total = sum(len(v) for v in issues.values())
print(f"TOTAL ISSUES IN SRC/: {total}")

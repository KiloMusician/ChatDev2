#!/usr/bin/env python3
"""Comprehensive diagnostic for misconfigured/incomplete files"""

import re
from pathlib import Path

repo_root = Path(".")
issues: dict[str, list[str]] = {
    "placeholder_patterns": [],
    "deprecated_patterns": [],
    "incomplete_patterns": [],
    "missing_implementations": [],
    "rigid_hardcoded": [],
    "config_issues": [],
}

# Patterns to search for
placeholder_patterns = [
    r"TODO[\s:]*implement",
    r"FIXME[\s:]*placeholder",
    r"pass\s*#\s*TODO",
    r"raise NotImplementedError",
]

deprecated_patterns = [
    r"@deprecated",
    r"# deprecated",
    r"# DEPRECATED",
    r"__deprecated__",
]

incomplete_patterns = [
    r"# TODO:",
    r"# FIXME:",
    r"# WIP:",
    r"# HACK:",
]

hardcoded_patterns = [
    r"'C:\\\\Users",
    r'"C:\\\\Users',
    r"'/home/",
    r"localhost:11434",
    r"localhost:5000",
    r"localhost:8081",
]


def scan_file(fpath: Path) -> None:
    """Scan a file for issues."""
    try:
        with open(fpath, encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Check for placeholders
                for pattern in placeholder_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues["placeholder_patterns"].append(f"{fpath}:{i}")
                        break

                # Check for deprecation
                for pattern in deprecated_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues["deprecated_patterns"].append(f"{fpath}:{i}")
                        break

                # Check for incompleteness
                for pattern in incomplete_patterns:
                    if re.search(pattern, line):
                        issues["incomplete_patterns"].append(f"{fpath}:{i}")
                        break

                # Check for hardcoding
                for pattern in hardcoded_patterns:
                    if re.search(pattern, line):
                        issues["rigid_hardcoded"].append(f"{fpath}:{i}")
                        break
    except (OSError, UnicodeDecodeError):
        pass


# Scan all Python files
for py_file in repo_root.rglob("*.py"):
    if ".git" not in str(py_file) and "__pycache__" not in str(py_file):
        scan_file(py_file)

# Print summary
print("=" * 80)
print("REPOSITORY DIAGNOSTIC: MISCONFIGURED & INCOMPLETE FILES")
print("=" * 80)

for category, items in issues.items():
    if items:
        print(f"\n{category.upper().replace('_', ' ')}: {len(set(items))} issues")
        for item in sorted(set(items))[:15]:  # Show first 15
            print(f"  - {item}")
        if len(set(items)) > 15:
            print(f"  ... and {len(set(items)) - 15} more")

print("\n" + "=" * 80)
print(f"TOTAL ISSUES: {sum(len(set(v)) for v in issues.values())}")

#!/usr/bin/env python3
"""Auto-fix script for mypy type errors - Phase 1.

Fixes [var-annotated] errors by adding basic type annotations.
"""

import argparse
import re
import sys
from pathlib import Path


def fix_dict_assignments(content: str) -> tuple[str, int]:
    """Fix: var = {} -> var: dict[str, Any] = {}"""
    fixes = 0
    pattern = r"^(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{\}\s*$"

    def replacement(match):
        nonlocal fixes
        fixes += 1
        return f"{match.group(1)}{match.group(2)}: dict[str, Any] = {{}}"

    return re.sub(pattern, replacement, content, flags=re.MULTILINE), fixes


def fix_list_assignments(content: str) -> tuple[str, int]:
    """Fix: var = [] -> var: list[Any] = []"""
    fixes = 0
    pattern = r"^(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\[\]\s*$"

    def replacement(match):
        nonlocal fixes
        fixes += 1
        return f"{match.group(1)}{match.group(2)}: list[Any] = []"

    return re.sub(pattern, replacement, content, flags=re.MULTILINE), fixes


def ensure_typing_any(content: str) -> str:
    """Add 'from typing import Any' if needed."""
    if "from typing import" in content:
        if "Any" not in content.split("from typing import")[1].split("\n")[0]:
            content = content.replace("from typing import ", "from typing import Any, ", 1)
    else:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith("#") and not line.strip().startswith('"""'):
                lines.insert(i, "from typing import Any\n")
                break
        content = "\n".join(lines)
    return content


def process_file(path: Path, dry_run: bool) -> int:
    """Process single file, return number of fixes."""
    try:
        content = path.read_text(encoding="utf-8")

        content, dict_fixes = fix_dict_assignments(content)
        content, list_fixes = fix_list_assignments(content)

        total = dict_fixes + list_fixes
        if total > 0:
            content = ensure_typing_any(content)
            if not dry_run:
                path.write_text(content, encoding="utf-8")
            print(f"{'[DRY RUN] ' if dry_run else ''}✓ {path}: {total} fixes")

        return total
    except Exception as e:
        print(f"✗ {path}: {e}", file=sys.stderr)
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    files = list(args.path.rglob("*.py")) if args.path.is_dir() else [args.path]
    total_fixes = sum(process_file(f, args.dry_run) for f in files)

    print(f"\n{'=' * 60}")
    print(f"Total fixes: {total_fixes}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

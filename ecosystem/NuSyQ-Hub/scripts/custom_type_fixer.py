#!/usr/bin/env python3
"""Custom type error auto-fixer for mypy issues.

Handles common patterns that mypy can't auto-fix:
- Missing type annotations
- Any casts for gradual typing
- Optional type fixes
- Import type stubs
"""

import re
from pathlib import Path


class CustomTypeFixer:
    """Smart type error fixer."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.fixes_applied = 0
        self.files_modified = []

    def fix_missing_return_types(self, filepath: Path) -> int:
        """Add -> None to functions missing return type."""
        content = filepath.read_text(encoding="utf-8")
        original = content

        # Pattern: def function(...):  (no -> annotation)
        pattern = r"(\n    def \w+\([^)]*\)):\n"
        replacement = r"\1 -> None:\n"
        content = re.sub(pattern, replacement, content)

        if content != original:
            filepath.write_text(content, encoding="utf-8")
            changes = content.count("-> None:") - original.count("-> None:")
            self.fixes_applied += changes
            if changes > 0:
                self.files_modified.append(str(filepath))
            return changes
        return 0

    def add_any_casts(self, filepath: Path, error_lines: list[str]) -> int:
        """Add 'cast(Any, ...)' for gradual typing migration."""
        # This is more conservative - only add typing.Any import
        content = filepath.read_text(encoding="utf-8")
        original = content

        if "from typing import" in content and "Any" not in content:
            # Add Any to existing typing import
            content = re.sub(
                r"from typing import ([^\n]+)",
                lambda m: (f"from typing import {m.group(1)}, Any" if "Any" not in m.group(1) else m.group(0)),
                content,
                count=1,
            )
        elif "from typing import" not in content and "import typing" not in content:
            # Add typing import at top after docstring
            lines = content.split("\n")
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('"""') or line.startswith("'''"):
                    # Find closing docstring
                    for j in range(i + 1, len(lines)):
                        if '"""' in lines[j] or "'''" in lines[j]:
                            insert_idx = j + 1
                            break
                    break
                elif not line.strip() or line.startswith("#"):
                    continue
                else:
                    insert_idx = i
                    break

            lines.insert(insert_idx, "from typing import Any\n")
            content = "\n".join(lines)

        if content != original:
            filepath.write_text(content, encoding="utf-8")
            self.fixes_applied += 1
            self.files_modified.append(str(filepath))
            return 1
        return 0

    def fix_all_files(self, error_file: Path) -> dict[str, int]:
        """Process all files with errors."""
        if not error_file.exists():
            return {"total_fixes": 0, "files_modified": 0}

        errors = error_file.read_text().split("\n")
        files_to_fix = set()

        for error_line in errors:
            if ":" in error_line:
                filepath = error_line.split(":")[0].strip()
                files_to_fix.add(filepath)

        stats = {"return_types": 0, "any_imports": 0}

        for filepath_str in files_to_fix:
            filepath = Path(filepath_str)
            if filepath.exists() and filepath.suffix == ".py":
                stats["return_types"] += self.fix_missing_return_types(filepath)
                # Only add Any import if file has type errors
                if any(str(filepath) in err for err in errors):
                    stats["any_imports"] += self.add_any_casts(filepath, errors)

        return {
            "total_fixes": self.fixes_applied,
            "files_modified": len(set(self.files_modified)),
            "stats": stats,
        }


def main():
    """Run custom type fixes."""
    repo_root = Path(__file__).parent.parent
    error_file = repo_root / "state" / "mypy_errors_for_fixing.txt"

    print("🔧 Custom Type Fixer")
    print("=" * 60)

    fixer = CustomTypeFixer(repo_root)
    results = fixer.fix_all_files(error_file)

    print(f"\n✅ Fixes applied: {results['total_fixes']}")
    print(f"📁 Files modified: {results['files_modified']}")
    print("\nBreakdown:")
    for key, value in results.get("stats", {}).items():
        print(f"   • {key}: {value}")

    if results["files_modified"] > 0:
        print("\n📝 Run 'mypy src/' again to verify fixes")

    return 0 if results["total_fixes"] > 0 else 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""Batch fix common Pylance type errors across multiple files.

Usage:
    python scripts/fix_type_errors_batch.py [file1] [file2] ...
"""

import json
import subprocess
import sys
from pathlib import Path


def fix_return_type_none_to_dict(file_path: Path) -> int:
    """Fix functions that return dict but are annotated with -> None."""
    content = file_path.read_text()
    original = content

    # First pass: find methods that actually return dicts
    lines = content.splitlines()
    methods_returning_dicts = set()

    for i, line in enumerate(lines):
        if " -> None:" in line and "    def " in line:
            # Look ahead for return {
            for j in range(i + 1, min(i + 10, len(lines))):
                if "return {" in lines[j] or "return dict(" in lines[j]:
                    methods_returning_dicts.add(i)
                    break
                elif "return " in lines[j] and lines[j].strip() != "return":
                    break

    # Replace -> None with appropriate return type
    for line_num in sorted(methods_returning_dicts, reverse=True):
        old_line = lines[line_num]
        new_line = old_line.replace(" -> None:", " -> dict[str, Any]:")
        lines[line_num] = new_line

    content = "\n".join(lines)

    if content != original:
        file_path.write_text(content)
        # Add import if needed
        if "from typing import Any" not in content and "dict[str, Any]" in content:
            content = content.replace("from typing import ", "from typing import Any, ", 1)
            file_path.write_text(content)
        return len(methods_returning_dicts)
    return 0


def fix_unused_imports(file_path: Path) -> int:
    """Remove unused imports using autoflake."""
    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "autoflake",
                "--remove-all-unused-imports",
                "--in-place",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return 1 if result.returncode == 0 else 0
    except Exception:
        return 0


def get_error_count(file_path: Path) -> int:
    """Get error count from pyright."""
    try:
        result = subprocess.run(
            ["python", "-m", "pyright", str(file_path), "--outputjson"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        data = json.loads(result.stdout)
        return data.get("summary", {}).get("errorCount", 0)
    except Exception:
        return -1


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_type_errors_batch.py <file1> <file2> ...")
        sys.exit(1)

    total_fixes = 0

    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue

        print(f"\n🔧 Processing: {file_path}")

        # Get initial error count
        errors_before = get_error_count(file_path)
        print(f"   Errors before: {errors_before}")

        # Apply fixes
        fixes = 0
        fixes += fix_return_type_none_to_dict(file_path)
        fixes += fix_unused_imports(file_path)

        # Get final error count
        errors_after = get_error_count(file_path)

        if errors_after < errors_before:
            fixed = errors_before - errors_after
            print(f"   ✅ {errors_before} → {errors_after} errors ({fixed} fixed)")
            total_fixes += fixed
        else:
            print(f"   ⚠️ No improvement ({errors_before} → {errors_after})")

    print(f"\n📊 Total errors fixed: {total_fixes}")


if __name__ == "__main__":
    main()

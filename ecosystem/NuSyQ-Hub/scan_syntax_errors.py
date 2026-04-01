#!/usr/bin/env python3
"""Scan for Python syntax errors in the repository."""

import py_compile
from pathlib import Path


def scan_syntax_errors(root_dir, max_errors=20):
    """Scan directory for Python syntax errors."""
    errors = []
    py_files = list(Path(root_dir).rglob("*.py"))

    print(f"Scanning {len(py_files)} Python files...")

    for py_file in sorted(py_files):
        # Skip __pycache__ and test files
        if "__pycache__" in str(py_file) or ".pyc" in str(py_file):
            continue

        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            rel_path = py_file.relative_to(root_dir)
            errors.append({"file": rel_path, "error": str(e)})
            if len(errors) >= max_errors:
                break

    return errors


if __name__ == "__main__":
    root = r"c:\Users\keath\Desktop\Legacy\NuSyQ-Hub\src"
    errors = scan_syntax_errors(root)

    if errors:
        print(f"\n❌ Found {len(errors)} files with syntax errors:\n")
        for err in errors:
            print(f"  {err['file']}")
            # print(f"    Error: {err['error'][:100]}")
    else:
        print(f"\n✅ All {len(list(Path(root).rglob('*.py')))} Python files have valid syntax!")

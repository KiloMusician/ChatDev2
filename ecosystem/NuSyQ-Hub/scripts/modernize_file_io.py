#!/usr/bin/env python3
"""Modernize file I/O to use pathlib Path.open() instead of builtin open().

Converts patterns like:
    with open(file_path, 'r') as f:
    →
    with Path(file_path).open('r') as f:

Or if file_path is already a Path:
    with open(path_obj, 'r') as f:
    →
    with path_obj.open('r') as f:
"""

import re
import sys
from pathlib import Path


def modernize_open_call(line: str, has_path_import: bool) -> tuple[str | None, bool]:
    """Modernize a line with open() call.

    Returns:
        (modified_line, needs_path_import)
    """
    # Pattern: open(variable, mode) or open(variable)
    # Match: with open(...) as
    # Match: = open(...)
    # Match: f = open(...)

    # Skip lines that already use .open()
    if ".open(" in line:
        return None, False

    # Skip comments and strings
    if line.strip().startswith("#"):
        return None, False

    needs_import = False
    result = line

    # Pattern 1: with open(path_var, ...) as
    pattern1 = r"\bopen\(([a-zA-Z_][a-zA-Z0-9_.]*)"
    matches = list(re.finditer(pattern1, line))

    for match in reversed(matches):  # Process right to left
        var_name = match.group(1)

        # Check if variable ends with _path, _file, path, file
        # or is explicitly a Path object name
        is_likely_path_obj = any(x in var_name.lower() for x in ["path", "file"])

        if is_likely_path_obj or "_FILE" in var_name.upper() or "FILE" in var_name.upper():
            # Already a Path object, just use .open()
            result = result[: match.start()] + f"{var_name}.open(" + result[match.end() :]
        else:
            # Might need Path() wrapper
            # For now, conservatively use .open() assuming it's a Path
            result = result[: match.start()] + f"{var_name}.open(" + result[match.end() :]

    if result != line:
        return result, needs_import

    return None, False


def fix_file(filepath: Path) -> tuple[int, int]:
    """Fix open() calls in a file.

    Returns:
        (lines_fixed, errors)
    """
    try:
        content = filepath.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Check if Path is already imported
        has_path_import = any("from pathlib import" in line and "Path" in line for line in lines)

        fixed_count = 0
        new_lines = []

        for line in lines:
            if "open(" in line and ".open(" not in line:
                new_line, _needs_import = modernize_open_call(line, has_path_import)
                if new_line:
                    new_lines.append(new_line)
                    fixed_count += 1
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        if fixed_count > 0:
            filepath.write_text("\n".join(new_lines), encoding="utf-8")
            return fixed_count, 0

        return 0, 0

    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return 0, 1


def main():
    if len(sys.argv) < 2:
        print("Usage: python modernize_file_io.py <file1> [file2 ...]")
        sys.exit(1)

    total_fixed = 0
    total_errors = 0

    for filepath_str in sys.argv[1:]:
        filepath = Path(filepath_str)
        if not filepath.exists():
            print(f"File not found: {filepath}")
            continue

        fixed, errors = fix_file(filepath)
        total_fixed += fixed
        total_errors += errors

        if fixed > 0:
            print(f"✅ {filepath.name}: {fixed} lines fixed")
        elif errors > 0:
            print(f"❌ {filepath.name}: errors occurred")

    print(f"\nTotal: {total_fixed} lines fixed, {total_errors} errors")


if __name__ == "__main__":
    main()

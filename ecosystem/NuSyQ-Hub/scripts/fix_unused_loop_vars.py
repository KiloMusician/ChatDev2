#!/usr/bin/env python3
"""Fix unused loop control variables by prefixing with underscore.

Converts:
    for var in list:
    →
    for _var in list:

When var is not used in the loop body.
"""

import re
import subprocess
import sys
from pathlib import Path


def get_unused_loop_vars():
    """Get list of unused loop variables from ruff."""
    result = subprocess.run(
        ["python", "-m", "ruff", "check", "src/", "--select=B007"],
        capture_output=True,
        text=True,
    )

    fixes = []
    lines = result.stderr.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for the error line with file path
        if "B007" in line and "-->" in line:
            # Extract file path
            match = re.search(r"--> (.*?):(\d+):", line)
            if match:
                file_path = match.group(1).replace("\\", "/")
                line_num = int(match.group(2))

                # Look ahead for the variable name
                i += 1
                while i < len(lines):
                    if "|" in lines[i] and "for " in lines[i]:
                        # Extract variable names from the for loop line
                        # Look for help message with variable name
                        help_idx = i + 1
                        while help_idx < len(lines) and "help:" not in lines[help_idx]:
                            help_idx += 1

                        if help_idx < len(lines):
                            help_line = lines[help_idx]
                            # Extract variable name from help message
                            var_match = re.search(r"Rename unused `(\w+)` to `_\1`", help_line)
                            if var_match:
                                var_name = var_match.group(1)
                                fixes.append((file_path, line_num, var_name))
                        break
                    i += 1
        i += 1

    return fixes


def fix_loop_variable(file_path: Path, line_num: int, var_name: str) -> bool:
    """Fix a single unused loop variable."""
    try:
        lines = file_path.read_text(encoding="utf-8").split("\n")

        if line_num > len(lines):
            return False

        # Get the line (1-indexed to 0-indexed)
        line_idx = line_num - 1
        line = lines[line_idx]

        # Only replace in for loop declaration, not in loop body
        # Match patterns like:
        # for var in ...
        # for var, other in ...
        # for key, value in ...

        # Use word boundaries to avoid partial matches
        pattern = rf"\bfor\s+([^:]*\b{re.escape(var_name)}\b[^:]*)\s+in\s+"
        match = re.search(pattern, line)

        if match:
            # Replace the variable name in the for loop
            for_vars = match.group(1)
            new_for_vars = re.sub(rf"\b{re.escape(var_name)}\b", f"_{var_name}", for_vars)
            new_line = line[: match.start(1)] + new_for_vars + line[match.end(1) :]

            lines[line_idx] = new_line
            file_path.write_text("\n".join(lines), encoding="utf-8")
            return True

    except Exception as e:
        print(f"Error fixing {file_path}:{line_num} {var_name}: {e}", file=sys.stderr)
        return False

    return False


def main():
    print("🔍 Finding unused loop variables...")
    fixes = get_unused_loop_vars()

    print(f"Found {len(fixes)} unused loop variables to fix")

    fixed_count = 0
    error_count = 0

    for file_path_str, line_num, var_name in fixes:
        file_path = Path(file_path_str)

        if fix_loop_variable(file_path, line_num, var_name):
            fixed_count += 1
            print(f"✅ {file_path.name}:{line_num} - {var_name} → _{var_name}")
        else:
            error_count += 1
            print(f"❌ {file_path.name}:{line_num} - Failed to fix {var_name}")

    print("\n📊 Summary:")
    print(f"  Variables fixed: {fixed_count}")
    if error_count > 0:
        print(f"  Errors: {error_count}")


if __name__ == "__main__":
    main()

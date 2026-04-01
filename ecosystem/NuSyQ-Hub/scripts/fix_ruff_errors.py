#!/usr/bin/env python3
"""Automatically fix common ruff errors"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.terminal_output import to_claude, to_tasks


def fix_unused_variable(file_path: Path, line_num: int, var_name: str) -> bool:
    """Fix F841 - unused variable by prefixing with underscore."""
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if line_num > len(lines):
            return False

        # Replace variable name with underscore prefix
        old_line = lines[line_num - 1]
        new_line = old_line.replace(f"{var_name} =", f"_{var_name} =")

        if old_line != new_line:
            lines[line_num - 1] = new_line
            file_path.write_text("".join(lines), encoding="utf-8")
            to_tasks(f"✅ Fixed unused variable {var_name} in {file_path.name}:{line_num}")
            return True

        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def fix_ambiguous_variable(file_path: Path, line_num: int, var_name: str) -> bool:
    """Fix E741 - ambiguous variable name."""
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if line_num > len(lines):
            return False

        # Replace ambiguous single-letter variable
        replacements = {"l": "line", "O": "obj", "I": "idx"}

        new_name = replacements.get(var_name, f"{var_name}_var")
        old_line = lines[line_num - 1]

        # Replace in list comprehension or loop
        new_line = re.sub(rf"\b{var_name}\b", new_name, old_line)

        if old_line != new_line:
            lines[line_num - 1] = new_line
            file_path.write_text("".join(lines), encoding="utf-8")
            to_tasks(f"✅ Fixed ambiguous variable {var_name} → {new_name} in {file_path.name}:{line_num}")
            return True

        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def fix_unused_loop_variable(file_path: Path, line_num: int, var_name: str) -> bool:
    """Fix B007 - unused loop control variable."""
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if line_num > len(lines):
            return False

        old_line = lines[line_num - 1]
        new_line = old_line.replace(f"for {var_name},", f"for _{var_name},")

        if old_line != new_line:
            lines[line_num - 1] = new_line
            file_path.write_text("".join(lines), encoding="utf-8")
            to_tasks(f"✅ Fixed unused loop var {var_name} in {file_path.name}:{line_num}")
            return True

        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Scan and fix ruff errors."""
    import subprocess

    to_claude("🔧 Starting automatic ruff error fixes...")

    # Get ruff output
    result = subprocess.run(
        ["python", "-m", "ruff", "check", ".", "--output-format=json"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    if not result.stdout.strip():
        print("✅ No ruff errors found!")
        return

    import json

    errors = json.loads(result.stdout)

    fixed = 0
    skipped = 0

    for error in errors[:50]:  # Fix first 50 errors
        code = error.get("code")
        file_path = Path(error["filename"])
        line_num = error["location"]["row"]

        # Extract variable name from message
        message = error.get("message", "")

        if code == "F841":
            # Extract variable name
            match = re.search(r"Local variable `(\w+)` is assigned", message)
            if match:
                var_name = match.group(1)
                if fix_unused_variable(file_path, line_num, var_name):
                    fixed += 1
                else:
                    skipped += 1

        elif code == "E741":
            # Extract variable name
            match = re.search(r"Ambiguous variable name: `(\w+)`", message)
            if match:
                var_name = match.group(1)
                if fix_ambiguous_variable(file_path, line_num, var_name):
                    fixed += 1
                else:
                    skipped += 1

        elif code == "B007":
            # Extract variable name
            match = re.search(r"Loop control variable `(\w+)` not used", message)
            if match:
                var_name = match.group(1)
                if fix_unused_loop_variable(file_path, line_num, var_name):
                    fixed += 1
                else:
                    skipped += 1
        else:
            skipped += 1

    print(f"\n{'=' * 70}")
    print("✨ AUTOMATIC FIX RESULTS")
    print(f"{'=' * 70}")
    print(f"\n✅ Fixed: {fixed}")
    print(f"⏭️  Skipped: {skipped}")
    print("\n💡 Run 'ruff check .' to see remaining errors")

    to_claude(f"✅ Auto-fixed {fixed} ruff errors")


if __name__ == "__main__":
    main()

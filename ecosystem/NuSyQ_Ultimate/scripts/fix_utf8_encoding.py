#!/usr/bin/env python3
"""
Systematic UTF-8 Fix - Add UTF-8 wrapper to Python files
Fixes Windows cp1252 encoding issues
"""

import io
import sys
from pathlib import Path

# Fix our own output first
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

UTF8_FIX = """import sys
import io

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
"""


def needs_utf8_fix(file_path: Path) -> bool:
    """Check if file needs UTF-8 fix"""
    try:
        content = file_path.read_text(encoding="utf-8")
        # Already has fix
        if "sys.stdout.buffer, encoding=" in content:
            return False
        # Has print or logger that might output Unicode
        if ("print(" in content or "logger." in content) and "utf-8" not in content:
            return True
        return False
    except (OSError, UnicodeDecodeError) as e:
        print(f"⚠️ Warning: Failed to check file {file_path}: {e}")
        return False


def add_utf8_fix(file_path: Path) -> bool:
    """Add UTF-8 fix to file"""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Find insertion point (after shebang and docstring)
        insert_idx = 0
        in_docstring = False

        for i, line in enumerate(lines):
            if i == 0 and line.startswith("#!"):
                insert_idx = i + 1
                continue
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
                if not in_docstring:
                    insert_idx = i + 1
                    break
            if not in_docstring and line.strip() and not line.startswith("#"):
                insert_idx = i
                break

        # Insert UTF-8 fix
        lines.insert(insert_idx, UTF8_FIX)

        file_path.write_text("\n".join(lines), encoding="utf-8")
        return True
    except (OSError, UnicodeDecodeError, ValueError, TypeError) as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    root = Path(".")

    # Priority files to fix
    priority_files = [
        "scripts/theater_audit.py",
        "scripts/autonomous_self_healer.py",
        "scripts/health_healing_orchestrator.py",
        "scripts/placeholder_investigator.py",
        "scripts/integrated_scanner.py",
    ]

    fixed = 0
    for file_rel in priority_files:
        file_path = root / file_rel
        if file_path.exists() and needs_utf8_fix(file_path):
            if add_utf8_fix(file_path):
                print(f"[OK] Fixed {file_rel}")
                fixed += 1
            else:
                print(f"[FAIL] Could not fix {file_rel}")
        else:
            print(f"[SKIP] {file_rel} (already fixed or doesn't exist)")

    print(f"\nFixed {fixed} files")


if __name__ == "__main__":
    main()

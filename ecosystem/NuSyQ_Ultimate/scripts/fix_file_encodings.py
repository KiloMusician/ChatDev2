#!/usr/bin/env python3
"""
Fix missing encoding parameters in open() calls across the codebase.
This script adds encoding='utf-8' to all file open operations that are missing it.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def find_files_with_encoding_issues(root_dir: Path) -> List[Path]:
    """Find all Python files that might have encoding issues."""
    return list(root_dir.glob("**/*.py"))


def fix_encoding_in_file(file_path: Path) -> Tuple[bool, int]:
    """
    Fix encoding issues in a single file.
    Returns: (was_modified, num_fixes)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"⚠️  Skipping {file_path}: {e}")
        return False, 0

    original_content = content
    fixes_made = 0

    # Pattern 1: open(path, "mode") without encoding
    pattern1 = r'open\(([^,)]+),\s*(["\'])([rwa][bt]?)\2\)'

    def replace_func1(match):
        nonlocal fixes_made
        full_match = match.group(0)

        start_pos = max(0, match.start() - 100)
        end_pos = min(len(content), match.end() + 100)
        context = content[start_pos:end_pos]

        if "encoding" in context[max(0, match.start() - start_pos - 50):match.end() - start_pos + 50]:
            return full_match

        path_arg = match.group(1)
        mode = match.group(3)

        if "def " in content[max(0, match.start() - 20):match.start()]:
            return full_match

        fixes_made += 1
        return f'open({path_arg}, "{mode}", encoding="utf-8")'

    content = re.sub(pattern1, replace_func1, content)

    # Pattern 2: open(path) without mode or encoding
    pattern2 = r'open\(([^,)]+)\)(?!\s*as\s+\w+\s*:)'
    apply_pattern2 = os.environ.get("FIX_ENCODING_APPLY_PATTERN2", "0") == "1"

    def replace_func2(match):
        nonlocal fixes_made
        full_match = match.group(0)

        start_pos = max(0, match.start() - 100)
        end_pos = min(len(content), match.end() + 100)
        context = content[start_pos:end_pos]

        if "encoding" in context[max(0, match.start() - start_pos - 50):match.end() - start_pos + 50]:
            return full_match

        if "def " in content[max(0, match.start() - 20):match.start()]:
            return full_match

        path_arg = match.group(1)
        fixes_made += 1
        return f'open({path_arg}, encoding="utf-8")'

    # Conservative: only apply pattern2 when explicitly enabled
    if apply_pattern2:
        content = re.sub(pattern2, replace_func2, content)

    if content != original_content and fixes_made > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, fixes_made

    return False, 0


def main():
    root_dir = Path(".")
    print("🔍 Scanning for Python files to check for encoding parameters...")

    files = find_files_with_encoding_issues(root_dir)
    print(f"📁 Found {len(files)} Python files to check")

    total_files_modified = 0
    total_fixes = 0

    for file_path in files:
        # Skip virtualenv and hidden directories
        if any(part.startswith('.') or part == '__pycache__' for part in file_path.parts):
            continue
        was_modified, num_fixes = fix_encoding_in_file(file_path)
        if was_modified:
            total_files_modified += 1
            total_fixes += num_fixes
            print(f"✅ Fixed {num_fixes} encoding issues in {file_path}")

    print("\n📊 Summary:")
    print(f"   Files modified: {total_files_modified}")
    print(f"   Total fixes: {total_fixes}")
    print(f"   Files scanned: {len(files)}")

    if total_fixes > 0:
        print("\n✨ Encoding issues fixed successfully!")
        print("💡 Recommendation: Run linters and tests to verify changes")
    else:
        print("\n✨ No encoding issues found!")


if __name__ == "__main__":
    main()

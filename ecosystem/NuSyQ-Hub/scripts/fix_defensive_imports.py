#!/usr/bin/env python3
"""Automated Import Pattern Modernizer
Fixes defensive import patterns across the codebase
"""

import re
from pathlib import Path


def fix_defensive_imports(file_path: Path) -> tuple[bool, int]:
    """Fix defensive import patterns in a single file"""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content
        fixes_made = 0

        # Pattern 1: Double try/except for timeout_config
        pattern1 = re.compile(
            r'try:\s*\n\s*from src\.utils\.timeout_config import ([^\n]+)\n\s*except ImportError:\s*\n\s*try:\s*\n\s*from \.\.utils\.timeout_config import \1\s*\n\s*except ImportError:\s*\n(?:\s*def [^\n]+\([^\)]*\)[^\n]*:\s*\n(?:\s*"""[^"]*"""\s*\n)?\s*return [^\n]+\s*\n)?',
            re.MULTILINE,
        )
        content = pattern1.sub(r"from src.utils.timeout_config import \1\n", content)
        if content != original_content:
            fixes_made += len(pattern1.findall(original_content))

        # Pattern 2: Simple try/except with fallback
        pattern2 = re.compile(
            r"try:\s*\n\s*from (src\.[^\s]+) import ([^\n]+)\n\s*except ImportError:\s*\n\s*(?:try:\s*\n\s*from (\.[^\s]+) import \2\s*\n\s*except ImportError:\s*\n\s*)?(?:.*?(?=\n\n|\nclass |\ndef |\nimport ))",
            re.MULTILINE | re.DOTALL,
        )

        def replace_import(match):
            module_path = match.group(1)
            imports = match.group(2)
            return f"from {module_path} import {imports}\n"

        new_content = pattern2.sub(replace_import, content)
        if new_content != content:
            fixes_made += len(pattern2.findall(content))
            content = new_content

        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return True, fixes_made

        return False, 0

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False, 0


def main():
    """Fix all defensive imports in src/"""
    repo_root = Path(__file__).parent.parent
    src_dir = repo_root / "src"

    if not src_dir.exists():
        print(f"❌ src/ directory not found at {src_dir}")
        return

    print("🔧 Automated Import Pattern Modernizer")
    print(f"📁 Scanning: {src_dir}")
    print()

    files_fixed = 0
    total_fixes = 0

    # Find all Python files with defensive imports
    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        fixed, count = fix_defensive_imports(py_file)
        if fixed:
            files_fixed += 1
            total_fixes += count
            print(f"✅ Fixed {count} patterns in {py_file.relative_to(repo_root)}")

    print()
    print("📊 Summary:")
    print(f"   Files modified: {files_fixed}")
    print(f"   Total fixes: {total_fixes}")
    print()
    print("✅ Import modernization complete!")


if __name__ == "__main__":
    main()

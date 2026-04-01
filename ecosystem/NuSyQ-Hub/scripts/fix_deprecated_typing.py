"""Fix deprecated typing imports (Dict, List, etc.) to modern syntax.
Automatically updates imports from typing.Dict/List to built-in dict/list.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def fix_file_typing(file_path: Path) -> bool:
    """Fix deprecated typing imports in a single file.

    Args:
        file_path: Path to the Python file

    Returns:
        True if file was modified, False otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Pattern 1: from typing import Dict, List, etc.
        # Replace with individual items removed if they're Dict/List
        typing_import_pattern = r"from typing import ([^\n]+)"

        def replace_typing_import(match):
            imports = match.group(1)
            items = [item.strip() for item in imports.split(",")]

            # Filter out deprecated types
            deprecated = {"Dict", "List", "Set", "Tuple", "FrozenSet"}
            kept_items = [item for item in items if item not in deprecated]

            if not kept_items:
                # If all items were deprecated, remove the import line
                return ""
            else:
                # Keep remaining items
                return f"from typing import {', '.join(kept_items)}"

        content = re.sub(typing_import_pattern, replace_typing_import, content)

        # Pattern 2: Replace Dict[ with dict[
        content = re.sub(r"\bDict\[", "dict[", content)

        # Pattern 3: Replace List[ with list[
        content = re.sub(r"\bList\[", "list[", content)

        # Pattern 4: Replace Set[ with set[
        content = re.sub(r"\bSet\[", "set[", content)

        # Pattern 5: Replace Tuple[ with tuple[
        content = re.sub(r"\bTuple\[", "tuple[", content)

        # Pattern 6: Replace FrozenSet[ with frozenset[
        content = re.sub(r"\bFrozenSet\[", "frozenset[", content)

        # Clean up empty import lines
        content = re.sub(r"\nfrom typing import\s*\n", "\n", content)

        # Write back if changed
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main() -> int:
    """Main execution function."""
    print("🔧 Fixing deprecated typing imports")
    print("=" * 60)

    repo_root = Path(__file__).parent.parent
    src_dir = repo_root / "src"

    # Find all Python files
    py_files = list(src_dir.rglob("*.py"))

    fixed_count = 0
    for py_file in py_files:
        if fix_file_typing(py_file):
            print(f"✅ Fixed: {py_file.relative_to(repo_root)}")
            fixed_count += 1

    print("\n" + "=" * 60)
    print(f"✨ Complete! Fixed {fixed_count} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())

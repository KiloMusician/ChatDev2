#!/usr/bin/env python3
"""Fix F401 (unused imports) and F821 (undefined names)"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.terminal_output import to_copilot, to_tasks


def fix_unused_imports(file_path: Path) -> int:
    """Remove unused imports from file."""
    try:
        # Use ruff to auto-fix unused imports
        result = subprocess.run(
            ["python", "-m", "ruff", "check", "--select=F401", "--fix", str(file_path)],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

        if "fixed" in result.stdout.lower() or result.returncode == 0:
            to_tasks(f"✅ Fixed unused imports in {file_path.name}")
            return 1
        return 0

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return 0


def add_missing_imports(file_path: Path, undefined_names: list[str]) -> int:
    """Add common missing imports."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)

        # Common imports for undefined names
        import_map = {
            "Path": "from pathlib import Path",
            "datetime": "from datetime import datetime",
            "timedelta": "from datetime import timedelta",
            "Dict": "from typing import Dict",
            "List": "from typing import List",
            "Optional": "from typing import Optional",
            "Any": "from typing import Any",
            "Union": "from typing import Union",
            "Callable": "from typing import Callable",
            "asyncio": "import asyncio",
            "json": "import json",
            "os": "import os",
            "sys": "import sys",
        }

        added = []
        for name in undefined_names:
            if name in import_map and import_map[name] not in content:
                # Find where to insert import (after existing imports or at top)
                import_line = import_map[name] + "\n"

                # Find last import line
                last_import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith(("import ", "from ")):
                        last_import_idx = i

                if last_import_idx > 0:
                    lines.insert(last_import_idx + 1, import_line)
                else:
                    # Add after docstring if present
                    insert_idx = 0
                    if lines and lines[0].strip().startswith(('"""', "'''")):
                        # Find end of docstring
                        for i in range(1, len(lines)):
                            if lines[i].strip().endswith(('"""', "'''")):
                                insert_idx = i + 1
                                break
                    lines.insert(insert_idx, import_line)

                added.append(name)

        if added:
            file_path.write_text("".join(lines), encoding="utf-8")
            to_tasks(f"✅ Added imports for {', '.join(added)} in {file_path.name}")
            return len(added)

        return 0

    except Exception as e:
        print(f"Error adding imports to {file_path}: {e}")
        return 0


def main():
    """Fix import-related errors."""
    import json

    to_copilot("🔧 Fixing import errors (F401, F821)...")

    # Get ruff output for import errors
    result = subprocess.run(
        ["python", "-m", "ruff", "check", ".", "--select=F401,F821,F541", "--output-format=json"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    if not result.stdout.strip():
        print("✅ No import errors found!")
        return

    errors = json.loads(result.stdout)

    # Group by file
    files_with_f401 = set()
    files_with_f821 = {}

    for error in errors:
        code = error.get("code")
        file_path = Path(error["filename"])

        if code == "F401":
            files_with_f401.add(file_path)
        elif code == "F821":
            # Extract undefined name
            message = error.get("message", "")
            match = re.search(r"Undefined name `(\w+)`", message)
            if match:
                name = match.group(1)
                if file_path not in files_with_f821:
                    files_with_f821[file_path] = []
                files_with_f821[file_path].append(name)

    fixed_f401 = 0
    fixed_f821 = 0

    # Fix F401 (unused imports)
    for file_path in files_with_f401:
        fixed_f401 += fix_unused_imports(file_path)

    # Fix F821 (undefined names) by adding imports
    for file_path, names in files_with_f821.items():
        fixed_f821 += add_missing_imports(file_path, names)

    print(f"\n{'=' * 70}")
    print("✨ IMPORT FIX RESULTS")
    print(f"{'=' * 70}")
    print(f"\n✅ Fixed F401 (unused imports): {fixed_f401}")
    print(f"✅ Fixed F821 (undefined names): {fixed_f821}")

    to_copilot(f"✅ Fixed {fixed_f401 + fixed_f821} import errors")


if __name__ == "__main__":
    main()

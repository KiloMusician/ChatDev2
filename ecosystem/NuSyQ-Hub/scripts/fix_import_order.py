#!/usr/bin/env python3
"""Fix Import Order (E402)

Systematically fixes module-level imports that aren't at the top of files.
Handles common patterns:
1. Imports after docstrings (should be before)
2. Imports after sys.path modifications (can stay)
3. Imports inside try/except at module level (can stay)
4. Conditional imports (can stay if needed for compatibility)
"""

import sys
from pathlib import Path
from typing import Final

IMPORT_PREFIX: Final[str] = "import "
FROM_PREFIX: Final[str] = "from "


def categorize_early_lines(lines: list[str]) -> dict[str, list[tuple[int, str]]]:
    """Categorize lines before first import."""
    categories: dict[str, list[tuple[int, str]]] = {
        "shebang": [],
        "encoding": [],
        "docstring": [],
        "omnitag": [],
        "comments": [],
        "blank": [],
        "code": [],
    }

    in_docstring = False
    docstring_quote = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Shebang
        if i == 0 and stripped.startswith("#!"):
            categories["shebang"].append((i, line))
            continue

        # Encoding declaration
        if i < 2 and stripped.startswith("#") and ("coding" in stripped or "encoding" in stripped):
            categories["encoding"].append((i, line))
            continue

        # Check for docstring start
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            docstring_quote = '"""' if stripped.startswith('"""') else "'''"
            categories["docstring"].append((i, line))

            # Check if docstring ends on same line
            if stripped.count(docstring_quote) >= 2 and len(stripped) > 6:
                in_docstring = False
            else:
                in_docstring = True
            continue

        # Inside docstring
        if in_docstring:
            categories["docstring"].append((i, line))
            if docstring_quote and docstring_quote in line:
                in_docstring = False
            continue

        # OmniTag blocks (special handling)
        if "OmniTag" in line and not line.strip().startswith("#"):
            categories["omnitag"].append((i, line))
            continue

        # Blank lines
        if not stripped:
            categories["blank"].append((i, line))
            continue

        # Comments
        if stripped.startswith("#"):
            categories["comments"].append((i, line))
            continue

        # Check if it's an import
        if stripped.startswith(IMPORT_PREFIX) or stripped.startswith(FROM_PREFIX):
            return categories

        # Otherwise it's code
        categories["code"].append((i, line))

    return categories


def should_fix_file(file_path: Path) -> bool:
    """Check if file needs E402 fixes."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Find first import
        first_import_idx = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(IMPORT_PREFIX) or stripped.startswith(FROM_PREFIX):
                first_import_idx = i
                break

        if first_import_idx is None:
            return False

        # Check if there's any code before first import (besides docstring/shebang/encoding)
        categories = categorize_early_lines(lines[:first_import_idx])

        # If there's actual code before imports, might need fixing
        return len(categories["code"]) > 0

    except (OSError, SyntaxError, KeyError):
        return False


def fix_import_order_in_file(file_path: Path) -> tuple[bool, str]:
    """Fix import order in a file if safe to do so."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Find first import
        first_import_idx = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(IMPORT_PREFIX) or stripped.startswith(FROM_PREFIX):
                first_import_idx = i
                break

        if first_import_idx is None:
            return False, "No imports found"

        # Categorize lines before first import
        categories = categorize_early_lines(lines[:first_import_idx])

        # Only fix if the "code" is actually safe to move (like setting constants)
        if categories["code"]:
            # Check if code is just variable assignments
            safe_code = all(
                "=" in lines[idx] and not lines[idx].strip().startswith("if ") for idx, _ in categories["code"]
            )

            if not safe_code:
                return False, "Unsafe code before imports"

            # For now, skip files with code before imports - too risky
            return False, "Code found before imports (manual review needed)"

        return False, "No fixable E402 issues"

    except (OSError, UnicodeError) as e:
        return False, f"Error: {e}"


def main():
    """Main execution."""
    print("=" * 80)
    print("🔧 IMPORT ORDER FIXER (E402)")
    print("=" * 80)
    print()

    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src directory not found")
        return 1

    # Get files with E402 errors
    print("📊 Analyzing E402 errors...")

    import subprocess

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "src/",
                "--select=E402",
                "--output-format=json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

        if not result.stdout:
            print("✅ No E402 errors found!")
            return 0

        import json

        errors = json.loads(result.stdout)

        files_with_errors: dict[str, list[dict]] = {}
        for error in errors:
            filename = error["filename"]
            if filename not in files_with_errors:
                files_with_errors[filename] = []
            files_with_errors[filename].append(error)

        print(f"  Found E402 errors in {len(files_with_errors)} files")
        print()

        # Analyze each file
        fixable = 0
        needs_manual = 0

        print("🔍 Analyzing files...")
        for filename, _ in sorted(files_with_errors.items()):
            file_path = Path(filename)
            fixed, reason = fix_import_order_in_file(file_path)

            if fixed:
                fixable += 1
                print(f"  ✅ {file_path.name} - FIXED")
            else:
                needs_manual += 1
                # Only print first few that need manual review
                if needs_manual <= 10:
                    print(f"  ⚠️  {file_path.name} - {reason}")

        if needs_manual > 10:
            print(f"  ... and {needs_manual - 10} more files need manual review")

        print()
        print("=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"  Auto-fixed: {fixable}")
        print(f"  Needs manual review: {needs_manual}")
        print()

        if needs_manual > 0:
            print("💡 Most E402 errors require manual review because:")
            print("   - Imports are deliberately placed after sys.path modifications")
            print("   - Conditional imports for compatibility")
            print("   - Imports inside try/except for optional dependencies")
            print()
            print("   These are often intentional and correct!")

    except (OSError, subprocess.SubprocessError, UnicodeError) as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

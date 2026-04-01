#!/usr/bin/env python3
"""Remove unnecessary type:ignore comments and add proper type hints.

This script identifies type:ignore comments that can be replaced with:
1. Proper type annotations
2. TYPE_CHECKING imports
3. Optional type hints
4. Union types where appropriate

Usage:
    python scripts/improve_type_hints.py [--file FILE] [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


# Patterns for type:ignore comments that can be improved
IMPROVABLE_PATTERNS = [
    # Pattern: Variable assignments that should use Optional or proper types
    (
        r"(\w+)\s*=\s*None\s*#\s*type:\s*ignore",
        r"\1: Any = None  # Consider: Optional[TypeName]",
        "Add proper Optional type hint",
    ),
    # Pattern: Import statements with missing stubs
    (
        r"(\s+from .+ import .+)\s*#\s*type:\s*ignore(?!\[)",
        r"\1  # type: ignore[import]  # Missing type stubs",
        "Specify ignore reason",
    ),
]


def improve_file_types(file_path: Path, dry_run: bool = False) -> dict[str, Any]:
    """Improve type hints in a single file.

    Args:
        file_path: Path to Python file
        dry_run: If True, only report changes without modifying file

    Returns:
        dict with improvements made
    """
    result = {"file": str(file_path), "improvements": [], "errors": []}

    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Apply improvement patterns
        for pattern, replacement, description in IMPROVABLE_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                result["improvements"].append(
                    {
                        "line": content[: match.start()].count("\n") + 1,
                        "type": description,
                        "original": match.group(0),
                        "replacement": re.sub(pattern, replacement, match.group(0)),
                    }
                )

            content = re.sub(pattern, replacement, content)

        # Write back if changes were made
        if content != original_content and not dry_run:
            file_path.write_text(content, encoding="utf-8")
            logger.info("type_hints", f"Updated {file_path}")

    except Exception as e:
        result["errors"].append(str(e))
        logger.error("type_hints", f"Failed to process {file_path}: {e}")

    return result


def scan_directory(directory: Path, dry_run: bool = False) -> dict[str, Any]:
    """Scan directory for type hint improvements.

    Args:
        directory: Directory to scan
        dry_run: If True, only report changes without modifying files

    Returns:
        dict with scan results
    """
    results = {"files_scanned": 0, "files_improved": 0, "total_improvements": 0, "details": []}

    for py_file in directory.rglob("*.py"):
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue

        results["files_scanned"] += 1
        file_result = improve_file_types(py_file, dry_run=dry_run)

        if file_result["improvements"]:
            results["files_improved"] += 1
            results["total_improvements"] += len(file_result["improvements"])
            results["details"].append(file_result)

    return results


def main():
    """Execute type hint improvements."""
    parser = argparse.ArgumentParser(description="Improve type hints in Python files")
    parser.add_argument("--file", type=Path, help="Specific file to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed")
    args = parser.parse_args()

    print("=" * 60)
    print("TYPE HINT IMPROVEMENT TOOL")
    print("=" * 60)
    if args.dry_run:
        print("🔍 DRY RUN MODE")
    print()

    if args.file:
        result = improve_file_types(args.file, dry_run=args.dry_run)
        print(f"File: {result['file']}")
        print(f"Improvements: {len(result['improvements'])}")
        for imp in result["improvements"]:
            print(f"  Line {imp['line']}: {imp['type']}")
            print(f"    {imp['original']}")
            print(f"    → {imp['replacement']}")
        if result["errors"]:
            print(f"⚠️ Errors: {len(result['errors'])}")
            for err in result["errors"]:
                print(f"  {err}")
    else:
        results = scan_directory(Path("src"), dry_run=args.dry_run)
        print(f"Files scanned: {results['files_scanned']}")
        print(f"Files improved: {results['files_improved']}")
        print(f"Total improvements: {results['total_improvements']}")
        print()

        if results["details"]:
            print("Details:")
            for detail in results["details"][:10]:  # Show first 10
                print(f"\n{detail['file']}:")
                for imp in detail["improvements"][:3]:  # Show first 3 per file
                    print(f"  Line {imp['line']}: {imp['type']}")

            if len(results["details"]) > 10:
                print(f"\n... and {len(results['details']) - 10} more files")

    print()
    if args.dry_run:
        print("✅ Dry run complete - use without --dry-run to apply changes")
    else:
        print("✅ Type hint improvements complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())

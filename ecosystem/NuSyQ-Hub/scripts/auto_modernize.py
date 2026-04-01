#!/usr/bin/env python3
"""Auto-Modernize - Fix common code patterns

Automatically fixes:
1. Bare except clauses (except: -> except Exception:)
2. Old-style string formatting (limited scope)

Run with --dry-run to preview changes.
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def fix_bare_except(content: str) -> tuple[str, int]:
    """Fix bare except clauses."""
    pattern = r"^(\s*)except\s*:(.*)$"
    replacement = r"\1except Exception:\2"

    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)

    return new_content, count


def modernize_file(file_path: Path, dry_run: bool = False) -> dict[str, int]:
    """Modernize a single file."""
    changes = {"bare_except": 0}

    try:
        content = file_path.read_text(encoding="utf-8")
        original = content

        # Fix bare except
        content, count = fix_bare_except(content)
        changes["bare_except"] = count

        # Write if changes and not dry run
        if content != original and not dry_run:
            file_path.write_text(content, encoding="utf-8")

    except Exception as e:
        print(f"  ⚠️ Error processing {file_path}: {e}")

    return changes


def main() -> int:
    """Auto-modernize codebase."""
    parser = argparse.ArgumentParser(description="Auto-modernize Python code")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--path", type=str, default="src", help="Path to scan (default: src)")
    args = parser.parse_args()

    mode = "DRY RUN" if args.dry_run else "APPLY"
    print(f"🔧 AUTO-MODERNIZE ({mode})")
    print("=" * 60)

    scan_dir = PROJECT_ROOT / args.path
    total_files = 0
    files_modified = 0
    total_changes = {"bare_except": 0}

    for py_file in scan_dir.rglob("*.py"):
        total_files += 1
        changes = modernize_file(py_file, dry_run=args.dry_run)

        if any(changes.values()):
            files_modified += 1
            rel_path = py_file.relative_to(PROJECT_ROOT)

            if args.dry_run:
                print(f"\n📝 Would modify: {rel_path}")
            else:
                print(f"\n✅ Modified: {rel_path}")

            for change_type, count in changes.items():
                if count > 0:
                    total_changes[change_type] += count
                    print(f"   - {change_type}: {count} fixes")

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print(f"   Files scanned: {total_files}")
    print(f"   Files {'would be ' if args.dry_run else ''}modified: {files_modified}")

    for change_type, count in total_changes.items():
        if count > 0:
            print(f"   {change_type}: {count} fixes")

    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes")

    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

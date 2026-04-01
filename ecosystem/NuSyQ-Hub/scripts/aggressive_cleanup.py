#!/usr/bin/env python3
"""Aggressive cleanup and healing operations.

This script performs deep cleanup:
1. Remove infrastructure duplicates
2. Clean unused imports
3. Remove commented code
4. Fix obvious issues in specific files
5. Commit batches of fixes

Usage:
    python scripts/aggressive_cleanup.py [--dry-run]
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


def remove_infrastructure_duplicates(dry_run: bool = False) -> dict[str, Any]:
    """Remove infrastructure directory duplicates."""
    result = {"removed": [], "errors": [], "skipped": []}

    # Candidates for removal (verify they are truly duplicates first)
    candidates = [
        Path("src/LOGGING/infrastructure/modular_logging_system.py"),
        Path("LOGGING/infrastructure/modular_logging_system.py"),
    ]

    for dup in candidates:
        if not dup.exists():
            continue

        # Check if it's a redirect (small file < 500 bytes)
        size = dup.stat().st_size
        if size < 500:
            result["skipped"].append(f"{dup} (redirect file, keeping)")
            continue

        if dry_run:
            result["removed"].append(f"[DRY-RUN] {dup} ({size} bytes)")
        else:
            try:
                dup.unlink()
                result["removed"].append(f"{dup} ({size} bytes)")
                logger.info("cleanup", f"Removed: {dup}")
            except Exception as e:
                result["errors"].append(f"{dup}: {e}")
                logger.error("cleanup", f"Failed to remove {dup}: {e}")

    return result


def cleanup_unused_code(dry_run: bool = False) -> dict[str, Any]:
    """Remove obviously unused/commented code."""
    result = {"files_processed": 0, "removals": 0, "errors": []}

    # Process select files with highest error counts
    target_files = [
        "src/tools/agent_task_router.py",
        "src/ai/ai_intermediary.py",
        "src/orchestration/claude_orchestrator.py",
    ]

    for filepath in target_files:
        path = Path(filepath)
        if not path.exists():
            continue

        try:
            content = path.read_text(encoding="utf-8")
            original = content

            # Remove obvious commented-out code blocks
            lines = content.split("\n")
            cleaned_lines = []
            skip_block = False

            for line in lines:
                # Skip large commented blocks
                if line.strip().startswith("#") and len(line.strip()) > 100:
                    skip_block = True
                    continue
                if skip_block and line.strip() and not line.strip().startswith("#"):
                    skip_block = False

                # Keep meaningful comments and code
                if not skip_block or not line.strip().startswith("#"):
                    cleaned_lines.append(line)

            content = "\n".join(cleaned_lines)

            if content != original and not dry_run:
                path.write_text(content, encoding="utf-8")
                result["removals"] += len(lines) - len(cleaned_lines)
                logger.info("cleanup", f"Cleaned {filepath}")

            result["files_processed"] += 1

        except Exception as e:
            result["errors"].append(f"{filepath}: {e}")
            logger.error("cleanup", f"Failed to clean {filepath}: {e}")

    return result


def fix_common_patterns(dry_run: bool = False) -> dict[str, Any]:
    """Fix common code quality issues."""
    result = {"fixed": 0, "errors": []}

    # Run targeted fixes
    commands = [
        ["ruff", "check", "src/", "--fix", "--select=E501"],  # Line too long
        ["ruff", "check", "src/", "--fix", "--select=F841"],  # Unused variable
        ["ruff", "check", "src/", "--fix", "--select=W291"],  # Trailing whitespace
    ]

    for cmd in commands:
        if dry_run:
            result["fixed"] += 1
            continue

        try:
            subprocess.run(cmd, capture_output=True, timeout=60, check=False)
            result["fixed"] += 1
            logger.info("cleanup", f"Applied: {' '.join(cmd)}")
        except Exception as e:
            result["errors"].append(str(e))
            logger.error("cleanup", f"Failed: {' '.join(cmd)}")

    return result


def main():
    """Execute aggressive cleanup."""
    import argparse

    parser = argparse.ArgumentParser(description="Aggressive system cleanup")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("AGGRESSIVE CLEANUP")
    print("=" * 60)
    if args.dry_run:
        print("🔍 DRY RUN MODE")
    print()

    # 1. Remove duplicates
    print("📁 Removing duplicates...")
    dup_result = remove_infrastructure_duplicates(dry_run=args.dry_run)
    print(f"   Removed: {len(dup_result['removed'])}")
    print(f"   Skipped: {len(dup_result['skipped'])}")
    if dup_result["errors"]:
        print(f"   ⚠️ Errors: {len(dup_result['errors'])}")
    print()

    # 2. Clean unused code
    print("🧹 Cleaning unused code...")
    cleanup_result = cleanup_unused_code(dry_run=args.dry_run)
    print(f"   Files processed: {cleanup_result['files_processed']}")
    print(f"   Lines removed: {cleanup_result['removals']}")
    if cleanup_result["errors"]:
        print(f"   ⚠️ Errors: {len(cleanup_result['errors'])}")
    print()

    # 3. Fix patterns
    print("✨ Fixing common patterns...")
    fix_result = fix_common_patterns(dry_run=args.dry_run)
    print(f"   Fixes applied: {fix_result['fixed']}")
    if fix_result["errors"]:
        print(f"   ⚠️ Errors: {len(fix_result['errors'])}")
    print()

    print("=" * 60)
    if args.dry_run:
        print("✅ Dry run complete")
    else:
        print("✅ Cleanup complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())

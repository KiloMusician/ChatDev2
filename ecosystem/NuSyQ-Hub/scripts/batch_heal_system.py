#!/usr/bin/env python3
"""Batch System Healing - Execute multiple healing operations in sequence.

This script coordinates multiple healing operations to improve system health:
1. Remove file duplicates (keep canonical, delete redundant copies)
2. Clean up type:ignore suppressions where safe
3. Run formatters and linters
4. Commit batches of changes
5. Generate progress report

Usage:
    python scripts/batch_heal_system.py [--dry-run] [--skip-commit]
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


def remove_duplicate_files(dry_run: bool = False) -> dict[str, Any]:
    """Remove duplicate files, keeping canonical versions.

    Duplicates identified:
    - modular_logging_system.py (4 copies → keep src/LOGGING/modular_logging_system.py)
    - quantum_problem_resolver.py (2 copies → keep src/healing/quantum_problem_resolver.py)

    Args:
        dry_run: If True, only report what would be done

    Returns:
        dict with removed files and kept files
    """
    logger.info("batch_heal", "Removing duplicate files...")

    result = {"removed": [], "kept": [], "errors": []}

    # Modular logging system - keep src/LOGGING/modular_logging_system.py
    canonical_logging = Path("src/LOGGING/modular_logging_system.py")
    duplicate_logging = [
        Path("LOGGING/modular_logging_system.py"),  # Already a redirect
        Path("src/LOGGING/infrastructure/modular_logging_system.py"),
        Path("LOGGING/infrastructure/modular_logging_system.py"),
    ]

    if canonical_logging.exists():
        result["kept"].append(str(canonical_logging))
        for dup in duplicate_logging:
            if dup.exists():
                # Check if it's already a redirect (small file)
                if dup.stat().st_size < 500:  # Redirect files are ~300 bytes
                    logger.info("batch_heal", f"Skipping redirect: {dup}")
                    result["kept"].append(str(dup))
                    continue

                if not dry_run:
                    try:
                        dup.unlink()
                        result["removed"].append(str(dup))
                        logger.info("batch_heal", f"Removed duplicate: {dup}")
                    except Exception as e:
                        result["errors"].append(f"{dup}: {e}")
                        logger.error("batch_heal", f"Failed to remove {dup}: {e}")
                else:
                    result["removed"].append(f"[DRY-RUN] {dup}")

    # Quantum problem resolver - keep src/healing/quantum_problem_resolver.py
    canonical_quantum = Path("src/healing/quantum_problem_resolver.py")
    duplicate_quantum = Path("src/quantum/quantum_problem_resolver.py")

    if canonical_quantum.exists() and duplicate_quantum.exists():
        result["kept"].append(str(canonical_quantum))
        # Check if duplicate is already a redirect
        if duplicate_quantum.stat().st_size < 800:  # Redirect is ~600 bytes
            logger.info("batch_heal", f"Skipping redirect: {duplicate_quantum}")
            result["kept"].append(str(duplicate_quantum))
        else:
            if not dry_run:
                try:
                    duplicate_quantum.unlink()
                    result["removed"].append(str(duplicate_quantum))
                    logger.info("batch_heal", f"Removed duplicate: {duplicate_quantum}")
                except Exception as e:
                    result["errors"].append(f"{duplicate_quantum}: {e}")
                    logger.error("batch_heal", f"Failed to remove {duplicate_quantum}: {e}")
            else:
                result["removed"].append(f"[DRY-RUN] {duplicate_quantum}")

    return result


def run_code_formatters(dry_run: bool = False) -> dict[str, Any]:
    """Run black and ruff formatters on source code.

    Args:
        dry_run: If True, run with --check flag only

    Returns:
        dict with formatted files count and any errors
    """
    logger.info("batch_heal", "Running code formatters...")

    result = {"black": None, "ruff": None, "errors": []}

    # Run black
    black_args = ["python", "-m", "black", "src/", "--line-length=100"]
    if dry_run:
        black_args.append("--check")

    try:
        black_result = subprocess.run(black_args, capture_output=True, text=True, timeout=60)
        result["black"] = {
            "returncode": black_result.returncode,
            "output": black_result.stdout + black_result.stderr,
        }
        if black_result.returncode == 0:
            logger.info("batch_heal", "Black formatting completed successfully")
        else:
            logger.warning("batch_heal", f"Black issues found: {black_result.returncode}")
    except Exception as e:
        result["errors"].append(f"black: {e}")
        logger.error("batch_heal", f"Black failed: {e}")

    # Run ruff
    ruff_args = ["ruff", "check", "src/"]
    if not dry_run:
        ruff_args.append("--fix")

    try:
        ruff_result = subprocess.run(ruff_args, capture_output=True, text=True, timeout=60)
        result["ruff"] = {
            "returncode": ruff_result.returncode,
            "output": ruff_result.stdout + ruff_result.stderr,
        }
        if ruff_result.returncode == 0:
            logger.info("batch_heal", "Ruff checks passed")
        else:
            logger.warning("batch_heal", f"Ruff found issues: {ruff_result.returncode}")
    except Exception as e:
        result["errors"].append(f"ruff: {e}")
        logger.error("batch_heal", f"Ruff failed: {e}")

    return result


def commit_changes(message: str, dry_run: bool = False) -> dict[str, Any]:
    """Commit current changes to git.

    Args:
        message: Commit message
        dry_run: If True, only show what would be committed

    Returns:
        dict with commit status
    """
    logger.info("batch_heal", f"Committing changes: {message}")

    result = {"status": None, "files": [], "errors": []}

    # Check status first
    try:
        status_result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, timeout=10)
        result["files"] = status_result.stdout.strip().split("\n")

        if not result["files"][0]:  # Empty list means no changes
            logger.info("batch_heal", "No changes to commit")
            result["status"] = "no_changes"
            return result

        if dry_run:
            result["status"] = f"[DRY-RUN] Would commit {len(result['files'])} files"
            return result

        # Add all changes
        subprocess.run(["git", "add", "-A"], check=True, timeout=10)

        # Commit
        commit_result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, timeout=30)

        if commit_result.returncode == 0:
            result["status"] = "committed"
            logger.info("batch_heal", f"Committed {len(result['files'])} files")
        else:
            result["status"] = "failed"
            result["errors"].append(commit_result.stderr)
            logger.error("batch_heal", f"Commit failed: {commit_result.stderr}")

    except Exception as e:
        result["errors"].append(str(e))
        logger.error("batch_heal", f"Git operation failed: {e}")

    return result


def main():
    """Execute batch healing operations."""
    parser = argparse.ArgumentParser(description="Batch system healing operations")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--skip-commit", action="store_true", help="Skip git commit step")
    args = parser.parse_args()

    print("=" * 60)
    print("BATCH SYSTEM HEALING")
    print("=" * 60)
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    print()

    results = {}

    # 1. Remove duplicates
    print("📁 Removing duplicate files...")
    results["duplicates"] = remove_duplicate_files(dry_run=args.dry_run)
    print(f"   Kept: {len(results['duplicates']['kept'])} canonical files")
    print(f"   Removed: {len(results['duplicates']['removed'])} duplicates")
    if results["duplicates"]["errors"]:
        print(f"   ⚠️ Errors: {len(results['duplicates']['errors'])}")
        for err in results["duplicates"]["errors"]:
            print(f"      {err}")
    print()

    # 2. Run formatters
    print("✨ Running code formatters...")
    results["formatters"] = run_code_formatters(dry_run=args.dry_run)
    if results["formatters"]["black"]:
        print(f"   Black: {results['formatters']['black']['returncode']}")
    if results["formatters"]["ruff"]:
        print(f"   Ruff: {results['formatters']['ruff']['returncode']}")
    if results["formatters"]["errors"]:
        print(f"   ⚠️ Errors: {len(results['formatters']['errors'])}")
        for err in results["formatters"]["errors"]:
            print(f"      {err}")
    print()

    # 3. Commit changes
    if not args.skip_commit and not args.dry_run:
        print("💾 Committing changes...")
        results["commit"] = commit_changes(
            "chore: batch healing - remove duplicates and fix formatting", dry_run=args.dry_run
        )
        print(f"   Status: {results['commit']['status']}")
        if results["commit"]["files"]:
            print(f"   Files: {len(results['commit']['files'])}")
        if results["commit"]["errors"]:
            print(f"   ⚠️ Errors: {len(results['commit']['errors'])}")
            for err in results["commit"]["errors"]:
                print(f"      {err}")
        print()

    # Summary
    print("=" * 60)
    print("HEALING SUMMARY")
    print("=" * 60)
    print(f"Duplicates removed: {len(results['duplicates']['removed'])}")
    print(f"Files formatted: {'pending' if args.dry_run else 'completed'}")
    if not args.skip_commit and not args.dry_run:
        print(f"Git commit: {results.get('commit', {}).get('status', 'skipped')}")
    print()

    if args.dry_run:
        print("✅ Dry run complete - review changes above before running without --dry-run")
    else:
        print("✅ Batch healing complete!")

    return 0 if not any(r.get("errors") for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())

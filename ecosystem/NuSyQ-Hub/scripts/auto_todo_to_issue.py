#!/usr/bin/env python3
"""Automated TODO-to-Issue conversion runner.

Automatically scans for TODOs, converts them to GitHub issues, and tracks
created issues. Can be run as a scheduled task or on-demand.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add scripts to path for todo_to_issue import
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="🤖 %(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_issue_tracker(tracker_path: Path) -> dict:
    """Load existing issue tracker to avoid duplicates."""
    if tracker_path.exists():
        try:
            with open(tracker_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load tracker: {e}")
            return {}
    return {}


def save_issue_tracker(tracker: dict, tracker_path: Path) -> None:
    """Save issue tracker."""
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tracker_path, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=2)
    logger.info(f"💾 Tracker saved: {tracker_path}")


def scan_and_convert_todos(
    dry_run: bool = False,
    max_issues: int | None = None,
    priority_filter: str | None = None,
) -> int:
    """Scan for TODOs and convert to GitHub issues.

    Args:
        dry_run: If True, scan but don't create issues
        max_issues: Maximum number of issues to create (None = unlimited)
        priority_filter: Only create issues with this priority (high/medium/low)

    Returns:
        Number of issues created (or would be created in dry run)
    """
    try:
        # Import todo_to_issue module
        import todo_to_issue

        logger.info("🔍 Scanning codebase for TODO comments...")

        # Get project root
        project_root = Path(__file__).parent.parent

        # Load existing tracker
        tracker_path = project_root / "state" / "todo_issue_tracker.json"
        tracker = load_issue_tracker(tracker_path)

        # Scan for todos
        scanner = todo_to_issue.TodoScanner(project_root)
        todos = scanner.scan()

        logger.info(f"📋 Found {len(todos)} TODO items")

        # Filter already tracked
        new_todos = [todo for todo in todos if f"{todo.file_path}:{todo.line_number}" not in tracker]
        logger.info(f"   {len(new_todos)} are new (not yet tracked)")

        # Apply priority filter
        if priority_filter:
            new_todos = [todo for todo in new_todos if todo.priority == priority_filter]
            logger.info(f"   {len(new_todos)} match priority filter '{priority_filter}'")

        # Apply max limit
        if max_issues and len(new_todos) > max_issues:
            logger.info(f"   Limiting to {max_issues} issues")
            new_todos = new_todos[:max_issues]

        if not new_todos:
            logger.info("✅ No new TODOs to convert")
            return 0

        # Dry run mode
        if dry_run:
            logger.info("🔍 DRY RUN MODE - Issues that would be created:")
            for i, todo in enumerate(new_todos, 1):
                logger.info(
                    f"   {i}. [{todo.todo_type}] {todo.description[:60]}... ({todo.file_path}:{todo.line_number})"
                )
            logger.info(f"   Total: {len(new_todos)} issues")
            return len(new_todos)

        # Create issues
        logger.info(f"🎫 Creating {len(new_todos)} GitHub issues...")
        converter = todo_to_issue.IssueConverter()
        created_count = 0

        for i, todo in enumerate(new_todos, 1):
            logger.info(f"   [{i}/{len(new_todos)}] Creating issue for {todo.file_path}:{todo.line_number}")

            try:
                issue_number = converter.create_issue(todo)
                if issue_number:
                    tracker[f"{todo.file_path}:{todo.line_number}"] = {
                        "issue_number": issue_number,
                        "description": todo.description[:100],
                        "created_at": todo_to_issue.datetime.now().isoformat(),
                    }
                    created_count += 1
                    logger.info(f"      ✅ Created issue #{issue_number}")
                else:
                    logger.warning("      ⚠️  Failed to create issue")

            except Exception as e:
                logger.error(f"      ❌ Error creating issue: {e}")

        # Save tracker
        save_issue_tracker(tracker, tracker_path)

        logger.info(f"✅ Successfully created {created_count}/{len(new_todos)} issues")
        return created_count

    except ImportError as e:
        logger.error(f"❌ Failed to import todo_to_issue module: {e}")
        logger.info("   Make sure todo_to_issue.py is in the scripts directory")
        return 0
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Automated TODO-to-Issue conversion")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan for TODOs but don't create issues",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=10,
        help="Maximum number of issues to create (default: 10)",
    )
    parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        help="Only create issues with this priority",
    )
    parser.add_argument(
        "--no-limit",
        action="store_true",
        help="Remove max issues limit (create all)",
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("AUTOMATED TODO-TO-ISSUE CONVERSION")
    logger.info("=" * 70)

    max_issues = None if args.no_limit else args.max_issues

    created = scan_and_convert_todos(
        dry_run=args.dry_run,
        max_issues=max_issues,
        priority_filter=args.priority,
    )

    logger.info("=" * 70)

    if args.dry_run:
        logger.info(f"🔍 Dry run complete. Would create {created} issues.")
        logger.info("   Run without --dry-run to actually create issues")
    else:
        logger.info(f"✅ Created {created} GitHub issues")

    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())

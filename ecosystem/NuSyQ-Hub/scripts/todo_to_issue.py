#!/usr/bin/env python3
"""Convert TODO comments to GitHub issues automatically.

Scans the codebase for TODO/FIXME comments and creates GitHub issues
via the GitHub CLI (gh). Tracks created issues to avoid duplicates.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="🎫 %(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)
FALLBACK_DIRS = ["src", "scripts", "docs"]
TODO_LINE_PATTERN = re.compile(r"^\s*#\s*(TODO|FIXME|XXX|HACK)\b[:\s-]*(.+)", re.IGNORECASE)


@dataclass
class TodoItem:
    """Represents a TODO comment in the code."""

    file_path: str
    line_number: int
    todo_type: str  # TODO, FIXME, XXX, HACK
    description: str
    context: str = ""
    priority: str = "medium"
    labels: list[str] = field(default_factory=list)
    issue_number: int | None = None

    def to_issue_body(self) -> str:
        """Convert to GitHub issue body format.

        Returns:
            Markdown formatted issue body
        """
        body = [
            "## Description",
            "",
            self.description,
            "",
            "## Location",
            "",
            f"- **File:** `{self.file_path}`",
            f"- **Line:** {self.line_number}",
            f"- **Type:** {self.todo_type}",
            "",
            "## Context",
            "",
            "```python",
            self.context,
            "```",
            "",
            "## Priority",
            f"{self.priority.capitalize()}",
            "",
            "---",
            "*Auto-generated from code comment*",
        ]
        return "\n".join(body)


class TodoToIssueConverter:
    """Converts TODO comments to GitHub issues."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize converter.

        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root or Path.cwd()
        self.todos: list[TodoItem] = []
        self.tracking_file = self.repo_root / ".github" / "todo_tracking.json"
        self.tracked_todos: dict[str, int] = {}

        # Load existing tracking data
        self._load_tracking_data()

    def _load_tracking_data(self):
        """Load tracking data for already created issues."""
        if self.tracking_file.exists():
            try:
                self.tracked_todos = json.loads(self.tracking_file.read_text())
                logger.info(f"Loaded {len(self.tracked_todos)} tracked TODOs")
            except Exception as e:
                logger.warning(f"Could not load tracking data: {e}")
                self.tracked_todos = {}

    def _save_tracking_data(self):
        """Save tracking data."""
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        self.tracking_file.write_text(json.dumps(self.tracked_todos, indent=2))
        logger.info(f"Saved tracking data: {len(self.tracked_todos)} TODOs")

    def _get_todo_key(self, todo: TodoItem) -> str:
        """Generate unique key for TODO item.

        Args:
            todo: TodoItem instance

        Returns:
            Unique key string
        """
        return f"{todo.file_path}:{todo.line_number}"

    def scan_for_todos(self, patterns: list[str] | None = None):
        """Scan repository for TODO comments.

        Args:
            patterns: TODO patterns to search for
        """
        if patterns is None:
            patterns = [r"TODO", r"FIXME", r"XXX", r"HACK"]

        logger.info(f"Scanning for TODOs in {self.repo_root}")

        # Use grep to find TODO comments
        pattern = "|".join(patterns)
        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", "-E", rf"^\s*#\s*({pattern})\b", "src/"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            lines = result.stdout.strip().split("\n")
            logger.info(f"Found {len([line for line in lines if line])} TODO comments")

            for line in lines:
                if not line:
                    continue

                match = re.match(r"([^:]+):(\d+):(.*)", line)
                if not match:
                    continue

                file_path, line_num, content = match.groups()
                self._capture_todo_from_line(file_path, int(line_num), content)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to scan for TODOs: {e}")
            self._fallback_scan(patterns)
        except FileNotFoundError as e:
            logger.warning(f"'grep' unavailable ({e}); using Python fallback scan")
            self._fallback_scan(patterns)
        except Exception as e:
            logger.error(f"Error scanning: {e}")

    def _capture_todo_from_line(self, file_path: str, line_num: int, content: str) -> bool:
        todo_match = TODO_LINE_PATTERN.match(content)
        if not todo_match:
            return False

        todo_type = todo_match.group(1).upper()
        description = todo_match.group(2).strip()

        priority = {
            "FIXME": "high",
            "HACK": "high",
            "XXX": "medium",
            "TODO": "medium",
        }.get(todo_type, "medium")

        labels = ["technical-debt", todo_type.lower()]
        if "test" in file_path.lower():
            labels.append("testing")
        if "doc" in file_path.lower():
            labels.append("documentation")

        todo = TodoItem(
            file_path=file_path,
            line_number=line_num,
            todo_type=todo_type,
            description=description,
            context=content.strip(),
            priority=priority,
            labels=labels,
        )
        self.todos.append(todo)
        return True

    def _fallback_scan(self, patterns: list[str]) -> None:
        regex = re.compile("|".join(patterns), re.IGNORECASE)
        for dir_name in FALLBACK_DIRS:
            directory = self.repo_root / dir_name
            if not directory.exists():
                continue
            for path in directory.rglob("*.py"):
                try:
                    for line_num, line in enumerate(
                        path.read_text(encoding="utf-8", errors="ignore").splitlines(),
                        start=1,
                    ):
                        if regex.search(line):
                            self._capture_todo_from_line(str(path), line_num, line)
                except OSError as e:
                    logger.warning(f"Skipping {path}: {e}")

    def create_github_issue(self, todo: TodoItem) -> int | None:
        """Create GitHub issue for TODO item.

        Args:
            todo: TodoItem to create issue for

        Returns:
            Issue number if created, None otherwise
        """
        try:
            # Check if already tracked
            key = self._get_todo_key(todo)
            if key in self.tracked_todos:
                logger.debug(f"Already tracked: {key} -> #{self.tracked_todos[key]}")
                return self.tracked_todos[key]

            # Create issue using gh CLI
            title = f"[{todo.todo_type}] {todo.description[:80]}"
            body = todo.to_issue_body()
            labels = ",".join(todo.labels)

            cmd = ["gh", "issue", "create", "--title", title, "--body", body, "--label", labels]

            result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)

            # Extract issue number from output
            output = result.stdout.strip()
            issue_match = re.search(r"/issues/(\d+)", output)
            if issue_match:
                issue_num = int(issue_match.group(1))
                logger.info(f"✅ Created issue #{issue_num}: {title}")

                # Track this TODO
                self.tracked_todos[key] = issue_num
                return issue_num
            else:
                logger.warning(f"Could not extract issue number from: {output}")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create issue: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            return None

    def run(self, dry_run: bool = False, limit: int | None = None):
        """Execute TODO to issue conversion.

        Args:
            dry_run: If True, don't actually create issues
            limit: Maximum number of issues to create
        """
        logger.info("🚀 Starting TODO to Issue Conversion")

        # Scan for TODOs
        self.scan_for_todos()

        if not self.todos:
            logger.info("No TODOs found")
            return

        logger.info(f"Found {len(self.todos)} TODOs")

        # Filter out already tracked
        new_todos = [t for t in self.todos if self._get_todo_key(t) not in self.tracked_todos]

        logger.info(f"New TODOs to process: {len(new_todos)}")

        if dry_run:
            logger.info("DRY RUN - No issues will be created")
            for todo in new_todos[:limit] if limit else new_todos:
                logger.info(f"  Would create: [{todo.todo_type}] {todo.description[:60]}")
            return

        # Create issues
        created = 0
        for todo in new_todos[:limit] if limit else new_todos:
            issue_num = self.create_github_issue(todo)
            if issue_num:
                created += 1

        # Save tracking data
        self._save_tracking_data()

        logger.info(f"✅ Created {created} GitHub issues")
        logger.info(f"📊 Total tracked: {len(self.tracked_todos)} TODOs")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Convert TODO comments to GitHub issues")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually create issues, just show what would be done",
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of issues to create")

    args = parser.parse_args()

    converter = TodoToIssueConverter()
    converter.run(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()

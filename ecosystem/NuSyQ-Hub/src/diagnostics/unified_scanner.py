#!/usr/bin/env python3
"""Unified diagnostic scanner for repository code quality issues.

Consolidates functionality from scan_issues.py and scan_src_issues.py
with improved typing, CLI arguments, and structured output.

OmniTag: {
    "purpose": "code_quality_diagnostics",
    "tags": ["Python", "diagnostics", "code_analysis", "quality_assurance"],
    "category": "developer_tools",
    "evolution_stage": "v2.0_unified"
}
"""

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)


@dataclass
class Issue:
    """Represents a single code quality issue."""

    category: str
    file_path: Path
    line_number: int
    line_content: str
    pattern_matched: str


class UnifiedScanner:
    """Unified repository scanner for code quality issues."""

    # Issue categories and their patterns
    PLACEHOLDER_PATTERNS: Final[list[str]] = [
        r"TODO[\s:]*implement",
        r"TODO[\s:]*placeholder",
        r"pass\s*#\s*TODO",
        r"raise NotImplementedError",
    ]

    DEPRECATED_PATTERNS: Final[list[str]] = [
        r"@deprecated",
        r"# deprecated",
        r"# DEPRECATED",
        r"__deprecated__",
    ]

    INCOMPLETE_PATTERNS: Final[list[str]] = [
        r"# TODO:",
        r"# FIXME:",
        r"# WIP:",
        r"# HACK:",
    ]

    HARDCODED_PATTERNS: Final[list[str]] = [
        r"'C:\\\\Users",
        r'"C:\\\\Users',
        r"'/home/",
        r"localhost:11434",
        r"localhost:5000",
        r"localhost:8081",
        r"localhost:[\d]{4,5}",
    ]

    EXCLUDED_DIRS: Final[set[str]] = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    }

    def __init__(self, root_path: Path, scan_extensions: set[str] | None = None) -> None:
        """Initialize the scanner.

        Args:
            root_path: Root directory to scan
            scan_extensions: File extensions to scan (default: {'.py'})
        """
        self.root_path = root_path
        self.scan_extensions = scan_extensions or {".py"}
        self.issues: dict[str, list[Issue]] = defaultdict(list)

    def should_scan_file(self, file_path: Path) -> bool:
        """Check if a file should be scanned.

        Args:
            file_path: Path to check

        Returns:
            True if file should be scanned, False otherwise
        """
        # Check extension
        if file_path.suffix not in self.scan_extensions:
            return False

        # Check if in excluded directory
        parts = file_path.parts
        return not any(excluded in parts for excluded in self.EXCLUDED_DIRS)

    def scan_file(self, file_path: Path) -> None:
        """Scan a single file for issues.

        Args:
            file_path: Path to file to scan
        """
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_number, line in enumerate(lines, start=1):
                self._check_line(file_path, line_number, line)

        except (OSError, UnicodeDecodeError) as e:
            logger.warning(
                f"Warning: Could not read {file_path}: {e}",
                file=sys.stderr,
            )

    def _check_line(self, file_path: Path, line_number: int, line: str) -> None:
        """Check a single line against all patterns.

        Args:
            file_path: Path to the file
            line_number: Line number (1-indexed)
            line: Line content
        """
        line_stripped = line.strip()

        # Check placeholders
        for pattern in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                self.issues["placeholder"].append(
                    Issue(
                        category="placeholder",
                        file_path=file_path,
                        line_number=line_number,
                        line_content=line_stripped[:80],
                        pattern_matched=pattern,
                    )
                )
                return  # Only report first match per line

        # Check deprecated code
        for pattern in self.DEPRECATED_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                self.issues["deprecated"].append(
                    Issue(
                        category="deprecated",
                        file_path=file_path,
                        line_number=line_number,
                        line_content=line_stripped[:80],
                        pattern_matched=pattern,
                    )
                )
                return

        # Check incomplete implementations
        for pattern in self.INCOMPLETE_PATTERNS:
            if re.search(pattern, line):
                self.issues["incomplete"].append(
                    Issue(
                        category="incomplete",
                        file_path=file_path,
                        line_number=line_number,
                        line_content=line_stripped[:80],
                        pattern_matched=pattern,
                    )
                )
                return

        # Check hardcoded values
        for pattern in self.HARDCODED_PATTERNS:
            if re.search(pattern, line):
                self.issues["hardcoded"].append(
                    Issue(
                        category="hardcoded",
                        file_path=file_path,
                        line_number=line_number,
                        line_content=line_stripped[:80],
                        pattern_matched=pattern,
                    )
                )
                return

    def scan_directory(self) -> None:
        """Scan all files in the root directory."""
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and self.should_scan_file(file_path):
                self.scan_file(file_path)

    def get_summary(self) -> dict[str, int]:
        """Get issue count summary.

        Returns:
            Dictionary mapping category to issue count
        """
        return {category: len(issues) for category, issues in self.issues.items()}

    def print_report(self, max_items: int = 20, show_details: bool = True) -> None:
        """Print human-readable report.

        Args:
            max_items: Maximum issues to show per category
            show_details: Whether to show detailed issue information
        """
        logger.info("=" * 90)
        logger.info(f"UNIFIED REPOSITORY SCAN: {self.root_path}")
        logger.info("=" * 90)

        total_issues = sum(len(issues) for issues in self.issues.values())

        if total_issues == 0:
            logger.info("\n✅ No issues found!")
            return

        for category in sorted(self.issues.keys()):
            issues = self.issues[category]
            if not issues:
                continue

            logger.info(f"\n{category.upper()}: {len(issues)} issues")

            if show_details:
                for issue in sorted(issues, key=lambda x: (x.file_path, x.line_number))[:max_items]:
                    rel_path = issue.file_path.relative_to(self.root_path)
                    logger.info(f"  {rel_path}:{issue.line_number}")
                    logger.info(f"    └─ {issue.line_content}")

                if len(issues) > max_items:
                    logger.info(f"    ... and {len(issues) - max_items} more")

        logger.info("\n" + "=" * 90)
        logger.info(f"TOTAL ISSUES: {total_issues}")
        logger.info("=" * 90)

    def export_json(self, output_path: Path) -> None:
        """Export results as JSON.

        Args:
            output_path: Path to output JSON file
        """
        data = {
            "scan_root": str(self.root_path),
            "total_issues": sum(len(issues) for issues in self.issues.values()),
            "summary": self.get_summary(),
            "issues": {
                category: [
                    {
                        "file": str(issue.file_path.relative_to(self.root_path)),
                        "line": issue.line_number,
                        "content": issue.line_content,
                        "pattern": issue.pattern_matched,
                    }
                    for issue in issues
                ]
                for category, issues in self.issues.items()
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"\n📄 Results exported to: {output_path}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified repository scanner for code quality issues"
    )
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--src-only",
        action="store_true",
        help="Only scan src/ directory",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=20,
        help="Maximum issues to display per category (default: 20)",
    )
    parser.add_argument(
        "--export-json",
        type=Path,
        help="Export results to JSON file",
    )
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="Only show summary, not detailed issues",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".py"],
        help="File extensions to scan (default: .py)",
    )

    args = parser.parse_args()

    # Determine scan root
    scan_root = args.path / "src" if args.src_only else args.path

    if not scan_root.exists():
        logger.error(f"Error: Path {scan_root} does not exist", file=sys.stderr)
        sys.exit(1)

    # Run scan
    scanner = UnifiedScanner(scan_root, scan_extensions=set(args.extensions))
    scanner.scan_directory()

    # Print report
    scanner.print_report(
        max_items=args.max_items,
        show_details=not args.no_details,
    )

    # Export JSON if requested
    if args.export_json:
        scanner.export_json(args.export_json)


if __name__ == "__main__":
    main()

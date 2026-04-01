#!/usr/bin/env python3
"""🔄 KILO-FOOLISH Safe Consolidation Engine.

PRESERVATION FIX: 2025-08-03 - Safe duplicate removal and consolidation.

Following File Preservation Mandate - only removes truly empty duplicates,
preserves all functional content, and maintains system integrity.
"""

import contextlib
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SafeConsolidator:
    """Safe consolidation engine following KILO-FOOLISH principles."""

    def __init__(self, repo_root=".") -> None:
        """Initialize SafeConsolidator with repo_root."""
        self.repo_root = Path(repo_root)
        self.src_root = self.repo_root / "src"

        # Track consolidation actions
        self.empty_files_found: list[Any] = []
        self.functional_files_preserved: list[Any] = []
        self.consolidation_actions: list[dict[str, Any]] = []

    def identify_safe_consolidations(self) -> list[dict[str, Any]]:
        """Identify safe consolidation opportunities."""
        # Find all Python files
        all_files = list(self.src_root.rglob("*.py"))

        # Group by filename
        filename_groups = defaultdict(list)
        for file_path in all_files:
            filename_groups[file_path.name].append(file_path)

        # Identify duplicates
        duplicates = {name: paths for name, paths in filename_groups.items() if len(paths) > 1}

        for filename, paths in duplicates.items():
            functional_files: list[Any] = []
            empty_files: list[Any] = []
            for path in paths:
                try:
                    size = os.path.getsize(path)
                    if size == 0:
                        empty_files.append(path)
                    else:
                        functional_files.append(path)
                except OSError:
                    logger.debug("Suppressed OSError", exc_info=True)

            if len(functional_files) == 1 and len(empty_files) > 0:
                self.consolidation_actions.append(
                    {
                        "filename": filename,
                        "preserve": functional_files[0],
                        "remove": empty_files,
                        "action": "safe_removal",
                        "risk": "none",
                    }
                )
            elif len(functional_files) > 1:
                # Multiple functional files - needs manual review
                self.consolidation_actions.append(
                    {
                        "filename": filename,
                        "preserve": functional_files,
                        "remove": empty_files,
                        "action": "manual_review_needed",
                        "risk": "medium",
                    }
                )

        sum(1 for action in self.consolidation_actions if action["action"] == "safe_removal")
        sum(
            1 for action in self.consolidation_actions if action["action"] == "manual_review_needed"
        )

        return self.consolidation_actions

    def execute_safe_consolidations(self, dry_run=True) -> None:
        """Execute safe consolidations (with dry-run option)."""
        safe_actions = [
            action for action in self.consolidation_actions if action["action"] == "safe_removal"
        ]

        if not safe_actions:
            return

        for action in safe_actions:
            for empty_file in action["remove"]:
                if dry_run:
                    pass
                else:
                    with contextlib.suppress(OSError):
                        os.remove(empty_file)

        if dry_run:
            pass
        else:
            pass

    def generate_consolidation_report(self) -> dict[str, Any]:
        """Generate detailed consolidation report."""
        report = {
            "timestamp": "2025-08-03",
            "consolidation_actions": self.consolidation_actions,
            "summary": {
                "total_duplicate_sets": len(self.consolidation_actions),
                "safe_removals": sum(
                    1 for a in self.consolidation_actions if a["action"] == "safe_removal"
                ),
                "manual_reviews": sum(
                    1 for a in self.consolidation_actions if a["action"] == "manual_review_needed"
                ),
                "files_to_remove": sum(
                    len(a["remove"])
                    for a in self.consolidation_actions
                    if a["action"] == "safe_removal"
                ),
                "files_preserved": sum(
                    1 for a in self.consolidation_actions if a["action"] == "safe_removal"
                ),
            },
            "manual_review_needed": [
                {
                    "filename": action["filename"],
                    "functional_files": [str(f) for f in action["preserve"]],
                    "reason": "Multiple functional files need manual consolidation",
                }
                for action in self.consolidation_actions
                if action["action"] == "manual_review_needed"
            ],
        }

        # Save report
        report_file = self.repo_root / "SAFE_CONSOLIDATION_REPORT.json"
        import json

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Print key findings

        if report["manual_review_needed"]:
            # Type: list of dicts with manual review info
            for item in report["manual_review_needed"]:
                for _file_path in item["functional_files"]:  # type: ignore[index]
                    pass

        return report


if __name__ == "__main__":
    consolidator = SafeConsolidator()

    # Phase 1: Identify safe consolidations
    actions = consolidator.identify_safe_consolidations()

    # Phase 2: Execute in dry-run mode first
    consolidator.execute_safe_consolidations(dry_run=True)

    # Phase 3: Generate report
    report = consolidator.generate_consolidation_report()

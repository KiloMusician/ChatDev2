"""Quest Log Validator.

Validates quest_log.jsonl structure, required fields, and data integrity.
Provides auto-fix suggestions for common issues.

OmniTag: {'purpose': 'validation', 'type': 'data_quality', 'evolution_stage': 'v1.0'}
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class QuestLogValidator:
    """Validates quest log structure and data integrity."""

    REQUIRED_QUEST_FIELDS: ClassVar[set] = {
        "id",
        "title",
        "description",
        "questline",
        "status",
        "created_at",
        "updated_at",
        "dependencies",
        "tags",
        "history",
    }

    VALID_STATUSES: ClassVar[set] = {
        "pending",
        "in-progress",
        "in_progress",
        "completed",
        "blocked",
        "mastered",
        "cancelled",
    }

    REQUIRED_QUESTLINE_FIELDS: ClassVar[set] = {
        "name",
        "description",
        "tags",
        "quests",
        "created_at",
    }

    def __init__(self, quest_log_path: Path | None = None) -> None:
        """Initialize QuestLogValidator with quest_log_path."""
        self.quest_log_path = quest_log_path or Path("src/Rosetta_Quest_System/quest_log.jsonl")
        self.entries: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.suggestions: list[dict[str, Any]] = []

    def load_quest_log(self) -> None:
        """Load and parse quest log entries."""
        if not self.quest_log_path.exists():
            self.errors.append(
                {
                    "type": "file_not_found",
                    "message": f"Quest log not found: {self.quest_log_path}",
                    "severity": "critical",
                }
            )
            return

        line_number = 0
        with open(self.quest_log_path, encoding="utf-8") as f:
            for line in f:
                line_number += 1
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    entry["_line_number"] = line_number
                    self.entries.append(entry)
                except json.JSONDecodeError as e:
                    self.errors.append(
                        {
                            "type": "invalid_json",
                            "line": line_number,
                            "message": f"Invalid JSON: {e}",
                            "severity": "error",
                        }
                    )

        logger.info(f"✅ Loaded {len(self.entries)} entries from quest log")

    def validate_entry_structure(self, entry: dict[str, Any]) -> None:
        """Validate a single entry's structure."""
        line_number = entry.get("_line_number", "unknown")
        event_type = entry.get("event", "unknown")

        # Check for required top-level fields
        if "event" not in entry:
            self.errors.append(
                {
                    "type": "missing_field",
                    "line": line_number,
                    "field": "event",
                    "message": "Missing 'event' field",
                    "severity": "error",
                }
            )

        if "details" not in entry:
            self.warnings.append(
                {
                    "type": "missing_field",
                    "line": line_number,
                    "field": "details",
                    "message": "Missing 'details' field (legacy format?)",
                    "severity": "warning",
                }
            )
            details = entry
        else:
            details = entry["details"]

        # Validate quest entries
        if event_type == "add_quest":
            self._validate_quest(details, line_number)

        # Validate questline entries
        elif event_type == "add_questline":
            self._validate_questline(details, line_number)

    def _validate_quest(self, quest: dict[str, Any], line_number: int) -> None:
        """Validate quest-specific fields."""
        # Check required fields
        for field in self.REQUIRED_QUEST_FIELDS:
            if field not in quest:
                self.errors.append(
                    {
                        "type": "missing_required_field",
                        "line": line_number,
                        "field": field,
                        "message": f"Quest missing required field: {field}",
                        "severity": "error",
                    }
                )

        # Validate status
        status = quest.get("status", "").lower()
        if status and status not in self.VALID_STATUSES:
            self.errors.append(
                {
                    "type": "invalid_status",
                    "line": line_number,
                    "value": status,
                    "message": f"Invalid status: {status}",
                    "severity": "error",
                    "suggestion": f"Use one of: {', '.join(sorted(self.VALID_STATUSES))}",
                }
            )

        # Validate ID format (should be UUID-like)
        quest_id = quest.get("id", "")
        if quest_id and not re.match(
            r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
            quest_id,
        ):
            self.warnings.append(
                {
                    "type": "invalid_id_format",
                    "line": line_number,
                    "value": quest_id,
                    "message": f"ID doesn't match UUID format: {quest_id}",
                    "severity": "warning",
                }
            )

        # Validate timestamps
        for field in ["created_at", "updated_at"]:
            if field in quest:
                try:
                    datetime.fromisoformat(quest[field].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    self.errors.append(
                        {
                            "type": "invalid_timestamp",
                            "line": line_number,
                            "field": field,
                            "value": quest.get(field),
                            "message": f"Invalid timestamp format: {field}",
                            "severity": "error",
                        }
                    )

        # Check for ZETA task mapping
        title = quest.get("title", "")
        tags = quest.get("tags", [])
        has_zeta_tag = any("zeta" in str(tag).lower() for tag in tags)
        has_zeta_title = bool(re.search(r"[Zz]eta\d+", title))

        if not has_zeta_tag and not has_zeta_title:
            self.suggestions.append(
                {
                    "type": "missing_zeta_mapping",
                    "line": line_number,
                    "message": "Quest has no ZETA task mapping",
                    "severity": "info",
                    "suggestion": "Add Zeta## tag or include 'Zeta##:' in title for automatic progress tracking",
                }
            )

        # Validate dependencies is a list
        if "dependencies" in quest and not isinstance(quest["dependencies"], list):
            self.errors.append(
                {
                    "type": "invalid_field_type",
                    "line": line_number,
                    "field": "dependencies",
                    "message": "Dependencies must be a list",
                    "severity": "error",
                }
            )

        # Validate tags is a list
        if "tags" in quest and not isinstance(quest["tags"], list):
            self.errors.append(
                {
                    "type": "invalid_field_type",
                    "line": line_number,
                    "field": "tags",
                    "message": "Tags must be a list",
                    "severity": "error",
                }
            )

    def _validate_questline(self, questline: dict[str, Any], line_number: int) -> None:
        """Validate questline-specific fields."""
        # Check required fields
        for field in self.REQUIRED_QUESTLINE_FIELDS:
            if field not in questline:
                self.errors.append(
                    {
                        "type": "missing_required_field",
                        "line": line_number,
                        "field": field,
                        "message": f"Questline missing required field: {field}",
                        "severity": "error",
                    }
                )

        # Validate quests is a list
        if "quests" in questline and not isinstance(questline["quests"], list):
            self.errors.append(
                {
                    "type": "invalid_field_type",
                    "line": line_number,
                    "field": "quests",
                    "message": "Quests must be a list",
                    "severity": "error",
                }
            )

    def validate_all(self) -> None:
        """Run all validation checks."""
        logger.info("\n🔍 Validating quest log...")

        for entry in self.entries:
            self.validate_entry_structure(entry)

        logger.info("✅ Validation complete!")
        logger.error(f"   Errors: {len(self.errors)}")
        logger.warning(f"   Warnings: {len(self.warnings)}")
        logger.info(f"   Suggestions: {len(self.suggestions)}")

    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""
        report_lines = [
            "=" * 80,
            "📋 QUEST LOG VALIDATION REPORT",
            "=" * 80,
            f"File: {self.quest_log_path}",
            f"Entries Analyzed: {len(self.entries)}",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Summary
        report_lines.extend(
            [
                "SUMMARY",
                "-" * 80,
                f"✓ Total Entries: {len(self.entries)}",
                f"✗ Errors: {len(self.errors)}",
                f"⚠ Warnings: {len(self.warnings)}",
                f"💡 Suggestions: {len(self.suggestions)}",
                "",
            ]
        )

        # Errors
        if self.errors:
            report_lines.extend(["ERRORS", "-" * 80])
            for error in self.errors:
                report_lines.append(
                    f"Line {error.get('line', '?')}: [{error['severity'].upper()}] {error['message']}"
                )
                if "suggestion" in error:
                    report_lines.append(f"  → {error['suggestion']}")
            report_lines.append("")

        # Warnings
        if self.warnings:
            report_lines.extend(["WARNINGS", "-" * 80])
            for warning in self.warnings:
                report_lines.append(f"Line {warning.get('line', '?')}: {warning['message']}")
            report_lines.append("")

        # Suggestions
        if self.suggestions:
            report_lines.extend(["SUGGESTIONS", "-" * 80])
            for suggestion in self.suggestions:
                report_lines.append(f"Line {suggestion.get('line', '?')}: {suggestion['message']}")
                if "suggestion" in suggestion:
                    report_lines.append(f"  → {suggestion['suggestion']}")
            report_lines.append("")

        # Health Status
        report_lines.extend(["HEALTH STATUS", "-" * 80])
        if not self.errors and not self.warnings:
            report_lines.append("✅ EXCELLENT - No issues found!")
        elif not self.errors:
            report_lines.append(f"✓ GOOD - {len(self.warnings)} warnings, no critical errors")
        elif len(self.errors) < 5:
            report_lines.append(f"⚠ NEEDS ATTENTION - {len(self.errors)} errors found")
        else:
            report_lines.append(f"✗ CRITICAL - {len(self.errors)} errors require immediate fixes")

        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def save_report(self, output_path: Path | None = None) -> None:
        """Save validation report to file."""
        if output_path is None:
            output_path = Path("data/quest_log_validation_report.txt")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = self.generate_report()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"📄 Report saved to {output_path}")

    def get_auto_fix_suggestions(self) -> list[dict[str, Any]]:
        """Generate auto-fix suggestions for common issues."""
        fixes: list[Any] = []
        # Group errors by type
        error_types: dict[str, list[dict[str, Any]]] = {}
        for error in self.errors:
            error_type = error["type"]
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)

        # Generate fixes for missing fields
        if "missing_required_field" in error_types:
            fixes.append(
                {
                    "type": "add_default_fields",
                    "description": "Add default values for missing required fields",
                    "affected_lines": [e["line"] for e in error_types["missing_required_field"]],
                    "action": "Add empty/default values for missing fields",
                }
            )

        # Generate fixes for invalid status
        if "invalid_status" in error_types:
            fixes.append(
                {
                    "type": "normalize_status",
                    "description": "Normalize invalid status values to valid ones",
                    "affected_lines": [e["line"] for e in error_types["invalid_status"]],
                    "action": "Map invalid statuses to closest valid status",
                }
            )

        return fixes

    def run(self) -> None:
        """Execute full validation workflow."""
        logger.info("=" * 80)
        logger.info("🔍 QUEST LOG VALIDATOR")
        logger.info("=" * 80)

        self.load_quest_log()
        self.validate_all()

        logger.info("\n" + self.generate_report())

        if self.errors or self.warnings:
            logger.info("\n💡 Auto-Fix Suggestions:")
            fixes = self.get_auto_fix_suggestions()
            for fix in fixes:
                logger.info(f"  • {fix['description']}")
                logger.info(f"    Lines affected: {len(fix['affected_lines'])}")

        logger.info("\n" + "=" * 80)


def main() -> None:
    """CLI entry point."""
    validator = QuestLogValidator()
    validator.run()


if __name__ == "__main__":
    main()

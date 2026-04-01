#!/usr/bin/env python3
"""Error-Quest Bridge: Auto-Generate Quests from Critical Errors.

This bridge creates automatic quest generation from the unified error reporter:
1. Scan multi-repo errors via UnifiedErrorReporter
2. Filter for critical errors (severity = error)
3. Auto-generate quests for each critical error
4. Add to quest board with appropriate metadata
5. Enable error-driven development workflow

OmniTag: [quest, error_reporting, automation, integration]
MegaTag: [ERROR_QUEST_BRIDGE, AUTOMATED_HEALING, CONSCIOUSNESS_FEEDBACK]

VS Code Integration:
- Extension awareness: Leverages Error Lens + GitLens patterns
- IntelliSense-guided: Type-safe integration points
- Copilot-assisted: Semantic error classification
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from src.diagnostics.unified_error_reporter import (ErrorDiagnostic,
                                                        ErrorSeverity,
                                                        ErrorType, RepoName,
                                                        UnifiedErrorReporter)
    from src.Rosetta_Quest_System.quest_engine import QuestEngine
except ImportError as e:
    logger.error(f"Failed to import dependencies: {e}")
    raise


class ErrorQuestBridge:
    """Bridge between error reporting and quest generation.

    Transforms critical errors into actionable quests on the quest board.
    This creates a feedback loop: errors → quests → fixes → receipts → learning.
    """

    def __init__(
        self,
        error_reporter: UnifiedErrorReporter | None = None,
        quest_engine: QuestEngine | None = None,
    ) -> None:
        """Initialize bridge with reporter and quest engine.

        Args:
            error_reporter: UnifiedErrorReporter instance (creates if None)
            quest_engine: QuestEngine instance (creates if None)
        """
        self.error_reporter = error_reporter or UnifiedErrorReporter()
        self.quest_engine = quest_engine or QuestEngine()
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _severity_rank(severity: ErrorSeverity) -> int:
        """Return numeric rank where higher means more severe."""
        rank = {
            ErrorSeverity.HINT: 0,
            ErrorSeverity.INFO: 1,
            ErrorSeverity.WARNING: 2,
            ErrorSeverity.ERROR: 3,
        }
        return rank.get(severity, 0)

    @classmethod
    def _meets_threshold(cls, severity: ErrorSeverity, threshold: ErrorSeverity) -> bool:
        """Return True when severity is at or above threshold."""
        return cls._severity_rank(severity) >= cls._severity_rank(threshold)

    def scan_and_create_quests(
        self,
        severity_threshold: ErrorSeverity = ErrorSeverity.ERROR,
        max_quests: int = 10,
        report_path: Path | None = None,
    ) -> dict[str, Any]:
        """Scan for errors and auto-create quests for critical ones.

        Args:
            severity_threshold: Minimum severity to create quests (default: ERROR)
            max_quests: Maximum number of quests to create in one scan
            report_path: Optional precomputed unified error report artifact path

        Returns:
            Dictionary with scan results and created quest IDs
        """
        diagnostics: list[ErrorDiagnostic] = []
        report_source = "scan"
        if report_path and Path(report_path).exists():
            report_source = "artifact"
            self.logger.info("📄 Loading diagnostics from artifact: %s", report_path)
            diagnostics = self._load_diagnostics_from_artifact(Path(report_path))
        else:
            self.logger.info("🔍 Scanning repositories for critical errors...")
            report = self.error_reporter.scan_all_repos()
            for repo_scan in report.get("scans", {}).values():
                diagnostics.extend(repo_scan.diagnostics)

        critical_errors = [
            d for d in diagnostics if self._meets_threshold(d.severity, severity_threshold)
        ]

        self.logger.info(
            f"📊 Found {len(critical_errors)} critical errors (threshold: {severity_threshold.value})"
        )

        # Limit quest creation
        errors_to_process = critical_errors[:max_quests]

        created_quests = []
        for error in errors_to_process:
            quest_id = self._create_quest_from_error(error)
            if quest_id:
                created_quests.append(quest_id)

        result = {
            "timestamp": datetime.now().isoformat(),
            "total_errors_found": len(critical_errors),
            "quests_created": len(created_quests),
            "quest_ids": created_quests,
            "severity_threshold": severity_threshold.value,
            "max_quests": max_quests,
            "report_source": report_source,
            "report_path": str(report_path) if report_path else None,
        }

        self.logger.info(
            f"✅ Created {len(created_quests)} quests from {len(critical_errors)} errors"
        )

        return result

    def _load_diagnostics_from_artifact(self, report_path: Path) -> list[ErrorDiagnostic]:
        """Load diagnostics from a unified_error_report JSON artifact."""
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            self.logger.warning("Failed to read artifact %s: %s", report_path, exc)
            return []

        rows = payload.get("diagnostic_details", [])
        if not isinstance(rows, list):
            return []

        diagnostics: list[ErrorDiagnostic] = []
        severity_map = {member.value: member for member in ErrorSeverity}
        type_map = {member.value: member for member in ErrorType}
        repo_map = {member.value: member for member in RepoName}

        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            try:
                severity_raw = str(row.get("severity") or ErrorSeverity.INFO.value).lower()
                error_type_raw = str(row.get("error_type") or ErrorType.LINTING.value).lower()
                repo_raw = str(row.get("repo") or RepoName.NUSYQ_HUB.value).lower()
                file_path = Path(str(row.get("file_path") or row.get("file") or "unknown.py"))
                line_num = int(row.get("line_num") or row.get("line") or 1)
                diagnostic = ErrorDiagnostic(
                    error_id=str(
                        row.get("error_id")
                        or f"artifact_{file_path.name}_{line_num}_{severity_raw}_{index}"
                    ),
                    severity=severity_map.get(severity_raw, ErrorSeverity.INFO),
                    error_type=type_map.get(error_type_raw, ErrorType.LINTING),
                    repo=repo_map.get(repo_raw, RepoName.NUSYQ_HUB),
                    file_path=file_path,
                    line_num=max(1, line_num),
                    column_num=int(row.get("column_num") or row.get("column") or 0),
                    message=str(row.get("message") or ""),
                    source=str(row.get("source") or "unified_report"),
                    suggestion=str(row.get("suggestion") or ""),
                    timestamp=str(row.get("timestamp") or datetime.now().isoformat()),
                )
                diagnostics.append(diagnostic)
            except Exception as exc:
                self.logger.debug("Skipping malformed diagnostic row: %s", exc)

        # Fallback when artifact contains summary-level severities that are not
        # represented in diagnostic_details (for example sampled info-only rows).
        by_repo = payload.get("by_repo", {})
        if isinstance(by_repo, dict):
            detail_counts: dict[tuple[str, str], int] = {}
            for diag in diagnostics:
                repo_key = str(diag.repo.value).lower()
                sev_key = str(diag.severity.value).lower()
                detail_counts[(repo_key, sev_key)] = detail_counts.get((repo_key, sev_key), 0) + 1

            synth_index = 0
            for repo_name, repo_summary in by_repo.items():
                if not isinstance(repo_summary, dict):
                    continue
                by_severity = repo_summary.get("by_severity", {})
                if not isinstance(by_severity, dict):
                    continue
                error_count = int(by_severity.get("error", 0) or 0)

                repo_key = str(repo_name).lower()
                repo_enum = repo_map.get(repo_key, RepoName.NUSYQ_HUB)
                repo_path_str = str(repo_summary.get("path") or "unknown_repo")

                if error_count > 0 and detail_counts.get((repo_key, "error"), 0) == 0:
                    diagnostics.append(
                        ErrorDiagnostic(
                            error_id=f"artifact_summary_error_{repo_key}_{synth_index}",
                            severity=ErrorSeverity.ERROR,
                            error_type=ErrorType.LOGIC,
                            repo=repo_enum,
                            file_path=Path(repo_path_str) / "UNKNOWN_ERROR_SUMMARY",
                            line_num=1,
                            column_num=0,
                            message=(
                                f"{error_count} critical errors reported in {repo_name} "
                                "(summary fallback; detail rows unavailable)"
                            ),
                            source="unified_report_summary",
                            suggestion="Run full diagnostics with detailed export and triage these errors first",
                            timestamp=datetime.now().isoformat(),
                        )
                    )
                    synth_index += 1

                warning_count = int(by_severity.get("warning", 0) or 0)
                if warning_count > 0 and detail_counts.get((repo_key, "warning"), 0) == 0:
                    diagnostics.append(
                        ErrorDiagnostic(
                            error_id=f"artifact_summary_warning_{repo_key}_{synth_index}",
                            severity=ErrorSeverity.WARNING,
                            error_type=ErrorType.LOGIC,
                            repo=repo_enum,
                            file_path=Path(repo_path_str) / "UNKNOWN_WARNING_SUMMARY",
                            line_num=1,
                            column_num=0,
                            message=(
                                f"{warning_count} warnings reported in {repo_name} "
                                "(summary fallback; detail rows unavailable)"
                            ),
                            source="unified_report_summary",
                            suggestion="Run full diagnostics with detailed export and triage these warnings",
                            timestamp=datetime.now().isoformat(),
                        )
                    )
                    synth_index += 1

        return diagnostics

    def _create_quest_from_error(self, error: ErrorDiagnostic) -> str | None:
        """Create a quest from an error diagnostic.

        Args:
            error: ErrorDiagnostic to convert to quest

        Returns:
            Quest ID if created, None if skipped
        """
        try:
            # Generate quest title
            file_name = Path(error.file_path).name
            title = f"Fix {error.error_type.value} error in {file_name}:{error.line_num}"

            # Generate description with context
            description = f"""Critical {error.severity.value} detected by {error.source}

**File**: {error.file_path}
**Line**: {error.line_num}
**Error**: {error.message}

**Suggestion**: {error.suggestion or "See error details above"}

**Repository**: {error.repo.value}
**Detected**: {error.timestamp}

This quest was auto-generated by the Error-Quest Bridge.
"""

            # Determine questline based on error type
            questline_map = {
                "linting": "code_quality",
                "type": "type_safety",
                "syntax": "critical_bugs",
                "import": "dependency_management",
                "logic": "critical_bugs",
                "async": "async_architecture",
                "exception": "error_handling",
                "complexity": "refactoring",
            }
            questline = questline_map.get(error.error_type.value, "bug_fixes")

            # Create quest
            quest_result = self.quest_engine.add_quest(
                title=title,
                description=description,
                questline=questline,
                tags=[
                    "auto_generated",
                    "error_driven",
                    error.error_type.value,
                    error.severity.value,
                    error.repo.value,
                ],
                priority="high" if error.severity == ErrorSeverity.ERROR else "medium",
            )

            quest_id: str | None = None
            if isinstance(quest_result, str):
                quest_id = quest_result
            else:
                candidate = getattr(quest_result, "id", None)
                if isinstance(candidate, str):
                    quest_id = candidate

            if not quest_id:
                self.logger.warning(
                    "Quest engine returned unexpected result type for %s:%s",
                    file_name,
                    error.line_num,
                )
                return None

            self.logger.debug(f"✅ Created quest {quest_id[:8]} for error in {file_name}")
            return quest_id

        except Exception as e:
            self.logger.error(f"❌ Failed to create quest from error: {e}")
            return None

    def get_error_quest_stats(self) -> dict[str, Any]:
        """Get statistics about error-generated quests.

        Returns:
            Dictionary with quest statistics
        """
        all_quests = list(self.quest_engine.quests.values())

        error_quests = [
            q for q in all_quests if "auto_generated" in q.tags and "error_driven" in q.tags
        ]

        stats = {
            "total_error_quests": len(error_quests),
            "pending": sum(1 for q in error_quests if q.status == "pending"),
            "active": sum(1 for q in error_quests if q.status == "active"),
            "complete": sum(1 for q in error_quests if q.status == "complete"),
            "by_questline": {},
            "by_repo": {},
        }

        for quest in error_quests:
            # Count by questline
            ql = quest.questline
            stats["by_questline"][ql] = stats["by_questline"].get(ql, 0) + 1

            # Count by repo (extract from tags)
            repo_tags = [t for t in quest.tags if t in ["nusyq-hub", "simulated-verse", "nusyq"]]
            for repo in repo_tags:
                stats["by_repo"][repo] = stats["by_repo"].get(repo, 0) + 1

        return stats


def auto_generate_error_quests(
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    max_quests: int = 5,
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Convenience function to auto-generate quests from errors.

    Args:
        severity: Minimum error severity to create quests for
        max_quests: Maximum number of quests to create
        report_path: Optional precomputed unified error report artifact path

    Returns:
        Dictionary with scan results and created quest IDs
    """
    bridge = ErrorQuestBridge()
    return bridge.scan_and_create_quests(
        severity_threshold=severity,
        max_quests=max_quests,
        report_path=report_path,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.error("🌉 Error-Quest Bridge - Auto-Generating Quests from Critical Errors\n")

    result = auto_generate_error_quests(severity=ErrorSeverity.ERROR, max_quests=10)

    logger.info("\n📊 Scan Results:")
    logger.error(f"   Total errors found: {result['total_errors_found']}")
    logger.info(f"   Quests created: {result['quests_created']}")
    logger.info(f"   Quest IDs: {', '.join([qid[:8] for qid in result['quest_ids']])}")

    # Show stats
    bridge = ErrorQuestBridge()
    stats = bridge.get_error_quest_stats()

    logger.error("\n📈 Error-Quest Statistics:")
    logger.error(f"   Total error quests: {stats['total_error_quests']}")
    logger.info(
        f"   Pending: {stats['pending']}, Active: {stats['active']}, Complete: {stats['complete']}"
    )
    logger.info(f"   By questline: {stats['by_questline']}")
    logger.info(f"   By repository: {stats['by_repo']}")

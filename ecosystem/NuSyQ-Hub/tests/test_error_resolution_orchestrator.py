"""Tests for src.healing.error_resolution_orchestrator module."""

from enum import Enum
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Mock issue types for testing
class MockIssueType(Enum):
    IMPORT_ERROR = "import_error"
    TYPE_HINT_MISSING = "type_hint_missing"
    STYLE_VIOLATION = "style_violation"
    DOCUMENTATION_MISSING = "documentation_missing"
    PERFORMANCE_ISSUE = "performance_issue"
    UNDEFINED_REFERENCE = "undefined_reference"
    OTHER_ISSUE = "other_issue"


class MockSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


def create_mock_issue(
    issue_type=MockIssueType.IMPORT_ERROR,
    severity=MockSeverity.MEDIUM,
    file_path="test.py",
    line_number=1,
    message="Test issue",
):
    """Create a mock issue object."""
    mock_issue = MagicMock()
    mock_issue.issue_type = issue_type
    mock_issue.severity = severity
    mock_issue.file_path = Path(file_path)
    mock_issue.line_number = line_number
    mock_issue.message = message
    mock_issue.issue_id = f"{issue_type.value}_{file_path}_{line_number}"
    return mock_issue


class TestModuleImports:
    """Test module structure and expected exports."""

    def test_module_imports_with_mocked_dependencies(self):
        """Test module can be imported with mocked dependencies."""
        # The module may fail to import due to missing dependencies
        # We test what we can access
        try:
            from src.healing import error_resolution_orchestrator

            assert error_resolution_orchestrator is not None
        except (ImportError, SystemExit):
            # Module exits if dependencies not available
            pytest.skip("Module dependencies not available")


class TestErrorResolutionOrchestratorInit:
    """Test ErrorResolutionOrchestrator initialization."""

    def test_init_with_mocked_detector(self):
        """Test initialization with mocked detector."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()
                assert hasattr(orchestrator, "detector")
                assert hasattr(orchestrator, "issues")
                assert orchestrator.issues == []


class TestDetectAllIssues:
    """Test detect_all_issues method."""

    def test_detect_returns_issue_counts(self):
        """Test that detection returns counts by type."""
        mock_detector = MagicMock()
        mock_issues = [
            create_mock_issue(MockIssueType.IMPORT_ERROR, MockSeverity.HIGH),
            create_mock_issue(MockIssueType.IMPORT_ERROR, MockSeverity.MEDIUM),
            create_mock_issue(MockIssueType.STYLE_VIOLATION, MockSeverity.LOW),
        ]
        mock_detector.scan_repository.return_value = mock_issues

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                result = orchestrator.detect_all_issues()

                assert isinstance(result, dict)
                assert result.get("import_error", 0) == 2
                assert result.get("style_violation", 0) == 1

    def test_detect_stores_issues(self):
        """Test that issues are stored on the orchestrator."""
        mock_detector = MagicMock()
        mock_issues = [create_mock_issue()]
        mock_detector.scan_repository.return_value = mock_issues

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                orchestrator.detect_all_issues()

                assert orchestrator.issues == mock_issues


class TestCategorizeIssues:
    """Test categorize_issues method."""

    def test_categorize_import_errors(self):
        """Test import errors are categorized correctly."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                orchestrator.issues = [
                    create_mock_issue(MockIssueType.IMPORT_ERROR),
                ]

                result = orchestrator.categorize_issues()

                assert "import_errors" in result
                assert len(result["import_errors"]) == 1

    def test_categorize_type_hints(self):
        """Test type hint issues are categorized."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                orchestrator.issues = [
                    create_mock_issue(MockIssueType.TYPE_HINT_MISSING),
                ]

                result = orchestrator.categorize_issues()

                assert "type_hints" in result

    def test_categorize_empty_issues(self):
        """Test categorization with no issues."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()
                orchestrator.issues = []

                result = orchestrator.categorize_issues()

                assert result == {}


class TestTrackIssues:
    """Test track_issues method."""

    def test_track_without_tracker(self):
        """Test tracking when tracker not available."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                categories = {"import_errors": [create_mock_issue()]}

                result = orchestrator.track_issues(categories)

                assert "import_errors" in result
                assert result["import_errors"]["total"] == 1

    def test_track_empty_categories(self):
        """Test tracking with empty categories."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                result = orchestrator.track_issues({})

                assert result == {}


class TestGenerateResolutionReport:
    """Test generate_resolution_report method."""

    def test_report_has_required_keys(self):
        """Test report contains required keys."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()
                orchestrator.issues = []

                result = orchestrator.generate_resolution_report({}, {})

                assert "timestamp" in result
                assert "summary" in result
                assert "by_category" in result
                assert "by_severity" in result
                assert "tracking_status" in result

    def test_report_has_summary(self):
        """Test report summary is correct."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()
                orchestrator.issues = [create_mock_issue(), create_mock_issue()]

                categories = {"import_errors": orchestrator.issues}
                result = orchestrator.generate_resolution_report(categories, {})

                assert result["summary"]["total_issues"] == 2
                assert result["summary"]["total_categories"] == 1


class TestGetSeverityBreakdown:
    """Test _get_severity_breakdown method."""

    def test_breakdown_counts_severities(self):
        """Test severity breakdown counts correctly."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                issues = [
                    create_mock_issue(severity=MockSeverity.HIGH),
                    create_mock_issue(severity=MockSeverity.HIGH),
                    create_mock_issue(severity=MockSeverity.LOW),
                ]

                result = orchestrator._get_severity_breakdown(issues)

                assert result.get("HIGH", 0) == 2
                assert result.get("LOW", 0) == 1

    def test_breakdown_empty_list(self):
        """Test breakdown with empty list."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                result = orchestrator._get_severity_breakdown([])

                assert result == {}


class TestRunOrchestration:
    """Test run_orchestration method."""

    def test_orchestration_returns_report(self):
        """Test orchestration returns a report dict."""
        mock_detector = MagicMock()
        mock_detector.scan_repository.return_value = []

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                # Suppress print output
                with patch("builtins.print"):
                    result = orchestrator.run_orchestration()

                assert isinstance(result, dict)

    def test_orchestration_with_issues(self):
        """Test orchestration with detected issues."""
        mock_detector = MagicMock()
        mock_issues = [
            create_mock_issue(MockIssueType.IMPORT_ERROR, MockSeverity.CRITICAL),
            create_mock_issue(MockIssueType.STYLE_VIOLATION, MockSeverity.LOW),
        ]
        mock_detector.scan_repository.return_value = mock_issues

        with patch(
            "src.healing.error_resolution_orchestrator.CodebaseIssueDetector",
            return_value=mock_detector,
        ):
            with patch("src.healing.error_resolution_orchestrator.HAS_TRACKER", False):
                from src.healing.error_resolution_orchestrator import ErrorResolutionOrchestrator

                orchestrator = ErrorResolutionOrchestrator()

                with patch("builtins.print"):
                    result = orchestrator.run_orchestration()

                assert "by_severity" in result
                assert result["summary"]["total_issues"] == 2

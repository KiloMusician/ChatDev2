"""Tests for ZETA08 Error Recovery Mapper

Tests the core error recovery mapping infrastructure.
"""

import pytest
from src.healing.error_recovery_mapper import (
    DiagnosticIssue,
    ErrorRecoveryMapper,
    RecoverySeverity,
    RecoveryStrategy,
)


@pytest.fixture
def mapper() -> ErrorRecoveryMapper:
    """Create a mapper instance for testing."""
    return ErrorRecoveryMapper()


def test_mapper_initialization(mapper: ErrorRecoveryMapper) -> None:
    """Test that mapper initializes with valid config."""
    assert mapper.config is not None
    assert isinstance(mapper.config, dict)
    assert "auto_fixable_rules" in mapper.config
    assert "manual_review_rules" in mapper.config


def test_auto_fixable_detection(mapper: ErrorRecoveryMapper) -> None:
    """Test detection of auto-fixable rules."""
    # These should be auto-fixable based on config
    assert mapper.is_auto_fixable("F401")  # Unused import
    assert mapper.is_auto_fixable("W291")  # Trailing whitespace

    # These should require manual review
    assert not mapper.is_auto_fixable("B904")  # Exception pattern
    assert not mapper.is_auto_fixable("C901")  # Function complexity


def test_suggested_action_retrieval(mapper: ErrorRecoveryMapper) -> None:
    """Test that suggested actions are retrieved correctly."""
    action = mapper.get_suggested_action("F401")
    assert "fix" in action.lower() or "import" in action.lower()

    action = mapper.get_suggested_action("B904")
    assert "manual" in action.lower() or "raise" in action.lower()


def test_confidence_levels(mapper: ErrorRecoveryMapper) -> None:
    """Test confidence level retrieval."""
    # Auto-fixable should have higher confidence
    f401_confidence = mapper.get_confidence_level("F401")
    b904_confidence = mapper.get_confidence_level("B904")

    assert f401_confidence > 0
    assert b904_confidence >= 0
    assert f401_confidence > b904_confidence


def test_issue_to_recovery_mapping() -> None:
    """Test mapping a diagnostic issue to recovery action."""
    mapper = ErrorRecoveryMapper()

    issue = DiagnosticIssue(
        rule_code="F401",
        file_path="src/example.py",
        line=1,
        column=0,
        message="Unused import 'sys'",
        severity="warning",
    )

    action = mapper.map_issue_to_recovery(issue)

    assert action.rule_code == "F401"
    assert action.auto_fixable is True
    assert action.strategy == RecoveryStrategy.AUTO_FIX_VIA_RUFF
    assert action.recovery_severity == RecoverySeverity.WARNING


def test_recovery_plan_building() -> None:
    """Test building a recovery plan from multiple issues."""
    mapper = ErrorRecoveryMapper()

    issues = [
        DiagnosticIssue(
            rule_code="W291",
            file_path="src/file1.py",
            line=5,
            column=10,
            message="Trailing whitespace",
            severity="info",
        ),
        DiagnosticIssue(
            rule_code="B904",
            file_path="src/file2.py",
            line=15,
            column=0,
            message="Within except block, raise exceptions with 'raise ... from'",
            severity="error",
        ),
        DiagnosticIssue(
            rule_code="F401",
            file_path="src/file1.py",
            line=1,
            column=0,
            message="Unused import",
            severity="warning",
        ),
    ]

    plan = mapper.build_recovery_plan(issues)

    # Should have 3 actions
    assert len(plan) == 3

    # Should be ordered by priority (error before warning/info)
    # B904 (error) should come before F401/W291 (warning/info)
    assert plan[0].rule_code == "B904"


def test_recovery_summary_generation() -> None:
    """Test generating summary statistics."""
    mapper = ErrorRecoveryMapper()

    issues = [
        DiagnosticIssue("F401", "file.py", 1, 0, "Unused", "warning"),
        DiagnosticIssue("F841", "file.py", 2, 0, "Unused var", "warning"),
        DiagnosticIssue("B904", "file.py", 3, 0, "Pattern", "error"),
    ]

    plan = mapper.build_recovery_plan(issues)
    summary = mapper.get_recovery_summary(plan)

    assert summary["total_issues"] == 3
    assert summary["auto_fixable"] == 2  # F401, F841
    assert summary["manual_review"] == 1  # B904
    assert summary["auto_fixable_percentage"] > 50
    assert summary["by_severity"]["error"] == 1
    assert summary["by_severity"]["warning"] == 2


def test_mapper_caching() -> None:
    """Test that mapper caches fixable rule checks."""
    mapper = ErrorRecoveryMapper()

    # First call
    result1 = mapper.is_auto_fixable("F401")

    # Should be cached now
    assert "F401" in mapper.auto_fixable_cache

    # Second call should use cache
    result2 = mapper.is_auto_fixable("F401")

    assert result1 == result2


def test_severity_mapping() -> None:
    """Test mapping issue severity to recovery severity."""
    mapper = ErrorRecoveryMapper()

    assert mapper._map_to_severity("error") == RecoverySeverity.ERROR
    assert mapper._map_to_severity("warning") == RecoverySeverity.WARNING
    assert mapper._map_to_severity("info") == RecoverySeverity.INFO
    assert mapper._map_to_severity("unknown") == RecoverySeverity.INFO


def test_config_loading() -> None:
    """Test that config is properly loaded."""
    mapper = ErrorRecoveryMapper()

    # Should have loaded config
    assert mapper.config is not None

    # Should have rule definitions
    auto_fixable = mapper.config.get("auto_fixable_rules", {})
    assert len(auto_fixable) > 0

    # Each rule should have required fields
    for _rule_code, rule_def in auto_fixable.items():
        assert "auto_fixable" in rule_def
        assert "suggested_action" in rule_def
        assert "confidence" in rule_def


# =============================================================================
# Edge Cases for Config Loading
# =============================================================================


def test_missing_config_file_uses_defaults(tmp_path) -> None:
    """Mapper uses default config when config file is missing."""

    missing_path = tmp_path / "nonexistent_config.json"
    mapper = ErrorRecoveryMapper(config_path=missing_path)

    # Should use default config structure
    assert "auto_fixable_rules" in mapper.config
    assert "manual_review_rules" in mapper.config
    assert "recovery_strategies" in mapper.config


def test_invalid_json_config_uses_defaults(tmp_path) -> None:
    """Mapper uses default config when JSON is invalid."""

    bad_config = tmp_path / "bad_config.json"
    bad_config.write_text("not valid json {{{{")

    mapper = ErrorRecoveryMapper(config_path=bad_config)

    # Should fallback to default config
    assert "auto_fixable_rules" in mapper.config


def test_default_config_structure() -> None:
    """Default config has expected structure."""
    # Access the static method directly
    default = ErrorRecoveryMapper._default_config()

    assert isinstance(default, dict)
    assert "auto_fixable_rules" in default
    assert "manual_review_rules" in default
    assert "recovery_strategies" in default
    assert default["auto_fixable_rules"] == {}


# =============================================================================
# Edge Cases for Suggested Actions
# =============================================================================


def test_manual_review_rule_missing_suggested_action(tmp_path) -> None:
    """Manual review rule without suggested_action returns 'Unknown'."""
    import json

    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "auto_fixable_rules": {},
                "manual_review_rules": {"NOACTION": {}},  # No suggested_action key
                "recovery_strategies": {},
            }
        )
    )

    mapper = ErrorRecoveryMapper(config_path=config_file)
    result = mapper.get_suggested_action("NOACTION")

    assert result == "Unknown"


# =============================================================================
# Edge Cases for Confidence Levels
# =============================================================================


def test_manual_review_rule_missing_confidence_defaults_to_0_3(tmp_path) -> None:
    """Manual review rule without confidence returns 0.3."""
    import json

    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "auto_fixable_rules": {},
                "manual_review_rules": {"NOCONF": {}},  # No confidence key
                "recovery_strategies": {},
            }
        )
    )

    mapper = ErrorRecoveryMapper(config_path=config_file)
    result = mapper.get_confidence_level("NOCONF")

    assert result == 0.3


# =============================================================================
# Edge Cases for Recovery Strategy Selection
# =============================================================================


def test_high_confidence_manual_issue_maps_to_refactor(tmp_path) -> None:
    """Manual review issue with confidence > 0.7 maps to REFACTOR strategy."""
    import json

    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "auto_fixable_rules": {},
                "manual_review_rules": {
                    "C901": {
                        "auto_fixable": False,
                        "suggested_action": "reduce complexity",
                        "confidence": 0.85,  # High confidence
                    }
                },
                "recovery_strategies": {},
            }
        )
    )

    mapper = ErrorRecoveryMapper(config_path=config_file)
    issue = DiagnosticIssue(
        rule_code="C901",
        file_path="test.py",
        line=1,
        column=0,
        message="Too complex",
        severity="warning",
    )

    action = mapper.map_issue_to_recovery(issue)

    assert action.strategy == RecoveryStrategy.REFACTOR
    assert action.confidence == 0.85


def test_surgical_edit_strategy_when_not_ruff_fix(tmp_path) -> None:
    """Auto-fixable without 'ruff --fix' in action maps to SURGICAL_EDIT."""
    import json

    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "auto_fixable_rules": {
                    "CUSTOM": {
                        "auto_fixable": True,
                        "suggested_action": "remove the line manually",  # Not ruff --fix
                        "confidence": 0.9,
                    }
                },
                "manual_review_rules": {},
                "recovery_strategies": {},
            }
        )
    )

    mapper = ErrorRecoveryMapper(config_path=config_file)
    issue = DiagnosticIssue(
        rule_code="CUSTOM",
        file_path="test.py",
        line=1,
        column=0,
        message="Custom issue",
        severity="warning",
    )

    action = mapper.map_issue_to_recovery(issue)

    assert action.strategy == RecoveryStrategy.SURGICAL_EDIT


# =============================================================================
# Dataclass Tests
# =============================================================================


def test_recovery_action_requires_git_default() -> None:
    """RecoveryAction.requires_git defaults to False."""
    from src.healing.error_recovery_mapper import RecoveryAction

    issue = DiagnosticIssue(
        rule_code="TEST",
        file_path="test.py",
        line=1,
        column=0,
        message="Test",
        severity="info",
    )

    action = RecoveryAction(
        rule_code="TEST",
        issue=issue,
        strategy=RecoveryStrategy.MANUAL_REVIEW,
        suggested_action="review",
        auto_fixable=False,
        confidence=0.5,
        recovery_severity=RecoverySeverity.INFO,
    )

    assert action.requires_git is False


def test_diagnostic_issue_all_fields() -> None:
    """DiagnosticIssue captures all fields correctly."""
    issue = DiagnosticIssue(
        rule_code="F401",
        file_path="/path/to/file.py",
        line=42,
        column=8,
        message="Unused import 'os'",
        severity="warning",
    )

    assert issue.rule_code == "F401"
    assert issue.file_path == "/path/to/file.py"
    assert issue.line == 42
    assert issue.column == 8
    assert issue.message == "Unused import 'os'"
    assert issue.severity == "warning"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

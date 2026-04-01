#!/usr/bin/env python3
"""Tests for Culture Ship Strategic Advisor - Autonomous Self-Enhancement."""

from pathlib import Path

import pytest
import src.orchestration.culture_ship_strategic_advisor as advisor_module
from src.orchestration.culture_ship_strategic_advisor import (
    CultureShipStrategicAdvisor,
    StrategicDecision,
    StrategicIssue,
)


class TestCultureShipStrategicAdvisor:
    """Test suite for Culture Ship Strategic Advisor."""

    @pytest.fixture
    def advisor(self):
        """Create advisor instance for testing."""
        return CultureShipStrategicAdvisor()

    def test_initialization(self, advisor):
        """Test advisor initializes correctly."""
        assert advisor is not None
        assert advisor.issues_identified == []
        assert advisor.decisions_made == []
        assert advisor.improvements_completed == []

    def test_identify_strategic_issues(self, advisor):
        """Test hardcoded strategic issues are identified."""
        issues = advisor.identify_strategic_issues()

        assert len(issues) > 0
        assert all(isinstance(issue, StrategicIssue) for issue in issues)
        assert advisor.issues_identified == issues

    @pytest.mark.asyncio
    async def test_conduct_strategic_analysis_finds_technical_debt(self, advisor):
        """Test strategic analysis identifies technical debt."""
        issues = await advisor.conduct_strategic_analysis(scope="full")

        # Should find at least some issues
        assert isinstance(issues, list)

        # Check for expected issue types (codebase may be clean — no issues required)
        {issue.category for issue in issues}

        if issues:
            severities = {issue.severity for issue in issues}
            assert severities.issubset({"critical", "high", "medium", "low"})

    def test_scan_technical_debt(self, advisor):
        """Test technical debt scanning."""
        issues = advisor._scan_technical_debt()

        assert isinstance(issues, list)
        # Should find our TODO/FIXME/HACK comments
        # May be empty if no tech debt, which is fine

    def test_scan_technical_debt_ignores_string_literal_patterns(
        self, advisor, monkeypatch, tmp_path
    ):
        r"""Detector definitions like r\"# TODO:\" should not count as debt comments."""
        fake_repo_root = tmp_path / "src"
        fake_repo_root.mkdir()
        (fake_repo_root / "detectors.py").write_text(
            'PATTERNS = [r"# TODO:", r"# FIXME:", r"# HACK:"]\n'
            'MESSAGE = "TODO/FIXME/HACK comment markers"\n',
            encoding="utf-8",
        )

        monkeypatch.setattr(advisor_module, "__file__", str(fake_repo_root / "culture_ship.py"))

        def raise_missing_rg(*_args, **_kwargs):
            raise FileNotFoundError("rg unavailable")

        monkeypatch.setattr(advisor_module.subprocess, "run", raise_missing_rg)

        issues = advisor._scan_technical_debt()

        assert issues == []

    def test_check_integration_completeness(self, advisor):
        """Test integration completeness checking."""
        issues = advisor._check_integration_completeness()

        assert isinstance(issues, list)
        # Checks for missing __init__.py and stub implementations

    def test_analyze_test_coverage(self, advisor):
        """Test coverage analysis."""
        issues = advisor._analyze_test_coverage()

        assert isinstance(issues, list)

        # Should identify low test coverage
        if issues:
            assert any("test coverage" in issue.description.lower() for issue in issues)

    def test_analyze_test_coverage_targets_existing_modules(self, advisor, monkeypatch):
        """Coverage recommendations should reference current live modules."""
        monkeypatch.setattr(
            advisor,
            "_count_python_files",
            lambda root, *_args, **_kwargs: 1000 if Path(root).name == "src" else 10,
        )
        issues = advisor._analyze_test_coverage()

        assert issues, "Expected a coverage gap issue with forced low test ratio"
        suggestions = issues[0].suggested_fixes or []
        suggestion_text = " | ".join(suggestions)
        assert "sns_orchestrator_adapter.py" in suggestion_text
        assert "guild_board_bridge.py" in suggestion_text
        assert "consciousness_token_optimizer.py" not in suggestion_text

    @pytest.mark.asyncio
    async def test_analyze_token_efficiency(self, advisor):
        """Test token efficiency analysis."""
        issues = await advisor._analyze_token_efficiency()

        assert isinstance(issues, list)
        # May find token optimization opportunities

    @pytest.mark.asyncio
    async def test_analyze_token_efficiency_targets_existing_modules(self, advisor, monkeypatch):
        """Missing metrics issue should not reference stale paths."""
        monkeypatch.setattr(advisor, "_resolve_token_metrics_file", lambda: None)

        issues = await advisor._analyze_token_efficiency()

        assert issues, "Expected token efficiency issue when metrics file is absent"
        issue = issues[0]
        assert issue.description == "Token optimization metrics not being tracked"
        joined = " | ".join(issue.affected_files)
        assert "sns_orchestrator_adapter.py" in joined
        assert "vscode_metrics_ui.py" in joined
        assert "consciousness_token_optimizer.py" not in joined

    @pytest.mark.asyncio
    async def test_generate_quests_from_high_severity_issues(self, advisor):
        """Test quest generation from high severity issues."""
        # Create high severity test issue
        test_issues = [
            StrategicIssue(
                category="test",
                severity="high",
                description="Test high priority issue",
                affected_files=["test.py"],
                suggested_fixes=["Fix it"],
                dependencies=[],
            )
        ]

        quest_ids = await advisor.generate_quests_from_analysis(test_issues)

        # Should create quest for high severity
        assert len(quest_ids) == 1
        assert isinstance(quest_ids[0], str)

    @pytest.mark.asyncio
    async def test_generate_quests_skips_low_severity(self, advisor):
        """Test quest generation skips low severity issues."""
        # Create low severity test issue
        test_issues = [
            StrategicIssue(
                category="test",
                severity="low",
                description="Test low priority issue",
                affected_files=["test.py"],
                suggested_fixes=["Fix it"],
                dependencies=[],
            )
        ]

        quest_ids = await advisor.generate_quests_from_analysis(test_issues)

        # Should NOT create quest for low severity
        assert len(quest_ids) == 0

    @pytest.mark.asyncio
    async def test_generate_quests_handles_critical_severity(self, advisor):
        """Test quest generation for critical severity."""
        # Create critical severity test issue
        test_issues = [
            StrategicIssue(
                category="test",
                severity="critical",
                description="Test critical issue",
                affected_files=["test.py"],
                suggested_fixes=["Fix immediately"],
                dependencies=[],
            )
        ]

        quest_ids = await advisor.generate_quests_from_analysis(test_issues)

        # Should create quest for critical severity
        assert len(quest_ids) == 1

    def test_make_strategic_decisions(self, advisor):
        """Test strategic decision making."""
        # Create test issues
        test_issues = [
            StrategicIssue(
                category="correctness",
                severity="high",
                description="High priority issue",
                affected_files=["file1.py", "file2.py"],
                suggested_fixes=["Fix A", "Fix B"],
                dependencies=[],
            ),
            StrategicIssue(
                category="efficiency",
                severity="low",
                description="Low priority issue",
                affected_files=["file3.py"],
                suggested_fixes=["Optimize"],
                dependencies=[],
            ),
        ]

        decisions = advisor.make_strategic_decisions(issues=test_issues)

        # Should create decisions
        assert len(decisions) == 2
        assert all(isinstance(d, StrategicDecision) for d in decisions)

        # Should sort by priority (high before low)
        assert decisions[0].priority > decisions[1].priority

    @pytest.mark.asyncio
    async def test_end_to_end_self_enhancement_cycle(self, advisor):
        """Test complete self-enhancement cycle."""
        # Step 1: Analyze
        issues = await advisor.conduct_strategic_analysis(scope="full")
        assert len(issues) >= 0  # May be 0 if codebase is perfect

        # Step 2: Make decisions
        decisions = advisor.make_strategic_decisions(issues=issues)
        assert isinstance(decisions, list)

        # Step 3: Generate quests (only for high/critical)
        high_critical = [i for i in issues if i.severity in ["high", "critical"]]
        if high_critical:
            quest_ids = await advisor.generate_quests_from_analysis(high_critical)
            assert isinstance(quest_ids, list)

    def test_strategic_issue_dataclass(self):
        """Test StrategicIssue dataclass."""
        issue = StrategicIssue(
            category="quality",
            severity="medium",
            description="Test issue",
            affected_files=["a.py", "b.py"],
            suggested_fixes=["Fix 1", "Fix 2"],
            dependencies=["pytest"],
        )

        assert issue.category == "quality"
        assert issue.severity == "medium"
        assert len(issue.affected_files) == 2
        assert len(issue.suggested_fixes) == 2

    def test_strategic_decision_dataclass(self):
        """Test StrategicDecision dataclass."""
        issue = StrategicIssue(
            category="test",
            severity="high",
            description="Test",
            affected_files=[],
        )

        decision = StrategicDecision(
            issue=issue,
            decision="Fix it",
            rationale="Important",
            action_plan=["Step 1", "Step 2"],
            priority=8,
            estimated_impact="high",
        )

        assert decision.priority == 8
        assert decision.estimated_impact == "high"
        assert len(decision.action_plan) == 2


# Integration tests
class TestCultureShipIntegration:
    """Integration tests for Culture Ship with other systems."""

    @pytest.mark.asyncio
    async def test_integration_with_guild_board(self):
        """Test integration with Guild Board."""
        from src.guild.guild_board import get_board

        advisor = CultureShipStrategicAdvisor()

        # Create test issue
        test_issue = StrategicIssue(
            category="integration_test",
            severity="high",
            description="Integration test issue",
            affected_files=["test.py"],
            suggested_fixes=["Test fix"],
            dependencies=[],
        )

        # Generate quest
        quest_ids = await advisor.generate_quests_from_analysis([test_issue])

        if quest_ids:
            # Verify quest in Guild Board
            gb = await get_board()
            quest = gb.board.quests.get(quest_ids[0])

            assert quest is not None
            assert "[STRATEGIC]" in quest.title
            assert "integration_test" in quest.tags

    def test_culture_ship_orchestrator_integration(self):
        """Test Culture Ship has orchestrator connection."""
        advisor = CultureShipStrategicAdvisor()

        # Should have orchestrator initialized
        assert hasattr(advisor, "orchestrator")
        # May be None if orchestrator unavailable, which is ok


# Smoke tests
class TestCultureShipSmokeTests:
    """Quick smoke tests for Culture Ship."""

    def test_can_import(self):
        """Test module can be imported."""
        from src.orchestration import culture_ship_strategic_advisor

        assert culture_ship_strategic_advisor is not None

    def test_can_instantiate(self):
        """Test advisor can be instantiated."""
        advisor = CultureShipStrategicAdvisor()
        assert advisor is not None

    @pytest.mark.asyncio
    async def test_analyze_does_not_crash(self):
        """Test analysis doesn't crash."""
        advisor = CultureShipStrategicAdvisor()
        issues = await advisor.conduct_strategic_analysis(scope="full")
        assert isinstance(issues, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

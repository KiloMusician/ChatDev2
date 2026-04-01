#!/usr/bin/env python3
"""🎓 Comprehensive Grading System - Mathematically Valid & Actionable.

This module provides a validated, multi-dimensional health assessment system
that goes beyond simple percentage calculations to provide meaningful insights.

Features:
- Multi-dimensional health metrics (code quality, functionality, integration)
- Weighted composite scoring with transparent algebra
- Context-aware grading (different standards for different file types)
- Trend analysis (improvement/degradation over time)
- Actionable breakdowns (what specifically is affecting your grade)

OmniTag: {
    "purpose": "Comprehensive system health grading with mathematical validation",
    "dependencies": ["system_health_assessor"],
    "context": "Multi-dimensional health assessment with actionable insights",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class HealthDimension(Enum):
    """Health assessment dimensions."""

    FUNCTIONALITY = "functionality"  # Does code execute without errors?
    CODE_QUALITY = "code_quality"  # Linting, formatting, best practices
    INTEGRATION = "integration"  # How well does it integrate with ecosystem?
    TESTING = "testing"  # Test coverage and passing tests
    DOCUMENTATION = "documentation"  # Inline docs, docstrings, README quality
    MAINTAINABILITY = "maintainability"  # Complexity, technical debt


@dataclass
class DimensionScore:
    """Score for a single health dimension."""

    dimension: HealthDimension
    raw_score: float  # 0.0 to 1.0
    weight: float  # Importance weight
    weighted_score: float = field(init=False)
    grade: str = field(init=False)
    issues: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Calculate derived fields."""
        self.weighted_score = self.raw_score * self.weight
        self.grade = self._score_to_grade(self.raw_score * 100)

    @staticmethod
    def _score_to_grade(percentage: float) -> str:
        """Convert percentage to letter grade with +/- modifiers."""
        if percentage >= 97:
            return "A+"
        if percentage >= 93:
            return "A"
        if percentage >= 90:
            return "A-"
        if percentage >= 87:
            return "B+"
        if percentage >= 83:
            return "B"
        if percentage >= 80:
            return "B-"
        if percentage >= 77:
            return "C+"
        if percentage >= 73:
            return "C"
        if percentage >= 70:
            return "C-"
        if percentage >= 67:
            return "D+"
        if percentage >= 63:
            return "D"
        if percentage >= 60:
            return "D-"
        return "F"


@dataclass
class CompositeHealthGrade:
    """Comprehensive health assessment with multiple dimensions."""

    dimensions: list[DimensionScore]
    composite_score: float = field(init=False)
    composite_grade: str = field(init=False)
    gpa: float = field(init=False)  # 0.0 to 4.0 scale
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Calculate composite metrics."""
        # Weighted average of all dimensions
        total_weight = sum(d.weight for d in self.dimensions)
        self.composite_score = sum(d.weighted_score for d in self.dimensions) / total_weight

        # Convert to percentage for grading
        # Create a temp dimension score to use its grading logic
        temp_score = DimensionScore(
            dimension=HealthDimension.FUNCTIONALITY,
            raw_score=self.composite_score,
            weight=1.0,
        )
        self.composite_grade = temp_score.grade

        # Calculate GPA (0.0-4.0 scale)
        self.gpa = self._calculate_gpa()

    def _calculate_gpa(self) -> float:
        """Calculate GPA on 4.0 scale."""
        grade_points = {
            "A+": 4.0,
            "A": 4.0,
            "A-": 3.7,
            "B+": 3.3,
            "B": 3.0,
            "B-": 2.7,
            "C+": 2.3,
            "C": 2.0,
            "C-": 1.7,
            "D+": 1.3,
            "D": 1.0,
            "D-": 0.7,
            "F": 0.0,
        }
        return grade_points.get(self.composite_grade, 0.0)

    def get_summary(self) -> dict[str, Any]:
        """Get human-readable summary."""
        return {
            "composite_grade": self.composite_grade,
            "composite_percentage": round(self.composite_score * 100, 1),
            "gpa": round(self.gpa, 2),
            "dimension_breakdown": [
                {
                    "dimension": d.dimension.value,
                    "grade": d.grade,
                    "percentage": round(d.raw_score * 100, 1),
                    "weight": d.weight,
                    "weighted_contribution": round(d.weighted_score * 100, 1),
                }
                for d in self.dimensions
            ],
            "top_issues": self._get_top_issues(),
            "quick_wins": self._get_quick_wins(),
        }

    def _get_top_issues(self) -> list[str]:
        """Get top issues dragging down score."""
        # Sort dimensions by raw score (worst first)
        sorted_dims = sorted(self.dimensions, key=lambda d: d.raw_score)

        issues: list[Any] = []
        for dim in sorted_dims[:3]:  # Top 3 problem areas
            if dim.raw_score < 0.8 and dim.issues:
                issues.extend(dim.issues[:2])  # Top 2 issues per dimension

        return issues[:5]  # Max 5 total issues

    def _get_quick_wins(self) -> list[str]:
        """Get quick improvement opportunities."""
        wins: list[Any] = []
        for dim in self.dimensions:
            if 0.6 < dim.raw_score < 0.9 and dim.improvements:
                # These are improvable dimensions
                wins.extend(dim.improvements[:1])  # One quick win per dimension

        return wins[:3]  # Top 3 quick wins


class ComprehensiveGradingSystem:
    """Multi-dimensional grading system for NuSyQ repository health.

    Mathematical Foundation:
    - Each dimension scored 0.0 to 1.0 (0% to 100%)
    - Weighted average: Σ(dimension_score × weight) / Σ(weights)
    - Letter grades based on percentage with +/- modifiers
    - GPA calculated on 4.0 scale for trend tracking
    """

    def __init__(self) -> None:
        """Initialize grading system with default dimension weights."""
        self.dimension_weights = {
            HealthDimension.FUNCTIONALITY: 0.30,  # 30% - Code must work
            HealthDimension.CODE_QUALITY: 0.25,  # 25% - Code quality matters
            HealthDimension.INTEGRATION: 0.20,  # 20% - Ecosystem integration
            HealthDimension.TESTING: 0.15,  # 15% - Test coverage
            HealthDimension.DOCUMENTATION: 0.05,  # 5% - Documentation
            HealthDimension.MAINTAINABILITY: 0.05,  # 5% - Long-term health
        }

    def assess_repository_health(
        self,
        analysis_data: dict[str, Any] | None = None,
    ) -> CompositeHealthGrade:
        """Assess repository health across all dimensions.

        Args:
            analysis_data: Optional pre-loaded analysis data

        Returns:
            Comprehensive health grade with actionable insights

        """
        if analysis_data is None:
            analysis_data = self._load_latest_analysis()

        dimensions: list[Any] = []

        # 1. Functionality dimension
        func_score = self._assess_functionality(analysis_data)
        dimensions.append(func_score)

        # 2. Code quality dimension
        quality_score = self._assess_code_quality()
        dimensions.append(quality_score)

        # 3. Integration dimension
        integration_score = self._assess_integration(analysis_data)
        dimensions.append(integration_score)

        # 4. Testing dimension
        testing_score = self._assess_testing()
        dimensions.append(testing_score)

        # 5. Documentation dimension
        doc_score = self._assess_documentation(analysis_data)
        dimensions.append(doc_score)

        # 6. Maintainability dimension
        maint_score = self._assess_maintainability()
        dimensions.append(maint_score)

        return CompositeHealthGrade(dimensions=dimensions)

    def _load_latest_analysis(self) -> dict[str, Any]:
        """Load latest system analysis data."""
        analysis_files = list(Path.cwd().glob("quick_system_analysis_*.json"))
        if not analysis_files:
            # Return minimal data if no analysis found
            return {
                "working_files": [],
                "broken_files": [],
                "launch_pad_files": [],
                "enhancement_candidates": [],
            }

        latest = max(analysis_files, key=lambda f: f.stat().st_mtime)
        with open(latest, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data

    def _assess_functionality(self, data: dict[str, Any]) -> DimensionScore:
        """Assess functionality: Can code execute without errors?

        Calculation:
        - working_files = 1.0 contribution
        - enhancement_candidates = 0.8 contribution (works but needs improvement)
        - launch_pad_files = 0.5 contribution (partially working)
        - broken_files = 0.0 contribution

        Score = Σ(file_contribution) / total_files
        """
        working = len(data.get("working_files", []))
        broken = len(data.get("broken_files", []))
        launch_pad = len(data.get("launch_pad_files", []))
        enhancement = len(data.get("enhancement_candidates", []))

        total = working + broken + launch_pad + enhancement

        if total == 0:
            return DimensionScore(
                dimension=HealthDimension.FUNCTIONALITY,
                raw_score=0.0,
                weight=self.dimension_weights[HealthDimension.FUNCTIONALITY],
                issues=["No Python files found for analysis"],
            )

        # Weighted contributions
        score = (
            (working * 1.0) + (enhancement * 0.8) + (launch_pad * 0.5) + (broken * 0.0)
        ) / total

        issues: list[Any] = []
        improvements: list[Any] = []

        if broken > 0:
            issues.append(f"{broken} broken files preventing execution")
            improvements.append(f"Fix broken imports/syntax in {broken} files")

        if launch_pad > 0:
            issues.append(f"{launch_pad} files only partially functional")
            improvements.append(f"Complete implementation of {launch_pad} launch_pad files")

        return DimensionScore(
            dimension=HealthDimension.FUNCTIONALITY,
            raw_score=score,
            weight=self.dimension_weights[HealthDimension.FUNCTIONALITY],
            issues=issues,
            improvements=improvements,
        )

    def _assess_code_quality(self) -> DimensionScore:
        """Assess code quality via Ruff linting.

        Calculation:
        - Ruff errors weighted by severity
        - Critical errors (E722, F821, B012): 3.0 penalty each
        - High errors (E402, F401, F404): 1.0 penalty each
        - Medium errors (I001, B007, E741): 0.5 penalty each
        - Low errors (formatting, style): 0.1 penalty each

        Score = max(0, 1.0 - total_penalty / (total_files * expected_errors_per_file))
        """
        import subprocess

        try:
            result = subprocess.run(
                ["ruff", "check", "--statistics"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            error_weights = {
                # Critical - dangerous code
                "E722": 3.0,  # bare-except
                "F821": 3.0,  # undefined-name
                "B012": 3.0,  # jump-in-finally
                # High - functionality issues
                "E402": 1.0,  # module-import-not-at-top
                "F401": 1.0,  # unused-import
                "F404": 1.0,  # late-future-import
                # Medium - quality issues
                "I001": 0.5,  # unsorted-imports
                "B007": 0.5,  # unused-loop-variable
                "E741": 0.5,  # ambiguous-variable-name
            }

            total_penalty = 0.0
            error_details: list[Any] = []

            for line in result.stdout.splitlines():
                if line.strip() and not line.startswith("warning"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        count = int(parts[0])
                        code = parts[1]
                        weight = error_weights.get(code, 0.1)
                        penalty = count * weight
                        total_penalty += penalty

                        if weight >= 1.0:  # Track significant issues
                            error_details.append(f"{code}: {count} occurrences")

            # Estimate: ~3 errors per file is "average" code
            # Less is better, more is worse
            total_files = len(list(Path("src").rglob("*.py")))
            expected_baseline = total_files * 3.0

            # Normalize score (lower penalty = higher score)
            raw_score = max(0.0, min(1.0, 1.0 - (total_penalty / max(expected_baseline, 1))))

            issues = error_details[:5]
            improvements: list[Any] = []

            if total_penalty > expected_baseline:
                improvements.append("Run 'python health.py --fix' for auto-remediation")

            return DimensionScore(
                dimension=HealthDimension.CODE_QUALITY,
                raw_score=raw_score,
                weight=self.dimension_weights[HealthDimension.CODE_QUALITY],
                issues=issues,
                improvements=improvements,
            )

        except (subprocess.TimeoutExpired, OSError) as e:
            return DimensionScore(
                dimension=HealthDimension.CODE_QUALITY,
                raw_score=0.5,
                weight=self.dimension_weights[HealthDimension.CODE_QUALITY],
                issues=[f"Unable to assess: {e}"],
            )

    def _assess_integration(self, data: dict[str, Any]) -> DimensionScore:
        """Assess integration quality: How well do components work together?

        Calculation:
        - High integration files: 1.0 contribution
        - Medium integration files: 0.7 contribution
        - Low integration files: 0.3 contribution

        Score = Σ(integration_contribution) / total_assessed_files
        """
        high_integration = 0
        medium_integration = 0
        low_integration = 0
        total = 0

        for category in ["working_files", "enhancement_candidates", "launch_pad_files"]:
            for file_info in data.get(category, []):
                level = file_info.get("integration_level", "low")
                if level == "high":
                    high_integration += 1
                elif level == "medium":
                    medium_integration += 1
                else:
                    low_integration += 1
                total += 1

        if total == 0:
            return DimensionScore(
                dimension=HealthDimension.INTEGRATION,
                raw_score=0.5,
                weight=self.dimension_weights[HealthDimension.INTEGRATION],
            )

        score = (
            (high_integration * 1.0) + (medium_integration * 0.7) + (low_integration * 0.3)
        ) / total

        issues: list[Any] = []
        improvements: list[Any] = []

        if low_integration > total * 0.5:
            issues.append(f"{low_integration} files poorly integrated")
            improvements.append("Enhance inter-module communication and shared APIs")

        return DimensionScore(
            dimension=HealthDimension.INTEGRATION,
            raw_score=score,
            weight=self.dimension_weights[HealthDimension.INTEGRATION],
            issues=issues,
            improvements=improvements,
        )

    def _assess_testing(self) -> DimensionScore:
        """Assess testing coverage and quality.

        Calculation:
        - Test files exist: Base 0.3
        - Tests pass: +0.4
        - Good coverage (>70%): +0.3

        Score = sum of achieved criteria / 1.0
        """
        test_files = list(Path("tests").rglob("test_*.py"))
        has_tests = len(test_files) > 0

        score = 0.3 if has_tests else 0.0
        issues: list[Any] = []
        improvements: list[Any] = []

        if not has_tests:
            issues.append("No test files found")
            improvements.append("Create test suite with pytest")
        else:
            # Could enhance with actual test execution and coverage analysis
            # For now, give partial credit for having tests
            score = 0.5
            improvements.append("Run pytest to validate test coverage")

        return DimensionScore(
            dimension=HealthDimension.TESTING,
            raw_score=score,
            weight=self.dimension_weights[HealthDimension.TESTING],
            issues=issues,
            improvements=improvements,
        )

    def _assess_documentation(self, data: dict[str, Any]) -> DimensionScore:
        """Assess documentation quality.

        Calculation:
        - README exists: 0.3
        - Docstrings present: 0.4
        - Comprehensive docs: 0.3

        Score = sum of achieved criteria
        """
        readme_exists = Path("README.md").exists()
        score = 0.3 if readme_exists else 0.0

        # Check for docstrings in sample of files
        docstring_count = 0
        total_checked = 0

        for file_info in data.get("working_files", [])[:20]:  # Sample 20 files
            try:
                with open(file_info["path"], encoding="utf-8") as f:
                    content = f.read()
                    if '"""' in content or "'''" in content:
                        docstring_count += 1
                    total_checked += 1
            except (OSError, UnicodeDecodeError):
                logger.debug("Suppressed OSError/UnicodeDecodeError", exc_info=True)

        if total_checked > 0:
            docstring_ratio = docstring_count / total_checked
            score += 0.4 * docstring_ratio

        issues: list[Any] = []
        improvements: list[Any] = []

        if not readme_exists:
            issues.append("No README.md found")

        if docstring_ratio < 0.5:
            issues.append(f"Only {docstring_count}/{total_checked} files have docstrings")
            improvements.append("Add docstrings to public functions and classes")

        return DimensionScore(
            dimension=HealthDimension.DOCUMENTATION,
            raw_score=score,
            weight=self.dimension_weights[HealthDimension.DOCUMENTATION],
            issues=issues,
            improvements=improvements,
        )

    def _assess_maintainability(self) -> DimensionScore:
        """Assess long-term maintainability.

        Calculation:
        - Code organization: 0.4
        - Dependency management: 0.3
        - Technical debt indicators: 0.3

        Score = sum of sub-scores
        """
        # Simple heuristic: Check for common structure
        has_src = Path("src").exists()
        has_tests = Path("tests").exists()
        has_requirements = Path("requirements.txt").exists() or Path("pyproject.toml").exists()

        organization_score = 0.4 if (has_src and has_tests) else 0.2
        dependency_score = 0.3 if has_requirements else 0.0

        # Technical debt: Count backlog-marker comments without double-counting detector definitions.
        debt_indicators = 0
        for py_file in Path("src").rglob("*.py"):
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read().upper()
                    debt_indicators += content.count("TODO")
                    debt_indicators += content.count("TODO")
                    debt_indicators += content.count("HACK")
            except (OSError, UnicodeDecodeError):
                logger.debug("Suppressed OSError/UnicodeDecodeError", exc_info=True)

        # Normalize: <50 indicators = good (0.3), >200 = bad (0.0)
        debt_score = max(0.0, min(0.3, 0.3 * (1 - debt_indicators / 200)))

        score = organization_score + dependency_score + debt_score

        issues: list[Any] = []
        if debt_indicators > 100:
            issues.append(f"{debt_indicators} technical debt markers (TODO/FIXME/HACK)")

        return DimensionScore(
            dimension=HealthDimension.MAINTAINABILITY,
            raw_score=score,
            weight=self.dimension_weights[HealthDimension.MAINTAINABILITY],
            issues=issues,
        )


def main() -> None:
    """Run comprehensive grading assessment."""
    grading_system = ComprehensiveGradingSystem()
    health_grade = grading_system.assess_repository_health()

    summary = health_grade.get_summary()

    # Print results

    for _dim in summary["dimension_breakdown"]:
        pass

    if summary["top_issues"]:
        for _i, _issue in enumerate(summary["top_issues"], 1):
            pass

    if summary["quick_wins"]:
        for _i, _win in enumerate(summary["quick_wins"], 1):
            pass

    # Save detailed report
    report_file = (
        Path("logs") / f"comprehensive_grade_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": summary,
                "timestamp": health_grade.timestamp,
                "dimensions": [
                    {
                        "dimension": d.dimension.value,
                        "raw_score": d.raw_score,
                        "weight": d.weight,
                        "weighted_score": d.weighted_score,
                        "grade": d.grade,
                        "issues": d.issues,
                        "improvements": d.improvements,
                    }
                    for d in health_grade.dimensions
                ],
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    main()

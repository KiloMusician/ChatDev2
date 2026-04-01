"""Risk Scorer - Assess and govern patch risk levels.

This module implements a 4-tier governance system:
- AUTO: Low risk, can merge automatically (<0.3 score)
- REVIEW: Medium risk, needs human review (0.3-0.6 score)
- PROPOSAL: High risk, create proposal package (0.6-0.8 score)
- BLOCKED: Critical risk, user action required (>0.8 score)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar

from src.autonomy.patch_builder import PatchSet

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk classification levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalPolicy(Enum):
    """Approval policy for patches."""

    AUTO = "auto"  # Merge automatically
    REVIEW = "review"  # Require human review
    PROPOSAL = "proposal"  # Create proposal package only
    BLOCKED = "blocked"  # User must approve


@dataclass
class RiskAssessment:
    """Risk assessment results for a patch set."""

    risk_level: RiskLevel
    risk_score: float  # 0.0-1.0
    approval_policy: ApprovalPolicy
    reasoning: list[str] = field(default_factory=list)
    required_checks: list[str] = field(default_factory=list)
    recommended_reviewers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class RiskScorer:
    """Score and govern patches based on risk assessment."""

    # Risk thresholds
    THRESHOLDS: ClassVar[dict] = {
        RiskLevel.LOW.value: 0.3,
        RiskLevel.MEDIUM.value: 0.6,
        RiskLevel.HIGH.value: 0.8,
        # CRITICAL is anything > 0.8
    }

    # Critical file patterns
    CRITICAL_PATHS: ClassVar[list] = [
        "orchestration",
        "core",
        "auth",
        "security",
        "main.py",
        "/__init__.py",
    ]

    def __init__(self):
        """Initialize risk scorer."""
        logger.info("RiskScorer initialized")

    def score(self, patchset: PatchSet) -> RiskAssessment:
        """Score a patch set and determine governance policy.

        Args:
            patchset: Patch set to assess

        Returns:
            RiskAssessment with score, level, policy, and reasoning
        """
        score = 0.0
        reasoning: list[str] = []
        warnings: list[str] = []
        required_checks: list[str] = []
        recommended_reviewers = ["@system-maintainer"]

        # Apply scoring factors
        score, reasoning, warnings = self._score_file_count(patchset, score, reasoning, warnings)
        score, reasoning, warnings, reviewers, checks = self._score_critical_paths(
            patchset, score, reasoning, warnings, recommended_reviewers, required_checks
        )
        recommended_reviewers.extend(reviewers)
        required_checks.extend(checks)

        score, reasoning, warnings, checks = self._score_deletions(
            patchset, score, reasoning, warnings, required_checks
        )
        required_checks.extend(checks)

        score, reasoning, warnings, checks = self._score_test_results(
            patchset, score, reasoning, warnings, required_checks
        )
        required_checks.extend(checks)

        # Clamp score to 0.0-1.0
        score = min(max(score, 0.0), 1.0)

        # Determine risk level and policy
        risk_level = self._determine_risk_level(score)
        approval_policy = self._determine_approval_policy(score, reasoning)

        return RiskAssessment(
            risk_level=risk_level,
            risk_score=score,
            approval_policy=approval_policy,
            reasoning=reasoning,
            required_checks=required_checks,
            recommended_reviewers=list(set(recommended_reviewers)),  # Deduplicate
            warnings=warnings,
        )

    def _score_file_count(
        self, patchset, score, reasoning, warnings
    ) -> tuple[float, list[str], list[str]]:
        file_count = len(patchset.patches)
        if file_count > 0:
            file_risk = min(file_count * 0.05, 0.4)
            score += file_risk
            if file_count > 10:
                score += 0.2
                warnings.append(f"Large changeset: {file_count} files modified")
                reasoning.append(f"Large changeset risk: {file_count} files")
            else:
                reasoning.append(f"File count: {file_count} files")
        return score, reasoning, warnings

    def _score_critical_paths(
        self, patchset, score, reasoning, warnings, reviewers, checks
    ) -> tuple[float, list[str], list[str], list[str], list[str]]:
        critical_files = []
        for patch in patchset.patches:
            if self._is_critical_path(patch.file_path):
                score += 0.3
                critical_files.append(patch.file_path)
                reviewers.append("@architecture-lead")

        if critical_files:
            reasoning.append(f"Critical paths: {', '.join(critical_files)}")
            warnings.append(f"Touching critical paths: {', '.join(critical_files)}")
            checks.extend(["security_audit", "architecture_review"])

        return score, reasoning, warnings, reviewers, checks

    def _score_deletions(
        self, patchset, score, reasoning, warnings, checks
    ) -> tuple[float, list[str], list[str], list[str]]:
        from src.autonomy.patch_builder import PatchAction

        deletions = sum(1 for p in patchset.patches if p.action == PatchAction.DELETE)
        if deletions > 0:
            score += deletions * 0.2
            reasoning.append(f"Deletions: {deletions} files")
            warnings.append(f"Patch deletes {deletions} files")
            checks.append("deletion_audit")

        return score, reasoning, warnings, checks

    def _score_test_results(
        self, patchset, score, reasoning, warnings, checks
    ) -> tuple[float, list[str], list[str], list[str]]:
        if patchset.test_results:
            if not patchset.test_results.get("passed", False):
                score *= 1.3
                reasoning.append("Test failures detected")
                warnings.append("Tests failed - patch not validated")
                checks.append("test_fix_required")
            else:
                # Reduce score if tests passed
                score *= 0.7
                reasoning.append("Tests passed - reduces risk")
        else:
            warnings.append("No test results available")
            checks.append("test_validation")

        return score, reasoning, warnings, checks

    def _determine_risk_level(self, score: float) -> "RiskLevel":
        if score < self.THRESHOLDS[RiskLevel.LOW.value]:
            return RiskLevel.LOW
        elif score < self.THRESHOLDS[RiskLevel.MEDIUM.value]:
            return RiskLevel.MEDIUM
        elif score < self.THRESHOLDS[RiskLevel.HIGH.value]:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _determine_approval_policy(self, score: float, reasoning: list[str]) -> "ApprovalPolicy":
        if score < 0.3:
            approval_policy = ApprovalPolicy.AUTO
            reasoning.append("Low risk - can merge automatically")
        elif score < 0.6:
            approval_policy = ApprovalPolicy.REVIEW
            reasoning.append("Medium risk - requires human review")
        elif score < 0.8:
            approval_policy = ApprovalPolicy.PROPOSAL
            reasoning.append("High risk - creating proposal package")
        else:
            approval_policy = ApprovalPolicy.BLOCKED
            reasoning.append("Critical risk - user approval required")
        return approval_policy

    def _is_critical_path(self, file_path: str) -> bool:
        """Check if file is on a critical path."""
        normalized = file_path.lower().replace("\\", "/")
        return any(critical in normalized for critical in self.CRITICAL_PATHS)

    def generate_governance_report(self, assessment: RiskAssessment) -> str:
        """Generate human-readable governance report.

        Args:
            assessment: Risk assessment results

        Returns:
            Formatted markdown report
        """
        report = []
        report.extend(self._format_header_section(assessment))
        report.extend(self._format_reasoning_section(assessment))
        report.extend(self._format_warnings_section(assessment))
        report.extend(self._format_checks_section(assessment))
        report.extend(self._format_reviewers_section(assessment))
        report.extend(self._format_action_plan_section(assessment))
        return "\n".join(report)

    def _format_header_section(self, assessment: RiskAssessment) -> list[str]:
        """Format header section with risk metrics."""
        return [
            "# Risk Assessment Report\n",
            f"**Risk Level:** {assessment.risk_level.value.upper()}",
            f"**Risk Score:** {assessment.risk_score:.2f}/1.0",
            f"**Approval Policy:** {assessment.approval_policy.value.upper()}\n",
        ]

    def _format_reasoning_section(self, assessment: RiskAssessment) -> list[str]:
        """Format reasoning section."""
        if not assessment.reasoning:
            return []
        lines = ["## Reasoning\n"]
        lines.extend(f"- {reason}" for reason in assessment.reasoning)
        lines.append("")
        return lines

    def _format_warnings_section(self, assessment: RiskAssessment) -> list[str]:
        """Format warnings section."""
        if not assessment.warnings:
            return []
        lines = ["## ⚠️ Warnings\n"]
        lines.extend(f"- {warning}" for warning in assessment.warnings)
        lines.append("")
        return lines

    def _format_checks_section(self, assessment: RiskAssessment) -> list[str]:
        """Format required checks section."""
        if not assessment.required_checks:
            return []
        lines = ["## Required Checks\n"]
        lines.extend(f"- [ ] {check}" for check in assessment.required_checks)
        lines.append("")
        return lines

    def _format_reviewers_section(self, assessment: RiskAssessment) -> list[str]:
        """Format recommended reviewers section."""
        if not assessment.recommended_reviewers:
            return []
        lines = ["## Recommended Reviewers\n"]
        lines.extend(f"- {reviewer}" for reviewer in assessment.recommended_reviewers)
        lines.append("")
        return lines

    def _format_action_plan_section(self, assessment: RiskAssessment) -> list[str]:
        """Format action plan section."""
        lines = ["## Action Plan\n"]
        if assessment.approval_policy == ApprovalPolicy.AUTO:
            lines.append("✅ This patch can be automatically merged after passing CI/CD checks.")
        elif assessment.approval_policy == ApprovalPolicy.REVIEW:
            lines.append("👤 This patch requires human review before merging.")
            lines.append("Please assign reviewers and address any comments.")
        elif assessment.approval_policy == ApprovalPolicy.PROPOSAL:
            lines.append("📋 This patch creates a proposal for discussion.")
            lines.append("Review the proposal and merge manually if approved.")
        else:  # BLOCKED
            lines.append("🚫 This patch is blocked and requires explicit user approval.")
            lines.append("Address warnings and security concerns before proceeding.")
        return lines

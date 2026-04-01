"""Error Recovery Mapper - ZETA08 Phase 1.

Maps ruff diagnostic errors to recovery strategies and actions.
Provides bidirectional mapping between error codes and recovery workflows.

OmniTag: {
    "purpose": "error_recovery_orchestration",
    "tags": ["diagnostics", "recovery", "automation", "ruff"],
    "category": "healing_system",
    "evolution_stage": "v1.0_zeta08_phase1"
}
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RecoverySeverity(str, Enum):
    """Severity levels for recovery actions."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RecoveryStrategy(str, Enum):
    """Available recovery strategies."""

    AUTO_FIX_VIA_RUFF = "auto_fix_via_ruff"
    SURGICAL_EDIT = "surgical_edit"
    MANUAL_REVIEW = "manual_review"
    REFACTOR = "refactor"


@dataclass
class DiagnosticIssue:
    """Represents a single diagnostic issue from ruff."""

    rule_code: str
    file_path: str
    line: int
    column: int
    message: str
    severity: str  # error, warning, info


@dataclass
class RecoveryAction:
    """Recommended recovery action for a diagnostic issue."""

    rule_code: str
    issue: DiagnosticIssue
    strategy: RecoveryStrategy
    suggested_action: str
    auto_fixable: bool
    confidence: float
    recovery_severity: RecoverySeverity
    requires_git: bool = False


class ErrorRecoveryMapper:
    """Maps ruff diagnostics to recovery actions.

    This is the core component of ZETA08 Phase 1, bridging diagnostics
    and recovery strategies. It maintains knowledge of:
    - Which errors are auto-fixable vs. manual review
    - Confidence levels for each recovery strategy
    - Priority ordering for recovery execution
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the mapper with recovery rules configuration.

        Args:
            config_path: Path to error_recovery_rules.json. If None,
                uses default path relative to this module.
        """
        self.config_path = config_path or self._default_config_path()
        self.config = self._load_config()
        self.auto_fixable_cache: dict[str, bool] = {}
        logger.info(f"Initialized ErrorRecoveryMapper with {len(self.config)} rule definitions")

    @staticmethod
    def _default_config_path() -> Path:
        """Get default config path relative to this module."""
        return Path(__file__).parent.parent.parent / "config" / "error_recovery_rules.json"

    def _load_config(self) -> dict[str, Any]:
        """Load error recovery rules configuration.

        Returns:
            Configuration dictionary with rule definitions
        """
        if not self.config_path.exists():
            logger.warning(f"Config not found at {self.config_path}, using defaults")
            return self._default_config()

        try:
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return self._default_config()

    @staticmethod
    def _default_config() -> dict[str, Any]:
        """Return minimal default configuration."""
        return {
            "auto_fixable_rules": {},
            "manual_review_rules": {},
            "recovery_strategies": {},
        }

    def is_auto_fixable(self, rule_code: str) -> bool:
        """Check if a rule is auto-fixable.

        Args:
            rule_code: Ruff rule code (e.g., "F401", "E402")

        Returns:
            True if the rule is safe to auto-fix
        """
        if rule_code in self.auto_fixable_cache:
            return self.auto_fixable_cache[rule_code]

        # Check config
        auto_fixable_rules = self.config.get("auto_fixable_rules", {})
        is_fixable = rule_code in auto_fixable_rules

        self.auto_fixable_cache[rule_code] = is_fixable
        return is_fixable

    def get_suggested_action(self, rule_code: str) -> str:
        """Get the suggested recovery action for a rule.

        Args:
            rule_code: Ruff rule code

        Returns:
            Suggested action string (e.g., "auto-fix via ruff --fix")
        """
        # Try auto-fixable rules
        auto_fixable = self.config.get("auto_fixable_rules", {})
        if rule_code in auto_fixable:
            return auto_fixable[rule_code].get("suggested_action", "Unknown")

        # Try manual review rules
        manual_review = self.config.get("manual_review_rules", {})
        if rule_code in manual_review:
            return manual_review[rule_code].get("suggested_action", "Unknown")

        return "manual review"

    def get_confidence_level(self, rule_code: str) -> float:
        """Get confidence level for recovery action.

        Args:
            rule_code: Ruff rule code

        Returns:
            Confidence level from 0.0 to 1.0
        """
        # Check auto-fixable
        auto_fixable = self.config.get("auto_fixable_rules", {})
        if rule_code in auto_fixable:
            return auto_fixable[rule_code].get("confidence", 0.5)

        # Check manual review
        manual_review = self.config.get("manual_review_rules", {})
        if rule_code in manual_review:
            return manual_review[rule_code].get("confidence", 0.3)

        return 0.0

    def map_issue_to_recovery(self, issue: DiagnosticIssue) -> RecoveryAction:
        """Map a diagnostic issue to a recovery action.

        Args:
            issue: Diagnostic issue from ruff

        Returns:
            Recommended recovery action
        """
        rule_code = issue.rule_code
        auto_fixable = self.is_auto_fixable(rule_code)
        suggested = self.get_suggested_action(rule_code)
        confidence = self.get_confidence_level(rule_code)

        # Determine recovery strategy
        if auto_fixable:
            if "ruff --fix" in suggested:
                strategy = RecoveryStrategy.AUTO_FIX_VIA_RUFF
            else:
                strategy = RecoveryStrategy.SURGICAL_EDIT
        elif confidence > 0.7:
            strategy = RecoveryStrategy.REFACTOR
        else:
            strategy = RecoveryStrategy.MANUAL_REVIEW

        # Determine severity
        severity = self._map_to_severity(issue.severity)

        return RecoveryAction(
            rule_code=rule_code,
            issue=issue,
            strategy=strategy,
            suggested_action=suggested,
            auto_fixable=auto_fixable,
            confidence=confidence,
            recovery_severity=severity,
        )

    @staticmethod
    def _map_to_severity(issue_severity: str) -> RecoverySeverity:
        """Map issue severity to recovery severity.

        Args:
            issue_severity: Original issue severity

        Returns:
            Recovery severity level
        """
        severity_map = {
            "error": RecoverySeverity.ERROR,
            "warning": RecoverySeverity.WARNING,
            "info": RecoverySeverity.INFO,
        }
        return severity_map.get(issue_severity, RecoverySeverity.INFO)

    def build_recovery_plan(self, issues: list[DiagnosticIssue]) -> list[RecoveryAction]:
        """Build a recovery plan from multiple issues.

        Args:
            issues: List of diagnostic issues

        Returns:
            Ordered list of recovery actions by priority

        Implementation:
        1. Map each issue to recovery action
        2. Sort by priority (critical → info)
        3. Group by strategy (auto-fix first)
        """
        actions = [self.map_issue_to_recovery(issue) for issue in issues]

        # Sort by severity (critical first) and auto-fixable (first)
        severity_order = {
            RecoverySeverity.CRITICAL: 1,
            RecoverySeverity.ERROR: 2,
            RecoverySeverity.WARNING: 3,
            RecoverySeverity.INFO: 4,
        }
        strategy_order = {
            RecoveryStrategy.AUTO_FIX_VIA_RUFF: 1,
            RecoveryStrategy.SURGICAL_EDIT: 2,
            RecoveryStrategy.REFACTOR: 3,
            RecoveryStrategy.MANUAL_REVIEW: 4,
        }

        actions.sort(
            key=lambda a: (
                severity_order.get(a.recovery_severity, 999),
                strategy_order.get(a.strategy, 999),
                -a.confidence,  # Higher confidence first
            )
        )

        return actions

    def get_recovery_summary(self, actions: list[RecoveryAction]) -> dict[str, Any]:
        """Generate summary statistics for recovery plan.

        Args:
            actions: Recovery plan (ordered list of actions)

        Returns:
            Summary dictionary with counts and statistics
        """
        auto_fixable = sum(1 for a in actions if a.auto_fixable)
        manual_review = sum(1 for a in actions if not a.auto_fixable)
        highest_confidence = max((a.confidence for a in actions), default=0)
        avg_confidence = sum(a.confidence for a in actions) / len(actions) if actions else 0

        severity_counts = {}
        for severity in RecoverySeverity:
            count = sum(1 for a in actions if a.recovery_severity == severity)
            if count > 0:
                severity_counts[severity.value] = count

        return {
            "total_issues": len(actions),
            "auto_fixable": auto_fixable,
            "manual_review": manual_review,
            "highest_confidence": highest_confidence,
            "avg_confidence": avg_confidence,
            "by_severity": severity_counts,
            "auto_fixable_percentage": (100 * auto_fixable / len(actions) if actions else 0),
        }

#!/usr/bin/env python3
"""Ecosystem Health Checker - Redirect Bridge to Canonical Health Assessment

Phase 3b Consolidation:
- Canonical source: src/diagnostics/system_health_assessor.py
- This module now imports from canonical health module for backward compatibility
- All health assessment logic centralized in canonical module
"""

from src.diagnostics.system_health_assessor import SystemHealthAssessment

# Re-export for backward compatibility
__all__ = [
    "EcosystemHealthChecker",
]


class EcosystemHealthChecker:
    """Backward-compatible wrapper around SystemHealthAssessment."""

    def __init__(self):
        """Initialize with canonical health assessment module."""
        self.health_assessment = SystemHealthAssessment()
        self.health_report = {}

    def run_comprehensive_check(self):
        """Run comprehensive ecosystem health check using canonical module."""
        return self.health_assessment.analyze_system_health()

    def __getattr__(self, name):
        """Delegate any other method calls to canonical health assessment."""
        return getattr(self.health_assessment, name)


if __name__ == "__main__":
    checker = EcosystemHealthChecker()
    checker.run_comprehensive_check()

#!/usr/bin/env python3
"""Zeta13 - Code Quality Tools Entry Point

Runs automated code quality analysis and generates reports.
This is part of Phase 1 ZETA implementation.
"""

import os
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

try:
    from src.code_quality_tools import CodeQualityAnalyzer
except ImportError:
    from code_quality_tools import CodeQualityAnalyzer
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run Zeta13 code quality analysis."""
    logger.info("🚀 ZETA13 - Code Quality Tools Starting")
    logger.info("=" * 70)

    # Change to repo root
    os.chdir(repo_root)

    # Create analyzer
    analyzer = CodeQualityAnalyzer("src")

    # Run analysis
    logger.info("📊 PHASE 1: Running Code Quality Analysis")
    report = analyzer.analyze()

    # Export report
    logger.info("💾 PHASE 2: Exporting Analysis Report")
    analyzer.export_report("docs/reports/code_quality.json")

    # Print summary
    print("\n" + "=" * 70)
    print("🎯 ZETA13 CODE QUALITY TOOLS - ANALYSIS RESULTS")
    print("=" * 70)

    print("\n📊 Analysis Scope:")
    print(f"  • Files with issues: {report.analyzed_files}")
    print(f"  • Total issues found: {report.total_issues}")
    print(f"  • Fixable issues: {report.fixable_issues}")

    if report.issues_by_severity:
        print("\n📋 Issues by Severity:")
        for severity, count in report.issues_by_severity.items():
            print(f"  • {severity.upper()}: {count}")

    if report.issues_by_type:
        print("\n🔧 Issues by Type (Top 10):")
        sorted_types = sorted(report.issues_by_type.items(), key=lambda x: x[1], reverse=True)
        for code, count in sorted_types[:10]:
            print(f"  • {code}: {count}")

    # Offer auto-fix
    if report.fixable_issues > 0:
        print(f"\n⚡ Suggestion: {report.fixable_issues} issues can be auto-fixed")
        print("  Run: python scripts/run_zeta13_code_quality_tools.py --fix")

    print("\n" + "=" * 70)
    print("✅ Analysis complete - Report: docs/reports/code_quality.json")
    print("=" * 70 + "\n")

    # Return based on issue count
    if report.total_issues > 100:
        logger.warning(f"⚠️  High issue count: {report.total_issues} (target: <50)")
        return 1
    else:
        logger.info(f"✅ Issue count acceptable: {report.total_issues}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

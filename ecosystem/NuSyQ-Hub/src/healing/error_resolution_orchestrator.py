#!/usr/bin/env python3
"""🏥 Comprehensive Error Resolution - Focused on Issue Detection & Tracking.

================================================================
Detects and tracks all errors and warnings systematically.
"""

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Add to path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from orchestration.extended_autonomous_cycle_runner import \
        CodebaseIssueDetector
except ImportError:
    try:
        from src.orchestration.extended_autonomous_cycle_runner import \
            CodebaseIssueDetector
    except ImportError as e:
        logger.error(f"Import error: {e}")
        sys.exit(1)

# Try to import tracker but handle gracefully
try:
    from analytics.resolution_tracker import ResolutionTracker

    HAS_TRACKER = True
except ImportError:
    try:
        from src.analytics.resolution_tracker import ResolutionTracker

        HAS_TRACKER = True
    except ImportError:
        logger.warning("Tracker not available - will collect metrics only")
        HAS_TRACKER = False


class ErrorResolutionOrchestrator:
    """Orchestrates comprehensive error detection and tracking."""

    def __init__(self) -> None:
        """Initialize orchestrator."""
        logger.info("🚀 Initializing Error Resolution Orchestrator...")
        self.detector = CodebaseIssueDetector(REPO_ROOT)
        self.tracker = None
        if HAS_TRACKER:
            try:
                self.tracker = ResolutionTracker()
            except Exception as e:
                logger.warning(f"Tracker initialization failed: {e}")
        self.issues: list[Any] = []
        logger.info("✅ Orchestrator initialized")

    def detect_all_issues(self) -> dict[str, int]:
        """Detect all issues in codebase."""
        logger.info("🔍 Scanning entire codebase for issues...")
        start = datetime.now()

        self.issues = self.detector.scan_repository()

        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"✅ Scan complete in {elapsed:.1f}s")
        logger.info(f"📊 Total issues detected: {len(self.issues)}")

        # Categorize by type
        by_type: defaultdict[str, int] = defaultdict(int)
        by_severity: defaultdict[str, int] = defaultdict(int)

        for issue in self.issues:
            by_type[issue.issue_type.value] += 1
            by_severity[issue.severity.name] += 1

        # Display results
        logger.info("\n📈 Issues by Type:")
        for issue_type, count in sorted(by_type.items(), key=lambda x: -x[1])[:15]:
            logger.info(f"   • {issue_type}: {count}")

        logger.warning("\n⚠️ Issues by Severity:")
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        for severity in severity_order:
            if severity in by_severity:
                count = by_severity[severity]
                emoji = (
                    "🔴"
                    if severity in ["CRITICAL", "HIGH"]
                    else "🟡" if severity == "MEDIUM" else "🟢"
                )
                logger.info(f"   {emoji} {severity}: {count}")

        return dict(by_type)

    def categorize_issues(self) -> dict[str, list[Any]]:
        """Categorize issues for targeted resolution."""
        categories: dict[str, list[Any]] = {
            "import_errors": [],
            "type_hints": [],
            "style_issues": [],
            "documentation": [],
            "performance": [],
            "undefined_refs": [],
            "other": [],
        }

        for issue in self.issues:
            issue_type = issue.issue_type.value

            if "import" in issue_type or "circular" in issue_type:
                categories["import_errors"].append(issue)
            elif "type_hint" in issue_type or "type_mismatch" in issue_type:
                categories["type_hints"].append(issue)
            elif "style" in issue_type:
                categories["style_issues"].append(issue)
            elif "documentation" in issue_type:
                categories["documentation"].append(issue)
            elif "performance" in issue_type:
                categories["performance"].append(issue)
            elif "undefined" in issue_type:
                categories["undefined_refs"].append(issue)
            else:
                categories["other"].append(issue)

        return {k: v for k, v in categories.items() if v}

    def track_issues(self, categories: dict[str, list]) -> dict[str, dict]:
        """Track all issues in the tracking system."""
        logger.info("📋 Registering issues in tracking system...")

        results = {}

        for category, issues in categories.items():
            results[category] = {"total": len(issues), "registered": 0, "failed": 0}

            for idx, issue in enumerate(issues, 1):
                try:
                    if self.tracker:
                        self.tracker.register_detected_issue(
                            issue_id=f"{issue.issue_type.value}_{issue.file_path.name}_{idx}",
                            issue_type=issue.issue_type.value,
                            description=issue.message,
                            file_path=str(issue.file_path),
                            severity=issue.severity.name,
                            cycle_num=1,
                        )
                    results[category]["registered"] += 1

                except Exception as e:
                    logger.debug(f"Failed to register {issue.issue_id}: {e}")
                    results[category]["failed"] += 1

        try:
            from src.system.agent_awareness import emit as _emit

            _total = sum(v.get("registered", 0) for v in results.values())
            _failed = sum(v.get("failed", 0) for v in results.values())
            _lvl = "WARNING" if _failed else "INFO"
            _emit(
                "system",
                f"Error resolution: registered={_total} failed={_failed} categories={list(results.keys())}",
                level=_lvl,
                source="error_resolution_orchestrator",
            )
        except Exception:
            pass

        return results

    def generate_resolution_report(
        self, categories: dict[str, list], tracking_results: dict
    ) -> dict:
        """Generate comprehensive resolution report."""
        logger.info("📊 Generating resolution report...")

        report: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_issues": len(self.issues),
                "total_categories": len(categories),
            },
            "by_category": {},
            "by_severity": {},
            "tracking_status": tracking_results,
        }

        # Categorize by severity
        by_severity: defaultdict[str, int] = defaultdict(int)
        for issue in self.issues:
            by_severity[issue.severity.name] += 1

        report["by_severity"] = dict(by_severity)

        # Details by category
        for category, issues in categories.items():
            report["by_category"][category] = {
                "count": len(issues),
                "severity_breakdown": self._get_severity_breakdown(issues),
                "sample_issues": [
                    {
                        "type": issue.issue_type.value,
                        "file": str(issue.file_path),
                        "line": issue.line_number,
                        "message": issue.message[:100],
                        "severity": issue.severity.name,
                    }
                    for issue in issues[:3]  # Top 3 samples
                ],
            }

        return report

    def _get_severity_breakdown(self, issues: list[Any]) -> dict[str, int]:
        """Get severity breakdown for a set of issues."""
        breakdown: defaultdict[str, int] = defaultdict(int)
        for issue in issues:
            breakdown[issue.severity.name] += 1
        return dict(breakdown)

    def run_orchestration(self) -> dict[str, Any]:
        """Run complete error resolution orchestration."""
        logger.info("\n" + "=" * 80)
        logger.error("🏥 COMPREHENSIVE ERROR & WARNING RESOLUTION ORCHESTRATION")
        logger.info("=" * 80)

        # Phase 1: Detection
        logger.info("\n[Phase 1/5] DETECTION")
        logger.info("-" * 80)
        issue_counts = self.detect_all_issues()

        # Phase 2: Categorization
        logger.info("\n[Phase 2/5] CATEGORIZATION")
        logger.info("-" * 80)
        categories = self.categorize_issues()
        logger.info("Categorized issues:")
        for category, issues in categories.items():
            logger.info(f"   • {category}: {len(issues)}")

        # Phase 3: Tracking
        logger.info("\n[Phase 3/5] TRACKING & REGISTRATION")
        logger.info("-" * 80)
        tracking_results = self.track_issues(categories)

        for category, stats in tracking_results.items():
            pct = (stats["registered"] / stats["total"] * 100) if stats["total"] > 0 else 0
            logger.info(
                f"   • {category}: {stats['registered']}/{stats['total']} registered ({pct:.0f}%)"
            )

        # Phase 4: Analysis
        logger.info("\n[Phase 4/5] ANALYSIS & INSIGHTS")
        logger.info("-" * 80)
        report = self.generate_resolution_report(categories, tracking_results)

        # Top issue types
        logger.info("Top 5 issue types:")
        for issue_type, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:5]:
            logger.info(f"   • {issue_type}: {count}")

        # Files with most issues
        file_counts: defaultdict[str, int] = defaultdict(int)
        for issue in self.issues:
            file_counts[str(issue.file_path)] += 1

        logger.info("\nFiles with most issues:")
        for file_path, count in sorted(file_counts.items(), key=lambda x: -x[1])[:5]:
            logger.info(f"   • {file_path}: {count}")

        # Phase 5: Report
        logger.info("\n[Phase 5/5] FINAL REPORT")
        logger.info("-" * 80)

        logger.info("\n📊 Resolution Summary:")
        logger.info(f"   • Total Issues Detected: {len(self.issues)}")
        logger.info(f"   • Total Categories: {len(categories)}")
        logger.info(
            f"   • Total Registered: {sum(t['registered'] for t in tracking_results.values())}"
        )

        logger.info(f"\n🔴 Critical Issues: {report['by_severity'].get('CRITICAL', 0)}")
        logger.info(f"🟠 High Issues: {report['by_severity'].get('HIGH', 0)}")
        logger.info(f"🟡 Medium Issues: {report['by_severity'].get('MEDIUM', 0)}")
        logger.info(f"🟢 Low Issues: {report['by_severity'].get('LOW', 0)}")
        logger.info(f"⚪ Info Issues: {report['by_severity'].get('INFO', 0)}")

        # Save reports
        logger.info("\n💾 Saving reports...")

        # JSON report
        json_path = REPO_ROOT / "error_resolution_report.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"   • JSON: {json_path}")

        # Markdown report
        md_path = REPO_ROOT / "ERROR_RESOLUTION_REPORT.md"
        self._write_markdown_report(md_path, report, categories)
        logger.info(f"   • Markdown: {md_path}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ COMPREHENSIVE RESOLUTION ORCHESTRATION COMPLETE")
        logger.info("=" * 80 + "\n")

        return report

    def _write_markdown_report(self, path: Path, report: dict, _categories: dict) -> None:
        """Write markdown report of errors and resolutions."""
        with open(path, "w") as f:
            f.write("# Error & Warning Resolution Report\n\n")
            f.write(f"**Generated:** {report['timestamp']}\n\n")

            f.write("## Summary\n\n")
            f.write(f"- **Total Issues Detected:** {report['summary']['total_issues']}\n")
            f.write(f"- **Total Categories:** {report['summary']['total_categories']}\n")
            f.write(f"- **Tracker Status:** {'Operational' if self.tracker else 'Limited'}\n\n")

            f.write("## Issues by Severity\n\n")
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
                count = report["by_severity"].get(severity, 0)
                if count > 0:
                    f.write(f"- **{severity}:** {count}\n")

            f.write("\n## Issues by Category\n\n")
            for category, details in report["by_category"].items():
                f.write(f"### {category.replace('_', ' ').title()}\n\n")
                f.write(f"**Count:** {details['count']}\n\n")
                f.write("**Severity Breakdown:**\n")
                for sev, count in sorted(details["severity_breakdown"].items()):
                    f.write(f"- {sev}: {count}\n")

                if details["sample_issues"]:
                    f.write("\n**Sample Issues:**\n")
                    for issue in details["sample_issues"]:
                        f.write(f"- {issue['type']} in {issue['file']}:{issue['line']}\n")
                        f.write(f"  {issue['message']}...\n")

                f.write("\n")


if __name__ == "__main__":
    orchestrator = ErrorResolutionOrchestrator()
    orchestrator.run_orchestration()

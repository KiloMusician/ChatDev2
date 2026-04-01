#!/usr/bin/env python3
"""Progress Tracker - Real-time Evolution Progress Dashboard.

Tracks which files have been:
- Scanned
- Analyzed
- Proposed for changes
- Approved by AI Council
- Implemented by ChatDev
- Tested and validated

Creates visual dashboards and progress reports.

OmniTag: [progress-tracking, dashboard, metrics, visualization]
MegaTag: [PROGRESS⨳TRACKER⦾REAL-TIME→∞]
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks the evolution progress of every file in the repository.

    Provides real-time dashboards showing:
    - Overall progress (X% of files modernized)
    - Per-file status (pending/analyzed/implemented)
    - Velocity metrics (files per day)
    - Impact metrics (issues resolved)
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize tracker with storage under data/evolution."""
        self.repo_root = repo_root or Path.cwd()
        self.data_dir = self.repo_root / "data" / "evolution"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.progress_file = self.data_dir / "progress.json"
        self.progress = self._load_progress()

    def _load_progress(self) -> dict:
        """Load progress tracking data."""
        if self.progress_file.exists():
            with open(self.progress_file, encoding="utf-8") as f:
                progress_data: dict[Any, Any] = json.load(f)
                return progress_data
        return {
            "files": {},  # file_path -> status info
            "sessions": [],  # list of audit/implementation sessions
            "metrics": self._initialize_metrics(),
        }

    def _initialize_metrics(self) -> dict:
        """Initialize metrics structure."""
        return {
            "total_files": 0,
            "files_scanned": 0,
            "files_analyzed": 0,
            "files_proposed": 0,
            "files_approved": 0,
            "files_implemented": 0,
            "files_tested": 0,
            "issues_found": 0,
            "issues_resolved": 0,
            "proposals_created": 0,
            "proposals_approved": 0,
            "proposals_rejected": 0,
            "start_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }

    def _save_progress(self) -> None:
        """Save progress to disk."""
        self.progress["metrics"]["last_updated"] = datetime.now().isoformat()
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, indent=2)

    def update_file_status(self, file_path: str, status: str, details: dict | None = None) -> None:
        """Update the status of a file."""
        if file_path not in self.progress["files"]:
            self.progress["files"][file_path] = {
                "status": "pending",
                "history": [],
                "issues": [],
                "proposals": [],
            }

        file_info = self.progress["files"][file_path]
        old_status = file_info["status"]
        file_info["status"] = status
        file_info["history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "old_status": old_status,
                "new_status": status,
                "details": details or {},
            },
        )

        # Update metrics
        self._update_metrics(old_status, status)
        self._save_progress()

    def _update_metrics(self, _old_status: str, new_status: str) -> None:
        """Update metrics when file status changes."""
        metrics = self.progress["metrics"]

        # Increment new status counter
        status_to_metric = {
            "scanned": "files_scanned",
            "analyzed": "files_analyzed",
            "proposed": "files_proposed",
            "approved": "files_approved",
            "implemented": "files_implemented",
            "tested": "files_tested",
        }

        if new_status in status_to_metric:
            metrics[status_to_metric[new_status]] += 1

    def record_audit_session(self, session_data: dict) -> None:
        """Record an audit session."""
        self.progress["sessions"].append(
            {
                "type": "audit",
                "timestamp": datetime.now().isoformat(),
                "data": session_data,
            },
        )

        # Update metrics from session
        self.progress["metrics"]["issues_found"] += session_data.get("issues_found", 0)
        self.progress["metrics"]["proposals_created"] += session_data.get("proposals_created", 0)

        self._save_progress()

    def record_implementation_session(self, session_data: dict) -> None:
        """Record an implementation session."""
        self.progress["sessions"].append(
            {
                "type": "implementation",
                "timestamp": datetime.now().isoformat(),
                "data": session_data,
            },
        )

        # Update metrics
        self.progress["metrics"]["issues_resolved"] += session_data.get("issues_resolved", 0)

        self._save_progress()

    def get_progress_summary(self) -> dict:
        """Get current progress summary."""
        metrics = self.progress["metrics"]
        total = metrics["total_files"] or len(self.progress["files"]) or 1

        return {
            "overall_progress": {
                "percent_analyzed": (metrics["files_analyzed"] / total) * 100,
                "percent_implemented": (metrics["files_implemented"] / total) * 100,
                "percent_tested": (metrics["files_tested"] / total) * 100,
            },
            "metrics": metrics,
            "recent_sessions": self.progress["sessions"][-10:],  # Last 10 sessions
            "status_breakdown": self._get_status_breakdown(),
        }

    def _get_status_breakdown(self) -> dict[str, int]:
        """Get count of files in each status."""
        breakdown: dict[str, int] = defaultdict(int)
        for file_info in self.progress["files"].values():
            breakdown[file_info["status"]] += 1
        return dict(breakdown)

    def generate_dashboard(self) -> str:
        """Generate a text-based dashboard."""
        summary = self.get_progress_summary()
        overall = summary["overall_progress"]
        metrics = summary["metrics"]
        breakdown = summary["status_breakdown"]

        dashboard = f"""
{"=" * 70}
 SYSTEM EVOLUTION PROGRESS DASHBOARD
{"=" * 70}

OVERALL PROGRESS:
  Analyzed:     [{self._progress_bar(overall["percent_analyzed"])}] {overall["percent_analyzed"]:.1f}%
  Implemented:  [{self._progress_bar(overall["percent_implemented"])}] {overall["percent_implemented"]:.1f}%
  Tested:       [{self._progress_bar(overall["percent_tested"])}] {overall["percent_tested"]:.1f}%

METRICS:
  Files Scanned:        {metrics["files_scanned"]:,}
  Issues Found:         {metrics["issues_found"]:,}
  Issues Resolved:      {metrics["issues_resolved"]:,}
  Proposals Created:    {metrics["proposals_created"]:,}
  Proposals Approved:   {metrics["proposals_approved"]:,}
  Files Implemented:    {metrics["files_implemented"]:,}

STATUS BREAKDOWN:
"""
        for status, count in sorted(breakdown.items()):
            dashboard += f"  {status:20s}: {count:4d} files\n"

        dashboard += f"\nLast Updated: {metrics['last_updated']}\n"
        dashboard += f"{'=' * 70}\n"

        return dashboard

    def _progress_bar(self, percent: float, width: int = 30) -> str:
        """Generate a text progress bar."""
        filled = int((percent / 100) * width)
        return "█" * filled + "░" * (width - filled)

    def export_report(self, output_file: Path | None = None) -> Path:
        """Export detailed progress report."""
        output_file = (
            output_file
            or self.data_dir / f"progress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )

        summary = self.get_progress_summary()

        report = f"""# System Evolution Progress Report

**Generated:** {datetime.now().isoformat()}
**Repository:** {self.repo_root}

## Executive Summary

{self.generate_dashboard()}

## Detailed Metrics

### Files by Status
"""
        for status, count in summary["status_breakdown"].items():
            report += f"- **{status}**: {count} files\n"

        report += "\n### Recent Sessions\n\n"
        for session in summary["recent_sessions"]:
            session_type = session["type"]
            timestamp = session["timestamp"]
            report += f"- **{session_type}** at {timestamp}\n"
            for key, value in session["data"].items():
                report += f"  - {key}: {value}\n"

        report += "\n## File Details\n\n"
        report += "| File | Status | Issues | Last Updated |\n"
        report += "|------|--------|--------|-------------|\n"

        for file_path, file_info in sorted(self.progress["files"].items())[:50]:  # First 50
            status = file_info["status"]
            issues = len(file_info["issues"])
            last_update = file_info["history"][-1]["timestamp"] if file_info["history"] else "N/A"
            report += f"| {file_path} | {status} | {issues} | {last_update} |\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        return output_file


def main() -> None:
    """Test the progress tracker."""
    tracker = ProgressTracker()

    # Simulate some progress
    tracker.update_file_status("src/test_file.py", "analyzed", {"issues_found": 3})
    tracker.update_file_status("src/another_file.py", "implemented", {"issues_resolved": 2})

    # Record a session
    tracker.record_audit_session({"files_scanned": 100, "issues_found": 25, "proposals_created": 3})

    # Show dashboard

    # Export report
    report_path = tracker.export_report()
    logger.info(f"\n[OK] Report exported to: {report_path}")


if __name__ == "__main__":
    main()

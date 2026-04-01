"""NuSyQ-Hub Issue Resolution Tracking System.

Tracks:
- Issue detection and resolution over time
- Healing success rates by issue type
- Time-to-resolution metrics
- Regression detection (new issues from fixes)
- Resolution trends and patterns
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


def _resolve_tracking_dir() -> Path:
    """Resolve tracking directory anchored to repo root unless overridden.

    Priority:
    1) Environment variable RESOLUTION_TRACKER_DIR
    2) Repo-root Reports/resolution_tracking (robust to CWD changes)
    """
    env_dir = os.getenv("RESOLUTION_TRACKER_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()

    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "Reports" / "resolution_tracking"


# Data persistence
TRACKING_DIR = _resolve_tracking_dir()
TRACKING_DIR.mkdir(parents=True, exist_ok=True)

ISSUES_DB = TRACKING_DIR / "issues_database.jsonl"
RESOLUTIONS_DB = TRACKING_DIR / "resolutions_database.jsonl"


class IssueStatus(Enum):
    """Issue lifecycle status."""

    DETECTED = "detected"
    ROUTED = "routed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FAILED = "failed"
    REVERTED = "reverted"
    WONT_FIX = "wont_fix"


@dataclass
class IssueRecord:
    """Tracks a single issue from detection to resolution."""

    issue_id: str
    issue_type: str
    description: str
    file_path: str
    severity: str  # critical, high, medium, low, info
    detected_at: str
    detected_in_cycle: int

    status: str = IssueStatus.DETECTED.value
    status_history: list[dict[str, str]] = field(default_factory=list)
    routed_at: str | None = None
    routed_to_agent: str | None = None
    resolved_at: str | None = None
    resolution_duration_seconds: int = 0
    attempted_fix: str | None = None
    fix_success: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "IssueRecord":
        """Create from dictionary."""
        record = IssueRecord(
            issue_id=d["issue_id"],
            issue_type=d["issue_type"],
            description=d["description"],
            file_path=d["file_path"],
            severity=d["severity"],
            detected_at=d["detected_at"],
            detected_in_cycle=d["detected_in_cycle"],
        )
        record.status = d.get("status", IssueStatus.DETECTED.value)
        record.status_history = d.get("status_history", [])
        record.routed_at = d.get("routed_at")
        record.routed_to_agent = d.get("routed_to_agent")
        record.resolved_at = d.get("resolved_at")
        record.resolution_duration_seconds = d.get("resolution_duration_seconds", 0)
        record.attempted_fix = d.get("attempted_fix")
        record.fix_success = d.get("fix_success", False)
        return record


@dataclass
class ResolutionMetrics:
    """Aggregated resolution metrics."""

    total_detected: int = 0
    total_resolved: int = 0
    total_failed: int = 0
    resolution_rate: float = 0.0
    avg_resolution_time: float = 0.0
    by_issue_type: dict[str, dict[str, int]] = field(default_factory=dict)
    by_severity: dict[str, dict[str, int]] = field(default_factory=dict)
    by_agent: dict[str, dict[str, int]] = field(default_factory=dict)


class ResolutionTracker:
    """Tracks issue detection and resolution."""

    def __init__(self) -> None:
        """Initialize ResolutionTracker."""
        self.issues: dict[str, IssueRecord] = {}
        self.load_from_database()

    def load_from_database(self) -> None:
        """Load issue database from JSONL file."""
        if ISSUES_DB.exists():
            try:
                with open(ISSUES_DB) as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            record = IssueRecord.from_dict(data)
                            self.issues[record.issue_id] = record
                logger.info(f"✅ Loaded {len(self.issues)} issue records from database")
            except Exception as e:
                logger.error(f"Failed to load issue database: {e}")

    def register_detected_issue(
        self,
        issue_id: str,
        issue_type: str,
        description: str,
        file_path: str,
        severity: str,
        cycle_num: int,
    ) -> IssueRecord:
        """Register a newly detected issue."""
        record = IssueRecord(
            issue_id=issue_id,
            issue_type=issue_type,
            description=description,
            file_path=file_path,
            severity=severity,
            detected_at=datetime.now().isoformat(),
            detected_in_cycle=cycle_num,
        )

        self.issues[issue_id] = record
        self._append_to_database(record)

        logger.info(f"🔍 Registered issue: {issue_type} in {file_path}")
        return record

    def mark_routed(
        self,
        issue_id: str,
        agent: str,
    ) -> bool:
        """Mark issue as routed to agent."""
        if issue_id not in self.issues:
            logger.warning(f"Issue {issue_id} not found")
            return False

        record = self.issues[issue_id]
        record.status = IssueStatus.ROUTED.value
        record.routed_at = datetime.now().isoformat()
        record.routed_to_agent = agent
        record.status_history.append(
            {
                "status": IssueStatus.ROUTED.value,
                "timestamp": record.routed_at,
                "agent": agent,
            }
        )

        self._update_database()
        logger.info(f"📋 Routed issue {issue_id} to {agent}")
        return True

    def mark_in_progress(self, issue_id: str) -> bool:
        """Mark issue as being fixed."""
        if issue_id not in self.issues:
            return False

        record = self.issues[issue_id]
        record.status = IssueStatus.IN_PROGRESS.value
        record.status_history.append(
            {
                "status": IssueStatus.IN_PROGRESS.value,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self._update_database()
        return True

    def mark_resolved(
        self,
        issue_id: str,
        fix_code: str | None = None,
        success: bool = True,
    ) -> bool:
        """Mark issue as resolved."""
        if issue_id not in self.issues:
            return False

        record = self.issues[issue_id]
        record.status = IssueStatus.RESOLVED.value if success else IssueStatus.FAILED.value
        record.resolved_at = datetime.now().isoformat()
        record.attempted_fix = fix_code
        record.fix_success = success

        if record.routed_at:
            routed_time = datetime.fromisoformat(record.routed_at)
            resolved_time = datetime.fromisoformat(record.resolved_at)
            record.resolution_duration_seconds = int((resolved_time - routed_time).total_seconds())

        record.status_history.append(
            {
                "status": record.status,
                "timestamp": record.resolved_at,
                "success": str(success),
            }
        )

        self._update_database()

        status_msg = "✅ Resolved" if success else "❌ Failed"
        logger.info(f"{status_msg} issue {issue_id} ({record.resolution_duration_seconds}s)")
        return True

    def detect_regression(self, issue_id: str) -> bool:
        """Mark issue as regression (reappeared after fix)."""
        if issue_id not in self.issues:
            return False

        record = self.issues[issue_id]
        record.status = IssueStatus.REVERTED.value
        record.status_history.append(
            {
                "status": IssueStatus.REVERTED.value,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self._update_database()
        logger.warning(f"⚠️ Regression detected for issue {issue_id}")
        return True

    def _append_to_database(self, record: IssueRecord) -> None:
        """Append issue record to database file."""
        try:
            with open(ISSUES_DB, "a") as f:
                f.write(json.dumps(record.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to append to database: {e}")

    def _update_database(self) -> None:
        """Update entire database file (called after record modification)."""
        try:
            with open(ISSUES_DB, "w") as f:
                for record in self.issues.values():
                    f.write(json.dumps(record.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to update database: {e}")

    def get_metrics(
        self,
        since_hours: int = 24,
        issue_type: str | None = None,
        severity: str | None = None,
    ) -> ResolutionMetrics:
        """Calculate resolution metrics."""
        cutoff_time = datetime.now() - timedelta(hours=since_hours)

        filtered = [
            record
            for record in self.issues.values()
            if datetime.fromisoformat(record.detected_at) > cutoff_time
            and (issue_type is None or record.issue_type == issue_type)
            and (severity is None or record.severity == severity)
        ]

        metrics = ResolutionMetrics(total_detected=len(filtered))

        resolution_times: list[int] = []

        def _increment_outcome(
            bucket: dict[str, dict[str, int]],
            key: str,
            status: str,
        ) -> None:
            entry = bucket.setdefault(
                key,
                {
                    "detected": 0,
                    "resolved": 0,
                    "failed": 0,
                },
            )
            entry["detected"] += 1
            if status == IssueStatus.RESOLVED.value:
                entry["resolved"] += 1
            elif status == IssueStatus.FAILED.value:
                entry["failed"] += 1

        for record in filtered:
            status = record.status
            if status == IssueStatus.RESOLVED.value:
                metrics.total_resolved += 1
                resolution_times.append(record.resolution_duration_seconds)
            elif status == IssueStatus.FAILED.value:
                metrics.total_failed += 1

            _increment_outcome(metrics.by_issue_type, record.issue_type, status)
            _increment_outcome(metrics.by_severity, record.severity, status)

            if record.routed_to_agent:
                agent = record.routed_to_agent
                agent_entry = metrics.by_agent.setdefault(
                    agent, {"routed": 0, "resolved": 0, "failed": 0}
                )
                agent_entry["routed"] += 1
                if status == IssueStatus.RESOLVED.value:
                    agent_entry["resolved"] += 1
                elif status == IssueStatus.FAILED.value:
                    agent_entry["failed"] += 1

        if metrics.total_detected > 0:
            metrics.resolution_rate = (metrics.total_resolved / metrics.total_detected) * 100

        if resolution_times:
            metrics.avg_resolution_time = sum(resolution_times) / len(resolution_times)

        return metrics

    def get_regression_count(self, hours: int = 24) -> int:
        """Count regressions (issues that reappeared)."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return sum(
            1
            for r in self.issues.values()
            if r.status == IssueStatus.REVERTED.value
            and datetime.fromisoformat(r.detected_at) > cutoff_time
        )

    def generate_report(
        self,
        since_hours: int = 24,
    ) -> dict:
        """Generate comprehensive resolution report."""
        metrics = self.get_metrics(since_hours=since_hours)
        regressions = self.get_regression_count(since_hours)

        report = {
            "generated_at": datetime.now().isoformat(),
            "time_period_hours": since_hours,
            "summary": {
                "total_detected": metrics.total_detected,
                "total_resolved": metrics.total_resolved,
                "total_failed": metrics.total_failed,
                "resolution_rate_percent": round(metrics.resolution_rate, 2),
                "avg_resolution_time_seconds": round(metrics.avg_resolution_time, 1),
                "regressions": regressions,
            },
            "by_issue_type": metrics.by_issue_type,
            "by_severity": metrics.by_severity,
            "by_agent": metrics.by_agent,
        }

        # Save report
        report_file = (
            TRACKING_DIR / f"resolution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"📊 Resolution report saved: {report_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

        return report


# Module-level convenience functions
_tracker_instance: ResolutionTracker | None = None


def initialize_tracker() -> ResolutionTracker:
    """Initialize global tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ResolutionTracker()
    return _tracker_instance


def get_tracker() -> ResolutionTracker:
    """Get global tracker instance."""
    return initialize_tracker()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    tracker = initialize_tracker()

    # Register some issues
    issue1 = tracker.register_detected_issue(
        issue_id="issue_001",
        issue_type="unused_import",
        description="Unused import 'json'",
        file_path="src/module.py",
        severity="low",
        cycle_num=1,
    )

    # Mark as routed and resolved
    tracker.mark_routed(issue1.issue_id, "programmer")
    tracker.mark_in_progress(issue1.issue_id)
    tracker.mark_resolved(issue1.issue_id, fix_code="Removed import", success=True)

    # Generate report
    report = tracker.generate_report(since_hours=24)
    logger.info(json.dumps(report, indent=2))

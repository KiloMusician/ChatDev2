"""Snapshot Delta Tracking - Historical system state awareness.

Computes deltas between snapshots to detect trends:
- File churn (dirty count over time)
- Commit velocity (commits/day)
- Quest progression (tasks completed)
- Error reduction (import failures, test failures)
- Agent activity (which AI systems used)

Enables suggestions like:
- "Commit rate increased 3x this week"
- "Quest XYZ has been stalled for 5 days"
- "Import errors reduced from 12 to 2"
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class SnapshotMetrics:
    """Quantified snapshot state for delta computation."""

    timestamp: str
    dirty_file_count: int
    commits_ahead: int
    commits_behind: int
    quest_status: str  # "active", "blocked", "completed", "unknown"
    quest_title: str
    import_failures: int
    test_failures: int
    agent_activity: dict[str, int]  # {"ollama": 3, "chatdev": 0, "copilot": 12}

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SnapshotMetrics:
        """Load from dict."""
        return cls(**data)


@dataclass
class SnapshotDelta:
    """Computed delta between two snapshots."""

    previous_timestamp: str
    current_timestamp: str
    time_delta_hours: float

    # Changes
    dirty_file_delta: int  # positive = more dirty
    commits_ahead_delta: int  # positive = more commits
    quest_changed: bool
    import_failures_delta: int  # negative = improvement
    test_failures_delta: int
    agent_activity_delta: dict[str, int]

    # Derived insights
    insights: list[str]

    def to_markdown(self) -> str:
        """Render delta as markdown."""
        lines = []
        lines.append("## Snapshot Delta")
        lines.append(f"**Previous**: {self.previous_timestamp}")
        lines.append(f"**Current**: {self.current_timestamp}")
        lines.append(f"**Time elapsed**: {self.time_delta_hours:.1f} hours\n")

        lines.append("### Changes")

        if self.dirty_file_delta != 0:
            direction = "↑" if self.dirty_file_delta > 0 else "↓"
            lines.append(f"- Dirty files: {direction} {abs(self.dirty_file_delta)}")

        if self.commits_ahead_delta != 0:
            lines.append(f"- Commits ahead: ↑ {self.commits_ahead_delta}")

        if self.quest_changed:
            lines.append("- Quest status: **CHANGED**")

        if self.import_failures_delta != 0:
            direction = "⬆️ WORSE" if self.import_failures_delta > 0 else "✅ BETTER"
            lines.append(f"- Import failures: {direction} ({abs(self.import_failures_delta)})")

        if self.test_failures_delta != 0:
            direction = "⬆️ WORSE" if self.test_failures_delta > 0 else "✅ BETTER"
            lines.append(f"- Test failures: {direction} ({abs(self.test_failures_delta)})")

        if self.agent_activity_delta:
            lines.append("\n### Agent Activity")
            for agent, count in sorted(self.agent_activity_delta.items()):
                if count > 0:
                    lines.append(f"- {agent}: +{count} tasks")

        if self.insights:
            lines.append("\n### Insights")
            for insight in self.insights:
                lines.append(f"- {insight}")

        return "\n".join(lines)


class SnapshotDeltaTracker:
    """Tracks snapshot history and computes deltas."""

    def __init__(self, hub_path: Path) -> None:
        """Initialize tracker.

        Args:
            hub_path: NuSyQ-Hub root directory
        """
        self.hub_path = hub_path
        self.history_dir = hub_path / "state" / "snapshot_history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.current_file = self.history_dir / "current.json"
        self.history_file = self.history_dir / "history.jsonl"

    def save_snapshot(self, metrics: SnapshotMetrics) -> None:
        """Save current snapshot to history.

        Args:
            metrics: Current snapshot metrics
        """
        # Save as current
        self.current_file.write_text(json.dumps(metrics.to_dict(), indent=2), encoding="utf-8")

        # Append to history
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics.to_dict()) + "\n")

    def load_previous_snapshot(self) -> SnapshotMetrics | None:
        """Load most recent snapshot from history.

        Returns:
            Previous snapshot metrics, or None if no history
        """
        if not self.current_file.exists():
            return None

        try:
            data = json.loads(self.current_file.read_text(encoding="utf-8"))
            return SnapshotMetrics.from_dict(data)
        except Exception:
            return None

    def compute_delta(self, previous: SnapshotMetrics, current: SnapshotMetrics) -> SnapshotDelta:
        """Compute delta between two snapshots.

        Args:
            previous: Previous snapshot
            current: Current snapshot

        Returns:
            Computed delta with insights
        """
        # Parse timestamps
        prev_time = datetime.fromisoformat(previous.timestamp.replace("_", " "))
        curr_time = datetime.fromisoformat(current.timestamp.replace("_", " "))
        time_delta = (curr_time - prev_time).total_seconds() / 3600  # hours

        # Compute deltas
        dirty_delta = current.dirty_file_count - previous.dirty_file_count
        commits_delta = current.commits_ahead - previous.commits_ahead
        quest_changed = (
            current.quest_title != previous.quest_title
            or current.quest_status != previous.quest_status
        )
        import_delta = current.import_failures - previous.import_failures
        test_delta = current.test_failures - previous.test_failures

        # Agent activity delta
        agent_delta = {}
        all_agents = set(previous.agent_activity.keys()) | set(current.agent_activity.keys())
        for agent in all_agents:
            prev_count = previous.agent_activity.get(agent, 0)
            curr_count = current.agent_activity.get(agent, 0)
            if curr_count - prev_count > 0:
                agent_delta[agent] = curr_count - prev_count

        # Generate insights
        insights = []

        if commits_delta > 0:
            rate = commits_delta / max(time_delta, 0.1)
            insights.append(
                f"Commit velocity: {commits_delta} commits in {time_delta:.1f}h ({rate:.1f}/h)"
            )

        if dirty_delta < 0:
            insights.append(f"Cleaner workspace: {abs(dirty_delta)} fewer dirty files")
        elif dirty_delta > 5:
            insights.append(f"Workspace churn: {dirty_delta} more dirty files")

        if import_delta < 0:
            insights.append(f"Import health improved: {abs(import_delta)} fewer failures")
        elif import_delta > 0:
            insights.append(f"Import regressions: {import_delta} new failures")

        if test_delta < 0:
            insights.append(f"Test health improved: {abs(test_delta)} fewer failures")

        if quest_changed:
            if current.quest_status == "completed":
                insights.append(f"Quest '{previous.quest_title}' completed!")
            else:
                insights.append(
                    f"Quest changed: '{previous.quest_title}' → '{current.quest_title}'"
                )

        if time_delta > 24 and commits_delta == 0:
            insights.append(f"Stalled: {time_delta:.0f}h since last commit")

        if agent_delta:
            most_active = max(agent_delta.items(), key=lambda x: x[1])
            insights.append(f"Most active AI: {most_active[0]} ({most_active[1]} tasks)")

        return SnapshotDelta(
            previous_timestamp=previous.timestamp,
            current_timestamp=current.timestamp,
            time_delta_hours=time_delta,
            dirty_file_delta=dirty_delta,
            commits_ahead_delta=commits_delta,
            quest_changed=quest_changed,
            import_failures_delta=import_delta,
            test_failures_delta=test_delta,
            agent_activity_delta=agent_delta,
            insights=insights,
        )

    def get_trend_summary(self, window_hours: int = 168) -> list[str]:
        """Get trend summary over time window.

        Args:
            window_hours: Hours to look back (default: 1 week)

        Returns:
            List of trend insights
        """
        if not self.history_file.exists():
            return ["No historical data available"]

        # Read recent history
        lines = self.history_file.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return ["No historical snapshots found"]

        snapshots = []
        cutoff = datetime.now().timestamp() - (window_hours * 3600)

        for line in lines:
            try:
                data = json.loads(line)
                snapshot = SnapshotMetrics.from_dict(data)
                snapshot_time = datetime.fromisoformat(
                    snapshot.timestamp.replace("_", " ")
                ).timestamp()
                if snapshot_time >= cutoff:
                    snapshots.append(snapshot)
            except Exception:
                continue

        if len(snapshots) < 2:
            return [f"Only {len(snapshots)} snapshot(s) in last {window_hours}h"]

        # Compute trends
        trends = []
        first = snapshots[0]
        last = snapshots[-1]

        total_commits = last.commits_ahead - first.commits_ahead
        trends.append(f"{len(snapshots)} snapshots over {window_hours}h")
        trends.append(f"Total commits: {total_commits}")

        if total_commits > 0:
            days = window_hours / 24
            trends.append(f"Commit rate: {total_commits / days:.1f} commits/day")

        # Import health trend
        if last.import_failures < first.import_failures:
            improvement = first.import_failures - last.import_failures
            trends.append(f"Import health: ✅ {improvement} failures resolved")

        return trends

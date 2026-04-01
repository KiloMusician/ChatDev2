"""Autonomy Dashboard - Phase 3 Real-Time Monitoring & Metrics.

Collects, aggregates, and visualizes autonomy system performance:
- Task queue metrics (pending, completed, failed)
- Risk distribution (AUTO/REVIEW/PROPOSAL/BLOCKED)
- Model utilization tracking
- Merge success rates
- Scheduler performance

OmniTag: [observability, dashboard, metrics, phase3]
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""

    TASK_COMPLETION = "task_completion"
    PR_CREATED = "pr_created"
    PR_MERGED = "pr_merged"
    PR_REJECTED = "pr_rejected"
    RISK_ASSESSMENT = "risk_assessment"
    MODEL_INVOCATION = "model_invocation"
    SCHEDULER_DECISION = "scheduler_decision"
    SYSTEM_HEALTH = "system_health"


@dataclass
class MetricEvent:
    """Individual metric event."""

    metric_type: MetricType
    timestamp: datetime
    data: dict[str, Any]
    task_id: int | None = None
    pr_number: int | None = None


@dataclass
class DashboardMetrics:
    """Aggregated dashboard metrics snapshot."""

    timestamp: datetime = field(default_factory=datetime.now)

    # Task Queue Stats
    total_tasks: int = 0
    pending_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    autonomy_ready_tasks: int = 0

    # Risk Distribution
    risk_auto_count: int = 0  # < 0.3
    risk_review_count: int = 0  # 0.3-0.6
    risk_proposal_count: int = 0  # 0.6-0.8
    risk_blocked_count: int = 0  # > 0.8

    # PR Metrics
    prs_created_today: int = 0
    prs_merged_today: int = 0
    prs_auto_merged_today: int = 0
    prs_rejected_today: int = 0
    avg_pr_merge_time_hours: float = 0.0

    # Model Utilization
    ollama_invocations: int = 0
    lm_studio_invocations: int = 0
    chatdev_invocations: int = 0
    copilot_invocations: int = 0

    # Scheduler Performance
    avg_task_score: float = 0.0
    diversity_score: float = 0.0  # 0.0-1.0 (higher = more diverse)
    category_distribution: dict[str, int] = field(default_factory=dict)

    # Success Rates
    pr_success_rate: float = 0.0  # % merged successfully
    auto_merge_success_rate: float = 0.0  # % auto-merged without issues
    test_pass_rate: float = 0.0  # % PRs with passing tests

    # System Health
    queue_processing_rate: float = 0.0  # tasks/hour
    avg_task_duration_minutes: float = 0.0
    error_rate: float = 0.0  # % tasks that error

    # Advanced AI / learning signals
    advanced_ai_ready_count: int = 0
    advanced_ai_partial_count: int = 0
    advanced_ai_missing_count: int = 0
    meta_learning_total_events: int = 0
    meta_learning_error_events: int = 0
    meta_learning_routed_events: int = 0
    meta_learning_max_recursion_depth: int = 0


class MetricsCollector:
    """Collects and aggregates metrics for dashboard."""

    def __init__(
        self,
        retention_days: int = 30,
        aggregation_interval_minutes: int = 5,
        storage_path: Path | None = None,
    ):
        """Initialize MetricsCollector with retention_days, aggregation_interval_minutes, storage_path."""
        self.retention_days = retention_days
        self.aggregation_interval = aggregation_interval_minutes
        self.storage_path = storage_path or Path("state/metrics/dashboard")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory event buffer (last 1000 events)
        self.event_buffer: deque[MetricEvent] = deque(maxlen=1000)

        # Current snapshot
        self.current_snapshot = DashboardMetrics()

        # Aggregation tracking
        self.last_aggregation = datetime.now()
        self.aggregation_lock = asyncio.Lock()
        reports_root = self.storage_path.parent.parent / "reports"
        self.meta_learning_report = reports_root / "ai_intermediary_meta_learning_latest.json"
        self.ai_status_report = reports_root / "ai_status_latest.json"
        self.latest_report_path = reports_root / "autonomy_dashboard_latest.json"

    async def record_event(self, event: MetricEvent):
        """Record a metric event."""
        self.event_buffer.append(event)

        # Trigger aggregation if interval passed
        if (datetime.now() - self.last_aggregation).total_seconds() > (
            self.aggregation_interval * 60
        ):
            await self.aggregate_metrics()

    async def record_task_completion(
        self, task_id: int, success: bool, duration_seconds: float, category: str
    ):
        """Record task completion event."""
        event = MetricEvent(
            metric_type=MetricType.TASK_COMPLETION,
            timestamp=datetime.now(),
            task_id=task_id,
            data={
                "success": success,
                "duration_seconds": duration_seconds,
                "category": category,
            },
        )
        await self.record_event(event)

    async def record_pr_created(
        self,
        pr_number: int,
        task_id: int,
        risk_score: float,
        risk_level: str,
        approval_policy: str,
    ):
        """Record PR creation event."""
        event = MetricEvent(
            metric_type=MetricType.PR_CREATED,
            timestamp=datetime.now(),
            task_id=task_id,
            pr_number=pr_number,
            data={
                "risk_score": risk_score,
                "risk_level": risk_level,
                "approval_policy": approval_policy,
            },
        )
        await self.record_event(event)

    async def record_pr_merged(self, pr_number: int, auto_merged: bool, merge_time_hours: float):
        """Record PR merge event."""
        event = MetricEvent(
            metric_type=MetricType.PR_MERGED,
            timestamp=datetime.now(),
            pr_number=pr_number,
            data={
                "auto_merged": auto_merged,
                "merge_time_hours": merge_time_hours,
            },
        )
        await self.record_event(event)

    async def record_model_invocation(self, model_name: str, task_id: int | None = None):
        """Record AI model invocation."""
        event = MetricEvent(
            metric_type=MetricType.MODEL_INVOCATION,
            timestamp=datetime.now(),
            task_id=task_id,
            data={"model": model_name},
        )
        await self.record_event(event)

    async def record_risk_assessment(self, task_id: int, risk_score: float, risk_level: str):
        """Record risk assessment."""
        event = MetricEvent(
            metric_type=MetricType.RISK_ASSESSMENT,
            timestamp=datetime.now(),
            task_id=task_id,
            data={"risk_score": risk_score, "risk_level": risk_level},
        )
        await self.record_event(event)

    async def aggregate_metrics(self) -> DashboardMetrics:
        """Aggregate events into dashboard snapshot."""
        async with self.aggregation_lock:
            snapshot = DashboardMetrics()

            # Get today's cutoff
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # Process events
            today_events = [e for e in self.event_buffer if e.timestamp >= today_start]

            # Task completions
            task_completions = [
                e for e in today_events if e.metric_type == MetricType.TASK_COMPLETION
            ]
            snapshot.completed_tasks = len(task_completions)
            snapshot.failed_tasks = sum(
                1 for e in task_completions if not e.data.get("success", True)
            )

            if task_completions:
                durations = [e.data.get("duration_seconds", 0) for e in task_completions]
                snapshot.avg_task_duration_minutes = sum(durations) / len(durations) / 60.0

            # Category distribution
            category_counts = defaultdict(int)
            for e in task_completions:
                category = e.data.get("category", "unknown")
                category_counts[category] += 1
            snapshot.category_distribution = dict(category_counts)

            # Calculate diversity score (Shannon entropy)
            if category_counts:
                total = sum(category_counts.values())
                probabilities = [count / total for count in category_counts.values()]
                import math

                entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
                max_entropy = math.log2(len(category_counts))
                snapshot.diversity_score = entropy / max_entropy if max_entropy > 0 else 0.0

            # PR events
            pr_created = [e for e in today_events if e.metric_type == MetricType.PR_CREATED]
            pr_merged = [e for e in today_events if e.metric_type == MetricType.PR_MERGED]

            snapshot.prs_created_today = len(pr_created)
            snapshot.prs_merged_today = len(pr_merged)
            snapshot.prs_auto_merged_today = sum(
                1 for e in pr_merged if e.data.get("auto_merged", False)
            )

            if pr_merged:
                merge_times = [e.data.get("merge_time_hours", 0) for e in pr_merged]
                snapshot.avg_pr_merge_time_hours = sum(merge_times) / len(merge_times)

            # Risk distribution
            risk_assessments = [
                e for e in today_events if e.metric_type == MetricType.RISK_ASSESSMENT
            ]
            for e in risk_assessments:
                score = e.data.get("risk_score", 0.5)
                if score < 0.3:
                    snapshot.risk_auto_count += 1
                elif score < 0.6:
                    snapshot.risk_review_count += 1
                elif score < 0.8:
                    snapshot.risk_proposal_count += 1
                else:
                    snapshot.risk_blocked_count += 1

            # Model invocations
            model_events = [e for e in today_events if e.metric_type == MetricType.MODEL_INVOCATION]
            for e in model_events:
                model = e.data.get("model", "").lower()
                if "ollama" in model:
                    snapshot.ollama_invocations += 1
                elif "lm" in model or "studio" in model:
                    snapshot.lm_studio_invocations += 1
                elif "chatdev" in model:
                    snapshot.chatdev_invocations += 1
                elif "copilot" in model:
                    snapshot.copilot_invocations += 1

            # Success rates
            if snapshot.prs_created_today > 0:
                snapshot.pr_success_rate = snapshot.prs_merged_today / snapshot.prs_created_today

            if snapshot.prs_merged_today > 0:
                snapshot.auto_merge_success_rate = (
                    snapshot.prs_auto_merged_today / snapshot.prs_merged_today
                )

            self._apply_advanced_ai_intelligence(snapshot)

            # Save snapshot
            self.current_snapshot = snapshot
            self.last_aggregation = datetime.now()
            await self._persist_snapshot(snapshot)

            logger.debug(
                f"Metrics aggregated: {snapshot.completed_tasks} tasks, {snapshot.prs_created_today} PRs"
            )
            try:
                from src.system.agent_awareness import emit as _emit

                _emit(
                    "metrics",
                    (
                        f"Dashboard snapshot: tasks={snapshot.completed_tasks} "
                        f"failed={snapshot.failed_tasks} PRs={snapshot.prs_created_today} "
                        f"models={snapshot.model_invocations}"
                    ),
                    level="INFO",
                    source="autonomy_dashboard",
                )
            except Exception:
                pass

            return snapshot

    async def _persist_snapshot(self, snapshot: DashboardMetrics):
        """Save snapshot to disk."""
        try:
            self.latest_report_path.parent.mkdir(parents=True, exist_ok=True)
            filename = f"snapshot_{snapshot.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.storage_path / filename

            with open(filepath, "w") as f:
                json.dump(asdict(snapshot), f, indent=2, default=str)
            with open(self.latest_report_path, "w") as f:
                json.dump(asdict(snapshot), f, indent=2, default=str)

            # Cleanup old snapshots
            await self._cleanup_old_snapshots()
        except Exception as e:
            logger.error(f"Failed to persist snapshot: {e}")

    async def _cleanup_old_snapshots(self):
        """Remove snapshots older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)

        for filepath in self.storage_path.glob("snapshot_*.json"):
            try:
                # Parse timestamp from filename
                timestamp_str = filepath.stem.replace("snapshot_", "")
                file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if file_time < cutoff:
                    filepath.unlink()
                    logger.debug(f"Deleted old snapshot: {filepath.name}")
            except Exception as e:
                logger.warning(f"Failed to process snapshot {filepath}: {e}")

    def _apply_advanced_ai_intelligence(self, snapshot: DashboardMetrics) -> None:
        """Overlay persisted advanced AI readiness and meta-learning signals."""
        if self.ai_status_report.exists():
            try:
                payload = json.loads(self.ai_status_report.read_text(encoding="utf-8"))
                capability_intel = payload.get("capability_intelligence", {})
                readiness = capability_intel.get("advanced_ai_readiness", {})
                capabilities = readiness.get("capabilities", {})
                if isinstance(capabilities, dict):
                    statuses = [
                        details.get("status")
                        for details in capabilities.values()
                        if isinstance(details, dict)
                    ]
                    snapshot.advanced_ai_ready_count = sum(
                        1 for status in statuses if status == "ready"
                    )
                    snapshot.advanced_ai_partial_count = sum(
                        1 for status in statuses if status == "partial"
                    )
                    snapshot.advanced_ai_missing_count = sum(
                        1 for status in statuses if status == "missing"
                    )
            except Exception as exc:
                logger.debug("Failed to load ai_status capability intelligence: %s", exc)

        if self.meta_learning_report.exists():
            try:
                payload = json.loads(self.meta_learning_report.read_text(encoding="utf-8"))
                meta = payload.get("snapshot", {})
                snapshot.meta_learning_total_events = int(meta.get("total_events", 0) or 0)
                snapshot.meta_learning_error_events = int(meta.get("error_events", 0) or 0)
                snapshot.meta_learning_routed_events = int(meta.get("routed_events", 0) or 0)
                snapshot.meta_learning_max_recursion_depth = int(
                    meta.get("max_recursion_depth", 0) or 0
                )
            except Exception as exc:
                logger.debug("Failed to load meta-learning report: %s", exc)

    def get_current_snapshot(self) -> DashboardMetrics:
        """Get current metrics snapshot."""
        return self.current_snapshot

    async def get_historical_snapshots(self, hours: int = 24) -> list[DashboardMetrics]:
        """Load historical snapshots from disk."""
        cutoff = datetime.now() - timedelta(hours=hours)
        snapshots = []

        for filepath in sorted(self.storage_path.glob("snapshot_*.json")):
            try:
                timestamp_str = filepath.stem.replace("snapshot_", "")
                file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if file_time >= cutoff:
                    with open(filepath) as f:
                        data = json.load(f)
                        # Reconstruct DashboardMetrics (simplified)
                        snapshot = DashboardMetrics(**data)
                        snapshots.append(snapshot)
            except Exception as e:
                logger.warning(f"Failed to load snapshot {filepath}: {e}")

        return snapshots

    def generate_text_dashboard(self) -> str:
        """Generate simple text-based dashboard."""
        s = self.current_snapshot

        dashboard = f"""
╔═══════════════════════════════════════════════════════════════╗
║              🎯 NuSyQ Autonomy Dashboard                      ║
║              Generated: {s.timestamp.strftime("%Y-%m-%d %H:%M:%S")}                    ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  📊 Task Queue Status                                         ║
║     Total Tasks: {s.total_tasks:<5}                                      ║
║     Completed:   {s.completed_tasks:<5} ({s.completed_tasks * 100 // max(1, s.total_tasks)}%)                                   ║
║     Failed:      {s.failed_tasks:<5}                                      ║
║     Pending:     {s.pending_tasks:<5}                                      ║
║                                                               ║
║  ⚖️  Risk Distribution                                         ║
║     AUTO     (<0.3): {s.risk_auto_count:<3} ({s.risk_auto_count * 100 // max(1, s.risk_auto_count + s.risk_review_count + s.risk_proposal_count + s.risk_blocked_count)}%)                            ║
║     REVIEW   (0.3-0.6): {s.risk_review_count:<3} ({s.risk_review_count * 100 // max(1, s.risk_auto_count + s.risk_review_count + s.risk_proposal_count + s.risk_blocked_count)}%)                            ║
║     PROPOSAL (0.6-0.8): {s.risk_proposal_count:<3} ({s.risk_proposal_count * 100 // max(1, s.risk_auto_count + s.risk_review_count + s.risk_proposal_count + s.risk_blocked_count)}%)                            ║
║     BLOCKED  (>0.8): {s.risk_blocked_count:<3} ({s.risk_blocked_count * 100 // max(1, s.risk_auto_count + s.risk_review_count + s.risk_proposal_count + s.risk_blocked_count)}%)                            ║
║                                                               ║
║  🔀 PR Metrics (Today)                                        ║
║     Created:     {s.prs_created_today:<3}                                        ║
║     Merged:      {s.prs_merged_today:<3} (Success: {s.pr_success_rate * 100:.0f}%)                    ║
║     Auto-Merged: {s.prs_auto_merged_today:<3} ({s.auto_merge_success_rate * 100:.0f}% of merges)              ║
║     Avg Merge Time: {s.avg_pr_merge_time_hours:.1f} hours                         ║
║                                                               ║
║  🤖 Model Utilization                                         ║
║     Ollama:    {s.ollama_invocations:<3} invocations                             ║
║     LM Studio: {s.lm_studio_invocations:<3} invocations                             ║
║     ChatDev:   {s.chatdev_invocations:<3} invocations                             ║
║     Copilot:   {s.copilot_invocations:<3} invocations                             ║
║                                                               ║
║  📈 Performance                                               ║
║     Diversity Score: {s.diversity_score:.2f}/1.00                           ║
║     Avg Task Duration: {s.avg_task_duration_minutes:.1f} min                        ║
║     Processing Rate: {s.queue_processing_rate:.1f} tasks/hour                 ║
║                                                               ║
║  🧠 Advanced AI                                                ║
║     Ready / Partial / Missing: {s.advanced_ai_ready_count:<2} / {s.advanced_ai_partial_count:<2} / {s.advanced_ai_missing_count:<2}                       ║
║     Meta-Learning Events: {s.meta_learning_total_events:<4}                         ║
║     Routed / Errors: {s.meta_learning_routed_events:<4} / {s.meta_learning_error_events:<4}                           ║
║     Max Recursion Depth: {s.meta_learning_max_recursion_depth:<3}                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        return dashboard


# Global collector instance
_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
        logger.info("✅ Autonomy Dashboard Metrics Collector initialized")
    return _collector


async def start_dashboard_collector(
    orchestrator: Any = None, scheduler: Any = None
) -> MetricsCollector:
    """Start dashboard metrics collection."""
    collector = get_metrics_collector()

    # Initial aggregation
    await collector.aggregate_metrics()

    logger.info("✅ Dashboard collector started (Phase 3)")
    logger.info(f"   - Storage: {collector.storage_path}")
    logger.info(f"   - Retention: {collector.retention_days} days")
    logger.info(f"   - Aggregation: Every {collector.aggregation_interval} minutes")

    return collector

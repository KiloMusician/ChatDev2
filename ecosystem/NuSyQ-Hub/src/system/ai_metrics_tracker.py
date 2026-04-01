#!/usr/bin/env python3
"""AI System Metrics Tracking - Uptime, Gate Rates, Health History.

Tracks AI system availability, work gate decisions, and health trends
for operational monitoring and diagnostics.

OmniTag: [monitoring, metrics, ai_health, uptime_tracking, gate_analytics]
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    from datetime import timezone

    UTC = timezone.utc  # noqa: UP017


@dataclass
class AIHealthMetric:
    """Single AI system health measurement."""

    timestamp: str
    system_name: str
    available: bool
    latency_ms: float | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class GateDecision:
    """Work gate decision record."""

    timestamp: str
    gate_status: str  # "open" | "closed"
    ai_systems_available: int
    ai_systems_total: int
    hygiene_status: str | None = None
    quests_available: bool | None = None
    reason: str | None = None


@dataclass
class DispatchProfileMetric:
    """Single dispatch profile telemetry event."""

    timestamp: str
    system_name: str
    mode: str
    risk_level: str
    signal_budget: str
    status: str
    non_blocking: bool
    metadata: dict[str, Any] | None = None


class AIMetricsTracker:
    """Tracks AI system metrics and gate decisions."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize metrics tracker.

        Args:
            repo_root: Repository root path (default: current directory)
        """
        self.repo_root = repo_root or Path.cwd()
        self.metrics_dir = self.repo_root / "state" / "metrics"
        self.health_file = self.metrics_dir / "ai_health_history.jsonl"
        self.gate_file = self.metrics_dir / "gate_decisions.jsonl"
        self.dispatch_profile_file = self.metrics_dir / "dispatch_profile_history.jsonl"

        # Ensure directories exist
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def record_health(
        self,
        system_name: str,
        available: bool,
        latency_ms: float | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record AI system health measurement.

        Args:
            system_name: Name of AI system (ollama, chatdev, quantum, etc.)
            available: Whether system is available
            latency_ms: Response latency in milliseconds
            error: Error message if unavailable
            metadata: Additional metadata
        """
        metric = AIHealthMetric(
            timestamp=datetime.now(UTC).isoformat(),
            system_name=system_name,
            available=available,
            latency_ms=latency_ms,
            error=error,
            metadata=metadata,
        )

        with self.health_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metric)) + "\n")

    def record_gate_decision(
        self,
        gate_status: str,
        ai_systems_available: int,
        ai_systems_total: int,
        hygiene_status: str | None = None,
        quests_available: bool | None = None,
        reason: str | None = None,
    ) -> None:
        """Record work gate decision.

        Args:
            gate_status: "open" or "closed"
            ai_systems_available: Number of AI systems healthy
            ai_systems_total: Total number of AI systems
            hygiene_status: Repository hygiene status
            quests_available: Whether quests are available
            reason: Reason for gate decision
        """
        decision = GateDecision(
            timestamp=datetime.now(UTC).isoformat(),
            gate_status=gate_status,
            ai_systems_available=ai_systems_available,
            ai_systems_total=ai_systems_total,
            hygiene_status=hygiene_status,
            quests_available=quests_available,
            reason=reason,
        )

        with self.gate_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(decision)) + "\n")

    def record_dispatch_profile(
        self,
        system_name: str,
        mode: str,
        risk_level: str,
        signal_budget: str,
        status: str,
        non_blocking: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record dispatch profile telemetry for routing observability."""
        metric = DispatchProfileMetric(
            timestamp=datetime.now(UTC).isoformat(),
            system_name=system_name,
            mode=str(mode or "balanced"),
            risk_level=str(risk_level or "medium"),
            signal_budget=str(signal_budget or "normal"),
            status=str(status or "unknown"),
            non_blocking=bool(non_blocking),
            metadata=metadata,
        )

        with self.dispatch_profile_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metric)) + "\n")

    def get_uptime_stats(self, hours: int = 24) -> dict[str, Any]:
        """Calculate AI system uptime statistics.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with uptime stats per system
        """
        if not self.health_file.exists():
            return {}

        cutoff = datetime.now(UTC).timestamp() - (hours * 3600)
        stats: dict[str, dict[str, Any]] = {}

        with self.health_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    metric = json.loads(line)
                    ts = datetime.fromisoformat(metric["timestamp"]).timestamp()

                    if ts < cutoff:
                        continue

                    system = metric["system_name"]
                    if system not in stats:
                        stats[system] = {
                            "total_checks": 0,
                            "available_checks": 0,
                            "total_latency_ms": 0.0,
                            "latency_count": 0,
                        }

                    stats[system]["total_checks"] += 1
                    if metric["available"]:
                        stats[system]["available_checks"] += 1

                    if metric.get("latency_ms") is not None:
                        stats[system]["total_latency_ms"] += metric["latency_ms"]
                        stats[system]["latency_count"] += 1

                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

        # Calculate percentages and averages
        for _system, data in stats.items():
            if data["total_checks"] > 0:
                data["uptime_percent"] = (data["available_checks"] / data["total_checks"]) * 100
            if data["latency_count"] > 0:
                data["avg_latency_ms"] = data["total_latency_ms"] / data["latency_count"]

        return stats

    def get_gate_stats(self, hours: int = 24) -> dict[str, Any]:
        """Calculate work gate statistics.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with gate decision stats
        """
        if not self.gate_file.exists():
            return {"total_decisions": 0, "open_count": 0, "closed_count": 0}

        cutoff = datetime.now(UTC).timestamp() - (hours * 3600)
        stats: dict[str, Any] = {
            "total_decisions": 0,
            "open_count": 0,
            "closed_count": 0,
            "reasons": {},
        }

        with self.gate_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    decision = json.loads(line)
                    ts = datetime.fromisoformat(decision["timestamp"]).timestamp()

                    if ts < cutoff:
                        continue

                    stats["total_decisions"] += 1
                    if decision["gate_status"] == "open":
                        stats["open_count"] += 1
                    else:
                        stats["closed_count"] += 1

                    reason = decision.get("reason", "unknown")
                    stats["reasons"][reason] = stats["reasons"].get(reason, 0) + 1

                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

        if stats["total_decisions"] > 0:
            stats["open_rate_percent"] = (stats["open_count"] / stats["total_decisions"]) * 100

        return stats

    def get_dispatch_profile_stats(self, hours: int = 24) -> dict[str, Any]:
        """Calculate dispatch profile telemetry aggregates."""
        if not self.dispatch_profile_file.exists():
            return {
                "total_dispatches": 0,
                "by_mode": {},
                "by_risk_level": {},
                "by_signal_budget": {},
                "by_system": {},
                "by_status": {},
                "non_blocking_count": 0,
                "blocking_count": 0,
            }

        cutoff = datetime.now(UTC).timestamp() - (hours * 3600)
        stats: dict[str, Any] = {
            "total_dispatches": 0,
            "by_mode": {},
            "by_risk_level": {},
            "by_signal_budget": {},
            "by_system": {},
            "by_status": {},
            "non_blocking_count": 0,
            "blocking_count": 0,
        }

        with self.dispatch_profile_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    metric = json.loads(line)
                    ts = datetime.fromisoformat(metric["timestamp"]).timestamp()
                    if ts < cutoff:
                        continue

                    stats["total_dispatches"] += 1

                    mode = str(metric.get("mode", "balanced"))
                    risk = str(metric.get("risk_level", "medium"))
                    budget = str(metric.get("signal_budget", "normal"))
                    system = str(metric.get("system_name", "unknown"))
                    status = str(metric.get("status", "unknown"))
                    non_blocking = bool(metric.get("non_blocking", False))

                    stats["by_mode"][mode] = stats["by_mode"].get(mode, 0) + 1
                    stats["by_risk_level"][risk] = stats["by_risk_level"].get(risk, 0) + 1
                    stats["by_signal_budget"][budget] = stats["by_signal_budget"].get(budget, 0) + 1
                    stats["by_system"][system] = stats["by_system"].get(system, 0) + 1
                    stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

                    if non_blocking:
                        stats["non_blocking_count"] += 1
                    else:
                        stats["blocking_count"] += 1
                except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                    continue

        total = stats["total_dispatches"]
        if total > 0:
            stats["non_blocking_rate_percent"] = (stats["non_blocking_count"] / total) * 100

        return stats


def generate_metrics_report(repo_root: Path | None = None, hours: int = 24) -> str:
    """Generate comprehensive metrics report.

    Args:
        repo_root: Repository root path
        hours: Number of hours to analyze

    Returns:
        Formatted metrics report
    """
    tracker = AIMetricsTracker(repo_root)
    uptime = tracker.get_uptime_stats(hours)
    gate = tracker.get_gate_stats(hours)
    dispatch = tracker.get_dispatch_profile_stats(hours)

    lines = [
        "📊 AI SYSTEM METRICS REPORT",
        f"Period: Last {hours} hours",
        "=" * 70,
        "",
        "## AI System Uptime",
        "",
    ]

    if uptime:
        for system, stats in uptime.items():
            lines.append(f"### {system.upper()}")
            lines.append(
                f"  Uptime: {stats.get('uptime_percent', 0):.1f}% "
                f"({stats['available_checks']}/{stats['total_checks']} checks)"
            )
            if "avg_latency_ms" in stats:
                lines.append(f"  Avg Latency: {stats['avg_latency_ms']:.1f}ms")
            lines.append("")
    else:
        lines.append("  No health data recorded yet")
        lines.append("")

    lines.extend(
        [
            "## Work Gate Decisions",
            "",
        ]
    )

    if gate["total_decisions"] > 0:
        lines.append(f"  Total Decisions: {gate['total_decisions']}")
        lines.append(f"  Gate Open: {gate['open_count']} ({gate.get('open_rate_percent', 0):.1f}%)")
        lines.append(f"  Gate Closed: {gate['closed_count']}")
        lines.append("")
        if gate["reasons"]:
            lines.append("  Reasons:")
            for reason, count in sorted(gate["reasons"].items(), key=lambda x: x[1], reverse=True):
                lines.append(f"    - {reason}: {count}")
    else:
        lines.append("  No gate decisions recorded yet")

    lines.extend(
        [
            "",
            "## Dispatch Profile Signals",
            "",
        ]
    )

    if dispatch["total_dispatches"] > 0:
        lines.append(f"  Total Dispatches: {dispatch['total_dispatches']}")
        lines.append(
            f"  Non-Blocking: {dispatch['non_blocking_count']} ({dispatch.get('non_blocking_rate_percent', 0):.1f}%)"
        )
        lines.append(f"  Blocking: {dispatch['blocking_count']}")

        if dispatch["by_mode"]:
            lines.append("  Modes:")
            for mode, count in sorted(
                dispatch["by_mode"].items(),
                key=lambda item: item[1],
                reverse=True,
            ):
                lines.append(f"    - {mode}: {count}")

        if dispatch["by_signal_budget"]:
            lines.append("  Signal Budgets:")
            for budget, count in sorted(
                dispatch["by_signal_budget"].items(),
                key=lambda item: item[1],
                reverse=True,
            ):
                lines.append(f"    - {budget}: {count}")
    else:
        lines.append("  No dispatch profile telemetry recorded yet")

    return "\n".join(lines)


if __name__ == "__main__":
    logger.info(generate_metrics_report())

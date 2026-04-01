"""Token Metrics Dashboard: Real-time SNS-Core and Zero-Token Savings Tracking.

Provides comprehensive metrics on token usage, savings, and cost optimization.

[OmniTag: token_metrics_dashboard, observability, sns_core, cost_tracking, zero_token]
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TokenMetrics:
    """Token usage metrics snapshot."""

    timestamp: str
    original_tokens: int
    sns_tokens: int
    savings_pct: float
    operation: str = "unknown"
    mode: str = "normal"  # normal or aggressive

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "original_tokens": self.original_tokens,
            "sns_tokens": self.sns_tokens,
            "savings_pct": self.savings_pct,
            "operation": self.operation,
            "mode": self.mode,
        }


class TokenMetricsDashboard:
    """Tracks and reports token usage metrics."""

    def __init__(self, state_dir: Path = Path("state")):
        """Initialize metrics dashboard.

        Args:
            state_dir: Directory to store metrics files
        """
        self.state_dir = state_dir
        self.report_dir = state_dir / "reports"
        self.metrics_file = state_dir / "token_metrics.jsonl"
        self.summary_file = state_dir / "token_metrics_summary.json"
        self.report_summary_file = self.report_dir / "token_metrics_summary.json"
        self.compatibility_summary_file = self.report_dir / "token_optimization_metrics.json"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def record_metric(self, metric: TokenMetrics) -> None:
        """Record a single token metric."""
        try:
            with open(self.metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metric.to_dict()) + "\n")
            self.save_summary()
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)

    def record_conversion(
        self,
        original_tokens: int,
        sns_tokens: int,
        operation: str = "conversion",
        mode: str = "normal",
    ) -> None:
        """Record SNS-Core conversion metric."""
        savings_pct = (
            ((original_tokens - sns_tokens) / original_tokens * 100) if original_tokens > 0 else 0
        )
        metric = TokenMetrics(
            timestamp=datetime.now().isoformat(),
            original_tokens=original_tokens,
            sns_tokens=sns_tokens,
            savings_pct=round(savings_pct, 1),
            operation=operation,
            mode=mode,
        )
        self.record_metric(metric)

    def get_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get metrics summary for recent period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        metrics = []

        if not self.metrics_file.exists():
            return self._empty_summary()

        try:
            with open(self.metrics_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        ts = datetime.fromisoformat(data["timestamp"])
                        if ts >= cutoff_time:
                            metrics.append(data)
                    except (json.JSONDecodeError, ValueError, KeyError):
                        continue
        except Exception:
            return self._empty_summary()

        if not metrics:
            return self._empty_summary()

        # Calculate summary statistics
        total_original = sum(m["original_tokens"] for m in metrics)
        total_sns = sum(m["sns_tokens"] for m in metrics)
        avg_savings = sum(m["savings_pct"] for m in metrics) / len(metrics)
        max_savings = max(m["savings_pct"] for m in metrics)
        min_savings = min(m["savings_pct"] for m in metrics)

        # Count by mode
        normal_count = sum(1 for m in metrics if m.get("mode") == "normal")
        aggressive_count = sum(1 for m in metrics if m.get("mode") == "aggressive")

        # Count by operation
        operations: dict[str, int] = {}
        for m in metrics:
            op = m.get("operation", "unknown")
            operations[op] = operations.get(op, 0) + 1

        return {
            "period_hours": hours,
            "metrics_count": len(metrics),
            "total_original_tokens": total_original,
            "total_sns_tokens": total_sns,
            "total_savings_tokens": total_original - total_sns,
            "avg_savings_pct": round(avg_savings, 1),
            "max_savings_pct": round(max_savings, 1),
            "min_savings_pct": round(min_savings, 1),
            "conversion_modes": {
                "normal": normal_count,
                "aggressive": aggressive_count,
            },
            "by_operation": operations,
            "estimated_cost_savings": self._estimate_cost_savings(total_original, total_sns),
        }

    def _empty_summary(self) -> dict[str, Any]:
        """Return empty summary template."""
        return {
            "period_hours": 24,
            "metrics_count": 0,
            "total_original_tokens": 0,
            "total_sns_tokens": 0,
            "total_savings_tokens": 0,
            "avg_savings_pct": 0.0,
            "max_savings_pct": 0.0,
            "min_savings_pct": 0.0,
            "conversion_modes": {"normal": 0, "aggressive": 0},
            "by_operation": {},
            "estimated_cost_savings": "$0.00",
        }

    def _estimate_cost_savings(self, original_tokens: int, sns_tokens: int) -> str:
        """Estimate USD cost savings."""
        # GPT-4 pricing approx: $0.03 per 1K tokens
        savings_tokens = original_tokens - sns_tokens
        savings_dollars = (savings_tokens / 1000) * 0.03
        return f"${savings_dollars:.2f}"

    def save_summary(self, hours: int = 24) -> None:
        """Save summary to file."""
        summary = self.get_summary(hours)
        summary_payload = {
            **summary,
            "generated_at": datetime.now().isoformat(),
            "source": "token_metrics_dashboard",
            "summary": summary,
        }
        try:
            with open(self.summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            with open(self.report_summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            with open(self.compatibility_summary_file, "w", encoding="utf-8") as f:
                json.dump(summary_payload, f, indent=2)
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)

    def format_dashboard(self, hours: int = 24) -> str:
        """Format metrics as dashboard display."""
        summary = self.get_summary(hours)

        lines = []
        lines.append("📊 Token Metrics Dashboard")
        lines.append("=" * 50)
        lines.append(f"Period: Last {summary['period_hours']} hours")
        lines.append(f"Metrics recorded: {summary['metrics_count']}")
        lines.append("")

        lines.append("📈 Token Usage")
        lines.append(f"  Original tokens: {summary['total_original_tokens']:,}")
        lines.append(f"  SNS-Core tokens: {summary['total_sns_tokens']:,}")
        lines.append(f"  Tokens saved: {summary['total_savings_tokens']:,}")
        lines.append("")

        lines.append("💰 Savings")
        lines.append(f"  Average reduction: {summary['avg_savings_pct']}%")
        lines.append(f"  Max reduction: {summary['max_savings_pct']}%")
        lines.append(f"  Min reduction: {summary['min_savings_pct']}%")
        lines.append(f"  Estimated cost savings: {summary['estimated_cost_savings']}")
        lines.append("")

        lines.append("🔧 Modes")
        lines.append(f"  Normal mode: {summary['conversion_modes']['normal']} conversions")
        lines.append(f"  Aggressive mode: {summary['conversion_modes']['aggressive']} conversions")
        lines.append("")

        lines.append("📋 Operations")
        for op, count in summary["by_operation"].items():
            lines.append(f"  {op}: {count}")

        return "\n".join(lines)

    def get_leaderboard(self, metric: str = "savings_pct", limit: int = 10) -> list[dict[str, Any]]:
        """Get leaderboard of top conversions."""
        metrics = []

        if not self.metrics_file.exists():
            return []

        try:
            with open(self.metrics_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        metrics.append(data)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except (json.JSONDecodeError, ValueError, OSError):
            return []

        # Sort by metric
        if metric == "savings_pct":
            metrics.sort(key=lambda x: x.get("savings_pct", 0), reverse=True)
        elif metric == "savings_tokens":
            metrics.sort(
                key=lambda x: (x.get("original_tokens", 0) - x.get("sns_tokens", 0)),
                reverse=True,
            )

        return metrics[:limit]


if __name__ == "__main__":
    # Test the dashboard
    dashboard = TokenMetricsDashboard()

    # Record some test metrics
    for i in range(5):
        dashboard.record_conversion(
            original_tokens=100 + (i * 10),
            sns_tokens=60 + (i * 5),
            operation=f"test_{i}",
            mode="normal" if i % 2 == 0 else "aggressive",
        )

    # Display dashboard
    logger.info(dashboard.format_dashboard(hours=24))
    logger.info("\n📊 Top Conversions:")
    for idx, metric in enumerate(dashboard.get_leaderboard(limit=5), 1):
        logger.info(f"  {idx}. {metric['operation']}: {metric['savings_pct']}% savings")

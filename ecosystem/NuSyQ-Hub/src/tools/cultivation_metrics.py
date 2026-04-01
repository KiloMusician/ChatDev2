#!/usr/bin/env python3
"""Cultivation Metrics Dashboard - Track and visualize autonomous development metrics.

This module aggregates cultivation data from quest logs, work queues, and session logs
to generate metrics and visualizations showing system evolution over time.

Metrics tracked:
- Intent events per iteration (emergence frequency)
- Work queue item completion rate
- Cycle time (seconds per iteration)
- System health trend (broken files over time)
- Task success/failure ratio
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CultivationMetrics:
    """Tracks and visualizes cultivation metrics."""

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize metrics tracker.

        Args:
            repo_root: Repository root (defaults to NuSyQ-Hub location)
        """
        self.repo_root = repo_root or Path(__file__).parent.parent.parent
        self.quest_log_path = self.repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        self.work_queue_path = self.repo_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        self.session_logs_dir = self.repo_root / "docs" / "Agent-Sessions"
        self.metrics_dir = self.repo_root / "docs" / "Metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        logger.info("📊 Cultivation Metrics initialized")

    async def build_dashboard(self) -> Path:
        """Build HTML dashboard with all metrics and visualizations.

        Returns:
            Path to generated dashboard HTML file
        """
        logger.info("📊 Building cultivation metrics dashboard...")

        try:
            # Collect all metrics
            metrics = {
                "generated_at": datetime.now().isoformat(),
                "quest_metrics": self._collect_quest_metrics(),
                "work_queue_metrics": self._collect_work_queue_metrics(),
                "session_metrics": self._collect_session_metrics(),
                "system_health": self._collect_system_health(),
                "recommendations": self._generate_recommendations(),
            }

            # Generate HTML dashboard
            dashboard_content = self._generate_dashboard_html(metrics)

            # Write dashboard
            dashboard_path = self.metrics_dir / "dashboard.html"
            with open(dashboard_path, "w", encoding="utf-8") as f:
                f.write(dashboard_content)

            logger.info(f"✅ Dashboard generated: {dashboard_path}")

            # Also save metrics as JSON
            metrics_path = (
                self.metrics_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)

            return dashboard_path

        except Exception as e:
            logger.error(f"❌ Dashboard generation failed: {e}")
            raise

    def _collect_quest_metrics(self) -> dict[str, Any]:
        """Collect metrics from quest log."""
        logger.info("📖 Collecting quest metrics...")

        try:
            if not self.quest_log_path.exists():
                return {"total_entries": 0, "intent_events": 0, "other_events": 0}

            intent_events = 0
            other_events = 0
            intent_types: dict[str, int] = {}

            with open(self.quest_log_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("task_type") == "cultivation_intent":
                            intent_events += 1
                            intent_type = entry.get("intent_type", "unknown")
                            intent_types[intent_type] = intent_types.get(intent_type, 0) + 1
                        else:
                            other_events += 1
                    except json.JSONDecodeError:
                        continue

            return {
                "total_entries": intent_events + other_events,
                "intent_events": intent_events,
                "other_events": other_events,
                "intent_types_breakdown": intent_types,
            }
        except Exception as e:
            logger.error(f"Failed to collect quest metrics: {e}")
            return {"error": str(e)}

    def _collect_work_queue_metrics(self) -> dict[str, Any]:
        """Collect metrics from work queue."""
        logger.info("📋 Collecting work queue metrics...")

        try:
            if not self.work_queue_path.exists():
                return {"total_items": 0, "queued": 0, "completed": 0, "failed": 0}

            with open(self.work_queue_path, encoding="utf-8") as f:
                queue_data = json.load(f)

            items = queue_data.get("items", [])

            queued = len([i for i in items if i.get("status") == "queued"])
            completed = len([i for i in items if i.get("status") == "completed"])
            failed = len([i for i in items if i.get("status") == "failed"])
            in_progress = len([i for i in items if i.get("status") == "in_progress"])

            completion_rate = completed / len(items) if items else 0

            # Count by priority
            priority_counts: dict[str, int] = {}
            for item in items:
                priority = item.get("priority", "normal")
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            return {
                "total_items": len(items),
                "queued": queued,
                "in_progress": in_progress,
                "completed": completed,
                "failed": failed,
                "completion_rate": round(completion_rate * 100, 1),
                "priority_breakdown": priority_counts,
                "created_at": queue_data.get("created", "N/A"),
                "last_updated": queue_data.get("last_updated", "N/A"),
            }
        except Exception as e:
            logger.error(f"Failed to collect work queue metrics: {e}")
            return {"error": str(e)}

    def _collect_session_metrics(self) -> dict[str, Any]:
        """Collect metrics from session logs."""
        logger.info("📝 Collecting session metrics...")

        try:
            if not self.session_logs_dir.exists():
                return {"total_sessions": 0, "total_intent_events_captured": 0}

            session_files = list(self.session_logs_dir.glob("CULTIVATION_SESSION_*.md"))

            total_intent_events = 0
            total_items_promoted = 0

            for session_file in session_files:
                try:
                    content = session_file.read_text()
                    # Parse intent count from summary line
                    if "captured" in content:
                        import re

                        match = re.search(r"captured \*\*(\d+)\*\* intent", content)
                        if match:
                            total_intent_events += int(match.group(1))

                        match = re.search(r"promoted \*\*(\d+)\*\* work", content)
                        if match:
                            total_items_promoted += int(match.group(1))
                except Exception:
                    continue

            return {
                "total_sessions": len(session_files),
                "total_intent_events_captured": total_intent_events,
                "total_items_promoted": total_items_promoted,
                "avg_events_per_session": (
                    round(total_intent_events / len(session_files), 1) if session_files else 0
                ),
            }
        except Exception as e:
            logger.error(f"Failed to collect session metrics: {e}")
            return {"error": str(e)}

    def _collect_system_health(self) -> dict[str, Any]:
        """Collect system health trend data."""
        logger.info("🏥 Collecting system health metrics...")

        try:
            # Look for latest develop_system logs
            reports_dir = self.repo_root / "state" / "reports"
            if not reports_dir.exists():
                return {"status": "unknown"}

            latest_log = None
            latest_mtime = 0.0

            for log_file in reports_dir.glob("develop_system_*.json"):
                if log_file.stat().st_mtime > latest_mtime:
                    latest_mtime = log_file.stat().st_mtime
                    latest_log = log_file

            if not latest_log:
                return {"status": "no_data"}

            with open(latest_log, encoding="utf-8") as f:
                log_data = json.load(f)

            iterations = log_data.get("iterations", [])

            # Extract health trend
            health_trend = []
            for iteration in iterations:
                broken = iteration.get("before_analysis", {}).get("broken_files", 0)
                working = iteration.get("before_analysis", {}).get("working_files", 0)
                health_trend.append(
                    {
                        "iteration": iteration.get("iteration", 0),
                        "broken_files": broken,
                        "working_files": working,
                        "health_score": (
                            round(working / (working + broken) * 100, 1)
                            if (working + broken) > 0
                            else 0
                        ),
                    }
                )

            return {
                "latest_broken_files": (
                    health_trend[-1].get("broken_files", 0) if health_trend else "N/A"
                ),
                "latest_working_files": (
                    health_trend[-1].get("working_files", 0) if health_trend else "N/A"
                ),
                "latest_health_score": (
                    health_trend[-1].get("health_score", 0) if health_trend else 0
                ),
                "trend": (
                    health_trend[-10:] if len(health_trend) > 10 else health_trend
                ),  # Last 10
            }
        except Exception as e:
            logger.error(f"Failed to collect health metrics: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on collected metrics."""
        recommendations = []

        try:
            queue_metrics = self._collect_work_queue_metrics()
            session_metrics = self._collect_session_metrics()
            health_metrics = self._collect_system_health()

            # Check work queue status
            if queue_metrics.get("queued", 0) > 5:
                recommendations.append(
                    "⚙️ Work queue has many pending items - consider batch execution"
                )

            if queue_metrics.get("completion_rate", 0) < 50:
                recommendations.append(
                    "⚠️ Work queue completion rate below 50% - review failed items"
                )

            if queue_metrics.get("failed", 0) > 0:
                recommendations.append("❌ Some work items failed - investigate errors")

            # Check session metrics
            if session_metrics.get("total_sessions", 0) > 10:
                recommendations.append("📈 Good session history - consider running replay analysis")

            # Check health
            if health_metrics.get("latest_broken_files", 0) > 0:
                recommendations.append("🏥 Broken files detected - run heal action")

            if not recommendations:
                recommendations.append("✅ System is healthy - continue autonomous development")

        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {e}")

        return recommendations

    def _generate_dashboard_html(self, metrics: dict[str, Any]) -> str:
        """Generate HTML dashboard from metrics.

        Args:
            metrics: Aggregated metrics dictionary

        Returns:
            HTML string ready to write to file
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌱 NuSyQ Cultivation Metrics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.1em;
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #764ba2;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .metric-breakdown {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }}
        .breakdown-item {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 0.9em;
        }}
        .breakdown-label {{
            color: #666;
        }}
        .breakdown-value {{
            font-weight: bold;
            color: #333;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            position: relative;
            height: 400px;
        }}
        .recommendations {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .recommendations h3 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        .recommendation-item {{
            padding: 10px;
            margin: 8px 0;
            background: #f5f5f5;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 10px;
        }}
        .status-success {{ background: #d4edda; color: #155724; }}
        .status-warning {{ background: #fff3cd; color: #856404; }}
        .status-danger {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌱 Cultivation Metrics Dashboard</h1>
            <p class="timestamp">Generated: {metrics.get("generated_at", "Unknown")}</p>
        </div>

        <div class="metrics-grid">
            <!-- Quest Metrics -->
            <div class="metric-card">
                <h3>📖 Quest Log</h3>
                <div class="metric-value">{metrics.get("quest_metrics", {}).get("intent_events", 0)}</div>
                <div class="metric-label">Intent Events Captured</div>
                <div class="metric-breakdown">
                    <div class="breakdown-item">
                        <span class="breakdown-label">Total Entries:</span>
                        <span class="breakdown-value">{metrics.get("quest_metrics", {}).get("total_entries", 0)}</span>
                    </div>
                </div>
            </div>

            <!-- Work Queue Metrics -->
            <div class="metric-card">
                <h3>📋 Work Queue</h3>
                <div class="metric-value">{metrics.get("work_queue_metrics", {}).get("completed", 0)}</div>
                <div class="metric-label">Items Completed</div>
                <div class="metric-breakdown">
                    <div class="breakdown-item">
                        <span class="breakdown-label">Queued:</span>
                        <span class="breakdown-value">{metrics.get("work_queue_metrics", {}).get("queued", 0)}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">In Progress:</span>
                        <span class="breakdown-value">{metrics.get("work_queue_metrics", {}).get("in_progress", 0)}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">Failed:</span>
                        <span class="breakdown-value">{metrics.get("work_queue_metrics", {}).get("failed", 0)}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">Completion Rate:</span>
                        <span class="breakdown-value">{metrics.get("work_queue_metrics", {}).get("completion_rate", 0)}%</span>
                    </div>
                </div>
            </div>

            <!-- Session Metrics -->
            <div class="metric-card">
                <h3>📝 Sessions</h3>
                <div class="metric-value">{metrics.get("session_metrics", {}).get("total_sessions", 0)}</div>
                <div class="metric-label">Cultivation Sessions</div>
                <div class="metric-breakdown">
                    <div class="breakdown-item">
                        <span class="breakdown-label">Items Promoted:</span>
                        <span class="breakdown-value">{metrics.get("session_metrics", {}).get("total_items_promoted", 0)}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">Avg Events/Session:</span>
                        <span class="breakdown-value">{metrics.get("session_metrics", {}).get("avg_events_per_session", 0)}</span>
                    </div>
                </div>
            </div>

            <!-- System Health -->
            <div class="metric-card">
                <h3>🏥 System Health</h3>
                <div class="metric-value">{metrics.get("system_health", {}).get("latest_health_score", 0)}%</div>
                <div class="metric-label">Health Score</div>
                <div class="metric-breakdown">
                    <div class="breakdown-item">
                        <span class="breakdown-label">Broken Files:</span>
                        <span class="breakdown-value">{metrics.get("system_health", {}).get("latest_broken_files", 0)}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">Working Files:</span>
                        <span class="breakdown-value">{metrics.get("system_health", {}).get("latest_working_files", 0)}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="recommendations">
            <h3>💡 Recommendations</h3>
            {"".join([f'<div class="recommendation-item">{rec}</div>' for rec in metrics.get("recommendations", [])])}
        </div>

        <div style="text-align: center; color: white; margin-top: 30px; font-size: 0.9em;">
            <p>Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC</p>
            <p>NuSyQ-Hub Cultivation System</p>
        </div>
    </div>
</body>
</html>"""

        return html


if __name__ == "__main__":

    async def main():
        metrics = CultivationMetrics()
        dashboard_path = await metrics.build_dashboard()
        logger.info(f"Dashboard created: {dashboard_path}")

    asyncio.run(main())

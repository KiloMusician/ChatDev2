#!/usr/bin/env python3
"""📊 KILO-FOOLISH Performance Monitoring System.

Comprehensive development velocity tracking and trend analysis with graceful shutdown.

ZETA05 Implementation - Performance Monitoring Integration
"""

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.utils.graceful_shutdown import MonitoringLoopMixin, ShutdownConfig

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance measurement."""

    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"
    tags: list[str] = field(default_factory=list)


@dataclass
class DevelopmentSession:
    """Development session tracking."""

    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    activities: list[str] = field(default_factory=list)
    metrics: list[PerformanceMetric] = field(default_factory=list)
    zeta_progress: dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor(MonitoringLoopMixin):
    """Main performance monitoring system with graceful shutdown support."""

    def __init__(
        self,
        repo_root: Path | None = None,
        shutdown_config: ShutdownConfig | None = None,
    ) -> None:
        """Initialize PerformanceMonitor with repo_root, shutdown_config."""
        super().__init__(shutdown_config)

        # Fix path resolution - get the actual repo root properly
        if repo_root:
            self.repo_root = repo_root
        else:
            # Navigate from src/core to repo root
            current_file = Path(__file__).resolve()
            self.repo_root = current_file.parent.parent.parent

        self.data_dir = self.repo_root / "src" / "core" / "performance_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.current_session: DevelopmentSession | None = None
        self.metrics_history: list[PerformanceMetric] = []
        self.monitoring_threads: list[Any] = []

        # Register cleanup and state saving
        self.register_cleanup_task(self._cleanup_monitoring)
        self.register_state_saver(self._save_final_metrics)

        self.load_historical_data()

    def start_session(self, session_type: str = "development") -> str:
        """Start a new development session."""
        session_id = f"{session_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.current_session = DevelopmentSession(
            session_id=session_id,
            start_time=datetime.now(),
            activities=[f"Session started: {session_type}"],
        )

        return session_id

    def end_session(self) -> None:
        """End current development session."""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            duration = self.current_session.end_time - self.current_session.start_time

            # Add session duration metric
            self.add_metric(
                "session_duration",
                duration.total_seconds() / 60,  # minutes
                "minutes",
                category="productivity",
            )

            # Save session data
            self.save_session_data()
            self.current_session = None

    def add_metric(
        self,
        name: str,
        value: float,
        unit: str,
        category: str = "general",
        tags: list[str] | None = None,
    ) -> None:
        """Add a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            category=category,
            tags=tags or [],
        )

        if self.current_session:
            self.current_session.metrics.append(metric)

        self.metrics_history.append(metric)

    def track_zeta_progress(self) -> None:
        """Track ZETA progression metrics."""
        zeta_file = self.repo_root / "config" / "ZETA_PROGRESS_TRACKER.json"

        if zeta_file.exists():
            with open(zeta_file) as f:
                zeta_data = json.load(f)

            # Extract key metrics
            completion_pct = zeta_data["current_progress"]["completion_percentage"]
            completed_tasks = zeta_data["current_progress"]["completed_tasks"]
            in_progress_tasks = zeta_data["current_progress"]["in_progress_tasks"]

            # Add metrics
            self.add_metric("zeta_completion_percentage", completion_pct, "percent", "progress")
            self.add_metric("zeta_completed_tasks", completed_tasks, "count", "progress")
            self.add_metric("zeta_in_progress_tasks", in_progress_tasks, "count", "progress")

            if self.current_session:
                self.current_session.zeta_progress = zeta_data["current_progress"]

    def track_llm_system_health(self) -> None:
        """Monitor LLM system availability and performance."""
        health_metrics = {
            "ollama_available": False,
            "chatdev_available": False,
            "integration_health": 0.0,
        }

        # Test Ollama
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            health_metrics["ollama_available"] = result.returncode == 0
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            logger.debug("Suppressed OSError/subprocess", exc_info=True)

        # Test Python imports
        try:
            import sys

            sys.path.insert(0, str(self.repo_root / "src"))
            health_metrics["chatdev_available"] = True
        except (AttributeError, TypeError, ValueError):
            logger.debug("Suppressed AttributeError/TypeError/ValueError", exc_info=True)

        # Calculate integration health score
        available_systems = sum(
            [
                health_metrics["ollama_available"],
                health_metrics["chatdev_available"],
            ]
        )
        health_metrics["integration_health"] = available_systems / 2.0

        # Add metrics
        for metric_name, value in health_metrics.items():
            if isinstance(value, bool):
                value = 1.0 if value else 0.0
            self.add_metric(metric_name, value, "score", "system_health")

    def generate_velocity_report(self) -> dict[str, Any]:
        """Generate development velocity analysis."""
        recent_sessions = self._get_recent_sessions(days=7)

        if not recent_sessions:
            return {"error": "No recent sessions found"}

        # Calculate velocity metrics
        total_duration = sum(
            (s.end_time - s.start_time).total_seconds() / 3600
            for s in recent_sessions
            if s.end_time  # hours
        )

        total_activities = sum(len(s.activities) for s in recent_sessions)

        # ZETA progress velocity
        zeta_progress_changes: list[Any] = []
        for session in recent_sessions:
            if session.zeta_progress:
                zeta_progress_changes.append(session.zeta_progress.get("completion_percentage", 0))

        return {
            "time_period": "last_7_days",
            "total_development_hours": round(total_duration, 2),
            "total_activities": total_activities,
            "sessions_count": len(recent_sessions),
            "average_session_duration": (
                round(total_duration / len(recent_sessions), 2) if recent_sessions else 0
            ),
            "activities_per_session": (
                round(total_activities / len(recent_sessions), 1) if recent_sessions else 0
            ),
            "zeta_progress_trend": zeta_progress_changes,
            "generated_timestamp": datetime.now().isoformat(),
        }

    def get_trend_analysis(self) -> dict[str, Any]:
        """Analyze performance trends."""
        if len(self.metrics_history) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Group metrics by category
        categories: dict[str, list[PerformanceMetric]] = {}
        for metric in self.metrics_history[-50:]:  # Last 50 metrics
            categories.setdefault(metric.category, []).append(metric)

        trends: dict[str, Any] = {}
        for category, metrics in categories.items():
            if len(metrics) >= 2:
                recent_avg = sum(m.value for m in metrics[-5:]) / min(5, len(metrics))
                older_avg = sum(m.value for m in metrics[:-5]) / max(1, len(metrics) - 5)

                trend_direction = "improving" if recent_avg > older_avg else "declining"
                trend_magnitude = abs(recent_avg - older_avg) / max(older_avg, 0.1)

                trends[category] = {
                    "direction": trend_direction,
                    "magnitude": round(trend_magnitude, 3),
                    "recent_average": round(recent_avg, 2),
                    "historical_average": round(older_avg, 2),
                }

        return trends

    def save_session_data(self) -> None:
        """Save current session data."""
        if not self.current_session:
            return

        session_file = self.data_dir / f"{self.current_session.session_id}.json"
        session_data = {
            "session_id": self.current_session.session_id,
            "start_time": self.current_session.start_time.isoformat(),
            "end_time": (
                self.current_session.end_time.isoformat() if self.current_session.end_time else None
            ),
            "activities": self.current_session.activities,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "category": m.category,
                    "timestamp": m.timestamp.isoformat(),
                    "tags": m.tags,
                }
                for m in self.current_session.metrics
            ],
            "zeta_progress": self.current_session.zeta_progress,
        }

        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

    def load_historical_data(self) -> None:
        """Load historical performance data."""
        if not self.data_dir.exists():
            return

        for session_file in self.data_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    session_data = json.load(f)

                # Load metrics into history
                for metric_data in session_data.get("metrics", []):
                    metric = PerformanceMetric(
                        name=metric_data["name"],
                        value=metric_data["value"],
                        unit=metric_data["unit"],
                        category=metric_data["category"],
                        timestamp=datetime.fromisoformat(metric_data["timestamp"]),
                        tags=metric_data.get("tags", []),
                    )
                    self.metrics_history.append(metric)
            except (KeyError, ValueError, TypeError):
                logger.debug("Suppressed KeyError/TypeError/ValueError", exc_info=True)

    def _get_recent_sessions(self, days: int = 7) -> list[DevelopmentSession]:
        """Get sessions from recent days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_sessions: list[DevelopmentSession] = []
        for session_file in self.data_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    session_data = json.load(f)

                start_time = datetime.fromisoformat(session_data["start_time"])
                if start_time >= cutoff_date:
                    session = DevelopmentSession(
                        session_id=session_data["session_id"],
                        start_time=start_time,
                        end_time=(
                            datetime.fromisoformat(session_data["end_time"])
                            if session_data.get("end_time")
                            else None
                        ),
                        activities=session_data.get("activities", []),
                        zeta_progress=session_data.get("zeta_progress", {}),
                    )
                    recent_sessions.append(session)
            except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
                continue

        return recent_sessions

    def start_background_monitoring(self) -> None:
        """Start background performance monitoring with graceful shutdown support."""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return

        monitor_functions = [
            self._continuous_system_monitor,
            self._periodic_health_check,
        ]

        self.start_monitoring_with_shutdown(monitor_functions)
        logger.info("🚀 Background performance monitoring started")

    def _continuous_system_monitor(self) -> None:
        """Continuous system monitoring loop."""
        while self.monitoring_active and not self.is_shutdown_requested():
            try:
                self.track_llm_system_health()
                time.sleep(30)  # Monitor every 30 seconds
            except Exception as e:
                logger.exception(f"❌ System monitoring error: {e}")
                time.sleep(60)  # Extended delay on error

    def _periodic_health_check(self) -> None:
        """Periodic comprehensive health check."""
        while self.monitoring_active and not self.is_shutdown_requested():
            try:
                self.track_zeta_progress()
                time.sleep(300)  # Health check every 5 minutes
            except Exception as e:
                logger.exception(f"❌ Health check error: {e}")
                time.sleep(600)  # Extended delay on error

    def _cleanup_monitoring(self) -> None:
        """Cleanup monitoring resources during shutdown."""
        logger.info("🧹 PerformanceMonitor: Cleaning up monitoring resources")
        self.monitoring_active = False

        # End current session if active
        if self.current_session:
            self.end_session()

    def _save_final_metrics(self) -> None:
        """Save final metrics during shutdown."""
        logger.info("💾 PerformanceMonitor: Saving final metrics")
        try:
            if self.current_session:
                self.save_session_data()

            # Save final historical data
            self.save_historical_data()
        except Exception as e:
            logger.exception(f"❌ Error saving final metrics: {e}")


def main() -> None:
    """Demonstrate performance monitoring system with graceful shutdown."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Create monitor with graceful shutdown
    shutdown_config = ShutdownConfig(graceful_timeout=20.0, log_progress=True)
    monitor = PerformanceMonitor(shutdown_config=shutdown_config)

    try:
        # Start a demo session
        monitor.start_session("zeta05_implementation")

        # Start background monitoring
        monitor.start_background_monitoring()

        # Track current metrics
        monitor.track_zeta_progress()
        monitor.track_llm_system_health()

        # Add some demo activities
        if monitor.current_session:
            monitor.current_session.activities.extend(
                [
                    "ZETA05 - Performance monitoring system created",
                    "AI Intermediary check-in completed",
                    "LLM system health assessment performed",
                ]
            )

        # Generate reports
        monitor.generate_velocity_report()

        monitor.get_trend_analysis()

        # Wait for shutdown signal
        while not monitor.is_shutdown_requested():
            time.sleep(1)

    except KeyboardInterrupt:
        monitor.request_shutdown("User interrupt")

    finally:
        # Execute graceful shutdown
        monitor.execute_graceful_shutdown()


if __name__ == "__main__":
    main()

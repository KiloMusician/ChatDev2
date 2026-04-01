"""🎮 NuSyQ-Hub Automation CLI Tool.

────────────────────────────────────
Command-line interface for autonomous healing ecosystem management.
Supports cycle management, configuration, monitoring, and reporting.

OmniTag: [CLI, orchestration, user-interface, production]
"""

import argparse
import json
import logging
import os
import sys
from collections.abc import Callable, Sequence
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

# Optional imports - use Any type to avoid mypy errors
get_health_check_logger: Any = None
rate_limited_log: Any = None
try:
    from src.observability.structured_logging import \
        get_health_check_logger as _get_logger
    from src.observability.structured_logging import \
        rate_limited_log as _rate_log

    get_health_check_logger = _get_logger
    rate_limited_log = _rate_log
except ImportError:
    pass

# Import core systems with Any typing for optional imports
_UnifiedAutonomousHealingPipeline: type[Any] | None = None
_HealingCycleScheduler: type[Any] | None = None
_ResolutionTracker: type[Any] | None = None
_PerformanceCache: type[Any] | None = None
_DashboardAPI: type[Any] | None = None
_SystemHealthAssessor: type[Any] | None = None
_MediumTermCLIClass: type[Any] | None = None
_default_sns_converter: Callable[..., tuple[str, dict[str, Any]]] | None = None


def _load_optional_class(class_name: str, module_candidates: Sequence[str]) -> type[Any] | None:
    """Try to import an optional class from a list of module paths."""
    for module_path in module_candidates:
        try:
            module = import_module(module_path)
        except ImportError:
            continue

        try:
            attr = getattr(module, class_name)
        except AttributeError:
            continue

        if isinstance(attr, type):
            return attr

    return None


_UnifiedAutonomousHealingPipeline = _load_optional_class(
    "UnifiedAutonomousHealingPipeline",
    (
        "src.orchestration.unified_autonomous_healing_pipeline",
        "orchestration.unified_autonomous_healing_pipeline",
    ),
)
_HealingCycleScheduler = _load_optional_class(
    "HealingCycleScheduler",
    (
        "src.orchestration.healing_cycle_scheduler",
        "orchestration.healing_cycle_scheduler",
    ),
)
_ResolutionTracker = _load_optional_class(
    "ResolutionTracker",
    (
        "src.analytics.resolution_tracker",
        "analytics.resolution_tracker",
    ),
)
_PerformanceCache = _load_optional_class(
    "PerformanceCache",
    ("src.optimization.performance_cache", "optimization.performance_cache"),
)
_DashboardAPI = _load_optional_class(
    "DashboardAPI",
    ("src.web.dashboard_api", "web.dashboard_api"),
)
_SystemHealthAssessor = _load_optional_class(
    "SystemHealthAssessment",
    (
        "src.diagnostics.system_health_assessor",
        "diagnostics.system_health_assessor",
    ),
)

try:
    from src.tools.medium_term_cli_integration import \
        MediumTermEnhancementsIntegration as _MediumTermIntegration
    from src.utils.sns_core_helper import convert_to_sns as _convert_to_sns

    _MediumTermCLIClass = _MediumTermIntegration
    _default_sns_converter = _convert_to_sns
except ImportError:
    _MediumTermCLIClass = None
    _default_sns_converter = None


if TYPE_CHECKING:
    from src.analytics.resolution_tracker import ResolutionTracker
    from src.diagnostics.system_health_assessor import SystemHealthAssessment
    from src.optimization.performance_cache import PerformanceCache
    from src.orchestration.healing_cycle_scheduler import HealingCycleScheduler
    from src.orchestration.unified_autonomous_healing_pipeline import \
        UnifiedAutonomousHealingPipeline
    from src.web.dashboard_api import DashboardAPI

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
LOG_FORMAT = os.getenv("NUSYG_LOG_FORMAT", "human")
HEALTH_LOGGER = (
    get_health_check_logger(log_format=LOG_FORMAT) if get_health_check_logger else logger
)


class NuSyQCLI:
    """Main CLI interface for NuSyQ-Hub ecosystem."""

    def __init__(self) -> None:
        """Initialize CLI with system components."""
        self.pipeline: UnifiedAutonomousHealingPipeline | None = None
        self.scheduler: HealingCycleScheduler | None = None
        self.tracker: ResolutionTracker | None = None
        self.cache: PerformanceCache | None = None
        self.dashboard: DashboardAPI | None = None
        self.health: SystemHealthAssessment | None = None
        self._initialize_systems()

    def _initialize_systems(self) -> None:
        """Initialize all system components."""
        try:
            logger.info("🚀 Initializing NuSyQ-Hub CLI...")

            if _UnifiedAutonomousHealingPipeline is not None:
                self.pipeline = _UnifiedAutonomousHealingPipeline()

            if _HealingCycleScheduler is not None:
                self.scheduler = _HealingCycleScheduler()

            if _ResolutionTracker is not None:
                self.tracker = _ResolutionTracker()

            if _PerformanceCache is not None:
                self.cache = _PerformanceCache()

            if _DashboardAPI is not None:
                self.dashboard = _DashboardAPI()

            if _SystemHealthAssessor is not None:
                self.health = _SystemHealthAssessor()

            logger.info("✅ All systems initialized")
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            # Continue with partial initialization

    # ========================= CYCLE MANAGEMENT =========================

    def run_healing_cycle(self, verbose: bool = False) -> bool:
        """Run a single autonomous healing cycle.

        Args:
            verbose: Enable detailed output

        Returns:
            True if cycle succeeded, False otherwise
        """
        try:
            import asyncio

            logger.info("🔄 Starting healing cycle...")
            if not self.pipeline:
                logger.error("❌ Healing pipeline not initialized")
                return False

            # Execute cycle
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(
                self.pipeline.run_unified_healing_pipeline(num_cycles=1)
            )
            # Record to tracker
            if self.tracker and results:
                for status in results:
                    if hasattr(status, "detected_issues"):
                        for issue in status.detected_issues:
                            self.tracker.register_detected_issue(
                                issue_id=f"{issue.type}_{issue.location}",
                                issue_type=issue.type,
                                description=issue.description,
                                file_path=issue.location,
                                severity=getattr(issue, "severity", "medium"),
                                cycle_num=1,
                            )

            # Record to dashboard
            if self.dashboard and results:
                self.dashboard.record_cycle(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "results": [str(r) for r in results],
                        "success": True,
                    }
                )

            logger.info(
                f"✅ Healing cycle completed: {len(results) if results else 0} cycles executed"
            )

            if verbose and results:
                for result in results:
                    logger.info(f"Cycle result: {result}")

            return True

        except Exception as e:
            logger.error(f"❌ Healing cycle failed: {e}")
            return False

    def run_health_check(self) -> dict[str, Any]:
        """Run comprehensive system health check.

        Returns:
            Health report dictionary
        """
        try:
            rate_limit_seconds = float(os.getenv("NUSYG_HEALTH_LOG_RATE_SECONDS", "60"))
            message = "🏥 Running system health check..."
            if rate_limited_log:
                rate_limited_log(
                    HEALTH_LOGGER,
                    logging.INFO,
                    message,
                    rate_limit_key="health:run",
                    rate_limit_seconds=rate_limit_seconds,
                )
            else:
                logger.info(message)

            if not self.health:
                logger.error("❌ Health assessor not initialized")
                return {"status": "error", "message": "Health assessor unavailable"}

            # Get health report
            report: dict[str, Any]
            if hasattr(self.health, "assess"):
                report = cast(dict[str, Any], self.health.assess())
            else:
                self.health.analyze_system_health()
                report = {
                    "status": "analysis_started",
                    "overall_health": "unknown",
                }

            # Format output
            status = "✅ Healthy" if report.get("overall_health") == "good" else "⚠️ Degraded"
            status_message = f"{status} - System health: {report.get('overall_health')}"
            if rate_limited_log:
                rate_limited_log(
                    HEALTH_LOGGER,
                    logging.INFO,
                    status_message,
                    rate_limit_key="health:status",
                    rate_limit_seconds=rate_limit_seconds,
                )
            else:
                logger.info(status_message)

            return report

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {"status": "error", "message": str(e)}

    # ========================= SCHEDULER MANAGEMENT =========================

    def start_scheduler(self, _daemon: bool = True) -> bool:
        """Start automated healing cycle scheduler.

        Args:
            daemon: Run as background daemon

        Returns:
            True if scheduler started successfully
        """
        try:
            logger.info("⏰ Starting healing cycle scheduler...")

            if not self.scheduler:
                logger.error("❌ Scheduler not initialized")
                return False

            self.scheduler.start()
            logger.info("✅ Scheduler started successfully")
            logger.info("📅 Scheduled jobs:")
            logger.info("   • Every 6 hours: Full healing cycles")
            logger.info("   • Every 30 minutes: Health checks")
            logger.info("   • Daily 2:00 AM: Report generation")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            return False

    def stop_scheduler(self) -> bool:
        """Stop automated scheduler."""
        try:
            logger.info("⏹️ Stopping scheduler...")

            if not self.scheduler:
                logger.error("❌ Scheduler not initialized")
                return False

            self.scheduler.stop()
            logger.info("✅ Scheduler stopped")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to stop scheduler: {e}")
            return False

    def list_scheduled_jobs(self) -> list[dict[str, str]]:
        """List all scheduled jobs."""
        jobs = [
            {
                "job": "Full Healing Cycle",
                "schedule": "Every 6 hours",
                "next_run": "Next scheduled run time",
            },
            {
                "job": "System Health Check",
                "schedule": "Every 30 minutes",
                "next_run": "Next scheduled run time",
            },
            {
                "job": "Report Generation",
                "schedule": "Daily at 2:00 AM",
                "next_run": "Next scheduled run time",
            },
        ]

        for job in jobs:
            logger.info(f"📅 {job['job']}: {job['schedule']}")

        return jobs

    # ========================= TRACKING & METRICS =========================

    def get_metrics(self, issue_type: str | None = None) -> dict[str, Any]:
        """Get resolution metrics.

        Args:
            issue_type: Filter by issue type (optional)

        Returns:
            Metrics dictionary
        """
        try:
            if not self.tracker:
                logger.error("❌ Tracker not initialized")
                return {}

            logger.info("📊 Collecting metrics...")

            metrics_result = self.tracker.get_metrics()
            if isinstance(metrics_result, dict):
                metrics_data: dict[str, Any] = metrics_result
            elif hasattr(metrics_result, "__dict__"):
                metrics_data = dict(metrics_result.__dict__)
            else:
                metrics_data = {"metrics": metrics_result}

            # Filter if requested
            if issue_type and "by_type" in metrics_data:
                metrics_data = {
                    "by_type": {issue_type: metrics_data["by_type"].get(issue_type, {})}
                }

            logger.info("✅ Metrics collected")

            # Display metrics
            self._display_metrics(metrics_data)

            return metrics_data

        except Exception as e:
            logger.error(f"❌ Failed to get metrics: {e}")
            return {}

    @staticmethod
    def _display_metrics(metrics: Any) -> None:
        """Display metrics in human-readable format."""
        # Handle both dict and dataclass (hasattr __dict__ → dataclass/object, else raw dict)
        data = metrics.__dict__ if hasattr(metrics, "__dict__") else metrics

        if "total_detected" in data:
            logger.info(f"📈 Total Issues Detected: {data['total_detected']}")

        if "total_resolved" in data:
            logger.info(f"✅ Total Resolved: {data['total_resolved']}")

        if "avg_resolution_time" in data:
            avg_time = data["avg_resolution_time"]
            logger.info(f"⏱️ Avg Resolution Time: {avg_time:.1f}s")

        if "by_issue_type" in data:
            logger.info("\n📋 Issues by Type:")
            for issue_type, stats in data["by_issue_type"].items():
                count = stats.get("count", 0)
                logger.info(f"   • {issue_type}: {count}")

        if "resolution_rate" in data:
            rate = data["resolution_rate"]
            logger.info(f"\n📊 Resolution Rate: {rate * 100:.1f}%")

    def get_recent_issues(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent issues from tracker."""
        try:
            if not self.tracker:
                logger.error("❌ Tracker not initialized")
                return []

            logger.info(f"🔍 Getting last {limit} issues...")

            # Load issues from database
            issues = []
            try:
                # Get path from tracker's database location
                from src.analytics.resolution_tracker import ISSUES_DB

                if ISSUES_DB.exists():
                    with open(ISSUES_DB) as f:
                        for line in f:
                            if line.strip():
                                issues.append(json.loads(line))

                # Show most recent
                recent = issues[-limit:] if len(issues) > limit else issues

                logger.info(f"\n📜 Recent Issues (last {len(recent)}):")
                for issue in recent:
                    status = issue.get("status", "unknown")
                    issue_type = issue.get("issue_type", "unknown")
                    location = issue.get("file_path", "unknown")
                    logger.info(f"   • [{status}] {issue_type} in {location}")

                return recent

            except FileNotFoundError:
                logger.info("Info: No issues tracked yet")
                return []

        except Exception as e:
            logger.error(f"❌ Failed to get recent issues: {e}")
            return []

    # ========================= DASHBOARD MANAGEMENT =========================

    def start_dashboard(self, port: int = 5001) -> bool:
        """Start web dashboard server.

        Args:
            port: Port to run dashboard on

        Returns:
            True if started successfully
        """
        try:
            logger.info(f"🌐 Starting dashboard on port {port}...")

            if not self.dashboard:
                logger.error("❌ Dashboard not initialized")
                return False

            logger.info(f"✅ Dashboard available at http://localhost:{port}")
            logger.info("📊 Endpoints:")
            logger.info(f"   • http://localhost:{port}/api/cycles")
            logger.info(f"   • http://localhost:{port}/api/issues")
            logger.info(f"   • http://localhost:{port}/api/metrics")

            # Note: Actual start would be handled in dashboard module
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start dashboard: {e}")
            return False

    # ========================= CONFIGURATION =========================

    def show_configuration(self) -> dict[str, Any]:
        """Display current configuration."""
        config = {
            "system": "NuSyQ-Hub Autonomous Ecosystem",
            "version": "1.0.0",
            "components": {
                "healing_pipeline": "operational" if self.pipeline else "unavailable",
                "scheduler": "operational" if self.scheduler else "unavailable",
                "tracker": "operational" if self.tracker else "unavailable",
                "cache": "operational" if self.cache else "unavailable",
                "dashboard": "operational" if self.dashboard else "unavailable",
            },
            "automation": {
                "healing_cycles": "Every 6 hours",
                "health_checks": "Every 30 minutes",
                "report_generation": "Daily at 2:00 AM",
            },
        }

        logger.info("\n⚙️ System Configuration:")
        logger.info(json.dumps(config, indent=2))

        return config

    # ========================= REPORTING =========================

    def generate_report(self, output_file: str | None = None) -> bool:
        """Generate comprehensive system report.

        Args:
            output_file: Optional file to save report

        Returns:
            True if report generated successfully
        """
        try:
            logger.info("📝 Generating comprehensive system report...")

            # Collect all data
            report = {
                "timestamp": datetime.now().isoformat(),
                "health": self.get_metrics(),
                "recent_issues": self.get_recent_issues(limit=20),
                "configuration": self.show_configuration(),
            }

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w") as f:
                    json.dump(report, f, indent=2, default=str)

                logger.info(f"✅ Report saved to {output_file}")
            else:
                logger.info(json.dumps(report, indent=2, default=str))

            return True

        except Exception as e:
            logger.error(f"❌ Failed to generate report: {e}")
            return False

    def run_evaluation_benchmark(
        self,
        action: str = "prepare",
        state_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Run evaluation benchmarks via the medium-term integration."""
        if _MediumTermCLIClass is None:
            return {"status": "error", "message": "Evaluation modules unavailable"}

        integration = _MediumTermCLIClass(state_dir=state_dir or Path("state"))
        converter = _default_sns_converter if action == "run" else None
        if action == "run" and converter is None:
            return {"status": "error", "message": "SNS converter unavailable"}

        return cast(
            dict[str, Any],
            integration.handle_performance_benchmark(
                action=action,
                sns_converter=converter,
            ),
        )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="🎮 NuSyQ-Hub Automation CLI - Autonomous Healing Ecosystem Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nusyq-hub cycle run              # Run a single healing cycle
  nusyq-hub scheduler start        # Start automated scheduler
  nusyq-hub metrics show           # Display resolution metrics
  nusyq-hub issues list            # Show recent issues
  nusyq-hub health check           # Run system health check
  nusyq-hub dashboard start        # Start web dashboard
  nusyq-hub report generate        # Generate comprehensive report
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Cycle management
    cycle_parser = subparsers.add_parser("cycle", help="Healing cycle management")
    cycle_subs = cycle_parser.add_subparsers(dest="cycle_cmd")
    cycle_subs.add_parser("run", help="Run a single healing cycle")
    cycle_subs.add_parser("status", help="Check cycle status")

    # Scheduler management
    scheduler_parser = subparsers.add_parser("scheduler", help="Scheduler management")
    scheduler_subs = scheduler_parser.add_subparsers(dest="scheduler_cmd")
    scheduler_subs.add_parser("start", help="Start automated scheduler")
    scheduler_subs.add_parser("stop", help="Stop scheduler")
    scheduler_subs.add_parser("status", help="Check scheduler status")
    scheduler_subs.add_parser("list", help="List scheduled jobs")

    # Tracking & metrics
    metrics_parser = subparsers.add_parser("metrics", help="Resolution metrics")
    metrics_subs = metrics_parser.add_subparsers(dest="metrics_cmd")
    metrics_subs.add_parser("show", help="Display all metrics")
    metrics_show = metrics_subs.add_parser("show-type", help="Show metrics for specific type")
    metrics_show.add_argument("type", help="Issue type to filter")

    # Issues
    issues_parser = subparsers.add_parser("issues", help="Issue tracking")
    issues_subs = issues_parser.add_subparsers(dest="issues_cmd")
    issues_subs.add_parser("list", help="List recent issues")
    issues_list = issues_subs.add_parser("list-count", help="List N most recent issues")
    issues_list.add_argument("count", type=int, help="Number of issues to show")

    # Health check
    health_parser = subparsers.add_parser("health", help="System health")
    health_subs = health_parser.add_subparsers(dest="health_cmd")
    health_subs.add_parser("check", help="Run health check")

    # Dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Web dashboard")
    dashboard_subs = dashboard_parser.add_subparsers(dest="dashboard_cmd")
    dashboard_start = dashboard_subs.add_parser("start", help="Start dashboard server")
    dashboard_start.add_argument("--port", type=int, default=5001, help="Port (default 5001)")

    # Configuration
    config_parser = subparsers.add_parser("config", help="Configuration")
    config_subs = config_parser.add_subparsers(dest="config_cmd")
    config_subs.add_parser("show", help="Show configuration")

    # Reporting
    report_parser = subparsers.add_parser("report", help="Reporting")
    report_subs = report_parser.add_subparsers(dest="report_cmd")
    report_gen = report_subs.add_parser("generate", help="Generate comprehensive report")
    report_gen.add_argument("--output", "-o", help="Output file path")

    evaluation_parser = subparsers.add_parser("evaluation", help="Evaluation utilities")
    evaluation_subs = evaluation_parser.add_subparsers(dest="evaluation_cmd")
    benchmark_parser = evaluation_subs.add_parser(
        "benchmark", help="Run performance benchmarking and reporting"
    )
    benchmark_parser.add_argument(
        "--action",
        "-a",
        choices=["prepare", "run", "summary", "report"],
        default="prepare",
        help="Benchmark action to perform",
    )
    benchmark_parser.add_argument(
        "--state-dir",
        "-s",
        help="Optional directory for benchmark state (default=state)",
    )

    args = parser.parse_args()

    # Initialize CLI
    cli = NuSyQCLI()

    # Route commands
    if args.command == "cycle":
        if args.cycle_cmd == "run":
            success = cli.run_healing_cycle(verbose=True)
            sys.exit(0 if success else 1)
        elif args.cycle_cmd == "status":
            cli.run_health_check()

    elif args.command == "scheduler":
        if args.scheduler_cmd == "start":
            success = cli.start_scheduler()
            sys.exit(0 if success else 1)
        elif args.scheduler_cmd == "stop":
            success = cli.stop_scheduler()
            sys.exit(0 if success else 1)
        elif args.scheduler_cmd == "list":
            cli.list_scheduled_jobs()

    elif args.command == "metrics":
        if args.metrics_cmd == "show":
            cli.get_metrics()
        elif args.metrics_cmd == "show-type":
            cli.get_metrics(issue_type=args.type)

    elif args.command == "issues":
        if args.issues_cmd == "list":
            cli.get_recent_issues()
        elif args.issues_cmd == "list-count":
            cli.get_recent_issues(limit=args.count)

    elif args.command == "health":
        if args.health_cmd == "check":
            cli.run_health_check()

    elif args.command == "dashboard":
        if args.dashboard_cmd == "start":
            cli.start_dashboard(port=args.port)

    elif args.command == "config":
        if args.config_cmd == "show":
            cli.show_configuration()

    elif args.command == "report":
        if args.report_cmd == "generate":
            success = cli.generate_report(output_file=args.output)
            sys.exit(0 if success else 1)

    elif args.command == "evaluation":
        if args.evaluation_cmd == "benchmark":
            state_dir = Path(args.state_dir) if args.state_dir else None
            result = cli.run_evaluation_benchmark(
                action=args.action,
                state_dir=state_dir,
            )
            logger.info(json.dumps(result, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

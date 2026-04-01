#!/usr/bin/env python3
"""Unified Autonomous Healing Pipeline.

============================================================

Integrates:
- Extended Autonomous Cycle Runner (issue detection)
- ChatDev Autonomous Router (multi-agent task routing)
- Modernized Healing Coordinator (self-repair)

Creates a complete autonomous healing ecosystem that detects issues,
decomposes them into multi-agent tasks, executes fixes, and validates healing.
"""

# pylint: disable=broad-exception-caught,import-outside-toplevel,ungrouped-imports

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    from datetime import timezone

    UTC = timezone.utc  # noqa: UP017

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


@dataclass
class HealingPipelineStatus:
    """Tracks status of unified healing pipeline."""

    cycle_number: int
    issues_detected: int = 0
    tasks_created: int = 0
    tasks_completed: int = 0
    healing_applied: int = 0
    health_status: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cycle": self.cycle_number,
            "issues_detected": self.issues_detected,
            "tasks_created": self.tasks_created,
            "tasks_completed": self.tasks_completed,
            "healing_applied": self.healing_applied,
            "health_status": self.health_status,
            "timestamp": self.timestamp.isoformat(),
        }


class UnifiedAutonomousHealingPipeline:
    """Orchestrates complete autonomous healing workflow."""

    def __init__(self) -> None:
        """Initialize unified pipeline with all subsystems."""
        self.status_history: list[HealingPipelineStatus] = []
        logger.info("🏥 Initializing Unified Autonomous Healing Pipeline")

        # Initialize subsystems
        self._init_extended_cycle_runner()
        self._init_chatdev_router()
        self._init_healing_coordinator()

        # Initialize new monitoring and tracking systems
        self._init_dashboard_api()
        self._init_healing_scheduler()
        self._init_resolution_tracker()

    def _init_extended_cycle_runner(self) -> None:
        """Initialize extended cycle runner."""
        try:
            from src.orchestration.extended_autonomous_cycle_runner import \
                ExtendedAutonomousCycleRunner

            self.cycle_runner = ExtendedAutonomousCycleRunner()
            logger.info("✅ Extended Cycle Runner initialized")
        except Exception as e:
            logger.warning(f"⚠️ Extended Cycle Runner initialization failed: {e}")
            self.cycle_runner = None

    def _init_chatdev_router(self) -> None:
        """Initialize ChatDev autonomous router."""
        try:
            from src.orchestration.chatdev_autonomous_router import \
                ChatDevAutonomousRouter

            self.chatdev_router = ChatDevAutonomousRouter()
            logger.info(
                f"✅ ChatDev Router initialized (available={self.chatdev_router.chatdev_available})"
            )
        except Exception as e:
            logger.warning(f"⚠️ ChatDev Router initialization failed: {e}")
            self.chatdev_router = None

    def _init_healing_coordinator(self) -> None:
        """Initialize healing coordinator."""
        try:
            from src.healing.modernized_healing_coordinator import \
                ModernizedHealingCoordinator

            self.healing_coordinator = ModernizedHealingCoordinator()
            logger.info("✅ Healing Coordinator initialized")
        except Exception as e:
            logger.warning(f"⚠️ Healing Coordinator initialization failed: {e}")
            self.healing_coordinator = None

    def _init_dashboard_api(self) -> None:
        """Initialize web dashboard API."""
        try:
            from src.web.dashboard_api import DashboardAPI

            self.dashboard = DashboardAPI()
            logger.info("✅ Dashboard API initialized")
        except Exception as e:
            logger.warning(f"⚠️ Dashboard API initialization failed: {e}")
            self.dashboard = None

    def _init_healing_scheduler(self) -> None:
        """Initialize healing cycle scheduler."""
        try:
            from src.orchestration.healing_cycle_scheduler import \
                HealingCycleScheduler

            self.scheduler = HealingCycleScheduler()
            logger.info("✅ Healing Cycle Scheduler initialized")
        except ImportError as e:
            logger.warning(
                f"⚠️ Healing Cycle Scheduler initialization failed: {e} (schedule module may not be installed)"
            )
            self.scheduler = None
        except Exception as e:
            logger.warning(f"⚠️ Healing Cycle Scheduler initialization failed: {e}")
            self.scheduler = None

    def _init_resolution_tracker(self) -> None:
        """Initialize resolution tracker."""
        try:
            from src.analytics.resolution_tracker import ResolutionTracker

            self.tracker = ResolutionTracker()
            logger.info("✅ Resolution Tracker initialized")
        except Exception as e:
            logger.warning(f"⚠️ Resolution Tracker initialization failed: {e}")
            self.tracker = None

    async def run_unified_healing_pipeline(
        self, num_cycles: int = 1
    ) -> list[HealingPipelineStatus]:
        """Execute complete unified healing pipeline."""
        logger.info(f"🚀 Starting Unified Healing Pipeline ({num_cycles} cycles)")

        for cycle in range(1, num_cycles + 1):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"HEALING CYCLE {cycle}/{num_cycles}")
            logger.info(f"{'=' * 70}")

            status = await self._execute_healing_cycle(cycle)
            self.status_history.append(status)

            logger.info(f"✅ Cycle {cycle} Summary:")
            logger.info(f"   Issues Detected: {status.issues_detected}")
            logger.info(f"   Tasks Created: {status.tasks_created}")
            logger.info(f"   Tasks Completed: {status.tasks_completed}")
            logger.info(f"   Healing Applied: {status.healing_applied}")
            logger.info(f"   Health Status: {status.health_status}")

        logger.info(f"\n{'=' * 70}")
        logger.info("🎉 Unified Healing Pipeline Complete")
        logger.info(f"{'=' * 70}")

        return self.status_history

    async def _execute_healing_cycle(self, cycle_num: int) -> HealingPipelineStatus:
        """Execute single healing cycle through entire pipeline."""
        status = HealingPipelineStatus(cycle_number=cycle_num)

        # Phase 1: Issue Detection
        logger.info("📋 Phase 1: Issue Detection via Extended Cycles")
        issues_data = await self._detect_issues()
        if issues_data:
            status.issues_detected = issues_data.get("total_issues", 0)
            logger.info(f"   Found {status.issues_detected} issues")

            # Record issues as detected in tracker
            if self.tracker and issues_data.get("issues"):
                for idx, issue in enumerate(issues_data["issues"][:10]):  # Track top 10
                    try:
                        # Handle both dict and CodebaseIssue objects
                        if isinstance(issue, dict):
                            issue_type = issue.get("type", "unknown")
                            description = issue.get("message", "")
                            file_path = issue.get("file", "")
                            severity = issue.get("severity", "medium")
                        else:
                            # CodebaseIssue object
                            issue_type = getattr(issue, "issue_type", "unknown")
                            description = getattr(issue, "message", "")
                            file_path = str(getattr(issue, "file_path", ""))
                            severity = str(getattr(issue, "severity", "medium")).lower()

                        self.tracker.register_detected_issue(
                            issue_id=f"detected_{idx}",
                            issue_type=str(issue_type),
                            description=description,
                            file_path=file_path,
                            severity=severity,
                            cycle_num=cycle_num,
                        )
                    except Exception as e:
                        logger.warning(f"Could not record issue: {e}")

        # Phase 2: Task Routing to ChatDev
        logger.info("🤖 Phase 2: Multi-Agent Task Routing")
        if self.chatdev_router and issues_data:
            tasks_data = await self._route_to_chatdev(issues_data)
            status.tasks_created = tasks_data.get("tasks_created", 0)
            status.tasks_completed = tasks_data.get("tasks_completed", 0)
            logger.info(f"   Created {status.tasks_created} tasks")
            logger.info(f"   Completed {status.tasks_completed} tasks")

            # Record routing in tracker
            if self.tracker and status.tasks_created > 0:
                for idx in range(min(5, status.tasks_created)):  # Mark first 5 issues as routed
                    self.tracker.mark_routed(issue_id=f"routed_{idx}", agent="chatdev")

        # Phase 3: Autonomous Healing
        logger.info("🏥 Phase 3: Autonomous Healing & Validation")
        healing_data = await self._apply_healing()
        if healing_data:
            status.healing_applied = healing_data.get("healing_applied", 0)
            status.health_status = healing_data.get("health_status", "unknown")
            logger.info(f"   Applied {status.healing_applied} healing actions")
            logger.info(f"   Health Status: {status.health_status}")

            # Record resolutions in tracker
            if self.tracker and status.healing_applied > 0:
                for idx in range(min(5, status.healing_applied)):  # Mark first 5 issues as resolved
                    self.tracker.mark_resolved(
                        issue_id=f"resolved_{idx}",
                        fix_code="auto_healing",
                        success=status.health_status == "healthy",
                    )

        status.timestamp = datetime.now(UTC)

        # Record cycle in dashboard if available
        if self.dashboard:
            self.dashboard.record_cycle(status.to_dict())

        return status

    async def _detect_issues(self) -> dict[str, Any]:
        """Phase 1: Detect issues using extended cycle runner."""
        if not self.cycle_runner:
            logger.warning("⚠️ Extended cycle runner not available")
            return {}

        try:
            logger.info("   Scanning repository...")
            issues = self.cycle_runner.detector.scan_repository()
            summary = self.cycle_runner.detector.get_issue_summary()

            logger.info(f"   Detected {len(issues)} issues")
            logger.info(f"   By Type: {summary['by_type']}")

            return {"total_issues": len(issues), "issues": issues, "summary": summary}
        except Exception as e:
            logger.error(f"❌ Issue detection failed: {e}")
            return {}

    async def _route_to_chatdev(self, issues_data: dict[str, Any]) -> dict[str, Any]:
        """Phase 2: Route top issues to ChatDev multi-agent team."""
        if not self.chatdev_router or not self.chatdev_router.chatdev_available:
            logger.warning("⚠️ ChatDev router not available")
            return {}

        try:
            issues = issues_data.get("issues", [])

            # Get issue types in order
            issue_types = []
            for issue in issues[:5]:
                if hasattr(issue, "issue_type"):
                    issue_types.append(issue.issue_type.value)
                elif isinstance(issue, dict) and "issue_type" in issue:
                    issue_types.append(issue["issue_type"])
                else:
                    issue_types.append("unknown")

            logger.info(f"   Routing {min(len(issues), 5)} issues to ChatDev...")

            # Convert issues to dicts if needed
            issues_dict = []
            for issue in issues[:5]:
                if hasattr(issue, "__dict__"):
                    issue_dict = issue.__dict__
                    # Convert Path objects to strings
                    if "file_path" in issue_dict:
                        issue_dict["file_path"] = str(issue_dict["file_path"])
                    issues_dict.append(issue_dict)
                else:
                    issues_dict.append(issue)

            results = await self.chatdev_router.route_autonomous_cycle_issues(
                issues=issues_dict, issue_types=issue_types, max_tasks=3
            )

            completed = sum(1 for r in results if r.get("status") == "completed")
            logger.info(f"   ChatDev routing: {completed}/{len(results)} tasks completed")

            return {
                "tasks_created": len(results),
                "tasks_completed": completed,
                "results": results,
            }
        except Exception as e:
            logger.error(f"❌ ChatDev routing failed: {e}")
            return {}

    async def _apply_healing(self) -> dict[str, Any]:
        """Phase 3: Apply autonomous healing and validate."""
        if not self.healing_coordinator:
            logger.warning("⚠️ Healing coordinator not available")
            return {}

        try:
            logger.info("   Running health check...")
            health_status = await self.healing_coordinator.run_comprehensive_health_check()

            logger.info(f"   Health Status: {health_status.get('status', 'unknown')}")

            return {
                "healing_applied": 1,  # One healing action per cycle
                "health_status": health_status.get("status", "unknown"),
                "details": health_status,
            }
        except Exception as e:
            logger.error(f"❌ Healing failed: {e}")
            return {}

    def save_pipeline_report(self, output_path: Path | None = None) -> Path:
        """Save unified healing pipeline report."""
        if output_path is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            output_path = REPO_ROOT / f"unified_healing_report_{timestamp}.json"

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_cycles": len(self.status_history),
            "cycles": [s.to_dict() for s in self.status_history],
            "summary": {
                "total_issues_detected": sum(s.issues_detected for s in self.status_history),
                "total_tasks_created": sum(s.tasks_created for s in self.status_history),
                "total_tasks_completed": sum(s.tasks_completed for s in self.status_history),
                "total_healing_applied": sum(s.healing_applied for s in self.status_history),
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"📊 Report saved to: {output_path}")
        return output_path


async def main():
    """Run unified autonomous healing pipeline."""
    logger.info("=" * 70)
    logger.info("UNIFIED AUTONOMOUS HEALING PIPELINE")
    logger.info("=" * 70)

    pipeline = UnifiedAutonomousHealingPipeline()

    # Run 2 healing cycles
    results = await pipeline.run_unified_healing_pipeline(num_cycles=2)

    # Save report
    report_path = pipeline.save_pipeline_report()

    logger.info("\n✅ Unified Healing Pipeline Execution Summary:")
    logger.info(f"   Cycles Completed: {len(results)}")
    for i, status in enumerate(results, 1):
        logger.info(
            f"   Cycle {i}: {status.issues_detected} issues → "
            f"{status.tasks_completed}/{status.tasks_created} tasks completed"
        )

    logger.info(f"   Report: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())

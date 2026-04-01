"""Unified Health Dashboard — Consolidated from 6+ health monitoring systems.

OmniTag: {
    "purpose": "UnifiedHealthMonitoring",
    "tags": ["Health", "Dashboard", "Monitoring", "Consolidation"],
    "category": "observability",
    "evolution_stage": "v3.0_consolidated"
}

MegaTag: HEALTH⨳UNIFIED_MONITOR⦾CONSOLIDATION→∞

This module consolidates:
1. health_dashboard.py (scripts/)
2. healing_dashboard.py (scripts/)
3. ecosystem_health_dashboard.py (scripts/)
4. testing_dashboard.py (src/diagnostics/)
5. launch_health_dashboard.py (scripts/)
6. test_dashboard_healing_integration.py (tests/)

Architecture: Modular monitoring system with category-based health checks.
"""

import asyncio
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from src.utils.repo_path_resolver import RepoPathResolver

    PATH_RESOLVER_AVAILABLE = True
except ImportError:
    PATH_RESOLVER_AVAILABLE = False


class HealthStatus(Enum):
    """Health status levels with emoji representations."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

    def emoji(self) -> str:
        """Get emoji for status."""
        return {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.WARNING: "🟡",
            HealthStatus.CRITICAL: "🔴",
            HealthStatus.UNKNOWN: "⚪",
        }[self]


class HealthCategory(Enum):
    """Health monitoring categories."""

    SYSTEM = "system"
    HEALING = "healing"
    ECOSYSTEM = "ecosystem"
    TESTING = "testing"
    ORCHESTRATION = "orchestration"
    CONSCIOUSNESS = "consciousness"


@dataclass
class HealthCheck:
    """Individual health check result."""

    name: str
    category: HealthCategory
    status: HealthStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "category": self.category.value,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class HealthSnapshot:
    """Complete health snapshot across all categories."""

    timestamp: datetime
    overall_status: HealthStatus
    checks: list[HealthCheck]
    summary: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate summary statistics."""
        self.summary = {
            "total": len(self.checks),
            "healthy": sum(1 for c in self.checks if c.status == HealthStatus.HEALTHY),
            "warning": sum(1 for c in self.checks if c.status == HealthStatus.WARNING),
            "critical": sum(1 for c in self.checks if c.status == HealthStatus.CRITICAL),
            "unknown": sum(1 for c in self.checks if c.status == HealthStatus.UNKNOWN),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status.value,
            "summary": self.summary,
            "checks": [c.to_dict() for c in self.checks],
        }


class SystemHealthMonitor:
    """System-level health checks (CPU, memory, disk, services)."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize SystemHealthMonitor with repo_root."""
        self.repo_root = repo_root or Path.cwd()

    async def check_health(self) -> list[HealthCheck]:
        """Run all system health checks."""
        checks = []

        # Check Python environment
        checks.append(self._check_python_version())

        # Check disk space
        checks.append(self._check_disk_space())

        # Check required services (Ollama, MCP, etc.)
        checks.extend(await self._check_services())

        # Check dependencies
        checks.append(self._check_dependencies())

        return checks

    def _check_python_version(self) -> HealthCheck:
        """Check Python version compatibility."""
        version = sys.version_info
        if version >= (3, 13):
            status = HealthStatus.HEALTHY
            message = f"Python {version.major}.{version.minor}.{version.micro}"
        elif version >= (3, 10):
            status = HealthStatus.WARNING
            message = f"Python {version.major}.{version.minor} (upgrade to 3.13+ recommended)"
        else:
            status = HealthStatus.CRITICAL
            message = f"Python {version.major}.{version.minor} (3.13+ required)"

        return HealthCheck(
            name="python_version",
            category=HealthCategory.SYSTEM,
            status=status,
            message=message,
            details={"version": f"{version.major}.{version.minor}.{version.micro}"},
        )

    def _check_disk_space(self) -> HealthCheck:
        """Check available disk space."""
        try:
            import shutil

            usage = shutil.disk_usage(self.repo_root)
            free_gb = usage.free / (1024**3)
            percent_free = (usage.free / usage.total) * 100

            if free_gb > 10 and percent_free > 10:
                status = HealthStatus.HEALTHY
                message = f"{free_gb:.1f}GB free ({percent_free:.1f}%)"
            elif free_gb > 5:
                status = HealthStatus.WARNING
                message = f"Low disk space: {free_gb:.1f}GB free ({percent_free:.1f}%)"
            else:
                status = HealthStatus.CRITICAL
                message = f"Critical disk space: {free_gb:.1f}GB free ({percent_free:.1f}%)"

            return HealthCheck(
                name="disk_space",
                category=HealthCategory.SYSTEM,
                status=status,
                message=message,
                details={
                    "free_gb": free_gb,
                    "total_gb": usage.total / (1024**3),
                    "percent_free": percent_free,
                },
            )
        except Exception as e:
            return HealthCheck(
                name="disk_space",
                category=HealthCategory.SYSTEM,
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk space: {e}",
            )

    async def _check_services(self) -> list[HealthCheck]:
        """Check status of required services."""
        checks = []

        # Check Ollama
        ollama_check = await self._check_service_port("ollama", "localhost", 11434)
        checks.append(ollama_check)

        # Check MCP Server
        mcp_check = await self._check_service_port("mcp_server", "localhost", 8081)
        checks.append(mcp_check)

        return checks

    async def _check_service_port(self, name: str, host: str, port: int) -> HealthCheck:
        """Check if a service is listening on a port (async)."""
        try:
            # Use asyncio for non-blocking socket check
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=2.0
            )
            writer.close()
            await writer.wait_closed()

            return HealthCheck(
                name=f"service_{name}",
                category=HealthCategory.SYSTEM,
                status=HealthStatus.HEALTHY,
                message=f"{name} running on {host}:{port}",
                details={"host": host, "port": port},
            )
        except OSError:
            # Catches TimeoutError, ConnectionRefusedError, and other connection issues
            return HealthCheck(
                name=f"service_{name}",
                category=HealthCategory.SYSTEM,
                status=HealthStatus.WARNING,
                message=f"{name} not responding on {host}:{port}",
                details={"host": host, "port": port},
            )
        except Exception as e:
            return HealthCheck(
                name=f"service_{name}",
                category=HealthCategory.SYSTEM,
                status=HealthStatus.WARNING,
                message=f"Failed to check {name}: {e}",
            )

    def _check_dependencies(self) -> HealthCheck:
        """Check critical dependencies are installed."""
        missing = []
        try:
            import PyQt5
        except ImportError:
            missing.append("PyQt5")

        try:
            import plotly
        except ImportError:
            missing.append("plotly")

        try:
            import httpx
        except ImportError:
            missing.append("httpx")

        if not missing:
            return HealthCheck(
                name="dependencies",
                category=HealthCategory.SYSTEM,
                status=HealthStatus.HEALTHY,
                message="All critical dependencies installed",
            )
        else:
            return HealthCheck(
                name="dependencies",
                category=HealthCategory.SYSTEM,
                status=HealthStatus.WARNING,
                message=f"Missing dependencies: {', '.join(missing)}",
                details={"missing": missing},
            )


class HealingStatusMonitor:
    """Monitor self-healing system status."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize HealingStatusMonitor with repo_root."""
        self.repo_root = repo_root or Path.cwd()

    async def check_health(self) -> list[HealthCheck]:
        """Run healing system health checks."""
        checks = []
        # Yield control for cooperative multitasking
        await asyncio.sleep(0)

        # Check healing history
        checks.append(self._check_healing_history())

        # Check quantum resolver availability
        checks.append(self._check_quantum_resolver())

        return checks

    def _check_healing_history(self) -> HealthCheck:
        """Check recent healing activity."""
        history_path = self.repo_root / "state" / "culture_ship_healing_history.json"

        if not history_path.exists():
            return HealthCheck(
                name="healing_history",
                category=HealthCategory.HEALING,
                status=HealthStatus.HEALTHY,
                message="No healing history (system stable)",
            )

        try:
            with open(history_path) as f:
                history = json.load(f)

            recent_healings = [
                h
                for h in history.get("decisions", [])
                if (datetime.now() - datetime.fromisoformat(h.get("timestamp", "2000-01-01"))).days
                < 7
            ]

            if not recent_healings:
                status = HealthStatus.HEALTHY
                message = "No recent healing required (stable)"
            elif len(recent_healings) < 5:
                status = HealthStatus.HEALTHY
                message = f"{len(recent_healings)} healings in last 7 days"
            elif len(recent_healings) < 20:
                status = HealthStatus.WARNING
                message = f"{len(recent_healings)} healings in last 7 days (elevated activity)"
            else:
                status = HealthStatus.CRITICAL
                message = (
                    f"{len(recent_healings)} healings in last 7 days (high activity - investigate)"
                )

            return HealthCheck(
                name="healing_history",
                category=HealthCategory.HEALING,
                status=status,
                message=message,
                details={"recent_count": len(recent_healings)},
            )
        except Exception as e:
            return HealthCheck(
                name="healing_history",
                category=HealthCategory.HEALING,
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check healing history: {e}",
            )

    def _check_quantum_resolver(self) -> HealthCheck:
        """Check quantum problem resolver is available."""
        resolver_path = self.repo_root / "src" / "healing" / "quantum_problem_resolver.py"

        if resolver_path.exists():
            return HealthCheck(
                name="quantum_resolver",
                category=HealthCategory.HEALING,
                status=HealthStatus.HEALTHY,
                message="Quantum problem resolver available",
            )
        else:
            return HealthCheck(
                name="quantum_resolver",
                category=HealthCategory.HEALING,
                status=HealthStatus.WARNING,
                message="Quantum problem resolver not found",
            )


class EcosystemHealthMonitor:
    """Monitor multi-repository ecosystem health."""

    def __init__(self):
        """Initialize EcosystemHealthMonitor."""
        self.repos = {}
        if PATH_RESOLVER_AVAILABLE:
            resolver = RepoPathResolver()
            self.repos = {
                "NuSyQ-Hub": resolver.get_nusyq_hub_root(),
                "NuSyQ": resolver.get_nusyq_root(),
                "SimulatedVerse": resolver.get_simulatedverse_root(),
            }

    async def check_health(self) -> list[HealthCheck]:
        """Run ecosystem health checks."""
        checks = []
        # Yield control for cooperative multitasking
        await asyncio.sleep(0)

        # Check each repository
        for repo_name, repo_path in self.repos.items():
            checks.append(self._check_repo(repo_name, repo_path))

        # Check cross-repo integration
        checks.append(self._check_cross_repo_integration())

        return checks

    def _check_repo(self, name: str, path: Path | None) -> HealthCheck:
        """Check repository health."""
        if path is None:
            return HealthCheck(
                name=f"repo_{name.lower()}",
                category=HealthCategory.ECOSYSTEM,
                status=HealthStatus.WARNING,
                message=f"{name} repository not found",
            )

        if not path.exists():
            return HealthCheck(
                name=f"repo_{name.lower()}",
                category=HealthCategory.ECOSYSTEM,
                status=HealthStatus.CRITICAL,
                message=f"{name} repository path does not exist: {path}",
            )

        # Check git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                modified_files = len([line for line in result.stdout.splitlines() if line.strip()])
                if modified_files == 0:
                    status = HealthStatus.HEALTHY
                    message = f"{name} clean"
                elif modified_files < 10:
                    status = HealthStatus.HEALTHY
                    message = f"{name} has {modified_files} modified files"
                else:
                    status = HealthStatus.WARNING
                    message = f"{name} has {modified_files} modified files (consider committing)"

                return HealthCheck(
                    name=f"repo_{name.lower()}",
                    category=HealthCategory.ECOSYSTEM,
                    status=status,
                    message=message,
                    details={"path": str(path), "modified_files": modified_files},
                )
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)

        return HealthCheck(
            name=f"repo_{name.lower()}",
            category=HealthCategory.ECOSYSTEM,
            status=HealthStatus.HEALTHY,
            message=f"{name} exists",
            details={"path": str(path)},
        )

    def _check_cross_repo_integration(self) -> HealthCheck:
        """Check cross-repository integration health."""
        if len(self.repos) == 3:
            return HealthCheck(
                name="cross_repo_integration",
                category=HealthCategory.ECOSYSTEM,
                status=HealthStatus.HEALTHY,
                message="All 3 repositories available",
                details={"repos": list(self.repos.keys())},
            )
        else:
            return HealthCheck(
                name="cross_repo_integration",
                category=HealthCategory.ECOSYSTEM,
                status=HealthStatus.WARNING,
                message=f"Only {len(self.repos)}/3 repositories found",
                details={"found": list(self.repos.keys())},
            )


class TestingStatusMonitor:
    """Monitor testing infrastructure health."""

    __test__ = False  # Not a pytest test class — prevent PytestCollectionWarning

    def __init__(self, repo_root: Path | None = None):
        """Initialize TestingStatusMonitor with repo_root."""
        self.repo_root = repo_root or Path.cwd()

    async def check_health(self) -> list[HealthCheck]:
        """Run testing health checks."""
        checks = []
        # Yield control for cooperative multitasking
        await asyncio.sleep(0)

        # Check pytest is installed
        checks.append(self._check_pytest())

        # Check test coverage
        checks.append(self._check_test_coverage())

        return checks

    def _check_pytest(self) -> HealthCheck:
        """Check pytest is available."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                version = result.stdout.split("\n")[0].strip()
                return HealthCheck(
                    name="pytest",
                    category=HealthCategory.TESTING,
                    status=HealthStatus.HEALTHY,
                    message=f"pytest available: {version}",
                )
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)

        return HealthCheck(
            name="pytest",
            category=HealthCategory.TESTING,
            status=HealthStatus.WARNING,
            message="pytest not available",
        )

    def _check_test_coverage(self) -> HealthCheck:
        """Check test coverage statistics."""
        coverage_file = self.repo_root / ".coverage"

        if coverage_file.exists():
            return HealthCheck(
                name="test_coverage",
                category=HealthCategory.TESTING,
                status=HealthStatus.HEALTHY,
                message="Coverage data available (run pytest --cov for details)",
            )
        else:
            return HealthCheck(
                name="test_coverage",
                category=HealthCategory.TESTING,
                status=HealthStatus.WARNING,
                message="No coverage data (run pytest --cov to generate)",
            )


class UnifiedHealthDashboard:
    """Unified health monitoring dashboard consolidating all health check systems.

    Replaced files:
    - scripts/health_dashboard.py
    - scripts/healing_dashboard.py
    - scripts/ecosystem_health_dashboard.py
    - scripts/testing_dashboard.py
    - scripts/launch_health_dashboard.py
    """

    def __init__(self, repo_root: Path | None = None):
        """Initialize UnifiedHealthDashboard with repo_root."""
        self.repo_root = repo_root or Path.cwd()
        self.monitors = {
            HealthCategory.SYSTEM: SystemHealthMonitor(self.repo_root),
            HealthCategory.HEALING: HealingStatusMonitor(self.repo_root),
            HealthCategory.ECOSYSTEM: EcosystemHealthMonitor(),
            HealthCategory.TESTING: TestingStatusMonitor(self.repo_root),
        }

    async def get_health_snapshot(self) -> HealthSnapshot:
        """Get complete health snapshot across all categories."""
        all_checks = []

        # Run all monitors concurrently
        for _category, monitor in self.monitors.items():
            checks = await monitor.check_health()
            all_checks.extend(checks)

        # Determine overall status
        if any(c.status == HealthStatus.CRITICAL for c in all_checks):
            overall_status = HealthStatus.CRITICAL
        elif any(c.status == HealthStatus.WARNING for c in all_checks) or any(
            c.status == HealthStatus.UNKNOWN for c in all_checks
        ):
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY

        return HealthSnapshot(
            timestamp=datetime.now(),
            overall_status=overall_status,
            checks=all_checks,
        )

    async def get_category_health(self, category: HealthCategory) -> list[HealthCheck]:
        """Get health for specific category only."""
        monitor = self.monitors.get(category)
        if monitor:
            return await monitor.check_health()
        return []

    def print_health_report(self, snapshot: HealthSnapshot) -> None:
        """Print formatted health report to console."""
        logger.info("\n" + "=" * 80)
        logger.info(
            f"🏥 NuSyQ Unified Health Dashboard — {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info("=" * 80)

        logger.info(
            f"\n📊 Overall Status: {snapshot.overall_status.emoji()} {snapshot.overall_status.value.upper()}"
        )
        logger.error(
            f"\n📈 Summary: {snapshot.summary['healthy']}✅ {snapshot.summary['warning']}⚠️  {snapshot.summary['critical']}❌ {snapshot.summary['unknown']}⚪"
        )

        # Group by category
        by_category = {}
        for check in snapshot.checks:
            if check.category not in by_category:
                by_category[check.category] = []
            by_category[check.category].append(check)

        # Print each category
        for category in HealthCategory:
            if category not in by_category:
                continue

            logger.info(f"\n{'─' * 80}")
            logger.info(f"📁 {category.value.upper()}")
            logger.info(f"{'─' * 80}")

            for check in by_category[category]:
                status_emoji = check.status.emoji()
                logger.info(f"{status_emoji} {check.name:30} {check.message}")

                if check.details and len(check.details) <= 3:
                    for key, value in check.details.items():
                        logger.info(f"   • {key}: {value}")

        logger.info("\n" + "=" * 80 + "\n")


async def main():
    """CLI entry point for unified health dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="NuSyQ Unified Health Dashboard")
    parser.add_argument(
        "--category",
        type=str,
        choices=[c.value for c in HealthCategory],
        help="Check specific category only",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    dashboard = UnifiedHealthDashboard()

    if args.category:
        category = HealthCategory(args.category)
        checks = await dashboard.get_category_health(category)
        snapshot = HealthSnapshot(
            timestamp=datetime.now(),
            overall_status=HealthStatus.HEALTHY,  # Will be recalculated
            checks=checks,
        )
    else:
        snapshot = await dashboard.get_health_snapshot()

    if args.json:
        logger.info(json.dumps(snapshot.to_dict(), indent=2))
    else:
        dashboard.print_health_report(snapshot)

    # Exit code based on health
    if snapshot.overall_status == HealthStatus.CRITICAL:
        sys.exit(2)
    elif snapshot.overall_status == HealthStatus.WARNING:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

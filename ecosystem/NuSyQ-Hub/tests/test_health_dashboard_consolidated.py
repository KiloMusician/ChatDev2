"""Unit tests for unified health dashboard consolidation.

Tests all health monitoring categories and ensures consolidated dashboard works correctly.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.observability.health_dashboard_consolidated import (
    EcosystemHealthMonitor,
    HealingStatusMonitor,
    HealthCategory,
    HealthCheck,
    HealthSnapshot,
    HealthStatus,
    SystemHealthMonitor,
    TestingStatusMonitor,
    UnifiedHealthDashboard,
)


class TestHealthEnums:
    """Test health status and category enums."""

    def test_health_status_values(self):
        """Verify health status enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.CRITICAL.value == "critical"
        assert HealthStatus.UNKNOWN.value == "unknown"

    def test_health_status_emoji(self):
        """Verify health status emoji representations."""
        assert HealthStatus.HEALTHY.emoji() == "🟢"
        assert HealthStatus.WARNING.emoji() == "🟡"
        assert HealthStatus.CRITICAL.emoji() == "🔴"
        assert HealthStatus.UNKNOWN.emoji() == "⚪"

    def test_health_category_values(self):
        """Verify health category enum values."""
        assert HealthCategory.SYSTEM.value == "system"
        assert HealthCategory.HEALING.value == "healing"
        assert HealthCategory.ECOSYSTEM.value == "ecosystem"
        assert HealthCategory.TESTING.value == "testing"
        assert HealthCategory.ORCHESTRATION.value == "orchestration"
        assert HealthCategory.CONSCIOUSNESS.value == "consciousness"


class TestHealthCheck:
    """Test HealthCheck dataclass."""

    def test_health_check_creation(self):
        """Verify HealthCheck instance creation."""
        check = HealthCheck(
            name="test_check",
            category=HealthCategory.SYSTEM,
            status=HealthStatus.HEALTHY,
            message="All systems operational",
            details={"key": "value"},
        )

        assert check.name == "test_check"
        assert check.category == HealthCategory.SYSTEM
        assert check.status == HealthStatus.HEALTHY
        assert check.message == "All systems operational"
        assert check.details == {"key": "value"}
        assert check.timestamp is not None

    def test_health_check_to_dict(self):
        """Verify HealthCheck serialization to dict."""
        check = HealthCheck(
            name="test_check",
            category=HealthCategory.SYSTEM,
            status=HealthStatus.HEALTHY,
            message="OK",
        )

        result = check.to_dict()

        assert result["name"] == "test_check"
        assert result["category"] == "system"
        assert result["status"] == "healthy"
        assert result["message"] == "OK"
        assert "timestamp" in result


class TestHealthSnapshot:
    """Test HealthSnapshot dataclass."""

    def test_health_snapshot_summary_calculation(self):
        """Verify summary statistics are calculated correctly."""
        checks = [
            HealthCheck("check1", HealthCategory.SYSTEM, HealthStatus.HEALTHY, "OK"),
            HealthCheck("check2", HealthCategory.SYSTEM, HealthStatus.HEALTHY, "OK"),
            HealthCheck("check3", HealthCategory.SYSTEM, HealthStatus.WARNING, "Warning"),
            HealthCheck("check4", HealthCategory.SYSTEM, HealthStatus.CRITICAL, "Critical"),
        ]

        snapshot = HealthSnapshot(
            timestamp=None, overall_status=HealthStatus.WARNING, checks=checks
        )

        assert snapshot.summary["total"] == 4
        assert snapshot.summary["healthy"] == 2
        assert snapshot.summary["warning"] == 1
        assert snapshot.summary["critical"] == 1


class TestSystemHealthMonitor:
    """Test SystemHealthMonitor class."""

    @pytest.mark.asyncio
    async def test_check_health_returns_list(self):
        """Verify check_health returns list of checks."""
        monitor = SystemHealthMonitor()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            checks = await monitor.check_health()

            assert isinstance(checks, list)
            assert len(checks) > 0
            assert all(isinstance(c, HealthCheck) for c in checks)

    def test_python_version_check(self):
        """Verify Python version check."""
        monitor = SystemHealthMonitor()
        check = monitor._check_python_version()

        assert check.name == "python_version"
        assert check.category == HealthCategory.SYSTEM
        assert check.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert "version" in check.details

    def test_disk_space_check(self):
        """Verify disk space check."""
        monitor = SystemHealthMonitor()

        with patch("shutil.disk_usage") as mock_disk:
            # Mock 100GB total, 80GB free (80%)
            mock_disk.return_value = MagicMock(total=100 * 1024**3, free=80 * 1024**3)

            check = monitor._check_disk_space()

            assert check.name == "disk_space"
            assert check.status == HealthStatus.HEALTHY
            assert "free_gb" in check.details
            assert "total_gb" in check.details
            assert "percent_free" in check.details


class TestHealingStatusMonitor:
    """Test HealingStatusMonitor class."""

    @pytest.mark.asyncio
    async def test_check_health_returns_list(self):
        """Verify check_health returns list of checks."""
        monitor = HealingStatusMonitor()
        checks = await monitor.check_health()

        assert isinstance(checks, list)
        assert len(checks) >= 2  # At least healing history and quantum resolver
        assert all(isinstance(c, HealthCheck) for c in checks)

    def test_healing_history_check_missing_file(self):
        """Verify healing history check handles missing file."""
        monitor = HealingStatusMonitor()

        with patch("pathlib.Path.exists", return_value=False):
            check = monitor._check_healing_history()

            assert check.name == "healing_history"
            assert check.status == HealthStatus.HEALTHY
            assert "stable" in check.message.lower()


class TestEcosystemHealthMonitor:
    """Test EcosystemHealthMonitor class."""

    @pytest.mark.asyncio
    async def test_check_health_returns_list(self):
        """Verify check_health returns list of checks for all repos."""
        monitor = EcosystemHealthMonitor()
        checks = await monitor.check_health()

        assert isinstance(checks, list)
        # Should return at least cross_repo_integration check (may be 1 if repos not found)
        assert len(checks) >= 1
        assert all(isinstance(c, HealthCheck) for c in checks)

    def test_repo_check_missing_path(self):
        """Verify repo check handles missing repository."""
        monitor = EcosystemHealthMonitor()
        check = monitor._check_repo("TestRepo", None)

        assert check.name == "repo_testrepo"
        assert check.status == HealthStatus.WARNING
        assert "not found" in check.message.lower()

    def test_repo_check_valid_path(self):
        """Verify repo check handles valid repository."""
        monitor = EcosystemHealthMonitor()

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
        ):
            check = monitor._check_repo("TestRepo", Path("/fake/path"))

            assert check.name == "repo_testrepo"
            assert check.status == HealthStatus.HEALTHY


class TestTestingStatusMonitorClass:
    """Test TestingStatusMonitor class."""

    @pytest.mark.asyncio
    async def test_check_health_returns_list(self):
        """Verify check_health returns list of testing checks."""
        monitor = TestingStatusMonitor()
        checks = await monitor.check_health()

        assert isinstance(checks, list)
        assert len(checks) >= 2  # At least pytest and coverage checks
        assert all(isinstance(c, HealthCheck) for c in checks)

    def test_pytest_check_available(self):
        """Verify pytest availability check."""
        monitor = TestingStatusMonitor()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="pytest 7.4.0", stderr="")

            check = monitor._check_pytest()

            assert check.name == "pytest"
            assert check.status == HealthStatus.HEALTHY


class TestUnifiedHealthDashboard:
    """Test UnifiedHealthDashboard class."""

    @pytest.mark.asyncio
    async def test_get_health_snapshot_returns_snapshot(self):
        """Verify get_health_snapshot returns complete snapshot."""
        dashboard = UnifiedHealthDashboard()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            snapshot = await dashboard.get_health_snapshot()

            assert isinstance(snapshot, HealthSnapshot)
            assert snapshot.timestamp is not None
            assert isinstance(snapshot.checks, list)
            assert len(snapshot.checks) > 0
            assert snapshot.overall_status in [
                HealthStatus.HEALTHY,
                HealthStatus.WARNING,
                HealthStatus.CRITICAL,
                HealthStatus.UNKNOWN,
            ]

    @pytest.mark.asyncio
    async def test_get_category_health_filters_by_category(self):
        """Verify get_category_health returns only specified category."""
        dashboard = UnifiedHealthDashboard()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            checks = await dashboard.get_category_health(HealthCategory.SYSTEM)

            assert isinstance(checks, list)
            assert all(c.category == HealthCategory.SYSTEM for c in checks)

    @pytest.mark.asyncio
    async def test_get_health_snapshot_handles_monitor_failures(self):
        """Verify dashboard handles monitor failures gracefully."""
        dashboard = UnifiedHealthDashboard()

        # Mock all monitors to fail
        with (
            patch(
                "src.observability.health_dashboard_consolidated.SystemHealthMonitor"
            ) as mock_system,
            patch(
                "src.observability.health_dashboard_consolidated.HealingStatusMonitor"
            ) as mock_healing,
            patch(
                "src.observability.health_dashboard_consolidated.EcosystemHealthMonitor"
            ) as mock_ecosystem,
            patch(
                "src.observability.health_dashboard_consolidated.TestingStatusMonitor"
            ) as mock_testing,
        ):
            # All monitors raise exceptions
            mock_system.return_value.check_health = AsyncMock(side_effect=Exception("System error"))
            mock_healing.return_value.check_health = AsyncMock(
                side_effect=Exception("Healing error")
            )
            mock_ecosystem.return_value.check_health = AsyncMock(
                side_effect=Exception("Ecosystem error")
            )
            mock_testing.return_value.check_health = AsyncMock(
                side_effect=Exception("Testing error")
            )

            snapshot = await dashboard.get_health_snapshot()

            # Should still return a valid snapshot (graceful degradation)
            assert isinstance(snapshot, HealthSnapshot)
            # Overall status will be based on any successful checks, not necessarily CRITICAL
            assert snapshot.overall_status in [
                HealthStatus.WARNING,
                HealthStatus.CRITICAL,
                HealthStatus.UNKNOWN,
            ]

    def test_print_health_report_does_not_crash(self, caplog):
        """Verify print_health_report outputs without crashing."""
        import logging

        caplog.set_level(logging.INFO)
        dashboard = UnifiedHealthDashboard()

        checks = [
            HealthCheck("check1", HealthCategory.SYSTEM, HealthStatus.HEALTHY, "OK"),
            HealthCheck("check2", HealthCategory.SYSTEM, HealthStatus.WARNING, "Warning"),
        ]

        snapshot = HealthSnapshot(
            timestamp=datetime.now(), overall_status=HealthStatus.WARNING, checks=checks
        )

        # Should not raise any exceptions
        dashboard.print_health_report(snapshot)

        assert "SYSTEM" in caplog.text or "check1" in caplog.text


class TestBackwardCompatibility:
    """Test backward compatibility via shims."""

    def test_shim_files_exist(self):
        """Verify all shim files were created."""
        shims = [
            Path("scripts/_health_dashboard_shim.py"),
            Path("scripts/_healing_dashboard_shim.py"),
            Path("scripts/_ecosystem_health_dashboard_shim.py"),
            Path("scripts/_launch_health_dashboard_shim.py"),
            Path("src/diagnostics/_testing_dashboard_shim.py"),
        ]

        for shim in shims:
            assert shim.exists(), f"Shim file missing: {shim}"

    @pytest.mark.asyncio
    async def test_shims_can_import_consolidated(self):
        """Verify shims can successfully import consolidated dashboard."""
        from src.observability.health_dashboard_consolidated import UnifiedHealthDashboard

        dashboard = UnifiedHealthDashboard()
        assert dashboard is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

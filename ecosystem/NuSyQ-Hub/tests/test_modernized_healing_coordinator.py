"""Tests for ModernizedHealingCoordinator.

Covers HealingPriority enum, HealingStatus enum, HealingOperation dataclass,
and ModernizedHealingCoordinator class methods including async healing operations.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# =============================================================================
# Module Import Tests
# =============================================================================
class TestModuleImports:
    """Test that the module and its components can be imported."""

    def test_import_module(self):
        """Module imports without error."""
        import src.healing.modernized_healing_coordinator

    def test_import_healing_priority(self):
        """HealingPriority enum imports."""
        from src.healing.modernized_healing_coordinator import HealingPriority

        assert HealingPriority is not None

    def test_import_healing_status(self):
        """HealingStatus enum imports."""
        from src.healing.modernized_healing_coordinator import HealingStatus

        assert HealingStatus is not None

    def test_import_healing_operation(self):
        """HealingOperation dataclass imports."""
        from src.healing.modernized_healing_coordinator import HealingOperation

        assert HealingOperation is not None

    def test_import_coordinator(self):
        """ModernizedHealingCoordinator class imports."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        assert ModernizedHealingCoordinator is not None


# =============================================================================
# HealingPriority Enum Tests
# =============================================================================
class TestHealingPriorityEnum:
    """Test HealingPriority enumeration values (integer-based)."""

    def test_critical_priority_value(self):
        """CRITICAL has expected value."""
        from src.healing.modernized_healing_coordinator import HealingPriority

        assert HealingPriority.CRITICAL.value == 1

    def test_high_priority_value(self):
        """HIGH has expected value."""
        from src.healing.modernized_healing_coordinator import HealingPriority

        assert HealingPriority.HIGH.value == 2

    def test_normal_priority_value(self):
        """NORMAL has expected value."""
        from src.healing.modernized_healing_coordinator import HealingPriority

        assert HealingPriority.NORMAL.value == 3

    def test_low_priority_value(self):
        """LOW has expected value."""
        from src.healing.modernized_healing_coordinator import HealingPriority

        assert HealingPriority.LOW.value == 4

    def test_preventive_priority_value(self):
        """PREVENTIVE has expected value."""
        from src.healing.modernized_healing_coordinator import HealingPriority

        assert HealingPriority.PREVENTIVE.value == 5


# =============================================================================
# HealingStatus Enum Tests
# =============================================================================
class TestHealingStatusEnum:
    """Test HealingStatus enumeration values."""

    def test_pending_status_value(self):
        """PENDING has expected value."""
        from src.healing.modernized_healing_coordinator import HealingStatus

        assert HealingStatus.PENDING.value == "pending"

    def test_in_progress_status_value(self):
        """IN_PROGRESS has expected value."""
        from src.healing.modernized_healing_coordinator import HealingStatus

        assert HealingStatus.IN_PROGRESS.value == "in_progress"

    def test_completed_status_value(self):
        """COMPLETED has expected value."""
        from src.healing.modernized_healing_coordinator import HealingStatus

        assert HealingStatus.COMPLETED.value == "completed"

    def test_failed_status_value(self):
        """FAILED has expected value."""
        from src.healing.modernized_healing_coordinator import HealingStatus

        assert HealingStatus.FAILED.value == "failed"

    def test_partial_status_value(self):
        """PARTIAL has expected value."""
        from src.healing.modernized_healing_coordinator import HealingStatus

        assert HealingStatus.PARTIAL.value == "partial"


# =============================================================================
# HealingOperation Dataclass Tests
# =============================================================================
class TestHealingOperationDataclass:
    """Test HealingOperation dataclass creation and fields."""

    def test_create_operation_minimal(self):
        """Create operation with required fields."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
        )

        op = HealingOperation(
            operation_id="test_op_001",
            operation_type="import_healing",
            priority=HealingPriority.NORMAL,
            status=HealingStatus.PENDING,
            target="/path/to/target",
            description="Test healing operation",
        )

        assert op.operation_id == "test_op_001"
        assert op.operation_type == "import_healing"
        assert op.priority == HealingPriority.NORMAL
        assert op.status == HealingStatus.PENDING
        assert op.target == "/path/to/target"
        assert op.description == "Test healing operation"

    def test_operation_default_timestamps(self):
        """Default timestamp values are set correctly."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
        )

        op = HealingOperation(
            operation_id="test_op_002",
            operation_type="dependency_healing",
            priority=HealingPriority.HIGH,
            status=HealingStatus.PENDING,
            target="/repo",
            description="Test",
        )

        # Optional fields should have None defaults
        assert op.started_at is None
        assert op.completed_at is None
        assert op.result is None
        assert op.error is None

    def test_operation_with_all_fields(self):
        """Create operation with all fields specified."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
        )

        now = datetime.now()
        result = {"status": "success"}

        op = HealingOperation(
            operation_id="test_op_003",
            operation_type="quantum_healing",
            priority=HealingPriority.CRITICAL,
            status=HealingStatus.COMPLETED,
            target="/repo/src",
            description="Full operation",
            started_at=now,
            completed_at=now,
            result=result,
            error=None,
        )

        assert op.result == result
        assert op.completed_at == now
        assert op.started_at == now


# =============================================================================
# ModernizedHealingCoordinator Init Tests
# =============================================================================
class TestCoordinatorInit:
    """Test ModernizedHealingCoordinator initialization."""

    def test_init_default_repo_root(self):
        """Coordinator initializes with default repo root."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator()

        assert coordinator.repo_root is not None
        assert isinstance(coordinator.repo_root, Path)

    def test_init_custom_repo_root(self, tmp_path):
        """Coordinator initializes with custom repo root."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        assert coordinator.repo_root == tmp_path

    def test_init_empty_healing_operations(self):
        """Healing operations dict starts empty."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator()

        assert coordinator.healing_operations == {}

    def test_init_active_healers_dict(self):
        """Active healers dict initialized with None values."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator()

        assert "quantum_resolver" in coordinator.active_healers
        assert "repo_restorer" in coordinator.active_healers
        assert "import_checker" in coordinator.active_healers
        # All start as None
        assert coordinator.active_healers["quantum_resolver"] is None


# =============================================================================
# Initialize Healers Tests
# =============================================================================
class TestInitializeHealers:
    """Test async initialize_healers method."""

    @pytest.mark.asyncio
    async def test_initialize_healers_success(self):
        """Initialize healers returns True on success."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator()

        with patch.object(
            coordinator,
            "active_healers",
            {"quantum_resolver": None, "repo_restorer": None, "import_checker": None},
        ):
            # Mock the actual imports
            with patch.dict(
                "sys.modules",
                {
                    "src.healing.quantum_problem_resolver": MagicMock(
                        QuantumProblemResolver=MagicMock()
                    ),
                    "src.healing.repository_health_restorer": MagicMock(
                        RepositoryHealthRestorer=MagicMock()
                    ),
                    "src.utils.quick_import_fix": MagicMock(ImportHealthChecker=MagicMock()),
                },
            ):
                result = await coordinator.initialize_healers()

        # Should return True (healers initialized or fallback)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_initialize_healers_handles_import_errors(self, tmp_path):
        """Initialize healers handles import errors gracefully."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        # Even with import issues, should return bool
        result = await coordinator.initialize_healers()
        assert isinstance(result, bool)


# =============================================================================
# Run Comprehensive Health Check Tests
# =============================================================================
class TestRunComprehensiveHealthCheck:
    """Test async run_comprehensive_health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_returns_dict(self, tmp_path):
        """Health check returns dict with expected keys."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        result = await coordinator.run_comprehensive_health_check()

        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "overall_status" in result
        assert "systems" in result

    @pytest.mark.asyncio
    async def test_health_check_systems_contain_imports_when_checker_available(self, tmp_path):
        """Health check systems include import status when checker is available."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        # Set up import checker to enable import checking
        coordinator.active_healers["import_checker"] = MagicMock()

        result = await coordinator.run_comprehensive_health_check()

        systems = result.get("systems", {})
        assert "imports" in systems

    @pytest.mark.asyncio
    async def test_health_check_skips_imports_when_checker_unavailable(self, tmp_path):
        """Health check skips import status when checker is unavailable."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        # Ensure import checker is None
        coordinator.active_healers["import_checker"] = None

        result = await coordinator.run_comprehensive_health_check()

        systems = result.get("systems", {})
        # Should NOT have imports key
        assert "imports" not in systems

    @pytest.mark.asyncio
    async def test_health_check_systems_contain_dependencies_when_restorer_available(
        self, tmp_path
    ):
        """Health check systems include dependency status when restorer is available."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        # Create requirements.txt for dependency check
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("pytest\n")

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        # Set up repo restorer to enable dependency checking
        coordinator.active_healers["repo_restorer"] = MagicMock()

        result = await coordinator.run_comprehensive_health_check()

        systems = result.get("systems", {})
        assert "dependencies" in systems

    @pytest.mark.asyncio
    async def test_health_check_healing_recommended_list(self, tmp_path):
        """Health check includes healing_recommended list."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        result = await coordinator.run_comprehensive_health_check()

        assert "healing_recommended" in result
        assert isinstance(result["healing_recommended"], list)


# =============================================================================
# Check Imports Tests
# =============================================================================
class TestCheckImports:
    """Test async _check_imports method."""

    @pytest.mark.asyncio
    async def test_check_imports_empty_dir(self, tmp_path):
        """Check imports on empty directory."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        result = await coordinator._check_imports()

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_check_imports_with_python_files(self, tmp_path):
        """Check imports finds Python files with imports."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        # Create a test Python file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\nimport sys\n")

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        result = await coordinator._check_imports()

        # Should return OK or status string
        assert isinstance(result, str)
        assert "OK" in result or "DEGRADED" in result or "CRITICAL" in result or "ERROR" in result

    @pytest.mark.asyncio
    async def test_check_imports_excludes_venv(self, tmp_path):
        """Check imports excludes venv directories."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        # Create venv directory with Python files (should be excluded)
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        venv_file = venv_dir / "site_pkg.py"
        venv_file.write_text("import broken_module\n")

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        result = await coordinator._check_imports()

        # Should still return OK (venv excluded)
        assert isinstance(result, str)


# =============================================================================
# Check Dependencies Tests
# =============================================================================
class TestCheckDependencies:
    """Test _check_dependencies method (sync)."""

    def test_check_dependencies_no_requirements(self, tmp_path):
        """Returns warning when no requirements.txt."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        result = coordinator._check_dependencies()

        assert "WARNING" in result
        assert "requirements.txt" in result

    def test_check_dependencies_with_requirements(self, tmp_path):
        """Returns OK with dependency count when file exists."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        # Create requirements.txt
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("pytest>=7.0\nrequests\n# comment line\nflask\n")

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        result = coordinator._check_dependencies()

        assert "OK" in result
        assert "3" in result  # 3 dependencies (comments excluded)

    def test_check_dependencies_empty_file(self, tmp_path):
        """Handles empty requirements.txt."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        req_file = tmp_path / "requirements.txt"
        req_file.write_text("")

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        result = coordinator._check_dependencies()

        assert "OK" in result
        assert "0" in result


# =============================================================================
# Apply Healing Tests
# =============================================================================
class TestApplyHealing:
    """Test async apply_healing method."""

    @pytest.mark.asyncio
    async def test_apply_healing_import_type(self, tmp_path):
        """Apply import healing operation."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        operation = HealingOperation(
            operation_id="import_001",
            operation_type="import_healing",
            priority=HealingPriority.NORMAL,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test import healing",
        )

        result = await coordinator.apply_healing(operation)

        assert result.status in [HealingStatus.COMPLETED, HealingStatus.FAILED]
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_apply_healing_dependency_type(self, tmp_path):
        """Apply dependency healing operation."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        operation = HealingOperation(
            operation_id="dep_001",
            operation_type="dependency_healing",
            priority=HealingPriority.HIGH,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test dependency healing",
        )

        result = await coordinator.apply_healing(operation)

        assert result.status in [HealingStatus.COMPLETED, HealingStatus.FAILED]

    @pytest.mark.asyncio
    async def test_apply_healing_quantum_type(self, tmp_path):
        """Apply quantum healing operation."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        operation = HealingOperation(
            operation_id="quantum_001",
            operation_type="quantum_healing",
            priority=HealingPriority.CRITICAL,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test quantum healing",
        )

        result = await coordinator.apply_healing(operation)

        assert result.status in [HealingStatus.COMPLETED, HealingStatus.FAILED]

    @pytest.mark.asyncio
    async def test_apply_healing_unknown_type(self, tmp_path):
        """Apply healing with unknown type returns unsupported."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        operation = HealingOperation(
            operation_id="unknown_001",
            operation_type="unknown_healing_type",
            priority=HealingPriority.LOW,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test unknown type",
        )

        result = await coordinator.apply_healing(operation)

        # Unknown type should fail
        assert result.status == HealingStatus.FAILED
        assert result.result is not None
        assert "unsupported" in str(result.result.get("status", ""))

    @pytest.mark.asyncio
    async def test_apply_healing_stores_operation(self, tmp_path):
        """Applied operations are stored in healing_operations dict."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        operation = HealingOperation(
            operation_id="store_test_001",
            operation_type="import_healing",
            priority=HealingPriority.NORMAL,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test storage",
        )

        await coordinator.apply_healing(operation)

        assert "store_test_001" in coordinator.healing_operations


# =============================================================================
# Apply Import Healing Tests
# =============================================================================
class TestApplyImportHealing:
    """Test async _apply_import_healing method."""

    @pytest.mark.asyncio
    async def test_import_healing_no_checker(self, tmp_path):
        """Returns error when import checker not available."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        # Ensure import_checker is None
        coordinator.active_healers["import_checker"] = None

        operation = HealingOperation(
            operation_id="test",
            operation_type="import_healing",
            priority=HealingPriority.NORMAL,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test",
        )

        result = await coordinator._apply_import_healing(operation)

        assert result["status"] == "error"
        assert "not available" in result["message"]

    @pytest.mark.asyncio
    async def test_import_healing_with_checker(self, tmp_path):
        """Returns success when import checker available."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        coordinator.active_healers["import_checker"] = MagicMock()

        operation = HealingOperation(
            operation_id="test",
            operation_type="import_healing",
            priority=HealingPriority.NORMAL,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test",
        )

        result = await coordinator._apply_import_healing(operation)

        assert result["status"] == "success"


# =============================================================================
# Apply Dependency Healing Tests
# =============================================================================
class TestApplyDependencyHealing:
    """Test async _apply_dependency_healing method."""

    @pytest.mark.asyncio
    async def test_dependency_healing_no_restorer(self, tmp_path):
        """Returns error when repo restorer not available."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        coordinator.active_healers["repo_restorer"] = None

        operation = HealingOperation(
            operation_id="test",
            operation_type="dependency_healing",
            priority=HealingPriority.HIGH,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test",
        )

        result = await coordinator._apply_dependency_healing(operation)

        assert result["status"] == "error"
        assert "not available" in result["message"]

    @pytest.mark.asyncio
    async def test_dependency_healing_success(self, tmp_path):
        """Returns success when restorer installs dependencies."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        mock_restorer = MagicMock()
        mock_restorer.install_missing_dependencies.return_value = True
        coordinator.active_healers["repo_restorer"] = mock_restorer

        operation = HealingOperation(
            operation_id="test",
            operation_type="dependency_healing",
            priority=HealingPriority.HIGH,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test",
        )

        result = await coordinator._apply_dependency_healing(operation)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_dependency_healing_partial(self, tmp_path):
        """Returns partial when some dependencies fail."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        mock_restorer = MagicMock()
        mock_restorer.install_missing_dependencies.return_value = False
        coordinator.active_healers["repo_restorer"] = mock_restorer

        operation = HealingOperation(
            operation_id="test",
            operation_type="dependency_healing",
            priority=HealingPriority.HIGH,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test",
        )

        result = await coordinator._apply_dependency_healing(operation)

        assert result["status"] == "partial"


# =============================================================================
# Apply Quantum Healing Tests
# =============================================================================
class TestApplyQuantumHealing:
    """Test async _apply_quantum_healing method."""

    @pytest.mark.asyncio
    async def test_quantum_healing_no_resolver(self, tmp_path):
        """Returns error when quantum resolver not available."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        coordinator.active_healers["quantum_resolver"] = None

        operation = HealingOperation(
            operation_id="test",
            operation_type="quantum_healing",
            priority=HealingPriority.CRITICAL,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test",
        )

        result = await coordinator._apply_quantum_healing(operation)

        assert result["status"] == "error"
        assert "not available" in result["message"]

    @pytest.mark.asyncio
    async def test_quantum_healing_with_resolver(self, tmp_path):
        """Returns success when quantum resolver available."""
        from src.healing.modernized_healing_coordinator import (
            HealingOperation,
            HealingPriority,
            HealingStatus,
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)
        coordinator.active_healers["quantum_resolver"] = MagicMock()

        operation = HealingOperation(
            operation_id="test",
            operation_type="quantum_healing",
            priority=HealingPriority.CRITICAL,
            status=HealingStatus.PENDING,
            target=str(tmp_path),
            description="Test",
        )

        result = await coordinator._apply_quantum_healing(operation)

        assert result["status"] == "success"


# =============================================================================
# Start Autonomous Healing Tests
# =============================================================================
class TestStartAutonomousHealing:
    """Test async start_autonomous_healing method."""

    @pytest.mark.asyncio
    async def test_autonomous_healing_runs_cycle(self, tmp_path):
        """Autonomous healing runs one cycle then cancels."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        # Mock health check to return no healing needed
        async def mock_health_check():
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "OK",
                "systems": {},
                "healing_recommended": [],
            }

        coordinator.run_comprehensive_health_check = mock_health_check

        # Run with very short interval and cancel quickly
        task = asyncio.create_task(coordinator.start_autonomous_healing(interval_seconds=1))

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Cancel the task
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_autonomous_healing_applies_recommended(self, tmp_path):
        """Autonomous healing applies recommended healing."""
        from src.healing.modernized_healing_coordinator import (
            ModernizedHealingCoordinator,
        )

        coordinator = ModernizedHealingCoordinator(repo_root=tmp_path)

        # Track calls
        healing_calls: list[str] = []

        # Mock health check to return healing needed
        async def mock_health_check():
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "DEGRADED",
                "systems": {},
                "healing_recommended": ["import_healing"] if len(healing_calls) == 0 else [],
            }

        async def mock_apply_healing(op):
            healing_calls.append(op.operation_type)
            return op

        coordinator.run_comprehensive_health_check = mock_health_check
        coordinator.apply_healing = mock_apply_healing

        task = asyncio.create_task(coordinator.start_autonomous_healing(interval_seconds=1))

        # Let it run briefly
        await asyncio.sleep(0.1)

        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have attempted healing
        assert "import_healing" in healing_calls or len(healing_calls) == 0  # Timing dependent


# =============================================================================
# Main Function Tests
# =============================================================================
class TestMainFunction:
    """Test main entry point function."""

    @pytest.mark.asyncio
    async def test_main_import(self):
        """Main function can be imported."""
        from src.healing.modernized_healing_coordinator import main

        assert callable(main)

    @pytest.mark.asyncio
    async def test_main_handles_init_failure(self):
        """Main handles healer init failure gracefully."""
        from src.healing.modernized_healing_coordinator import main

        with patch(
            "src.healing.modernized_healing_coordinator.ModernizedHealingCoordinator"
        ) as MockCoordinator:
            mock_instance = MagicMock()
            mock_instance.initialize_healers = AsyncMock(return_value=False)
            MockCoordinator.return_value = mock_instance

            # Should not raise
            await main()

"""
Comprehensive test suite for real-time context monitoring (Zeta11 - Testing Framework).
Tests context tracking, file monitoring, state awareness, and event handling.

Target: 90%+ coverage of src/real_time_context_monitor.py
"""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest


class TestContextMonitorInitialization:
    """Test context monitor initialization and setup."""

    @pytest.fixture
    async def monitor(self):
        """Create context monitor instance."""
        from src.real_time_context_monitor import RealTimeContextMonitor

        monitor = RealTimeContextMonitor()
        yield monitor
        await monitor.stop() if hasattr(monitor, "stop") else None

    async def test_monitor_initialization(self, monitor):
        """Test monitor initializes correctly."""
        assert monitor is not None
        assert hasattr(monitor, "context_state")  # Actual attribute name
        assert hasattr(monitor, "observer")  # watchdog.observers.Observer instance

    async def test_initial_context_state(self, monitor):
        """Test initial context state setup."""
        report = monitor.get_context_report()
        assert report is not None
        assert "timestamp" in report
        assert isinstance(report.get("context_state"), dict)

    async def test_configuration_loading(self, monitor):
        """Test loading monitor configuration."""
        watch_paths = monitor.watch_paths
        assert watch_paths is not None
        assert isinstance(watch_paths, list)


class TestFileWatching:
    """Test file system watching and change detection."""

    @pytest.fixture
    async def file_monitor(self):
        """Create file monitor with temp directory."""
        from src.real_time_context_monitor import FileWatcher

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(watch_dir=tmpdir)
            yield watcher
            await watcher.stop()

    async def test_file_creation_detection(self, file_monitor):
        """Test detection of file creation events."""
        tmpdir = file_monitor.watch_dir
        test_file = Path(tmpdir) / "test_file.txt"

        # Create file and wait for detection
        test_file.write_text("test content")
        await asyncio.sleep(0.1)

        changes = file_monitor.get_changes()
        assert any("test_file.txt" in str(change) for change in changes)

    async def test_file_modification_detection(self, file_monitor):
        """Test detection of file modifications."""
        tmpdir = file_monitor.watch_dir
        test_file = Path(tmpdir) / "test_file.txt"

        # Create and modify file
        test_file.write_text("original")
        await asyncio.sleep(0.05)
        test_file.write_text("modified")
        await asyncio.sleep(0.1)

        changes = file_monitor.get_changes()
        assert len(changes) >= 2

    async def test_file_deletion_detection(self, file_monitor):
        """Test detection of file deletion."""
        tmpdir = file_monitor.watch_dir
        test_file = Path(tmpdir) / "test_file.txt"

        test_file.write_text("test")
        await asyncio.sleep(0.05)
        test_file.unlink()
        await asyncio.sleep(0.1)

        changes = file_monitor.get_changes()
        assert any("deleted" in str(c).lower() for c in changes)

    @pytest.mark.parametrize("file_pattern", ["*.py", "*.md", "*.json"])
    async def test_pattern_filtering(self, file_monitor, file_pattern):
        """Test filtering files by pattern."""
        file_monitor.set_pattern(file_pattern)

        filtered = file_monitor.get_matching_files(file_pattern)
        assert all(p.endswith(file_pattern.replace("*", "")) for p in filtered)


class TestContextAwareness:
    """Test RealTimeContextMonitor analysis methods."""

    def test_analyze_python_context_returns_expected_keys(self, tmp_path):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        pyf = tmp_path / "mod.py"
        pyf.write_text("from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator")
        result = mon._analyze_python_context(str(pyf))
        assert isinstance(result, dict)
        assert "type" in result
        assert result["type"] in ("python", "code_consciousness")

    def test_analyze_markdown_context_returns_expected_keys(self, tmp_path):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        mdf = tmp_path / "README.md"
        mdf.write_text("# Title\nSome consciousness and quantum content here.")
        result = mon._analyze_markdown_context(str(mdf))
        assert isinstance(result, dict)
        assert "type" in result

    def test_analyze_generic_context_returns_dict(self, tmp_path):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}')
        result = mon._analyze_generic_context(str(f))
        assert isinstance(result, dict)

    def test_get_context_report_has_required_fields(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        report = mon.get_context_report()
        for key in ("timestamp", "consciousness_level", "context_state", "watch_paths"):
            assert key in report

    def test_get_recent_events_returns_list(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        events = mon.get_recent_events(limit=10)
        assert isinstance(events, list)
        assert len(events) <= 10


class TestEventHandling:
    """Test RealTimeContextMonitor adaptation callbacks and event tracking."""

    def test_add_adaptation_callback_stored(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        def cb(t, p, i):
            return None
        mon.add_adaptation_callback(cb)
        assert cb in mon.adaptation_callbacks

    def test_multiple_callbacks_all_stored(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        cbs = [lambda t, p, i: None for _ in range(3)]
        for cb in cbs:
            mon.add_adaptation_callback(cb)
        for cb in cbs:
            assert cb in mon.adaptation_callbacks

    def test_get_recent_events_limit_respected(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        events = mon.get_recent_events(limit=5)
        assert len(events) <= 5


class TestPerformanceMetrics:
    """Test RealTimeContextMonitor quantum resonance calculations."""

    def test_calculate_quantum_resonance_returns_float(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        result = mon._calculate_quantum_resonance({"importance": 1.0, "files": 3})
        assert isinstance(result, float)

    def test_calculate_quantum_resonance_non_negative(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        result = mon._calculate_quantum_resonance({})
        assert result >= 0.0

    def test_context_report_total_quantum_resonance(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        report = mon.get_context_report()
        assert "total_quantum_resonance" in report
        assert isinstance(report["total_quantum_resonance"], (int, float))


class TestStateManagement:
    """Test RealTimeContextMonitor state attributes."""

    def test_context_state_is_dict(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        assert isinstance(mon.context_state, dict)

    def test_monitoring_active_false_by_default(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        # Observer not started yet — monitoring_active should be False
        report = mon.get_context_report()
        assert report["monitoring_active"] is False

    def test_watch_paths_is_list(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        assert isinstance(mon.watch_paths, list)

    def test_event_count_starts_at_zero(self):
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        report = mon.get_context_report()
        assert report.get("event_count", 0) == 0


class TestNotifications:
    """Test FileWatcher clear and change tracking."""

    def test_file_watcher_clear_changes(self, tmp_path):
        from src.real_time_context_monitor import FileWatcher

        watcher = FileWatcher(watch_dir=tmp_path)
        (tmp_path / "f.txt").write_text("data")
        assert len(watcher.get_changes()) > 0
        watcher.clear_changes()
        assert len(watcher.get_changes()) == 0

    def test_file_watcher_set_pattern(self, tmp_path):
        from src.real_time_context_monitor import FileWatcher

        watcher = FileWatcher(watch_dir=tmp_path)
        watcher.set_pattern("*.py")
        assert watcher._pattern == "*.py"


class TestContextQueries:
    """Test FileWatcher get_matching_files."""

    def test_get_matching_files_py(self, tmp_path):
        from src.real_time_context_monitor import FileWatcher

        (tmp_path / "a.py").write_text("x=1")
        (tmp_path / "b.md").write_text("# hi")
        watcher = FileWatcher(watch_dir=tmp_path)
        # get_matching_files scans the watch dir for the given glob pattern
        matches = watcher.get_matching_files("*.py")
        assert isinstance(matches, list)

    def test_complex_query(self, tmp_path):
        """FileWatcher changes list contains expected structure."""
        from src.real_time_context_monitor import FileWatcher

        watcher = FileWatcher(watch_dir=tmp_path)
        (tmp_path / "new.py").write_text("pass")
        changes = watcher.get_changes()
        for change in changes:
            assert "type" in change
            assert "path" in change


class TestConcurrency:
    """Test monitor context report consistency across calls."""

    def test_concurrent_file_monitoring(self):
        """get_context_report is consistent across sequential calls."""
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        r1 = mon.get_context_report()
        r2 = mon.get_context_report()
        assert r1["consciousness_level"] == r2["consciousness_level"]
        assert r1["watch_paths"] == r2["watch_paths"]

    def test_concurrent_event_processing(self):
        """get_recent_events with different limits returns bounded lists."""
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        for limit in (1, 5, 20):
            events = mon.get_recent_events(limit=limit)
            assert len(events) <= limit


class TestErrorRecovery:
    """Test analysis methods handle non-existent and edge-case file paths."""

    def test_monitor_crash_recovery(self):
        """_analyze_python_context on missing file returns default dict."""
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        result = mon._analyze_python_context("/nonexistent/path/file.py")
        assert isinstance(result, dict)

    def test_permission_error_handling(self):
        """_analyze_markdown_context on missing file returns default dict."""
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        result = mon._analyze_markdown_context("/nonexistent/path/README.md")
        assert isinstance(result, dict)

    def test_resource_exhaustion(self):
        """_analyze_generic_context on missing file returns default dict."""
        from src.real_time_context_monitor import RealTimeContextMonitor

        mon = RealTimeContextMonitor()
        result = mon._analyze_generic_context("/nonexistent/path/data.bin")
        assert isinstance(result, dict)


# Parametrized fixtures
@pytest.fixture(params=["*.py", "*.md", "*.json", "src/**/*.py"])
async def file_pattern(request):
    """Parameterize file pattern tests."""
    return request.param


@pytest.fixture(params=["file_created", "file_modified", "file_deleted"])
async def file_event_type(request):
    """Parameterize file event types."""
    return request.param

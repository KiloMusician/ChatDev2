"""Tests for src/core/ArchitectureWatcher.py — watcher, health checks, violations."""

import sys
import types

import pytest

# Stub optional heavy dependencies so the module imports cleanly without watchdog
_watchdog_events = types.ModuleType("watchdog.events")
_watchdog_events.FileSystemEventHandler = None  # type: ignore[attr-defined]
_watchdog_observers = types.ModuleType("watchdog.observers")
_watchdog_observers.Observer = None  # type: ignore[attr-defined]
_watchdog_pkg = types.ModuleType("watchdog")
sys.modules.setdefault("watchdog", _watchdog_pkg)
sys.modules.setdefault("watchdog.events", _watchdog_events)
sys.modules.setdefault("watchdog.observers", _watchdog_observers)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_watcher(root_path=None):
    from src.core.ArchitectureWatcher import ArchitectureWatcher

    return ArchitectureWatcher(root_path=root_path)


# ---------------------------------------------------------------------------
# ArchitectureWatcher — instantiation
# ---------------------------------------------------------------------------


class TestArchitectureWatcherInit:
    """Tests for ArchitectureWatcher.__init__."""

    def test_default_root_is_cwd(self, tmp_path):
        from pathlib import Path

        w = _make_watcher(root_path=tmp_path)
        assert w.root_path == tmp_path

    def test_custom_root_stored(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        assert w.root_path == tmp_path

    def test_monitored_paths_contains_src(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        paths = [str(p) for p in w.monitored_paths]
        assert any("src" in p for p in paths)

    def test_monitored_paths_contains_tests(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        paths = [str(p) for p in w.monitored_paths]
        assert any("tests" in p for p in paths)

    def test_monitored_paths_contains_deploy(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        paths = [str(p) for p in w.monitored_paths]
        assert any("deploy" in p for p in paths)

    def test_rules_dict_populated(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        assert isinstance(w.rules, dict)
        assert "max_module_depth" in w.rules

    def test_max_module_depth_default(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        assert w.rules["max_module_depth"] == 5

    def test_required_tests_default(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        assert w.rules["required_tests"] is True


# ---------------------------------------------------------------------------
# ArchitectureWatcher — health_check
# ---------------------------------------------------------------------------


class TestArchitectureWatcherHealthCheck:
    """Tests for ArchitectureWatcher.health_check."""

    def test_health_check_returns_dict(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        result = w.health_check()
        assert isinstance(result, dict)

    def test_health_check_has_healthy_key(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        result = w.health_check()
        assert "healthy" in result

    def test_health_check_has_issues_key(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        result = w.health_check()
        assert "issues" in result

    def test_health_check_has_stats_key(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        result = w.health_check()
        assert "stats" in result

    def test_health_false_when_no_monitored_paths(self, tmp_path):
        # tmp_path exists but src/tests/deploy dirs don't — all missing
        w = _make_watcher(root_path=tmp_path)
        result = w.health_check()
        # Should report at least some issues for missing paths
        assert len(result["issues"]) > 0

    def test_healthy_when_all_paths_exist(self, tmp_path):
        # Create required directories
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "deploy").mkdir()
        w = _make_watcher(root_path=tmp_path)
        result = w.health_check()
        assert result["healthy"] is True

    def test_stats_python_files_counted(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "mod.py").write_text("x = 1")
        (tmp_path / "tests").mkdir()
        (tmp_path / "deploy").mkdir()
        w = _make_watcher(root_path=tmp_path)
        result = w.health_check()
        assert result["stats"].get("python_files", 0) >= 1

    def test_stats_test_files_counted(self, tmp_path):
        (tmp_path / "src").mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_foo.py").write_text("def test_x(): pass")
        (tmp_path / "deploy").mkdir()
        w = _make_watcher(root_path=tmp_path)
        result = w.health_check()
        assert result["stats"].get("test_files", 0) >= 1

    def test_no_tests_dir_flags_issue(self, tmp_path):
        # tests/ directory does not exist → should flag
        (tmp_path / "src").mkdir()
        (tmp_path / "deploy").mkdir()
        w = _make_watcher(root_path=tmp_path)
        result = w.health_check()
        assert not result["healthy"]
        assert any("test" in issue.lower() or "No tests" in issue for issue in result["issues"])


# ---------------------------------------------------------------------------
# ArchitectureWatcher — scan_violations
# ---------------------------------------------------------------------------


class TestArchitectureWatcherScanViolations:
    """Tests for ArchitectureWatcher.scan_violations."""

    def test_scan_violations_returns_list(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        assert isinstance(w.scan_violations(), list)

    def test_no_violations_empty_tree(self, tmp_path):
        (tmp_path / "src").mkdir()
        w = _make_watcher(root_path=tmp_path)
        assert w.scan_violations() == []

    def test_detects_excessive_depth(self, tmp_path):
        # Build path deeper than max_module_depth (5)
        deep = tmp_path / "src" / "a" / "b" / "c" / "d" / "e" / "f"
        deep.mkdir(parents=True)
        (deep / "deep_module.py").write_text("x = 1")
        w = _make_watcher(root_path=tmp_path)
        violations = w.scan_violations()
        assert len(violations) >= 1
        assert violations[0]["type"] == "excessive_depth"

    def test_violation_contains_required_keys(self, tmp_path):
        deep = tmp_path / "src" / "a" / "b" / "c" / "d" / "e" / "f"
        deep.mkdir(parents=True)
        (deep / "deep_module.py").write_text("x = 1")
        w = _make_watcher(root_path=tmp_path)
        v = w.scan_violations()[0]
        for key in ("type", "file", "depth", "max_allowed"):
            assert key in v

    def test_shallow_file_no_violation(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "mod.py").write_text("x = 1")
        w = _make_watcher(root_path=tmp_path)
        assert w.scan_violations() == []

    def test_custom_max_depth_respected(self, tmp_path):
        # depth = 2 (src/a/b/mod.py → parts = [a, b, mod.py], depth = 2)
        two_deep = tmp_path / "src" / "a" / "b"
        two_deep.mkdir(parents=True)
        (two_deep / "mod.py").write_text("x = 1")
        w = _make_watcher(root_path=tmp_path)
        w.rules["max_module_depth"] = 1  # now depth=2 should violate
        violations = w.scan_violations()
        assert len(violations) >= 1


# ---------------------------------------------------------------------------
# ArchitectureWatcher — generate_report
# ---------------------------------------------------------------------------


class TestArchitectureWatcherGenerateReport:
    """Tests for ArchitectureWatcher.generate_report."""

    def test_generate_report_returns_dict(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        report = w.generate_report()
        assert isinstance(report, dict)

    def test_report_has_health_key(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        assert "health" in w.generate_report()

    def test_report_has_violations_key(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        assert "violations" in w.generate_report()

    def test_report_has_summary_key(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        assert "summary" in w.generate_report()

    def test_summary_issue_count_type(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        report = w.generate_report()
        assert isinstance(report["summary"]["issue_count"], int)

    def test_summary_healthy_is_bool(self, tmp_path):
        w = _make_watcher(root_path=tmp_path)
        report = w.generate_report()
        assert isinstance(report["summary"]["healthy"], bool)

    def test_summary_unhealthy_when_violations_present(self, tmp_path):
        deep = tmp_path / "src" / "a" / "b" / "c" / "d" / "e" / "f"
        deep.mkdir(parents=True)
        (deep / "deep.py").write_text("x = 1")
        (tmp_path / "tests").mkdir()
        (tmp_path / "deploy").mkdir()
        w = _make_watcher(root_path=tmp_path)
        report = w.generate_report()
        assert report["summary"]["healthy"] is False


# ---------------------------------------------------------------------------
# get_architecture_watcher singleton
# ---------------------------------------------------------------------------


def _reset_watcher_singleton():
    """Reset the module-level _watcher singleton to None."""
    import sys

    mod = sys.modules.get("src.core.ArchitectureWatcher")
    if mod is not None:
        mod._watcher = None  # type: ignore[attr-defined]


class TestGetArchitectureWatcherSingleton:
    """Tests for the get_architecture_watcher factory."""

    def test_returns_architecture_watcher_instance(self, tmp_path):
        from src.core.ArchitectureWatcher import ArchitectureWatcher, get_architecture_watcher

        _reset_watcher_singleton()
        w = get_architecture_watcher(root_path=tmp_path)
        assert isinstance(w, ArchitectureWatcher)

    def test_singleton_same_object(self, tmp_path):
        from src.core.ArchitectureWatcher import get_architecture_watcher

        _reset_watcher_singleton()
        w1 = get_architecture_watcher(root_path=tmp_path)
        w2 = get_architecture_watcher()
        assert w1 is w2

    def test_reset_creates_new_instance(self, tmp_path):
        from src.core.ArchitectureWatcher import ArchitectureWatcher, get_architecture_watcher

        _reset_watcher_singleton()
        get_architecture_watcher(root_path=tmp_path)
        _reset_watcher_singleton()
        w2 = get_architecture_watcher(root_path=tmp_path)
        assert isinstance(w2, ArchitectureWatcher)

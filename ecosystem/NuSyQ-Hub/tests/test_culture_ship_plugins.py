"""Tests for the Culture Ship plugin system.

Covers:
- Plugin registry: get_all_plugins(), get_plugin(), ordering
- BlackFormatterPlugin: analyze, fix, error handling
- RuffFixerPlugin: analyze, fix, _count_fixable, error handling
- MypyCheckerPlugin: analyze, fix, _parse_output, _top_codes, error handling
- PytestRunnerPlugin: analyze, fix, fallback, error handling
- SemgrepScannerPlugin: analyze (semgrep not found), fix dry_run
"""

from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    """Build a mock CompletedProcess."""
    cp: subprocess.CompletedProcess[str] = subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )
    return cp


# ===========================================================================
# Plugin registry
# ===========================================================================


class TestPluginRegistry:
    def test_get_all_plugins_returns_list(self) -> None:
        from src.culture_ship.plugins import get_all_plugins

        plugins = get_all_plugins()
        assert isinstance(plugins, list)

    def test_get_all_plugins_count(self) -> None:
        from src.culture_ship.plugins import get_all_plugins

        plugins = get_all_plugins()
        assert len(plugins) == 5

    def test_get_all_plugins_order(self) -> None:
        """Audit order must be: format → lint → type-check → test → security."""
        from src.culture_ship.plugins import get_all_plugins

        names = [p.name for p in get_all_plugins()]
        assert names == [
            "black_formatter",
            "ruff_fixer",
            "mypy_checker",
            "pytest_runner",
            "semgrep_scanner",
        ]

    def test_get_plugin_found(self) -> None:
        from src.culture_ship.plugins import get_plugin

        plugin = get_plugin("black_formatter")
        assert plugin is not None
        assert plugin.name == "black_formatter"

    def test_get_plugin_not_found_returns_none(self) -> None:
        from src.culture_ship.plugins import get_plugin

        assert get_plugin("nonexistent_plugin") is None

    def test_get_plugin_ruff(self) -> None:
        from src.culture_ship.plugins import get_plugin

        plugin = get_plugin("ruff_fixer")
        assert plugin is not None
        assert plugin.name == "ruff_fixer"

    def test_get_plugin_mypy(self) -> None:
        from src.culture_ship.plugins import get_plugin

        plugin = get_plugin("mypy_checker")
        assert plugin is not None

    def test_get_plugin_pytest(self) -> None:
        from src.culture_ship.plugins import get_plugin

        plugin = get_plugin("pytest_runner")
        assert plugin is not None

    def test_get_plugin_semgrep(self) -> None:
        from src.culture_ship.plugins import get_plugin

        plugin = get_plugin("semgrep_scanner")
        assert plugin is not None

    def test_each_plugin_has_name_and_description(self) -> None:
        from src.culture_ship.plugins import get_all_plugins

        for plugin in get_all_plugins():
            assert hasattr(plugin, "name")
            assert isinstance(plugin.name, str)
            assert plugin.name
            assert hasattr(plugin, "description")
            assert isinstance(plugin.description, str)
            assert plugin.description

    def test_each_plugin_has_analyze_and_fix(self) -> None:
        from src.culture_ship.plugins import get_all_plugins

        for plugin in get_all_plugins():
            assert callable(getattr(plugin, "analyze", None))
            assert callable(getattr(plugin, "fix", None))

    def test_all_plugin_names_unique(self) -> None:
        from src.culture_ship.plugins import get_all_plugins

        names = [p.name for p in get_all_plugins()]
        assert len(names) == len(set(names))


# ===========================================================================
# BlackFormatterPlugin
# ===========================================================================


class TestBlackFormatterPlugin:
    def test_name_and_description(self) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        p = BlackFormatterPlugin()
        assert p.name == "black_formatter"
        assert "black" in p.description.lower()

    @patch("subprocess.run")
    def test_analyze_no_reformats(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        mock_run.return_value = _completed(stdout="All done! ✨ 🍰 ✨\n1 file left unchanged.", returncode=0)
        p = BlackFormatterPlugin()
        result = p.analyze(["src/"])
        assert result["plugin"] == "black_formatter"
        assert result["would_reformat"] == 0
        assert result["needs_formatting"] is False

    @patch("subprocess.run")
    def test_analyze_with_reformats(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        mock_run.return_value = _completed(
            stdout="would reformat src/foo.py\nwould reformat src/bar.py\n",
            returncode=1,
        )
        p = BlackFormatterPlugin()
        result = p.analyze(["src/"])
        assert result["would_reformat"] == 2
        assert result["needs_formatting"] is True

    @patch("subprocess.run")
    def test_analyze_reads_stderr_fallback(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        mock_run.return_value = _completed(stdout="", stderr="would reformat src/baz.py\n", returncode=1)
        p = BlackFormatterPlugin()
        result = p.analyze(["src/"])
        assert result["would_reformat"] == 1

    @patch("subprocess.run")
    def test_analyze_includes_targets_and_dry_run(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        mock_run.return_value = _completed()
        p = BlackFormatterPlugin()
        result = p.analyze(["a.py", "b.py"], dry_run=True)
        assert result["targets"] == ["a.py", "b.py"]
        assert result["dry_run"] is True

    @patch("subprocess.run")
    def test_analyze_file_not_found_error(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        mock_run.side_effect = FileNotFoundError("black not found")
        p = BlackFormatterPlugin()
        result = p.analyze(["src/"])
        assert "error" in result
        assert result["would_reformat"] == 0

    @patch("subprocess.run")
    def test_analyze_timeout_error(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["black"], timeout=10)
        p = BlackFormatterPlugin()
        result = p.analyze(["src/"])
        assert "error" in result

    @patch("subprocess.run")
    def test_fix_dry_run_returns_zero(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        p = BlackFormatterPlugin()
        result = p.fix({"needs_formatting": True, "targets": ["src/"]}, dry_run=True)
        mock_run.assert_not_called()
        assert result["formatted_files"] == 0
        assert result["success"] is True

    @patch("subprocess.run")
    def test_fix_skipped_when_not_needed(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        p = BlackFormatterPlugin()
        result = p.fix({"needs_formatting": False, "targets": ["src/"]})
        mock_run.assert_not_called()
        assert result["formatted_files"] == 0

    @patch("subprocess.run")
    def test_fix_applies_formatting(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        mock_run.return_value = _completed(
            stdout="reformatted src/foo.py\nreformatted src/bar.py\n",
            returncode=0,
        )
        p = BlackFormatterPlugin()
        result = p.fix({"needs_formatting": True, "targets": ["src/"]})
        assert result["formatted_files"] == 2
        assert result["success"] is True

    @patch("subprocess.run")
    def test_fix_empty_targets(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        p = BlackFormatterPlugin()
        result = p.fix({"needs_formatting": True, "targets": []})
        mock_run.assert_not_called()
        assert result["formatted_files"] == 0

    @patch("subprocess.run")
    def test_fix_failure_returncode(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import BlackFormatterPlugin

        mock_run.return_value = _completed(stdout="", returncode=123)
        p = BlackFormatterPlugin()
        result = p.fix({"needs_formatting": True, "targets": ["src/"]})
        assert result["success"] is False


# ===========================================================================
# RuffFixerPlugin
# ===========================================================================


class TestRuffFixerPlugin:
    def test_name_and_description(self) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        p = RuffFixerPlugin()
        assert p.name == "ruff_fixer"
        assert "ruff" in p.description.lower()

    @patch("subprocess.run")
    def test_analyze_no_issues(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        mock_run.return_value = _completed(stdout="[]", returncode=0)
        p = RuffFixerPlugin()
        result = p.analyze(["src/"])
        assert result["issues_found"] == 0
        assert result["fixable_issues"] == 0

    @patch("subprocess.run")
    def test_analyze_with_issues(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        issues = [
            {"filename": "src/a.py", "code": "E501", "message": "line too long"},
            {"filename": "src/a.py", "code": "F401", "message": "unused import"},
            {"filename": "src/b.py", "code": "E302", "message": "expected blank lines"},
        ]
        mock_run.return_value = _completed(stdout=json.dumps(issues), returncode=1)
        p = RuffFixerPlugin()
        result = p.analyze(["src/"])
        assert result["issues_found"] == 3
        assert result["fixable_issues"] == 3
        assert "src/a.py" in result["issues_by_file"]
        assert "src/b.py" in result["issues_by_file"]

    @patch("subprocess.run")
    def test_analyze_json_decode_error(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        mock_run.return_value = _completed(stdout="not-json", returncode=1)
        p = RuffFixerPlugin()
        result = p.analyze(["src/"])
        assert "error" in result
        assert result["issues_found"] == 0

    @patch("subprocess.run")
    def test_analyze_timeout(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["ruff"], timeout=120)
        p = RuffFixerPlugin()
        result = p.analyze(["src/"])
        assert "error" in result

    def test_count_fixable_e_and_f_codes(self) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        p = RuffFixerPlugin()
        issues = [
            {"code": "E501"},
            {"code": "F401"},
            {"code": "W291"},  # W prefix — not counted
            {"code": ""},
        ]
        assert p._count_fixable(issues) == 2

    def test_count_fixable_uses_message_id_fallback(self) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        p = RuffFixerPlugin()
        issues = [{"message_id": "F811"}]
        assert p._count_fixable(issues) == 1

    @patch("subprocess.run")
    def test_fix_dry_run(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        p = RuffFixerPlugin()
        result = p.fix({"fixable_issues": 5, "issues_by_file": {"src/a.py": []}}, dry_run=True)
        mock_run.assert_not_called()
        assert result["fixes_applied"] == 0

    @patch("subprocess.run")
    def test_fix_no_fixable_issues(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        p = RuffFixerPlugin()
        result = p.fix({"fixable_issues": 0, "issues_by_file": {}})
        mock_run.assert_not_called()
        assert result["fixes_applied"] == 0

    @patch("subprocess.run")
    def test_fix_applies_per_file(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        mock_run.return_value = _completed(returncode=0)
        p = RuffFixerPlugin()
        result = p.fix(
            {
                "fixable_issues": 2,
                "issues_by_file": {"src/a.py": [], "src/b.py": []},
            }
        )
        assert result["fixes_applied"] == 2
        assert set(result["files_modified"]) == {"src/a.py", "src/b.py"}

    @patch("subprocess.run")
    def test_fix_skips_none_file_path(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import RuffFixerPlugin

        mock_run.return_value = _completed(returncode=0)
        p = RuffFixerPlugin()
        p.fix({"fixable_issues": 1, "issues_by_file": {None: []}})
        # None key should be skipped
        assert mock_run.call_count == 0


# ===========================================================================
# MypyCheckerPlugin
# ===========================================================================


class TestMypyCheckerPlugin:
    def test_name_and_description(self) -> None:
        from src.culture_ship.plugins import MypyCheckerPlugin

        p = MypyCheckerPlugin()
        assert p.name == "mypy_checker"
        assert "mypy" in p.description.lower()

    @patch("subprocess.run")
    def test_analyze_no_errors(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import MypyCheckerPlugin

        mock_run.return_value = _completed(stdout="", returncode=0)
        p = MypyCheckerPlugin()
        result = p.analyze(["src/"])
        assert result["errors"] == 0
        assert result["warnings"] == 0
        assert result["notes"] == 0

    @patch("subprocess.run")
    def test_analyze_parses_errors(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import MypyCheckerPlugin

        mypy_output = (
            "src/foo.py:10:5: error: Incompatible types [assignment]\n"
            "src/bar.py:3: warning: Some warning\n"
            "src/baz.py:1: note: Revealed type is 'int'\n"
        )
        mock_run.return_value = _completed(stdout=mypy_output, returncode=1)
        p = MypyCheckerPlugin()
        result = p.analyze(["src/"])
        assert result["errors"] == 1
        assert result["warnings"] == 1
        assert result["notes"] == 1
        assert result["exit_code"] == 1

    @patch("subprocess.run")
    def test_analyze_caps_error_details_at_100(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import MypyCheckerPlugin

        lines = "\n".join(
            f"src/f.py:{i}: error: err [assignment]" for i in range(1, 150)
        )
        mock_run.return_value = _completed(stdout=lines, returncode=1)
        p = MypyCheckerPlugin()
        result = p.analyze(["src/"])
        assert len(result["error_details"]) <= 100

    @patch("subprocess.run")
    def test_analyze_timeout(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import MypyCheckerPlugin

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["mypy"], timeout=120)
        p = MypyCheckerPlugin()
        result = p.analyze(["src/"])
        assert "error" in result
        assert result["errors"] == 0

    def test_fix_dry_run(self) -> None:
        from src.culture_ship.plugins import MypyCheckerPlugin

        p = MypyCheckerPlugin()
        result = p.fix({"errors": 5, "error_details": []}, dry_run=True)
        assert result["fixes_applied"] == 0
        assert result["files_modified"] == []

    def test_fix_returns_report(self) -> None:
        from src.culture_ship.plugins import MypyCheckerPlugin

        p = MypyCheckerPlugin()
        details: list[dict[str, Any]] = [
            {"file": "src/a.py", "line": 1, "severity": "error", "message": "x", "code": "assignment"},
            {"file": "src/a.py", "line": 2, "severity": "error", "message": "y", "code": "assignment"},
            {"file": "src/b.py", "line": 5, "severity": "error", "message": "z", "code": "arg-type"},
        ]
        result = p.fix({"errors": 3, "error_details": details})
        assert result["fixes_applied"] == 0
        assert set(result["files_with_errors"]) == {"src/a.py", "src/b.py"}
        assert result["errors_by_file"]["src/a.py"] == 2
        assert result["errors_by_file"]["src/b.py"] == 1
        assert "note" in result

    def test_top_codes_aggregation(self) -> None:
        from src.culture_ship.plugins import MypyCheckerPlugin

        p = MypyCheckerPlugin()
        errors = [
            {"code": "assignment"},
            {"code": "assignment"},
            {"code": "arg-type"},
            {"code": ""},
        ]
        top = p._top_codes(errors)
        assert top[0]["code"] == "assignment"
        assert top[0]["count"] == 2

    def test_parse_output_unmatched_lines_ignored(self) -> None:
        from src.culture_ship.plugins import MypyCheckerPlugin

        p = MypyCheckerPlugin()
        errs, warns, notes = p._parse_output("Success: no issues found\nSome random line\n")
        assert errs == []
        assert warns == []
        assert notes == []


# ===========================================================================
# PytestRunnerPlugin
# ===========================================================================


class TestPytestRunnerPlugin:
    def test_name_and_description(self) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        p = PytestRunnerPlugin()
        assert p.name == "pytest_runner"
        assert "pytest" in p.description.lower()

    @patch("subprocess.run")
    def test_analyze_discovers_tests(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        collect_output = (
            "tests/test_foo.py::test_one\n"
            "tests/test_foo.py::test_two\n"
            "tests/test_bar.py::test_three\n"
        )
        mock_run.return_value = _completed(stdout=collect_output, returncode=0)
        p = PytestRunnerPlugin()
        result = p.analyze(["tests/"])
        assert result["tests_discovered"] == 3
        assert len(result["test_ids"]) == 3

    @patch("subprocess.run")
    def test_analyze_caps_test_ids_at_50(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        lines = "\n".join(f"tests/test_x.py::test_{i}" for i in range(80))
        mock_run.return_value = _completed(stdout=lines, returncode=0)
        p = PytestRunnerPlugin()
        result = p.analyze(["tests/"])
        assert result["tests_discovered"] == 80
        assert len(result["test_ids"]) == 50

    @patch("subprocess.run")
    def test_analyze_timeout(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["pytest"], timeout=60)
        p = PytestRunnerPlugin()
        result = p.analyze(["tests/"])
        assert "error" in result
        assert result["tests_discovered"] == 0

    def test_fix_dry_run(self) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        p = PytestRunnerPlugin()
        result = p.fix({"targets": ["tests/"]}, dry_run=True)
        assert result["fixes_applied"] == 0
        assert result["files_modified"] == []

    @patch("subprocess.run")
    def test_fix_parses_passed_count(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        summary = "42 passed, 3 failed, 1 error, 2 skipped in 5.00s"
        mock_run.return_value = _completed(stdout=summary, returncode=1)
        p = PytestRunnerPlugin()
        result = p.fix({"targets": ["tests/"]})
        assert result["passed"] == 42
        assert result["failed"] == 3
        assert result["errors"] == 1
        assert result["skipped"] == 2

    @patch("subprocess.run")
    def test_fix_uses_fallback_on_unrecognized_args(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        # First call returns "unrecognized arguments" → triggers fallback
        first = _completed(stderr="unrecognized arguments: --json-report", returncode=1)
        second = _completed(stdout="5 passed in 1s", returncode=0)
        mock_run.side_effect = [first, second]
        p = PytestRunnerPlugin()
        result = p.fix({"targets": ["tests/"]})
        assert mock_run.call_count == 2
        assert result["passed"] == 5

    @patch("subprocess.run")
    def test_fix_uses_fallback_on_returncode_4(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        first = _completed(stdout="", returncode=4)
        second = _completed(stdout="3 passed in 0.5s", returncode=0)
        mock_run.side_effect = [first, second]
        p = PytestRunnerPlugin()
        p.fix({"targets": ["tests/"]})
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_fix_timeout_returns_error(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["pytest"], timeout=300)
        p = PytestRunnerPlugin()
        result = p.fix({"targets": ["tests/"]})
        assert "error" in result
        assert "timed out" in result["error"]

    @patch("subprocess.run")
    def test_fix_default_target_when_missing(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        mock_run.return_value = _completed(stdout="0 passed in 0s", returncode=0)
        p = PytestRunnerPlugin()
        # analysis dict has no "targets" key
        p.fix({})
        called_cmd = mock_run.call_args[0][0]
        # default target "." should appear in command
        assert "." in called_cmd

    @patch("subprocess.run")
    def test_fix_includes_exit_code(self, mock_run: MagicMock) -> None:
        from src.culture_ship.plugins import PytestRunnerPlugin

        mock_run.return_value = _completed(stdout="1 failed in 0.2s", returncode=1)
        p = PytestRunnerPlugin()
        result = p.fix({"targets": ["tests/"]})
        assert result["exit_code"] == 1


# ===========================================================================
# SemgrepScannerPlugin
# ===========================================================================


class TestSemgrepScannerPlugin:
    def test_name_and_description(self) -> None:
        from src.culture_ship.plugins import SemgrepScannerPlugin

        p = SemgrepScannerPlugin()
        assert p.name == "semgrep_scanner"
        assert "semgrep" in p.description.lower()

    @patch("shutil.which", return_value=None)
    def test_analyze_semgrep_not_in_path(self, mock_which: MagicMock) -> None:
        from src.culture_ship.plugins import SemgrepScannerPlugin

        p = SemgrepScannerPlugin()
        result = p.analyze(["src/"])
        assert "error" in result
        assert result["findings"] == 0

    @patch("shutil.which", return_value=None)
    def test_fix_semgrep_not_in_path_returns_zero(self, mock_which: MagicMock) -> None:
        from src.culture_ship.plugins import SemgrepScannerPlugin

        p = SemgrepScannerPlugin()
        result = p.fix({"targets": ["src/"], "findings": 3})
        assert result["fixes_applied"] == 0
        assert result["files_modified"] == []

    def test_fix_dry_run_returns_zero(self) -> None:
        from src.culture_ship.plugins import SemgrepScannerPlugin

        with patch("shutil.which", return_value="/usr/bin/semgrep"):
            p = SemgrepScannerPlugin()
            result = p.fix({"targets": ["src/"], "findings": 5}, dry_run=True)
        assert result["fixes_applied"] == 0
        assert result["files_modified"] == []

    def test_custom_config_stored(self) -> None:
        from src.culture_ship.plugins import SemgrepScannerPlugin

        p = SemgrepScannerPlugin(config="p/python")
        assert p._config == "p/python"

"""Tests for classify_python_files.py.

Tests the Python file classification utilities.
"""

from pathlib import Path

from src.utils.classify_python_files import (
    EXCLUDE_DIRS,
    classify_file,
    print_report,
    scan_repo,
    should_exclude,
)


class TestExcludeDirs:
    """Tests for EXCLUDE_DIRS constant."""

    def test_is_set(self):
        """EXCLUDE_DIRS is a set."""
        assert isinstance(EXCLUDE_DIRS, set)

    def test_contains_venv(self):
        """Contains virtual environment directories."""
        assert ".venv" in EXCLUDE_DIRS
        assert "venv" in EXCLUDE_DIRS

    def test_contains_pycache(self):
        """Contains __pycache__ directory."""
        assert "__pycache__" in EXCLUDE_DIRS

    def test_contains_git(self):
        """Contains .git directory."""
        assert ".git" in EXCLUDE_DIRS

    def test_contains_cache_dirs(self):
        """Contains cache directories."""
        assert ".mypy_cache" in EXCLUDE_DIRS
        assert ".pytest_cache" in EXCLUDE_DIRS


class TestShouldExclude:
    """Tests for should_exclude function."""

    def test_excludes_venv(self):
        """Excludes .venv directory."""
        assert should_exclude(".venv/lib/file.py") is True

    def test_excludes_pycache(self):
        """Excludes __pycache__ directory."""
        assert should_exclude("src/__pycache__/module.pyc") is True

    def test_excludes_git(self):
        """Excludes .git directory."""
        assert should_exclude(".git/hooks/pre-commit") is True

    def test_allows_normal_paths(self):
        """Allows normal paths."""
        assert should_exclude("src/utils/helper.py") is False

    def test_allows_root_file(self):
        """Allows file in root."""
        assert should_exclude("main.py") is False

    def test_accepts_path_object(self):
        """Accepts Path object."""
        assert should_exclude(Path(".venv/test.py")) is True

    def test_accepts_string(self):
        """Accepts string path."""
        assert should_exclude("normal/path/file.py") is False


class TestClassifyFile:
    """Tests for classify_file function."""

    def test_classifies_test_file_by_name(self, tmp_path):
        """Classifies test_ prefix files as Test."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text("def test_foo(): pass")
        assert classify_file(test_file) == "Test"

    def test_classifies_test_file_by_directory(self, tmp_path):
        """Classifies files in tests directory as Test."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "example.py"
        test_file.write_text("def check(): pass")
        assert classify_file(test_file) == "Test"

    def test_classifies_config_file_by_name(self, tmp_path):
        """Classifies config in filename as Config."""
        config_file = tmp_path / "app_config.py"
        config_file.write_text("DEBUG = True")
        assert classify_file(config_file) == "Config"

    def test_classifies_settings_file(self, tmp_path):
        """Classifies settings files as Config."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text("PORT = 8080")
        assert classify_file(settings_file) == "Config"

    def test_classifies_setup_file(self, tmp_path):
        """Classifies setup files as Config."""
        setup_file = tmp_path / "setup.py"
        setup_file.write_text("from setuptools import setup")
        assert classify_file(setup_file) == "Config"

    def test_classifies_config_directory(self, tmp_path):
        """Classifies files in config directory as Config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "main.py"
        config_file.write_text("value = 1")
        assert classify_file(config_file) == "Config"

    def test_classifies_tool_by_directory(self, tmp_path):
        """Classifies files in tools directory as Tool."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        tool_file = tools_dir / "helper.py"
        tool_file.write_text("pass")
        assert classify_file(tool_file) == "Tool"

    def test_classifies_scripts_directory(self, tmp_path):
        """Classifies files in scripts directory as Tool."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "run.py"
        script_file.write_text("pass")
        assert classify_file(script_file) == "Tool"

    def test_classifies_tool_by_name(self, tmp_path):
        """Classifies tool-like names as Tool."""
        tool_file = tmp_path / "file_manager.py"
        tool_file.write_text("pass")
        assert classify_file(tool_file) == "Tool"

    def test_classifies_cli_as_tool(self, tmp_path):
        """Classifies cli files as Tool."""
        cli_file = tmp_path / "cli.py"
        cli_file.write_text("pass")
        assert classify_file(cli_file) == "Tool"

    def test_classifies_script_with_main(self, tmp_path):
        """Classifies files with __main__ as Script."""
        script_file = tmp_path / "run.py"
        script_file.write_text('if __name__ == "__main__":\n    main()')
        assert classify_file(script_file) == "Script"

    def test_classifies_module_with_functions(self, tmp_path):
        """Classifies files with functions as Module."""
        module_file = tmp_path / "utils.py"
        module_file.write_text("def helper(x):\n    return x + 1")
        assert classify_file(module_file) == "Module"

    def test_classifies_module_with_classes(self, tmp_path):
        """Classifies files with classes as Module."""
        module_file = tmp_path / "models.py"
        module_file.write_text("class User(Model):\n    pass")
        assert classify_file(module_file) == "Module"

    def test_classifies_unknown_for_empty(self, tmp_path):
        """Classifies empty files as Unknown."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")
        assert classify_file(empty_file) == "Unknown"

    def test_handles_missing_file(self, tmp_path):
        """Returns Unknown for missing files."""
        missing = tmp_path / "nonexistent.py"
        assert classify_file(missing) == "Unknown"

    def test_handles_large_file(self, tmp_path):
        """Returns Unknown for large files (>1MB)."""
        large_file = tmp_path / "large.py"
        # Create file larger than 1MB
        large_file.write_text("x = 1\n" * 200_000)
        assert classify_file(large_file) == "Unknown"

    def test_priority_test_over_script(self, tmp_path):
        """Test classification takes priority over Script."""
        # File in tests with __main__
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "runner.py"
        test_file.write_text('if __name__ == "__main__": run()')
        assert classify_file(test_file) == "Test"

    def test_priority_config_over_module(self, tmp_path):
        """Config classification takes priority over Module."""
        config_file = tmp_path / "config.py"
        config_file.write_text("def load_config():\n    pass")
        assert classify_file(config_file) == "Config"


class TestScanRepo:
    """Tests for scan_repo function."""

    def test_returns_list(self, tmp_path):
        """Returns a list."""
        result = scan_repo(tmp_path)
        assert isinstance(result, list)

    def test_finds_python_files(self, tmp_path):
        """Finds .py files."""
        py_file = tmp_path / "module.py"
        py_file.write_text("x = 1")
        result = scan_repo(tmp_path)
        assert len(result) == 1
        assert result[0]["path"].endswith("module.py")

    def test_ignores_non_python(self, tmp_path):
        """Ignores non-Python files."""
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("readme")
        result = scan_repo(tmp_path)
        assert len(result) == 0

    def test_excludes_venv(self, tmp_path):
        """Excludes .venv directory."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        venv_file = venv_dir / "module.py"
        venv_file.write_text("pass")
        result = scan_repo(tmp_path)
        assert len(result) == 0

    def test_excludes_pycache(self, tmp_path):
        """Excludes __pycache__ directory."""
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        cache_file = cache_dir / "module.cpython-312.pyc"
        cache_file.write_bytes(b"compiled")
        result = scan_repo(tmp_path)
        assert len(result) == 0

    def test_includes_classification(self, tmp_path):
        """Includes classification in result."""
        py_file = tmp_path / "test_example.py"
        py_file.write_text("def test(): pass")
        result = scan_repo(tmp_path)
        assert result[0]["classification"] == "Test"

    def test_scans_subdirectories(self, tmp_path):
        """Scans subdirectories."""
        sub_dir = tmp_path / "src" / "utils"
        sub_dir.mkdir(parents=True)
        py_file = sub_dir / "helper.py"
        py_file.write_text("def help(): pass")
        result = scan_repo(tmp_path)
        assert len(result) == 1

    def test_result_dict_structure(self, tmp_path):
        """Result dicts have path and classification keys."""
        py_file = tmp_path / "file.py"
        py_file.write_text("pass")
        result = scan_repo(tmp_path)
        assert "path" in result[0]
        assert "classification" in result[0]


class TestPrintReport:
    """Tests for print_report function."""

    def test_creates_report_file(self, tmp_path):
        """Creates report file when export_path provided."""
        results = [{"path": "test.py", "classification": "Test"}]
        report_path = tmp_path / "report.md"
        print_report(results, export_path=str(report_path))
        assert report_path.exists()

    def test_report_contains_categories(self, tmp_path):
        """Report contains category headers."""
        results = [
            {"path": "test_foo.py", "classification": "Test"},
            {"path": "main.py", "classification": "Script"},
        ]
        report_path = tmp_path / "report.md"
        print_report(results, export_path=str(report_path))
        content = report_path.read_text()
        assert "--- TEST ---" in content
        assert "--- SCRIPT ---" in content

    def test_report_contains_paths(self, tmp_path):
        """Report contains file paths."""
        results = [{"path": "src/module.py", "classification": "Module"}]
        report_path = tmp_path / "report.md"
        print_report(results, export_path=str(report_path))
        content = report_path.read_text()
        assert "src/module.py" in content

    def test_no_export_doesnt_crash(self):
        """Doesn't crash when export_path is None."""
        results = [{"path": "file.py", "classification": "Unknown"}]
        # Should not raise
        print_report(results, export_path=None)

    def test_empty_results(self, tmp_path):
        """Handles empty results."""
        report_path = tmp_path / "empty_report.md"
        print_report([], export_path=str(report_path))
        assert report_path.exists()

    def test_report_has_title(self, tmp_path):
        """Report has title line."""
        report_path = tmp_path / "report.md"
        print_report([], export_path=str(report_path))
        content = report_path.read_text()
        assert "Classification Report" in content


class TestEdgeCases:
    """Edge case tests."""

    def test_classify_auditor_file(self, tmp_path):
        """Classifies auditor files as Tool."""
        file = tmp_path / "security_auditor.py"
        file.write_text("pass")
        assert classify_file(file) == "Tool"

    def test_classify_dashboard_file(self, tmp_path):
        """Classifies dashboard files as Tool."""
        file = tmp_path / "dashboard.py"
        file.write_text("pass")
        assert classify_file(file) == "Tool"

    def test_classify_export_import(self, tmp_path):
        """Classifies export/import files as Tool."""
        export_file = tmp_path / "data_export.py"
        export_file.write_text("pass")
        import_file = tmp_path / "data_import.py"
        import_file.write_text("pass")
        assert classify_file(export_file) == "Tool"
        assert classify_file(import_file) == "Tool"

    def test_nested_excluded_dir(self, tmp_path):
        """Excludes nested excluded directories."""
        nested = tmp_path / "src" / "__pycache__" / "module.cpython-312.pyc"
        nested.parent.mkdir(parents=True)
        nested.write_bytes(b"")
        assert should_exclude(nested) is True

    def test_path_object_in_classify(self, tmp_path):
        """classify_file accepts Path objects."""
        file = tmp_path / "module.py"
        file.write_text("class Foo(object): pass")  # Needs parens for Module detection
        result = classify_file(Path(file))
        assert result == "Module"

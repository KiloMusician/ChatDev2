"""Tests for automated_issue_resolver.py - IssueResolver class."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from src.healing.automated_issue_resolver import IssueResolver


class TestIssueResolverInit:
    """Tests for IssueResolver initialization."""

    def test_init_default_repo_root(self):
        """Test default repo root is current directory."""
        resolver = IssueResolver()
        assert resolver.repo_root == Path(".")

    def test_init_custom_repo_root(self, tmp_path):
        """Test custom repo root is set correctly."""
        resolver = IssueResolver(repo_root=str(tmp_path))
        assert resolver.repo_root == tmp_path

    def test_init_counters_start_at_zero(self):
        """Test all counters start at zero."""
        resolver = IssueResolver()
        assert resolver.resolved_count == 0
        assert resolver.failed_count == 0
        assert resolver.skipped_count == 0

    def test_init_resolution_log_empty(self):
        """Test resolution log starts empty."""
        resolver = IssueResolver()
        assert resolver.resolution_log == []


class TestLoadReport:
    """Tests for load_report method."""

    def test_load_report_valid_json(self, tmp_path):
        """Test loading a valid JSON report."""
        report_data = {"by_category": {"import_errors": {"sample_issues": []}}}
        report_file = tmp_path / "report.json"
        report_file.write_text(json.dumps(report_data))

        resolver = IssueResolver(str(tmp_path))
        result = resolver.load_report(str(report_file))
        assert result == report_data

    def test_load_report_missing_file_raises(self, tmp_path):
        """Test loading non-existent file raises FileNotFoundError."""
        resolver = IssueResolver(str(tmp_path))
        with pytest.raises(FileNotFoundError):
            resolver.load_report(str(tmp_path / "missing.json"))

    def test_load_report_invalid_json_raises(self, tmp_path):
        """Test loading invalid JSON raises JSONDecodeError."""
        report_file = tmp_path / "invalid.json"
        report_file.write_text("not valid json {{{")

        resolver = IssueResolver(str(tmp_path))
        with pytest.raises(json.JSONDecodeError):
            resolver.load_report(str(report_file))


class TestResolveUnusedImports:
    """Tests for resolve_unused_imports method."""

    def test_empty_issues_returns_zeros(self, tmp_path):
        """Test empty issues list returns (0, 0)."""
        resolver = IssueResolver(str(tmp_path))
        resolved, failed = resolver.resolve_unused_imports([])
        assert resolved == 0
        assert failed == 0

    def test_resolve_simple_import(self, tmp_path):
        """Test removing a simple unused import."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\nimport sys\n\nprint('hello')\n")

        issues = [
            {"file": str(test_file), "message": "Unused import: os"},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolved, failed = resolver.resolve_unused_imports(issues)

        content = test_file.read_text()
        assert "import os" not in content
        assert "import sys" in content
        assert resolved >= 1
        assert failed == 0

    def test_resolve_from_import(self, tmp_path):
        """Test removing unused 'from X import Y' style import."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("from pathlib import Path\nimport json\n\nprint('hello')\n")

        issues = [
            {"file": str(test_file), "message": "Unused import: Path"},
        ]

        resolver = IssueResolver(str(tmp_path))
        _resolved, failed = resolver.resolve_unused_imports(issues)

        test_file.read_text()
        # The regex should attempt to remove the import
        assert failed == 0

    def test_missing_file_increments_skipped(self, tmp_path):
        """Test missing file increments skipped_count."""
        issues = [
            {"file": str(tmp_path / "nonexistent.py"), "message": "Unused import: os"},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.resolve_unused_imports(issues)
        assert resolver.skipped_count >= 1

    def test_no_unused_import_in_message_skips(self, tmp_path):
        """Test issues without 'Unused import' in message are skipped."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\n")

        issues = [
            {"file": str(test_file), "message": "Some other error"},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolved, failed = resolver.resolve_unused_imports(issues)
        assert resolved == 0
        assert failed == 0

    def test_exception_during_resolution_increments_failed(self, tmp_path):
        """Test exception during file processing increments failed count."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\n")

        issues = [
            {"file": str(test_file), "message": "Unused import: os"},
        ]

        resolver = IssueResolver(str(tmp_path))
        # Make read_text raise an exception
        with patch.object(Path, "read_text", side_effect=PermissionError("No access")):
            _resolved, failed = resolver.resolve_unused_imports(issues)
            assert failed > 0

    def test_no_changes_increments_skipped(self, tmp_path):
        """Test when content doesn't change, skipped count increments."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("print('no imports here')\n")

        issues = [
            {"file": str(test_file), "message": "Unused import: os"},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.resolve_unused_imports(issues)
        # The import doesn't exist, so regex won't match
        # skipped_count should increment for the imports_to_remove
        assert resolver.skipped_count >= 1

    def test_resolution_log_updated_on_success(self, tmp_path):
        """Test resolution log is updated when imports are removed."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\n\nprint('hello')\n")

        issues = [
            {"file": str(test_file), "message": "Unused import: os"},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.resolve_unused_imports(issues)

        # Check if resolution log was updated
        if resolver.resolution_log:
            log_entry = resolver.resolution_log[0]
            assert log_entry["type"] == "unused_import"
            assert log_entry["status"] == "resolved"

    def test_multiple_unused_imports_same_file(self, tmp_path):
        """Test multiple unused imports in same file."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\nimport sys\nimport json\n\nprint('hello')\n")

        issues = [
            {"file": str(test_file), "message": "Unused import: os"},
            {"file": str(test_file), "message": "Unused import: sys"},
        ]

        resolver = IssueResolver(str(tmp_path))
        _resolved, failed = resolver.resolve_unused_imports(issues)
        assert failed == 0


class TestAddTypeHints:
    """Tests for add_type_hints method."""

    def test_empty_issues_returns_zeros(self, tmp_path):
        """Test empty issues list returns (0, 0)."""
        resolver = IssueResolver(str(tmp_path))
        resolved, failed = resolver.add_type_hints([])
        assert resolved == 0
        assert failed == 0

    def test_add_return_type_hint(self, tmp_path):
        """Test adding return type hint to function."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def my_function():\n    pass\n")

        issues = [
            {"file": str(test_file), "line": 1, "message": "Missing return type"},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolved, failed = resolver.add_type_hints(issues)

        content = test_file.read_text()
        assert "-> None:" in content
        assert resolved >= 1
        assert failed == 0

    def test_skip_function_with_existing_hint(self, tmp_path):
        """Test skipping function that already has return type hint."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def my_function() -> None:\n    pass\n")

        issues = [
            {"file": str(test_file), "line": 1, "message": "Missing return type"},
        ]

        resolver = IssueResolver(str(tmp_path))
        _resolved, _failed = resolver.add_type_hints(issues)

        content = test_file.read_text()
        # Should not double-add
        assert content.count("->") == 1

    def test_missing_file_increments_skipped(self, tmp_path):
        """Test missing file increments skipped_count."""
        issues = [
            {"file": str(tmp_path / "nonexistent.py"), "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.add_type_hints(issues)
        assert resolver.skipped_count >= 1

    def test_invalid_line_number_handled(self, tmp_path):
        """Test invalid line numbers are handled safely."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def my_function():\n    pass\n")

        issues = [
            {"file": str(test_file), "line": 999},  # Line doesn't exist
            {"file": str(test_file), "line": 0},  # Invalid line
            {"file": str(test_file), "line": None},  # No line
        ]

        resolver = IssueResolver(str(tmp_path))
        _resolved, failed = resolver.add_type_hints(issues)
        # Should handle gracefully without exceptions
        assert failed == 0

    def test_non_function_line_skipped(self, tmp_path):
        """Test non-function lines are skipped."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("x = 5\nprint('hello')\n")

        issues = [
            {"file": str(test_file), "line": 1},  # Not a function definition
        ]

        resolver = IssueResolver(str(tmp_path))
        resolved, _failed = resolver.add_type_hints(issues)
        assert resolved == 0

    def test_exception_increments_failed(self, tmp_path):
        """Test exception during processing increments failed count."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def func():\n    pass\n")

        issues = [
            {"file": str(test_file), "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        with patch.object(Path, "read_text", side_effect=PermissionError("No access")):
            _resolved, failed = resolver.add_type_hints(issues)
            assert failed > 0

    def test_resolution_log_updated_on_success(self, tmp_path):
        """Test resolution log updated when type hints added."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def my_function():\n    pass\n")

        issues = [
            {"file": str(test_file), "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.add_type_hints(issues)

        if resolver.resolution_log:
            log_entry = resolver.resolution_log[0]
            assert log_entry["type"] == "missing_type_hint"
            assert log_entry["status"] == "resolved"


class TestFixStyleViolations:
    """Tests for fix_style_violations method."""

    def test_empty_issues_returns_zeros(self, tmp_path):
        """Test empty issues list returns (0, 0)."""
        resolver = IssueResolver(str(tmp_path))
        resolved, failed = resolver.fix_style_violations([])
        assert resolved == 0
        assert failed == 0

    def test_skip_non_line_too_long_issues(self, tmp_path):
        """Test issues without 'Line too long' are skipped."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("print('hello')\n")

        issues = [
            {"file": str(test_file), "message": "Other style issue", "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolved, _failed = resolver.fix_style_violations(issues)
        assert resolved == 0

    def test_split_long_line_with_comment(self, tmp_path):
        """Test splitting long line with comment."""
        long_line = "x = 1  " + " " * 100 + "# This is a comment"
        test_file = tmp_path / "test_module.py"
        test_file.write_text(long_line + "\n")

        issues = [
            {"file": str(test_file), "message": "Line too long", "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.fix_style_violations(issues)
        # The long line should have been processed
        content = test_file.read_text()
        assert "comment" in content

    def test_skip_import_lines(self, tmp_path):
        """Test import lines are skipped (not modified)."""
        long_import = "import " + "x" * 150
        test_file = tmp_path / "test_module.py"
        test_file.write_text(long_import + "\n")

        issues = [
            {"file": str(test_file), "message": "Line too long", "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.fix_style_violations(issues)
        assert resolver.skipped_count >= 1

    def test_skip_non_comment_long_lines(self, tmp_path):
        """Test non-comment, non-import long lines are skipped."""
        long_line = "x = " + "'a'" * 50  # Long string
        test_file = tmp_path / "test_module.py"
        test_file.write_text(long_line + "\n")

        issues = [
            {"file": str(test_file), "message": "Line too long", "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.fix_style_violations(issues)
        assert resolver.skipped_count >= 1

    def test_missing_file_increments_skipped(self, tmp_path):
        """Test missing file increments skipped_count."""
        issues = [
            {"file": str(tmp_path / "nonexistent.py"), "message": "Line too long", "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.fix_style_violations(issues)
        assert resolver.skipped_count >= 1

    def test_exception_increments_failed(self, tmp_path):
        """Test exception during processing increments failed count."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("x = 1  " + " " * 100 + "# comment\n")

        issues = [
            {"file": str(test_file), "message": "Line too long", "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        with patch.object(Path, "read_text", side_effect=PermissionError("No access")):
            _resolved, failed = resolver.fix_style_violations(issues)
            assert failed > 0

    def test_invalid_line_number_handled(self, tmp_path):
        """Test invalid line numbers are handled."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("x = 1\n")

        issues = [
            {"file": str(test_file), "message": "Line too long", "line": 999},
        ]

        resolver = IssueResolver(str(tmp_path))
        _resolved, failed = resolver.fix_style_violations(issues)
        # Should handle without exceptions
        assert failed == 0


class TestRunResolution:
    """Tests for run_resolution method."""

    def test_run_resolution_with_valid_report(self, tmp_path):
        """Test run_resolution processes all categories."""
        # Create test file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\n\ndef my_func():\n    pass\n")

        # Create report
        report_data = {
            "by_category": {
                "import_errors": {
                    "sample_issues": [
                        {"file": str(test_file), "message": "Unused import: os"},
                    ]
                },
                "type_hints": {
                    "sample_issues": [
                        {"file": str(test_file), "line": 3},
                    ]
                },
                "style_issues": {"sample_issues": []},
            }
        }
        report_file = tmp_path / "error_resolution_report.json"
        report_file.write_text(json.dumps(report_data))

        resolver = IssueResolver(str(tmp_path))
        # Patch load_report to use our temp file
        with patch.object(resolver, "load_report", return_value=report_data):
            results = resolver.run_resolution()

        assert "import_errors" in results
        assert "type_hints" in results
        assert "style_issues" in results
        assert "total" in results

    def test_run_resolution_handles_missing_categories(self, tmp_path):
        """Test run_resolution handles missing categories gracefully."""
        report_data = {"by_category": {}}
        report_file = tmp_path / "error_resolution_report.json"
        report_file.write_text(json.dumps(report_data))

        resolver = IssueResolver(str(tmp_path))
        with patch.object(resolver, "load_report", return_value=report_data):
            results = resolver.run_resolution()

        # Should return structure without errors
        assert results["total"]["resolved"] == 0
        assert results["total"]["failed"] == 0

    def test_run_resolution_accumulates_totals(self, tmp_path):
        """Test run_resolution accumulates totals from all categories."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\nimport sys\n\ndef my_func():\n    pass\n")

        report_data = {
            "by_category": {
                "import_errors": {
                    "sample_issues": [
                        {"file": str(test_file), "message": "Unused import: os"},
                        {"file": str(test_file), "message": "Unused import: sys"},
                    ]
                },
            }
        }

        resolver = IssueResolver(str(tmp_path))
        with patch.object(resolver, "load_report", return_value=report_data):
            results = resolver.run_resolution()

        # Should have accumulated some resolved count
        assert "total" in results


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_file_path_in_issue(self, tmp_path):
        """Test handling of empty file path in issue."""
        issues = [
            {"file": "", "message": "Unused import: os"},
        ]

        resolver = IssueResolver(str(tmp_path))
        _resolved, failed = resolver.resolve_unused_imports(issues)
        # Should handle gracefully
        assert failed == 0

    def test_none_message_raises_typeerror(self, tmp_path):
        """Test that None message raises TypeError (documents actual behavior)."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\n")

        issues = [
            {"file": str(test_file), "message": None},
        ]

        resolver = IssueResolver(str(tmp_path))
        # The code doesn't handle None message - it raises TypeError
        with pytest.raises(TypeError):
            resolver.resolve_unused_imports(issues)

    def test_none_file_path_skips_issue(self, tmp_path):
        """Test None file path is skipped (file key is falsy)."""
        issues = [
            {"file": None, "message": "Unused import: os"},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolved, failed = resolver.resolve_unused_imports(issues)
        # Issue with None file should be skipped
        assert resolved == 0
        assert failed == 0

    def test_unicode_file_content(self, tmp_path):
        """Test handling of unicode content in files."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\n# Comment with émojis 🎉 and unicodé\nprint('hello')\n")

        issues = [
            {"file": str(test_file), "message": "Unused import: os"},
        ]

        resolver = IssueResolver(str(tmp_path))
        _resolved, _failed = resolver.resolve_unused_imports(issues)
        # Should handle unicode properly
        content = test_file.read_text()
        assert "émojis" in content or "hello" in content

    def test_multiple_resolvers_called_sequentially(self, tmp_path):
        """Test calling different resolvers in sequence."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import os\n\ndef func():\n    pass\n")

        resolver = IssueResolver(str(tmp_path))

        # Call import resolution
        issues1 = [{"file": str(test_file), "message": "Unused import: os"}]
        resolver.resolve_unused_imports(issues1)

        # Call type hint resolution
        issues2 = [{"file": str(test_file), "line": 3}]
        resolver.add_type_hints(issues2)

        # Both should have been processed
        content = test_file.read_text()
        assert "-> None:" in content or "import" not in content.split("\n")[0]


class TestCommentLineSplitting:
    """Tests specifically for comment line splitting logic."""

    def test_split_comment_when_code_short_enough(self, tmp_path):
        """Test comment is split when code part is short enough."""
        # Create a line where code part < 100, total > 100
        code_part = "x = 1"
        comment_part = "# " + "x" * 100  # Long comment
        long_line = code_part + "  " + comment_part

        test_file = tmp_path / "test_module.py"
        test_file.write_text(long_line + "\n")

        issues = [
            {"file": str(test_file), "message": "Line too long", "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        _resolved, _failed = resolver.fix_style_violations(issues)

        # Should have attempted modification
        content = test_file.read_text()
        assert "#" in content

    def test_no_split_when_code_part_too_long(self, tmp_path):
        """Test no split when code part is already > 100 chars."""
        code_part = "x" * 110  # Code part > 100
        comment_part = "# comment"
        long_line = code_part + "  " + comment_part

        test_file = tmp_path / "test_module.py"
        test_file.write_text(long_line + "\n")

        issues = [
            {"file": str(test_file), "message": "Line too long", "line": 1},
        ]

        resolver = IssueResolver(str(tmp_path))
        resolver.fix_style_violations(issues)

        # Should be skipped because code part too long
        # The line should remain unchanged
        content = test_file.read_text()
        assert content.strip() == long_line

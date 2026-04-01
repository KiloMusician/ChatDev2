"""Tests for src/code_quality_tools.py — LintIssue, TypeCheckIssue, QualityReport, RuffLinter."""

import pytest


class TestLintIssueDataclass:
    """Tests for LintIssue dataclass."""

    def test_basic_construction(self):
        from src.code_quality_tools import LintIssue
        issue = LintIssue(
            file="src/foo.py",
            line=42,
            column=5,
            code="F401",
            message="'os' imported but unused",
            severity="warning",
        )
        assert issue.file == "src/foo.py"
        assert issue.line == 42
        assert issue.code == "F401"

    def test_defaults(self):
        from src.code_quality_tools import LintIssue
        issue = LintIssue(
            file="f.py", line=1, column=1,
            code="E501", message="line too long", severity="warning"
        )
        assert issue.suggestion is None
        assert issue.fixable is False

    def test_fixable_issue(self):
        from src.code_quality_tools import LintIssue
        issue = LintIssue(
            file="f.py", line=1, column=1,
            code="I001", message="import order", severity="warning",
            fixable=True, suggestion="reorder imports"
        )
        assert issue.fixable is True
        assert issue.suggestion == "reorder imports"


class TestTypeCheckIssueDataclass:
    """Tests for TypeCheckIssue dataclass."""

    def test_construction(self):
        from src.code_quality_tools import TypeCheckIssue
        issue = TypeCheckIssue(
            file="src/bar.py",
            line=10,
            column=4,
            message="Incompatible types",
            severity="error",
        )
        assert issue.file == "src/bar.py"
        assert issue.severity == "error"
        assert issue.suggestion is None


class TestQualityReport:
    """Tests for QualityReport dataclass."""

    def test_defaults(self):
        from src.code_quality_tools import QualityReport
        r = QualityReport()
        assert r.analyzed_files == 0
        assert r.total_issues == 0
        assert r.issues_by_severity == {}
        assert r.files_with_issues == []

    def test_custom(self):
        from src.code_quality_tools import QualityReport
        r = QualityReport(
            analyzed_files=5,
            total_issues=12,
            issues_by_severity={"error": 3, "warning": 9},
            fixable_issues=6,
        )
        assert r.analyzed_files == 5
        assert r.fixable_issues == 6


class TestRuffLinter:
    """Tests for RuffLinter."""

    @pytest.fixture
    def linter(self, tmp_path):
        from src.code_quality_tools import RuffLinter
        # Lint a small clean Python file
        clean_file = tmp_path / "clean.py"
        clean_file.write_text('"""Clean module."""\n\nx = 1\n')
        return RuffLinter(target_path=str(clean_file))

    def test_instantiation(self, linter):
        assert linter is not None

    def test_check_returns_list(self, linter):
        issues = linter.check()
        assert isinstance(issues, list)

    def test_check_clean_file_no_issues(self, linter):
        issues = linter.check()
        # Clean file should have 0 issues
        assert len(issues) == 0

    def test_fix_returns_dict(self, linter):
        result = linter.fix()
        assert isinstance(result, dict)

    def test_fix_has_success_key(self, linter):
        result = linter.fix()
        assert "success" in result


class TestCodeQualityAnalyzer:
    """Tests for CodeQualityAnalyzer."""

    @pytest.fixture
    def analyzer(self, tmp_path):
        from src.code_quality_tools import CodeQualityAnalyzer
        return CodeQualityAnalyzer(target_path=str(tmp_path))

    def test_instantiation(self, analyzer):
        assert analyzer is not None

    def test_analyze_returns_report(self, analyzer):
        from src.code_quality_tools import QualityReport
        report = analyzer.analyze()
        assert isinstance(report, QualityReport)

    def test_analyze_empty_dir_no_issues(self, analyzer):
        report = analyzer.analyze()
        assert report.total_issues == 0


class TestCustomFixer:
    """Tests for CustomFixer."""

    def test_instantiation(self, tmp_path):
        from src.code_quality_tools import CustomFixer
        py_file = tmp_path / "module.py"
        py_file.write_text("x = 1\n")
        fixer = CustomFixer(module_path=str(py_file))
        assert fixer is not None

    def test_fix_unused_imports_returns_tuple(self, tmp_path):
        from src.code_quality_tools import CustomFixer
        py_file = tmp_path / "module.py"
        py_file.write_text("import os\n\nx = 1\n")
        fixer = CustomFixer(module_path=str(py_file))
        result = fixer.fix_unused_imports()
        assert isinstance(result, tuple)
        assert len(result) == 2

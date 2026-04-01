"""Test suite for doc_sync_checker.py

Comprehensive testing for documentation synchronization validation.
Covers claim extraction, codebase scanning, comparison, and report generation.
"""

import tempfile
from pathlib import Path

from src.tools.doc_sync_checker import DocSyncChecker


class TestDocSyncCheckerInit:
    """Test DocSyncChecker initialization."""

    def test_default_initialization(self):
        """Test initialization with default paths."""
        checker = DocSyncChecker()
        assert checker.readme_path == Path("README.md")
        assert checker.src_path == Path("src")
        assert checker.readme_claims == []
        assert checker.codebase_features == []
        assert checker.discrepancies == []
        assert checker.matches == []

    def test_custom_initialization(self):
        """Test initialization with custom paths."""
        readme_path = Path("custom_readme.md")
        src_path = Path("custom_src")
        checker = DocSyncChecker(readme_path=readme_path, src_path=src_path)
        assert checker.readme_path == readme_path
        assert checker.src_path == src_path


class TestExtractReadmeClaims:
    """Test README claim extraction."""

    def test_extract_module_references(self):
        """Test extraction of module references from README."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            readme_content = """
# Project

This project uses:
- `config.py` for configuration
- `utils.py` for utilities
- `main.py` as entry point
"""
            readme_path.write_text(readme_content, encoding="utf-8")

            checker = DocSyncChecker(readme_path=readme_path, src_path=tmpdir_path)
            checker.extract_readme_claims()

            # Should find 3 module references
            module_claims = [c for c in checker.readme_claims if c["type"] == "module"]
            assert len(module_claims) >= 3
            module_names = {c["name"] for c in module_claims}
            assert "config.py" in module_names
            assert "utils.py" in module_names
            assert "main.py" in module_names

    def test_extract_feature_descriptions(self):
        """Test extraction of feature descriptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            readme_content = """
# Features

- `config_handler` handles configuration
- `utils_parser` processes utilities
- `main_app` runs the application
"""
            readme_path.write_text(readme_content, encoding="utf-8")

            checker = DocSyncChecker(readme_path=readme_path, src_path=tmpdir_path)
            checker.extract_readme_claims()

            # Should find backtick references in feature descriptions
            assert len(checker.readme_claims) > 0

    def test_extract_empty_readme(self):
        """Test extraction from empty README."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            readme_path.write_text("", encoding="utf-8")

            checker = DocSyncChecker(readme_path=readme_path, src_path=tmpdir_path)
            checker.extract_readme_claims()

            assert len(checker.readme_claims) == 0

    def test_extract_missing_readme(self):
        """Test extraction when README doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "missing.md"

            checker = DocSyncChecker(readme_path=readme_path, src_path=tmpdir_path)
            checker.extract_readme_claims()

            # Should handle gracefully
            assert len(checker.readme_claims) == 0

    def test_extract_unicode_readme(self):
        """Test extraction from README with Unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            readme_content = """
# 项目特性

- `config.py` 配置管理
- `utils.py` 工具函数 🚀
"""
            readme_path.write_text(readme_content, encoding="utf-8")

            checker = DocSyncChecker(readme_path=readme_path, src_path=tmpdir_path)
            checker.extract_readme_claims()

            # Should handle Unicode
            assert len(checker.readme_claims) > 0


class TestScanCodebaseFeatures:
    """Test codebase feature scanning."""

    def test_scan_single_module(self):
        """Test scanning a single Python module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            module_path = src_path / "example.py"
            module_path.write_text("def hello(): pass\nclass Example: pass")

            checker = DocSyncChecker(src_path=src_path)
            checker.scan_codebase_features()

            # Should find module, function, and class
            assert len(checker.codebase_features) >= 3
            types = {f["type"] for f in checker.codebase_features}
            assert "module" in types
            assert "function" in types
            assert "class" in types

    def test_scan_multiple_modules(self):
        """Test scanning multiple modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            # Create multiple modules
            for i in range(3):
                module_path = src_path / f"module{i}.py"
                module_path.write_text(f"class Module{i}: pass\ndef func{i}(): pass")

            checker = DocSyncChecker(src_path=src_path)
            checker.scan_codebase_features()

            # Should find 3 modules + 3 classes + 3 functions = 9+ features
            assert len(checker.codebase_features) >= 9

    def test_scan_nested_modules(self):
        """Test scanning nested module structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            # Create nested structure
            subdir = src_path / "subdir"
            subdir.mkdir()
            (subdir / "nested.py").write_text("class Nested: pass")

            checker = DocSyncChecker(src_path=src_path)
            checker.scan_codebase_features()

            # Should find nested module
            module_names = {f["name"] for f in checker.codebase_features if f["type"] == "module"}
            assert "nested.py" in module_names

    def test_scan_missing_source_path(self):
        """Test scanning when source path doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            src_path = tmpdir_path / "missing_src"

            checker = DocSyncChecker(src_path=src_path)
            checker.scan_codebase_features()

            # Should handle gracefully
            assert len(checker.codebase_features) == 0

    def test_scan_ignores_private_features(self):
        """Test that private features are still scanned (but filtered in comparison)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            module_path = src_path / "example.py"
            module_path.write_text("""
def public_func(): pass
def _private_func(): pass
class PublicClass: pass
class _PrivateClass: pass
""")

            checker = DocSyncChecker(src_path=src_path)
            checker.scan_codebase_features()

            # Should find both public and private
            function_names = {
                f["name"] for f in checker.codebase_features if f["type"] == "function"
            }
            assert "public_func" in function_names
            assert "_private_func" in function_names


class TestCompareClaimsWithReality:
    """Test comparison logic."""

    def test_find_matches(self):
        """Test finding matches between claims and features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            # Create matching module
            module_path = src_path / "config.py"
            module_path.write_text("class ConfigManager: pass")

            # Create README claiming it
            readme_path.write_text("- `config.py` configuration management")

            checker = DocSyncChecker(readme_path=readme_path, src_path=src_path)
            checker.extract_readme_claims()
            checker.scan_codebase_features()
            checker.compare_claims_with_reality()

            # Should find match
            matches = [m for m in checker.matches if m["type"] == "documented_and_exists"]
            assert len(matches) > 0

    def test_find_documented_but_missing(self):
        """Test finding documented but missing features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            # Create README claiming non-existent module
            readme_path.write_text("- `missing.py` nonexistent module")

            checker = DocSyncChecker(readme_path=readme_path, src_path=src_path)
            checker.extract_readme_claims()
            checker.scan_codebase_features()
            checker.compare_claims_with_reality()

            # Should find discrepancy
            discrepancies = [
                d for d in checker.discrepancies if d["type"] == "documented_but_missing"
            ]
            assert len(discrepancies) > 0

    def test_find_undocumented_features(self):
        """Test finding undocumented features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            # Create undocumented module
            module_path = src_path / "undocumented.py"
            module_path.write_text("class UndocumentedClass: pass")

            # Create minimal README
            readme_path.write_text("# Project\n")

            checker = DocSyncChecker(readme_path=readme_path, src_path=src_path)
            checker.extract_readme_claims()
            checker.scan_codebase_features()
            checker.compare_claims_with_reality()

            # Should find undocumented feature
            discrepancies = [
                d for d in checker.discrepancies if d["type"] == "exists_but_undocumented"
            ]
            # At least UndocumentedClass should be found
            assert any(d["name"] == "UndocumentedClass" for d in discrepancies)


class TestGenerateReport:
    """Test report generation."""

    def test_generate_perfect_sync_report(self):
        """Test report generation for perfect sync."""
        checker = DocSyncChecker()
        checker.readme_claims = [{"name": "module.py", "type": "module"}]
        checker.codebase_features = [{"name": "module.py", "type": "module"}]
        checker.matches = [{"type": "documented_and_exists", "name": "module.py"}]
        checker.discrepancies = []

        report = checker.generate_report()

        assert "DOCUMENTATION SYNC REPORT" in report
        assert "EXCELLENT - Perfect sync!" in report
        assert "Verified Matches: 1" in report

    def test_generate_with_discrepancies(self):
        """Test report generation with discrepancies."""
        checker = DocSyncChecker()
        checker.readme_claims = [{"name": "module.py", "type": "module"}]
        checker.codebase_features = []
        checker.matches = []
        checker.discrepancies = [
            {
                "type": "documented_but_missing",
                "name": "module.py",
                "description": "A module",
                "severity": "warning",
            }
        ]

        report = checker.generate_report()

        assert "DOCUMENTED BUT MISSING" in report
        assert "module.py" in report

    def test_generate_accuracy_metrics(self):
        """Test accuracy metrics in report."""
        checker = DocSyncChecker()
        checker.readme_claims = [
            {"name": "a.py", "type": "module"},
            {"name": "b.py", "type": "module"},
            {"name": "c.py", "type": "module"},
        ]
        checker.codebase_features = []
        checker.matches = [
            {"type": "documented_and_exists", "name": "a.py"},
            {"type": "documented_and_exists", "name": "b.py"},
        ]
        checker.discrepancies = [{"type": "documented_but_missing", "name": "c.py"}]

        report = checker.generate_report()

        # Should show 66.7% accuracy (2/3)
        assert "66.7%" in report or "66.66" in report or "66.7" in report

    def test_report_handles_many_discrepancies(self):
        """Test report limits output for many discrepancies."""
        checker = DocSyncChecker()
        checker.readme_claims = [{"name": f"claim{i}.py", "type": "module"} for i in range(30)]
        checker.codebase_features = []
        checker.matches = []
        checker.discrepancies = [
            {"type": "documented_but_missing", "name": f"claim{i}.py"} for i in range(30)
        ]

        report = checker.generate_report()

        # Should mention there are more
        assert "... and" in report


class TestSaveReport:
    """Test report persistence."""

    def test_save_report_default_path(self):
        """Test saving report to default path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checker = DocSyncChecker()
            checker.readme_claims = []
            checker.codebase_features = []
            checker.matches = []
            checker.discrepancies = []

            output_path = Path(tmpdir) / "report.txt"
            checker.save_report(output_path)

            assert output_path.exists()
            content = output_path.read_text(encoding="utf-8")
            assert "DOCUMENTATION SYNC REPORT" in content

    def test_save_report_creates_parent_directories(self):
        """Test that save_report creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checker = DocSyncChecker()
            checker.readme_claims = []
            checker.codebase_features = []
            checker.matches = []
            checker.discrepancies = []

            output_path = Path(tmpdir) / "nested" / "deep" / "report.txt"
            checker.save_report(output_path)

            assert output_path.exists()
            assert output_path.parent.exists()

    def test_save_report_overwrites_existing(self):
        """Test that save_report overwrites existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.txt"
            output_path.write_text("old content")

            checker = DocSyncChecker()
            checker.readme_claims = []
            checker.codebase_features = []
            checker.matches = []
            checker.discrepancies = []

            checker.save_report(output_path)

            content = output_path.read_text(encoding="utf-8")
            assert "old content" not in content
            assert "DOCUMENTATION SYNC REPORT" in content


class TestRun:
    """Test full workflow."""

    def test_run_complete_workflow(self):
        """Test running complete workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            # Create test setup
            readme_path.write_text("- `example.py` example module")
            (src_path / "example.py").write_text("class Example: pass")

            checker = DocSyncChecker(readme_path=readme_path, src_path=src_path)

            # Should not raise any exceptions
            checker.run()

            # Should have populated data
            assert len(checker.readme_claims) > 0
            assert len(checker.codebase_features) > 0

    def test_run_with_empty_project(self):
        """Test running on empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            readme_path.write_text("# Empty Project")

            checker = DocSyncChecker(readme_path=readme_path, src_path=src_path)

            # Should handle gracefully
            checker.run()

            assert len(checker.discrepancies) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_scan_file_with_syntax_error(self):
        """Test scanning file with syntax errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            # Create file with syntax error
            module_path = src_path / "broken.py"
            module_path.write_text("def broken( : pass")

            checker = DocSyncChecker(src_path=src_path)
            # Should handle gracefully
            checker.scan_codebase_features()

            # Should still scan other aspects
            assert any(f["name"] == "broken.py" for f in checker.codebase_features)

    def test_extract_malformed_readme(self):
        """Test extracting from malformed README."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            # Badly formatted markdown
            readme_path.write_text("`unclosed code block\n- `also.py`")

            checker = DocSyncChecker(readme_path=readme_path, src_path=tmpdir_path)
            # Should handle gracefully
            checker.extract_readme_claims()

            assert len(checker.readme_claims) >= 0

    def test_multiple_runs_same_instance(self):
        """Test running checker multiple times on same instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            readme_path = tmpdir_path / "README.md"
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            # Create README with items not all in codebase
            readme_path.write_text("- `test.py`\n- `missing.py`")
            (src_path / "test.py").write_text("pass")

            checker = DocSyncChecker(readme_path=readme_path, src_path=src_path)

            # First run
            checker.run()

            # Second run (reset and recompute)
            checker.readme_claims = []
            checker.codebase_features = []
            checker.matches = []
            checker.discrepancies = []
            checker.run()

            # Results should be consistent
            assert len(checker.discrepancies) > 0


class TestIntegration:
    """Integration tests with real file structure."""

    def test_with_realistic_project_structure(self):
        """Test with realistic project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            src_path = tmpdir_path / "src"
            src_path.mkdir()

            # Create realistic structure
            (src_path / "main.py").write_text("def main(): pass")
            (src_path / "config.py").write_text("class Config: pass")

            utils_dir = src_path / "utils"
            utils_dir.mkdir()
            (utils_dir / "__init__.py").write_text("")
            (utils_dir / "helpers.py").write_text("def helper(): pass")

            # Create README
            readme_path = tmpdir_path / "README.md"
            readme_path.write_text("""
# Project

## Core Modules
- `main.py` - Entry point
- `config.py` - Configuration management

## Utilities
- `utils/helpers.py` - Helper functions
""")

            checker = DocSyncChecker(readme_path=readme_path, src_path=src_path)
            checker.run()

            # Should have reasonable results
            assert len(checker.readme_claims) > 0
            assert len(checker.codebase_features) > 0

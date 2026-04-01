"""Test auto-fix import error functionality."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add scripts to path
repo_root = Path(__file__).parent.parent
scripts_path = repo_root / "scripts"
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

from auto_fix_imports import ImportErrorFixer


def test_fixer_can_import_actual_src_module():
    """Test that the fixer can handle imports from src/."""
    fixer = ImportErrorFixer()
    test_content = """
from src.config.orchestration_config_loader import validate_config
from src.tools.agent_task_router import route_analysis_task
from src.guild.guild_board import GuildBoard

def test_function():
    return validate_config()
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp:
        temp.write(test_content)
        temp_file = temp.name
    try:
        issues = fixer.analyze_file(temp_file)
        assert isinstance(issues, list)
    finally:
        os.unlink(temp_file)


def test_fixer_with_broken_import():
    """Test fixing a broken import with fallback."""
    fixer = ImportErrorFixer()
    test_content = """
from nonexistent.module import some_function
import another.missing.module as missing

def use_imports():
    try:
        result = some_function()
    except Exception:  # noqa: BLE001
        result = None
    return result
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp:
        temp.write(test_content)
        temp_file = temp.name
    try:
        fixed_content = fixer.fix_imports_in_content(test_content, temp_file)
        assert "try:" in fixed_content
        assert "ImportError" in fixed_content
        assert "nonexistent = None" in fixed_content or "some_function = None" in fixed_content
    finally:
        os.unlink(temp_file)


class TestImportErrorFixer:
    """Test import error detection and fixing."""

    @pytest.fixture
    def fixer(self, tmp_path):
        """Create fixer instance with temp repo root."""
        return ImportErrorFixer(tmp_path)

    def test_detect_module_not_found(self, fixer):
        """Test detection of ModuleNotFoundError."""
        error = "ModuleNotFoundError: No module named 'src.missing'"
        error_type = fixer.detect_error_type(error)
        assert error_type == "module_not_found"

    def test_detect_cannot_import_name(self, fixer):
        """Test detection of ImportError for missing name."""
        error = "ImportError: cannot import name 'Foo' from 'src.bar'"
        error_type = fixer.detect_error_type(error)
        assert error_type == "cannot_import_name"

    def test_detect_circular_import(self, fixer):
        """Test detection of circular import error."""
        error = "ImportError: cannot import name 'x' due to circular import"
        error_type = fixer.detect_error_type(error)
        assert error_type == "circular_import"

    def test_extract_module_name(self, fixer):
        """Test extraction of module name from error."""
        error = "ModuleNotFoundError: No module named 'src.config.loader'"
        module = fixer.extract_module_name(error)
        assert module == "src.config.loader"

    def test_extract_missing_name(self, fixer):
        """Test extraction of missing import name."""
        error = "ImportError: cannot import name 'ConfigLoader' from 'src.config'"
        name = fixer.extract_missing_name(error)
        assert name == "ConfigLoader"

    def test_generate_stub_module(self, fixer):
        """Test stub module generation."""
        stub = fixer.generate_stub_module("src.test_module")
        assert "class TestModule" in stub
        assert "def __init__" in stub
        assert "test_module = TestModule()" in stub

    def test_generate_stub_import(self, fixer):
        """Test stub import generation."""
        stub = fixer.generate_stub_import("TestClass", "src.module")
        assert "class TestClass" in stub
        assert "def __init__" in stub

    def test_fix_module_not_found(self, fixer):
        """Test fix suggestion for missing module."""
        fix = fixer.fix_module_not_found("src.missing.module")
        assert fix["action"] == "create_stub_module"
        assert fix["module"] == "src.missing.module"
        assert "content" in fix
        assert "class MissingModule" in fix["content"]

    def test_fix_module_not_found_without_src_prefix(self, fixer):
        """Confirm stubs from top-level modules still map under src/."""
        module_name = "custom.module"
        fix = fixer.fix_module_not_found(module_name)
        expected_path = fixer.repo_root / "src" / "custom" / "module" / "__init__.py"
        assert Path(fix["file_path"]) == expected_path

    def test_fix_cannot_import_name(self, fixer):
        """Test fix suggestion for missing import name."""
        fix = fixer.fix_cannot_import_name("MissingClass", "src.config")
        assert fix["action"] == "add_stub_to_module"
        assert fix["name"] == "MissingClass"
        assert fix["module"] == "src.config"
        assert "class MissingClass" in fix["content"]

    def test_analyze_and_fix_module_not_found(self, fixer):
        """Test end-to-end analysis and fix for missing module."""
        error = "ModuleNotFoundError: No module named 'src.test'"
        fix = fixer.analyze_and_fix(error)
        assert fix["action"] == "create_stub_module"
        assert "content" in fix

    def test_analyze_and_fix_cannot_import(self, fixer):
        """Test end-to-end analysis and fix for missing import."""
        error = "ImportError: cannot import name 'Foo' from 'src.bar'"
        fix = fixer.analyze_and_fix(error)
        assert fix["action"] == "add_stub_to_module"
        assert fix["name"] == "Foo"

    def test_analyze_and_fix_circular_import(self, fixer):
        """Test circular import suggestion."""
        error = "ImportError: circular import detected"
        fix = fixer.analyze_and_fix(error)
        assert fix["action"] == "suggest_local_import"
        assert "suggestion" in fix
        assert "Local import" in fix["example"]

    def test_fix_circular_import(self, fixer):
        """Test circular import fix suggestion."""
        fix = fixer.fix_circular_import("ImportError: circular import")
        assert fix["action"] == "suggest_local_import"
        assert "Move import inside function" in fix["suggestion"]
        assert "def my_function" in fix["example"]

    def test_analyze_and_fix_unknown_error(self, fixer):
        """Test handling of unknown error types."""
        error = "SomeRandomError: unexpected format"
        fix = fixer.analyze_and_fix(error)
        assert fix["action"] == "unknown"
        assert "Could not detect error type" in fix["message"]

    def test_analyze_and_fix_empty_error(self, fixer):
        """Test handling of empty error message."""
        error = ""
        fix = fixer.analyze_and_fix(error)
        assert fix["action"] in ("unknown", "unhandled")

    def test_import_line_resolves_valid(self, fixer):
        """Test that valid imports resolve correctly."""
        result = fixer._import_line_resolves("import sys")
        assert result is True

    def test_import_line_resolves_invalid(self, fixer):
        """Test that invalid imports fail as expected."""
        result = fixer._import_line_resolves("from nonexistent_module_xyz import something")
        assert result is False

    def test_module_from_line_valid(self, fixer):
        """Test extraction of module name from import line."""
        line = "from src.config.loader import validate"
        module = fixer._module_from_line(line)
        assert module == "src.config.loader"

    def test_fallback_name_from_line(self, fixer):
        """Test extraction of fallback name from import line."""
        line = "from src.module import MyClass, another_func"
        fallback = fixer._fallback_name_from_line(line)
        assert "MyClass" in fallback or "my_class" in fallback.lower()

    def test_analyze_file_with_valid_imports(self, fixer):
        """Test analyzing a file with only valid imports."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp:
            temp.write("import os\nimport sys\nfrom pathlib import Path\n")
            temp_file = temp.name
        try:
            issues = fixer.analyze_file(temp_file)
            # Valid imports should result in empty or minimal issues
            assert isinstance(issues, list)
        finally:
            os.unlink(temp_file)

    def test_analyze_file_nonexistent(self, fixer):
        """Test analyzing a nonexistent file."""
        issues = fixer.analyze_file("/nonexistent/path/file.py")
        assert issues == []

    def test_stub_module_path_normalization(self, fixer):
        """Test that stub module paths are normalized correctly."""
        fix = fixer.fix_module_not_found("deeply.nested.module.structure")
        file_path = Path(fix["file_path"])
        assert "deeply" in str(file_path)
        assert "__init__.py" in str(file_path)
        assert "src" in str(file_path)

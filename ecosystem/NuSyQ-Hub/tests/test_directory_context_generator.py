"""Tests for directory_context_generator module."""

import sys
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# Mock missing dependencies before import
sys.modules["src.utils.Repository_Pandas_Library"] = MagicMock()

from src.utils.directory_context_generator import DirectoryContextGenerator


class TestDirectoryContextGenerator:
    """Test suite for DirectoryContextGenerator class."""

    @pytest.fixture
    def temp_repo(self) -> Generator[Path, None, None]:
        """Create temporary repository structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            # Create typical repo structure
            (temp_path / "src").mkdir()
            (temp_path / "tests").mkdir()
            (temp_path / "docs").mkdir()
            (temp_path / "config").mkdir()
            yield temp_path

    @pytest.fixture
    def generator(self, temp_repo: Path) -> DirectoryContextGenerator:
        """Create DirectoryContextGenerator instance for testing."""
        with (
            patch("src.utils.directory_context_generator.OmniTagSystem"),
            patch("src.utils.directory_context_generator.MegaTagProcessor"),
            patch("src.utils.directory_context_generator.RepositoryPandasLibrary"),
        ):
            return DirectoryContextGenerator(str(temp_repo))

    def test_init_with_default_root(self) -> None:
        """Test initialization with default repository root."""
        with (
            patch("src.utils.directory_context_generator.OmniTagSystem"),
            patch("src.utils.directory_context_generator.MegaTagProcessor"),
            patch("src.utils.directory_context_generator.RepositoryPandasLibrary"),
        ):
            gen = DirectoryContextGenerator()
            assert gen.repository_root == Path.cwd()

    def test_init_with_custom_root(self, temp_repo: Path) -> None:
        """Test initialization with custom repository root."""
        with (
            patch("src.utils.directory_context_generator.OmniTagSystem"),
            patch("src.utils.directory_context_generator.MegaTagProcessor"),
            patch("src.utils.directory_context_generator.RepositoryPandasLibrary"),
        ):
            gen = DirectoryContextGenerator(str(temp_repo))
            assert gen.repository_root == temp_repo

    def test_load_infrastructure_config(self, generator: DirectoryContextGenerator) -> None:
        """Test loading infrastructure configuration."""
        # Should not raise an error
        generator.load_infrastructure_config()
        assert hasattr(generator, "omnitag_system")
        assert hasattr(generator, "megatag_processor")

    def test_generate_context_filename_for_src_directory(
        self, generator: DirectoryContextGenerator
    ) -> None:
        """Test context filename generation for src directory."""
        with patch.object(
            generator, "context_templates", {"src": "SOURCE_CODE_SYSTEMS_CONTEXT.md"}
        ):
            result = generator.generate_context_filename(generator.repository_root / "src")
            assert "CONTEXT" in result or "context" in result.lower()

    def test_calculate_context_priority_src_directory(
        self, generator: DirectoryContextGenerator
    ) -> None:
        """Test priority calculation for src directory."""
        priority = generator.calculate_context_priority(generator.repository_root / "src")
        assert isinstance(priority, int)
        assert priority > 0

    def test_calculate_context_priority_tests_directory(
        self, generator: DirectoryContextGenerator
    ) -> None:
        """Test priority calculation for tests directory."""
        priority = generator.calculate_context_priority(generator.repository_root / "tests")
        assert isinstance(priority, int)
        assert priority > 0

    def test_scan_repository_structure(self, generator: DirectoryContextGenerator) -> None:
        """Test repository structure scanning."""
        with patch.object(generator, "pandas_lib") as mock_pandas:
            mock_pandas.discover_components.return_value = {
                "src": {"type": "module", "files": 10},
                "tests": {"type": "tests", "files": 5},
            }
            result = generator.scan_repository_structure()
            assert isinstance(result, dict)

    def test_extract_component_info(self, generator: DirectoryContextGenerator) -> None:
        """Test component information extraction."""
        test_dir = str(generator.repository_root / "src")
        with patch.object(generator.pandas_lib, "analyze_directory", return_value={"files": 5}):
            result = generator.extract_component_info(test_dir)
            assert isinstance(result, dict)

    def test_extract_architecture_info(self, generator: DirectoryContextGenerator) -> None:
        """Test architecture information extraction."""
        test_dir = str(generator.repository_root / "src")
        with patch.object(
            generator.pandas_lib, "get_architecture_info", return_value={"patterns": []}
        ):
            result = generator.extract_architecture_info(test_dir)
            assert isinstance(result, dict)

    def test_generate_omnitag(self, generator: DirectoryContextGenerator) -> None:
        """Test OmniTag generation."""
        test_dir = generator.repository_root / "src"
        component_info = {"type": "module", "files": 10}
        with patch.object(
            generator.omnitag_system,
            "create_tag",
            return_value=["Purpose", "Dependencies", "Context"],
        ):
            result = generator.generate_omnitag(test_dir, component_info)
            assert isinstance(result, dict)

    def test_generate_metatag(self, generator: DirectoryContextGenerator) -> None:
        """Test MegaTag generation."""
        test_dir = generator.repository_root / "src"
        arch_info = {"patterns": [], "complexity": "medium"}
        with patch.object(
            generator.megatag_processor,
            "process_tag",
            return_value="[UTILS⨳CONTEXT⦾GENERATION→∞]",
        ):
            result = generator.generate_metatag(test_dir, arch_info)
            assert isinstance(result, dict)

    def test_create_missing_context_files(self, generator: DirectoryContextGenerator) -> None:
        """Test missing context file creation."""
        structure_data = {
            "src": {"priority": 1, "type": "source"},
            "tests": {"priority": 2, "type": "tests"},
            "missing_context_files": [],
        }
        with patch.object(generator, "generate_context_content", return_value="# Content"):
            with patch("builtins.open", create=True):
                result = generator.create_missing_context_files(structure_data)
                assert isinstance(result, list)

    def test_update_existing_readme_files(self, generator: DirectoryContextGenerator) -> None:
        """Test updating existing README files."""
        with patch("pathlib.Path.rglob", return_value=[]):
            result = generator.update_existing_readme_files()
            assert isinstance(result, list)

    def test_enhance_existing_content(self, generator: DirectoryContextGenerator) -> None:
        """Test enhancing existing content."""
        existing = "# Original Content\n\nSome description here."
        test_dir = generator.repository_root / "src"
        enhanced = generator.enhance_existing_content(existing, test_dir)
        assert isinstance(enhanced, str)

    def test_generate_comprehensive_report(self, generator: DirectoryContextGenerator) -> None:
        """Test comprehensive report generation."""
        mock_structure = {
            "src": {},
            "tests": {},
            "directories": [],
            "existing_context_files": [],
            "missing_context_files": [],
        }
        with patch.object(generator, "scan_repository_structure", return_value=mock_structure):
            with patch.object(generator, "create_missing_context_files", return_value=[]):
                with patch.object(generator, "update_existing_readme_files", return_value=[]):
                    report = generator.generate_comprehensive_report()
                    assert isinstance(report, str)
                    assert len(report) > 0

    def test_context_templates_initialization(self, generator: DirectoryContextGenerator) -> None:
        """Test that context templates are properly initialized."""
        assert "src" in generator.context_templates
        assert "tests" in generator.context_templates
        assert "docs" in generator.context_templates


class TestDirectoryContextGeneratorIntegration:
    """Integration tests for DirectoryContextGenerator."""

    def test_full_workflow_with_real_paths(self) -> None:
        """Test full workflow with temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create structure
            (temp_path / "src").mkdir()
            (temp_path / "tests").mkdir()
            (temp_path / "docs").mkdir()

            # Create some files
            (temp_path / "src" / "module.py").write_text("# Test module")
            (temp_path / "README.md").write_text("# Test Project")

            with (
                patch("src.utils.directory_context_generator.OmniTagSystem"),
                patch("src.utils.directory_context_generator.MegaTagProcessor"),
                patch("src.utils.directory_context_generator.RepositoryPandasLibrary"),
            ):
                gen = DirectoryContextGenerator(str(temp_path))
                assert gen.repository_root == temp_path
                assert (temp_path / "src").exists()

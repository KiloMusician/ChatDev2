"""
Comprehensive tests for Universal Project Generator

Tests template definitions, generation, registration, and integration.
"""

import json
import tempfile
from pathlib import Path

import pytest
from src.generators.template_definitions import (
    AIProvider,
    LanguageType,
    ProjectType,
    get_template,
    list_template_ids,
    list_templates,
)
from src.generators.universal_project_generator import UniversalProjectGenerator


class TestTemplateDefinitions:
    """Test template schema and definitions."""

    def test_template_loading(self):
        """Verify all templates can be loaded."""
        template_ids = list_template_ids()
        assert len(template_ids) >= 8, "Should have at least 8 templates"

        for tid in template_ids:
            template = get_template(tid)
            assert template is not None, f"Template {tid} should be loadable"

    def test_template_schema_validation(self):
        """Verify template schema completeness."""
        templates = list_templates()

        for template in templates:
            # Required fields
            assert template.template_id, f"{template.name}: missing template_id"
            assert template.name, f"{template.name}: missing name"
            assert 1 <= template.complexity <= 10, f"{template.name}: invalid complexity"
            assert template.type in ProjectType, f"{template.name}: invalid type"
            assert template.language in LanguageType, f"{template.name}: invalid language"
            assert (
                template.primary_ai_provider in AIProvider
            ), f"{template.name}: invalid AI provider"

    def test_template_by_type(self):
        """Verify templates are categorized correctly."""
        # Games
        games = list_templates(ProjectType.GAME)
        assert len(games) >= 2, "Should have at least 2 game templates"

        # Webapps
        webapps = list_templates(ProjectType.WEBAPP)
        assert len(webapps) >= 3, "Should have at least 3 webapp templates"

        # Packages
        packages = list_templates(ProjectType.PACKAGE)
        assert len(packages) >= 2, "Should have at least 2 package templates"

        # Extensions
        extensions = list_templates(ProjectType.EXTENSION)
        assert len(extensions) >= 2, "Should have at least 2 extension templates"

        # CLI tools
        cli_tools = list_templates(ProjectType.CLI)
        assert len(cli_tools) >= 2, "Should have at least 2 CLI templates"

    def test_template_complexity_ordering(self):
        """Verify templates are ordered by complexity."""
        templates = list_templates()
        complexities = [t.complexity for t in templates]

        assert complexities == sorted(complexities), "Templates should be ordered by complexity"

    def test_template_ai_provider_selection(self):
        """Verify AI provider selection logic."""
        simple_template = get_template("package_python")
        assert simple_template.complexity <= 5, "package_python should be simple"
        assert simple_template.primary_ai_provider in [AIProvider.OLLAMA, AIProvider.CLAUDE]

        complex_template = get_template("game_godot_3d")
        assert complex_template.complexity >= 8, "game_godot_3d should be complex"
        assert complex_template.primary_ai_provider == AIProvider.CHATDEV


class TestUniversalProjectGenerator:
    """Test UPG core functionality."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_base = tmpdir_path / "projects"
            registry_path = tmpdir_path / "registry.json"
            quest_log = tmpdir_path / "quest.jsonl"

            yield {
                "base": tmpdir_path,
                "output": output_base,
                "registry": registry_path,
                "quest": quest_log,
            }

    @pytest.fixture
    def upg(self, temp_dirs):
        """Create UPG instance with temp directories."""
        return UniversalProjectGenerator(
            output_base=temp_dirs["output"],
            registry_path=temp_dirs["registry"],
            quest_log_path=temp_dirs["quest"],
        )

    def test_upg_initialization(self, upg):
        """Test UPG initialization and directory creation."""
        assert upg.output_base.exists(), "Output base should be created"
        assert upg.registry_path.parent.exists(), "Registry parent should be created"
        assert upg.quest_log_path.parent.exists(), "Quest log parent should be created"

    def test_template_retrieval(self, upg):
        """Test template loading via UPG."""
        template = upg.get_template("package_python")
        assert template is not None, "Should retrieve package_python template"
        assert template.template_id == "package_python"

    def test_template_validation(self, upg):
        """Test template validation."""
        template = get_template("game_godot_3d")
        is_valid, errors = upg.validate_template(template)

        assert is_valid, f"game_godot_3d should be valid, errors: {errors}"
        assert errors == [], "No errors expected"

    def test_ai_provider_selection_simple(self, upg):
        """Test AI provider selection for simple templates."""
        template = get_template("package_python")
        provider = upg.select_ai_provider(template)

        # Simple projects use Ollama
        assert provider == AIProvider.OLLAMA or provider == template.primary_ai_provider

    def test_ai_provider_selection_complex(self, upg):
        """Test AI provider selection for complex templates."""
        template = get_template("game_godot_3d")
        provider = upg.select_ai_provider(template)

        # Complex projects use ChatDev
        assert provider == AIProvider.CHATDEV or provider == template.primary_ai_provider

    def test_project_generation_success(self, upg):
        """Test successful project generation."""
        result = upg.generate("package_python", "test_package")

        assert result.status == "success", f"Generation should succeed: {result.error_message}"
        assert result.project_id, "Should have project ID"
        assert result.project_name == "test_package"
        assert result.output_path, "Should have output path"
        assert Path(result.output_path).exists(), "Output directory should exist"

    def test_project_generation_creates_files(self, upg):
        """Test that generation creates starter files."""
        result = upg.generate("webapp_minimal_fastapi", "test_api")

        assert result.status == "success"

        project_dir = Path(result.output_path)

        # Check starter files exist
        assert (project_dir / "main.py").exists(), "main.py should be created"
        assert (project_dir / "requirements.txt").exists(), "requirements.txt should be created"

        # Check metadata file
        assert (project_dir / ".nusyq.json").exists(), ".nusyq.json metadata should be created"

    def test_metadata_file_content(self, upg):
        """Test metadata file contains correct information."""
        result = upg.generate("package_python", "metadata_test")

        metadata_file = Path(result.output_path) / ".nusyq.json"
        metadata = json.loads(metadata_file.read_text())

        assert metadata["project_id"] == result.project_id
        assert metadata["template_id"] == "package_python"
        assert metadata["language"] == "python"
        assert metadata["type"] == "package"

    def test_registry_artifact_registration(self, upg):
        """Test artifact registration in registry."""
        result = upg.generate("cli_python_click", "test_cli")

        assert result.status == "success"

        # Check registry
        projects = upg.list_generated_projects()
        assert len(projects) > 0, "Registry should have projects"

        # Find our project
        project = next((p for p in projects if p["project_id"] == result.project_id), None)
        assert project is not None, "Project should be in registry"
        assert project["name"] == "test_cli"

    def test_quest_logging(self, upg):
        """Test quest system integration."""
        result = upg.generate("extension_vscode", "test_ext")

        assert result.status == "success"
        assert upg.quest_log_path.exists(), "Quest log should be created"

        # Read quest log
        lines = upg.quest_log_path.read_text().strip().split("\n")
        assert len(lines) > 0, "Quest log should have entries"

        # Parse last entry
        last_event = json.loads(lines[-1])
        assert last_event["event_type"] == "project_generated"
        assert last_event["project_id"] == result.project_id

    def test_generation_failure_invalid_template(self, upg):
        """Test generation failure with invalid template."""
        result = upg.generate("nonexistent_template", "test_proj")

        assert result.status == "failed", "Should fail for invalid template"
        assert result.error_message, "Should have error message"

    def test_generation_multiple_projects(self, upg):
        """Test generating multiple projects."""
        results = []

        for i in range(3):
            result = upg.generate("package_python", f"package_{i}")
            results.append(result)
            assert result.status == "success"

        # Check all registered
        projects = upg.list_generated_projects()
        assert len(projects) == 3, "All projects should be registered"

    def test_project_info_retrieval(self, upg):
        """Test retrieving project information."""
        result = upg.generate("package_npm", "test_npm_pkg")

        info = upg.get_project_info(result.project_id)
        assert info is not None, "Should retrieve project info"
        assert info["name"] == "test_npm_pkg"
        assert info["template_id"] == "package_npm"

    def test_template_complexity_info(self, upg):
        """Test template complexity information."""
        info = upg.get_template_complexity_info("game_godot_3d")

        assert info is not None
        assert info["complexity"] == 9
        assert info["ai_provider"] == "chatdev"

    def test_generation_time_tracking(self, upg):
        """Test generation time is tracked."""
        result = upg.generate("package_python", "timing_test")

        assert result.generation_time >= 0, "Generation time should be measured"

    def test_registry_persistence(self, temp_dirs):
        """Test registry is persisted to disk."""
        upg1 = UniversalProjectGenerator(
            output_base=temp_dirs["output"],
            registry_path=temp_dirs["registry"],
            quest_log_path=temp_dirs["quest"],
        )

        result = upg1.generate("package_python", "persist_test")
        assert result.status == "success"

        # Create new UPG instance - should load registry
        upg2 = UniversalProjectGenerator(
            output_base=temp_dirs["output"],
            registry_path=temp_dirs["registry"],
            quest_log_path=temp_dirs["quest"],
        )

        projects = upg2.list_generated_projects()
        assert len(projects) == 1, "Registry should persist"
        assert projects[0]["name"] == "persist_test"


class TestTemplateVariety:
    """Test diversity and completeness of templates."""

    def test_language_coverage(self):
        """Verify templates cover multiple languages."""
        templates = list_templates()
        languages = {t.language.value for t in templates}

        assert "python" in languages, "Should support Python"
        assert any(
            "javascript" in lang or "typescript" in lang for lang in languages
        ), "Should support JS/TS"
        assert "gdscript" in languages, "Should support GDScript"

    def test_project_type_coverage(self):
        """Verify all project types are represented."""
        templates = list_templates()
        types = {t.type for t in templates}

        assert ProjectType.GAME in types
        assert ProjectType.WEBAPP in types
        assert ProjectType.PACKAGE in types
        assert ProjectType.EXTENSION in types
        assert ProjectType.CLI in types

    def test_complexity_range_coverage(self):
        """Verify templates span complexity range."""
        templates = list_templates()
        complexities = {t.complexity for t in templates}

        assert min(complexities) <= 3, "Should have simple templates (1-3)"
        assert max(complexities) >= 8, "Should have complex templates (8-10)"

    def test_ai_provider_distribution(self):
        """Verify AI providers are appropriately selected."""
        templates = list_templates()

        simple = [t for t in templates if t.complexity <= 4]
        complex = [t for t in templates if t.complexity >= 7]

        # Simple templates should use Ollama
        ollama_simple = sum(1 for t in simple if t.primary_ai_provider == AIProvider.OLLAMA)
        assert ollama_simple > 0, "Simple templates should use Ollama"

        # Complex templates should use ChatDev
        chatdev_complex = sum(1 for t in complex if t.primary_ai_provider == AIProvider.CHATDEV)
        assert chatdev_complex > 0, "Complex templates should use ChatDev"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

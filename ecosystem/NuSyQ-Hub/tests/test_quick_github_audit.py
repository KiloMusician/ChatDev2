"""Tests for quick_github_audit module."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from src.utils.quick_github_audit import quick_github_audit


class TestQuickGitHubAudit:
    """Test suite for quick_github_audit function."""

    @pytest.fixture
    def temp_github_repo(self) -> Generator[Path, None, None]:
        """Create temporary GitHub repository structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            github_dir = repo_root / ".github"
            github_dir.mkdir()

            # Create subdirectories
            (github_dir / "workflows").mkdir()
            (github_dir / "instructions").mkdir()
            (github_dir / "prompts").mkdir()

            # Create some sample files
            (github_dir / "workflows" / "test.yml").write_text("""
name: Test Workflow
jobs:
  test:
    runs-on: ubuntu-latest
""")

            (
                github_dir / "instructions" / "COPILOT_INSTRUCTIONS_CONFIG.instructions.md"
            ).write_text("# Copilot Instructions")

            yield repo_root

    def test_quick_github_audit_returns_bool(self, temp_github_repo: Path) -> None:
        """Test that quick_github_audit returns a boolean."""
        with patch("pathlib.Path.cwd", return_value=temp_github_repo):
            result = quick_github_audit()
            assert isinstance(result, bool)

    def test_quick_github_audit_with_minimal_structure(self) -> None:
        """Test audit with minimal GitHub directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            github_dir = repo_root / ".github"
            github_dir.mkdir()

            with patch("pathlib.Path.cwd", return_value=repo_root):
                result = quick_github_audit()
                assert result is True

    def test_quick_github_audit_without_github_dir(self) -> None:
        """Test audit when .github directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            # No .github directory created

            with patch("pathlib.Path.cwd", return_value=repo_root):
                result = quick_github_audit()
                assert result is True

    def test_quick_github_audit_with_workflows(self, temp_github_repo: Path) -> None:
        """Test audit detects workflow files."""
        with patch("pathlib.Path.cwd", return_value=temp_github_repo):
            # Add additional workflows
            workflows_dir = temp_github_repo / ".github" / "workflows"
            (workflows_dir / "ci.yaml").write_text("""
name: CI
jobs:
  build:
    runs-on: ubuntu-latest
""")

            result = quick_github_audit()
            assert result is True

    def test_quick_github_audit_with_invalid_yaml(self, temp_github_repo: Path) -> None:
        """Test audit handles invalid YAML gracefully."""
        with patch("pathlib.Path.cwd", return_value=temp_github_repo):
            # Write invalid YAML
            workflows_dir = temp_github_repo / ".github" / "workflows"
            (workflows_dir / "bad.yml").write_text(": invalid: yaml: content:")

            # Should not raise an exception
            result = quick_github_audit()
            assert result is True

    def test_quick_github_audit_with_all_essential_instructions(
        self, temp_github_repo: Path
    ) -> None:
        """Test audit with all essential instruction files."""
        with patch("pathlib.Path.cwd", return_value=temp_github_repo):
            instructions_dir = temp_github_repo / ".github" / "instructions"

            essential_files = [
                "COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
                "FILE_PRESERVATION_MANDATE.instructions.md",
                "NuSyQ-Hub_INSTRUCTIONS.instructions.md",
            ]

            for file_name in essential_files:
                (instructions_dir / file_name).write_text(f"# {file_name}")

            result = quick_github_audit()
            assert result is True

    def test_quick_github_audit_detects_missing_workflows(self) -> None:
        """Test audit logic for detecting missing essential workflows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            github_dir = repo_root / ".github"
            workflows_dir = github_dir / "workflows"
            workflows_dir.mkdir(parents=True)

            # Create minimal workflow file
            (workflows_dir / "existing.yml").write_text("name: Existing")

            with patch("pathlib.Path.cwd", return_value=repo_root):
                result = quick_github_audit()
                # Should complete successfully
                assert result is True

    def test_quick_github_audit_with_prompts_directory(self, temp_github_repo: Path) -> None:
        """Test audit with prompts directory and files."""
        with patch("pathlib.Path.cwd", return_value=temp_github_repo):
            prompts_dir = temp_github_repo / ".github" / "prompts"
            (prompts_dir / "system_prompt.md").write_text("# System Prompt\n" * 100)

            result = quick_github_audit()
            assert result is True

    def test_quick_github_audit_detects_integration_references(
        self, temp_github_repo: Path
    ) -> None:
        """Test audit logic for detecting src/ references."""
        with patch("pathlib.Path.cwd", return_value=temp_github_repo):
            # Write content with src references
            instructions_dir = temp_github_repo / ".github" / "instructions"
            (instructions_dir / "integration.md").write_text(
                "# Integration\n\nSee `src/orchestration/` for details.\n"
            )

            result = quick_github_audit()
            assert result is True

    def test_quick_github_audit_with_unicode_files(self, temp_github_repo: Path) -> None:
        """Test audit handles Unicode content gracefully."""
        with patch("pathlib.Path.cwd", return_value=temp_github_repo):
            instructions_dir = temp_github_repo / ".github" / "instructions"
            (instructions_dir / "unicode.md").write_text("# Unicode: 🎯 ✨ 🚀\n" * 10)

            result = quick_github_audit()
            assert result is True

    def test_quick_github_audit_handles_permission_errors(self, temp_github_repo: Path) -> None:
        """Test audit handles permission errors gracefully."""
        with patch("pathlib.Path.cwd", return_value=temp_github_repo):
            # Mock Path.read_text to raise PermissionError for certain files
            original_read_text = Path.read_text

            def mock_read_text(self: Path, *args: object, **kwargs: object) -> str:
                if "test.yml" in str(self):
                    raise PermissionError("Access denied")
                return original_read_text(self, *args, **kwargs)

            with patch.object(Path, "read_text", mock_read_text):
                # Should handle gracefully and return True despite PermissionError
                result = quick_github_audit()
                assert result is True


class TestQuickGitHubAuditIntegration:
    """Integration tests for quick_github_audit."""

    def test_full_audit_workflow(self) -> None:
        """Test complete audit workflow with realistic structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Create complete GitHub structure
            github_dir = repo_root / ".github"
            github_dir.mkdir()

            (github_dir / "workflows").mkdir()
            (github_dir / "instructions").mkdir()
            (github_dir / "prompts").mkdir()

            # Create realistic workflow files
            workflows = {
                "ci.yml": """
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pytest
""",
                "coverage.yml": """
name: Coverage
on: [push]
jobs:
  coverage:
    runs-on: ubuntu-latest
""",
            }

            for name, content in workflows.items():
                (github_dir / "workflows" / name).write_text(content)

            # Create instruction files
            for file_name in [
                "COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
                "FILE_PRESERVATION_MANDATE.instructions.md",
            ]:
                (github_dir / "instructions" / file_name).write_text(f"# {file_name}")

            # Create prompts
            (github_dir / "prompts" / "agent_prompt.md").write_text("# Agent Prompt")

            with patch("pathlib.Path.cwd", return_value=repo_root):
                result = quick_github_audit()
                assert result is True

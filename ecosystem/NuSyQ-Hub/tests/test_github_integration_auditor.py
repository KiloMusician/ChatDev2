"""Tests for GitHubIntegrationAuditor.

Test coverage for GitHub integration audit and validation system.
Target: 13% → 30-40% coverage for github_integration_auditor.py
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from src.utils.github_integration_auditor import GitHubIntegrationAuditor


class TestGitHubIntegrationAuditorInit:
    """Test GitHubIntegrationAuditor initialization."""

    def test_init_with_default_root(self) -> None:
        """Test initialization with default repository root."""
        auditor = GitHubIntegrationAuditor()
        assert auditor.repo_root == Path.cwd()
        assert auditor.github_dir == Path.cwd() / ".github"
        assert auditor.workflows_dir == Path.cwd() / ".github" / "workflows"

    def test_init_with_custom_root(self) -> None:
        """Test initialization with custom repository root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_root = Path(tmpdir)
            auditor = GitHubIntegrationAuditor(repo_root=custom_root)
            assert auditor.repo_root == custom_root
            assert auditor.github_dir == custom_root / ".github"
            assert auditor.workflows_dir == custom_root / ".github" / "workflows"

    def test_init_creates_audit_results_dict(self) -> None:
        """Test that initialization creates audit results dictionary."""
        auditor = GitHubIntegrationAuditor()
        assert isinstance(auditor.audit_results, dict)
        assert "timestamp" in auditor.audit_results
        assert "workflows" in auditor.audit_results
        assert "instructions" in auditor.audit_results
        assert "recommendations" in auditor.audit_results


class TestDirectoryStructureAudit:
    """Test directory structure audit functionality."""

    def test_audit_directory_structure_when_github_exists(self) -> None:
        """Test directory audit when .github directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            github_dir = repo_root / ".github"
            github_dir.mkdir()
            (github_dir / "workflows").mkdir()

            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_directory_structure()

            assert "structure" in auditor.audit_results
            assert auditor.audit_results["structure"]["github_dir_exists"] is True
            assert auditor.audit_results["structure"]["workflows_dir_exists"] is True

    def test_audit_directory_structure_when_github_missing(self) -> None:
        """Test directory audit when .github directory is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_directory_structure()

            assert "structure" in auditor.audit_results
            assert auditor.audit_results["structure"]["github_dir_exists"] is False

    def test_audit_directory_structure_lists_subdirectories(self) -> None:
        """Test that directory audit lists subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            github_dir = repo_root / ".github"
            github_dir.mkdir()
            (github_dir / "workflows").mkdir()
            (github_dir / "instructions").mkdir()

            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_directory_structure()

            subdirs = auditor.audit_results["structure"]["subdirectories"]
            assert len(subdirs) >= 2
            subdir_names = [d["name"] for d in subdirs]
            assert "workflows" in subdir_names
            assert "instructions" in subdir_names


class TestWorkflowAudit:
    """Test workflow audit functionality."""

    def test_audit_workflows_when_directory_missing(self) -> None:
        """Test workflow audit when workflows directory is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_workflows()

            assert auditor.audit_results["workflows"]["status"] == "no_workflows_directory"
            assert any(
                "workflows directory does not exist" in issue
                for issue in auditor.audit_results["issues"]
            )

    def test_audit_workflows_finds_yaml_files(self) -> None:
        """Test that workflow audit finds .yml and .yaml files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            workflows_dir = repo_root / ".github" / "workflows"
            workflows_dir.mkdir(parents=True)

            # Create test workflow files
            test_workflow_yml = workflows_dir / "test.yml"
            test_workflow_yaml = workflows_dir / "deploy.yaml"

            workflow_content = """
name: Test Workflow
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
"""
            test_workflow_yml.write_text(workflow_content)
            test_workflow_yaml.write_text(workflow_content)

            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_workflows()

            assert "test.yml" in auditor.audit_results["workflows"]
            assert "deploy.yaml" in auditor.audit_results["workflows"]

    def test_audit_workflows_recommends_essential_workflows(self) -> None:
        """Test that workflow audit recommends missing essential workflows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            workflows_dir = repo_root / ".github" / "workflows"
            workflows_dir.mkdir(parents=True)

            # Create minimal workflow (missing security-scan, coverage-verification, etc.)
            test_workflow = workflows_dir / "basic.yml"
            test_workflow.write_text(
                "name: Basic\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest"
            )

            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_workflows()

            # Check for recommendations about missing workflows
            recommendations = auditor.audit_results["recommendations"]
            assert any("security-scan" in rec for rec in recommendations)


class TestWorkflowFileAnalysis:
    """Test individual workflow file analysis."""

    def test_analyze_workflow_file_parses_yaml(self) -> None:
        """Test that workflow analysis parses YAML correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "test.yml"
            workflow_content = """
name: Test Workflow
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest
"""
            workflow_file.write_text(workflow_content)

            auditor = GitHubIntegrationAuditor()
            analysis = auditor._analyze_workflow_file(workflow_file)

            assert analysis["valid_yaml"] is True
            assert analysis["name"] == "Test Workflow"
            assert "test" in analysis["jobs"]
            assert analysis["job_count"] == 1

    def test_analyze_workflow_file_handles_invalid_yaml(self) -> None:
        """Test that workflow analysis handles invalid YAML gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "invalid.yml"
            workflow_file.write_text("invalid: yaml: content: [unclosed")

            auditor = GitHubIntegrationAuditor()
            analysis = auditor._analyze_workflow_file(workflow_file)

            assert analysis["valid_yaml"] is False
            assert "error" in analysis

    def test_analyze_workflow_file_extracts_python_version(self) -> None:
        """Test that workflow analysis extracts Python version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "python.yml"
            workflow_content = """
name: Python Tests
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
"""
            workflow_file.write_text(workflow_content)

            auditor = GitHubIntegrationAuditor()
            analysis = auditor._analyze_workflow_file(workflow_file)

            assert "3.12" in analysis.get("python_version", "")

    def test_analyze_workflow_file_identifies_actions(self) -> None:
        """Test that workflow analysis identifies used actions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "actions.yml"
            workflow_content = """
name: Actions Test
jobs:
  build:
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - uses: codecov/codecov-action@v3
 """
            workflow_file.write_text(workflow_content)

            auditor = GitHubIntegrationAuditor()
            analysis = auditor._analyze_workflow_file(workflow_file)

            actions = analysis.get("uses_actions", [])
            assert "actions/checkout@v3" in actions
            assert "actions/setup-python@v4" in actions
            assert "codecov/codecov-action@v3" in actions


class TestInstructionsAudit:
    """Test instructions audit functionality."""

    def test_audit_instructions_when_directory_missing(self) -> None:
        """Test instructions audit when directory is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_instructions()

            assert auditor.audit_results["instructions"]["status"] == "no_instructions_directory"

    def test_audit_instructions_finds_markdown_files(self) -> None:
        """Test that instructions audit finds .md files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            instructions_dir = repo_root / ".github" / "instructions"
            instructions_dir.mkdir(parents=True)

            # Create test instruction files
            (instructions_dir / "README.instructions.md").write_text(
                "# Instructions\n\nTest content"
            )
            (instructions_dir / "GUIDE.instructions.md").write_text("# Guide\n\nMore content")

            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_instructions()

            assert "README.instructions.md" in auditor.audit_results["instructions"]
            assert "GUIDE.instructions.md" in auditor.audit_results["instructions"]


class TestPromptsAudit:
    """Test prompts audit functionality."""

    def test_audit_prompts_when_directory_missing(self) -> None:
        """Test prompts audit when directory is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_prompts()

            assert auditor.audit_results["prompts"]["status"] == "no_prompts_directory"

    def test_audit_prompts_finds_template_files(self) -> None:
        """Test that prompts audit finds template files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            prompts_dir = repo_root / ".github" / "prompts"
            prompts_dir.mkdir(parents=True)

            # Create test prompt files
            (prompts_dir / "system.prompt.md").write_text("System prompt template")
            (prompts_dir / "user.prompt.md").write_text("User prompt template")

            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            auditor._audit_prompts()

            assert "system.prompt.md" in auditor.audit_results["prompts"]
            assert "user.prompt.md" in auditor.audit_results["prompts"]


class TestComprehensiveAudit:
    """Test comprehensive audit workflow."""

    def test_run_comprehensive_audit_returns_dict(self) -> None:
        """Test that comprehensive audit returns results dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            auditor = GitHubIntegrationAuditor(repo_root=repo_root)
            results = auditor.run_comprehensive_audit()

            assert isinstance(results, dict)
            assert "timestamp" in results
            assert "workflows" in results
            assert "instructions" in results
            assert "prompts" in results

    def test_run_comprehensive_audit_handles_errors(self) -> None:
        """Test that comprehensive audit handles errors gracefully."""
        with patch.object(
            GitHubIntegrationAuditor,
            "_audit_directory_structure",
            side_effect=Exception("Test error"),
        ):
            auditor = GitHubIntegrationAuditor()
            results = auditor.run_comprehensive_audit()

            assert "error" in results
            assert "Test error" in results["error"]

    def test_run_comprehensive_audit_calls_all_phases(self) -> None:
        """Test that comprehensive audit calls all audit phases."""
        auditor = GitHubIntegrationAuditor()

        with (
            patch.object(auditor, "_audit_directory_structure") as mock_dir,
            patch.object(auditor, "_audit_workflows") as mock_workflows,
            patch.object(auditor, "_audit_instructions") as mock_instructions,
            patch.object(auditor, "_audit_prompts") as mock_prompts,
            patch.object(auditor, "_audit_infrastructure_integration") as mock_infra,
            patch.object(auditor, "_audit_documentation_completeness") as mock_docs,
            patch.object(auditor, "_generate_enhancement_recommendations") as mock_enhance,
            patch.object(auditor, "_create_audit_report") as mock_report,
        ):
            auditor.run_comprehensive_audit()

            mock_dir.assert_called_once()
            mock_workflows.assert_called_once()
            mock_instructions.assert_called_once()
            mock_prompts.assert_called_once()
            mock_infra.assert_called_once()
            mock_docs.assert_called_once()
            mock_enhance.assert_called_once()
            mock_report.assert_called_once()


class TestHelperMethods:
    """Test helper and utility methods."""

    def test_extract_used_actions_from_workflow_content(self) -> None:
        """Test extraction of GitHub Actions from workflow content."""
        auditor = GitHubIntegrationAuditor()
        content = """
steps:
  - uses: actions/checkout@v3
  - uses: actions/setup-python@v4
  - uses: codecov/codecov-action@v3
"""
        actions = auditor._extract_used_actions(content)

        assert "actions/checkout@v3" in actions
        assert "actions/setup-python@v4" in actions
        assert len(actions) >= 2

    def test_extract_python_version_from_workflow(self) -> None:
        """Test extraction of Python version from workflow content."""
        auditor = GitHubIntegrationAuditor()
        content = """
- uses: actions/setup-python@v4
  with:
    python-version: '3.12'
"""
        version = auditor._extract_python_version(content)
        assert "3.12" in version

    def test_extract_python_version_when_not_specified(self) -> None:
        """Test Python version extraction when not specified."""
        auditor = GitHubIntegrationAuditor()
        content = "steps:\n  - run: echo 'no python here'"
        version = auditor._extract_python_version(content)
        # Method returns None when no version found
        assert version is None or version == "not specified"

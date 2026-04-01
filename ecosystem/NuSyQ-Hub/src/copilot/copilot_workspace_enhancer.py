#!/usr/bin/env python3
"""Copilot Workspace Enhancer - VS Code Integration Optimizer.

Enhances GitHub Copilot functionality within the workspace context.

This module provides:
- Dynamic workspace configuration for Copilot
- Context-aware code suggestions
- Repository structure integration
- AI prompt optimization for domain-specific development
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import]

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CopilotWorkspaceEnhancer:
    """OmniTag: [workspace_enhancer, tagging, symbol_mapping].

    MegaTag: [COPILOT_INFRASTRUCTURE, SYSTEM_MAP, CONTEXT_AWARENESS]
    Enhanced GitHub Copilot integration for repository-aware development.
    Provides tagging, symbol mapping, and system mapping for advanced context propagation.
    """

    def __init__(self, workspace_path: Path) -> None:
        """Initialize enhancer with workspace path."""
        self.workspace_path = Path(workspace_path).resolve()
        self.copilot_config: dict[str, Any] = {}
        self.vscode_settings: dict[str, Any] = {}
        self.workspace_context: dict[str, Any] = {}

    VSCODE_DIRNAME = ".vscode"
    REQUIREMENTS_FILE = "requirements.txt"
    DOCS_DIR = "docs/"  # This line remains unchanged, but is included for context

    def enhance_workspace(self) -> dict[str, Any]:
        """Apply comprehensive Copilot enhancements to workspace.

        Returns:
            dict containing enhancement results and configuration

        """
        logger.info(f"Enhancing Copilot workspace integration for: {self.workspace_path}")

        results = {
            "workspace_path": str(self.workspace_path),
            "enhancements_applied": [],
            "configurations_updated": [],
            "context_mappings": {},
            "success": False,
        }

        try:
            # Core enhancement operations
            self.analyze_workspace_structure()
            self.update_copilot_yaml()
            self.configure_workspace_settings()
            self.setup_context_awareness()
            self.enhance_prompt_templates()
            self.configure_domain_specific_features()

            results["enhancements_applied"] = [
                "copilot_yaml_updated",
                "workspace_settings_configured",
                "context_awareness_enabled",
                "prompt_templates_enhanced",
                "domain_features_configured",
            ]
            results["success"] = True

        except Exception as e:
            logger.exception(f"Enhancement failed: {e}")
            results["error"] = str(e)

        try:
            from src.system.agent_awareness import emit as _emit

            _level = "INFO" if results["success"] else "ERROR"
            _count = len(results.get("enhancements_applied", []))
            _emit(
                "copilot",
                f"Workspace enhanced: {self.workspace_path.name} | enhancements={_count} success={results['success']}",
                level=_level,
                source="copilot_workspace_enhancer",
            )
        except Exception:
            pass

        return results

    def analyze_workspace_structure(self) -> None:
        """Analyze workspace structure to understand context."""
        logger.info("Analyzing workspace structure for Copilot context")

        self.workspace_context = {
            "project_type": self._detect_project_type(),
            "languages": self._detect_languages(),
            "frameworks": self._detect_frameworks(),
            "domains": self._detect_domains(),
            "structure_patterns": self._analyze_structure_patterns(),
            "dependency_context": self._analyze_dependencies(),
        }

        logger.info(f"Detected project context: {self.workspace_context['project_type']}")

    def update_copilot_yaml(self) -> None:
        """Update .github/copilot.yaml with repository-specific context."""
        copilot_yaml_path = self.workspace_path / ".github" / "copilot.yaml"

        # Ensure .github directory exists
        copilot_yaml_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate enhanced Copilot configuration
        enhanced_config = self._generate_copilot_config()

        # Save configuration
        with open(copilot_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(enhanced_config, f, default_flow_style=False, indent=2)

        self.copilot_config = enhanced_config
        logger.info(f"Updated Copilot configuration: {copilot_yaml_path}")

    def configure_workspace_settings(self) -> None:
        """Configure VS Code workspace settings for enhanced Copilot integration."""
        vscode_dir = self.workspace_path / self.VSCODE_DIRNAME
        settings_path = vscode_dir / "settings.json"
        # Ensure .vscode directory exists
        vscode_dir.mkdir(exist_ok=True)
        # Load existing settings or create new
        existing_settings: dict[str, Any] = {}
        if settings_path.exists():
            try:
                with open(settings_path, encoding="utf-8") as f:
                    existing_settings = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing settings: {e}")
        # Generate enhanced settings
        enhanced_settings = self._generate_vscode_settings(existing_settings)
        # Save enhanced settings
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(enhanced_settings, f, indent=2, ensure_ascii=False)
        self.vscode_settings = enhanced_settings
        logger.info(f"Updated VS Code settings: {settings_path}")

    def setup_context_awareness(self) -> None:
        """Setup context-aware features for repository-specific suggestions."""
        context_config = {
            "file_associations": self._generate_file_associations(),
            "language_patterns": self._generate_language_patterns(),
            "domain_keywords": self._generate_domain_keywords(),
            "project_conventions": self._detect_project_conventions(),
        }
        # Save context configuration
        context_path = self.workspace_path / self.VSCODE_DIRNAME / "copilot_context.json"
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump(context_config, f, indent=2, ensure_ascii=False)
        logger.info("Context awareness configuration created")

    def enhance_prompt_templates(self) -> None:
        """Create enhanced prompt templates for domain-specific development."""
        templates_dir = self.workspace_path / self.VSCODE_DIRNAME / "copilot_templates"
        templates_dir.mkdir(exist_ok=True)
        # Generate templates based on detected domains
        templates = self._generate_prompt_templates()
        for template_name, template_content in templates.items():
            template_path = templates_dir / f"{template_name}.md"
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content)
        logger.info(f"Created {len(templates)} prompt templates")

    def configure_domain_specific_features(self) -> None:
        """Configure domain-specific Copilot features."""
        domains = self.workspace_context.get("domains", [])

        for domain in domains:
            if domain == "quantum_computing":
                self._configure_quantum_features()
            elif domain == "ai_ml":
                self._configure_ai_ml_features()
            elif domain == "blockchain":
                self._configure_blockchain_features()
            elif domain == "consciousness_simulation":
                self._configure_consciousness_features()

        logger.info(f"Configured domain-specific features for: {', '.join(domains)}")

    def _detect_project_type(self) -> str:
        """Detect the primary project type."""
        indicators = {
            "python_ai_research": [
                "src/ai/",
                "src/ml/",
                "src/quantum/",
                self.REQUIREMENTS_FILE,
            ],
            "quantum_computing": ["src/quantum/", "quantum", "consciousness"],
            "multi_ai_system": ["src/ai/", "src/orchestration/", "copilot", "ollama"],
            "repository_management": ["src/utils/", "src/diagnostics/", "structure"],
            "python_application": ["src/", self.REQUIREMENTS_FILE, "*.py"],
            "documentation_system": [
                self.DOCS_DIR,
                "markdown",
                "notebooks/",
            ],  # Updated to use DOCS_DIR
        }

        for project_type, patterns in indicators.items():
            if self._check_patterns_exist(patterns):
                return project_type

        return "general_development"

    def _detect_languages(self) -> list[str]:
        """Detect programming languages in use."""
        extensions: dict[str, Any] = {}
        for file_path in self.workspace_path.rglob("*"):
            if file_path.is_file() and file_path.suffix:
                ext = file_path.suffix.lower()
                extensions[ext] = extensions.get(ext, 0) + 1

        # Map extensions to languages
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
            ".ps1": "powershell",
            ".sh": "bash",
            ".ipynb": "jupyter",
        }

        detected_languages: list[Any] = []
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
            if ext in language_map and count > 5:  # Threshold for significance
                detected_languages.append(language_map[ext])

        return detected_languages[:10]  # Top 10 languages

    def _detect_frameworks(self) -> list[str]:
        """Detect frameworks and libraries in use."""
        frameworks: list[Any] = []
        # Check for common framework indicators
        framework_indicators = {
            "fastapi": ["from fastapi", "import fastapi"],
            "flask": ["from flask", "import flask"],
            "django": ["django", "manage.py"],
            "pytest": ["pytest", "test_"],
            "jupyter": [".ipynb", "notebook"],
            "pandas": ["import pandas", "pd."],
            "numpy": ["import numpy", "np."],
            "pytorch": ["import torch", "pytorch"],
            "tensorflow": ["import tensorflow", "tf."],
            "copilot": ["copilot", "github copilot"],
        }

        # Search for indicators in Python files
        for file_path in self.workspace_path.rglob("*.py"):
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()

                for framework, indicators in framework_indicators.items():
                    if (
                        any(indicator in content for indicator in indicators)
                        and framework not in frameworks
                    ):
                        frameworks.append(framework)
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue

        return frameworks

    def _detect_domains(self) -> list[str]:
        """Detect specialized domains in the project."""
        domains: list[Any] = []
        domain_keywords = {
            "quantum_computing": ["quantum", "consciousness", "multidimensional"],
            "ai_ml": ["artificial intelligence", "machine learning", "neural", "llm"],
            "blockchain": ["blockchain", "crypto", "consensus"],
            "consciousness_simulation": ["consciousness", "cognitive", "transcendent"],
            "repository_management": ["repository", "git", "structure", "organization"],
            "automation": ["orchestration", "workflow", "automation", "ci/cd"],
            "diagnostics": ["diagnostic", "health", "monitoring", "analysis"],
        }

        # Check directory names and file content for domain indicators
        all_text = " ".join(
            [
                str(self.workspace_path).lower(),
                " ".join(p.name.lower() for p in self.workspace_path.rglob("*") if p.is_dir()),
            ]
        )

        for domain, keywords in domain_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                domains.append(domain)

        return domains

    def _detect_project_conventions(self) -> dict[str, Any]:
        """Detect common repository conventions and tooling signals."""
        return {
            "has_pyproject": (self.workspace_path / "pyproject.toml").exists(),
            "has_setup_cfg": (self.workspace_path / "setup.cfg").exists(),
            "has_tox": (self.workspace_path / "tox.ini").exists(),
            "has_editorconfig": (self.workspace_path / ".editorconfig").exists(),
            "has_precommit": (self.workspace_path / ".pre-commit-config.yaml").exists(),
            "has_ruff_config": (self.workspace_path / "ruff.toml").exists(),
            "has_mypy_config": (self.workspace_path / "mypy.ini").exists(),
            "has_docs": (self.workspace_path / "docs").exists(),
            "has_readme": (self.workspace_path / "README.md").exists(),
        }

    def _analyze_structure_patterns(self) -> dict[str, Any]:
        """Analyze repository structure patterns."""
        return {
            "src_structure": self._analyze_src_structure(),
            "documentation_patterns": self._analyze_documentation_patterns(),
            "configuration_patterns": self._analyze_configuration_patterns(),
            "testing_patterns": self._analyze_testing_patterns(),
        }

    def _analyze_dependencies(self) -> dict[str, list[str]]:
        """Analyze project dependencies."""
        return {
            "python": self._extract_python_dependencies(),
            "node": self._extract_node_dependencies(),
            "system": self._extract_system_dependencies(),
        }

    def _extract_system_dependencies(self) -> list[str]:
        """Extract basic system-level dependencies.

        Designed to be lightweight for test environments: we look for common
        infrastructure descriptors (Docker, Compose, or shell scripts) and
        return their names. If nothing is found, we safely return an empty
        list.
        """
        candidates: list[tuple[str, Path]] = []
        for filename in [
            "docker-compose.yml",
            "docker-compose.yaml",
            "Dockerfile",
            "Makefile",
            "start-dev.sh",
            "start-dev.js",
        ]:
            path = self.workspace_path / filename
            if path.exists():
                candidates.append((filename, path))

        dependencies: list[str] = []
        for name, path in candidates:
            dependencies.append(name)
            # For docker-compose, try to read service names (best-effort, safe)
            if name.startswith("docker-compose"):
                try:
                    with open(path, encoding="utf-8") as f:
                        content = yaml.safe_load(f) or {}
                    services = content.get("services", {})
                    dependencies.extend(list(services.keys())[:10])
                except (FileNotFoundError, yaml.YAMLError, OSError):
                    # Keep silent and continue with what we have
                    continue

        return dependencies

    def _generate_copilot_config(self) -> dict[str, Any]:
        """Generate enhanced Copilot YAML configuration."""
        return {
            "suggestions": {
                "enabled": True,
                "auto_trigger": True,
                "context_aware": True,
            },
            "completions": {
                "enabled": True,
                "inline": True,
                "multi_line": True,
            },
            "prompts": self._generate_copilot_prompts(),
            "file_associations": self._generate_file_associations(),
            "experimental_features": {
                "quantum_context": True,
                "consciousness_patterns": True,
                "multi_ai_orchestration": True,
            },
        }

    def _generate_vscode_settings(self, existing: dict) -> dict[str, Any]:
        """Generate enhanced VS Code settings."""
        enhanced = existing.copy()

        # Copilot-specific settings
        copilot_settings = {
            "github.copilot.enable": {
                "*": True,
                "python": True,
                "javascript": True,
                "typescript": True,
                "markdown": True,
                "yaml": True,
                "json": True,
            },
            "github.copilot.advanced": {
                "secret_key": "off",
                "length": 10000,
                "temperature": 0.1,
                "top_p": 1,
                "inlineSuggestEnable": True,
            },
            "editor.inlineSuggest.enabled": True,
            "editor.inlineSuggest.showToolbar": "always",
            "files.associations": self._generate_file_associations(),
        }

        # Language-specific settings based on detected languages
        if "python" in self.workspace_context.get("languages", []):
            copilot_settings.update(
                {
                    "python.defaultInterpreterPath": "./venv/bin/python",
                    "python.linting.enabled": True,
                    "python.linting.pylintEnabled": True,
                }
            )

        enhanced.update(copilot_settings)
        return enhanced

    def _generate_file_associations(self) -> dict[str, str]:
        """Generate file associations for domain-specific extensions."""
        return {
            "*.kilo": "python",
            "*.foolish": "python",
            "*.nusyq": "json",
            "*.quantum": "python",
            "*.consciousness": "python",
            "*.bridge": "yaml",
            "*.copilot": "yaml",
        }

    def _generate_language_patterns(self) -> dict[str, list[str]]:
        """Generate language-specific patterns for context."""
        return {
            "python": [
                "import",
                "from",
                "def",
                "class",
                "async def",
                "quantum",
                "consciousness",
                "ai",
                "copilot",
            ],
            "markdown": [
                "#",
                "##",
                "###",
                "```",
                "copilot",
                "instructions",
            ],
            "yaml": [
                "prompts:",
                "suggestions:",
                "completions:",
            ],
        }

    def _generate_domain_keywords(self) -> dict[str, list[str]]:
        """Generate domain-specific keywords for context."""
        return {
            "quantum": ["quantum", "superposition", "entanglement", "consciousness"],
            "ai": [
                "artificial intelligence",
                "machine learning",
                "neural network",
                "llm",
            ],
            "copilot": ["github copilot", "code suggestions", "ai assistant"],
            "repository": ["structure", "organization", "analysis", "health"],
        }

    def _generate_copilot_prompts(self) -> dict[str, str]:
        """Generate domain-specific Copilot prompts."""
        project_type = self.workspace_context.get("project_type", "general")
        domains = self.workspace_context.get("domains", [])

        prompts = {
            "context": f"This is a {project_type} project focusing on {', '.join(domains)}",
            "style": "Use quantum-inspired patterns and consciousness-aware development approaches",
            "conventions": "Follow repository structure patterns and maintain integration with existing AI systems",
        }

        if "quantum_computing" in domains:
            prompts["quantum"] = (
                "Implement quantum computing concepts with consciousness simulation patterns"
            )

        if "ai_ml" in domains:
            prompts["ai"] = "Integrate with existing AI orchestration and multi-LLM systems"

        return prompts

    def _generate_prompt_templates(self) -> dict[str, str]:
        """Generate prompt templates for common tasks."""
        templates: dict[str, Any] = {}
        # Base template
        templates[
            "base"
        ] = """# Copilot Context Template

## Project Context

## Development Guidelines

## Code Style
"""
        # Domain-specific templates
        if "quantum_computing" in self.workspace_context.get("domains", []):
            templates[
                "quantum"
            ] = """# Quantum Computing Development

When implementing quantum computing features:
"""
        if "ai_ml" in self.workspace_context.get("domains", []):
            templates[
                "ai"
            ] = """# AI/ML Development

When implementing AI/ML features:
"""
        return templates

    def _configure_quantum_features(self) -> None:
        """Configure quantum computing specific features."""
        quantum_config = {
            "quantum_patterns": True,
            "consciousness_simulation": True,
            "multidimensional_processing": True,
        }
        config_path = self.workspace_path / self.VSCODE_DIRNAME / "quantum_copilot.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(quantum_config, f, indent=2)

    def _configure_ai_ml_features(self) -> None:
        """Configure AI/ML specific features."""
        ai_config = {
            "multi_llm_integration": True,
            "ai_orchestration_patterns": True,
            "consciousness_bridges": True,
        }
        config_path = self.workspace_path / self.VSCODE_DIRNAME / "ai_copilot.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(ai_config, f, indent=2)

    def _configure_blockchain_features(self) -> None:
        """Configure blockchain specific features."""
        blockchain_config = {
            "quantum_blockchain_patterns": True,
            "consensus_mechanisms": True,
            "consciousness_integration": True,
        }
        config_path = self.workspace_path / self.VSCODE_DIRNAME / "blockchain_copilot.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(blockchain_config, f, indent=2)

    def _configure_consciousness_features(self) -> None:
        """Configure consciousness simulation specific features."""
        consciousness_config = {
            "transcendent_patterns": True,
            "reality_weaving": True,
            "consciousness_bridges": True,
        }
        config_path = self.workspace_path / self.VSCODE_DIRNAME / "consciousness_copilot.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(consciousness_config, f, indent=2)

    # Helper methods for analysis
    def _check_patterns_exist(self, patterns: list[str]) -> bool:
        """Check if file/directory patterns exist in workspace."""
        for pattern in patterns:
            if "*" in pattern:
                if list(self.workspace_path.rglob(pattern)):
                    return True
            elif (self.workspace_path / pattern).exists():
                return True
        return False

    def _analyze_src_structure(self) -> dict[str, Any]:
        """Analyze src directory structure."""
        src_path = self.workspace_path / "src"
        if not src_path.exists():
            return {}

        subdirs = [d.name for d in src_path.iterdir() if d.is_dir()]
        return {
            "subdirectories": subdirs,
            "has_modular_structure": len(subdirs) > 3,
            "patterns": self._detect_structural_patterns(subdirs),
        }

    def _analyze_documentation_patterns(self) -> dict[str, Any]:
        """Analyze documentation structure."""
        return {
            "has_docs_directory": (self.workspace_path / self.DOCS_DIR).exists(),
            "markdown_files": len(list(self.workspace_path.rglob("*.md"))),
            "documentation_level": (
                "comprehensive"
                if self._check_patterns_exist([self.DOCS_DIR, "notebooks/"])
                else "basic"
            ),
        }

    def _analyze_configuration_patterns(self) -> dict[str, Any]:
        """Analyze configuration file patterns."""
        config_files = [
            ".github/",
            "config/",
            self.VSCODE_DIRNAME,
            self.REQUIREMENTS_FILE,
            "package.json",
            "*.yml",
            "*.yaml",
        ]
        return {
            "has_github_config": (self.workspace_path / ".github").exists(),
            "has_vscode_config": (self.workspace_path / self.VSCODE_DIRNAME).exists(),
            "config_sophistication": (
                "advanced" if self._check_patterns_exist(config_files[:3]) else "basic"
            ),
        }

    def _analyze_testing_patterns(self) -> dict[str, Any]:
        """Analyze testing structure."""
        return {
            "has_test_directory": (self.workspace_path / "tests").exists(),
            "test_files": len(list(self.workspace_path.rglob("test_*.py")))
            + len(list(self.workspace_path.rglob("*_test.py"))),
            "testing_framework": (
                "pytest" if self._check_patterns_exist(["pytest"]) else "unittest"
            ),
        }

    def _extract_python_dependencies(self) -> list[str]:
        """Extract Python dependencies from requirements files."""
        deps: list[Any] = []
        for req_file in [self.REQUIREMENTS_FILE, "pyproject.toml", "Pipfile"]:
            req_path = self.workspace_path / req_file
            if req_path.exists():
                try:
                    with open(req_path, encoding="utf-8") as f:
                        content = f.read()
                        # Basic extraction (could be more sophisticated)
                        lines = [line.strip() for line in content.split("\n") if line.strip()]
                        deps.extend(lines[:20])  # First 20 lines
                except (FileNotFoundError, UnicodeDecodeError, OSError):
                    continue
        return deps

    def _extract_node_dependencies(self) -> list[str]:
        """OmniTag: [node_dependency_extraction, context_mapping].

        MegaTag: [WORKSPACE_ENHANCEMENT, SYSTEM_DISCOVERY]
        Extract Node.js dependencies for workspace mapping and context propagation.
        """
        package_json = self.workspace_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, encoding="utf-8") as f:
                    data = json.load(f)
                    deps = list(data.get("dependencies", {}).keys())
                    dev_deps = list(data.get("devDependencies", {}).keys())
                    return deps + dev_deps
            except Exception as e:
                # Enhanced: Log the error for debugging
                import logging

                logging.warning(f"Failed to extract Node.js dependencies from {package_json}: {e}")
        return []

    def _detect_structural_patterns(self, subdirs: list[str]) -> list[str]:
        """OmniTag: [structural_pattern_detection, system_mapping].

        MegaTag: [PATTERN_DISCOVERY, CONTEXT_PROPAGATION]
        Detect common structural patterns in subdirectories for system mapping.
        """
        patterns: list[Any] = []
        common_patterns = {
            "mvc": ["models", "views", "controllers"],
            "layered": ["data", "business", "presentation"],
            "domain": ["ai", "quantum", "consciousness"],
            "feature": ["user", "auth", "admin"],
            "technical": ["utils", "config", "core"],
        }

        for pattern_name, pattern_dirs in common_patterns.items():
            if any(pdir in subdirs for pdir in pattern_dirs):
                patterns.append(pattern_name)

        return patterns


def main() -> None:
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Enhance Copilot workspace integration")
    parser.add_argument(
        "--workspace",
        "-w",
        type=Path,
        default=Path.cwd(),
        help="Workspace path (default: current directory)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    enhancer = CopilotWorkspaceEnhancer(args.workspace)
    results = enhancer.enhance_workspace()

    if results["success"]:
        for _enhancement in results["enhancements_applied"]:
            pass
    else:
        pass


if __name__ == "__main__":
    main()

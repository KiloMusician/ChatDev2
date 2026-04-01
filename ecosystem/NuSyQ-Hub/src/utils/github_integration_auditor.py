import logging

logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""🔍 GitHub Integration Comprehensive Auditor & Enhancer.

PRESERVATION FIX: 2025-08-05 - Creating comprehensive GitHub integration audit system
RATIONALE: Preserving existing GitHub infrastructure while adding comprehensive audit capabilities
CHANGE: Adding new audit system without modifying existing files
PRESERVED: All existing .github configurations and workflows intact

# 🏷️ OmniTag
purpose: github_integration_audit_enhancement
dependencies:
  - yaml_processing
  - markdown_analysis
  - workflow_validation
context: Comprehensive GitHub integration audit and enhancement system
evolution_stage: v1.0_initial_implementation
metadata:
  component: github_integration_auditor
  file_type: utility_system
  integration_level: comprehensive
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Import existing infrastructure
try:
    from src.LOGGING.modular_logging_system import log_error, log_info
except ImportError:
    # Fallback logging if main system unavailable
    def log_info(tag: str, message: str) -> None:
        pass

    def log_warning(tag: str, message: str) -> None:
        pass

    def log_error(tag: str, message: str) -> None:
        pass


class GitHubIntegrationAuditor:
    """🔍 Comprehensive GitHub Integration Auditor & Enhancer.

    Features:
    - Workflow validation and analysis
    - Instructions consistency checking
    - Prompts template verification
    - Infrastructure integration assessment
    - Documentation completeness audit
    - Enhancement recommendations
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize GitHub Integration Auditor."""
        self.repo_root = repo_root or Path.cwd()
        self.github_dir = self.repo_root / ".github"
        self.workflows_dir = self.github_dir / "workflows"
        self.instructions_dir = self.github_dir / "instructions"
        self.prompts_dir = self.github_dir / "prompts"

        # Infrastructure integration points
        self.src_dir = self.repo_root / "src"
        self.docs_dir = self.repo_root / "docs"
        self.logging_dir = self.repo_root / "LOGGING"

        # Audit results storage
        self.audit_results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "workflows": {},
            "instructions": {},
            "prompts": {},
            "integration": {},
            "recommendations": [],
            "issues": [],
            "enhancements": [],
        }

        log_info(
            "GitHubAuditor",
            f"🔍 Initialized GitHub Integration Auditor for {self.repo_root}",
        )

    def run_comprehensive_audit(self) -> dict[str, Any]:
        """🎯 Run comprehensive GitHub integration audit.

        Returns:
            dict containing complete audit results and recommendations

        """
        log_info("GitHubAuditor", "🚀 Starting comprehensive GitHub integration audit...")

        try:
            # Phase 1: Directory Structure Audit
            self._audit_directory_structure()

            # Phase 2: Workflow Analysis
            self._audit_workflows()

            # Phase 3: Instructions Validation
            self._audit_instructions()

            # Phase 4: Prompts Assessment
            self._audit_prompts()

            # Phase 5: Infrastructure Integration Check
            self._audit_infrastructure_integration()

            # Phase 6: Documentation Completeness
            self._audit_documentation_completeness()

            # Phase 7: Generate Enhancement Recommendations
            self._generate_enhancement_recommendations()

            # Phase 8: Create Audit Report
            self._create_audit_report()

            log_info("GitHubAuditor", "✅ Comprehensive audit completed successfully!")
            return self.audit_results

        except Exception as e:
            log_error("GitHubAuditor", f"❌ Audit failed: {e!s}")
            self.audit_results["error"] = str(e)
            return self.audit_results

    def _audit_directory_structure(self) -> None:
        """🏗️ Audit GitHub directory structure."""
        log_info("GitHubAuditor", "📁 Auditing directory structure...")

        structure_check = {
            "github_dir_exists": self.github_dir.exists(),
            "workflows_dir_exists": self.workflows_dir.exists(),
            "instructions_dir_exists": self.instructions_dir.exists(),
            "prompts_dir_exists": self.prompts_dir.exists(),
            "subdirectories": [],
        }

        if self.github_dir.exists():
            for item in self.github_dir.iterdir():
                if item.is_dir():
                    structure_check["subdirectories"].append(
                        {
                            "name": item.name,
                            "path": str(item.relative_to(self.repo_root)),
                            "file_count": (len(list(item.glob("*"))) if item.exists() else 0),
                            "context_file_exists": (
                                item / f"{item.name.upper()}_CONTEXT.md"
                            ).exists(),
                        }
                    )

        self.audit_results["structure"] = structure_check

    def _audit_workflows(self) -> None:
        """⚙️ Audit GitHub Actions workflows."""
        log_info("GitHubAuditor", "⚙️ Auditing GitHub Actions workflows...")

        if not self.workflows_dir.exists():
            self.audit_results["workflows"]["status"] = "no_workflows_directory"
            self.audit_results["issues"].append("❌ .github/workflows directory does not exist")
            return

        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(
            self.workflows_dir.glob("*.yaml")
        )

        for workflow_file in workflow_files:
            workflow_analysis = self._analyze_workflow_file(workflow_file)
            self.audit_results["workflows"][workflow_file.name] = workflow_analysis

        # Check for essential workflows
        essential_workflows = ["security-scan", "coverage-verification", "ci", "test"]
        existing_workflows = [f.stem for f in workflow_files]

        for essential in essential_workflows:
            if not any(essential in existing for existing in existing_workflows):
                self.audit_results["recommendations"].append(
                    f"💡 Consider adding {essential} workflow for better automation",
                )

    def _analyze_workflow_file(self, workflow_file: Path) -> dict[str, Any]:
        """🔍 Analyze individual workflow file."""
        try:
            with open(workflow_file, encoding="utf-8") as f:
                workflow_content = f.read()
                workflow_data = yaml.safe_load(workflow_content)

            analysis = {
                "valid_yaml": True,
                "name": workflow_data.get("name", "Unnamed"),
                "triggers": workflow_data.get("on", {}),
                "jobs": list(workflow_data.get("jobs", {}).keys()),
                "job_count": len(workflow_data.get("jobs", {})),
                "uses_actions": self._extract_used_actions(workflow_content),
                "python_version": self._extract_python_version(workflow_content),
                "permissions": workflow_data.get("permissions", {}),
                "integration_points": self._identify_integration_points(workflow_content),
                "issues": [],
                "recommendations": [],
            }

            # Validate workflow structure
            self._validate_workflow_structure(workflow_data, analysis)

            return analysis

        except yaml.YAMLError as e:
            return {
                "valid_yaml": False,
                "error": str(e),
                "issues": [f"❌ Invalid YAML syntax: {e!s}"],
            }
        except Exception as e:
            return {
                "valid_yaml": False,
                "error": str(e),
                "issues": [f"❌ Failed to analyze workflow: {e!s}"],
            }

    def _extract_used_actions(self, content: str) -> list[str]:
        """📝 Extract GitHub Actions used in workflow."""
        action_pattern = r"uses:\s*([^\s\n]+)"
        return re.findall(action_pattern, content)

    def _extract_python_version(self, content: str) -> str:
        """🐍 Extract Python version from workflow."""
        python_pattern = r'python-version:\s*[\'"]?([0-9.]+)[\'"]?'
        match = re.search(python_pattern, content)
        return match.group(1) if match else None

    def _identify_integration_points(self, content: str) -> list[str]:
        """🔗 Identify integration points with KILO-FOOLISH infrastructure."""
        integration_points: list[Any] = []
        # Check for src/ directory references
        if "src/" in content:
            integration_points.append("src_directory_integration")

        # Check for specific system integrations
        system_patterns = {
            "orchestration": r"src/orchestration",
            "ai_systems": r"src/ai",
            "logging": r"LOGGING/infrastructure",
            "consciousness": r"src/consciousness",
            "chatdev": r"chatdev",
            "ollama": r"ollama",
        }

        for system, pattern in system_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                integration_points.append(system)

        return integration_points

    def _validate_workflow_structure(self, workflow_data: dict, analysis: dict) -> None:
        """✅ Validate workflow structure and add recommendations."""
        # Check for required fields
        if "name" not in workflow_data:
            analysis["issues"].append("❌ Workflow missing 'name' field")

        if "on" not in workflow_data:
            analysis["issues"].append("❌ Workflow missing trigger configuration ('on' field)")

        if "jobs" not in workflow_data or not workflow_data["jobs"]:
            analysis["issues"].append("❌ Workflow has no jobs defined")

        # Check for security best practices
        jobs = workflow_data.get("jobs", {})
        for job_name, job_config in jobs.items():
            if "runs-on" not in job_config:
                analysis["issues"].append(f"❌ Job '{job_name}' missing 'runs-on' field")

            # Check for permissions
            if "permissions" not in job_config and "permissions" not in workflow_data:
                analysis["recommendations"].append(
                    f"💡 Consider adding explicit permissions for job '{job_name}'",
                )

    def _audit_instructions(self) -> None:
        """📋 Audit GitHub instructions."""
        log_info("GitHubAuditor", "📋 Auditing GitHub instructions...")

        if not self.instructions_dir.exists():
            self.audit_results["instructions"]["status"] = "no_instructions_directory"
            self.audit_results["issues"].append("❌ .github/instructions directory does not exist")
            return

        instruction_files = list(self.instructions_dir.glob("*.md"))

        for instruction_file in instruction_files:
            instruction_analysis = self._analyze_instruction_file(instruction_file)
            self.audit_results["instructions"][instruction_file.name] = instruction_analysis

        # Check for essential instruction files
        essential_instructions = [
            "COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
            "FILE_PRESERVATION_MANDATE.instructions.md",
            "NuSyQ-Hub_INSTRUCTIONS.instructions.md",
        ]

        existing_instructions = [f.name for f in instruction_files]

        for essential in essential_instructions:
            if essential not in existing_instructions:
                self.audit_results["recommendations"].append(
                    f"💡 Essential instruction file missing: {essential}",
                )

    def _analyze_instruction_file(self, instruction_file: Path) -> dict[str, Any]:
        """📝 Analyze individual instruction file."""
        try:
            content = instruction_file.read_text(encoding="utf-8")

            analysis = {
                "file_size": len(content),
                "line_count": len(content.splitlines()),
                "has_yaml_frontmatter": content.startswith("---"),
                "sections": self._extract_markdown_sections(content),
                "integration_references": self._find_integration_references(content),
                "tag_usage": self._analyze_tag_usage(content),
                "issues": [],
                "recommendations": [],
            }

            # Validate instruction structure
            self._validate_instruction_structure(content, analysis)

            return analysis

        except Exception as e:
            return {
                "error": str(e),
                "issues": [f"❌ Failed to analyze instruction file: {e!s}"],
            }

    def _extract_markdown_sections(self, content: str) -> list[str]:
        """📑 Extract markdown section headers."""
        section_pattern = r"^#{1,6}\s+(.+)$"
        return re.findall(section_pattern, content, re.MULTILINE)

    def _find_integration_references(self, content: str) -> list[str]:
        """🔗 Find references to KILO-FOOLISH infrastructure."""
        integration_refs: list[Any] = []
        # Common integration patterns
        patterns = {
            "src_core": r"src/core",
            "src_ai": r"src/ai",
            "logging_system": r"LOGGING/infrastructure",
            "copilot_bridge": r"copilot_enhancement_bridge",
            "chatdev": r"ChatDev",
            "ollama": r"Ollama",
            "quantum": r"quantum",
            "consciousness": r"consciousness",
        }

        for ref_type, pattern in patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                integration_refs.append(ref_type)

        return integration_refs

    def _analyze_tag_usage(self, content: str) -> dict[str, Any]:
        """🏷️ Analyze OmniTag/MegaTag usage."""
        tag_analysis = {
            "has_omnitag": "OmniTag" in content or "omnitag" in content.lower(),
            "has_megatag": "MegaTag" in content or "megatag" in content.lower(),
            "has_rshts": "RSHTS" in content,
            "tag_sections": [],
        }

        # Find tag sections
        tag_section_pattern = r"(?:### \*\*(?:OmniTag|MegaTag|RSHTS)\*\*|## 🏷️ Semantic Tags)"
        if re.search(tag_section_pattern, content):
            tag_analysis["tag_sections"] = re.findall(tag_section_pattern, content)

        return tag_analysis

    def _validate_instruction_structure(self, _content: str, analysis: dict) -> None:
        """✅ Validate instruction file structure."""
        # Check for YAML frontmatter
        if not analysis["has_yaml_frontmatter"]:
            analysis["recommendations"].append(
                "💡 Consider adding YAML frontmatter with applyTo and priority fields",
            )

        # Check for essential sections
        essential_sections = ["Philosophy", "Guidelines", "Principles"]
        sections = [s.lower() for s in analysis["sections"]]

        for essential in essential_sections:
            if not any(essential.lower() in section for section in sections):
                analysis["recommendations"].append(
                    f"💡 Consider adding {essential} section for better structure",
                )

        # Check for tag usage
        if not analysis["tag_usage"]["has_omnitag"]:
            analysis["recommendations"].append(
                "💡 Consider adding OmniTag for better semantic organization",
            )

    def _audit_prompts(self) -> None:
        """🎯 Audit GitHub prompts."""
        log_info("GitHubAuditor", "🎯 Auditing GitHub prompts...")

        if not self.prompts_dir.exists():
            self.audit_results["prompts"]["status"] = "no_prompts_directory"
            self.audit_results["issues"].append("❌ .github/prompts directory does not exist")
            return

        prompt_files = list(self.prompts_dir.glob("*.md"))

        for prompt_file in prompt_files:
            prompt_analysis = self._analyze_prompt_file(prompt_file)
            self.audit_results["prompts"][prompt_file.name] = prompt_analysis

    def _analyze_prompt_file(self, prompt_file: Path) -> dict[str, Any]:
        """🎯 Analyze individual prompt file."""
        try:
            content = prompt_file.read_text(encoding="utf-8")

            analysis = {
                "file_size": len(content),
                "line_count": len(content.splitlines()),
                "has_yaml_frontmatter": content.startswith("---"),
                "prompt_sections": self._extract_prompt_sections(content),
                "integration_references": self._find_integration_references(content),
                "directive_patterns": self._analyze_directive_patterns(content),
                "issues": [],
                "recommendations": [],
            }

            # Validate prompt structure
            self._validate_prompt_structure(content, analysis)

            return analysis

        except Exception as e:
            return {
                "error": str(e),
                "issues": [f"❌ Failed to analyze prompt file: {e!s}"],
            }

    def _extract_prompt_sections(self, content: str) -> list[str]:
        """📝 Extract prompt-specific sections."""
        # Look for directive sections
        directive_pattern = r"(?:DIRECTIVE|PRINCIPLE|MANDATE|PROTOCOL):\s*([^\n]+)"
        return re.findall(directive_pattern, content, re.IGNORECASE)

    def _analyze_directive_patterns(self, content: str) -> dict[str, int]:
        """🎯 Analyze directive and instruction patterns."""
        return {
            "directives": len(re.findall(r"DIRECTIVE", content, re.IGNORECASE)),
            "principles": len(re.findall(r"PRINCIPLE", content, re.IGNORECASE)),
            "mandates": len(re.findall(r"MANDATE", content, re.IGNORECASE)),
            "protocols": len(re.findall(r"PROTOCOL", content, re.IGNORECASE)),
            "examples": len(re.findall(r"Example|```", content, re.IGNORECASE)),
        }

    def _validate_prompt_structure(self, content: str, analysis: dict) -> None:
        """✅ Validate prompt file structure."""
        # Check for mode specification in frontmatter
        if analysis["has_yaml_frontmatter"]:
            try:
                frontmatter = content.split("---")[1]
                if "mode:" not in frontmatter:
                    analysis["recommendations"].append(
                        "💡 Consider specifying mode (ask, instruct, etc.) in frontmatter",
                    )
            except IndexError:
                logger.debug("Suppressed IndexError", exc_info=True)

        # Check for balanced directive structure
        directive_counts = analysis["directive_patterns"]
        if sum(directive_counts.values()) == 0:
            analysis["recommendations"].append(
                "💡 Consider adding clear directives or principles for better prompt structure",
            )

    def _audit_infrastructure_integration(self) -> None:
        """🔗 Audit integration with KILO-FOOLISH infrastructure."""
        log_info("GitHubAuditor", "🔗 Auditing infrastructure integration...")

        integration_check = {
            "src_integration": self._check_src_integration(),
            "logging_integration": self._check_logging_integration(),
            "docs_integration": self._check_docs_integration(),
            "ai_systems_integration": self._check_ai_systems_integration(),
            "workflow_automation": self._check_workflow_automation_integration(),
        }

        self.audit_results["integration"] = integration_check

    def _check_src_integration(self) -> dict[str, Any]:
        """🔍 Check integration with src/ directory systems."""
        integration_status = {
            "chatdev_launcher_available": (
                self.src_dir / "integration" / "chatdev_launcher.py"
            ).exists(),
            "testing_chamber_available": (
                self.src_dir / "orchestration" / "chatdev_testing_chamber.py"
            ).exists(),
            "quantum_automator_available": (
                self.src_dir / "orchestration" / "quantum_workflow_automation.py"
            ).exists(),
            "ollama_integrator_available": (
                self.src_dir / "ai" / "ollama_chatdev_integrator.py"
            ).exists(),
            "ai_coordinator_available": (self.src_dir / "core" / "ai_coordinator.py").exists(),
        }

        # Check for references in GitHub files
        github_files = list(self.github_dir.rglob("*.md")) + list(self.github_dir.rglob("*.yml"))
        integration_references = 0

        for file in github_files:
            try:
                content = file.read_text(encoding="utf-8")
                if "src/" in content:
                    integration_references += 1
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue

        integration_status["github_references_to_src"] = integration_references
        integration_status["integration_level"] = (
            "high"
            if integration_references > 5
            else "medium" if integration_references > 2 else "low"
        )

        return integration_status

    def _check_logging_integration(self) -> dict[str, Any]:
        """📊 Check integration with logging system."""
        return {
            "logging_infrastructure_exists": (self.logging_dir / "infrastructure").exists(),
            "modular_logging_available": (
                self.logging_dir / "infrastructure" / "modular_logging_system.py"
            ).exists(),
            "logs_storage_exists": (self.repo_root / "logs" / "storage").exists(),
            "github_logging_references": self._count_file_references(
                self.github_dir, ["LOGGING", "modular_logging"]
            ),
        }

    def _check_docs_integration(self) -> dict[str, Any]:
        """📚 Check integration with documentation system."""
        return {
            "docs_directory_exists": self.docs_dir.exists(),
            "architecture_codex_exists": (
                self.docs_dir / "REPOSITORY_ARCHITECTURE_CODEX.yaml"
            ).exists(),
            "github_context_files": len(list(self.github_dir.rglob("*CONTEXT*.md"))),
            "docs_references_in_github": self._count_file_references(
                self.github_dir, ["docs/", "documentation"]
            ),
        }

    def _check_ai_systems_integration(self) -> dict[str, Any]:
        """🤖 Check integration with AI systems."""
        ai_systems = ["ChatDev", "Ollama", "copilot", "consciousness", "quantum"]
        return {
            "ai_system_references": {
                system: self._count_file_references(self.github_dir, [system])
                for system in ai_systems
            },
            "copilot_config_available": (
                self.instructions_dir / "COPILOT_INSTRUCTIONS_CONFIG.instructions.md"
            ).exists(),
            "ai_prompt_templates": (
                len(list(self.prompts_dir.glob("*.md"))) if self.prompts_dir.exists() else 0
            ),
        }

    def _check_workflow_automation_integration(self) -> dict[str, Any]:
        """⚙️ Check workflow automation integration."""
        return {
            "workflow_count": (
                len(list(self.workflows_dir.glob("*.yml"))) if self.workflows_dir.exists() else 0
            ),
            "automation_references": self._count_file_references(
                self.github_dir, ["automation", "orchestration", "workflow"]
            ),
            "quantum_workflow_integration": self._count_file_references(
                self.github_dir, ["quantum_workflow", "quantum_automator"]
            ),
        }

    def _count_file_references(self, directory: Path, search_terms: list[str]) -> int:
        """📊 Count references to specific terms in directory files."""
        count = 0
        for file in directory.rglob("*.md"):
            try:
                content = file.read_text(encoding="utf-8").lower()
                for term in search_terms:
                    count += content.count(term.lower())
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue
        return count

    def _audit_documentation_completeness(self) -> None:
        """📚 Audit documentation completeness."""
        log_info("GitHubAuditor", "📚 Auditing documentation completeness...")

        completeness_check = {
            "main_context_file": (self.github_dir / "GITHUB_INTEGRATION_CONTEXT.md").exists(),
            "subdirectory_contexts": {},
            "readme_files": {},
            "missing_documentation": [],
        }

        # Check subdirectory context files
        for subdir in ["workflows", "instructions", "prompts"]:
            subdir_path = self.github_dir / subdir
            if subdir_path.exists():
                context_file = subdir_path / f"GITHUB_{subdir.upper()}_CONTEXT.md"
                completeness_check["subdirectory_contexts"][subdir] = context_file.exists()

                if not context_file.exists():
                    completeness_check["missing_documentation"].append(
                        f"Missing context file: {context_file}"
                    )

        self.audit_results["documentation_completeness"] = completeness_check

    def _generate_enhancement_recommendations(self) -> None:
        """💡 Generate comprehensive enhancement recommendations."""
        log_info("GitHubAuditor", "💡 Generating enhancement recommendations...")

        recommendations: list[Any] = []
        # Workflow enhancements
        if len(self.audit_results.get("workflows", {})) < 3:
            recommendations.append(
                {
                    "category": "workflows",
                    "priority": "high",
                    "title": "Expand GitHub Actions Workflows",
                    "description": (
                        "Add comprehensive CI/CD workflows for testing, deployment, and automation"
                    ),
                    "implementation": (
                        "Create additional .yml files in .github/workflows/ for comprehensive automation"
                    ),
                }
            )

        # Infrastructure integration enhancements
        integration_level = (
            self.audit_results.get("integration", {})
            .get("src_integration", {})
            .get("integration_level", "low")
        )
        if integration_level != "high":
            recommendations.append(
                {
                    "category": "integration",
                    "priority": "high",
                    "title": "Enhance Infrastructure Integration",
                    "description": (
                        "Improve integration between GitHub automation and KILO-FOOLISH infrastructure"
                    ),
                    "implementation": (
                        "Add more references to src/ systems in workflows and instructions"
                    ),
                }
            )

        # Documentation enhancements
        missing_docs = self.audit_results.get("documentation_completeness", {}).get(
            "missing_documentation", []
        )
        if missing_docs:
            recommendations.append(
                {
                    "category": "documentation",
                    "priority": "medium",
                    "title": "Complete Documentation Coverage",
                    "description": (f"Add missing documentation files: {' '.join(missing_docs)}"),
                    "implementation": (
                        "Create comprehensive context files for all GitHub subdirectories"
                    ),
                }
            )

        # AI integration enhancements
        ai_references = (
            self.audit_results.get("integration", {})
            .get("ai_systems_integration", {})
            .get("ai_system_references", {})
        )
        if sum(ai_references.values()) < 10:
            recommendations.append(
                {
                    "category": "ai_integration",
                    "priority": "medium",
                    "title": "Enhance AI Systems Integration",
                    "description": (
                        "Improve integration with ChatDev, Ollama, and other AI systems"
                    ),
                    "implementation": (
                        "Add AI system references and automation in GitHub workflows"
                    ),
                }
            )

        self.audit_results["enhancement_recommendations"] = recommendations

    def _create_audit_report(self) -> None:
        """📋 Create comprehensive audit report."""
        report_path = (
            self.repo_root
            / "docs"
            / "reports"
            / (f"github_integration_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Build report content
        exec_summary_status = f"""
- **Workflows**: {len(self.audit_results.get("workflows", {}))} files analyzed
- **Instructions**: {len(self.audit_results.get("instructions", {}))} files analyzed
- **Prompts**: {len(self.audit_results.get("prompts", {}))} files analyzed
- **Issues Found**: {len(self.audit_results.get("issues", []))}
- **Recommendations**: {len(self.audit_results.get("enhancement_recommendations", []))}
"""

        integration_level = (
            self.audit_results.get("integration", {})
            .get("src_integration", {})
            .get("integration_level", "unknown")
            .title()
        )
        doc_coverage = (
            "Complete"
            if not self.audit_results.get("documentation_completeness", {}).get(
                "missing_documentation"
            )
            else "Partial"
        )
        ai_integration = (
            "High"
            if sum(
                self.audit_results.get("integration", {})
                .get("ai_systems_integration", {})
                .get("ai_system_references", {})
                .values()
            )
            > 10
            else "Medium"
        )

        report_content = f"""# 🔍 GitHub Integration Comprehensive Audit Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Repository**: KILO-FOOLISH NuSyQ-Hub
**Audit Scope**: Complete .github directory analysis and recommendations

---

## 📊 Executive Summary

### 🎯 Overall Status{exec_summary_status}
### 🔗 Integration Level
- **Infrastructure Integration**: {integration_level}
- **Documentation Coverage**: {doc_coverage}
- **AI Systems Integration**: {ai_integration}

---

## 🔧 Detailed Findings

### ⚙️ GitHub Actions Workflows
{self._format_workflow_findings()}

### 📋 Instructions Analysis
{self._format_instructions_findings()}

### 🎯 Prompts Assessment
{self._format_prompts_findings()}

### 🔗 Infrastructure Integration
{self._format_integration_findings()}

---

## 💡 Enhancement Recommendations

{self._format_enhancement_recommendations()}

---

## 🚨 Issues Requiring Attention

{self._format_issues_list()}

---

## 📈 Next Steps

1. **Immediate Actions**: Address critical issues and missing components
2. **Infrastructure Enhancement**: Improve integration with KILO-FOOLISH systems
3. **Documentation Completion**: Fill gaps in context documentation
4. **Workflow Expansion**: Add comprehensive automation workflows
5. **AI Integration**: Enhance AI system connectivity and automation

---

*Generated by KILO-FOOLISH GitHub Integration Auditor v1.0*
*Mission: Comprehensive GitHub integration analysis and enhancement*
"""

        report_path.write_text(report_content, encoding="utf-8")
        log_info("GitHubAuditor", f"📋 Audit report created: {report_path}")

        self.audit_results["report_path"] = str(report_path)

    def _format_workflow_findings(self) -> str:
        """Format workflow findings for report."""
        if not self.audit_results.get("workflows"):
            return "❌ No workflows found or analyzed"

        findings: list[Any] = []
        for workflow_name, analysis in self.audit_results["workflows"].items():
            if workflow_name == "status":
                continue

            status = "✅" if analysis.get("valid_yaml", False) else "❌"
            findings.append(f"- **{workflow_name}** {status}")

            if analysis.get("issues"):
                for issue in analysis["issues"]:
                    findings.append(f"  - {issue}")

        return "\n".join(findings) if findings else "✅ All workflows validated successfully"

    def _format_instructions_findings(self) -> str:
        """Format instructions findings for report."""
        if not self.audit_results.get("instructions"):
            return "❌ No instructions found or analyzed"

        findings: list[Any] = []
        for instruction_name, analysis in self.audit_results["instructions"].items():
            if instruction_name == "status":
                continue

            findings.append(f"- **{instruction_name}**: {analysis.get('line_count', 0)} lines")

            if analysis.get("integration_references"):
                findings.append(
                    f"  - Integration refs: {', '.join(analysis['integration_references'])}"
                )

        return (
            "\n".join(findings) if findings else "Info: No detailed instruction analysis available"
        )

    def _format_prompts_findings(self) -> str:
        """Format prompts findings for report."""
        if not self.audit_results.get("prompts"):
            return "❌ No prompts found or analyzed"

        findings: list[Any] = []
        for prompt_name, analysis in self.audit_results["prompts"].items():
            if prompt_name == "status":
                continue

            findings.append(f"- **{prompt_name}**: {analysis.get('line_count', 0)} lines")

            directive_counts = analysis.get("directive_patterns", {})
            if directive_counts:
                total_directives = sum(directive_counts.values())
                findings.append(f"  - Directives: {total_directives}")

        return "\n".join(findings) if findings else "Info: No detailed prompt analysis available"

    def _format_integration_findings(self) -> str:
        """Format integration findings for report."""
        integration = self.audit_results.get("integration", {})
        findings: list[Any] = []
        src_integration = integration.get("src_integration", {})
        findings.append(
            f"- **Source Integration Level**: {src_integration.get('integration_level', 'unknown').title()}"
        )

        ai_integration = integration.get("ai_systems_integration", {})
        ai_refs = ai_integration.get("ai_system_references", {})
        if ai_refs:
            findings.append(f"- **AI System References**: {sum(ai_refs.values())} total")

        logging_integration = integration.get("logging_integration", {})
        if logging_integration.get("modular_logging_available"):
            findings.append("- **Logging System**: ✅ Available")

        return "\n".join(findings) if findings else "Info: No integration data available"

    def _format_enhancement_recommendations(self) -> str:
        """Format enhancement recommendations for report."""
        recommendations = self.audit_results.get("enhancement_recommendations", [])

        if not recommendations:
            return "✅ No specific enhancement recommendations at this time"

        formatted: list[Any] = []
        for rec in recommendations:
            priority_emoji = (
                "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            )
            formatted.append(f"### {priority_emoji} {rec['title']} ({rec['category'].title()})")
            formatted.append(f"**Description**: {rec['description']}")
            formatted.append(f"**Implementation**: {rec['implementation']}")
            formatted.append("")

        return "\n".join(formatted)

    def _format_issues_list(self) -> str:
        """Format issues list for report."""
        issues = self.audit_results.get("issues", [])

        if not issues:
            return "✅ No critical issues found"

        return "\n".join(f"- {issue}" for issue in issues)


def main():
    """🚀 Main execution function."""
    # Initialize auditor
    auditor = GitHubIntegrationAuditor()

    # Run comprehensive audit
    results = auditor.run_comprehensive_audit()

    # Display summary

    if results.get("report_path"):
        pass

    return results


if __name__ == "__main__":
    main()

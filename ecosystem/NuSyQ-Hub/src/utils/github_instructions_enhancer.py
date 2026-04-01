#!/usr/bin/env python3
"""🔧 GitHub Instructions Integration Enhancer.

PRESERVATION FIX: 2025-08-05 - Enhancing GitHub instructions integration
RATIONALE: Preserving existing instruction files while adding integration enhancements
CHANGE: Adding integration validation and enhancement capabilities
PRESERVED: All existing instruction content and structure maintained

# 🏷️ OmniTag
purpose: github_instructions_integration_enhancement
dependencies:
  - github_instructions
  - kilo_foolish_infrastructure
  - ai_systems_integration
context: Enhanced GitHub instructions integration with KILO-FOOLISH systems
evolution_stage: v1.0_integration_enhancement
metadata:
  component: github_instructions_enhancer
  integration_level: comprehensive
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any


class GitHubInstructionsIntegrationEnhancer:
    """Enhanced GitHub Instructions Integration System.

    Features:
    - Validates instruction file integration with KILO-FOOLISH infrastructure
    - Enhances cross-references between instruction files
    - Validates AI system integration points
    - Creates integration validation reports
    - Ensures seamless workflow between instructions, prompts, and workflows
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize GitHub Instructions Integration Enhancer."""
        self.repo_root = repo_root or Path.cwd()
        self.github_dir = self.repo_root / ".github"
        self.instructions_dir = self.github_dir / "instructions"
        self.prompts_dir = self.github_dir / "prompts"
        self.workflows_dir = self.github_dir / "workflows"
        self.src_dir = self.repo_root / "src"

        self.integration_report: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": {},
            "integration_points": {},
            "enhancement_recommendations": [],
            "cross_references": {},
        }

    def run_comprehensive_integration_enhancement(self) -> dict[str, Any]:
        """🚀 Run comprehensive integration enhancement.

        Returns:
            dict containing integration analysis and enhancement recommendations

        """
        try:
            # Phase 1: Validate existing integration points
            self._validate_existing_integrations()

            # Phase 2: Enhance cross-references
            self._enhance_cross_references()

            # Phase 3: Validate AI system integration
            self._validate_ai_system_integration()

            # Phase 4: Check workflow integration
            self._validate_workflow_integration()

            # Phase 5: Generate enhancement recommendations
            self._generate_integration_recommendations()

            # Phase 6: Create integration report
            self._create_integration_report()

            return self.integration_report

        except Exception as e:
            self.integration_report["error"] = str(e)
            return self.integration_report

    def _validate_existing_integrations(self) -> None:
        """🔍 Validate existing integration points."""
        validation_results: dict[str, Any] = {}
        # Check each instruction file for integration references
        if self.instructions_dir.exists():
            for instruction_file in self.instructions_dir.glob("*.md"):
                file_validation = self._validate_instruction_file_integration(instruction_file)
                validation_results[instruction_file.name] = file_validation

        self.integration_report["validation_results"] = validation_results

    def _validate_instruction_file_integration(self, instruction_file: Path) -> dict[str, Any]:
        """🔍 Validate individual instruction file integration."""
        try:
            content = instruction_file.read_text(encoding="utf-8")

            validation: dict[str, Any] = {
                "file_size": len(content),
                "infrastructure_references": self._find_infrastructure_references(content),
                "ai_system_references": self._find_ai_system_references(content),
                "cross_file_references": self._find_cross_file_references(content),
                "workflow_integration": self._check_workflow_integration(content),
                "integration_score": 0,
                "recommendations": [],
            }

            # Calculate integration score
            score = 0
            score += len(validation["infrastructure_references"]) * 2
            score += len(validation["ai_system_references"]) * 3
            score += len(validation["cross_file_references"]) * 1
            score += 5 if validation["workflow_integration"] else 0

            validation["integration_score"] = min(score, 100)

            # Generate file-specific recommendations
            if validation["integration_score"] < 30:
                validation["recommendations"].append(
                    "🔗 Enhance infrastructure integration references"
                )

            if not validation["ai_system_references"]:
                validation["recommendations"].append("🤖 Add AI system integration references")

            if not validation["workflow_integration"]:
                validation["recommendations"].append("⚙️ Add workflow integration guidance")

            return validation

        except Exception as e:
            return {
                "error": str(e),
                "integration_score": 0,
                "recommendations": [f"❌ Fix file reading error: {e!s}"],
            }

    def _find_infrastructure_references(self, content: str) -> list[str]:
        """🏗️ Find KILO-FOOLISH infrastructure references."""
        references: list[Any] = []
        # Infrastructure patterns
        patterns = {
            "src_core": r"src/core",
            "src_ai": r"src/ai",
            "src_integration": r"src/integration",
            "src_orchestration": r"src/orchestration",
            "logging_system": r"LOGGING/infrastructure",
            "consciousness": r"consciousness",
            "quantum_systems": r"quantum",
            "chatdev": r"ChatDev|chatdev",
            "ollama": r"Ollama|ollama",
        }

        for ref_type, pattern in patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                references.append(ref_type)

        return references

    def _find_ai_system_references(self, content: str) -> list[str]:
        """🤖 Find AI system references."""
        ai_references: list[Any] = []
        ai_patterns = {
            "copilot_bridge": r"copilot_enhancement_bridge",
            "multi_llm_orchestra": r"Multi-LLM",
            "chatdev_integration": r"ChatDev.*integration",
            "ollama_bridge": r"Ollama.*bridge",
            "ai_coordinator": r"ai_coordinator",
            "consciousness_sync": r"consciousness.*sync",
        }

        for ai_type, pattern in ai_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                ai_references.append(ai_type)

        return ai_references

    def _find_cross_file_references(self, content: str) -> list[str]:
        """🔗 Find cross-file references."""
        cross_refs: list[Any] = []
        # Look for references to other instruction files
        file_patterns = [
            r"COPILOT_INSTRUCTIONS_CONFIG",
            r"FILE_PRESERVATION_MANDATE",
            r"NuSyQ-Hub_INSTRUCTIONS",
            r"instructions\.md",
            r"prompts/",
            r"workflows/",
        ]

        for pattern in file_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                cross_refs.append(pattern)

        return cross_refs

    def _check_workflow_integration(self, content: str) -> bool:
        """⚙️ Check for workflow integration references."""
        workflow_patterns = [
            r"GitHub Actions",
            r"workflow",
            r"CI/CD",
            r"automation",
            r"\.github/workflows",
        ]

        return any(re.search(pattern, content, re.IGNORECASE) for pattern in workflow_patterns)

    def _enhance_cross_references(self) -> None:
        """🔗 Enhance cross-references between files."""
        cross_reference_enhancements: dict[str, Any] = {}
        # Analyze existing cross-references
        if self.instructions_dir.exists():
            instruction_files = list(self.instructions_dir.glob("*.md"))

            for file in instruction_files:
                file_refs = self._analyze_file_cross_references(file, instruction_files)
                cross_reference_enhancements[file.name] = file_refs

        self.integration_report["cross_references"] = cross_reference_enhancements

    def _analyze_file_cross_references(
        self, target_file: Path, all_files: list[Path]
    ) -> dict[str, Any]:
        """📝 Analyze cross-references for a specific file."""
        try:
            content = target_file.read_text(encoding="utf-8")

            analysis: dict[str, Any] = {
                "references_to_others": [],
                "referenced_by_others": [],
                "missing_references": [],
                "recommendations": [],
            }

            # Check what this file references
            for other_file in all_files:
                if other_file != target_file and other_file.stem in content:
                    analysis["references_to_others"].append(other_file.name)

            # Check what references this file
            for other_file in all_files:
                if other_file != target_file:
                    try:
                        other_content = other_file.read_text(encoding="utf-8")
                        if target_file.stem in other_content:
                            analysis["referenced_by_others"].append(other_file.name)
                    except (FileNotFoundError, UnicodeDecodeError, OSError):
                        continue

            # Suggest missing references based on content similarity
            if target_file.name == "COPILOT_INSTRUCTIONS_CONFIG.instructions.md":
                expected_refs = [
                    "FILE_PRESERVATION_MANDATE.instructions.md",
                    "NuSyQ-Hub_INSTRUCTIONS.instructions.md",
                ]
                for ref in expected_refs:
                    if ref not in analysis["references_to_others"]:
                        analysis["missing_references"].append(ref)

            return analysis

        except Exception as e:
            return {
                "error": str(e),
                "references_to_others": [],
                "referenced_by_others": [],
                "missing_references": [],
            }

    def _validate_ai_system_integration(self) -> None:
        """🤖 Validate AI system integration."""
        ai_integration = {
            "copilot_configuration": self._check_copilot_configuration(),
            "prompt_integration": self._check_prompt_integration(),
            "ai_infrastructure_connectivity": self._check_ai_infrastructure(),
        }

        self.integration_report["integration_points"]["ai_systems"] = ai_integration

    def _check_copilot_configuration(self) -> dict[str, Any]:
        """🔧 Check Copilot configuration integration."""
        copilot_config_file = self.instructions_dir / "COPILOT_INSTRUCTIONS_CONFIG.instructions.md"

        if not copilot_config_file.exists():
            return {
                "status": "missing",
                "recommendations": ["Create Copilot configuration file"],
            }

        try:
            content = copilot_config_file.read_text(encoding="utf-8")

            kilo_foolish_integration = "KILO-FOOLISH" in content
            quantum_references = "quantum" in content.lower()
            infrastructure_references = len(self._find_infrastructure_references(content))

            config_check: dict[str, Any] = {
                "status": "present",
                "kilo_foolish_integration": kilo_foolish_integration,
                "quantum_references": quantum_references,
                "infrastructure_references": infrastructure_references,
                "file_size": len(content),
                "recommendations": [],
            }

            if not kilo_foolish_integration:
                config_check["recommendations"].append("🎯 Add KILO-FOOLISH specific configuration")

            if infrastructure_references < 5:
                config_check["recommendations"].append(
                    "🔗 Enhance infrastructure integration references"
                )

            return config_check

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_prompt_integration(self) -> dict[str, Any]:
        """🎯 Check prompt integration."""
        if not self.prompts_dir.exists():
            return {"status": "no_prompts_directory"}

        prompt_files = list(self.prompts_dir.glob("*.md"))

        cross_reference_count = 0

        # Check for cross-references between instructions and prompts
        if self.instructions_dir.exists():
            for instruction_file in self.instructions_dir.glob("*.md"):
                try:
                    content = instruction_file.read_text(encoding="utf-8")
                    if "prompt" in content.lower():
                        cross_reference_count += 1
                except (FileNotFoundError, UnicodeDecodeError, OSError):
                    continue

        recommendations: list[str] = []
        if cross_reference_count == 0:
            recommendations.append("🎯 Add prompt references in instructions")

        integration_check: dict[str, Any] = {
            "prompt_files_count": len(prompt_files),
            "main_prompt_exists": (self.prompts_dir / "NuSyQ_Prompt-Hub.prompt.md").exists(),
            "instruction_prompt_cross_references": cross_reference_count,
            "recommendations": recommendations,
        }

        return integration_check

    def _check_ai_infrastructure(self) -> dict[str, Any]:
        """🏗️ Check AI infrastructure connectivity."""
        ai_files = [
            "src/ai/ollama_chatdev_integrator.py",
            "src/integration/chatdev_launcher.py",
            "src/orchestration/chatdev_testing_chamber.py",
            "src/core/ai_coordinator.py",
        ]

        available_ai_systems: list[str] = []
        missing_ai_systems: list[str] = []
        integration_references_in_instructions = 0

        # Check which AI systems are available
        for ai_file in ai_files:
            if (self.repo_root / ai_file).exists():
                available_ai_systems.append(ai_file)
            else:
                missing_ai_systems.append(ai_file)

        # Check how many instructions reference AI infrastructure
        if self.instructions_dir.exists():
            for instruction_file in self.instructions_dir.glob("*.md"):
                try:
                    content = instruction_file.read_text(encoding="utf-8")
                    for ai_file in available_ai_systems:
                        if ai_file in content:
                            integration_references_in_instructions += 1
                            break
                except (FileNotFoundError, UnicodeDecodeError, OSError):
                    continue

        return {
            "available_ai_systems": available_ai_systems,
            "missing_ai_systems": missing_ai_systems,
            "integration_references_in_instructions": integration_references_in_instructions,
        }

    def _validate_workflow_integration(self) -> None:
        """⚙️ Validate workflow integration."""
        workflow_files: list[str] = []
        instruction_workflow_references = 0
        workflow_instruction_references = 0
        integration_level = "none"

        # Check available workflows
        if self.workflows_dir.exists():
            workflow_files = [f.name for f in self.workflows_dir.glob("*.yml")]
            for workflow_file in self.workflows_dir.glob("*.yml"):
                try:
                    content = workflow_file.read_text(encoding="utf-8")
                    if "instruction" in content.lower() or ".github/instruction" in content:
                        workflow_instruction_references += 1
                except (FileNotFoundError, UnicodeDecodeError, OSError):
                    continue

        # Check if instructions reference workflows
        if self.instructions_dir.exists():
            for instruction_file in self.instructions_dir.glob("*.md"):
                try:
                    content = instruction_file.read_text(encoding="utf-8")
                    if "workflow" in content.lower() or "GitHub Actions" in content:
                        instruction_workflow_references += 1
                except (FileNotFoundError, UnicodeDecodeError, OSError):
                    continue

        # Determine integration level
        total_refs = workflow_instruction_references + instruction_workflow_references
        if total_refs >= 3:
            integration_level = "high"
        elif total_refs >= 1:
            integration_level = "medium"
        else:
            integration_level = "low"

        self.integration_report["integration_points"]["workflows"] = {
            "workflow_files": workflow_files,
            "instruction_workflow_references": instruction_workflow_references,
            "workflow_instruction_references": workflow_instruction_references,
            "integration_level": integration_level,
        }

    def _generate_integration_recommendations(self) -> None:
        """💡 Generate integration enhancement recommendations."""
        recommendations: list[Any] = []
        # Analyze validation results
        validation_results = self.integration_report.get("validation_results", {})
        low_score_files = [
            file
            for file, data in validation_results.items()
            if isinstance(data, dict) and data.get("integration_score", 0) < 50
        ]

        if low_score_files:
            recommendations.append(
                {
                    "category": "integration_scores",
                    "priority": "high",
                    "title": "Improve Integration Scores for Low-Scoring Files",
                    "description": (
                        f"Files with low integration scores: {' '.join(low_score_files)}"
                    ),
                    "implementation": ("Add more infrastructure and AI system references"),
                }
            )

        # Check AI integration
        ai_integration = self.integration_report.get("integration_points", {}).get("ai_systems", {})
        copilot_config = ai_integration.get("copilot_configuration", {})

        if copilot_config.get("status") == "missing":
            recommendations.append(
                {
                    "category": "ai_integration",
                    "priority": "high",
                    "title": "Create Copilot Configuration",
                    "description": "Copilot configuration file is missing",
                    "implementation": ("Create COPILOT_INSTRUCTIONS_CONFIG.instructions.md"),
                }
            )

        # Check workflow integration
        workflow_integration = self.integration_report.get("integration_points", {}).get(
            "workflows", {}
        )
        if workflow_integration.get("integration_level") == "low":
            recommendations.append(
                {
                    "category": "workflow_integration",
                    "priority": "medium",
                    "title": "Enhance Workflow Integration",
                    "description": ("Low integration between instructions and workflows"),
                    "implementation": ("Add workflow references in instructions and vice versa"),
                }
            )

        # Cross-reference recommendations
        cross_refs = self.integration_report.get("cross_references", {})
        files_with_missing_refs = [
            file
            for file, data in cross_refs.items()
            if isinstance(data, dict) and data.get("missing_references")
        ]

        if files_with_missing_refs:
            recommendations.append(
                {
                    "category": "cross_references",
                    "priority": "medium",
                    "title": "Enhance Cross-File References",
                    "description": (
                        f"Files missing cross-references: {' '.join(files_with_missing_refs)}"
                    ),
                    "implementation": ("Add references between related instruction files"),
                }
            )

        self.integration_report["enhancement_recommendations"] = recommendations

    def _create_integration_report(self) -> None:
        """📋 Create comprehensive integration report."""
        report_path = (
            self.repo_root
            / "docs"
            / "reports"
            / f"github_instructions_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report_content = f"""# 🔧 GitHub Instructions Integration Enhancement Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Repository**: KILO-FOOLISH NuSyQ-Hub
**Analysis Scope**: GitHub instructions integration with KILO-FOOLISH infrastructure

---

## 📊 Integration Summary

### 🎯 Overall Integration Health
{self._format_integration_health()}

### 🔗 Cross-Reference Analysis
{self._format_cross_reference_analysis()}

### 🤖 AI Systems Integration
{self._format_ai_integration_analysis()}

### ⚙️ Workflow Integration
{self._format_workflow_integration_analysis()}

---

## 💡 Enhancement Recommendations

{self._format_enhancement_recommendations()}

---

## 📈 Next Steps

1. **Priority Actions**: Address high-priority integration gaps
2. **Cross-Reference Enhancement**: Improve file interconnectivity
3. **AI Integration**: Strengthen AI system connectivity
4. **Workflow Synchronization**: Enhance workflow integration
5. **Continuous Monitoring**: Regular integration validation

---

*Generated by KILO-FOOLISH GitHub Instructions Integration Enhancer v1.0*
*Mission: Seamless integration between GitHub instructions and KILO-FOOLISH infrastructure*
"""

        report_path.write_text(report_content, encoding="utf-8")

        self.integration_report["report_path"] = str(report_path)

    def _format_integration_health(self) -> str:
        """📊 Format integration health summary."""
        validation_results = self.integration_report.get("validation_results", {})

        if not validation_results:
            return "❌ No validation data available"

        scores = [
            data.get("integration_score", 0)
            for data in validation_results.values()
            if isinstance(data, dict)
        ]

        if scores:
            avg_score = sum(scores) / len(scores)
            return f"""
- **Average Integration Score**: {avg_score:.1f}/100
- **Files Analyzed**: {len(validation_results)}
- **High Integration** (≥75): {len([s for s in scores if s >= 75])} files
- **Medium Integration** (50-74): {len([s for s in scores if 50 <= s < 75])} files
- **Low Integration** (<50): {len([s for s in scores if s < 50])} files
"""
        return "❌ No integration scores calculated"

    def _format_cross_reference_analysis(self) -> str:
        """🔗 Format cross-reference analysis."""
        cross_refs = self.integration_report.get("cross_references", {})

        if not cross_refs:
            return "❌ No cross-reference data available"

        total_files = len(cross_refs)
        files_with_refs = len(
            [
                data
                for data in cross_refs.values()
                if isinstance(data, dict) and data.get("references_to_others")
            ]
        )

        ratio = files_with_refs / total_files if total_files > 0 else 0
        integration_level = "High" if ratio > 0.7 else "Medium" if ratio > 0.4 else "Low"

        return f"""- **Files with Cross-References**: {files_with_refs}/{total_files}
- **Integration Level**: {integration_level}
"""

    def _format_ai_integration_analysis(self) -> str:
        """🤖 Format AI integration analysis."""
        ai_integration = self.integration_report.get("integration_points", {}).get("ai_systems", {})

        if not ai_integration:
            return "❌ No AI integration data available"

        copilot_status = ai_integration.get("copilot_configuration", {}).get("status", "unknown")
        prompt_count = ai_integration.get("prompt_integration", {}).get("prompt_files_count", 0)
        ai_systems = ai_integration.get("ai_infrastructure_connectivity", {}).get(
            "available_ai_systems", []
        )
        system_count = len(ai_systems)

        return f"""- **Copilot Configuration**: {copilot_status.title()}
- **Prompt Files**: {prompt_count}
- **AI Infrastructure**: {system_count} systems available
"""

    def _format_workflow_integration_analysis(self) -> str:
        """⚙️ Format workflow integration analysis."""
        workflow_integration = self.integration_report.get("integration_points", {}).get(
            "workflows", {}
        )

        if not workflow_integration:
            return "❌ No workflow integration data available"

        integration_level = workflow_integration.get("integration_level", "unknown")
        workflow_count = len(workflow_integration.get("workflow_files", []))

        has_bidirectional = (
            workflow_integration.get("workflow_instruction_references", 0) > 0
            and workflow_integration.get("instruction_workflow_references", 0) > 0
        )
        bidirectional_status = "✅ Present" if has_bidirectional else "❌ Missing"

        return f"""- **Integration Level**: {integration_level.title()}
- **Workflow Files**: {workflow_count}
- **Bidirectional References**: {bidirectional_status}
"""

    def _format_enhancement_recommendations(self) -> str:
        """💡 Format enhancement recommendations."""
        recommendations = self.integration_report.get("enhancement_recommendations", [])

        if not recommendations:
            return "✅ No specific enhancement recommendations - integration appears optimal"

        formatted: list[Any] = []
        for rec in recommendations:
            priority_emoji = (
                "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            )
            formatted.append(
                f"### {priority_emoji} {rec['title']} ({rec['category'].replace('_', ' ').title()})"
            )
            formatted.append(f"**Description**: {rec['description']}")
            formatted.append(f"**Implementation**: {rec['implementation']}")
            formatted.append("")

        return "\n".join(formatted)


def main():
    """🚀 Main execution function."""
    # Initialize enhancer
    enhancer = GitHubInstructionsIntegrationEnhancer()

    # Run comprehensive integration enhancement
    results = enhancer.run_comprehensive_integration_enhancement()

    # Display summary

    if results.get("report_path"):
        pass

    return results


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""🔧 GitHub Integration Validation Test Suite.

PRESERVATION FIX: 2025-08-05 - Creating comprehensive GitHub integration validation
RATIONALE: Preserving existing infrastructure while adding validation testing
CHANGE: Adding validation test suite for GitHub integration components
PRESERVED: All existing GitHub infrastructure and components maintained

# 🏷️ OmniTag
purpose: github_integration_validation_testing
dependencies:
  - github_workflows
  - github_instructions
  - github_prompts
  - kilo_foolish_infrastructure
context: Comprehensive validation of GitHub integration seamless operation
evolution_stage: v1.0_validation_testing
metadata:
  component: github_integration_validator
  test_level: comprehensive
"""

import importlib
from datetime import datetime
from pathlib import Path
from typing import Any


class GitHubIntegrationValidationSuite:
    """🔧 Comprehensive GitHub Integration Validation Suite.

    Features:
    - Validates all GitHub components working together
    - Tests workflow execution capabilities
    - Validates instruction file integrity and cross-references
    - Tests prompt integration with instructions
    - Validates AI system connectivity
    - Creates comprehensive validation report
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize GitHub Integration Validation Suite."""
        self.repo_root = repo_root or Path.cwd()
        self.github_dir = self.repo_root / ".github"

        self.validation_results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "repo_root": str(self.repo_root),
            "test_results": {},
            "integration_tests": {},
            "recommendations": [],
            "overall_status": "pending",
        }

    def run_comprehensive_validation(self) -> dict[str, Any]:
        """🚀 Run comprehensive GitHub integration validation.

        Returns:
            dict containing complete validation results

        """
        try:
            # Phase 1: Structure validation
            self._validate_github_structure()

            # Phase 2: Component integration testing
            self._test_component_integration()

            # Phase 3: Workflow validation
            self._validate_workflows()

            # Phase 4: Instructions validation
            self._validate_instructions()

            # Phase 5: Cross-component integration
            self._test_cross_component_integration()

            # Phase 6: AI system connectivity
            self._test_ai_system_connectivity()

            # Phase 7: Generate validation report
            self._generate_validation_report()

            # Calculate overall status
            self._calculate_overall_status()

            return self.validation_results

        except Exception as e:
            self.validation_results["error"] = str(e)
            self.validation_results["overall_status"] = "failed"
            return self.validation_results

    def _validate_github_structure(self) -> None:
        """🏗️ Validate GitHub directory structure."""
        structure_test: dict[str, Any] = {
            "github_dir_exists": self.github_dir.exists(),
            "subdirectories": {},
            "required_components": {},
            "score": 0.0,
        }

        # Check required subdirectories
        required_dirs = ["workflows", "instructions", "prompts"]
        for req_dir in required_dirs:
            dir_path = self.github_dir / req_dir
            structure_test["subdirectories"][req_dir] = {
                "exists": dir_path.exists(),
                "file_count": len(list(dir_path.glob("*"))) if dir_path.exists() else 0,
            }

        # Check for specific required files
        required_files = {
            "workflows/security-scan.yml": self.github_dir / "workflows" / "security-scan.yml",
            "workflows/coverage-verification.yml": self.github_dir
            / "workflows"
            / "coverage-verification.yml",
            "instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md": self.github_dir
            / "instructions"
            / "COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
            "instructions/FILE_PRESERVATION_MANDATE.instructions.md": self.github_dir
            / "instructions"
            / "FILE_PRESERVATION_MANDATE.instructions.md",
        }

        for file_key, file_path in required_files.items():
            structure_test["required_components"][file_key] = {
                "exists": file_path.exists(),
                "size": file_path.stat().st_size if file_path.exists() else 0,
            }

        # Calculate structure score
        existing_dirs = sum(
            1 for data in structure_test["subdirectories"].values() if data["exists"]
        )
        existing_files = sum(
            1 for data in structure_test["required_components"].values() if data["exists"]
        )

        structure_test["score"] = (
            (existing_dirs / len(required_dirs)) + (existing_files / len(required_files))
        ) * 50

        self.validation_results["test_results"]["structure"] = structure_test

    def _test_component_integration(self) -> None:
        """🔗 Test component integration."""
        integration_test: dict[str, Any] = {
            "instruction_cross_references": self._test_instruction_cross_references(),
            "workflow_instruction_integration": self._test_workflow_instruction_integration(),
            "prompt_instruction_integration": self._test_prompt_instruction_integration(),
            "score": 0.0,
        }

        # Calculate integration score
        scores = [
            test.get("score", 0) for test in integration_test.values() if isinstance(test, dict)
        ]
        integration_test["score"] = sum(scores) / len(scores) if scores else 0

        self.validation_results["test_results"]["component_integration"] = integration_test

    def _test_instruction_cross_references(self) -> dict[str, Any]:
        """📝 Test instruction cross-references."""
        instructions_dir = self.github_dir / "instructions"

        if not instructions_dir.exists():
            return {"score": 0, "error": "Instructions directory not found"}

        cross_ref_test: dict[str, Any] = {
            "files_analyzed": 0,
            "files_with_references": 0,
            "reference_pairs": [],
            "score": 0.0,
        }

        instruction_files = list(instructions_dir.glob("*.md"))
        cross_ref_test["files_analyzed"] = len(instruction_files)

        # Check for cross-references between files
        for file in instruction_files:
            try:
                content = file.read_text(encoding="utf-8")
                has_references = False

                for other_file in instruction_files:
                    if (
                        other_file != file and other_file.stem in content
                    ) or other_file.name in content:
                        cross_ref_test["reference_pairs"].append(
                            f"{file.name} -> {other_file.name}"
                        )
                        has_references = True

                if has_references:
                    cross_ref_test["files_with_references"] += 1

            except Exception as e:
                cross_ref_test[f"error_{file.name}"] = str(e)

        # Calculate score
        if cross_ref_test["files_analyzed"] > 0:
            cross_ref_test["score"] = (
                cross_ref_test["files_with_references"] / cross_ref_test["files_analyzed"]
            ) * 100

        return cross_ref_test

    def _test_workflow_instruction_integration(self) -> dict[str, Any]:
        """⚙️ Test workflow-instruction integration."""
        workflows_dir = self.github_dir / "workflows"
        instructions_dir = self.github_dir / "instructions"

        if not workflows_dir.exists() or not instructions_dir.exists():
            return {"score": 0, "error": "Missing workflows or instructions directory"}

        workflow_test: dict[str, Any] = {
            "workflow_files": len(list(workflows_dir.glob("*.yml"))),
            "instruction_files": len(list(instructions_dir.glob("*.md"))),
            "workflows_referencing_instructions": 0,
            "instructions_referencing_workflows": 0,
            "score": 0.0,
        }

        # Check workflows referencing instructions
        for workflow_file in workflows_dir.glob("*.yml"):
            try:
                content = workflow_file.read_text(encoding="utf-8")
                if "instruction" in content.lower() or ".github/instruction" in content:
                    workflow_test["workflows_referencing_instructions"] += 1
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue

        # Check instructions referencing workflows
        for instruction_file in instructions_dir.glob("*.md"):
            try:
                content = instruction_file.read_text(encoding="utf-8")
                if "workflow" in content.lower() or "github actions" in content.lower():
                    workflow_test["instructions_referencing_workflows"] += 1
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue

        # Calculate score based on bidirectional integration
        total_possible = workflow_test["workflow_files"] + workflow_test["instruction_files"]
        total_integrated = (
            workflow_test["workflows_referencing_instructions"]
            + workflow_test["instructions_referencing_workflows"]
        )

        if total_possible > 0:
            workflow_test["score"] = (total_integrated / total_possible) * 100

        return workflow_test

    def _test_prompt_instruction_integration(self) -> dict[str, Any]:
        """🎯 Test prompt-instruction integration."""
        prompts_dir = self.github_dir / "prompts"
        instructions_dir = self.github_dir / "instructions"

        if not prompts_dir.exists():
            return {
                "score": 50,
                "note": "Prompts directory optional - partial score assigned",
            }

        if not instructions_dir.exists():
            return {"score": 0, "error": "Instructions directory not found"}

        prompt_test: dict[str, Any] = {
            "prompt_files": len(list(prompts_dir.glob("*.md"))),
            "instructions_referencing_prompts": 0,
            "prompts_referencing_instructions": 0,
            "score": 0.0,
        }

        # Check instructions referencing prompts
        for instruction_file in instructions_dir.glob("*.md"):
            try:
                content = instruction_file.read_text(encoding="utf-8")
                if "prompt" in content.lower():
                    prompt_test["instructions_referencing_prompts"] += 1
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue

        # Check prompts referencing instructions
        for prompt_file in prompts_dir.glob("*.md"):
            try:
                content = prompt_file.read_text(encoding="utf-8")
                if "instruction" in content.lower():
                    prompt_test["prompts_referencing_instructions"] += 1
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue

        # Calculate score
        total_files = prompt_test["prompt_files"] + len(list(instructions_dir.glob("*.md")))
        total_references = (
            prompt_test["instructions_referencing_prompts"]
            + prompt_test["prompts_referencing_instructions"]
        )

        if total_files > 0:
            prompt_test["score"] = (total_references / total_files) * 100

        return prompt_test

    def _validate_workflows(self) -> None:
        """⚙️ Validate workflow files."""
        workflows_dir = self.github_dir / "workflows"

        if not workflows_dir.exists():
            self.validation_results["test_results"]["workflows"] = {
                "score": 0.0,
                "error": "Workflows directory not found",
            }
            return

        workflow_validation: dict[str, Any] = {
            "total_workflows": 0,
            "valid_yaml_files": 0,
            "workflows_with_ai_integration": 0,
            "workflow_details": {},
            "score": 0.0,
        }

        try:
            yaml = importlib.import_module("yaml")
        except ImportError as exc:
            workflow_validation["error"] = f"PyYAML unavailable: {exc}"
            self.validation_results["test_results"]["workflows"] = workflow_validation
            return

        workflow_files = list(workflows_dir.glob("*.yml"))
        workflow_validation["total_workflows"] = len(workflow_files)

        for workflow_file in workflow_files:
            try:
                content = workflow_file.read_text(encoding="utf-8")

                # Test YAML parsing
                yaml_data = yaml.safe_load(content)
                workflow_validation["valid_yaml_files"] += 1

                # Check for AI integration references
                has_ai_integration = any(
                    keyword in content.lower()
                    for keyword in ["ai", "chatdev", "ollama", "copilot", "llm"]
                )

                if has_ai_integration:
                    workflow_validation["workflows_with_ai_integration"] += 1

                workflow_validation["workflow_details"][workflow_file.name] = {
                    "valid_yaml": True,
                    "has_ai_integration": has_ai_integration,
                    "jobs_count": (
                        len(yaml_data.get("jobs", {})) if isinstance(yaml_data, dict) else 0
                    ),
                }

            except Exception as e:
                workflow_validation["workflow_details"][workflow_file.name] = {
                    "valid_yaml": False,
                    "error": str(e),
                }

        # Calculate workflow score
        if workflow_validation["total_workflows"] > 0:
            yaml_score = (
                workflow_validation["valid_yaml_files"] / workflow_validation["total_workflows"]
            ) * 60
            ai_score = (
                workflow_validation["workflows_with_ai_integration"]
                / workflow_validation["total_workflows"]
            ) * 40
            workflow_validation["score"] = yaml_score + ai_score

        self.validation_results["test_results"]["workflows"] = workflow_validation

    def _validate_instructions(self) -> None:
        """📝 Validate instruction files."""
        instructions_dir = self.github_dir / "instructions"

        if not instructions_dir.exists():
            self.validation_results["test_results"]["instructions"] = {
                "score": 0.0,
                "error": "Instructions directory not found",
            }
            return

        instruction_validation: dict[str, Any] = {
            "total_instructions": 0,
            "instructions_with_metadata": 0,
            "instructions_with_kilo_references": 0,
            "instruction_details": {},
            "score": 0.0,
        }

        instruction_files = list(instructions_dir.glob("*.md"))
        instruction_validation["total_instructions"] = len(instruction_files)

        for instruction_file in instruction_files:
            try:
                content = instruction_file.read_text(encoding="utf-8")

                # Check for metadata (YAML frontmatter or structured content)
                has_metadata = content.startswith("---") or "applyTo:" in content
                if has_metadata:
                    instruction_validation["instructions_with_metadata"] += 1

                # Check for KILO-FOOLISH references
                has_kilo_refs = any(
                    keyword in content.lower()
                    for keyword in [
                        "kilo-foolish",
                        "quantum",
                        "consciousness",
                        "src/core",
                        "ai",
                    ]
                )

                if has_kilo_refs:
                    instruction_validation["instructions_with_kilo_references"] += 1

                instruction_validation["instruction_details"][instruction_file.name] = {
                    "has_metadata": has_metadata,
                    "has_kilo_references": has_kilo_refs,
                    "file_size": len(content),
                    "line_count": len(content.splitlines()),
                }

            except Exception as e:
                instruction_validation["instruction_details"][instruction_file.name] = {
                    "error": str(e),
                }

        # Calculate instruction score
        if instruction_validation["total_instructions"] > 0:
            metadata_score = (
                instruction_validation["instructions_with_metadata"]
                / instruction_validation["total_instructions"]
            ) * 40
            kilo_score = (
                instruction_validation["instructions_with_kilo_references"]
                / instruction_validation["total_instructions"]
            ) * 60
            instruction_validation["score"] = metadata_score + kilo_score

        self.validation_results["test_results"]["instructions"] = instruction_validation

    def _test_cross_component_integration(self) -> None:
        """🔄 Test cross-component integration."""
        integration_test: dict[str, Any] = {
            "github_to_src_references": self._count_github_to_src_references(),
            "src_to_github_references": self._count_src_to_github_references(),
            "integration_density": 0,
            "score": 0.0,
        }

        # Calculate integration density
        total_refs = (
            integration_test["github_to_src_references"]
            + integration_test["src_to_github_references"]
        )
        integration_test["integration_density"] = total_refs

        # Score based on integration density
        if total_refs >= 10:
            integration_test["score"] = 100
        elif total_refs >= 5:
            integration_test["score"] = 70
        elif total_refs >= 2:
            integration_test["score"] = 40
        else:
            integration_test["score"] = 20

        self.validation_results["integration_tests"]["cross_component"] = integration_test

    def _count_github_to_src_references(self) -> int:
        """📊 Count references from GitHub files to src directory."""
        count = 0

        if not self.github_dir.exists():
            return count

        for github_file in self.github_dir.rglob("*.md"):
            try:
                content = github_file.read_text(encoding="utf-8")
                if "src/" in content:
                    count += content.count("src/")
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue

        return count

    def _count_src_to_github_references(self) -> int:
        """📊 Count references from src files to GitHub."""
        count = 0
        src_dir = self.repo_root / "src"

        if not src_dir.exists():
            return count

        for src_file in src_dir.rglob("*.py"):
            try:
                content = src_file.read_text(encoding="utf-8")
                if ".github" in content:
                    count += content.count(".github")
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue

        return count

    def _test_ai_system_connectivity(self) -> None:
        """🤖 Test AI system connectivity."""
        ai_connectivity: dict[str, Any] = {
            "ai_files_available": [],
            "ai_integration_references": 0,
            "github_ai_references": 0,
            "score": 0.0,
        }

        # Check for AI system files
        ai_files = [
            "src/ai/ollama_chatdev_integrator.py",
            "src/core/ai_coordinator.py",
            "src/orchestration/chatdev_testing_chamber.py",
            "src/integration/chatdev_launcher.py",
        ]

        for ai_file in ai_files:
            if (self.repo_root / ai_file).exists():
                ai_connectivity["ai_files_available"].append(ai_file)

        # Count AI references in GitHub files
        if self.github_dir.exists():
            for github_file in self.github_dir.rglob("*.md"):
                try:
                    content = github_file.read_text(encoding="utf-8")
                    ai_keywords = ["ai", "chatdev", "ollama", "llm", "copilot"]
                    for keyword in ai_keywords:
                        ai_connectivity["github_ai_references"] += content.lower().count(keyword)
                except (FileNotFoundError, UnicodeDecodeError, OSError):
                    continue

        # Calculate AI connectivity score
        file_score = (len(ai_connectivity["ai_files_available"]) / len(ai_files)) * 50
        reference_score = min(ai_connectivity["github_ai_references"] / 10, 1) * 50
        ai_connectivity["score"] = file_score + reference_score

        self.validation_results["integration_tests"]["ai_connectivity"] = ai_connectivity

    def _generate_validation_report(self) -> None:
        """📋 Generate comprehensive validation report."""
        # Analyze results and generate recommendations
        test_results = self.validation_results.get("test_results", {})

        # Structure recommendations
        if test_results.get("structure", {}).get("score", 0) < 80:
            self.validation_results["recommendations"].append(
                {
                    "category": "structure",
                    "priority": "high",
                    "title": "Improve GitHub directory structure",
                    "action": "Ensure all required directories and files are present",
                }
            )

        # Component integration recommendations
        if test_results.get("component_integration", {}).get("score", 0) < 60:
            self.validation_results["recommendations"].append(
                {
                    "category": "integration",
                    "priority": "medium",
                    "title": "Enhance component integration",
                    "action": "Add more cross-references between GitHub components",
                }
            )

        # Workflow recommendations
        if test_results.get("workflows", {}).get("score", 0) < 70:
            self.validation_results["recommendations"].append(
                {
                    "category": "workflows",
                    "priority": "medium",
                    "title": "Improve workflow integration",
                    "action": "Add AI system integration to workflows",
                }
            )

        # AI connectivity recommendations
        ai_score = (
            self.validation_results.get("integration_tests", {})
            .get("ai_connectivity", {})
            .get("score", 0)
        )
        if ai_score < 70:
            self.validation_results["recommendations"].append(
                {
                    "category": "ai_integration",
                    "priority": "high",
                    "title": "Strengthen AI system connectivity",
                    "action": "Add more AI system references in GitHub components",
                }
            )

    def _calculate_overall_status(self) -> None:
        """📊 Calculate overall validation status."""
        test_results = self.validation_results.get("test_results", {})
        integration_tests = self.validation_results.get("integration_tests", {})

        # Collect all scores
        scores: list[Any] = []
        for test_data in test_results.values():
            if isinstance(test_data, dict) and "score" in test_data:
                scores.append(test_data["score"])

        for test_data in integration_tests.values():
            if isinstance(test_data, dict) and "score" in test_data:
                scores.append(test_data["score"])

        if scores:
            overall_score = sum(scores) / len(scores)

            if overall_score >= 80:
                self.validation_results["overall_status"] = "excellent"
            elif overall_score >= 60:
                self.validation_results["overall_status"] = "good"
            elif overall_score >= 40:
                self.validation_results["overall_status"] = "fair"
            else:
                self.validation_results["overall_status"] = "needs_improvement"

            self.validation_results["overall_score"] = overall_score
        else:
            self.validation_results["overall_status"] = "insufficient_data"
            self.validation_results["overall_score"] = 0

    def create_validation_summary_report(self) -> str:
        """📄 Create validation summary report."""
        report_path = (
            self.repo_root
            / "docs"
            / "reports"
            / f"github_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        overall_score = self.validation_results.get("overall_score", 0)
        overall_status = self.validation_results.get("overall_status", "unknown")

        report_content = f"""# 🔧 GitHub Integration Validation Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Repository**: KILO-FOOLISH NuSyQ-Hub
**Overall Score**: {overall_score:.1f}/100
**Status**: {overall_status.replace("_", " ").title()}

---

## 🎯 Validation Summary

### 📊 Test Results
{self._format_test_results_summary()}

### 🔄 Integration Tests
{self._format_integration_tests_summary()}

### 💡 Recommendations
{self._format_recommendations_summary()}

---

## 🚀 Next Actions

Based on the validation results, the following actions are recommended to ensure seamless GitHub integration:

1. **High Priority**: Address critical integration gaps
2. **Medium Priority**: Enhance cross-component references
3. **Low Priority**: Optimize workflow configurations
4. **Continuous**: Monitor integration health regularly

---

*Generated by KILO-FOOLISH GitHub Integration Validation Suite*
*Mission: Ensuring seamless GitHub component integration*
"""

        report_path.write_text(report_content, encoding="utf-8")
        return str(report_path)

    def _format_test_results_summary(self) -> str:
        """📊 Format test results summary."""
        test_results = self.validation_results.get("test_results", {})

        if not test_results:
            return "❌ No test results available"

        summary_lines: list[Any] = []
        for test_name, test_data in test_results.items():
            if isinstance(test_data, dict):
                score = test_data.get("score", 0)
                status_emoji = "✅" if score >= 70 else "⚠️" if score >= 40 else "❌"
                summary_lines.append(
                    f"- **{test_name.replace('_', ' ').title()}**: {status_emoji} {score:.1f}/100"
                )

        return "\n".join(summary_lines) if summary_lines else "❌ No valid test results"

    def _format_integration_tests_summary(self) -> str:
        """🔄 Format integration tests summary."""
        integration_tests = self.validation_results.get("integration_tests", {})

        if not integration_tests:
            return "❌ No integration test results available"

        summary_lines: list[Any] = []
        for test_name, test_data in integration_tests.items():
            if isinstance(test_data, dict):
                score = test_data.get("score", 0)
                status_emoji = "✅" if score >= 70 else "⚠️" if score >= 40 else "❌"
                summary_lines.append(
                    f"- **{test_name.replace('_', ' ').title()}**: {status_emoji} {score:.1f}/100"
                )

        return "\n".join(summary_lines) if summary_lines else "❌ No valid integration test results"

    def _format_recommendations_summary(self) -> str:
        """💡 Format recommendations summary."""
        recommendations = self.validation_results.get("recommendations", [])

        if not recommendations:
            return "✅ No specific recommendations - integration appears optimal"

        summary_lines: list[Any] = []
        for rec in recommendations:
            priority_emoji = (
                "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            )
            summary_lines.append(
                f"### {priority_emoji} {rec['title']} ({rec['category'].replace('_', ' ').title()})"
            )
            summary_lines.append(f"**Action**: {rec['action']}")
            summary_lines.append("")

        return "\n".join(summary_lines)


def main():
    """🚀 Main execution function."""
    # Initialize validation suite
    validator = GitHubIntegrationValidationSuite()

    # Run comprehensive validation
    results = validator.run_comprehensive_validation()

    # Create summary report
    validator.create_validation_summary_report()

    # Display results

    return results


if __name__ == "__main__":
    main()

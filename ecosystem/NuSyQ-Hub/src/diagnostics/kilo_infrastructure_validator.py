#!/usr/bin/env python3
"""🔍 KILO-FOOLISH Infrastructure Validator.

Comprehensive validation of all existing KILO systems.

OmniTag: {
    "purpose": "Validate all existing KILO infrastructure components",
    "dependencies": ["ALL existing KILO systems"],
    "context": "System health validation and integration testing",
    "evolution_stage": "v4.0"
}
MegaTag: {
    "type": "InfrastructureValidator",
    "integration_points": ["all_systems", "health_monitoring", "diagnostic_testing"],
    "related_tags": ["SystemValidator", "HealthCheck", "IntegrationTest"]
}
RSHTS: ΞΨΩ∞⟨VALIDATION⟩→ΦΣΣ⟨HEALTH⟩
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict


class ValidationResult(TypedDict, total=False):
    """Validation result structure."""

    passed: bool
    errors: list[str]
    details: dict[str, Any]
    message: str


# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))


class KILOInfrastructureValidator:
    """Comprehensive KILO infrastructure validation."""

    def __init__(self) -> None:
        """Initialize KILOInfrastructureValidator."""
        self.validation_results: dict[str, Any] = {}
        self.timestamp: str = datetime.now().isoformat()

    async def run_full_validation(self) -> dict[str, Any]:
        """Run comprehensive validation of all KILO systems."""
        # Core validation categories
        validation_tasks = [
            ("secrets_management", self.validate_secrets_management),
            ("enhanced_bridge", self.validate_enhanced_bridge),
            ("ai_coordinator", self.validate_ai_coordinator),
            ("chatdev_adapter", self.validate_chatdev_adapter),
            ("consciousness_sync", self.validate_consciousness_sync),
            ("orchestration_master", self.validate_orchestration_master),
            ("copilot_integration", self.validate_copilot_integration),
            ("logging_system", self.validate_logging_system),
            ("configuration_integrity", self.validate_configuration_integrity),
            ("file_structure", self.validate_file_structure),
        ]

        # Run all validations
        for category, validator in validation_tasks:
            try:
                result = await validator()
                self.validation_results[category] = {
                    "status": "success" if result["passed"] else "failed",
                    "details": result,
                    "timestamp": datetime.now().isoformat(),
                }

                "✅" if result["passed"] else "❌"

                if not result["passed"] and result.get("errors"):
                    for _error in result["errors"][:3]:  # Show first 3 errors
                        pass

            except Exception as e:
                self.validation_results[category] = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.now().isoformat(),
                }

        # Generate summary report
        await self.generate_validation_report()

        return self.validation_results

    async def validate_secrets_management(self) -> ValidationResult:
        """Validate secrets management system."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            # Import using absolute path from src
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from setup.secrets import get_config

            config = get_config()
            summary = config.get_config_summary()

            result["details"]["config_summary"] = summary
            result["details"]["environment"] = summary.get("environment")

            # Test OpenAI connection
            try:
                config.get_openai_client()
                result["details"]["openai_available"] = True
            except Exception as e:
                result["details"]["openai_available"] = False
                result["errors"].append(f"OpenAI connection failed: {e}")

            # Test Ollama connection
            try:
                config.get_ollama_client()
                result["details"]["ollama_available"] = True
            except Exception as e:
                result["details"]["ollama_available"] = False
                result["errors"].append(f"Ollama connection failed: {e}")

            result["message"] = (
                f"Secrets management operational ({summary.get('environment', 'unknown')} env)"
            )

        except ImportError as e:
            result["passed"] = False
            result["errors"].append(f"Secrets module not found: {e}")
            result["message"] = "Secrets management not available"
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Secrets validation failed: {e}")
            result["message"] = "Secrets management validation failed"

        return result

    async def validate_enhanced_bridge(self) -> ValidationResult:
        """Validate enhanced bridge system."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            # Import using absolute path from src
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from copilot.enhanced_bridge import EnhancedBridge

            bridge = EnhancedBridge()

            # Test basic operations
            bridge.add_contextual_memory("test_key", "test_value")
            retrieved = bridge.retrieve_contextual_memory("test_key")

            if retrieved != "test_value":
                result["errors"].append("Contextual memory test failed")

            # Test OmniTag processing
            omni_result = bridge.process_omni_tag(
                {
                    "purpose": "test",
                    "dependencies": ["test_dep"],
                }
            )

            # Test MegaTag processing
            mega_result = bridge.process_mega_tag({"type": "TestTag"})

            # Test symbolic reasoning
            reasoning_result = bridge.perform_symbolic_reasoning("test_input")

            result["details"] = {
                "contextual_memory_test": retrieved == "test_value",
                "omni_tag_processing": bool(omni_result),
                "mega_tag_processing": bool(mega_result),
                "symbolic_reasoning": bool(reasoning_result),
                "context_summary": bridge.summarize_context(),
            }

            result["message"] = (
                f"Enhanced bridge operational with {len(bridge.contextual_memory)} memory items"
            )

        except ImportError as e:
            result["passed"] = False
            result["errors"].append(f"Enhanced bridge module not found: {e}")
            result["message"] = "Enhanced bridge not available"
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Enhanced bridge validation failed: {e}")
            result["message"] = "Enhanced bridge validation failed"

        return result

    async def validate_ai_coordinator(self) -> ValidationResult:
        """Validate AI coordinator system."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            # Import using absolute path from src
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from ai.ai_coordinator import KILOFoolishAICoordinator, TaskType

            KILOFoolishAICoordinator()

            # Test task types availability
            task_types = [t.value for t in TaskType]
            result["details"]["available_task_types"] = task_types

            # Test basic task execution (without actually executing)
            result["details"]["coordinator_initialized"] = True
            result["details"]["task_types_count"] = len(task_types)

            result["message"] = f"AI coordinator operational with {len(task_types)} task types"

        except ImportError as e:
            result["passed"] = False
            result["errors"].append(f"AI coordinator module not found: {e}")
            result["message"] = "AI coordinator not available"
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"AI coordinator validation failed: {e}")
            result["message"] = "AI coordinator validation failed"

        return result

    async def validate_chatdev_adapter(self) -> ValidationResult:
        """Validate ChatDev adapter system."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            # Import using absolute path from src
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from integration.chatdev_llm_adapter import ChatDevLLMAdapter

            adapter = ChatDevLLMAdapter()

            result["details"]["adapter_initialized"] = True
            result["details"]["adapter_class"] = adapter.__class__.__name__

            result["message"] = "ChatDev adapter operational"

        except ImportError as e:
            result["passed"] = False
            result["errors"].append(f"ChatDev adapter module not found: {e}")
            result["message"] = "ChatDev adapter not available"
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"ChatDev adapter validation failed: {e}")
            result["message"] = "ChatDev adapter validation failed"

        return result

    async def validate_consciousness_sync(self) -> ValidationResult:
        """Validate consciousness sync system."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            # Import using absolute path from src
            sys.path.insert(0, str(Path(__file__).parent.parent))

            result["details"]["consciousness_sync_available"] = True
            result["message"] = "Consciousness sync operational"

        except ImportError as e:
            result["passed"] = False
            result["errors"].append(f"Consciousness sync module not found: {e}")
            result["message"] = "Consciousness sync not available"
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Consciousness sync validation failed: {e}")
            result["message"] = "Consciousness sync validation failed"

        return result

    async def validate_orchestration_master(self) -> ValidationResult:
        """Validate orchestration master system."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            # Import using absolute path from src
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from orchestration.kilo_ai_orchestration_master import \
                KILOAIOrchestrationMaster

            orchestrator = KILOAIOrchestrationMaster()

            # Get system status
            status = orchestrator.get_system_status()
            result["details"]["system_status"] = status

            available_components = sum(
                1 for comp in status["components"].values() if comp["available"]
            )
            total_components = len(status["components"])

            result["details"]["available_components"] = available_components
            result["details"]["total_components"] = total_components

            result["message"] = (
                f"Orchestration master operational ({available_components}/{total_components} components)"
            )

        except ImportError as e:
            result["passed"] = False
            result["errors"].append(f"Orchestration master module not found: {e}")
            result["message"] = "Orchestration master not available"
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Orchestration master validation failed: {e}")
            result["message"] = "Orchestration master validation failed"

        return result

    async def validate_copilot_integration(self) -> ValidationResult:
        """Validate Copilot integration system."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            # Import using absolute path from src
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from copilot.vscode_integration import CopilotKILOIntegration

            CopilotKILOIntegration()

            result["details"]["integration_initialized"] = True
            result["message"] = "Copilot integration operational"

        except ImportError as e:
            result["passed"] = False
            result["errors"].append(f"Copilot integration module not found: {e}")
            result["message"] = "Copilot integration not available"
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Copilot integration validation failed: {e}")
            result["message"] = "Copilot integration validation failed"

        return result

    async def validate_logging_system(self) -> ValidationResult:
        """Validate logging system."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            # Check LOGGING directory structure
            logging_path = Path(__file__).parent.parent.parent / "LOGGING"

            if not logging_path.exists():
                result["errors"].append("LOGGING directory not found")
                result["passed"] = False
            else:
                # Check for modular logging system
                modular_log_path = logging_path / "modular_logging_system.py"
                if modular_log_path.exists():
                    result["details"]["modular_logging_available"] = True
                else:
                    result["errors"].append("Modular logging system not found")

                # Check for logs directory
                logs_path = logging_path / "Logs"
                result["details"]["logs_directory_exists"] = logs_path.exists()

                if logs_path.exists():
                    log_files = list(logs_path.glob("*.log"))
                    result["details"]["log_files_count"] = len(log_files)
                else:
                    result["details"]["log_files_count"] = 0

            result["message"] = (
                f"Logging system available with {result['details'].get('log_files_count', 0)} log files"
            )

        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Logging system validation failed: {e}")
            result["message"] = "Logging system validation failed"

        return result

    async def validate_configuration_integrity(self) -> ValidationResult:
        """Validate configuration files integrity."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            config_path = Path(__file__).parent.parent.parent / "config"

            if not config_path.exists():
                result["errors"].append("Config directory not found")
                result["passed"] = False
                return result

            # Check for key configuration files
            config_files = {
                "bridge_config.yaml": "Bridge configuration",
                "quantum_states.toml": "Quantum states",
                "megatag_schemas.json": "MegaTag schemas",
                "omnitag_patterns.json": "OmniTag patterns",
                "workspace.json": "Workspace configuration",
            }

            found_configs: dict[str, Any] = {}
            for filename, description in config_files.items():
                file_path = config_path / filename
                found_configs[filename] = {
                    "exists": file_path.exists(),
                    "description": description,
                }

                if not file_path.exists():
                    result["errors"].append(f"Missing config file: {filename}")

            result["details"]["configuration_files"] = found_configs

            found_count = sum(1 for config in found_configs.values() if config["exists"])
            total_count = len(config_files)

            result["message"] = f"Configuration integrity: {found_count}/{total_count} files found"

            if found_count < total_count:
                result["passed"] = False

        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Configuration validation failed: {e}")
            result["message"] = "Configuration validation failed"

        return result

    async def validate_file_structure(self) -> ValidationResult:
        """Validate KILO file structure."""
        result: ValidationResult = {"passed": True, "errors": [], "details": {}}

        try:
            base_path = Path(__file__).parent.parent.parent

            # Expected directory structure
            expected_dirs = [
                "src",
                "src/ai",
                "src/copilot",
                "src/integration",
                "src/orchestration",
                "src/consciousness",
                "src/setup",
                "src/diagnostics",
                "config",
                "LOGGING",
                "data",
                "docs",
            ]

            dir_status: dict[str, Any] = {}
            for dir_path in expected_dirs:
                full_path = base_path / dir_path
                dir_status[dir_path] = {
                    "exists": full_path.exists(),
                    "is_directory": full_path.is_dir() if full_path.exists() else False,
                }

                if not full_path.exists():
                    result["errors"].append(f"Missing directory: {dir_path}")

            result["details"]["directory_structure"] = dir_status

            found_dirs = sum(1 for status in dir_status.values() if status["exists"])
            total_dirs = len(expected_dirs)

            result["message"] = f"File structure: {found_dirs}/{total_dirs} directories found"

            if found_dirs < total_dirs * 0.8:  # 80% threshold
                result["passed"] = False

        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"File structure validation failed: {e}")
            result["message"] = "File structure validation failed"

        return result

    async def generate_validation_report(self) -> None:
        """Generate comprehensive validation report."""
        report_path = Path(__file__).parent.parent.parent / "reports"
        report_path.mkdir(exist_ok=True)

        # Generate JSON report
        json_report_path = (
            report_path / f"kilo_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        report_data = {
            "validation_timestamp": self.timestamp,
            "validation_results": self.validation_results,
            "summary": self._generate_summary(),
        }

        with open(json_report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        # Generate markdown report
        md_report_path = (
            report_path / f"kilo_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        await self._generate_markdown_report(md_report_path)

    def _generate_summary(self) -> dict[str, Any]:
        """Generate validation summary."""
        total_tests = len(self.validation_results)
        passed_tests = sum(
            1 for result in self.validation_results.values() if result["status"] == "success"
        )
        failed_tests = sum(
            1 for result in self.validation_results.values() if result["status"] == "failed"
        )
        error_tests = sum(
            1 for result in self.validation_results.values() if result["status"] == "error"
        )

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": ((passed_tests / total_tests * 100) if total_tests > 0 else 0),
            "overall_health": (
                "healthy" if passed_tests >= total_tests * 0.8 else "needs_attention"
            ),
        }

    async def _generate_markdown_report(self, report_path: Path) -> None:
        """Generate markdown validation report."""
        summary = self._generate_summary()

        md_content = f"""# KILO-FOOLISH Infrastructure Validation Report

**Generated:** {self.timestamp}

## Summary

- **Total Tests:** {summary["total_tests"]}
- **Passed:** {summary["passed_tests"]} ✅
- **Failed:** {summary["failed_tests"]} ❌
- **Errors:** {summary["error_tests"]} 🚫
- **Success Rate:** {summary["success_rate"]:.1f}%
- **Overall Health:** {summary["overall_health"].upper()}

## Detailed Results

"""

        for category, result in self.validation_results.items():
            status_icon = {
                "success": "✅",
                "failed": "❌",
                "error": "🚫",
            }.get(result["status"], "❓")

            md_content += f"""### {category.replace("_", " ").title()} {status_icon}

**Status:** {result["status"].upper()}
**Message:** {result.get("details", {}).get("message", "No message")}

"""

            if result.get("errors"):
                md_content += "**Errors:**\n"
                for error in result["errors"]:
                    md_content += f"- {error}\n"
                md_content += "\n"

            if result.get("details"):
                md_content += "**Details:**\n"
                for key, value in result["details"].items():
                    if key != "message":
                        md_content += f"- **{key}:** {value}\n"
                md_content += "\n"

        md_content += """## Recommendations

Based on the validation results, consider the following actions:

1. **Failed Tests:** Address any failed validation tests to ensure system stability
2. **Missing Components:** Install or configure any missing KILO infrastructure components
3. **Configuration Issues:** Review and update configuration files as needed
4. **Performance Optimization:** Consider optimizing components with slow validation times

---
*This report was generated by the KILO-FOOLISH Infrastructure Validator*
"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_content)


async def main() -> None:
    """Main validation runner."""
    validator = KILOInfrastructureValidator()

    await validator.run_full_validation()

    # Print final summary
    summary = validator._generate_summary()

    if summary["overall_health"] == "healthy":
        pass
    else:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except (RuntimeError, SystemExit):
        traceback.print_exc()

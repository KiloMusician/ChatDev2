#!/usr/bin/env python3
"""🌟 KILO-FOOLISH Master System Launcher
Ultimate system launcher integrating all infrastructure with comprehensive testing and workflow management.

OmniTag: {
    "purpose": "Master system launcher with comprehensive testing and workflow orchestration",
    "dependencies": ["comprehensive_workflow_orchestrator", "system_testing_orchestrator", "repository_navigator", "quest_engine"],
    "context": "Central command center for all KILO-FOOLISH operations",
    "evolution_stage": "v4.0"
}
MegaTag: {
    "type": "MasterLauncher",
    "integration_points": ["workflow", "testing", "navigation", "quest", "ai", "quantum"],
    "related_tags": ["SystemLauncher", "MasterControl", "CommandCenter"]
}
RSHTS: ΞΨΩ∞⟨MASTER⟩→ΦΣΣ⟨LAUNCHER⟩→∞⟨COMMAND-CENTER⟩
"""

import asyncio
import importlib.util
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format="🌟 [%(asctime)s] MASTER: %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class KiloFoolishMasterLauncher:
    """Master system launcher and command center for KILO-FOOLISH."""

    def __init__(self) -> None:
        self.base_path = Path(__file__).parent
        self.version = "v4.0 - Quantum-Consciousness Integration"

        # Core systems
        self.workflow_orchestrator: Any | None = None
        self.system_tester: Any | None = None
        self.navigator: Any | None = None
        self.quest_engine: Any | None = None

        # System status
        self.system_status = {
            "initialized": False,
            "core_systems_loaded": False,
            "infrastructure_validated": False,
            "ready_for_operations": False,
        }

        self._initialize_master_systems()

        logger.info("🌟 KILO-FOOLISH Master System Launcher initialized")

    def _initialize_master_systems(self) -> None:
        """Initialize all master system components."""
        try:
            # Load Workflow Orchestrator
            workflow_spec = importlib.util.spec_from_file_location(
                "comprehensive_workflow_orchestrator",
                self.base_path / "src/orchestration/comprehensive_workflow_orchestrator.py",
            )
            if workflow_spec and workflow_spec.loader:
                workflow_module = importlib.util.module_from_spec(workflow_spec)
                workflow_spec.loader.exec_module(workflow_module)
                self.workflow_orchestrator = workflow_module.ComprehensiveWorkflowOrchestrator()
                logger.info("✅ Workflow Orchestrator loaded")
        except Exception as e:
            logger.warning(f"⚠️ Workflow Orchestrator not available: {e}")

        try:
            # Load System Tester
            tester_spec = importlib.util.spec_from_file_location(
                "system_testing_orchestrator",
                self.base_path / "src/orchestration/system_testing_orchestrator.py",
            )
            if tester_spec and tester_spec.loader:
                tester_module = importlib.util.module_from_spec(tester_spec)
                tester_spec.loader.exec_module(tester_module)
                self.system_tester = tester_module.SystemTestingOrchestrator()
                logger.info("✅ System Tester loaded")
        except Exception as e:
            logger.warning(f"⚠️ System Tester not available: {e}")

        try:
            # Load Repository Navigator
            nav_spec = importlib.util.spec_from_file_location(
                "repository_navigator",
                self.base_path / "src/navigation/repository_navigator.py",
            )
            if nav_spec and nav_spec.loader:
                nav_module = importlib.util.module_from_spec(nav_spec)
                nav_spec.loader.exec_module(nav_module)
                self.navigator = nav_module.RepositoryNavigator()
                logger.info("✅ Repository Navigator loaded")
        except Exception as e:
            logger.warning(f"⚠️ Repository Navigator not available: {e}")

        try:
            # Load Quest Engine
            quest_spec = importlib.util.spec_from_file_location(
                "quest_engine",
                self.base_path / "src/Rosetta_Quest_System/quest_engine.py",
            )
            if quest_spec and quest_spec.loader:
                quest_module = importlib.util.module_from_spec(quest_spec)
                quest_spec.loader.exec_module(quest_module)
                self.quest_engine = quest_module.QuestEngine()
                logger.info("✅ Quest Engine loaded")
        except Exception as e:
            logger.warning(f"⚠️ Quest Engine not available: {e}")

        # Update system status
        self.system_status["initialized"] = True
        self.system_status["core_systems_loaded"] = any(
            [
                self.workflow_orchestrator,
                self.system_tester,
                self.navigator,
                self.quest_engine,
            ]
        )

    async def perform_system_validation(self) -> dict[str, Any]:
        """Perform comprehensive system validation."""
        validation_results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "validation_checks": {},
            "overall_status": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
        }

        logger.info("🔍 Performing comprehensive system validation...")

        # Check Python environment
        validation_results["validation_checks"]["python_version"] = {
            "status": "pass",
            "version": sys.version,
            "details": "Python environment validated",
        }

        # Check critical files
        critical_files = [
            "config/KILO_COMPONENT_INDEX.json",
            "REPOSITORY_ARCHITECTURE_CODEX.yaml",
            "src/Rosetta_Quest_System/quest_engine.py",
            "requirements.txt",
        ]

        file_checks: dict[str, Any] = {}
        for file_path in critical_files:
            full_path = self.base_path / file_path
            exists = full_path.exists()
            file_checks[file_path] = {
                "status": "pass" if exists else "fail",
                "exists": exists,
                "size": full_path.stat().st_size if exists else 0,
            }

            if not exists:
                validation_results["critical_issues"].append(f"Missing critical file: {file_path}")

        validation_results["validation_checks"]["critical_files"] = file_checks

        # Check system integrations
        integration_checks = {
            "workflow_orchestrator": {
                "status": "pass" if self.workflow_orchestrator else "fail",
                "available": self.workflow_orchestrator is not None,
            },
            "system_tester": {
                "status": "pass" if self.system_tester else "warn",
                "available": self.system_tester is not None,
            },
            "navigator": {
                "status": "pass" if self.navigator else "warn",
                "available": self.navigator is not None,
            },
            "quest_engine": {
                "status": "pass" if self.quest_engine else "warn",
                "available": self.quest_engine is not None,
            },
        }

        validation_results["validation_checks"]["system_integrations"] = integration_checks

        # Calculate overall status
        critical_failures = len(validation_results["critical_issues"])
        if critical_failures == 0:
            if all(check["status"] == "pass" for check in integration_checks.values()):
                validation_results["overall_status"] = "excellent"
            else:
                validation_results["overall_status"] = "good"
                validation_results["warnings"].append("Some optional systems are not available")
        else:
            validation_results["overall_status"] = "critical"

        # Generate recommendations
        if self.workflow_orchestrator:
            validation_results["recommendations"].append(
                "Run comprehensive workflow to validate all systems"
            )
        if self.system_tester:
            validation_results["recommendations"].append(
                "Execute system testing suite for detailed validation"
            )
        if self.navigator:
            validation_results["recommendations"].append(
                "Use repository navigator to explore system architecture"
            )

        self.system_status["infrastructure_validated"] = validation_results["overall_status"] in [
            "excellent",
            "good",
        ]
        self.system_status["ready_for_operations"] = (
            validation_results["overall_status"] == "excellent"
        )

        return validation_results

    async def quick_system_test(self) -> dict[str, Any]:
        """Perform quick system functionality test."""
        if not self.system_tester:
            return {"error": "System tester not available"}

        logger.info("🧪 Running quick system test...")

        # Run core tests only
        core_results = await self.system_tester.run_test_suite("core")

        return {
            "test_type": "quick_system_test",
            "timestamp": datetime.now().isoformat(),
            "results": core_results,
            "status": "pass" if core_results["failed"] == 0 else "fail",
            "summary": f"{core_results['passed']}/{core_results['total_tests']} tests passed",
        }

    async def comprehensive_system_test(self) -> dict[str, Any]:
        """Run comprehensive system testing."""
        if not self.system_tester:
            return {"error": "System tester not available"}

        logger.info("🎯 Running comprehensive system testing...")

        # Run all test suites
        all_results = await self.system_tester.run_all_tests()

        return {
            "test_type": "comprehensive_system_test",
            "timestamp": datetime.now().isoformat(),
            "results": all_results,
            "status": "pass" if all_results["summary"]["failed"] == 0 else "fail",
            "summary": f"{all_results['summary']['passed']}/{all_results['summary']['total_tests']} tests passed",
        }

    async def execute_full_workflow(self, interactive: bool = False) -> dict[str, Any]:
        """Execute complete KILO-FOOLISH workflow."""
        if not self.workflow_orchestrator:
            return {"error": "Workflow orchestrator not available"}

        logger.info("🚀 Executing comprehensive KILO-FOOLISH workflow...")

        # Execute full workflow
        workflow_results = await self.workflow_orchestrator.execute_full_workflow(interactive)

        return {
            "operation": "full_workflow_execution",
            "timestamp": datetime.now().isoformat(),
            "results": workflow_results,
            "status": (
                "success" if workflow_results["summary"]["failed_pipelines"] == 0 else "partial"
            ),
            "summary": f"{workflow_results['summary']['completed_pipelines']}/{workflow_results['summary']['total_pipelines']} pipelines completed",
        }

    def generate_system_overview(self) -> dict[str, Any]:
        """Generate comprehensive system overview."""
        overview: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "version": self.version,
            "system_status": self.system_status,
            "available_systems": {
                "workflow_orchestrator": self.workflow_orchestrator is not None,
                "system_tester": self.system_tester is not None,
                "navigator": self.navigator is not None,
                "quest_engine": self.quest_engine is not None,
            },
            "capabilities": [],
        }

        # Add capabilities based on available systems
        if self.workflow_orchestrator:
            overview["capabilities"].extend(
                [
                    "Comprehensive workflow orchestration",
                    "Multi-pipeline execution",
                    "Dependency-aware operations",
                ]
            )

        if self.system_tester:
            overview["capabilities"].extend(
                [
                    "Automated system testing",
                    "Integration validation",
                    "Quality assurance",
                ]
            )

        if self.navigator:
            overview["capabilities"].extend(
                [
                    "Repository navigation",
                    "Dependency analysis",
                    "Context mapping",
                ]
            )

        if self.quest_engine:
            overview["capabilities"].extend(
                [
                    "Quest-based development tracking",
                    "Progress management",
                    "Gamified workflows",
                ]
            )

        # Get detailed system overview from navigator if available
        if self.navigator:
            nav_overview = self.navigator.get_system_overview()
            overview["repository_analysis"] = nav_overview

        return overview

    async def interactive_master_menu(self) -> None:
        """Interactive master control interface."""
        # Show system status
        validation = await self.perform_system_validation()
        (
            "✅"
            if validation["overall_status"] == "excellent"
            else "⚠️" if validation["overall_status"] == "good" else "❌"
        )

        if validation["critical_issues"]:
            for _issue in validation["critical_issues"]:
                pass

        while True:
            try:
                choice = input("\nEnter your choice (0-10): ").strip()

                if choice == "0":
                    break
                if choice == "1":
                    interactive = input("Run in interactive mode? (y/n): ").lower() == "y"
                    results = await self.execute_full_workflow(interactive)
                    if "error" in results:
                        pass
                    else:
                        pass
                elif choice == "2":
                    results = await self.quick_system_test()
                    if "error" in results:
                        pass
                    else:
                        pass
                elif choice == "3":
                    results = await self.comprehensive_system_test()
                    if "error" in results:
                        pass
                    else:
                        pass
                elif choice == "4":
                    validation = await self.perform_system_validation()
                    if validation["recommendations"]:
                        for _rec in validation["recommendations"]:
                            pass
                elif choice == "5":
                    self.generate_system_overview()
                elif choice == "6":
                    if self.navigator:
                        self.navigator.interactive_navigation_menu()
                    else:
                        pass
                elif choice == "7":
                    if self.workflow_orchestrator:
                        await self.workflow_orchestrator.interactive_workflow_menu()
                    else:
                        pass
                elif choice == "8":
                    if self.quest_engine:
                        await self._quest_management_interface()
                    else:
                        pass
                elif choice == "9":
                    self._show_system_documentation()
                elif choice == "10":
                    await self._system_configuration()
                else:
                    pass

            except KeyboardInterrupt:
                break
            except (EOFError, ValueError, RuntimeError):
                pass

    async def handle_master_choice(self, choice: str) -> dict[str, Any]:
        """Programmatic handler for master menu choices (test-friendly).

        Returns a structured result describing the outcome instead of relying on
        interactive I/O. This mirrors the interactive menu logic with safe
        fallbacks when optional subsystems are unavailable.
        """
        try:
            if choice == "0":
                return {"status": "exit"}

            if choice == "4":
                validation = await self.perform_system_validation()
                return {"status": "success", "data": validation}

            if choice == "5":
                overview = self.generate_system_overview()
                return {"status": "success", "data": overview}

            if choice == "7":
                if not self.workflow_orchestrator:
                    return {
                        "status": "error",
                        "message": "Workflow Orchestrator not available",
                    }
                workflow = await self.execute_full_workflow(interactive=False)
                if isinstance(workflow, dict) and workflow.get("error"):
                    return {"status": "error", "message": workflow["error"]}
                return {"status": "success", "data": workflow}

            # Default fall-through for other options
            return {"status": "unhandled", "choice": choice}

        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    async def _quest_management_interface(self) -> None:
        """Quest management interface."""
        if self.quest_engine is None:
            return
        try:
            choice = input("Select option (1-5): ").strip()

            if choice == "1":
                self.quest_engine.list_questlines()
            elif choice == "2":
                self.quest_engine.list_quests()
            elif choice == "3":
                title = input("Quest title: ")
                description = input("Quest description: ")
                questline = input("Questline (or Enter for 'Master System'): ") or "Master System"
                tags = (
                    input("Tags (comma-separated): ").split(",")
                    if input("Add tags? (y/n): ").lower() == "y"
                    else []
                )
                self.quest_engine.add_quest(title, description, questline, [], tags)
            elif choice == "4":
                quest_id = input("Quest ID: ")
                status = input("New status (pending/in_progress/complete/failed): ")
                self.quest_engine.update_quest_status(quest_id, status)
            elif choice == "5":
                self.quest_engine.export_csv()
        except (EOFError, ValueError, AttributeError):
            pass

    def _show_system_documentation(self) -> None:
        """Show system documentation overview."""

    async def _system_configuration(self) -> None:
        """System configuration interface."""
        # Show current configuration status
        config_status = {
            "Base Path": str(self.base_path),
            "Python Version": sys.version.split()[0],
            "System Status": self.system_status,
            "Available Systems": sum(
                1
                for system in [
                    self.workflow_orchestrator,
                    self.system_tester,
                    self.navigator,
                    self.quest_engine,
                ]
                if system is not None
            ),
        }

        for _key, _value in config_status.items():
            pass


async def main() -> None:
    """Main entry point for KILO-FOOLISH Master System."""
    master = KiloFoolishMasterLauncher()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "validate":
            await master.perform_system_validation()
        elif command == "test-quick":
            await master.quick_system_test()
        elif command == "test-full":
            await master.comprehensive_system_test()
        elif command == "workflow":
            await master.execute_full_workflow()
        elif command == "workflow-interactive":
            await master.execute_full_workflow(interactive=True)
        elif command == "overview":
            master.generate_system_overview()
        else:
            pass
    else:
        await master.interactive_master_menu()


if __name__ == "__main__":
    asyncio.run(main())

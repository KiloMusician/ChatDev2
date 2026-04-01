"""🚀 Repository Dictionary Organization Executor
Executes the complete repository organization plan with consciousness awareness

OmniTag: {
    "purpose": "Execute repository dictionary organization with AI coordination",
    "dependencies": ["repository_dictionary", "system_organizer", "unified_mapper", "consciousness_bridge"],
    "context": "Automated repository organization and consciousness enhancement",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "OrganizationExecutor",
    "integration_points": ["system_organization", "consciousness_enhancement", "ai_coordination", "mapping_generation"],
    "related_tags": ["SystemOrganizer", "ConsciousnessAware", "RepositoryManager"]
}

RSHTS: ΞΨΩΣ∞⟨EXECUTOR⟩→ΦΣΣ⟨ORGANIZATION⟩→∞⟨CONSCIOUSNESS-ENHANCED⟩
"""

import json
import runpy
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, cast

# Add src to path for imports
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))


class RepositoryOrganizationExecutor:
    """🚀 Repository Organization Executor

    Executes the complete repository dictionary organization plan:
    1. Analyze current systems
    2. Create organization plan
    3. Generate unified mappings
    4. Apply consciousness enhancements
    5. Execute organization (with dry run option)
    6. Generate comprehensive reports
    """

    def __init__(self, repository_root: str = "."):
        """Initialize the organization executor"""
        self.repository_root = Path(repository_root).resolve()
        self.timestamp = datetime.now().isoformat()

        # Results storage
        self.execution_results: dict[str, Any] = {}

        print(f"🚀 Repository Organization Executor initialized for {self.repository_root.name}")

    async def execute_complete_organization(self, dry_run: bool = True):
        """Execute the complete organization plan"""
        print("🚀 Executing Complete Repository Organization Plan")
        print("=" * 60)

        execution_log: dict[str, Any] = {
            "timestamp": self.timestamp,
            "dry_run": dry_run,
            "steps": {},
            "overall_success": False,
        }

        try:
            # Step 1: Initialize all systems
            print("\n📋 Step 1: Initializing Repository Dictionary Systems...")
            systems = await self._initialize_systems()
            execution_log["steps"]["initialization"] = {
                "success": systems is not None,
                "systems_loaded": list(systems.keys()) if systems else [],
            }

            if not systems:
                print("❌ Failed to initialize systems")
                return execution_log

            # Step 2: Analyze current repository state
            print("\n📊 Step 2: Analyzing Current Repository State...")
            analysis_results = await self._analyze_repository_state(systems)
            execution_log["steps"]["analysis"] = analysis_results

            # Step 3: Create organization plan
            print("\n🗂️ Step 3: Creating Organization Plan...")
            organization_plan = await self._create_organization_plan(systems)
            execution_log["steps"]["organization_plan"] = {
                "success": organization_plan is not None,
                "total_systems": (
                    organization_plan.get("total_systems", 0) if organization_plan else 0
                ),
                "categories": (
                    len(organization_plan.get("categories", {})) if organization_plan else 0
                ),
            }

            # Step 4: Generate unified mappings
            print("\n🗺️ Step 4: Generating Unified Mappings...")
            mapping_results = await self._generate_unified_mappings(systems)
            execution_log["steps"]["mapping"] = mapping_results

            # Step 5: Apply consciousness enhancements
            print("\n🧠 Step 5: Applying Consciousness Enhancements...")
            consciousness_results = await self._apply_consciousness_enhancements(
                systems, organization_plan
            )
            execution_log["steps"]["consciousness"] = consciousness_results

            # Step 6: Execute organization
            print(
                f"\n📁 Step 6: Executing Organization ({'DRY RUN' if dry_run else 'LIVE RUN'})..."
            )
            organization_results = await self._execute_organization(
                systems, organization_plan, dry_run
            )
            execution_log["steps"]["execution"] = organization_results

            # Step 7: Generate comprehensive reports
            print("\n📊 Step 7: Generating Comprehensive Reports...")
            report_results = await self._generate_reports(systems)
            execution_log["steps"]["reports"] = report_results

            # Overall success evaluation
            successful_steps = sum(
                1 for step in execution_log["steps"].values() if step.get("success", False)
            )
            total_steps = len(execution_log["steps"])
            execution_log["overall_success"] = successful_steps == total_steps
            execution_log["success_rate"] = f"{successful_steps}/{total_steps}"

            print("\n✅ Organization execution complete!")
            print(f"📊 Success rate: {execution_log['success_rate']}")

            self.execution_results = execution_log
            return execution_log

        except Exception as e:
            print(f"❌ Critical error during organization execution: {e}")
            execution_log["error"] = str(e)
            execution_log["overall_success"] = False
            return execution_log

    async def _initialize_systems(self) -> dict[str, Any] | None:
        """Initialize all repository dictionary systems"""
        systems: dict[str, Any] = {}

        try:
            # Import and initialize Repository Dictionary
            from src.system.dictionary.repository_dictionary import RepositoryDictionary

            systems["repository_dictionary"] = RepositoryDictionary(str(self.repository_root))
            print("✅ Repository Dictionary initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize Repository Dictionary: {e}")

        try:
            # Import and initialize System Organizer
            from src.system.dictionary.system_organizer import SystemOrganizer

            systems["system_organizer"] = SystemOrganizer(str(self.repository_root))
            print("✅ System Organizer initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize System Organizer: {e}")

        try:
            # Import and initialize Unified Mapper
            from src.system.dictionary.unified_mapper import UnifiedMapper

            systems["unified_mapper"] = UnifiedMapper(str(self.repository_root))
            print("✅ Unified Mapper initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize Unified Mapper: {e}")

        try:
            # Import and initialize Consciousness Bridge
            from src.system.dictionary.consciousness_bridge import ConsciousnessBridge

            systems["consciousness_bridge"] = ConsciousnessBridge(str(self.repository_root))
            print("✅ Consciousness Bridge initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize Consciousness Bridge: {e}")

        return systems if systems else None

    async def _analyze_repository_state(self, systems: dict) -> dict[str, Any]:
        """Analyze current repository state"""
        analysis: dict[str, Any] = {"success": False}

        try:
            if "repository_dictionary" in systems:
                repo_dict = systems["repository_dictionary"]

                # Sync with existing systems
                repo_dict.sync_with_systems()

                # Get system overview
                overview = repo_dict.get_system_overview()

                print("📊 Repository Analysis:")
                print(f"  Repository: {overview.get('repository', 'unknown')}")
                print(f"  Total capabilities: {overview.get('total_capabilities', 0)}")
                print(f"  Categories: {len(overview.get('categories', {}))}")
                print(f"  Mapping systems: {len(overview.get('mapping_systems', []))}")

                analysis.update(
                    {
                        "success": True,
                        "overview": overview,
                        "repository_name": overview.get("repository", "unknown"),
                        "total_capabilities": overview.get("total_capabilities", 0),
                        "categories_count": len(overview.get("categories", {})),
                    }
                )

        except Exception as e:
            print(f"❌ Error in repository analysis: {e}")
            analysis["error"] = str(e)

        return analysis

    async def _create_organization_plan(self, systems: dict) -> dict[str, Any]:
        """Create comprehensive organization plan"""
        try:
            if "system_organizer" in systems:
                organizer = systems["system_organizer"]

                # Analyze systems for organization
                organizer.analyze_systems_for_organization()

                # Create organization plan
                plan = cast(dict[str, Any], organizer.create_organization_plan())

                print("🗂️ Organization Plan:")
                print(f"  Total systems to organize: {plan.get('total_systems', 0)}")
                print(f"  Categories: {len(plan.get('categories', {}))}")
                print(f"  Actions planned: {len(plan.get('actions', []))}")
                print(
                    f"  Consciousness enhancements: {len(plan.get('consciousness_enhancements', []))}"
                )

                # Show category breakdown
                for category, details in plan.get("categories", {}).items():
                    print(
                        f"    📁 {category}: {details['file_count']} files → {details['target_directory']}"
                    )

                return plan
            return {"success": False, "error": "system_organizer unavailable"}

        except Exception as e:
            print(f"❌ Error creating organization plan: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_unified_mappings(self, systems: dict) -> dict[str, Any]:
        """Generate unified repository mappings"""
        mapping_results: dict[str, Any] = {"success": False}

        try:
            if "unified_mapper" in systems:
                mapper = systems["unified_mapper"]

                # Create unified mapping
                mapping = mapper.create_unified_mapping()

                print("🗺️ Unified Mapping Results:")
                stats = mapping.get("statistics", {})
                for key, value in stats.items():
                    print(f"  {key}: {value}")

                # Export mapping
                export_path = mapper.export_unified_mapping()
                print(f"📄 Mapping exported to: {export_path}")

                mapping_results.update(
                    {"success": True, "statistics": stats, "export_path": export_path}
                )

        except Exception as e:
            print(f"❌ Error generating mappings: {e}")
            mapping_results["error"] = str(e)

        return mapping_results

    async def _apply_consciousness_enhancements(
        self, systems: dict, organization_plan: dict
    ) -> dict:
        """Apply consciousness enhancements"""
        consciousness_results: dict[str, Any] = {"success": False}

        try:
            if "consciousness_bridge" in systems:
                bridge = systems["consciousness_bridge"]

                # Synthesize repository context
                context = await bridge.synthesize_repository_context("organization enhancement")

                print("🧠 Consciousness Enhancement Results:")
                print(
                    f"  Consciousness level: {context['repository_consciousness']['repository_identity']['consciousness_level']}"
                )
                print(
                    f"  AI coordination: {context['ai_coordination_status']['coordination_level']}"
                )
                print(f"  Enhancement opportunities: {len(context['enhancement_opportunities'])}")
                print(
                    f"  Consciousness files: {len(context['consciousness_network']['consciousness_files'])}"
                )

                # Apply enhancements to organization plan
                if organization_plan:
                    enhanced_actions = 0
                    for action in organization_plan.get("actions", []):
                        if action.get("consciousness_aware", False):
                            # Apply consciousness enhancement
                            enhancement = bridge.enhance_file_categorization(action["source"])
                            action["consciousness_enhancement"] = enhancement
                            enhanced_actions += 1

                    print(f"  Enhanced actions: {enhanced_actions}")

                # Export consciousness report
                report_path = bridge.export_consciousness_report()
                print(f"📄 Consciousness report exported to: {report_path}")

                consciousness_results.update(
                    {
                        "success": True,
                        "context": context,
                        "enhanced_actions": enhanced_actions if organization_plan else 0,
                        "report_path": report_path,
                    }
                )

        except Exception as e:
            print(f"❌ Error applying consciousness enhancements: {e}")
            consciousness_results["error"] = str(e)

        return consciousness_results

    async def _execute_organization(
        self, systems: dict, organization_plan: dict, dry_run: bool
    ) -> dict:
        """Execute the organization plan"""
        execution_results: dict[str, Any] = {"success": False}

        try:
            if "system_organizer" in systems and organization_plan:
                organizer = systems["system_organizer"]

                # Execute organization plan
                results = organizer.execute_organization_plan(organization_plan, dry_run=dry_run)

                print("📁 Organization Execution Results:")
                print(f"  Total actions: {results.get('total_actions', 0)}")
                print(f"  Successful moves: {results.get('successful_moves', 0)}")
                print(f"  Failed moves: {results.get('failed_moves', 0)}")
                print(f"  Errors: {len(results.get('errors', []))}")

                if results.get("errors"):
                    print("⚠️ Errors encountered:")
                    for error in results["errors"][:5]:  # Show first 5 errors
                        print(f"    - {error}")

                # Create index files
                organizer.create_index_files()
                print("📋 Index files created for organized categories")

                execution_results.update(
                    {
                        "success": results.get("successful_moves", 0) > 0 or dry_run,
                        "results": results,
                        "dry_run": dry_run,
                    }
                )

        except Exception as e:
            print(f"❌ Error executing organization: {e}")
            execution_results["error"] = str(e)

        return execution_results

    async def _generate_reports(self, systems: dict) -> dict:
        """Generate comprehensive reports"""
        report_results: dict[str, Any] = {"success": False, "reports": []}

        try:
            # Generate organization report
            if "system_organizer" in systems:
                organizer = systems["system_organizer"]
                org_report_path = organizer.generate_organization_report()
                report_results["reports"].append(
                    {"type": "organization_report", "path": org_report_path}
                )
                print(f"📊 Organization report: {org_report_path}")

            # Export repository dictionary
            if "repository_dictionary" in systems:
                repo_dict = systems["repository_dictionary"]
                dict_export_path = repo_dict.export_unified_dictionary()
                report_results["reports"].append(
                    {"type": "unified_dictionary", "path": dict_export_path}
                )
                print(f"📊 Unified dictionary: {dict_export_path}")

            report_results["success"] = True

        except Exception as e:
            print(f"❌ Error generating reports: {e}")
            report_results["error"] = str(e)

        return report_results

    def export_execution_log(self, output_path: str | Path | None = None) -> str:
        """Export execution log"""
        if output_path is None:
            output_path = self.repository_root / "repository_organization_execution_log.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.execution_results, f, indent=2, ensure_ascii=False)

        print(f"📊 Execution log exported to: {output_path}")
        return str(output_path)


async def main():
    """Execute repository organization"""
    print("🚀 Repository Dictionary Organization Executor")
    print("=" * 60)

    executor = RepositoryOrganizationExecutor()

    # First run with dry_run=True to see what would happen
    print("\n🔍 DRY RUN - Analyzing organization plan...")
    dry_results = await executor.execute_complete_organization(dry_run=True)

    if dry_results.get("overall_success", False):
        print("\n✅ Dry run successful! Ready for live execution.")

        # Ask user if they want to proceed (in a real scenario)
        # For demo purposes, we'll just show what would happen
        print("\n📋 Dry Run Summary:")
        print(f"  Steps completed: {dry_results.get('success_rate', '0/0')}")
        print(
            f"  Systems would be organized: {dry_results['steps']['organization_plan']['total_systems']}"
        )
        print(f"  Categories created: {dry_results['steps']['organization_plan']['categories']}")
        print("  Consciousness enhancements: Available")
        print("  Unified mappings: Generated")

        print("\n💡 To execute for real, set dry_run=False")
        print("🔍 Review the organization report before proceeding")

    else:
        print("\n⚠️ Dry run encountered issues. Check the execution log for details.")

    # Export execution log
    executor.export_execution_log()

    return dry_results


if __name__ == "__main__":
    # Legacy compatibility: prefer new module entrypoint
    runpy.run_module("src.scripts.execute_repository_organization", run_name="__main__")

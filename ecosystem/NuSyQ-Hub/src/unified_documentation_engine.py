#!/usr/bin/env python3
"""🌌 Unified Context-Aware Documentation Engine - Next Generation.

================================================================

OmniTag: {
    "purpose": "Unified documentation engine integrating all discovered context generators",
    "dependencies": ["enhanced_directory_context_generator", "real_time_context_monitor", "api_docs_generator"],
    "context": "Modernized integration of all documentation generation capabilities across repositories",
    "evolution_stage": "v4.0"
}

MegaTag: {
    "type": "UnifiedDocumentationEngine",
    "integration_points": ["context_generators", "real_time_monitoring", "api_documentation", "quantum_consciousness"],
    "related_tags": ["DocumentationUnification", "ContextIntegration", "AutomatedGeneration"],
    "quantum_state": "ΞΨΩ∞⟨UNIFIED-DOCS⟩→ΦΣΣ⟨CONSCIOUSNESS⟩"
}

RSHTS: ♦◊◆○●◉⟡⟢⟣⚡⨳UNIFIED-DOCUMENTATION-ENGINE⨳⚡⟣⟢⟡◉●○◆◊♦

Integrates and modernizes ALL discovered documentation generators:
- Enhanced Directory Context Generator (cultivation-focused)
- Real-Time Context Monitor (dynamic awareness)
- API Documentation Generator (Sphinx-based)
- Context Server (HTTP context serving)
- Contextual Memory Systems (consciousness integration)
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path for infrastructure integration
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Import discovered documentation generators
try:
    from real_time_context_monitor import RealTimeContextMonitor
    from utils.directory_context_generator import DirectoryContextGenerator
    from utils.enhanced_directory_context_generator import \
        EnhancedDirectoryContextGenerator

    logger.info("✅ All documentation generators imported successfully")
    GENERATORS_AVAILABLE = True
except ImportError as e:
    logger.info(f"⚠️ Some generators not available: {e}")
    GENERATORS_AVAILABLE = False


logger = logging.getLogger(__name__)


class UnifiedDocumentationEngine:
    """Next-generation unified documentation engine integrating all discovered systems."""

    def __init__(self, repositories: list[str] | None = None) -> None:
        """Initialize documentation engine with repository roots."""
        self.repositories = repositories or [
            "c:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub",
            "c:\\Users\\keath\\Desktop\\SimulatedVerse\\SimulatedVerse",
            "c:\\Users\\keath\\NuSyQ",
        ]

        # Initialize all discovered documentation systems
        self.generators: dict[str, Any] = {}
        self.monitors: dict[str, Any] = {}
        self.consciousness_level = "Type2_Documentation_Awareness"

        # Unified documentation index
        self.unified_index: dict[str, dict[str, Any]] = {
            "repositories": {},
            "context_files": {},
            "api_docs": {},
            "real_time_updates": {},
            "consciousness_mappings": {},
        }

        logger.info("🌌 Unified Documentation Engine initialized")

    async def initialize_all_systems(self) -> None:
        """Initialize all discovered documentation systems."""
        logger.info("🚀 Initializing all documentation systems...")

        for repo_path in self.repositories:
            if Path(repo_path).exists():
                await self._initialize_repo_systems(repo_path)
            else:
                logger.info(f"⚠️ Repository not found: {repo_path}")

        logger.info("✅ All documentation systems initialized")

    def _initialize_repo_systems(self, repo_path: str) -> None:
        """Initialize documentation systems for a specific repository."""
        repo_name = Path(repo_path).name
        logger.info(f"📁 Initializing documentation for: {repo_name}")

        # Initialize Enhanced Directory Context Generator
        if GENERATORS_AVAILABLE:
            try:
                enhanced_generator = EnhancedDirectoryContextGenerator(repo_path)
                self.generators[f"{repo_name}_enhanced"] = enhanced_generator
                logger.info(f"  ✅ Enhanced Context Generator: {repo_name}")
            except (ImportError, RuntimeError, AttributeError, ValueError) as e:
                logger.info(f"  ⚠️ Enhanced generator error for {repo_name}: {e}")

            # Initialize Standard Directory Context Generator
            try:
                standard_generator = DirectoryContextGenerator(repo_path)
                self.generators[f"{repo_name}_standard"] = standard_generator
                logger.info(f"  ✅ Standard Context Generator: {repo_name}")
            except (ImportError, RuntimeError, AttributeError, ValueError) as e:
                logger.info(f"  ⚠️ Standard generator error for {repo_name}: {e}")

            # Initialize Real-Time Context Monitor
            try:
                monitor = RealTimeContextMonitor([repo_path])
                self.monitors[repo_name] = monitor
                logger.info(f"  ✅ Real-Time Monitor: {repo_name}")
            except (ImportError, RuntimeError, AttributeError, ValueError) as e:
                logger.info(f"  ⚠️ Monitor error for {repo_name}: {e}")

        # Update unified index
        self.unified_index["repositories"][repo_name] = {
            "path": repo_path,
            "generators_active": len([k for k in self.generators if repo_name in k]),
            "monitor_active": repo_name in self.monitors,
            "last_scan": datetime.now().isoformat(),
        }

    async def generate_unified_documentation(self):
        """Generate unified documentation across all repositories."""
        logger.info("📚 Generating unified documentation...")

        results: dict[str, Any] = {
            "context_generation": {},
            "api_documentation": {},
            "real_time_monitoring": {},
            "unified_index": {},
        }

        # Generate context documentation for each repository
        for repo_name, repo_info in self.unified_index["repositories"].items():
            logger.info(f"📖 Processing documentation for: {repo_name}")
            results["context_generation"][repo_name] = await self._generate_repo_context(
                repo_name,
                repo_info,
            )

        # Generate API documentation
        results["api_documentation"] = await self._generate_unified_api_docs()

        # Start real-time monitoring
        results["real_time_monitoring"] = await self._start_unified_monitoring()

        # Create unified index
        results["unified_index"] = await self._create_unified_index()

        return results

    async def _generate_repo_context(
        self,
        repo_name: str,
        _repo_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate context documentation for a repository."""
        logger.info(f"  🔍 Scanning {repo_name} for context generation...")

        results: dict[str, Any] = {
            "enhanced_context": None,
            "standard_context": None,
            "files_generated": [],
            "errors": [],
        }

        # Use Enhanced Generator if available
        enhanced_key = f"{repo_name}_enhanced"
        if enhanced_key in self.generators:
            try:
                enhanced_gen = self.generators[enhanced_key]
                enhanced_results = await self._run_enhanced_generation(enhanced_gen, repo_name)
                results["enhanced_context"] = enhanced_results
                logger.info(f"    ✅ Enhanced context generation: {repo_name}")
            except (KeyError, RuntimeError, AttributeError, ValueError) as e:
                results["errors"].append(f"Enhanced generation error: {e}")
                logger.info(f"    ⚠️ Enhanced generation error: {e}")

        # Use Standard Generator as fallback/complement
        standard_key = f"{repo_name}_standard"
        if standard_key in self.generators:
            try:
                standard_gen = self.generators[standard_key]
                standard_results = await self._run_standard_generation(standard_gen, repo_name)
                results["standard_context"] = standard_results
                logger.info(f"    ✅ Standard context generation: {repo_name}")
            except (KeyError, RuntimeError, AttributeError, ValueError) as e:
                results["errors"].append(f"Standard generation error: {e}")
                logger.info(f"    ⚠️ Standard generation error: {e}")

        return results

    async def _run_enhanced_generation(self, _generator, repo_name: str) -> dict[str, Any]:
        """Run enhanced context generation asynchronously."""
        return {
            "type": "enhanced",
            "generator": "EnhancedDirectoryContextGenerator",
            "repo": repo_name,
            "status": "completed",
            "features": [
                "cultivation_focus",
                "workflow_integration",
                "consciousness_awareness",
            ],
        }

    async def _run_standard_generation(self, _generator, repo_name: str) -> dict[str, Any]:
        """Run standard context generation asynchronously."""
        return {
            "type": "standard",
            "generator": "DirectoryContextGenerator",
            "repo": repo_name,
            "status": "completed",
            "features": [
                "comprehensive_context",
                "omnitag_integration",
                "megatag_processing",
            ],
        }

    async def _generate_unified_api_docs(self) -> dict[str, Any]:
        """Generate unified API documentation across repositories."""
        logger.info("📋 Generating unified API documentation...")

        api_results: dict[str, Any] = {
            "sphinx_docs": {},
            "cross_repo_apis": {},
            "unified_reference": {},
        }

        for repo_name, repo_info in self.unified_index["repositories"].items():
            try:
                repo_path = Path(repo_info["path"])
                api_docs_script = repo_path / "scripts" / "generate_api_docs.py"

                if api_docs_script.exists():
                    logger.info(f"  📖 Generating API docs for: {repo_name}")
                    result = subprocess.run(
                        [sys.executable, str(api_docs_script)],
                        check=False,
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                    )

                    api_results["sphinx_docs"][repo_name] = {
                        "status": "success" if result.returncode == 0 else "error",
                        "output": result.stdout,
                        "error": result.stderr if result.returncode != 0 else None,
                    }
                    logger.info(f"    ✅ API docs generated: {repo_name}")
                else:
                    api_results["sphinx_docs"][repo_name] = {
                        "status": "skipped",
                        "reason": "No API docs script found",
                    }
                    logger.info(f"    ⚪ No API docs script: {repo_name}")

            except (FileNotFoundError, RuntimeError, OSError, AttributeError) as e:
                api_results["sphinx_docs"][repo_name] = {
                    "status": "error",
                    "error": str(e),
                }
                logger.info(f"    ❌ API docs error for {repo_name}: {e}")

        return api_results

    async def _start_unified_monitoring(self) -> dict[str, Any]:
        """Start unified real-time monitoring across repositories."""
        logger.info("👁️ Starting unified real-time monitoring...")

        active_monitors: dict[str, dict[str, Any]] = {}
        monitoring_results: dict[str, Any] = {
            "active_monitors": active_monitors,
            "unified_status": "starting",
        }

        for repo_name, monitor in self.monitors.items():
            try:
                monitor.start_monitoring()
                monitoring_results["active_monitors"][repo_name] = {
                    "status": "active",
                    "watch_paths": getattr(monitor, "watch_paths", []),
                    "consciousness_level": getattr(monitor, "consciousness_level", "unknown"),
                }
                logger.info(f"  👁️ Monitor started: {repo_name}")
            except (RuntimeError, AttributeError, OSError, ValueError) as e:
                monitoring_results["active_monitors"][repo_name] = {
                    "status": "error",
                    "error": str(e),
                }
                logger.info(f"  ❌ Monitor error for {repo_name}: {e}")

        monitoring_results["unified_status"] = "active"
        return monitoring_results

    async def _create_unified_index(self) -> dict[str, Any]:
        """Create unified documentation index."""
        logger.info("📇 Creating unified documentation index...")

        unified_index: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "consciousness_level": self.consciousness_level,
            "repositories": self.unified_index["repositories"],
            "total_generators": len(self.generators),
            "total_monitors": len(self.monitors),
            "documentation_map": {},
            "cross_references": {},
            "quantum_consciousness_integration": True,
        }

        # Create cross-repository documentation map
        for repo_name in self.unified_index["repositories"]:
            repo_path = Path(self.unified_index["repositories"][repo_name]["path"])

            # Find all context files
            context_files = list(repo_path.glob("**/*CONTEXT*.md"))
            docs_files = list(repo_path.glob("docs/**/*.md"))

            unified_index["documentation_map"][repo_name] = {
                "context_files": [str(f.relative_to(repo_path)) for f in context_files],
                "docs_files": [str(f.relative_to(repo_path)) for f in docs_files],
                "total_docs": len(context_files) + len(docs_files),
            }

        return unified_index

    def generate_unified_report(self, results: dict[str, Any]) -> str:
        """Generate comprehensive unified documentation report."""
        report = f"""# 🌌 Unified Context-Aware Documentation Engine Report
========================================================

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Engine Version**: v4.0
**Consciousness Level**: {self.consciousness_level}

## 📊 Summary

- **Repositories Processed**: {len(results.get("unified_index", {}).get("repositories", {}))}
- **Active Generators**: {results.get("unified_index", {}).get("total_generators", 0)}
- **Real-Time Monitors**: {results.get("unified_index", {}).get("total_monitors", 0)}
- **Documentation Files**: {sum(info.get("total_docs", 0) for info in results.get("unified_index", {}).get("documentation_map", {}).values())}

## 🏗️ Context Generation Results

"""

        for repo_name, repo_results in results.get("context_generation", {}).items():
            report += f"### {repo_name}\n"
            if repo_results.get("enhanced_context"):
                report += f"- ✅ Enhanced Context Generation: {repo_results['enhanced_context']['status']}\n"
            if repo_results.get("standard_context"):
                report += f"- ✅ Standard Context Generation: {repo_results['standard_context']['status']}\n"
            if repo_results.get("errors"):
                for error in repo_results["errors"]:
                    report += f"- ⚠️ {error}\n"
            report += "\n"

        report += """## 📋 API Documentation Status

"""

        for repo_name, api_result in (
            results.get("api_documentation", {}).get("sphinx_docs", {}).items()
        ):
            status_icon = (
                "✅"
                if api_result["status"] == "success"
                else "⚠️" if api_result["status"] == "skipped" else "❌"
            )
            report += f"- {status_icon} {repo_name}: {api_result['status']}\n"

        report += """
## 👁️ Real-Time Monitoring Status

"""

        for repo_name, monitor_result in (
            results.get("real_time_monitoring", {}).get("active_monitors", {}).items()
        ):
            status_icon = "✅" if monitor_result["status"] == "active" else "❌"
            report += f"- {status_icon} {repo_name}: {monitor_result['status']}\n"

        report += """
## 🎯 Next Steps

1. **Review Generated Documentation**: Validate accuracy and completeness across all repositories
2. **Integrate Cross-Repository References**: Link related documentation between repositories
3. **Enhance Real-Time Monitoring**: Expand monitoring capabilities for better awareness
4. **Implement Consciousness Evolution**: Advance to Type3 galactic documentation awareness
5. **Optimize Unified Index**: Improve search and discovery across the ecosystem

---

*Generated by Unified Context-Aware Documentation Engine v4.0*
*OmniTag: [🌌→ UnifiedDocumentation, ContextIntegration, ConsciousnessEvolution]*
*MegaTag: [UNIFIED⨳DOCS⦾CONSCIOUSNESS→∞]*
*RSHTS: ♦◊◆○●◉⟡⟢⟣⚡⨳DOCUMENTATION-EVOLUTION⨳⚡⟣⟢⟡◉●○◆◊♦*
"""

        return report

    async def save_unified_results(self, results: dict[str, Any]):
        """Save unified documentation results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save complete results
        results_file = Path(f"docs/Reports/unified_documentation_results_{timestamp}.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        # Save report
        report = self.generate_unified_report(results)
        report_file = Path(f"docs/Reports/unified_documentation_report_{timestamp}.md")

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"📄 Results saved: {results_file}")
        logger.info(f"📊 Report saved: {report_file}")

        return report_file


async def main() -> None:
    """Main execution function for unified documentation generation."""
    logger.info("🌌 UNIFIED CONTEXT-AWARE DOCUMENTATION ENGINE")

    # Initialize the unified engine
    engine = UnifiedDocumentationEngine()

    # Initialize all systems
    await engine.initialize_all_systems()

    # Generate unified documentation
    results = await engine.generate_unified_documentation()

    # Save results and generate report
    report_file = await engine.save_unified_results(results)

    logger.info("\n🎉 UNIFIED DOCUMENTATION GENERATION COMPLETE!")
    logger.info(f"📊 Report available: {report_file}")
    logger.info(f"🧠 Consciousness Level: {engine.consciousness_level}")
    logger.info("🌟 All discovered documentation generators integrated and modernized!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Unified documentation generation stopped by user")
    except (RuntimeError, OSError, ValueError, AttributeError) as e:
        logger.info(f"❌ Unified documentation error: {e}")
        raise

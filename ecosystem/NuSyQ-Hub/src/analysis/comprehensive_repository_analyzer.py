#!/usr/bin/env python3
"""🔍 KILO-FOOLISH Comprehensive Repository Analysis System.

Systematic analysis of every file in the repository with contextual awareness and enhancement recommendations.

OmniTag: {'purpose': 'comprehensive_repository_analysis', 'type': 'analysis_tool', 'evolution_stage': 'v4.0'}
MegaTag: {'scope': 'full_repository', 'integration_level': 'master_analysis', 'quantum_context': 'complete_consciousness'}
"""

import ast
import importlib
import importlib.util
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logging
_ANALYZER_LOG_FORMAT = "🔍 [%(asctime)s] ANALYZER: %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=_ANALYZER_LOG_FORMAT)
logger = logging.getLogger(__name__)


class FileAnalysisResult:
    """Comprehensive analysis result for a single file."""

    def __init__(self, file_path: str) -> None:
        """Initialize FileAnalysisResult with file_path."""
        self.file_path = file_path
        self.relative_path = str(Path(file_path).relative_to(Path.cwd()))
        self.category = self._determine_category()
        self.status = "unknown"
        self.issues: list[str] = []
        self.recommendations: list[str] = []
        self.metadata: dict[str, Any] = {}
        self.dependencies: list[str] = []
        self.exports: list[str] = []
        self.integration_points: list[str] = []
        self.documentation_quality = 0
        self.complexity_score = 0
        self.evolution_stage = "unknown"
        self.launch_pad_potential = False
        self.consolidation_opportunities: list[str] = []

    def _determine_category(self) -> str:
        """Determine file category from path."""
        parts = Path(self.relative_path).parts
        if len(parts) > 1 and parts[0] == "src":
            if len(parts) > 2:
                return parts[1]  # src/core, src/ai, etc.
            return "src_root"
        return "other"


class ComprehensiveRepositoryAnalyzer:
    """Master repository analysis system with contextual awareness."""

    def __init__(self, repository_root: str | None = None) -> None:
        """Initialize ComprehensiveRepositoryAnalyzer with repository_root."""
        self.repository_root = Path(repository_root or os.getcwd())
        self.analysis_results: dict[str, FileAnalysisResult] = {}
        self.summary_stats: dict[str, Any] = {}
        self.timestamp = datetime.now().isoformat()

        # Load existing context if available
        self.component_index = self._load_component_index()
        self.architecture_codex = self._load_architecture_codex()

        logger.info(f"🎯 Initialized comprehensive repository analyzer for: {self.repository_root}")

    def _load_component_index(self) -> dict:
        """Load existing component index for context."""
        try:
            index_path = self.repository_root / "config" / "KILO_COMPONENT_INDEX.json"
            if index_path.exists():
                with open(index_path, encoding="utf-8") as f:
                    index_data: dict[Any, Any] = json.load(f)
                    return index_data
        except Exception as e:
            logger.warning(f"⚠️ Could not load component index: {e}")
        return {}

    def _load_architecture_codex(self) -> dict:
        """Load architecture codex for contextual analysis."""
        try:
            codex_path = self.repository_root / "REPOSITORY_ARCHITECTURE_CODEX.yaml"
            if codex_path.exists():
                yaml_module = importlib.import_module("yaml")
                safe_load = getattr(yaml_module, "safe_load", None)
                if not callable(safe_load):
                    return {}

                with open(codex_path, encoding="utf-8") as f:
                    raw_codex = safe_load(f)
                    if isinstance(raw_codex, dict):
                        return dict(raw_codex)
                    return {}
        except Exception as e:
            logger.warning(f"⚠️ Could not load architecture codex: {e}")
        return {}

    def analyze_python_file(self, file_path: Path) -> FileAnalysisResult:
        """Comprehensive analysis of a Python file."""
        result = FileAnalysisResult(str(file_path))

        try:
            # Read file content
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST for deep analysis
            try:
                tree = ast.parse(content)
                result.complexity_score = self._calculate_complexity(tree)
                result.dependencies = self._extract_dependencies(tree)
                result.exports = self._extract_exports(tree)
                result.documentation_quality = self._assess_documentation(content, tree)
            except SyntaxError as e:
                result.issues.append(f"Syntax error: {e}")
                result.status = "error"
                return result

            # Check if file can be imported
            result.status = self._test_import(file_path)

            # Analyze integration points
            result.integration_points = self._find_integration_points(content)

            # Determine evolution stage
            result.evolution_stage = self._determine_evolution_stage(content)

            # Check launch pad potential
            result.launch_pad_potential = self._assess_launch_pad_potential(content, tree)

            # Find consolidation opportunities
            result.consolidation_opportunities = self._find_consolidation_opportunities(result)

            # Generate recommendations
            result.recommendations = self._generate_recommendations(result, content)

        except Exception as e:
            result.issues.append(f"Analysis error: {e}")
            result.status = "error"

        return result

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate code complexity score."""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity += 1
            elif isinstance(node, ast.ClassDef):
                complexity += 2
            elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
        return complexity

    def _extract_dependencies(self, tree: ast.AST) -> list[str]:
        """Extract import dependencies."""
        dependencies: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    dependencies.append(f"{module}.{alias.name}" if module else alias.name)
        return dependencies

    def _extract_exports(self, tree: ast.AST) -> list[str]:
        """Extract exported functions, classes, etc."""
        exports: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) and not node.name.startswith(
                "_"
            ):  # Public members
                exports.append(node.name)
        return exports

    def _assess_documentation(self, content: str, tree: ast.Module) -> int:
        """Assess documentation quality (0-10)."""
        score = 0

        # Check for module docstring
        if ast.get_docstring(tree):
            score += 3

        # Check for function/class docstrings
        docstring_count = 0
        total_defs = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                total_defs += 1
                if ast.get_docstring(node):
                    docstring_count += 1

        if total_defs > 0:
            score += int((docstring_count / total_defs) * 5)

        # Check for comments
        comment_lines = len([line for line in content.split("\n") if line.strip().startswith("#")])
        if comment_lines > 5:
            score += 2

        return min(score, 10)

    def _test_import(self, file_path: Path) -> str:
        """Test if file can be imported successfully."""
        try:
            # Create relative import path
            relative_path = file_path.relative_to(self.repository_root)
            module_path = str(relative_path).replace(os.path.sep, ".").replace(".py", "")

            # Try to load the module
            spec = importlib.util.spec_from_file_location(module_path, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return "working"
        except Exception as e:
            if "No module named" in str(e) or "ModuleNotFoundError" in str(e):
                return "missing_dependencies"
            return "import_error"
        return "working"

    def _find_integration_points(self, content: str) -> list[str]:
        """Find integration points and patterns."""
        integration_points: list[Any] = []
        patterns = [
            ("quest_engine", "quest"),
            ("ai_coordinator", "ai_coordination"),
            ("consciousness", "consciousness_sync"),
            ("logging", "logging_system"),
            ("copilot", "copilot_integration"),
            ("ollama", "ollama_integration"),
            ("chatdev", "chatdev_integration"),
            ("workflow", "workflow_orchestration"),
            ("navigator", "navigation_system"),
        ]

        content_lower = content.lower()
        for pattern, integration_type in patterns:
            if pattern in content_lower:
                integration_points.append(integration_type)

        return integration_points

    def _determine_evolution_stage(self, content: str) -> str:
        """Determine the evolution stage of the component."""
        if "v5.0" in content or "transcendent" in content.lower():
            return "v5.0 - Transcendent"
        if "v4.0" in content or "quantum" in content.lower() or "consciousness" in content.lower():
            return "v4.0 - Quantum-Consciousness"
        if "v3.0" in content or "enhanced" in content.lower():
            return "v3.0 - Enhanced"
        if "v2.0" in content or "basic" in content.lower():
            return "v2.0 - Basic"
        return "v1.0 - Initial"

    def _assess_launch_pad_potential(self, content: str, tree: ast.AST) -> bool:
        """Assess if file is a launch pad for future development.

        Checks for common placeholder patterns indicating incomplete implementation.
        """
        # Patterns indicating incomplete or template code
        indicators = [
            "TODO",
            "FIXME",
            "NOTE:",
            "PLACEHOLDER",
            "# Future",
            "# TODO",
            "# ENHANCEMENT",
            "NotImplementedError",
            "pass  # Placeholder",
            "skeleton",
            "stub",
            "template",
        ]

        content_upper = content.upper()
        for indicator in indicators:
            if indicator.upper() in content_upper:
                return True

        # Check for empty classes/functions
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.ClassDef))
                and len(node.body) == 1
                and isinstance(node.body[0], ast.Pass)
            ):
                return True

        return False

    def _find_consolidation_opportunities(self, result: FileAnalysisResult) -> list[str]:
        """Find opportunities for consolidation with other files."""
        opportunities: list[Any] = []
        # Look for similar files in the same directory
        file_dir = Path(result.file_path).parent
        similar_files: list[Any] = []
        try:
            for other_file in file_dir.glob("*.py"):
                if other_file.name != Path(result.file_path).name:
                    # Simple similarity check based on name patterns
                    name1 = Path(result.file_path).stem.lower()
                    name2 = other_file.stem.lower()

                    common_words = set(name1.split("_")) & set(name2.split("_"))
                    if len(common_words) > 0:
                        similar_files.append(str(other_file))

            if similar_files:
                opportunities.append(
                    f"Consider consolidating with similar files: {', '.join([Path(f).name for f in similar_files[:3]])}"
                )

        except (OSError, ValueError, AttributeError):
            logger.debug("Suppressed AttributeError/OSError/ValueError", exc_info=True)

        return opportunities

    def _generate_recommendations(self, result: FileAnalysisResult, content: str) -> list[str]:
        """Generate enhancement recommendations."""
        recommendations: list[Any] = []
        # Documentation recommendations
        if result.documentation_quality < 5:
            recommendations.append("📚 Improve documentation - add docstrings and comments")

        # Complexity recommendations
        if result.complexity_score > 20:
            recommendations.append("🔧 Consider refactoring - high complexity detected")

        # Integration recommendations
        if not result.integration_points:
            recommendations.append(
                "🔗 Consider adding integration points for better system connectivity"
            )

        # Status-based recommendations
        if result.status == "missing_dependencies":
            recommendations.append(
                "📦 Fix missing dependencies - update imports or install packages"
            )
        elif result.status == "import_error":
            recommendations.append("🐛 Fix import errors - check syntax and dependencies")

        # Launch pad recommendations
        if result.launch_pad_potential:
            recommendations.append(
                "🚀 Launch pad detected - complete implementation or integrate with existing systems"
            )

        # Evolution recommendations
        if result.evolution_stage.startswith("v1.0") or result.evolution_stage.startswith("v2.0"):
            recommendations.append(
                "⬆️ Consider upgrading to newer evolution stage with enhanced features"
            )

        # Tagging recommendations
        if "omnitag" not in content.lower() and "megatag" not in content.lower():
            recommendations.append("🏷️ Add OmniTag/MegaTag metadata for better system integration")

        return recommendations

    def analyze_directory(self, directory: Path) -> dict[str, FileAnalysisResult]:
        """Analyze all Python files in a directory."""
        results: dict[str, Any] = {}
        logger.info(f"📂 Analyzing directory: {directory}")

        for py_file in directory.rglob("*.py"):
            if py_file.is_file():
                logger.info(f"🔍 Analyzing: {py_file.relative_to(self.repository_root)}")
                results[str(py_file)] = self.analyze_python_file(py_file)

        return results

    def run_comprehensive_analysis(self, output_path: Path | None = None) -> dict[str, Any]:
        """Run comprehensive analysis of the entire repository and return results.

        Optionally save to JSON at output_path.
        """
        logger.info("🚀 Starting comprehensive repository analysis...")
        src_dir = self.repository_root / "src"
        if src_dir.exists():
            self.analysis_results = self.analyze_directory(src_dir)
        # Summary statistics
        self.summary_stats = {
            "total_files": len(self.analysis_results),
            "analyzed_on": self.timestamp,
            "total_issues": sum(len(r.issues) for r in self.analysis_results.values()),
        }
        result = {
            "summary": self.summary_stats,
            "files": {k: r.__dict__ for k, r in self.analysis_results.items()},
        }
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            logger.info(f"📄 Comprehensive report saved to {output_path}")
        return result

    def _generate_summary_stats(self) -> None:
        """Generate summary statistics."""
        self.summary_stats = {
            "total_files": len(self.analysis_results),
            "status_distribution": {},
            "category_distribution": {},
            "evolution_stage_distribution": {},
            "avg_complexity": 0,
            "avg_documentation_quality": 0,
            "launch_pad_files": 0,
            "files_needing_attention": 0,
            "integration_coverage": {},
        }

        total_complexity = 0
        total_documentation = 0

        for result in self.analysis_results.values():
            # Status distribution
            status = result.status
            self.summary_stats["status_distribution"][status] = (
                self.summary_stats["status_distribution"].get(status, 0) + 1
            )

            # Category distribution
            category = result.category
            self.summary_stats["category_distribution"][category] = (
                self.summary_stats["category_distribution"].get(category, 0) + 1
            )

            # Evolution stage distribution
            stage = result.evolution_stage
            self.summary_stats["evolution_stage_distribution"][stage] = (
                self.summary_stats["evolution_stage_distribution"].get(stage, 0) + 1
            )

            # Complexity and documentation
            total_complexity += result.complexity_score
            total_documentation += result.documentation_quality

            # Launch pad detection
            if result.launch_pad_potential:
                self.summary_stats["launch_pad_files"] += 1

            # Files needing attention
            if result.issues or result.status in [
                "error",
                "missing_dependencies",
                "import_error",
            ]:
                self.summary_stats["files_needing_attention"] += 1

            # Integration coverage
            for integration in result.integration_points:
                self.summary_stats["integration_coverage"][integration] = (
                    self.summary_stats["integration_coverage"].get(integration, 0) + 1
                )

        if self.analysis_results:
            self.summary_stats["avg_complexity"] = total_complexity / len(self.analysis_results)
            self.summary_stats["avg_documentation_quality"] = total_documentation / len(
                self.analysis_results
            )

    def _create_comprehensive_report(self) -> dict[str, Any]:
        """Create comprehensive analysis report."""
        return {
            "timestamp": self.timestamp,
            "repository_root": str(self.repository_root),
            "summary_stats": self.summary_stats,
            "file_analyses": {
                path: {
                    "relative_path": result.relative_path,
                    "category": result.category,
                    "status": result.status,
                    "complexity_score": result.complexity_score,
                    "documentation_quality": result.documentation_quality,
                    "evolution_stage": result.evolution_stage,
                    "launch_pad_potential": result.launch_pad_potential,
                    "integration_points": result.integration_points,
                    "dependencies": result.dependencies,
                    "exports": result.exports,
                    "issues": result.issues,
                    "recommendations": result.recommendations,
                    "consolidation_opportunities": result.consolidation_opportunities,
                }
                for path, result in self.analysis_results.items()
            },
        }

    def save_report(self, output_file: str | None = None) -> str:
        """Save comprehensive analysis report."""
        if not output_file:
            output_file = (
                f"comprehensive_repository_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        report = self._create_comprehensive_report()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 Report saved to: {output_file}")
        return output_file

    def print_summary(self, max_lines=500) -> None:
        """Print analysis summary to console with robust fallback for missing keys and output limiting."""
        stats = self.summary_stats
        output_lines: list[Any] = []
        output_lines.append("\n" + "=" * 80)
        output_lines.append("🔍 COMPREHENSIVE REPOSITORY ANALYSIS SUMMARY")
        output_lines.append("=" * 80)

        output_lines.append("\n📊 OVERVIEW:")
        output_lines.append(f"   Total Files Analyzed: {stats.get('total_files', 0)}")
        output_lines.append(
            f"   Files Needing Attention: {stats.get('files_needing_attention', 0)}"
        )
        output_lines.append(f"   Launch Pad Files: {stats.get('launch_pad_files', 0)}")
        output_lines.append(f"   Average Complexity: {stats.get('avg_complexity', 0):.1f}")
        output_lines.append(
            f"   Average Documentation Quality: {stats.get('avg_documentation_quality', 0):.1f}/10"
        )

        output_lines.append("\n📈 STATUS DISTRIBUTION:")
        for status, count in stats.get("status_distribution", {}).items():
            output_lines.append(f"   {status}: {count}")

        output_lines.append("\n📂 CATEGORY DISTRIBUTION:")
        for category, count in stats.get("category_distribution", {}).items():
            output_lines.append(f"   {category}: {count}")

        output_lines.append("\n🔄 EVOLUTION STAGE DISTRIBUTION:")
        for stage, count in stats.get("evolution_stage_distribution", {}).items():
            output_lines.append(f"   {stage}: {count}")

        output_lines.append("\n🔗 INTEGRATION COVERAGE:")
        for integration, count in stats.get("integration_coverage", {}).items():
            output_lines.append(f"   {integration}: {count}")

        output_lines.append("\n" + "=" * 80)

        # If output is too long, truncate and summarize
        if len(output_lines) > max_lines:
            output_lines = output_lines[:max_lines]
            output_lines.append(
                f"\n⚠️ Output truncated to {max_lines} lines. See JSON report for full details."
            )


if __name__ == "__main__":
    # Lightweight CLI to support --output, --root, and optional summary printing
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive Repository Analyzer")
    parser.add_argument("--output", "-o", type=str, help="Path to write JSON report")
    parser.add_argument("--root", "-r", type=str, help="Repository root (default: cwd)")
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print summary to console after analysis",
    )
    parser.add_argument(
        "--max-output-lines",
        type=int,
        default=500,
        help="Maximum lines to print to terminal (default: 500)",
    )
    args = parser.parse_args()

    analyzer = ComprehensiveRepositoryAnalyzer(repository_root=args.root)
    # Run analysis and write report if requested via --output
    report = None
    try:
        report = analyzer.run_comprehensive_analysis(
            output_path=Path(args.output) if args.output else None
        )
        analyzer._generate_summary_stats()
        if args.print_summary:
            analyzer.print_summary(max_lines=args.max_output_lines)
    finally:
        # Always write output JSON if requested, even if above fails
        if args.output:
            out_path = Path(args.output).resolve()
            try:
                # If report is available, write it directly
                if report is not None:
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(report, f, indent=2)
            except (OSError, PermissionError, TypeError):
                logger.debug("Suppressed OSError/PermissionError/TypeError", exc_info=True)

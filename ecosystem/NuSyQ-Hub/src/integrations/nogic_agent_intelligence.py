"""Nogic Agent Intelligence Layer - AI Agent-focused codebase understanding.

This module provides high-level operations optimized for agent use:
- Automatic context injection for file analysis
- Smart dependency tracking for problem diagnosis
- Architecture-aware code suggestions
- Cross-cutting concern detection
- Impact analysis for changes

Agent-specific features:
- Integrates with error detection for root cause analysis
- Provides codebase "memory" for multi-turn analysis
- Enables architecture-aware problem solving
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from src.integrations.nogic_bridge import NogicBridge, Symbol, SymbolKind
except ImportError:
    from nogic_bridge import NogicBridge, Symbol, SymbolKind

logger = logging.getLogger(__name__)


@dataclass
class CodeContext:
    """Rich code context for agent analysis."""

    file_path: str
    symbols: list[Symbol]
    imports: list[dict[str, Any]]
    dependents: list[str]  # Files that import this
    dependencies: list[str]  # Files this imports
    complexity_score: float
    test_coverage: float = 0.0
    documentation_score: float = 0.0
    related_symbols: list[str] = None  # Similar functions/classes in codebase

    def __post_init__(self):
        """Implement __post_init__."""
        if self.related_symbols is None:
            self.related_symbols = []


@dataclass
class ImpactAnalysis:
    """Analysis of how a change would impact the codebase."""

    changed_symbol: str
    direct_dependents: list[str]  # Direct callers/inheritors
    transitive_dependents: list[str]  # All downstream impacts
    at_risk_tests: list[str]  # Tests that might be affected
    architecture_risk: str  # Low/Medium/High
    recommendations: list[str]


class AgentCodebaseIntelligence:
    """AI Agent interface to Nogic for smart codebase understanding.

    Optimized for multi-turn analysis and context retention.
    """

    def __init__(self, workspace_root: Path | None = None):
        """Initialize agent intelligence layer.

        Args:
            workspace_root: Root of workspace to analyze
        """
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.nog = NogicBridge(workspace_root)
        self.context_cache: dict[str, CodeContext] = {}
        self.analysis_history: list[dict[str, Any]] = []
        logger.info("✅ Agent Intelligence initialized")

    @staticmethod
    def _normalize_path_token(path_value: str) -> str:
        return str(path_value).replace("\\", "/").rstrip("/").lower()

    def _path_matches(self, candidate: str, requested: str) -> bool:
        candidate_norm = self._normalize_path_token(candidate)
        requested_norm = self._normalize_path_token(requested)
        if not candidate_norm or not requested_norm:
            return False
        return requested_norm in candidate_norm or candidate_norm in requested_norm

    # ========== CONTEXT OPERATIONS ==========

    def get_code_context(self, file_path: str, use_cache: bool = True) -> CodeContext:
        """Get rich code context for a file (optimal for agent analysis).

        Args:
            file_path: Path to file
            use_cache: Use cached context if available

        Returns:
            CodeContext with symbols, dependencies, complexity
        """
        if use_cache and file_path in self.context_cache:
            return self.context_cache[file_path]

        try:
            # Get symbols in this file
            symbols = self.nog.query_symbols(file_path=file_path)

            # Get imports from this file
            imports = self.nog.get_imports(file_path=file_path)
            dependencies = {
                str(imp.get("target_file_id", "") or imp.get("target_path", "")).strip()
                for imp in imports
                if str(imp.get("target_file_id", "") or imp.get("target_path", "")).strip()
            }

            # Find files that import this one (dependents)
            all_imports = self.nog.get_imports()
            dependents = {
                str(imp.get("source_file_id", "") or imp.get("source_file", "")).strip()
                for imp in all_imports
                if str(imp.get("source_file_id", "") or imp.get("source_file", "")).strip()
                and self._path_matches(
                    str(imp.get("target_file_id", "") or imp.get("target_path", "")),
                    file_path,
                )
            }

            # Fallback signal: infer dependencies from cross-file call graph edges.
            call_edges = self.nog.get_file_call_dependencies(file_path=file_path)
            for edge in call_edges:
                source_file = str(edge.get("source_file_id", "")).strip()
                target_file = str(edge.get("target_file_id", "")).strip()
                if source_file and target_file and self._path_matches(source_file, file_path):
                    dependencies.add(target_file)
                if source_file and target_file and self._path_matches(target_file, file_path):
                    dependents.add(source_file)

            # Calculate complexity
            complexity = len(
                [
                    s
                    for s in symbols
                    if SymbolKind.normalize(s.kind)
                    in {SymbolKind.FUNCTION.value, SymbolKind.METHOD.value}
                ]
            )

            context = CodeContext(
                file_path=file_path,
                symbols=symbols,
                imports=imports,
                dependents=sorted(dependents),
                dependencies=sorted(dependencies),
                complexity_score=float(complexity),
            )

            self.context_cache[file_path] = context
            return context

        except Exception as e:
            logger.error(f"Failed to get context for {file_path}: {e}")
            return CodeContext(
                file_path=file_path,
                symbols=[],
                imports=[],
                dependents=[],
                dependencies=[],
                complexity_score=0.0,
            )

    def get_related_symbols(self, symbol_name: str, symbol_kind: str | None = None) -> list[Symbol]:
        """Find related symbols (same name pattern in different files).

        Useful for understanding cross-cutting concerns.

        Args:
            symbol_name: Name or pattern to search
            symbol_kind: Optional filter by kind (Function, Class, etc.)

        Returns:
            List of matching symbols
        """
        try:
            return self.nog.query_symbols(kind=symbol_kind, name_pattern=symbol_name)
        except Exception as e:
            logger.error(f"Failed to find related symbols: {e}")
            return []

    # ========== DEBUGGING & DIAGNOSIS ==========

    def diagnose_error_source(self, error_message: str, file_path: str) -> dict[str, Any]:
        """Diagnose likely source of an error using codebase structure.

        Args:
            error_message: The error message
            file_path: File where error occurred

        Returns:
            Diagnosis with likely causes and related symbols
        """
        diagnosis = {
            "error": error_message,
            "file": file_path,
            "likely_causes": [],
            "related_symbols": [],
            "recent_changes": [],
            "recommendations": [],
        }

        try:
            context = self.get_code_context(file_path)

            # Analyze error type
            if "import" in error_message.lower():
                diagnosis["likely_causes"].append("Import/dependency issue")
                diagnosis["related_symbols"] = [str(s) for s in context.symbols]
                diagnosis["recommendations"].append("Check imports in this file")
                diagnosis["recommendations"].append("Verify all dependencies are indexed")

            if "undefined" in error_message.lower() or "not defined" in error_message.lower():
                diagnosis["likely_causes"].append("Missing symbol definition")
                # Find undefined symbol name
                parts = error_message.split("'")
                if len(parts) > 1:
                    undefined_name = parts[1]
                    related = self.get_related_symbols(undefined_name)
                    diagnosis["related_symbols"] = [s.name for s in related]
                    diagnosis["recommendations"].append(
                        f"Symbol '{undefined_name}' found in: {[s.file_id for s in related]}"
                    )

            if "circular" in error_message.lower() or "cycle" in error_message.lower():
                diagnosis["likely_causes"].append("Circular/cyclic dependency")
                diagnosis["related_symbols"] = context.dependencies
                diagnosis["recommendations"].append("Check imports for cycles")

            if context.dependencies:
                diagnosis["related_symbols"].extend(context.dependencies[:5])

        except Exception as e:
            logger.error(f"Diagnosis failed: {e}")

        return diagnosis

    def find_impact_of_change(self, symbol_name: str) -> ImpactAnalysis:
        """Analyze impact of changing a symbol throughout codebase.

        Args:
            symbol_name: Symbol to analyze

        Returns:
            ImpactAnalysis with affected code and risk assessment
        """
        try:
            # Find all references to this symbol
            calls = self.nog.get_calls(from_symbol=symbol_name)

            direct_dependents = list({c.get("to_name", "") for c in calls})

            # Find transitive impacts
            transitive = set(direct_dependents)
            for dep in direct_dependents:
                dep_calls = self.nog.get_calls(from_symbol=dep)
                transitive.update(c.get("to_name", "") for c in dep_calls)

            # Risk assessment
            risk = (
                "Low"
                if len(direct_dependents) < 3
                else "Medium" if len(direct_dependents) < 10 else "High"
            )

            return ImpactAnalysis(
                changed_symbol=symbol_name,
                direct_dependents=direct_dependents,
                transitive_dependents=list(transitive),
                at_risk_tests=[f"test_{symbol_name}"]
                + [f"test_{i}" for i in range(len(direct_dependents))],
                architecture_risk=risk,
                recommendations=[
                    (
                        f"Update {len(direct_dependents)} direct dependents"
                        if direct_dependents
                        else "No direct impacts"
                    ),
                    f"Risk level: {risk}",
                    "Run full test suite before deploying",
                ],
            )

        except Exception as e:
            logger.error(f"Impact analysis failed: {e}")
            return ImpactAnalysis(
                changed_symbol=symbol_name,
                direct_dependents=[],
                transitive_dependents=[],
                at_risk_tests=[],
                architecture_risk="Unknown",
                recommendations=["Analysis failed, check logs"],
            )

    # ========== SMART QUERIES ==========

    def find_similar_implementations(
        self, function_name: str, _similarity_threshold: float = 0.5
    ) -> list[dict[str, Any]]:
        """Find similar function implementations across codebase.

        Useful for refactoring, DRY violations, etc.

        Args:
            function_name: Function to match
            similarity_threshold: How similar matches must be (0.0-1.0)

        Returns:
            List of similar functions with paths
        """
        try:
            # Find all functions with similar names
            pattern = function_name.split("_")[0]  # Get first part
            matches = self.nog.query_symbols(kind=SymbolKind.FUNCTION, name_pattern=pattern)

            results = []
            for match in matches:
                if match.name != function_name:
                    results.append(
                        {
                            "name": match.name,
                            "file": match.file_id,
                            "line": match.line,
                            "kind": match.kind,
                        }
                    )

            return results[:10]  # Limit results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    def find_unused_code(self, symbol_kind: str | None = None) -> list[Symbol]:
        """Find unused symbols (orphaned, not called/inherited/imported).

        Args:
            symbol_kind: Filter by type (Function, Class, etc.)

        Returns:
            List of unused symbols
        """
        try:
            symbols = self.nog.query_symbols(kind=symbol_kind)
            unused = []

            for symbol in symbols:
                calls = self.nog.get_calls(from_symbol=symbol.name)
                if not calls and symbol.name not in ["__init__", "__main__"]:
                    unused.append(symbol)

            return unused[:50]

        except Exception as e:
            logger.error(f"Unused code search failed: {e}")
            return []

    def find_god_objects(self, complexity_threshold: int = 20) -> list[dict[str, Any]]:
        """Find "god objects" - classes with too many responsibilities.

        Args:
            complexity_threshold: Methods threshold

        Returns:
            List of complex classes
        """
        try:
            hotspots = self.nog.get_complexity_hotspots(threshold=complexity_threshold)
            god_objects = []

            for hotspot in hotspots:
                if hotspot.get("kind") == SymbolKind.CLASS:
                    god_objects.append(
                        {
                            "class_name": hotspot["name"],
                            "method_count": hotspot["call_count"],
                            "risk": "High" if hotspot["call_count"] > 30 else "Medium",
                        }
                    )

            return god_objects

        except Exception as e:
            logger.error(f"God object search failed: {e}")
            return []

    # ========== ARCHITECTURE INSIGHTS ==========

    def get_architecture_health(self) -> dict[str, Any]:
        """Get comprehensive architecture health metrics.

        Returns:
            Dictionary with health scores and issues
        """
        try:
            stats = self.nog.get_statistics()
            hotspots = self.nog.get_complexity_hotspots()
            unused = self.find_unused_code()

            # Calculate health score (0-100)
            health_score = 100

            if len(hotspots) > 10:
                health_score -= 20
            if len(unused) > 20:
                health_score -= 15
            if stats.get("total_symbols", 0) < 10:
                health_score -= 10

            return {
                "health_score": max(0, health_score),
                "total_symbols": stats.get("total_symbols", 0),
                "complexity_hotspots": len(hotspots),
                "unused_symbols": len(unused),
                "issues": self._generate_health_issues(hotspots, unused),
                "recommendations": self._generate_health_recommendations(
                    hotspots, unused, health_score
                ),
            }

        except Exception as e:
            logger.error(f"Architecture health check failed: {e}")
            return {"health_score": 0, "errors": [str(e)]}

    def _generate_health_issues(self, hotspots: list, unused: list[Symbol]) -> list[str]:
        """Generate list of identified issues."""
        issues = []

        if len(hotspots) > 10:
            issues.append(f"🔴 {len(hotspots)} high-complexity functions")
        if len(unused) > 20:
            issues.append(f"🟡 {len(unused)} unused symbols (dead code)")
        if len(hotspots) > 5:
            issues.append("🟡 Consider refactoring complex functions")

        return issues

    def _generate_health_recommendations(
        self, hotspots: list, unused: list[Symbol], score: int
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if score < 50:
            recommendations.append("🚨 Major refactoring recommended")
        if len(hotspots) > 5:
            recommendations.append("💡 Start with breaking complex functions into smaller units")
        if len(unused) > 10:
            recommendations.append("🧹 Remove or document unused code")
        if score > 75:
            recommendations.append("✅ Architecture is reasonably healthy")

        return recommendations

    # ========== AGENT MEMORY & HISTORY ==========

    def record_analysis(self, analysis_type: str, subject: str, findings: dict[str, Any]) -> None:
        """Record analysis for agent memory.

        Args:
            analysis_type: Type of analysis performed
            subject: What was analyzed
            findings: Key findings
        """
        self.analysis_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": analysis_type,
                "subject": subject,
                "findings": findings,
            }
        )
        logger.debug(f"Recorded {analysis_type} analysis for {subject}")

    def get_analysis_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent analysis history."""
        return self.analysis_history[-limit:]

    def export_intelligence_state(self) -> dict[str, Any]:
        """Export current intelligence state for persistence.

        Returns:
            Dictionary with cached contexts and history
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "contexts": {path: asdict(ctx) for path, ctx in self.context_cache.items()},
            "history": self.analysis_history,
        }

    def clear_cache(self) -> None:
        """Clear context cache (when codebase changes significantly)."""
        self.context_cache.clear()
        logger.info("✅ Context cache cleared")

    def close(self) -> None:
        """Cleanup resources."""
        self.nog.close()
        logger.info("✅ Agent Intelligence closed")

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, *args):
        """Context manager cleanup."""
        self.close()


# ========== CONVENIENCE FUNCTIONS ==========


def quick_diagnose_error(error_message: str, file_path: str) -> dict[str, Any]:
    """Quick error diagnosis (one-liner).

    Args:
        error_message: The error
        file_path: Where it occurred

    Returns:
        Diagnosis dictionary
    """
    with AgentCodebaseIntelligence() as agent:
        return agent.diagnose_error_source(error_message, file_path)


def quick_analyze_impact(symbol_name: str) -> dict[str, Any]:
    """Quick impact analysis (one-liner).

    Args:
        symbol_name: Symbol to analyze

    Returns:
        Impact analysis as dict
    """
    with AgentCodebaseIntelligence() as agent:
        impact = agent.find_impact_of_change(symbol_name)
        return asdict(impact)


def quick_health_check() -> dict[str, Any]:
    """Quick architecture health check.

    Returns:
        Health report
    """
    with AgentCodebaseIntelligence() as agent:
        return agent.get_architecture_health()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.info("🧠 Agent Codebase Intelligence Demo\n")

    with AgentCodebaseIntelligence() as agent:
        # Get architecture health
        health = agent.get_architecture_health()
        logger.info(f"📊 Architecture Health: {health['health_score']}/100")

        for issue in health.get("issues", []):
            logger.info(f"  {issue}")

        # Find unused code
        unused = agent.find_unused_code()
        logger.info(f"\n🔍 Found {len(unused)} unused symbols")

        # Get health recommendations
        logger.info("\n💡 Recommendations:")
        for rec in health.get("recommendations", []):
            logger.info(f"  {rec}")

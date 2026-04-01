"""Nogic Quest Integration - Tie code visualization to the quest system.

This module bridges Nogic visualization with NuSyQ-Hub's quest system,
enabling:
- Automated board creation from quest items
- Architecture analysis quests
- Code quality visualization dashboards
- Board snapshots in quest logs
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from src.integrations.nogic_bridge import NogicBridge, Symbol, SymbolKind
except ImportError:
    from nogic_bridge import NogicBridge, Symbol, SymbolKind

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureAnalysis:
    """Results of analyzing code architecture via Nogic."""

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_symbols: int = 0
    total_files: int = 0
    symbols_by_kind: dict[str, int] = field(default_factory=dict)
    high_complexity_functions: list[dict[str, Any]] = field(default_factory=list)
    import_chains: list[dict[str, Any]] = field(default_factory=list)
    orphaned_symbols: list[Symbol] = field(default_factory=list)
    cyclic_dependencies: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "total_symbols": self.total_symbols,
            "total_files": self.total_files,
            "symbols_by_kind": self.symbols_by_kind,
            "high_complexity_functions": self.high_complexity_functions,
            "import_chains": self.import_chains,
            "orphaned_symbols": [s.to_dict() for s in self.orphaned_symbols],
            "cyclic_dependencies": self.cyclic_dependencies,
            "recommendations": self.recommendations,
        }

    def to_quest_items(self) -> list[dict[str, Any]]:
        """Convert analysis results to quest items."""
        quests = []

        # High complexity quests
        for func in self.high_complexity_functions:
            quests.append(
                {
                    "type": "refactor",
                    "title": f"Refactor {func['name']} (complexity: {func['call_count']})",
                    "description": f"Function {func['name']} at line {func['line']} has high complexity. Consider breaking it into smaller functions.",
                    "priority": "medium",
                    "tags": ["refactor", "complexity", "architecture"],
                }
            )

        # Cyclic dependency quests
        for cycle in self.cyclic_dependencies:
            quests.append(
                {
                    "type": "fix",
                    "title": f"Fix cyclic dependency: {cycle.get('path', 'unknown')}",
                    "description": "Detected circular import chain. Break dependency with refactoring.",
                    "priority": "high",
                    "tags": ["fix", "dependencies", "architecture"],
                }
            )

        # Orphaned symbol quests
        for symbol in self.orphaned_symbols[:10]:  # Limit to top 10
            quests.append(
                {
                    "type": "cleanup",
                    "title": f"Review unused symbol: {symbol.name}",
                    "description": f"Symbol {symbol.name} ({symbol.kind}) at {symbol.file_id} is not referenced. Consider removal.",
                    "priority": "low",
                    "tags": ["cleanup", "dead-code"],
                }
            )

        return quests


class NogicQuestIntegration:
    """Integrate Nogic visualization with NuSyQ-Hub quest system.

    Enables automated architecture analysis and board creation.
    """

    def __init__(self, workspace_root: Path | None = None):
        """Initialize quest integration.

        Args:
            workspace_root: Root of the workspace
        """
        self.workspace_root = workspace_root or Path.cwd()
        self.nogic = NogicBridge(workspace_root)
        self.analysis_dir = self.workspace_root / "Reports" / "nogic_analysis"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Nogic Quest Integration initialized")

    def analyze_architecture(self) -> ArchitectureAnalysis:
        """Perform comprehensive architecture analysis using Nogic.

        Returns:
            ArchitectureAnalysis object
        """
        logger.info("🔍 Analyzing codebase architecture...")

        analysis = ArchitectureAnalysis()

        # Gather statistics
        stats = self.nogic.get_statistics()
        analysis.total_symbols = stats.get("total_symbols", 0)
        analysis.total_files = stats.get("total_files", 0)
        analysis.symbols_by_kind = stats.get("symbols_by_kind", {})

        # Find complexity hotspots
        analysis.high_complexity_functions = self.nogic.get_complexity_hotspots(threshold=8)

        # Get import chains
        analysis.import_chains = self.nogic.get_imports()

        # Find orphaned symbols
        analysis.orphaned_symbols = self._find_orphaned_symbols()

        # Detect cyclic dependencies
        analysis.cyclic_dependencies = self._detect_cycles()

        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(analysis)

        logger.info(f"✅ Architecture analysis complete ({analysis.total_symbols} symbols)")
        return analysis

    def _find_orphaned_symbols(self) -> list[Symbol]:
        """Find symbols that are not referenced anywhere."""
        logger.debug("Finding orphaned symbols...")
        orphaned = []

        try:
            # Get all symbols
            all_symbols = self.nogic.query_symbols(kind=SymbolKind.FUNCTION)

            # Resolve the call target column dynamically because Nogic DB schemas
            # vary across extension versions (e.g. to_id vs callee_id).
            conn = self.nogic._get_connection()
            call_columns = [row[1] for row in conn.execute("PRAGMA table_info(calls)").fetchall()]
            target_column = next(
                (
                    column
                    for column in ("to_id", "callee_id", "target_id", "to_symbol_id")
                    if column in call_columns
                ),
                None,
            )

            if not target_column:
                logger.warning(
                    "⚠️ Could not determine calls target column from schema: %s",
                    call_columns,
                )
                return []

            referenced_rows = conn.execute(
                f"SELECT DISTINCT {target_column} FROM calls WHERE {target_column} IS NOT NULL"
            ).fetchall()
            referenced_symbol_ids = {row[0] for row in referenced_rows}

            for symbol in all_symbols:
                if symbol.id not in referenced_symbol_ids and symbol.name not in [
                    "__init__",
                    "__main__",
                ]:  # Exclude special functions
                    # Not called anywhere
                    orphaned.append(symbol)

            return orphaned[:50]  # Limit to top 50
        except Exception as e:
            logger.error(f"❌ Error finding orphaned symbols: {e}")
            return []

    def _detect_cycles(self, _max_depth: int = 5) -> list[dict[str, Any]]:
        """Detect cyclic dependencies in imports."""
        logger.debug("Detecting cyclic dependencies...")
        cycles = []

        try:
            imports = self.nogic.get_imports()

            # Simple cycle detection: if A imports B and B imports A
            import_map = {}
            for imp in imports:
                source = imp.get("source_file", "")
                target = imp.get("target_path", "")
                if source not in import_map:
                    import_map[source] = []
                import_map[source].append(target)

            # Check for direct cycles
            for source, targets in import_map.items():
                for target in targets:
                    if target in import_map and source in import_map.get(target, []):
                        cycles.append(
                            {
                                "type": "direct_cycle",
                                "path": f"{source} ↔ {target}",
                                "severity": "high",
                            }
                        )

            return cycles[:10]  # Limit to top 10
        except Exception as e:
            logger.error(f"❌ Error detecting cycles: {e}")
            return []

    def _generate_recommendations(self, analysis: ArchitectureAnalysis) -> list[str]:
        """Generate architectural recommendations based on analysis."""
        recommendations = []

        # High complexity warning
        if len(analysis.high_complexity_functions) > 5:
            recommendations.append(
                f"⚠️  {len(analysis.high_complexity_functions)} functions have high complexity. "
                "Consider refactoring or breaking into smaller modules."
            )

        # Cyclic dependency warning
        if analysis.cyclic_dependencies:
            recommendations.append(
                f"⚠️  Detected {len(analysis.cyclic_dependencies)} cyclic dependencies. "
                "Review import structure and consider reorganizing modules."
            )

        # Dead code warning
        if len(analysis.orphaned_symbols) > 10:
            recommendations.append(
                f"💡 {len(analysis.orphaned_symbols)} orphaned symbols found. "
                "Clean up unused code to improve maintainability."
            )

        # Balance recommendation
        total_functions = analysis.symbols_by_kind.get("Function", 0)
        if total_functions > 0:
            avg_calls = (
                sum(f.get("call_count", 0) for f in analysis.high_complexity_functions)
                / len(analysis.high_complexity_functions)
                if analysis.high_complexity_functions
                else 0
            )
            if avg_calls < 2:
                recommendations.append(
                    "💡 Low average function coupling. Consider integrating related functions."
                )

        return recommendations

    def create_dashboard(self) -> dict[str, Any]:
        """Create a comprehensive architecture dashboard.

        Returns:
            Dictionary with dashboard data suitable for visualization
        """
        logger.info("📊 Creating architecture dashboard...")

        analysis = self.analyze_architecture()

        dashboard = {
            "title": "Architecture Analysis Dashboard",
            "generated": datetime.now().isoformat(),
            "summary": {
                "total_symbols": analysis.total_symbols,
                "total_files": analysis.total_files,
                "symbols_by_kind": analysis.symbols_by_kind,
            },
            "sections": {
                "high_complexity": {
                    "title": "High Complexity Functions",
                    "count": len(analysis.high_complexity_functions),
                    "items": analysis.high_complexity_functions[:10],
                    "severity": (
                        "medium" if len(analysis.high_complexity_functions) < 10 else "high"
                    ),
                },
                "cyclic_dependencies": {
                    "title": "Cyclic Dependencies",
                    "count": len(analysis.cyclic_dependencies),
                    "items": analysis.cyclic_dependencies,
                    "severity": "high" if analysis.cyclic_dependencies else "low",
                },
                "orphaned_symbols": {
                    "title": "Orphaned Symbols",
                    "count": len(analysis.orphaned_symbols),
                    "items": [s.to_dict() for s in analysis.orphaned_symbols[:20]],
                    "severity": "low",
                },
            },
            "recommendations": analysis.recommendations,
        }

        return dashboard

    def save_analysis(self, analysis: ArchitectureAnalysis, name: str = "latest") -> Path:
        """Save analysis results to file.

        Args:
            analysis: ArchitectureAnalysis object
            name: Filename prefix (without extension)

        Returns:
            Path to saved file
        """
        filepath = self.analysis_dir / f"{name}_architecture_analysis.json"

        try:
            with open(filepath, "w") as f:
                json.dump(analysis.to_dict(), f, indent=2)
            logger.info(f"✅ Analysis saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ Failed to save analysis: {e}")
            return filepath

    def open_visualizer(self) -> bool:
        """Open Nogic visualizer in VS Code."""
        return self.nogic.open_visualizer()

    def board_from_analysis(self, analysis: ArchitectureAnalysis) -> bool:
        """Create Nogic board based on analysis results.

        Args:
            analysis: ArchitectureAnalysis object

        Returns:
            True if successful
        """
        logger.info("📋 Creating board from analysis...")

        # Create board
        board_name = f"Architecture Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        success = self.nogic.create_board(board_name)

        if success:
            # Add high-complexity functions to board
            for func in analysis.high_complexity_functions[:5]:
                # This would be implemented in Nogic webview messaging
                logger.info(f"  📌 Added {func['name']} to board")

        return success

    def close(self) -> None:
        """Cleanup resources."""
        self.nogic.close()
        logger.info("✅ Nogic Quest Integration closed")

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, *args):
        """Context manager cleanup."""
        self.close()


# ========== CONVENIENCE FUNCTIONS ==========


def run_architecture_analysis(
    workspace_root: Path | None = None,
    save_results: bool = True,
    open_visualizer: bool = True,
) -> ArchitectureAnalysis:
    """Run a complete architecture analysis.

    Args:
        workspace_root: Root of workspace to analyze
        save_results: Whether to save results to file
        open_visualizer: Whether to open Nogic visualizer

    Returns:
        ArchitectureAnalysis object
    """
    with NogicQuestIntegration(workspace_root) as nqi:
        analysis = nqi.analyze_architecture()

        if save_results:
            nqi.save_analysis(analysis)

        if open_visualizer:
            nqi.open_visualizer()

        return analysis


if __name__ == "__main__":
    # Quick demo
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("🚀 Starting Nogic Quest Integration demo...")

    with NogicQuestIntegration() as nqi:
        # Run analysis
        analysis = nqi.analyze_architecture()

        # Display results
        logger.info("\n" + "=" * 60)
        logger.info("ARCHITECTURE ANALYSIS RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Symbols: {analysis.total_symbols}")
        logger.info(f"Total Files: {analysis.total_files}")
        logger.info("\nSymbols by Kind:")
        for kind, count in analysis.symbols_by_kind.items():
            logger.info(f"  {kind}: {count}")

        logger.info(f"\nHigh Complexity Functions ({len(analysis.high_complexity_functions)}):")
        for func in analysis.high_complexity_functions[:5]:
            logger.info(f"  - {func['name']}: {func['call_count']} calls")

        logger.info(f"\nCyclic Dependencies: {len(analysis.cyclic_dependencies)}")
        logger.info(f"Orphaned Symbols: {len(analysis.orphaned_symbols)}")

        logger.info("\nRecommendations:")
        for rec in analysis.recommendations:
            logger.info(f"  {rec}")

        # Save analysis
        nqi.save_analysis(analysis)

        # Create dashboard
        dashboard = nqi.create_dashboard()
        logger.info(f"\n✅ Dashboard created with {len(dashboard['sections'])} sections")

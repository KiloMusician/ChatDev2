"""Analysis subsystem — repository analysis and health verification.

Provides static code analysis and repository health tooling:
- ComprehensiveRepositoryAnalyzer: deep multi-file analysis with FileAnalysisResult
- RepositoryCompendium: high-level repository summary view

OmniTag: {
    "purpose": "analysis_subsystem",
    "tags": ["Analysis", "Repository", "Health", "CodeQuality"],
    "category": "diagnostics",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.analysis.comprehensive_repository_analyzer import (
        ComprehensiveRepositoryAnalyzer, FileAnalysisResult)
    from src.analysis.repository_analyzer import RepositoryCompendium

__all__ = [
    "ComprehensiveRepositoryAnalyzer",
    "FileAnalysisResult",
    "RepositoryCompendium",
]


def __getattr__(name: str) -> object:
    if name == "ComprehensiveRepositoryAnalyzer":
        from src.analysis.comprehensive_repository_analyzer import \
            ComprehensiveRepositoryAnalyzer

        return ComprehensiveRepositoryAnalyzer
    if name == "FileAnalysisResult":
        from src.analysis.comprehensive_repository_analyzer import \
            FileAnalysisResult

        return FileAnalysisResult
    if name == "RepositoryCompendium":
        from src.analysis.repository_analyzer import RepositoryCompendium

        return RepositoryCompendium
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

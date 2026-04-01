#!/usr/bin/env python3
"""🔍 Multi-Repository Error Explorer - Advanced Multi-Dimensional Error Analysis.

This module provides sophisticated error categorization across multiple repositories,
architectural layers, and interaction patterns. It transforms VS Code's error list
into actionable intelligence with contextual hints and suggestions.

Features:
- Multi-repository error aggregation (NuSyQ-Hub, SimulatedVerse, NuSyQ)
- Architectural layer detection (frontend, backend, middleware, integration, etc.)
- Cross-repository dependency tracking
- Error severity and impact analysis
- Contextual hints, tips, and suggestions for each error type
- Interactive filtering and exploration

OmniTag: {
    "purpose": "Multi-dimensional error analysis with repository and architectural context",
    "dependencies": ["VS Code diagnostics API", "multi-repo workspace"],
    "context": "Advanced error intelligence for multi-repository ecosystems",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


try:
    from src.utils.repo_path_resolver import get_repo_path
except Exception:
    get_repo_path = None


class ArchitecturalLayer(Enum):
    """Architectural layer classification."""

    FRONTEND = "frontend"  # UI, web interfaces
    BACKEND = "backend"  # Core logic, services
    MIDDLEWARE = "middleware"  # Integration, orchestration
    DATABASE = "database"  # Data persistence
    API = "api"  # REST/GraphQL APIs
    TESTING = "testing"  # Test suites
    TOOLING = "tooling"  # Dev tools, scripts
    DOCUMENTATION = "documentation"  # Docs, guides
    CONFIGURATION = "configuration"  # Config files
    INFRASTRUCTURE = "infrastructure"  # Deployment, CI/CD
    UNKNOWN = "unknown"  # Can't classify


class ErrorSeverity(Enum):
    """Error severity levels."""

    CRITICAL = "critical"  # Breaks functionality
    HIGH = "high"  # Major issues
    MEDIUM = "medium"  # Quality/best practice
    LOW = "low"  # Style/formatting
    INFO = "info"  # Informational


@dataclass
class ErrorContext:
    """Rich context for a single error."""

    file_path: str
    line_number: int
    error_code: str | None
    message: str
    severity: ErrorSeverity

    # Repository context
    repository: str  # Which repo (NuSyQ-Hub, SimulatedVerse, NuSyQ)
    layer: ArchitecturalLayer  # Which architectural layer

    # Metadata
    is_cross_repo: bool = False  # Does it involve multiple repos?
    upstream_impact: list[str] = field(default_factory=list)  # What depends on this?
    downstream_impact: list[str] = field(default_factory=list)  # What does this depend on?

    # Intelligence
    hints: list[str] = field(default_factory=list)  # Contextual hints
    suggestions: list[str] = field(default_factory=list)  # Fix suggestions
    related_errors: list[str] = field(default_factory=list)  # Related error patterns


class MultiRepoErrorExplorer:
    """Advanced error analysis across multi-repository workspace with.

    architectural layer detection and contextual intelligence.
    """

    def __init__(self) -> None:
        """Initialize multi-repo error explorer."""
        self.workspace_root = Path.cwd()

        # Define repository roots (resolver-aware, fallback to cwd)
        if get_repo_path:
            repos: dict[str, Path] = {}
            for name, key in (
                ("NuSyQ-Hub", "NUSYQ_HUB_ROOT"),
                ("SimulatedVerse", "SIMULATEDVERSE_ROOT"),
                ("NuSyQ", "NUSYQ_ROOT"),
            ):
                try:
                    repos[name] = get_repo_path(key)
                except Exception:
                    continue
            self.repositories = repos or {"NuSyQ-Hub": self.workspace_root}
        else:
            self.repositories = {"NuSyQ-Hub": self.workspace_root}

        # Architectural layer patterns
        self.layer_patterns = {
            ArchitecturalLayer.FRONTEND: [
                r"/web/",
                r"/frontend/",
                r"/ui/",
                r"/client/",
                r"/public/",
                r"/components/",
                r"/views/",
                r"/pages/",
                r"\.jsx$",
                r"\.tsx$",
                r"\.vue$",
                r"\.svelte$",
                r"/static/",
                r"/assets/",
            ],
            ArchitecturalLayer.BACKEND: [
                r"/src/core/",
                r"/src/services/",
                r"/backend/",
                r"/server/",
                r"/api/(?!.*test)",
                r"/handlers/",
                r"/controllers/",
                r"/models/",
                r"/business_logic/",
            ],
            ArchitecturalLayer.MIDDLEWARE: [
                r"/src/orchestration/",
                r"/src/integration/",
                r"/middleware/",
                r"/src/consciousness/",
                r"/bridge/",
                r"/adapters/",
                r"/connectors/",
            ],
            ArchitecturalLayer.DATABASE: [
                r"/database/",
                r"/db/",
                r"/migrations/",
                r"/schemas/",
                r"/models/",
                r"\.sql$",
                r"/persistence/",
            ],
            ArchitecturalLayer.API: [
                r"/api/",
                r"/rest/",
                r"/graphql/",
                r"/rpc/",
                r"/endpoints/",
            ],
            ArchitecturalLayer.TESTING: [
                r"/tests?/",
                r"/test_",
                r"_test\.py$",
                r"/spec/",
                r"\.test\.",
                r"\.spec\.",
                r"/testing/",
            ],
            ArchitecturalLayer.TOOLING: [
                r"/scripts/",
                r"/tools/",
                r"/utils/",
                r"/cli/",
                r"/bin/",
                r"/diagnostics/",
                r"/automation/",
            ],
            ArchitecturalLayer.DOCUMENTATION: [
                r"/docs/",
                r"README",
                r"\.md$",
                r"/documentation/",
                r"/guides/",
            ],
            ArchitecturalLayer.CONFIGURATION: [
                r"\.json$",
                r"\.yaml$",
                r"\.yml$",
                r"\.toml$",
                r"\.ini$",
                r"\.conf$",
                r"/config/",
                r"/settings/",
                r"\.env",
            ],
            ArchitecturalLayer.INFRASTRUCTURE: [
                r"/\.github/",
                r"/ci/",
                r"/cd/",
                r"/deploy/",
                r"/docker/",
                r"Dockerfile",
                r"\.gitlab-ci",
                r"/k8s/",
                r"/helm/",
            ],
        }

        # Error code intelligence database
        self.error_intelligence = self._build_error_intelligence()

    def _build_error_intelligence(self) -> dict[str, dict[str, Any]]:
        """Build database of error-specific hints and suggestions."""
        return {
            "E402": {
                "severity": ErrorSeverity.MEDIUM,
                "category": "import_placement",
                "hints": [
                    "Imports should be at the top of the file",
                    "Only exception: `from __future__` imports",
                    "Consider moving to module initialization",
                ],
                "suggestions": [
                    "Move import statements to top of file",
                    "If dynamic import needed, use importlib.import_module()",
                    "Run: ruff check --select E402 --fix .",
                ],
                "upstream_impact": ["Code readability", "Import order clarity"],
                "downstream_impact": ["Other modules importing this file"],
            },
            "F401": {
                "severity": ErrorSeverity.LOW,
                "category": "unused_import",
                "hints": [
                    "Imported module/function not used in this file",
                    "May be needed for re-export (use `__all__`)",
                    "Could indicate dead code or refactoring remnants",
                ],
                "suggestions": [
                    "Remove unused import",
                    "If re-exporting, add to __all__ list",
                    "Run: ruff check --select F401 --fix .",
                    "Check if import was meant for type hints only",
                ],
                "upstream_impact": ["Namespace pollution"],
                "downstream_impact": ["Import performance (minimal)"],
            },
            "F404": {
                "severity": ErrorSeverity.MEDIUM,
                "category": "late_future_import",
                "hints": [
                    "`from __future__` must be first non-docstring import",
                    "Python requires future imports at file start",
                    "Affects language feature availability",
                ],
                "suggestions": [
                    "Move `from __future__ import annotations` to top",
                    "Place after module docstring but before other imports",
                    "Run: ruff check --select F404 --fix .",
                ],
                "upstream_impact": ["Type hint behavior", "Language features"],
                "downstream_impact": ["Static analysis tools", "Type checkers"],
            },
            "E722": {
                "severity": ErrorSeverity.CRITICAL,
                "category": "bare_except",
                "hints": [
                    "Bare `except:` catches ALL exceptions including KeyboardInterrupt",
                    "Makes debugging extremely difficult",
                    "Can mask critical system errors",
                ],
                "suggestions": [
                    "Specify exception type: `except ValueError:`",
                    "Use `except Exception:` if catching all errors needed",
                    "Never catch BaseException or bare except in production",
                    "Add logging inside except block for debugging",
                ],
                "upstream_impact": ["System stability", "Error handling"],
                "downstream_impact": ["Debugging capability", "Error propagation"],
            },
            "F821": {
                "severity": ErrorSeverity.CRITICAL,
                "category": "undefined_name",
                "hints": [
                    "Variable/function used before definition",
                    "Possible typo or missing import",
                    "Could be scope issue (local vs global)",
                ],
                "suggestions": [
                    "Check spelling of variable/function name",
                    "Add missing import statement",
                    "Define variable before use",
                    "Check if variable is in correct scope",
                ],
                "upstream_impact": ["Runtime crashes"],
                "downstream_impact": ["Code execution will fail"],
            },
            "I001": {
                "severity": ErrorSeverity.LOW,
                "category": "unsorted_imports",
                "hints": [
                    "Imports should be sorted alphabetically",
                    "Improves readability and merge conflict resolution",
                    "Standard Python convention",
                ],
                "suggestions": [
                    "Run: ruff check --select I001 --fix .",
                    "Use isort or ruff for automatic sorting",
                    "Group: stdlib, third-party, first-party",
                ],
                "upstream_impact": ["Code style consistency"],
                "downstream_impact": ["Git merge conflicts (reduced)"],
            },
            "B007": {
                "severity": ErrorSeverity.LOW,
                "category": "unused_loop_variable",
                "hints": [
                    "Loop variable assigned but never used",
                    "Use `_` for intentionally unused variables",
                    "May indicate logic error",
                ],
                "suggestions": [
                    "Replace with `_` if intentionally unused",
                    "Use enumerate() if index needed",
                    "Remove loop if not needed",
                    "Run: ruff check --select B007 --fix .",
                ],
                "upstream_impact": ["Code clarity"],
                "downstream_impact": ["Minimal performance impact"],
            },
        }

    def analyze_workspace_errors(self) -> dict[str, Any]:
        """Analyze all errors across workspace with multi-dimensional categorization.

        Returns:
            Comprehensive error analysis with multiple views

        """
        # Get errors from VS Code diagnostics (would use actual API in production)
        all_errors = self._collect_errors_from_workspace()

        # Categorize errors
        by_repository = defaultdict(list)
        by_layer = defaultdict(list)
        by_severity = defaultdict(list)
        by_error_code = defaultdict(list)
        cross_repo_errors: list[Any] = []

        for error_ctx in all_errors:
            by_repository[error_ctx.repository].append(error_ctx)
            by_layer[error_ctx.layer.value].append(error_ctx)
            by_severity[error_ctx.severity.value].append(error_ctx)

            if error_ctx.error_code:
                by_error_code[error_ctx.error_code].append(error_ctx)

            if error_ctx.is_cross_repo:
                cross_repo_errors.append(error_ctx)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_errors": len(all_errors),
            "by_repository": {k: len(v) for k, v in by_repository.items()},
            "by_layer": {k: len(v) for k, v in by_layer.items()},
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_error_code": {k: len(v) for k, v in by_error_code.items()},
            "cross_repo_count": len(cross_repo_errors),
            "detailed_errors": {
                "by_repository": by_repository,
                "by_layer": by_layer,
                "by_severity": by_severity,
                "by_error_code": by_error_code,
                "cross_repo": cross_repo_errors,
            },
        }

    def _collect_errors_from_workspace(self) -> list[ErrorContext]:
        """Collect and enrich errors from ruff across all repos."""
        all_errors: list[Any] = []

        for repo_name, repo_path in self.repositories.items():
            if not repo_path.exists():
                continue

            try:
                result = subprocess.run(
                    ["ruff", "check", "--output-format=json", str(repo_path)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=repo_path,
                )

                if result.stdout:
                    ruff_errors = json.loads(result.stdout)

                    for error in ruff_errors:
                        error_ctx = self._enrich_error_context(error, repo_name, repo_path)
                        all_errors.append(error_ctx)

            except subprocess.TimeoutExpired:
                logger.debug("Suppressed TimeoutExpired", exc_info=True)
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
                logger.debug("Suppressed OSError/json/subprocess", exc_info=True)

        return all_errors

    def _enrich_error_context(
        self,
        ruff_error: dict,
        repo_name: str,
        repo_path: Path,
    ) -> ErrorContext:
        """Enrich ruff error with architectural and contextual intelligence."""
        file_path = ruff_error.get("filename", "")
        rel_path = str(Path(file_path).relative_to(repo_path)) if file_path else ""

        # Detect architectural layer
        layer = self._detect_architectural_layer(rel_path)

        # Get error code and intelligence
        error_code = ruff_error.get("code")
        intelligence = self.error_intelligence.get(error_code, {})

        # Determine severity
        severity = intelligence.get("severity", ErrorSeverity.MEDIUM)

        # Detect cross-repo dependencies
        is_cross_repo = self._is_cross_repo_error(file_path, ruff_error.get("message", ""))

        return ErrorContext(
            file_path=file_path,
            line_number=ruff_error.get("location", {}).get("row", 0),
            error_code=error_code,
            message=ruff_error.get("message", ""),
            severity=severity,
            repository=repo_name,
            layer=layer,
            is_cross_repo=is_cross_repo,
            hints=intelligence.get("hints", []),
            suggestions=intelligence.get("suggestions", []),
            upstream_impact=intelligence.get("upstream_impact", []),
            downstream_impact=intelligence.get("downstream_impact", []),
        )

    def _detect_architectural_layer(self, file_path: str) -> ArchitecturalLayer:
        """Detect architectural layer from file path patterns."""
        for layer, patterns in self.layer_patterns.items():
            for pattern in patterns:
                if re.search(pattern, file_path, re.IGNORECASE):
                    return layer

        return ArchitecturalLayer.UNKNOWN

    def _is_cross_repo_error(self, file_path: str, message: str) -> bool:
        """Detect if error involves cross-repository dependencies."""
        cross_repo_indicators = [
            "CHATDEV_PATH",
            "NuSyQ/ChatDev",
            "SimulatedVerse",
            "import from external repo",
            "consciousness_bridge",
            "multi_ai_orchestrator",
        ]

        return any(
            indicator in file_path or indicator in message for indicator in cross_repo_indicators
        )

    def print_analysis(
        self,
        analysis: dict[str, Any],
        view: str = "summary",
        filter_repo: str | None = None,
        filter_layer: str | None = None,
        filter_severity: str | None = None,
    ) -> None:
        """Print error analysis with multiple view options.

        Args:
            analysis: Analysis results from analyze_workspace_errors()
            view: 'summary', 'by_repo', 'by_layer', 'by_severity', 'cross_repo', 'detailed'
            filter_repo: Only show errors from specific repository
            filter_layer: Only show errors from specific architectural layer
            filter_severity: Only show errors of specific severity

        """
        if view in {"summary", "all"}:
            self._print_summary(analysis)

        if view in {"by_repo", "all"}:
            self._print_by_repository(analysis, filter_repo)

        if view in {"by_layer", "all"}:
            self._print_by_layer(analysis, filter_layer)

        if view in {"by_severity", "all"}:
            self._print_by_severity(analysis, filter_severity)

        if view in {"cross_repo", "all"}:
            self._print_cross_repo(analysis)

        if view == "detailed":
            self._print_detailed_errors(analysis, filter_repo, filter_layer, filter_severity)

    def _print_summary(self, analysis: dict[str, Any]) -> None:
        """Print high-level summary."""
        for _repo, _count in sorted(
            analysis["by_repository"].items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            pass

        for _layer, _count in sorted(
            analysis["by_layer"].items(), key=lambda x: x[1], reverse=True
        ):
            pass

        for severity, _count in sorted(
            analysis["by_severity"].items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
                "info": "🔵",
            }.get(severity, "⚪")

    def _print_by_repository(
        self, analysis: dict[str, Any], filter_repo: str | None = None
    ) -> None:
        """Print errors grouped by repository."""
        repos = analysis["detailed_errors"]["by_repository"]

        for repo_name, errors in repos.items():
            if filter_repo and repo_name != filter_repo:
                continue

            # Group by error code
            by_code: dict[str, int] = defaultdict(int)
            for error in errors:
                if error.error_code:
                    by_code[error.error_code] += 1

            for _code, _count in sorted(by_code.items(), key=lambda x: x[1], reverse=True)[:5]:
                pass

    def _print_by_layer(self, analysis: dict[str, Any], filter_layer: str | None = None) -> None:
        """Print errors grouped by architectural layer."""
        layers = analysis["detailed_errors"]["by_layer"]

        for layer_name, errors in layers.items():
            if filter_layer and layer_name != filter_layer:
                continue

            # Show top error codes
            by_code: dict[str, int] = defaultdict(int)
            for error in errors:
                if error.error_code:
                    by_code[error.error_code] += 1

            for _code, _count in sorted(by_code.items(), key=lambda x: x[1], reverse=True)[:3]:
                pass

    def _print_by_severity(
        self, analysis: dict[str, Any], filter_severity: str | None = None
    ) -> None:
        """Print errors grouped by severity."""
        severities = analysis["detailed_errors"]["by_severity"]

        severity_order = ["critical", "high", "medium", "low", "info"]

        for severity in severity_order:
            if severity not in severities:
                continue

            if filter_severity and severity != filter_severity:
                continue

            errors = severities[severity]
            {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
                "info": "🔵",
            }.get(severity, "⚪")

            # Show top error codes
            by_code: dict[str, int] = defaultdict(int)
            for error in errors:
                if error.error_code:
                    by_code[error.error_code] += 1

            for code, _count in sorted(by_code.items(), key=lambda x: x[1], reverse=True)[:3]:
                intel = self.error_intelligence.get(code, {})
                intel.get("category", "unknown")

    def _print_cross_repo(self, analysis: dict[str, Any]) -> None:
        """Print cross-repository errors with upstream/downstream analysis."""
        cross_errors = analysis["detailed_errors"]["cross_repo"]

        if not cross_errors:
            return

        for _i, error in enumerate(cross_errors[:10], 1):  # Top 10
            if error.upstream_impact:
                pass

            if error.downstream_impact:
                pass

    def _print_detailed_errors(
        self,
        analysis: dict[str, Any],
        filter_repo: str | None,
        filter_layer: str | None,
        filter_severity: str | None,
    ) -> None:
        """Print detailed error view with hints and suggestions."""
        # Get all errors
        all_errors: list[Any] = []
        for errors in analysis["detailed_errors"]["by_repository"].values():
            all_errors.extend(errors)

        # Apply filters
        filtered = all_errors
        if filter_repo:
            filtered = [e for e in filtered if e.repository == filter_repo]
        if filter_layer:
            filtered = [e for e in filtered if e.layer.value == filter_layer]
        if filter_severity:
            filtered = [e for e in filtered if e.severity.value == filter_severity]

        # Group by error code
        by_code = defaultdict(list)
        for error in filtered:
            if error.error_code:
                by_code[error.error_code].append(error)

        # Show top error codes with full intelligence
        for code in sorted(by_code.keys(), key=lambda k: len(by_code[k]), reverse=True)[:5]:
            errors = by_code[code]
            intel = self.error_intelligence.get(code, {})

            if intel.get("hints"):
                for _hint in intel["hints"]:
                    pass

            if intel.get("suggestions"):
                for _suggestion in intel["suggestions"]:
                    pass

            if intel.get("upstream_impact"):
                for _impact in intel["upstream_impact"]:
                    pass

            if intel.get("downstream_impact"):
                for _impact in intel["downstream_impact"]:
                    pass

            # Show sample occurrences
            for _error in errors[:3]:
                pass


def main() -> None:
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="🔍 Multi-Repository Error Explorer - Advanced error analysis",
    )
    parser.add_argument(
        "--view",
        choices=[
            "summary",
            "by_repo",
            "by_layer",
            "by_severity",
            "cross_repo",
            "detailed",
            "all",
        ],
        default="summary",
        help="View mode for error analysis",
    )
    parser.add_argument(
        "--repo",
        choices=["NuSyQ-Hub", "SimulatedVerse", "NuSyQ"],
        help="Filter by repository",
    )
    parser.add_argument(
        "--layer",
        choices=[layer.value for layer in ArchitecturalLayer],
        help="Filter by architectural layer",
    )
    parser.add_argument(
        "--severity",
        choices=[sev.value for sev in ErrorSeverity],
        help="Filter by severity level",
    )

    args = parser.parse_args()

    explorer = MultiRepoErrorExplorer()
    analysis = explorer.analyze_workspace_errors()

    explorer.print_analysis(
        analysis,
        view=args.view,
        filter_repo=args.repo,
        filter_layer=args.layer,
        filter_severity=args.severity,
    )

    # Save detailed analysis
    report_file = (
        Path("logs") / f"multi_repo_error_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    report_file.parent.mkdir(exist_ok=True)

    # Convert ErrorContext objects to dicts for JSON serialization
    serializable_analysis = {
        "timestamp": analysis["timestamp"],
        "total_errors": analysis["total_errors"],
        "by_repository": analysis["by_repository"],
        "by_layer": analysis["by_layer"],
        "by_severity": analysis["by_severity"],
        "by_error_code": analysis["by_error_code"],
        "cross_repo_count": analysis["cross_repo_count"],
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(serializable_analysis, f, indent=2)


if __name__ == "__main__":
    main()

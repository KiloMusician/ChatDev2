"""Nogic Agent Diagnostics - AI-powered debugging and analysis.

Integrates Nogic with error detection for intelligent diagnosis:
- Root cause analysis
- Automatic code suggestions
- Smart test recommendations
- Architecture-aware fixes
"""

import logging
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

try:
    from src.integrations.nogic_agent_intelligence import (
        AgentCodebaseIntelligence, CodeContext)
except ImportError:
    from nogic_agent_intelligence import AgentCodebaseIntelligence, CodeContext

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categorized error types."""

    IMPORT_ERROR = "import_error"
    UNDEFINED_SYMBOL = "undefined_symbol"
    TYPE_ERROR = "type_error"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    ATTRIBUTE_ERROR = "attribute_error"
    NAME_ERROR = "name_error"
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    TEST_FAILURE = "test_failure"
    UNKNOWN = "unknown"


@dataclass
class DiagnosticResult:
    """Complete diagnostic information."""

    error_message: str
    file_path: str
    line_number: int | None
    category: ErrorCategory
    root_cause: str
    affected_symbols: list[str]
    suggested_fixes: list[str]
    related_files: list[str]
    test_recommendations: list[str]
    severity: str  # Low, Medium, High, Critical
    confidence: float  # 0.0-1.0


@dataclass
class NogicOperationalState:
    """Operational state snapshot for agent-first Nogic usage."""

    workspace_root: str
    db_path: str | None
    db_accessible: bool
    schema_version: str | None
    counts: dict[str, int]
    board_summary: list[dict[str, Any]]
    language_coverage: dict[str, Any]
    has_user_config: bool
    has_workspace_config: bool
    latest_cli_log: str | None
    cli_log_findings: list[str]
    ready_for_agent: bool
    recommendations: list[str]
    command_uris: dict[str, str]


class AgentDiagnostics:
    """Intelligent diagnostic engine using Nogic graph data.

    Analyzes errors in context of codebase architecture.
    """

    # Error pattern matchers
    ERROR_PATTERNS: ClassVar[dict] = {
        ErrorCategory.IMPORT_ERROR: [
            r"ModuleNotFoundError|ImportError|cannot import",
            r"No module named",
        ],
        ErrorCategory.UNDEFINED_SYMBOL: [
            r"NameError.*not defined",
            r"undefined.*reference",
            r"is not defined",
        ],
        ErrorCategory.CIRCULAR_DEPENDENCY: [
            r"circular import",
            r"cannot import.*circular",
            r"cyclic import",
        ],
        ErrorCategory.ATTRIBUTE_ERROR: [
            r"AttributeError.*has no attribute",
            r"has no attribute",
        ],
        ErrorCategory.TYPE_ERROR: [
            r"TypeError",
            r"expected.*got",
            r"type mismatch",
        ],
        ErrorCategory.SYNTAX_ERROR: [
            r"SyntaxError",
            r"invalid syntax",
        ],
    }

    def __init__(self, workspace_root: str | None = None):
        """Initialize diagnostics engine.

        Args:
            workspace_root: Root of workspace to analyze
        """
        self.intelligence = AgentCodebaseIntelligence(workspace_root)
        logger.info("✅ Agent Diagnostics initialized")

    @staticmethod
    def _to_wsl_path_if_needed(raw_path: str) -> Path:
        """Convert Windows-style path to WSL path when required."""
        win_match = re.match(r"^([A-Za-z]):[\\/](.*)$", raw_path)
        if win_match:
            drive = win_match.group(1).lower()
            rest = win_match.group(2).replace("\\", "/")
            return Path(f"/mnt/{drive}/{rest}")
        return Path(raw_path)

    def _user_nogic_config_candidates(self) -> list[Path]:
        candidates: list[Path] = [Path.home() / ".nogic" / "config.json"]
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            candidates.append(Path(userprofile) / ".nogic" / "config.json")
            candidates.append(self._to_wsl_path_if_needed(userprofile) / ".nogic" / "config.json")

        deduped: list[Path] = []
        seen: set[str] = set()
        for path in candidates:
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(path)
        return deduped

    def _latest_nogic_cli_log(self) -> Path | None:
        roots: list[Path] = [Path.home() / ".config" / "Code" / "logs"]
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            roots.append(
                self._to_wsl_path_if_needed(userprofile) / "AppData" / "Roaming" / "Code" / "logs"
            )
            roots.append(Path(userprofile) / "AppData" / "Roaming" / "Code" / "logs")

        candidates: list[Path] = []
        for root in roots:
            if not root.exists():
                continue
            candidates.extend(root.glob("**/*Nogic CLI.log"))

        if not candidates:
            return None
        return max(candidates, key=lambda p: p.stat().st_mtime)

    def _analyze_cli_log(self, log_path: Path | None) -> list[str]:
        if not log_path or not log_path.exists():
            return ["Nogic CLI log not found."]

        try:
            lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return ["Failed to read Nogic CLI log."]

        if not lines:
            return ["Nogic CLI log is empty."]

        recent = lines[-200:]
        findings: list[str] = []
        for line in recent:
            if "ENOENT" in line and "config.json" in line:
                findings.append("Nogic user config is missing (~/.nogic/config.json).")
            if "api_key found: false" in line:
                findings.append("Nogic login not completed (api_key not found).")
            if "Error" in line and "ENOENT" not in line:
                findings.append(f"Nogic CLI error signal: {line.strip()}")

        if not findings:
            findings.append("No critical Nogic CLI errors detected in recent log lines.")
        return sorted(set(findings))

    def inspect_nogic_operational_state(self) -> NogicOperationalState:
        """Inspect Nogic operability without opening external VS Code windows.

        Returns:
            NogicOperationalState: Agent-focused readiness and recommendations.
        """
        nog = self.intelligence.nog
        workspace_root = str(self.intelligence.workspace_root)
        db_path = str(nog.db_path) if nog.db_path else None

        counts: dict[str, int] = {}
        schema_version: str | None = None
        board_summary: list[dict[str, Any]] = []
        language_coverage: dict[str, Any] = {}
        db_accessible = False
        try:
            stats = nog.get_statistics()
            if stats:
                db_accessible = True
                schema_version = (
                    str(stats.get("schema_version")) if stats.get("schema_version") else None
                )
                counts = {
                    "total_files": int(stats.get("total_files", 0)),
                    "total_symbols": int(stats.get("total_symbols", 0)),
                    "total_imports": int(stats.get("total_imports", 0)),
                    "total_calls": int(stats.get("total_calls", 0)),
                    "total_boards": int(stats.get("total_boards", 0)),
                }
                board_summary = nog.get_board_summary()
                language_coverage = nog.get_language_coverage()
        except Exception as exc:
            logger.error("Failed to inspect Nogic DB state: %s", exc)

        user_config_candidates = self._user_nogic_config_candidates()
        has_user_config = any(path.exists() for path in user_config_candidates)

        workspace_config = Path(self.intelligence.workspace_root) / ".nogic" / "config.json"
        has_workspace_config = workspace_config.exists()

        latest_log = self._latest_nogic_cli_log()
        cli_log_findings = self._analyze_cli_log(latest_log)

        recommendations: list[str] = []
        if not db_accessible:
            recommendations.append(
                "Nogic DB not accessible; open Nogic visualizer and run workspace index once."
            )
        if counts.get("total_symbols", 0) == 0:
            recommendations.append("Nogic index has zero symbols; verify parser/index workflow.")
        if counts.get("total_imports", 0) == 0:
            recommendations.append(
                "Imports table is empty; verify import extraction for this workspace."
            )
        files_by_language = language_coverage.get("files_by_language", {})
        symbols_by_language = language_coverage.get("symbols_by_language", {})
        if (
            int(files_by_language.get("python", 0)) > 50
            and int(symbols_by_language.get("python", 0)) == 0
        ):
            recommendations.append(
                "Python files are indexed but Python symbols are missing; run Python-symbol backfill or reindex."
            )
        if counts.get("total_boards", 0) > 0 and all(
            int(b.get("node_count", 0)) == 0 for b in board_summary
        ):
            recommendations.append(
                "Existing boards have zero nodes; seed a board from high-value folders/files."
            )
        if not has_user_config:
            recommendations.append(
                "Nogic user config missing; complete login/onboarding in current window."
            )
        if not has_workspace_config:
            recommendations.append(
                "Workspace .nogic/config.json missing; run Nogic project initialization."
            )

        ready_for_agent = db_accessible and counts.get("total_symbols", 0) > 0
        if ready_for_agent and not recommendations:
            recommendations.append("Nogic is agent-ready for local graph-based diagnostics.")

        command_uris = {
            "open_visualizer": nog.get_command_uri("nogic.openVisualizer"),
            "status": nog.get_command_uri("nogic.cliStatus"),
            "onboard": nog.get_command_uri("nogic.cliOnboard"),
            "watch_toggle": nog.get_command_uri("nogic.cliWatchToggle"),
            "reindex": nog.get_command_uri("nogic.cliReindex"),
        }

        return NogicOperationalState(
            workspace_root=workspace_root,
            db_path=db_path,
            db_accessible=db_accessible,
            schema_version=schema_version,
            counts=counts,
            board_summary=board_summary,
            language_coverage=language_coverage,
            has_user_config=has_user_config,
            has_workspace_config=has_workspace_config,
            latest_cli_log=str(latest_log) if latest_log else None,
            cli_log_findings=cli_log_findings,
            ready_for_agent=ready_for_agent,
            recommendations=recommendations,
            command_uris=command_uris,
        )

    def render_nogic_operational_report(self) -> str:
        """Render an agent-readable text report from Nogic operational state."""
        state = self.inspect_nogic_operational_state()
        lines = [
            "Nogic Operational Report",
            f"workspace_root: {state.workspace_root}",
            f"db_path: {state.db_path}",
            f"db_accessible: {state.db_accessible}",
            f"schema_version: {state.schema_version}",
            f"ready_for_agent: {state.ready_for_agent}",
            "counts:",
        ]
        for key in sorted(state.counts):
            lines.append(f"  - {key}: {state.counts[key]}")

        lines.append("board_summary:")
        if state.board_summary:
            for board in state.board_summary[:10]:
                lines.append(
                    f"  - {board.get('name')} (id={board.get('id')} nodes={board.get('node_count')})"
                )
        else:
            lines.append("  - (none)")

        lines.append("language_coverage:")
        files_by_language = state.language_coverage.get("files_by_language", {})
        symbols_by_language = state.language_coverage.get("symbols_by_language", {})
        lines.append(f"  - files_by_language: {files_by_language}")
        lines.append(f"  - symbols_by_language: {symbols_by_language}")

        lines.append(f"has_user_config: {state.has_user_config}")
        lines.append(f"has_workspace_config: {state.has_workspace_config}")
        lines.append(f"latest_cli_log: {state.latest_cli_log}")
        lines.append("cli_log_findings:")
        for finding in state.cli_log_findings:
            lines.append(f"  - {finding}")
        lines.append("recommendations:")
        for recommendation in state.recommendations:
            lines.append(f"  - {recommendation}")
        lines.append("command_uris:")
        for key, uri in state.command_uris.items():
            lines.append(f"  - {key}: {uri}")
        return "\n".join(lines)

    def apply_safe_nogic_fixes(self) -> dict[str, Any]:
        """Apply safe, local-only fixes to improve Nogic utility for agents.

        This method avoids opening VS Code windows and avoids destructive resets.
        """
        nog = self.intelligence.nog
        result: dict[str, Any] = {}

        result["config_bootstrap"] = nog.bootstrap_nogic_configs(
            create_user_config_template=True,
            force=False,
        )
        result["python_symbols_backfill"] = nog.backfill_python_symbols()
        result["imports_backfill"] = nog.backfill_imports_from_workspace(clear_existing=False)
        result["board_seed"] = nog.seed_board_from_workspace(max_nodes=24)
        result["post_state"] = self.inspect_nogic_operational_state()
        return result

    def analyze_error(
        self,
        error_message: str,
        file_path: str,
        line_number: int | None = None,
        _context_code: str | None = None,
    ) -> DiagnosticResult:
        """Analyze an error using full codebase context.

        Args:
            error_message: The error message
            file_path: File where error occurred
            line_number: Optional line number
            context_code: Optional surrounding code

        Returns:
            DiagnosticResult with analysis and recommendations
        """
        # Categorize error
        category = self._categorize_error(error_message)

        # Get code context
        context = self.intelligence.get_code_context(file_path)

        # Extract key information from error
        extracted_info = self._extract_error_info(error_message, category)

        # Determine root cause
        root_cause = self._find_root_cause(error_message, category, context, extracted_info)

        # Find affected symbols
        affected = self._find_affected_symbols(error_message, category, extracted_info, context)

        # Generate fixes
        fixes = self._generate_fixes(category, root_cause, context, affected, extracted_info)

        # Recommend tests
        tests = self._recommend_tests(category, affected, context)

        # Find related files
        related = self._find_related_files(affected, context)

        # Assess severity
        severity = self._assess_severity(category, len(affected), context)

        # Confidence score
        confidence = self._calculate_confidence(category, root_cause, extracted_info)

        result = DiagnosticResult(
            error_message=error_message,
            file_path=file_path,
            line_number=line_number,
            category=category,
            root_cause=root_cause,
            affected_symbols=affected,
            suggested_fixes=fixes,
            related_files=related,
            test_recommendations=tests,
            severity=severity,
            confidence=confidence,
        )

        # Record analysis
        self.intelligence.record_analysis(
            "error_diagnosis",
            str(error_message[:50]),
            {
                "category": category.value,
                "severity": severity,
                "affected_count": len(affected),
            },
        )

        return result

    def _categorize_error(self, error_message: str) -> ErrorCategory:
        """Categorize error by message."""
        error_lower = error_message.lower()

        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_lower, re.IGNORECASE):
                    return category

        # Try to infer from message content
        if "test" in error_lower and "fail" in error_lower:
            return ErrorCategory.TEST_FAILURE

        return ErrorCategory.UNKNOWN

    def _extract_error_info(self, error_message: str, category: ErrorCategory) -> dict[str, Any]:
        """Extract specific information from error message."""
        info = {}

        if category == ErrorCategory.IMPORT_ERROR:
            # Extract module name
            match = re.search(r"named ['\"](\w+)['\"]", error_message)
            if match:
                info["module_name"] = match.group(1)

        elif category == ErrorCategory.UNDEFINED_SYMBOL:
            # Extract symbol name
            match = re.search(r"['\"]?(\w+)['\"]? is not defined", error_message)
            if match:
                info["symbol_name"] = match.group(1)

        elif category == ErrorCategory.ATTRIBUTE_ERROR:
            # Extract attribute name
            match = re.search(r"has no attribute ['\"](\w+)['\"]", error_message)
            if match:
                info["attribute_name"] = match.group(1)

        # Try to extract line info
        match = re.search(r"line (\d+)", error_message)
        if match:
            info["line_number"] = int(match.group(1))

        return info

    def _find_root_cause(
        self,
        _error_message: str,
        category: ErrorCategory,
        context: CodeContext,
        extracted_info: dict[str, Any],
    ) -> str:
        """Determine likely root cause."""
        if category == ErrorCategory.IMPORT_ERROR:
            module_name = extracted_info.get("module_name", "unknown")
            related = self.intelligence.get_related_symbols(module_name)

            if not related:
                return (
                    f"Module '{module_name}' not found in codebase. Possible reasons:\n"
                    "1. Module not installed\n"
                    "2. Typo in import name\n"
                    "3. Module not indexed by Nogic yet"
                )
            else:
                return f"Import path incorrect. Found similar symbols: {[s.name for s in related]}"

        elif category == ErrorCategory.CIRCULAR_DEPENDENCY:
            deps = context.dependencies
            if deps:
                return f"Circular import detected. Files involved: {', '.join(deps[:3])}"
            return "Circular import detected in module loading chain"

        elif category == ErrorCategory.UNDEFINED_SYMBOL:
            symbol_name = extracted_info.get("symbol_name", "unknown")
            related = self.intelligence.get_related_symbols(symbol_name)

            if related:
                return f"Symbol '{symbol_name}' may be defined in: {[s.file_id for s in related]}"
            return f"Symbol '{symbol_name}' is not defined anywhere in the codebase"

        else:
            return f"Error category: {category.value}\nSee detailed analysis below."

    def _find_affected_symbols(
        self,
        _error_message: str,
        category: ErrorCategory,
        extracted_info: dict[str, Any],
        context: CodeContext,
    ) -> list[str]:
        """Find all symbols affected by this error."""
        affected = []

        if category == ErrorCategory.UNDEFINED_SYMBOL:
            symbol_name = extracted_info.get("symbol_name")
            if symbol_name:
                affected.append(symbol_name)

        elif category == ErrorCategory.IMPORT_ERROR:
            module_name = extracted_info.get("module_name")
            if module_name:
                affected.append(f"import:{module_name}")

        elif category == ErrorCategory.CIRCULAR_DEPENDENCY:
            affected.extend(context.dependencies[:5])

        # Add symbols from the file
        affected.extend([s.name for s in context.symbols[:3]])

        return list(set(affected))

    def _generate_fixes(
        self,
        category: ErrorCategory,
        _root_cause: str,
        _context: CodeContext,
        _affected_symbols: list[str],
        extracted_info: dict[str, Any],
    ) -> list[str]:
        """Generate suggested fixes."""
        fixes = []

        if category == ErrorCategory.IMPORT_ERROR:
            module_name = extracted_info.get("module_name")
            fixes.append(f"Verify module '{module_name}' is installed")
            fixes.append(f"Check import path: 'from ... import {module_name}'")
            fixes.append("Run `pip install <module_name>` if it's a third-party package")

        elif category == ErrorCategory.UNDEFINED_SYMBOL:
            symbol_name = extracted_info.get("symbol_name")
            fixes.append(f"Define '{symbol_name}' in this file")
            fixes.append(f"Import '{symbol_name}' from another module")
            fixes.append("Check spelling of symbol name")

        elif category == ErrorCategory.CIRCULAR_DEPENDENCY:
            fixes.append("Restructure imports to break the cycle")
            fixes.append("Move shared code to a new module")
            fixes.append("Use lazy imports (import inside function)")

        elif category == ErrorCategory.ATTRIBUTE_ERROR:
            attr_name = extracted_info.get("attribute_name")
            fixes.append(f"Verify object has '{attr_name}' attribute")
            fixes.append(f"Check class definition for '{attr_name}'")
            fixes.append("Use hasattr() to safely check for attribute")

        else:
            fixes.append("Check official Python documentation for this error type")
            fixes.append("Review similar code in the codebase")

        return fixes

    def _recommend_tests(
        self, category: ErrorCategory, _affected: list[str], _context: CodeContext
    ) -> list[str]:
        """Recommend tests to verify the fix."""
        tests = []

        if category == ErrorCategory.IMPORT_ERROR:
            tests.append("Test import statement in isolation")
            tests.append("Verify module exports the required symbols")

        elif category == ErrorCategory.UNDEFINED_SYMBOL:
            tests.append("Add unit test for symbol definition")
            tests.append("Test all code paths using this symbol")

        elif category == ErrorCategory.CIRCULAR_DEPENDENCY:
            tests.append("Test module can be imported independently")
            tests.append("verify all circular imports are resolved")

        else:
            tests.append("Run full test suite after fix")
            tests.append("Add regression test for this specific error")

        return tests

    def _find_related_files(self, _affected_symbols: list[str], context: CodeContext) -> list[str]:
        """Find files related to affected symbols."""
        related = set(context.dependencies + context.dependents)
        return list(related)[:5]

    def _assess_severity(
        self, category: ErrorCategory, affected_count: int, _context: CodeContext
    ) -> str:
        """Assess severity of the error."""
        if category in [ErrorCategory.CIRCULAR_DEPENDENCY, ErrorCategory.SYNTAX_ERROR]:
            return "Critical"

        if affected_count > 10:
            return "High"

        if affected_count > 3:
            return "Medium"

        return "Low"

    def _calculate_confidence(
        self,
        category: ErrorCategory,
        root_cause: str,
        extracted_info: dict[str, Any],
    ) -> float:
        """Calculate confidence score (0-1)."""
        confidence = 0.5  # Base confidence

        # Known categories increase confidence
        if category != ErrorCategory.UNKNOWN:
            confidence += 0.2

        # Successfully extracted info
        if extracted_info:
            confidence += 0.2

        # Root cause found
        if "likely" not in root_cause.lower():
            confidence += 0.1

        return min(1.0, confidence)

    def batch_analyze_errors(self, errors: list[tuple[str, str]]) -> list[DiagnosticResult]:
        """Analyze multiple errors efficiently.

        Args:
            errors: List of (error_message, file_path) tuples

        Returns:
            List of DiagnosticResult
        """
        results = []
        for error_msg, file_path in errors:
            result = self.analyze_error(error_msg, file_path)
            results.append(result)

        return results

    def get_diagnostics_summary(self, results: list[DiagnosticResult]) -> dict[str, Any]:
        """Generate summary of diagnostic results.

        Args:
            results: List of diagnostic results

        Returns:
            Summary statistics and insights
        """
        categories = {}
        severities = {}

        for result in results:
            cat = result.category.value
            categories[cat] = categories.get(cat, 0) + 1

            sev = result.severity
            severities[sev] = severities.get(sev, 0) + 1

        return {
            "total_errors": len(results),
            "by_category": categories,
            "by_severity": severities,
            "avg_confidence": sum(r.confidence for r in results) / len(results) if results else 0,
            "critical_count": severities.get("Critical", 0),
        }

    def close(self) -> None:
        """Cleanup resources."""
        self.intelligence.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc, tb):
        """Context manager cleanup."""
        self.close()


# ========== CONVENIENCE FUNCTIONS ==========


def diagnose(error_message: str, file_path: str) -> DiagnosticResult:
    """Quick diagnostic (one-liner).

    Args:
        error_message: Error to diagnose
        file_path: File where error occurred

    Returns:
        Diagnostic result
    """
    with AgentDiagnostics() as diag:
        return diag.analyze_error(error_message, file_path)


def diagnose_batch(errors: list[tuple[str, str]]) -> list[DiagnosticResult]:
    """Batch error diagnosis."""
    with AgentDiagnostics() as diag:
        return diag.batch_analyze_errors(errors)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.info("🔍 Agent Diagnostics Demo\n")

    # Demo error analysis
    test_errors = [
        ("ModuleNotFoundError: No module named 'orchestration'", "src/main.py"),
        ("NameError: name 'undefined_function' is not defined", "src/core/handler.py"),
    ]

    results = diagnose_batch(test_errors)

    for result in results:
        logger.error(f"❌ {result.error_message}")
        logger.info(f"   Category: {result.category.value}")
        logger.info(f"   Severity: {result.severity}")
        logger.info(f"   Root Cause: {result.root_cause}")
        logger.info("   Suggested Fixes:")
        for fix in result.suggested_fixes[:2]:
            logger.info(f"     • {fix}")
        logger.info()

    with AgentDiagnostics() as diagnostics:
        logger.info("📊 Nogic Operational Snapshot")
        logger.info(diagnostics.render_nogic_operational_report())
        if "--apply-safe-fixes" in sys.argv:
            logger.info("\n🛠 Applying safe Nogic fixes...")
            applied = diagnostics.apply_safe_nogic_fixes()
            logger.info(f"Config bootstrap: {applied.get('config_bootstrap')}")
            logger.info(f"Imports backfill: {applied.get('imports_backfill')}")
            logger.info(f"Board seed: {applied.get('board_seed')}")

#!/usr/bin/env python3
"""🎯 Actionable Intelligence Agent - Transforms diagnostics into executable actions.

This agent embeds solutions directly into health assessments, moving beyond
"sophisticated theater" to actual productive work. It analyzes system state,
generates concrete action plans, and can auto-execute safe remediation tasks.

OmniTag: {
    "purpose": "Transform passive diagnostics into active remediation orchestration",
    "dependencies": ["system_health_assessor", "quantum_problem_resolver", "multi_ai_orchestrator"],
    "context": "Action-oriented diagnostic intelligence with auto-remediation",
    "evolution_stage": "v2.0"
}

MegaTag: {
    "type": "ActionableIntelligenceAgent",
    "integration_points": ["diagnostics", "healing", "orchestration", "consciousness_bridge"],
    "related_tags": ["AutoRemediation", "ActionPlanner", "IntelligentDiagnostics"]
}
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ActionableIntelligenceAgent:
    """Intelligent diagnostic agent that provides actionable recommendations.

    and can auto-execute safe remediation tasks.
    """

    def __init__(self, auto_execute: bool = False, confidence_threshold: float = 0.8) -> None:
        """Initialize the actionable intelligence agent.

        Args:
            auto_execute: If True, automatically execute high-confidence actions
            confidence_threshold: Minimum confidence to auto-execute (0.0-1.0)

        """
        self.repo_root = Path.cwd()
        self.auto_execute = auto_execute
        self.confidence_threshold = confidence_threshold
        self.timestamp = datetime.now().isoformat()
        self.action_history: list[dict[str, Any]] = []

    def analyze_and_act(self) -> dict[str, Any]:
        """Run comprehensive analysis and generate actionable intelligence.

        Returns:
            Dictionary containing analysis, actions, and execution results

        """
        # Gather diagnostic data
        diagnostics = self._gather_diagnostics()

        # Generate actionable intelligence
        actions = self._generate_action_plan(diagnostics)

        # Prioritize and filter actions
        prioritized_actions = self._prioritize_actions(actions)

        # Execute high-confidence actions if auto_execute enabled
        execution_results: list[Any] = []
        if self.auto_execute:
            execution_results = self._execute_safe_actions(prioritized_actions)

        # Generate comprehensive report
        report = {
            "timestamp": self.timestamp,
            "diagnostics": diagnostics,
            "total_actions_identified": len(actions),
            "prioritized_actions": prioritized_actions,
            "auto_executed": len(execution_results),
            "execution_results": execution_results,
            "next_manual_steps": self._extract_manual_steps(prioritized_actions),
        }

        self._print_actionable_report(report)
        self._save_action_log(report)

        return report

    def _gather_diagnostics(self) -> dict[str, Any]:
        """Gather comprehensive diagnostic data from all available sources."""
        return {
            "ruff_errors": self._get_ruff_stats(),
            "test_status": self._get_test_status(),
            "import_health": self._check_import_health(),
            "ollama_status": self._check_ollama_status(),
            "system_health": self._get_system_health_score(),
            "recent_changes": self._get_recent_changes(),
        }

    def _get_ruff_stats(self) -> dict[str, Any]:
        """Get Ruff linting statistics with error categorization."""
        try:
            result = subprocess.run(
                ["ruff", "check", "--statistics"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            stats: dict[str, Any] = {
                "total_errors": 0,
                "categories": {},
                "raw_output": result.stdout,
            }

            # Parse statistics
            for line in result.stdout.splitlines():
                if line.strip() and not line.startswith("warning"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        count = int(parts[0])
                        code = parts[1]
                        stats["categories"][code] = count
                        stats["total_errors"] += count

            return stats
        except Exception as e:
            return {"error": str(e), "total_errors": -1, "categories": {}}

    def _get_test_status(self) -> dict[str, Any]:
        """Get test suite status."""
        try:
            # Quick test discovery
            test_files = list(Path("tests").rglob("test_*.py"))
            return {
                "test_files_found": len(test_files),
                "test_directory_exists": Path("tests").exists(),
                "status": "ready" if test_files else "no_tests",
            }
        except Exception as e:
            return {"error": str(e), "status": "unknown"}

    def _check_import_health(self) -> dict[str, Any]:
        """Check for common import issues."""
        import_issues: list[Any] = []

        # Check for common problematic imports
        for py_file in Path("src").rglob("*.py"):
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Look for relative import issues
                if "from .. import" in content or "from ... import" in content:
                    import_issues.append(
                        {
                            "file": str(py_file),
                            "issue": "complex_relative_imports",
                            "confidence": 0.6,
                        },
                    )
            except (OSError, UnicodeDecodeError, AttributeError):
                logger.debug("Suppressed AttributeError/OSError/UnicodeDecodeError", exc_info=True)

        return {
            "total_issues": len(import_issues),
            "issues": import_issues[:10],  # Limit to top 10
        }

    def _check_ollama_status(self) -> dict[str, Any]:
        """Check if Ollama is running and list models."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                models: list[Any] = []
                for line in result.stdout.splitlines()[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if parts:
                            models.append(parts[0])

                return {
                    "status": "running",
                    "model_count": len(models),
                    "models": models,
                }
            return {"status": "not_running", "model_count": 0}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_system_health_score(self) -> dict[str, Any]:
        """Get overall system health score from recent analysis."""
        try:
            analysis_files = list(Path.cwd().glob("quick_system_analysis_*.json"))
            if analysis_files:
                latest = max(analysis_files, key=lambda f: f.stat().st_mtime)
                with open(latest, encoding="utf-8") as f:
                    data = json.load(f)

                total_files = (
                    len(data.get("working_files", []))
                    + len(data.get("broken_files", []))
                    + len(data.get("launch_pad_files", []))
                    + len(data.get("enhancement_candidates", []))
                )

                working = len(data.get("working_files", []))
                score = (working / max(total_files, 1)) * 100

                return {
                    "score": round(score, 1),
                    "grade": self._score_to_grade(score),
                    "total_files": total_files,
                    "working_files": working,
                }

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            logger.debug("Suppressed FileNotFoundError/KeyError/json", exc_info=True)

        return {"score": 0, "grade": "Unknown", "total_files": 0}

    def _get_recent_changes(self) -> dict[str, Any]:
        """Get information about recent changes (git status)."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                lines = [line for line in result.stdout.splitlines() if line.strip()]
                return {
                    "uncommitted_changes": len(lines),
                    "has_changes": len(lines) > 0,
                }
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            logger.debug("Suppressed OSError/subprocess", exc_info=True)

        return {"uncommitted_changes": 0, "has_changes": False}

    def _generate_action_plan(self, diagnostics: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate concrete action plan based on diagnostics."""
        actions: list[Any] = []

        # Ruff auto-fix opportunities
        ruff_stats = diagnostics.get("ruff_errors", {})
        if ruff_stats.get("total_errors", 0) > 0:
            categories = ruff_stats.get("categories", {})

            # I001 - Auto-fixable import sorting
            if categories.get("I001", 0) > 0:
                actions.append(
                    {
                        "id": "ruff_fix_i001",
                        "title": f"Auto-fix {categories['I001']} unsorted imports",
                        "command": ["ruff", "check", "--select", "I001", "--fix", "."],
                        "impact": f"Eliminates {categories['I001']} import sorting errors",
                        "confidence": 0.95,
                        "risk": "low",
                        "category": "quick_win",
                        "estimated_time": "30 seconds",
                    },
                )

            # B007 - Unused loop variables
            if categories.get("B007", 0) > 0:
                actions.append(
                    {
                        "id": "ruff_fix_b007",
                        "title": f"Auto-fix {categories['B007']} unused loop variables",
                        "command": ["ruff", "check", "--select", "B007", "--fix", "."],
                        "impact": f"Fixes {categories['B007']} unused variable warnings",
                        "confidence": 0.90,
                        "risk": "low",
                        "category": "quick_win",
                        "estimated_time": "30 seconds",
                    },
                )

            # Black formatting
            if ruff_stats.get("total_errors", 0) > 50:
                actions.append(
                    {
                        "id": "black_format",
                        "title": "Auto-format code with Black",
                        "command": ["black", "src/", "tests/"],
                        "impact": "Fixes formatting issues across codebase",
                        "confidence": 0.92,
                        "risk": "low",
                        "category": "quality",
                        "estimated_time": "1 minute",
                    },
                )

        # Ollama integration tests
        ollama = diagnostics.get("ollama_status", {})
        if ollama.get("status") == "running" and ollama.get("model_count", 0) > 0:
            actions.append(
                {
                    "id": "test_ollama_integration",
                    "title": "Test Ollama integration with local models",
                    "command": [
                        sys.executable,
                        "-c",
                        "from src.integration.ollama_integration import OllamaHub; "
                        "hub = OllamaHub(); print(f'Models: {hub.list_models()}')",
                    ],
                    "impact": "Validates Ollama connectivity and model availability",
                    "confidence": 0.85,
                    "risk": "none",
                    "category": "validation",
                    "estimated_time": "10 seconds",
                },
            )

        # Test suite execution
        test_status = diagnostics.get("test_status", {})
        if test_status.get("test_files_found", 0) > 0:
            actions.append(
                {
                    "id": "run_tests",
                    "title": f"Run test suite ({test_status['test_files_found']} test files)",
                    "command": [
                        sys.executable,
                        "-m",
                        "pytest",
                        "tests/",
                        "-v",
                        "--tb=short",
                    ],
                    "impact": "Validates code changes and identifies failures",
                    "confidence": 0.70,
                    "risk": "none",
                    "category": "validation",
                    "estimated_time": "2-5 minutes",
                },
            )

        # Quantum problem resolver for complex issues
        if ruff_stats.get("total_errors", 0) > 100:
            actions.append(
                {
                    "id": "quantum_resolve",
                    "title": "Run Quantum Problem Resolver for complex issues",
                    "command": [
                        sys.executable,
                        "src/healing/quantum_problem_resolver.py",
                    ],
                    "impact": "AI-driven analysis and remediation suggestions",
                    "confidence": 0.65,
                    "risk": "none",
                    "category": "advanced",
                    "estimated_time": "3-5 minutes",
                },
            )

        return actions

    def _prioritize_actions(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Prioritize actions by confidence, impact, and category."""
        # Priority weights
        category_priority = {
            "quick_win": 10,
            "quality": 8,
            "validation": 6,
            "advanced": 4,
        }

        risk_penalty = {
            "none": 0,
            "low": -1,
            "medium": -3,
            "high": -5,
        }

        for action in actions:
            cat_score = category_priority.get(action.get("category", ""), 5)
            risk_score = risk_penalty.get(action.get("risk", "medium"), -2)
            confidence_score = action.get("confidence", 0.5) * 10

            action["priority_score"] = cat_score + risk_score + confidence_score

        # Sort by priority score descending
        return sorted(actions, key=lambda a: a["priority_score"], reverse=True)

    def _execute_safe_actions(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute actions that meet confidence threshold and are low-risk."""
        results: list[Any] = []

        for action in actions:
            # Only auto-execute if confidence >= threshold and risk is low/none
            if action.get("confidence", 0) >= self.confidence_threshold and action.get(
                "risk",
                "high",
            ) in ["none", "low"]:
                result = self._execute_action(action)
                results.append(result)

                # Brief pause between actions
                import time

                time.sleep(1)

        return results

    def _execute_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Execute a single action and capture results."""
        start_time = datetime.now()

        try:
            result = subprocess.run(
                action["command"],
                check=False,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            execution_result = {
                "action_id": action["id"],
                "title": action["title"],
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "duration_seconds": duration,
                "stdout": result.stdout[:1000],  # Limit output size
                "stderr": result.stderr[:1000],
            }

            self.action_history.append(execution_result)
            return execution_result

        except subprocess.TimeoutExpired:
            return {
                "action_id": action["id"],
                "title": action["title"],
                "success": False,
                "error": "Timeout after 5 minutes",
            }
        except Exception as e:
            return {
                "action_id": action["id"],
                "title": action["title"],
                "success": False,
                "error": str(e),
            }

    def _extract_manual_steps(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract actions that require manual intervention."""
        manual: list[Any] = []

        for action in actions:
            if action.get("confidence", 0) < self.confidence_threshold or action.get(
                "risk",
                "low",
            ) not in ["none", "low"]:
                manual.append(
                    {
                        "title": action["title"],
                        "command": " ".join(action["command"]),
                        "impact": action["impact"],
                        "why_manual": self._explain_manual_requirement(action),
                    },
                )

        return manual

    def _explain_manual_requirement(self, action: dict[str, Any]) -> str:
        """Explain why action requires manual intervention."""
        reasons: list[Any] = []

        if action.get("confidence", 1.0) < self.confidence_threshold:
            reasons.append(
                f"Low confidence ({action['confidence']:.0%} < {self.confidence_threshold:.0%})",
            )

        if action.get("risk", "low") not in ["none", "low"]:
            reasons.append(f"Risk level: {action['risk']}")

        return "; ".join(reasons) if reasons else "Manual review recommended"

    def _print_actionable_report(self, report: dict[str, Any]) -> None:
        """Print human-readable actionable intelligence report."""
        diagnostics = report["diagnostics"]

        # Ruff errors
        ruff = diagnostics.get("ruff_errors", {})
        if ruff.get("categories"):
            top_5 = sorted(ruff["categories"].items(), key=lambda x: x[1], reverse=True)[:5]
            for _code, _count in top_5:
                pass

        # Ollama status
        ollama = diagnostics.get("ollama_status", {})
        "✅" if ollama.get("status") == "running" else "❌"
        if ollama.get("models"):
            pass

        # System health
        diagnostics.get("system_health", {})

        # Actions

        if report.get("auto_executed", 0) > 0:
            for result in report.get("execution_results", []):
                "✅" if result["success"] else "❌"
                if not result["success"] and result.get("error"):
                    pass

        # Top priority actions (not executed)
        manual_steps = report.get("next_manual_steps", [])
        if manual_steps:
            for _i, _step in enumerate(manual_steps[:5], 1):
                pass

    def _save_action_log(self, report: dict[str, Any]) -> None:
        """Save action log for historical tracking."""
        log_file = (
            Path("logs")
            / f"actionable_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        log_file.parent.mkdir(exist_ok=True)

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 95:
            return "A+"
        if score >= 90:
            return "A"
        if score >= 85:
            return "B+"
        if score >= 80:
            return "B"
        if score >= 75:
            return "C+"
        if score >= 70:
            return "C"
        if score >= 65:
            return "D+"
        if score >= 60:
            return "D"
        return "F"


def main() -> None:
    """Main entry point with CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Actionable Intelligence Agent - Transform diagnostics into actions",
    )
    parser.add_argument(
        "--auto-execute",
        action="store_true",
        help="Automatically execute high-confidence, low-risk actions",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.8,
        help="Minimum confidence for auto-execution (0.0-1.0, default: 0.8)",
    )

    args = parser.parse_args()

    agent = ActionableIntelligenceAgent(
        auto_execute=args.auto_execute,
        confidence_threshold=args.confidence_threshold,
    )

    report = agent.analyze_and_act()

    # Exit with error code if critical issues found
    if report["diagnostics"]["ruff_errors"].get("total_errors", 0) > 500:
        sys.exit(1)


if __name__ == "__main__":
    main()

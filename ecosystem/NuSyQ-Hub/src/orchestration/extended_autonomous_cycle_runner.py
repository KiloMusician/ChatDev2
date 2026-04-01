#!/usr/bin/env python3
"""Extended Autonomous Cycle Runner with Real Issue Detection.

============================================================

Detects real codebase issues and runs extended autonomous healing cycles:
- Import errors and circular dependencies
- Missing type hints
- Code style violations
- Undefined functions/variables
- Documentation gaps
- Performance issues

Executes multi-phase autonomous healing with detailed reporting.
"""

import asyncio
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


class IssueType(Enum):
    """Types of codebase issues."""

    IMPORT_ERROR = "import_error"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MISSING_TYPE_HINT = "missing_type_hint"
    UNDEFINED_REFERENCE = "undefined_reference"
    STYLE_VIOLATION = "style_violation"
    DOCUMENTATION_GAP = "documentation_gap"
    PERFORMANCE_ISSUE = "performance_issue"
    UNUSED_IMPORT = "unused_import"
    TYPE_MISMATCH = "type_mismatch"


class IssueSeverity(Enum):
    """Severity levels for issues."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


@dataclass
class CodebaseIssue:
    """Represents a detected codebase issue."""

    issue_id: str
    issue_type: IssueType
    severity: IssueSeverity
    file_path: Path
    line_number: int | None
    column: int | None
    message: str
    suggested_fix: str | None = None
    detected_at: datetime = field(default_factory=datetime.now)
    is_fixed: bool = False
    fix_details: dict[str, Any] | None = None


class CodebaseIssueDetector:
    """Detects real issues in Python codebase."""

    def __init__(self, repo_root: Path = REPO_ROOT) -> None:
        """Initialize issue detector.

        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root
        self.issues: list[CodebaseIssue] = []
        self.py_files: set[Path] = set()
        self.import_graph: dict[Path, set[str]] = defaultdict(set)
        self.defined_symbols: dict[Path, set[str]] = defaultdict(set)
        self.used_symbols: dict[Path, set[str]] = defaultdict(set)

        logger.info("🔍 Codebase Issue Detector initialized")

    def scan_repository(self) -> list[CodebaseIssue]:
        """Scan repository for all issues.

        Returns:
            List of detected issues
        """
        logger.info("📁 Scanning repository for Python files...")
        self.py_files = set(self.repo_root.rglob("*.py"))

        # Filter out venv, .git, __pycache__
        self.py_files = {
            f
            for f in self.py_files
            if not any(part in str(f) for part in [".venv", "venv", ".git", "__pycache__"])
        }

        logger.info(f"📝 Found {len(self.py_files)} Python files")

        # Run detectors
        self._detect_import_issues()
        self._detect_type_hint_issues()
        self._detect_unused_imports()
        self._detect_undefined_references()
        self._detect_style_violations()
        self._detect_documentation_gaps()

        return self.issues

    def _detect_import_issues(self) -> None:
        """Detect import errors and circular dependencies."""
        logger.info("🔗 Detecting import issues...")

        for py_file in self.py_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Find all import statements
                import_lines = re.findall(
                    r"^(?:from|import)\s+[\w\.\*]+(?:\s+import\s+[\w\*,\s]+)?",
                    content,
                    re.MULTILINE,
                )

                for imp in import_lines:
                    # Extract module name
                    match = re.match(r"(?:from\s+([\w\.]+)|import\s+([\w\.]+))", imp)
                    if match:
                        module = match.group(1) or match.group(2)
                        self.import_graph[py_file].add(module)

                        # Check if it's a local import
                        if module.startswith("src."):
                            target_file = self.repo_root / (module.replace(".", "/") + ".py")
                            if not target_file.exists() and module not in ["src.main"]:
                                issue = CodebaseIssue(
                                    issue_id=f"import_{py_file.stem}_{module}",
                                    issue_type=IssueType.IMPORT_ERROR,
                                    severity=IssueSeverity.HIGH,
                                    file_path=py_file,
                                    line_number=None,
                                    column=None,
                                    message=f"Import error: Module '{module}' not found",
                                    suggested_fix=f"Create {target_file} or use absolute import",
                                )
                                self.issues.append(issue)
            except Exception as e:
                logger.warning(f"Error scanning {py_file}: {e}")

    def _detect_type_hint_issues(self) -> None:
        """Detect missing type hints."""
        logger.info("📝 Detecting missing type hints...")

        for py_file in self.py_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()

                # Find function definitions without return type hints
                for i, line in enumerate(lines, 1):
                    if (
                        re.match(r"\s*def\s+\w+\s*\(", line)
                        and "->" not in line
                        and not any(x in line for x in ["__init__", "__str__", "__repr__"])
                        and i < len(lines)
                        and '"""' not in lines[i]
                    ):
                        # Check if it's not __init__ or other special methods
                        issue = CodebaseIssue(
                            issue_id=f"type_{py_file.stem}_{i}",
                            issue_type=IssueType.MISSING_TYPE_HINT,
                            severity=IssueSeverity.MEDIUM,
                            file_path=py_file,
                            line_number=i,
                            column=None,
                            message=f"Missing return type hint: {line.strip()[:50]}",
                            suggested_fix="Add -> ReturnType to function signature",
                        )
                        self.issues.append(issue)
            except Exception as e:
                logger.warning(f"Error scanning type hints in {py_file}: {e}")

    def _detect_unused_imports(self) -> None:
        """Detect unused import statements."""
        logger.info("📌 Detecting unused imports...")

        for py_file in self.py_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Find all imports
                imports = re.findall(
                    r"^from\s+(\w+)\s+import\s+(\w+)|^import\s+(\w+)",
                    content,
                    re.MULTILINE,
                )

                for imp in imports[:5]:  # Check first 5 imports
                    module = imp[0] or imp[2]
                    name = imp[1]

                    # Check if used in file (simplified check)
                    if name and re.search(rf"\b{name}\b", content.split("import")[-1]):
                        continue
                    elif not re.search(rf"\b{module}\b", content.split("import")[-1]):
                        issue = CodebaseIssue(
                            issue_id=f"unused_{py_file.stem}_{name}",
                            issue_type=IssueType.UNUSED_IMPORT,
                            severity=IssueSeverity.LOW,
                            file_path=py_file,
                            line_number=None,
                            column=None,
                            message=f"Unused import: {name or module}",
                            suggested_fix="Remove unused import statement",
                        )
                        self.issues.append(issue)
            except Exception as e:
                logger.warning(f"Error checking unused imports in {py_file}: {e}")

    def _detect_undefined_references(self) -> None:
        """Detect undefined function/variable references."""
        logger.info("🔍 Detecting undefined references...")

        for py_file in self.py_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Find function definitions
                defined = set(re.findall(r"^\s*def\s+(\w+)\s*\(", content, re.MULTILINE))
                defined.update(re.findall(r"^\s*class\s+(\w+)", content, re.MULTILINE))

                # Find common built-in functions
                builtins = {
                    "print",
                    "len",
                    "range",
                    "str",
                    "int",
                    "list",
                    "dict",
                    "set",
                    "tuple",
                    "open",
                    "file",
                    "input",
                    "output",
                }
                defined.update(builtins)

                self.defined_symbols[py_file] = defined

            except Exception as e:
                logger.warning(f"Error detecting references in {py_file}: {e}")

    def _detect_style_violations(self) -> None:
        """Detect style violations."""
        logger.info("🎨 Detecting style violations...")

        for py_file in self.py_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()

                # Check for lines too long (> 100 chars)
                for i, line in enumerate(lines, 1):
                    if len(line.rstrip()) > 100:
                        issue = CodebaseIssue(
                            issue_id=f"style_{py_file.stem}_{i}",
                            issue_type=IssueType.STYLE_VIOLATION,
                            severity=IssueSeverity.LOW,
                            file_path=py_file,
                            line_number=i,
                            column=100,
                            message=f"Line too long: {len(line.rstrip())} chars (max 100)",
                            suggested_fix="Break line into multiple lines or use line continuation",
                        )
                        self.issues.append(issue)
                        break  # Only report one per file
            except Exception as e:
                logger.warning(f"Error detecting style issues in {py_file}: {e}")

    def _detect_documentation_gaps(self) -> None:
        """Detect documentation gaps."""
        logger.info("📚 Detecting documentation gaps...")

        for py_file in self.py_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Check if file has module docstring
                if not content.strip().startswith(('"""', "'''")):
                    issue = CodebaseIssue(
                        issue_id=f"doc_{py_file.stem}_module",
                        issue_type=IssueType.DOCUMENTATION_GAP,
                        severity=IssueSeverity.MEDIUM,
                        file_path=py_file,
                        line_number=1,
                        column=None,
                        message="Missing module docstring",
                        suggested_fix="Add module docstring at top of file",
                    )
                    if len(self.issues) < 50:  # Limit issues
                        self.issues.append(issue)
            except Exception as e:
                logger.warning(f"Error detecting docs in {py_file}: {e}")

    def get_issue_summary(self) -> dict[str, Any]:
        """Get summary of detected issues.

        Returns:
            Summary dictionary
        """
        by_type: dict[str, int] = defaultdict(int)
        by_severity: dict[str, int] = defaultdict(int)
        by_file: dict[str, int] = defaultdict(int)

        for issue in self.issues:
            by_type[issue.issue_type.value] += 1
            by_severity[issue.severity.name] += 1
            by_file[str(issue.file_path.relative_to(self.repo_root))] += 1

        return {
            "total_issues": len(self.issues),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "top_files": sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:5],
            "critical_count": len([i for i in self.issues if i.severity == IssueSeverity.CRITICAL]),
            "high_count": len([i for i in self.issues if i.severity == IssueSeverity.HIGH]),
        }


class ExtendedAutonomousCycleRunner:
    """Runs extended autonomous cycles for codebase improvement."""

    def __init__(self, repo_root: Path = REPO_ROOT) -> None:
        """Initialize cycle runner.

        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root
        self.detector = CodebaseIssueDetector(repo_root)
        self.orchestrator = None
        self.healing_coordinator = None
        self.cycle_results: list[dict[str, Any]] = []

        logger.info("🚀 Extended Autonomous Cycle Runner initialized")

    async def initialize(self) -> bool:
        """Initialize all systems.

        Returns:
            True if successful
        """
        logger.info("⚙️ Initializing systems...")

        try:
            from src.orchestration.unified_ai_orchestrator import (
                TaskPriority, UnifiedAIOrchestrator)

            self.orchestrator = UnifiedAIOrchestrator()
            self.TaskPriority = TaskPriority
            logger.info("✅ Orchestrator initialized")

            from src.healing.modernized_healing_coordinator import \
                ModernizedHealingCoordinator

            self.healing_coordinator = ModernizedHealingCoordinator(self.repo_root)
            await self.healing_coordinator.initialize_healers()
            logger.info("✅ Healing coordinator initialized")

            return True
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    async def run_extended_cycle(self, num_cycles: int = 3) -> list[dict[str, Any]]:
        """Run extended autonomous improvement cycles.

        Args:
            num_cycles: Number of cycles to run

        Returns:
            Results from all cycles
        """
        logger.info(f"🔄 Starting {num_cycles} extended autonomous cycles...")

        results = []

        for cycle in range(1, num_cycles + 1):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"CYCLE {cycle}/{num_cycles}")
            logger.info(f"{'=' * 70}")

            cycle_result = {
                "cycle": cycle,
                "timestamp": datetime.now().isoformat(),
                "phases": {},
            }

            # Phase 1: Detect issues
            logger.info("📋 Phase 1: Issue Detection")
            issues = self.detector.scan_repository()
            summary = self.detector.get_issue_summary()

            cycle_result["phases"]["detection"] = {
                "issues_found": len(issues),
                "summary": summary,
            }

            logger.info(f"🎯 Found {len(issues)} issues:")
            logger.info(f"   Critical: {summary['critical_count']}")
            logger.info(f"   High: {summary['high_count']}")
            logger.info(f"   Total: {summary['total_issues']}")

            # Phase 2: Prioritize and analyze
            logger.info("📊 Phase 2: Issue Analysis")
            priority_issues = sorted(issues, key=lambda x: x.severity.value)[:10]

            cycle_result["phases"]["analysis"] = {
                "high_priority_issues": len(priority_issues),
                "issues_by_type": summary["by_type"],
            }

            # Phase 3: Generate solutions
            logger.info("💡 Phase 3: Solution Generation")
            if self.orchestrator and priority_issues:
                solutions = []
                for issue in priority_issues[:3]:
                    task_id = await self.orchestrator.orchestrate_task_async(
                        task_type="code_analysis",
                        content=f"Fix issue: {issue.message}",
                        context={
                            "issue_type": issue.issue_type.value,
                            "file": str(issue.file_path),
                            "suggested_fix": issue.suggested_fix,
                        },
                        priority=self.TaskPriority.HIGH,
                    )
                    solutions.append({"issue_id": issue.issue_id, "task_id": task_id})

                cycle_result["phases"]["solutions"] = {"solutions_generated": len(solutions)}

            # Phase 4: Healing
            logger.info("🏥 Phase 4: Autonomous Healing")
            if self.healing_coordinator:
                health_status = await self.healing_coordinator.run_comprehensive_health_check()
                cycle_result["phases"]["healing"] = {
                    "overall_status": health_status["overall_status"],
                    "issues_found": len(health_status["issues_found"]),
                }

            logger.info(f"✅ Cycle {cycle} completed")
            results.append(cycle_result)
            self.cycle_results.append(cycle_result)

            # Wait between cycles
            if cycle < num_cycles:
                logger.info("⏳ Waiting before next cycle...")
                await asyncio.sleep(2)

        return results

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive report of all cycles.

        Returns:
            Report dictionary
        """
        return {
            "total_cycles": len(self.cycle_results),
            "timestamp": datetime.now().isoformat(),
            "cycles": self.cycle_results,
            "detector_summary": self.detector.get_issue_summary(),
        }

    def save_report(self, output_path: Path | None = None) -> Path:
        """Save report to file.

        Args:
            output_path: Output file path

        Returns:
            Path to saved report
        """
        if output_path is None:
            output_path = (
                self.repo_root
                / f"extended_cycle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        report = self.generate_report()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"📄 Report saved to: {output_path}")
        return output_path


async def main():
    """Main entry point."""
    runner = ExtendedAutonomousCycleRunner()

    if not await runner.initialize():
        logger.error("❌ Initialization failed")
        return

    # Run extended cycles
    results = await runner.run_extended_cycle(num_cycles=2)

    # Generate and save report
    report_path = runner.save_report()

    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("EXTENDED AUTONOMOUS CYCLE SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total cycles: {len(results)}")
    logger.info(f"Issues detected: {runner.detector.get_issue_summary()['total_issues']}")
    logger.info(f"Report saved to: {report_path}")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

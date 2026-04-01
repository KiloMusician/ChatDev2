#!/usr/bin/env python3
"""Culture Ship Strategic Advisor - Orchestrates Strategic Ecosystem Improvement.

This module bridges my (Copilot) analysis capabilities with Culture Ship's
real action capabilities. It coordinates:

1. Problem identification (my analysis)
2. Strategic decision-making (collaborative)
3. Real implementation (Culture Ship Real Action)
4. Verification (post-fix validation)
5. Learning (updating decision rules)

OmniTag: {
    "purpose": "Strategic ecosystem improvement orchestration",
    "dependencies": ["culture_ship_real_action", "multi_ai_orchestrator", "quantum_resolver"],
    "context": "Strategic advisor for ecosystem optimization",
    "evolution_stage": "v1.0"
}

MegaTag: CULTURE_SHIP⨳STRATEGIC_ADVISOR⦾ECOSYSTEM_OPTIMIZATION→∞
"""

import inspect
import json
import logging
import os
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)

# Try to import Culture Ship Real Action
try:
    from src.culture_ship_real_action import RealActionCultureShip

    CULTURE_SHIP_AVAILABLE = True
except ImportError:
    CULTURE_SHIP_AVAILABLE = False
    RealActionCultureShip = None  # type: ignore

# Try to import orchestration systems
try:
    from src.orchestration.unified_ai_orchestrator import MultiAIOrchestrator

    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    MultiAIOrchestrator = None  # type: ignore

try:
    from src.healing.quantum_problem_resolver import QuantumProblemResolver

    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False
    QuantumProblemResolver = None  # type: ignore

try:
    from src.orchestration.gitnexus import GitNexus

    GITNEXUS_AVAILABLE = True
except ImportError:
    GITNEXUS_AVAILABLE = False
    GitNexus = None  # type: ignore


@dataclass
class StrategicIssue:
    """Represents a strategic issue needing improvement."""

    category: str  # "correctness", "efficiency", "quality", "architecture"
    severity: str  # "critical", "high", "medium", "low"
    description: str
    affected_files: list[str]
    suggested_fixes: list[str] | None = None
    dependencies: list[str] | None = None


@dataclass
class StrategicDecision:
    """Represents a strategic decision made."""

    issue: StrategicIssue
    decision: str
    rationale: str
    action_plan: list[str]
    priority: int  # 1-10, where 10 is highest
    estimated_impact: str  # "low", "medium", "high", "transformative"


class CultureShipStrategicAdvisor:
    """Coordinates strategic ecosystem improvements using Culture Ship."""

    def __init__(self) -> None:
        """Initialize the strategic advisor."""
        self.logger = logging.getLogger("CultureShipStrategicAdvisor")

        # Initialize systems
        self.culture_ship: Any | None = None
        self.orchestrator: Any | None = None
        self.quantum_resolver: Any | None = None
        self.gitnexus: Any | None = None

        self.issues_identified: list[StrategicIssue] = []
        self.decisions_made: list[StrategicDecision] = []
        self.improvements_completed: list[dict[str, Any]] = []

        self._initialize_systems()

    def _initialize_systems(self) -> None:
        """Initialize connected systems."""
        if CULTURE_SHIP_AVAILABLE:
            try:
                self.culture_ship = RealActionCultureShip()
                self.logger.info("✅ Culture Ship Real Action initialized")
            except (OSError, RuntimeError, ValueError, TypeError) as e:
                self.logger.warning(f"⚠️  Culture Ship initialization failed: {e}")

        if ORCHESTRATOR_AVAILABLE:
            try:
                self.orchestrator = MultiAIOrchestrator()
                self.logger.info("✅ MultiAIOrchestrator connected")
            except (OSError, RuntimeError, ValueError, TypeError) as e:
                self.logger.warning(f"⚠️  Orchestrator initialization failed: {e}")

        if QUANTUM_AVAILABLE:
            try:
                self.quantum_resolver = QuantumProblemResolver()
                self.logger.info("✅ QuantumProblemResolver connected")
            except (OSError, RuntimeError, ValueError, TypeError) as e:
                self.logger.warning(f"⚠️  Quantum Resolver initialization failed: {e}")

        if GITNEXUS_AVAILABLE:
            try:
                self.gitnexus = GitNexus()
                self.logger.info("✅ GitNexus connected")
            except (OSError, RuntimeError, ValueError, TypeError) as e:
                self.logger.warning(f"⚠️  GitNexus initialization failed: {e}")

    def identify_strategic_issues(self) -> list[StrategicIssue]:
        """Identify strategic issues in the ecosystem.

        This is where Copilot's analysis integrates with Culture Ship's
        understanding of what's fixable.

        Returns:
            List of strategic issues identified
        """
        self.logger.info("🔍 Identifying strategic ecosystem issues...")

        issues = []

        # Issue 1: Type safety and linting
        issues.append(
            StrategicIssue(
                category="correctness",
                severity="high",
                description="Type annotation inconsistencies and linting violations prevent reliable code analysis",
                affected_files=[
                    "src/utils/async_task_wrapper.py",
                    "src/orchestration/healing_cycle_scheduler.py",
                    "src/orchestration/unified_autonomous_healing_pipeline.py",
                ],
                suggested_fixes=[
                    "Fix timeout parameter type mismatches in async_task_wrapper.py",
                    "Remove unused variables and import statements",
                    "Fix exception handling to be more specific",
                    "Reduce cognitive complexity in healing systems",
                ],
                dependencies=["ruff", "mypy"],
            )
        )

        # Issue 2: Async/await patterns
        issues.append(
            StrategicIssue(
                category="efficiency",
                severity="medium",
                description="Async functions that don't use async features cause overhead",
                affected_files=[
                    "src/orchestration/healing_cycle_scheduler.py",
                    "src/orchestration/unified_autonomous_healing_pipeline.py",
                ],
                suggested_fixes=[
                    "Remove async keyword from functions that don't await",
                    "Use asynchronous file operations in async functions",
                    "Fix global state management patterns",
                ],
                dependencies=["asyncio"],
            )
        )

        # Issue 3: Culture Ship integration gap
        if not self._culture_ship_integration_ready():
            issues.append(
                StrategicIssue(
                    category="architecture",
                    severity="critical",
                    description="Culture Ship Real Action system is implemented but not integrated into orchestrator",
                    affected_files=[
                        "scripts/start_nusyq.py",
                        "src/orchestration/unified_ai_orchestrator.py",
                        "src/main.py",
                    ],
                    suggested_fixes=[
                        "Wire Culture Ship into main orchestrator",
                        "Add a primary culture_ship entrypoint",
                        "Enable automated fixes in ecosystem status",
                        "Create feedback loop for learned patterns",
                    ],
                    dependencies=["src/culture_ship_real_action.py"],
                )
            )

        # Issue 4: Test suite health
        issues.append(
            StrategicIssue(
                category="quality",
                severity="medium",
                description="Some test files have unused variables and import issues",
                affected_files=[
                    "tests/integration/test_dashboard_healing_integration.py",
                    "SimulatedVerse/tsconfig.json",
                ],
                suggested_fixes=[
                    "Remove unused scheduler variable in test_dashboard_healing_integration.py",
                    "Update TypeScript deprecation flag to 6.0",
                ],
                dependencies=["pytest", "typescript"],
            )
        )

        self.issues_identified = issues
        return issues

    def _culture_ship_integration_ready(self) -> bool:
        """Check whether Culture Ship is wired into the main runtime surfaces."""
        repo_root = Path(__file__).resolve().parents[2]
        required_markers = {
            repo_root
            / "src"
            / "main.py": [
                '"culture_ship": self._culture_ship_mode',
                "--mode=culture_ship",
            ],
            repo_root
            / "src"
            / "orchestration"
            / "unified_ai_orchestrator.py": [
                "def ensure_culture_ship_system_registered",
                '"culture_ship": AISystemType.CULTURE_SHIP',
                "if system.system_type == AISystemType.CULTURE_SHIP",
            ],
            repo_root
            / "scripts"
            / "start_nusyq.py": [
                '"culture_ship"',
                '"culture_ship_cycle"',
            ],
        }

        try:
            for path, markers in required_markers.items():
                if not path.exists():
                    return False
                content = path.read_text(encoding="utf-8")
                if any(marker not in content for marker in markers):
                    return False
        except OSError as exc:
            self.logger.debug("Culture Ship integration readiness check failed: %s", exc)
            return False

        return True

    async def conduct_strategic_analysis(
        self, scope: str = "full", target: str | None = None
    ) -> list[StrategicIssue]:
        """Conduct dynamic strategic analysis of codebase to identify issues.

        This method performs real-time analysis using the orchestrator and other systems,
        unlike identify_strategic_issues() which returns hardcoded issues.

        Args:
            scope: Analysis scope - "full", "module", or "file"
            target: Specific target for module/file scope

        Returns:
            List of dynamically identified strategic issues
        """
        del target
        self.logger.info(f"🔬 Conducting strategic analysis (scope: {scope})...")
        analysis_started = time.monotonic()
        issues = []

        # 1. Scan for TODOs and FIXMEs (technical debt)
        phase_started = time.monotonic()
        tech_debt_issues = self._scan_technical_debt()
        issues.extend(tech_debt_issues)
        self.logger.debug(
            "Strategic analysis phase 'technical_debt' completed in %.2fs",
            time.monotonic() - phase_started,
        )

        # 2. Check integration completeness
        phase_started = time.monotonic()
        integration_issues = self._check_integration_completeness()
        issues.extend(integration_issues)
        self.logger.debug(
            "Strategic analysis phase 'integration' completed in %.2fs",
            time.monotonic() - phase_started,
        )

        # 3. Analyze test coverage
        phase_started = time.monotonic()
        test_issues = self._analyze_test_coverage()
        issues.extend(test_issues)
        self.logger.debug(
            "Strategic analysis phase 'test_coverage' completed in %.2fs",
            time.monotonic() - phase_started,
        )

        # 4. Check token optimization opportunities
        if self.orchestrator:
            phase_started = time.monotonic()
            token_issues = await self._analyze_token_efficiency()
            issues.extend(token_issues)
            self.logger.debug(
                "Strategic analysis phase 'token_efficiency' completed in %.2fs",
                time.monotonic() - phase_started,
            )

        # 5. Run code quality analysis via Ollama (if available)
        if self.orchestrator and scope == "full":
            try:
                ask_ollama = cast(
                    Callable[..., Any] | None,
                    getattr(self.orchestrator, "ask_ollama", None),
                )
                if callable(ask_ollama):
                    maybe_analysis = ask_ollama(  # pylint: disable=not-callable
                        prompt=(
                            "Analyze NuSyQ-Hub for: incomplete implementations, "
                            "configuration gaps, deprecated patterns. Return 3 top issues."
                        ),
                        model="qwen2.5-coder:14b",
                        temperature=0.3,
                        optimize=True,
                    )
                    ollama_analysis = (
                        await maybe_analysis
                        if inspect.isawaitable(maybe_analysis)
                        else maybe_analysis
                    )
                    if isinstance(ollama_analysis, dict) and ollama_analysis.get("success"):
                        # Parse ollama response into issues
                        self.logger.info("✅ Ollama analysis complete")
                        # Note: In production, would parse response into StrategicIssue objects
                else:
                    self.logger.debug(
                        "Ollama analysis skipped: orchestrator does not expose ask_ollama()"
                    )
            except Exception as e:
                self.logger.warning(f"Ollama analysis failed: {e}")

        self.logger.info(
            "📊 Analysis complete: %s issues found in %.2fs",
            len(issues),
            time.monotonic() - analysis_started,
        )
        try:
            from src.system.agent_awareness import emit as _emit

            elapsed = round((time.monotonic() - analysis_started) * 1000, 1)
            _emit(
                "culture_ship",
                f"Strategic analysis complete — {len(issues)} issues found in {elapsed}ms (scope={scope})",
                level="INFO",
                source="culture_ship",
            )
            if issues:
                top_issue = issues[0]
                priority = getattr(top_issue, "priority", "?")
                title = getattr(top_issue, "title", str(top_issue))[:60]
                _emit(
                    "culture_ship",
                    f"Top issue [{priority}]: {title}",
                    level="INFO",
                    source="culture_ship",
                )
        except Exception:
            pass
        return issues

    def build_ecosystem_coordination_plan(self) -> dict[str, Any]:
        """Build a bounded, tandem workflow plan across the known repos.

        This is intentionally low-token and deterministic. It consumes live
        GitNexus data when available instead of re-deriving repo state through
        open-ended search.
        """
        repo_roles = {
            "concept": "machine-governance, keeper preflight, pressure scoring, maintenance",
            "dev_mentor": "interactive task plane, MCP/game/API operator workflows",
            "terminaldepths": "Dev-Mentor alias for game/task/operator plane",
            "simulatedverse": "simulation layer, patch-bay runtime, Culture Ship-heavy UX/runtime",
            "nusyq": "RosettaStone normalization, proof gates, durable artifacts",
            "nusyq_hub": "orchestration brain, diagnostics, healing, Nogic, GitNexus",
        }
        token_strategy = {
            "prefer": [
                "Keeper score/advisor/think before heavier work",
                "GitNexus matrix before repo rediscovery",
                "Nogic for topology instead of reconstructing architecture manually",
                "Rosetta artifacts instead of rerunning identical context discovery",
                "local backends (Ollama / LM Studio) before paid or rate-limited paths",
            ],
            "avoid": [
                "broad repo archaeology before checking GitNexus",
                "re-running health discovery when recent structured state already exists",
                "treating Culture Ship as lore-only instead of workflow orchestration",
            ],
        }

        workflows = [
            {
                "name": "full_stack_feature_pass",
                "steps": [
                    "concept: keeper snapshot/score/advisor",
                    "nusyq_hub: gitnexus matrix + nogic topology review",
                    "dev_mentor: operator/game/task surface chooses bounded target",
                    "simulatedverse: validate runtime/UI effects and ChatDev-facing paths",
                    "nusyq: run RosettaStone pipeline to normalize artifacts and gate results",
                    "nusyq_hub: record outcomes and surface follow-on healing/coordination work",
                ],
            },
            {
                "name": "runtime_recovery_pass",
                "steps": [
                    "concept: machine-pressure preflight",
                    "nusyq_hub: inspect gitnexus for repo drift",
                    "simulatedverse: recover missing runtime surfaces",
                    "dev_mentor: verify operator-facing health",
                    "nusyq: persist artifacts or receipts for the repair path",
                ],
            },
        ]

        matrix = None
        if self.gitnexus:
            try:
                matrix = self.gitnexus.get_matrix()
            except Exception as exc:
                self.logger.warning("GitNexus matrix unavailable for Culture Ship plan: %s", exc)

        status = "ready" if matrix else "degraded"
        return {
            "status": status,
            "repo_roles": repo_roles,
            "git_matrix": matrix,
            "token_strategy": token_strategy,
            "tandem_workflows": workflows,
        }

    def _scan_technical_debt(self) -> list[StrategicIssue]:
        """Scan codebase for explicit Python comment debt markers."""
        issues = []
        result: subprocess.CompletedProcess[str] | None = None
        debt_pattern = r"^\s*#.*\b(TODO|FIXME|HACK)\b"
        try:
            # Prefer ripgrep for speed on large repositories.
            result = subprocess.run(
                ["rg", "-n", "--glob", "*.py", debt_pattern, "src"],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
        except FileNotFoundError:
            # Fallback for environments without rg (try grep).
            try:
                result = subprocess.run(
                    [
                        "grep",
                        "-r",
                        "-n",
                        "--include=*.py",
                        "-E",
                        debt_pattern,
                        "src/",
                    ],
                    cwd=Path.cwd(),
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
            except FileNotFoundError:
                # Neither rg nor grep available (e.g., Windows without GNU tools)
                self.logger.debug("Neither rg nor grep available — using Python fallback")
                result = None
        except subprocess.TimeoutExpired as e:
            self.logger.debug("Technical debt scan timed out: %s", e)
            result = None

        # Pure-Python fallback when subprocess scan yields no usable results (Windows native)
        if not (result and result.returncode == 0 and result.stdout):
            import re

            debt_re = re.compile(r"^\s*#.*\b(TODO|FIXME|HACK)\b")
            src_dir = Path(__file__).resolve().parents[1]  # = src/ regardless of cwd
            py_fallback: list[str] = []
            if src_dir.exists():
                for py_file in src_dir.rglob("*.py"):
                    try:
                        for lineno, line in enumerate(
                            py_file.read_text(encoding="utf-8", errors="replace").splitlines(), 1
                        ):
                            if debt_re.search(line):
                                py_fallback.append(f"{py_file}:{lineno}:{line.strip()}")
                    except OSError:
                        pass
            if py_fallback:
                result = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="\n".join(py_fallback)
                )

        if result and result.returncode == 0 and result.stdout:
            matches = [line for line in result.stdout.splitlines() if line.strip()]
            if len(matches) >= 5:  # Significant technical debt (≥5 markers)
                issues.append(
                    StrategicIssue(
                        category="quality",
                        severity="medium",
                        description=f"Found {len(matches)} TODO/FIXME/HACK comment markers indicating technical debt",
                        affected_files=list({m.split(":")[0] for m in matches[:20]}),
                        suggested_fixes=[
                            "Review and resolve high-priority TODOs",
                            "Convert FIXMEs into tracked issues",
                            "Refactor code marked with HACK comments",
                        ],
                        dependencies=[],
                    )
                )
                self.logger.info(f"📝 Found {len(matches)} technical debt markers")

        return issues

    def _list_python_files(
        self,
        root: Path,
        glob_pattern: str = "*.py",
        timeout_s: int = 8,
        fallback_limit: int = 3000,
    ) -> list[Path]:
        """Fast Python file discovery with rg fallback."""
        if not root.exists():
            return []
        try:
            result = subprocess.run(
                ["rg", "--files", str(root), "-g", glob_pattern],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("Suppressed FileNotFoundError/subprocess", exc_info=True)

        files: list[Path] = []
        for idx, py_file in enumerate(root.rglob(glob_pattern)):
            if idx >= fallback_limit:
                break
            files.append(py_file)
        return files

    def _count_python_files(
        self,
        root: Path,
        glob_pattern: str = "*.py",
        timeout_s: int = 6,
    ) -> int:
        """Count matching files quickly with rg fallback."""
        if not root.exists():
            return 0
        try:
            result = subprocess.run(
                ["rg", "--files", str(root), "-g", glob_pattern],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            if result.returncode == 0:
                return sum(1 for line in result.stdout.splitlines() if line.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("Suppressed FileNotFoundError/subprocess", exc_info=True)
        return sum(1 for _ in root.rglob(glob_pattern))

    def _check_integration_completeness(self) -> list[StrategicIssue]:
        """Check for incomplete module integrations."""
        issues = []
        src_dir = Path(__file__).resolve().parents[1]  # = src/ regardless of cwd
        if not src_dir.exists():
            return issues

        python_files = self._list_python_files(src_dir, "*.py", timeout_s=10)

        # Check for missing __init__.py files based on package dirs that contain Python code
        dirs_without_init: list[str] = []
        dir_scan_limit = int(os.getenv("CULTURE_SHIP_DIR_SCAN_LIMIT", "2000"))
        seen_dirs: set[Path] = set()
        for py_file in python_files:
            for parent in py_file.parents:
                if parent == src_dir or src_dir not in parent.parents:
                    break
                if len(seen_dirs) >= dir_scan_limit:
                    break
                if parent in seen_dirs:
                    continue
                seen_dirs.add(parent)
                if (
                    any(part.startswith(".") for part in parent.parts)
                    or "__pycache__" in parent.parts
                ):
                    continue
                if not (parent / "__init__.py").exists():
                    dirs_without_init.append(str(parent))
            if len(seen_dirs) >= dir_scan_limit:
                break

        if len(dirs_without_init) > 5:
            issues.append(
                StrategicIssue(
                    category="architecture",
                    severity="low",
                    description=f"{len(dirs_without_init)} directories missing __init__.py files",
                    affected_files=dirs_without_init[:10],
                    suggested_fixes=["Add __init__.py to all package directories"],
                    dependencies=[],
                )
            )

        # Check for stub implementations
        stub_files: list[str] = []
        try:
            rg_result = subprocess.run(
                [
                    "rg",
                    "-n",
                    "--glob",
                    "src/**/*.py",
                    "-e",
                    r"^\s*pass\s+# TODO\b",
                    "-e",
                    r"^\s*raise\s+NotImplementedError\b",
                    "-e",
                    r"^\s*# PLACEHOLDER\b",
                    "src",
                ],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            if rg_result.returncode == 0 and rg_result.stdout:
                stub_files = list({line.split(":", 1)[0] for line in rg_result.stdout.splitlines()})
        except FileNotFoundError:
            stub_patterns = (
                re.compile(r"^\s*pass\s+# TODO\b", re.MULTILINE),
                re.compile(r"^\s*raise\s+NotImplementedError\b", re.MULTILINE),
                re.compile(r"^\s*# PLACEHOLDER\b", re.MULTILINE),
            )
            stub_scan_limit = int(os.getenv("CULTURE_SHIP_STUB_SCAN_LIMIT", "500"))
            for idx, py_file in enumerate(python_files):
                if idx >= stub_scan_limit:
                    break
                try:
                    content = py_file.read_text(encoding="utf-8")
                    if any(pattern.search(content) for pattern in stub_patterns):
                        stub_files.append(str(py_file))
                except Exception:
                    continue
            stub_files = list(dict.fromkeys(stub_files))
        except subprocess.TimeoutExpired:
            self.logger.debug("Stub scan timed out; skipping for this cycle")

        if len(stub_files) > 3:
            issues.append(
                StrategicIssue(
                    category="architecture",
                    severity="high",
                    description=f"{len(stub_files)} files contain placeholder/stub implementations",
                    affected_files=stub_files,
                    suggested_fixes=[
                        "Complete stub implementations",
                        "Remove unused placeholder files",
                    ],
                    dependencies=[],
                )
            )
            self.logger.info(f"🚧 Found {len(stub_files)} stub implementations")

        return issues

    def _analyze_test_coverage(self) -> list[StrategicIssue]:
        """Analyze test coverage gaps."""
        issues = []
        src_file_count = self._count_python_files(Path("src"), "*.py")
        test_file_count = self._count_python_files(Path("tests"), "test_*.py")

        # Simple heuristic: should have ~30% as many test files as source files
        expected_test_files = src_file_count * 0.3

        if test_file_count < expected_test_files:
            issues.append(
                StrategicIssue(
                    category="quality",
                    severity="medium",
                    description=(
                        f"Low test coverage: {test_file_count} test files for {src_file_count} source files"
                    ),
                    affected_files=["tests/"],
                    suggested_fixes=[
                        "Add tests for critical orchestration modules",
                        "Add tests for src/orchestration/sns_orchestrator_adapter.py",
                        "Add tests for src/agents/bridges/guild_board_bridge.py",
                    ],
                    dependencies=["pytest"],
                )
            )
            self.logger.info(
                "📊 Test coverage: %s tests for %s source files",
                test_file_count,
                src_file_count,
            )

        return issues

    def _resolve_token_metrics_file(self) -> Path | None:
        """Locate token optimization metrics file from known locations."""
        candidates = (
            Path("state/reports/token_metrics_summary.json"),
            Path("data/token_optimization_metrics.json"),
            Path("state/reports/token_optimization_metrics.json"),
            Path("state/reports/sns_metrics.json"),
            Path("data/metrics/token_optimization_metrics.json"),
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    async def _analyze_token_efficiency(self) -> list[StrategicIssue]:
        """Identify token optimization opportunities."""
        issues = []

        try:
            metrics_file = self._resolve_token_metrics_file()

            if metrics_file is None:
                issues.append(
                    StrategicIssue(
                        category="efficiency",
                        severity="low",
                        description="Token optimization metrics not being tracked",
                        affected_files=[
                            "src/orchestration/sns_orchestrator_adapter.py",
                            "src/ui/vscode_metrics_ui.py",
                        ],
                        suggested_fixes=[
                            "Export SNS token metrics to a stable metrics file",
                            "Wire exported token metrics into the metrics dashboard",
                        ],
                        dependencies=[],
                    )
                )
            else:
                metrics = json.loads(metrics_file.read_text(encoding="utf-8"))

                # Check if SNS usage is low
                sns_usage_raw = metrics.get("sns_usage_rate")
                if sns_usage_raw is None:
                    summary = metrics.get("summary", {})
                    if isinstance(summary, dict):
                        sns_usage_raw = summary.get("sns_usage_rate")

                if sns_usage_raw is None:
                    self.logger.debug(
                        "SNS usage rate not present in %s; skipping adoption check",
                        metrics_file,
                    )
                    return issues

                sns_usage = float(sns_usage_raw)
                if sns_usage < 0.3:  # Less than 30% SNS adoption
                    issues.append(
                        StrategicIssue(
                            category="efficiency",
                            severity="medium",
                            description=f"Low SNS-Core adoption ({sns_usage * 100:.0f}%), missing 60-85% token savings",
                            affected_files=[
                                "src/orchestration/unified_ai_orchestrator.py",
                                "src/agents/bridges/guild_board_bridge.py",
                            ],
                            suggested_fixes=[
                                "Enable SNS optimization in orchestrator calls",
                                "Add SNS metrics visibility to guild board bridge workflows",
                            ],
                            dependencies=["src/ai/sns_core_integration.py"],
                        )
                    )
                    self.logger.info(
                        f"💰 Token optimization opportunity: {sns_usage * 100:.0f}% SNS usage"
                    )

        except Exception as e:
            self.logger.debug(f"Token efficiency analysis skipped: {e}")

        return issues

    async def generate_quests_from_analysis(self, issues: list[StrategicIssue]) -> list[str]:
        """Convert strategic issues into Guild Board quests.

        Args:
            issues: List of strategic issues to convert

        Returns:
            List of quest IDs created
        """
        from src.guild.guild_board import get_board

        self.logger.info(f"📋 Generating quests from {len(issues)} strategic issues...")
        quest_ids = []

        try:
            guild_board = await get_board()  # IS async!

            for issue in issues:
                # Only create quests for HIGH and CRITICAL severity
                if issue.severity in ["critical", "high"]:
                    priority = 5 if issue.severity == "critical" else 4

                    # Create quest (add_quest IS async)
                    success, result = await guild_board.add_quest(
                        quest_id=None,  # Auto-generate ID
                        title=f"[STRATEGIC] {issue.description[:60]}",
                        description=f"""
**Category**: {issue.category}
**Severity**: {issue.severity}

{issue.description}

**Affected Files**:
{chr(10).join("- " + f for f in issue.affected_files[:5])}

**Suggested Fixes**:
{chr(10).join("- " + f for f in (issue.suggested_fixes or []))}
""",
                        priority=priority,
                        safety_tier="standard",
                        acceptance_criteria=issue.suggested_fixes or [],
                        tags=["strategic", "auto-generated", issue.category, issue.severity],
                    )
                    if success:
                        quest_ids.append(result)  # result is the quest_id
                        self.logger.info(f"✅ Created quest: {result}")

            self.logger.info(f"📊 Generated {len(quest_ids)} quests from strategic analysis")
            try:
                from src.system.agent_awareness import emit as _emit

                _emit(
                    "culture_ship",
                    f"Generated {len(quest_ids)} strategic quests from {len(issues)} issues",
                    level="INFO",
                    source="culture_ship",
                )
            except Exception:
                pass

        except Exception as e:
            self.logger.error(f"❌ Quest generation failed: {e}")

        return quest_ids

    def make_strategic_decisions(
        self, issues: list[StrategicIssue] | None = None
    ) -> list[StrategicDecision]:
        """Make strategic decisions on how to address issues.

        Args:
            issues: Issues to decide on (uses identified issues if None)

        Returns:
            List of strategic decisions
        """
        if issues is None:
            if not self.issues_identified:
                self.identify_strategic_issues()
            issues = self.issues_identified

        self.logger.info("🎯 Making strategic decisions...")
        decisions = []

        for issue in issues:
            if issue.severity == "critical":
                priority = 10
                estimated_impact = "transformative"
            elif issue.severity == "high":
                priority = 8
                estimated_impact = "high"
            elif issue.severity == "medium":
                priority = 5
                estimated_impact = "medium"
            else:
                priority = 2
                estimated_impact = "low"

            decision = StrategicDecision(
                issue=issue,
                decision=f"Address {issue.category}: {issue.description}",
                rationale=f"{issue.severity} severity issue affecting {len(issue.affected_files)} files",
                action_plan=issue.suggested_fixes or [],
                priority=priority,
                estimated_impact=estimated_impact,
            )
            decisions.append(decision)

        # Sort by priority (descending)
        decisions.sort(key=lambda d: d.priority, reverse=True)
        self.decisions_made = decisions

        return decisions

    def implement_decisions(self) -> dict[str, Any]:
        """Implement strategic decisions using Culture Ship Real Action.

        Returns:
            Implementation results
        """
        if not self.decisions_made:
            self.make_strategic_decisions()

        self.logger.info("🚀 Implementing strategic decisions via Culture Ship...")

        if not self.culture_ship:
            self.logger.error("❌ Culture Ship not available for implementation")
            return {
                "status": "failed",
                "reason": "Culture Ship not available",
                "decisions_processed": len(self.decisions_made),
                "implementations": [],
                "total_fixes_applied": 0,
            }

        results: dict[str, Any] = {
            "decisions_processed": len(self.decisions_made),
            "implementations": [],
            "total_fixes_applied": 0,
        }

        ship_results = self.culture_ship.scan_and_fix_ecosystem()
        total_fixes_applied = ship_results.get("fixes_applied", 0)

        for idx, decision in enumerate(self.decisions_made):
            self.logger.info(f"\n📋 Implementing: {decision.issue.category.upper()}")
            self.logger.info(f"   Severity: {decision.issue.severity}")
            self.logger.info(f"   Priority: {decision.priority}/10")
            self.logger.info(f"   Estimated Impact: {decision.estimated_impact}")

            if idx == 0:
                fixes_applied = ship_results.get("fixes_applied", 0)
                files_fixed = ship_results.get("files_fixed", [])
                status = "completed" if fixes_applied > 0 else "analyzed"
            else:
                self.logger.info(
                    "   Lower-priority decision: reusing previously applied fixes (batched)"
                )
                fixes_applied = 0
                files_fixed = []
                status = "batched"

            implementation = {
                "decision": decision.decision,
                "rationale": decision.rationale,
                "action_plan": decision.action_plan,
                "fixes_applied": fixes_applied,
                "files_fixed": files_fixed,
                "status": status,
            }
            results["implementations"].append(implementation)

            self.improvements_completed.append(implementation)

        results["total_fixes_applied"] = total_fixes_applied

        self.logger.info(f"\n✅ Total fixes applied: {results['total_fixes_applied']}")
        return results

    def _record_learning_cycle(
        self, decisions: list[StrategicDecision], results: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Persist outcomes so agents can reuse learnings next time."""
        timestamp = datetime.now().isoformat()
        history_path = Path("state/culture_ship_healing_history.json")
        receipt_dir = Path("state/receipts")

        implementations = results.get("implementations", {}).get("implementations", [])
        decisions_payload: list[dict[str, Any]] = []

        for idx, decision in enumerate(decisions):
            impl = implementations[idx] if idx < len(implementations) else {}
            decisions_payload.append(
                {
                    "decision": decision.decision,
                    "category": decision.issue.category,
                    "severity": decision.issue.severity,
                    "priority": decision.priority,
                    "rationale": decision.rationale,
                    "action_plan": decision.action_plan,
                    "affected_files": decision.issue.affected_files,
                    "dependencies": decision.issue.dependencies,
                    "files_fixed": impl.get("files_fixed", []),
                    "fixes_applied": impl.get("fixes_applied", 0),
                    "status": impl.get("status", "unknown"),
                }
            )

        cycle = {
            "timestamp": timestamp,
            "issues_identified": results.get("issues_identified"),
            "decisions_made": len(decisions),
            "strategic_decisions": decisions_payload,
            "total_fixes_applied": results.get("implementations", {}).get("total_fixes_applied", 0),
            "source": "culture_ship_strategic_cycle",
        }

        try:
            history_path.parent.mkdir(parents=True, exist_ok=True)
            existing: dict[str, Any]
            try:
                existing = json.loads(history_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError):
                existing = {"cycles": []}

            if not isinstance(existing.get("cycles"), list):
                existing["cycles"] = []

            existing["cycles"].append(cycle)
            history_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
            self.logger.info("📚 Recorded Culture Ship learning cycle at %s", history_path)

            # Dual-write strategic decisions to DuckDB for realtime queries
            try:
                from src.duckdb_integration.dual_write import \
                    insert_single_event

                for decision in decisions_payload:
                    insert_single_event(
                        Path("data/state.duckdb"),
                        {
                            "timestamp": cycle["timestamp"],
                            "event": "culture_ship_decision",
                            "details": decision,
                        },
                    )
                self.logger.debug("✅ Dual-wrote %d decisions to DuckDB", len(decisions_payload))
            except Exception as db_err:
                self.logger.warning("Failed to write decisions to DuckDB: %s", db_err)

            # Auto-convert strategic decisions to quests for tracking
            try:
                from src.orchestration.culture_ship_quest_bridge import \
                    journal_strategic_decision_as_quest

                quest_ids = []
                for decision in decisions_payload:
                    # Only create quests for critical/high priority decisions
                    priority = decision.get("priority", 0)
                    if priority >= 8:  # Critical (10) and High (8) priorities
                        quest_id = journal_strategic_decision_as_quest(decision)
                        quest_ids.append(quest_id)

                if quest_ids:
                    self.logger.info(
                        "🎯 Created %d strategic quests: %s", len(quest_ids), quest_ids
                    )
            except Exception as quest_err:
                self.logger.warning("Failed to create strategic quests: %s", quest_err)

        except Exception as exc:  # pragma: no cover - best effort
            self.logger.warning("⚠️  Failed to record learning cycle: %s", exc)
            return None

        try:
            receipt_dir.mkdir(parents=True, exist_ok=True)
            receipt_ts = datetime.now().strftime("%Y%m%dT%H%M%S")
            receipt_path = receipt_dir / f"culture_ship_learning_{receipt_ts}.json"
            receipt_path.write_text(json.dumps(cycle, indent=2), encoding="utf-8")
            self.logger.info("🧾 Learning receipt saved to %s", receipt_path)
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.warning("⚠️  Failed to write learning receipt: %s", exc)

        try:
            from src.orchestration.culture_ship_quest_bridge import \
                sync_culture_ship_history_to_quests

            quest_ids = sync_culture_ship_history_to_quests()
            if quest_ids:
                self.logger.info("📌 Synced %s decisions into quests", len(quest_ids))
        except ImportError:
            self.logger.info("Info: Quest bridge not available; skipping quest sync")
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.warning("⚠️  Quest sync failed: %s", exc)

        return cycle

    def _escalate_unresolved_to_guild(
        self, decisions: list[StrategicDecision], results: dict[str, Any]
    ) -> int:
        """Escalate unresolved high-priority decisions to the Guild Board.

        Args:
            decisions: Strategic decisions that were attempted
            results: Implementation results with fixes applied info

        Returns:
            Number of decisions escalated to Guild Board
        """
        escalated_count = 0
        fixes_applied = results.get("total_fixes_applied", 0)

        # If all fixes were applied, nothing to escalate
        if fixes_applied >= len(decisions):
            self.logger.info("✅ All decisions resolved; no escalation needed")
            return 0

        # Identify unresolved high-priority decisions (priority >= 7)
        unresolved = [d for d in decisions if d.priority >= 7]

        if not unresolved:
            self.logger.info("ℹ️  No high-priority unresolved decisions to escalate")
            return 0

        self.logger.info(f"📋 Escalating {len(unresolved)} unresolved decisions to Guild Board")

        try:
            from src.orchestration.culture_ship_quest_bridge import \
                journal_strategic_decision_as_quest

            for decision in unresolved:
                decision_dict = {
                    "category": decision.issue.category,
                    "severity": decision.issue.severity,
                    "priority": decision.priority,
                    "description": decision.issue.description,
                    "action_plan": decision.action_plan or [],
                    "escalated": True,
                }
                try:
                    quest_id = journal_strategic_decision_as_quest(decision_dict)
                    if quest_id:
                        escalated_count += 1
                        self.logger.info(f"  ↗️  Escalated: {quest_id}")
                except Exception as e:
                    self.logger.warning(f"  ⚠️  Failed to escalate decision: {e}")

            self.logger.info(f"✅ Escalated {escalated_count}/{len(unresolved)} to Guild Board")

        except ImportError:
            self.logger.info("Info: Quest bridge not available; skipping escalation")
        except Exception as e:
            self.logger.warning(f"⚠️  Guild escalation failed: {e}")

        return escalated_count

    def run_full_strategic_cycle(self) -> dict[str, Any]:
        """Run a complete strategic improvement cycle.

        Returns:
            Results of the complete cycle
        """
        self.logger.info("=" * 70)
        self.logger.info("🌟 CULTURE SHIP STRATEGIC ADVISOR - FULL CYCLE")
        self.logger.info("=" * 70)

        # Phase 1: Identify issues
        self.logger.info("\n📊 PHASE 1: ISSUE IDENTIFICATION")
        # Use real dynamic analysis instead of hardcoded issues
        try:
            import asyncio

            issues = asyncio.run(self.conduct_strategic_analysis())
            self.logger.info(f"   Identified {len(issues)} strategic issues (dynamic analysis)")
        except Exception as e:
            self.logger.warning(f"Dynamic analysis failed, falling back to static: {e}")
            issues = self.identify_strategic_issues()
            self.logger.info(f"   Identified {len(issues)} strategic issues (static fallback)")

        # Phase 2: Make decisions
        self.logger.info("\n🎯 PHASE 2: STRATEGIC DECISION MAKING")
        decisions = self.make_strategic_decisions(issues)
        self.logger.info(f"   Made {len(decisions)} strategic decisions")

        for decision in decisions[:3]:  # Show top 3
            self.logger.info(
                f"   - [{decision.priority}/10] {decision.issue.category}: {decision.issue.severity}"
            )

        # Phase 3: Implement
        self.logger.info("\n🚀 PHASE 3: IMPLEMENTATION")
        results = self.implement_decisions()

        # Phase 3.5: Escalate unresolved high-priority issues to Guild Board
        escalated = self._escalate_unresolved_to_guild(decisions, results)
        results["guild_escalated"] = escalated

        # Summary
        self.logger.info("\n" + "=" * 70)
        self.logger.info("📈 STRATEGIC CYCLE COMPLETE")
        self.logger.info("=" * 70)
        self.logger.info(f"   Issues identified: {len(issues)}")
        self.logger.info(f"   Decisions made: {len(decisions)}")
        self.logger.info(f"   Total fixes applied: {results['total_fixes_applied']}")
        self.logger.info(f"   Improvements completed: {len(self.improvements_completed)}")
        coordination_plan = self.build_ecosystem_coordination_plan()
        self.logger.info("   Ecosystem coordination plan: %s", coordination_plan["status"])

        summary = {
            "status": "complete",
            "issues_identified": len(issues),
            "decisions_made": len(decisions),
            "implementations": results,
            "improvements_completed": len(self.improvements_completed),
            "ecosystem_coordination": coordination_plan,
        }

        # Persist learnings so future runs/agents can reuse patterns
        self._record_learning_cycle(decisions, summary)

        return summary


def main() -> None:
    """Run Culture Ship Strategic Advisor."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    advisor = CultureShipStrategicAdvisor()
    results = advisor.run_full_strategic_cycle()

    # Print JSON results for integration
    import json

    logger.info("\n" + json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

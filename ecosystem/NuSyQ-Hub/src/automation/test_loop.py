"""TestLoop - Self-testing AI loop for iterative test fixes.

Provides automated test running with AI-powered fix attempts:
- Runs tests on specified targets
- Analyzes failures and dispatches AI fixes
- Iterates until tests pass or max attempts reached
- Logs all attempts to eventlog for audit

OmniTag: [testing, automation, ai, self-healing]
MegaTag: TEST⨳LOOP⦾AUTOMATION→∞

Usage:
    from src.automation.test_loop import TestLoop

    loop = TestLoop()
    result = loop.iterate_until_pass("tests/", max_iterations=5)
"""

import logging
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.core.result import Fail, Ok, Result

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a test run.

    Attributes:
        passed: Whether all tests passed
        total: Total number of tests
        passed_count: Number of passing tests
        failed_count: Number of failing tests
        failed_tests: Details of failed tests
        duration: Test run duration in seconds
        output: Raw test output
    """

    passed: bool
    total: int = 0
    passed_count: int = 0
    failed_count: int = 0
    failed_tests: list[dict] = field(default_factory=list)
    duration: float = 0.0
    output: str = ""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "total": self.total,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "failed_tests": self.failed_tests,
            "duration": self.duration,
        }


@dataclass
class FixAttempt:
    """Record of an AI fix attempt.

    Attributes:
        iteration: Iteration number
        failed_tests: Tests that failed before fix
        fix_applied: Whether a fix was successfully applied
        task_id: Background task ID for the fix
        result: Outcome of the fix attempt
    """

    iteration: int
    failed_tests: list[dict]
    fix_applied: bool = False
    task_id: str | None = None
    result: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "failed_tests_count": len(self.failed_tests),
            "fix_applied": self.fix_applied,
            "task_id": self.task_id,
            "result": self.result,
            "timestamp": self.timestamp,
        }


class TestLoop:
    """Self-testing AI loop that runs tests and attempts fixes.

    Integrates with:
    - BackgroundTaskOrchestrator for AI-powered fixes
    - Event logging for audit trails
    - QuestExecutor for safe code modifications

    Example:
        loop = TestLoop()

        # Run tests once
        result = loop.run_tests("tests/")

        # Iterate with AI fixes until pass
        result = loop.iterate_until_pass("tests/unit/", max_iterations=5)
    """

    def __init__(
        self,
        root_path: Path | None = None,
        pytest_args: list[str] | None = None,
        enable_ai_fixes: bool = True,
    ):
        """Initialize the test loop.

        Args:
            root_path: Project root path (auto-detected if None)
            pytest_args: Additional pytest arguments
            enable_ai_fixes: Whether to attempt AI fixes on failures
        """
        self.root_path = root_path or Path(__file__).parent.parent.parent
        # Keep loop runs deterministic; coverage gates are enforced in CI/full test jobs.
        self.pytest_args = pytest_args or ["-v", "--tb=short", "--no-cov"]
        self.enable_ai_fixes = enable_ai_fixes

        # Track iterations
        self._attempts: list[FixAttempt] = []
        self._session_id = str(uuid.uuid4())[:8]

        # Initialize background orchestrator if available
        self._orchestrator = None
        if enable_ai_fixes:
            try:
                from src.orchestration.background_task_orchestrator import \
                    BackgroundTaskOrchestrator

                self._orchestrator = BackgroundTaskOrchestrator()
            except ImportError:
                logger.warning("BackgroundTaskOrchestrator not available, AI fixes disabled")
                self.enable_ai_fixes = False

        logger.info(f"TestLoop initialized (session: {self._session_id})")
        logger.info(f"  Root path: {self.root_path}")
        logger.info(f"  AI fixes: {'enabled' if self.enable_ai_fixes else 'disabled'}")

    def run_tests(self, target: str, timeout: int = 120) -> Result[TestResult]:
        """Run tests on the specified target.

        Args:
            target: Test target (file, directory, or pattern)
            timeout: Timeout in seconds

        Returns:
            Result[TestResult]: Test results or error
        """
        import time

        start_time = time.time()

        target_path = self.root_path / target if not Path(target).is_absolute() else Path(target)

        if not target_path.exists():
            return Fail(f"Test target not found: {target}", code="TARGET_NOT_FOUND")

        try:
            # Build pytest command
            cmd = [
                "python",
                "-m",
                "pytest",
                str(target_path),
                *self.pytest_args,
            ]

            logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=self.root_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            duration = time.time() - start_time

            # Parse results
            test_result = self._parse_pytest_output(
                result.stdout,
                result.stderr,
                result.returncode,
                duration,
            )

            # Log event
            self._log_event(
                "test_run",
                {
                    "target": target,
                    "passed": test_result.passed,
                    "total": test_result.total,
                    "failed_count": test_result.failed_count,
                    "duration": duration,
                },
            )

            return Ok(test_result)

        except subprocess.TimeoutExpired:
            return Fail(f"Test timeout after {timeout}s", code="TIMEOUT")
        except Exception as e:
            return Fail(str(e), code="TEST_ERROR")

    def iterate_until_pass(
        self,
        target: str,
        max_iterations: int = 5,
        _fix_timeout: int = 60,
    ) -> Result[dict]:
        """Run tests and iterate with AI fixes until passing.

        Args:
            target: Test target (file, directory, or pattern)
            max_iterations: Maximum fix attempts
            fix_timeout: Timeout for each fix attempt

        Returns:
            Result[dict]: Final status with all attempts
        """
        logger.info(f"Starting test loop for: {target}")
        logger.info(f"  Max iterations: {max_iterations}")

        self._attempts = []

        for iteration in range(1, max_iterations + 1):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"ITERATION {iteration}/{max_iterations}")
            logger.info(f"{'=' * 60}")

            # Run tests
            test_result = self.run_tests(target)

            if not test_result.success:
                return Fail(f"Test run failed: {test_result.error}", code="TEST_RUN_FAILED")

            result = test_result.data

            # Check if all passed
            if result.passed:
                logger.info(f"\n✅ All tests passed on iteration {iteration}!")

                self._log_event(
                    "test_loop_success",
                    {
                        "iterations": iteration,
                        "target": target,
                        "total_tests": result.total,
                    },
                )

                return Ok(
                    {
                        "status": "passed",
                        "iterations": iteration,
                        "final_result": result.to_dict(),
                        "attempts": [a.to_dict() for a in self._attempts],
                    }
                )

            # Tests failed - attempt AI fix
            logger.info(f"\n❌ {result.failed_count} tests failed")

            if not self.enable_ai_fixes:
                logger.warning("AI fixes disabled, stopping iteration")
                self._log_event(
                    "test_loop_stopped_no_ai",
                    {
                        "iterations": iteration,
                        "target": target,
                        "failed_count": result.failed_count,
                    },
                )
                return Ok(
                    {
                        "status": "failed_no_ai",
                        "iterations": iteration,
                        "final_result": result.to_dict(),
                        "attempts": [a.to_dict() for a in self._attempts],
                    }
                )

            if iteration == max_iterations:
                logger.warning("Max iterations reached, not attempting fix")
                break

            # Attempt AI fix
            fix_result = self._attempt_ai_fix(result.failed_tests, iteration)

            attempt = FixAttempt(
                iteration=iteration,
                failed_tests=result.failed_tests,
                fix_applied=fix_result.success if fix_result else False,
                task_id=(
                    fix_result.data.get("task_id") if fix_result and fix_result.success else None
                ),
                result=(
                    fix_result.data.get("status")
                    if fix_result and fix_result.success
                    else fix_result.error if fix_result else "No fix attempted"
                ),
            )
            self._attempts.append(attempt)

            if not fix_result or not fix_result.success:
                logger.warning(
                    f"Fix attempt failed: {fix_result.error if fix_result else 'Unknown'}"
                )
                # Continue anyway - maybe the fix was partial

        # Loop exhausted without all tests passing
        final_test = self.run_tests(target)
        final_result = final_test.data if final_test.success else None

        self._log_event(
            "test_loop_exhausted",
            {
                "iterations": max_iterations,
                "target": target,
                "final_status": "passed" if final_result and final_result.passed else "failed",
                "failed_count": final_result.failed_count if final_result else -1,
            },
        )

        return Ok(
            {
                "status": "exhausted",
                "iterations": max_iterations,
                "final_result": final_result.to_dict() if final_result else None,
                "attempts": [a.to_dict() for a in self._attempts],
            }
        )

    def _attempt_ai_fix(
        self,
        failed_tests: list[dict],
        iteration: int,
    ) -> Result[dict]:
        """Attempt to fix failed tests using AI.

        Args:
            failed_tests: List of failed test details
            iteration: Current iteration number

        Returns:
            Result[dict]: Fix attempt result
        """
        if not self._orchestrator:
            return Fail("No orchestrator available", code="NO_ORCHESTRATOR")

        logger.info(f"\n🤖 Attempting AI fix (iteration {iteration})")

        # Build prompt from failed tests
        prompt = self._build_fix_prompt(failed_tests)

        try:
            # Try nusyq facade first
            try:
                from src.core import nusyq

                result = nusyq.background.dispatch(
                    prompt=prompt,
                    task_type="code_fix",
                    priority="high",
                )

                if result.success:
                    logger.info(f"   Fix dispatched: {result.data}")
                    return Ok(
                        {
                            "status": "dispatched",
                            "task_id": result.data,
                            "prompt_length": len(prompt),
                        }
                    )

            except (ImportError, AttributeError):
                logger.debug("Suppressed AttributeError/ImportError", exc_info=True)

            # Fallback to direct orchestrator call
            import asyncio

            task_id = asyncio.run(
                self._orchestrator.submit_task(
                    prompt=prompt,
                    task_type="code_fix",
                    priority=8,  # High priority
                    requesting_agent="test_loop",
                    metadata={
                        "session_id": self._session_id,
                        "iteration": iteration,
                        "failed_count": len(failed_tests),
                    },
                )
            )

            logger.info(f"   Fix task submitted: {task_id}")

            return Ok(
                {
                    "status": "submitted",
                    "task_id": task_id,
                    "prompt_length": len(prompt),
                }
            )

        except Exception as e:
            logger.error(f"   Fix attempt failed: {e}")
            return Fail(str(e), code="FIX_ERROR")

    def _build_fix_prompt(self, failed_tests: list[dict]) -> str:
        """Build an AI prompt for fixing failed tests.

        Args:
            failed_tests: List of failed test details

        Returns:
            Formatted prompt string
        """
        lines = [
            "# Test Fix Request",
            "",
            "The following tests are failing. Please analyze the failures and suggest fixes.",
            "",
            "## Failed Tests",
            "",
        ]

        for i, test in enumerate(failed_tests[:10], 1):  # Limit to 10 tests
            lines.append(f"### {i}. {test.get('name', 'Unknown test')}")
            lines.append(f"- **File:** {test.get('file', 'unknown')}")
            lines.append(f"- **Line:** {test.get('line', 'unknown')}")

            if test.get("message"):
                message = test.get("message")
                lines.append(f"- **Error:** {str(message)[:500]}")

            if test.get("traceback"):
                lines.append("- **Traceback:**")
                lines.append("```")
                traceback_text = test.get("traceback")
                lines.append(str(traceback_text)[:1000])
                lines.append("```")

            lines.append("")

        if len(failed_tests) > 10:
            lines.append(f"*... and {len(failed_tests) - 10} more failed tests*")
            lines.append("")

        lines.extend(
            [
                "## Instructions",
                "",
                "1. Analyze the error messages and tracebacks",
                "2. Identify the root cause of each failure",
                "3. Suggest specific code fixes",
                "4. If the test itself is wrong, explain why",
                "",
                "Please provide your analysis and suggested fixes.",
            ]
        )

        return "\n".join(lines)

    def _parse_pytest_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
        duration: float,
    ) -> TestResult:
        """Parse pytest output to extract test results.

        Args:
            stdout: Standard output from pytest
            stderr: Standard error from pytest
            returncode: Exit code from pytest
            duration: Test run duration

        Returns:
            TestResult with parsed data
        """
        # Fallback: parse text output
        summary_text = f"{stdout}\n{stderr}"
        passed = returncode == 0

        # Try to extract counts from output
        total = 0
        passed_count = 0
        failed_count = 0
        failed_tests = []

        import re

        # Look for summary line like "5 passed, 2 failed"
        summary_match = re.search(
            r"(\d+)\s+passed(?:,\s+(\d+)\s+failed)?",
            summary_text,
        )

        if summary_match:
            passed_count = int(summary_match.group(1))
            failed_count = int(summary_match.group(2) or 0)
            total = passed_count + failed_count
        else:
            collected_match = re.search(r"collected\s+(\d+)\s+items", summary_text)
            if collected_match:
                total = int(collected_match.group(1))

            passed_count = len(re.findall(r"\bPASSED\b", summary_text))
            failed_count = len(re.findall(r"\bFAILED\b", summary_text))

            if total == 0 and (passed_count > 0 or failed_count > 0):
                total = passed_count + failed_count

            # If test collection/execution succeeded but return code was polluted
            # by plugins (coverage, extra reporters), trust parsed outcomes.
            error_count = len(re.findall(r"\bERROR\b", summary_text))
            if total > 0 and failed_count == 0 and error_count == 0:
                passed = True

        # Extract failed test names
        failed_pattern = re.compile(r"FAILED\s+([^\s]+)")
        for match in failed_pattern.finditer(stdout):
            test_id = match.group(1)
            failed_tests.append(
                {
                    "name": test_id,
                    "file": test_id.split("::")[0] if "::" in test_id else test_id,
                    "line": 0,
                    "message": "",
                }
            )

        return TestResult(
            passed=passed,
            total=total,
            passed_count=passed_count,
            failed_count=failed_count,
            failed_tests=failed_tests,
            duration=duration,
            output=stdout[:5000],
        )

    def _log_event(self, action: str, data: dict) -> None:
        """Log an event to the event log.

        Args:
            action: Event action name
            data: Event data
        """
        try:
            from src.nusyq_spine.eventlog import append_event

            append_event(
                {
                    "trace_id": f"testloop_{self._session_id}",
                    "actor": "test_loop",
                    "action": action,
                    "inputs_hash": "",
                    "outputs_hash": "",
                    "status": "success",
                    **data,
                }
            )
        except ImportError:
            # Event logging not available
            pass

    def get_attempt_history(self) -> list[dict]:
        """Get history of fix attempts in current session.

        Returns:
            List of attempt records
        """
        return [a.to_dict() for a in self._attempts]

    def reset_session(self) -> None:
        """Reset the test loop session."""
        self._attempts = []
        self._session_id = str(uuid.uuid4())[:8]
        logger.info(f"TestLoop session reset: {self._session_id}")


def get_test_loop() -> TestLoop:
    """Get a TestLoop instance.

    Returns:
        TestLoop instance
    """
    return TestLoop()

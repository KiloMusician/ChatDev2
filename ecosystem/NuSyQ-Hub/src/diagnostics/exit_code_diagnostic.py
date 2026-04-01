#!/usr/bin/env python3
"""🔍 Exit Code Diagnostic Tool.

Investigates exit code patterns, failures, and system issues.
"""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def test_command(cmd: list[str], description: str, timeout: int = 10) -> dict[str, Any]:
    """Test a command and return diagnostic info."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.cwd(),
        )
        return {
            "description": description,
            "command": " ".join(cmd),
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "stdout_length": len(result.stdout),
            "stderr_length": len(result.stderr),
            "stderr_preview": result.stderr[:500] if result.stderr else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "description": description,
            "command": " ".join(cmd),
            "exit_code": -1,
            "success": False,
            "error": f"Timeout after {timeout}s",
        }
    except Exception as e:
        return {
            "description": description,
            "command": " ".join(cmd),
            "exit_code": -2,
            "success": False,
            "error": str(e),
        }


def main() -> None:
    """Run comprehensive exit code diagnostics."""
    logger.info("🔍 Exit Code Diagnostic Report")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Working Directory: {Path.cwd()}")
    logger.info()

    results: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {},
    }

    # Test suite
    tests = [
        (["python", "--version"], "Python version check"),
        (["python", "-m", "mypy", "--version"], "MyPy availability"),
        (["python", "-m", "black", "--version"], "Black availability"),
        (["ruff", "--version"], "Ruff availability"),
        (["git", "--version"], "Git availability"),
        (["python", "-m", "pytest", "--version"], "Pytest availability"),
        (
            ["python", "src/diagnostics/quick_quest_audit.py"],
            "Quick quest audit execution",
        ),
        (
            ["python", "src/diagnostics/comprehensive_integration_validator.py"],
            "Integration validator execution",
        ),
        (
            ["python", "-m", "mypy", "src/main.py", "--no-incremental"],
            "MyPy on main.py",
        ),
        (["ruff", "check", "src/main.py"], "Ruff check on main.py"),
    ]

    logger.info("Running diagnostic tests...")
    logger.info()

    for cmd, description in tests:
        logger.info(f"  Testing: {description}...", end=" ")
        test_result = test_command(cmd, description)
        results["tests"].append(test_result)

        if test_result["success"]:
            logger.info("✅")
        else:
            logger.error(f"❌ (exit code: {test_result['exit_code']})")
            if test_result.get("error"):
                logger.error(f"    Error: {test_result['error']}")
            if test_result.get("stderr_preview"):
                logger.info(f"    Stderr: {test_result['stderr_preview'][:100]}")

    # Summary
    total_tests = len(results["tests"])
    passed_tests = sum(1 for t in results["tests"] if t["success"])
    failed_tests = total_tests - passed_tests

    results["summary"] = {
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
    }

    logger.info()
    logger.info("=" * 70)
    logger.info("📊 Summary")
    logger.info(f"  Total Tests: {total_tests}")
    logger.info(f"  Passed: {passed_tests} ✅")
    logger.error(f"  Failed: {failed_tests} ❌")
    logger.info(f"  Success Rate: {results['summary']['success_rate']:.1f}%")
    logger.info()

    # Identify common failure patterns
    if failed_tests > 0:
        logger.error("🔍 Failed Tests:")
        for test in results["tests"]:
            if not test["success"]:
                logger.info(f"  - {test['description']}")
                logger.info(f"    Command: {test['command']}")
                logger.info(f"    Exit Code: {test['exit_code']}")
                if test.get("error"):
                    logger.error(f"    Error: {test['error']}")
        logger.info()

    # Save results
    output_file = Path("data/logs/exit_code_diagnostic.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"📝 Full diagnostic saved to: {output_file}")
    logger.info()

    # Exit with appropriate code
    sys.exit(0 if failed_tests == 0 else 1)


if __name__ == "__main__":
    main()

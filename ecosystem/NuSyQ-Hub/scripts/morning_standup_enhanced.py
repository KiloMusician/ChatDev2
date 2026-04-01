#!/usr/bin/env python3
"""Enhanced Daily Development Automation - Morning Standup
Uses dual-channel output framework for maximum insight and utility.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.enhanced_output import create_enhanced_output


def run_check(cmd: list[str], timeout: int = 30) -> tuple[bool, str, str]:
    """Run a command and return success, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def main():
    """Run enhanced morning standup."""
    output = create_enhanced_output("morning_standup")

    # Define check pipeline
    checks = [
        {
            "name": "System Health (Selfcheck)",
            "cmd": [sys.executable, "scripts/start_nusyq.py", "selfcheck"],
            "timeout": 30,
            "hint": "Run 'python scripts/start_nusyq.py heal' to auto-repair",
        },
        {
            "name": "Guild Board Status",
            "cmd": [sys.executable, "scripts/start_nusyq.py", "guild_status"],
            "timeout": 15,
            "hint": "Check state/guild/guild_board.json for details",
        },
        {
            "name": "Capability Inventory",
            "cmd": [sys.executable, "scripts/start_nusyq.py", "capabilities"],
            "timeout": 15,
            "hint": "Review docs/CAPABILITY_DIRECTORY.md",
        },
        {
            "name": "Code Format (Black)",
            "cmd": [sys.executable, "-m", "black", "src/", "--check", "--quiet"],
            "timeout": 30,
            "hint": "Run 'python -m black src/' to format",
        },
        {
            "name": "Linting (Ruff)",
            "cmd": [sys.executable, "-m", "ruff", "check", "src/", "--select=E,F"],
            "timeout": 30,
            "hint": "Run 'ruff check src/ --fix' for auto-fixes",
        },
        {
            "name": "Quick Tests",
            "cmd": [sys.executable, "-m", "pytest", "tests/", "-q", "-x", "--tb=short"],
            "timeout": 60,
            "hint": "Run 'pytest tests/ -v' for detailed output",
        },
    ]

    # Execute checks
    for check in checks:
        success, stdout, stderr = run_check(check["cmd"], check["timeout"])

        if success:
            output.add_section(
                name=check["name"],
                status="pass",
                details="Completed successfully",
            )
        else:
            # Parse error details
            error_output = stderr or stdout
            error_lines = error_output.split("\n")[:5]  # First 5 lines
            error_summary = " | ".join(line.strip() for line in error_lines if line.strip())

            output.add_section(
                name=check["name"],
                status="fail",
                details=error_summary[:200],  # Truncate to 200 chars
            )

            # Add structured failure
            output.add_failure(
                tool=check["name"].split("(")[0].strip(),
                kind="check_failed",
                file="",
                line=None,
                message=error_summary[:100],
                hint=check["hint"],
                confidence=0.9,
            )

            # Suggest next action
            output.add_next_action(check["hint"], priority="high")

    # Add contextual insights
    total_checks = len(checks)
    failed_checks = len([s for s in output.sections if s["status"] == "fail"])

    if failed_checks == 0:
        output.add_insight("All systems operational - ready for productive development!", category="general")
        output.add_next_action("Start work on highest-priority guild quest", priority="medium")
    elif failed_checks <= 2:
        output.add_insight(
            f"System mostly healthy with {failed_checks} minor issues - can proceed with caution",
            category="pattern",
        )
        output.add_insight(
            "These failures are likely cosmetic (format/lint) and don't block core functionality",
            category="opportunity",
        )
    else:
        output.add_insight(
            f"System degraded with {failed_checks}/{total_checks} failures - recommend fixing before new work",
            category="general",
        )
        output.add_next_action("Run comprehensive healing: python scripts/start_nusyq.py heal", priority="high")

    # Check for common patterns
    if any("E501" in s["details"] for s in output.sections):
        output.add_insight(
            "E501 (line too long) detected - configure max line length or use Black with --line-length=100",
            category="pattern",
        )

    if any("SyntaxError" in s["details"] for s in output.sections):
        output.add_insight(
            "Syntax errors detected - likely from incomplete edits or encoding issues",
            category="pattern",
        )

    # Guild Board integration
    if any("guild" in s["name"].lower() for s in output.sections if s["status"] == "pass"):
        output.add_artifact("state/guild/guild_board.json")
        output.add_next_action(
            "Review available quests: python scripts/start_nusyq.py guild_available claude code,refactor",
            priority="medium",
        )

    # Finalize and print report
    output.finalize()

    # Return exit code
    return 0 if failed_checks == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

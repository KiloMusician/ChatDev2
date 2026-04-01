#!/usr/bin/env python3
"""Post-merge validation and status report generator."""

import subprocess
from datetime import datetime


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run command and return exit code, stdout, stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def main():
    """Generate post-merge validation report."""
    print("=" * 70)
    print("POST-MERGE VALIDATION REPORT")
    print("=" * 70)
    print(f"Generated: {datetime.now().isoformat()}")
    print()

    # Check git status
    print("Git Status:")
    print("-" * 70)
    returncode, stdout, stderr = run_command(["git", "status", "--short"])
    if stdout.strip():
        print(stdout)
    else:
        print("Working directory clean")
    print()

    # Check services
    print("Critical Services Status:")
    print("-" * 70)
    returncode, stdout, stderr = run_command(["python", "scripts/start_all_critical_services.py", "status"])
    if returncode == 0:
        print(stdout)
    else:
        print(f"Service check failed: {stderr}")
    print()

    # Check branch
    print("Current Branch:")
    print("-" * 70)
    returncode, stdout, stderr = run_command(["git", "branch", "--show-current"])
    print(f"Branch: {stdout.strip()}")
    print()

    # Check merge commit
    print("Recent Commits:")
    print("-" * 70)
    returncode, stdout, stderr = run_command(["git", "log", "--oneline", "-5"])
    print(stdout)

    # Check tags
    print("Release Tags:")
    print("-" * 70)
    returncode, stdout, stderr = run_command(["git", "tag", "-l", "v*"])
    tags = stdout.strip().split("\n") if stdout.strip() else []
    print(f"Total tags: {len(tags)}")
    if tags:
        print(f"Latest: {tags[-1]}")
    print()

    # Summary
    print("=" * 70)
    print("POST-MERGE VALIDATION COMPLETE")
    print("=" * 70)
    print("\nNext Actions:")
    print("  1. Review uncommitted changes (if any)")
    print("  2. Plan next feature development")
    print("  3. Monitor service health")
    print("  4. Review coverage gaps for improvement")


if __name__ == "__main__":
    main()

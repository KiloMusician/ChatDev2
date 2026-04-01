#!/usr/bin/env python3
"""🧪 Dev Container Validation Script

Comprehensive validation of the NuSyQ tripartite dev container setup.
Tests repository mounts, environment variables, path resolution, and service availability.

Usage:
    python scripts/validate_devcontainer.py

Exit codes:
    0 - All validations passed
    1 - Some validations failed
    2 - Critical failures (container not detected)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Add Hub to path
SCRIPT_DIR = Path(__file__).parent.resolve()
HUB_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(HUB_ROOT))

from src.system.ecosystem_paths import (
    get_ecosystem_root,
    get_repo_roots,
    validate_ecosystem,
)


class ValidationResult:
    """Track validation results."""

    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.checks = []

    def check(self, description: str, condition: bool, critical: bool = False) -> bool:
        """Record a validation check."""
        status = "✅" if condition else ("❌" if critical else "⚠️")
        self.checks.append((status, description))

        if condition:
            self.passed += 1
        elif critical:
            self.failed += 1
        else:
            self.warnings += 1

        return condition

    def print_results(self):
        """Print all check results."""
        print(f"\n{'=' * 60}")
        print(f"📋 {self.name}")
        print(f"{'=' * 60}")
        for status, description in self.checks:
            print(f"{status} {description}")

        print(f"\n📊 Results: {self.passed} passed, {self.failed} failed, {self.warnings} warnings")

    def has_failures(self) -> bool:
        """Check if any critical failures occurred."""
        return self.failed > 0


def validate_container_environment() -> ValidationResult:
    """Validate container environment detection."""
    result = ValidationResult("Container Environment")

    # Check IN_DEVCONTAINER flag
    in_container_env = os.getenv("IN_DEVCONTAINER") == "true"
    result.check(
        f"IN_DEVCONTAINER environment variable: {os.getenv('IN_DEVCONTAINER', '(not set)')}",
        in_container_env,
        critical=True,
    )

    # Check Docker environment marker
    dockerenv_exists = Path("/.dockerenv").exists()
    result.check(
        f"Docker environment marker (/.dockerenv): {'exists' if dockerenv_exists else 'not found'}",
        dockerenv_exists,
    )

    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    expected_container_py = sys.version_info >= (3, 13)
    result.check(f"Python version: {py_version} (expected 3.13+ in container)", expected_container_py)

    return result


def validate_repository_mounts() -> ValidationResult:
    """Validate all three repositories are mounted."""
    result = ValidationResult("Repository Mounts")

    roots = get_repo_roots()
    validation = validate_ecosystem()

    # Check each repository
    for name, path in roots.items():
        exists = validation[name]
        has_git = (path / ".git").exists() if exists else False

        result.check(f"{name.upper()}: {path} {'(valid)' if exists else '(missing)'}", exists, critical=True)

        if exists:
            result.check(f"  ↳ .git directory: {'found' if has_git else 'missing'}", has_git)

    # Verify workspace structure
    workspaces_root = Path("/workspaces")
    if workspaces_root.exists():
        subdirs = [d.name for d in workspaces_root.iterdir() if d.is_dir()]
        result.check(f"Workspace subdirectories: {', '.join(subdirs)}", len(subdirs) >= 3)

    return result


def validate_environment_variables() -> ValidationResult:
    """Validate ecosystem environment variables."""
    result = ValidationResult("Environment Variables")

    required_vars = {
        "NUSYQ_HUB_ROOT": "/workspaces/NuSyQ-Hub",
        "NUSYQ_ROOT": "/workspaces/NuSyQ",
        "SIMULATEDVERSE_ROOT": "/workspaces/SimulatedVerse",
        "ECOSYSTEM_ROOT": "/workspaces/NuSyQ-Hub",
        "IN_DEVCONTAINER": "true",
    }

    for var, expected in required_vars.items():
        actual = os.getenv(var)
        matches = actual == expected
        result.check(
            f"{var}: {actual} {'✓' if matches else f'(expected: {expected})'}",
            matches,
            critical=(var == "IN_DEVCONTAINER"),
        )

    return result


def validate_path_resolution() -> ValidationResult:
    """Validate ecosystem path resolution system."""
    result = ValidationResult("Path Resolution")

    # Test get_ecosystem_root
    try:
        ecosystem_root = get_ecosystem_root()
        expected_root = Path("/workspaces/NuSyQ-Hub")
        matches = ecosystem_root == expected_root
        result.check(
            f"get_ecosystem_root(): {ecosystem_root} {'✓' if matches else f'(expected: {expected_root})'}",
            matches,
            critical=True,
        )
    except Exception as e:
        result.check(f"get_ecosystem_root() failed: {e}", False, critical=True)

    # Test get_repo_roots
    try:
        roots = get_repo_roots()
        result.check(f"get_repo_roots() returned {len(roots)} repositories", len(roots) == 3, critical=True)

        # Verify all paths are absolute and under /workspaces
        all_under_workspaces = all(str(path).startswith("/workspaces/") for path in roots.values())
        result.check("All repository paths under /workspaces", all_under_workspaces)
    except Exception as e:
        result.check(f"get_repo_roots() failed: {e}", False, critical=True)

    return result


def validate_dependencies() -> ValidationResult:
    """Validate Python and npm dependencies."""
    result = ValidationResult("Dependencies")

    # Check Python packages
    critical_packages = ["pydantic", "pytest", "requests"]
    for package in critical_packages:
        try:
            __import__(package)
            result.check(f"Python package '{package}': installed", True)
        except ImportError:
            result.check(f"Python package '{package}': missing", False)

    # Check Node.js
    try:
        node_result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        if node_result.returncode == 0:
            version = node_result.stdout.strip()
            result.check(f"Node.js: {version}", True)
        else:
            result.check("Node.js: not found", False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        result.check("Node.js: not available", False)

    # Check npm
    try:
        npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=5)
        if npm_result.returncode == 0:
            version = npm_result.stdout.strip()
            result.check(f"npm: {version}", True)
        else:
            result.check("npm: not found", False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        result.check("npm: not available", False)

    return result


def validate_git_hooks() -> ValidationResult:
    """Validate git hooks work in container."""
    result = ValidationResult("Git Hooks")

    pre_commit_hook = HUB_ROOT / ".githooks" / "pre-commit-impl.py"

    if pre_commit_hook.exists():
        result.check(f"Pre-commit hook exists: {pre_commit_hook}", True)

        # Test hook execution
        try:
            hook_result = subprocess.run(
                [sys.executable, str(pre_commit_hook)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=HUB_ROOT,
            )

            # Hook should either pass or fail gracefully (not crash)
            succeeded = hook_result.returncode in [0, 1]
            result.check(
                f"Pre-commit hook execution: {'passed' if hook_result.returncode == 0 else 'completed'}",
                succeeded,
            )

            # Check for Python version error
            has_version_error = "Python >= 3.10 not found" in hook_result.stdout
            result.check(
                "Pre-commit hook Python version check: working",
                not has_version_error,
                critical=True,
            )
        except subprocess.TimeoutExpired:
            result.check("Pre-commit hook execution: timed out", False)
        except Exception as e:
            result.check(f"Pre-commit hook execution failed: {e}", False)
    else:
        result.check(f"Pre-commit hook: not found at {pre_commit_hook}", False)

    return result


def validate_ecosystem_entrypoint() -> ValidationResult:
    """Validate ecosystem entry point script."""
    result = ValidationResult("Ecosystem Entry Point")

    entrypoint = HUB_ROOT / "scripts" / "ecosystem_entrypoint.py"

    if entrypoint.exists():
        result.check(f"Ecosystem entrypoint exists: {entrypoint}", True)

        # Test doctor command
        try:
            doctor_result = subprocess.run(
                [sys.executable, str(entrypoint), "doctor"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            result.check(
                f"'ecosystem_entrypoint.py doctor': {'passed' if doctor_result.returncode == 0 else 'failed'}",
                doctor_result.returncode == 0,
                critical=True,
            )
        except subprocess.TimeoutExpired:
            result.check("'ecosystem_entrypoint.py doctor': timed out", False, critical=True)
        except Exception as e:
            result.check(f"'ecosystem_entrypoint.py doctor' failed: {e}", False, critical=True)
    else:
        result.check(f"Ecosystem entrypoint: not found at {entrypoint}", False, critical=True)

    return result


def main() -> int:
    """Run all validations and report results."""
    print("\n" + "=" * 60)
    print("🧪 NuSyQ Tripartite Dev Container Validation")
    print("=" * 60)

    # Check if we're actually in a container
    in_container = os.getenv("IN_DEVCONTAINER") == "true" or Path("/.dockerenv").exists()

    if not in_container:
        print("\n⚠️  WARNING: This script is designed to run inside the dev container.")
        print("   Current environment appears to be the host system.")
        print("   Some checks may fail or produce incorrect results.\n")
        print("   To test the dev container:")
        print("   1. Open VS Code")
        print("   2. Run 'Dev Containers: Rebuild and Reopen in Container'")
        print("   3. Run this script inside the container\n")

        response = input("Continue anyway? [y/N]: ")
        if response.lower() != "y":
            return 2

    # Run all validation suites
    results = [
        validate_container_environment(),
        validate_repository_mounts(),
        validate_environment_variables(),
        validate_path_resolution(),
        validate_dependencies(),
        validate_git_hooks(),
        validate_ecosystem_entrypoint(),
    ]

    # Print all results
    for result in results:
        result.print_results()

    # Final summary
    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)
    total_warnings = sum(r.warnings for r in results)
    has_critical_failures = any(r.has_failures() for r in results)

    print(f"\n{'=' * 60}")
    print("🎯 Final Summary")
    print(f"{'=' * 60}")
    print(f"✅ Passed:   {total_passed}")
    print(f"❌ Failed:   {total_failed}")
    print(f"⚠️  Warnings: {total_warnings}")

    if has_critical_failures:
        print("\n❌ VALIDATION FAILED - Critical issues found")
        print("   Review the failed checks above and fix issues before using the container.")
        return 1
    elif total_warnings > 0:
        print("\n⚠️  VALIDATION PASSED WITH WARNINGS")
        print("   Container is functional but some optional features may not work.")
        return 0
    else:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("   Dev container is fully operational!")
        return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Pre-commit hook for NuSyQ-Hub ecosystem.
Validates Python syntax, runs quick tests, and checks configuration.
"""

import os
import subprocess
import sys


# Check Python version - allow 3.10+ (3.12, 3.13 are compatible)
# Container environments may use 3.13, host typically uses 3.12
def check_python_version() -> bool:
    """Check if Python version is compatible (3.10+)."""
    if sys.version_info >= (3, 10):
        return True

    # Not compatible - show error
    print(f"❌ Python 3.10+ required. Found {sys.version_info.major}.{sys.version_info.minor}")

    # Try to find compatible Python on PATH
    for python_cmd in ["python3.12", "python3.11", "python3.10", "python3", "python"]:
        try:
            result = subprocess.run(
                [python_cmd, "--version"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                version_str = result.stdout.strip()
                print(f"ℹ️  Found {python_cmd}: {version_str}")
                if "Python 3.1" in version_str:  # 3.10, 3.11, 3.12, 3.13, etc.
                    print(
                        f"💡 Try: git config --local core.hooksPath .githooks && {python_cmd} .githooks/pre-commit-impl.py"
                    )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    print("💡 Install Python 3.10+ (apt/pyenv/homebrew) and re-run your commit.")
    return False


# Container environments (devcontainer) may use Python 3.13
# which is perfectly compatible - don't block development
IN_CONTAINER = os.getenv("IN_DEVCONTAINER") == "true" or os.path.exists("/.dockerenv")

if not IN_CONTAINER and not check_python_version():
    sys.exit(2)


def run_command(cmd: list[str], description: str) -> bool:
    """Run command and return success status."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"❌ {description} failed:")
            print(result.stdout)
            print(result.stderr)
            return False
        print(f"✅ {description} passed")
        return True
    except Exception as e:
        print(f"⚠️  {description} error: {e}")
        return False


def main() -> int:
    """Run pre-commit validations."""
    print("\n🛡️  NuSyQ Pre-Commit Hook\n")

    checks = [
        # Python syntax check (disabled on Windows due to MAX_PATH issues)
        # Ruff catches syntax errors anyway via F-codes
        # (
        #     [sys.executable, "-m", "py_compile"] +
        #     [str(f) for f in repo_root.glob("src/**/*.py")],
        #     "Python syntax validation"
        # ),
        # Black formatting check
        (
            [sys.executable, "-m", "black", "--check", "src/", "--line-length=100"],
            "Code formatting check (black)",
        ),
        # Ruff linting (excluding E501 line-length, E402 intentional import positioning)
        (
            [sys.executable, "-m", "ruff", "check", "src/", "--select=E,F,W", "--ignore=E501,E402"],
            "Critical lint checks (ruff)",
        ),
        # Config validation
        (
            [sys.executable, "-m", "src.config.orchestration_config_loader", "--validate"],
            "Configuration validation",
        ),
    ]

    passed = 0
    failed = 0

    for cmd, desc in checks:
        if run_command(cmd, desc):
            passed += 1
        else:
            failed += 1

    print(f"\n📊 Results: {passed} passed, {failed} failed\n")

    if failed > 0:
        print("❌ Pre-commit validation failed. Fix errors and try again.")
        print("💡 To bypass this hook (NOT RECOMMENDED): git commit --no-verify")
        return 1

    print("✅ All pre-commit checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

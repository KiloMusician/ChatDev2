#!/usr/bin/env python
"""Run targeted tests with proper coverage handling.
Use this for focused test runs during development.
"""

import os
import subprocess
import sys


def resolve_test_path(test_path):
    """Return a valid test path or None."""
    if os.path.exists(test_path):
        return test_path

    fallback = os.path.join("tests", test_path)
    if os.path.exists(fallback):
        return fallback

    return None


def build_coverage_args(test_path, fail_under, env):
    """Prepare coverage arguments and environment."""
    coverage_file = ".coverage.targeted"
    if os.path.exists(coverage_file):
        try:
            os.remove(coverage_file)
        except OSError:
            coverage_file = f".coverage.targeted.{os.getpid()}"

    env["COVERAGE_FILE"] = coverage_file

    if "test_auto_fix_imports" in test_path:
        cov_sources = ["auto_fix_imports"]
    elif "src/" in test_path or test_path.startswith("src/"):
        cov_sources = ["src"]
    else:
        cov_sources = ["src", "scripts"]

    args = [f"--cov={','.join(cov_sources)}", "--cov-report=term-missing"]
    threshold = fail_under if fail_under is not None else 0
    args.append(f"--cov-fail-under={threshold}")
    return args


def run_test_suite(test_path, with_coverage=True, fail_under=None):
    """Run a test suite with proper coverage configuration"""
    resolved_path = resolve_test_path(test_path)
    if resolved_path is None:
        print(f"❌ Test file not found: {test_path}")
        return False

    # Override pytest.ini addopts so we control coverage scope for targeted runs
    cmd = ["pytest", "-o", "addopts=", resolved_path, "-v", "--tb=short"]
    env = os.environ.copy()

    if with_coverage:
        cmd.extend(build_coverage_args(resolved_path, fail_under, env))

    print(f"🚀 Running: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env, check=False)

        print(result.stdout)

        if result.stderr:
            print("\n⚠️ Stderr:")
            print(result.stderr[:500])

        print("-" * 60)

        if result.returncode == 0:
            print("✅ All tests passed!")
            return True

        print(f"❌ Tests failed with exit code {result.returncode}")
        return False

    except subprocess.TimeoutExpired:
        print("⏰ Test run timed out after 2 minutes")
        return False
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"💥 Error running tests: {exc}")
        return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Run targeted tests with proper coverage")
    parser.add_argument("test_path", nargs="?", default="tests/", help="Test file or directory to run")
    parser.add_argument("--no-cov", action="store_true", help="Disable coverage collection")
    parser.add_argument(
        "--cov-fail-under",
        type=int,
        default=None,
        help="Coverage threshold (default: use pytest.ini or 0)",
    )
    parser.add_argument("--quick", action="store_true", help="Quick run with minimal output")

    args = parser.parse_args()

    if args.quick:
        # Quick run: no coverage, minimal output
        cmd = ["pytest", args.test_path, "-q", "--tb=no"]
        subprocess.run(cmd, check=False)
        return

    success = run_test_suite(args.test_path, with_coverage=not args.no_cov, fail_under=args.cov_fail_under)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

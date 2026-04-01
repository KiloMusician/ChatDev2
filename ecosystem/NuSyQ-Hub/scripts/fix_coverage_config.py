import configparser
import os


def fix_coverage_include_exclude():
    """Fix the .coveragerc to include relevant files and exclude properly"""
    config_path = ".coveragerc"

    if not os.path.exists(config_path):
        print("❌ .coveragerc not found")
        return

    # Backup original
    with open(config_path) as f:
        original = f.read()

    # Create a more sensible config that:
    # 1. Includes all Python files in src/ and scripts/
    # 2. Properly excludes test files, __pycache__, etc.
    new_config = r"""[run]
branch = True
source =
    src
    scripts
omit =
    */test_*
    */tests/*
    */__pycache__/*
    */venv/*
    */.*/*
    */.pytest_cache/*
    setup.py
    */_version.py
    */conftest.py

[report]
# Regexes for lines to exclude from consideration
exclude_lines =
    # Have to re-enable the standard pragma
    pragma: no cover

    # Don't complain about missing debug-only code:
    def __repr__
    if self.debug

    # Don't complain if tests don't hit defensive assertion code:
    raise AssertionError
    raise NotImplementedError

    # Don't complain if non-runnable code isn't run:
    if 0:
    if __name__ == .__main__.

    # Don't complain about abstract methods:
    @(abc\.)?abstractmethod

ignore_errors = True

[html]
directory = coverage_html_report
title = Coverage Report
"""

    with open(config_path, "w") as f:
        f.write(new_config)

    print("✅ Updated .coveragerc to include src/ and scripts/")
    print("   Removed restrictive include patterns")
    return original


def fix_pytest_cov_config():
    """Ensure pytest.ini has proper cov configuration"""
    ini_path = "pytest.ini"

    if not os.path.exists(ini_path):
        print("❌ pytest.ini not found")
        return

    config = configparser.ConfigParser()
    config.read(ini_path)

    # Ensure pytest-cov configuration is correct
    if not config.has_section("tool:pytest"):
        config["tool:pytest"] = {}

    config["tool:pytest"]["testpaths"] = "tests"
    config["tool:pytest"]["python_files"] = "test_*.py"
    config["tool:pytest"]["python_classes"] = "Test*"
    config["tool:pytest"]["python_functions"] = "test_*"
    config["tool:pytest"]["addopts"] = "--cov=src --cov=scripts --cov-report=term-missing --cov-fail-under=70"

    with open(ini_path, "w") as f:
        config.write(f)

    print("✅ Updated pytest.ini with proper cov configuration")


if __name__ == "__main__":
    print("🔧 Fixing coverage configuration...")

    # Backup original .coveragerc
    original_config = fix_coverage_include_exclude()

    # Update pytest.ini
    fix_pytest_cov_config()

    # Test the fix
    print("\n🧪 Testing coverage collection...")
    import subprocess

    # Run a test with coverage
    result = subprocess.run(
        ["pytest", "tests/test_auto_fix_imports.py", "-v", "--cov=scripts"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    print("Coverage output:")
    if "No data was collected" in result.stderr:
        print("❌ Still no data collected")
        # Restore original config
        if original_config:
            with open(".coveragerc", "w") as f:
                f.write(original_config)
            print("Restored original .coveragerc")
    else:
        print("✅ Coverage data collected successfully")
        # Show coverage summary
        for line in result.stdout.split("\n"):
            if "TOTAL" in line or "coverage" in line.lower():
                print(line)

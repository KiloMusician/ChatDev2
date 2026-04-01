#!/usr/bin/env python
"""Run tests with clean coverage collection, ignoring pytest.ini addopts.
Use this for focused test runs that need accurate coverage metrics.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def create_clean_pytest_config(test_paths, cov_sources=None, fail_under=0, output_dir=None):
    """Create a clean pytest config file without global addopts interference."""
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="clean_cov_")

    config_content = """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
# Minimal addopts - override the global ones
addopts = --tb=short
"""
    config_path = Path(output_dir) / "pytest.ini"
    config_path.write_text(config_content, encoding="utf-8")

    if cov_sources:
        if Path(".coveragerc").exists():
            cov_config = Path(".coveragerc").read_text(encoding="utf-8")
            cov_config = cov_config.replace("*/test_*.py", "# */test_*.py")
            cov_config = cov_config.replace("*/tests/*", "# */tests/*")
        else:
            cov_config = r"""[run]
branch = True
source =
    src
    scripts
omit =
    */__pycache__/*
    */.pytest_cache/*
    */.*/*
    */venv/*
    */virtualenvs/*
    */.tox/*
    */build/*
    */dist/*
    */node_modules/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__
    @(abc\.)?abstractmethod

ignore_errors = True
"""
        cov_path = Path(output_dir) / ".coveragerc"
        cov_path.write_text(cov_config, encoding="utf-8")

    return output_dir, str(config_path)


def run_clean_coverage(
    test_paths,
    cov_sources=None,
    fail_under=0,
    report="term",
    verbose=False,
    keep_config=False,
    quiet=True,
):
    """Run tests with a clean coverage environment."""
    print("🚀 Running clean coverage test suite")
    print(f"   Tests: {test_paths}")
    if cov_sources:
        print(f"   Coverage sources: {cov_sources}")
        print(f"   Fail under: {fail_under}%")
    print("-" * 60)

    config_dir, config_file = create_clean_pytest_config(test_paths, cov_sources, fail_under)

    try:
        cmd = [sys.executable, "-m", "pytest"]

        if isinstance(test_paths, str):
            cmd.append(test_paths)
        else:
            cmd.extend(test_paths)

        cmd.extend(["-c", config_file])

        if cov_sources:
            cmd.extend(
                [
                    f"--cov={cov_sources}",
                    f"--cov-report={report}",
                    f"--cov-fail-under={fail_under}",
                ]
            )

        if verbose:
            cmd.append("-v")
        elif quiet:
            cmd.extend(["-q", "--tb=no"])
        else:
            cmd.append("--tb=no")

        cmd.append("-s")

        print(f"Command: {' '.join(cmd)}")
        print("-" * 60)

        env = os.environ.copy()
        env["PYTEST_ADDOPTS"] = ""

        result = subprocess.run(
            cmd,
            env=env,
            text=True,
            timeout=300,
        )
        return result.returncode == 0

    finally:
        if not keep_config:
            shutil.rmtree(config_dir, ignore_errors=True)


def check_file_encoding_issue():
    """Check why check_file_encoding.py causes parse warnings."""
    file_path = Path("scripts/check_file_encoding.py")

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    print(f"\n🔍 Investigating {file_path}...")

    try:
        raw_content = file_path.read_bytes()
        import chardet

        detection = chardet.detect(raw_content)
        print(f"   Detected encoding: {detection['encoding']} (confidence: {detection['confidence']:.2f})")

        try:
            content = raw_content.decode("utf-8")
            compile(content, str(file_path), "exec")
            print("   ✅ File compiles successfully")
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {e}")
            lines = content.split("\n")
            if e.lineno:
                start = max(0, e.lineno - 3)
                end = min(len(lines), e.lineno + 2)
                print(f"   Context (lines {start + 1}-{end}):")
                for i in range(start, end):
                    marker = ">>>" if i == e.lineno - 1 else "   "
                    print(f"   {i + 1:3}{marker} {lines[i]}")
        except UnicodeDecodeError:
            print("   ❌ UTF-8 decode error")

    except Exception as e:
        print(f"   ⚠️  Error checking file: {e}")

    stat = file_path.stat()
    print(f"   File size: {stat.st_size} bytes")

    try:
        content = file_path.read_text(encoding="utf-8")
        non_ascii = [(i + 1, c) for i, c in enumerate(content) if ord(c) > 127]
        if non_ascii:
            print(f"   ⚠️  Non-ASCII characters found: {len(non_ascii)}")
            for line_num, char in non_ascii[:5]:
                print(f"      Line {line_num}: {char!r} (U+{ord(char):04X})")
        if content.startswith("\ufeff"):
            print("   ⚠️  File starts with UTF-8 BOM")
    except Exception as e:
        print(f"   ⚠️  Error reading file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Run tests with a clean coverage environment")
    parser.add_argument("test_paths", nargs="+", help="Test file(s) or directory(s) to run")
    parser.add_argument("--cov", default=None, help="Coverage sources (comma-separated)")
    parser.add_argument("--cov-fail-under", type=int, default=0, help="Coverage threshold (default: 0)")
    parser.add_argument(
        "--cov-report",
        default="term",
        choices=["term", "term-missing", "html", "xml", "json"],
        help="Coverage report type",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Alias for the default quiet execution (added for compatibility).",
    )
    parser.add_argument(
        "--no-quiet",
        action="store_true",
        help="Run without the default pytest -q/--tb=no flags.",
    )
    parser.add_argument("--keep-config", action="store_true", help="Keep temporary config files for inspection")
    parser.add_argument("--check-encoding", action="store_true", help="Check file encoding issues before running")

    args = parser.parse_args()

    if args.check_encoding:
        check_file_encoding_issue()
        print("\n" + "-" * 60)

    success = run_clean_coverage(
        test_paths=args.test_paths,
        cov_sources=args.cov,
        fail_under=args.cov_fail_under,
        report=args.cov_report,
        verbose=args.verbose,
        keep_config=args.keep_config,
        quiet=not args.no_quiet,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

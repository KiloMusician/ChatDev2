#!/usr/bin/env python3
"""Run pytest programmatically with a safe environment for this repo.

This script ensures 'src' is on sys.path so tests can import local modules.
It also avoids honoring project-level pytest addopts (coverage args) which
can break when test runner invocation differs. Use this for CI-local runs.
"""

import os
import sys
import tempfile
from pathlib import Path


def main():
    # Ensure 'src' is importable
    repo_root = Path(__file__).resolve().parent
    src_path = str(repo_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Prevent pytest from picking up project-level addopts (coverage flags)
    os.environ.pop("PYTEST_ADDOPTS", None)

    # Ensure pytest plugins required by the test-suite are installed. Tests use async
    # fixtures and the 'benchmark' fixture; install small plugins if missing so
    # test execution is consistent in CI-local runs.
    # Detect whether pytest plugins are installed without importing them
    import importlib.util

    import pytest

    missing_pkgs = []
    if importlib.util.find_spec("pytest_asyncio") is None:
        missing_pkgs.append("pytest-asyncio")
    if importlib.util.find_spec("pytest_benchmark") is None:
        missing_pkgs.append("pytest-benchmark")

    if missing_pkgs:
        import subprocess

        print(f"Installing missing test plugins: {missing_pkgs}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_pkgs])

    # Create a minimal temporary pytest.ini to avoid project-level addopts
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as tf:
        tf.write("[pytest]\n")
        tmp_ini = tf.name

    # Force-load commonly used pytest plugins to avoid plugin-autoload issues
    args = [
        "-p",
        "pytest_asyncio",
        "-p",
        "pytest_benchmark",
        "-c",
        tmp_ini,
        "-q",
        "tests",
    ]
    print(f"Running pytest with args: {args} and PYTHONPATH includes: {sys.path[0]}")
    try:
        rc = pytest.main(args)
    finally:
        try:
            os.remove(tmp_ini)
        except (OSError, FileNotFoundError):
            pass

    # Propagate pytest return code
    raise SystemExit(rc)


if __name__ == "__main__":
    main()

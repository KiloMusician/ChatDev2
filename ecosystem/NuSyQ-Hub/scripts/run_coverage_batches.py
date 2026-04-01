#!/usr/bin/env python3
"""Run pytest coverage in batches so long suites don’t time out."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def gather_tests(base: Path) -> list[str]:
    """Collect test files under `base`."""
    tests = sorted(str(p) for p in base.rglob("test_*.py") if p.is_file())
    return tests


def chunk_tests(tests: Sequence[str], chunk_size: int) -> list[list[str]]:
    """Split tests into equal-sized chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    return [tests[i : i + chunk_size] for i in range(0, len(tests), chunk_size)]


def run_chunk(cmd: list[str], chunk_id: int, coverage_file: Path, timeout: int) -> tuple[bool, str]:
    """Run pytest coverage for one chunk."""
    env = os.environ.copy()
    env["COVERAGE_FILE"] = str(coverage_file)
    print(f"🔹 Chunk {chunk_id}: running {len(cmd) - 4} tests")
    try:
        result = subprocess.run(cmd, env=env, text=True, capture_output=True, timeout=timeout)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        success = result.returncode == 0
    except subprocess.TimeoutExpired as exc:
        print(f"⚠️ Chunk {chunk_id} timed out after {timeout}s")
        print(exc.stdout or "")
        success = False
    return success, str(coverage_file)


def combine_coverage(data_dir: Path, combined_file: Path) -> None:
    """Combine coverage data into one report."""
    env = os.environ.copy()
    env["COVERAGE_FILE"] = str(combined_file)
    coverage_files = sorted(data_dir.glob(".coverage_chunk_*"))
    if not coverage_files:
        raise FileNotFoundError("No chunk coverage data found.")
    args = ["coverage", "combine", str(data_dir)]
    subprocess.run(args, check=True, env=env)


def report_coverage(combined_file: Path) -> None:
    """Generate a coverage report using the combined data."""
    env = os.environ.copy()
    env["COVERAGE_FILE"] = str(combined_file)
    subprocess.run(["coverage", "report", "-m"], check=True, env=env)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run coverage in manageable batches.")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=120,
        help="Number of tests to run per chunk (default: 120)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout (seconds) per chunk run (default: 600)",
    )
    parser.add_argument(
        "--tests-dir",
        type=str,
        default="tests",
        help="Directory rooted at the test suite",
    )
    parser.add_argument(
        "--fast-only",
        action="store_true",
        help="Only run the fast subset (start_nusyq fast tests)",
    )
    args = parser.parse_args()

    tests_root = Path(args.tests_dir)
    if not tests_root.exists():
        raise SystemExit(f"Tests directory {tests_root} does not exist.")

    if args.fast_only:
        chunks = [
            [
                "tests/test_start_nusyq.py::test_hygiene_runs",
                "tests/test_chatdev_integration.py::test_chatdev_spawn_mocked",
                "tests/test_agent_task_router.py::TestOllamaRouting::test_ollama_routing_success",
            ]
        ]
    else:
        all_tests = gather_tests(tests_root)
        if not all_tests:
            raise SystemExit("No tests found.")
        chunks = chunk_tests(all_tests, args.chunk_size)

    coverage_dir = Path("coverage_batches")
    coverage_dir.mkdir(exist_ok=True)

    successes = []
    for idx, chunk in enumerate(chunks, 1):
        coverage_file = coverage_dir / f".coverage_chunk_{idx}"
        cmd = ["coverage", "run", "-m", "pytest", "--capture=no", *chunk]
        success, _ = run_chunk(cmd, idx, coverage_file, args.timeout)
        successes.append(success)

    combined_file = coverage_dir / "combined.coverage"
    try:
        combine_coverage(coverage_dir, combined_file)
        report_coverage(combined_file)
        print("✅ Combined coverage report generated.")
    except Exception as exc:
        print(f"⚠️ Coverage combine/report failed: {exc}")
    print(f"✅ Chunks succeeded: {sum(successes)}/{len(successes)}")


if __name__ == "__main__":
    main()

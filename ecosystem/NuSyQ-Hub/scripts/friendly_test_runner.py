#!/usr/bin/env python3
"""Friendly test runner with modes (quick/full/targeted/smart/smoke/ci).

Usage examples:
    python scripts/friendly_test_runner.py                         # default full pytest
    python scripts/friendly_test_runner.py --mode quick -q tests/test_quantum_import.py
    python scripts/friendly_test_runner.py --mode smoke src/foo.py
    python scripts/friendly_test_runner.py --mode ci

Notes:
- `--mode quick` mirrors `scripts/run_tests_quick.py` (coverage-free, override addopts).
- `--mode smoke` uses `src/diagnostics/smoke_test_runner.py` for AST/import/syntax checks.
- `--mode smart` delegates to `scripts/run_tests_intelligent.py` if present.
- `--mode ci` delegates to `scripts/lint_test_check.py`.
"""

import argparse
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODES = ["full", "quick", "targeted", "smart", "smoke", "ci"]


def _run_command(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str, float]:
    start_time = time.monotonic()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        check=False,
    )
    duration = time.monotonic() - start_time
    return proc.returncode, proc.stdout, duration


def _run_in_wsl(cmd: list[str]) -> tuple[int, str, list[str], float]:
    start_time = time.monotonic()
    script_path = ROOT / "scripts" / "wsl_test_runner.ps1"
    if not script_path.exists():
        out = "WSL backend requested but wsl_test_runner.ps1 not found"
        return 1, out, [str(script_path)], time.monotonic() - start_time

    command_str = " ".join(shlex.quote(c) for c in cmd)
    pwsh_cmd = [
        "pwsh",
        "-NoProfile",
        "-File",
        str(script_path),
        "-Workdir",
        str(ROOT),
        "-Command",
        command_str,
    ]

    try:
        proc = subprocess.run(pwsh_cmd, capture_output=True, text=True, check=False)
        duration = time.monotonic() - start_time
        out = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
        return proc.returncode, out, pwsh_cmd, duration
    except FileNotFoundError:
        duration = time.monotonic() - start_time
        return 1, "PowerShell (pwsh) not found for WSL backend", pwsh_cmd, duration


def run_pytest(pytest_args: list[str], mode: str, fail_fast: bool, max_fail: int | None, backend: str):
    env = None

    cmd: list[str]
    if mode == "quick":
        env = os.environ.copy()
        env.pop("PYTEST_ADDOPTS", None)
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--override-ini=addopts=",
            "-p",
            "no:cov",
            *pytest_args,
        ]
    else:
        cmd = [sys.executable, "-m", "pytest", *pytest_args]

    if fail_fast:
        cmd.append("-x")
    if max_fail is not None:
        cmd.extend(["--maxfail", str(max_fail)])

    print("Running:", " ".join(shlex.quote(c) for c in cmd))

    if backend == "wsl":
        rc, out, wsl_cmd, duration = _run_in_wsl(cmd)
        return rc, out, wsl_cmd, duration

    rc, out, duration = _run_command(cmd, env=env)
    return rc, out, cmd, duration


def analyze_output(out: str):
    """Look for known patterns and create a short diagnostic."""
    diag_lines = []
    # Coverage parse warning
    m_parse = re.search(r"Couldn't parse Python file '([^']+)' \(couldnt-parse\)", out)
    if m_parse:
        path = Path(m_parse.group(1))
        diag_lines.append("Coverage parse warning: coverage could not parse a Python file.")
        diag_lines.append(f"  File: {path}")
        diag_lines.append("  Likely causes: Syntax error, invalid bytes (null/BOM), or unmatched f-strings/quotes.")
        diag_lines.append("  Quick checks:")
        diag_lines.append(f"    python -m py_compile {path}")
        diag_lines.append(f"    python scripts/check_file_encoding.py {path}")
        diag_lines.append(
            "  If file intentionally contains non-Python content, add it to coverage omit in pytest.ini or adjust package layout."
        )
    # SyntaxError traceback
    m_syntax = re.search(r"File \"([^\"]+)\", line (\d+).*?SyntaxError: (.+)", out, re.S)
    if m_syntax:
        fpath = Path(m_syntax.group(1))
        line = int(m_syntax.group(2))
        err = m_syntax.group(3).strip()
        diag_lines.append("SyntaxError detected:")
        diag_lines.append(f"  File: {fpath}, line {line}")
        diag_lines.append(f"  Error: {err}")
        diag_lines.append(
            "  Suggested action: open file at the location and fix unmatched quotes/f-strings or invalid syntax."
        )
    # Coverage fail-under
    m_cov = re.search(r"Total coverage: (\d+(?:\.\d+)?)%", out)
    if m_cov:
        pct = m_cov.group(1)
        diag_lines.append("Coverage threshold not met:")
        diag_lines.append(f"  Total coverage reported: {pct}%")
        diag_lines.append("  Why: only a small subset of tests ran (smoke tests) vs the entire codebase.")
        diag_lines.append("  Quick local actions:")
        diag_lines.append(
            "    - Run `python scripts/run_tests_quick.py -q tests/<your_test>.py` to iterate locally without coverage enforcement."
        )
        diag_lines.append("    - Add import-only smoke tests for large modules to ensure they at least import.")
        diag_lines.append("    - Use coverage omit rules for third-party or generated files if appropriate.")
    # Generic failure
    if not diag_lines:
        if "ERROR: Coverage failure" in out or "FAIL Required test coverage" in out:
            diag_lines.append(
                "Coverage enforcement caused the run to fail. Consider running quick mode for iteration or adding more tests."
            )
        elif "Traceback (most recent call last):" in out:
            diag_lines.append("An exception occurred during tests. Inspect the traceback above for details.")
        else:
            diag_lines.append("No specific patterns matched. See the pytest output above for details.")
    return diag_lines


def print_diagnostic(diag_lines):
    print("\n" + "=" * 60)
    print("FRIENDLY DIAGNOSTIC:")
    for line in diag_lines:
        print(line)
    print("=" * 60 + "\n")


def _record_run(cmd: list[str], rc: int, duration: float, source: str) -> None:
    try:
        from src.utils.terminal_output import to_tests
        from src.utils.test_run_registry import record_test_run

        summary = record_test_run(
            command=cmd,
            cwd=str(ROOT),
            status="pass" if rc == 0 else "fail",
            exit_code=rc,
            duration_seconds=duration,
            source=source,
        )
        duplicate_note = ""
        if summary.run_count_window > 1:
            duplicate_note = f" (run {summary.run_count_window}x in window)"
        to_tests(
            f"Friendly tests {summary.run_id} status={summary.status} "
            f"duration={summary.duration_seconds}s{duplicate_note}"
        )
    except (ImportError, AttributeError, OSError):
        return


def _expand_smoke_targets(targets: list[str]) -> list[Path]:
    paths: list[Path] = []
    for target in targets:
        p = Path(target)
        if "*" in target or p.is_dir():
            base = p if p.is_dir() else p.parent
            pattern = p.name if "*" in target else "*.py"
            paths.extend(sorted(base.glob(pattern)))
        elif p.exists():
            paths.append(p)
    return paths


def run_smoke(targets: list[str], timeout: int, backend: str) -> tuple[int, str, list[str], float]:
    start_time = time.monotonic()
    from src.diagnostics.smoke_test_runner import SmokeTestRunner

    runner = SmokeTestRunner(timeout_seconds=timeout)
    py_files = _expand_smoke_targets(targets)
    if not py_files:
        return 1, "No smoke targets found", [], time.monotonic() - start_time

    if backend == "wsl":
        warning = "WSL backend not supported for smoke mode; running locally."
        print(f"⚠️  {warning}")

    failures: list[str] = []
    for file_path in py_files:
        results = runner.run_all_tests(file_path)
        if not all(results.values()):
            failures.append(str(file_path))

    duration = time.monotonic() - start_time
    if failures:
        out = "\n".join(["Smoke failures:", *failures])
        return 1, out, [str(f) for f in py_files], duration
    return 0, "Smoke tests passed", [str(f) for f in py_files], duration


def _delegate_script(script_relpath: str, extra_args: list[str]) -> tuple[int, str, list[str], float]:
    start_time = time.monotonic()
    script_path = ROOT / script_relpath
    if not script_path.exists():
        return 1, f"Delegate script not found: {script_relpath}", [], 0.0
    cmd = [sys.executable, str(script_path), *extra_args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    duration = time.monotonic() - start_time
    out = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, out, cmd, duration


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=MODES, default="full", help="Select runner mode")
    p.add_argument("--backend", choices=["local", "wsl"], default="local")
    p.add_argument("--fail-fast", action="store_true", help="Stop on first failure (-x)")
    p.add_argument("--max-fail", type=int, help="Max failures before stopping")
    p.add_argument("--timeout", type=int, default=120, help="Timeout seconds for smoke mode")
    p.add_argument("--list-modes", action="store_true", help="List available modes and exit")
    ns, extra = p.parse_known_args(argv)

    if ns.list_modes:
        print("Available modes:", ", ".join(MODES))
        return 0

    args = list(extra)

    if ns.mode == "smoke":
        if not args:
            args = ["src"]
        rc, out, cmd, duration = run_smoke(args, timeout=ns.timeout, backend=ns.backend)
    elif ns.mode == "targeted":
        rc, out, cmd, duration = _delegate_script("scripts/run_targeted_tests.py", args)
    elif ns.mode == "smart":
        rc, out, cmd, duration = _delegate_script("scripts/run_tests_intelligent.py", args)
    elif ns.mode == "ci":
        rc, out, cmd, duration = _delegate_script("scripts/lint_test_check.py", args)
    else:
        # Default test selection
        if not args and ns.mode == "quick":
            args = ["-q", "tests/test_quantum_import.py"]
        rc, out, cmd, duration = run_pytest(
            args,
            mode=ns.mode,
            fail_fast=ns.fail_fast,
            max_fail=ns.max_fail,
            backend=ns.backend,
        )

    print(out)

    diag = analyze_output(out)
    print_diagnostic(diag)

    _record_run(cmd, rc, duration, source=f"friendly_test_runner:{ns.mode}")

    m_parse = re.search(r"Couldn't parse Python file '([^']+)' \(couldnt-parse\)", out)
    if m_parse:
        path = Path(m_parse.group(1))
        print("Running encoding check on the problematic file...")
        check_cmd = [sys.executable, str(ROOT / "scripts" / "check_file_encoding.py"), str(path)]
        proc = subprocess.run(check_cmd, check=False)
        print(f"\n(checker exit code: {proc.returncode})")

    if "FAIL Required test coverage" in out or "ERROR: Coverage failure" in out:
        print("Tip: to iterate quickly without failing on coverage, run:")
        print("  python scripts/run_tests_quick.py -q tests/test_quantum_import.py")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())

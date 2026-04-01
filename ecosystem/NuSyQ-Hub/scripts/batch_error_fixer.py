#!/usr/bin/env python3
"""🔧 Consolidated Error Fixer

Consolidates multiple error-fixing flows into one entry point.

Modes:
  fast      - Black + Ruff --fix + isort + autoflake
  boss      - Crush trivial/simple targets (<=5 errors/file) via Ruff
  ecosystem - F401/F841 specialists via AutonomousErrorFixer (if available)
  syntax    - Quick compile-based syntax scan (top 50 files) and report

Options:
  --json            Emit machine-readable summary
  --report PATH     Save JSON report
  --max-files N     Limit files in boss mode (default: 50)

This consolidates: autonomous_error_fixer, boss_rush_error_crusher,
chug_mode_error_fixer, prioritized_error_scanner into one canonical tool.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def run_command(cmd: list[str], cwd: Path | None = None, timeout: int = 60) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"Timeout after {timeout}s"
    except FileNotFoundError as exc:
        return 1, "", f"Command not found: {exc}"
    except Exception as exc:
        return 1, "", str(exc)


def _count_ruff_errors(stdout: str) -> int:
    return len([line for line in stdout.splitlines() if line.strip() and ":" in line])


def baseline_errors() -> int:
    """Return baseline error count using ruff check (fast, no JSON parsing)."""
    code, out, _ = run_command([sys.executable, "-m", "ruff", "check", "src"], cwd=ROOT, timeout=90)
    if code != 0 and not out:
        return 0
    return _count_ruff_errors(out)


def fix_formatting() -> dict[str, Any]:
    print("\n📝 Running black formatter...")
    code, _, err = run_command(
        [sys.executable, "-m", "black", "src", "--line-length", "100", "--quiet"],
        cwd=ROOT,
        timeout=120,
    )
    return {"black_ok": code == 0, "black_err": err or None}


def fix_linting() -> dict[str, Any]:
    print("\n🔍 Running ruff auto-fix...")
    code, out, err = run_command([sys.executable, "-m", "ruff", "check", "src", "--fix"], cwd=ROOT, timeout=180)
    return {"ruff_ok": code == 0, "ruff_fixed": out.count("Fixed"), "ruff_err": err or None}


def fix_imports() -> dict[str, Any]:
    print("\n📦 Running isort...")
    code, _, err = run_command([sys.executable, "-m", "isort", "src", "--quiet"], cwd=ROOT, timeout=120)
    return {"isort_ok": code == 0, "isort_err": err or None}


def remove_unused_imports() -> dict[str, Any]:
    print("\n🧹 Removing unused imports (autoflake)...")
    code, _, err = run_command(
        [
            sys.executable,
            "-m",
            "autoflake",
            "--in-place",
            "--remove-all-unused-imports",
            "--recursive",
            "src",
        ],
        cwd=ROOT,
        timeout=180,
    )
    return {"autoflake_ok": code == 0, "autoflake_err": err or None}


def mode_fast() -> dict[str, Any]:
    start = time.time()
    before = baseline_errors()

    results: dict[str, Any] = {"mode": "fast", "before": before}
    results.update(fix_formatting())
    results.update(fix_linting())
    results.update(fix_imports())
    results.update(remove_unused_imports())

    after = baseline_errors()
    results.update({"after": after, "fixed": before - after, "duration": time.time() - start})
    return results


AUTO_FIXABLE = {"F401", "F541", "I001", "E501", "W291", "W293"}


def _scan_ruff_json() -> list[dict[str, Any]]:
    code, out, err = run_command(
        [sys.executable, "-m", "ruff", "check", "src", "scripts", "tests", "--output-format=json"],
        cwd=ROOT,
        timeout=180,
    )
    if code != 0 and not out:
        print(f"⚠️ Ruff scan failed: {err}")
        return []
    try:
        return json.loads(out) if out.strip() else []
    except json.JSONDecodeError:
        return []


def mode_boss(max_files: int = 50) -> dict[str, Any]:
    start = time.time()
    records = _scan_ruff_json()
    targets = defaultdict(list)

    for rec in records:
        filename = rec.get("filename")
        code = rec.get("code", "")
        targets[filename].append(code)

    # Build target list sorted by error count
    target_list = []
    for fname, codes in targets.items():
        count = len(codes)
        auto_fixable = all(c in AUTO_FIXABLE for c in codes)
        if count <= 3 and auto_fixable:
            complexity = "trivial"
        elif count <= 5:
            complexity = "simple"
        else:
            complexity = "skip"

        target_list.append({"file": fname, "count": count, "codes": list(set(codes)), "complexity": complexity})

    target_list = [t for t in target_list if t["complexity"] != "skip"]
    target_list.sort(key=lambda t: (0 if t["complexity"] == "trivial" else 1, t["count"]))
    target_list = target_list[:max_files]

    crushed = 0
    for target in target_list:
        cmd = [sys.executable, "-m", "ruff", "check", "--fix", str(target["file"])]
        code, _, _ = run_command(cmd, cwd=ROOT, timeout=120)
        if code == 0:
            crushed += 1

    return {
        "mode": "boss",
        "targets": len(target_list),
        "crushed": crushed,
        "duration": time.time() - start,
    }


def mode_ecosystem() -> dict[str, Any]:
    start = time.time()
    summary: dict[str, Any] = {"mode": "ecosystem"}

    def _ruff_fix(select: list[str]) -> int:
        code, out, err = run_command(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "src",
                f"--select={','.join(select)}",
                "--fix",
                "--no-cache",
            ],
            cwd=ROOT,
            timeout=180,
        )
        if code != 0:
            summary.setdefault("errors", []).append(err)
            return 0
        return out.count("Fixed")

    summary["f401_fixed"] = _ruff_fix(["F401"])
    summary["f841_fixed"] = _ruff_fix(["F841"])
    summary["duration"] = time.time() - start
    return summary


def mode_syntax(limit: int = 50) -> dict[str, Any]:
    start = time.time()
    repo_files = list((ROOT / "src").rglob("*.py"))[:limit]
    errors: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for py_file in repo_files:
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            compile(source, str(py_file), "exec")
        except SyntaxError as exc:
            errors[str(py_file)].append({"line": exc.lineno, "msg": exc.msg})
        except (OSError, ValueError):
            continue

    return {
        "mode": "syntax",
        "files_scanned": len(repo_files),
        "files_with_errors": len(errors),
        "errors": errors,
        "duration": time.time() - start,
    }


MODES: dict[str, Callable[..., dict[str, Any]]] = {
    "fast": mode_fast,
    "boss": mode_boss,
    "ecosystem": mode_ecosystem,
    "syntax": mode_syntax,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolidated error fixer")
    parser.add_argument("--mode", choices=MODES.keys(), default="fast", help="Select mode")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    parser.add_argument("--report", type=Path, help="Path to save JSON report")
    parser.add_argument("--max-files", type=int, default=50, help="Max files to process in boss mode")
    parser.add_argument("--syntax-limit", type=int, default=50, help="Files to scan in syntax mode")
    args = parser.parse_args()

    # Execute selected mode
    if args.mode == "boss":
        result = mode_boss(max_files=args.max_files)
    elif args.mode == "syntax":
        result = mode_syntax(limit=args.syntax_limit)
    elif args.mode == "ecosystem":
        result = mode_ecosystem()
    else:
        result = mode_fast()

    # Save report if requested
    if args.report:
        try:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
            result["report_saved"] = str(args.report)
        except (OSError, ValueError) as exc:
            result["report_error"] = str(exc)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 70)
        print(f"✅ MODE: {result.get('mode')}")
        for k, v in result.items():
            if k == "mode":
                continue
            print(f"  {k}: {v}")
        print("=" * 70)

    return 0 if not result.get("error") else 1


if __name__ == "__main__":
    sys.exit(main())

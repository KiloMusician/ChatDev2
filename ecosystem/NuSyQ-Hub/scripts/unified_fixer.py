#!/usr/bin/env python3
"""Unified fixer orchestrator for NuSyQ-Hub.
[ROUTE ERRORS] 🔥

This wrapper consolidates the many fix/auto_fix scripts behind a single CLI.
It **reuses existing scripts**; no behavioral changes. Modes map to legacy
commands so we can phase out duplication safely.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
PYTHON = sys.executable


@dataclass
class FixStep:
    name: str
    command: list[str]


@dataclass
class FixResult:
    name: str
    command: list[str]
    status: str
    returncode: int | None
    stdout: str | None
    stderr: str | None
    started_at: str
    finished_at: str


def build_command(script_name: str, *extra: str) -> list[str]:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Missing fixer script: {script_path}")
    return [PYTHON, str(script_path), *extra]


def plan_steps(mode: str) -> list[FixStep]:
    """Return ordered fix steps for a given mode."""
    if mode == "imports":
        scripts: list[str | tuple[str, Sequence[str]]] = [
            "auto_fix_imports.py",
            "fix_defensive_imports.py",
            "fix_future_imports.py",
        ]
    elif mode == "types":
        scripts = [
            "auto_fix_type_hints.py",
            "auto_fix_types.py",
            "fix_type_errors_batch.py",
            "unified_type_fixer.py",
        ]
    elif mode == "syntax":
        scripts = [
            "fix_bare_except.py",
            "fix_async_patterns.py",
            "fix_backticks.py",
            "fix_logging_v2.py",
        ]
    elif mode == "format":
        scripts = [
            ("fix_file_encodings.py", ["--fix"]),
            ("fix_file_encodings_nusyq.py", ["--fix"]),
        ]
    elif mode == "circular":
        scripts = [
            "fix_circular_dependencies.py",
        ]
    elif mode == "all":
        scripts = [
            "auto_fix_imports.py",
            "fix_defensive_imports.py",
            "fix_future_imports.py",
            "auto_fix_type_hints.py",
            "auto_fix_types.py",
            "fix_type_errors_batch.py",
            "unified_type_fixer.py",
            "fix_bare_except.py",
            "fix_async_patterns.py",
            "fix_backticks.py",
            "fix_logging_v2.py",
            ("fix_file_encodings.py", ["--fix"]),
            ("fix_file_encodings_nusyq.py", ["--fix"]),
            "fix_circular_dependencies.py",
        ]
    else:
        raise ValueError(f"Unknown mode: {mode}")

    steps: list[FixStep] = []
    for entry in scripts:
        if isinstance(entry, tuple):
            script_name, extra = entry[0], list(entry[1])
            cmd = build_command(script_name, *extra)
        else:
            cmd = build_command(entry)
            script_name = entry
        steps.append(FixStep(name=script_name, command=cmd))
    return steps


def run_step(step: FixStep, dry_run: bool = False, verbose: bool = False) -> FixResult:
    started = datetime.utcnow().isoformat()
    if dry_run:
        return FixResult(
            name=step.name,
            command=step.command,
            status="DRY-RUN",
            returncode=None,
            stdout=None,
            stderr=None,
            started_at=started,
            finished_at=started,
        )

    proc = subprocess.run(step.command, capture_output=True, text=True)
    finished = datetime.utcnow().isoformat()
    status = "OK" if proc.returncode == 0 else "FAIL"

    if verbose:
        print(f"\n▶ {step.name} -> {' '.join(step.command)}")
        if proc.stdout:
            print(proc.stdout.rstrip())
        if proc.stderr:
            print(proc.stderr.rstrip())

    return FixResult(
        name=step.name,
        command=step.command,
        status=status,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        started_at=started,
        finished_at=finished,
    )


def write_summary(results: Iterable[FixResult], outfile: Path) -> None:
    data = {
        "generated_at": datetime.utcnow().isoformat(),
        "results": [asdict(r) for r in results],
    }
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(json.dumps(data, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified fixer orchestrator")
    parser.add_argument(
        "--mode",
        choices=["imports", "types", "syntax", "format", "circular", "all"],
        default="imports",
        help="Fixer bundle to run",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing")
    parser.add_argument("--verbose", action="store_true", help="Print stdout/stderr from steps")
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "state" / "fixer_runs" / "latest.json",
        help="Where to write JSON summary (default: state/fixer_runs/latest.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    steps = plan_steps(args.mode)

    print(f"🛠️  Unified Fixer: mode={args.mode} dry_run={args.dry_run}")

    results = [run_step(step, dry_run=args.dry_run, verbose=args.verbose) for step in steps]

    failures = [r for r in results if r.status not in {"OK", "DRY-RUN"}]
    write_summary(results, args.summary)

    if failures:
        print(f"❌ Completed with {len(failures)} failure(s). Summary: {args.summary}")
        for fail in failures:
            print(f" - {fail.name} (rc={fail.returncode})")
        return 1

    print(f"✅ Fixer completed. Summary: {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

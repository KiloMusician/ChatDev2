#!/usr/bin/env python3
"""Unified NuSyQ activation CLI.

[ROUTE AGENTS] 🤖

Consolidates legacy activation entrypoints into a single, mode-driven launcher.
Keeps legacy scripts intact while providing a clearer surface for automation.
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
class ActivationStep:
    """Represents a single activation step to run."""

    name: str
    command: list[str]


@dataclass
class ActivationResult:
    """Result of running an activation step."""

    name: str
    command: list[str]
    status: str
    returncode: int | None
    stdout: str | None
    stderr: str | None
    started_at: str
    finished_at: str


def build_command(script_name: str, *extra: str) -> list[str]:
    """Build a python command for a script, ensuring it exists."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Missing script: {script_path}")
    return [PYTHON, str(script_path), *extra]


def plan_steps(mode: str) -> list[ActivationStep]:
    """Return ordered activation steps for a given mode."""
    if mode == "services":
        scripts = ["activate_ecosystem.py", "activate_complete_ecosystem.py"]
    elif mode == "terminals":
        scripts = ["activate_agent_terminals.py", "activate_intelligent_terminals.py"]
    elif mode == "guild":
        scripts = ["activate_guild_board.py"]
    elif mode == "agents":
        scripts = ["activate_culture_ship.py"]
    elif mode == "health-check":
        # Prefer JSON for downstream tooling
        scripts = [("integration_health_check.py", ["--mode", "full", "--format", "json"])]
    elif mode == "all":
        scripts: list[ActivationStep | tuple[str, Sequence[str]]] = [
            "activate_ecosystem.py",
            "activate_complete_ecosystem.py",
            "activate_agent_terminals.py",
            "activate_intelligent_terminals.py",
            "activate_guild_board.py",
            "activate_culture_ship.py",
            ("integration_health_check.py", ["--mode", "full", "--format", "json"]),
        ]
    else:
        raise ValueError(f"Unknown mode: {mode}")

    steps: list[ActivationStep] = []
    for item in scripts:
        if isinstance(item, tuple):
            script_name, extra = item[0], list(item[1])
            cmd = build_command(script_name, *extra)
            steps.append(ActivationStep(name=script_name, command=cmd))
        else:
            cmd = build_command(item)
            steps.append(ActivationStep(name=item, command=cmd))
    return steps


def run_step(step: ActivationStep, dry_run: bool = False, verbose: bool = False) -> ActivationResult:
    """Execute a single activation step."""
    started = datetime.utcnow().isoformat()
    if dry_run:
        return ActivationResult(
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

    return ActivationResult(
        name=step.name,
        command=step.command,
        status=status,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        started_at=started,
        finished_at=finished,
    )


def write_summary(results: Iterable[ActivationResult], outfile: Path) -> None:
    """Persist a JSON summary to disk."""
    data = {
        "generated_at": datetime.utcnow().isoformat(),
        "results": [asdict(r) for r in results],
    }
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(json.dumps(data, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified NuSyQ activation CLI")
    parser.add_argument(
        "--mode",
        choices=["all", "services", "terminals", "guild", "agents", "health-check"],
        default="all",
        help="Activation bundle to run",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing")
    parser.add_argument("--verbose", action="store_true", help="Print stdout/stderr from steps")
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "state" / "activation_runs" / "latest.json",
        help="Where to write JSON summary (default: state/activation_runs/latest.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    steps = plan_steps(args.mode)

    print(f"🧠 NuSyQ Activation: mode={args.mode} dry_run={args.dry_run}")

    results = [run_step(step, dry_run=args.dry_run, verbose=args.verbose) for step in steps]

    failures = [r for r in results if r.status not in {"OK", "DRY-RUN"}]
    write_summary(results, args.summary)

    if failures:
        print(f"❌ Completed with {len(failures)} failure(s). Summary: {args.summary}")
        for fail in failures:
            print(f" - {fail.name} (rc={fail.returncode})")
        return 1

    print(f"✅ Activation completed. Summary: {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

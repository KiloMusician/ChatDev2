#!/usr/bin/env python3
"""Minimal CI runner for local dev: runs orchestrator (DryRun), then tests, then gathers key logs.

This is intentionally conservative: orchestrator is invoked with -DryRun to avoid
making system changes. Adjust flags if you want full run.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_orchestrator_dryrun(repo_dir: Path) -> int:
    # Try to locate NuSyQ.Orchestrator.ps1 in likely workspace locations
    candidates = [
        repo_dir / "NuSyQ.Orchestrator.ps1",
        Path.home() / "NuSyQ" / "NuSyQ.Orchestrator.ps1",
        repo_dir.parent / "NuSyQ" / "NuSyQ.Orchestrator.ps1",
    ]
    orchestrator = None
    for c in candidates:
        if c.exists():
            orchestrator = c
            break

    # As a fallback, do a shallow walk up to 3 levels searching for the file
    if orchestrator is None:
        for root, _dirs, files in os.walk(repo_dir.parent, topdown=True):
            if "NuSyQ.Orchestrator.ps1" in files:
                orchestrator = Path(root) / "NuSyQ.Orchestrator.ps1"
                break

    if orchestrator is None:
        print(
            "Could not locate NuSyQ.Orchestrator.ps1 in common locations. Skipping orchestrator step."
        )
        return 0

    cmd = [
        "pwsh",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(orchestrator),
        "-DryRun",
    ]
    print("Running orchestrator (DryRun):", " ".join(cmd))
    return subprocess.call(cmd)


def run_tests(repo_dir: Path) -> int:
    cmd = [sys.executable, str(repo_dir / "run_tests.py")]
    print("Running tests:", " ".join(cmd))
    return subprocess.call(cmd)


def gather_reports(repo_dir: Path):
    reports = {}
    br = repo_dir / "bootstrap_report.json"
    if br.exists():
        try:
            reports["bootstrap_report"] = json.loads(br.read_text(encoding="utf-8"))
        except Exception as e:
            reports["bootstrap_report"] = f"error reading: {e}"

    audit_log = repo_dir / ".git" / "tmp_audit" / "chatdev_consensus_test.log"
    if audit_log.exists():
        reports["chatdev_audit_snippet"] = audit_log.read_text(encoding="utf-8")[:800]

    print("\n=== Reports Summary ===")
    for k, v in reports.items():
        print(f"-- {k}:")
        if isinstance(v, str):
            print(v)
        else:
            print(json.dumps(v, indent=2))


def main():
    repo_dir = Path(__file__).resolve().parent

    rc = run_orchestrator_dryrun(repo_dir)
    print("Orchestrator DryRun exit code:", rc)

    rc_tests = run_tests(repo_dir)
    print("Tests exit code:", rc_tests)

    gather_reports(repo_dir)

    sys.exit(0 if (rc == 0 and rc_tests == 0) else 2)


if __name__ == "__main__":
    main()

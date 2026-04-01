"""Chug-bot runner: run the automated sequence in a single command.

Steps:
  - Run programmatic import checks
  - Run apply_missing_inits dry-run
  - Generate PHASE1 plan
  - Run triage on import report
  - Summarize and exit with non-zero if important failures
"""

import json
import subprocess
from pathlib import Path

ROOT = Path(".")


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    reports = Path("reports")
    reports.mkdir(exist_ok=True)

    print("[chugbot] Running programmatic import checks...")
    _code, out = run(["python", "scripts/run_repo_import_checks.py", "."])
    print(out)

    print("[chugbot] Running apply_missing_inits dry-run...")
    _code2, out2 = run(
        [
            "python",
            "scripts/apply_missing_inits.py",
            "--roots",
            "src",
            "projects",
            "--exclude",
            ".venv",
            ".git",
            "node_modules",
            "reports",
            "--dry-run",
        ]
    )
    print(out2)

    print("[chugbot] Generating PHASE1 plan...")
    _code3, out3 = run(["python", "scripts/generate_phase1_plan.py"])
    print(out3)

    print("[chugbot] Running triage on import report...")
    _code4, out4 = run(["python", "scripts/triage_import_failures.py", "reports/import_failures_programmatic.json"])
    print(out4)

    # Read the programmatic import report and summarize
    report_path = reports / "import_failures_programmatic.json"
    failures = {}
    if report_path.exists():
        failures = json.loads(report_path.read_text(encoding="utf-8"))

    important = {m: r for m, r in failures.items() if r != "skipped_heavy_imports"}

    print(f"[chugbot] Programmatic import failures: {len(failures)}; important: {len(important)}")

    return 0 if not important else 2


if __name__ == "__main__":
    raise SystemExit(main())

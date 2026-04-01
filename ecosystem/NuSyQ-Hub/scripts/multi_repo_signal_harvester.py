"""Harvest lightweight build/test/lint signals across NuSyQ repos.

This script is a conservative, non-destructive implementation intended to
be import-safe for tests. It harvests basic data (git head, status, and a
ruff lint snapshot) and writes a JSON report to the requested output.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _run(cmd: Iterable[str], cwd: Path) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            list(cmd),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired as exc:
        return 1, "", f"Timeout ({exc})"
    except (subprocess.SubprocessError, OSError) as exc:  # more specific than Exception
        return 1, "", str(exc)


def _collect_repo_signals(repo_path: Path) -> dict[str, Any]:
    signals: dict[str, Any] = {}
    signals["path"] = str(repo_path)

    if not repo_path.exists():
        signals["error"] = "path missing"
        return signals

    _, stdout, _ = _run(["git", "status", "-sb"], repo_path)
    signals["git_status"] = stdout.splitlines()[:5]
    _, stdout, _ = _run(["git", "log", "-1", "--oneline"], repo_path)
    signals["git_head"] = stdout.strip()

    lint_code, lint_out, _ = _run(
        ["python", "-m", "ruff", "check", "--select=F401,F821,E999", "--exit-zero"], repo_path
    )
    signals["lint_command"] = "ruff check --select=F401,F821,E999 --exit-zero"
    signals["lint_output_lines"] = len(lint_out.splitlines())
    signals["lint_errors_count"] = sum(1 for line in lint_out.splitlines() if line.strip() and ":" in line)
    signals["lint_failed"] = lint_code != 0

    return signals


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Harvest signals across NuSyQ repos")
    parser.add_argument(
        "--repos",
        nargs="+",
        type=Path,
        help="Paths to the repositories to scan (defaults to hub/root/simulatedverse)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("state/reports/multi_repo_signals.json"),
        help="Where to save the harvested signal report",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress printed summary",
    )
    return parser.parse_args()


def _default_repos() -> list[tuple[str, Path]]:
    hub = Path(__file__).resolve().parents[1]
    candidates = [
        ("hub", hub),
        ("nusyq_root", hub.parent / "NuSyQ"),
        ("simulatedverse", hub.parent / "SimulatedVerse" / "SimulatedVerse"),
    ]
    existing: list[tuple[str, Path]] = []
    for name, path in candidates:
        if path.exists():
            existing.append((name, path))
    return existing


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()

    repo_targets = args.repos or []
    labeled_repos: list[tuple[str, Path]] = []
    if repo_targets:
        for idx, path in enumerate(repo_targets):
            labeled_repos.append((f"repo_{idx}", path))
    else:
        labeled_repos = _default_repos()

    if not labeled_repos:
        logger.warning("No repositories found; nothing to harvest.")
        return 1

    report: dict[str, Any] = {"repos": {}, "summary": {}}
    for label, repo_path in labeled_repos:
        report["repos"][label] = _collect_repo_signals(repo_path)

    report["summary"]["total_repos"] = len(labeled_repos)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Saved multi-repo signal report to %s", args.output)

    if not args.quiet:
        for label, signals in report["repos"].items():
            print(f"=== {label} ===")
            print(f"path: {signals.get('path')}")
            print(f"git_head: {signals.get('git_head')}")
            print("git_status (top 5 lines):")
            for line in signals.get("git_status", []):
                print(f"  {line}")
            print(f"lint_errors_count: {signals.get('lint_errors_count')}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

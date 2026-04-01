#!/usr/bin/env python3
"""
NuSyQ-Chug — Autonomous CHUG proof-of-concept

This script implements a lightweight autonomous loop that:
- Scans the workspace for TODOs/BUGs/FIXMEs
- Checks system / nusyq health (best-effort)
- Prioritizes small tasks
- Logs events to a chug log directory
- Supports dry-run (default) and optional commit/sync flags

Usage (dry-run):
  python nusyq_chug.py --once

Run continuously (example):
  python nusyq_chug.py --max-cycles 12 --phases 5 10 15 30 60

This is intentionally conservative: no source edits or commits unless
--allow-commit is supplied.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any


DEFAULT_WORKSPACE_ROOTS = [
    r"c:\\CONCEPT",
    r"c:\\prime_anchor\\NuSyQ-Hub",
    r"c:\\prime_anchor\\NuSyQ",
    r"c:\\prime_anchor\\SimulatedVerse\\SimulatedVerse",
    r"c:\\Users\\keath\\Dev-Mentor",
]


def run_cmd(cmd: str, cwd: str | Path | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """Run a shell command and capture output (text)."""
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as e:
        return {"cmd": cmd, "returncode": -1, "stdout": "", "stderr": str(e)}


def health_check(roots: List[str], log: List[str]) -> Dict[str, Any]:
    """Attempt to check NuSyQ system health using known entrypoints."""
    results = {"checked": [], "success": False}
    # Try nusyq CLI
    res = run_cmd("nusyq command system_status")
    results["checked"].append({"method": "nusyq cli", "result": res})
    if res["returncode"] == 0 and res["stdout"]:
        results["success"] = True
        log.append("system_status via nusyq CLI succeeded")
        return results

    # Fallback: try repository-local start_nusyq.py if present
    for r in roots:
        p = Path(r)
        script = p / "scripts" / "start_nusyq.py"
        if script.exists():
            cmd = f'python "{script}" brief'
            res2 = run_cmd(cmd, cwd=p)
            results["checked"].append({"method": str(script), "result": res2})
            if res2["returncode"] == 0:
                results["success"] = True
                log.append(f"health via {script} succeeded")
                return results

    log.append("health_check: no nuSyQ entrypoints succeeded")
    return results


def find_todos(roots: List[str], fast: bool = False) -> List[Dict[str, Any]]:
    pattern = re.compile(r"\b(TODO|FIXME|BUG)\b", flags=re.IGNORECASE)
    matches: List[Dict[str, Any]] = []
    exts = {".py", ".ps1", ".md", ".js", ".ts", ".json", ".yaml", ".yml", ".cs"}
    for r in roots:
        p = Path(r)
        if not p.exists():
            continue
        if fast:
            # Fast mode: only scan top-level common directories to avoid long runs
            candidates = []
            for d in ("app", "src", "scripts", "tools", "tests"):
                dd = p / d
                if dd.exists():
                    candidates.extend(list(dd.rglob("*")))
        else:
            candidates = list(p.rglob("*"))
        for f in candidates:
            try:
                if f.is_file() and f.suffix.lower() in exts:
                    text = f.read_text(errors="ignore")
                    for i, line in enumerate(text.splitlines(), start=1):
                        m = pattern.search(line)
                        if m:
                            match_item = {
                                "file": str(f),
                                "line": i,
                                "text": line.strip(),
                            }
                            matches.append(match_item)
            except Exception:
                continue
    return matches


def find_scriptanalyzer_issues(roots: List[str]) -> List[Dict[str, Any]]:
    issues = []
    for r in roots:
        p = Path(r)
        j = p / ".scriptanalyzer_issues.json"
        if j.exists():
            try:
                data = json.loads(j.read_text())
                if isinstance(data, list):
                    issues.extend(data)
                else:
                    issues.append(data)
            except Exception:
                continue
    return issues


def git_status(repo_root: str) -> Dict[str, Any]:
    p = Path(repo_root)
    if not (p / ".git").exists():
        return {"repo": repo_root, "git": False}
    res = run_cmd(f'git -C "{repo_root}" status --porcelain')
    files = []
    if res["returncode"] == 0 and res["stdout"]:
        for line_out in res["stdout"].splitlines():
            files.append(line_out.strip())
    return {"repo": repo_root, "git": True, "pending": files}


def save_event(logdir: Path, event: Dict[str, Any]) -> None:
    logdir.mkdir(parents=True, exist_ok=True)
    fname = logdir / "events.jsonl"
    with fname.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, default=str, ensure_ascii=False) + "\n")


def phase_work(
    duration_minutes: int,
    roots: List[str],
    dry_run: bool,
    allow_commit: bool,
    logdir: Path,
    session_id: str,
    fast: bool = False,
) -> Dict[str, Any]:
    start = datetime.now(timezone.utc)
    log_lines: List[str] = []
    log_lines.append(f"Phase start: {start.isoformat()} ({duration_minutes}m)")
    # Persist a lightweight phase-start event early so runs are observable
    start_event = {
        "session": session_id,
        "phase_minutes": duration_minutes,
        "start": start.isoformat(),
        "note": "phase_started",
    }
    save_event(logdir, start_event)
    # Health
    health = health_check(roots, log_lines)
    # Scan TODOs and analyzer issues
    todos = find_todos(roots, fast=fast)
    analyzer = find_scriptanalyzer_issues(roots)
    # Git status
    git_reports = [git_status(r) for r in roots if Path(r).exists()]
    # Pick small tasks to triage (first 3 TODOs or analyzer items)
    small_tasks = []
    for t in todos[:3]:
        small_tasks.append({"type": "todo", "detail": t})
    for a in analyzer[:3]:
        small_tasks.append({"type": "analyzer", "detail": a})

    # Simulate attempt/fix steps (no edits unless allow_commit)
    actions = []
    for task in small_tasks:
        note = f"Triage: {task['type']} {task['detail'].get('file', '')}"
        log_lines.append(note)
        actions.append({"task": task, "result": "triaged", "note": note})

    # If there are pending git changes and allow_commit is True,
    # optionally commit minimal changes
    commits = []
    if allow_commit:
        for gr in git_reports:
            if gr.get("git") and gr.get("pending"):
                repo = gr["repo"]
                # Stage and commit minimal placeholder if not dry-run
                if not dry_run:
                    # Stage all pending changes first
                    run_cmd(f'git -C "{repo}" add -A')
                    now_str = datetime.now(timezone.utc).isoformat()
                    cm_msg = (
                        f"chug: automated triage {session_id} "
                        f"{now_str}"
                    )
                    # Use shlex.quote to safely wrap the commit message
                    commit_cmd = (
                        'git -C "{}" commit -m {}'.format(repo, shlex.quote(cm_msg))
                    )
                    res = run_cmd(commit_cmd)
                    commits.append({"repo": repo, "commit": res})
                else:
                    commits.append({"repo": repo, "commit": "dry-run (not committed)"})

    end = datetime.now(timezone.utc)
    event = {
        "session": session_id,
        "phase_minutes": duration_minutes,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "health": health,
        "small_tasks": small_tasks,
        "git_reports": git_reports,
        "commits": commits,
        "log_lines": log_lines,
    }
    save_event(logdir, event)
    return event


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nusyq_chug")
    parser.add_argument(
        "--roots",
        nargs="*",
        help="Workspace roots to scan",
        default=DEFAULT_WORKSPACE_ROOTS,
    )
    parser.add_argument(
        "--phases",
        nargs="*",
        type=int,
        help="Phase durations (minutes)",
        default=[5, 10, 15, 30, 60],
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not modify or commit; default is False (safe).",
    )
    parser.add_argument(
        "--allow-commit",
        action="store_true",
        help=(
            "Allow commits when changes are staged (implies non-dry-run)"
        ),
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one cycle (through all phases) and exit",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast scan mode: limit file scanning to common top-level dirs",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=1,
        help="Number of cycles to run",
    )
    parser.add_argument(
        "--log-dir",
        default=None,
        help=(
            "Directory to write chug logs (default: ./tools/nusyq_chug/chug_logs)"
        ),
    )
    default_session = f"chug-{datetime.now(timezone.utc).isoformat()}"
    parser.add_argument("--session-id", default=default_session)
    args = parser.parse_args(argv)

    roots = args.roots
    if args.log_dir:
        logdir = Path(args.log_dir)
    else:
        logdir = Path(__file__).parent / "chug_logs"
    dry_run = args.dry_run or (not args.allow_commit)

    print("NuSyQ-Chug:")
    print("  roots=", roots)
    print("  logdir=", logdir)
    print("  dry_run=", dry_run)
    print("  phases=", args.phases)
    logdir.mkdir(parents=True, exist_ok=True)

    cycles = args.max_cycles if not args.once else 1
    for cycle in range(cycles):
        now_str = datetime.now(timezone.utc).isoformat()
        print(f"Starting cycle {cycle+1}/{cycles} at {now_str}")
        for minutes in args.phases:
            print(" - Phase:", minutes, "minute goal (soft)")
            evt = phase_work(
                minutes,
                roots,
                dry_run,
                args.allow_commit,
                logdir,
                args.session_id,
                fast=args.fast,
            )
            summary = {
                "phase_summary": {
                    "minutes": minutes,
                    "small_tasks": len(evt["small_tasks"]),
                }
            }
            print(json.dumps(summary))
            # short sleep for POC; real runs would wait minutes * 60
            time.sleep(0.5)
        print(f"Cycle {cycle+1} complete")
        events_file = logdir / "events.jsonl"
        print("Events saved to", events_file)
        if args.once:
            break

    print("NuSyQ-Chug run complete (POC).")
    print("Review chug_logs/events.jsonl for details.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""ecosystem/sync_steward.py — Cross-repo sync steward for the NuSyQ ecosystem.

Adapted from the PowerShell sync-steward spec for Linux/Python/Replit.

Modes:
    hourly   — fetch + inspect only; no commit/push; log blockers
    full     — fetch, rebase, validate, stage, commit, push
    status   — read-only snapshot; no git writes whatsoever
    dryrun   — full pipeline, zero writes (git and filesystem)

Usage:
    python3 ecosystem/sync_steward.py --mode hourly
    python3 ecosystem/sync_steward.py --mode full
    python3 ecosystem/sync_steward.py --mode status
    python3 ecosystem/sync_steward.py --mode full --dry-run

Exit codes:
    0  all operations succeeded
    1  one or more blockers recorded
    2  no usable git repo found
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent  # /home/runner/workspace
ECOSYSTEM = Path(__file__).parent        # /home/runner/workspace/ecosystem

ECO_MODULES = [
    ("Dev-Mentor",          ECOSYSTEM / "Dev-Mentor"),
    ("NuSyQ-Hub",           ECOSYSTEM / "NuSyQ-Hub"),
    ("CONCEPT_SAMURAI",     ECOSYSTEM / "CONCEPT_SAMURAI"),
    ("NuSyQ_Ultimate",      ECOSYSTEM / "NuSyQ_Ultimate"),
    ("SimulatedVerse",      ECOSYSTEM / "SimulatedVerse"),
    ("awesome-vibe-coding", ECOSYSTEM / "awesome-vibe-coding"),
]

LOG_DIR = ECOSYSTEM / "logs" / "steward"

RUNTIME_SKIP = (
    "__pycache__", "node_modules", ".pyc", ".pyo",
    "sessions/", ".db", ".log", ".lock", "*.egg-info",
    "dist/", ".DS_Store",
)


# ── Git helpers ────────────────────────────────────────────────────────────────

def _git(args: list[str], cwd: Path, allow_fail: bool = False, timeout: int = 30) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=cwd, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
        out = (r.stdout + r.stderr).strip()
        if r.returncode != 0 and not allow_fail:
            raise RuntimeError(f"git {' '.join(args)} failed in {cwd}: {out}")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        return 124, f"git {' '.join(args)} timed out after {timeout}s"


def _is_git_repo(path: Path) -> bool:
    code, _ = _git(["rev-parse", "--git-dir"], cwd=path, allow_fail=True)
    return code == 0


def _branch(cwd: Path) -> str:
    _, out = _git(["branch", "--show-current"], cwd=cwd, allow_fail=True)
    return out.strip() or "main"


def _status_porcelain(cwd: Path) -> list[str]:
    _, out = _git(["status", "--porcelain"], cwd=cwd, allow_fail=True)
    return [l for l in out.splitlines() if l.strip()]


def _status_sb(cwd: Path) -> str:
    _, out = _git(["status", "-sb"], cwd=cwd, allow_fail=True)
    return out.strip()


def _remotes(cwd: Path) -> str:
    _, out = _git(["remote", "-v"], cwd=cwd, allow_fail=True)
    return out.strip()


def _divergence(cwd: Path, branch: str) -> dict[str, Any]:
    upstream = f"origin/{branch}"
    code, _ = _git(["rev-parse", "--verify", upstream], cwd=cwd, allow_fail=True)
    if code != 0:
        return {"upstream_exists": False, "ahead": 0, "behind": 0, "diverged": False, "summary": "no upstream"}

    _, out = _git(["rev-list", "--left-right", "--count", f"HEAD...{upstream}"],
                   cwd=cwd, allow_fail=True)
    parts = out.split()
    ahead = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    behind = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    diverged = ahead > 0 and behind > 0

    if ahead == 0 and behind == 0:
        summary = "up to date"
    elif ahead > 0 and behind == 0:
        summary = f"ahead {ahead}"
    elif ahead == 0 and behind > 0:
        summary = f"behind {behind}"
    else:
        summary = f"diverged: ahead {ahead} / behind {behind}"

    return {
        "upstream_exists": True,
        "ahead": ahead, "behind": behind,
        "diverged": diverged, "summary": summary,
    }


def _recent_log(cwd: Path, n: int = 5) -> str:
    _, out = _git(
        ["log", "--oneline", "--decorate", "--graph", f"-n{n}"],
        cwd=cwd, allow_fail=True,
    )
    return out.strip()


def _is_clean(cwd: Path) -> bool:
    return len(_status_porcelain(cwd)) == 0


# ── Validation helpers ─────────────────────────────────────────────────────────

def _validate_module(name: str, path: Path, quick: bool = True) -> str:
    """Run targeted validation for a known ecosystem module."""
    if name == "Dev-Mentor":
        script = path / "scripts" / "validate_all.py"
        if script.exists():
            args = [sys.executable, str(script)]
            if quick:
                args.append("--quick")
            try:
                r = subprocess.run(args, cwd=path, capture_output=True, text=True, timeout=60)
                tail = (r.stdout + r.stderr)[-800:]
                return f"validate_all.py: {'ok' if r.returncode == 0 else 'FAIL'}\n{tail}"
            except subprocess.TimeoutExpired:
                return "validate_all.py: timed out"
        return "no validate_all.py found"

    if name == "NuSyQ-Hub":
        src = path / "src" / "api" / "main.py"
        if src.exists():
            try:
                import urllib.request
                with urllib.request.urlopen("http://localhost:3003/api/status", timeout=3) as r:
                    d = json.loads(r.read())
                    return f"NuSyQ-Hub API: ok | status={d.get('status','?')}"
            except Exception as e:
                return f"NuSyQ-Hub API: unreachable ({e})"
        return "NuSyQ-Hub: no src/api/main.py"

    # Generic: count Python files, check for syntax errors
    py_files = list(path.rglob("*.py"))
    bad = []
    import ast
    for f in py_files[:50]:  # cap at 50
        try:
            ast.parse(f.read_bytes())
        except SyntaxError as e:
            bad.append(f"{f.relative_to(path)}: {e}")
    if bad:
        return f"syntax: {len(bad)} error(s): " + "; ".join(bad[:3])
    return f"syntax: ok ({len(py_files)} py files scanned)"


# ── gh_sync helper ─────────────────────────────────────────────────────────────

def _gh_sync(module_path: Path, dry_run: bool = False) -> str:
    """Run gh_sync.py for a module that has one (Dev-Mentor)."""
    gh = module_path / "scripts" / "gh_sync.py"
    if not gh.exists():
        return "no gh_sync.py"
    args = [sys.executable, str(gh)]
    if dry_run:
        args.append("--dry-run")
    try:
        r = subprocess.run(args, cwd=module_path, capture_output=True, text=True, timeout=90)
        tail = (r.stdout + r.stderr)[-500:]
        return f"gh_sync: {'ok' if r.returncode == 0 else 'warn'}\n{tail}"
    except subprocess.TimeoutExpired:
        return "gh_sync: timed out"


# ── Auto commit message ────────────────────────────────────────────────────────

def _commit_msg() -> str:
    stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"chore(sync): steward checkpoint @ {stamp}"


# ── Core steward cycle ────────────────────────────────────────────────────────

def _sync_workspace(mode: str, dry_run: bool) -> dict[str, Any]:
    """Steward the root workspace git repo."""
    cwd = WORKSPACE
    if not _is_git_repo(cwd):
        return {"error": "workspace is not a git repo", "path": str(cwd)}

    actions: list[str] = []
    blockers: list[str] = []
    branch = _branch(cwd)
    status_before = _status_sb(cwd)
    remotes_out = _remotes(cwd)
    log_before = _recent_log(cwd)

    # ── 1. Fetch ──────────────────────────────────────────────────────────────
    if not dry_run and mode in ("hourly", "full"):
        code, out = _git(["fetch", "--all", "--prune"], cwd=cwd, allow_fail=True, timeout=30)
        if code == 0:
            actions.append("fetched")
        else:
            blockers.append(f"fetch failed: {out[:80]}")

    # ── 2. Divergence check ───────────────────────────────────────────────────
    div = _divergence(cwd, branch)

    # ── 3. Pull/rebase (full mode only) ──────────────────────────────────────
    if mode == "full" and not dry_run and div.get("behind", 0) > 0 and not div.get("diverged"):
        if _is_clean(cwd):
            code, out = _git(["pull", "--rebase", "origin", branch], cwd=cwd, allow_fail=True, timeout=45)
            if code == 0:
                actions.append(f"rebased from origin/{branch}")
            else:
                blockers.append(f"rebase failed: {out[:80]}")
        else:
            # stash → pull → pop
            code, _ = _git(["stash", "push", "-u", "-m", "sync-steward auto-stash"], cwd=cwd, allow_fail=True)
            if code == 0:
                actions.append("stashed local work")
                code2, out2 = _git(["pull", "--rebase", "origin", branch], cwd=cwd, allow_fail=True, timeout=45)
                if code2 == 0:
                    actions.append(f"rebased from origin/{branch}")
                else:
                    blockers.append(f"rebase failed: {out2[:80]}")
                code3, out3 = _git(["stash", "pop"], cwd=cwd, allow_fail=True)
                if code3 == 0:
                    actions.append("restored stashed work")
                else:
                    blockers.append(f"stash pop needs manual resolution: {out3[:80]}")
    elif div.get("diverged"):
        blockers.append("branch diverged — manual review before automated push")

    # ── 4. Validation ─────────────────────────────────────────────────────────
    validation = {}
    if mode == "full" and not dry_run:
        # Full validation: run validate_all.py for Dev-Mentor, syntax for others
        for name, path in ECO_MODULES:
            if path.exists():
                validation[name] = _validate_module(name, path, quick=True)
        actions.append("validation run")
    elif mode == "full" and dry_run:
        # Dry-run: syntax check only — no subprocess/API calls
        import ast as _ast
        for name, path in ECO_MODULES:
            if not path.exists():
                continue
            py_files = list(path.rglob("*.py"))[:30]
            bad = []
            for f in py_files:
                try:
                    _ast.parse(f.read_bytes())
                except SyntaxError as e:
                    bad.append(f"{f.name}: {e}")
            validation[name] = f"syntax ok ({len(py_files)} files)" if not bad else "; ".join(bad[:3])
        actions.append("syntax validation run (dry-run mode)")
    else:
        validation["note"] = "hourly/status mode: validation deferred"

    # ── 5. Stage + commit (full only) ─────────────────────────────────────────
    changed = _status_porcelain(cwd)
    files_touched = [l[3:].strip() for l in changed if l.strip()]

    if mode == "full" and files_touched and not dry_run:
        # Filter out runtime files before staging
        to_stage = [
            f for f in files_touched
            if not any(pat.strip("*") in f for pat in RUNTIME_SKIP)
        ]
        if to_stage:
            code, _ = _git(["add"] + to_stage, cwd=cwd, allow_fail=True)
            actions.append(f"staged {len(to_stage)} file(s)")

            commit_code, commit_out = _git(
                ["commit", "-m", _commit_msg()], cwd=cwd, allow_fail=True
            )
            if commit_code == 0:
                actions.append("committed")
            elif "nothing to commit" in commit_out:
                actions.append("nothing new to commit")
            else:
                blockers.append(f"commit failed: {commit_out[:80]}")
        else:
            actions.append("no non-runtime files to stage")

    # ── 6. Push (full only) ───────────────────────────────────────────────────
    post_div = _divergence(cwd, branch)
    if mode == "full" and not dry_run and post_div.get("ahead", 0) > 0 and not post_div.get("diverged"):
        push_code, push_out = _git(["push", "origin", branch], cwd=cwd, allow_fail=True, timeout=45)
        if push_code == 0:
            actions.append("pushed")
        else:
            blockers.append(f"push blocked: {push_out[:100]}")

    final_div = _divergence(cwd, branch)

    return {
        "repo": "workspace (root)",
        "branch": branch,
        "remotes": remotes_out,
        "remote_sync_state": final_div.get("summary", "unknown"),
        "log": log_before,
        "status_before": status_before,
        "files_touched": files_touched[:30],
        "actions": actions,
        "validation": validation,
        "blockers": blockers,
    }


def _inspect_module(name: str, path: Path) -> dict[str, Any]:
    """Fast read-only snapshot of an ecosystem module directory."""
    if not path.exists():
        return {"name": name, "exists": False}
    py_count = len(list(path.rglob("*.py")))
    js_count = len(list(path.rglob("*.js")))
    ts_count = len(list(path.rglob("*.ts")))
    key_files = []
    for kf in ["package.json", "pyproject.toml", "requirements.txt", "README.md"]:
        if (path / kf).exists():
            key_files.append(kf)
    has_td = (path / "td_bridge.py").exists()
    has_validate = (path / "scripts" / "validate_all.py").exists()
    return {
        "name": name,
        "exists": True,
        "py": py_count, "js": js_count, "ts": ts_count,
        "key_files": key_files,
        "td_bridge": has_td,
        "has_validate": has_validate,
    }


# ── Report formatter ───────────────────────────────────────────────────────────

def _fmt_report(ws: dict, modules: list[dict], mode: str, elapsed: float) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append(f"SYNC STEWARD REPORT — {mode.upper()} — {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("=" * 72)

    lines.append("")
    lines.append(f"  repo:              {ws.get('repo','?')}")
    lines.append(f"  branch:            {ws.get('branch','?')}")
    lines.append(f"  remote_sync_state: {ws.get('remote_sync_state','?')}")
    lines.append(f"  actions:           {', '.join(ws.get('actions',[]))}")
    lines.append(f"  files_touched:     {len(ws.get('files_touched',[]))} file(s)")

    if ws.get("blockers"):
        lines.append(f"  BLOCKERS:")
        for b in ws["blockers"]:
            lines.append(f"    ✗ {b}")
    else:
        lines.append("  blockers:          none")

    if ws.get("validation"):
        lines.append("")
        lines.append("  VALIDATION:")
        for k, v in ws["validation"].items():
            summary = v.split("\n")[0] if isinstance(v, str) else str(v)
            lines.append(f"    [{k}]  {summary}")

    lines.append("")
    lines.append("  RECENT GIT LOG:")
    for gl in ws.get("log", "").splitlines()[:5]:
        lines.append(f"    {gl}")

    lines.append("")
    lines.append("  ECOSYSTEM MODULE SNAPSHOT:")
    for m in modules:
        if m.get("exists"):
            td = "✓" if m.get("td_bridge") else "—"
            lines.append(
                f"    {m['name']:<22} py={m['py']:<4} js={m['js']:<4}  td_bridge={td}"
            )
        else:
            lines.append(f"    {m['name']:<22} NOT FOUND")

    lines.append("")
    lines.append(f"  elapsed: {elapsed:.1f}s")
    cadence = {
        "hourly": "next: top of next hour",
        "full": "next: 3 hours (or sooner if active)",
        "status": "next: on demand",
        "dryrun": "next: when ready for real run",
    }.get(mode, "next: on demand")
    lines.append(f"  {cadence}")
    lines.append("=" * 72)
    return "\n".join(lines)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="NuSyQ Ecosystem Sync Steward")
    parser.add_argument("--mode", choices=["hourly", "full", "status", "dryrun"], default="status")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    parser.add_argument("--log", action="store_true", help="Write log file to ecosystem/logs/steward/")
    args = parser.parse_args()

    mode = args.mode
    dry_run = args.dry_run or mode == "dryrun"
    if mode == "dryrun":
        mode = "full"

    t0 = time.monotonic()

    ws = _sync_workspace(mode, dry_run)
    modules = [_inspect_module(name, path) for name, path in ECO_MODULES]

    elapsed = time.monotonic() - t0

    display_mode = "dryrun" if dry_run else mode
    report = _fmt_report(ws, modules, display_mode, elapsed)

    if args.json:
        out = {
            "mode": display_mode,
            "workspace": ws,
            "modules": modules,
            "elapsed": round(elapsed, 2),
        }
        print(json.dumps(out, indent=2, default=str))
    else:
        print(report)

    if args.log:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_path = LOG_DIR / f"sync_steward_{display_mode}_{stamp}.log"
        log_path.write_text(report)
        print(f"\nLog written to: {log_path}")

    return 1 if ws.get("blockers") else 0


if __name__ == "__main__":
    sys.exit(main())

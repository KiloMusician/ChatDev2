#!/usr/bin/env python3
"""scripts/sync_guard.py — Pre-push safety guard for VS Code / Claude co-dev.

Runs 7 checks before a git push:
  1. No index.lock (stale git lock)
  2. No in-progress merge or rebase
  3. On correct branch (main)
  4. Runtime files not staged as additions/modifications
  5. Runtime files not still tracked in index
  6. Not behind origin/main (local reflog — no network fetch)
  7. No stale ghost remotes

Usage:
    python scripts/sync_guard.py           # check only
    python scripts/sync_guard.py --fix     # auto-fix where safe
    python scripts/sync_guard.py --quiet   # only print failures
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

RUNTIME_FILES = [
    "cost_log.csv",
    "devlog.md",
    "state/nusyq_service_state.json",
    "state/scheduler_state.json",
    "state/agent_manifest.json",
    "state/quest_log.jsonl",
    "state/memory_chronicle.jsonl",
]

RUNTIME_PREFIXES = ("state/", ".devmentor/", "sessions/", "reports/")
ALLOWED_REMOTES = {"origin", "gitsafe-backup"}


def _run(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    return r.returncode, r.stdout.strip()


def _is_runtime(path: str) -> bool:
    return path in RUNTIME_FILES or path.startswith(RUNTIME_PREFIXES)


# ── individual checks ────────────────────────────────────────────────────────


def check_index_lock(fix: bool) -> bool:
    lock = REPO_ROOT / ".git" / "index.lock"
    if not lock.exists():
        return True
    if fix:
        lock.unlink()
        print("  [FIXED] Removed stale .git/index.lock")
        return True
    print("  [FAIL] .git/index.lock exists — another git process may be running.")
    print("         Fix: rm .git/index.lock  OR run with --fix")
    return False


def check_no_merge_rebase() -> bool:
    merge_head = REPO_ROOT / ".git" / "MERGE_HEAD"
    rebase_dirs = [
        REPO_ROOT / ".git" / "rebase-merge",
        REPO_ROOT / ".git" / "rebase-apply",
    ]
    if merge_head.exists():
        print("  [FAIL] Merge in progress. Abort: git merge --abort")
        return False
    if any(d.exists() for d in rebase_dirs):
        print("  [FAIL] Rebase in progress. Abort: git rebase --abort")
        return False
    return True


def check_branch() -> bool:
    _, branch = _run(["git", "branch", "--show-current"])
    if branch != "main":
        print(f"  [WARN] On branch '{branch}' — expected 'main'.")
    return True  # warn only


def check_runtime_not_staged(fix: bool) -> bool:
    """Block runtime files staged as A/M; allow staged deletions (untracking)."""
    _, out = _run(["git", "diff", "--cached", "--name-status"])
    bad = []
    for line in out.splitlines():
        parts = line.split("\t", 1)
        if len(parts) < 2:
            continue
        status, path = parts[0].strip(), parts[1].strip()
        if status.startswith("D"):
            continue  # deletion = untracking runtime file — correct action
        if _is_runtime(path):
            bad.append(path)
    if not bad:
        return True
    if fix:
        for path in bad:
            _run(["git", "rm", "--cached", path])
        print(f"  [FIXED] Unstaged runtime files: {bad}")
        return True
    print(f"  [FAIL] Runtime files staged for commit: {bad}")
    print("         Fix: git rm --cached <file>  OR run with --fix")
    return False


def check_runtime_not_tracked(fix: bool) -> bool:
    _, out = _run(["git", "ls-files", "--cached"])
    tracked = set(out.splitlines()) if out else set()
    bad = [f for f in RUNTIME_FILES if f in tracked]
    if not bad:
        return True
    if fix:
        for path in bad:
            _run(["git", "rm", "--cached", path])
        print(f"  [FIXED] Removed runtime files from index: {bad}")
        return True
    print(f"  [FAIL] Runtime files still tracked: {bad}")
    print("         Fix: git rm --cached <file>  OR run with --fix")
    return False


def check_not_behind_origin() -> bool:
    """Local-only divergence check via cached remote ref — no network needed."""
    rc, remote_sha = _run(["git", "rev-parse", "refs/remotes/origin/main"])
    if rc != 0:
        print("  [SKIP] No cached origin/main — run 'git fetch' to enable check.")
        return True
    _, local_sha = _run(["git", "rev-parse", "HEAD"])
    rc2, _ = _run(["git", "merge-base", "--is-ancestor", remote_sha, local_sha])
    if rc2 == 0:
        return True
    _, ab = _run(
        [
            "git",
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...refs/remotes/origin/main",
        ]
    )
    if "\t" in ab:
        _, behind = ab.split("\t")
        if int(behind) > 0:
            print(
                f"  [WARN] {behind} commit(s) behind origin/main. "
                "Consider: git pull --rebase"
            )
    return True  # warn only


def check_ghost_remotes(fix: bool) -> bool:
    _, out = _run(["git", "remote"])
    remotes = set(out.splitlines()) if out else set()
    ghost = remotes - ALLOWED_REMOTES
    if not ghost:
        return True
    if fix:
        for r in ghost:
            _run(["git", "remote", "remove", r])
        print(f"  [FIXED] Removed ghost remotes: {ghost}")
        return True
    print(f"  [WARN] Unexpected remotes: {ghost}. Allowed: {ALLOWED_REMOTES}")
    print("         Fix: git remote remove <name>  OR run with --fix")
    return True  # warn only


# ── main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    fix = "--fix" in sys.argv
    quiet = "--quiet" in sys.argv
    os.chdir(REPO_ROOT)

    if not quiet:
        print("Dev-Mentor Sync Guard")
        print("=" * 40)

    checks = [
        ("Index lock", lambda: check_index_lock(fix)),
        ("No merge/rebase", check_no_merge_rebase),
        ("Branch", check_branch),
        ("Runtime files not staged", lambda: check_runtime_not_staged(fix)),
        ("Runtime files not tracked", lambda: check_runtime_not_tracked(fix)),
        ("Not behind origin", check_not_behind_origin),
        ("Ghost remotes", lambda: check_ghost_remotes(fix)),
    ]

    results = []
    for name, fn in checks:
        try:
            ok = fn()
        except Exception as exc:
            print(f"  [ERROR] {name}: {exc}")
            ok = False
        results.append((name, ok))

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    if not quiet:
        icon = "✅" if passed == total else "⚠️ "
        print("=" * 40)
        print(f"{icon} {passed}/{total} checks passed")

    if passed == total:
        if not quiet:
            print("Safe to push.")
        return 0

    failed = [n for n, ok in results if not ok]
    if not quiet:
        print(f"Issues: {failed}")
        if not fix:
            print("Run with --fix to auto-resolve where safe.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

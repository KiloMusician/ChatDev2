#!/usr/bin/env python3
"""scripts/gh_sync.py — GitHub divergence reconciliation.

Strategy (in order of preference):
  1. Use `git push` with GITHUB_TOKEN credentials — preserves full commit
     ancestry and creates a connected history on GitHub.
  2. If diverged, merge origin/main into local (local code wins) first,
     then push — produces a real merge commit with both parents.
  3. Fall back to GitHub REST API blob-upload only if git networking is
     completely blocked (timeout); in that case, creates a content-sync
     commit from remote HEAD as single parent (documented limitation).

Usage:
    python3 scripts/gh_sync.py [--dry-run] [--message "custom msg"]
    python3 scripts/gh_sync.py --api-only   # force REST API fallback
"""
from __future__ import annotations

import base64
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
GH_REPO = "KiloMusician/Dev-Mentor"
GH_BRANCH = "main"
GIT_PUSH_TIMEOUT = 45  # seconds

SKIP_PATTERNS = {
    "__pycache__",
    ".git",
    "node_modules",
    ".pyc",
    ".pyo",
    "sessions/",
    ".db",
    ".lock",
    ".log",
    "*.egg-info",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(cmd: str | list[str], timeout: int = 30) -> tuple[int, str, str]:
    import shlex

    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    try:
        r = subprocess.run(  # nosec B603
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=timeout,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"


def _token() -> str:
    token = ""
    env_local = REPO_ROOT / ".env.local"
    if env_local.exists():
        for line in env_local.read_text().splitlines():
            if line.startswith("GITHUB_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not token:
        token = os.environ.get("GITHUB_TOKEN", "")
    return token


def _authed_url(token: str) -> str:
    return f"https://x-access-token:{token}@github.com/{GH_REPO}.git"


def _should_skip(path: str) -> bool:
    return any(pat in path for pat in SKIP_PATTERNS)


def _clear_stale_lock() -> bool:
    """Remove .git/index.lock if it is empty (0-byte stale lock)."""
    lock = REPO_ROOT / ".git" / "index.lock"
    try:
        if lock.exists() and lock.stat().st_size == 0:
            lock.unlink()
            print("[gh_sync] Removed stale empty .git/index.lock", flush=True)
            return True
    except OSError as exc:
        print(f"[gh_sync] Could not remove stale lock: {exc}", flush=True)
    return False


def _configure_git() -> None:
    run('git config user.name "DevMentor Agent"')
    run('git config user.email "agent@devmentor.local"')


# ---------------------------------------------------------------------------
# Git-native push (preferred — preserves commit ancestry)
# ---------------------------------------------------------------------------


def _git_push(token: str, force: bool = False) -> tuple[bool, str]:
    """Push local main to GitHub using git push with token-auth URL.
    Preserves full commit ancestry — the correct way to sync histories.
    Returns (ok, message).
    """
    orig_url_code, orig_url, _ = run("git remote get-url origin")
    authed = _authed_url(token)
    run(f"git remote set-url origin {authed}")
    try:
        cmd = ["git", "push", "--force" if force else "", "origin", GH_BRANCH]
        cmd = [c for c in cmd if c]  # remove empty --force when not needed
        code, out, err = run(cmd, timeout=GIT_PUSH_TIMEOUT)
        if code == 0:
            return True, out or "pushed"
        if "fetch first" in err or "non-fast-forward" in err:
            return False, f"rejected:non-ff:{err[:120]}"
        if "timed out" in err or code == 124:
            return False, "network:timeout"
        return False, err[:200]
    finally:
        # Restore original remote URL (never leave token in URL)
        run(
            f"git remote set-url origin {orig_url or f'https://github.com/{GH_REPO}.git'}"
        )


def _force_resolve_conflicts() -> tuple[bool, str]:
    """Force-resolve remaining merge conflicts by checking out our version of
    every conflicting file (--ours), then staging and committing.
    This is a last-resort after `git merge -X ours` still leaves unresolved
    binary/rename conflicts.

    Returns (True, "") on success.
    Returns (False, reason) if no conflicts exist (caller should treat merge
    failure as non-conflict error and NOT proceed to push) or if commit fails.
    """
    _, conflict_str, _ = run("git diff --name-only --diff-filter=U")
    conflicts = [f.strip() for f in conflict_str.splitlines() if f.strip()]
    if not conflicts:
        # No unresolved conflict markers found — merge failure was NOT due to
        # content conflicts. Do not silently succeed; caller must not push.
        return False, "no conflict files found — merge failed for a non-conflict reason"
    print(
        f"[gh_sync] Force-resolving {len(conflicts)} conflict(s) with --ours...",
        flush=True,
    )
    for path in conflicts:
        run(["git", "checkout", "--ours", "--", path])
    _clear_stale_lock()
    run("git add --all")
    code, _, err = run(
        ["git", "commit", "-m", "merge: force-resolved conflicts (local wins)"]
    )
    if code != 0 and "nothing to commit" not in err:
        return False, f"commit after force-resolve failed: {err[:120]}"
    return True, ""


def _merge_remote_and_push(token: str) -> tuple[bool, str]:
    """Fetch origin/main, merge into local (local-wins strategy), then git push.
    Produces a real merge commit with connected ancestry on both sides.
    Fails closed: if we cannot prove merge succeeded, we do not push.
    """
    _configure_git()
    _clear_stale_lock()

    # Step 1: try to fetch (may timeout if Replit blocks outbound git)
    fetch_code, _, fetch_err = run(["git", "fetch", "origin"], timeout=20)
    if fetch_code == 0:
        print("[gh_sync] Fetched origin/main successfully", flush=True)
    else:
        # Fetch failed/timed-out — check if we have a cached origin/main ref
        _, cached_ref, _ = run("git rev-parse origin/main")
        if not cached_ref:
            # No cached ref AND fetch failed → cannot prove merge is safe; fail closed
            return False, (
                f"fetch failed ({fetch_err[:80]}) and no cached origin/main ref — "
                "cannot reconcile histories; refusing to force-push without known ancestry"
            )
        print(
            f"[gh_sync] Fetch unavailable; using cached origin/main ({cached_ref[:8]})",
            flush=True,
        )

    # Step 2: abort any in-flight merge state before starting fresh
    _clear_stale_lock()
    run(["git", "merge", "--abort"], timeout=10)  # no-op if no merge in progress

    # Step 3: merge origin/main with local-wins strategy
    _clear_stale_lock()
    merge_code, merge_out, merge_err = run(
        ["git", "merge", "-s", "recursive", "-X", "ours", "origin/main", "--no-edit"],
        timeout=30,
    )
    combined = merge_out + merge_err
    if merge_code == 0 or "Already up to date" in combined:
        print(f"[gh_sync] Merge OK: {merge_out[:120]}", flush=True)
    elif merge_code != 0:
        # Non-zero may mean unresolved conflicts (binary files, renames).
        # Only attempt force-resolve if git actually left conflict markers;
        # otherwise the failure has a different cause and we must fail closed.
        print(
            f"[gh_sync] merge returned {merge_code}: '{merge_err[:80]}' — checking conflicts",
            flush=True,
        )
        resolved, reason = _force_resolve_conflicts()
        if not resolved:
            # Abort the failed merge and report — do NOT push
            run(["git", "merge", "--abort"], timeout=10)
            return False, f"merge failed ({reason}): {merge_err[:200]}"

    _clear_stale_lock()
    ok, msg = _git_push(token, force=False)
    if not ok and "rejected" in msg:
        # Force push as last resort to connect histories
        print(
            "[gh_sync] Normal push rejected — force-pushing to connect histories",
            flush=True,
        )
        ok, msg = _git_push(token, force=True)
    return ok, msg


# ---------------------------------------------------------------------------
# REST API fallback (last resort — documents connected-history limitation)
# ---------------------------------------------------------------------------


def _api_push(token: str, message: str) -> dict:
    """Push local working tree to GitHub via REST API blobs.
    Uses remote HEAD as single parent — content syncs correctly but does NOT
    preserve local commit ancestry. Should only be used when git networking
    is completely unavailable.
    """
    try:
        import requests as req
    except ImportError:
        return {"ok": False, "error": "requests not installed"}

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base = f"https://api.github.com/repos/{GH_REPO}"

    # Get remote HEAD
    r = req.get(f"{base}/git/refs/heads/{GH_BRANCH}", headers=headers, timeout=15)
    if r.status_code != 200:
        return {"ok": False, "error": f"Cannot get remote ref: {r.status_code}"}
    remote_sha = r.json()["object"]["sha"]

    rc = req.get(f"{base}/git/commits/{remote_sha}", headers=headers, timeout=15)
    if rc.status_code != 200:
        return {"ok": False, "error": f"Cannot get remote commit: {rc.status_code}"}
    remote_tree_sha = rc.json()["tree"]["sha"]

    # Get remote file blobs for comparison
    rt = req.get(
        f"{base}/git/trees/{remote_tree_sha}?recursive=1", headers=headers, timeout=60
    )
    remote_blobs = {}
    if rt.status_code == 200:
        remote_blobs = {
            item["path"]: item["sha"]
            for item in rt.json().get("tree", [])
            if item["type"] == "blob"
        }

    # Walk local tracked files
    _, tracked_str, _ = run("git ls-files")
    all_tracked = [
        f.strip()
        for f in tracked_str.splitlines()
        if f.strip() and not _should_skip(f.strip())
    ]

    tree_items = []
    for file_path in all_tracked:
        full = REPO_ROOT / file_path
        if not full.exists():
            if file_path in remote_blobs:
                tree_items.append(
                    {"path": file_path, "mode": "100644", "type": "blob", "sha": None}
                )
            continue
        try:
            content = full.read_bytes()
        except Exception:
            continue

        # Compute git blob SHA to avoid uploading unchanged files
        header = f"blob {len(content)}\0".encode()
        local_sha = hashlib.sha1(header + content).hexdigest()
        if remote_blobs.get(file_path) == local_sha:
            continue  # unchanged

        blob_r = req.post(
            f"{base}/git/blobs",
            headers=headers,
            json={"content": base64.b64encode(content).decode(), "encoding": "base64"},
            timeout=30,
        )
        time.sleep(0.3)
        if blob_r.status_code not in (200, 201):
            continue
        mode = "100755" if full.stat().st_mode & 0o100 else "100644"
        tree_items.append(
            {
                "path": file_path,
                "mode": mode,
                "type": "blob",
                "sha": blob_r.json()["sha"],
            }
        )

    if not tree_items:
        return {
            "ok": True,
            "message": "No file changes to upload (API fallback)",
            "pushed": False,
        }

    print(
        f"[gh_sync] API fallback: uploading {len(tree_items)} changed files...",
        flush=True,
    )

    tr = req.post(
        f"{base}/git/trees",
        headers=headers,
        json={"base_tree": remote_tree_sha, "tree": tree_items},
        timeout=60,
    )
    if tr.status_code not in (200, 201):
        return {
            "ok": False,
            "error": f"Tree creation failed: {tr.status_code} {tr.text[:300]}",
        }
    new_tree_sha = tr.json()["sha"]

    # NOTE: Uses remote_sha as single parent (content-sync commit, not a true merge).
    # Local commit ancestry is not preserved in this fallback path.
    cr = req.post(
        f"{base}/git/commits",
        headers=headers,
        json={
            "message": message
            or "chore: content-sync fallback (git network unavailable)",
            "tree": new_tree_sha,
            "parents": [remote_sha],
            "author": {"name": "DevMentor Agent", "email": "agent@devmentor.local"},
        },
        timeout=30,
    )
    if cr.status_code not in (200, 201):
        return {
            "ok": False,
            "error": f"Commit creation failed: {cr.status_code} {cr.text[:300]}",
        }
    new_commit_sha = cr.json()["sha"]

    rr = req.patch(
        f"{base}/git/refs/heads/{GH_BRANCH}",
        headers=headers,
        json={"sha": new_commit_sha, "force": True},
        timeout=15,
    )
    if rr.status_code not in (200, 201):
        return {
            "ok": False,
            "error": f"Ref update failed: {rr.status_code} {rr.text[:200]}",
        }

    return {
        "ok": True,
        "message": message,
        "pushed": True,
        "new_remote_sha": rr.json()["object"]["sha"],
        "files_synced": len(tree_items),
        "warning": "API fallback used: local commit ancestry not preserved in GitHub history",
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def gh_sync(dry_run: bool = False, message: str = "", api_only: bool = False) -> dict:
    _clear_stale_lock()

    token = _token()
    if not token:
        return {"ok": False, "error": "GITHUB_TOKEN not set"}

    # Quick check — local vs remote
    _, local_sha, _ = run("git rev-parse HEAD")
    if not local_sha:
        return {"ok": False, "error": "Cannot get local HEAD SHA"}

    # Get remote SHA via API (reliable even when git network is blocked)
    try:
        import requests as req

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        rr = req.get(
            f"https://api.github.com/repos/{GH_REPO}/git/refs/heads/{GH_BRANCH}",
            headers=headers,
            timeout=10,
        )
        remote_sha = rr.json()["object"]["sha"] if rr.status_code == 200 else ""
    except Exception:
        remote_sha = ""

    print(
        f"[gh_sync] Local: {local_sha[:12]}  Remote: {(remote_sha or 'unknown')[:12]}",
        flush=True,
    )

    if local_sha == remote_sha:
        return {
            "ok": True,
            "message": "Already in sync — nothing to do",
            "pushed": False,
        }

    # Compute divergence using local git knowledge
    _, ahead_str, _ = (
        run(f"git rev-list {remote_sha}..{local_sha}") if remote_sha else (0, "", "")
    )
    _, behind_str, _ = (
        run(f"git rev-list {local_sha}..{remote_sha}") if remote_sha else (0, "", "")
    )
    commits_ahead = [c for c in ahead_str.splitlines() if c.strip()]
    commits_behind = [c for c in behind_str.splitlines() if c.strip()]
    print(
        f"[gh_sync] Local ahead: {len(commits_ahead)}, remote ahead: {len(commits_behind)}",
        flush=True,
    )

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "local_ahead": len(commits_ahead),
            "remote_ahead": len(commits_behind),
            "action": "would merge-then-push" if commits_behind else "would git-push",
        }

    if api_only:
        print("[gh_sync] --api-only flag: using REST API fallback", flush=True)
        return _api_push(token, message)

    # Primary path: git push (preserves commit ancestry)
    _configure_git()

    if not commits_behind:
        # Local is strictly ahead — simple push
        print("[gh_sync] Strictly ahead — attempting git push...", flush=True)
        ok, msg = _git_push(token, force=False)
        if ok:
            return {"ok": True, "message": msg, "pushed": True, "method": "git-push"}
        if "network:timeout" in msg:
            print(
                "[gh_sync] git network blocked — falling back to REST API", flush=True
            )
            return _api_push(token, message)
        # Push rejected (remote moved ahead concurrently) — fall through to merge+push
        print(
            f"[gh_sync] Push rejected ({msg}) — switching to merge-then-push",
            flush=True,
        )

    # Diverged (or push was rejected) — merge remote into local then push
    print(
        "[gh_sync] Diverged — merging origin/main (local wins) then pushing...",
        flush=True,
    )
    ok, msg = _merge_remote_and_push(token)
    if ok:
        _, new_sha, _ = run("git rev-parse HEAD")
        return {
            "ok": True,
            "message": msg,
            "pushed": True,
            "method": "merge-then-git-push",
            "new_local_sha": new_sha[:12],
        }

    if "network:timeout" in msg or "timeout" in msg.lower():
        print("[gh_sync] git network blocked — falling back to REST API", flush=True)
        return _api_push(
            token,
            message
            or f"chore: content-sync (local +{len(commits_ahead)}, remote +{len(commits_behind)})",
        )

    return {"ok": False, "error": f"Push failed: {msg}"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    api_only = "--api-only" in sys.argv
    message = ""
    for i, arg in enumerate(sys.argv):
        if arg == "--message" and i + 1 < len(sys.argv):
            message = sys.argv[i + 1]
            break

    result = gh_sync(dry_run=dry_run, message=message, api_only=api_only)
    print()
    for k, v in result.items():
        print(f"  {k:<22} {v}")

    sys.exit(0 if result.get("ok") else 1)

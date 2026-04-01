"""scripts/git_auto_push.py — Automated git commit + push to GitHub.

Uses the GitHub REST API (via requests) to push, bypassing any
credential prompt issues in sandboxed environments.

Safe to run any time — only commits if there are actual changes.
Requires GITHUB_TOKEN secret for push.

Usage:
    python scripts/git_auto_push.py                         # commit + push
    python scripts/git_auto_push.py --dry-run               # show what would happen
    python scripts/git_auto_push.py --message "My message"  # custom commit message
    python scripts/git_auto_push.py --no-push               # commit only, no push
"""

from __future__ import annotations

import base64
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REMOTE_URL = "https://github.com/KiloMusician/Dev-Mentor.git"
GH_REPO = "KiloMusician/Dev-Mentor"
GH_BRANCH = "main"
RUNTIME_EXCLUDES = {"tasks/queue.json"}


def run(
    cmd: str | list[str], check: bool = False, timeout: int = 30
) -> tuple[int, str, str]:
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


def has_changes() -> bool:
    return bool(_filtered_status_lines())


def _filtered_status_lines() -> list[str]:
    _, out, _ = run("git status --short")
    lines = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path in RUNTIME_EXCLUDES:
            continue
        lines.append(line)
    return lines


def make_commit_message(custom: str = "") -> str:
    if custom:
        return custom
    ts = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    lines = [l[3:].strip() for l in _filtered_status_lines()]
    if not lines:
        return f"runtime: workspace update [{ts}]"
    # Show up to 3 file names so the log is scannable from VS Code GitLens
    shown = lines[:3]
    remainder = len(lines) - len(shown)
    file_summary = ", ".join(shown)
    if remainder > 0:
        file_summary += f" (+{remainder} more)"
    return f"runtime: {file_summary} [{ts}]"


def configure_git() -> None:
    run('git config user.name "DevMentor Agent"')
    run('git config user.email "agent@devmentor.local"')


def _clear_stale_lock() -> bool:
    """Remove .git/index.lock if it is empty (0-byte stale lock).
    Returns True if a lock was removed, False if nothing to do.
    Stale locks are left by crashed git processes; removing a 0-byte lock is safe.
    """
    lock = REPO_ROOT / ".git" / "index.lock"
    try:
        if lock.exists() and lock.stat().st_size == 0:
            lock.unlink()
            print("[auto-push] Removed stale empty .git/index.lock", flush=True)
            return True
    except OSError as exc:
        print(f"[auto-push] Could not remove stale lock: {exc}", flush=True)
    return False


def _stage_and_commit(message: str) -> tuple[bool, str]:
    """Stage all changes and commit. Returns (committed, message)."""
    if not has_changes():
        return False, "Nothing to commit after filtering runtime-only paths."
    _clear_stale_lock()
    _, _, add_err = run("git add --all")
    if add_err and "error" in add_err.lower():
        return False, f"git add failed: {add_err}"

    if RUNTIME_EXCLUDES:
        run(["git", "reset", "HEAD", "--", *sorted(RUNTIME_EXCLUDES)])

    _, _, commit_err = run(["git", "commit", "-m", message])
    if "nothing to commit" in commit_err:
        return False, "Nothing to commit after staging."
    return True, message


def _gh_api_push() -> tuple[bool, str]:
    """Push the latest commit to GitHub.
    Strategy:
      1. Try native `git push` with .env.local token (preserves commit ancestry).
      2. Fall back to REST API blob-upload if git networking is blocked (timeout).
    """
    # Token resolution priority:
    #   1. GITHUB_PERSONAL_ACCESS_TOKEN (Replit-managed integration — always fresh)
    #   2. .env.local GITHUB_TOKEN (local override)
    #   3. GITHUB_TOKEN env var (user secret — may be stale)
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        env_local = REPO_ROOT / ".env.local"
        if env_local.exists():
            for line in env_local.read_text().splitlines():
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not token:
        token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return (
            False,
            "No GitHub token found (set GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN)",
        )

    # --- Attempt 1: native git push (preserves full commit ancestry) ---
    orig_url_code, orig_url, _ = run("git remote get-url origin")
    authed_url = f"https://x-access-token:{token}@github.com/{GH_REPO}.git"
    run(f"git remote set-url origin {authed_url}")
    try:
        code, out, err = run(["git", "push", "origin", GH_BRANCH], timeout=35)
    finally:
        run(
            f"git remote set-url origin {orig_url or f'https://github.com/{GH_REPO}.git'}"
        )

    if code == 0:
        return True, out or "git push succeeded"
    if code != 124 and "timeout" not in err.lower():
        # Non-timeout failure (e.g. rejected) — return the error
        return False, f"git push failed (code {code}): {err[:200]}"
    # code==124 or timeout — fall through to REST API fallback

    try:
        import requests
    except ImportError:
        return False, "requests library not available"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base = f"https://api.github.com/repos/{GH_REPO}"

    # 1. Get the current HEAD ref from GitHub
    r = requests.get(f"{base}/git/refs/heads/{GH_BRANCH}", headers=headers, timeout=15)
    if r.status_code != 200:
        return False, f"Could not get ref: {r.status_code} {r.text[:200]}"
    remote_sha = r.json()["object"]["sha"]

    # 2. Get our local HEAD commit SHA
    _, local_sha, _ = run("git rev-parse HEAD")
    if not local_sha:
        return False, "Could not get local HEAD SHA"

    if local_sha == remote_sha:
        # Nothing to push
        return True, "Already up to date"

    # 3. Walk commits between remote_sha and local_sha
    _, commits_str, _ = run(f"git rev-list --reverse {remote_sha}..{local_sha}")
    commits = [c.strip() for c in commits_str.splitlines() if c.strip()]

    # Check if remote is ahead of local (diverged case)
    _, behind_str, _ = run(f"git rev-list --reverse {local_sha}..{remote_sha}")
    commits_behind = [c.strip() for c in behind_str.splitlines() if c.strip()]

    if not commits and not commits_behind:
        return True, "Already up to date"

    if commits_behind and not commits:
        return True, "Remote is ahead of local — run gh_sync.py to reconcile"

    if commits_behind:
        # Diverged: delegate to gh_sync which merges then git-push (preserves ancestry)
        import importlib.util

        sync_path = REPO_ROOT / "scripts" / "gh_sync.py"
        if sync_path.exists():
            spec = importlib.util.spec_from_file_location("gh_sync", sync_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result = mod.gh_sync(
                message=f"auto: sync diverged branches (local +{len(commits)}, remote +{len(commits_behind)})"
            )
            return result.get("ok", False), result.get("message", str(result))
        return (
            False,
            f"Branches diverged (local +{len(commits)}, remote +{len(commits_behind)}) — run scripts/gh_sync.py",
        )

    # 4. For each commit, upload the tree and create a commit via API
    # Simple approach: upload all changed files for the top commit as a single API commit
    _, diff_files_str, _ = run(f"git diff --name-only {remote_sha} {local_sha}")
    changed_files = [f.strip() for f in diff_files_str.splitlines() if f.strip()]

    # Build a new tree on top of remote_sha
    import time as _time

    tree_items = []
    for file_path in changed_files:
        abs_path = REPO_ROOT / file_path
        if not abs_path.exists():
            # Deleted file
            tree_items.append(
                {"path": file_path, "mode": "100644", "type": "blob", "sha": None}
            )
            continue
        try:
            content = abs_path.read_bytes()
        except Exception:
            continue
        # Upload blob (with rate-limit safety delay)
        blob_r = requests.post(
            f"{base}/git/blobs",
            headers=headers,
            json={"content": base64.b64encode(content).decode(), "encoding": "base64"},
            timeout=30,
        )
        _time.sleep(0.3)
        if blob_r.status_code not in (200, 201):
            # Warn but continue — other files should still be pushed
            print(
                f"  [WARN] blob upload failed for {file_path}: {blob_r.status_code}",
                flush=True,
            )
            continue
        tree_items.append(
            {
                "path": file_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_r.json()["sha"],
            }
        )

    if not tree_items:
        return True, "No file changes to push"

    # Get commit message from local HEAD
    _, commit_msg, _ = run("git log -1 --pretty=%B HEAD")

    # Get author info
    _, author_name, _ = run("git log -1 --pretty=%an HEAD")
    _, author_email, _ = run("git log -1 --pretty=%ae HEAD")
    _, author_date, _ = run("git log -1 --pretty=%aI HEAD")

    # Create tree
    tree_r = requests.post(
        f"{base}/git/trees",
        headers=headers,
        json={"base_tree": remote_sha, "tree": tree_items},
        timeout=30,
    )
    if tree_r.status_code not in (200, 201):
        return False, f"Tree creation failed: {tree_r.status_code} {tree_r.text[:200]}"
    tree_sha = tree_r.json()["sha"]

    # Create commit
    commit_r = requests.post(
        f"{base}/git/commits",
        headers=headers,
        json={
            "message": commit_msg.strip(),
            "tree": tree_sha,
            "parents": [remote_sha],
            "author": {
                "name": author_name or "DevMentor Agent",
                "email": author_email or "agent@devmentor.local",
                "date": author_date,
            },
        },
        timeout=30,
    )
    if commit_r.status_code not in (200, 201):
        return (
            False,
            f"Commit creation failed: {commit_r.status_code} {commit_r.text[:200]}",
        )
    new_commit_sha = commit_r.json()["sha"]

    # Update ref
    ref_r = requests.patch(
        f"{base}/git/refs/heads/{GH_BRANCH}",
        headers=headers,
        json={"sha": new_commit_sha, "force": False},
        timeout=15,
    )
    if ref_r.status_code not in (200, 201):
        # Try force update
        ref_r = requests.patch(
            f"{base}/git/refs/heads/{GH_BRANCH}",
            headers=headers,
            json={"sha": new_commit_sha, "force": True},
            timeout=15,
        )
        if ref_r.status_code not in (200, 201):
            return False, f"Ref update failed: {ref_r.status_code} {ref_r.text[:200]}"

    return True, f"Pushed {len(changed_files)} file(s) → commit {new_commit_sha[:8]}"


def push(dry_run: bool = False, no_push: bool = False, message: str = "") -> dict:
    _clear_stale_lock()
    configure_git()

    if not has_changes():
        return {
            "ok": True,
            "message": "No changes to commit.",
            "committed": False,
            "pushed": False,
        }

    if dry_run:
        _, stat, _ = run("git status --short")
        return {"ok": True, "dry_run": True, "would_commit": stat[:400]}

    msg = make_commit_message(message)
    committed, commit_result = _stage_and_commit(msg)
    if not committed:
        return {
            "ok": True,
            "message": commit_result,
            "committed": False,
            "pushed": False,
        }

    result: dict = {"ok": True, "committed": True, "message": msg, "pushed": False}

    if no_push:
        return result

    pushed, push_result = _gh_api_push()
    result["pushed"] = pushed
    if pushed:
        result["remote"] = REMOTE_URL
        result["push_detail"] = push_result
    else:
        result["push_warning"] = push_result
        result["hint"] = "Check GITHUB_TOKEN secret and repo permissions."

    return result


def main():
    dry_run = "--dry-run" in sys.argv
    no_push = "--no-push" in sys.argv
    custom_msg = ""
    for i, arg in enumerate(sys.argv):
        if arg == "--message" and i + 1 < len(sys.argv):
            custom_msg = sys.argv[i + 1]
            break

    result = push(dry_run=dry_run, no_push=no_push, message=custom_msg)
    for k, v in result.items():
        print(f"  {k:<18} {v}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())

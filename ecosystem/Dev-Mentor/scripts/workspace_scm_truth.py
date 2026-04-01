#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = ROOT / "TerminalKeeper.ecosystem.code-workspace"
STATE_PATH = ROOT / "state" / "workspace_scm_truth.json"
WINDOWS_GIT = Path("/mnt/c/Program Files/Git/cmd/git.exe")
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".cache",
    "dist",
    "build",
}
SKIP_NESTED_PREFIXES = ("_", "tmp", "temp")


@dataclass
class RepoStatus:
    path: str
    label: str
    branch: str | None
    ahead: int
    behind: int
    pending_count: int
    tracked_count: int
    untracked_count: int
    files: list[str]
    git_command: str
    nested: bool
    notes: list[str]
    error: str | None = None


def _run(
    cmd: list[str], cwd: Path, timeout: int = 30
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _windows_path(path: Path) -> str:
    resolved = path.resolve()
    text = resolved.as_posix()
    if text.startswith("/mnt/") and len(text) > 6:
        drive = text[5].upper()
        suffix = text[6:]
        return f"{drive}:{suffix.replace('/', os.sep)}"
    return str(resolved)


def choose_git_command(repo_path: Path) -> list[str]:
    resolved = repo_path.resolve()
    if str(resolved).startswith("/mnt/") and WINDOWS_GIT.exists():
        return [str(WINDOWS_GIT), "-C", _windows_path(resolved)]
    return ["git", "-C", str(resolved)]


def load_jsonc(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    return json.loads(text)


def resolve_workspace_path(raw_path: str) -> Path:
    text = raw_path.strip()
    match = re.match(r"^([a-zA-Z]):[\\/](.*)$", text)
    if match and os.name != "nt":
        drive = match.group(1).lower()
        remainder = match.group(2).replace("\\", "/")
        return (Path("/mnt") / drive / remainder).resolve()
    return Path(text).resolve()


def collect_boundary_notes(repo_path: Path) -> list[str]:
    notes: list[str] = []
    resolved = repo_path.resolve()

    if (
        str(resolved).startswith("/mnt/c/")
        and resolved.name.lower() == "simulatedverse"
    ):
        notes.append(
            "Windows-mounted WSL worktree: status scans may be slow; prefer Windows git or repo-local git:doctor when SCM checks stall."
        )

    if shutil.which("git-lfs") is None:
        for hook_name in ("pre-push", "post-checkout", "post-merge", "post-commit"):
            hook_path = resolved / ".git" / "hooks" / hook_name
            try:
                if hook_path.exists() and "git lfs" in hook_path.read_text(
                    encoding="utf-8", errors="ignore"
                ):
                    notes.append(
                        "git-lfs is missing on PATH while repo hooks depend on it; hook failures may be environmental rather than repo corruption."
                    )
                    break
            except OSError:
                continue

    return notes


def load_workspace_folders(workspace_path: Path) -> list[tuple[str, Path]]:
    data = load_jsonc(workspace_path)
    folders: list[tuple[str, Path]] = []
    for item in data.get("folders", []):
        path = resolve_workspace_path(item["path"])
        label = str(item.get("name") or path.name)
        folders.append((label, path))
    return folders


def _iter_candidate_dirs(root: Path, max_depth: int) -> Iterable[Path]:
    queue: list[tuple[Path, int]] = [(root, 0)]
    while queue:
        current, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue
            name = entry.name
            if name in SKIP_DIRS:
                continue
            candidate = Path(entry.path)
            yield candidate
            queue.append((candidate, depth + 1))


def _allow_nested_repo(path: Path) -> bool:
    name = path.name.lower()
    return not any(name.startswith(prefix) for prefix in SKIP_NESTED_PREFIXES)


def discover_repos_from_folder(
    label: str, root: Path, max_depth: int = 2
) -> list[tuple[str, Path, bool]]:
    repos: list[tuple[str, Path, bool]] = []
    seen: set[Path] = set()

    def add(found_label: str, path: Path, nested: bool) -> None:
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        repos.append((found_label, resolved, nested))

    if (root / ".git").exists():
        add(label, root, False)

    for candidate in _iter_candidate_dirs(root, max_depth):
        if (candidate / ".git").exists() and _allow_nested_repo(candidate):
            add(f"{label}:{candidate.name}", candidate, True)
    return repos


def discover_workspace_repos(workspace_path: Path) -> list[tuple[str, Path, bool]]:
    repos: list[tuple[str, Path, bool]] = []
    seen: set[Path] = set()
    for label, folder in load_workspace_folders(workspace_path):
        for found_label, repo_path, nested in discover_repos_from_folder(label, folder):
            if repo_path in seen:
                continue
            seen.add(repo_path)
            repos.append((found_label, repo_path, nested))
    return repos


def parse_porcelain(output: str) -> tuple[int, int, list[str]]:
    tracked = 0
    untracked = 0
    files: list[str] = []
    for raw in output.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        status = line[:2]
        path = line[3:] if len(line) > 3 else ""
        files.append(path or line)
        if status == "??":
            untracked += 1
        else:
            tracked += 1
    return tracked, untracked, files


def collect_repo_status(label: str, repo_path: Path, nested: bool) -> RepoStatus:
    git_base = choose_git_command(repo_path)
    git_display = " ".join(git_base[:1])
    notes = collect_boundary_notes(repo_path)

    try:
        branch_proc = _run([*git_base, "branch", "--show-current"], repo_path)
        branch = branch_proc.stdout.strip() or None
    except subprocess.TimeoutExpired:
        branch = None
        notes.append("Timed out while resolving branch name.")

    ahead = 0
    behind = 0
    try:
        upstream_proc = _run(
            [*git_base, "rev-list", "--left-right", "--count", "@{upstream}...HEAD"],
            repo_path,
        )
        if upstream_proc.returncode == 0 and upstream_proc.stdout.strip():
            parts = upstream_proc.stdout.strip().split()
            if len(parts) == 2:
                behind = int(parts[0])
                ahead = int(parts[1])
    except subprocess.TimeoutExpired:
        notes.append("Timed out while checking ahead/behind against upstream.")

    try:
        status_proc = _run(
            [*git_base, "status", "--porcelain=v1"], repo_path, timeout=45
        )
    except subprocess.TimeoutExpired:
        return RepoStatus(
            path=str(repo_path),
            label=label,
            branch=branch,
            ahead=ahead,
            behind=behind,
            pending_count=0,
            tracked_count=0,
            untracked_count=0,
            files=[],
            git_command=git_display,
            nested=nested,
            notes=notes + ["git status timed out after 45s."],
            error="git status timed out",
        )

    if status_proc.returncode != 0:
        return RepoStatus(
            path=str(repo_path),
            label=label,
            branch=branch,
            ahead=ahead,
            behind=behind,
            pending_count=0,
            tracked_count=0,
            untracked_count=0,
            files=[],
            git_command=git_display,
            nested=nested,
            notes=notes,
            error=(status_proc.stderr or status_proc.stdout).strip()
            or f"git status failed ({status_proc.returncode})",
        )

    tracked, untracked, files = parse_porcelain(status_proc.stdout)
    return RepoStatus(
        path=str(repo_path),
        label=label,
        branch=branch,
        ahead=ahead,
        behind=behind,
        pending_count=tracked + untracked,
        tracked_count=tracked,
        untracked_count=untracked,
        files=files,
        git_command=git_display,
        nested=nested,
        notes=notes,
        error=None,
    )


def build_report(workspace_path: Path) -> dict:
    repos = [
        collect_repo_status(label, path, nested)
        for label, path, nested in discover_workspace_repos(workspace_path)
    ]
    report = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "workspace_file": str(workspace_path.resolve()),
        "repo_count": len(repos),
        "pending_repo_count": sum(1 for repo in repos if repo.pending_count),
        "total_pending_files": sum(repo.pending_count for repo in repos),
        "repos": [asdict(repo) for repo in repos],
    }
    return report


def save_report(report: dict, path: Path = STATE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def print_report(report: dict) -> None:
    print(f"Workspace: {report['workspace_file']}")
    print(
        f"Repos: {report['repo_count']}  Pending repos: {report['pending_repo_count']}  Pending files: {report['total_pending_files']}"
    )
    for repo in report["repos"]:
        branch = repo["branch"] or "detached"
        counts = f"ahead {repo['ahead']} / behind {repo['behind']} / pending {repo['pending_count']}"
        nested = " nested" if repo["nested"] else ""
        print(f"- {repo['label']} [{branch}]{nested}")
        print(f"  {repo['path']}")
        print(f"  {counts}")
        if repo.get("error"):
            print(f"  error: {repo['error']}")
            for note in repo.get("notes", []):
                print(f"  note: {note}")
            continue
        for note in repo.get("notes", []):
            print(f"  note: {note}")
        for path in repo["files"][:8]:
            print(f"  · {path}")
        if len(repo["files"]) > 8:
            print(f"  · ... +{len(repo['files']) - 8} more")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Authoritative workspace SCM truth for multi-repo/nested-repo workspaces"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE,
        help="Path to .code-workspace file",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save report to state/workspace_scm_truth.json",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = build_report(args.workspace)
    if args.save:
        save_report(report)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0 if report["pending_repo_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

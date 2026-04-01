"""GitNexus - lightweight Git + ecosystem orchestration surface.

This module turns the long-planned GitNexus concept into a concrete,
deployable capability for NuSyQ-Hub without depending on heavyweight
GitPython or remote APIs.

Current scope:
- discover the known local ecosystem repositories
- inspect each repository using the git CLI
- expose a stable matrix for operators, MCP surfaces, or HTTP clients
- optionally run as a small FastAPI app on port 9001
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

try:
    from fastapi import APIRouter, FastAPI, HTTPException

    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    FASTAPI_AVAILABLE = False
    APIRouter = None
    FastAPI = None
    HTTPException = None

from src.utils.repo_path_resolver import get_repo_path

logger = logging.getLogger(__name__)

DEFAULT_PORT = 9001
router = APIRouter(prefix="/api/gitnexus", tags=["gitnexus"]) if FASTAPI_AVAILABLE else None


@dataclass(slots=True)
class RepoSnapshot:
    """Normalized git state for one ecosystem repository."""

    repo_id: str
    path: str
    exists: bool
    is_git_repo: bool
    status: str
    branch: str | None = None
    head: str | None = None
    head_short: str | None = None
    last_commit_subject: str | None = None
    last_commit_at: str | None = None
    remote_origin: str | None = None
    staged_changes: int = 0
    unstaged_changes: int = 0
    untracked_changes: int = 0
    dirty: bool = False
    ahead: int | None = None
    behind: int | None = None
    error: str | None = None


class GitNexus:
    """Inspect and summarize git state across the local NuSyQ ecosystem."""

    def __init__(self) -> None:
        self.repo_paths = self._discover_repo_paths()

    def _discover_repo_paths(self) -> dict[str, Path]:
        """Resolve the known local repositories with portable fallbacks."""
        hub_root = Path(get_repo_path("NUSYQ_HUB_ROOT"))
        user_root = hub_root.parents[2] if len(hub_root.parents) > 2 else Path.home()

        concept_env = os.getenv("CONCEPT_ROOT")
        dev_mentor_env = os.getenv("DEV_MENTOR_ROOT")
        terminal_depths_env = os.getenv("TERMINALDEPTHS_ROOT")

        concept_candidates = [
            Path(concept_env) if concept_env else None,
            Path("/mnt/c/CONCEPT"),
            Path("C:/CONCEPT"),
            user_root / "CONCEPT",
        ]
        dev_mentor_candidates = [
            Path(dev_mentor_env) if dev_mentor_env else None,
            user_root / "Dev-Mentor",
            hub_root.parents[2] / "Dev-Mentor" if len(hub_root.parents) > 2 else None,
            Path("/mnt/c/Users/keath/Dev-Mentor"),
            Path("C:/Users/keath/Dev-Mentor"),
        ]
        simulatedverse_root = Path(get_repo_path("SIMULATEDVERSE_ROOT"))
        nusyq_root = Path(get_repo_path("NUSYQ_ROOT"))

        def _pick(candidates: list[Path | None], fallback: Path) -> Path:
            for candidate in candidates:
                if candidate and candidate.exists():
                    return candidate
            return fallback

        concept_root = _pick(concept_candidates, Path("/mnt/c/CONCEPT"))
        dev_mentor_root = _pick(dev_mentor_candidates, user_root / "Dev-Mentor")

        terminal_depths_root = Path(terminal_depths_env) if terminal_depths_env else dev_mentor_root
        if not terminal_depths_root.exists():
            terminal_depths_root = dev_mentor_root

        return {
            "concept": concept_root,
            "dev_mentor": dev_mentor_root,
            "terminaldepths": terminal_depths_root,
            "simulatedverse": simulatedverse_root,
            "nusyq": nusyq_root,
            "nusyq_hub": hub_root,
        }

    @staticmethod
    def _run_git(
        repo_path: Path, *args: str, timeout_seconds: float = 5
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command in a repo and return decoded output."""
        try:
            return subprocess.run(
                ["git", *args],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(
                args=["git", *args],
                returncode=124,
                stdout=exc.stdout or "",
                stderr=f"git command timed out after {timeout_seconds}s: {' '.join(args)}",
            )

    @staticmethod
    def _count_status_lines(status_lines: list[str]) -> tuple[int, int]:
        """Count staged and unstaged changes from porcelain lines."""
        staged = 0
        unstaged = 0

        for line in status_lines:
            if not line:
                continue
            if len(line) >= 2:
                if line[0] != " ":
                    staged += 1
                if line[1] != " ":
                    unstaged += 1

        return staged, unstaged

    def inspect_repo(self, repo_id: str) -> RepoSnapshot:
        """Inspect one configured repository."""
        repo_path = self.repo_paths[repo_id]

        if not repo_path.exists():
            return RepoSnapshot(
                repo_id=repo_id,
                path=str(repo_path),
                exists=False,
                is_git_repo=False,
                status="missing",
                error="Repository path does not exist",
            )

        if not (repo_path / ".git").exists():
            return RepoSnapshot(
                repo_id=repo_id,
                path=str(repo_path),
                exists=True,
                is_git_repo=False,
                status="not_git_repo",
                error="Path exists but is not a Git repository",
            )

        branch_proc = self._run_git(
            repo_path, "rev-parse", "--abbrev-ref", "HEAD", timeout_seconds=2
        )
        head_proc = self._run_git(repo_path, "rev-parse", "HEAD", timeout_seconds=2)
        status_proc = self._run_git(repo_path, "status", "--porcelain", "-uno", timeout_seconds=1)
        log_proc = self._run_git(
            repo_path, "log", "-1", "--pretty=format:%h%n%H%n%s%n%cI", timeout_seconds=2
        )
        remote_proc = self._run_git(
            repo_path, "config", "--get", "remote.origin.url", timeout_seconds=2
        )
        upstream_proc = self._run_git(
            repo_path,
            "rev-list",
            "--left-right",
            "--count",
            "@{upstream}...HEAD",
            timeout_seconds=2,
        )

        status_lines = [line for line in status_proc.stdout.splitlines() if line.strip()]
        staged, unstaged = self._count_status_lines(status_lines)
        cleanliness_known = status_proc.returncode != 124
        dirty = bool(status_lines) if cleanliness_known else False

        ahead: int | None = None
        behind: int | None = None
        if upstream_proc.returncode == 0:
            try:
                behind_str, ahead_str = upstream_proc.stdout.strip().split()
                behind = int(behind_str)
                ahead = int(ahead_str)
            except (TypeError, ValueError):
                ahead = None
                behind = None

        last_commit_subject = None
        last_commit_at = None
        head_short = None
        head_full = None
        if log_proc.returncode == 0:
            log_lines = log_proc.stdout.splitlines()
            if len(log_lines) >= 4:
                head_short, head_full, last_commit_subject, last_commit_at = log_lines[:4]

        errors: list[str] = []
        for proc in (branch_proc, head_proc):
            if proc.returncode != 0 and proc.stderr.strip():
                errors.append(proc.stderr.strip())
        if status_proc.returncode not in (0, 124) and status_proc.stderr.strip():
            errors.append(status_proc.stderr.strip())

        if errors:
            state = "error"
        elif not cleanliness_known:
            state = "unknown"
        elif dirty:
            state = "dirty"
        else:
            state = "clean"

        return RepoSnapshot(
            repo_id=repo_id,
            path=str(repo_path),
            exists=True,
            is_git_repo=True,
            status=state,
            branch=branch_proc.stdout.strip() or None,
            head=head_proc.stdout.strip() or head_full,
            head_short=head_short,
            last_commit_subject=last_commit_subject,
            last_commit_at=last_commit_at,
            remote_origin=remote_proc.stdout.strip() or None,
            staged_changes=staged,
            unstaged_changes=unstaged,
            untracked_changes=0,
            dirty=dirty,
            ahead=ahead,
            behind=behind,
            error=" | ".join(errors) if errors else None,
        )

    def get_matrix(self) -> dict[str, Any]:
        """Return an ecosystem-wide git status matrix."""
        snapshots: dict[str, dict[str, Any]] = {}
        inspected_by_path: dict[Path, dict[str, Any]] = {}

        for repo_id, repo_path in self.repo_paths.items():
            resolved = repo_path.resolve(strict=False)
            if resolved in inspected_by_path:
                snapshot = dict(inspected_by_path[resolved])
                snapshot["repo_id"] = repo_id
            else:
                snapshot = asdict(self.inspect_repo(repo_id))
                inspected_by_path[resolved] = dict(snapshot)
            snapshots[repo_id] = snapshot

        available = sum(1 for snapshot in snapshots.values() if snapshot["exists"])
        git_repos = sum(1 for snapshot in snapshots.values() if snapshot["is_git_repo"])
        dirty_repos = sum(1 for snapshot in snapshots.values() if snapshot["dirty"])
        missing_repos = sum(1 for snapshot in snapshots.values() if not snapshot["exists"])

        return {
            "service": "gitnexus",
            "status": "healthy" if missing_repos == 0 else "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "summary": {
                "configured_repos": len(self.repo_paths),
                "available_repos": available,
                "git_repos": git_repos,
                "dirty_repos": dirty_repos,
                "missing_repos": missing_repos,
            },
            "repos": snapshots,
        }

    def get_health(self) -> dict[str, Any]:
        """Return a compact service health payload."""
        matrix = self.get_matrix()
        return {
            "service": "gitnexus",
            "status": matrix["status"],
            "timestamp": matrix["timestamp"],
            "summary": matrix["summary"],
        }


def _get_gitnexus() -> GitNexus:
    return GitNexus()


if FASTAPI_AVAILABLE:

    @router.get("/health")
    def gitnexus_health() -> dict[str, Any]:
        """FastAPI health endpoint for GitNexus."""
        return _get_gitnexus().get_health()

    @router.get("/matrix")
    def gitnexus_matrix() -> dict[str, Any]:
        """Return the current cross-repo git matrix."""
        return _get_gitnexus().get_matrix()

    @router.get("/repos/{repo_id}")
    def gitnexus_repo(repo_id: str) -> dict[str, Any]:
        """Return one repo snapshot by id."""
        nexus = _get_gitnexus()
        if repo_id not in nexus.repo_paths:
            raise HTTPException(status_code=404, detail=f"Unknown repo_id: {repo_id}")
        return asdict(nexus.inspect_repo(repo_id))


def build_app() -> FastAPI:
    """Build a standalone FastAPI app for GitNexus."""
    if not FASTAPI_AVAILABLE:  # pragma: no cover - optional dependency
        raise RuntimeError("FastAPI is not installed")

    app = FastAPI(
        title="GitNexus", version="1.0.0", description="Ecosystem git matrix for NuSyQ-Hub"
    )
    app.include_router(router)

    @app.get("/")
    def root() -> dict[str, Any]:
        return {
            "service": "gitnexus",
            "status": "operational",
            "endpoints": {
                "health": "/api/gitnexus/health",
                "matrix": "/api/gitnexus/matrix",
            },
        }

    return app


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Inspect local ecosystem repositories with GitNexus."
    )
    parser.add_argument("--json", action="store_true", help="Print the full matrix as JSON.")
    parser.add_argument("--repo", help="Print one repository snapshot by id.")
    parser.add_argument("--serve", action="store_true", help="Run the standalone FastAPI app.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port for --serve mode.")
    args = parser.parse_args(argv)

    nexus = GitNexus()

    if args.serve:
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI is required for --serve mode")
        try:
            import uvicorn
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("uvicorn is required for --serve mode") from exc

        uvicorn.run(build_app(), host="127.0.0.1", port=args.port)
        return 0

    if args.repo:
        if args.repo not in nexus.repo_paths:
            raise SystemExit(f"Unknown repo id: {args.repo}")
        print(json.dumps(asdict(nexus.inspect_repo(args.repo)), indent=2))
        return 0

    payload = nexus.get_matrix() if args.json else nexus.get_health()
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""GitKraken MCP Bridge for NuSyQ ecosystem.

Provides integration with GitKraken MCP tools for multi-platform git operations,
cross-provider issue/PR management, and GitLens features.

MCP Tool Prefix: mcp_gitkraken_
Total Tools: 24

Categories:
- Git Operations: Core git commands (add, commit, push, stash, worktree)
- GitLens Features: AI commit composer, launchpad, code review
- Cross-Provider Issues: GitHub, GitLab, Jira, Azure DevOps, Linear
- Cross-Provider PRs: Multi-platform pull request management
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from urllib import error, request

try:
    from src.config.service_config import ServiceConfig
except ImportError:  # pragma: no cover - standalone fallback
    ServiceConfig = None

logger = logging.getLogger(__name__)


class GitProvider(Enum):
    """Supported git providers."""

    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"
    UNKNOWN = "unknown"


class IssueProvider(Enum):
    """Supported issue tracking providers."""

    GITHUB = "github"
    GITLAB = "gitlab"
    JIRA = "jira"
    AZURE_DEVOPS = "azure_devops"
    LINEAR = "linear"


@dataclass
class GitStatus:
    """Git repository status."""

    branch: str
    clean: bool
    staged_count: int = 0
    unstaged_count: int = 0
    untracked_count: int = 0
    ahead: int = 0
    behind: int = 0


@dataclass
class GitKrakenBridgeStatus:
    """GitKraken bridge availability status."""

    available: bool
    git_installed: bool = True
    gitlens_available: bool = False
    providers_detected: list[str] = field(default_factory=list)
    message: str = ""
    mcp_server_running: bool = False
    mcp_server_url: str = ""


# ── MCP Tool Catalog ──────────────────────────────────────────────────────────

GITKRAKEN_MCP_TOOLS: dict[str, dict[str, Any]] = {
    # Git Operations
    "git_add_or_commit": {
        "category": "git",
        "description": "Stage files and create commits",
        "parameters": ["files", "message", "amend"],
        "usage": "Stage and commit changes in one operation",
    },
    "git_blame": {
        "category": "git",
        "description": "Show file blame/annotation",
        "parameters": ["file", "line_range"],
        "usage": "Show who last modified each line of a file",
    },
    "git_branch": {
        "category": "git",
        "description": "Branch management operations",
        "parameters": ["action", "name", "base"],
        "usage": "Create, delete, rename, or list branches",
    },
    "git_checkout": {
        "category": "git",
        "description": "Checkout branch or commit",
        "parameters": ["target", "create_branch"],
        "usage": "Switch branches or restore files",
    },
    "git_log_or_diff": {
        "category": "git",
        "description": "View commit history or diffs",
        "parameters": ["log", "diff", "range", "file"],
        "usage": "Inspect commit history or compare changes",
    },
    "git_push": {
        "category": "git",
        "description": "Push commits to remote",
        "parameters": ["remote", "branch", "force", "tags"],
        "usage": "Upload local commits to remote repository",
    },
    "git_stash": {
        "category": "git",
        "description": "Stash management",
        "parameters": ["action", "message", "index"],
        "usage": "Save, list, apply, or drop stashed changes",
    },
    "git_status": {
        "category": "git",
        "description": "Repository status",
        "parameters": ["short", "porcelain"],
        "usage": "Show working tree status",
    },
    "git_worktree": {
        "category": "git",
        "description": "Worktree management",
        "parameters": ["action", "path", "branch"],
        "usage": "Manage multiple working trees",
    },
    # GitLens Features
    "gitlens_commit_composer": {
        "category": "gitlens",
        "description": "AI-powered commit message generation",
        "parameters": ["diff", "context", "style"],
        "usage": "Generate semantic commit messages with AI assistance",
    },
    "gitlens_launchpad": {
        "category": "gitlens",
        "description": "PR/Issue launchpad view",
        "parameters": ["filter", "provider"],
        "usage": "Quick access to PRs and issues assigned to you",
    },
    "gitlens_start_review": {
        "category": "gitlens",
        "description": "Start code review session",
        "parameters": ["pr_url", "branch"],
        "usage": "Begin structured code review workflow",
    },
    "gitlens_start_work": {
        "category": "gitlens",
        "description": "Start work on issue",
        "parameters": ["issue_id", "provider", "branch_pattern"],
        "usage": "Create branch and associate with issue tracker",
    },
    # Cross-Provider Issues
    "issues_assigned_to_me": {
        "category": "issues",
        "description": "List issues assigned to current user",
        "parameters": ["provider", "state", "labels"],
        "usage": "Aggregate issues from multiple providers",
    },
    "issues_get_detail": {
        "category": "issues",
        "description": "Get detailed issue information",
        "parameters": ["issue_id", "provider"],
        "usage": "Fetch issue details from any provider",
    },
    "issues_add_comment": {
        "category": "issues",
        "description": "Add comment to issue",
        "parameters": ["issue_id", "provider", "body"],
        "usage": "Comment on issues across providers",
    },
    # Cross-Provider Pull Requests
    "pull_request_assigned_to_me": {
        "category": "pr",
        "description": "List PRs assigned to current user",
        "parameters": ["provider", "state", "role"],
        "usage": "Aggregate PRs from multiple platforms",
    },
    "pull_request_get_detail": {
        "category": "pr",
        "description": "Get detailed PR information",
        "parameters": ["pr_id", "provider"],
        "usage": "Fetch PR details from any provider",
    },
    "pull_request_get_comments": {
        "category": "pr",
        "description": "Get PR comments and reviews",
        "parameters": ["pr_id", "provider"],
        "usage": "Retrieve all comments on a PR",
    },
    "pull_request_create": {
        "category": "pr",
        "description": "Create new pull request",
        "parameters": ["title", "body", "head", "base", "provider"],
        "usage": "Create PR in any supported provider",
    },
    "pull_request_create_review": {
        "category": "pr",
        "description": "Submit PR review",
        "parameters": ["pr_id", "provider", "event", "body", "comments"],
        "usage": "Submit review with approve/request changes/comment",
    },
    # Repository
    "repository_get_file_content": {
        "category": "repo",
        "description": "Get file content from repository",
        "parameters": ["path", "ref", "provider"],
        "usage": "Retrieve file content at specific revision",
    },
    "gitkraken_workspace_list": {
        "category": "workspace",
        "description": "List GitKraken workspaces",
        "parameters": [],
        "usage": "Show configured GitKraken workspaces",
    },
}


class GitKrakenBridge:
    """Bridge to GitKraken MCP tools.

    Provides unified access to:
    - Multi-repo git operations
    - Cross-platform issue tracking
    - AI-powered commit composition
    - Pull request management across providers
    """

    MCP_PREFIX = "mcp_gitkraken_"

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize GitKraken bridge.

        Args:
            workspace_root: Root path for git operations. Defaults to CWD.
        """
        self.workspace_root = workspace_root or Path.cwd()
        self._status: GitKrakenBridgeStatus | None = None
        self._managed_mcp_process: subprocess.Popen[str] | None = None
        self.mcp_server_url = self._resolve_mcp_server_url()

    def _resolve_mcp_server_url(self) -> str:
        """Resolve the MCP server base URL from config/env/defaults."""
        if ServiceConfig is not None:
            try:
                url = ServiceConfig.get_mcp_server_url().rstrip("/")
                if url:
                    return url
            except (AttributeError, OSError, ValueError):
                pass

        env_url = str(os.getenv("MCP_SERVER_URL") or "").strip().rstrip("/")
        if env_url:
            return env_url

        host = str(os.getenv("MCP_SERVER_HOST") or "127.0.0.1").strip() or "127.0.0.1"
        port = str(os.getenv("MCP_SERVER_PORT") or "8081").strip() or "8081"
        if "://" not in host:
            host = f"http://{host}"
        return f"{host.rstrip('/')}:{port}"

    def _mcp_endpoint(self, path: str) -> str:
        return f"{self.mcp_server_url}{path}"

    def _mcp_request(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout_s: float = 5.0,
    ) -> dict[str, Any]:
        data: bytes | None = None
        headers = {"Accept": "application/json"}
        method = "GET"
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
            method = "POST"

        req = request.Request(
            self._mcp_endpoint(path),
            data=data,
            headers=headers,
            method=method,
        )
        with request.urlopen(req, timeout=timeout_s) as response:
            body = response.read().decode("utf-8", errors="replace")
        parsed = json.loads(body) if body else {}
        return parsed if isinstance(parsed, dict) else {"data": parsed}

    def _mcp_is_running(self) -> bool:
        try:
            payload = self._mcp_request("/health", timeout_s=2.0)
        except (OSError, ValueError, error.URLError, error.HTTPError):
            return False
        return str(payload.get("status", "")).lower() in {"healthy", "running", "ok"}

    def _ensure_mcp_server(self, wait_timeout_s: float = 8.0) -> bool:
        if self._mcp_is_running():
            return True

        cmd = [sys.executable, "-m", "src.integration.mcp_server"]
        env = os.environ.copy()
        pythonpath_parts = [str(self.workspace_root)]
        if env.get("PYTHONPATH"):
            pythonpath_parts.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

        try:
            self._managed_mcp_process = subprocess.Popen(
                cmd,
                cwd=self.workspace_root,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except OSError as exc:
            logger.error("Failed to start MCP server: %s", exc)
            return False

        deadline = time.time() + wait_timeout_s
        while time.time() < deadline:
            if self._mcp_is_running():
                return True
            time.sleep(0.25)
        return False

    def probe(self) -> GitKrakenBridgeStatus:
        """Probe GitKraken MCP availability.

        Returns:
            GitKrakenBridgeStatus with availability details.
        """
        import shutil

        git_installed = shutil.which("git") is not None

        # Detect git providers from remotes
        providers_detected: list[str] = []
        if git_installed and (self.workspace_root / ".git").exists():
            providers_detected = self._detect_providers()

        # GitLens is available if the extension is installed
        # (we assume it is since GitKraken MCP requires it)
        gitlens_available = True

        mcp_running = self._mcp_is_running()

        self._status = GitKrakenBridgeStatus(
            available=git_installed,
            git_installed=git_installed,
            gitlens_available=gitlens_available,
            providers_detected=providers_detected,
            message=(
                "GitKraken MCP ready"
                if git_installed and mcp_running
                else (
                    "GitKraken git bridge ready (MCP dormant)"
                    if git_installed
                    else "Git not installed"
                )
            ),
            mcp_server_running=mcp_running,
            mcp_server_url=self.mcp_server_url,
        )

        try:
            from src.system.agent_awareness import emit as _emit

            _detail = f"git={git_installed} mcp={mcp_running} providers={providers_detected}"
            _emit("agents", f"GitKraken probe: {_detail}", level="INFO", source="gitkraken_bridge")
        except Exception:
            pass

        return self._status

    def _detect_providers(self) -> list[str]:
        """Detect git providers from remote URLs.

        Returns:
            List of detected provider names.
        """
        import subprocess

        providers: set[str] = set()

        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                cwd=self.workspace_root,
                timeout=5,
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if "github.com" in output:
                    providers.add("github")
                if "gitlab.com" in output or "gitlab" in output:
                    providers.add("gitlab")
                if "bitbucket.org" in output:
                    providers.add("bitbucket")
                if "dev.azure.com" in output or "visualstudio.com" in output:
                    providers.add("azure_devops")
        except Exception:
            pass

        return sorted(providers)

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a specific MCP tool.

        Args:
            tool_name: Tool name without prefix (e.g., 'git_push').

        Returns:
            Tool metadata dict or None if not found.
        """
        return GITKRAKEN_MCP_TOOLS.get(tool_name)

    def get_tools_by_category(self, category: str) -> list[str]:
        """Get all tools in a category.

        Args:
            category: Category name (git, gitlens, issues, pr, repo, workspace).

        Returns:
            List of tool names in the category.
        """
        return [name for name, info in GITKRAKEN_MCP_TOOLS.items() if info["category"] == category]

    def get_mcp_tool_name(self, tool: str) -> str:
        """Get full MCP tool name with prefix.

        Args:
            tool: Short tool name (e.g., 'git_push').

        Returns:
            Full MCP name (e.g., 'mcp_gitkraken_git_push').
        """
        return f"{self.MCP_PREFIX}{tool}"

    def format_recommendation(self, task_type: str) -> list[str]:
        """Get recommended tools for a task type.

        Args:
            task_type: Type of task (commit, review, issues, prs, blame).

        Returns:
            List of recommended MCP tool names.
        """
        recommendations: dict[str, list[str]] = {
            "commit": ["git_status", "git_add_or_commit", "gitlens_commit_composer"],
            "review": [
                "pull_request_get_detail",
                "pull_request_get_comments",
                "pull_request_create_review",
            ],
            "issues": ["issues_assigned_to_me", "issues_get_detail", "gitlens_start_work"],
            "prs": [
                "pull_request_assigned_to_me",
                "pull_request_get_detail",
                "pull_request_create",
            ],
            "blame": ["git_blame", "git_log_or_diff"],
            "branch": ["git_branch", "git_checkout", "git_worktree"],
        }

        tools = recommendations.get(task_type, [])
        return [self.get_mcp_tool_name(t) for t in tools]

    def execute_tool(
        self, tool_name: str, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a GitKraken-backed MCP tool."""
        if not self._ensure_mcp_server():
            return {
                "status": "failed",
                "error": "mcp_server_unavailable",
                "tool": tool_name,
                "mcp_server_url": self.mcp_server_url,
            }

        payload: dict[str, Any] | None = None
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                payload = self._mcp_request(
                    "/execute",
                    payload={"tool": tool_name, "parameters": parameters or {}},
                    timeout_s=60.0,
                )
                break
            except (OSError, ValueError, error.URLError, error.HTTPError) as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.5)
                    self._ensure_mcp_server(wait_timeout_s=4.0)
                    continue
                return {
                    "status": "failed",
                    "error": f"mcp_execute_failed: {exc}",
                    "tool": tool_name,
                    "mcp_server_url": self.mcp_server_url,
                }

        if payload is None:
            return {
                "status": "failed",
                "error": f"mcp_execute_failed: {last_error or 'no_response'}",
                "tool": tool_name,
                "mcp_server_url": self.mcp_server_url,
            }

        if not payload.get("success"):
            return {
                "status": "failed",
                "error": payload.get("error", "tool_execution_failed"),
                "tool": tool_name,
                "mcp_server_url": self.mcp_server_url,
            }

        result = payload.get("result")
        if isinstance(result, dict):
            result.setdefault("tool", tool_name)
            result.setdefault("mcp_server_url", self.mcp_server_url)
            return result

        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "agents",
                f"GitKraken tool: {tool_name} | status=success",
                level="INFO",
                source="gitkraken_bridge",
            )
        except Exception:
            pass

        return {
            "status": "success",
            "result": result,
            "tool": tool_name,
            "mcp_server_url": self.mcp_server_url,
        }

    def execute_git_operation(
        self, operation: str, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a supported git operation through the MCP bridge."""
        op_map = {
            "status": "mcp_gitkraken_git_status",
            "commit": "mcp_gitkraken_git_add_or_commit",
            "push": "mcp_gitkraken_git_push",
        }
        tool_name = op_map.get(operation.strip().lower())
        if tool_name is None:
            return {
                "status": "failed",
                "error": f"unsupported_gitkraken_operation: {operation}",
                "supported_operations": sorted(op_map),
            }
        return self.execute_tool(tool_name, parameters)


# ── Module-Level Functions ────────────────────────────────────────────────────

_bridge: GitKrakenBridge | None = None


def get_bridge(workspace_root: Path | None = None) -> GitKrakenBridge:
    """Get or create GitKraken bridge singleton.

    Args:
        workspace_root: Optional workspace root path.

    Returns:
        GitKrakenBridge instance.
    """
    global _bridge
    if _bridge is None:
        _bridge = GitKrakenBridge(workspace_root)
    return _bridge


def probe_gitkraken() -> dict[str, Any]:
    """Probe GitKraken availability for agent registry.

    Returns:
        Dict with status and detail for agent registry.
    """
    bridge = get_bridge()
    status = bridge.probe()

    if not status.available:
        return {
            "status": "offline",
            "detail": "Git not installed",
        }

    providers = (
        ", ".join(status.providers_detected) if status.providers_detected else "none detected"
    )

    return {
        "status": "online",
        "detail": f"GitKraken MCP: {len(GITKRAKEN_MCP_TOOLS)} tools, providers: {providers}",
    }


def quick_status() -> str:
    """Get quick one-line status for display.

    Returns:
        Status string.
    """
    bridge = get_bridge()
    status = bridge.probe()

    if not status.available:
        return "GitKraken: OFFLINE - Git not installed"

    providers = ", ".join(status.providers_detected) if status.providers_detected else "none"
    return f"GitKraken: ONLINE - {len(GITKRAKEN_MCP_TOOLS)} tools, providers: [{providers}]"


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("GitKraken MCP Bridge - NuSyQ Integration")
    print("=" * 60)

    bridge = get_bridge()
    status = bridge.probe()

    print(f"\nStatus: {'ONLINE' if status.available else 'OFFLINE'}")
    print(f"Git Installed: {status.git_installed}")
    print(f"GitLens Available: {status.gitlens_available}")
    print(f"Providers Detected: {', '.join(status.providers_detected) or 'None'}")

    print(f"\nTotal MCP Tools: {len(GITKRAKEN_MCP_TOOLS)}")
    print("\nTools by Category:")
    for category in ["git", "gitlens", "issues", "pr", "repo", "workspace"]:
        tools = bridge.get_tools_by_category(category)
        print(f"  {category}: {len(tools)} tools")
        for tool in tools:
            info = bridge.get_tool_info(tool)
            if info:
                print(f"    - {tool}: {info['description']}")

    print("\nRecommended Tools for Common Tasks:")
    for task in ["commit", "review", "issues", "prs", "blame"]:
        print(f"  {task}: {', '.join(bridge.format_recommendation(task))}")

    print(f"\nQuick Status: {quick_status()}")

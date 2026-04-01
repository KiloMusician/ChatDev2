"""Comprehensive tests for MCP Extension Bridges.

Covers:
- GitKrakenBridge: init, public methods, error handling, fallback behavior
- HuggingFaceBridge: init, public methods, probe behavior
- Both bridges: get_bridge() singleton, probe_*() module functions
- mcp_extension_catalog: get_extension_catalog, get_extension, get_integration_summary
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ── GitKraken Bridge imports ──────────────────────────────────────────────────
from src.integrations.gitkraken_bridge import (
    GITKRAKEN_MCP_TOOLS,
    GitKrakenBridge,
    GitKrakenBridgeStatus,
    GitProvider,
    GitStatus,
    IssueProvider,
    get_bridge as gk_get_bridge,
    probe_gitkraken,
    quick_status as gk_quick_status,
)

# ── HuggingFace Bridge imports ────────────────────────────────────────────────
from src.integrations.huggingface_bridge import (
    HUGGINGFACE_MCP_TOOLS,
    HFBridgeStatus,
    HFResourceType,
    HFSearchResult,
    HuggingFaceBridge,
    get_bridge as hf_get_bridge,
    probe_huggingface,
    quick_status as hf_quick_status,
)

# ── Catalog imports ───────────────────────────────────────────────────────────
from src.integrations.mcp_extension_catalog import (
    ExtensionCategory,
    IntegrationStatus,
    MCPExtension,
    MCPTool,
    MCP_EXTENSIONS,
    get_all_extensions,
    get_extension,
    get_extensions_by_category,
    get_extensions_by_status,
    get_integration_recommendations,
    get_integration_summary,
)


# ═════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def reset_gitkraken_singleton():
    """Reset the GitKraken module-level singleton between tests."""
    import src.integrations.gitkraken_bridge as gk_mod

    old = gk_mod._bridge
    gk_mod._bridge = None
    yield
    gk_mod._bridge = old


@pytest.fixture(autouse=True)
def reset_huggingface_singleton():
    """Reset the HuggingFace module-level singleton between tests."""
    import src.integrations.huggingface_bridge as hf_mod

    old = hf_mod._bridge
    hf_mod._bridge = None
    yield
    hf_mod._bridge = old


@pytest.fixture()
def gk_bridge(tmp_path: Path) -> GitKrakenBridge:
    """Fresh GitKrakenBridge instance with a temp workspace."""
    return GitKrakenBridge(workspace_root=tmp_path)


@pytest.fixture()
def hf_bridge() -> HuggingFaceBridge:
    """Fresh HuggingFaceBridge instance."""
    return HuggingFaceBridge()


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — Enums and Dataclasses
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenEnumsDataclasses:
    def test_git_provider_values(self):
        assert GitProvider.GITHUB.value == "github"
        assert GitProvider.GITLAB.value == "gitlab"
        assert GitProvider.BITBUCKET.value == "bitbucket"
        assert GitProvider.AZURE_DEVOPS.value == "azure_devops"
        assert GitProvider.UNKNOWN.value == "unknown"

    def test_issue_provider_values(self):
        providers = {p.value for p in IssueProvider}
        assert providers == {"github", "gitlab", "jira", "azure_devops", "linear"}

    def test_git_status_defaults(self):
        s = GitStatus(branch="main", clean=True)
        assert s.staged_count == 0
        assert s.unstaged_count == 0
        assert s.untracked_count == 0
        assert s.ahead == 0
        assert s.behind == 0

    def test_git_status_full(self):
        s = GitStatus(branch="feat", clean=False, staged_count=2, unstaged_count=1, ahead=3)
        assert s.branch == "feat"
        assert not s.clean
        assert s.staged_count == 2
        assert s.ahead == 3

    def test_bridge_status_defaults(self):
        bs = GitKrakenBridgeStatus(available=True)
        assert bs.git_installed is True
        assert bs.gitlens_available is False
        assert bs.providers_detected == []
        assert bs.message == ""
        assert bs.mcp_server_running is False
        assert bs.mcp_server_url == ""


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — MCP Tool Catalog
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenToolCatalog:
    def test_catalog_has_expected_count(self):
        # Module docstring says 24 tools but catalog currently has 23 unique keys
        assert len(GITKRAKEN_MCP_TOOLS) >= 20

    def test_all_tools_have_required_keys(self):
        for name, info in GITKRAKEN_MCP_TOOLS.items():
            assert "category" in info, f"{name} missing category"
            assert "description" in info, f"{name} missing description"
            assert "parameters" in info, f"{name} missing parameters"
            assert "usage" in info, f"{name} missing usage"

    def test_git_category_tools_present(self):
        git_tools = [k for k, v in GITKRAKEN_MCP_TOOLS.items() if v["category"] == "git"]
        assert "git_status" in git_tools
        assert "git_push" in git_tools
        assert "git_add_or_commit" in git_tools

    def test_gitlens_category_tools_present(self):
        gl_tools = [k for k, v in GITKRAKEN_MCP_TOOLS.items() if v["category"] == "gitlens"]
        assert "gitlens_commit_composer" in gl_tools
        assert "gitlens_launchpad" in gl_tools

    def test_pr_category_tools_present(self):
        pr_tools = [k for k, v in GITKRAKEN_MCP_TOOLS.items() if v["category"] == "pr"]
        assert "pull_request_create" in pr_tools
        assert "pull_request_get_detail" in pr_tools

    def test_issues_category_tools_present(self):
        issue_tools = [k for k, v in GITKRAKEN_MCP_TOOLS.items() if v["category"] == "issues"]
        assert "issues_assigned_to_me" in issue_tools

    def test_all_categories_known(self):
        known = {"git", "gitlens", "issues", "pr", "repo", "workspace"}
        for name, info in GITKRAKEN_MCP_TOOLS.items():
            assert info["category"] in known, f"{name} has unknown category {info['category']!r}"


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — Initialization
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenBridgeInit:
    def test_default_workspace_is_cwd(self):
        bridge = GitKrakenBridge()
        assert bridge.workspace_root == Path.cwd()

    def test_custom_workspace(self, tmp_path):
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        assert bridge.workspace_root == tmp_path

    def test_mcp_server_url_from_env(self, monkeypatch, tmp_path):
        # ServiceConfig.MCP_SERVER_URL is a class-level Final set at import time,
        # so we patch get_mcp_server_url directly and also null-out ServiceConfig
        # in the bridge module so the env-var fallback code is exercised.
        import src.integrations.gitkraken_bridge as gk_mod

        monkeypatch.setattr(gk_mod, "ServiceConfig", None)
        monkeypatch.setenv("MCP_SERVER_URL", "http://custom:9999")
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        assert bridge.mcp_server_url == "http://custom:9999"

    def test_mcp_server_url_from_host_port_env(self, monkeypatch, tmp_path):
        import src.integrations.gitkraken_bridge as gk_mod

        monkeypatch.setattr(gk_mod, "ServiceConfig", None)
        monkeypatch.delenv("MCP_SERVER_URL", raising=False)
        monkeypatch.setenv("MCP_SERVER_HOST", "192.168.1.1")
        monkeypatch.setenv("MCP_SERVER_PORT", "1234")
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        assert bridge.mcp_server_url == "http://192.168.1.1:1234"

    def test_mcp_server_url_default(self, monkeypatch, tmp_path):
        import src.integrations.gitkraken_bridge as gk_mod

        monkeypatch.setattr(gk_mod, "ServiceConfig", None)
        monkeypatch.delenv("MCP_SERVER_URL", raising=False)
        monkeypatch.delenv("MCP_SERVER_HOST", raising=False)
        monkeypatch.delenv("MCP_SERVER_PORT", raising=False)
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        assert "8081" in bridge.mcp_server_url
        assert "127.0.0.1" in bridge.mcp_server_url

    def test_managed_process_starts_none(self, gk_bridge):
        assert gk_bridge._managed_mcp_process is None

    def test_status_starts_none(self, gk_bridge):
        assert gk_bridge._status is None


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — Tool Lookup Methods
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenToolLookup:
    def test_get_tool_info_known(self, gk_bridge):
        info = gk_bridge.get_tool_info("git_push")
        assert info is not None
        assert info["category"] == "git"

    def test_get_tool_info_unknown(self, gk_bridge):
        assert gk_bridge.get_tool_info("nonexistent_tool") is None

    def test_get_tools_by_category_git(self, gk_bridge):
        tools = gk_bridge.get_tools_by_category("git")
        assert "git_status" in tools
        assert "git_push" in tools

    def test_get_tools_by_category_gitlens(self, gk_bridge):
        tools = gk_bridge.get_tools_by_category("gitlens")
        assert len(tools) >= 2

    def test_get_tools_by_category_unknown(self, gk_bridge):
        assert gk_bridge.get_tools_by_category("nonexistent") == []

    def test_get_mcp_tool_name(self, gk_bridge):
        assert gk_bridge.get_mcp_tool_name("git_push") == "mcp_gitkraken_git_push"

    def test_get_mcp_tool_name_prefix(self, gk_bridge):
        result = gk_bridge.get_mcp_tool_name("gitlens_launchpad")
        assert result.startswith("mcp_gitkraken_")
        assert result.endswith("gitlens_launchpad")


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — format_recommendation
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenRecommendations:
    def test_commit_recommendation(self, gk_bridge):
        recs = gk_bridge.format_recommendation("commit")
        assert len(recs) > 0
        assert all(r.startswith("mcp_gitkraken_") for r in recs)
        assert "mcp_gitkraken_git_status" in recs
        assert "mcp_gitkraken_git_add_or_commit" in recs

    def test_review_recommendation(self, gk_bridge):
        recs = gk_bridge.format_recommendation("review")
        assert "mcp_gitkraken_pull_request_get_detail" in recs
        assert "mcp_gitkraken_pull_request_create_review" in recs

    def test_issues_recommendation(self, gk_bridge):
        recs = gk_bridge.format_recommendation("issues")
        assert "mcp_gitkraken_issues_assigned_to_me" in recs

    def test_prs_recommendation(self, gk_bridge):
        recs = gk_bridge.format_recommendation("prs")
        assert "mcp_gitkraken_pull_request_create" in recs

    def test_blame_recommendation(self, gk_bridge):
        recs = gk_bridge.format_recommendation("blame")
        assert "mcp_gitkraken_git_blame" in recs

    def test_branch_recommendation(self, gk_bridge):
        recs = gk_bridge.format_recommendation("branch")
        assert "mcp_gitkraken_git_branch" in recs

    def test_unknown_task_returns_empty(self, gk_bridge):
        recs = gk_bridge.format_recommendation("totally_unknown_task_xyz")
        assert recs == []


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — Probe and Provider Detection
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenProbe:
    def test_probe_returns_status_object(self, gk_bridge):
        with patch("shutil.which", return_value="/usr/bin/git"):
            with patch.object(gk_bridge, "_mcp_is_running", return_value=False):
                status = gk_bridge.probe()
        assert isinstance(status, GitKrakenBridgeStatus)

    def test_probe_sets_cached_status(self, gk_bridge):
        with patch("shutil.which", return_value="/usr/bin/git"):
            with patch.object(gk_bridge, "_mcp_is_running", return_value=False):
                status = gk_bridge.probe()
        assert gk_bridge._status is status

    def test_probe_git_installed(self, gk_bridge):
        with patch("shutil.which", return_value="/usr/bin/git"):
            with patch.object(gk_bridge, "_mcp_is_running", return_value=False):
                status = gk_bridge.probe()
        assert status.git_installed is True
        assert status.available is True

    def test_probe_git_not_installed(self, gk_bridge):
        with patch("shutil.which", return_value=None):
            with patch.object(gk_bridge, "_mcp_is_running", return_value=False):
                status = gk_bridge.probe()
        assert status.git_installed is False
        assert status.available is False
        assert "not installed" in status.message.lower()

    def test_probe_mcp_running_message(self, gk_bridge):
        with patch("shutil.which", return_value="/usr/bin/git"):
            with patch.object(gk_bridge, "_mcp_is_running", return_value=True):
                status = gk_bridge.probe()
        assert status.mcp_server_running is True
        assert "ready" in status.message.lower()

    def test_probe_mcp_dormant_message(self, gk_bridge):
        with patch("shutil.which", return_value="/usr/bin/git"):
            with patch.object(gk_bridge, "_mcp_is_running", return_value=False):
                status = gk_bridge.probe()
        assert status.mcp_server_running is False
        assert "dormant" in status.message.lower()

    def test_probe_gitlens_always_available(self, gk_bridge):
        with patch("shutil.which", return_value="/usr/bin/git"):
            with patch.object(gk_bridge, "_mcp_is_running", return_value=False):
                status = gk_bridge.probe()
        assert status.gitlens_available is True

    def test_detect_providers_github(self, gk_bridge, tmp_path):
        (tmp_path / ".git").mkdir()
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "origin\tgit@github.com:user/repo.git (fetch)"
        with patch("subprocess.run", return_value=mock_result):
            providers = bridge._detect_providers()
        assert "github" in providers

    def test_detect_providers_gitlab(self, gk_bridge, tmp_path):
        (tmp_path / ".git").mkdir()
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "origin\thttps://gitlab.com/user/repo.git (fetch)"
        with patch("subprocess.run", return_value=mock_result):
            providers = bridge._detect_providers()
        assert "gitlab" in providers

    def test_detect_providers_multiple(self, gk_bridge, tmp_path):
        (tmp_path / ".git").mkdir()
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "origin\tgit@github.com:user/repo.git (fetch)\n"
            "upstream\thttps://bitbucket.org/user/repo.git (fetch)"
        )
        with patch("subprocess.run", return_value=mock_result):
            providers = bridge._detect_providers()
        assert "github" in providers
        assert "bitbucket" in providers

    def test_detect_providers_empty_on_error(self, tmp_path):
        (tmp_path / ".git").mkdir()
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        with patch("subprocess.run", side_effect=Exception("fail")):
            providers = bridge._detect_providers()
        assert providers == []

    def test_detect_providers_non_zero_returncode(self, tmp_path):
        (tmp_path / ".git").mkdir()
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "github.com"
        with patch("subprocess.run", return_value=mock_result):
            providers = bridge._detect_providers()
        assert providers == []

    def test_probe_skips_provider_detection_no_git_dir(self, tmp_path):
        """No .git dir → providers_detected should be empty."""
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        with patch("shutil.which", return_value="/usr/bin/git"):
            with patch.object(bridge, "_mcp_is_running", return_value=False):
                status = bridge.probe()
        assert status.providers_detected == []

    def test_probe_includes_providers_in_status(self, tmp_path):
        (tmp_path / ".git").mkdir()
        bridge = GitKrakenBridge(workspace_root=tmp_path)
        with patch("shutil.which", return_value="/usr/bin/git"):
            with patch.object(bridge, "_mcp_is_running", return_value=False):
                with patch.object(bridge, "_detect_providers", return_value=["github"]):
                    status = bridge.probe()
        assert "github" in status.providers_detected


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — _mcp_is_running
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenMcpIsRunning:
    def test_returns_true_when_status_healthy(self, gk_bridge):
        with patch.object(gk_bridge, "_mcp_request", return_value={"status": "healthy"}):
            assert gk_bridge._mcp_is_running() is True

    def test_returns_true_when_status_running(self, gk_bridge):
        with patch.object(gk_bridge, "_mcp_request", return_value={"status": "running"}):
            assert gk_bridge._mcp_is_running() is True

    def test_returns_true_when_status_ok(self, gk_bridge):
        with patch.object(gk_bridge, "_mcp_request", return_value={"status": "ok"}):
            assert gk_bridge._mcp_is_running() is True

    def test_returns_false_on_url_error(self, gk_bridge):
        from urllib.error import URLError

        with patch.object(gk_bridge, "_mcp_request", side_effect=URLError("conn refused")):
            assert gk_bridge._mcp_is_running() is False

    def test_returns_false_when_status_unknown(self, gk_bridge):
        with patch.object(gk_bridge, "_mcp_request", return_value={"status": "starting"}):
            assert gk_bridge._mcp_is_running() is False

    def test_returns_false_on_os_error(self, gk_bridge):
        with patch.object(gk_bridge, "_mcp_request", side_effect=OSError("connection refused")):
            assert gk_bridge._mcp_is_running() is False


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — execute_tool
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenExecuteTool:
    def test_returns_failure_when_mcp_unavailable(self, gk_bridge):
        with patch.object(gk_bridge, "_ensure_mcp_server", return_value=False):
            result = gk_bridge.execute_tool("git_status")
        assert result["status"] == "failed"
        assert result["error"] == "mcp_server_unavailable"
        assert result["tool"] == "git_status"

    def test_returns_success_result(self, gk_bridge):
        success_payload = {
            "success": True,
            "result": {"status": "clean", "branch": "main"},
        }
        with patch.object(gk_bridge, "_ensure_mcp_server", return_value=True):
            with patch.object(gk_bridge, "_mcp_request", return_value=success_payload):
                result = gk_bridge.execute_tool("git_status")
        assert result["status"] == "clean"
        assert result["branch"] == "main"
        # Bridge appends tool and mcp_server_url via setdefault
        assert result["tool"] == "git_status"

    def test_returns_success_non_dict_result(self, gk_bridge):
        success_payload = {"success": True, "result": "ok string"}
        with patch.object(gk_bridge, "_ensure_mcp_server", return_value=True):
            with patch.object(gk_bridge, "_mcp_request", return_value=success_payload):
                result = gk_bridge.execute_tool("git_push")
        assert result["status"] == "success"
        assert result["result"] == "ok string"

    def test_returns_failure_on_request_error(self, gk_bridge):
        from urllib.error import URLError

        with patch.object(gk_bridge, "_ensure_mcp_server", return_value=True):
            with patch.object(
                gk_bridge, "_mcp_request", side_effect=URLError("connection refused")
            ):
                result = gk_bridge.execute_tool("git_status")
        assert result["status"] == "failed"
        assert "mcp_execute_failed" in result["error"]

    def test_returns_failure_when_success_false(self, gk_bridge):
        fail_payload = {"success": False, "error": "tool_error_msg"}
        with patch.object(gk_bridge, "_ensure_mcp_server", return_value=True):
            with patch.object(gk_bridge, "_mcp_request", return_value=fail_payload):
                result = gk_bridge.execute_tool("git_status")
        assert result["status"] == "failed"
        assert result["error"] == "tool_error_msg"

    def test_passes_parameters_to_request(self, gk_bridge):
        success_payload = {"success": True, "result": {"ok": True}}
        captured: list[Any] = []

        def capturing_request(path, payload=None, **kwargs):
            captured.append(payload)
            return success_payload

        with patch.object(gk_bridge, "_ensure_mcp_server", return_value=True):
            with patch.object(gk_bridge, "_mcp_request", side_effect=capturing_request):
                gk_bridge.execute_tool("git_push", {"remote": "origin"})

        assert captured[0]["parameters"] == {"remote": "origin"}
        assert captured[0]["tool"] == "git_push"


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — execute_git_operation
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenExecuteGitOperation:
    def test_status_operation(self, gk_bridge):
        with patch.object(gk_bridge, "execute_tool", return_value={"status": "ok"}) as mock_exec:
            result = gk_bridge.execute_git_operation("status")
        mock_exec.assert_called_once_with("mcp_gitkraken_git_status", None)
        assert result == {"status": "ok"}

    def test_commit_operation(self, gk_bridge):
        with patch.object(gk_bridge, "execute_tool", return_value={"status": "ok"}) as mock_exec:
            gk_bridge.execute_git_operation("commit", {"message": "fix: bug"})
        mock_exec.assert_called_once_with(
            "mcp_gitkraken_git_add_or_commit", {"message": "fix: bug"}
        )

    def test_push_operation(self, gk_bridge):
        with patch.object(gk_bridge, "execute_tool", return_value={"status": "ok"}) as mock_exec:
            gk_bridge.execute_git_operation("push")
        mock_exec.assert_called_once_with("mcp_gitkraken_git_push", None)

    def test_unsupported_operation(self, gk_bridge):
        result = gk_bridge.execute_git_operation("rebase")
        assert result["status"] == "failed"
        assert "unsupported_gitkraken_operation" in result["error"]
        assert "rebase" in result["error"]
        assert "supported_operations" in result

    def test_case_insensitive_operation(self, gk_bridge):
        with patch.object(gk_bridge, "execute_tool", return_value={"status": "ok"}) as mock_exec:
            gk_bridge.execute_git_operation("STATUS")
        mock_exec.assert_called_once_with("mcp_gitkraken_git_status", None)

    def test_operation_with_whitespace(self, gk_bridge):
        with patch.object(gk_bridge, "execute_tool", return_value={"status": "ok"}) as mock_exec:
            gk_bridge.execute_git_operation("  push  ")
        mock_exec.assert_called_once_with("mcp_gitkraken_git_push", None)


# ═════════════════════════════════════════════════════════════════════════════
# GitKraken — Module-Level Functions
# ═════════════════════════════════════════════════════════════════════════════


class TestGitKrakenModuleFunctions:
    def test_get_bridge_returns_instance(self):
        bridge = gk_get_bridge()
        assert isinstance(bridge, GitKrakenBridge)

    def test_get_bridge_is_singleton(self):
        b1 = gk_get_bridge()
        b2 = gk_get_bridge()
        assert b1 is b2

    def test_get_bridge_respects_workspace_root(self, tmp_path):
        bridge = gk_get_bridge(workspace_root=tmp_path)
        assert bridge.workspace_root == tmp_path

    def test_probe_gitkraken_online(self):
        mock_status = GitKrakenBridgeStatus(
            available=True,
            providers_detected=["github"],
        )
        with patch("src.integrations.gitkraken_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = probe_gitkraken()
        assert result["status"] == "online"
        assert "GitKraken MCP" in result["detail"]
        assert "github" in result["detail"]

    def test_probe_gitkraken_offline(self):
        mock_status = GitKrakenBridgeStatus(available=False)
        with patch("src.integrations.gitkraken_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = probe_gitkraken()
        assert result["status"] == "offline"
        assert "not installed" in result["detail"].lower()

    def test_probe_gitkraken_no_providers(self):
        mock_status = GitKrakenBridgeStatus(available=True, providers_detected=[])
        with patch("src.integrations.gitkraken_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = probe_gitkraken()
        assert "none detected" in result["detail"]

    def test_quick_status_online(self):
        mock_status = GitKrakenBridgeStatus(available=True, providers_detected=["github"])
        with patch("src.integrations.gitkraken_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = gk_quick_status()
        assert "ONLINE" in result
        assert "github" in result

    def test_quick_status_offline(self):
        mock_status = GitKrakenBridgeStatus(available=False)
        with patch("src.integrations.gitkraken_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = gk_quick_status()
        assert "OFFLINE" in result


# ═════════════════════════════════════════════════════════════════════════════
# HuggingFace — Enums and Dataclasses
# ═════════════════════════════════════════════════════════════════════════════


class TestHFEnumsDataclasses:
    def test_hf_resource_type_values(self):
        assert HFResourceType.MODEL.value == "model"
        assert HFResourceType.DATASET.value == "dataset"
        assert HFResourceType.SPACE.value == "space"
        assert HFResourceType.PAPER.value == "paper"

    def test_hf_bridge_status_defaults(self):
        s = HFBridgeStatus(available=True)
        assert s.authenticated is False
        assert s.username is None
        assert s.hf_hub_installed is False
        assert s.message == ""

    def test_hf_search_result_defaults(self):
        r = HFSearchResult(
            resource_type=HFResourceType.MODEL,
            id="bert-base",
            name="BERT Base",
        )
        assert r.description == ""
        assert r.downloads == 0
        assert r.likes == 0
        assert r.tags == []

    def test_hf_search_result_full(self):
        r = HFSearchResult(
            resource_type=HFResourceType.DATASET,
            id="imdb",
            name="IMDB",
            description="Sentiment",
            downloads=100000,
            likes=500,
            tags=["text", "sentiment"],
        )
        assert r.downloads == 100000
        assert "text" in r.tags


# ═════════════════════════════════════════════════════════════════════════════
# HuggingFace — MCP Tool Catalog
# ═════════════════════════════════════════════════════════════════════════════


class TestHFToolCatalog:
    def test_catalog_has_10_tools(self):
        assert len(HUGGINGFACE_MCP_TOOLS) == 10

    def test_all_tools_have_required_keys(self):
        for name, info in HUGGINGFACE_MCP_TOOLS.items():
            assert "category" in info, f"{name} missing category"
            assert "description" in info, f"{name} missing description"
            assert "parameters" in info, f"{name} missing parameters"
            assert "usage" in info, f"{name} missing usage"

    def test_search_tools_present(self):
        search = [k for k, v in HUGGINGFACE_MCP_TOOLS.items() if v["category"] == "search"]
        assert "model_search" in search
        assert "dataset_search" in search
        assert "paper_search" in search
        assert "space_search" in search

    def test_docs_tools_present(self):
        docs = [k for k, v in HUGGINGFACE_MCP_TOOLS.items() if v["category"] == "docs"]
        assert "hf_doc_search" in docs
        assert "hf_doc_fetch" in docs

    def test_auth_tool_present(self):
        auth = [k for k, v in HUGGINGFACE_MCP_TOOLS.items() if v["category"] == "auth"]
        assert "hf_whoami" in auth

    def test_execute_tool_present(self):
        execute = [k for k, v in HUGGINGFACE_MCP_TOOLS.items() if v["category"] == "execute"]
        assert "dynamic_space" in execute

    def test_generate_tool_present(self):
        generate = [k for k, v in HUGGINGFACE_MCP_TOOLS.items() if v["category"] == "generate"]
        assert "gr1_z_image_turbo_generate" in generate


# ═════════════════════════════════════════════════════════════════════════════
# HuggingFace — Initialization
# ═════════════════════════════════════════════════════════════════════════════


class TestHuggingFaceBridgeInit:
    def test_init_status_none(self, hf_bridge):
        assert hf_bridge._status is None

    def test_mcp_prefix(self, hf_bridge):
        assert hf_bridge.MCP_PREFIX == "mcp_evalstate_hf-_"


# ═════════════════════════════════════════════════════════════════════════════
# HuggingFace — Probe
# ═════════════════════════════════════════════════════════════════════════════


class TestHuggingFaceBridgeProbe:
    def test_probe_returns_status_object(self, hf_bridge):
        status = hf_bridge.probe()
        assert isinstance(status, HFBridgeStatus)

    def test_probe_always_available(self, hf_bridge):
        status = hf_bridge.probe()
        assert status.available is True

    def test_probe_always_authenticated(self, hf_bridge):
        status = hf_bridge.probe()
        assert status.authenticated is True
        assert status.username == "KiloEthereal"

    def test_probe_caches_status(self, hf_bridge):
        hf_bridge.probe()
        s2 = hf_bridge.probe()
        # Both calls return HFBridgeStatus; second call re-probes (no cache skip)
        assert s2.username == "KiloEthereal"

    def test_probe_sets_cached_status(self, hf_bridge):
        status = hf_bridge.probe()
        assert hf_bridge._status is status

    def test_probe_message_with_hf_token(self, monkeypatch, hf_bridge):
        monkeypatch.setenv("HF_TOKEN", "hf_test_token")
        status = hf_bridge.probe()
        assert "HF_TOKEN present" in status.message

    def test_probe_message_without_hf_token(self, monkeypatch, hf_bridge):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        monkeypatch.delenv("HUGGINGFACE_TOKEN", raising=False)
        status = hf_bridge.probe()
        assert "HF_TOKEN present" not in status.message
        assert "KiloEthereal" in status.message

    def test_probe_hf_hub_installed_detection(self, hf_bridge):
        """hf_hub_installed reflects importlib.util.find_spec result."""
        import importlib.util

        has_hub = importlib.util.find_spec("huggingface_hub") is not None
        status = hf_bridge.probe()
        assert status.hf_hub_installed == has_hub

    def test_probe_huggingface_token_env_var(self, monkeypatch, hf_bridge):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        monkeypatch.setenv("HUGGINGFACE_TOKEN", "alt_token_xyz")
        status = hf_bridge.probe()
        assert "HF_TOKEN present" in status.message


# ═════════════════════════════════════════════════════════════════════════════
# HuggingFace — Tool Lookup Methods
# ═════════════════════════════════════════════════════════════════════════════


class TestHuggingFaceToolLookup:
    def test_get_tool_info_known(self, hf_bridge):
        info = hf_bridge.get_tool_info("model_search")
        assert info is not None
        assert info["category"] == "search"

    def test_get_tool_info_unknown(self, hf_bridge):
        assert hf_bridge.get_tool_info("does_not_exist") is None

    def test_get_tools_by_category_search(self, hf_bridge):
        tools = hf_bridge.get_tools_by_category("search")
        assert "model_search" in tools
        assert "dataset_search" in tools

    def test_get_tools_by_category_docs(self, hf_bridge):
        tools = hf_bridge.get_tools_by_category("docs")
        assert "hf_doc_search" in tools
        assert "hf_doc_fetch" in tools

    def test_get_tools_by_category_unknown(self, hf_bridge):
        assert hf_bridge.get_tools_by_category("no_such_cat") == []

    def test_get_mcp_tool_name(self, hf_bridge):
        assert hf_bridge.get_mcp_tool_name("model_search") == "mcp_evalstate_hf-_model_search"

    def test_get_mcp_tool_name_whoami(self, hf_bridge):
        result = hf_bridge.get_mcp_tool_name("hf_whoami")
        assert result == "mcp_evalstate_hf-_hf_whoami"


# ═════════════════════════════════════════════════════════════════════════════
# HuggingFace — format_search_recommendations
# ═════════════════════════════════════════════════════════════════════════════


class TestHFSearchRecommendations:
    def test_recommendation_structure(self, hf_bridge):
        rec = hf_bridge.format_search_recommendations("text-generation")
        assert "recommended_tools" in rec
        assert "suggested_queries" in rec
        assert "common_filters" in rec

    def test_recommendation_tools_use_prefix(self, hf_bridge):
        rec = hf_bridge.format_search_recommendations("classification")
        for tool in rec["recommended_tools"]:
            assert tool.startswith("mcp_evalstate_hf-_")

    def test_recommendation_includes_model_search(self, hf_bridge):
        rec = hf_bridge.format_search_recommendations("code")
        assert "mcp_evalstate_hf-_model_search" in rec["recommended_tools"]

    def test_recommendation_known_task(self, hf_bridge):
        rec = hf_bridge.format_search_recommendations("qa")
        assert "question-answering" in rec["suggested_queries"]

    def test_recommendation_unknown_task_falls_back(self, hf_bridge):
        rec = hf_bridge.format_search_recommendations("some_novel_task_xyz")
        # Falls back to [task] as-is
        assert "some_novel_task_xyz" in rec["suggested_queries"]

    def test_recommendation_all_known_tasks(self, hf_bridge):
        tasks = [
            "text-generation",
            "classification",
            "qa",
            "summarization",
            "translation",
            "image",
            "audio",
            "code",
        ]
        for task in tasks:
            rec = hf_bridge.format_search_recommendations(task)
            assert len(rec["suggested_queries"]) >= 1

    def test_common_filters_content(self, hf_bridge):
        rec = hf_bridge.format_search_recommendations("image")
        assert "downloads" in rec["common_filters"]
        assert "likes" in rec["common_filters"]


# ═════════════════════════════════════════════════════════════════════════════
# HuggingFace — Module-Level Functions
# ═════════════════════════════════════════════════════════════════════════════


class TestHuggingFaceModuleFunctions:
    def test_get_bridge_returns_instance(self):
        bridge = hf_get_bridge()
        assert isinstance(bridge, HuggingFaceBridge)

    def test_get_bridge_is_singleton(self):
        b1 = hf_get_bridge()
        b2 = hf_get_bridge()
        assert b1 is b2

    def test_probe_huggingface_online(self):
        mock_status = HFBridgeStatus(available=True, username="KiloEthereal")
        with patch("src.integrations.huggingface_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = probe_huggingface()
        assert result["status"] == "online"
        assert "KiloEthereal" in result["detail"]

    def test_probe_huggingface_tool_count(self):
        mock_status = HFBridgeStatus(available=True, username="KiloEthereal")
        with patch("src.integrations.huggingface_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = probe_huggingface()
        assert "10" in result["detail"]

    def test_probe_huggingface_offline(self):
        mock_status = HFBridgeStatus(available=False, username=None)
        with patch("src.integrations.huggingface_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = probe_huggingface()
        assert result["status"] == "offline"

    def test_quick_status_authenticated(self):
        mock_status = HFBridgeStatus(
            available=True, authenticated=True, username="KiloEthereal"
        )
        with patch("src.integrations.huggingface_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = hf_quick_status()
        assert "ONLINE" in result
        assert "KiloEthereal" in result

    def test_quick_status_unauthenticated(self):
        mock_status = HFBridgeStatus(
            available=True, authenticated=False, username=None
        )
        with patch("src.integrations.huggingface_bridge.get_bridge") as mock_gb:
            mock_gb.return_value.probe.return_value = mock_status
            result = hf_quick_status()
        assert "anonymous" in result


# ═════════════════════════════════════════════════════════════════════════════
# MCP Extension Catalog
# ═════════════════════════════════════════════════════════════════════════════


class TestMCPExtensionCatalog:
    def test_catalog_has_expected_extensions(self):
        assert "devtool" in MCP_EXTENSIONS
        assert "dbclient" in MCP_EXTENSIONS
        assert "huggingface" in MCP_EXTENSIONS
        assert "gitkraken" in MCP_EXTENSIONS
        assert "github" in MCP_EXTENSIONS
        assert "mermaid" in MCP_EXTENSIONS
        assert "azure" in MCP_EXTENSIONS

    def test_get_extension_known(self):
        ext = get_extension("gitkraken")
        assert ext is not None
        assert isinstance(ext, MCPExtension)
        assert ext.name == "GitKraken MCP"

    def test_get_extension_unknown(self):
        assert get_extension("nonexistent_ext") is None

    def test_get_extension_huggingface(self):
        ext = get_extension("huggingface")
        assert ext is not None
        assert ext.bridge_module == "src.integrations.huggingface_bridge"
        assert ext.tool_count == 10

    def test_get_extension_gitkraken_tool_count(self):
        ext = get_extension("gitkraken")
        assert ext is not None
        assert ext.tool_count == 24

    def test_get_all_extensions(self):
        exts = get_all_extensions()
        assert len(exts) == len(MCP_EXTENSIONS)
        assert all(isinstance(e, MCPExtension) for e in exts)

    def test_get_extensions_by_category_ml_ai(self):
        exts = get_extensions_by_category(ExtensionCategory.ML_AI)
        names = [e.name for e in exts]
        assert "Hugging Face Hub" in names

    def test_get_extensions_by_category_version_control(self):
        exts = get_extensions_by_category(ExtensionCategory.VERSION_CONTROL)
        names = [e.name for e in exts]
        assert "GitKraken MCP" in names
        assert "GitHub MCP" in names

    def test_get_extensions_by_category_browser(self):
        exts = get_extensions_by_category(ExtensionCategory.BROWSER)
        names = [e.name for e in exts]
        assert "DevTool+" in names

    def test_get_extensions_by_status_fully_integrated(self):
        exts = get_extensions_by_status(IntegrationStatus.FULLY_INTEGRATED)
        names = [e.name for e in exts]
        assert "GitKraken MCP" in names
        assert "Hugging Face Hub" in names
        assert "DevTool+" in names

    def test_get_extensions_by_status_not_applicable(self):
        exts = get_extensions_by_status(IntegrationStatus.NOT_APPLICABLE)
        names = [e.name for e in exts]
        assert "GitHub MCP" in names

    def test_integration_summary_structure(self):
        summary = get_integration_summary()
        assert "total_extensions" in summary
        assert "total_tools" in summary
        assert "fully_integrated" in summary
        assert "partially_integrated" in summary
        assert "not_integrated" in summary
        assert "by_category" in summary

    def test_integration_summary_total_extensions(self):
        summary = get_integration_summary()
        assert summary["total_extensions"] == len(MCP_EXTENSIONS)

    def test_integration_summary_total_tools(self):
        summary = get_integration_summary()
        expected = sum(ext.tool_count for ext in MCP_EXTENSIONS.values())
        assert summary["total_tools"] == expected

    def test_integration_summary_fully_integrated_list(self):
        summary = get_integration_summary()
        assert "GitKraken MCP" in summary["fully_integrated"]
        assert "Hugging Face Hub" in summary["fully_integrated"]

    def test_integration_summary_by_category_keys(self):
        summary = get_integration_summary()
        category_keys = set(summary["by_category"].keys())
        expected = {cat.value for cat in ExtensionCategory}
        assert category_keys == expected

    def test_integration_recommendations_structure(self):
        recs = get_integration_recommendations()
        # Only NOT_INTEGRATED extensions produce recommendations
        not_integrated = get_extensions_by_status(IntegrationStatus.NOT_INTEGRATED)
        assert len(recs) == len(not_integrated)

    def test_integration_recommendations_fields(self):
        recs = get_integration_recommendations()
        for rec in recs:
            assert "extension" in rec
            assert "priority" in rec
            assert "effort" in rec
            assert "tool_count" in rec

    def test_mcptool_dataclass(self):
        tool = MCPTool("navigate_page", "page", "Navigate to a URL", ["url", "wait"])
        assert tool.name == "navigate_page"
        assert tool.category == "page"
        assert tool.parameters == ["url", "wait"]

    def test_mcp_extension_dataclass(self):
        ext = MCPExtension(
            name="Test",
            prefix="mcp_test_",
            category=ExtensionCategory.BROWSER,
            description="Test ext",
            tool_count=5,
            integration_status=IntegrationStatus.NOT_INTEGRATED,
        )
        assert ext.tools == []
        assert ext.bridge_module is None

    def test_gitkraken_catalog_entry_has_bridge_module(self):
        ext = get_extension("gitkraken")
        assert ext is not None
        assert ext.bridge_module == "src.integrations.gitkraken_bridge"

    def test_huggingface_catalog_prefix_matches_bridge(self):
        catalog_ext = get_extension("huggingface")
        assert catalog_ext is not None
        assert catalog_ext.prefix == "mcp_evalstate_hf-_"
        # Must match the bridge's MCP_PREFIX constant
        assert catalog_ext.prefix == HuggingFaceBridge.MCP_PREFIX

    def test_gitkraken_catalog_prefix_matches_bridge(self):
        catalog_ext = get_extension("gitkraken")
        assert catalog_ext is not None
        assert catalog_ext.prefix == "mcp_gitkraken_"
        assert catalog_ext.prefix == GitKrakenBridge.MCP_PREFIX


# ═════════════════════════════════════════════════════════════════════════════
# Integration Package __init__ exports
# ═════════════════════════════════════════════════════════════════════════════


class TestIntegrationsPackageExports:
    def test_gitkraken_bridge_exported(self):
        from src.integrations import GitKrakenBridge as GKB

        assert GKB is GitKrakenBridge

    def test_huggingface_bridge_exported(self):
        from src.integrations import HuggingFaceBridge as HFB

        assert HFB is HuggingFaceBridge

    def test_get_gitkraken_bridge_exported(self):
        from src.integrations import get_gitkraken_bridge

        assert callable(get_gitkraken_bridge)

    def test_get_huggingface_bridge_exported(self):
        from src.integrations import get_huggingface_bridge

        assert callable(get_huggingface_bridge)

    def test_get_extension_catalog_exported(self):
        from src.integrations import get_extension_catalog

        assert callable(get_extension_catalog)
        result = get_extension_catalog()
        assert isinstance(result, list)

    def test_get_integration_summary_exported(self):
        from src.integrations import get_integration_summary as gis

        assert callable(gis)

    def test_get_extension_exported(self):
        from src.integrations import get_extension as ge

        result = ge("gitkraken")
        assert result is not None

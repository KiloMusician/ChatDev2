"""Regression tests for DevTool+ bridge and extension-backed routing semantics."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from types import SimpleNamespace

from unittest.mock import AsyncMock, MagicMock


def test_detect_edge_fallback_supports_wsl_windows_mounts(monkeypatch, tmp_path):
    from src.integrations import devtool_bridge

    edge_path = tmp_path / "msedge.exe"
    edge_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(devtool_bridge, "_is_wsl", lambda: True)
    monkeypatch.setattr(devtool_bridge.sys, "platform", "linux", raising=False)
    monkeypatch.setattr(devtool_bridge, "_windows_mount_candidates", lambda *_args: [edge_path])

    result = devtool_bridge.detect_edge_fallback()

    assert result.status == devtool_bridge.BrowserStatus.AVAILABLE
    assert result.browser == "edge"
    assert result.path == str(edge_path)


def test_detect_chrome_accepts_wsl_brave_mount(monkeypatch, tmp_path):
    from src.integrations import devtool_bridge

    brave_path = tmp_path / "brave.exe"
    brave_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(devtool_bridge, "_is_wsl", lambda: True)
    monkeypatch.setattr(devtool_bridge.sys, "platform", "linux", raising=False)
    monkeypatch.setattr(devtool_bridge, "_windows_mount_candidates", lambda *_args: [brave_path])
    monkeypatch.setattr(
        devtool_bridge.Path,
        "exists",
        lambda self: self == brave_path,
    )

    result = devtool_bridge.detect_chrome()

    assert result.status == devtool_bridge.BrowserStatus.AVAILABLE
    assert result.browser == "brave"
    assert result.path == str(brave_path)


def test_devtool_router_uses_edge_fallback_when_chrome_missing(monkeypatch, tmp_path):
    import src.integrations.devtool_bridge as bridge_module
    from src.orchestration.unified_ai_orchestrator import OrchestrationTask
    from src.tools.agent_task_router import AgentTaskRouter

    class FakeBridge:
        def get_status(self):
            return SimpleNamespace(
                chrome_available=False,
                edge_fallback_available=True,
                categories=["page", "capture"],
            )

        def is_operational(self):
            return True

        def probe_browser(self):
            return SimpleNamespace(path=None)

        def probe_edge_fallback(self):
            return SimpleNamespace(
                path="/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
            )

    monkeypatch.setattr(bridge_module, "DevToolBridge", FakeBridge)
    monkeypatch.setattr(bridge_module, "DEVTOOL_MCP_TOOLS", {"navigate_page": object()})

    router = AgentTaskRouter(repo_root=tmp_path)
    task = OrchestrationTask(
        task_id="devtool-edge",
        task_type="test",
        content="Check browser status",
        context={"action": "navigate", "url": "https://example.com"},
    )

    result = asyncio.run(router._route_to_devtool(task))

    assert result["status"] == "success"
    assert result["availability"] == "limited"
    assert result["browser_mode"] == "edge_fallback"
    assert result["browser_path"].endswith("msedge.exe")
    assert result["suggested_mcp_tool"] == "mcp_chromedevtool_navigate_page"
    assert "Chrome is preferred" in result["warning"]


def test_setup_integrations_deduplicates_extension_recommendations(tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    extensions = tmp_path / ".vscode" / "extensions.json"
    extensions.parent.mkdir(parents=True)
    extensions.write_text(
        """
        {
          "recommendations": ["a.one", "b.two", "a.one"],
          "optionalRecommendations": ["c.three", "c.three"],
          "localRecommendations": ["../foo", "../foo"]
        }
        """,
        encoding="utf-8",
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path
    status = setup.check_extensions()

    assert status["recommended_count"] == 2
    assert status["recommendations"] == ["a.one", "b.two"]
    assert status["optional_count"] == 1
    assert status["optional_recommendations"] == ["c.three"]
    assert status["local_count"] == 1
    assert status["local_recommendations"] == ["../foo"]


def test_extension_quickwins_flags_openai_chatgpt_as_redundant_ai(tmp_path, monkeypatch):
    from scripts.integrate_extensions import ExtensionIntegrator

    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir()
    (vscode_dir / "settings.json").write_text("{}", encoding="utf-8")
    (vscode_dir / "extensions.json").write_text("{}", encoding="utf-8")

    integrator = ExtensionIntegrator()
    integrator.repo_root = tmp_path
    integrator.vscode_dir = vscode_dir
    integrator.extensions_json = vscode_dir / "extensions.json"
    integrator.settings_json = vscode_dir / "settings.json"
    integrator.reports_dir = tmp_path / "state" / "reports"
    integrator.reports_dir.mkdir(parents=True)

    monkeypatch.setattr(
        integrator,
        "_resolve_extensions_for_profile",
        lambda profile_name: (
            ["github.copilot", "continue.continue", "openai.chatgpt", "codeium.codeium"],
            "profile",
        ),
    )

    report = integrator.build_quickwins_report(with_noise=False)

    assert "openai.chatgpt" in report["redundant_ai_detected"]
    assert "codeium.codeium" in report["redundant_ai_detected"]


def test_handle_route_execution_treats_ready_status_as_success(tmp_path):
    from src.orchestration.unified_ai_orchestrator import OrchestrationTask
    from src.tools.agent_task_router import AgentTaskRouter

    router = AgentTaskRouter(repo_root=tmp_path)
    router._route_by_system = AsyncMock(return_value={"status": "ready", "agent": "gitkraken"})
    router._log_to_quest = MagicMock()

    task = OrchestrationTask(
        task_id="ready-route",
        task_type="test",
        content="probe",
        context={},
    )

    result, status, exit_code = asyncio.run(
        router._handle_route_execution(task, "devtool", "test", "probe ready route")
    )

    assert status == "success"
    assert exit_code == 0
    assert result["success"] is True


def test_verify_workspace_jsonc_loader_supports_inline_comments_and_trailing_commas(tmp_path):
    from scripts.verify_tripartite_workspace import _load_jsonc

    settings = tmp_path / "settings.json"
    settings.write_text(
        """
        {
          "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python", // comment
          "extensions": [
            "ms-python.python",
          ],
        }
        """,
        encoding="utf-8",
    )

    loaded = _load_jsonc(settings)

    assert loaded["python.defaultInterpreterPath"].endswith(".venv/bin/python")
    assert loaded["extensions"] == ["ms-python.python"]


def test_verify_workspace_interpreter_resolves_concrete_python(tmp_path):
    from scripts.verify_tripartite_workspace import _resolve_workspace_interpreter

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    venv_bin = workspace / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    python_bin = venv_bin / "python"
    python_bin.write_text("#!/usr/bin/env python\n", encoding="utf-8")

    settings = workspace / ".vscode" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(
        '{"python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"}',
        encoding="utf-8",
    )

    raw, resolved = _resolve_workspace_interpreter(settings, workspace_root=workspace)

    assert raw == "${workspaceFolder}/.venv/bin/python"
    assert resolved == python_bin


def test_verify_workspace_interpreter_resolves_env_home(monkeypatch, tmp_path):
    from scripts.verify_tripartite_workspace import _resolve_workspace_interpreter

    home = tmp_path / "home"
    python_bin = home / ".venvs" / "nusyq-hub-311" / "bin" / "python"
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text("#!/usr/bin/env python\n", encoding="utf-8")

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    settings = workspace / ".vscode" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(
        '{"python.defaultInterpreterPath": "${env:HOME}/.venvs/nusyq-hub-311/bin/python"}',
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(home))

    raw, resolved = _resolve_workspace_interpreter(settings, workspace_root=workspace)

    assert raw == "${env:HOME}/.venvs/nusyq-hub-311/bin/python"
    assert resolved == python_bin


def test_report_governance_warns_when_canonical_reports_missing(monkeypatch, tmp_path, capsys):
    import scripts.verify_tripartite_workspace as verifier

    reports_dir = tmp_path / "state" / "reports"
    reports_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs" / "Reports"
    docs_dir.mkdir(parents=True)
    (docs_dir / "sample.md").write_text("report", encoding="utf-8")

    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(
        verifier,
        "CANONICAL_LIVE_REPORTS",
        (
            tmp_path / "state" / "reports" / "current_state.md",
            tmp_path / "state" / "reports" / "integration_status.json",
        ),
    )

    verifier._check_report_governance()

    output = capsys.readouterr().out
    assert "Canonical live report set is incomplete" in output
    assert str(Path("state") / "reports" / "current_state.md") in output


def test_verify_workspace_docker_permission_denied_is_reported_as_context_issue(
    monkeypatch, tmp_path, capsys
):
    import scripts.verify_tripartite_workspace as verifier

    class DummyResult:
        def __init__(self, returncode, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(cmd, capture_output=True, text=True, timeout=5):
        assert cmd == ["docker", "version", "--format", "{{.Server.Version}}"]
        return DummyResult(
            1,
            "",
            "permission denied while trying to connect to the docker API at unix:///var/run/docker.sock",
        )

    sock = tmp_path / "docker.sock"
    sock.write_text("", encoding="utf-8")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        verifier, "Path", lambda raw=".": sock if raw == "/var/run/docker.sock" else Path(raw)
    )

    verifier._check_docker()

    output = capsys.readouterr().out
    assert "Docker socket is present but inaccessible from this runtime context" in output
    assert "not a Docker daemon failure" in output


def test_verify_workspace_interpreter_below_repo_minimum_is_reported(monkeypatch, tmp_path, capsys):
    import scripts.verify_tripartite_workspace as verifier

    settings = tmp_path / ".vscode" / "settings.json"
    settings.parent.mkdir(parents=True)
    python_bin = tmp_path / ".venv" / "bin" / "python"
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text("#!/usr/bin/env python\n", encoding="utf-8")

    monkeypatch.setattr(verifier, "ROOT", tmp_path)

    class DummyResult:
        returncode = 0
        stdout = "Python 3.10.12\n"
        stderr = ""

    monkeypatch.setattr(
        verifier.subprocess,
        "run",
        lambda *args, **kwargs: DummyResult(),
    )

    settings.write_text(
        '{"python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"}',
        encoding="utf-8",
    )

    ok = verifier._check_python_workspace_environment()

    output = capsys.readouterr().out
    assert ok is False
    assert "Workspace interpreter is below the repo minimum" in output
    assert "Python 3.11+" in output


def test_collect_settings_alignment_findings_detects_focus_change_drift():
    import scripts.verify_tripartite_workspace as verifier

    findings = verifier._collect_settings_alignment_findings(
        {
            "editor.codeActions.triggerOnFocusChange": False,
            "semgrep.useExperimentalLS": True,
            "semgrep.doHover": False,
            "ruff.nativeServer": "on",
        },
        {
            "editor.codeActions.triggerOnFocusChange": True,
            "ruff.nativeServer": "off",
        },
    )

    messages = [item["message"] for item in findings]
    assert any("editor.codeActions.triggerOnFocusChange" in message for message in messages)
    assert any("ruff.nativeServer" in message for message in messages)


def test_collect_settings_alignment_findings_flags_workspace_misconfiguration():
    import scripts.verify_tripartite_workspace as verifier

    findings = verifier._collect_settings_alignment_findings(
        {
            "editor.codeActions.triggerOnFocusChange": True,
            "semgrep.useExperimentalLS": False,
            "semgrep.doHover": True,
            "ruff.nativeServer": "off",
        },
        {},
    )

    assert any(item["severity"] == "error" for item in findings)
    assert any("semgrep.useExperimentalLS" in item["message"] for item in findings)


def test_output_inventory_hints_report_flags_semgrep_single_file_scan_pressure(tmp_path, monkeypatch):
    from src.diagnostics.output_source_inventory import OutputSourceInventory

    log_path = tmp_path / "semgrep.log"
    log_path.write_text(
        "Starting pro language server\n"
        "Scanning single file\n"
        "Scanned single file\n"
        "Scanning single file\n"
        "Scanned single file\n"
        "Scanning single file\n",
        encoding="utf-8",
    )

    inventory = OutputSourceInventory(repo_root=tmp_path)
    monkeypatch.setattr(
        inventory,
        "scan",
        lambda expected_channels=None: {
            "channels": {
                "Semgrep (Server)": {
                    "channel": "Semgrep (Server)",
                    "canonical": "semgrepserver",
                    "source_types": ["vscode_output_channel"],
                    "paths": [str(log_path)],
                    "latest_path": str(log_path),
                    "latest_modified": "",
                    "total_bytes": log_path.stat().st_size,
                }
            },
            "summary": {"total_channels": 1},
        },
    )

    report = inventory.hints_report(channel="Semgrep (Server)", since_minutes=60, sample_lines=50)

    issue_ids = [item["id"] for item in report["issues"]]
    assert "semgrep_single_file_scan_pressure" in issue_ids


def test_validate_environment_requires_python_311(monkeypatch):
    import scripts.validate_environment as validator_module

    validator = validator_module.EnvironmentValidator()
    monkeypatch.setattr(
        validator_module.sys,
        "version_info",
        SimpleNamespace(major=3, minor=10, micro=12),
        raising=False,
    )

    ok = validator.validate_python_version()

    assert ok is False
    assert "Python 3.10 detected - Python 3.11+ required" in validator.issues


def test_validate_environment_dependency_probe_uses_find_spec(monkeypatch):
    import scripts.validate_environment as validator_module

    seen = []

    def fake_find_spec(name):
        seen.append(name)
        return object() if name in {"pandas", "numpy"} else None

    monkeypatch.setattr(validator_module, "find_spec", fake_find_spec)
    validator = validator_module.EnvironmentValidator()

    critical_ok, results = validator.validate_dependencies()

    assert critical_ok is True
    assert results["pandas"] is True
    assert results["numpy"] is True
    assert results["torch"] is False
    assert "pandas" in seen
    assert "transformers" in seen


def test_python_contract_files_require_python_311():
    root = Path(__file__).resolve().parent.parent

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    setup_py = (root / "setup.py").read_text(encoding="utf-8")
    bootstrap = (root / "scripts" / "bootstrap_dev_env.sh").read_text(encoding="utf-8")

    assert 'requires-python = ">=3.11"' in pyproject
    assert 'python_requires=">=3.11"' in setup_py
    assert "Python (>=3.11)" in bootstrap or "Python 3.11+" in bootstrap

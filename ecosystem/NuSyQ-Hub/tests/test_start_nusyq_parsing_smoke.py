import json
import os
import sys
import types
from pathlib import Path

import scripts.integration_health_check as integration_health_check
import scripts.start_nusyq as start_nusyq


def test_unknown_action_fast_fail(monkeypatch, tmp_path):
    # Avoid spine initialization side effects
    monkeypatch.setattr(start_nusyq, "initialize_spine", None)
    monkeypatch.setattr(start_nusyq, "export_spine_health", None)

    monkeypatch.setenv("NUSYQ_FAST_TEST_MODE", "1")
    # Point cwd to tmp to avoid touching real repo; main uses __file__ for hub_default
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTHONWARNINGS", "ignore")

    monkeypatch.setattr(sys, "argv", ["start_nusyq.py", "unknown_action"])
    rc = start_nusyq.main()
    assert rc == 1


def test_list_background_tasks_json_routed_to_handler(monkeypatch, tmp_path):
    monkeypatch.setattr(start_nusyq, "initialize_spine", None)
    monkeypatch.setattr(start_nusyq, "export_spine_health", None)
    monkeypatch.chdir(tmp_path)

    captured: dict[str, object] = {}

    def fake_handler(args, json_mode=False):
        captured["args"] = list(args)
        captured["json_mode"] = json_mode
        return 0

    monkeypatch.setattr(start_nusyq, "handle_list_background_tasks", fake_handler)
    monkeypatch.setattr(
        sys, "argv", ["start_nusyq.py", "list_background_tasks", "--limit=1", "--json"]
    )

    rc = start_nusyq.main()
    assert rc == 0
    assert captured["args"] == ["--limit=1"]
    assert captured["json_mode"] is True


def test_review_requires_path(monkeypatch, tmp_path):
    monkeypatch.setattr(start_nusyq, "initialize_spine", None)
    monkeypatch.setattr(start_nusyq, "export_spine_health", None)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["start_nusyq.py", "review"])
    rc = start_nusyq.main()
    assert rc == 1


def test_count_lint_errors_prefers_ground_truth(tmp_path):
    diagnostics_dir = tmp_path / "docs" / "Reports" / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    report_path = diagnostics_dir / "unified_error_report_latest.json"
    report_path.write_text(
        (
            "{"
            '"ground_truth":{"errors":0,"warnings":0,"infos":0,"total":0},'
            '"by_severity":{"errors":99}'
            "}"
        ),
        encoding="utf-8",
    )

    count = start_nusyq._count_lint_errors(tmp_path)
    assert count == 0


def test_infer_job_status_from_checkpoint_generated_at(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text(
        '{"status":"ok","generated_at":"2026-02-20T15:10:10+00:00"}', encoding="utf-8"
    )
    job = {
        "started_at": "2026-02-20T15:10:09+00:00",
        "metadata": {"checkpoint_file": str(checkpoint_path)},
    }
    inferred = start_nusyq._infer_job_status_from_checkpoint(job)
    assert inferred == ("completed", 0)


def test_probe_working_tree_dirty_fast_path(monkeypatch, tmp_path):
    def fake_run(cmd, cwd=None, timeout_s=0):
        if cmd == start_nusyq.FAST_DIRTY_DIFF_CMD:
            return 1, "", ""
        if cmd == start_nusyq.FAST_DIRTY_CACHED_CMD:
            return 0, "", ""
        return 0, "", ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    state, error = start_nusyq._probe_working_tree_dirty(tmp_path)
    assert state == "DIRTY"
    assert error is None


def test_probe_working_tree_dirty_fallback_status(monkeypatch, tmp_path):
    diff_cmd = tuple(start_nusyq.FAST_DIRTY_DIFF_CMD)
    cached_cmd = tuple(start_nusyq.FAST_DIRTY_CACHED_CMD)
    status_cmd = tuple(start_nusyq.FAST_STATUS_CMD)

    def fake_run(cmd, cwd=None, timeout_s=0):
        if cmd in {diff_cmd, cached_cmd}:
            return 1, "", "TimeoutExpired"
        if cmd == status_cmd:
            return 0, "M scripts/start_nusyq.py\n", ""
        return 0, "", ""

    def fake_run_normalized(cmd, cwd=None, timeout_s=0):
        return fake_run(tuple(cmd) if isinstance(cmd, list) else cmd, cwd=cwd, timeout_s=timeout_s)

    monkeypatch.setattr(start_nusyq, "run", fake_run_normalized)
    state, error = start_nusyq._probe_working_tree_dirty(tmp_path)
    assert state == "DIRTY"
    assert error is None


def test_openclaw_status_reports_degraded_when_disabled(tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "secrets.json").write_text(
        json.dumps(
            {
                "openclaw": {
                    "enabled": False,
                    "gateway_url": "ws://127.0.0.1:18789",
                    "api_url": "http://127.0.0.1:18790",
                    "channels": {"slack": {"enabled": False, "bot_token": "", "app_token": ""}},
                }
            }
        ),
        encoding="utf-8",
    )
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_openclaw_status(paths, json_mode=True)
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "openclaw_status"
    assert payload["status"] == "offline"
    assert payload["functional"] is False


def test_openclaw_status_reports_online_when_ready(monkeypatch, tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "secrets.json").write_text(
        json.dumps(
            {
                "openclaw": {
                    "enabled": True,
                    "gateway_url": "ws://127.0.0.1:18789",
                    "api_url": "http://127.0.0.1:18790",
                    "channels": {
                        "slack": {
                            "enabled": True,
                            "bot_token": "xoxb-live-token",
                            "app_token": "xapp-live-token",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        start_nusyq, "_probe_endpoint_reachable", lambda *_args, **_kwargs: (True, "ok")
    )
    monkeypatch.setattr(start_nusyq, "_resolve_openclaw_cli", lambda: (None, {"strategy": "none"}))
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_openclaw_status(paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "online"
    assert payload["functional"] is True
    assert payload["channels_ready"] == ["slack"]
    assert payload["channels_ready_config"] == ["slack"]


def test_openclaw_status_unknown_channel_does_not_count_as_messaging_ready(
    monkeypatch, tmp_path, capsys
):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "secrets.json").write_text(
        json.dumps(
            {
                "openclaw": {
                    "enabled": True,
                    "gateway_url": "ws://127.0.0.1:18789",
                    "api_url": "http://127.0.0.1:18790",
                    # "my_custom_webhook" is a truly unknown channel — not in
                    # OPENCLAW_CHANNEL_REQUIRED_FIELDS (messaging) nor in
                    # OPENCLAW_SYSTEM_CHANNEL_NAMES (internal targets).
                    # "ollama" was moved to OPENCLAW_INTERNAL_TARGET_SYSTEMS and now
                    # counts as a system channel (routing-ready), changing its behaviour.
                    "channels": {"my_custom_webhook": {"enabled": True}},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        start_nusyq, "_probe_endpoint_reachable", lambda *_args, **_kwargs: (True, "ok")
    )
    monkeypatch.setattr(start_nusyq, "_resolve_openclaw_cli", lambda: (None, {"strategy": "none"}))
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_openclaw_status(paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "degraded"
    assert payload["functional"] is True
    assert payload["messaging_functional"] is False
    assert payload["channels_enabled_known"] == []
    assert payload["channels_enabled_unknown"] == ["my_custom_webhook"]
    assert payload["channels_ready_config"] == []
    assert payload["channels_ready"] == []
    assert any("unknown channels" in note for note in payload["notes"])


def test_handle_copilot_doctor_reports_ok(monkeypatch, tmp_path, capsys):
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    monkeypatch.setattr(
        start_nusyq,
        "_probe_copilot_cli",
        lambda _paths: {
            "installed": True,
            "runtime_ok": True,
            "authenticated": True,
            "functional": True,
            "copilot_path": "/usr/bin/copilot",
        },
    )
    monkeypatch.setattr(
        start_nusyq,
        "_collect_copilot_chat_surface",
        lambda _hub: {
            "copilot_chat_installed": True,
            "pull_request_extension_installed": True,
            "continue_installed": True,
            "chat_ready": True,
            "token_ready": True,
            "activated": True,
            "recovered_after_cancel": False,
            "workspace_profile_hardened": True,
        },
    )
    monkeypatch.setattr(
        start_nusyq,
        "_probe_copilot_router",
        lambda _paths: {
            "functional": True,
            "route_ok": True,
            "execution_path": "copilot_cli",
            "execution_surface": "copilot_cli",
            "requested_surface": "auto",
            "response_preview": "ROUTER-OK",
        },
    )
    monkeypatch.setattr(
        start_nusyq,
        "_collect_copilot_terminal_surface",
        lambda _hub: {
            "log_exists": True,
            "recent_router_receipts": True,
            "registry_status": "active",
            "pid": 27528,
        },
    )

    rc = start_nusyq._handle_copilot_doctor(paths, json_mode=True)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "copilot_doctor"
    assert payload["status"] == "ok"
    assert payload["functional"] is True
    assert payload["router_probe"]["execution_path"] == "copilot_cli"
    assert payload["router_probe"]["execution_surface"] == "copilot_cli"
    assert payload["surface_contract"]["observed_only_surfaces"]["chat_ui"]["surface"] == "vscode_copilot_chat_surface"
    assert payload["report_path"].endswith("copilot_doctor_latest.json")


def test_handle_claude_doctor_reports_ok(monkeypatch, tmp_path, capsys):
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    script_dir = tmp_path / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    (script_dir / "run_claude.ps1").write_text("# test stub\n", encoding="utf-8")
    monkeypatch.setattr(
        start_nusyq,
        "_resolve_powershell_executable",
        lambda: "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
    )
    monkeypatch.setattr(
        start_nusyq,
        "run",
        lambda cmd, cwd=None, timeout_s=0: (
            0,
            "=== Claude Preflight ===\nclaude: ok",
            "",
        ),
    )
    monkeypatch.setattr(
        start_nusyq,
        "_probe_claude_cli",
        lambda _paths: {
            "installed": True,
            "authenticated": True,
            "functional": True,
            "claude_path": "/usr/bin/claude",
            "surface": "anthropic_claude_cli",
        },
    )
    monkeypatch.setattr(
        start_nusyq,
        "_probe_claude_router",
        lambda _paths: {
            "functional": True,
            "route_ok": True,
            "execution_path": "claude_cli",
            "execution_surface": "claude_cli",
            "agent_identity": "anthropic_claude",
            "response_preview": "CLAUDE-ROUTER-OK.",
        },
    )
    monkeypatch.setattr(
        start_nusyq,
        "_collect_claude_terminal_surface",
        lambda _hub: {
            "surface": "claude_terminal_receipts",
            "log_exists": True,
            "recent_router_receipts": True,
            "registry_status": "active",
            "pid": 27529,
        },
    )

    rc = start_nusyq._handle_claude_doctor(paths, json_mode=True)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "claude_doctor"
    assert payload["status"] == "ok"
    assert payload["functional"] is True
    assert payload["router_probe"]["execution_path"] == "claude_cli"
    assert payload["router_probe"]["execution_surface"] == "claude_cli"
    assert payload["surface_contract"]["routable_surfaces"]["cli"]["surface"] == "anthropic_claude_cli"
    assert payload["report_path"].endswith("claude_doctor_latest.json")


def test_handle_codex_doctor_reports_ok(monkeypatch, tmp_path, capsys):
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    monkeypatch.setattr(
        start_nusyq,
        "_probe_codex_cli",
        lambda _paths: {
            "installed": True,
            "runtime_ok": True,
            "functional": True,
            "codex_path": "/usr/bin/codex",
            "surface": "openai_codex_cli",
        },
    )
    monkeypatch.setattr(
        start_nusyq,
        "_probe_codex_router",
        lambda _paths: {
            "functional": True,
            "route_ok": True,
            "execution_path": "codex_cli",
            "execution_surface": "codex_cli",
            "agent_identity": "openai_codex",
            "response_preview": "CODEX-ROUTER-OK",
            "target": "codex",
        },
    )
    monkeypatch.setattr(
        start_nusyq,
        "_collect_codex_terminal_surface",
        lambda _hub: {
            "surface": "codex_terminal_receipts",
            "log_exists": True,
            "recent_router_receipts": True,
            "registry_status": "active",
            "pid": 27530,
        },
    )

    rc = start_nusyq._handle_codex_doctor(paths, json_mode=True)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "codex_doctor"
    assert payload["status"] == "ok"
    assert payload["functional"] is True
    assert payload["router_probe"]["execution_path"] == "codex_cli"
    assert payload["router_probe"]["execution_surface"] == "codex_cli"
    assert payload["surface_contract"]["routable_surfaces"]["cli"]["surface"] == "openai_codex_cli"
    assert payload["report_path"].endswith("codex_doctor_latest.json")


def test_handle_multi_agent_doctor_reports_ok(monkeypatch, tmp_path, capsys):
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    monkeypatch.setattr(
        start_nusyq,
        "_handle_claude_doctor",
        lambda _paths, json_mode=False: (
            print(
                json.dumps(
                    {
                        "action": "claude_doctor",
                        "status": "ok",
                        "functional": True,
                        "surface_contract": {"router_target": "claude"},
                    }
                )
            )
            if json_mode
            else None
        )
        or 0,
    )
    monkeypatch.setattr(
        start_nusyq,
        "_handle_codex_doctor",
        lambda _paths, json_mode=False: (
            print(
                json.dumps(
                    {
                        "action": "codex_doctor",
                        "status": "ok",
                        "functional": True,
                        "surface_contract": {"router_target": "codex"},
                    }
                )
            )
            if json_mode
            else None
        )
        or 0,
    )
    monkeypatch.setattr(
        start_nusyq,
        "_handle_copilot_doctor",
        lambda _paths, json_mode=False: (
            print(
                json.dumps(
                    {
                        "action": "copilot_doctor",
                        "status": "ok",
                        "functional": True,
                        "surface_contract": {"router_target": "copilot"},
                    }
                )
            )
            if json_mode
            else None
        )
        or 0,
    )

    rc = start_nusyq._handle_multi_agent_doctor(paths, json_mode=True)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "multi_agent_doctor"
    assert payload["status"] == "ok"
    assert payload["functional"] is True
    assert payload["summary"]["healthy_agents"] == ["claude", "codex", "copilot"]
    assert payload["summary"]["surface_contracts"]["claude"]["router_target"] == "claude"
    assert payload["report_path"].endswith("multi_agent_doctor_latest.json")


def test_handle_delegation_matrix_reports_ok(monkeypatch, tmp_path, capsys):
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    matrix_payload = {
        "summary": {
            "handler_count": 24,
            "delegation_edge_count": 4,
            "execution_path_ready_count": 5,
            "execution_path_ready_systems": ["claude_cli", "codex", "copilot"],
        }
    }
    monkeypatch.setattr(
        start_nusyq,
        "run",
        lambda cmd, cwd=None, timeout_s=0: (
            0,
            json.dumps(matrix_payload),
            "",
        ),
    )

    rc = start_nusyq._handle_delegation_matrix(paths, json_mode=True)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "delegation_matrix"
    assert payload["status"] == "ok"
    assert payload["functional"] is True
    assert payload["summary"]["delegation_edge_count"] == 4
    assert payload["report_path"].endswith("delegation_matrix_latest.json")


def test_handle_agent_fleet_doctor_reports_degraded_with_taxonomy(monkeypatch, tmp_path, capsys):
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    reports_dir = tmp_path / "state" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "terminal_awareness_latest.json").write_text(
        json.dumps({"terminals": [{"key": "ai_council"}, {"key": "culture_ship"}, {"key": "simulatedverse"}]}),
        encoding="utf-8",
    )
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "ROSETTA_STONE.md").write_text("ok", encoding="utf-8")
    (docs_dir / "AGENT_TUTORIAL.md").write_text("ok", encoding="utf-8")
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts" / "nusyq_dispatch.py").write_text("# stub\n", encoding="utf-8")

    monkeypatch.setattr(
        start_nusyq,
        "_handle_ai_status",
        lambda _paths, json_mode=False: (
            print(
                json.dumps(
                    {
                        "action": "ai_status",
                        "status": "ok",
                        "services": {
                            "chatdev": {"healthy": True, "status": "ready"},
                            "ollama": {"healthy": True, "status": "ready"},
                            "lmstudio": {"healthy": False, "status": "offline"},
                            "skyclaw": {"healthy": True, "status": "ready"},
                            "simulatedverse": {"healthy": True, "status": "ready"},
                            "metaclaw": {"healthy": True, "status": "ready"},
                            "hermes_agent": {"healthy": True, "status": "ready"},
                            "factory": {"healthy": True, "status": "ready"},
                            "quantum_resolver": {"healthy": True, "status": "ready"},
                        },
                    }
                )
            )
            if json_mode
            else None
        )
        or 0,
    )
    monkeypatch.setattr(
        start_nusyq,
        "_handle_openclaw_status",
        lambda _paths, json_mode=False: (
            print(
                json.dumps(
                    {
                        "action": "openclaw_status",
                        "status": "online",
                        "functional": True,
                        "messaging_functional": False,
                    }
                )
            )
            if json_mode
            else None
        )
        or 0,
    )
    monkeypatch.setattr(
        start_nusyq,
        "_handle_culture_ship_status",
        lambda _args, _paths, json_mode=False: (
            print(
                json.dumps(
                    {
                        "action": "culture_ship_status",
                        "status": "completed",
                        "rc": 0,
                        "finished_at": "2026-03-01T00:00:00+00:00",
                    }
                )
            )
            if json_mode
            else None
        )
        or 0,
    )
    monkeypatch.setattr(
        start_nusyq,
        "_handle_delegation_matrix",
        lambda _paths, json_mode=False: (
            print(
                json.dumps(
                    {
                        "action": "delegation_matrix",
                        "status": "ok",
                        "functional": True,
                        "result": {
                            "summary": {
                                "router_runtime_contract_enabled": True,
                                "execution_path_ready_systems": [
                                    "chatdev",
                                    "openclaw",
                                    "skyclaw",
                                    "quantum_resolver",
                                    "factory",
                                ],
                            },
                            "entries": [
                                {"system": "chatdev", "probe": {"ok": True}},
                                {"system": "openclaw", "probe": {"ok": True}},
                                {"system": "skyclaw", "probe": {"ok": True}},
                                {"system": "intermediary", "probe": {"ok": None}},
                            ],
                        },
                    }
                )
            )
            if json_mode
            else None
        )
        or 0,
    )
    monkeypatch.setattr(
        start_nusyq,
        "_handle_multi_agent_doctor",
        lambda _paths, json_mode=False: (
            print(
                json.dumps(
                    {
                        "action": "multi_agent_doctor",
                        "status": "ok",
                        "functional": True,
                        "agents": {
                            "claude": {"functional": True, "status": "ok"},
                            "codex": {"functional": True, "status": "ok"},
                            "copilot": {"functional": False, "status": "degraded"},
                        },
                    }
                )
            )
            if json_mode
            else None
        )
        or 0,
    )

    rc = start_nusyq._handle_agent_fleet_doctor(paths, json_mode=True)

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "agent_fleet_doctor"
    assert payload["status"] == "degraded"
    assert "copilot" in payload["summary"]["critical_degraded"]
    assert payload["surfaces"]["ai_council"]["kind"] == "dispatcher_only"
    assert payload["surfaces"]["metaclaw"]["kind"] == "passive_runtime"
    assert payload["surfaces"]["culture_ship"]["status"] == "stale_history"
    assert payload["surfaces"]["rosetta_stone"]["kind"] == "documentation"
    assert payload["report_path"].endswith("agent_fleet_doctor_latest.json")


def test_parse_openclaw_internal_send_args_parses_flags():
    options, error = start_nusyq._parse_openclaw_internal_send_args(
        [
            "openclaw_internal_send",
            "--system=ollama",
            "--channel=internal",
            "--user-id=codex",
            "--username=codex",
            "--task-type=analyze",
            "--text=hello world",
        ]
    )
    assert error is None
    assert options is not None
    assert options.target_system == "ollama"
    assert options.channel == "internal"
    assert options.user_id == "codex"
    assert options.username == "codex"
    assert options.task_type == "analyze"
    assert options.text == "hello world"


def test_parse_openclaw_internal_send_args_rejects_missing_text():
    options, error = start_nusyq._parse_openclaw_internal_send_args(
        ["openclaw_internal_send", "--system=ollama"]
    )
    assert options is None
    assert error == "missing_text"


def test_parse_openclaw_internal_send_args_supports_claude_and_codex_targets():
    options, error = start_nusyq._parse_openclaw_internal_send_args(
        ["openclaw_internal_send", "--system=claude_cli", "--text=hello"]
    )
    assert error is None
    assert options is not None
    assert options.target_system == "claude_cli"

    alias_options, alias_error = start_nusyq._parse_openclaw_internal_send_args(
        ["openclaw_internal_send", "--system=vscode_codex", "--text=hello"]
    )
    assert alias_error is None
    assert alias_options is not None
    assert alias_options.target_system == "vscode_codex"


def test_handle_openclaw_internal_send_uses_bridge_and_receipt(tmp_path, capsys, monkeypatch):
    class _Bridge:
        async def handle_inbound_message(self, message):
            assert message["target_system"] == "ollama"
            return {
                "status": "success",
                "channel": message["channel"],
                "user_id": message["user_id"],
                "task_id": "task-123",
                "result_text": "ok",
            }

        async def send_result(self, channel, target_user_id, result_text, task_id):
            assert channel == "internal"
            assert target_user_id == "codex"
            assert result_text == "ok"
            assert task_id == "task-123"
            return True

    fake_module = types.SimpleNamespace(
        get_openclaw_gateway_bridge=lambda force_reload=False: _Bridge()
    )
    monkeypatch.setitem(sys.modules, "src.integrations.openclaw_gateway_bridge", fake_module)

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_openclaw_internal_send(
        [
            "openclaw_internal_send",
            "--system=ollama",
            "--user-id=codex",
            "--channel=internal",
            "--text=ping",
        ],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "openclaw_internal_send"
    assert payload["functional"] is True
    assert payload["local_receipt_written"] is True
    assert payload["result"]["task_id"] == "task-123"


def test_integration_health_degraded_when_required_signal_fails(monkeypatch, tmp_path, capsys):
    health_payload = {
        "mode": "fast",
        "environment": {
            "ollama_status": {"ok": True, "code": 200},
            "simulatedverse_status": {"ok": False, "error": "down"},
            "mcp_server": None,
            "mcp_status": None,
        },
    }
    monkeypatch.setattr(
        start_nusyq, "run", lambda *_args, **_kwargs: (0, json.dumps(health_payload), "")
    )

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_integration_health(["integration_health"], paths, json_mode=True)
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "degraded"
    assert payload["functional"] is False
    assert payload["signal_checks"]["simulatedverse"] is False
    assert payload["failed_signals"] == ["simulatedverse"]


def test_integration_health_ok_when_signals_pass(monkeypatch, tmp_path, capsys):
    health_payload = {
        "mode": "fast",
        "environment": {
            "ollama_status": {"ok": True, "code": 200},
            "simulatedverse_status": {"ok": True, "code": 200},
            "mcp_server": None,
            "mcp_status": None,
        },
    }
    monkeypatch.setattr(
        start_nusyq, "run", lambda *_args, **_kwargs: (0, json.dumps(health_payload), "")
    )

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_integration_health(["integration_health"], paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["functional"] is True
    assert payload["failed_signals"] == []


def test_integration_health_attempts_simulatedverse_repair_and_rechecks(
    monkeypatch, tmp_path, capsys
):
    responses = [
        (
            0,
            json.dumps(
                {
                    "mode": "fast",
                    "environment": {
                        "ollama_status": {"ok": True, "code": 200},
                        "simulatedverse_status": {"ok": False, "error": "down"},
                        "mcp_server": None,
                        "mcp_status": None,
                    },
                }
            ),
            "",
        ),
        (
            0,
            json.dumps(
                {
                    "mode": "fast",
                    "environment": {
                        "ollama_status": {"ok": True, "code": 200},
                        "simulatedverse_status": {"ok": True, "code": 200},
                        "mcp_server": None,
                        "mcp_status": None,
                    },
                }
            ),
            "",
        ),
    ]

    def fake_run(*_args, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setattr(
        start_nusyq,
        "_attempt_simulatedverse_autostart",
        lambda *_args, **_kwargs: {"status": "ok", "functional": True},
    )

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    rc = start_nusyq._handle_integration_health(["integration_health"], paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["simulatedverse_repair_attempt"]["functional"] is True
    assert payload["simulatedverse_repair_recheck"]["signal_checks"]["simulatedverse"] is True


def test_integration_health_can_skip_simulatedverse_repair(monkeypatch, tmp_path, capsys):
    health_payload = {
        "mode": "fast",
        "environment": {
            "ollama_status": {"ok": True, "code": 200},
            "simulatedverse_status": {"ok": False, "error": "down"},
            "mcp_server": None,
            "mcp_status": None,
        },
    }
    monkeypatch.setattr(
        start_nusyq, "run", lambda *_args, **_kwargs: (0, json.dumps(health_payload), "")
    )
    called = {"repair": False}

    def fake_repair(*_args, **_kwargs):
        called["repair"] = True
        return {"status": "ok", "functional": True}

    monkeypatch.setattr(start_nusyq, "_attempt_simulatedverse_autostart", fake_repair)

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    rc = start_nusyq._handle_integration_health(
        ["integration_health", "--no-repair-simulatedverse"], paths, json_mode=True
    )
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["repair_allowed"] is False
    assert payload["simulatedverse_repair_attempt"] is None
    assert called["repair"] is False


def test_integration_health_does_not_forward_local_repair_flag(monkeypatch, tmp_path, capsys):
    captured_cmd: list[str] = []

    def fake_run(cmd, **_kwargs):
        nonlocal captured_cmd
        captured_cmd = list(cmd)
        payload = {
            "mode": "fast",
            "environment": {
                "ollama_status": {"ok": True, "code": 200},
                "simulatedverse_status": {"ok": False, "error": "down"},
                "mcp_server": None,
                "mcp_status": None,
            },
        }
        return 0, json.dumps(payload), ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setattr(
        start_nusyq,
        "_attempt_simulatedverse_autostart",
        lambda *_args, **_kwargs: {"status": "degraded", "functional": False},
    )

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    rc = start_nusyq._handle_integration_health(
        ["integration_health", "--no-repair-simulatedverse"], paths, json_mode=True
    )
    assert rc == 1
    assert "--no-repair-simulatedverse" not in captured_cmd
    payload = json.loads(capsys.readouterr().out)
    assert payload["repair_allowed"] is False


def test_integration_health_does_not_forward_orchestration_flags(monkeypatch, tmp_path, capsys):
    captured_cmd: list[str] = []

    def fake_run(cmd, **_kwargs):
        nonlocal captured_cmd
        captured_cmd = list(cmd)
        payload = {
            "mode": "fast",
            "environment": {
                "ollama_status": {"ok": True, "code": 200},
                "simulatedverse_status": {"ok": False, "error": "down"},
                "mcp_server": None,
                "mcp_status": None,
            },
        }
        return 0, json.dumps(payload), ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setattr(
        start_nusyq,
        "_attempt_simulatedverse_autostart",
        lambda *_args, **_kwargs: {"status": "degraded", "functional": False},
    )

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    rc = start_nusyq._handle_integration_health(
        ["integration_health", "--sync", "--json", "--attempt-simulatedverse-repair"],
        paths,
        json_mode=True,
    )
    assert rc == 1
    assert "--sync" not in captured_cmd
    assert "--json" not in captured_cmd
    assert "--attempt-simulatedverse-repair" not in captured_cmd
    payload = json.loads(capsys.readouterr().out)
    assert payload["repair_allowed"] is True
    assert payload["simulatedverse_repair_attempt"]["functional"] is False


def test_integration_health_off_mode_ignores_simulatedverse_signal(monkeypatch, tmp_path, capsys):
    health_payload = {
        "mode": "fast",
        "environment": {
            "ollama_status": {"ok": True, "code": 200},
            "simulatedverse_status": {"ok": False, "error": "down"},
            "mcp_server": None,
            "mcp_status": None,
        },
    }
    monkeypatch.setattr(
        start_nusyq, "run", lambda *_args, **_kwargs: (0, json.dumps(health_payload), "")
    )
    called = {"repair": False}

    def fake_repair(*_args, **_kwargs):
        called["repair"] = True
        return {"status": "ok", "functional": True}

    monkeypatch.setattr(start_nusyq, "_attempt_simulatedverse_autostart", fake_repair)

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    rc = start_nusyq._handle_integration_health(
        ["integration_health", "--simulatedverse-mode=off"], paths, json_mode=True
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["functional"] is True
    assert payload["simulatedverse_mode"] == "off"
    assert "simulatedverse" in payload["ignored_signals"]
    assert payload["failed_signals"] == []
    assert payload["repair_allowed"] is False
    assert called["repair"] is False


def test_integration_health_auto_mode_ignores_probe_blocked_signals(monkeypatch, tmp_path, capsys):
    # Ensure auto mode is used regardless of ambient env vars
    monkeypatch.setenv("NUSYQ_SIMULATEDVERSE_MODE", "auto")

    health_payload = {
        "mode": "fast",
        "environment": {
            "ollama_status": {
                "ok": False,
                "error": "[Errno 1] Operation not permitted",
                "probe_blocked": True,
            },
            "simulatedverse_status": {
                "ok": False,
                "error": [{"http://127.0.0.1:5002/health": "Permission denied"}],
                "probe_blocked": True,
            },
            "mcp_server": None,
            "mcp_status": None,
        },
    }
    monkeypatch.setattr(
        start_nusyq, "run", lambda *_args, **_kwargs: (0, json.dumps(health_payload), "")
    )
    called = {"repair": False}

    def fake_repair(*_args, **_kwargs):
        called["repair"] = True
        return {"status": "ok", "functional": True}

    monkeypatch.setattr(start_nusyq, "_attempt_simulatedverse_autostart", fake_repair)

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    rc = start_nusyq._handle_integration_health(["integration_health"], paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["functional"] is True
    assert sorted(payload["probe_blocked_signals"]) == ["ollama", "simulatedverse"]
    assert sorted(payload["ignored_signals"]) == ["ollama", "simulatedverse"]
    assert called["repair"] is False


def test_integration_health_auto_mode_keeps_connection_refused_signal(
    monkeypatch, tmp_path, capsys
):
    health_payload = {
        "mode": "fast",
        "environment": {
            "ollama_status": {"ok": True, "code": 200},
            "simulatedverse_status": {
                "ok": False,
                "error": "[Errno 111] Connection refused",
            },
            "mcp_server": None,
            "mcp_status": None,
        },
    }
    monkeypatch.setattr(
        start_nusyq, "run", lambda *_args, **_kwargs: (0, json.dumps(health_payload), "")
    )
    monkeypatch.setattr(
        start_nusyq,
        "_attempt_simulatedverse_autostart",
        lambda *_args, **_kwargs: {"status": "degraded", "functional": False},
    )

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    rc = start_nusyq._handle_integration_health(["integration_health"], paths, json_mode=True)
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["functional"] is False
    assert payload["failed_signals"] == ["simulatedverse"]
    assert payload["probe_blocked_signals"] == []
    assert payload["ignored_signals"] == []


def test_attempt_simulatedverse_autostart_sanitizes_windows_launch_path(monkeypatch, tmp_path):
    captured_cmd: list[str] = []

    monkeypatch.setattr(
        start_nusyq, "_simulatedverse_health_urls", lambda _port: ["http://x/health"]
    )
    monkeypatch.setattr(
        start_nusyq, "_probe_http_health", lambda *_args, **_kwargs: (False, "down")
    )
    monkeypatch.setattr(start_nusyq, "_to_windows_path", lambda _path: "C:\\SimVerse\\Runtime\\")
    monkeypatch.setattr(
        start_nusyq.shutil, "which", lambda exe: "cmd.exe" if exe == "cmd.exe" else None
    )

    def fake_run(cmd, **_kwargs):
        nonlocal captured_cmd
        captured_cmd = list(cmd)
        return 0, "", ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    payload = {"environment": {"simulatedverse_base": "http://127.0.0.1:5000"}}
    result = start_nusyq._attempt_simulatedverse_autostart(paths, payload, timeout_s=0)

    assert result["launch_rc"] == 0
    assert captured_cmd[:2] == ["cmd.exe", "/c"]
    launch_script = captured_cmd[2]
    assert "cd /d C:\\SimVerse\\Runtime" in launch_script
    assert 'set "SIMULATEDVERSE_PORT=5000"' in launch_script
    assert 'start "" /b cmd /c npm run dev' in launch_script
    assert '\\" &&' not in launch_script


def test_attempt_simulatedverse_autostart_detects_blocked_windows_launcher(monkeypatch, tmp_path):
    calls: list[list[str]] = []
    monkeypatch.setattr(
        start_nusyq, "_simulatedverse_health_urls", lambda _port: ["http://x/health"]
    )
    monkeypatch.setattr(
        start_nusyq, "_probe_http_health", lambda *_args, **_kwargs: (False, "down")
    )
    monkeypatch.setattr(start_nusyq, "_to_windows_path", lambda _path: "C:\\SimVerse\\Runtime")

    def fake_which(exe: str):
        if exe == "cmd.exe":
            return "cmd.exe"
        if exe == "powershell.exe":
            return "powershell.exe"
        return None

    monkeypatch.setattr(start_nusyq.shutil, "which", fake_which)

    def fake_run(cmd, **_kwargs):
        calls.append(list(cmd))
        if cmd[0] == "cmd.exe":
            return 1, "", "PermissionError: [Errno 13] Permission denied: 'cmd.exe'"
        return 0, "unexpected", ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)

    class _FakeMinimal:
        def __init__(self):
            self.simulatedverse_path = None
            self.base_url = None

        def start_agents_only(self, timeout=30):
            return None

        def check_if_running(self):
            return False

    fake_module = types.SimpleNamespace(SimulatedVerseMinimal=_FakeMinimal)
    monkeypatch.setitem(sys.modules, "scripts.start_simulatedverse_minimal", fake_module)

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    payload = {"environment": {"simulatedverse_base": "http://127.0.0.1:5000"}}
    result = start_nusyq._attempt_simulatedverse_autostart(paths, payload, timeout_s=0)

    assert calls[0][0] == "cmd.exe"
    assert not any(call and call[0] == "powershell.exe" for call in calls)
    assert result["launcher_blocked"] is True
    assert result["fallback_attempt"] is None


def test_attempt_simulatedverse_autostart_uses_powershell_fallback(monkeypatch, tmp_path):
    calls: list[list[str]] = []
    starter_script = tmp_path / "scripts" / "Start-SimulatedVerse.ps1"
    starter_script.parent.mkdir(parents=True, exist_ok=True)
    starter_script.write_text("Write-Host 'starter'", encoding="utf-8")

    # Enable legacy PowerShell fallback for this test
    monkeypatch.setenv("NUSYQ_ENABLE_LEGACY_SIMVERSE_FALLBACK", "1")

    # Disable minimal launcher by making the module unavailable
    import sys

    monkeypatch.setitem(sys.modules, "scripts.start_simulatedverse_minimal", None)

    monkeypatch.setattr(
        start_nusyq, "_simulatedverse_health_urls", lambda _port: ["http://x/health"]
    )
    monkeypatch.setattr(
        start_nusyq, "_probe_http_health", lambda *_args, **_kwargs: (False, "down")
    )
    monkeypatch.setattr(start_nusyq, "_to_windows_path", lambda _path: "C:\\SimVerse\\Runtime")

    def fake_which(exe: str):
        if exe == "cmd.exe":
            return "cmd.exe"
        if exe == "powershell.exe":
            return "powershell.exe"
        return None

    monkeypatch.setattr(start_nusyq.shutil, "which", fake_which)

    def fake_run(cmd, **_kwargs):
        calls.append(list(cmd))
        if cmd[0] == "cmd.exe":
            return 1, "", "cmd launch failed"
        return 0, "fallback ok", ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    payload = {"environment": {"simulatedverse_base": "http://127.0.0.1:5000"}}
    result = start_nusyq._attempt_simulatedverse_autostart(paths, payload, timeout_s=0)

    assert calls[0][0] == "cmd.exe"
    assert any(call and call[0] == "powershell.exe" for call in calls)
    assert result["fallback_attempt"]["status"] == "ok"
    assert result["fallback_attempt"]["rc"] == 0


def test_attempt_simulatedverse_autostart_uses_minimal_launcher_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(
        start_nusyq, "_simulatedverse_health_urls", lambda _port: ["http://x/health"]
    )
    monkeypatch.setattr(
        start_nusyq, "_probe_http_health", lambda *_args, **_kwargs: (False, "down")
    )
    monkeypatch.setattr(start_nusyq.shutil, "which", lambda _exe: None)
    monkeypatch.setattr(start_nusyq, "run", lambda *_args, **_kwargs: (1, "", "no launcher"))

    class _FakeMinimal:
        def __init__(self):
            self.simulatedverse_path = None
            self.base_url = None

        def start_agents_only(self, timeout=30):
            return object()

        def check_if_running(self):
            return True

    fake_module = types.SimpleNamespace(SimulatedVerseMinimal=_FakeMinimal)
    monkeypatch.setitem(sys.modules, "scripts.start_simulatedverse_minimal", fake_module)

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=tmp_path, nusyq_root=None)
    payload = {"environment": {"simulatedverse_base": "http://127.0.0.1:5000"}}
    result = start_nusyq._attempt_simulatedverse_autostart(paths, payload, timeout_s=0)

    assert result["launch_command"] is None
    assert result["minimal_attempt"]["status"] == "ok"
    assert result["minimal_attempt"]["running"] is True
    assert result["minimal_attempt"]["process_started"] is True


def test_integration_health_check_uses_wsl_gateway_fallback(monkeypatch):
    class _Resp:
        def __init__(self, status_code):
            self.status_code = status_code

    def fake_get(url, timeout=0):
        if url.endswith("/api/tags"):
            return _Resp(200)
        if url.startswith("http://127.0.0.1:5002/"):
            raise integration_health_check.requests.RequestException("connection refused")
        if url.startswith("http://172.24.224.1:5002/"):
            return _Resp(200)
        raise integration_health_check.requests.RequestException(f"unexpected url: {url}")

    monkeypatch.setattr(
        integration_health_check, "_resolve_ollama_url", lambda: "http://127.0.0.1:11434"
    )
    monkeypatch.setattr(
        integration_health_check, "_resolve_simulatedverse_url", lambda: "http://127.0.0.1:5002"
    )
    monkeypatch.setattr(integration_health_check, "_is_wsl", lambda: True)
    monkeypatch.setattr(integration_health_check, "_wsl_default_gateway_ip", lambda: "172.24.224.1")
    monkeypatch.setattr(integration_health_check.requests, "get", fake_get)

    result = integration_health_check.check_environment()
    sim_status = result.get("simulatedverse_status", {})
    assert sim_status.get("ok") is True
    assert sim_status.get("probe") == "wsl_gateway"
    assert result.get("simulatedverse_base") == "http://172.24.224.1:5002"


def test_integration_health_normalizes_windows_paths_in_linux_runtime(monkeypatch):
    raw_path = r"C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse"

    original_exists = Path.exists

    def fake_exists(path_obj):
        if str(path_obj) == raw_path:
            return True
        return original_exists(path_obj)

    monkeypatch.setattr(Path, "exists", fake_exists)

    resolved = integration_health_check._resolve_filesystem_path(raw_path)

    if os.name == "nt":
        assert str(resolved) == raw_path
    else:
        assert str(resolved) == "/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"


def test_integration_health_check_without_wsl_fallback_reports_failure(monkeypatch):
    class _Resp:
        def __init__(self, status_code):
            self.status_code = status_code

    def fake_get(url, timeout=0):
        if url.endswith("/api/tags"):
            return _Resp(200)
        if url.startswith("http://127.0.0.1:5002/"):
            raise integration_health_check.requests.RequestException("connection refused")
        raise integration_health_check.requests.RequestException(f"unexpected url: {url}")

    monkeypatch.setattr(
        integration_health_check, "_resolve_ollama_url", lambda: "http://127.0.0.1:11434"
    )
    monkeypatch.setattr(
        integration_health_check, "_resolve_simulatedverse_url", lambda: "http://127.0.0.1:5002"
    )
    monkeypatch.setattr(integration_health_check, "_is_wsl", lambda: False)
    monkeypatch.setattr(integration_health_check.requests, "get", fake_get)

    result = integration_health_check.check_environment()
    sim_status = result.get("simulatedverse_status", {})
    assert sim_status.get("ok") is False


def test_integration_health_check_mode_off_skips_simulatedverse_probe(monkeypatch):
    class _Resp:
        def __init__(self, status_code):
            self.status_code = status_code

    seen_urls: list[str] = []

    def fake_get(url, timeout=0):
        seen_urls.append(url)
        if url.endswith("/api/tags"):
            return _Resp(200)
        raise integration_health_check.requests.RequestException(f"unexpected url: {url}")

    monkeypatch.setattr(
        integration_health_check, "_resolve_ollama_url", lambda: "http://127.0.0.1:11434"
    )
    monkeypatch.setattr(
        integration_health_check, "_resolve_simulatedverse_url", lambda: "http://127.0.0.1:5002"
    )
    monkeypatch.setattr(integration_health_check.requests, "get", fake_get)

    result = integration_health_check.check_environment(simulatedverse_mode="off")
    sim_status = result.get("simulatedverse_status", {})
    assert sim_status.get("ok") is True
    assert sim_status.get("skipped") is True
    assert all("/5002/" not in url for url in seen_urls)


def test_integration_health_check_marks_probe_blocked_status(monkeypatch):
    def fake_get(_url, timeout=0):
        raise integration_health_check.requests.RequestException(
            "[Errno 1] Operation not permitted"
        )

    monkeypatch.setenv("MCP_SERVER_URL", "http://127.0.0.1:9000")
    monkeypatch.setattr(
        integration_health_check, "_resolve_ollama_url", lambda: "http://127.0.0.1:11434"
    )
    monkeypatch.setattr(
        integration_health_check, "_resolve_simulatedverse_url", lambda: "http://127.0.0.1:5002"
    )
    monkeypatch.setattr(integration_health_check, "_is_wsl", lambda: False)
    monkeypatch.setattr(integration_health_check.requests, "get", fake_get)

    result = integration_health_check.check_environment()
    assert result["ollama_status"]["ok"] is False
    assert result["ollama_status"]["probe_blocked"] is True
    assert result["simulatedverse_status"]["ok"] is False
    assert result["simulatedverse_status"]["probe_blocked"] is True
    assert result["mcp_status"]["ok"] is False
    assert result["mcp_status"]["probe_blocked"] is True


def test_integration_health_check_connection_refused_not_probe_blocked(monkeypatch):
    class _Resp:
        def __init__(self, status_code):
            self.status_code = status_code

    def fake_get(url, timeout=0):
        if url.endswith("/api/tags"):
            return _Resp(200)
        raise integration_health_check.requests.RequestException("[Errno 111] Connection refused")

    monkeypatch.setattr(
        integration_health_check, "_resolve_ollama_url", lambda: "http://127.0.0.1:11434"
    )
    monkeypatch.setattr(
        integration_health_check, "_resolve_simulatedverse_url", lambda: "http://127.0.0.1:5002"
    )
    monkeypatch.setattr(integration_health_check, "_is_wsl", lambda: False)
    monkeypatch.setattr(integration_health_check.requests, "get", fake_get)

    result = integration_health_check.check_environment()
    sim_status = result.get("simulatedverse_status", {})
    assert sim_status.get("ok") is False
    assert sim_status.get("probe_blocked") is not True


def test_simulatedverse_base_candidates_include_legacy_port_variant(monkeypatch):
    monkeypatch.setenv("SIMULATEDVERSE_PORT", "5001")
    candidates = integration_health_check._simulatedverse_base_candidates("http://127.0.0.1:5001")
    assert candidates == [
        "http://127.0.0.1:5001",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5002",
    ]


def test_antigravity_status_uses_probe(monkeypatch, tmp_path, capsys):
    from src.api import systems as systems_api

    monkeypatch.setattr(
        systems_api, "_probe_system_status", lambda _system_id: ("online", "required 1/1")
    )
    monkeypatch.setattr(
        start_nusyq,
        "_collect_open_antigravity_runtime",
        lambda _paths, _options: {
            "pid": 1234,
            "running": True,
            "port": 8080,
            "host": "127.0.0.1",
            "health_url": "http://127.0.0.1:8080/health",
            "health_ok": True,
            "health_detail": "HTTP 200",
            "pid_file": str(tmp_path / "state" / "runtime" / "open_antigravity_runtime.pid"),
        },
    )
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_antigravity_status(paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "antigravity_status"
    assert payload["status"] == "online"
    assert payload["functional"] is True


def test_open_antigravity_start_status_stop(monkeypatch, tmp_path, capsys):
    web_root = tmp_path / "web" / "modular-window-server"
    web_root.mkdir(parents=True, exist_ok=True)
    (web_root / "server.js").write_text("console.log('ok');\n", encoding="utf-8")
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)

    state = {"running": True}

    class FakePopen:
        def __init__(
            self, cmd, cwd=None, env=None, stdout=None, stderr=None, start_new_session=None
        ):
            self.pid = 6262

    monkeypatch.setattr(start_nusyq.shutil, "which", lambda _name: "/usr/bin/node")
    monkeypatch.setattr(start_nusyq.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(
        start_nusyq, "_is_process_running", lambda _pid: bool(_pid) and state["running"]
    )
    monkeypatch.setattr(
        start_nusyq,
        "_terminate_job_process",
        lambda _pid, grace_s=2.0: state.update({"running": False}) or True,
    )
    monkeypatch.setattr(
        start_nusyq,
        "_probe_http_health",
        lambda _url, timeout_s=1.5: (state["running"], "HTTP 200" if state["running"] else "down"),
    )
    monkeypatch.setattr(start_nusyq, "_antigravity_probe_truth", lambda: ("online", "required 1/1"))

    rc_start = start_nusyq._handle_open_antigravity_start(
        ["open_antigravity_start"], paths, json_mode=True
    )
    assert rc_start == 0
    payload_start = json.loads(capsys.readouterr().out)
    assert payload_start["action"] == "open_antigravity_start"
    assert payload_start["status"] == "ok"
    assert payload_start["functional"] is True

    rc_status = start_nusyq._handle_open_antigravity_runtime_status(
        ["open_antigravity_runtime_status"], paths, json_mode=True
    )
    assert rc_status == 0
    payload_status = json.loads(capsys.readouterr().out)
    assert payload_status["status"] == "online"
    assert payload_status["functional"] is True

    rc_stop = start_nusyq._handle_open_antigravity_stop(
        ["open_antigravity_stop"], paths, json_mode=True
    )
    assert rc_stop == 0
    payload_stop = json.loads(capsys.readouterr().out)
    assert payload_stop["status"] == "stopped"


def test_openclaw_status_uses_cli_health_probe(monkeypatch, tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "secrets.json").write_text(
        json.dumps(
            {
                "openclaw": {
                    "enabled": True,
                    "gateway_url": "ws://127.0.0.1:18789",
                    "api_url": "http://127.0.0.1:18790",
                    "channels": {"slack": {"enabled": False, "bot_token": "", "app_token": ""}},
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        start_nusyq, "_probe_endpoint_reachable", lambda *_a, **_k: (False, "refused")
    )
    monkeypatch.setattr(
        start_nusyq, "_resolve_openclaw_cli", lambda: (["openclaw"], {"strategy": "mock"})
    )
    monkeypatch.setattr(
        start_nusyq,
        "_probe_openclaw_gateway_health",
        lambda *_a, **_k: (True, "Gateway Health OK", ["openclaw", "gateway", "health"]),
    )
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_openclaw_status(paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["functional"] is True
    assert payload["gateway_probe_source"] == "openclaw_cli_health"


def test_openclaw_status_rejects_invalid_channel_format(monkeypatch, tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "secrets.json").write_text(
        json.dumps(
            {
                "openclaw": {
                    "enabled": True,
                    "gateway_url": "ws://127.0.0.1:18789",
                    "api_url": "http://127.0.0.1:18790",
                    "channels": {
                        "slack": {
                            "enabled": True,
                            "bot_token": "not-a-real-bot-token",
                            "app_token": "not-a-real-app-token",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(start_nusyq, "_probe_endpoint_reachable", lambda *_a, **_k: (True, "ok"))
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_openclaw_status(paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "degraded"
    assert payload["messaging_functional"] is False
    assert payload["channel_status"]["slack"]["invalid_format_fields"] == ["bot_token", "app_token"]


def test_openclaw_status_runtime_channel_truth_alignment(monkeypatch, tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "secrets.json").write_text(
        json.dumps(
            {
                "openclaw": {
                    "enabled": True,
                    "gateway_url": "ws://127.0.0.1:18789",
                    "api_url": "http://127.0.0.1:18790",
                    "channels": {
                        "slack": {
                            "enabled": True,
                            "bot_token": "xoxb-live-token",
                            "app_token": "xapp-live-token",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(start_nusyq, "_probe_endpoint_reachable", lambda *_a, **_k: (True, "ok"))
    monkeypatch.setattr(
        start_nusyq, "_resolve_openclaw_cli", lambda: (["openclaw"], {"strategy": "mock"})
    )
    monkeypatch.setattr(
        start_nusyq,
        "_probe_openclaw_runtime_channels",
        lambda *_a, **_k: (True, "ok", ["openclaw", "channels", "list", "--json"], [], {}),
    )
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_openclaw_status(paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "degraded"
    assert payload["channels_ready_config"] == ["slack"]
    assert payload["channels_ready"] == []
    assert payload["openclaw_cli_channels_probe_ok"] is True
    assert payload["openclaw_cli_channels"] == []


def test_openclaw_gateway_start_and_stop(monkeypatch, tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "secrets.json").write_text(
        json.dumps({"openclaw": {"gateway_url": "ws://127.0.0.1:18789"}}), encoding="utf-8"
    )
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)

    class FakePopen:
        def __init__(
            self, cmd, cwd=None, stdout=None, stderr=None, start_new_session=None
        ):
            self.pid = 4242

    monkeypatch.setattr(
        start_nusyq, "_resolve_openclaw_cli", lambda: (["openclaw"], {"strategy": "mock"})
    )
    monkeypatch.setattr(start_nusyq.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: bool(_pid))
    monkeypatch.setattr(start_nusyq, "_terminate_job_process", lambda _pid, grace_s=2.0: True)
    monkeypatch.setattr(
        start_nusyq,
        "_probe_openclaw_gateway_health",
        lambda *_a, **_k: (True, "Gateway Health OK", ["openclaw", "gateway", "health"]),
    )

    rc_start = start_nusyq._handle_openclaw_gateway_start(
        ["openclaw_gateway_start"], paths, json_mode=True
    )
    assert rc_start == 0
    payload_start = json.loads(capsys.readouterr().out)
    assert payload_start["action"] == "openclaw_gateway_start"
    assert payload_start["status"] == "ok"

    rc_status = start_nusyq._handle_openclaw_gateway_status(
        ["openclaw_gateway_status"], paths, json_mode=True
    )
    assert rc_status == 0
    payload_status = json.loads(capsys.readouterr().out)
    assert payload_status["action"] == "openclaw_gateway_status"
    assert payload_status["functional"] is True

    rc_stop = start_nusyq._handle_openclaw_gateway_stop(
        ["openclaw_gateway_stop"], paths, json_mode=True
    )
    assert rc_stop == 1
    payload_stop = json.loads(capsys.readouterr().out)
    assert payload_stop["action"] == "openclaw_gateway_stop"


def test_openclaw_bridge_start_status_stop(monkeypatch, tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "secrets.json").write_text(
        json.dumps({"openclaw": {"gateway_url": "ws://127.0.0.1:18789", "bind": "lan"}}),
        encoding="utf-8",
    )
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)

    class FakePopen:
        def __init__(
            self, cmd, cwd=None, stdout=None, stderr=None, start_new_session=None
        ):
            self.pid = 5151

    monkeypatch.setattr(start_nusyq.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: bool(_pid))
    monkeypatch.setattr(start_nusyq, "_terminate_job_process", lambda _pid, grace_s=2.0: True)
    monkeypatch.setattr(start_nusyq, "_bridge_log_markers", lambda _path: (True, None))
    monkeypatch.setattr(start_nusyq, "_wsl_default_gateway_ip", lambda: "172.24.224.1")

    rc_start = start_nusyq._handle_openclaw_bridge_start(
        ["openclaw_bridge_start"], paths, json_mode=True
    )
    assert rc_start == 0
    payload_start = json.loads(capsys.readouterr().out)
    assert payload_start["action"] == "openclaw_bridge_start"
    assert payload_start["status"] == "ok"
    assert payload_start["functional"] is True

    rc_status = start_nusyq._handle_openclaw_bridge_status(
        ["openclaw_bridge_status"], paths, json_mode=True
    )
    assert rc_status == 0
    payload_status = json.loads(capsys.readouterr().out)
    assert payload_status["status"] == "online"
    assert payload_status["functional"] is True

    rc_stop = start_nusyq._handle_openclaw_bridge_stop(
        ["openclaw_bridge_stop"], paths, json_mode=True
    )
    assert rc_stop == 0
    payload_stop = json.loads(capsys.readouterr().out)
    assert payload_stop["status"] == "stopped"


def test_openclaw_bridge_status_masks_stale_connected_marker(monkeypatch, tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "secrets.json").write_text(
        json.dumps({"openclaw": {"gateway_url": "ws://127.0.0.1:18789", "bind": "lan"}}),
        encoding="utf-8",
    )
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)

    runtime_dir = tmp_path / "state" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "openclaw_bridge.pid").write_text(json.dumps({"pid": 5151}), encoding="utf-8")

    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: False)
    monkeypatch.setattr(start_nusyq, "_bridge_log_markers", lambda _path: (True, None))
    monkeypatch.setattr(start_nusyq, "_wsl_default_gateway_ip", lambda: "172.24.224.1")

    rc_status = start_nusyq._handle_openclaw_bridge_status(
        ["openclaw_bridge_status"], paths, json_mode=True
    )
    assert rc_status == 1
    payload_status = json.loads(capsys.readouterr().out)
    assert payload_status["status"] == "offline"
    assert payload_status["running"] is False
    assert payload_status["connected"] is False
    assert payload_status["connected_from_log"] is True


def test_vscode_extensions_quickwins_handler_success(monkeypatch, tmp_path, capsys):
    quickwins = {"status": "ok", "actions": [{"id": "consolidate_ai_assistants"}]}
    monkeypatch.setattr(start_nusyq, "run", lambda *_a, **_k: (0, json.dumps(quickwins), ""))
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)

    rc = start_nusyq._handle_vscode_extensions_quickwins(
        ["vscode_extensions_quickwins", "--with-noise"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "vscode_extensions_quickwins"
    assert payload["functional"] is True
    assert payload["quickwins"]["status"] == "ok"


def test_vscode_extensions_quickwins_handler_forwards_flags(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run(cmd, cwd=None, timeout_s=0):
        captured["cmd"] = list(cmd)
        return 0, json.dumps({"status": "ok"}), ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)

    rc = start_nusyq._handle_vscode_extensions_quickwins(
        [
            "vscode_extensions_quickwins",
            "--with-noise",
            "--since-minutes",
            "120",
            "--channel",
            "Codex",
        ],
        paths,
        json_mode=False,
    )
    assert rc == 0
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert cmd[:3] == [sys.executable, "scripts/integrate_extensions.py", "--quickwins"]
    assert "--with-noise" in cmd
    assert "--since-minutes" in cmd
    assert "120" in cmd


def test_run_causal_analysis_detects_causal_relationships(tmp_path):
    payload = start_nusyq._run_causal_analysis(
        "retries happen because cache invalidation triggers rebuild after deploy",
        nusyq_hub=tmp_path,
        system_name="build_pipeline",
        variables=["growth_rate", "error_regulation"],
    )

    assert payload["status"] == "ok"
    assert "because" in payload["semantics"]["relationships"]
    assert "triggers" in payload["semantics"]["relationships"]
    assert payload["causality_chain"]
    assert payload["feedback_loop"]["system"] == "build_pipeline"


def test_handle_causal_analysis_json_mode(tmp_path, capsys):
    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)

    rc = start_nusyq._handle_causal_analysis(
        [
            "causal_analysis",
            "--system=build_pipeline",
            "--vars=growth_rate,error_regulation",
            "--text=retries happen because cache invalidation triggers rebuild after deploy",
        ],
        paths,
        json_mode=True,
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "causal_analysis"
    assert payload["system_name"] == "build_pipeline"
    assert payload["causality_chain"]
    assert payload["feedback_loop"]["system"] == "build_pipeline"
    assert (tmp_path / "state" / "reports" / "causal_analysis_latest.json").exists()


def test_handle_specialization_status_json_mode(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / "state" / "specialization"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "agent_profiles.json").write_text(
        json.dumps(
            {
                "ollama": {
                    "analysis_0.20": {
                        "agent_name": "ollama",
                        "task_type": "analysis",
                        "temperature": 0.2,
                        "success_count": 3,
                        "failure_count": 0,
                        "avg_quality": 0.9,
                        "avg_tokens": 1200,
                        "avg_latency_ms": 250.0,
                        "specialization_score": 96.0,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (state_dir / "specialization_history.jsonl").write_text(
        json.dumps(
            {
                "timestamp": "2026-03-15T00:00:00",
                "agent": "ollama",
                "task_type": "analysis",
                "temperature": 0.2,
                "success": True,
                "quality_score": 0.9,
                "tokens_used": 1200,
                "latency_ms": 250.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_specialization_status(
        ["specialization_status", "--agent=ollama"],
        paths,
        json_mode=True,
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "specialization_status"
    assert payload["agent"]["agent"] == "ollama"
    assert payload["history_events"] == 1
    assert (tmp_path / "state" / "reports" / "specialization_status_latest.json").exists()

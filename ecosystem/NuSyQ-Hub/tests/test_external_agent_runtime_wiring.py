"""Regression tests for Hermes/MetaClaw runtime detection and registry wiring."""

from __future__ import annotations

from pathlib import Path

import requests


def _create_runtime_tree(base: Path, name: str) -> Path:
    runtime = base / "state" / "runtime" / "external" / name
    runtime.mkdir(parents=True)
    return runtime


def test_setup_integrations_detects_hermes_constraints(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    hermes_path = _create_runtime_tree(tmp_path, "hermes-agent")
    (hermes_path / "pyproject.toml").write_text(
        "[project]\nname='hermes-agent'\n", encoding="utf-8"
    )
    (hermes_path / "package.json").write_text("{}", encoding="utf-8")

    which_map = {
        "node": "/usr/bin/node",
        "npm": "/usr/bin/npm",
        "python3.11": None,
        "python311": None,
    }
    monkeypatch.setattr(
        "scripts.setup_integrations.shutil.which",
        lambda command: which_map.get(command),
    )
    # _detect_python_311 returns sys.executable first (bypasses which mock);
    # patch the method directly to simulate no Python 3.11 available.
    monkeypatch.setattr(
        IntegrationSetup,
        "_detect_python_311",
        staticmethod(lambda: None),
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path

    status = setup.detect_hermes_agent()

    assert status["available"] is True
    assert status["python_3_11_available"] is False
    assert status["runnable"] is False
    assert status["node_available"] is True


def test_setup_integrations_detects_metaclaw_readiness(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")
    (metaclaw_path / ".env").write_text(
        "PRIVATE_KEY=abc123\nCLOWNCH_API_KEY=live-key\n",
        encoding="utf-8",
    )
    (metaclaw_path / "node_modules").mkdir()

    which_map = {"node": "/usr/bin/node", "npm": "/usr/bin/npm"}
    monkeypatch.setattr(
        "scripts.setup_integrations.shutil.which",
        lambda command: which_map.get(command),
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path

    status = setup.detect_metaclaw()

    assert status["available"] is True
    assert status["env_configured"] is True
    assert status["node_modules_ready"] is True
    assert status["runnable"] is True
    assert status["api_key_configured"] is True
    assert status["private_key_configured"] is True


def test_setup_integrations_marks_ollama_probe_blocked_without_false_offline(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    def _raise_probe_blocked(*_args, **_kwargs):
        raise requests.RequestException("operation not permitted")

    monkeypatch.setattr("scripts.setup_integrations.requests.get", _raise_probe_blocked)

    setup = IntegrationSetup()
    setup.repo_root = tmp_path
    setup.status["ollama"] = {"available": True}

    status = setup.detect_ollama()

    assert status["available"] is True
    assert status["probe_blocked"] is True
    assert status["check_mode"] == "probe_blocked_fallback"


def test_setup_integrations_marks_simulatedverse_probe_blocked(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    sim_path = tmp_path / "SimulatedVerse"
    sim_path.mkdir()
    (sim_path / "package.json").write_text("{}", encoding="utf-8")

    def _raise_probe_blocked(*_args, **_kwargs):
        raise requests.RequestException("operation not permitted")

    monkeypatch.setattr("scripts.setup_integrations.requests.get", _raise_probe_blocked)
    monkeypatch.setenv("SIMULATEDVERSE_PATH", str(sim_path))

    setup = IntegrationSetup()
    setup.repo_root = tmp_path

    status = setup.detect_simulatedverse()

    assert status["available"] is True
    assert status["probe_blocked"] is True
    assert status["server_running"] is False


def test_probe_metaclaw_status_classifies_timeout(monkeypatch):
    from scripts.setup_integrations import IntegrationSetup

    def _raise_timeout(*_args, **_kwargs):
        raise requests.Timeout("timed out")

    monkeypatch.setattr("scripts.setup_integrations.requests.get", _raise_timeout)
    status = IntegrationSetup._probe_metaclaw_status({"CLOWNCH_API_KEY": "live-key"})

    assert status["ok"] is False
    assert status["status"] == "timeout"


def test_probe_metaclaw_status_classifies_auth_error(monkeypatch):
    from scripts.setup_integrations import IntegrationSetup

    class _Response:
        status_code = 401
        text = '{"error":"unauthorized"}'

        @staticmethod
        def json():
            return {"error": "unauthorized"}

    monkeypatch.setattr("scripts.setup_integrations.requests.get", lambda *_args, **_kwargs: _Response())
    status = IntegrationSetup._probe_metaclaw_status({"CLOWNCH_API_KEY": "live-key"})

    assert status["ok"] is False
    assert status["status"] == "auth_error"
    assert status["http_status"] == 401


def test_probe_metaclaw_status_classifies_connectivity_error(monkeypatch):
    from scripts.setup_integrations import IntegrationSetup

    def _raise_connect_error(*_args, **_kwargs):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr("scripts.setup_integrations.requests.get", _raise_connect_error)
    status = IntegrationSetup._probe_metaclaw_status({"CLOWNCH_API_KEY": "live-key"})

    assert status["ok"] is False
    assert status["status"] == "connect_error"


def test_setup_integrations_detects_metaclaw_clawncher_alias(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")
    (metaclaw_path / ".env").write_text(
        "PRIVATE_KEY=abc123\nCLAWNCHER_API_KEY=live-key\n",
        encoding="utf-8",
    )
    (metaclaw_path / "node_modules").mkdir()

    which_map = {"node": "/usr/bin/node", "npm": "/usr/bin/npm"}
    monkeypatch.setattr(
        "scripts.setup_integrations.shutil.which",
        lambda command: which_map.get(command),
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path

    status = setup.detect_metaclaw()

    assert status["env_configured"] is True
    assert status["api_key_configured"] is True
    assert status["missing_required_env"] == []


def test_setup_integrations_updates_metaclaw_next_step_on_auth_error(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")
    (metaclaw_path / ".env").write_text(
        "PRIVATE_KEY=abc123\nCLOWNCH_API_KEY=live-key\n",
        encoding="utf-8",
    )
    (metaclaw_path / "node_modules").mkdir()

    which_map = {"node": "/usr/bin/node", "npm": "/usr/bin/npm"}
    monkeypatch.setattr(
        "scripts.setup_integrations.shutil.which",
        lambda command: which_map.get(command),
    )
    monkeypatch.setattr(
        IntegrationSetup,
        "_probe_metaclaw_status",
        staticmethod(
            lambda _env_values, timeout_s=12: {
                "ok": False,
                "status": "auth_error",
                "http_status": 401,
                "error": '{"error":"Invalid or missing API key"}',
            }
        ),
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path

    status = setup.detect_metaclaw()

    assert status["externally_verified"] is False
    assert status["status_check"]["status"] == "auth_error"
    assert status["registration_recommended"] is True
    assert status["next_step"] == "npm run register"


def test_setup_integrations_reports_metaclaw_missing_required_env(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")
    (metaclaw_path / ".env").write_text(
        "PRIVATE_KEY=your_private_key_here\n",
        encoding="utf-8",
    )
    (metaclaw_path / "node_modules").mkdir()

    which_map = {"node": "/usr/bin/node", "npm": "/usr/bin/npm"}
    monkeypatch.setattr(
        "scripts.setup_integrations.shutil.which",
        lambda command: which_map.get(command),
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path

    status = setup.detect_metaclaw()

    assert status["env_configured"] is False
    assert status["private_key_configured"] is False
    assert "PRIVATE_KEY" in status["missing_required_env"]
    assert "CLOWNCH_API_KEY or CLAWNCHER_API_KEY" in status["missing_required_env"]


def test_setup_integrations_syncs_metaclaw_from_workspace_env(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")
    (metaclaw_path / "node_modules").mkdir()
    (tmp_path / ".env.workspace").write_text(
        "BASE_PRIVATE_KEY=abc123\nCLAWNCHER_API_KEY=live-key\nAGENT_NAME=NuSyQMetaClaw\n",
        encoding="utf-8",
    )

    which_map = {"node": "/usr/bin/node", "npm": "/usr/bin/npm"}
    monkeypatch.setattr(
        "scripts.setup_integrations.shutil.which",
        lambda command: which_map.get(command),
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path

    status = setup.detect_metaclaw()
    synced_env = (metaclaw_path / ".env").read_text(encoding="utf-8")

    assert status["env_configured"] is True
    assert status["env_sync_applied"] is True
    assert "workspace:env" in status["resolved_secret_sources"]
    assert "PRIVATE_KEY=abc123" in synced_env
    assert "CLOWNCH_API_KEY=live-key" in synced_env
    assert "CLAWNCHER_API_KEY=live-key" in synced_env
    assert "AGENT_NAME=NuSyQMetaClaw" in synced_env


def test_setup_integrations_marks_metaclaw_registration_ready(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")
    (metaclaw_path / "node_modules").mkdir()
    (tmp_path / ".env").write_text("PRIVATE_KEY=abc123\n", encoding="utf-8")

    which_map = {"node": "/usr/bin/node", "npm": "/usr/bin/npm"}
    monkeypatch.setattr(
        "scripts.setup_integrations.shutil.which",
        lambda command: which_map.get(command),
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path

    status = setup.detect_metaclaw()

    assert status["registration_ready"] is True
    assert status["runnable"] is False
    assert status["next_step"] == "npm run register"


def test_setup_integrations_detects_metaclaw_from_secrets_json(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")
    (metaclaw_path / "node_modules").mkdir()
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "secrets.json").write_text(
        '{"metaclaw": {"private_key": "abc123", "clawnch_api_key": "live-key"}}',
        encoding="utf-8",
    )

    which_map = {"node": "/usr/bin/node", "npm": "/usr/bin/npm"}
    monkeypatch.setattr(
        "scripts.setup_integrations.shutil.which",
        lambda command: which_map.get(command),
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path
    setup.config_path = config_dir / "secrets.json"

    status = setup.detect_metaclaw()

    assert status["env_configured"] is True
    assert "config:secrets.json:metaclaw" in status["resolved_secret_sources"]
    assert status["resolved_secret_aliases"]["PRIVATE_KEY"] == "private_key"


def test_setup_integrations_recovers_metaclaw_from_backup_file(monkeypatch, tmp_path):
    from scripts.setup_integrations import IntegrationSetup

    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")
    (metaclaw_path / "node_modules").mkdir()
    (metaclaw_path / ".env.backup").write_text(
        "PRIVATE_KEY: abc123\nCLAWNCHER_API_KEY: live-key\n",
        encoding="utf-8",
    )

    which_map = {"node": "/usr/bin/node", "npm": "/usr/bin/npm"}
    monkeypatch.setattr(
        "scripts.setup_integrations.shutil.which",
        lambda command: which_map.get(command),
    )

    setup = IntegrationSetup()
    setup.repo_root = tmp_path

    status = setup.detect_metaclaw()

    assert status["env_configured"] is True
    assert "metaclaw:.env.backup" in status["resolved_secret_sources"]
    assert status["env_sync_applied"] is True


def test_agent_registry_marks_external_agents_offline_until_runnable(monkeypatch, tmp_path):
    import src.orchestration.agent_registry as registry_module

    hermes_path = _create_runtime_tree(tmp_path, "hermes-agent")
    (hermes_path / "pyproject.toml").write_text(
        "[project]\nname='hermes-agent'\n", encoding="utf-8"
    )
    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(registry_module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_ollama_available", lambda self: False
    )
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_chatdev_available", lambda self: False
    )
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_continue_available", lambda self: False
    )
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_jupyter_available", lambda self: False
    )
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_docker_available", lambda self: False
    )
    monkeypatch.setattr("src.config.feature_flag_manager.is_feature_enabled", lambda _name: False)
    monkeypatch.setattr(
        registry_module.shutil,
        "which",
        lambda command: {
            "node": "/usr/bin/node",
            "npm": "/usr/bin/npm",
            "python3.11": None,
            "python311": None,
        }.get(command),
    )

    registry = registry_module.AgentRegistry(registry_path=tmp_path / "registry.json")

    assert registry.get_agent("hermes_agent") is not None
    assert registry.get_agent("hermes_agent").status == "offline"
    assert registry.get_agent("metaclaw") is not None
    assert registry.get_agent("metaclaw").status == "offline"


def test_agent_registry_marks_metaclaw_idle_when_locally_runnable(monkeypatch, tmp_path):
    import src.orchestration.agent_registry as registry_module

    metaclaw_path = _create_runtime_tree(tmp_path, "metaclaw-agent")
    (metaclaw_path / "package.json").write_text("{}", encoding="utf-8")
    (metaclaw_path / ".env").write_text(
        "PRIVATE_KEY=abc123\nCLOWNCH_API_KEY=live-key\n",
        encoding="utf-8",
    )
    (metaclaw_path / "node_modules").mkdir()

    monkeypatch.setattr(registry_module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_ollama_available", lambda self: False
    )
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_chatdev_available", lambda self: False
    )
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_continue_available", lambda self: False
    )
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_jupyter_available", lambda self: False
    )
    monkeypatch.setattr(
        registry_module.AgentRegistry, "_check_docker_available", lambda self: False
    )
    monkeypatch.setattr("src.config.feature_flag_manager.is_feature_enabled", lambda _name: False)
    monkeypatch.setattr(
        registry_module.shutil,
        "which",
        lambda command: {
            "node": "/usr/bin/node",
            "npm": "/usr/bin/npm",
            "python3.11": None,
            "python311": None,
        }.get(command),
    )

    registry = registry_module.AgentRegistry(registry_path=tmp_path / "registry.json")

    assert registry.get_agent("metaclaw") is not None
    assert registry.get_agent("metaclaw").status == "idle"

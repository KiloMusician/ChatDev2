"""Tests for language-aware project factory generation behavior."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest
from src.factories.generators.chatdev_generator import ChatDevGenerationResult, ChatDevGenerator
from src.factories.project_factory import ProjectFactory


class _FakeOllamaResponse:
    status_code = 200

    def __init__(self, body: str = "// generated file\n", eval_count: int = 64):
        self._body = body
        self._eval_count = eval_count

    def json(self):
        return {"response": self._body, "eval_count": self._eval_count}


def _factory_with_ollama(tmp_path: Path) -> ProjectFactory:
    """Create factory configured to force deterministic Ollama path in tests."""
    factory = ProjectFactory()
    factory.output_root = tmp_path / "generated"
    factory.output_root.mkdir(parents=True, exist_ok=True)
    factory.orchestrator.ollama_available = True
    factory.orchestrator.chatdev_path = None
    return factory


def test_javascript_template_creates_package_manifest(monkeypatch, tmp_path: Path) -> None:
    """JavaScript templates should emit package.json and Node run instructions."""
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: _FakeOllamaResponse())
    monkeypatch.setattr("time.sleep", lambda *args, **kwargs: None)

    factory = _factory_with_ollama(tmp_path)

    result = factory.create(
        name="LangFlexJS",
        template="default_js_cli",
        description="Language flexibility smoke test",
        ai_provider="ollama",
        auto_register=False,
    )

    package_json = result.output_path / "package.json"
    assert package_json.exists()
    package_text = package_json.read_text(encoding="utf-8")
    assert '"name": "langflexjs"' in package_text
    assert '"start": "node src/main.js"' in package_text
    assert '"commander": "latest"' in package_text


def test_ollama_failure_falls_back_to_placeholder(monkeypatch, tmp_path: Path) -> None:
    """If Ollama request fails, file placeholders should still be written."""

    def _raise(*_args, **_kwargs):
        raise RuntimeError("blocked network")

    monkeypatch.setattr("requests.post", _raise)
    monkeypatch.setattr("time.sleep", lambda *args, **kwargs: None)

    factory = _factory_with_ollama(tmp_path)

    template = {
        "name": "FallbackPy",
        "type": "cli",
        "language": "python",
        "description": "placeholder fallback",
        "dependencies": [],
        "file_structure": {"main.py": "Entry point"},
        "complexity": 3,
        "requires_multifile": False,
    }

    result = factory.create(
        name="LangFlexFallback",
        custom_template=template,
        ai_provider="ollama",
        auto_register=False,
    )

    main_file = result.output_path / "main.py"
    assert main_file.exists()
    assert "placeholder" in main_file.read_text(encoding="utf-8").lower()
    diagnostics = result.metadata.get("factory_generation", {})
    assert diagnostics.get("provider_chain") == ["ollama"]
    assert diagnostics.get("ollama_placeholder_files", 0) >= 1
    assert (result.output_path / "factory" / "generation_diagnostics.json").exists()


@pytest.mark.parametrize(
    ("runtime_profile", "expected_hook_path", "expected_profile_path"),
    [
        (
            "native_terminal",
            "packaging/native/hooks/steam_overlay_hook.py",
            "packaging/native/launch_windows.bat",
        ),
        (
            "electron_local",
            "packaging/electron/hooks/steam_overlay_hook.js",
            "packaging/electron/steam_adapter.json",
        ),
        (
            "electron_web_wrapper",
            "packaging/electron/hooks/web_wrapper_launcher.js",
            "packaging/electron/web_wrapper.json",
        ),
        (
            "godot_export",
            "packaging/godot/hooks/steam_overlay_hook.gd",
            "packaging/godot/export_presets.cfg",
        ),
    ],
)
def test_runtime_profiles_emit_profile_specific_packaging(
    monkeypatch,
    tmp_path: Path,
    runtime_profile: str,
    expected_hook_path: str,
    expected_profile_path: str,
) -> None:
    """Each runtime profile should emit its profile-specific packaging adapter."""
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: _FakeOllamaResponse())
    monkeypatch.setattr("time.sleep", lambda *args, **kwargs: None)

    factory = _factory_with_ollama(tmp_path)

    template = {
        "name": f"Runtime {runtime_profile}",
        "type": "game",
        "language": "python",
        "description": "runtime packaging test",
        "dependencies": [],
        "file_structure": {"main.py": "Entry point"},
        "complexity": 2,
        "requires_multifile": False,
        "runtime_profile": runtime_profile,
        "feature_flags": {
            "data_pipeline": False,
            "event_router": False,
            "save_migration": False,
            "modding_api": False,
        },
    }

    result = factory.create(
        name=f"Profile_{runtime_profile}",
        custom_template=template,
        ai_provider="ollama",
        auto_register=False,
    )

    assert (result.output_path / expected_hook_path).exists()
    assert (result.output_path / expected_profile_path).exists()
    assert (result.output_path / "packaging/runtime_profile.json").exists()
    assert (result.output_path / "packaging/steam/layout.json").exists()
    preflight_path = result.output_path / "packaging/health/preflight.json"
    assert preflight_path.exists()
    assert '"healthy": true' in preflight_path.read_text(encoding="utf-8").lower()
    hook_path = result.output_path / "packaging/health/hook_validation.json"
    assert hook_path.exists()
    assert '"healthy"' in hook_path.read_text(encoding="utf-8").lower()


def test_game_feature_flags_emit_extended_scaffolds(monkeypatch, tmp_path: Path) -> None:
    """Game templates with feature flags should emit data/event/save/modding scaffolds."""
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: _FakeOllamaResponse())
    monkeypatch.setattr("time.sleep", lambda *args, **kwargs: None)

    factory = _factory_with_ollama(tmp_path)

    template = {
        "name": "FeatureFlagsGame",
        "type": "game",
        "language": "python",
        "description": "feature scaffolds test",
        "dependencies": [],
        "file_structure": {"main.py": "Entry point"},
        "complexity": 2,
        "requires_multifile": False,
        "runtime_profile": "native_terminal",
        "feature_flags": {
            "data_pipeline": True,
            "event_router": True,
            "save_migration": True,
            "modding_api": True,
        },
    }

    result = factory.create(
        name="FeatureFlagsGame",
        custom_template=template,
        ai_provider="ollama",
        auto_register=False,
    )

    required = [
        "data/pipeline_manifest.yaml",
        "data/events/combat_proc_chains.yaml",
        "config/save_schema.json",
        "config/user_config.schema.json",
        "migrations/save/0001_initial.yaml",
        "mods/hooks.json",
        "mods/manifest.schema.json",
        "game/data_pipeline.py",
        "game/event_router.py",
        "game/save_system.py",
        "game/modding_api.py",
        "mods/examples/sample_mod.py",
    ]
    for relpath in required:
        assert (result.output_path / relpath).exists(), relpath


def test_python_game_entrypoint_bootstraps_runtime_scaffolds(monkeypatch, tmp_path: Path) -> None:
    """Python game entrypoint should actively bootstrap runtime scaffold systems."""
    monkeypatch.setattr(
        "requests.post",
        lambda *args, **kwargs: _FakeOllamaResponse(
            body="def run():\n    return 0\n\nif __name__ == '__main__':\n    run()\n",
        ),
    )
    monkeypatch.setattr("time.sleep", lambda *args, **kwargs: None)

    factory = _factory_with_ollama(tmp_path)

    template = {
        "name": "RuntimeWiredGame",
        "type": "game",
        "language": "python",
        "description": "runtime wiring test",
        "dependencies": [],
        "file_structure": {"main.py": "Entry point"},
        "complexity": 2,
        "requires_multifile": False,
        "runtime_profile": "native_terminal",
        "feature_flags": {
            "data_pipeline": True,
            "event_router": True,
            "save_migration": True,
            "modding_api": True,
        },
    }

    result = factory.create(
        name="RuntimeWiredGame",
        custom_template=template,
        ai_provider="ollama",
        auto_register=False,
    )

    main_path = result.output_path / "main.py"
    runtime_module = result.output_path / "game/runtime_services.py"
    main_text = main_path.read_text(encoding="utf-8")

    assert runtime_module.exists()
    assert "# NuSyQ runtime bootstrap (auto-generated)" in main_text
    assert "NUSYQ_RUNTIME_SERVICES" in main_text

    run_result = subprocess.run(
        ["python", "main.py"],
        cwd=result.output_path,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert run_result.returncode == 0, run_result.stderr


def test_non_game_template_does_not_emit_game_scaffolds_by_default(
    monkeypatch, tmp_path: Path
) -> None:
    """CLI templates should not emit game-only scaffold files unless explicitly enabled."""
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: _FakeOllamaResponse())
    monkeypatch.setattr("time.sleep", lambda *args, **kwargs: None)

    factory = _factory_with_ollama(tmp_path)

    template = {
        "name": "CliNoGameFeatures",
        "type": "cli",
        "language": "python",
        "description": "cli should stay lean",
        "dependencies": [],
        "file_structure": {"main.py": "Entry point"},
        "complexity": 2,
        "requires_multifile": False,
    }

    result = factory.create(
        name="CliNoGameFeatures",
        custom_template=template,
        ai_provider="ollama",
        auto_register=False,
    )

    assert not (result.output_path / "data/pipeline_manifest.yaml").exists()
    assert not (result.output_path / "mods/hooks.json").exists()
    assert not (result.output_path / "migrations/save/0001_initial.yaml").exists()


def test_chatdev_generator_uses_run_py_when_run_ollama_missing(tmp_path: Path) -> None:
    """ChatDev generator should gracefully use run.py when run_ollama.py is absent."""
    chatdev_dir = tmp_path / "ChatDev"
    chatdev_dir.mkdir(parents=True, exist_ok=True)
    (chatdev_dir / "run.py").write_text("print('runner')\n", encoding="utf-8")

    generator = ChatDevGenerator(chatdev_dir)
    assert generator.runner.name == "run.py"


def test_chatdev_generation_failure_falls_back_to_ollama(monkeypatch, tmp_path: Path) -> None:
    """If ChatDev returns an unsuccessful result, factory should fallback to Ollama output."""
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: _FakeOllamaResponse())
    monkeypatch.setattr("time.sleep", lambda *args, **kwargs: None)

    chatdev_dir = tmp_path / "ChatDev"
    chatdev_dir.mkdir(parents=True, exist_ok=True)
    (chatdev_dir / "run.py").write_text("print('runner')\n", encoding="utf-8")
    warehouse_dir = chatdev_dir / "WareHouse"
    warehouse_dir.mkdir(parents=True, exist_ok=True)

    def _fake_generate(self, *_args, **_kwargs):
        return ChatDevGenerationResult(
            project_name="FallbackGame",
            warehouse_path=warehouse_dir,
            model_used="qwen2.5-coder:14b",
            token_cost=0.0,
            created_at="2026-02-07T00:00:00",
            task_description="force fallback",
            success=False,
            error_message="simulated failure",
        )

    monkeypatch.setattr(
        "src.factories.generators.chatdev_generator.ChatDevGenerator.generate",
        _fake_generate,
    )

    factory = ProjectFactory()
    factory.output_root = tmp_path / "generated"
    factory.output_root.mkdir(parents=True, exist_ok=True)
    factory.orchestrator.chatdev_path = chatdev_dir
    factory.orchestrator.ollama_available = True

    template = {
        "name": "FallbackGame",
        "type": "game",
        "language": "python",
        "description": "chatdev fallback test",
        "dependencies": [],
        "file_structure": {"main.py": "Entry point"},
        "complexity": 8,
        "requires_multifile": True,
        "runtime_profile": "native_terminal",
        "feature_flags": {
            "data_pipeline": False,
            "event_router": False,
            "save_migration": False,
            "modding_api": False,
        },
    }

    result = factory.create(
        name="FallbackGame",
        custom_template=template,
        ai_provider="chatdev",
        auto_register=False,
    )

    assert result.ai_provider == "ollama"
    assert result.chatdev_warehouse_path is None
    assert (result.output_path / "main.py").exists()
    diagnostics = result.metadata.get("factory_generation", {})
    assert diagnostics.get("provider_chain") == ["chatdev", "ollama"]
    assert "simulated failure" in diagnostics.get("fallback_reason", "")


def test_factory_health_check_runs_smoke_probes() -> None:
    """Factory health command surface should report all smoke probes passing."""
    factory = ProjectFactory()
    report = factory.run_health_check(include_packaging=True)

    assert isinstance(report, dict)
    assert "healthy" in report
    assert "checks" in report
    names = [check.get("name") for check in report.get("checks", [])]
    assert "provider_fallback" in names
    assert "runtime_bootstrap" in names
    assert "packaging_adapters" in names
    assert report["healthy"] is True
    packaging_check = next(
        (check for check in report.get("checks", []) if check.get("name") == "packaging_adapters"),
        {},
    )
    assert "hook_validation" in packaging_check.get("details", {})


def test_inspect_reference_games_detects_runtime_profiles(tmp_path: Path) -> None:
    """Reference game inspection should infer runtime profiles from package signals."""
    electron_path = tmp_path / "Bitburner"
    (electron_path / "resources" / "app").mkdir(parents=True, exist_ok=True)
    (electron_path / "resources" / "app" / "package.json").write_text("{}", encoding="utf-8")

    godot_path = tmp_path / "Path of Achra"
    godot_path.mkdir(parents=True, exist_ok=True)
    (godot_path / "PathofAchra.pck").write_text("bundle", encoding="utf-8")

    native_path = tmp_path / "Cogmind"
    native_path.mkdir(parents=True, exist_ok=True)
    (native_path / "COGMIND.exe").write_text("binary", encoding="utf-8")
    (native_path / "manual.txt").write_text("ops", encoding="utf-8")

    factory = ProjectFactory()
    report = factory.inspect_reference_games(
        paths=[str(electron_path), str(godot_path), str(native_path)]
    )

    by_path = {item["path"]: item for item in report["reports"]}
    assert by_path[str(electron_path)]["runtime_profile"] == "electron_local"
    assert by_path[str(godot_path)]["runtime_profile"] == "godot_export"
    assert by_path[str(native_path)]["runtime_profile"] == "native_terminal"


def test_factory_doctor_detects_degraded_generation_quality(monkeypatch, tmp_path: Path) -> None:
    """Doctor should fail fast when recent diagnostics show repeated fallback."""
    generated = tmp_path / "generated"
    run_a = generated / "RunA" / "factory"
    run_b = generated / "RunB" / "factory"
    run_a.mkdir(parents=True, exist_ok=True)
    run_b.mkdir(parents=True, exist_ok=True)

    run_payload = {
        "provider_chain": ["chatdev", "ollama"],
        "ollama_files_targeted": 5,
        "ollama_placeholder_files": 3,
    }
    (run_a / "generation_diagnostics.json").write_text(
        json.dumps(run_payload),
        encoding="utf-8",
    )
    (run_b / "generation_diagnostics.json").write_text(
        json.dumps(run_payload),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        ProjectFactory,
        "run_health_check",
        lambda self, include_packaging=True: {"healthy": True, "checks": []},
    )

    factory = ProjectFactory()
    factory.output_root = generated
    report = factory.run_doctor(
        strict_hooks=False,
        include_examples=False,
        include_health=True,
        recent_limit=10,
    )
    assert report["healthy"] is False
    issue_codes = {item.get("code") for item in report.get("issues", [])}
    assert "repeated_fallback" in issue_codes


def test_factory_doctor_detects_missing_runtime_bootstrap(tmp_path: Path, monkeypatch) -> None:
    """Doctor should report missing runtime bootstrap wiring on recent Python outputs."""
    generated = tmp_path / "generated" / "RuntimeGap"
    (generated / "packaging" / "health").mkdir(parents=True, exist_ok=True)
    (generated / "factory").mkdir(parents=True, exist_ok=True)

    (generated / "main.py").write_text("print('hello')\n", encoding="utf-8")
    runtime_profile = {
        "runtime_profile": "native_terminal",
        "entry_point": "main.py",
        "language": "python",
        "project_type": "game",
    }
    (generated / "packaging" / "runtime_profile.json").write_text(
        f"{json.dumps(runtime_profile, indent=2)}\n",
        encoding="utf-8",
    )
    (generated / "packaging" / "health" / "preflight.json").write_text(
        f"{json.dumps({'healthy': True}, indent=2)}\n",
        encoding="utf-8",
    )
    (generated / "factory" / "generation_diagnostics.json").write_text(
        f"{json.dumps({'feature_flags': ['data_pipeline']}, indent=2)}\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        ProjectFactory,
        "run_health_check",
        lambda self, include_packaging=True: {"healthy": True, "checks": []},
    )

    factory = ProjectFactory()
    factory.output_root = tmp_path / "generated"
    report = factory.run_doctor(
        strict_hooks=False,
        include_examples=False,
        include_health=True,
        recent_limit=10,
    )
    issue_codes = {item.get("code") for item in report.get("issues", [])}
    assert "missing_runtime_bootstrap" in issue_codes


def test_factory_doctor_fix_regenerates_packaging_hooks(monkeypatch, tmp_path: Path) -> None:
    """Doctor fix should regenerate missing packaging hooks for recent projects."""
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: _FakeOllamaResponse())
    monkeypatch.setattr("time.sleep", lambda *args, **kwargs: None)

    template_dir = tmp_path / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    factory = ProjectFactory(template_dir=template_dir)
    factory.output_root = tmp_path / "generated"
    factory.output_root.mkdir(parents=True, exist_ok=True)
    factory.orchestrator.ollama_available = True
    factory.orchestrator.chatdev_path = None

    template = {
        "name": "FixableGame",
        "type": "game",
        "language": "python",
        "description": "doctor fix packaging regeneration test",
        "dependencies": [],
        "file_structure": {"main.py": "Entry point"},
        "complexity": 2,
        "requires_multifile": False,
        "runtime_profile": "native_terminal",
        "feature_flags": {
            "data_pipeline": False,
            "event_router": False,
            "save_migration": False,
            "modding_api": False,
        },
    }
    result = factory.create(
        name="FixableGame",
        custom_template=template,
        ai_provider="ollama",
        auto_register=False,
    )
    hook_path = result.output_path / "packaging/native/hooks/steam_overlay_hook.py"
    hook_path.unlink()
    assert not hook_path.exists()

    report = factory.run_doctor_fix(
        strict_hooks=False,
        include_examples=False,
        include_health=False,
        recent_limit=10,
    )
    assert hook_path.exists()
    assert report["post_fix"]["healthy"] is True
    actions = {item.get("action"): item for item in report.get("actions", [])}
    assert actions["packaging_hook_regeneration"]["applied"] is True
    assert actions["packaging_hook_regeneration"]["updated_count"] >= 1


def test_factory_doctor_fix_repairs_runtime_bootstrap(tmp_path: Path, monkeypatch) -> None:
    """Doctor fix should repair Python runtime bootstrap marker/module when missing."""
    generated = tmp_path / "generated" / "BootstrapFix"
    (generated / "packaging" / "health").mkdir(parents=True, exist_ok=True)
    (generated / "factory").mkdir(parents=True, exist_ok=True)
    (generated / "main.py").write_text("print('hello')\n", encoding="utf-8")

    runtime_profile = {
        "runtime_profile": "native_terminal",
        "entry_point": "main.py",
        "language": "python",
        "project_type": "game",
    }
    (generated / "packaging" / "runtime_profile.json").write_text(
        f"{json.dumps(runtime_profile, indent=2)}\n",
        encoding="utf-8",
    )
    (generated / "packaging" / "health" / "preflight.json").write_text(
        f"{json.dumps({'healthy': True}, indent=2)}\n",
        encoding="utf-8",
    )
    (generated / "factory" / "generation_diagnostics.json").write_text(
        f"{json.dumps({'feature_flags': ['data_pipeline']}, indent=2)}\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        ProjectFactory,
        "run_health_check",
        lambda self, include_packaging=True: {"healthy": True, "checks": []},
    )

    factory = ProjectFactory()
    factory.output_root = tmp_path / "generated"
    report = factory.run_doctor_fix(
        strict_hooks=False,
        include_examples=False,
        include_health=True,
        recent_limit=10,
    )

    main_text = (generated / "main.py").read_text(encoding="utf-8")
    assert "# NuSyQ runtime bootstrap (auto-generated)" in main_text
    assert (generated / "game" / "runtime_services.py").exists()
    actions = {item.get("action"): item for item in report.get("actions", [])}
    assert actions["runtime_bootstrap_repair"]["applied"] is True


def test_factory_doctor_fix_applies_medium_profile_hardening(tmp_path: Path, monkeypatch) -> None:
    """Doctor fix should execute medium autopilot hardening actions when signaled."""
    factory = ProjectFactory(template_dir=tmp_path / "templates")
    factory.output_root = tmp_path / "generated"
    factory.output_root.mkdir(parents=True, exist_ok=True)

    def _seed_project(name: str, runtime_profile: str) -> Path:
        root = factory.output_root / name
        packaging = root / "packaging"
        packaging.mkdir(parents=True, exist_ok=True)
        runtime_payload = {
            "runtime_profile": runtime_profile,
            "entry_point": "main.py",
            "language": "python",
            "project_type": "game",
        }
        (packaging / "runtime_profile.json").write_text(
            f"{json.dumps(runtime_payload, indent=2)}\n",
            encoding="utf-8",
        )
        return root

    electron_root = _seed_project("ElectronHardening", "electron_local")
    native_root = _seed_project("NativeHardening", "native_terminal")
    godot_root = _seed_project("GodotHardening", "godot_export")

    doctor_payload = {
        "healthy": False,
        "status": "degraded",
        "issues": [],
        "health": {"healthy": True, "checks": []},
        "generation_quality": {"degraded": False, "issues": []},
        "examples": {"profiles": {"electron_local": 1, "native_terminal": 1, "godot_export": 1}},
    }
    monkeypatch.setattr(factory, "run_doctor", lambda **kwargs: doctor_payload)

    report = factory.run_doctor_fix(
        strict_hooks=False,
        include_examples=True,
        include_health=True,
        recent_limit=10,
    )
    actions = {item.get("action"): item for item in report.get("actions", [])}
    assert actions["electron_release_hardening"]["applied"] is True
    assert actions["native_ops_hardening"]["applied"] is True
    assert actions["godot_export_hardening"]["applied"] is True

    assert (electron_root / "packaging/electron/release_channels.json").exists()
    assert (electron_root / "packaging/electron/asar_manifest.json").exists()
    assert (native_root / "packaging/native/ops/save_policy.json").exists()
    assert (native_root / "packaging/native/ops/logging_policy.json").exists()
    assert (native_root / "packaging/native/OPERATIONS.md").exists()
    assert (godot_root / "packaging/godot/export_contract.json").exists()
    assert (godot_root / "packaging/godot/plugin_hooks.json").exists()


def test_factory_autopilot_builds_targeted_patch_plan(monkeypatch, tmp_path: Path) -> None:
    """Autopilot should emit a targeted plan from doctor+reference signals."""
    factory = ProjectFactory(template_dir=tmp_path / "templates")
    monkeypatch.setattr(
        factory,
        "run_doctor",
        lambda **kwargs: {
            "healthy": False,
            "issues": [
                {"code": "repeated_fallback", "message": "fallback churn"},
                {"code": "hook_runtime_skipped", "message": "node unavailable"},
                {"code": "workspace_extension_contention", "message": "foreign roots detected"},
            ],
        },
    )
    monkeypatch.setattr(
        factory,
        "inspect_reference_games",
        lambda paths=None: {
            "profiles": {"electron_local": 1, "native_terminal": 1, "godot_export": 1}
        },
    )

    report = factory.run_autopilot(
        fix=False,
        strict_hooks=False,
        include_examples=True,
        recent_limit=10,
    )
    actions = [item.get("action") for item in report.get("patch_plan", [])]
    assert "provider_policy_hardening" in actions
    assert "packaging_hook_regeneration" in actions
    assert "electron_release_hardening" in actions
    assert "native_ops_hardening" in actions
    assert "godot_export_hardening" in actions
    assert "workspace_window_isolation" in actions


def test_factory_doctor_reports_workspace_contention_when_enabled(
    monkeypatch, tmp_path: Path
) -> None:
    """Doctor should surface workspace extension-host contention when explicitly enabled."""
    factory = ProjectFactory(template_dir=tmp_path / "templates")
    monkeypatch.setattr(
        factory,
        "run_health_check",
        lambda include_packaging=True: {"healthy": True, "checks": []},
    )
    monkeypatch.setattr(
        factory,
        "_probe_workspace_contention",
        lambda: {
            "name": "workspace_contention",
            "passed": False,
            "details": {
                "status": "contention_detected",
                "foreign_workspaces": [
                    "c:\\Program Files (x86)\\Steam\\steamapps\\common\\Cogmind"
                ],
                "signals": ["ruff_stream_destroyed"],
            },
        },
    )

    report = factory.run_doctor(
        strict_hooks=False,
        include_examples=False,
        include_health=True,
        include_workspace=True,
        recent_limit=5,
    )
    issue_codes = {item.get("code") for item in report.get("issues", [])}
    assert "workspace_extension_contention" in issue_codes
    assert report.get("workspace_integrity", {}).get("passed") is False


def test_factory_autopilot_forwards_workspace_integrity_flag(monkeypatch, tmp_path: Path) -> None:
    """Autopilot should forward include_workspace to doctor path."""
    factory = ProjectFactory(template_dir=tmp_path / "templates")
    captured: dict[str, Any] = {}

    def _fake_doctor(**kwargs):
        captured.update(kwargs)
        return {"healthy": True, "issues": []}

    monkeypatch.setattr(factory, "run_doctor", _fake_doctor)
    monkeypatch.setattr(
        factory,
        "inspect_reference_games",
        lambda paths=None: {"profiles": {}, "reports": [], "recommendations": []},
    )

    factory.run_autopilot(
        fix=False,
        strict_hooks=True,
        include_examples=False,
        include_workspace=True,
        recent_limit=3,
    )
    assert captured.get("include_workspace") is True


def test_workspace_contention_probe_ignores_stale_logs(tmp_path: Path, monkeypatch) -> None:
    """Workspace contention probe should not fail CI on stale historical logs."""
    logs_root = tmp_path / "Code" / "logs"
    exthost = logs_root / "20260201T000000" / "window1" / "exthost"
    output = exthost / "output_logging_20260201T000000"
    output.mkdir(parents=True, exist_ok=True)
    isort_dir = exthost / "ms-python.isort"
    isort_dir.mkdir(parents=True, exist_ok=True)

    ruff_log = output / "37-Ruff Language Server.log"
    semgrep_log = output / "36-Semgrep (Server).log"
    isort_log = isort_dir / "isort.log"
    ruff_log.write_text(
        "Registering workspace: c:\\Program Files (x86)\\Steam\\steamapps\\common\\Cogmind\n"
        "Cannot call write after a stream was destroyed\n",
        encoding="utf-8",
    )
    semgrep_log.write_text(
        "TypeError: Cannot read properties of undefined (reading 'positionEncoding')\n",
        encoding="utf-8",
    )
    isort_log.write_text(
        "[Error - 9:44:12 PM] Client isort: connection to server is erroring.\n",
        encoding="utf-8",
    )

    stale_mtime = time.time() - (3 * 60 * 60)
    for path in (ruff_log, semgrep_log, isort_log):
        os.utime(path, (stale_mtime, stale_mtime))

    factory = ProjectFactory(template_dir=tmp_path / "templates")
    monkeypatch.setattr(factory, "_candidate_vscode_logs_roots", lambda: [logs_root])
    report = factory._probe_workspace_contention()

    assert report["passed"] is True
    assert report["details"]["status"] in {"stale_logs", "stale_logs_after_settings_change"}
    assert report["details"]["stale"] is True


def test_workspace_contention_probe_ignores_logs_older_than_settings(
    tmp_path: Path, monkeypatch
) -> None:
    """Probe should treat contention logs as stale after settings were updated."""
    logs_root = tmp_path / "Code" / "logs"
    exthost = logs_root / "20260201T000000" / "window1" / "exthost"
    output = exthost / "output_logging_20260201T000000"
    output.mkdir(parents=True, exist_ok=True)
    ruff_log = output / "37-Ruff Language Server.log"
    ruff_log.write_text(
        "Registering workspace: c:\\Program Files (x86)\\Steam\\steamapps\\common\\Bitburner\n",
        encoding="utf-8",
    )

    settings_path = tmp_path / "Code" / "User" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("{}", encoding="utf-8")

    old_mtime = time.time() - (10 * 60)
    new_mtime = time.time()
    os.utime(ruff_log, (old_mtime, old_mtime))
    os.utime(settings_path, (new_mtime, new_mtime))

    factory = ProjectFactory(template_dir=tmp_path / "templates")
    monkeypatch.setattr(factory, "_candidate_vscode_logs_roots", lambda: [logs_root])
    monkeypatch.setattr(factory, "_candidate_vscode_settings_paths", lambda: [settings_path])

    report = factory._probe_workspace_contention()
    assert report["passed"] is True
    assert report["details"]["status"] == "stale_logs_after_settings_change"
    assert report["details"]["stale"] is True

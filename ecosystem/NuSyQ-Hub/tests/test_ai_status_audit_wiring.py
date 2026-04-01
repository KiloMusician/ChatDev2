"""Tests for ai_status audit-intelligence wiring."""

from __future__ import annotations

import json
import asyncio
import sys
import types

import scripts.start_nusyq as start_nusyq


def test_ai_status_json_includes_audit_intelligence(monkeypatch, tmp_path, capsys) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "SYSTEM_AUDIT_2026-02-25.md").write_text("# audit\n", encoding="utf-8")

    monkeypatch.setattr(
        start_nusyq,
        "_collect_ai_health",
        lambda _paths: {"services": {"ollama": {"healthy": True}}, "quantum": {"healthy": True}},
    )

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_ai_status(paths, json_mode=True)
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "ai_status"
    assert "audit_intelligence" in payload
    assert "capability_intelligence" in payload
    assert payload["audit_intelligence"]["status"] in {"ok", "unavailable"}
    latest_report = tmp_path / "state" / "reports" / "ai_status_latest.json"
    assert latest_report.exists()


def test_collect_ai_capability_intelligence_reads_meta_learning_and_readiness(
    monkeypatch, tmp_path
) -> None:
    report_dir = tmp_path / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "ai_intermediary_meta_learning_latest.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-03-13T00:00:00+00:00",
                "snapshot": {
                    "total_events": 7,
                    "error_events": 1,
                    "routed_events": 4,
                    "max_recursion_depth": 2,
                },
            }
        ),
        encoding="utf-8",
    )

    class DummyAssessor:
        def __init__(self):
            self.repo_root = None

        def _audit_advanced_ai_capabilities(self):
            return {
                "ensemble_consensus": {"status": "ready", "summary": "ok"},
                "graph_learning": {"status": "missing", "summary": "missing"},
            }

    fake_module = types.ModuleType("src.diagnostics.system_health_assessor")
    fake_module.SystemHealthAssessment = DummyAssessor
    monkeypatch.setitem(sys.modules, "src.diagnostics.system_health_assessor", fake_module)

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    payload = start_nusyq._collect_ai_capability_intelligence(paths)

    assert payload["advanced_ai_readiness"]["status"] == "partial"
    assert payload["advanced_ai_readiness"]["capabilities"]["ensemble_consensus"]["status"] == "ready"
    assert payload["meta_learning"]["status"] == "ok"
    assert payload["meta_learning"]["snapshot"]["total_events"] == 7


def test_collect_ai_health_timeout_degrades_gracefully(monkeypatch, tmp_path) -> None:
    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def health_check(self):
            await asyncio.sleep(2)
            return {"systems": {"ollama": {"healthy": True}}}

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)
    monkeypatch.setenv("NUSYQ_AI_STATUS_TIMEOUT_S", "1")

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    payload = start_nusyq._collect_ai_health(paths, record_metrics=False)
    router = payload["services"]["router"]
    assert router["healthy"] is False
    assert router["error"] == "health_check_timeout"
    assert router["timeout_seconds"] == 1.0


def test_collect_ai_health_subprocess_probe_mode(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE", "subprocess")
    monkeypatch.setenv("NUSYQ_AI_STATUS_TIMEOUT_S", "5")

    monkeypatch.setattr(
        start_nusyq,
        "run",
        lambda _cmd, cwd=None, timeout_s=10: (
            0,
            json.dumps({"systems": {"ollama": {"healthy": True, "models": ["qwen"]}}}),
            "",
        ),
    )

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    payload = start_nusyq._collect_ai_health(paths, record_metrics=False)
    assert payload["services"]["ollama"]["healthy"] is True
    assert payload["services"]["ollama"]["models"] == ["qwen"]


def test_collect_ai_health_subprocess_timeout_normalized(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE", "subprocess")
    monkeypatch.setenv("NUSYQ_AI_STATUS_TIMEOUT_S", "4")
    monkeypatch.setattr(start_nusyq, "run", lambda *_args, **_kwargs: (1, "", "TimeoutExpired: x"))

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    payload = start_nusyq._collect_ai_health(paths, record_metrics=False)
    router = payload["services"]["router"]
    assert router["healthy"] is False
    assert router["error"] == "health_check_timeout"
    assert router["timeout_seconds"] == 4.0


def test_collect_ai_health_includes_external_runtime_status(monkeypatch, tmp_path) -> None:
    report_dir = tmp_path / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "integration_status.json").write_text(
        json.dumps(
            {
                "hermes_agent": {
                    "available": True,
                    "path": str(tmp_path / "state" / "runtime" / "external" / "hermes-agent"),
                    "runnable": False,
                    "python_3_11_available": False,
                    "node_modules_ready": True,
                },
                "metaclaw": {
                    "available": True,
                    "path": str(tmp_path / "state" / "runtime" / "external" / "metaclaw-agent"),
                    "runnable": False,
                    "env_configured": False,
                    "registration_ready": True,
                    "missing_required_env": ["CLOWNCH_API_KEY or CLAWNCHER_API_KEY"],
                    "next_step": "npm run register",
                    "resolved_secret_sources": ["workspace:env"],
                    "node_modules_ready": True,
                },
            }
        ),
        encoding="utf-8",
    )

    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def health_check(self):
            return {"systems": {"ollama": {"healthy": True}}}

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)
    monkeypatch.setenv("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE", "in_process")

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    payload = start_nusyq._collect_ai_health(paths, record_metrics=False)

    assert payload["services"]["hermes_agent"]["status"] == "installed"
    assert payload["services"]["hermes_agent"]["healthy"] is False
    assert payload["services"]["metaclaw"]["env_configured"] is False
    assert payload["services"]["metaclaw"]["registration_ready"] is True
    assert payload["services"]["metaclaw"]["next_step"] == "npm run register"


def test_collect_ai_health_degrades_metaclaw_when_external_auth_fails(monkeypatch, tmp_path) -> None:
    report_dir = tmp_path / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "integration_status.json").write_text(
        json.dumps(
            {
                "metaclaw": {
                    "available": True,
                    "path": str(tmp_path / "state" / "runtime" / "external" / "metaclaw-agent"),
                    "runnable": True,
                    "env_configured": True,
                    "registration_ready": False,
                    "registration_recommended": True,
                    "missing_required_env": [],
                    "next_step": "npm run status",
                    "resolved_secret_sources": ["metaclaw:.env"],
                    "node_modules_ready": True,
                    "externally_verified": False,
                    "status_check": {
                        "ok": False,
                        "status": "auth_error",
                        "http_status": 401,
                        "error": '{"error":"Invalid or missing API key"}',
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def health_check(self):
            return {"systems": {"ollama": {"healthy": True}}}

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)
    monkeypatch.setenv("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE", "in_process")

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    payload = start_nusyq._collect_ai_health(paths, record_metrics=False)

    assert payload["services"]["metaclaw"]["healthy"] is False
    assert payload["services"]["metaclaw"]["status"] == "degraded"
    assert payload["services"]["metaclaw"]["error"] == "external_status_auth_error"
    assert payload["services"]["metaclaw"]["registration_recommended"] is True
    assert payload["services"]["metaclaw"]["next_step"] == "npm run register"


def test_collect_ai_health_overlays_live_core_service_probes(monkeypatch, tmp_path) -> None:
    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def health_check(self):
            return {"systems": {"ollama": {"healthy": False, "status": "metadata"}}}

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)
    monkeypatch.setenv("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE", "in_process")
    monkeypatch.setattr(
        start_nusyq,
        "_preflight_openclaw_target",
        lambda _system, timeout_s=0: {
            "checked": True,
            "available": True,
            "reachable": True,
            "model_count": 3,
            "url": "http://127.0.0.1:11434/api/tags",
            "detail": "ok",
            "timeout_seconds": timeout_s,
        },
    )
    monkeypatch.setattr(
        start_nusyq,
        "_simulatedverse_health_urls",
        lambda _port: ["http://127.0.0.1:5001/api/health"],
    )
    monkeypatch.setattr(start_nusyq, "_probe_http_health", lambda _url, timeout_s=1.5: (True, "HTTP 200"))

    sim_root = tmp_path / "SimulatedVerse"
    sim_root.mkdir(parents=True, exist_ok=True)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=sim_root,
        nusyq_root=None,
    )
    payload = start_nusyq._collect_ai_health(paths, record_metrics=False)

    assert payload["services"]["ollama"]["healthy"] is True
    assert payload["services"]["ollama"]["check_mode"] == "live_probe"
    assert payload["services"]["ollama"]["model_count"] == 3
    assert payload["services"]["simulatedverse"]["healthy"] is True
    assert payload["services"]["simulatedverse"]["url"] == "http://127.0.0.1:5001/api/health"
    assert payload["services"]["simulatedverse"]["check_mode"] == "live_probe"


def test_collect_ai_health_keeps_existing_ollama_health_when_probe_is_blocked(
    monkeypatch, tmp_path
) -> None:
    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def health_check(self):
            return {"systems": {"ollama": {"healthy": True, "status": "metadata"}}}

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)
    monkeypatch.setenv("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE", "in_process")
    monkeypatch.setattr(
        start_nusyq,
        "_preflight_openclaw_target",
        lambda _system, timeout_s=0: {
            "checked": True,
            "available": False,
            "reachable": False,
            "model_count": 0,
            "url": "http://127.0.0.1:11434/api/tags",
            "detail": "operation not permitted",
            "timeout_seconds": timeout_s,
        },
    )

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    payload = start_nusyq._collect_ai_health(paths, record_metrics=False)

    assert payload["services"]["ollama"]["healthy"] is True
    assert payload["services"]["ollama"]["check_mode"] == "live_probe_blocked_fallback"
    assert payload["services"]["ollama"]["probe_blocked"] is True

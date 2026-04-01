"""Tests for start_nusyq.py spine command.

Contract tests - verify CLI outputs and exit codes without full integration.
"""

import json
import subprocess
import sys
import time
import types
from datetime import datetime, timedelta, timezone, UTC
from enum import Enum
from pathlib import Path

import pytest

pytestmark = [pytest.mark.no_cov, pytest.mark.timeout(180)]


# Get the workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent.absolute()
START_NUSYQ_PATH = WORKSPACE_ROOT / "scripts" / "start_nusyq.py"


try:
    from src.utils.intelligent_timeout_manager import get_adaptive_timeout
except ImportError:
    get_adaptive_timeout = None


def _get_adaptive_timeout(service: str, default: int) -> int:
    try:
        if get_adaptive_timeout is None:
            return default
        return max(default, get_adaptive_timeout(service, complexity=1.2, priority="high"))
    except (ImportError, AttributeError, TypeError):
        return default


HYGIENE_TIMEOUT = _get_adaptive_timeout("hygiene", default=240)
DOCTRINE_TIMEOUT = _get_adaptive_timeout("analysis", default=120)
EMERGENCE_TIMEOUT = _get_adaptive_timeout("analysis", default=120)
SELFCHECK_TIMEOUT = _get_adaptive_timeout("analysis", default=120)
MAP_TIMEOUT = _get_adaptive_timeout("analysis", default=120)


def test_help_output():
    """Test help output contains all actions."""
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "help"],
        capture_output=True,
        text=True,
        timeout=_get_adaptive_timeout("tool_help", default=120),
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    assert result.returncode == 0
    assert "snapshot" in result.stdout
    assert "heal" in result.stdout
    assert "suggest" in result.stdout
    assert "hygiene" in result.stdout
    assert "analyze" in result.stdout
    assert "review" in result.stdout
    assert "debug" in result.stdout
    assert "test" in result.stdout
    assert "doctor" in result.stdout


@pytest.mark.timeout(HYGIENE_TIMEOUT)
def test_hygiene_runs():
    """Test hygiene action executes without crash."""
    timeout = HYGIENE_TIMEOUT
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "hygiene"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    assert result.returncode == 0
    # Should contain either "CLEAN" or "DIRTY" or "ahead"
    assert any(x in result.stdout for x in ["CLEAN", "DIRTY", "ahead", "behind"])


def test_analyze_missing_file():
    """Test analyze shows usage when file missing."""
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "analyze", "nonexistent.py"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    assert result.returncode == 1
    assert "ERROR" in result.stdout
    assert "File not found" in result.stdout


def test_review_missing_arg():
    """Test review shows usage when no file provided."""
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "review"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    assert result.returncode == 1
    assert "ERROR" in result.stdout
    assert "Missing file path" in result.stdout


def test_debug_missing_arg():
    """Test debug shows usage when no description provided."""
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "debug"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    assert result.returncode == 1
    assert "ERROR" in result.stdout
    assert "Missing error description" in result.stdout


def test_unknown_action():
    """Test unknown action shows error."""
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "invalidaction"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    assert result.returncode == 1
    assert "ERROR" in result.stdout
    assert "Unknown action" in result.stdout


@pytest.mark.timeout(DOCTRINE_TIMEOUT)
def test_doctrine_check_runs():
    """Test doctrine_check action executes and generates report."""
    timeout = DOCTRINE_TIMEOUT
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "doctrine_check"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    # Returns 0 if compliant (>=90%), 1 if violations
    assert result.returncode in [0, 1]
    assert "Compliance Score" in result.stdout
    assert "Violations Found" in result.stdout


@pytest.mark.timeout(EMERGENCE_TIMEOUT)
def test_emergence_capture_runs():
    """Test emergence_capture action executes and generates log."""
    timeout = EMERGENCE_TIMEOUT
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "emergence_capture"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    assert result.returncode == 0
    assert "Emergence log saved" in result.stdout or "Emergence Capture" in result.stdout


@pytest.mark.timeout(SELFCHECK_TIMEOUT)
def test_selfcheck_runs():
    """Test selfcheck action executes diagnostics."""
    timeout = SELFCHECK_TIMEOUT
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "selfcheck"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    assert result.returncode == 0
    assert "checks passed" in result.stdout or "Selfcheck" in result.stdout


@pytest.mark.timeout(MAP_TIMEOUT)
def test_map_generates_report():
    """Test map action generates capability map."""
    timeout = MAP_TIMEOUT
    result = subprocess.run(
        [sys.executable, str(START_NUSYQ_PATH), "map"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        cwd=str(WORKSPACE_ROOT),
    )
    assert result.returncode == 0
    assert "Capability map saved" in result.stdout or "Wired Actions" in result.stdout


def test_collect_ai_health_awaits_async_health_check(monkeypatch, tmp_path):
    """Regression: ai_status must await AgentTaskRouter.health_check()."""
    import scripts.start_nusyq as start_nusyq

    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def health_check(self):
            return {"systems": {"ollama": {"healthy": True, "models": ["qwen"]}}}

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)
    monkeypatch.setenv("NUSYQ_AI_STATUS_ROUTER_PROBE_MODE", "in_process")

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    health = start_nusyq._collect_ai_health(paths, record_metrics=False)

    assert health["services"]["ollama"]["healthy"] is True
    assert health["services"]["ollama"]["models"] == ["qwen"]


def test_handle_advanced_ai_quests_writes_latest_report(monkeypatch, tmp_path, capsys):
    """advanced_ai_quests should emit a canonical latest report."""
    import scripts.start_nusyq as start_nusyq

    fake_module = types.ModuleType("src.automation.autonomous_quest_generator")

    class DummyGenerator:
        async def generate_advanced_ai_capability_quests(self):
            return {
                "success": True,
                "created": 2,
                "skipped": 1,
                "failed": 0,
                "quest_ids": ["q1", "q2"],
            }

    fake_module.AutonomousQuestGenerator = DummyGenerator
    monkeypatch.setitem(sys.modules, "src.automation.autonomous_quest_generator", fake_module)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_advanced_ai_quests(["advanced_ai_quests"], paths, json_mode=True)
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["created"] == 2
    latest_report = tmp_path / "state" / "reports" / "advanced_ai_quests_latest.json"
    assert latest_report.exists()


def test_handle_graph_learning_writes_latest_report(monkeypatch, tmp_path, capsys):
    """graph_learning should emit a canonical latest report."""
    import scripts.start_nusyq as start_nusyq

    fake_module = types.ModuleType("src.tools.dependency_analyzer")

    class DummyAnalyzer:
        def __init__(self, repos=None, max_files_per_repo=None):
            self.repos = repos or {}
            self.max_files_per_repo = max_files_per_repo

        def analyze_all(self):
            return None

        def generate_graph_learning_report(self, top_k=10):
            return {
                "status": "ok",
                "backend": "networkx",
                "summary": {
                    "node_count": 12,
                    "edge_count": 24,
                    "community_count": 3,
                    "cycle_count": 1,
                },
                "top_impact_nodes": [{"path": "src/core.py", "impact_score": 9.5}],
            }

    fake_module.DependencyAnalyzer = DummyAnalyzer
    monkeypatch.setitem(sys.modules, "src.tools.dependency_analyzer", fake_module)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=tmp_path / "simverse",
        nusyq_root=tmp_path / "root",
    )
    rc = start_nusyq._handle_graph_learning(
        ["graph_learning", "--hub-only", "--top-k=4", "--max-files=25"], paths, json_mode=True
    )
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["graph_learning"]["summary"]["node_count"] == 12
    assert payload["options"]["hub_only"] is True
    assert payload["options"]["top_k"] == 4
    assert payload["options"]["max_files_per_repo"] == 25
    assert payload["attempts"][0]["timed_out"] is False
    latest_report = tmp_path / "state" / "reports" / "graph_learning_latest.json"
    assert latest_report.exists()


def test_handle_graph_learning_timeout_degrades_with_retry_plan(monkeypatch, tmp_path, capsys):
    """graph_learning should return structured partial output after adaptive timeouts."""
    import scripts.start_nusyq as start_nusyq

    fake_module = types.ModuleType("src.tools.dependency_analyzer")

    class DummyAnalyzer:
        def __init__(self, repos=None, max_files_per_repo=None):
            self.repos = repos or {}
            self.max_files_per_repo = max_files_per_repo

        def analyze_all(self):
            return None

        def generate_graph_learning_report(self, top_k=10):
            return {"status": "ok", "summary": {"node_count": 1}}

    class FakeFuture:
        def result(self, timeout=None):
            raise start_nusyq.FuturesTimeoutError()

        def cancel(self):
            return True

    class FakeExecutor:
        def __init__(self, max_workers=1):
            pass

        def submit(self, fn):
            return FakeFuture()

        def shutdown(self, wait=False, cancel_futures=False):
            return None

    fake_module.DependencyAnalyzer = DummyAnalyzer
    monkeypatch.setitem(sys.modules, "src.tools.dependency_analyzer", fake_module)
    monkeypatch.setattr(start_nusyq, "ThreadPoolExecutor", FakeExecutor)
    monkeypatch.setenv("NUSYQ_GRAPH_LEARNING_TIMEOUT_S", "1")

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=tmp_path / "simverse",
        nusyq_root=tmp_path / "root",
    )
    rc = start_nusyq._handle_graph_learning(["graph_learning"], paths, json_mode=True)

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "partial"
    assert payload["error"] == "analysis_timeout"
    assert len(payload["attempts"]) == 3
    assert payload["next_suggested_args"]["max_files_per_repo"] >= 25
    latest_report = tmp_path / "state" / "reports" / "graph_learning_latest.json"
    assert latest_report.exists()


def test_handle_graph_learning_reuses_fresh_cached_report(monkeypatch, tmp_path, capsys):
    """graph_learning should reuse a fresh latest report when scope/options match."""
    import scripts.start_nusyq as start_nusyq

    report_dir = tmp_path / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    cached_payload = {
        "action": "graph_learning",
        "status": "ok",
        "generated_at": (datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
        "options": {
            "hub_only": True,
            "include_simulatedverse": False,
            "include_root": False,
            "top_k": 4,
            "max_files_per_repo": 25,
        },
        "graph_learning": {"status": "ok", "summary": {"node_count": 9}},
    }
    (report_dir / "graph_learning_latest.json").write_text(
        json.dumps(cached_payload),
        encoding="utf-8",
    )

    fake_module = types.ModuleType("src.tools.dependency_analyzer")

    class DummyAnalyzer:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Analyzer should not be constructed when cache is reusable")

    fake_module.DependencyAnalyzer = DummyAnalyzer
    monkeypatch.setitem(sys.modules, "src.tools.dependency_analyzer", fake_module)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_graph_learning(
        ["graph_learning", "--hub-only", "--top-k=4", "--max-files=25", "--reuse-ttl-s=3600"],
        paths,
        json_mode=True,
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["graph_learning"]["summary"]["node_count"] == 9
    assert payload["cache_info"]["reused"] is True


def test_run_ai_task_generate_accepts_description(monkeypatch, tmp_path, capsys):
    """Generate should accept natural-language descriptions (no file path required)."""
    import scripts.start_nusyq as start_nusyq

    calls: list[dict[str, object]] = []
    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def route_task(self, task_type, description, context, target_system):
            calls.append(
                {
                    "task_type": task_type,
                    "description": description,
                    "context": context,
                    "target_system": target_system,
                }
            )
            return {
                "status": "success",
                "system": target_system,
                "task_id": "gen_001",
                "output": "generated",
            }

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)

    rc = start_nusyq.run_ai_task(tmp_path, "generate", "Create a REST API with JWT", "chatdev")
    assert rc == 0
    assert len(calls) == 1
    assert calls[0]["task_type"] == "generate"
    assert calls[0]["description"] == "Create a REST API with JWT"
    assert calls[0]["target_system"] == "chatdev"
    assert isinstance(calls[0]["context"], dict)
    assert calls[0]["context"].get("source_mode") == "text"

    out = capsys.readouterr().out
    assert "Task input:" in out
    assert "Create a REST API with JWT" in out


def test_run_ai_task_chatdev_failover_to_ollama(monkeypatch, tmp_path, capsys):
    """ChatDev auth/runtime failures should automatically fail over to configured systems."""
    import scripts.start_nusyq as start_nusyq

    calls: list[str] = []
    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def route_task(self, task_type, description, context, target_system):
            calls.append(str(target_system))
            if target_system == "chatdev":
                return {
                    "status": "failed",
                    "system": "chatdev",
                    "task_id": "gen_failover",
                    "error": "HTTP 401 Unauthorized",
                }
            return {
                "status": "success",
                "system": target_system,
                "task_id": "gen_failover",
                "output": f"{target_system} fallback output",
            }

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)
    monkeypatch.setenv("NUSYQ_CHATDEV_FAILOVER_CHAIN", "ollama")

    rc = start_nusyq.run_ai_task(tmp_path, "generate", "Create service", "chatdev")
    assert rc == 0
    assert calls == ["chatdev", "ollama"]

    out = capsys.readouterr().out.lower()
    assert "chatdev failure signal detected" in out
    assert "fallback succeeded via ollama" in out


def test_run_ai_task_writes_failover_receipt_artifact(monkeypatch, tmp_path):
    """Each failover attempt should emit a JSON telemetry receipt artifact."""
    import scripts.start_nusyq as start_nusyq

    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def route_task(self, task_type, description, context, target_system):
            if target_system == "chatdev":
                return {
                    "status": "failed",
                    "system": "chatdev",
                    "task_id": "failover_receipt_001",
                    "error": "HTTP 401 Unauthorized",
                }
            return {
                "status": "success",
                "system": target_system,
                "task_id": "failover_receipt_001",
                "output": "fallback output",
            }

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)

    rc = start_nusyq.run_ai_task(
        tmp_path,
        "generate",
        "Create service",
        "chatdev",
        failover_chain_override="ollama",
    )
    assert rc == 0

    receipts_dir = tmp_path / "state" / "reports" / "failover_receipts"
    receipts = sorted(receipts_dir.glob("failover_*.json"))
    assert receipts, "Expected failover receipt artifact(s)"
    payload = json.loads(receipts[-1].read_text(encoding="utf-8"))
    assert payload["task_id"] == "failover_receipt_001"
    assert payload["trigger_system"] == "chatdev"
    assert payload["candidate_system"] == "ollama"
    assert payload["candidate_status"] == "success"
    assert payload["selected"] is True


def test_run_ai_task_debug_accepts_text_description(monkeypatch, tmp_path):
    """Debug should support raw error descriptions instead of forcing a file path."""
    import scripts.start_nusyq as start_nusyq

    calls: list[dict[str, object]] = []
    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def route_task(self, task_type, description, context, target_system):
            calls.append(
                {
                    "task_type": task_type,
                    "description": description,
                    "context": context,
                    "target_system": target_system,
                }
            )
            return {
                "status": "success",
                "system": target_system,
                "task_id": "dbg_001",
                "output": "debug suggestions",
            }

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)

    rc = start_nusyq.run_ai_task(
        tmp_path,
        "debug",
        "ImportError: cannot import name 'foo' from bar",
        "quantum_resolver",
    )
    assert rc == 0
    assert len(calls) == 1
    assert calls[0]["task_type"] == "debug"
    assert "Debug this error and propose concrete fixes" in str(calls[0]["description"])
    assert calls[0]["context"].get("source_mode") == "text"


def test_run_ai_task_quantum_resolver_output_error_normalized_to_failure(monkeypatch, tmp_path):
    """Quantum resolver payload errors must not be treated as success."""
    import scripts.start_nusyq as start_nusyq

    fake_module = types.ModuleType("src.tools.agent_task_router")

    class DummyRouter:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        async def route_task(self, task_type, description, context, target_system):
            return {
                "status": "success",
                "system": "quantum_resolver",
                "task_id": "quantum_semantic_error_001",
                "output": {
                    "status": "error",
                    "error_message": "Unknown problem type: debug",
                },
            }

    fake_module.AgentTaskRouter = DummyRouter
    monkeypatch.setitem(sys.modules, "src.tools.agent_task_router", fake_module)

    rc = start_nusyq.run_ai_task(
        tmp_path,
        "debug",
        "ImportError: cannot import foo",
        "quantum_resolver",
    )
    assert rc == 1


def test_ai_actions_parse_failover_chain_override_for_generate():
    """Generate should pass --failover-chain to run_ai_task."""
    from scripts.nusyq_actions import ai_actions

    class DummyPaths:
        nusyq_hub = Path("/tmp")

    captured: dict[str, object] = {}

    def fake_run_ai_task(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return 0

    rc = ai_actions.handle_generate(
        [
            "generate",
            "Create a REST API",
            "--system=chatdev",
            "--failover-chain=codex,ollama",
        ],
        DummyPaths(),
        fake_run_ai_task,
    )
    assert rc == 0
    assert captured["args"][1] == "generate"
    assert captured["kwargs"]["failover_chain_override"] == "codex,ollama"


def test_ai_actions_parse_failover_chain_override_for_review():
    """Review should pass --failover-chain to run_ai_task."""
    from scripts.nusyq_actions import ai_actions

    class DummyPaths:
        nusyq_hub = Path("/tmp")

    captured: dict[str, object] = {}

    def fake_run_ai_task(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return 0

    rc = ai_actions.handle_review(
        [
            "review",
            "src/main.py",
            "--system=chatdev",
            "--failover-chain=ollama,lmstudio",
        ],
        DummyPaths(),
        fake_run_ai_task,
    )
    assert rc == 0
    assert captured["args"][1] == "review"
    assert captured["kwargs"]["failover_chain_override"] == "ollama,lmstudio"


def test_ai_actions_parse_failover_chain_override_for_analyze(tmp_path):
    """Analyze should pass --failover-chain to run_ai_task."""
    from scripts.nusyq_actions import ai_actions

    target_file = tmp_path / "sample.py"
    target_file.write_text("print('ok')\n", encoding="utf-8")

    class DummyPaths:
        nusyq_hub = tmp_path

    captured: dict[str, object] = {}

    def fake_run_ai_task(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return 0

    rc = ai_actions.handle_analyze(
        [
            "analyze",
            str(target_file),
            "--system=chatdev",
            "--failover-chain=codex,ollama",
        ],
        DummyPaths(),
        fake_run_ai_task,
    )
    assert rc == 0
    assert captured["args"][1] == "analyze"
    assert captured["kwargs"]["failover_chain_override"] == "codex,ollama"


def test_ai_actions_parse_failover_chain_override_for_debug():
    """Debug should pass --failover-chain to run_ai_task."""
    from scripts.nusyq_actions import ai_actions

    class DummyPaths:
        nusyq_hub = Path("/tmp")

    captured: dict[str, object] = {}

    def fake_run_ai_task(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return 0

    rc = ai_actions.handle_debug(
        [
            "debug",
            "ImportError: cannot import foo",
            "--system=ollama",
            "--failover-chain=codex,ollama",
        ],
        DummyPaths(),
        fake_run_ai_task,
    )
    assert rc == 0
    assert captured["args"][1] == "debug"
    assert captured["kwargs"]["failover_chain_override"] == "codex,ollama"


def test_failover_status_summarizes_newest_receipts(tmp_path, capsys):
    """failover_status should summarize newest receipts and success rates."""
    import scripts.start_nusyq as start_nusyq

    receipts_dir = tmp_path / "state" / "reports" / "failover_receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)

    payloads = [
        {
            "generated_at": "2026-02-21T00:00:01Z",
            "task_id": "t1",
            "trigger_system": "chatdev",
            "candidate_system": "ollama",
            "candidate_status": "success",
            "selected": True,
            "trigger_reason": "401 unauthorized",
        },
        {
            "generated_at": "2026-02-21T00:00:02Z",
            "task_id": "t2",
            "trigger_system": "chatdev",
            "candidate_system": "codex",
            "candidate_status": "failed",
            "selected": False,
            "trigger_reason": "401 unauthorized",
        },
        {
            "generated_at": "2026-02-21T00:00:03Z",
            "task_id": "t3",
            "trigger_system": "chatdev",
            "candidate_system": "ollama",
            "candidate_status": "submitted",
            "selected": True,
            "trigger_reason": "401 unauthorized",
        },
    ]
    for idx, payload in enumerate(payloads, start=1):
        path = receipts_dir / f"failover_2026-02-21_00000{idx}_t{idx}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        time.sleep(0.01)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_failover_status(
        ["failover_status", "--limit=2"], paths, json_mode=True
    )
    assert rc == 0

    report = json.loads(capsys.readouterr().out)
    assert report["action"] == "failover_status"
    assert report["total_receipts"] == 3
    assert report["recent_limit"] == 2
    assert report["recent_receipts_count"] == 2
    assert report["summary"]["attempted"] == 2
    assert report["summary"]["successful"] == 1
    assert report["summary"]["selected"] == 1
    assert report["summary"]["selected_successful"] == 1
    assert len(report["newest_receipts"]) == 2
    systems = {row["candidate_system"] for row in report["by_candidate_system"]}
    assert systems == {"codex", "ollama"}


def test_failover_status_registered_in_known_actions():
    """failover_status must be routable from the top-level CLI."""
    import scripts.start_nusyq as start_nusyq

    assert "failover_status" in start_nusyq.KNOWN_ACTIONS


def test_find_repo_by_name_prefers_exact_match(monkeypatch, tmp_path):
    """Regression: NuSyQ should not resolve to NuSyQ-Hub via substring."""
    import scripts.start_nusyq as start_nusyq

    hub = tmp_path / "NuSyQ-Hub"
    root = tmp_path / "NuSyQ"
    hub.mkdir()
    root.mkdir()

    monkeypatch.setattr(start_nusyq, "is_git_repo", lambda p: p == root)
    found = start_nusyq.find_repo_by_name([tmp_path], "NuSyQ")

    assert found == root


def test_canonicalize_repo_path_resolves_nested_repo(monkeypatch, tmp_path):
    """Wrapper folder should resolve to nested real git repo when present."""
    import scripts.start_nusyq as start_nusyq

    wrapper = tmp_path / "SimulatedVerse"
    nested = wrapper / "SimulatedVerse"
    nested.mkdir(parents=True)

    monkeypatch.setattr(start_nusyq, "is_git_repo", lambda p: p == nested)
    resolved = start_nusyq._canonicalize_repo_path(wrapper, "SimulatedVerse")

    assert resolved == nested


def test_action_contracts_cover_required_actions():
    """Required key actions must have timeout/schema/safety contract coverage."""
    import scripts.start_nusyq as start_nusyq

    contracts = start_nusyq.read_action_contracts(WORKSPACE_ROOT)
    payload = start_nusyq._validate_contracts_payload(contracts)

    assert payload["valid"] is True, payload["issues"]


def test_validate_contracts_probe_success(monkeypatch, tmp_path):
    """Runtime probe should pass when command emits contract-compliant JSON."""
    import scripts.start_nusyq as start_nusyq

    monkeypatch.setattr(start_nusyq, "CONTRACT_REQUIRED_ACTIONS", ("ai_status",))

    def fake_run(_cmd, cwd=None, timeout_s=10):
        return 0, json.dumps({"action": "ai_status", "status": "ok", "generated_at": "now"}), ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    contracts = {
        "actions": {
            "ai_status": {
                "cmd": "python scripts/start_nusyq.py ai_status --json",
                "timeout_s": 30,
                "safety_tier": "read_only",
                "probe_enabled": True,
                "probe_cmd": ["python", "scripts/start_nusyq.py", "ai_status", "--json"],
                "output_schema": {
                    "type": "object",
                    "required": ["action", "status", "generated_at"],
                },
                "side_effects": {
                    "network": "none",
                    "long_running": False,
                    "idempotent": True,
                },
            }
        }
    }
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    payload = start_nusyq._validate_contracts_payload(contracts, paths=paths, probe=True)
    assert payload["valid"] is True, payload["issues"]
    assert payload["probe_requested"] is True
    assert payload["probe_results"]
    assert payload["probe_results"][0]["ok"] is True


def test_validate_contracts_probe_detects_schema_mismatch(monkeypatch, tmp_path):
    """Runtime probe should fail when output misses required schema keys."""
    import scripts.start_nusyq as start_nusyq

    monkeypatch.setattr(start_nusyq, "CONTRACT_REQUIRED_ACTIONS", ("ai_status",))

    def fake_run(_cmd, cwd=None, timeout_s=10):
        return 0, json.dumps({"action": "ai_status"}), ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    contracts = {
        "actions": {
            "ai_status": {
                "cmd": "python scripts/start_nusyq.py ai_status --json",
                "timeout_s": 30,
                "safety_tier": "read_only",
                "probe_enabled": True,
                "probe_cmd": ["python", "scripts/start_nusyq.py", "ai_status", "--json"],
                "output_schema": {
                    "type": "object",
                    "required": ["action", "status"],
                },
                "side_effects": {
                    "network": "none",
                    "long_running": False,
                    "idempotent": True,
                },
            }
        }
    }
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    payload = start_nusyq._validate_contracts_payload(contracts, paths=paths, probe=True)
    assert payload["valid"] is False
    assert "ai_status: runtime probe failed" in payload["issues"]


def test_system_complete_json_emits_dashboard_artifacts(monkeypatch, tmp_path, capsys):
    """system_complete --json should emit payload with history/dashboard references."""
    import scripts.start_nusyq as start_nusyq

    def fake_run(_cmd, cwd=None, timeout_s=10):
        return 0, "ok", ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setattr(
        start_nusyq,
        "_collect_ai_health",
        lambda _paths, record_metrics=False: {
            "services": {"ollama": {"healthy": True}, "chatdev": {"healthy": True}},
            "quantum": {"healthy": True},
        },
    )

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_system_complete(paths, json_mode=True)
    assert rc == 0

    payload = capsys.readouterr().out
    assert "system_complete_history.jsonl" in payload
    assert "system_complete_dashboard_latest.json" in payload
    assert "system_complete_checkpoint_latest.json" in payload
    assert (tmp_path / "state" / "reports" / "system_complete_gate_latest.json").exists()
    assert (tmp_path / "state" / "reports" / "system_complete_dashboard_latest.json").exists()
    assert (tmp_path / "state" / "reports" / "system_complete_checkpoint_latest.json").exists()


def test_system_complete_retries_ai_status_timeout(monkeypatch, tmp_path, capsys):
    """system_complete should retry ai_status once when router probe times out."""
    import scripts.start_nusyq as start_nusyq

    def fake_run(_cmd, cwd=None, timeout_s=10):
        return 0, "ok", ""

    attempts = {"count": 0}

    def fake_collect(_paths, record_metrics=False):
        attempts["count"] += 1
        if attempts["count"] == 1:
            return {
                "services": {
                    "router": {
                        "healthy": False,
                        "error": "health_check_timeout",
                        "timeout_seconds": 8.0,
                        "probe_mode": "subprocess",
                    }
                },
                "quantum": {"healthy": True},
            }
        return {
            "services": {"ollama": {"healthy": True}, "chatdev": {"healthy": True}},
            "quantum": {"healthy": True},
        }

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setattr(start_nusyq, "_collect_ai_health", fake_collect)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_system_complete(paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    checks = payload.get("checks", [])
    ai_check = next(check for check in checks if check.get("name") == "ai_status_clean")
    assert ai_check["passed"] is True
    retry_meta = ai_check["details"]["probe_retry"]
    assert retry_meta["attempted"] is True
    assert retry_meta["recovered"] is True


def test_system_complete_async_submits_background_job(monkeypatch, tmp_path, capsys):
    """system_complete --async should submit a background gate job."""
    import scripts.start_nusyq as start_nusyq

    captured: dict[str, object] = {}

    def fake_start_job(paths, job_type, command, cwd=None, metadata=None):
        captured["paths"] = paths
        captured["job_type"] = job_type
        captured["command"] = list(command)
        captured["cwd"] = cwd
        captured["metadata"] = metadata or {}
        return {
            "job_id": "system_complete_20260218_abcd1234",
            "pid": 5150,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        }

    monkeypatch.setattr(start_nusyq, "_start_subprocess_job", fake_start_job)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_system_complete(
        paths,
        json_mode=True,
        args=["system_complete", "--async", "--budget-s=600"],
    )
    assert rc == 0
    assert captured["job_type"] == "system_complete"
    assert captured["command"] == [
        sys.executable,
        "scripts/start_nusyq.py",
        "system_complete",
        "--sync",
        "--json",
        "--budget-s=600",
    ]
    metadata = captured["metadata"]
    assert isinstance(metadata, dict)
    assert metadata.get("checkpoint_file")
    payload = capsys.readouterr().out
    assert '"status": "submitted"' in payload
    assert '"action": "system_complete"' in payload


def test_system_complete_async_startup_profile_submits_startup_flag(monkeypatch, tmp_path, capsys):
    """system_complete --startup --async should preserve the startup profile in the job command."""
    import scripts.start_nusyq as start_nusyq

    captured: dict[str, object] = {}

    def fake_start_job(paths, job_type, command, cwd=None, metadata=None):
        captured["paths"] = paths
        captured["job_type"] = job_type
        captured["command"] = list(command)
        captured["cwd"] = cwd
        captured["metadata"] = metadata or {}
        return {
            "job_id": "system_complete_20260312_abcd1234",
            "pid": 5151,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        }

    monkeypatch.setattr(start_nusyq, "_start_subprocess_job", fake_start_job)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_system_complete(
        paths,
        json_mode=True,
        args=["system_complete", "--startup", "--async", "--budget-s=90"],
    )
    assert rc == 0
    assert captured["job_type"] == "system_complete"
    assert captured["command"] == [
        sys.executable,
        "scripts/start_nusyq.py",
        "system_complete",
        "--sync",
        "--json",
        "--startup",
        "--budget-s=90",
    ]
    payload = capsys.readouterr().out
    assert '"status": "submitted"' in payload


def test_system_complete_status_json_includes_checkpoint(monkeypatch, tmp_path, capsys):
    """system_complete_status should include checkpoint summary when available."""
    import scripts.start_nusyq as start_nusyq

    checkpoint_path = tmp_path / "state" / "reports" / "system_complete_checkpoint_latest.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        json.dumps(
            {
                "status": "running",
                "current_check": "openclaw_smoke",
                "completed_checks": 2,
                "total_planned": 7,
                "checks": [
                    {"name": "ai_status_clean", "passed": True},
                    {"name": "chatdev_e2e", "passed": False},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_refresh(_paths, _job_id):
        return {
            "job_id": "system_complete_20260218_abcd1234",
            "job_type": "system_complete",
            "status": "running",
            "pid": 5150,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
            "metadata": {"checkpoint_file": str(checkpoint_path)},
        }

    monkeypatch.setattr(start_nusyq, "_refresh_job_status", fake_refresh)
    monkeypatch.setattr(start_nusyq, "_reconcile_jobs", lambda *_args, **_kwargs: {})
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_system_complete_status(
        ["system_complete_status", "system_complete_20260218_abcd1234"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = capsys.readouterr().out
    assert '"action": "system_complete_status"' in payload
    assert '"checkpoint"' in payload
    assert '"completed_checks": 2' in payload


def test_system_complete_reuses_recent_successful_heavy_checks(monkeypatch, tmp_path, capsys):
    """system_complete --reuse-recent should reuse fresh heavy check passes."""
    import scripts.start_nusyq as start_nusyq

    reports_dir = tmp_path / "state" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    latest_report = reports_dir / "system_complete_gate_latest.json"
    latest_report.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(),
                "checks": [
                    {"name": "chatdev_e2e", "passed": True, "elapsed_s": 100.0},
                    {"name": "openclaw_smoke", "passed": True, "elapsed_s": 1.0},
                    {"name": "culture_ship_cycle", "passed": True, "elapsed_s": 5.0},
                    {"name": "nogic_hotspot_ingestion", "passed": True, "elapsed_s": 1.0},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_run(_cmd, cwd=None, timeout_s=10):
        return 0, "ok", ""

    def should_not_run_heavy(*_args, **_kwargs):
        raise AssertionError("Heavy gate check should have been reused")

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setattr(start_nusyq, "_run_system_gate_check", should_not_run_heavy)
    monkeypatch.setattr(
        start_nusyq,
        "_collect_ai_health",
        lambda _paths, record_metrics=False: {
            "services": {"ollama": {"healthy": True}, "chatdev": {"healthy": True}},
            "quantum": {"healthy": True},
        },
    )

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_system_complete(
        paths,
        json_mode=True,
        args=["system_complete", "--sync", "--reuse-recent", "--reuse-ttl-s=600"],
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    checks = payload.get("checks", [])
    assert isinstance(checks, list)
    reused = {str(c.get("name")): c for c in checks if isinstance(c, dict) and c.get("reused")}
    assert reused["chatdev_e2e"]["reused"] is True
    assert reused["openclaw_smoke"]["reused"] is True
    assert reused["culture_ship_cycle"]["reused"] is True
    assert reused["nogic_hotspot_ingestion"]["reused"] is True


def test_system_complete_startup_profile_runs_bounded_checks(monkeypatch, tmp_path, capsys):
    """Startup profile should run workspace/startup checks without full-stack lint/type gates."""
    import scripts.start_nusyq as start_nusyq

    executed: list[list[str]] = []

    def fake_run(cmd, cwd=None, timeout_s=10):
        _ = (cwd, timeout_s)
        executed.append(list(cmd))
        return 0, json.dumps({"status": "ok"}), ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setattr(
        start_nusyq,
        "_collect_ai_health",
        lambda _paths, record_metrics=False: {
            "services": {"ollama": {"healthy": True}, "chatdev": {"healthy": True}},
            "quantum": {"healthy": True},
        },
    )

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_system_complete(
        paths, json_mode=True, args=["system_complete", "--startup"]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    check_names = [check["name"] for check in payload["checks"]]
    assert payload["profile"] == "startup"
    assert check_names == [
        "ai_status_clean",
        "workspace_verifier",
        "doctor_quick",
        "integration_health_startup",
    ]
    assert "lint_threshold" not in check_names
    assert "type_threshold" not in check_names
    assert [cmd[1:] for cmd in executed] == [
        ["scripts/verify_tripartite_workspace.py"],
        ["scripts/start_nusyq.py", "doctor", "--quick", "--json"],
        [
            "scripts/start_nusyq.py",
            "integration_health",
            "--mode",
            "startup",
            "--simulatedverse-mode",
            "auto",
            "--no-repair-simulatedverse",
            "--json",
        ],
    ]


def test_load_recent_system_complete_checks_requires_matching_profile(tmp_path):
    """Recent reuse should not cross-contaminate startup and full-stack gate profiles."""
    import scripts.start_nusyq as start_nusyq

    report_path = tmp_path / "state" / "reports" / "system_complete_gate_latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(),
                "profile": "full-stack",
                "checks": [{"name": "openclaw_smoke", "passed": True}],
            }
        ),
        encoding="utf-8",
    )

    checks, metadata = start_nusyq._load_recent_system_complete_checks(
        tmp_path, ttl_s=600, profile="startup"
    )
    assert checks == {}
    assert metadata == {}


def test_system_complete_startup_profile_tolerates_optional_external_runtimes(
    monkeypatch, tmp_path, capsys
):
    """Startup profile should not fail on installed-but-unconfigured optional runtimes."""
    import scripts.start_nusyq as start_nusyq

    def fake_run(cmd, cwd=None, timeout_s=10):
        _ = (cmd, cwd, timeout_s)
        return 0, json.dumps({"status": "ok"}), ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setattr(
        start_nusyq,
        "_collect_ai_health",
        lambda _paths, record_metrics=False: {
            "services": {
                "skyclaw": {"healthy": True},
                "ollama": {"healthy": True},
                "hermes_agent": {
                    "healthy": False,
                    "status": "installed",
                    "error": "runtime_not_ready",
                },
                "metaclaw": {
                    "healthy": False,
                    "status": "installed",
                    "error": "runtime_not_ready",
                },
                "factory": {
                    "healthy": False,
                    "error": "ProjectFactory not available (optional dependency)",
                },
            },
            "quantum": {"healthy": True},
        },
    )

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_system_complete(
        paths, json_mode=True, args=["system_complete", "--startup"]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    ai_check = next(check for check in payload["checks"] if check["name"] == "ai_status_clean")
    assert ai_check["passed"] is True


def test_system_complete_startup_profile_fails_when_live_integration_probe_fails(
    monkeypatch, tmp_path, capsys
):
    """Startup gate must fail when integration_health reports live core-service failure."""
    import scripts.start_nusyq as start_nusyq

    def fake_run(cmd, cwd=None, timeout_s=10):
        _ = (cwd, timeout_s)
        if "integration_health" in cmd:
            payload = {
                "status": "degraded",
                "functional": False,
                "signal_checks": {"ollama": False, "simulatedverse": True},
                "failed_signals": ["ollama"],
            }
            return 1, json.dumps(payload), ""
        return 0, json.dumps({"status": "ok"}), ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setattr(
        start_nusyq,
        "_collect_ai_health",
        lambda _paths, record_metrics=False: {
            "services": {"ollama": {"healthy": True}, "chatdev": {"healthy": True}},
            "quantum": {"healthy": True},
        },
    )

    paths = start_nusyq.WorkspacePaths(nusyq_hub=tmp_path, simulatedverse=None, nusyq_root=None)
    rc = start_nusyq._handle_system_complete(paths, json_mode=True, args=["system_complete", "--startup"])

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    integration_check = next(
        check for check in payload["checks"] if check["name"] == "integration_health_startup"
    )
    assert integration_check["passed"] is False


def test_should_skip_lifecycle_refresh_for_read_only_actions():
    import scripts.start_nusyq as start_nusyq

    assert start_nusyq._should_skip_lifecycle_refresh("doctor") is True
    assert start_nusyq._should_skip_lifecycle_refresh("ai_status") is True
    assert start_nusyq._should_skip_lifecycle_refresh("error_report_status") is True
    assert start_nusyq._should_skip_lifecycle_refresh("culture_ship") is True
    assert start_nusyq._should_skip_lifecycle_refresh("heal") is False


def test_error_report_async_submits_background_job(monkeypatch, tmp_path, capsys):
    """error_report --async should submit job and avoid synchronous scan."""
    import scripts.start_nusyq as start_nusyq

    captured: dict[str, object] = {}

    def fake_start_job(paths, job_type, command, cwd=None, metadata=None):
        captured["paths"] = paths
        captured["job_type"] = job_type
        captured["command"] = list(command)
        captured["cwd"] = cwd
        captured["metadata"] = metadata or {}
        return {
            "job_id": "error_report_20260217_abcd1234",
            "pid": 4242,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        }

    monkeypatch.setattr(start_nusyq, "_start_subprocess_job", fake_start_job)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_error_report(["error_report", "--quick", "--async"], paths)
    assert rc == 0
    assert captured["job_type"] == "error_report"
    command = captured["command"]
    assert isinstance(command, list)
    assert command[:5] == [
        sys.executable,
        "scripts/start_nusyq.py",
        "error_report",
        "--sync",
        "--json",
    ]
    assert "--quick" in command
    assert any(token.startswith("--checkpoint-file=") for token in command)
    metadata = captured["metadata"]
    assert isinstance(metadata, dict)
    assert metadata.get("checkpoint_file")
    assert metadata.get("checkpoint_latest_file")
    out = capsys.readouterr().out
    assert "submitted as background job" in out.lower()
    assert "error_report_status" in out


def test_parse_error_report_args_budget(monkeypatch):
    """error_report parser should honor --budget-s and env fallback."""
    import scripts.start_nusyq as start_nusyq

    monkeypatch.setenv("NUSYQ_ERROR_REPORT_BUDGET_S", "15")
    opts = start_nusyq._parse_error_report_args(["error_report"])
    assert opts.budget_s == 15

    opts = start_nusyq._parse_error_report_args(["error_report", "--budget-s=3"])
    assert opts.budget_s == 3


def test_parse_error_report_args_repo_aliases_and_checkpoint_flag():
    """Parser should support --include/--exclude aliases and checkpoint override."""
    import scripts.start_nusyq as start_nusyq

    opts = start_nusyq._parse_error_report_args(
        [
            "error_report",
            "--include=nusyq-hub,simverse",
            "--exclude=nusyq",
            "--checkpoint-file=state/reports/custom_checkpoint.json",
        ]
    )
    assert set(opts.include) == {"nusyq-hub", "simulated-verse"}
    assert set(opts.exclude) == {"nusyq"}
    assert opts.checkpoint_file.endswith("custom_checkpoint.json")


def test_parse_error_report_args_bridge_chain_flags():
    """error_report parser should support bridge-chain flags and parameters."""
    import scripts.start_nusyq as start_nusyq

    opts = start_nusyq._parse_error_report_args(
        [
            "error_report",
            "--chain-bridges",
            "--bridge-test",
            "--bridge-severity=warning",
            "--bridge-max-quests=7",
        ]
    )
    assert opts.bridge_signals is True
    assert opts.bridge_signal_to_quest is True
    assert opts.bridge_error_quests is True
    assert opts.bridge_test_mode is True
    assert opts.bridge_severity == "warning"
    assert opts.bridge_max_quests == 7


def test_error_report_sync_ignores_cached_mode_mismatch(monkeypatch, tmp_path, capsys):
    """A full scan request must not reuse a cached quick report."""
    import scripts.start_nusyq as start_nusyq

    class DummyRepoName(str, Enum):
        NUSYQ_HUB = "nusyq-hub"

    class DummyReporter:
        scan_calls = 0

        def __init__(self, hub_path=None, include_repos=None, exclude_repos=None, **_kw):
            _ = (hub_path, include_repos, exclude_repos)
            self.repos = {DummyRepoName.NUSYQ_HUB: tmp_path}
            self.reports_dir = tmp_path / "docs" / "Reports" / "diagnostics"
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            self.scans = {}
            self.scan_warnings: list[str] = []
            self.all_diagnostics: list[object] = []
            self.scan_mode = "full"

        def load_cached_report(self, max_age_seconds=None):
            _ = max_age_seconds
            return {
                "scan_mode": "quick",
                "targets": ["nusyq-hub"],
                "cache_info": {"age_seconds": 5},
            }

        def scan_all_repos(self, quick=False):
            DummyReporter.scan_calls += 1
            repo_key = next(iter(self.repos.keys()))
            self.scans[repo_key] = types.SimpleNamespace(diagnostics=[])
            return self.generate_unified_report()

        def generate_unified_report(self):
            return {
                "timestamp": datetime.now().isoformat(),
                "scan_mode": "full",
                "total_diagnostics": 0,
                "by_severity": {"errors": 0, "warnings": 0, "infos_hints": 0},
                "by_repo": {
                    "nusyq-hub": {
                        "repo": "nusyq-hub",
                        "total": 0,
                        "by_severity": {},
                        "by_type": {},
                        "by_source": {},
                        "path": str(tmp_path),
                        "python_targets": 1,
                        "python_target_names": ["src"],
                    }
                },
                "targets": ["nusyq-hub"],
                "filters": {"include": [], "exclude": []},
                "partial_scan": False,
                "scan_warnings": [],
            }

        def write_report(self):
            report_json = self.reports_dir / "unified_error_report_latest.json"
            report_md = self.reports_dir / "unified_error_report_latest.md"
            report_json.write_text("{}", encoding="utf-8")
            report_md.write_text("# report", encoding="utf-8")
            return {
                "json": str(report_json),
                "md": str(report_md),
                "latest_json": str(report_json),
                "latest_md": str(report_md),
            }

    fake_module = types.ModuleType("src.diagnostics.unified_error_reporter")
    fake_module.RepoName = DummyRepoName
    fake_module.UnifiedErrorReporter = DummyReporter
    monkeypatch.setitem(sys.modules, "src.diagnostics.unified_error_reporter", fake_module)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_error_report(["error_report", "--sync"], paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "full"
    assert payload["report"]["scan_mode"] == "full"
    assert DummyReporter.scan_calls >= 1


def test_error_report_sync_mirrors_latest_artifacts_to_state_reports(monkeypatch, tmp_path, capsys):
    """Canonical latest error artifacts should be mirrored into state/reports."""
    import scripts.start_nusyq as start_nusyq

    class DummyRepoName(str, Enum):
        NUSYQ_HUB = "nusyq-hub"

    class DummyReporter:
        def __init__(self, hub_path=None, include_repos=None, exclude_repos=None, **_kw):
            _ = (hub_path, include_repos, exclude_repos)
            self.repos = {DummyRepoName.NUSYQ_HUB: tmp_path}
            self.reports_dir = tmp_path / "docs" / "Reports" / "diagnostics"
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            self.scans = {}
            self.scan_warnings: list[str] = []
            self.all_diagnostics: list[object] = []
            self.scan_mode = "quick"

        def load_cached_report(self, max_age_seconds=None):
            _ = max_age_seconds
            return None

        def scan_all_repos(self, quick=False):
            repo_key = next(iter(self.repos.keys()))
            self.scans[repo_key] = types.SimpleNamespace(diagnostics=[])
            return self.generate_unified_report()

        def generate_unified_report(self):
            return {
                "timestamp": datetime.now().isoformat(),
                "scan_mode": "quick",
                "total_diagnostics": 0,
                "by_severity": {"errors": 0, "warnings": 0, "infos_hints": 0},
                "by_repo": {
                    "nusyq-hub": {
                        "repo": "nusyq-hub",
                        "total": 0,
                        "by_severity": {},
                        "by_type": {},
                        "by_source": {},
                        "path": str(tmp_path),
                        "python_targets": 1,
                        "python_target_names": ["src"],
                    }
                },
                "targets": ["nusyq-hub"],
                "filters": {"include": ["nusyq-hub"], "exclude": []},
                "partial_scan": False,
                "scan_warnings": [],
            }

        def write_report(self):
            report_json = self.reports_dir / "unified_error_report_latest.json"
            report_md = self.reports_dir / "unified_error_report_latest.md"
            report_json.write_text(
                json.dumps(self.generate_unified_report(), indent=2), encoding="utf-8"
            )
            report_md.write_text("# report", encoding="utf-8")
            return {
                "json": str(report_json),
                "md": str(report_md),
                "latest_json": str(report_json),
                "latest_md": str(report_md),
            }

    fake_module = types.ModuleType("src.diagnostics.unified_error_reporter")
    fake_module.RepoName = DummyRepoName
    fake_module.UnifiedErrorReporter = DummyReporter
    monkeypatch.setitem(sys.modules, "src.diagnostics.unified_error_reporter", fake_module)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_error_report(
        ["error_report", "--quick", "--sync"], paths, json_mode=True
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    state_latest_json = tmp_path / "state" / "reports" / "unified_error_report_latest.json"
    state_latest_md = tmp_path / "state" / "reports" / "unified_error_report_latest.md"
    assert state_latest_json.exists()
    assert state_latest_md.exists()
    assert payload["outputs"]["state_latest_json"] == str(state_latest_json)
    assert payload["outputs"]["state_latest_md"] == str(state_latest_md)
    mirrored = json.loads(state_latest_json.read_text(encoding="utf-8"))
    assert mirrored["scan_mode"] == "quick"
    assert mirrored["targets"] == ["nusyq-hub"]


def test_prune_reports_dry_run_includes_diagnostics_history(monkeypatch, tmp_path, capsys):
    """prune_reports should account for docs/Reports/diagnostics unified error history."""
    import scripts.start_nusyq as start_nusyq

    state_reports = tmp_path / "state" / "reports"
    diagnostics_reports = tmp_path / "docs" / "Reports" / "diagnostics"
    state_reports.mkdir(parents=True, exist_ok=True)
    diagnostics_reports.mkdir(parents=True, exist_ok=True)

    for idx in range(25):
        (diagnostics_reports / f"unified_error_report_20260312_{idx:06d}.json").write_text(
            "{}", encoding="utf-8"
        )
        (diagnostics_reports / f"unified_error_report_20260312_{idx:06d}.md").write_text(
            "# report", encoding="utf-8"
        )
    (diagnostics_reports / "unified_error_report_latest.json").write_text("{}", encoding="utf-8")
    (diagnostics_reports / "unified_error_report_latest.md").write_text(
        "# latest", encoding="utf-8"
    )

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_prune_reports(["prune_reports", "--dry-run"], paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    patterns = {row["name"]: row for row in payload["patterns"]}
    assert patterns["diagnostics_unified_error_json"]["base_dir"] == str(diagnostics_reports)
    assert patterns["diagnostics_unified_error_md"]["base_dir"] == str(diagnostics_reports)
    assert patterns["diagnostics_unified_error_json"]["stale"] == 5
    assert patterns["diagnostics_unified_error_md"]["stale"] == 5
    assert payload["diagnostics_reports_dir"] == str(diagnostics_reports)


def test_prune_reports_dry_run_includes_state_report_history_families(tmp_path, capsys):
    """prune_reports should account for key state/report families beyond diagnostics."""
    import scripts.start_nusyq as start_nusyq

    state_reports = tmp_path / "state" / "reports"
    state_reports.mkdir(parents=True, exist_ok=True)

    for idx in range(25):
        (state_reports / f"openclaw_smoke_20260312_{idx:06d}.json").write_text(
            "{}", encoding="utf-8"
        )
        (state_reports / f"system_complete_checkpoint_20260312_{idx:06d}.json").write_text(
            "{}", encoding="utf-8"
        )
    for idx in range(35):
        (state_reports / f"doctrine_compliance_20260312_{idx:06d}.md").write_text(
            "# report", encoding="utf-8"
        )

    (state_reports / "openclaw_smoke_latest.json").write_text("{}", encoding="utf-8")
    (state_reports / "system_complete_checkpoint_latest.json").write_text("{}", encoding="utf-8")

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_prune_reports(["prune_reports", "--dry-run"], paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    patterns = {row["name"]: row for row in payload["patterns"]}
    assert patterns["openclaw_smoke"]["stale"] == 5
    assert patterns["system_complete_checkpoint"]["stale"] == 5
    assert patterns["doctrine_compliance"]["stale"] == 5


def test_prune_reports_execute_skips_error_refresh_by_default(monkeypatch, tmp_path, capsys):
    """prune_reports should avoid the expensive error_report refresh unless explicitly requested."""
    import scripts.start_nusyq as start_nusyq

    state_reports = tmp_path / "state" / "reports"
    state_reports.mkdir(parents=True, exist_ok=True)
    (state_reports / "doctrine_compliance_20260312_000001.md").write_text("# report", encoding="utf-8")
    (state_reports / "doctrine_compliance_20260312_000002.md").write_text("# report", encoding="utf-8")

    invoked: list[list[str]] = []

    def fake_run(cmd, cwd=None, timeout_s=10):
        _ = (cwd, timeout_s)
        invoked.append(list(cmd))
        return 0, "{}", ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    monkeypatch.setenv("NUSYQ_DOCTRINE_COMPLIANCE_HISTORY_KEEP", "1")

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_prune_reports(["prune_reports", "--execute"], paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["refresh_signals"] is True
    assert payload["refresh_error_report"] is False
    assert [row["name"] for row in payload["refresh_runs"]] == ["problem_signal_snapshot"]
    assert all("error_report" not in " ".join(cmd) for cmd in invoked)


def test_prune_reports_dry_run_includes_docs_and_agent_session_families(tmp_path, capsys):
    """prune_reports should account for docs report/session history families."""
    import scripts.start_nusyq as start_nusyq

    docs_reports = tmp_path / "docs" / "Reports"
    agent_sessions = tmp_path / "docs" / "Agent-Sessions"
    docs_reports.mkdir(parents=True, exist_ok=True)
    agent_sessions.mkdir(parents=True, exist_ok=True)

    for idx in range(65):
        (docs_reports / f"github_validation_20260312_{idx:06d}.md").write_text(
            "# report", encoding="utf-8"
        )
    for idx in range(70):
        (agent_sessions / f"GUILD_BOARD_SNAPSHOT_20260312_{idx:06d}.md").write_text(
            "# snapshot", encoding="utf-8"
        )
    for idx in range(7):
        (agent_sessions / f"commit_batch_20260312_{idx:06d}.json").write_text(
            "{}", encoding="utf-8"
        )

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_prune_reports(["prune_reports", "--dry-run"], paths, json_mode=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    patterns = {row["name"]: row for row in payload["patterns"]}
    assert patterns["docs_reports_github_validation"]["stale"] == 5
    assert patterns["agent_sessions_guild_board"]["stale"] == 10
    assert patterns["agent_sessions_commit_batch"]["stale"] == 2
    assert payload["docs_reports_dir"] == str(docs_reports)
    assert payload["agent_sessions_dir"] == str(agent_sessions)


def test_run_error_report_bridge_chain_test_mode_skips_error_quest(monkeypatch, tmp_path):
    """Bridge chain should execute signal stages and skip error_quest in test mode."""
    import scripts.start_nusyq as start_nusyq

    fake_error_signal = types.ModuleType("src.orchestration.error_signal_bridge")
    fake_signal_quest = types.ModuleType("src.orchestration.signal_quest_mapper")

    async def error_signal_cycle(test_mode=False):
        return {"signals_created": 2, "test_mode": test_mode}

    async def signal_quest_cycle(test_mode=False):
        return {"quests_created": 1, "test_mode": test_mode}

    fake_error_signal.bridge_cycle = error_signal_cycle
    fake_signal_quest.bridge_cycle = signal_quest_cycle
    monkeypatch.setitem(sys.modules, "src.orchestration.error_signal_bridge", fake_error_signal)
    monkeypatch.setitem(sys.modules, "src.orchestration.signal_quest_mapper", fake_signal_quest)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    options = start_nusyq.ErrorReportOptions(
        bridge_signals=True,
        bridge_signal_to_quest=True,
        bridge_error_quests=True,
        bridge_test_mode=True,
    )

    chain = start_nusyq._run_error_report_bridge_chain(paths, options)
    assert chain["enabled"] is True
    assert chain["status"] == "ok"
    stage_names = [stage["name"] for stage in chain["stages"]]
    assert stage_names == [
        "error_signal_bridge",
        "signal_quest_bridge",
        "error_quest_bridge",
    ]
    assert chain["stages"][2]["status"] == "skipped"


def test_run_error_report_bridge_chain_prefers_existing_report_artifact(monkeypatch, tmp_path):
    """Bridge chain should reuse current report artifact when bridge supports it."""
    import scripts.start_nusyq as start_nusyq

    fake_error_signal = types.ModuleType("src.orchestration.error_signal_bridge")
    called = {"report_path": None, "test_mode": None}

    async def bridge_from_report(report_path, test_mode=False):
        called["report_path"] = str(report_path)
        called["test_mode"] = test_mode
        return {"signals_created": 1, "report_path": str(report_path), "test_mode": test_mode}

    fake_error_signal.bridge_from_report = bridge_from_report
    fake_error_signal.bridge_cycle = bridge_from_report
    monkeypatch.setitem(sys.modules, "src.orchestration.error_signal_bridge", fake_error_signal)
    # Also patch the package attribute: CPython _handle_fromlist skips sys.modules lookup if the
    # package already has the attribute set (from a prior import in the full suite).
    import src.orchestration as _orch_pkg

    monkeypatch.setattr(_orch_pkg, "error_signal_bridge", fake_error_signal, raising=False)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    options = start_nusyq.ErrorReportOptions(bridge_signals=True, bridge_test_mode=False)
    report_path = str(tmp_path / "state" / "reports" / "unified_error_report_latest.json")

    chain = start_nusyq._run_error_report_bridge_chain(paths, options, report_path)
    assert chain["enabled"] is True
    assert chain["status"] == "ok"
    assert called["report_path"] == report_path
    assert called["test_mode"] is False


def test_run_error_report_bridge_chain_invalid_severity(monkeypatch, tmp_path):
    """Invalid error_quest severity should mark chain partial/error with stage details."""
    import scripts.start_nusyq as start_nusyq

    fake_error_quest = types.ModuleType("src.integration.error_quest_bridge")

    class ErrorSeverity(Enum):
        ERROR = "error"
        WARNING = "warning"

    class ErrorQuestBridge:
        def get_error_quest_stats(self):
            return {}

    def auto_generate_error_quests(severity, max_quests, report_path=None):
        return {"quests_created": 0}

    fake_error_quest.ErrorSeverity = ErrorSeverity
    fake_error_quest.ErrorQuestBridge = ErrorQuestBridge
    fake_error_quest.auto_generate_error_quests = auto_generate_error_quests
    monkeypatch.setitem(sys.modules, "src.integration.error_quest_bridge", fake_error_quest)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    options = start_nusyq.ErrorReportOptions(
        bridge_error_quests=True,
        bridge_severity="invalid",
    )

    chain = start_nusyq._run_error_report_bridge_chain(paths, options)
    assert chain["enabled"] is True
    assert chain["status"] == "error"
    assert chain["errors"]
    assert chain["stages"][0]["name"] == "error_quest_bridge"
    assert chain["stages"][0]["status"] == "error"


def test_run_error_report_bridge_chain_passes_report_path_to_error_quest(monkeypatch, tmp_path):
    """Bridge chain should forward report artifact path to error_quest bridge."""
    import scripts.start_nusyq as start_nusyq

    fake_error_quest = types.ModuleType("src.integration.error_quest_bridge")
    captured: dict[str, object] = {"report_path": None}

    class ErrorSeverity(Enum):
        ERROR = "error"

    class ErrorQuestBridge:
        def get_error_quest_stats(self):
            return {"total_error_quests": 0}

    def auto_generate_error_quests(severity, max_quests, report_path=None):
        captured["report_path"] = report_path
        captured["severity"] = severity.value
        captured["max_quests"] = max_quests
        return {"quests_created": 0}

    fake_error_quest.ErrorSeverity = ErrorSeverity
    fake_error_quest.ErrorQuestBridge = ErrorQuestBridge
    fake_error_quest.auto_generate_error_quests = auto_generate_error_quests
    monkeypatch.setitem(sys.modules, "src.integration.error_quest_bridge", fake_error_quest)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    options = start_nusyq.ErrorReportOptions(
        bridge_error_quests=True,
        bridge_severity="error",
        bridge_max_quests=3,
    )
    report_path = str(
        tmp_path / "docs" / "Reports" / "diagnostics" / "unified_error_report_latest.json"
    )

    chain = start_nusyq._run_error_report_bridge_chain(paths, options, report_path)
    assert chain["enabled"] is True
    assert chain["status"] == "ok"
    assert str(captured["report_path"]) == report_path
    assert captured["severity"] == "error"
    assert captured["max_quests"] == 3


def test_error_report_status_json(monkeypatch, tmp_path, capsys):
    """error_report_status should emit structured job payload in json mode."""
    import scripts.start_nusyq as start_nusyq

    def fake_refresh(_paths, _job_id):
        return {
            "job_id": "error_report_20260217_abcd1234",
            "job_type": "error_report",
            "status": "completed",
            "pid": 4242,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        }

    monkeypatch.setattr(start_nusyq, "_refresh_job_status", fake_refresh)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_error_report_status(
        ["error_report_status", "error_report_20260217_abcd1234"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = capsys.readouterr().out
    assert '"action": "error_report_status"' in payload
    assert '"status": "completed"' in payload


def test_error_report_status_json_includes_checkpoint(monkeypatch, tmp_path, capsys):
    """error_report_status should include checkpoint summary when available."""
    import scripts.start_nusyq as start_nusyq

    checkpoint_path = tmp_path / "state" / "reports" / "error_report_checkpoint_latest.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        json.dumps(
            {
                "status": "running",
                "current_check": "scan_nusyq-hub",
                "completed_checks": 3,
                "total_planned": 8,
                "checks": [
                    {"name": "parse_options", "passed": True},
                    {"name": "cache_lookup", "passed": True},
                    {"name": "scan_nusyq-hub", "passed": False, "skipped": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_refresh(_paths, _job_id):
        return {
            "job_id": "error_report_20260218_abcd1234",
            "job_type": "error_report",
            "status": "running",
            "pid": 4242,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
            "metadata": {"checkpoint_file": str(checkpoint_path)},
        }

    monkeypatch.setattr(start_nusyq, "_refresh_job_status", fake_refresh)
    monkeypatch.setattr(start_nusyq, "_reconcile_jobs", lambda *_args, **_kwargs: {})
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_error_report_status(
        ["error_report_status", "error_report_20260218_abcd1234"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = capsys.readouterr().out
    assert '"action": "error_report_status"' in payload
    assert '"checkpoint"' in payload
    assert '"completed_checks": 3' in payload


def test_doctor_async_submits_background_job(monkeypatch, tmp_path, capsys):
    """Doctor --async should submit job and avoid synchronous execution."""
    import scripts.start_nusyq as start_nusyq

    captured: dict[str, object] = {}

    def fake_start_job(paths, job_type, command, cwd=None, metadata=None):
        captured["paths"] = paths
        captured["job_type"] = job_type
        captured["command"] = list(command)
        captured["cwd"] = cwd
        captured["metadata"] = metadata or {}
        return {
            "job_id": "doctor_20260218_abcd1234",
            "pid": 7777,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        }

    monkeypatch.setattr(start_nusyq, "_start_subprocess_job", fake_start_job)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_doctor_action(["doctor", "--quick", "--async"], paths, json_mode=True)
    assert rc == 0
    assert captured["job_type"] == "doctor"
    assert captured["command"] == [
        sys.executable,
        "scripts/start_nusyq.py",
        "doctor",
        "--sync",
        "--json",
        "--quick",
    ]
    metadata = captured["metadata"]
    assert isinstance(metadata, dict)
    assert metadata.get("checkpoint_file")
    payload = capsys.readouterr().out
    assert '"action": "doctor"' in payload
    assert '"status": "submitted"' in payload


def test_doctor_status_json_includes_checkpoint(monkeypatch, tmp_path, capsys):
    """doctor_status should include checkpoint summary when available."""
    import scripts.start_nusyq as start_nusyq

    checkpoint_path = tmp_path / "state" / "reports" / "doctor_checkpoint_latest.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        json.dumps(
            {
                "status": "running",
                "current_check": "lint_test_diagnostic",
                "completed_checks": 2,
                "total_planned": 3,
                "checks": [
                    {"name": "system_health", "passed": True},
                    {"name": "quick_system_analyzer", "passed": False, "skipped": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_refresh(_paths, _job_id):
        return {
            "job_id": "doctor_20260218_abcd1234",
            "job_type": "doctor",
            "status": "running",
            "pid": 7777,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
            "metadata": {"checkpoint_file": str(checkpoint_path)},
        }

    monkeypatch.setattr(start_nusyq, "_refresh_job_status", fake_refresh)
    monkeypatch.setattr(start_nusyq, "_reconcile_jobs", lambda *_args, **_kwargs: {})
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_doctor_status(
        ["doctor_status", "doctor_20260218_abcd1234"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = capsys.readouterr().out
    assert '"action": "doctor_status"' in payload
    assert '"checkpoint"' in payload
    assert '"completed_checks": 2' in payload


def test_status_action_retry_submits_new_job(monkeypatch, tmp_path, capsys):
    """Status actions should support --retry using the original command payload."""
    import scripts.start_nusyq as start_nusyq

    existing_job = {
        "job_id": "error_report_old",
        "job_type": "error_report",
        "status": "failed",
        "pid": 999,
        "command": [sys.executable, "scripts/start_nusyq.py", "error_report", "--sync", "--json"],
        "cwd": str(tmp_path),
        "metadata": {"action": "error_report"},
    }
    submitted: dict[str, object] = {}

    def fake_start_job(paths, job_type, command, cwd=None, metadata=None):
        submitted["job_type"] = job_type
        submitted["command"] = list(command)
        submitted["cwd"] = str(cwd) if cwd else ""
        submitted["metadata"] = metadata or {}
        return {
            "job_id": "error_report_new",
            "pid": 4242,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        }

    monkeypatch.setattr(start_nusyq, "_read_job", lambda _paths, _job_id: existing_job)
    monkeypatch.setattr(start_nusyq, "_start_subprocess_job", fake_start_job)
    monkeypatch.setattr(start_nusyq, "_reconcile_jobs", lambda *_args, **_kwargs: {})

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_error_report_status(
        ["error_report_status", "error_report_old", "--retry"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    assert submitted["job_type"] == "error_report"
    assert submitted["command"] == existing_job["command"]
    metadata = submitted["metadata"]
    assert isinstance(metadata, dict)
    assert metadata.get("retry_of") == "error_report_old"
    payload = capsys.readouterr().out
    assert '"status": "submitted"' in payload
    assert '"retry_of": "error_report_old"' in payload


def test_status_action_cancel_marks_job_canceled(monkeypatch, tmp_path, capsys):
    """Status actions should support --cancel and persist canceled job state."""
    import scripts.start_nusyq as start_nusyq

    stored: dict[str, object] = {}
    existing_job = {
        "job_id": "doctor_old",
        "job_type": "doctor",
        "status": "running",
        "pid": 5151,
        "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
        "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
    }

    def fake_write_job(_paths, payload):
        stored["payload"] = payload
        return tmp_path / "state" / "jobs" / "doctor_old.json"

    monkeypatch.setattr(start_nusyq, "_read_job", lambda _paths, _job_id: dict(existing_job))
    monkeypatch.setattr(start_nusyq, "_write_job", fake_write_job)
    monkeypatch.setattr(start_nusyq, "_terminate_job_process", lambda _pid: True)
    monkeypatch.setattr(start_nusyq, "_reconcile_jobs", lambda *_args, **_kwargs: {})

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_doctor_status(
        ["doctor_status", "doctor_old", "--cancel"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = capsys.readouterr().out
    assert '"action": "doctor_status"' in payload
    assert '"status": "canceled"' in payload
    persisted = stored.get("payload")
    assert isinstance(persisted, dict)
    assert persisted.get("status") == "canceled"
    assert persisted.get("cancel_succeeded") is True


def test_openclaw_smoke_async_submits_background_job(monkeypatch, tmp_path, capsys):
    """openclaw_smoke --async should submit a background smoke job."""
    import scripts.start_nusyq as start_nusyq

    captured: dict[str, object] = {}

    def fake_start_job(paths, job_type, command, cwd=None, metadata=None):
        captured["paths"] = paths
        captured["job_type"] = job_type
        captured["command"] = list(command)
        captured["cwd"] = cwd
        captured["metadata"] = metadata or {}
        return {
            "job_id": "openclaw_smoke_20260218_abcd1234",
            "pid": 8181,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        }

    monkeypatch.setattr(start_nusyq, "_start_subprocess_job", fake_start_job)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_openclaw_smoke(
        ["openclaw_smoke", "--async", "--help-timeout-s=7", "--max-help-runtime-s=2"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    assert captured["job_type"] == "openclaw_smoke"
    command = captured["command"]
    assert isinstance(command, list)
    assert command[:4] == [sys.executable, "scripts/start_nusyq.py", "openclaw_smoke", "--sync"]
    assert "--json" in command
    assert any(token.startswith("--help-timeout-s=") for token in command)
    assert any(token.startswith("--max-help-runtime-s=") for token in command)
    metadata = captured["metadata"]
    assert isinstance(metadata, dict)
    assert metadata.get("checkpoint_file")
    payload = capsys.readouterr().out
    assert '"action": "openclaw_smoke"' in payload
    assert '"status": "submitted"' in payload


def test_openclaw_smoke_status_json_includes_checkpoint(monkeypatch, tmp_path, capsys):
    """openclaw_smoke_status should include checkpoint summary when available."""
    import scripts.start_nusyq as start_nusyq

    checkpoint_path = tmp_path / "state" / "reports" / "openclaw_smoke_latest.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        json.dumps(
            {
                "status": "ok",
                "summary": {"passed": 5, "total": 5},
                "checks": [
                    {"name": "Gateway Bridge Import", "passed": True},
                    {"name": "Main CLI Flags", "passed": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_refresh(_paths, _job_id):
        return {
            "job_id": "openclaw_smoke_20260218_abcd1234",
            "job_type": "openclaw_smoke",
            "status": "completed",
            "pid": 8181,
            "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
            "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
            "metadata": {"checkpoint_file": str(checkpoint_path)},
        }

    monkeypatch.setattr(start_nusyq, "_refresh_job_status", fake_refresh)
    monkeypatch.setattr(start_nusyq, "_reconcile_jobs", lambda *_args, **_kwargs: {})
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_openclaw_smoke_status(
        ["openclaw_smoke_status", "openclaw_smoke_20260218_abcd1234"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = capsys.readouterr().out
    assert '"action": "openclaw_smoke_status"' in payload
    assert '"checkpoint"' in payload


def test_openclaw_smoke_sync_json_wraps_script_payload(monkeypatch, tmp_path, capsys):
    """openclaw_smoke sync should wrap script JSON output in action payload."""
    import scripts.start_nusyq as start_nusyq

    script_payload = {
        "action": "openclaw_smoke",
        "status": "ok",
        "summary": {"passed": 5, "total": 5},
    }

    def fake_run(_cmd, cwd=None, timeout_s=10):
        return 0, json.dumps(script_payload), ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_openclaw_smoke(["openclaw_smoke", "--sync"], paths, json_mode=True)
    assert rc == 0
    payload = capsys.readouterr().out
    assert '"action": "openclaw_smoke"' in payload
    assert '"status": "ok"' in payload
    assert '"result"' in payload


def test_doctor_budget_enforces_step_skips_and_checkpoint(monkeypatch, tmp_path, capsys):
    """Doctor --budget-s should skip remaining heavy steps once budget is exhausted."""
    import scripts.start_nusyq as start_nusyq

    def fake_run(cmd, cwd=None, timeout_s=10):
        script = cmd[1] if len(cmd) > 1 else ""
        if script.endswith("quick_system_analyzer.py"):
            time.sleep(1.1)
            return 0, "analyzer ok", ""
        if script.endswith("lint_test_check.py"):
            return 0, "lint ok", ""
        return 0, "", ""

    monkeypatch.setattr(start_nusyq, "run", fake_run)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_doctor_action(
        ["doctor", "--sync", "--with-analyzer", "--with-lint", "--budget-s=1"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "doctor"
    assert payload["options"]["budget_s"] == 1
    assert payload["status"] == "degraded"
    assert payload["checkpoint_file"].endswith("doctor_checkpoint_latest.json")
    lint_step = next(step for step in payload["steps"] if step["name"] == "lint_test_diagnostic")
    assert lint_step.get("skipped") is True
    assert lint_step.get("reason") == "budget_exceeded"


def test_refresh_job_status_reads_rc_file(monkeypatch, tmp_path):
    """Background job status should honor persisted exit code file."""
    import scripts.start_nusyq as start_nusyq

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc_file = tmp_path / "state" / "jobs" / "error_report_unit.rc"
    rc_file.parent.mkdir(parents=True, exist_ok=True)
    rc_file.write_text("7", encoding="utf-8")

    payload = {
        "job_id": "error_report_unit",
        "job_type": "error_report",
        "status": "running",
        "pid": 43210,
        "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
        "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        "rc_file": str(rc_file),
    }
    start_nusyq._write_job(paths, payload)

    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: False)
    refreshed = start_nusyq._refresh_job_status(paths, "error_report_unit")

    assert isinstance(refreshed, dict)
    assert refreshed["rc"] == 7
    assert refreshed["status"] == "failed"


def test_refresh_job_status_marks_unknown_when_rc_missing(monkeypatch, tmp_path):
    """If rc_file is declared but absent, status should be unknown (not completed)."""
    import scripts.start_nusyq as start_nusyq

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    missing_rc_file = tmp_path / "state" / "jobs" / "missing.rc"
    payload = {
        "job_id": "error_report_missing_rc",
        "job_type": "error_report",
        "status": "running",
        "pid": 54321,
        "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
        "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        "rc_file": str(missing_rc_file),
    }
    start_nusyq._write_job(paths, payload)

    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: False)
    refreshed = start_nusyq._refresh_job_status(paths, "error_report_missing_rc")

    assert isinstance(refreshed, dict)
    assert refreshed["status"] == "unknown"
    assert refreshed.get("rc") is None


def test_refresh_job_status_marks_failed_when_rc_missing_and_no_artifacts(monkeypatch, tmp_path):
    """Stale checkpoint + missing rc + empty logs should be a deterministic failure."""
    import scripts.start_nusyq as start_nusyq

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    checkpoint_file = tmp_path / "state" / "reports" / "error_report_checkpoint_latest.json"
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_file.write_text(
        json.dumps(
            {
                "status": "running",
                "updated_at": "2026-01-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )

    stdout_log = tmp_path / "state" / "jobs" / "stdout.log"
    stderr_log = tmp_path / "state" / "jobs" / "stderr.log"
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stdout_log.write_text("", encoding="utf-8")
    stderr_log.write_text("", encoding="utf-8")

    missing_rc_file = tmp_path / "state" / "jobs" / "missing.rc"
    payload = {
        "job_id": "error_report_missing_artifacts",
        "job_type": "error_report",
        "status": "running",
        "pid": 54322,
        "started_at": "2026-02-01T00:00:00",
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
        "rc_file": str(missing_rc_file),
        "metadata": {"checkpoint_file": str(checkpoint_file)},
    }
    start_nusyq._write_job(paths, payload)

    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: False)
    refreshed = start_nusyq._refresh_job_status(paths, "error_report_missing_artifacts")

    assert isinstance(refreshed, dict)
    assert refreshed["status"] == "failed"
    assert refreshed["rc"] == 1
    assert refreshed["failure_reason"] == "missing_rc_and_no_artifacts"


def test_refresh_job_status_uses_checkpoint_when_rc_missing(monkeypatch, tmp_path):
    """Missing rc file can be reconciled from checkpoint completion state."""
    import scripts.start_nusyq as start_nusyq

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    checkpoint_file = tmp_path / "state" / "reports" / "error_report_checkpoint_latest.json"
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_file.write_text(json.dumps({"status": "completed"}), encoding="utf-8")

    missing_rc_file = tmp_path / "state" / "jobs" / "missing.rc"
    payload = {
        "job_id": "error_report_missing_rc_checkpoint",
        "job_type": "error_report",
        "status": "running",
        "pid": 65432,
        "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
        "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        "rc_file": str(missing_rc_file),
        "metadata": {"checkpoint_file": str(checkpoint_file)},
    }
    start_nusyq._write_job(paths, payload)

    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: False)
    refreshed = start_nusyq._refresh_job_status(paths, "error_report_missing_rc_checkpoint")

    assert isinstance(refreshed, dict)
    assert refreshed["status"] == "completed"
    assert refreshed["rc"] == 0


def test_refresh_job_status_uses_stdout_payload_when_checkpoint_stale(monkeypatch, tmp_path):
    """When checkpoint is stale, status should be inferred from stdout JSON payload."""
    import scripts.start_nusyq as start_nusyq

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    checkpoint_file = tmp_path / "state" / "reports" / "error_report_checkpoint_latest.json"
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_file.write_text(json.dumps({"status": "running"}), encoding="utf-8")

    stdout_log = tmp_path / "state" / "jobs" / "stdout.log"
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stdout_log.write_text(
        "\n".join(
            [
                "spine prelude",
                json.dumps({"action": "error_report", "status": "completed"}),
            ]
        ),
        encoding="utf-8",
    )

    missing_rc_file = tmp_path / "state" / "jobs" / "missing.rc"
    payload = {
        "job_id": "error_report_missing_rc_stdout",
        "job_type": "error_report",
        "status": "running",
        "pid": 65433,
        "stdout_log": str(stdout_log),
        "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        "rc_file": str(missing_rc_file),
        "metadata": {"checkpoint_file": str(checkpoint_file)},
    }
    start_nusyq._write_job(paths, payload)

    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: False)
    refreshed = start_nusyq._refresh_job_status(paths, "error_report_missing_rc_stdout")

    assert isinstance(refreshed, dict)
    assert refreshed["status"] == "completed"
    assert refreshed["rc"] == 0


def test_refresh_job_status_ignores_stale_checkpoint_completion(monkeypatch, tmp_path):
    """Completed checkpoints older than job start should not force a false completion."""
    import scripts.start_nusyq as start_nusyq

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    checkpoint_file = tmp_path / "state" / "reports" / "error_report_checkpoint_latest.json"
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_file.write_text(
        json.dumps({"status": "completed", "updated_at": "2026-01-01T00:00:00"}),
        encoding="utf-8",
    )

    stdout_log = tmp_path / "state" / "jobs" / "stdout.log"
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stdout_log.write_text(
        json.dumps({"action": "error_report", "status": "error"}),
        encoding="utf-8",
    )
    missing_rc_file = tmp_path / "state" / "jobs" / "missing.rc"
    payload = {
        "job_id": "error_report_stale_checkpoint",
        "job_type": "error_report",
        "status": "running",
        "pid": 76543,
        "started_at": "2026-02-20T00:00:00",
        "stdout_log": str(stdout_log),
        "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        "rc_file": str(missing_rc_file),
        "metadata": {"checkpoint_file": str(checkpoint_file)},
    }
    start_nusyq._write_job(paths, payload)

    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: False)
    refreshed = start_nusyq._refresh_job_status(paths, "error_report_stale_checkpoint")

    assert isinstance(refreshed, dict)
    assert refreshed["status"] == "failed"
    assert refreshed["rc"] == 1


def test_refresh_job_status_treats_partial_checkpoint_as_completed(monkeypatch, tmp_path):
    """Partial checkpoints should be treated as completed-with-warnings, not failed."""
    import scripts.start_nusyq as start_nusyq

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    checkpoint_file = tmp_path / "state" / "reports" / "error_report_checkpoint_latest.json"
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_file.write_text(
        json.dumps({"status": "partial", "updated_at": "2026-02-20T00:00:10"}),
        encoding="utf-8",
    )

    payload = {
        "job_id": "error_report_partial_checkpoint",
        "job_type": "error_report",
        "status": "running",
        "pid": 80001,
        "started_at": "2026-02-20T00:00:00",
        "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
        "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        "rc_file": str(tmp_path / "state" / "jobs" / "missing.rc"),
        "metadata": {"checkpoint_file": str(checkpoint_file)},
    }
    start_nusyq._write_job(paths, payload)

    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: False)
    refreshed = start_nusyq._refresh_job_status(paths, "error_report_partial_checkpoint")

    assert isinstance(refreshed, dict)
    assert refreshed["status"] == "completed"
    assert refreshed["rc"] == 0


def test_write_job_exit_code_from_env(monkeypatch, tmp_path):
    """Helper should persist exit code when rc-file env is set."""
    import scripts.start_nusyq as start_nusyq

    rc_file = tmp_path / "state" / "jobs" / "helper.rc"
    monkeypatch.setenv("NUSYQ_JOB_RC_FILE", str(rc_file))

    start_nusyq._write_job_exit_code_from_env(9)

    assert rc_file.exists()
    assert rc_file.read_text(encoding="utf-8") == "9"


def test_start_subprocess_job_sets_job_env(monkeypatch, tmp_path):
    """Background launcher should pass job id/rc file env vars to subprocess."""
    import scripts.start_nusyq as start_nusyq

    captured: dict[str, object] = {}

    class DummyProc:
        pid = 12345

    def fake_popen(
        cmd, cwd=None, stdout=None, stderr=None, text=None, env=None
    ):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["text"] = text
        captured["env"] = env or {}
        return DummyProc()

    monkeypatch.setattr(start_nusyq.subprocess, "Popen", fake_popen)
    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    payload = start_nusyq._start_subprocess_job(
        paths,
        job_type="unit_job",
        command=[sys.executable, "-c", "print('ok')"],
        cwd=tmp_path,
    )

    assert payload["job_id"].startswith("unit_job_")
    env = captured["env"]
    assert isinstance(env, dict)
    assert env["NUSYQ_JOB_ID"] == payload["job_id"]
    assert env["NUSYQ_JOB_RC_FILE"] == payload["rc_file"]


def test_reconcile_jobs_expires_old_unknown(monkeypatch, tmp_path):
    """Unknown jobs older than threshold should be marked expired."""
    import scripts.start_nusyq as start_nusyq

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    stale = {
        "job_id": "error_report_old_unknown",
        "job_type": "error_report",
        "status": "unknown",
        "pid": 99999,
        "started_at": "2026-01-01T00:00:00",
        "finished_at": "2026-01-01T00:10:00",
        "stdout_log": str(tmp_path / "state" / "jobs" / "stdout.log"),
        "stderr_log": str(tmp_path / "state" / "jobs" / "stderr.log"),
        "rc_file": str(tmp_path / "state" / "jobs" / "missing.rc"),
    }
    start_nusyq._write_job(paths, stale)

    monkeypatch.setattr(start_nusyq, "_is_process_running", lambda _pid: False)
    summary = start_nusyq._reconcile_jobs(paths, job_type="error_report", expire_hours=1)
    assert summary["expired"] >= 1

    refreshed = start_nusyq._read_job(paths, "error_report_old_unknown")
    assert isinstance(refreshed, dict)
    assert refreshed["status"] == "expired"


def test_parse_bridge_run_args_supports_mode_and_interval():
    """Bridge mode parser should parse --mode and --interval flags."""
    import scripts.start_nusyq as start_nusyq

    opts = start_nusyq._parse_bridge_run_args(
        ["error_signal_bridge", "--mode=test", "--interval=15"],
        "error_signal_bridge",
    )
    assert opts.mode == "test"
    assert opts.interval_s == 15


def test_error_signal_bridge_json_handler(monkeypatch, tmp_path, capsys):
    """error_signal_bridge should return structured JSON and persist latest report."""
    import scripts.start_nusyq as start_nusyq

    fake_module = types.ModuleType("src.orchestration.error_signal_bridge")

    async def bridge_cycle(test_mode=False):
        return {
            "error_groups_found": 2,
            "signals_created": 2,
            "signals_posted": 2 if not test_mode else 0,
        }

    async def bridge_from_report(report_path, test_mode=False):
        return {
            "error_groups_found": 2,
            "signals_created": 2,
            "signals_posted": 2 if not test_mode else 0,
        }

    async def watch_mode(interval=60):
        return None

    fake_module.bridge_cycle = bridge_cycle
    fake_module.bridge_from_report = bridge_from_report
    fake_module.watch_mode = watch_mode
    monkeypatch.setitem(sys.modules, "src.orchestration.error_signal_bridge", fake_module)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_error_signal_bridge(
        ["error_signal_bridge", "--mode=test"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "error_signal_bridge"
    assert payload["status"] == "ok"
    assert payload["result"]["error_groups_found"] == 2
    assert Path(payload["report_file"]).exists()


def test_signal_quest_bridge_json_handler(monkeypatch, tmp_path, capsys):
    """signal_quest_bridge should return structured JSON and persist latest report."""
    import scripts.start_nusyq as start_nusyq

    fake_module = types.ModuleType("src.orchestration.signal_quest_mapper")

    async def bridge_cycle(test_mode=False):
        return {"signals_found": 3, "quests_created": 2, "test_mode": test_mode}

    async def watch_mode(interval=60):
        return None

    fake_module.bridge_cycle = bridge_cycle
    fake_module.watch_mode = watch_mode
    monkeypatch.setitem(sys.modules, "src.orchestration.signal_quest_mapper", fake_module)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_signal_quest_bridge(
        ["signal_quest_bridge", "--mode=once"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "signal_quest_bridge"
    assert payload["result"]["quests_created"] == 2
    assert Path(payload["report_file"]).exists()


def test_error_quest_bridge_json_handler_and_alias(monkeypatch, tmp_path, capsys):
    """error_quest_bridge and auto_quest alias should emit structured payload."""
    import scripts.start_nusyq as start_nusyq

    fake_module = types.ModuleType("src.integration.error_quest_bridge")

    class ErrorSeverity(Enum):
        ERROR = "error"
        WARNING = "warning"
        INFO = "info"

    class ErrorQuestBridge:
        def get_error_quest_stats(self):
            return {"total_error_quests": 4}

    def auto_generate_error_quests(severity, max_quests, report_path=None):
        return {
            "total_errors_found": 12,
            "quests_created": min(2, max_quests),
            "severity_threshold": severity.value,
        }

    fake_module.ErrorSeverity = ErrorSeverity
    fake_module.ErrorQuestBridge = ErrorQuestBridge
    fake_module.auto_generate_error_quests = auto_generate_error_quests
    monkeypatch.setitem(sys.modules, "src.integration.error_quest_bridge", fake_module)

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )

    rc = start_nusyq._handle_error_quest_bridge(
        ["error_quest_bridge", "--severity=warning", "--max-quests=3"],
        paths,
        json_mode=True,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "error_quest_bridge"
    assert payload["severity"] == "warning"
    assert payload["result"]["quests_created"] == 2
    assert payload["alias_used"] is False

    rc_alias = start_nusyq._handle_error_quest_bridge(
        ["auto_quest", "--severity=error", "--max-quests=1"],
        paths,
        json_mode=True,
    )
    assert rc_alias == 0
    alias_payload = json.loads(capsys.readouterr().out)
    assert alias_payload["alias_used"] is True
    assert Path(alias_payload["report_file"]).exists()


def test_compact_signal_open_quest_duplicates_closes_older_entries(tmp_path):
    """Compaction should close older duplicate open signal quests and keep newest."""
    import scripts.start_nusyq as start_nusyq

    quest_log = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    report_dir = tmp_path / "state" / "reports"
    quest_log.parent.mkdir(parents=True, exist_ok=True)

    entries = [
        {
            "id": "quest_old",
            "timestamp": "2026-02-18T00:00:00",
            "title": "Fix 50 ruff linting issues",
            "status": "open",
            "signal_id": "sig-old",
        },
        {
            "id": "quest_new",
            "timestamp": "2026-02-18T01:00:00",
            "title": "Fix 50 ruff linting issues",
            "status": "open",
            "signal_id": "sig-new",
        },
        {
            "id": "quest_other",
            "timestamp": "2026-02-18T02:00:00",
            "title": "Fix mypy issues",
            "status": "open",
            "signal_id": "sig-mypy",
        },
    ]
    quest_log.write_text("\n".join(json.dumps(row) for row in entries) + "\n", encoding="utf-8")

    result = start_nusyq._compact_signal_open_quest_duplicates(
        quest_log_path=quest_log,
        report_dir=report_dir,
        dry_run=False,
    )
    assert result["status"] == "ok"
    assert result["groups_compacted"] == 1
    assert result["duplicates_closed"] == 1
    assert result["duplicate_titles_after"] == {}
    assert result["backup_file"] is not None
    assert Path(result["backup_file"]).exists()

    updated_rows = [json.loads(line) for line in quest_log.read_text(encoding="utf-8").splitlines()]
    by_id = {row["id"]: row for row in updated_rows}
    assert by_id["quest_new"]["status"] == "open"
    assert by_id["quest_old"]["status"] == "closed"
    assert by_id["quest_old"]["superseded_by"] == "quest_new"
    assert by_id["quest_old"]["closed_reason"] == "deduplicated_open_signal_quest"


def test_main_error_report_uses_repo_discovery(monkeypatch):
    """Main dispatcher should discover all repos for error_report fast-path."""
    import scripts.start_nusyq as start_nusyq

    captured: dict[str, object] = {}

    def fake_load_paths(hub_default, allow_discovery=True):
        captured["allow_discovery"] = allow_discovery
        return start_nusyq.WorkspacePaths(
            nusyq_hub=Path("/tmp/hub"),
            simulatedverse=Path("/tmp/simverse"),
            nusyq_root=Path("/tmp/nusyq"),
        )

    def fake_handle_error_report(args, paths, json_mode=False):
        captured["paths"] = paths
        captured["json_mode"] = json_mode
        captured["args"] = list(args)
        return 0

    monkeypatch.setattr(start_nusyq, "initialize_spine", None)
    monkeypatch.setattr(start_nusyq, "emit_terminal_route", lambda _action: None)
    monkeypatch.setattr(start_nusyq, "load_paths", fake_load_paths)
    monkeypatch.setattr(start_nusyq, "_handle_error_report", fake_handle_error_report)
    monkeypatch.setattr(
        start_nusyq.sys, "argv", ["start_nusyq.py", "error_report", "--quick", "--json"]
    )

    rc = start_nusyq.main()
    assert rc == 0
    assert captured["allow_discovery"] is True
    paths = captured["paths"]
    assert isinstance(paths, start_nusyq.WorkspacePaths)
    assert paths.simulatedverse is not None
    assert paths.nusyq_root is not None
    assert captured["json_mode"] is True


def test_quest_compact_json_handler_dry_run(tmp_path, capsys):
    """quest_compact dry-run should report compaction plan without mutating quest log."""
    import scripts.start_nusyq as start_nusyq

    quest_log = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    quest_log.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "id": "quest_a",
            "timestamp": "2026-02-18T00:00:00",
            "title": "Fix 50 ruff linting issues",
            "status": "open",
            "signal_id": "sig-a",
        },
        {
            "id": "quest_b",
            "timestamp": "2026-02-18T01:00:00",
            "title": "Fix 50 ruff linting issues",
            "status": "open",
            "signal_id": "sig-b",
        },
    ]
    quest_log.write_text("\n".join(json.dumps(row) for row in entries) + "\n", encoding="utf-8")
    original_content = quest_log.read_text(encoding="utf-8")

    paths = start_nusyq.WorkspacePaths(
        nusyq_hub=tmp_path,
        simulatedverse=None,
        nusyq_root=None,
    )
    rc = start_nusyq._handle_quest_compact(["quest_compact", "--dry-run"], paths, json_mode=True)
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "quest_compact"
    assert payload["status"] == "ok"
    assert payload["result"]["dry_run"] is True
    assert payload["result"]["duplicates_closed"] == 1
    assert payload["result"]["backup_file"] is None
    assert Path(payload["report_file"]).exists()
    assert quest_log.read_text(encoding="utf-8") == original_content


def test_write_json_report_serializes_paths(tmp_path):
    """_write_json_report should handle Path objects in nested payloads."""
    import scripts.start_nusyq as start_nusyq

    report_path = tmp_path / "state" / "reports" / "sample.json"
    payload = {"path": tmp_path / "src" / "example.py", "items": [{"target": tmp_path / "tests"}]}

    start_nusyq._write_json_report(report_path, payload)

    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["path"].endswith("example.py")
    assert data["items"][0]["target"].endswith("tests")

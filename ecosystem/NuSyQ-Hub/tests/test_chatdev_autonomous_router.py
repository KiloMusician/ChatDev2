"""Tests for src/orchestration/chatdev_autonomous_router.py.

All imports are inside test functions to avoid module-level side effects.
Uses unittest.mock.patch to stub subprocess, network calls, and file I/O.
Uses tmp_path for file operations.
"""
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_completed_process(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _make_router(chatdev_path=None, available=False):
    """Create ChatDevAutonomousRouter with no real disk/network activity."""
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    with patch.object(ChatDevAutonomousRouter, "_get_chatdev_path", return_value=chatdev_path), \
         patch.object(ChatDevAutonomousRouter, "_validate_chatdev_installation", return_value=available):
        return ChatDevAutonomousRouter()


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------

def test_agent_role_enum_values():
    from src.orchestration.chatdev_autonomous_router import AgentRole

    assert AgentRole.CEO.value == "chief_executive_officer"
    assert AgentRole.CTO.value == "chief_technology_officer"
    assert AgentRole.PROGRAMMER.value == "programmer"
    assert AgentRole.TESTER.value == "code_tester"
    assert AgentRole.PRODUCT_MANAGER.value == "product_manager"


def test_agent_role_enum_members():
    from src.orchestration.chatdev_autonomous_router import AgentRole

    members = {m.name for m in AgentRole}
    assert members == {"CEO", "CTO", "PROGRAMMER", "TESTER", "PRODUCT_MANAGER"}


def test_task_category_enum_values():
    from src.orchestration.chatdev_autonomous_router import TaskCategory

    assert TaskCategory.CODE_GENERATION.value == "code_generation"
    assert TaskCategory.BUG_FIX.value == "bug_fix"
    assert TaskCategory.TEST_GENERATION.value == "test_generation"
    assert TaskCategory.CODE_REVIEW.value == "code_review"
    assert TaskCategory.REFACTORING.value == "refactoring"
    assert TaskCategory.DOCUMENTATION.value == "documentation"


# ---------------------------------------------------------------------------
# Dataclass tests
# ---------------------------------------------------------------------------

def test_chatdev_task_defaults():
    from src.orchestration.chatdev_autonomous_router import AgentRole, ChatDevTask, TaskCategory

    task = ChatDevTask(
        task_id="t1",
        category=TaskCategory.BUG_FIX,
        title="Fix bug",
        description="desc",
    )
    assert task.task_id == "t1"
    assert task.category == TaskCategory.BUG_FIX
    assert task.title == "Fix bug"
    assert task.description == "desc"
    assert task.status == "pending"
    assert task.codebase_issues == []
    assert task.assigned_agents == []
    assert task.execution_log == ""
    assert task.results == {}
    assert isinstance(task.created_at, datetime)


def test_chatdev_task_custom_agents():
    from src.orchestration.chatdev_autonomous_router import AgentRole, ChatDevTask, TaskCategory

    agents = [AgentRole.CEO, AgentRole.PROGRAMMER]
    task = ChatDevTask(
        task_id="t2",
        category=TaskCategory.CODE_GENERATION,
        title="Gen",
        description="d",
        assigned_agents=agents,
    )
    assert task.assigned_agents == agents


def test_chatdev_task_mutable_defaults_independent():
    """Each ChatDevTask instance should get its own list defaults."""
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    t1 = ChatDevTask("a", TaskCategory.CODE_REVIEW, "t", "d")
    t2 = ChatDevTask("b", TaskCategory.CODE_REVIEW, "t", "d")
    t1.codebase_issues.append({"x": 1})
    assert t2.codebase_issues == []


# ---------------------------------------------------------------------------
# Router instantiation
# ---------------------------------------------------------------------------

def test_router_init_no_chatdev():
    """Router initializes successfully even with no ChatDev installation."""
    router = _make_router(chatdev_path=None, available=False)

    assert router.chatdev_path is None
    assert router.chatdev_available is False
    assert router.tasks == {}
    assert router._supported_chatdev_flags is None
    assert router._resolved_router_settings is None


def test_router_init_with_chatdev(tmp_path):
    router = _make_router(chatdev_path=tmp_path, available=True)

    assert router.chatdev_path == tmp_path
    assert router.chatdev_available is True


# ---------------------------------------------------------------------------
# Static/pure helpers
# ---------------------------------------------------------------------------

def test_ensure_openai_compatible_url_adds_v1():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    result = ChatDevAutonomousRouter._ensure_openai_compatible_ollama_url(
        "http://localhost:11434"
    )
    assert result == "http://localhost:11434/v1"


def test_ensure_openai_compatible_url_already_v1():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    result = ChatDevAutonomousRouter._ensure_openai_compatible_ollama_url(
        "http://localhost:11434/v1"
    )
    assert result == "http://localhost:11434/v1"


def test_ensure_openai_compatible_url_adds_scheme():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    result = ChatDevAutonomousRouter._ensure_openai_compatible_ollama_url("localhost:11434")
    assert result.startswith("http://")
    assert result.endswith("/v1")


def test_ensure_openai_compatible_url_empty():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    result = ChatDevAutonomousRouter._ensure_openai_compatible_ollama_url("")
    assert result == "http://localhost:11434/v1"


def test_to_ollama_root_url_strips_v1():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    assert (
        ChatDevAutonomousRouter._to_ollama_root_url("http://localhost:11434/v1")
        == "http://localhost:11434"
    )


def test_to_ollama_root_url_no_v1():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    url = "http://localhost:11434"
    assert ChatDevAutonomousRouter._to_ollama_root_url(url) == url


def test_sanitize_project_name_basic():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    result = ChatDevAutonomousRouter._sanitize_project_name("Fix: bug report!")
    # Non-alphanumeric runs collapse to a single underscore; leading/trailing stripped
    assert " " not in result
    assert ":" not in result
    assert result.startswith("Fix")


def test_sanitize_project_name_empty():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    assert ChatDevAutonomousRouter._sanitize_project_name("") == "NuSyQ_Task"


def test_sanitize_project_name_spaces():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    result = ChatDevAutonomousRouter._sanitize_project_name("hello world")
    assert " " not in result
    assert result


def test_strip_model_flag_removes_flag_and_value():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    cmd = ["python", "run.py", "--task", "do it", "--model", "ollama", "--name", "proj"]
    result = ChatDevAutonomousRouter._strip_model_flag(cmd)
    assert "--model" not in result
    assert "ollama" not in result
    assert "--task" in result
    assert "--name" in result


def test_strip_model_flag_no_model():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    cmd = ["python", "run.py", "--task", "do it"]
    assert ChatDevAutonomousRouter._strip_model_flag(cmd) == cmd


def test_summarize_chatdev_error_openai_key():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    msg = ChatDevAutonomousRouter._summarize_chatdev_error(
        "OpenAI API key not found", returncode=1
    )
    assert "credentials" in msg.lower() or "openai api key" in msg.lower()


def test_summarize_chatdev_error_generic():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    msg = ChatDevAutonomousRouter._summarize_chatdev_error("some error text", returncode=2)
    assert "some error text" in msg


def test_summarize_chatdev_error_empty_stderr():
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    msg = ChatDevAutonomousRouter._summarize_chatdev_error("", returncode=5)
    assert "5" in msg


def test_chatdev_timeout_default(monkeypatch):
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    monkeypatch.delenv("CHATDEV_TASK_TIMEOUT_SECONDS", raising=False)
    assert ChatDevAutonomousRouter._chatdev_timeout_seconds() == 300


def test_chatdev_timeout_env_override(monkeypatch):
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    monkeypatch.setenv("CHATDEV_TASK_TIMEOUT_SECONDS", "600")
    assert ChatDevAutonomousRouter._chatdev_timeout_seconds() == 600


def test_chatdev_timeout_env_invalid(monkeypatch):
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    monkeypatch.setenv("CHATDEV_TASK_TIMEOUT_SECONDS", "notanumber")
    assert ChatDevAutonomousRouter._chatdev_timeout_seconds() == 300


def test_chatdev_timeout_env_clamped_low(monkeypatch):
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    monkeypatch.setenv("CHATDEV_TASK_TIMEOUT_SECONDS", "5")
    assert ChatDevAutonomousRouter._chatdev_timeout_seconds() == 30  # min bound


def test_chatdev_timeout_env_clamped_high(monkeypatch):
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    monkeypatch.setenv("CHATDEV_TASK_TIMEOUT_SECONDS", "9999")
    assert ChatDevAutonomousRouter._chatdev_timeout_seconds() == 3600  # max bound


# ---------------------------------------------------------------------------
# _read_json_file
# ---------------------------------------------------------------------------

def test_read_json_file_missing(tmp_path):
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    result = ChatDevAutonomousRouter._read_json_file(tmp_path / "nope.json")
    assert result is None


def test_read_json_file_valid(tmp_path):
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    p = tmp_path / "data.json"
    p.write_text('{"key": "value"}', encoding="utf-8")
    result = ChatDevAutonomousRouter._read_json_file(p)
    assert result == {"key": "value"}


def test_read_json_file_invalid_json(tmp_path):
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    p = tmp_path / "bad.json"
    p.write_text("NOT JSON", encoding="utf-8")
    result = ChatDevAutonomousRouter._read_json_file(p)
    assert result is None


def test_read_json_file_non_dict(tmp_path):
    from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter

    p = tmp_path / "list.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    result = ChatDevAutonomousRouter._read_json_file(p)
    assert result is None


# ---------------------------------------------------------------------------
# _should_try_legacy_ollama_shim
# ---------------------------------------------------------------------------

def test_should_try_legacy_shim_success_returncode():
    router = _make_router()
    # returncode == 0 → never retry
    assert router._should_try_legacy_ollama_shim("openai api key not found", 0) is False


def test_should_try_legacy_shim_no_chatdev_path():
    router = _make_router(chatdev_path=None)
    assert router._should_try_legacy_ollama_shim("openai api key not found", 1) is False


def test_should_try_legacy_shim_no_run_ollama(tmp_path):
    # chatdev_path exists but run_ollama.py is absent
    router = _make_router(chatdev_path=tmp_path)
    assert router._should_try_legacy_ollama_shim("openai api key not found", 1) is False


def test_should_try_legacy_shim_with_run_ollama(tmp_path):
    (tmp_path / "run_ollama.py").write_text("# stub", encoding="utf-8")
    router = _make_router(chatdev_path=tmp_path)
    assert router._should_try_legacy_ollama_shim("openai api key not found", 1) is True


def test_should_try_legacy_shim_unrelated_error(tmp_path):
    (tmp_path / "run_ollama.py").write_text("# stub", encoding="utf-8")
    router = _make_router(chatdev_path=tmp_path)
    assert router._should_try_legacy_ollama_shim("some other error", 1) is False


# ---------------------------------------------------------------------------
# decompose_issue_into_task
# ---------------------------------------------------------------------------

def test_decompose_issue_maps_missing_type_hint():
    from src.orchestration.chatdev_autonomous_router import AgentRole, TaskCategory

    router = _make_router()
    issue = {"issue_id": "i1", "message": "Missing type hint", "file_path": "src/foo.py", "line_number": 10}
    task = router.decompose_issue_into_task(issue, "missing_type_hint")

    assert task.category == TaskCategory.REFACTORING
    assert AgentRole.PROGRAMMER in task.assigned_agents
    assert task.task_id == "chatdev_task_i1"
    assert "chatdev_task_i1" in router.tasks


def test_decompose_issue_maps_bug_fix():
    from src.orchestration.chatdev_autonomous_router import TaskCategory

    router = _make_router()
    issue = {"issue_id": "i2", "message": "undefined ref"}
    task = router.decompose_issue_into_task(issue, "undefined_reference")
    assert task.category == TaskCategory.BUG_FIX


def test_decompose_issue_maps_documentation():
    from src.orchestration.chatdev_autonomous_router import AgentRole, TaskCategory

    router = _make_router()
    issue = {"issue_id": "i3", "message": "doc gap"}
    task = router.decompose_issue_into_task(issue, "documentation_gap")
    assert task.category == TaskCategory.DOCUMENTATION
    assert AgentRole.PRODUCT_MANAGER in task.assigned_agents


def test_decompose_issue_unknown_type_defaults_to_code_review():
    from src.orchestration.chatdev_autonomous_router import AgentRole, TaskCategory

    router = _make_router()
    issue = {"issue_id": "i4", "message": "weird issue"}
    task = router.decompose_issue_into_task(issue, "totally_unknown_type")
    assert task.category == TaskCategory.CODE_REVIEW
    assert AgentRole.PROGRAMMER in task.assigned_agents


def test_decompose_issue_status_is_pending():
    router = _make_router()
    issue = {"issue_id": "i5", "message": "msg"}
    task = router.decompose_issue_into_task(issue, "style_violation")
    assert task.status == "pending"


# ---------------------------------------------------------------------------
# get_task_status / get_all_tasks
# ---------------------------------------------------------------------------

def test_get_task_status_unknown():
    router = _make_router()
    assert router.get_task_status("nonexistent") is None


def test_get_task_status_known():
    from src.orchestration.chatdev_autonomous_router import TaskCategory

    router = _make_router()
    issue = {"issue_id": "s1", "message": "m"}
    task = router.decompose_issue_into_task(issue, "unused_import")
    status = router.get_task_status(task.task_id)

    assert status is not None
    assert status["task_id"] == task.task_id
    assert status["status"] == "pending"
    assert "category" in status
    assert "agents" in status
    assert "created_at" in status
    assert "updated_at" in status
    assert "results" in status


def test_get_all_tasks_empty():
    router = _make_router()
    assert router.get_all_tasks() == {}


def test_get_all_tasks_populated():
    router = _make_router()
    for i in range(3):
        router.decompose_issue_into_task({"issue_id": str(i), "message": "m"}, "style_violation")
    all_tasks = router.get_all_tasks()
    assert len(all_tasks) == 3


# ---------------------------------------------------------------------------
# route_task_to_chatdev — unavailable path
# ---------------------------------------------------------------------------

def test_route_task_to_chatdev_unavailable():
    import asyncio
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    router = _make_router(chatdev_path=None, available=False)
    task = ChatDevTask("t99", TaskCategory.BUG_FIX, "title", "desc")

    result = asyncio.run(router.route_task_to_chatdev(task))

    assert result["success"] is False
    assert result["status"] == "chatdev_unavailable"
    assert task.status == "failed"


# ---------------------------------------------------------------------------
# _execute_chatdev_task — subprocess stubbed
# ---------------------------------------------------------------------------

def test_execute_chatdev_task_success(tmp_path):
    import asyncio
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    # Create minimal ChatDev structure so _build_chatdev_command doesn't raise
    router = _make_router(chatdev_path=tmp_path, available=True)
    # Stub flag discovery to avoid real subprocess
    router._supported_chatdev_flags = {"--task"}

    task = ChatDevTask("exec1", TaskCategory.CODE_GENERATION, "Gen code", "Generate something")

    fake_result = _make_completed_process(returncode=0, stdout="All good", stderr="")

    with patch.object(router, "_run_subprocess", return_value=fake_result):
        result = asyncio.run(router._execute_chatdev_task(task))

    assert result["success"] is True
    assert result["status"] == "success"
    assert result["task_id"] == "exec1"


def test_execute_chatdev_task_failure(tmp_path):
    import asyncio
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    router = _make_router(chatdev_path=tmp_path, available=True)
    router._supported_chatdev_flags = {"--task"}

    task = ChatDevTask("exec2", TaskCategory.BUG_FIX, "Fix", "desc")
    fake_result = _make_completed_process(returncode=1, stdout="", stderr="some failure")

    with patch.object(router, "_run_subprocess", return_value=fake_result):
        result = asyncio.run(router._execute_chatdev_task(task))

    assert result["success"] is False
    assert result["status"] == "failed"


def test_execute_chatdev_task_timeout(tmp_path):
    import asyncio
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    router = _make_router(chatdev_path=tmp_path, available=True)
    router._supported_chatdev_flags = {"--task"}

    task = ChatDevTask("exec3", TaskCategory.TEST_GENERATION, "Tests", "desc")

    with patch.object(router, "_run_subprocess", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=300)):
        result = asyncio.run(router._execute_chatdev_task(task))

    assert result["success"] is False
    assert result["status"] == "timeout"


def test_execute_chatdev_task_no_chatdev_path():
    import asyncio
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    router = _make_router(chatdev_path=None, available=False)
    task = ChatDevTask("exec4", TaskCategory.DOCUMENTATION, "Docs", "desc")

    result = asyncio.run(router._execute_chatdev_task(task))
    assert result["success"] is False
    assert "not configured" in result.get("error", "")


# ---------------------------------------------------------------------------
# _get_supported_chatdev_flags
# ---------------------------------------------------------------------------

def test_get_supported_chatdev_flags_cached():
    router = _make_router()
    router._supported_chatdev_flags = {"--task", "--name"}
    # Should return cached value without hitting subprocess
    flags = router._get_supported_chatdev_flags()
    assert "--task" in flags
    assert "--name" in flags


def test_get_supported_chatdev_flags_no_chatdev_path():
    router = _make_router(chatdev_path=None)
    flags = router._get_supported_chatdev_flags()
    assert "--task" in flags
    assert len(flags) == 1


def test_get_supported_chatdev_flags_subprocess(tmp_path):
    (tmp_path / "run.py").write_text("# stub", encoding="utf-8")
    router = _make_router(chatdev_path=tmp_path)
    router._supported_chatdev_flags = None

    fake_result = _make_completed_process(
        returncode=0,
        stdout="usage: run.py [--task TASK] [--name NAME] [--model MODEL]",
        stderr="",
    )
    with patch.object(router, "_run_subprocess", return_value=fake_result):
        flags = router._get_supported_chatdev_flags()

    assert "--task" in flags
    assert "--name" in flags
    assert "--model" in flags


# ---------------------------------------------------------------------------
# _build_chatdev_command
# ---------------------------------------------------------------------------

def test_build_chatdev_command_raises_without_path():
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    router = _make_router(chatdev_path=None)
    task = ChatDevTask("c1", TaskCategory.CODE_REVIEW, "Review", "desc")
    try:
        router._build_chatdev_command(task)
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_build_chatdev_command_basic(tmp_path):
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    router = _make_router(chatdev_path=tmp_path)
    router._supported_chatdev_flags = {"--task"}  # only --task supported
    task = ChatDevTask("c2", TaskCategory.CODE_GENERATION, "My Project", "Do the thing")

    cmd = router._build_chatdev_command(task)

    assert sys.executable in cmd
    assert "--task" in cmd
    assert "Do the thing" in cmd
    # --name and --model NOT in cmd since flags not supported
    assert "--name" not in cmd


def test_build_chatdev_command_with_extra_flags(tmp_path):
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    router = _make_router(chatdev_path=tmp_path)
    router._supported_chatdev_flags = {"--task", "--name", "--model"}
    task = ChatDevTask("c3", TaskCategory.BUG_FIX, "My Fix", "Fix this bug")

    with patch.dict("os.environ", {"CHATDEV_RUNPY_MODEL": "llama3"}, clear=False):
        cmd = router._build_chatdev_command(task)

    assert "--name" in cmd
    assert "My Fix" in cmd
    assert "--model" in cmd
    assert "llama3" in cmd


# ---------------------------------------------------------------------------
# _resolve_router_settings
# ---------------------------------------------------------------------------

def test_resolve_router_settings_cached():
    router = _make_router()
    cached = {"ollama_base_url": "http://cached:11434"}
    router._resolved_router_settings = cached
    result = router._resolve_router_settings()
    assert result is cached


def test_resolve_router_settings_env_url(monkeypatch):
    monkeypatch.setenv("CHATDEV_OLLAMA_URL", "http://myserver:11434")
    monkeypatch.delenv("CHATDEV_OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("CHATDEV_ORG", raising=False)

    router = _make_router()
    # Ensure no cached result
    router._resolved_router_settings = None

    with patch.object(router, "_read_json_file", return_value=None), \
         patch("src.orchestration.chatdev_autonomous_router.get_repo_path", None):
        settings = router._resolve_router_settings()

    assert settings.get("ollama_base_url") == "http://myserver:11434"


def test_resolve_router_settings_default_org(monkeypatch):
    monkeypatch.delenv("CHATDEV_OLLAMA_URL", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.delenv("CHATDEV_OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("CHATDEV_ORG", raising=False)

    router = _make_router()
    router._resolved_router_settings = None

    with patch.object(router, "_read_json_file", return_value=None), \
         patch("src.orchestration.chatdev_autonomous_router.get_repo_path", None):
        try:
            from src.utils import config_helper
            with patch("src.utils.config_helper.get_ollama_host", return_value=None):
                settings = router._resolve_router_settings()
        except ImportError:
            settings = router._resolve_router_settings()

    assert settings.get("organization") == "NuSyQ"


# ---------------------------------------------------------------------------
# _build_chatdev_env
# ---------------------------------------------------------------------------

def test_build_chatdev_env_sets_ollama_vars(monkeypatch):
    router = _make_router()
    router._resolved_router_settings = {"ollama_base_url": "http://ollama:11434"}

    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    env = router._build_chatdev_env(prefer_ollama=False)

    assert "OLLAMA_BASE_URL" in env
    assert "/v1" in env["OLLAMA_BASE_URL"]


def test_build_chatdev_env_prefer_ollama(monkeypatch):
    router = _make_router()
    router._resolved_router_settings = {"ollama_base_url": "http://ollama:11434"}

    monkeypatch.delenv("CHATDEV_USE_OLLAMA", raising=False)

    env = router._build_chatdev_env(prefer_ollama=True)

    assert env.get("CHATDEV_USE_OLLAMA") == "1"


# ---------------------------------------------------------------------------
# propose_task_to_council — ImportError path
# ---------------------------------------------------------------------------

def test_propose_task_to_council_no_voting_module():
    router = _make_router()

    with patch.dict(sys.modules, {"src.orchestration.ai_council_voting": None}):
        result = router.propose_task_to_council("Fix everything", "BUG_FIX")

    assert result["success"] is False


# ---------------------------------------------------------------------------
# dispatch_via_nusyq — facade unavailable
# ---------------------------------------------------------------------------

def test_dispatch_via_nusyq_facade_unavailable():
    from src.orchestration import chatdev_autonomous_router as mod

    router = _make_router()

    original = mod._NUSYQ_FACADE_LOADED
    try:
        mod._NUSYQ_FACADE_LOADED = True
        mod.NUSYQ_FACADE_AVAILABLE = False
        mod.nusyq = None

        with patch.object(router, "route_task", return_value={"success": True, "status": "scheduled"}):
            result = router.dispatch_via_nusyq("Do something")

        assert result["success"] is True
    finally:
        mod._NUSYQ_FACADE_LOADED = original


# ---------------------------------------------------------------------------
# route_autonomous_cycle_issues — unavailable path
# ---------------------------------------------------------------------------

def test_route_autonomous_cycle_issues_unavailable():
    import asyncio

    router = _make_router(chatdev_path=None, available=False)
    result = asyncio.run(router.route_autonomous_cycle_issues([{"issue_id": "1"}], ["style_violation"]))
    assert result == []


# ---------------------------------------------------------------------------
# route_task (sync wrapper)
# ---------------------------------------------------------------------------

def test_route_task_chatdev_unavailable():
    """When chatdev unavailable, route_task returns chatdev_unavailable status."""
    router = _make_router(chatdev_path=None, available=False)
    result = router.route_task("Generate a utility function")
    # Should complete synchronously and return chatdev_unavailable
    assert result.get("success") is False
    assert result.get("status") == "chatdev_unavailable"


def test_route_task_with_codebase_issues():
    """Extra codebase_issues are appended to the task."""
    router = _make_router(chatdev_path=None, available=False)
    extra = [{"issue_id": "extra", "message": "extra issue"}]
    router.route_task("Fix imports", codebase_issues=extra)
    # Task should have been decomposed and stored
    assert len(router.tasks) == 1
    stored_task = next(iter(router.tasks.values()))
    # The extra issue is appended after the primary issue
    assert len(stored_task.codebase_issues) == 2


# ---------------------------------------------------------------------------
# _build_chatdev_ollama_shim_command
# ---------------------------------------------------------------------------

def test_build_chatdev_ollama_shim_no_chatdev_path():
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    router = _make_router(chatdev_path=None)
    task = ChatDevTask("s1", TaskCategory.CODE_GENERATION, "Gen", "desc")
    assert router._build_chatdev_ollama_shim_command(task) is None


def test_build_chatdev_ollama_shim_no_run_ollama(tmp_path):
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    router = _make_router(chatdev_path=tmp_path)
    task = ChatDevTask("s2", TaskCategory.CODE_GENERATION, "Gen", "desc")
    # run_ollama.py does not exist
    assert router._build_chatdev_ollama_shim_command(task) is None


def test_build_chatdev_ollama_shim_with_run_ollama(tmp_path):
    from src.orchestration.chatdev_autonomous_router import ChatDevTask, TaskCategory

    (tmp_path / "run_ollama.py").write_text("# stub", encoding="utf-8")
    router = _make_router(chatdev_path=tmp_path)
    router._resolved_router_settings = {"organization": "TestOrg"}

    task = ChatDevTask("s3", TaskCategory.CODE_GENERATION, "Generate Feature", "desc")
    cmd = router._build_chatdev_ollama_shim_command(task)

    assert cmd is not None
    assert "--task" in cmd
    assert "--name" in cmd
    assert "--org" in cmd
    assert "TestOrg" in cmd
    assert "Generate_Feature" in cmd  # sanitized name

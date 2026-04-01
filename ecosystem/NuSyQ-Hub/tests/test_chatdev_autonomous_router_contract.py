"""Contract tests for ChatDev autonomous router result semantics."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from src.orchestration.chatdev_autonomous_router import (
    AgentRole,
    ChatDevAutonomousRouter,
    ChatDevTask,
    TaskCategory,
)


class _TestableRouter(ChatDevAutonomousRouter):
    """Router variant with deterministic local path for tests."""

    def _get_chatdev_path(self) -> Path | None:
        return Path(".")

    def _validate_chatdev_installation(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_route_task_to_chatdev_marks_task_failed_on_unsuccessful_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _TestableRouter()
    task = ChatDevTask(
        task_id="task-1",
        category=TaskCategory.CODE_GENERATION,
        title="Generate code",
        description="Generate code",
        assigned_agents=[AgentRole.PROGRAMMER],
    )

    async def _fake_execute(_task: ChatDevTask) -> dict[str, object]:
        return {"success": False, "status": "failed", "task_id": _task.task_id}

    monkeypatch.setattr(router, "_execute_chatdev_task", _fake_execute)

    result = await router.route_task_to_chatdev(task)

    assert result["success"] is False
    assert task.status == "failed"


@pytest.mark.asyncio
async def test_execute_chatdev_task_sets_success_from_returncode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _TestableRouter()
    task = ChatDevTask(
        task_id="task-2",
        category=TaskCategory.CODE_GENERATION,
        title="Generate code",
        description="Generate code",
        assigned_agents=[AgentRole.PROGRAMMER],
    )

    def _fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["python", "run.py"],
            returncode=1,
            stdout="",
            stderr="failed",
        )

    monkeypatch.setattr(router, "_run_subprocess", _fake_run)

    result = await router._execute_chatdev_task(task)

    assert result["success"] is False
    assert result["status"] == "failed"
    assert result["returncode"] == 1
    assert "failed" in str(result.get("error", ""))


@pytest.mark.asyncio
async def test_execute_chatdev_task_uses_only_supported_cli_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _TestableRouter()
    task = ChatDevTask(
        task_id="task-3",
        category=TaskCategory.CODE_GENERATION,
        title="Generate code",
        description="Generate code from prompt",
        assigned_agents=[AgentRole.PROGRAMMER],
    )

    def _fake_run(*args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd = list(args[0])  # first positional arg to subprocess.run
        if "--help" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="usage: run.py [--task TASK] [--model MODEL]",
                stderr="",
            )
        assert "--description" not in cmd
        assert "--auto-mode" not in cmd
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(router, "_run_subprocess", _fake_run)

    result = await router._execute_chatdev_task(task)

    assert result["success"] is True
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_execute_chatdev_task_retries_without_model_on_model_keyerror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _TestableRouter()
    task = ChatDevTask(
        task_id="task-4",
        category=TaskCategory.CODE_GENERATION,
        title="Generate code",
        description="Generate code from prompt",
        assigned_agents=[AgentRole.PROGRAMMER],
    )
    run_calls: list[list[str]] = []

    def _fake_run(*args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd = list(args[0])  # first positional arg to subprocess.run
        run_calls.append(cmd)
        if "--help" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="usage: run.py [--task TASK] [--model MODEL]",
                stderr="",
            )
        if "--model" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr="KeyError: 'ollama'",
            )
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(router, "_run_subprocess", _fake_run)

    result = await router._execute_chatdev_task(task)

    assert result["success"] is True
    assert result["status"] == "success"
    assert any("--model" in call for call in run_calls)
    assert any("--model" not in call and "--help" not in call for call in run_calls)


@pytest.mark.asyncio
async def test_execute_chatdev_task_surfaces_credential_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _TestableRouter()
    task = ChatDevTask(
        task_id="task-5",
        category=TaskCategory.CODE_GENERATION,
        title="Generate code",
        description="Generate code from prompt",
        assigned_agents=[AgentRole.PROGRAMMER],
    )

    def _fake_run(*args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd = list(args[0])  # first positional arg to subprocess.run
        if "--help" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="usage: run.py [--task TASK]",
                stderr="",
            )
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=1,
            stdout="",
            stderr="ValueError: OpenAI API key not found.",
        )

    monkeypatch.setattr(router, "_run_subprocess", _fake_run)

    result = await router._execute_chatdev_task(task)

    assert result["success"] is False
    assert "missing credentials" in str(result.get("error", "")).lower()


@pytest.mark.asyncio
async def test_execute_chatdev_task_uses_legacy_ollama_shim_on_credential_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    router = _TestableRouter()
    router.chatdev_path = tmp_path
    (tmp_path / "run.py").write_text("print('run')\n", encoding="utf-8")
    (tmp_path / "run_ollama.py").write_text("print('run_ollama')\n", encoding="utf-8")

    task = ChatDevTask(
        task_id="task-6",
        category=TaskCategory.CODE_GENERATION,
        title="Generate code",
        description="Generate code from prompt",
        assigned_agents=[AgentRole.PROGRAMMER],
    )
    run_calls: list[list[str]] = []

    def _fake_run(*args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd = list(args[0])  # first positional arg to subprocess.run
        run_calls.append(cmd)
        command_path = cmd[1] if len(cmd) > 1 else ""
        if "--help" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="usage: run.py [--task TASK] [--name NAME] [--model MODEL]",
                stderr="",
            )
        if command_path.endswith("run.py"):
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr="ValueError: OpenAI API key not found.",
            )
        if command_path.endswith("run_ollama.py"):
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="ok via ollama shim",
                stderr="",
            )
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="unexpected")

    monkeypatch.setattr(router, "_run_subprocess", _fake_run)

    result = await router._execute_chatdev_task(task)

    assert result["success"] is True
    assert result["status"] == "success"
    assert any(call[1].endswith("run_ollama.py") for call in run_calls if len(call) > 1)


@pytest.mark.asyncio
async def test_execute_chatdev_task_maps_subprocess_timeout_to_timeout_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _TestableRouter()
    task = ChatDevTask(
        task_id="task-7",
        category=TaskCategory.CODE_GENERATION,
        title="Generate code",
        description="Generate code from prompt",
        assigned_agents=[AgentRole.PROGRAMMER],
    )

    def _fake_run(*args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd = list(args[0])  # first positional arg to subprocess.run
        if "--help" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="usage: run.py [--task TASK]",
                stderr="",
            )
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=300)

    monkeypatch.setattr(router, "_run_subprocess", _fake_run)

    result = await router._execute_chatdev_task(task)

    assert result["success"] is False
    assert result["status"] == "timeout"
    assert "timed out" in str(result.get("error", "")).lower()


def test_chatdev_timeout_seconds_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHATDEV_TASK_TIMEOUT_SECONDS", "900")
    assert ChatDevAutonomousRouter._chatdev_timeout_seconds() == 900

    monkeypatch.setenv("CHATDEV_TASK_TIMEOUT_SECONDS", "5")
    assert ChatDevAutonomousRouter._chatdev_timeout_seconds() == 30

    monkeypatch.setenv("CHATDEV_TASK_TIMEOUT_SECONDS", "not-a-number")
    assert ChatDevAutonomousRouter._chatdev_timeout_seconds() == 300


def test_resolve_router_settings_prefers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    router = _TestableRouter()
    monkeypatch.setenv("CHATDEV_OLLAMA_URL", "http://env-ollama:11434")
    monkeypatch.setenv("CHATDEV_OLLAMA_MODEL", "env-model:latest")
    monkeypatch.setenv("CHATDEV_ORG", "EnvOrg")

    resolved = router._resolve_router_settings()

    assert resolved["ollama_base_url"] == "http://env-ollama:11434"
    assert resolved["ollama_model"] == "env-model:latest"
    assert resolved["organization"] == "EnvOrg"


def test_build_chatdev_ollama_shim_command_uses_resolved_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    router = _TestableRouter()
    router.chatdev_path = tmp_path
    (tmp_path / "run_ollama.py").write_text("print('shim')\n", encoding="utf-8")
    task = ChatDevTask(
        task_id="task-8",
        category=TaskCategory.CODE_GENERATION,
        title="Generate code",
        description="Generate code from prompt",
        assigned_agents=[AgentRole.PROGRAMMER],
    )

    monkeypatch.setattr(
        router,
        "_resolve_router_settings",
        lambda: {
            "ollama_base_url": "http://cfg-ollama:11434/v1",
            "ollama_model": "qwen2.5-coder:7b",
            "organization": "CfgOrg",
        },
    )

    cmd = router._build_chatdev_ollama_shim_command(task)

    assert cmd is not None
    assert "--org" in cmd and "CfgOrg" in cmd
    assert "--model" in cmd and "qwen2.5-coder:7b" in cmd
    assert "--ollama-url" in cmd and "http://cfg-ollama:11434" in cmd


def test_build_chatdev_env_populates_openai_compatible_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _TestableRouter()
    monkeypatch.setattr(
        router,
        "_resolve_router_settings",
        lambda: {
            "ollama_base_url": "http://cfg-ollama:11434",
            "ollama_model": "qwen2.5-coder:7b",
            "organization": "CfgOrg",
        },
    )
    # Clear environment variables so setdefault() can use config values
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("CHATDEV_MODEL", raising=False)

    env = router._build_chatdev_env(prefer_ollama=True)

    assert env["OLLAMA_BASE_URL"] == "http://cfg-ollama:11434/v1"
    assert env["BASE_URL"] == "http://cfg-ollama:11434/v1"
    assert env["OPENAI_BASE_URL"] == "http://cfg-ollama:11434/v1"
    assert env["CHATDEV_MODEL"] == "qwen2.5-coder:7b"
    assert env["CHATDEV_USE_OLLAMA"] == "1"
    assert env["OPENAI_API_KEY"] == "ollama-local"


@pytest.mark.asyncio
async def test_execute_chatdev_task_without_path_returns_failed_contract() -> None:
    router = _TestableRouter()
    router.chatdev_path = None
    task = ChatDevTask(
        task_id="task-no-path",
        category=TaskCategory.CODE_GENERATION,
        title="Generate code",
        description="Generate code from prompt",
        assigned_agents=[AgentRole.PROGRAMMER],
    )

    result = await router._execute_chatdev_task(task)

    assert result["success"] is False
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_route_with_council_impl_uses_sync_proposal_method(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _TestableRouter()
    monkeypatch.setattr(
        router,
        "propose_task_to_council",
        lambda *_args, **_kwargs: {"success": False, "error": "blocked"},
    )

    result = await router._route_with_council_impl(
        task_description="Generate code",
        task_category="CODE_GENERATION",
        auto_approve=False,
        auto_approve_agents=None,
    )

    assert result["success"] is False
    assert result["error"] == "blocked"

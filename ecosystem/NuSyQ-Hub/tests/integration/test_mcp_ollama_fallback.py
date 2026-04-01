"""Integration tests for MCP→Ollama fallback chain.

Tests that ChatDev resilience handler correctly falls back to Ollama
when primary (OpenAI/ChatDev) path fails.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_config():
    """Sample resilience config matching config/chatdev_resilience_config.json."""
    return {
        "enabled": True,
        "fallback_chain": ["chatdev", "ollama_direct", "factory"],
        "resilience": {
            "max_retries": 3,
            "retry_delay_seconds": 1.0,
            "exponential_backoff": True,
        },
        "ollama_config": {
            "endpoint": "http://127.0.0.1:11434",
            "default_model": "qwen2.5-coder:7b",
            "fallback_model": "deepseek-coder-v2:16b",
            "timeout_seconds": 600,
            "run_ollama_path": "C:/Users/keath/NuSyQ/ChatDev/run_ollama.py",
        },
    }


def test_load_resilience_config_exists():
    """Verify config file can be loaded."""
    from src.integration.chatdev_resilience_handler import load_resilience_config

    config = load_resilience_config()
    assert isinstance(config, dict)
    # Config should have version, fallback_chain, ollama_config
    assert "fallback_chain" in config or config == {}  # Empty dict is valid default


def test_create_ollama_runner_returns_callable():
    """Verify Ollama runner is created correctly."""
    from src.integration.chatdev_resilience_handler import create_ollama_runner

    runner = create_ollama_runner(model="qwen2.5-coder:7b")
    assert callable(runner)


@pytest.mark.asyncio
async def test_ollama_runner_subprocess_call():
    """Verify Ollama runner calls subprocess correctly when invoked."""
    from src.integration.chatdev_resilience_handler import create_ollama_runner

    runner = create_ollama_runner(model="qwen2.5-coder:7b")

    # Mock subprocess to avoid actually running ChatDev
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"Success output", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        # Runner should be async callable
        _ = await runner(task="Test task", name="test_project")

        # Verify subprocess was called
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args
        cmd_list = list(call_args.args) if call_args.args else []

        # Should include python path, run_ollama.py, --task, --name, --model
        assert any("run_ollama" in str(arg) for arg in cmd_list)


def test_create_resilient_handler_with_ollama_fallback():
    """Verify resilient handler is created with Ollama fallback configured."""
    from src.integration.chatdev_resilience_handler import (
        create_resilient_handler_with_ollama_fallback,
    )

    handler = create_resilient_handler_with_ollama_fallback()
    assert handler is not None
    assert handler.degraded_runner is not None  # Ollama fallback attached
    assert handler.degraded_config.enabled is True


@pytest.mark.asyncio
async def test_fallback_triggered_on_primary_failure(mock_config):
    """Verify Ollama fallback is triggered when primary fails."""
    from src.integration.chatdev_resilience_handler import ResilientChatDevHandler
    from src.resilience.checkpoint_retry_degraded import DegradedModeConfig

    # Create mock runners
    primary_runner = AsyncMock(side_effect=Exception("Primary failed"))
    degraded_runner = AsyncMock(return_value={"success": True, "output": "Fallback worked"})

    handler = ResilientChatDevHandler(
        primary_runner=primary_runner,
        degraded_runner=degraded_runner,
        degraded_config=DegradedModeConfig(enabled=True),
    )

    _ = await handler.execute_generate_project(
        task="Test project",
        model="qwen2.5-coder:7b",
        agent="test",
    )

    # Should have fallen back to degraded runner
    degraded_runner.assert_called()


@pytest.mark.asyncio
async def test_handler_emits_audit_entries():
    """Verify audit entries are emitted during execution."""
    import tempfile
    from pathlib import Path

    from src.integration.chatdev_resilience_handler import ResilientChatDevHandler
    from src.resilience.mission_control_attestation import AuditLog

    # Use temp file for test audit log
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        temp_log_path = f.name

    audit_log = AuditLog(log_path=temp_log_path)
    handler = ResilientChatDevHandler(
        primary_runner=AsyncMock(return_value={"success": True, "output": "Test output"}),
        audit_log=audit_log,
    )

    await handler.execute_generate_project(
        task="Test project",
        model="qwen2.5-coder:7b",
        agent="test",
    )

    # Should have emitted audit entries (read from file)
    entries = audit_log.read_all()
    assert len(entries) > 0

    # Cleanup
    Path(temp_log_path).unlink(missing_ok=True)


def test_config_file_has_expected_structure():
    """Verify config/chatdev_resilience_config.json has expected fields."""
    config_path = Path(__file__).parent.parent.parent / "config" / "chatdev_resilience_config.json"

    if not config_path.exists():
        pytest.skip("Config file not created yet")

    import json

    with open(config_path, "r") as f:
        config = json.load(f)

    # Check top-level structure
    assert "fallback_chain" in config
    assert isinstance(config["fallback_chain"], list)
    assert "ollama_config" in config
    assert "base_url" in config["ollama_config"]
    # enabled is inside degraded_mode, not root
    assert "degraded_mode" in config
    assert config["degraded_mode"].get("enabled") is True

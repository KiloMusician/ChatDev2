"""Contract tests for Update-ChatDev-to-use-Ollama legacy adapter responses."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import ClassVar

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _load_update_chatdev_module(monkeypatch) -> types.ModuleType:
    """Load the hyphenated legacy module with dependency shims."""
    fake_config = types.ModuleType("LocalLLMConfigurationChatDevOllama")

    class _FakeConfig:
        role_models: ClassVar[dict[str, str]] = {}

        @staticmethod
        def get_model_for_role(_role: str) -> str:
            return "qwen2.5-coder:7b"

    fake_config.ollama_config = _FakeConfig()

    fake_client_module = types.ModuleType("Ollama_Client_for_ChatDev_Integration")

    class _FakeClient:
        async def test_connection(self) -> bool:
            return True

        async def list_models(self) -> list[str]:
            return ["qwen2.5-coder:7b"]

    fake_client_module.ollama_client = _FakeClient()

    monkeypatch.setitem(sys.modules, "LocalLLMConfigurationChatDevOllama", fake_config)
    monkeypatch.setitem(sys.modules, "Ollama_Client_for_ChatDev_Integration", fake_client_module)

    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "integration"
        / "Update-ChatDev-to-use-Ollama.py"
    )
    spec = importlib.util.spec_from_file_location("legacy_update_chatdev_ollama", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_unknown_phase_returns_success_false(monkeypatch) -> None:
    module = _load_update_chatdev_module(monkeypatch)
    adapter = object.__new__(module.ChatDevOllamaAdapter)
    result = await module.ChatDevOllamaAdapter._run_phase(
        adapter, "unknown_phase", team={}, session_data={}
    )
    assert result["success"] is False
    assert result["status"] == "skipped"


async def test_placeholder_phase_handlers_return_success_true(monkeypatch) -> None:
    module = _load_update_chatdev_module(monkeypatch)
    adapter = object.__new__(module.ChatDevOllamaAdapter)

    design = await module.ChatDevOllamaAdapter._handle_design_phase(
        adapter, team={}, session_data={}
    )
    testing = await module.ChatDevOllamaAdapter._handle_testing_phase(
        adapter, team={}, session_data={}
    )
    review = await module.ChatDevOllamaAdapter._handle_review_phase(
        adapter, team={}, session_data={}
    )
    docs = await module.ChatDevOllamaAdapter._handle_documentation_phase(
        adapter, team={}, session_data={}
    )

    for payload in (design, testing, review, docs):
        assert payload["success"] is True
        assert payload["status"] == "completed"

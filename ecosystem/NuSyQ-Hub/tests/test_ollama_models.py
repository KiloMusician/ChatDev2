import logging

import pytest

# Note: These tests have Ollama module imports that may timeout.
# Tests are designed to handle import failures gracefully via lazy import.
# Use intelligent timeout manager instead of hardcoded value
try:
    from src.utils.intelligent_timeout_manager import get_adaptive_timeout

    OLLAMA_TIMEOUT = get_adaptive_timeout("ollama", complexity=0.5, priority="normal")
except (ImportError, AttributeError):
    OLLAMA_TIMEOUT = 60  # Fallback if manager unavailable

pytestmark = pytest.mark.timeout(OLLAMA_TIMEOUT)


def test_list_ollama_models_success(requests_mock):
    """Test listing Ollama models with successful response."""
    try:
        from src.integration.Ollama_Integration_Hub import get_ollama_url, list_ollama_models
    except Exception as e:
        pytest.skip(f"Cannot import Ollama module: {e}")

    url = f"{get_ollama_url().rstrip('/')}/v1/models"
    fake_models = [{"name": "llama2:7b"}, {"name": "codellama:7b"}]
    requests_mock.get(url, status_code=200, json=fake_models)
    models = list_ollama_models()
    assert isinstance(models, list)
    assert any(m.get("name") == "llama2:7b" for m in models)


def test_list_ollama_models_unavailable(requests_mock):
    """Test listing Ollama models when service is unavailable."""
    try:
        from src.integration.Ollama_Integration_Hub import get_ollama_url, list_ollama_models
    except Exception as e:
        pytest.skip(f"Cannot import Ollama module: {e}")

    base_url = get_ollama_url().rstrip("/")
    requests_mock.get(f"{base_url}/v1/models", status_code=500)
    requests_mock.get(f"{base_url}/api/tags", status_code=500)  # also mock the fallback
    models = list_ollama_models()
    assert models == []


def test_list_ollama_models_falls_back_to_api_tags(requests_mock):
    """Test fallback to /api/tags when /v1/models is unavailable."""
    try:
        from src.integration.Ollama_Integration_Hub import get_ollama_url, list_ollama_models
    except Exception as e:
        pytest.skip(f"Cannot import Ollama module: {e}")

    base_url = get_ollama_url().rstrip("/")
    requests_mock.get(f"{base_url}/v1/models", status_code=404)
    requests_mock.get(
        f"{base_url}/api/tags",
        status_code=200,
        json={"models": [{"name": "llama3.1:8b", "size": 123}]},
    )

    models = list_ollama_models()
    assert isinstance(models, list)
    assert any(m.get("name") == "llama3.1:8b" for m in models)


def test_discover_models_handles_listresponse_with_models_attr():
    """Test discover_models parses modern ollama list responses with .models."""
    try:
        from src.integration.Ollama_Integration_Hub import KILOOllamaHub
    except Exception as e:
        pytest.skip(f"Cannot import Ollama module: {e}")

    class FakeListResponse:
        def __init__(self, models):
            self.models = models

    class FakeClient:
        def __init__(self, response):
            self._response = response

        def list(self):
            return self._response

    hub = KILOOllamaHub.__new__(KILOOllamaHub)
    hub.is_connected = True
    hub.logger = logging.getLogger("test.ollama_discover_models")
    hub.client = FakeClient(
        FakeListResponse(
            [
                {
                    "id": "gpt-3.5-turbo-16k:latest",
                    "size": 1000,
                    "details": {"family": "qwen2", "parameter_size": "14.8B"},
                },
                {"name": "llama3.1:8b", "size": 2000, "details": {"family": "llama"}},
            ]
        )
    )
    hub.available_models = {}

    discovered = hub.discover_models()
    assert "gpt-3.5-turbo-16k:latest" in discovered
    assert "llama3.1:8b" in discovered
    assert discovered["gpt-3.5-turbo-16k:latest"].family == "qwen2"

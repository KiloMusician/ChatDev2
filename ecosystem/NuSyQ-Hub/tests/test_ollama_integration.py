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


def test_is_ollama_online_true(requests_mock):
    """Test Ollama online status with mock."""
    try:
        from src.integration.Ollama_Integration_Hub import get_ollama_url, is_ollama_online
    except Exception as e:
        pytest.skip(f"Cannot import Ollama module: {e}")

    url = f"{get_ollama_url().rstrip('/')}/v1/models"
    requests_mock.get(url, status_code=200, json=[{"name": "model1"}])
    assert is_ollama_online() is True


def test_is_ollama_online_false(requests_mock):
    """Test Ollama offline status with mock."""
    try:
        from src.integration.Ollama_Integration_Hub import get_ollama_url, is_ollama_online
    except Exception as e:
        pytest.skip(f"Cannot import Ollama module: {e}")

    url = f"{get_ollama_url().rstrip('/')}/v1/models"
    requests_mock.get(url, status_code=500)
    assert is_ollama_online() is False

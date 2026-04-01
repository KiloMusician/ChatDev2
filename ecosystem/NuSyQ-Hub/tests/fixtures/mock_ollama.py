"""Phase 3: Mock Infrastructure Integration - pytest fixtures

Rehabilitates 6 orphaned mock functions by providing pytest fixtures:
- health, generate (deploy/ollama_mock/app.py)
- health, generate, generate_stream, generate_sse (deploy/ollama_mock/app_fastapi.py)

Usage in tests:
    def test_with_mock_ollama(mock_ollama_server):
        # Server running at mock_ollama_server URL
        response = requests.get(f"{mock_ollama_server}/health")
        assert response.json()["status"] == "ok"

    def test_offline_mode(mock_ollama_url):
        # Just the URL, server managed elsewhere
        orchestrator = MultiAIOrchestrator(ollama_url=mock_ollama_url)
"""

import subprocess
import time
from pathlib import Path
from typing import Generator

import pytest
import requests


@pytest.fixture(scope="session")
def mock_ollama_server_process() -> Generator[subprocess.Popen, None, None]:
    """Start FastAPI mock Ollama server for testing.

    Phase 3 rehabilitation: Makes orphaned mock functions testable.

    Yields:
        subprocess.Popen: Running mock server process
    """
    # Find the mock server script
    repo_root = Path(__file__).resolve().parents[2]  # tests/conftest.py -> NuSyQ-Hub/
    mock_script = repo_root / "deploy" / "ollama_mock" / "app_fastapi.py"

    if not mock_script.exists():
        pytest.skip(f"Mock server not found: {mock_script}")

    # Start the server
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "app_fastapi:app", "--host", "127.0.0.1", "--port", "8765"],
        cwd=mock_script.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready (max 5 seconds)
    for _ in range(50):
        try:
            response = requests.get("http://127.0.0.1:8765/health", timeout=1)
            if response.json().get("status") == "ok":
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            time.sleep(0.1)
    else:
        proc.terminate()
        pytest.fail("Mock Ollama server failed to start within 5 seconds")

    yield proc

    # Cleanup
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def mock_ollama_url(mock_ollama_server_process: subprocess.Popen) -> str:
    """Get the URL of the running mock Ollama server.

    Phase 3 rehabilitation: Simple URL fixture for tests that need the endpoint.

    Returns:
        str: Mock server base URL (e.g., "http://127.0.0.1:8765")
    """
    return "http://127.0.0.1:8765"


@pytest.fixture(scope="function")
def mock_ollama_client(mock_ollama_url: str):
    """Get a pre-configured client for the mock Ollama server.

    Phase 3 rehabilitation: High-level client fixture for convenience.

    Returns:
        object: Client configured to use mock server
    """
    from requests import Session

    session = Session()
    session.base_url = mock_ollama_url  # type: ignore

    # Add helper methods
    def health():
        return session.get(f"{mock_ollama_url}/health")

    def generate(prompt: str, model: str = "mock-ollama", scenario: str | None = None):
        payload = {"model": model, "prompt": prompt}
        params = {"scenario": scenario} if scenario else {}
        return session.post(f"{mock_ollama_url}/v1/generate", json=payload, params=params)

    def generate_stream(prompt: str, model: str = "mock-ollama"):
        payload = {"model": model, "prompt": prompt}
        return session.post(f"{mock_ollama_url}/v1/generate_stream", json=payload)

    def generate_sse(prompt: str, model: str = "mock-ollama"):
        payload = {"model": model, "prompt": prompt}
        return session.post(f"{mock_ollama_url}/v1/generate_sse", json=payload, stream=True)

    session.health = health  # type: ignore
    session.generate = generate  # type: ignore
    session.generate_stream = generate_stream  # type: ignore
    session.generate_sse = generate_sse  # type: ignore

    return session


@pytest.fixture(scope="session", autouse=False)
def use_mock_ollama_globally(mock_ollama_url: str, monkeypatch_session):
    """Auto-monkeypatch Ollama URLs to use mock server.

    Phase 3 rehabilitation: Global test isolation without explicit fixture use.

    When enabled (autouse=True), all Ollama requests go to mock automatically.
    """
    # This would monkeypatch environment variables or config
    monkeypatch_session.setenv("OLLAMA_BASE_URL", mock_ollama_url)
    monkeypatch_session.setenv("NUSYQ_MOCK_OLLAMA", "1")
    return mock_ollama_url


# Pytest plugin hook to enable --offline flag
def pytest_addoption(parser):
    """Add --offline flag to pytest for mock-only testing."""
    parser.addoption(
        "--offline",
        action="store_true",
        default=False,
        help="Run tests in offline mode using mock Ollama server",
    )


def pytest_configure(config):
    """Configure pytest with offline mode marker."""
    config.addinivalue_line("markers", "offline: mark test as requiring offline mock server")
    config.addinivalue_line("markers", "requires_ollama: mark test as requiring real Ollama")


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests based on --offline flag.

    Phase 3 rehabilitation: Smart test filtering for CI/CD and airplane mode.

    - If --offline: Skip tests marked "requires_ollama"
    - If NOT --offline: All tests run (mocks and real)
    """
    offline = config.getoption("--offline")

    skip_real = pytest.mark.skip(reason="--offline mode, skipping real Ollama tests")

    for item in items:
        if offline and "requires_ollama" in item.keywords:
            item.add_marker(skip_real)


# Session-scoped monkeypatch (for use_mock_ollama_globally)
@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch for global config changes."""
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()

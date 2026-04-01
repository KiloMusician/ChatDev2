"""Phase 3 smoke test: Verify mock Ollama infrastructure rehabilitation

Tests that rehabilitated orphaned mock functions are accessible via pytest fixtures.
"""

import pytest


@pytest.mark.offline
def test_mock_ollama_health(mock_ollama_client):
    """Test that mock Ollama server health endpoint works."""
    response = mock_ollama_client.health()
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.offline
def test_mock_ollama_generate(mock_ollama_client):
    """Test that mock Ollama generate endpoint works."""
    response = mock_ollama_client.generate("Hello, world!")
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "MOCK_RESPONSE" in data["response"]
    assert "Hello, world!" in data["response"]


@pytest.mark.offline
def test_mock_ollama_generate_stream(mock_ollama_client):
    """Test that mock Ollama streaming endpoint works."""
    response = mock_ollama_client.generate_stream("Stream test")
    assert response.status_code == 200
    data = response.json()
    assert "fragments" in data
    assert len(data["fragments"]) == 3
    assert all("MOCK_PART_" in frag for frag in data["fragments"])


@pytest.mark.offline
def test_mock_ollama_url_fixture(mock_ollama_url):
    """Test that URL fixture provides valid endpoint."""
    assert mock_ollama_url.startswith("http://")
    assert "8765" in mock_ollama_url  # Mock server port


def test_mock_ollama_optional(mock_ollama_client):
    """Test without offline marker - runs in both modes.

    This demonstrates that mock fixtures can be used even without --offline flag.
    """
    response = mock_ollama_client.health()
    assert response.status_code == 200


@pytest.mark.requires_ollama
def test_real_ollama_required():
    """Test that would require real Ollama (skipped in --offline mode).

    This demonstrates automatic test filtering based on --offline flag.
    """
    # This test is auto-skipped when pytest is run with --offline
    # It would connect to real Ollama server at http://localhost:11434
    pass

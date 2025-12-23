# test_ollama.py
import pytest
import httpx
from conftest import client, model_name
async def test_connection(client):
    """Test connection to localhost:11434"""
    response = await client.get("/")
    assert response.status_code == 200
async def test_model_listing(client):
    """Validate model listing and availability"""
    response = await client.get("/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert any(model["name"] == model_name for model in models)
async def test_model_inference(client, model_name):
    """Test model inference with qwen2.5-coder:7b"""
    payload = {
        "model": model_name,
        "prompt": "Hello, how are you?"
    }
    response = await client.post("/inference", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, dict)
    assert "response" in result
async def test_streaming_responses(client, model_name):
    """Test streaming responses"""
    payload = {
        "model": model_name,
        "prompt": "Hello, how are you?",
        "stream": True
    }
    async with client.stream("POST", "/inference", json=payload) as response:
        assert response.status_code == 200
        async for chunk in response.aiter_text():
            assert isinstance(chunk, str)
def test_error_handling_offline(client):
    """Include error handling for offline scenarios"""
    # Simulate an offline scenario by changing the base URL to a non-existent server
    client.base_url = "http://localhost:9999"
    with pytest.raises(httpx.ConnectError):
        response = client.get("/")
def test_performance_benchmarks(client, model_name):
    """Add performance benchmarks"""
    import time
    payload = {
        "model": model_name,
        "prompt": "Hello, how are you?"
    }
    start_time = time.time()
    response = client.post("/inference", json=payload)
    end_time = time.time()
    assert response.status_code == 200
    print(f"Response time: {end_time - start_time:.4f} seconds")
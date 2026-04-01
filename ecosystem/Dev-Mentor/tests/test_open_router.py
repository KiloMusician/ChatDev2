from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import llm_client as llm_client_module
import scripts.model_router as model_router_module
from services.router import OpenRouter, load_router_config
from services.router.router_config import EndpointConfig, RouterConfig, ServiceConfig


def test_load_router_config_expands_env(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_ROUTER_URL", "http://example.invalid")
    config_path = tmp_path / "router.yml"
    config_path.write_text(
        """
redis_url: "redis://localhost:6379"
services:
  llm:
    default_endpoint: primary
    endpoints:
      primary:
        provider: ollama
        url: "${TEST_ROUTER_URL:-http://fallback.invalid}"
        default_model: test-model
        """.strip(),
        encoding="utf-8",
    )

    config = load_router_config(config_path)
    endpoint = config.get_service("llm").endpoints["primary"]
    assert endpoint.url == "http://example.invalid"
    assert endpoint.default_model == "test-model"


def test_open_router_falls_back_to_next_endpoint(monkeypatch):
    service = ServiceConfig(
        name="llm",
        default_endpoint="first",
        action_routing={"generate": ["first", "second"]},
        endpoints={
            "first": EndpointConfig(id="first", provider="ollama", url="http://first"),
            "second": EndpointConfig(id="second", provider="ollama", url="http://second"),
        },
    )
    router = OpenRouter(RouterConfig(services={"llm": service}))

    async def fake_call(endpoint, action, request):
        if endpoint.id == "first":
            raise RuntimeError("boom")
        return {"model": "fallback-model", "output": "ok", "raw": {"ok": True}}

    monkeypatch.setattr(router, "_call_endpoint", fake_call)
    result = asyncio.run(router.route("llm", {"action": "generate", "prompt": "hello", "cache": False}))
    assert result["endpoint_id"] == "second"
    assert result["output"] == "ok"


def test_model_router_http_endpoints(monkeypatch):
    async def fake_route(service_name, request):
        return {
            "ok": True,
            "service": service_name,
            "action": request["action"],
            "endpoint_id": "ollama",
            "provider": "ollama",
            "model": "qwen2.5-coder:7b",
            "output": "hello",
            "raw": {"response": "hello"},
            "cached": False,
        }

    monkeypatch.setattr(model_router_module.OPEN_ROUTER, "route", fake_route)
    monkeypatch.setattr(
        model_router_module,
        "MODEL_REGISTRY",
        {
            "models": [
                {
                    "id": "fast-local",
                    "name": "Fast Local",
                    "provider": "ollama",
                    "endpoint": "http://localhost:11434",
                    "capabilities": ["chat"],
                    "priority": 10,
                    "hardware_requirement": "low",
                    "suitable_for": ["chat"],
                }
            ],
            "model_routing": {"rules": [{"task_type": "chat", "required_capabilities": ["chat"]}]},
        },
    )

    client = TestClient(model_router_module.app)
    route_response = client.post("/route/llm", json={"action": "generate", "prompt": "hi"})
    assert route_response.status_code == 200
    assert route_response.json()["output"] == "hello"

    legacy_response = client.post("/api/route", json={"task_type": "chat", "required_capabilities": ["chat"]})
    assert legacy_response.status_code == 200
    assert legacy_response.json()["model_id"] == "fast-local"


def test_llm_client_uses_router_when_enabled(monkeypatch):
    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"status={self.status_code}")

        def json(self):
            return self._payload

    monkeypatch.setenv("USE_ROUTER", "1")
    monkeypatch.setenv("MODEL_ROUTER_URL", "http://router.test:8080")
    monkeypatch.setattr(llm_client_module.requests, "get", lambda *args, **kwargs: FakeResponse(200, {"status": "healthy"}))
    monkeypatch.setattr(
        llm_client_module.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(200, {"output": "router-response"}),
    )

    client = llm_client_module.LLMClient(backend="auto")
    assert client.backend_name == "router"
    assert client.generate("hello from router") == "router-response"

#!/usr/bin/env python3
"""Terminal Depths — Open Router service.

Upgrades the existing model router into a resilient execution gateway while
preserving the legacy /api/route and /api/models endpoints used elsewhere in
the workspace.

New execution surface:
  POST /route/{service}

Compatibility surface:
  GET  /health
  GET  /metrics
  POST /api/route
  GET  /api/models
  GET  /api/models/{model_id}
  POST /api/discover
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

import httpx
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from services.router import (OpenRouter, RouterExecutionError,
                             load_router_config)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "models.yaml"
ROUTER_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "router.yml"

MODEL_REGISTRY = yaml.safe_load(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))
ROUTER_CONFIG = load_router_config(ROUTER_CONFIG_PATH)
OPEN_ROUTER = OpenRouter(ROUTER_CONFIG)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Open Router starting with config: %s", ROUTER_CONFIG_PATH)
    logger.info("Configured services: %s", ", ".join(sorted(ROUTER_CONFIG.services)))
    yield


app = FastAPI(
    title="Terminal Depths Open Router",
    description="Resilient AI service routing with fallbacks, retries, and compatibility endpoints.",
    version="2.0.0",
    lifespan=lifespan,
)


class ModelSelectionRequest(BaseModel):
    task_type: str
    required_capabilities: list[str] | None = None
    preferred_model: str | None = None
    timeout_sec: int = 10


class ModelSelectionResponse(BaseModel):
    model_id: str
    model_name: str
    endpoint: str
    openai_compatible: str | None = None
    capabilities: list[str]
    reasoning: str


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    capabilities: list[str]
    priority: int
    hardware_requirement: str
    suitable_for: list[str]


class RouteRequest(BaseModel):
    action: str
    prompt: str | None = None
    messages: list[dict[str, Any]] | None = None
    input: str | None = None
    system: str | None = None
    model: str | None = None
    max_tokens: int = Field(default=500, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    cache: bool = True
    cache_ttl: int | None = Field(default=None, ge=1, le=86400)
    user_id: str | None = None
    agent_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteExecutionResponse(BaseModel):
    ok: bool
    service: str
    action: str
    endpoint_id: str
    provider: str
    model: str | None = None
    output: Any
    raw: dict[str, Any] | None = None
    cached: bool = False


def _select_best_model(
    required_capabilities: list[str], preferred_model: str | None = None
) -> dict[str, Any] | None:
    models = MODEL_REGISTRY.get("models", [])
    if preferred_model:
        for model in models:
            if model.get("id") == preferred_model and all(
                capability in model.get("capabilities", [])
                for capability in required_capabilities
            ):
                return model

    matching_models = [
        model
        for model in models
        if all(
            capability in model.get("capabilities", [])
            for capability in required_capabilities
        )
    ]
    if not matching_models:
        return None
    matching_models.sort(key=lambda model: model.get("priority", 0), reverse=True)
    return matching_models[0]


def _route_by_task_type(task_type: str) -> dict[str, Any] | None:
    rules = MODEL_REGISTRY.get("model_routing", {}).get("rules", [])
    for rule in rules:
        if rule.get("task_type") != task_type:
            continue
        preferred = _select_best_model(
            rule.get("required_capabilities", []), rule.get("preferred_model")
        )
        if preferred:
            return preferred
        fallback_model = rule.get("fallback_model")
        if fallback_model:
            return _select_best_model(
                rule.get("required_capabilities", []), fallback_model
            )
    return None


async def _discover_ollama_models(base_url: str) -> list[str]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{base_url.rstrip('/')}/api/tags")
        response.raise_for_status()
        return [model.get("name", "") for model in response.json().get("models", [])]


@app.get("/health")
async def health_check() -> dict[str, Any]:
    router_health = await OPEN_ROUTER.health()
    llm_service = router_health["services"].get("llm", {})
    return {
        "status": router_health["status"],
        "router_config": str(ROUTER_CONFIG_PATH),
        "services": router_health["services"],
        "primary_endpoint": next(
            (ep for ep, ok in llm_service.get("endpoints", {}).items() if ok),
            (
                ROUTER_CONFIG.get_service("llm").default_endpoint
                if "llm" in ROUTER_CONFIG.services
                else None
            ),
        ),
        "llm_available": llm_service.get("healthy", False),
    }


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(
        OPEN_ROUTER.prometheus_metrics(), media_type="text/plain; version=0.0.4"
    )


@app.post("/route/{service_name}", response_model=RouteExecutionResponse)
async def route_service(
    service_name: str, request: RouteRequest
) -> RouteExecutionResponse:
    try:
        result = await OPEN_ROUTER.route(service_name, request.model_dump())
        return RouteExecutionResponse(**result)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RouterExecutionError as exc:
        raise HTTPException(
            status_code=503, detail={"message": str(exc), "errors": exc.errors}
        ) from exc


@app.post("/api/route", response_model=ModelSelectionResponse)
async def route_model(request: ModelSelectionRequest) -> ModelSelectionResponse:
    logger.info(
        "Legacy route request: task=%s caps=%s",
        request.task_type,
        request.required_capabilities,
    )
    model = _route_by_task_type(request.task_type)
    if not model and request.required_capabilities:
        model = _select_best_model(
            request.required_capabilities, request.preferred_model
        )
    if not model:
        raise HTTPException(
            status_code=404, detail=f"No model found for task: {request.task_type}"
        )
    return ModelSelectionResponse(
        model_id=model["id"],
        model_name=model["name"],
        endpoint=model["endpoint"],
        openai_compatible=model.get("openai_compatible"),
        capabilities=model.get("capabilities", []),
        reasoning=f"Selected {model['name']} for {request.task_type} (priority: {model.get('priority', 0)})",
    )


@app.get("/api/models", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id=model["id"],
            name=model["name"],
            provider=model["provider"],
            capabilities=model.get("capabilities", []),
            priority=model.get("priority", 0),
            hardware_requirement=model.get("hardware_requirement", "unknown"),
            suitable_for=model.get("suitable_for", []),
        )
        for model in MODEL_REGISTRY.get("models", [])
    ]


@app.get("/api/models/{model_id}")
async def get_model(model_id: str) -> dict[str, Any]:
    for model in MODEL_REGISTRY.get("models", []):
        if model.get("id") == model_id:
            return model
    raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")


@app.post("/api/discover")
async def discover_available_models() -> dict[str, list[str]]:
    discovered: dict[str, list[str]] = {}
    llm_service = ROUTER_CONFIG.get_service("llm")
    for endpoint in llm_service.endpoints.values():
        if endpoint.provider != "ollama" or not endpoint.enabled:
            continue
        try:
            discovered[endpoint.id] = await _discover_ollama_models(endpoint.url)
        except Exception as exc:
            logger.warning("Model discovery failed for %s: %s", endpoint.id, exc)
    return discovered


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "name": "Terminal Depths Open Router",
        "version": "2.0.0",
        "config": str(ROUTER_CONFIG_PATH),
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "metrics": "GET /metrics",
            "route_service": "POST /route/{service}",
            "legacy_route": "POST /api/route",
            "models": "GET /api/models",
        },
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MODEL_ROUTER_PORT", "9001"))
    logger.info("Starting Open Router on port %s", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

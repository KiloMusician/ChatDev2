from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import time
from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

from .router_config import EndpointConfig, RouterConfig, ServiceConfig

logger = logging.getLogger(__name__)


class RouterExecutionError(RuntimeError):
    def __init__(self, message: str, *, errors: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.errors = errors or []


class InMemoryStateStore:
    def __init__(self) -> None:
        self._values: dict[str, tuple[Any, float | None]] = {}
        self._counts: dict[str, tuple[int, float]] = {}
        self._lock = asyncio.Lock()

    async def get_json(self, key: str) -> Any | None:
        async with self._lock:
            value = self._values.get(key)
            if not value:
                return None
            payload, expires_at = value
            if expires_at is not None and expires_at <= time.time():
                self._values.pop(key, None)
                return None
            return payload

    async def set_json(self, key: str, payload: Any, ttl: int | None = None) -> None:
        async with self._lock:
            expires_at = time.time() + ttl if ttl else None
            self._values[key] = (payload, expires_at)

    async def incr_window(self, key: str, window_seconds: int) -> int:
        async with self._lock:
            count, expires_at = self._counts.get(key, (0, 0.0))
            now = time.time()
            if expires_at <= now:
                count = 0
                expires_at = now + window_seconds
            count += 1
            self._counts[key] = (count, expires_at)
            return count


class RedisStateStore:
    def __init__(self, redis_url: str):
        from redis import asyncio as redis_async

        self._client = redis_async.from_url(redis_url, decode_responses=True)

    async def get_json(self, key: str) -> Any | None:
        raw = await self._client.get(key)
        return json.loads(raw) if raw else None

    async def set_json(self, key: str, payload: Any, ttl: int | None = None) -> None:
        raw = json.dumps(payload)
        if ttl:
            await self._client.setex(key, ttl, raw)
        else:
            await self._client.set(key, raw)

    async def incr_window(self, key: str, window_seconds: int) -> int:
        async with self._client.pipeline(transaction=True) as pipe:
            current = await pipe.incr(key).expire(key, window_seconds, nx=True).execute()
        return int(current[0])


def _serialise_for_hash(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)


class OpenRouter:
    def __init__(self, config: RouterConfig):
        self.config = config
        self.metrics: dict[str, Any] = {
            "requests_total": defaultdict(int),
            "errors_total": defaultdict(int),
            "latency_seconds": defaultdict(float),
            "cache_hits_total": defaultdict(int),
            "fallbacks_total": defaultdict(int),
            "circuit_state": {},
        }
        self._store = self._build_store(config.redis_url)

    @staticmethod
    def _build_store(redis_url: str | None):
        if redis_url:
            try:
                return RedisStateStore(redis_url)
            except Exception as exc:
                logger.warning("Router falling back to in-memory state: %s", exc)
        return InMemoryStateStore()

    async def route(self, service_name: str, request: dict[str, Any]) -> dict[str, Any]:
        service = self.config.get_service(service_name)
        action = str(request.get("action") or "").strip().lower()
        if not action:
            raise RouterExecutionError("Missing router action")

        candidates = service.route_for_action(action)
        if not candidates:
            raise RouterExecutionError(f"No endpoints configured for service '{service_name}' action '{action}'")

        cache_key = self._cache_key(service_name, request)
        if request.get("cache", True):
            cached = await self._store.get_json(cache_key)
            if cached is not None:
                self.metrics["cache_hits_total"][service_name] += 1
                return {**cached, "cached": True}

        errors: list[dict[str, Any]] = []
        for index, endpoint in enumerate(candidates):
            if not endpoint.enabled:
                continue
            limited = await self._is_rate_limited(service, endpoint, request)
            if limited:
                errors.append({"endpoint_id": endpoint.id, "error": "rate_limited"})
                continue
            if not await self._circuit_allows(service, endpoint):
                errors.append({"endpoint_id": endpoint.id, "error": "circuit_open"})
                continue

            started = time.perf_counter()
            try:
                result = await self._call_with_retry(service, endpoint, action, request)
                latency = time.perf_counter() - started
                await self._record_success(service, endpoint)
                await self._cache_result(cache_key, request, service, endpoint, result)
                self.metrics["requests_total"][service_name] += 1
                self.metrics["latency_seconds"][service_name] += latency
                if index > 0:
                    self.metrics["fallbacks_total"][service_name] += index
                return {
                    "ok": True,
                    "service": service_name,
                    "action": action,
                    "endpoint_id": endpoint.id,
                    "provider": endpoint.provider,
                    "model": result.get("model"),
                    "output": result.get("output"),
                    "raw": result.get("raw"),
                    "cached": False,
                }
            except Exception as exc:
                await self._record_failure(service, endpoint)
                self.metrics["errors_total"][service_name] += 1
                errors.append({"endpoint_id": endpoint.id, "error": str(exc)})
                logger.warning("Router endpoint failed: service=%s endpoint=%s error=%s", service.name, endpoint.id, exc)

        raise RouterExecutionError(f"All router endpoints failed for service '{service_name}' action '{action}'", errors=errors)

    async def health(self) -> dict[str, Any]:
        services: dict[str, Any] = {}
        overall = "healthy"
        for service_name, service in self.config.services.items():
            service_state = {"endpoints": {}, "healthy": False}
            for endpoint in service.endpoints.values():
                healthy = endpoint.enabled and await self._endpoint_health(endpoint)
                service_state["endpoints"][endpoint.id] = healthy
                service_state["healthy"] = service_state["healthy"] or healthy
            if not service_state["healthy"]:
                overall = "degraded"
            services[service_name] = service_state
        return {"status": overall, "services": services}

    async def _endpoint_health(self, endpoint: EndpointConfig) -> bool:
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                if endpoint.provider == "ollama":
                    response = await client.get(f"{endpoint.url.rstrip('/')}/api/tags")
                elif endpoint.provider == "lmstudio":
                    health_url = self._lmstudio_health_url(endpoint.url)
                    response = await client.get(health_url)
                elif endpoint.provider == "openai":
                    return self._has_auth(endpoint)
                elif endpoint.provider == "anthropic":
                    return self._has_auth(endpoint)
                else:
                    response = await client.get(endpoint.url)
                return response.status_code < 500
        except Exception:
            return False

    @staticmethod
    def _lmstudio_health_url(url: str) -> str:
        parsed = urlsplit(url)
        path = parsed.path.rstrip("/")
        if path.endswith("/chat/completions"):
            path = path[: -len("/chat/completions")] + "/models"
        elif not path.endswith("/models"):
            path = f"{path}/models" if path else "/v1/models"
        return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))

    @staticmethod
    def _has_auth(endpoint: EndpointConfig) -> bool:
        if endpoint.auth == "none":
            return True
        if endpoint.auth == "bearer" and endpoint.auth_env:
            return bool(__import__("os").environ.get(endpoint.auth_env, ""))
        if endpoint.auth == "anthropic" and endpoint.auth_env:
            return bool(__import__("os").environ.get(endpoint.auth_env, ""))
        return False

    async def _is_rate_limited(self, service: ServiceConfig, endpoint: EndpointConfig, request: dict[str, Any]) -> bool:
        policy = endpoint.rate_limit
        if not policy:
            return False
        actor = str(request.get("agent_id") or request.get("user_id") or "anonymous")
        key = f"router:rate:{service.name}:{endpoint.id}:{actor}"
        count = await self._store.incr_window(key, policy.window_seconds)
        return count > policy.max_requests

    async def _circuit_allows(self, service: ServiceConfig, endpoint: EndpointConfig) -> bool:
        key = f"router:circuit:{service.name}:{endpoint.id}"
        state = await self._store.get_json(key) or {"state": "closed", "failures": 0}
        self.metrics["circuit_state"][f"{service.name}:{endpoint.id}"] = state.get("state", "closed")
        if state.get("state") != "open":
            return True
        opens_until = float(state.get("opens_until", 0))
        if opens_until <= time.time():
            await self._store.set_json(key, {"state": "half_open", "failures": state.get("failures", 0)}, ttl=endpoint.circuit_breaker.recovery_timeout)
            self.metrics["circuit_state"][f"{service.name}:{endpoint.id}"] = "half_open"
            return True
        return False

    async def _record_success(self, service: ServiceConfig, endpoint: EndpointConfig) -> None:
        key = f"router:circuit:{service.name}:{endpoint.id}"
        await self._store.set_json(key, {"state": "closed", "failures": 0}, ttl=endpoint.circuit_breaker.recovery_timeout)
        self.metrics["circuit_state"][f"{service.name}:{endpoint.id}"] = "closed"

    async def _record_failure(self, service: ServiceConfig, endpoint: EndpointConfig) -> None:
        key = f"router:circuit:{service.name}:{endpoint.id}"
        state = await self._store.get_json(key) or {"state": "closed", "failures": 0}
        failures = int(state.get("failures", 0)) + 1
        payload: dict[str, Any] = {"state": "closed", "failures": failures}
        if failures >= endpoint.circuit_breaker.failure_threshold:
            payload = {
                "state": "open",
                "failures": failures,
                "opens_until": time.time() + endpoint.circuit_breaker.recovery_timeout,
            }
        await self._store.set_json(key, payload, ttl=endpoint.circuit_breaker.recovery_timeout)
        self.metrics["circuit_state"][f"{service.name}:{endpoint.id}"] = payload["state"]

    async def _call_with_retry(self, service: ServiceConfig, endpoint: EndpointConfig, action: str, request: dict[str, Any]) -> dict[str, Any]:
        attempts = max(endpoint.retry.attempts, 1)
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return await self._call_endpoint(endpoint, action, request)
            except Exception as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                sleep_for = endpoint.retry.backoff ** (attempt - 1)
                sleep_for += random.uniform(0, endpoint.retry.jitter)
                await asyncio.sleep(sleep_for)
        raise RouterExecutionError(f"{service.name}:{endpoint.id} failed after {attempts} attempt(s): {last_error!r}")

    async def _call_endpoint(self, endpoint: EndpointConfig, action: str, request: dict[str, Any]) -> dict[str, Any]:
        headers = dict(endpoint.headers)
        self._apply_auth(endpoint, headers)
        model = endpoint.resolve_model(request.get("model"))
        async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
            if endpoint.provider == "ollama":
                url, payload = self._build_ollama_request(endpoint, action, request, model)
                response = await client.post(url, json=payload, headers=headers)
            elif endpoint.provider in {"openai", "lmstudio"}:
                url, payload = self._build_openai_request(endpoint, action, request, model)
                response = await client.post(url, json=payload, headers=headers)
            elif endpoint.provider == "anthropic":
                url, payload = self._build_anthropic_request(endpoint, action, request, model)
                headers.setdefault("anthropic-version", "2023-06-01")
                response = await client.post(url, json=payload, headers=headers)
            else:
                raise RouterExecutionError(f"Unsupported router provider: {endpoint.provider}")

        response.raise_for_status()
        data = response.json()
        return {
            "model": model,
            "output": self._extract_output(endpoint.provider, data),
            "raw": data,
        }

    def _apply_auth(self, endpoint: EndpointConfig, headers: dict[str, str]) -> None:
        if endpoint.auth == "bearer" and endpoint.auth_env:
            env_token = endpoint.auth_env and __import__("os").environ.get(endpoint.auth_env, "")
            if env_token:
                headers["Authorization"] = f"Bearer {env_token}"
        elif endpoint.auth == "anthropic" and endpoint.auth_env:
            env_token = __import__("os").environ.get(endpoint.auth_env, "")
            if env_token:
                headers["x-api-key"] = env_token

    def _build_ollama_request(self, endpoint: EndpointConfig, action: str, request: dict[str, Any], model: str | None) -> tuple[str, dict[str, Any]]:
        base = endpoint.url.rstrip("/")
        options = {
            "num_predict": int(request.get("max_tokens", 500)),
            "temperature": float(request.get("temperature", 0.7)),
        }
        if action == "chat":
            return (
                f"{base}{endpoint.paths.get('chat', '/api/chat')}",
                {
                    "model": model,
                    "messages": request.get("messages") or self._messages_from_request(request),
                    "stream": False,
                    "options": options,
                },
            )
        return (
            f"{base}{endpoint.paths.get('generate', '/api/generate')}",
            {
                "model": model,
                "prompt": request.get("prompt") or request.get("input") or "",
                "system": request.get("system"),
                "stream": False,
                "options": options,
            },
        )

    def _build_openai_request(self, endpoint: EndpointConfig, action: str, request: dict[str, Any], model: str | None) -> tuple[str, dict[str, Any]]:
        return (
            endpoint.url,
            {
                "model": model,
                "messages": request.get("messages") or self._messages_from_request(request),
                "max_tokens": int(request.get("max_tokens", 500)),
                "temperature": float(request.get("temperature", 0.7)),
            },
        )

    def _build_anthropic_request(self, endpoint: EndpointConfig, action: str, request: dict[str, Any], model: str | None) -> tuple[str, dict[str, Any]]:
        messages = request.get("messages") or self._messages_from_request(request, include_system=False)
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": int(request.get("max_tokens", 500)),
            "temperature": float(request.get("temperature", 0.7)),
            "messages": messages,
        }
        if request.get("system"):
            payload["system"] = request["system"]
        return endpoint.url, payload

    @staticmethod
    def _messages_from_request(request: dict[str, Any], include_system: bool = True) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        system = request.get("system")
        prompt = request.get("prompt") or request.get("input")
        if include_system and system:
            messages.append({"role": "system", "content": system})
        if prompt:
            messages.append({"role": "user", "content": str(prompt)})
        return messages

    @staticmethod
    def _extract_output(provider: str, data: dict[str, Any]) -> str:
        if provider == "ollama":
            if "response" in data:
                return str(data["response"]).strip()
            message = data.get("message") or {}
            return str(message.get("content", "")).strip()
        if provider in {"openai", "lmstudio"}:
            choices = data.get("choices") or []
            if choices:
                message = choices[0].get("message") or {}
                return str(message.get("content", "")).strip()
        if provider == "anthropic":
            content = data.get("content") or []
            parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            return "".join(parts).strip()
        return json.dumps(data, ensure_ascii=False)

    async def _cache_result(self, cache_key: str, request: dict[str, Any], service: ServiceConfig, endpoint: EndpointConfig, result: dict[str, Any]) -> None:
        if not request.get("cache", True):
            return
        ttl = int(request.get("cache_ttl") or endpoint.cache_ttl or service.cache_ttl)
        await self._store.set_json(cache_key, {
            "ok": True,
            "service": service.name,
            "action": request.get("action"),
            "endpoint_id": endpoint.id,
            "provider": endpoint.provider,
            "model": result.get("model"),
            "output": result.get("output"),
            "raw": result.get("raw"),
        }, ttl=ttl)

    @staticmethod
    def _cache_key(service_name: str, request: dict[str, Any]) -> str:
        canonical = {
            "service": service_name,
            "action": request.get("action"),
            "prompt": request.get("prompt"),
            "messages": request.get("messages"),
            "system": request.get("system"),
            "model": request.get("model"),
            "max_tokens": request.get("max_tokens"),
            "temperature": request.get("temperature"),
        }
        digest = hashlib.sha256(_serialise_for_hash(canonical).encode("utf-8")).hexdigest()
        return f"router:cache:{service_name}:{digest}"

    def prometheus_metrics(self) -> str:
        lines = [
            "# HELP open_router_requests_total Total routed requests by service.",
            "# TYPE open_router_requests_total counter",
        ]
        for service, count in self.metrics["requests_total"].items():
            lines.append(f'open_router_requests_total{{service="{service}"}} {count}')
        lines.extend([
            "# HELP open_router_errors_total Total routed errors by service.",
            "# TYPE open_router_errors_total counter",
        ])
        for service, count in self.metrics["errors_total"].items():
            lines.append(f'open_router_errors_total{{service="{service}"}} {count}')
        lines.extend([
            "# HELP open_router_cache_hits_total Total cache hits by service.",
            "# TYPE open_router_cache_hits_total counter",
        ])
        for service, count in self.metrics["cache_hits_total"].items():
            lines.append(f'open_router_cache_hits_total{{service="{service}"}} {count}')
        lines.extend([
            "# HELP open_router_fallbacks_total Total fallback hops by service.",
            "# TYPE open_router_fallbacks_total counter",
        ])
        for service, count in self.metrics["fallbacks_total"].items():
            lines.append(f'open_router_fallbacks_total{{service="{service}"}} {count}')
        lines.extend([
            "# HELP open_router_latency_seconds_total Aggregate routed latency by service.",
            "# TYPE open_router_latency_seconds_total counter",
        ])
        for service, total_latency in self.metrics["latency_seconds"].items():
            lines.append(f'open_router_latency_seconds_total{{service="{service}"}} {total_latency}')
        lines.extend([
            "# HELP open_router_circuit_state Circuit breaker state per endpoint (0=closed, 0.5=half_open, 1=open).",
            "# TYPE open_router_circuit_state gauge",
        ])
        state_values = {"closed": 0.0, "half_open": 0.5, "open": 1.0}
        for target, state in self.metrics["circuit_state"].items():
            service, endpoint = target.split(":", 1)
            lines.append(
                f'open_router_circuit_state{{service="{service}",endpoint="{endpoint}",state="{state}"}} {state_values.get(state, -1.0)}'
            )
        return "\n".join(lines) + "\n"

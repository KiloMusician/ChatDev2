from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


_ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::-(.*?))?\}")


def _expand_env_scalar(value: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2) or ""
        return os.environ.get(var_name, default)

    return _ENV_PATTERN.sub(_replace, value)


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return _expand_env_scalar(value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


@dataclass(slots=True)
class RetryPolicy:
    attempts: int = 2
    backoff: float = 1.5
    jitter: float = 0.1


@dataclass(slots=True)
class CircuitBreakerPolicy:
    failure_threshold: int = 3
    recovery_timeout: int = 30


@dataclass(slots=True)
class RateLimitPolicy:
    window_seconds: int = 60
    max_requests: int = 120


@dataclass(slots=True)
class EndpointConfig:
    id: str
    provider: str
    url: str
    timeout: float = 30.0
    auth: str = "none"
    auth_env: str | None = None
    enabled_if_env: str | None = None
    models: list[str] = field(default_factory=list)
    default_model: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    paths: dict[str, str] = field(default_factory=dict)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    circuit_breaker: CircuitBreakerPolicy = field(default_factory=CircuitBreakerPolicy)
    rate_limit: RateLimitPolicy | None = None
    cache_ttl: int = 300

    @property
    def enabled(self) -> bool:
        if self.enabled_if_env and not os.environ.get(self.enabled_if_env):
            return False
        return bool(self.url.strip())

    def resolve_model(self, requested_model: str | None = None) -> str | None:
        if requested_model:
            return requested_model
        if self.default_model:
            return self.default_model
        if self.models:
            return self.models[0]
        return None


@dataclass(slots=True)
class ServiceConfig:
    name: str
    description: str = ""
    default_endpoint: str = ""
    action_routing: dict[str, list[str]] = field(default_factory=dict)
    endpoints: dict[str, EndpointConfig] = field(default_factory=dict)
    cache_ttl: int = 300

    def route_for_action(self, action: str) -> list[EndpointConfig]:
        endpoint_ids = self.action_routing.get(action) or ([self.default_endpoint] if self.default_endpoint else [])
        ordered: list[EndpointConfig] = []
        seen: set[str] = set()
        for endpoint_id in endpoint_ids:
            endpoint = self.endpoints.get(endpoint_id)
            if endpoint and endpoint.id not in seen:
                ordered.append(endpoint)
                seen.add(endpoint.id)
        if self.default_endpoint and self.default_endpoint not in seen:
            endpoint = self.endpoints.get(self.default_endpoint)
            if endpoint:
                ordered.append(endpoint)
                seen.add(endpoint.id)
        for endpoint in self.endpoints.values():
            if endpoint.id not in seen:
                ordered.append(endpoint)
        return ordered


@dataclass(slots=True)
class RouterConfig:
    services: dict[str, ServiceConfig]
    redis_url: str | None = None

    def get_service(self, service_name: str) -> ServiceConfig:
        try:
            return self.services[service_name]
        except KeyError as exc:
            raise KeyError(f"Unknown router service: {service_name}") from exc


def _build_endpoint(endpoint_id: str, payload: dict[str, Any]) -> EndpointConfig:
    retry_cfg = payload.get("retry") or {}
    circuit_cfg = payload.get("circuit_breaker") or {}
    rate_limit_cfg = payload.get("rate_limit")
    endpoint = EndpointConfig(
        id=endpoint_id,
        provider=str(payload.get("provider", "generic")),
        url=str(payload.get("url", "")),
        timeout=float(payload.get("timeout", 30)),
        auth=str(payload.get("auth", "none")),
        auth_env=payload.get("auth_env"),
        enabled_if_env=payload.get("enabled_if_env"),
        models=list(payload.get("models") or []),
        default_model=payload.get("default_model"),
        headers=dict(payload.get("headers") or {}),
        paths=dict(payload.get("paths") or {}),
        retry=RetryPolicy(
            attempts=int(retry_cfg.get("attempts", 2)),
            backoff=float(retry_cfg.get("backoff", 1.5)),
            jitter=float(retry_cfg.get("jitter", 0.1)),
        ),
        circuit_breaker=CircuitBreakerPolicy(
            failure_threshold=int(circuit_cfg.get("failure_threshold", 3)),
            recovery_timeout=int(circuit_cfg.get("recovery_timeout", 30)),
        ),
        cache_ttl=int(payload.get("cache_ttl", 300)),
    )
    if rate_limit_cfg:
        endpoint.rate_limit = RateLimitPolicy(
            window_seconds=int(rate_limit_cfg.get("window_seconds", 60)),
            max_requests=int(rate_limit_cfg.get("max_requests", 120)),
        )
    return endpoint


def load_router_config(config_path: str | Path | None = None) -> RouterConfig:
    path = Path(config_path or os.environ.get("ROUTER_CONFIG_PATH") or Path(__file__).resolve().parents[2] / "config" / "router.yml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = _expand_env(raw)

    services: dict[str, ServiceConfig] = {}
    service_blocks = raw.get("services") or {}
    if isinstance(service_blocks, list):
        iterable = []
        for item in service_blocks:
            if isinstance(item, dict) and item.get("name"):
                iterable.append((str(item["name"]), item))
    else:
        iterable = [(str(name), data) for name, data in service_blocks.items()]

    for service_name, payload in iterable:
        endpoints_payload = payload.get("endpoints") or {}
        if isinstance(endpoints_payload, list):
            endpoints = {
                str(item["id"]): _build_endpoint(str(item["id"]), item)
                for item in endpoints_payload
                if isinstance(item, dict) and item.get("id")
            }
        else:
            endpoints = {
                str(endpoint_id): _build_endpoint(str(endpoint_id), endpoint_payload)
                for endpoint_id, endpoint_payload in endpoints_payload.items()
            }

        services[service_name] = ServiceConfig(
            name=service_name,
            description=str(payload.get("description", "")),
            default_endpoint=str(payload.get("default_endpoint", "")),
            action_routing={str(k): list(v or []) for k, v in (payload.get("action_routing") or {}).items()},
            endpoints=endpoints,
            cache_ttl=int(payload.get("cache_ttl", 300)),
        )

    return RouterConfig(
        services=services,
        redis_url=raw.get("redis_url") or os.environ.get("REDIS_URL"),
    )

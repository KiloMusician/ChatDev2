"""Universal LLM Gateway adapter (Phase 2).

Routes requests across providers (OpenAI, Ollama, ChatDev, MCP) based on
capability tags, cost/latency preferences, and explicit hints.
Returns a routing decision plus a placeholder response envelope; actual
provider clients can be plugged in later.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from src.config.feature_flag_manager import is_feature_enabled
from src.system.telemetry import log_span

MODEL_CAPS_PATH = Path("config") / "model_capabilities.json"
_CAPS_CACHE: list[ModelCapability] | None = None
_CAPS_CACHE_AT: float | None = None


def _env_flag_enabled(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _caps_cache_ttl() -> int:
    return int(os.getenv("NUSYQ_MODEL_CAPS_TTL_SECONDS", "300"))


def _tag_model_name(model_name: str) -> list[str]:
    lowered = model_name.lower()
    tags: list[str] = []
    if any(token in lowered for token in ("code", "coder", "qwen", "codellama", "starcoder")):
        tags.append("code")
    if any(token in lowered for token in ("llama", "mistral", "phi", "gemma")):
        tags.append("general")
    if "reason" in lowered:
        tags.append("reasoning")
    return tags


def _normalize_base_url(base_url: str, strip_v1: bool = False) -> str:
    normalized = base_url.rstrip("/")
    if strip_v1 and normalized.endswith("/v1"):
        normalized = normalized[: -len("/v1")]
    return normalized


def _discover_ollama_models() -> list[ModelCapability]:
    base_url = (
        os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_API_BASE") or "http://localhost:11434"
    )
    base_url = _normalize_base_url(base_url, strip_v1=True)
    timeout = float(os.getenv("NUSYQ_LLM_DISCOVERY_TIMEOUT", "5"))

    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        return []

    models = payload.get("models", []) if isinstance(payload, dict) else []
    results: list[ModelCapability] = []
    for model in models:
        name = model.get("name") if isinstance(model, dict) else None
        if not name:
            continue
        tags = ["local", *_tag_model_name(name)]
        results.append(
            ModelCapability(
                provider="ollama",
                model=name,
                tags=list(dict.fromkeys(tags)),
                cost="low",
                latency="low",
            )
        )
    return results


def _discover_lmstudio_models() -> list[ModelCapability]:
    base_url = os.getenv("LMSTUDIO_BASE_URL") or os.getenv("NUSYQ_LMSTUDIO_BASE_URL")
    if not base_url:
        return []
    base_url = _normalize_base_url(base_url, strip_v1=False)
    timeout = float(os.getenv("NUSYQ_LLM_DISCOVERY_TIMEOUT", "5"))

    try:
        resp = httpx.get(f"{base_url}/v1/models", timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        return []

    data = payload.get("data", []) if isinstance(payload, dict) else []
    results: list[ModelCapability] = []
    for entry in data:
        model_id = entry.get("id") if isinstance(entry, dict) else None
        if not model_id:
            continue
        tags = ["local", *_tag_model_name(model_id)]
        results.append(
            ModelCapability(
                provider="lmstudio",
                model=model_id,
                tags=list(dict.fromkeys(tags)),
                cost="low",
                latency="low",
            )
        )
    return results


def _merge_capabilities(
    static_caps: list[ModelCapability],
    discovered_caps: list[ModelCapability],
) -> list[ModelCapability]:
    merged: dict[tuple[str, str], ModelCapability] = {
        (cap.provider, cap.model): cap for cap in static_caps
    }
    for cap in discovered_caps:
        merged[(cap.provider, cap.model)] = cap
    return list(merged.values())


def _persist_model_capabilities(capabilities: list[ModelCapability]) -> None:
    if not _env_flag_enabled("NUSYQ_MODEL_CAPS_PERSIST", default=True):
        return
    # Use dict format with provider:model keys for human readability
    payload = {
        f"{cap.provider}:{cap.model}": {
            "tags": cap.tags,
            "cost": cap.cost,
            "latency": cap.latency,
        }
        for cap in capabilities
    }
    try:
        MODEL_CAPS_PATH.parent.mkdir(parents=True, exist_ok=True)
        MODEL_CAPS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        # Best-effort persistence; ignore failures
        return


def _emit_provider_event(
    provider: str,
    event_type: str,
    message: str,
    level: str = "INFO",
    extra: dict[str, Any] | None = None,
) -> None:
    """Best-effort mirror of provider activity to specialized agent terminals."""
    try:
        from src.system.agent_awareness import emit

        emit.event(
            provider,
            event_type,
            {
                "message": message,
                **(extra or {}),
            },
            level=level,
        )
    except Exception:
        return


@dataclass
class ModelCapability:
    provider: str
    model: str
    tags: list[str]
    cost: str = "unknown"
    latency: str = "unknown"


def load_model_capabilities() -> list[ModelCapability]:
    global _CAPS_CACHE, _CAPS_CACHE_AT

    if (
        _CAPS_CACHE is not None
        and _CAPS_CACHE_AT is not None
        and time.time() - _CAPS_CACHE_AT < _caps_cache_ttl()
    ):
        return _CAPS_CACHE

    static_caps: list[ModelCapability] = []
    if MODEL_CAPS_PATH.exists():
        data = json.loads(MODEL_CAPS_PATH.read_text())
        # Support both dict and list formats
        if isinstance(data, dict):
            static_caps = [
                ModelCapability(
                    provider=key.split(":", 1)[0],
                    model=key.split(":", 1)[1],
                    tags=value.get("tags", []),
                    cost=value.get("cost", "unknown"),
                    latency=value.get("latency", "unknown"),
                )
                for key, value in data.items()
            ]
        else:
            # Legacy list format
            static_caps = [
                ModelCapability(
                    provider=item.get("provider", "openai"),
                    model=item.get("model", ""),
                    tags=item.get("tags", []),
                    cost=item.get("cost", "unknown"),
                    latency=item.get("latency", "unknown"),
                )
                for item in data
            ]

    discovered: list[ModelCapability] = []
    if _env_flag_enabled("NUSYQ_MODEL_DISCOVERY", default=True):
        discovered.extend(_discover_ollama_models())
        discovered.extend(_discover_lmstudio_models())

    merged = _merge_capabilities(static_caps, discovered)
    _CAPS_CACHE = merged
    _CAPS_CACHE_AT = time.time()
    _persist_model_capabilities(merged)
    return merged


class UniversalLLMGateway:
    def __init__(
        self, capabilities: list[ModelCapability] | None = None, dry_run: bool = True
    ) -> None:
        """Initialize UniversalLLMGateway with capabilities, dry_run."""
        self.capabilities = capabilities or load_model_capabilities()
        self.dry_run = dry_run or not os.getenv("OPENAI_API_KEY")

    def select_model(
        self,
        model_hint: str | None,
        capability_tags: list[str],
        prefer_local: bool = False,
        max_cost: str | None = None,
    ) -> ModelCapability | None:
        candidates = self.capabilities

        # Explicit hint wins
        if model_hint:
            for cap in candidates:
                if cap.model == model_hint:
                    return cap

        # Filter by local preference
        if prefer_local:
            local = [c for c in candidates if "local" in c.tags]
            if local:
                candidates = local

        # Filter by capability tags
        if capability_tags:
            tagged = [c for c in candidates if all(tag in c.tags for tag in capability_tags)]
            if tagged:
                candidates = tagged

        # Filter by cost if provided
        if max_cost:
            cost_order = {"low": 0, "medium": 1, "high": 2, "variable": 3, "unknown": 4}
            candidates = [
                c for c in candidates if cost_order.get(c.cost, 4) <= cost_order.get(max_cost, 4)
            ]

        return candidates[0] if candidates else None

    def route_request(
        self,
        prompt: str,
        model_hint: str | None = None,
        capability_tags: list[str] | None = None,
        prefer_local: bool = False,
        max_cost: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not is_feature_enabled("gateway_router_enabled"):
            return {"error": "gateway_router_disabled"}

        cap = self.select_model(model_hint, capability_tags or [], prefer_local, max_cost)
        if not cap:
            return {"error": "no_model_available", "models_seen": len(self.capabilities)}

        if self.dry_run:
            log_span(
                "llm_route",
                {
                    "provider": cap.provider,
                    "model": cap.model,
                    "dry_run": True,
                    "tags": cap.tags,
                },
            )
            return {
                "routed": True,
                "provider": cap.provider,
                "model": cap.model,
                "capability_tags": cap.tags,
                "cost": cap.cost,
                "latency": cap.latency,
                "echo": prompt[:200],
                "dry_run": True,
                "metadata": metadata or {},
            }

        # Real call routing
        if cap.provider == "openai":
            out = self._call_openai(cap.model, prompt, metadata)
            log_span(
                "llm_route", {"provider": "openai", "model": cap.model, "error": out.get("error")}
            )
            return out
        if cap.provider == "ollama":
            out = self._call_ollama(cap.model, prompt, metadata)
            log_span(
                "llm_route", {"provider": "ollama", "model": cap.model, "error": out.get("error")}
            )
            return out
        if cap.provider == "lmstudio":
            out = self._call_lmstudio(cap.model, prompt, metadata)
            log_span(
                "llm_route",
                {"provider": "lmstudio", "model": cap.model, "error": out.get("error")},
            )
            return out
        if cap.provider == "chatdev":
            log_span("llm_route", {"provider": "chatdev", "model": cap.model})
            return {
                "routed": True,
                "provider": "chatdev",
                "model": cap.model,
                "message": "invoke ChatDev pipeline",
            }
        return {"error": f"unsupported provider {cap.provider}"}

    def _call_openai(
        self, model: str, prompt: str, metadata: dict[str, Any] | None
    ) -> dict[str, Any]:
        try:
            import openai

            client = openai.OpenAI()
            started = time.time()
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=512,
            )
            duration = time.time() - started
            content = resp.choices[0].message.content if resp.choices else ""
            return {
                "routed": True,
                "provider": "openai",
                "model": model,
                "duration_s": duration,
                "output": content,
                "metadata": metadata or {},
            }
        except Exception as e:
            return {"error": f"openai_call_failed: {e}"}

    def _call_ollama(
        self, model: str, prompt: str, metadata: dict[str, Any] | None
    ) -> dict[str, Any]:
        base_url = (
            os.getenv("OLLAMA_API_BASE")
            or os.getenv("OLLAMA_BASE_URL")
            or os.getenv("BASE_URL")
            or "http://localhost:11434/v1"
        )
        base_url = _normalize_base_url(base_url, strip_v1=False)
        url = f"{base_url}/chat/completions"
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        try:
            started = time.time()
            resp = httpx.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            duration = time.time() - started
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            _emit_provider_event(
                "ollama",
                "model_invocation",
                f"{model} responded in {duration:.2f}s",
                extra={"model": model, "duration_s": round(duration, 3)},
            )
            return {
                "routed": True,
                "provider": "ollama",
                "model": model,
                "duration_s": duration,
                "output": content,
                "metadata": metadata or {},
            }
        except Exception as e:
            _emit_provider_event(
                "ollama",
                "model_invocation_failed",
                f"{model} failed via UniversalLLMGateway",
                level="ERROR",
                extra={"model": model, "url": url, "error": str(e)},
            )
            return {"error": f"ollama_call_failed: {e}", "url": url}

    def _call_lmstudio(
        self, model: str, prompt: str, metadata: dict[str, Any] | None
    ) -> dict[str, Any]:
        base_url = os.getenv("LMSTUDIO_BASE_URL") or os.getenv("NUSYQ_LMSTUDIO_BASE_URL")
        if not base_url:
            return {"error": "lmstudio_base_url_missing"}
        base_url = _normalize_base_url(base_url, strip_v1=False)
        url = f"{base_url}/v1/chat/completions"
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        try:
            started = time.time()
            resp = httpx.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            duration = time.time() - started
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            _emit_provider_event(
                "lmstudio",
                "model_invocation",
                f"{model} responded in {duration:.2f}s",
                extra={"model": model, "duration_s": round(duration, 3)},
            )
            return {
                "routed": True,
                "provider": "lmstudio",
                "model": model,
                "duration_s": duration,
                "output": content,
                "metadata": metadata or {},
            }
        except Exception as e:
            _emit_provider_event(
                "lmstudio",
                "model_invocation_failed",
                f"{model} failed via UniversalLLMGateway",
                level="ERROR",
                extra={"model": model, "url": url, "error": str(e)},
            )
            return {"error": f"lmstudio_call_failed: {e}", "url": url}

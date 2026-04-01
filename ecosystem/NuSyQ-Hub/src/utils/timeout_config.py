"""Timeout configuration helpers.

Centralize environment-driven timeout lookups. Prefer environment variables for
service-specific overrides. For Ollama-specific settings we expose helpers too.

Env vars supported (examples):
- HTTP_TIMEOUT_SECONDS                (global default for HTTP calls)
- OLLAMA_HTTP_TIMEOUT_SECONDS         (Ollama HTTP probe/generate timeout)
- SIMULATEDVERSE_HTTP_TIMEOUT_SECONDS (SimulatedVerse HTTP calls)
- OLLAMA_MAX_TIMEOUT_SECONDS         (max allowed subprocess timeout for Ollama; if unset -> None)
- OLLAMA_ADAPTIVE_TIMEOUT            (set to '1' or 'true' to enable adaptive)
"""

from __future__ import annotations

import logging
import os

from src.utils.intelligent_timeout_manager import \
    get_adaptive_timeout as _adaptive

logger = logging.getLogger(__name__)


def _env_int(name: str) -> int | None:
    v = os.getenv(name)
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None


def get_timeout(
    key: str,
    default: int | None = None,
    *,
    complexity: float = 1.0,
    priority: str = "normal",
) -> int | None:
    """Flexible timeout getter.

    Behaviors:
    - If `key` looks like an ENV var name (contains uppercase or underscores),
      return the ENV-driven timeout (or default).
    - Otherwise, treat `key` as a service name and return an adaptive timeout.
    """
    # Heuristic: ENV var names are typically uppercase/with underscores
    if key.isupper():
        val = _env_int(key)
        return val if val is not None else default

    # Service-based adaptive timeout
    try:
        return _adaptive(key, complexity=complexity, priority=priority)
    except Exception:
        # Fallback to default if adaptive manager is unavailable
        return default or 30


def get_http_timeout(service: str | None = None, default: int = 10) -> int:
    """Get an HTTP timeout in seconds for a service.

    Resolution order:
    1. If `service` provided, try <SERVICE>_HTTP_TIMEOUT_SECONDS
    2. Try global HTTP_TIMEOUT_SECONDS
    3. Return `default`.
    """
    if service:
        env = f"{service.upper()}_HTTP_TIMEOUT_SECONDS"
        v = get_timeout(env)
        if v is not None:
            return v

    global_v = get_timeout("HTTP_TIMEOUT_SECONDS")
    if global_v is not None:
        return global_v

    return default


def get_ollama_max_timeout() -> int | None:
    """Return the configured maximum Ollama subprocess timeout in seconds, or None."""
    return _env_int("OLLAMA_MAX_TIMEOUT_SECONDS")


def ollama_adaptive_enabled() -> bool:
    v = os.getenv("OLLAMA_ADAPTIVE_TIMEOUT")
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def get_adaptive_timeout(base_timeout: int, service: str = "default") -> int:
    """Get adaptive timeout using breathing integration.

    Args:
        base_timeout: Base timeout value in seconds
        service: Service name for logging

    Returns:
        Adjusted timeout value based on breathing factor
    """
    try:
        from src.integration.breathing_integration import breathing_integration

        if breathing_integration.enable_breathing:
            adjusted = breathing_integration.apply_to_timeout(float(base_timeout))
            return int(adjusted)
    except (ImportError, AttributeError, RuntimeError):
        # Graceful fallback if breathing integration unavailable
        logger.debug("Suppressed AttributeError/ImportError/RuntimeError", exc_info=True)

    return base_timeout

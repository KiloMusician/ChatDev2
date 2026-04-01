"""Dev-Mentor Relay - thin HTTP bridge to Dev-Mentor's agent bus.

Forwards NuSyQ-Hub inter-agent messages to Dev-Mentor's
POST /api/agent/publish endpoint so all ecosystem agents share
the same T2 pub/sub stream.

Configuration:
    DEV_MENTOR_URL  env var (default: http://localhost:7337)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_DEV_MENTOR_BASE = os.getenv("DEV_MENTOR_URL", "http://localhost:7337").rstrip("/")
_PUBLISH_PATH = "/api/agent/publish"
_STATUS_PATH = "/api/agent/bus/status"

# aiohttp is preferred; fall back to httpx, then requests (sync wrapped)
_HTTP_CLIENT: str | None = None


def _detect_http_client() -> str:
    global _HTTP_CLIENT
    if _HTTP_CLIENT:
        return _HTTP_CLIENT
    for lib in ("aiohttp", "httpx", "requests"):
        try:
            __import__(lib)
            _HTTP_CLIENT = lib
            logger.debug("dev_mentor_relay using %s", lib)
            return lib
        except ImportError:
            continue
    _HTTP_CLIENT = "none"
    return "none"


async def relay_to_dev_mentor(
    from_agent: str,
    text: str,
    to_agent: str | None = None,
    channel: str = "hive.broadcast",
) -> bool:
    """POST a message to Dev-Mentor's agent bus.

    Returns True on HTTP 2xx, False otherwise (never raises).
    """
    payload: dict[str, Any] = {
        "from_agent": from_agent,
        "text": text,
        "channel": channel,
    }
    if to_agent:
        payload["to_agent"] = to_agent

    url = _DEV_MENTOR_BASE + _PUBLISH_PATH
    lib = _detect_http_client()

    try:
        if lib == "aiohttp":
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status < 300

        if lib == "httpx":
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, json=payload)
                return resp.status_code < 300

        if lib == "requests":
            import asyncio

            import requests

            loop = asyncio.get_event_loop()

            def _sync() -> bool:
                r = requests.post(url, json=payload, timeout=5)
                return r.status_code < 300

            return await loop.run_in_executor(None, _sync)

        logger.warning("No HTTP client available — relay skipped")
        return False

    except Exception as exc:
        logger.debug("relay_to_dev_mentor failed (non-fatal): %s", exc)
        return False


async def get_dev_mentor_status() -> dict[str, Any]:
    """GET Dev-Mentor bus status. Returns a status dict."""
    url = _DEV_MENTOR_BASE + _STATUS_PATH
    lib = _detect_http_client()

    try:
        if lib == "aiohttp":
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status < 300:
                        return await resp.json()
                    return {"status": "error", "http_status": resp.status}

        if lib == "httpx":
            import httpx

            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(url)
                if resp.status_code < 300:
                    return resp.json()
                return {"status": "error", "http_status": resp.status_code}

        if lib == "requests":
            import asyncio

            import requests

            loop = asyncio.get_event_loop()

            def _sync() -> dict[str, Any]:
                r = requests.get(url, timeout=3)
                return (
                    r.json()
                    if r.status_code < 300
                    else {"status": "error", "http_status": r.status_code}
                )

            return await loop.run_in_executor(None, _sync)

        return {"status": "no_http_client", "dev_mentor_url": _DEV_MENTOR_BASE}

    except Exception as exc:
        return {"status": "unreachable", "error": str(exc), "dev_mentor_url": _DEV_MENTOR_BASE}

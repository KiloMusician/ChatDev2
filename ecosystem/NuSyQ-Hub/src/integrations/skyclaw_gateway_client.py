"""SkyClaw HTTP Gateway Client.

Manages the SkyClaw Rust sidecar gateway process and provides a typed
Python client for its HTTP API surface.

SkyClaw gateway endpoints (axum HTTP server, default :8080):
    GET /health   → {status, version, uptime_seconds}
    GET /status   → {status, version, provider, channels, tools, memory_backend}
    GET /dashboard → HTML monitoring dashboard

The gateway is the long-running daemon mode of SkyClaw.  Starting it
enables:
- Persistent SQLite memory (cross-session context)
- Multi-channel routing (Telegram, Discord, Slack, CLI)
- 200-turn autonomous agent runtime (git/shell/browser/file tools)
- Multi-provider support (Anthropic, OpenAI, OpenRouter, Gemini, …)

Typical usage::

    from src.integrations.skyclaw_gateway_client import SkyclawGatewayClient

    client = SkyclawGatewayClient()
    if not await client.is_running():
        await client.start_gateway()

    status = await client.get_status()
    print(status)   # {provider, channels, tools, memory_backend}

    await client.stop_gateway()
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

_DEFAULT_GATEWAY_HOST = "127.0.0.1"
_DEFAULT_GATEWAY_PORT = 8080
_HEALTH_TIMEOUT = 5.0  # seconds for health probe
_START_WAIT_TIMEOUT = 15.0  # seconds to wait for gateway to become ready
_START_POLL_INTERVAL = 0.5  # seconds between readiness polls


def _get_skyclaw_binary() -> Path | None:
    """Locate the SkyClaw binary. Returns None if not found."""
    runtime_dir = Path(__file__).resolve().parents[2] / "state" / "runtime" / "skyclaw"
    candidates: list[tuple[Path, bool]] = [
        (runtime_dir / "target" / "debug" / "skyclaw.exe", False),
        (runtime_dir / "target" / "debug" / "skyclaw", sys.platform == "win32"),
        (runtime_dir / "target" / "release" / "skyclaw.exe", False),
        (runtime_dir / "target" / "release" / "skyclaw", sys.platform == "win32"),
    ]
    for path, _needs_wsl in candidates:
        if path.exists():
            return path  # caller inspects needs_wsl via _binary_needs_wsl()
    return None


def _binary_needs_wsl(binary: Path) -> bool:
    """Return True if binary must be run via WSL (Linux ELF on Windows)."""
    if sys.platform != "win32":
        return False
    return binary.suffix == "" and binary.exists()


def _build_cmd(binary: Path, *args: str) -> list[str]:
    """Build a command list, wrapping in WSL if required."""
    if _binary_needs_wsl(binary):
        wsl_path = str(binary).replace("\\", "/")
        if len(wsl_path) >= 2 and wsl_path[1] == ":":
            drive = wsl_path[0].lower()
            wsl_path = f"/mnt/{drive}{wsl_path[2:]}"
        return ["wsl", "-e", wsl_path, *args]
    return [str(binary), *args]


def _get_gateway_url() -> str:
    """Return the gateway base URL from env or default."""
    env_url = os.getenv("NUSYQ_SKYCLAW_GATEWAY_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    host = os.getenv("SKYCLAW_GATEWAY_HOST", _DEFAULT_GATEWAY_HOST)
    port = os.getenv("SKYCLAW_GATEWAY_PORT", str(_DEFAULT_GATEWAY_PORT))
    return f"http://{host}:{port}"


# ── Process manager ───────────────────────────────────────────────────────────

_gateway_process: subprocess.Popen | None = None  # type: ignore[type-arg]


class SkyclawGatewayClient:
    """HTTP client + process manager for the SkyClaw gateway daemon.

    Thread-safe for concurrent health probes; process management should
    be called from a single async context.
    """

    def __init__(self, gateway_url: str | None = None) -> None:
        """Initialize SkyClaw gateway client.

        Args:
            gateway_url: Override for gateway base URL (default: from env or :8080).
        """
        self.gateway_url = (gateway_url or _get_gateway_url()).rstrip("/")
        self._binary: Path | None = _get_skyclaw_binary()

    # ── Health & status ───────────────────────────────────────────────────────

    async def is_running(self) -> bool:
        """Return True if the gateway is accepting HTTP connections."""
        try:
            result = (await self.get_health()) is not None
            # Broadcast status to skyclaw terminal (best-effort)
            try:
                from src.system.agent_awareness import emit

                if result:
                    emit.agent_online("skyclaw", f"gateway={self.gateway_url}")
                else:
                    emit(
                        "skyclaw",
                        f"OFFLINE at {self.gateway_url}",
                        level="WARNING",
                        source="skyclaw",
                    )
            except Exception:
                pass
            return result
        except Exception:
            return False

    async def get_health(self) -> dict[str, Any] | None:
        """Probe GET /health. Returns None on connection error or timeout.

        Returns:
            Dict with keys: status, version, uptime_seconds — or None.
        """
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.gateway_url}/health",
                    timeout=aiohttp.ClientTimeout(total=_HEALTH_TIMEOUT),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
        except ImportError:
            # aiohttp not installed — fall back to urllib
            return await self._get_health_urllib()
        except Exception as exc:
            logger.debug("SkyClaw health probe failed: %s", exc)
            return None

    async def _get_health_urllib(self) -> dict[str, Any] | None:
        """Fallback health probe using urllib (no aiohttp dependency)."""
        import json
        import urllib.error
        import urllib.request

        try:
            with urllib.request.urlopen(
                f"{self.gateway_url}/health", timeout=_HEALTH_TIMEOUT
            ) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, OSError, ValueError):
            return None

    async def get_status(self) -> dict[str, Any] | None:
        """Probe GET /status for detailed runtime information.

        Returns:
            Dict with provider, channels, tools, memory_backend — or None.
        """
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.gateway_url}/status",
                    timeout=aiohttp.ClientTimeout(total=_HEALTH_TIMEOUT),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
        except Exception as exc:
            logger.debug("SkyClaw status probe failed: %s", exc)
            return None

    # ── Process lifecycle ─────────────────────────────────────────────────────

    async def start_gateway(self, wait: bool = True) -> bool:
        """Spawn the SkyClaw gateway daemon (``skyclaw start``).

        The gateway starts on the port configured in
        ``state/runtime/skyclaw/config/skyclaw.toml`` (default 8080).

        Args:
            wait: If True, block until the gateway is accepting HTTP
                  connections (up to _START_WAIT_TIMEOUT seconds).

        Returns:
            True if gateway started (or was already running), False on failure.
        """
        global _gateway_process

        if await self.is_running():
            logger.info("SkyClaw gateway already running at %s", self.gateway_url)
            return True

        binary = self._binary
        if binary is None:
            logger.error("SkyClaw binary not found — cannot start gateway")
            return False

        config_dir = binary.resolve().parents[3] / "config"
        config_file = config_dir / "skyclaw.toml"

        cmd = _build_cmd(binary, "start")
        if config_file.exists():
            cmd += ["--config", str(config_file)]

        try:
            logger.info("Starting SkyClaw gateway: %s", " ".join(cmd))
            _gateway_process = subprocess.Popen(
                cmd,
                cwd=str(binary.resolve().parents[3]),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError as exc:
            logger.error("Failed to spawn SkyClaw gateway: %s", exc)
            return False

        if not wait:
            return True

        # Poll until healthy or timeout
        elapsed = 0.0
        while elapsed < _START_WAIT_TIMEOUT:
            await asyncio.sleep(_START_POLL_INTERVAL)
            elapsed += _START_POLL_INTERVAL
            if await self.is_running():
                health = await self.get_health()
                logger.info(
                    "SkyClaw gateway ready (v%s) at %s",
                    health.get("version", "?") if health else "?",
                    self.gateway_url,
                )
                return True

        logger.warning("SkyClaw gateway did not become ready within %.0fs", _START_WAIT_TIMEOUT)
        return False

    async def stop_gateway(self) -> None:
        """Terminate the managed gateway process if started by this client."""
        global _gateway_process
        if _gateway_process is not None and _gateway_process.poll() is None:
            logger.info("Stopping SkyClaw gateway (PID %d)", _gateway_process.pid)
            _gateway_process.terminate()
            try:
                _gateway_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _gateway_process.kill()
            _gateway_process = None
            logger.info("SkyClaw gateway stopped")

    def binary_path(self) -> Path | None:
        """Return the resolved binary path, or None if not found."""
        return self._binary

    def binary_info(self) -> dict[str, Any]:
        """Return a dict with binary path, platform, and WSL-mode flag."""
        if self._binary is None:
            return {"found": False}
        return {
            "found": True,
            "path": str(self._binary),
            "needs_wsl": _binary_needs_wsl(self._binary),
            "platform": sys.platform,
        }

    async def summary(self) -> dict[str, Any]:
        """Return a combined summary suitable for CLI display.

        Returns:
            Dict with keys: binary, gateway_url, running, health, status.
        """
        running = await self.is_running()
        health = await self.get_health() if running else None
        status = await self.get_status() if running else None
        return {
            "binary": self.binary_info(),
            "gateway_url": self.gateway_url,
            "running": running,
            "health": health,
            "status": status,
        }


# ── Module-level singleton ────────────────────────────────────────────────────

_client: SkyclawGatewayClient | None = None


def get_skyclaw_gateway_client(gateway_url: str | None = None) -> SkyclawGatewayClient:
    """Return or create the module-level SkyclawGatewayClient singleton.

    Args:
        gateway_url: Optional URL override (only applied on first call).

    Returns:
        The singleton SkyclawGatewayClient instance.
    """
    global _client
    if _client is None:
        _client = SkyclawGatewayClient(gateway_url=gateway_url)
    return _client

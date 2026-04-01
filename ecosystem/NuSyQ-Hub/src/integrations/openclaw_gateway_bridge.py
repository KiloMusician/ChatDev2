#!/usr/bin/env python3
"""OpenClaw Gateway Bridge - Multi-Channel Messaging Integration.

Bridges OpenClaw Gateway (WebSocket control plane) to NuSyQ orchestration system.
Enables agents to receive commands from 12+ messaging platforms (Slack, Discord,
Telegram, WhatsApp, Signal, Teams, Google Chat, Matrix, iMessage, Zalo, WebChat, etc.)
and route them through the unified orchestrator.

FILE-ID: nusyq.integrations.openclaw_gateway_bridge
TYPE: Integration Module
STATUS: Production (Phase 1)
VERSION: 1.0.0
CONTEXT: OpenClaw↔NuSyQ-Hub Message Flow
TAGS: [openclaw, messaging, gateway, integration, multi-channel]
CREATED: 2025-12-26
AUTHOR: GitHub Copilot + NuSyQ Team
STABILITY: High (Production Ready)

Architecture:
    OpenClaw Gateway (ws://127.0.0.1:18789)
           ↓ (WebSocket Messages)
    OpenClawGatewayBridge (this module)
           ↓ (route_task with channel context)
    UnifiedAIOrchestrator (src/orchestration/)
           ↓ (execution)
    OpenClawGatewayBridge.send_result()
           ↓ (channel.send for Slack, Discord, etc.)
    Original Channel (user receives response)

OmniTag: [openclaw, integration, messaging, gateway, bidirectional]
MegaTag: [OPENCLAW⨳GATEWAY⦾ORCHESTRATION→∞]
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    UTC = timezone.utc  # noqa: UP017

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

logger = logging.getLogger(__name__)

# Prefer environment variable override (set via .env.workspace or shell)
OPENCLAW_DEFAULT_GATEWAY_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "ws://127.0.0.1:18789")
OPENCLAW_DEFAULT_TIMEOUT_SECONDS = 30
OPENCLAW_CONFIG_PATH = REPO_ROOT / "config" / "secrets.json"
OPENCLAW_INTERNAL_CHANNELS = {"internal", "loopback", "local", "nusyq", "terminal"}
OPENCLAW_TARGET_SYSTEMS = {
    "auto",
    "ollama",
    "lmstudio",
    "chatdev",
    "copilot",
    "codex",
    "claude_cli",
    "claude",
    "vscode_copilot",
    "vscode_claude",
    "vscode_codex",
    "consciousness",
    "quantum_resolver",
}

# Optional WebSocket dependency
try:
    import aiohttp
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning(
        "aiohttp/websockets not available; OpenClaw Gateway Bridge requires: pip install aiohttp websockets"
    )


class OpenClawGatewayBridge:
    """Bridges OpenClaw Gateway to NuSyQ orchestration system.

    Establishes persistent WebSocket connection to OpenClaw Gateway
    (ws://127.0.0.1:18789), listens for inbound messages from 12+
    messaging platforms, routes them to UnifiedAIOrchestrator via
    agent_task_router, and sends results back through original channel.

    Attributes:
        gateway_url (str): WebSocket URL to OpenClaw Gateway (default: ws://127.0.0.1:18789)
        orchestrator: UnifiedAIOrchestrator instance for task routing
        quest_manager: QuestManager for persistent task logging
        session: aiohttp ClientSession for HTTP requests
        websocket: Active WebSocket connection to gateway
        running (bool): Flag indicating whether bridge is actively listening
        timeout_seconds (int): Timeout for gateway operations
    """

    def __init__(
        self,
        gateway_url: str = OPENCLAW_DEFAULT_GATEWAY_URL,
        orchestrator: Any | None = None,
        quest_manager: Any | None = None,
        timeout_seconds: int = OPENCLAW_DEFAULT_TIMEOUT_SECONDS,
    ):
        """Initialize OpenClaw Gateway Bridge.

        Args:
            gateway_url: WebSocket URL to OpenClaw Gateway (default: ws://127.0.0.1:18789)
            orchestrator: UnifiedAIOrchestrator instance (lazy-loaded if not provided)
            quest_manager: QuestManager instance (lazy-loaded if not provided)
            timeout_seconds: Timeout for gateway operations (default: 30)

        Raises:
            ImportError: If aiohttp/websockets not installed
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "OpenClaw Gateway Bridge requires aiohttp and websockets. Install with: pip install aiohttp websockets"
            )

        self.gateway_url = gateway_url
        self.orchestrator = orchestrator
        self.quest_manager = quest_manager
        self.timeout_seconds = timeout_seconds
        self.session: aiohttp.ClientSession | None = None
        self.websocket: Any | None = None
        self.running = False

        logger.info(
            f"🔌 OpenClaw Gateway Bridge initialized | gateway={gateway_url} | timeout={timeout_seconds}s"
        )

    def _lazy_load_dependencies(self) -> None:
        """Lazy-load orchestrator and quest_manager if not provided."""
        if self.orchestrator is None:
            try:
                from src.orchestration.unified_ai_orchestrator import \
                    UnifiedAIOrchestrator

                self.orchestrator = UnifiedAIOrchestrator()
                logger.info("✅ UnifiedAIOrchestrator loaded")
            except ImportError as e:
                logger.error(f"Failed to load UnifiedAIOrchestrator: {e}")
                raise

        if self.quest_manager is None:
            try:
                from src.Rosetta_Quest_System.quest_manager import QuestManager

                self.quest_manager = QuestManager()
                logger.info("✅ QuestManager loaded")
            except ImportError as e:
                logger.error(f"Failed to load QuestManager: {e}")
                raise

    async def connect(self) -> bool:
        """Establish WebSocket connection to OpenClaw Gateway.

        Returns:
            bool: True if connection successful, False otherwise

        Example:
            >>> bridge = OpenClawGatewayBridge()
            >>> success = await bridge.connect()
            >>> if success:
            ...     await bridge.run()
        """
        try:
            logger.info(f"🔗 Connecting to OpenClaw Gateway: {self.gateway_url}")

            # Create session if not exists
            if self.session is None:
                self.session = aiohttp.ClientSession()

            # Establish WebSocket connection
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.gateway_url),  # type: ignore[attr-defined]
                timeout=self.timeout_seconds,
            )

            logger.info("✅ Successfully connected to OpenClaw Gateway")
            return True

        except TimeoutError:
            logger.error(f"⏱️ Connection timeout to OpenClaw Gateway (>{self.timeout_seconds}s)")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to OpenClaw Gateway: {e}")
            return False

    def _infer_task_type(self, text: str) -> str:
        """Infer task type from message text.

        Defaults to "analyze" when no explicit intent is detected.
        """
        lowered = text.strip().lower()
        if lowered.startswith(("generate", "create", "build", "scaffold")):
            return "generate"
        if lowered.startswith(("review", "audit", "critique")):
            return "review"
        if lowered.startswith(("debug", "fix", "repair")):
            return "debug"
        if lowered.startswith(("plan", "design", "outline")):
            return "plan"
        if lowered.startswith(("test", "tests", "qa")):
            return "test"
        if lowered.startswith(("document", "docs", "doc")):
            return "document"
        return "analyze"

    def _extract_target_system(self, text: str) -> tuple[str, str]:
        """Extract optional target system prefix from message text.

        Supports prefixes like:
          - "copilot: ..."
          - "ollama: ..."
          - "chatdev: ..."
          - "quantum: ..."
        Returns (target_system, cleaned_text).
        """
        raw = text.strip()
        lowered = raw.lower()
        prefix_map = {
            "copilot": "copilot",
            "vscode_copilot": "copilot",
            "ollama": "ollama",
            "lmstudio": "lmstudio",
            "chatdev": "chatdev",
            "codex": "codex",
            "vscode_codex": "codex",
            "claude": "claude_cli",
            "claude_cli": "claude_cli",
            "vscode_claude": "claude_cli",
            "consciousness": "consciousness",
            "consciousness_bridge": "consciousness",
            "quantum": "quantum_resolver",
            "quantum_resolver": "quantum_resolver",
        }

        for prefix, target in prefix_map.items():
            for token in (f"{prefix}:", f"/{prefix}", f"@{prefix}"):
                if lowered.startswith(token):
                    cleaned = raw[len(token) :].strip()
                    return target, cleaned

        return "auto", raw

    def _emit_internal_receipt(
        self,
        channel: str,
        target_user_id: str,
        result_text: str,
        task_id: str | None,
    ) -> None:
        """Persist loopback delivery receipts for local-only orchestration."""
        try:
            receipt_dir = REPO_ROOT / "state" / "reports"
            receipt_dir.mkdir(parents=True, exist_ok=True)
            receipt_path = receipt_dir / "openclaw_internal_receipts.jsonl"
            payload = {
                "timestamp": datetime.now(UTC).isoformat(),
                "channel": channel,
                "target_user_id": target_user_id,
                "task_id": task_id,
                "message": result_text,
                "delivery": "local_receipt",
            }
            with receipt_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning("Failed to persist local OpenClaw receipt: %s", exc)

    def _log_openclaw_message(
        self,
        channel: str,
        username: str,
        text: str,
        task_id: str | None,
        result_status: str,
        target_system: str,
    ) -> None:
        """Best-effort quest logging that tolerates quest manager API variants."""
        if not self.quest_manager:
            return

        try:
            if hasattr(self.quest_manager, "log_quest"):
                self.quest_manager.log_quest(
                    quest_type="openclaw_message",
                    data={
                        "channel": channel,
                        "user": username,
                        "message": text,
                        "task_id": task_id,
                        "status": result_status,
                        "target_system": target_system,
                    },
                )
                return

            if hasattr(self.quest_manager, "add_quest"):
                self.quest_manager.add_quest(
                    title=f"OpenClaw {channel} message from {username}",
                    description=(
                        f"Message: {text}\nTask ID: {task_id}\nStatus: {result_status}\nTarget: {target_system}"
                    ),
                    questline="OpenClaw",
                    tags=["openclaw", "messaging", channel],
                    priority="low",
                )
                return

            logger.debug("Quest manager has no compatible logging API; skipping OpenClaw quest log")
        except Exception as exc:
            logger.warning("Quest logging skipped: %s", exc)

    def _build_channels_api_url(self) -> str:
        """Derive channels API URL from gateway URL safely.

        Respects OPENCLAW_API_URL env var override when set (e.g. in .env.workspace).
        """
        env_override = os.environ.get("OPENCLAW_API_URL")
        if env_override:
            base = env_override.rstrip("/")
            return f"{base}/api/channels/send"
        parsed = urlparse(self.gateway_url)
        host = parsed.hostname or "127.0.0.1"
        scheme = "https" if parsed.scheme == "wss" else "http"
        return f"{scheme}://{host}:18790/api/channels/send"

    async def handle_inbound_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Route inbound message from OpenClaw channel to orchestrator.

        Message format expected from OpenClaw Gateway:
            {
                "timestamp": "2025-12-26T10:30:00Z",
                "channel": "slack",           # slack, discord, telegram, whatsapp, etc.
                "user_id": "U12345",          # Platform-specific user ID
                "username": "alice",           # Display name
                "text": "analyze my file.py",  # Message text
                "context": {...}              # Optional channel/thread context
            }

        Returns:
            dict: Result from orchestrator with structure:
                {
                    "status": "success|error",
                    "result_text": "...",
                    "task_id": "...",
                    "channel": "slack"
                }

        Args:
            message: Inbound message dict from OpenClaw Gateway
        """
        try:
            # Extract message fields
            timestamp = message.get("timestamp", datetime.now(UTC).isoformat())
            channel = message.get("channel", "unknown")
            user_id = message.get("user_id", "anonymous")
            username = message.get("username", "user")
            text = message.get("text", "")
            context = message.get("context", {})
            if not isinstance(context, dict):
                context = {}
            explicit_target = str(
                message.get("target_system") or context.get("target_system") or ""
            )
            explicit_target = explicit_target.strip().lower()

            logger.info(f"📨 Inbound: channel={channel} | user={username} | text={text[:50]}...")

            # Lazy load dependencies
            self._lazy_load_dependencies()

            # Route to orchestrator via agent_task_router
            try:
                from src.tools.agent_task_router import AgentTaskRouter

                router = AgentTaskRouter()

                target_system, cleaned_text = self._extract_target_system(text)
                if explicit_target:
                    if explicit_target in OPENCLAW_TARGET_SYSTEMS:
                        target_system = explicit_target
                    else:
                        logger.warning(
                            "Ignoring unsupported explicit target_system '%s'; using extracted target '%s'",
                            explicit_target,
                            target_system,
                        )
                task_type = context.get("task_type") or self._infer_task_type(cleaned_text)
                if target_system == "chatdev" and task_type != "generate":
                    task_type = "generate"

                # Route task with channel context
                result = await router.route_task(
                    task_type=task_type,
                    description=cleaned_text or text,
                    context={
                        "channel": channel,
                        "user_id": user_id,
                        "username": username,
                        "timestamp": timestamp,
                        "openclaw": True,
                        "task_type": task_type,
                        "explicit_target_system": explicit_target or None,
                        "target_system": target_system,
                        **context,
                    },
                    target_system=target_system,
                )

                task_id = result.get("task_id")
                result_status = result.get("status", "submitted")
                result_system = result.get("system", target_system)
                result_text = (
                    result.get("output") if isinstance(result.get("output"), str) else None
                )
                output_status = ""
                nested_error: str | None = None
                if isinstance(result.get("output"), dict):
                    output_status = str(result["output"].get("status", "")).strip().lower()
                    nested_error = (
                        result["output"].get("error_message")
                        or result["output"].get("error")
                        or result["output"].get("message")
                    )
                status_norm = str(result_status).strip().lower()
                hard_failure = status_norm in {"error", "failed", "failure"} or output_status in {
                    "error",
                    "failed",
                    "failure",
                }

                if hard_failure:
                    summary = (
                        result_text
                        or result.get("error")
                        or nested_error
                        or result.get("note")
                        or f"❌ Routed to {result_system} ({result_status})"
                    )
                else:
                    summary = (
                        result_text
                        or result.get("note")
                        or f"✅ Routed to {result_system} ({result_status})"
                    )

                # Log to quest system (best effort)
                self._log_openclaw_message(
                    channel=channel,
                    username=username,
                    text=text,
                    task_id=task_id,
                    result_status=result_status,
                    target_system=target_system,
                )

                logger.info(
                    "✅ Message routed | task_id=%s | target=%s | task_type=%s",
                    task_id,
                    target_system,
                    task_type,
                )

                return {
                    "status": "error" if hard_failure else "success",
                    "channel": channel,
                    "user_id": user_id,
                    "task_id": task_id,
                    "system": result_system,
                    "result_status": result_status,
                    "result_text": summary,
                    "error": (result.get("error") or nested_error) if hard_failure else None,
                }

            except Exception as e:
                logger.error(f"❌ Failed to route message: {e}")
                return {
                    "status": "error",
                    "channel": channel,
                    "user_id": user_id,
                    "error": str(e),
                    "result_text": f"❌ Failed to route task: {e}",
                }

        except Exception as e:
            logger.error(f"❌ Error handling inbound message: {e}")
            return {
                "status": "error",
                "error": str(e),
                "result_text": f"❌ Message handling error: {e}",
            }

    async def send_result(
        self,
        channel: str,
        target_user_id: str,
        result_text: str,
        task_id: str | None = None,
    ) -> bool:
        """Send result back through original channel.

        Sends execution result through OpenClaw channels API (Slack, Discord, etc.)
        to the user who initiated the request.

        Args:
            channel: Channel platform (slack, discord, telegram, etc.)
            target_user_id: User ID in that platform
            result_text: Result message to send
            task_id: Optional task ID for reference

        Returns:
            bool: True if send successful, False otherwise

        Example:
            >>> await bridge.send_result(
            ...     channel="slack",
            ...     target_user_id="U12345",
            ...     result_text="✅ Analysis complete...",
            ...     task_id="task-123"
            ... )
        """
        try:
            if channel.strip().lower() in OPENCLAW_INTERNAL_CHANNELS:
                self._emit_internal_receipt(channel, target_user_id, result_text, task_id)
                logger.info("✅ Result routed to internal receipt sink | channel=%s", channel)
                return True

            if not self.session:
                self.session = aiohttp.ClientSession()

            channels_api = self._build_channels_api_url()

            payload = {
                "channel": channel,
                "target_user_id": target_user_id,
                "message": result_text,
                "timestamp": datetime.now(UTC).isoformat(),
                "task_id": task_id,
            }

            async with self.session.post(
                channels_api, json=payload, timeout=self.timeout_seconds
            ) as resp:
                if resp.status == 200:
                    logger.info(f"✅ Result sent | channel={channel} | user={target_user_id}")
                    return True
                else:
                    logger.error(f"❌ Failed to send result | status={resp.status}")
                    return False

        except TimeoutError:
            logger.error(f"⏱️ Timeout sending result to {channel}/{target_user_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending result: {e}")
            return False

    async def listen_for_messages(self) -> None:
        """Listen for inbound messages from OpenClaw Gateway.

        Main loop that:
        1. Listens on WebSocket for incoming messages from any channel
        2. Routes each message to orchestrator
        3. Sends result back through original channel
        4. Logs all operations to quest system

        Blocking operation; runs until websocket closes or error occurs.
        """
        if not self.websocket:
            logger.error("❌ WebSocket not connected; call connect() first")
            return

        logger.info("👂 Listening for messages from OpenClaw Gateway...")
        self.running = True

        try:
            while self.running:
                try:
                    # Receive message from gateway
                    message_json = await asyncio.wait_for(
                        self.websocket.recv(),  # type: ignore[attr-defined]
                        timeout=self.timeout_seconds,
                    )

                    message = json.loads(message_json)
                    logger.debug(f"📨 Raw message: {message}")

                    # Handle inbound message
                    result = await self.handle_inbound_message(message)

                    # Send result back through channel
                    if result.get("status") == "success":
                        await self.send_result(
                            channel=result.get("channel", "unknown"),
                            target_user_id=result.get("user_id", ""),
                            result_text=result.get("result_text", ""),
                            task_id=result.get("task_id"),
                        )

                except TimeoutError:
                    # Timeout waiting for message; continue loop
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON from gateway: {e}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error in listen loop: {e}")
                    continue

        except asyncio.CancelledError:
            logger.info("🛑 Listener cancelled")
            self.running = False
            raise
        except Exception as e:
            logger.error(f"❌ Listen loop error: {e}")
            self.running = False

    async def disconnect(self) -> None:
        """Gracefully disconnect from OpenClaw Gateway."""
        logger.info("🔌 Disconnecting from OpenClaw Gateway...")
        self.running = False

        if self.websocket:
            await self.websocket.close()  # type: ignore[attr-defined]
            self.websocket = None

        if self.session:
            await self.session.close()
            self.session = None

        logger.info("✅ Disconnected from OpenClaw Gateway")

    async def run(self) -> None:
        """Main entry point for gateway bridge.

        Establishes connection, listens for messages, and handles graceful shutdown.
        Blocking operation; recommended to run in dedicated asyncio task or process.

        Example:
            >>> bridge = OpenClawGatewayBridge()
            >>> await bridge.run()

        Or in background:
            >>> asyncio.create_task(bridge.run())
        """
        try:
            # Connect to gateway
            connected = await self.connect()
            if not connected:
                logger.error("❌ Failed to connect to OpenClaw Gateway; exiting")
                return

            # Listen for messages (blocking)
            await self.listen_for_messages()

        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        except Exception as e:
            logger.error(f"❌ Gateway bridge error: {e}")
        finally:
            await self.disconnect()


# Singleton instance
_bridge_instance: OpenClawGatewayBridge | None = None


def _load_openclaw_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load OpenClaw config from secrets file (best effort)."""
    path = config_path or OPENCLAW_CONFIG_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            openclaw = payload.get("openclaw", {})
            if isinstance(openclaw, dict):
                return openclaw
    except Exception:
        logger.debug("Suppressed Exception", exc_info=True)
    return {}


def get_openclaw_gateway_bridge(
    gateway_url: str | None = None,
    orchestrator: Any | None = None,
    quest_manager: Any | None = None,
    timeout_seconds: int | None = None,
    force_reload: bool = False,
    config_path: Path | None = None,
) -> OpenClawGatewayBridge:
    """Get or create singleton OpenClaw Gateway Bridge instance.

    Args:
        gateway_url: WebSocket URL to OpenClaw Gateway (defaults to config/secrets.json openclaw.gateway_url)
        orchestrator: Optional UnifiedAIOrchestrator instance
        quest_manager: Optional QuestManager instance
        timeout_seconds: Timeout for gateway operations (defaults to config/secrets.json openclaw.timeout_seconds)
        force_reload: Recreate singleton instance with resolved settings even if one already exists
        config_path: Optional path to secrets-style config file for OpenClaw settings

    Returns:
        OpenClawGatewayBridge: Singleton bridge instance

    Example:
        >>> bridge = get_openclaw_gateway_bridge()
        >>> await bridge.run()
    """
    global _bridge_instance

    config = _load_openclaw_config(config_path)
    resolved_gateway = str(gateway_url or config.get("gateway_url") or OPENCLAW_DEFAULT_GATEWAY_URL)
    resolved_timeout = int(
        timeout_seconds
        if timeout_seconds is not None
        else config.get("timeout_seconds", OPENCLAW_DEFAULT_TIMEOUT_SECONDS)
    )

    should_reload = force_reload
    if _bridge_instance is not None:
        should_reload = should_reload or (
            _bridge_instance.gateway_url != resolved_gateway
            or _bridge_instance.timeout_seconds != resolved_timeout
        )

    if _bridge_instance is None or should_reload:
        if _bridge_instance is not None and getattr(_bridge_instance, "running", False):
            logger.warning(
                "OpenClaw bridge is currently running; keeping existing instance "
                "until next restart to avoid disrupting active WebSocket sessions."
            )
            return _bridge_instance
        _bridge_instance = OpenClawGatewayBridge(
            gateway_url=resolved_gateway,
            orchestrator=orchestrator,
            quest_manager=quest_manager,
            timeout_seconds=resolved_timeout,
        )

    return _bridge_instance


if __name__ == "__main__":
    # Enable debug logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run bridge
    async def main():
        bridge = get_openclaw_gateway_bridge()
        await bridge.run()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bridge shutdown")

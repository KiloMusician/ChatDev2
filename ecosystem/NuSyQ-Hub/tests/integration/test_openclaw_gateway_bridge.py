#!/usr/bin/env python3
"""Unit and Integration Tests for OpenClaw Gateway Bridge.

Tests cover:
- Gateway bridge initialization and configuration
- Inbound message handling and routing
- Result sending to channels
- WebSocket connection lifecycle
- Error handling and recovery
- Quest logging integration

FILE-ID: tests.integration.test_openclaw_gateway_bridge
TYPE: Test Module
STATUS: Production (Phase 1)
VERSION: 1.0.0
CREATED: 2025-12-26
AUTHOR: GitHub Copilot + NuSyQ Team

Run with: pytest tests/integration/test_openclaw_gateway_bridge.py -v

OmniTag: [openclaw, tests, integration, gateway]
MegaTag: [TESTS⨳OPENCLAW⦾INTEGRATION→∞]
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


class TestOpenClawGatewayBridgeInitialization:
    """Test OpenClaw Gateway Bridge initialization."""

    def test_initialization_default_config(self):
        """Test bridge initialization with default configuration."""
        # Import at test time to avoid import errors if aiohttp not installed
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        assert bridge.gateway_url == "ws://127.0.0.1:18789"
        assert bridge.timeout_seconds == 30
        assert bridge.orchestrator is None
        assert bridge.quest_manager is None
        assert bridge.running is False

    def test_initialization_custom_config(self):
        """Test bridge initialization with custom configuration."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        gateway_url = "ws://custom.example.com:9999"
        timeout = 60

        bridge = OpenClawGatewayBridge(
            gateway_url=gateway_url,
            timeout_seconds=timeout,
        )

        assert bridge.gateway_url == gateway_url
        assert bridge.timeout_seconds == timeout

    def test_initialization_missing_websockets_raises_error(self):
        """Test initialization raises ImportError if websockets not installed."""
        try:
            from src.integrations.openclaw_gateway_bridge import (
                WEBSOCKETS_AVAILABLE,
                OpenClawGatewayBridge,
            )
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        # If websockets not available, should raise on __init__
        if not WEBSOCKETS_AVAILABLE:
            with pytest.raises(ImportError, match="OpenClaw Gateway Bridge requires"):
                OpenClawGatewayBridge()

    def test_build_channels_api_url_uses_gateway_host(self):
        """Ensure channels API URL derivation preserves host and scheme."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge(gateway_url="ws://172.24.224.1:18789")
        assert bridge._build_channels_api_url() == "http://172.24.224.1:18790/api/channels/send"

    def test_extract_target_system_supports_codex_and_claude_prefixes(self):
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()
        target, cleaned = bridge._extract_target_system("codex: implement a parser")
        assert target == "codex"
        assert cleaned == "implement a parser"

        target, cleaned = bridge._extract_target_system("claude: review src/app.py")
        assert target == "claude_cli"
        assert cleaned == "review src/app.py"


class TestOpenClawGatewayBridgeHandleInboundMessage:
    """Test inbound message handling."""

    @pytest.mark.asyncio
    async def test_handle_inbound_message_success(self):
        """Test successful routing of inbound message."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        # Create bridge with mocked dependencies
        mock_orchestrator = MagicMock()
        mock_quest_manager = MagicMock()

        bridge = OpenClawGatewayBridge(
            orchestrator=mock_orchestrator,
            quest_manager=mock_quest_manager,
        )

        # Mock the router
        with patch("src.tools.agent_task_router.AgentTaskRouter") as mock_router_class:
            mock_router = MagicMock()
            mock_router.route_task = AsyncMock(
                return_value={
                    "status": "success",
                    "system": "ollama",
                    "task_id": "task-123",
                    "output": "✅ done",
                }
            )
            mock_router_class.return_value = mock_router

            # Test message
            message = {
                "timestamp": "2025-12-26T10:30:00Z",
                "channel": "slack",
                "user_id": "U12345",
                "username": "alice",
                "text": "analyze my code",
                "context": {"thread_ts": "1234567890.000001"},
            }

            # Handle message
            result = await bridge.handle_inbound_message(message)

            # Verify result
            assert result["status"] == "success"
            assert result["channel"] == "slack"
            assert result["user_id"] == "U12345"
            assert result["task_id"] == "task-123"
            assert "✅" in result["result_text"]

            # Verify router was called
            mock_router.route_task.assert_called_once()

            # Verify quest was logged
            mock_quest_manager.log_quest.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_inbound_message_missing_fields(self):
        """Test handling of message with missing fields."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        # Minimal message (missing most fields)
        message = {"text": "help"}

        result = await bridge.handle_inbound_message(message)

        # Should have defaults
        assert "channel" in result
        assert "user_id" in result
        assert "result_text" in result

    @pytest.mark.asyncio
    async def test_handle_inbound_message_routing_error(self):
        """Test error handling when routing fails."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        mock_orchestrator = MagicMock()
        bridge = OpenClawGatewayBridge(orchestrator=mock_orchestrator)

        # Mock router that raises error
        with patch("src.tools.agent_task_router.AgentTaskRouter") as mock_router_class:
            mock_router = MagicMock()
            mock_router.route_task = AsyncMock(side_effect=ValueError("Routing failed"))
            mock_router_class.return_value = mock_router

            message = {
                "channel": "discord",
                "user_id": "user123",
                "text": "broken command",
            }

            result = await bridge.handle_inbound_message(message)

            # Should return error status
            assert result["status"] == "error"
            assert "error" in result
            assert "❌" in result["result_text"]

    @pytest.mark.asyncio
    async def test_handle_inbound_message_allows_quest_manager_without_log_quest(self):
        """Successful routes should not fail when quest manager lacks log_quest API."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        class QuestManagerWithoutLogQuest:
            pass

        bridge = OpenClawGatewayBridge(quest_manager=QuestManagerWithoutLogQuest())

        with patch("src.tools.agent_task_router.AgentTaskRouter") as mock_router_class:
            mock_router = AsyncMock()
            mock_router.route_task = AsyncMock(
                return_value={
                    "status": "success",
                    "system": "ollama",
                    "task_id": "task-quest-fallback",
                    "output": "ok",
                }
            )
            mock_router_class.return_value = mock_router

            message = {
                "timestamp": "2025-12-26T10:30:00Z",
                "channel": "slack",
                "user_id": "U12345",
                "username": "alice",
                "text": "ollama: test",
                "context": {},
            }

            result = await bridge.handle_inbound_message(message)
            assert result["status"] == "success"
            assert result["task_id"] == "task-quest-fallback"

    @pytest.mark.asyncio
    async def test_handle_inbound_message_respects_explicit_target_system(self):
        """Explicit target_system should override text-prefix extraction when valid."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        with patch("src.tools.agent_task_router.AgentTaskRouter") as mock_router_class:
            mock_router = MagicMock()
            mock_router.route_task = AsyncMock(
                return_value={
                    "status": "success",
                    "system": "lmstudio",
                    "task_id": "task-override",
                    "output": "ok",
                }
            )
            mock_router_class.return_value = mock_router

            message = {
                "timestamp": "2025-12-26T10:30:00Z",
                "channel": "internal",
                "user_id": "U12345",
                "username": "alice",
                "text": "ollama: this should be overridden",
                "target_system": "lmstudio",
                "context": {"task_type": "analyze"},
            }

            result = await bridge.handle_inbound_message(message)
            assert result["status"] == "success"
            _, kwargs = mock_router.route_task.call_args
            assert kwargs["target_system"] == "lmstudio"

    @pytest.mark.asyncio
    async def test_handle_inbound_message_supports_explicit_alias_targets(self):
        """Alias target systems should flow through to the router."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        with patch("src.tools.agent_task_router.AgentTaskRouter") as mock_router_class:
            mock_router = MagicMock()
            mock_router.route_task = AsyncMock(
                return_value={
                    "status": "success",
                    "system": "claude_cli",
                    "task_id": "task-claude-alias",
                    "output": "ok",
                }
            )
            mock_router_class.return_value = mock_router

            message = {
                "timestamp": "2025-12-26T10:30:00Z",
                "channel": "internal",
                "user_id": "U12345",
                "username": "alice",
                "text": "ollama: this should be overridden",
                "target_system": "vscode_claude",
                "context": {"task_type": "analyze"},
            }

            result = await bridge.handle_inbound_message(message)
            assert result["status"] == "success"
            _, kwargs = mock_router.route_task.call_args
            assert kwargs["target_system"] == "vscode_claude"

    @pytest.mark.asyncio
    async def test_handle_inbound_message_propagates_failed_route_as_error(self):
        """Bridge status should be error when backend routing returns failed/error."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        with patch("src.tools.agent_task_router.AgentTaskRouter") as mock_router_class:
            mock_router = MagicMock()
            mock_router.route_task = AsyncMock(
                return_value={
                    "status": "failed",
                    "system": "lmstudio",
                    "error": "bridge unavailable",
                    "task_id": "task-failed",
                }
            )
            mock_router_class.return_value = mock_router

            message = {
                "channel": "internal",
                "user_id": "U12345",
                "username": "alice",
                "text": "test failure path",
            }
            result = await bridge.handle_inbound_message(message)
            assert result["status"] == "error"
            assert result["task_id"] == "task-failed"


class TestOpenClawGatewayBridgeSendResult:
    """Test result sending to channels."""

    @pytest.mark.asyncio
    async def test_send_result_success(self):
        """Test successful result sending."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response

            success = await bridge.send_result(
                channel="slack",
                target_user_id="U12345",
                result_text="✅ Done!",
                task_id="task-123",
            )

            assert success is True
        await bridge.disconnect()

    @pytest.mark.asyncio
    async def test_send_result_internal_channel_writes_local_receipt(self):
        """Internal channels should bypass OpenClaw API and use local receipts."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        with patch.object(bridge, "_emit_internal_receipt") as mock_emit:
            with patch("aiohttp.ClientSession.post") as mock_post:
                success = await bridge.send_result(
                    channel="internal",
                    target_user_id="local-user",
                    result_text="ok",
                    task_id="task-123",
                )

        assert success is True
        mock_emit.assert_called_once()
        mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_result_failed_request(self):
        """Test handling of failed result send."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status = 500

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response

            success = await bridge.send_result(
                channel="telegram",
                target_user_id="user456",
                result_text="Error occurred",
            )

            assert success is False
        await bridge.disconnect()

    @pytest.mark.asyncio
    async def test_send_result_timeout(self):
        """Test handling of timeout when sending result."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge(timeout_seconds=1)

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.side_effect = TimeoutError()

            success = await bridge.send_result(
                channel="whatsapp",
                target_user_id="number123",
                result_text="Message",
            )

            assert success is False
        await bridge.disconnect()


class TestOpenClawGatewayBridgeConnection:
    """Test WebSocket connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection to gateway."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        # Mock websockets.connect
        with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value = mock_ws

            success = await bridge.connect()

            assert success is True
            assert bridge.websocket is not None
        await bridge.disconnect()

    @pytest.mark.asyncio
    async def test_connect_timeout(self):
        """Test connection timeout."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge(timeout_seconds=1)

        # Mock connection that times out
        with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = TimeoutError()

            success = await bridge.connect()

            assert success is False
        await bridge.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test graceful disconnect."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        bridge = OpenClawGatewayBridge()

        # Setup mock websocket and session
        bridge.websocket = AsyncMock()
        bridge.session = AsyncMock()
        bridge.running = True

        await bridge.disconnect()

        # Verify cleanup
        assert bridge.running is False
        assert bridge.websocket is None
        assert bridge.session is None


class TestOpenClawGatewayBridgeSingleton:
    """Test singleton pattern."""

    def test_get_openclaw_gateway_bridge_singleton(self):
        """Test get_openclaw_gateway_bridge returns same instance."""
        try:
            from src.integrations.openclaw_gateway_bridge import (
                get_openclaw_gateway_bridge,
            )
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        # Reset singleton
        from src.integrations import openclaw_gateway_bridge

        openclaw_gateway_bridge._bridge_instance = None

        # Get bridge twice
        bridge1 = get_openclaw_gateway_bridge()
        bridge2 = get_openclaw_gateway_bridge()

        # Should be same instance
        assert bridge1 is bridge2

    def test_get_openclaw_gateway_bridge_custom_args(self):
        """Test get_openclaw_gateway_bridge with custom arguments."""
        try:
            from src.integrations.openclaw_gateway_bridge import (
                get_openclaw_gateway_bridge,
            )
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        # Reset singleton
        from src.integrations import openclaw_gateway_bridge

        openclaw_gateway_bridge._bridge_instance = None

        custom_url = "ws://custom.example.com:9999"
        bridge = get_openclaw_gateway_bridge(gateway_url=custom_url)

        assert bridge.gateway_url == custom_url

    def test_get_openclaw_gateway_bridge_uses_config_defaults(self):
        """Factory should use config defaults when args are omitted."""
        try:
            from src.integrations import openclaw_gateway_bridge
            from src.integrations.openclaw_gateway_bridge import get_openclaw_gateway_bridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        openclaw_gateway_bridge._bridge_instance = None
        with patch.object(
            openclaw_gateway_bridge,
            "_load_openclaw_config",
            return_value={"gateway_url": "ws://cfg.example:9999", "timeout_seconds": 44},
        ):
            bridge = get_openclaw_gateway_bridge()
        assert bridge.gateway_url == "ws://cfg.example:9999"
        assert bridge.timeout_seconds == 44

    def test_get_openclaw_gateway_bridge_force_reload(self):
        """force_reload should replace singleton with fresh resolved settings."""
        try:
            from src.integrations import openclaw_gateway_bridge
            from src.integrations.openclaw_gateway_bridge import get_openclaw_gateway_bridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        openclaw_gateway_bridge._bridge_instance = None
        bridge_one = get_openclaw_gateway_bridge(gateway_url="ws://first.example:1111")
        bridge_two = get_openclaw_gateway_bridge(
            gateway_url="ws://second.example:2222",
            timeout_seconds=55,
            force_reload=True,
        )
        assert bridge_one is not bridge_two
        assert bridge_two.gateway_url == "ws://second.example:2222"
        assert bridge_two.timeout_seconds == 55


class TestOpenClawGatewayBridgeIntegration:
    """Integration tests for full message flow."""

    @pytest.mark.asyncio
    async def test_full_message_flow(self):
        """Test complete flow: message in -> orchestration -> result out."""
        try:
            from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge
        except ImportError:
            pytest.skip("aiohttp/websockets not installed")

        # Create bridge with mocks
        mock_orchestrator = MagicMock()
        mock_quest_manager = MagicMock()

        bridge = OpenClawGatewayBridge(
            gateway_url="ws://127.0.0.1:18789",
            orchestrator=mock_orchestrator,
            quest_manager=mock_quest_manager,
            timeout_seconds=5,
        )

        # Mock router
        with patch("src.tools.agent_task_router.AgentTaskRouter") as mock_router_class:
            mock_router = MagicMock()
            mock_router.route_task = AsyncMock(
                return_value={
                    "status": "success",
                    "system": "ollama",
                    "task_id": "task-abc-123",
                    "output": "ready",
                }
            )
            mock_router_class.return_value = mock_router

            # Mock HTTP post for result sending
            mock_response = AsyncMock()
            mock_response.status = 200

            with patch("aiohttp.ClientSession.post") as mock_post:
                mock_post.return_value.__aenter__.return_value = mock_response

                # Simulate message flow
                message = {
                    "timestamp": "2025-12-26T10:30:00Z",
                    "channel": "slack",
                    "user_id": "U12345",
                    "username": "alice",
                    "text": "what is quantum computing",
                }

                # Handle message
                result = await bridge.handle_inbound_message(message)

                # Verify routing happened
                assert result["status"] == "success"
                assert result["task_id"] == "task-abc-123"

                # Send result back
                send_success = await bridge.send_result(
                    channel=result["channel"],
                    target_user_id=result["user_id"],
                    result_text=result["result_text"],
                    task_id=result["task_id"],
                )

                assert send_success is True

                # Verify quest was logged
                mock_quest_manager.log_quest.assert_called()
            await bridge.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

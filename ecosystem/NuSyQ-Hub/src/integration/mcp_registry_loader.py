"""MCP Registry Loader - Auto-load MCP servers from registry config.

Wires the orchestrator to read mcp_registry.json and automatically
register MCP servers when feature flags are enabled.

OmniTag: {
    "purpose": "Dynamic MCP server discovery and registration",
    "dependencies": ["mcp_registry.json", "feature_flag_manager", "orchestrator"],
    "context": "MCP server lifecycle management, Phase 3",
    "evolution_stage": "v1.0"
}
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server in registry."""

    id: str
    description: str
    command: list[str]
    env: dict[str, str]
    tags: list[str]
    requires: list[str]  # Feature flags required
    process: subprocess.Popen | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            command=data.get("command", []),
            env=data.get("env", {}),
            tags=data.get("tags", []),
            requires=data.get("requires", []),
        )


class MCPRegistryLoader:
    """Loads and manages MCP servers from registry configuration."""

    def __init__(self, registry_path: Path | None = None):
        """Initialize registry loader.

        Args:
            registry_path: Path to mcp_registry.json
        """
        self.registry_path = registry_path or self._get_default_registry_path()
        self.servers: dict[str, MCPServerConfig] = {}
        self.active_servers: dict[str, MCPServerConfig] = {}
        self._load_registry()

    def _get_default_registry_path(self) -> Path:
        """Get default registry path."""
        repo_root = Path(__file__).parent.parent.parent
        return repo_root / "config" / "mcp_registry.json"

    def _load_registry(self) -> None:
        """Load registry from JSON file."""
        try:
            if not self.registry_path.exists():
                logger.warning(f"Registry not found: {self.registry_path}")
                return

            with open(self.registry_path, encoding="utf-8") as f:
                data = json.load(f)

            # Parse servers
            for item in data:
                config = MCPServerConfig.from_dict(item)
                self.servers[config.id] = config

            logger.info(f"✅ Loaded {len(self.servers)} MCP servers from registry")
            for server_id in self.servers:
                logger.debug(f"  • {server_id}")

        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to load registry: {e}")

    def check_feature_flags(self, server: MCPServerConfig) -> bool:
        """Check if required feature flags are enabled.

        Args:
            server: MCP server config

        Returns:
            True if all required flags are enabled
        """
        try:
            from src.config.feature_flag_manager import \
                get_feature_flag_manager

            mgr = get_feature_flag_manager()

            for flag in server.requires:
                if not mgr.is_feature_enabled(flag):
                    logger.debug(f"  ⚠️  {server.id}: flag '{flag}' not enabled")
                    return False

            return True

        except Exception as e:
            logger.warning(f"Failed to check feature flags: {e}")
            return False

    def validate_server(self, server: MCPServerConfig) -> bool:
        """Validate server configuration.

        Args:
            server: MCP server config

        Returns:
            True if valid
        """
        # Check feature flags
        if not self.check_feature_flags(server):
            return False

        # Validate command
        if not server.command or len(server.command) == 0:
            logger.warning(f"{server.id}: no command specified")
            return False

        return True

    def start_server(self, server_id: str) -> bool:
        """Start an MCP server process.

        Args:
            server_id: Server ID to start

        Returns:
            True if successful
        """
        server = self.servers.get(server_id)
        if not server:
            logger.error(f"Server not found: {server_id}")
            return False

        # Validate
        if not self.validate_server(server):
            logger.warning(f"Skipping {server_id}: validation failed")
            return False

        try:
            # Setup environment
            env = os.environ.copy()
            env.update(server.env)

            # Start process
            logger.info(f"🚀 Starting MCP server: {server_id}")
            logger.debug(f"   Command: {' '.join(server.command)}")

            process = subprocess.Popen(
                server.command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            server.process = process
            self.active_servers[server_id] = server

            logger.info(f"✅ {server_id} started (PID: {process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start {server_id}: {e}")
            return False

    def start_enabled_servers(self) -> int:
        """Start all servers with required flags enabled.

        Returns:
            Number of started servers
        """
        count = 0

        for server_id, server in self.servers.items():
            if self.validate_server(server) and self.start_server(server_id):
                count += 1

        return count

    def stop_server(self, server_id: str) -> bool:
        """Stop an MCP server process.

        Args:
            server_id: Server ID to stop

        Returns:
            True if successful
        """
        server = self.active_servers.get(server_id)
        if not server or not server.process:
            return False

        try:
            server.process.terminate()
            server.process.wait(timeout=5)
            del self.active_servers[server_id]
            logger.info(f"✅ Stopped {server_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop {server_id}: {e}")
            return False

    def stop_all_servers(self) -> int:
        """Stop all active servers.

        Returns:
            Number of stopped servers
        """
        count = 0
        for server_id in self.active_servers:
            if self.stop_server(server_id):
                count += 1
        return count

    def get_server_info(self, server_id: str) -> dict[str, Any] | None:
        """Get information about a server.

        Args:
            server_id: Server ID

        Returns:
            Server info dict or None
        """
        server = self.servers.get(server_id)
        if not server:
            return None

        return {
            "id": server.id,
            "description": server.description,
            "command": server.command,
            "tags": server.tags,
            "requires": server.requires,
            "status": "active" if server_id in self.active_servers else "inactive",
            "pid": server.process.pid if server.process else None,
        }

    def list_servers(self) -> list[dict[str, Any]]:
        """List all registered servers.

        Returns:
            List of server info dicts
        """
        return [
            info
            for server_id in self.servers
            if (info := self.get_server_info(server_id)) is not None
        ]

    def export_manifest(self) -> dict[str, Any]:
        """Export registry manifest.

        Returns:
            Manifest dict
        """
        return {
            "version": "1.0.0",
            "total_servers": len(self.servers),
            "active_servers": len(self.active_servers),
            "servers": [self.get_server_info(sid) for sid in self.servers],
        }


# Global instance
_loader: MCPRegistryLoader | None = None


def get_mcp_registry_loader() -> MCPRegistryLoader:
    """Get global MCP registry loader instance.

    Returns:
        MCPRegistryLoader instance
    """
    global _loader
    if _loader is None:
        _loader = MCPRegistryLoader()
    return _loader


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    loader = get_mcp_registry_loader()

    logger.info("MCP Registry Loader")
    logger.info("=" * 60)

    # Show registry status
    logger.info(f"\n📋 Registered Servers: {len(loader.servers)}")
    for server_id in loader.servers:
        info = loader.get_server_info(server_id)
        if info:
            flags = ", ".join(info.get("requires", [])) if info.get("requires") else "none"
            logger.info(f"  • {server_id}")
            logger.info(f"    {info.get('description', 'No description')}")
            logger.info(f"    Flags: {flags}")

    # Check which can be started
    logger.info("\n✅ Servers that can be started:")
    for server_id, server in loader.servers.items():
        can_start = loader.validate_server(server)
        if can_start:
            logger.info(f"  ✓ {server_id}")
        else:
            logger.error(f"  ✗ {server_id} (flags not enabled)")

    # Show manifest
    logger.info("\n📊 Manifest:")
    manifest = loader.export_manifest()
    logger.info(json.dumps(manifest, indent=2))

"""🔧 Core Configuration Manager for KILO-FOOLISH & NuSyQ-Hub Systems.

=================================================================

Advanced configuration management system that provides:
- Multi-source configuration loading (JSON files, environment variables, defaults)
- Hierarchical configuration with dotted key notation
- Environment variable overrides with intelligent type casting
- Configuration validation and caching
- Hot-reload capabilities for development
- Integration with ZETA development pipeline

🔗 **System Connections:**
- Used by: All core systems, AI orchestrators, quantum processors
- Integrates with: Environment management, performance monitoring
- Supports: Context servers, LLM services, game development pipeline

📋 **Configuration Sources (Priority Order):**
1. Environment variables (highest priority)
2. JSON configuration files
3. Default values (fallback)

🎮 **ZETA Integration:**
- ZETA05: Performance monitoring configuration
- ZETA03: Model selection preferences
- ZETA04: Conversation persistence settings

Author: Enhanced by autonomous agent for systematic repository linking
Last Updated: 2025-08-08
Part of: KILO-FOOLISH Quantum Development Ecosystem
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging for configuration management
logger = logging.getLogger(__name__)


class ConfigManager:
    """🔧 Advanced Configuration Manager.

    Provides hierarchical configuration management with intelligent type casting,
    environment variable overrides, and validation capabilities.

    Features:
    - Dotted key notation for nested configurations
    - Environment variable overrides with type preservation
    - Configuration validation and error handling
    - Hot-reload support for development

    Example:
        >>> config = ConfigManager("config.json")
        >>> host = config.get("context_server.host", "localhost")
        >>> port = config.get("context_server.port", 8000)
        >>> debug = config.get("system.debug", False)

    """

    def __init__(self, config_path: str | Path | None = None) -> None:
        """Initialize ConfigManager with optional configuration file.

        Args:
            config_path: Path to JSON configuration file (optional)

        """
        self._config: dict[str, Any] = {}
        self._config_path: Path | None = None
        self._last_modified: datetime | None = None

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str | Path) -> bool:
        """Load configuration from JSON file with error handling.

        Args:
            config_path: Path to configuration file

        Returns:
            True if successful, False otherwise

        """
        try:
            path = Path(config_path)
            self._config_path = path

            if path.exists():
                content = path.read_text(encoding="utf-8")
                self._config = json.loads(content)
                self._last_modified = datetime.fromtimestamp(path.stat().st_mtime)
                logger.info(f"✅ Configuration loaded from {path}")
                return True
            logger.warning(f"⚠️  Configuration file not found: {path}")
            return False

        except json.JSONDecodeError as e:
            logger.exception(f"❌ Invalid JSON in config file {config_path}: {e}")
            self._config = {}
            return False
        except (ValueError, OSError) as e:
            logger.exception(f"❌ Error loading config from {config_path}: {e}")
            self._config = {}
            return False

    def get(self, key: str, default: Any | None = None) -> Any:
        """🔍 Retrieve configuration value by dotted key with environment override.

        Supports hierarchical access using dot notation (e.g., 'server.database.host').
        Environment variables take precedence and are automatically type-cast.

        Args:
            key: Configuration key in dotted notation
            default: Default value if key not found

        Returns:
            Configuration value with proper type casting

        Examples:
            >>> config.get('context_server.host', 'localhost')
            >>> config.get('context_server.port', 8000)  # Returns int
            >>> config.get('system.debug', False)        # Returns bool

        """
        # Navigate through nested configuration
        parts = key.split(".")
        node: Any = self._config

        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                node = None
                break

        # Use config value or default
        value = node if node is not None else default

        # Check for environment variable override
        env_key = key.replace(".", "_").upper()
        env_val = os.getenv(env_key)

        if env_val is not None:
            # Intelligent type casting based on default value type
            try:
                if isinstance(default, bool):
                    return env_val.lower() in ("1", "true", "yes", "on")
                if isinstance(default, int):
                    return int(env_val)
                if isinstance(default, float):
                    return float(env_val)
                if isinstance(default, list):
                    # Parse comma-separated values
                    return [item.strip() for item in env_val.split(",")]
                return env_val
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️  Type casting failed for {env_key}={env_val}: {e}")
                return env_val

        return value

    def set(self, key: str, value: Any) -> None:
        """🔧 Set configuration value using dotted notation.

        Args:
            key: Configuration key in dotted notation
            value: Value to set

        """
        parts = key.split(".")
        node = self._config

        # Navigate to parent node
        for part in parts[:-1]:
            if part not in node:
                node[part] = {}
            node = node[part]

        # set the value
        node[parts[-1]] = value
        logger.debug(f"🔧 Set config {key} = {value}")

    def get_section(self, section_key: str) -> dict[str, Any]:
        """📂 Get entire configuration section.

        Args:
            section_key: Section key (e.g., 'context_server')

        Returns:
            Dictionary containing all values in the section

        """
        section = self.get(section_key, {})
        return section if isinstance(section, dict) else {}

    def has_config_changed(self) -> bool:
        """🔄 Check if configuration file has been modified.

        Returns:
            True if file was modified since last load

        """
        if not self._config_path or not self._config_path.exists():
            return False

        current_modified = datetime.fromtimestamp(self._config_path.stat().st_mtime)
        return current_modified > (self._last_modified or datetime.min)

    def reload_if_changed(self) -> bool:
        """🔄 Reload configuration if file has changed.

        Returns:
            True if configuration was reloaded

        """
        if self.has_config_changed() and self._config_path:
            logger.info("🔄 Configuration file changed, reloading...")
            return self.load_config(self._config_path)
        return False

    def validate_required_keys(self, required_keys: list) -> bool:
        """✅ Validate that all required configuration keys exist.

        Args:
            required_keys: list of required keys in dotted notation

        Returns:
            True if all keys exist and have non-None values

        """
        missing_keys: list[Any] = []
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)

        if missing_keys:
            logger.error(f"❌ Missing required configuration keys: {missing_keys}")
            return False

        logger.info("✅ All required configuration keys present")
        return True

    def get_all_config(self) -> dict[str, Any]:
        """📋 Get complete configuration dictionary.

        Returns:
            Full configuration dictionary

        """
        return self._config.copy()

    def save_config(self, output_path: str | Path | None = None) -> bool:
        """💾 Save current configuration to JSON file.

        Args:
            output_path: Output file path (uses current path if None)

        Returns:
            True if successful

        """
        try:
            path = Path(output_path) if output_path else self._config_path
            if not path:
                logger.error("❌ No output path specified for config save")
                return False

            path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(self._config, indent=2, ensure_ascii=False)
            path.write_text(content, encoding="utf-8")

            logger.info(f"💾 Configuration saved to {path}")
            return True

        except Exception as e:
            logger.exception(f"❌ Error saving configuration: {e}")
            return False


# 🌟 Global Configuration Instance for System-Wide Access
_global_config_manager: ConfigManager | None = None


def get_global_config() -> ConfigManager:
    """🌍 Get or create global configuration manager instance.

    Returns:
        Global ConfigManager instance

    """
    global _global_config_manager
    if _global_config_manager is None:
        # Try to load from standard locations
        config_paths = [
            Path("config.json"),
            Path("config/config.json"),
            Path("../config.json"),
            Path("../../config.json"),
        ]

        _global_config_manager = ConfigManager()
        for path in config_paths:
            if path.exists():
                _global_config_manager.load_config(path)
                break

    return _global_config_manager


def set_global_config(config_manager: ConfigManager) -> None:
    """🔧 Set global configuration manager instance.

    Args:
        config_manager: ConfigManager instance to use globally

    """
    global _global_config_manager
    _global_config_manager = config_manager


# 🎯 Convenience Functions for Common Configuration Access
def get_context_server_config() -> dict[str, Any]:
    """Get context server configuration section."""
    return get_global_config().get_section("context_server")


def get_ollama_config() -> dict[str, Any]:
    """Get Ollama LLM configuration section."""
    return get_global_config().get_section("ollama")


def get_system_config() -> dict[str, Any]:
    """Get system configuration section."""
    return get_global_config().get_section("system")


def get_zeta_config() -> dict[str, Any]:
    """Get ZETA development pipeline configuration."""
    return get_global_config().get_section("zeta")


# 🧪 Development and Testing Utilities
if __name__ == "__main__":
    # Demo and testing functionality

    # Create test configuration
    config = ConfigManager()
    config.set("context_server.host", "localhost")
    config.set("context_server.port", 8000)
    config.set("system.debug", True)
    config.set("ollama.models", ["llama2", "codellama"])

    # Demonstrate functionality

    # Test environment override
    os.environ["CONTEXT_SERVER_PORT"] = "9000"

    # Test validation
    required = ["context_server.host", "context_server.port"]
    is_valid = config.validate_required_keys(required)

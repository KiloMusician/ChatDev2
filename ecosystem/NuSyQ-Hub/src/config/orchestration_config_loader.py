"""Orchestration Configuration Loader.

Provides centralized access to orchestration_defaults.json for all NuSyQ systems.
This module serves as the single source of truth for operational configuration.

Usage:
    from src.config.orchestration_config_loader import load_orchestration_defaults

    config = load_orchestration_defaults()

    # Access terminal routing
    routing_strategy = config["terminal_routing"]["routing_strategy"]

    # Access guild board settings
    quest_id_format = config["guild_board"]["quest_management"]["quest_id_format"]

    # Access lifecycle management
    cadence_minutes = config["lifecycle_management"]["cadence_minutes"]
"""

import json
import logging
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "orchestration_defaults.json"


class OrchestrationConfigLoader:
    """Lazy loader for orchestration defaults with singleton factory behavior."""

    _instance: "OrchestrationConfigLoader | None" = None
    _config: dict[str, Any] | None

    def __new__(cls) -> "OrchestrationConfigLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = None
        return cls._instance

    def get_config(self) -> dict[str, Any]:
        """Get cached config or load it on first access."""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def refresh(self) -> dict[str, Any]:
        """Force a reload of the configuration."""
        self._config = None
        return self.get_config()

    def _load_config(self) -> dict[str, Any]:
        """Load orchestration_defaults.json from disk."""
        if not CONFIG_FILE.exists():
            raise FileNotFoundError(
                f"orchestration_defaults.json not found at {CONFIG_FILE}. Current working directory: {Path.cwd()}"
            )

        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"✅ Loaded configuration from {CONFIG_FILE}")
            if not isinstance(config, dict):
                raise TypeError("orchestration_defaults.json must contain a JSON object")
            return cast(dict[str, Any], config)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON in {CONFIG_FILE}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading configuration: {e}")
            raise


_CONFIG_LOADER = OrchestrationConfigLoader()


def _get_section(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key, {})
    return value if isinstance(value, dict) else {}


def load_orchestration_defaults() -> dict[str, Any]:
    """Load and cache orchestration_defaults.json.

    Returns:
        Dict containing all operational configuration
    """
    return _CONFIG_LOADER.get_config()


def get_terminal_routing_config() -> dict[str, Any]:
    """Get terminal routing configuration section."""
    config = load_orchestration_defaults()
    return _get_section(config, "terminal_routing")


def get_guild_board_config() -> dict[str, Any]:
    """Get guild board configuration section."""
    config = load_orchestration_defaults()
    return _get_section(config, "guild_board")


def get_guild_heartbeat_config() -> dict[str, Any]:
    """Get guild board heartbeat configuration."""
    guild_config = get_guild_board_config()
    return _get_section(guild_config, "heartbeat")


def get_guild_quest_config() -> dict[str, Any]:
    """Get guild board quest management configuration."""
    guild_config = get_guild_board_config()
    return _get_section(guild_config, "quest_management")


def get_guild_state_config() -> dict[str, Any]:
    """Get guild board state configuration."""
    guild_config = get_guild_board_config()
    return _get_section(guild_config, "board_state")


def get_guild_rendering_config() -> dict[str, Any]:
    """Get guild board rendering configuration."""
    guild_config = get_guild_board_config()
    return _get_section(guild_config, "rendering")


def get_guild_permissions_config() -> dict[str, Any]:
    """Get guild board permissions configuration."""
    guild_config = get_guild_board_config()
    return _get_section(guild_config, "permissions")


def get_guild_integration_config() -> dict[str, Any]:
    """Get guild board integration configuration."""
    guild_config = get_guild_board_config()
    return _get_section(guild_config, "integration")


def get_guild_signals_config() -> dict[str, Any]:
    """Get guild board signals configuration."""
    guild_config = get_guild_board_config()
    return _get_section(guild_config, "signals")


def get_guild_automation_config() -> dict[str, Any]:
    """Get guild board automation configuration."""
    guild_config = get_guild_board_config()
    return _get_section(guild_config, "automation")


def get_guild_advanced_config() -> dict[str, Any]:
    """Get guild board advanced configuration."""
    guild_config = get_guild_board_config()
    return _get_section(guild_config, "advanced")


def get_lifecycle_management_config() -> dict[str, Any]:
    """Get lifecycle management configuration section."""
    config = load_orchestration_defaults()
    return _get_section(config, "lifecycle_management")


def get_navigation_config() -> dict[str, Any]:
    """Get navigation (wizard navigator) configuration section."""
    config = load_orchestration_defaults()
    return _get_section(config, "navigation")


def get_error_remediation_config() -> dict[str, Any]:
    """Get error remediation configuration section."""
    config = load_orchestration_defaults()
    return _get_section(config, "error_remediation")


def get_observability_config() -> dict[str, Any]:
    """Get observability configuration section."""
    config = load_orchestration_defaults()
    return _get_section(config, "observability")


def get_dispatch_profiles_config() -> dict[str, Any]:
    """Get dispatch profile defaults/overrides configuration section."""
    config = load_orchestration_defaults()
    return _get_section(config, "dispatch_profiles")


def get_achievements_config() -> dict[str, Any]:
    """Get achievements configuration section."""
    config = load_orchestration_defaults()
    return _get_section(config, "achievements")


def get_readiness_scoring_config() -> dict[str, Any]:
    """Get readiness scoring configuration section."""
    config = load_orchestration_defaults()
    return _get_section(config, "readiness_scoring")


def get_config_value(path: str, default: Any | None = None) -> Any:
    """Get a configuration value using dot notation path.

    Args:
        path: Dot-separated path (e.g., "guild_board.heartbeat.heartbeat_interval_seconds")
        default: Default value if path not found

    Returns:
        Configuration value or default

    Example:
        >>> heartbeat_interval = get_config_value("guild_board.heartbeat.heartbeat_interval_seconds")
        >>> routing_strategy = get_config_value("terminal_routing.routing_strategy")
    """
    config = load_orchestration_defaults()
    keys = path.split(".")
    value = config

    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        logger.warning(f"⚠️ Configuration path not found: {path}")
        return default


def validate_config() -> bool:
    """Validate that orchestration_defaults.json is properly formatted.

    Returns:
        True if valid, False otherwise
    """
    try:
        config = load_orchestration_defaults()

        # Validate top-level keys
        required_sections = [
            "terminal_routing",
            "guild_board",
            "lifecycle_management",
            "navigation",
            "error_remediation",
        ]

        for section in required_sections:
            if section not in config:
                logger.error(f"❌ Missing required section: {section}")
                return False

        # Validate guild_board subsections
        guild = config.get("guild_board", {})
        guild_subsections = [
            "heartbeat",
            "quest_management",
            "board_state",
            "rendering",
            "permissions",
            "integration",
            "signals",
            "automation",
            "advanced",
        ]

        for subsection in guild_subsections:
            if subsection not in guild:
                logger.error(f"❌ Missing guild_board subsection: {subsection}")
                return False

        logger.info("✅ Configuration validation passed")
        return True

    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return False


def print_config_summary() -> None:
    """Print a summary of loaded configuration for debugging."""
    config = load_orchestration_defaults()

    logger.info("\n" + "=" * 70)
    logger.info("🔧 ORCHESTRATION CONFIGURATION SUMMARY")
    logger.info("=" * 70)

    for section, values in config.items():
        if isinstance(values, dict):
            logger.info(f"\n[{section.upper()}]")
            if section == "guild_board":
                # Special handling for nested guild_board
                for subsection, subvalues in values.items():
                    logger.info(f"  {subsection}:")
                    if isinstance(subvalues, dict):
                        for key, val in list(subvalues.items())[:3]:  # First 3 items
                            logger.info(f"    {key}: {val}")
                        if len(subvalues) > 3:
                            logger.info(f"    ... +{len(subvalues) - 3} more")
            else:
                for key, val in list(values.items())[:3]:  # First 3 items
                    logger.info(f"  {key}: {val}")
                if len(values) > 3:
                    logger.info(f"  ... +{len(values) - 3} more")

    logger.info("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    # Test configuration loading
    logger.info("Testing orchestration configuration loader...\n")

    # Load and validate
    if validate_config():
        logger.info("\n✅ Configuration is valid\n")

        # Print summary
        print_config_summary()

        # Test path access
        logger.info("\nTesting path-based access:")
        quest_format = get_config_value("guild_board.quest_management.quest_id_format")
        logger.info(f"  Quest ID format: {quest_format}")

        routing = get_config_value("terminal_routing.routing_strategy")
        logger.info(f"  Terminal routing strategy: {routing}")

        cadence = get_config_value("lifecycle_management.cadence_minutes")
        logger.info(f"  Lifecycle cadence: {cadence} minutes")
    else:
        logger.error("❌ Configuration validation failed")

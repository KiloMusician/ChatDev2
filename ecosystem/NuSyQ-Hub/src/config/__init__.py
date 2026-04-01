"""Config subsystem — feature flags, service config, and orchestration settings.

Provides centralized configuration management for the NuSyQ ecosystem:
feature flag evaluation, service endpoint configuration, and orchestration
parameter loading from JSON/YAML config files.

OmniTag: {
    "purpose": "config_subsystem",
    "tags": ["Config", "FeatureFlags", "ServiceConfig", "Orchestration"],
    "category": "infrastructure",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.feature_flag_manager import (Environment,
                                                 FeatureFlagManager,
                                                 get_feature_flag_manager,
                                                 is_feature_enabled)
    from src.config.orchestration_config_loader import (
        OrchestrationConfigLoader, get_guild_board_config,
        get_terminal_routing_config, load_orchestration_defaults)
    from src.config.service_config import ServiceConfig, get_service_config

__all__ = [
    # Feature flags
    "Environment",
    "FeatureFlagManager",
    # Orchestration config
    "OrchestrationConfigLoader",
    # Service config
    "ServiceConfig",
    "get_feature_flag_manager",
    "get_guild_board_config",
    "get_service_config",
    "get_terminal_routing_config",
    "is_feature_enabled",
    "load_orchestration_defaults",
]


def __getattr__(name: str):
    if name in (
        "Environment",
        "FeatureFlagManager",
        "get_feature_flag_manager",
        "is_feature_enabled",
    ):
        from src.config.feature_flag_manager import (Environment,
                                                     FeatureFlagManager,
                                                     get_feature_flag_manager,
                                                     is_feature_enabled)

        return locals()[name]
    if name in ("ServiceConfig", "get_service_config"):
        from src.config.service_config import ServiceConfig, get_service_config

        return locals()[name]
    if name in (
        "OrchestrationConfigLoader",
        "load_orchestration_defaults",
        "get_terminal_routing_config",
        "get_guild_board_config",
    ):
        from src.config.orchestration_config_loader import (
            OrchestrationConfigLoader, get_guild_board_config,
            get_terminal_routing_config, load_orchestration_defaults)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

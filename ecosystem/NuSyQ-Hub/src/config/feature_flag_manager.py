"""Feature Flag Manager for NuSyQ-Hub.

Provides environment-based feature gating and ACL controls for experimental
features and tool access.

Inspired by: ChatOllama's toggleable module architecture
OmniTag: {
    "purpose": "Feature flag and ACL management",
    "dependencies": ["config/feature_flags.json"],
    "context": "Production safety, experimental feature gating",
    "evolution_stage": "v1.0"
}
"""

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Execution environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class FeatureFlagManager:
    """Manages feature flags and ACL controls for NuSyQ-Hub.

    Features:
    - Environment-based feature gating
    - ACL controls for sensitive operations
    - Runtime feature toggles
    - Safe defaults (opt-in for experimental features)
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize feature flag manager.

        Args:
            config_path: Path to feature_flags.json config file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config: dict[str, Any] = self._load_config()
        self.environment = self._detect_environment()
        # Env override for global ACL (ChatOllama-style ACL_ENABLED flag)
        if os.getenv("ACL_ENABLED", "").lower() in {"1", "true", "yes", "on"}:
            self.config.setdefault("acl", {}).setdefault("global_acl", {})["enabled"] = True

    def _get_default_config_path(self) -> Path:
        """Get default path to feature flags config."""
        repo_root = Path(__file__).parent.parent.parent
        return repo_root / "config" / "feature_flags.json"

    def _detect_environment(self) -> Environment:
        """Detect current execution environment."""
        env_var = os.getenv("NUSYQ_ENVIRONMENT", "development").lower()

        try:
            return Environment(env_var)
        except ValueError:
            # Default to development for safety
            return Environment.DEVELOPMENT

    def _load_config(self) -> dict[str, Any]:
        """Load feature flags configuration."""
        if not self.config_path.exists():
            # Return safe defaults if config doesn't exist
            return self._get_default_config()

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            return self._get_default_config()
        except (OSError, json.JSONDecodeError):
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default feature flag configuration (safe defaults)."""
        return {
            "features": {
                "chatdev_mcp_enabled": {
                    "enabled": False,
                    "description": "Expose ChatDev as MCP server",
                    "environments": ["development", "staging"],
                    "requires_acl": True,
                },
                "testing_chamber_enabled": {
                    "enabled": True,
                    "description": "Allow Testing Chamber operations",
                    "environments": ["development"],
                    "requires_acl": False,
                },
                "consensus_mode_enabled": {
                    "enabled": False,
                    "description": "Multi-model consensus experiments",
                    "environments": ["development"],
                    "requires_acl": True,
                },
                "quantum_resolver_enabled": {
                    "enabled": True,
                    "description": "Quantum problem resolution",
                    "environments": ["development", "production"],
                    "requires_acl": False,
                },
                "chatdev_tools_enabled": {
                    "enabled": False,
                    "description": "ChatDev agent tool access",
                    "environments": ["development"],
                    "requires_acl": True,
                },
                "project_auto_index_enabled": {
                    "enabled": False,
                    "description": "Auto-index ChatDev projects to RAG",
                    "environments": ["development", "staging"],
                    "requires_acl": False,
                },
                "overnight_safe_mode": {
                    "enabled": False,
                    "description": "Restricted operations for autonomous work",
                    "environments": ["development", "production"],
                    "requires_acl": False,
                },
                "chatdev_git_mode_enabled": {
                    "enabled": False,
                    "description": "Git-aware ChatDev runs that write to branches",
                    "environments": ["development", "staging"],
                    "requires_acl": True,
                },
                "mcp_registry_enabled": {
                    "enabled": True,
                    "description": "MCP registry for auto-routing",
                    "environments": ["development", "staging"],
                    "requires_acl": False,
                },
                "trust_artifacts_enabled": {
                    "enabled": True,
                    "description": "Artifact ledger + manifest + replay bundle for every run",
                    "environments": ["development", "staging"],
                    "requires_acl": False,
                },
                "gateway_router_enabled": {
                    "enabled": True,
                    "description": "Universal LLM gateway + SwarmRouter facade",
                    "environments": ["development", "staging"],
                    "requires_acl": False,
                },
                "sandbox_runner_enabled": {
                    "enabled": False,
                    "description": "Per-task sandbox/containers",
                    "environments": ["development", "staging"],
                    "requires_acl": True,
                },
                "planning_discipline_enabled": {
                    "enabled": True,
                    "description": "Dual-plan + early-test + cost/time telemetry",
                    "environments": ["development", "staging"],
                    "requires_acl": False,
                },
                "mission_control_enabled": {
                    "enabled": False,
                    "description": "Mission Control reporting and observability stubs",
                    "environments": ["development", "staging"],
                    "requires_acl": False,
                },
                "knowledge_reuse_enabled": {
                    "enabled": True,
                    "description": "Artifact ingest, pattern catalog, Three-Before-New checks",
                    "environments": ["development", "staging"],
                    "requires_acl": False,
                },
                "policy_audit_enabled": {
                    "enabled": True,
                    "description": "Safety preflight/PII checks",
                    "environments": ["development", "staging"],
                    "requires_acl": True,
                },
                "attestation_enabled": {
                    "enabled": False,
                    "description": "Manifest signing/attestation",
                    "environments": ["development", "staging"],
                    "requires_acl": True,
                },
                "chatdev_ci_smoke_enabled": {
                    "enabled": False,
                    "description": "Dockerized ChatDev smoke tests",
                    "environments": ["development"],
                    "requires_acl": False,
                },
            },
            "acl": {
                "mcp_management": {
                    "enabled": False,
                    "allowed_users": [],
                    "allowed_environments": ["development"],
                },
                "tool_registration": {
                    "enabled": False,
                    "allowed_tools": [],
                    "allowed_roles": ["Programmer", "Tester"],
                },
                "global_acl": {
                    "enabled": False,
                    "allowed_environments": ["development", "staging", "production"],
                },
            },
        }

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled in current environment.

        Args:
            feature_name: Name of feature flag to check

        Returns:
            True if feature is enabled, False otherwise
        """
        features = self.config.get("features", {})

        # Also check root level for flat feature structure
        if not features and feature_name in self.config:
            feature = self.config[feature_name]
        else:
            feature = features.get(feature_name)

        if not feature:
            # Unknown features default to disabled for safety
            return False

        # Handle both schema formats:
        # Format 1: {"enabled": true, "environments": ["dev"]}
        # Format 2: {"default": true, "development": true, "staging": false}

        # Format 1 (new schema with enabled/environments)
        if "enabled" in feature:
            if not feature.get("enabled", False):
                return False

            # Check environment restriction
            allowed_envs = feature.get("environments", [])
            if allowed_envs and self.environment.value not in allowed_envs:
                return False

        # Format 2 (existing schema with environment-specific flags)
        else:
            env_key = self.environment.value
            enabled = feature.get(env_key, feature.get("default", False))

            if not enabled:
                return False

        # Check ACL if required
        if feature.get("requires_acl", False):
            return self._check_acl_permission(feature_name)

        return True

    def _check_acl_permission(self, feature_name: str) -> bool:
        """Check ACL permission for a feature.

        Args:
            feature_name: Name of feature requiring ACL check

        Returns:
            True if ACL permits access, False otherwise
        """
        acl_config = self.config.get("acl", {})

        # Map features to ACL rules
        acl_mapping = {
            "chatdev_mcp_enabled": "mcp_management",
            "chatdev_tools_enabled": "tool_registration",
            "consensus_mode_enabled": "mcp_management",
        }

        acl_key = acl_mapping.get(feature_name)
        if not acl_key:
            # No ACL rule, deny by default
            return False

        acl_rule = acl_config.get(acl_key, {})
        global_acl = acl_config.get("global_acl", {})
        acl_enabled = acl_rule.get("enabled", False) or global_acl.get("enabled", False)
        if not acl_enabled:
            return False

        # Check environment restriction
        allowed_envs = acl_rule.get("allowed_environments", [])
        if allowed_envs and self.environment.value not in allowed_envs:
            return False

        # Check user restriction (if applicable)
        allowed_users = acl_rule.get("allowed_users", [])
        if allowed_users:
            current_user = os.getenv("USER") or os.getenv("USERNAME")
            if current_user and current_user not in allowed_users:
                return False

        return True

    def get_feature_description(self, feature_name: str) -> str | None:
        """Get description of a feature.

        Args:
            feature_name: Name of feature flag

        Returns:
            Feature description or None if not found
        """
        features = self.config.get("features", {})

        # Check features dict
        if isinstance(features, dict) and feature_name in features:
            feature_config = features[feature_name]
            if isinstance(feature_config, dict):
                description = feature_config.get("description")
                return str(description) if description is not None else None

        # Check root level (flat structure)
        if feature_name in self.config and isinstance(self.config[feature_name], dict):
            description = self.config[feature_name].get("description")
            return str(description) if description is not None else None

        return None

    def list_enabled_features(self) -> list[str]:
        """List all enabled features in current environment.

        Returns:
            List of enabled feature names
        """
        enabled = []

        # Check features dict if it exists
        features = self.config.get("features", {})
        if features:
            for feature_name in features:
                if self.is_feature_enabled(feature_name):
                    enabled.append(feature_name)
        else:
            # Flat structure - each key is a feature
            for feature_name in self.config:
                if feature_name in ["metadata", "acl"]:
                    continue
                if self.is_feature_enabled(feature_name):
                    enabled.append(feature_name)

        return enabled

    def enable_feature(self, feature_name: str, environments: list[str] | None = None) -> bool:
        """Enable a feature (runtime toggle).

        Args:
            feature_name: Name of feature to enable
            environments: Optional list of environments to enable for

        Returns:
            True if successful, False otherwise
        """
        features = self.config.get("features", {})

        if feature_name not in features:
            return False

        features[feature_name]["enabled"] = True

        if environments:
            features[feature_name]["environments"] = environments

        return self._save_config()

    def disable_feature(self, feature_name: str) -> bool:
        """Disable a feature (runtime toggle).

        Args:
            feature_name: Name of feature to disable

        Returns:
            True if successful, False otherwise
        """
        features = self.config.get("features", {})

        if feature_name not in features:
            return False

        features[feature_name]["enabled"] = False
        return self._save_config()

    def _save_config(self) -> bool:
        """Save current configuration to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)

            return True
        except OSError:
            return False

    def get_status_report(self) -> dict[str, Any]:
        """Get comprehensive status report.

        Returns:
            Status report with environment and enabled features
        """
        features = self.config.get("features", {})
        total_features = (
            len(features)
            if features
            else len([k for k in self.config if k not in ["metadata", "acl"]])
        )

        return {
            "environment": self.environment.value,
            "config_path": str(self.config_path),
            "enabled_features": self.list_enabled_features(),
            "total_features": total_features,
            "acl_enabled": any(
                acl.get("enabled", False) for acl in self.config.get("acl", {}).values()
            ),
        }


# Global instance for easy access
_manager: FeatureFlagManager | None = None


def get_feature_flag_manager() -> FeatureFlagManager:
    """Get global feature flag manager instance.

    Returns:
        FeatureFlagManager instance
    """
    global _manager
    if _manager is None:
        _manager = FeatureFlagManager()
    return _manager


def is_feature_enabled(feature_name: str) -> bool:
    """Convenience function to check if a feature is enabled.

    Args:
        feature_name: Name of feature flag

    Returns:
        True if enabled, False otherwise
    """
    return get_feature_flag_manager().is_feature_enabled(feature_name)


if __name__ == "__main__":
    # Demo usage
    manager = FeatureFlagManager()

    logger.info("Feature Flag Status Report")
    logger.info("=" * 60)

    status = manager.get_status_report()
    logger.info(f"Environment: {status['environment']}")
    logger.info(f"Config: {status['config_path']}")
    logger.info(f"Total Features: {status['total_features']}")
    logger.info(f"ACL Enabled: {status['acl_enabled']}")
    logger.info(f"\nEnabled Features ({len(status['enabled_features'])}):")

    for feature in status["enabled_features"]:
        desc = manager.get_feature_description(feature)
        logger.info(f"  ✅ {feature}")
        logger.info(f"     {desc}")

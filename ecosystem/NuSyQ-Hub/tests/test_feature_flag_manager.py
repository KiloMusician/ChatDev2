"""Tests for src/config/feature_flag_manager.py."""

import json
import os

import pytest

from src.config.feature_flag_manager import (
    Environment,
    FeatureFlagManager,
    get_feature_flag_manager,
    is_feature_enabled,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_config(tmp_path, data):
    """Write a feature_flags.json file and return its path."""
    cfg = tmp_path / "feature_flags.json"
    cfg.write_text(json.dumps(data), encoding="utf-8")
    return cfg


def _minimal_config(extra_features=None, extra_acl=None):
    """Return a minimal valid config dict."""
    features = {
        "alpha": {
            "enabled": True,
            "description": "Alpha feature",
            "environments": ["development"],
            "requires_acl": False,
        },
        "beta": {
            "enabled": False,
            "description": "Beta feature",
            "environments": ["development", "staging"],
            "requires_acl": False,
        },
    }
    if extra_features:
        features.update(extra_features)

    acl = {
        "global_acl": {"enabled": False, "allowed_environments": ["development"]},
    }
    if extra_acl:
        acl.update(extra_acl)

    return {"features": features, "acl": acl}


# ---------------------------------------------------------------------------
# TestEnvironmentEnum
# ---------------------------------------------------------------------------

class TestEnvironmentEnum:
    """Tests for the Environment enum."""

    def test_enum_members_exist(self):
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TESTING.value == "testing"

    def test_enum_from_value(self):
        env = Environment("staging")
        assert env is Environment.STAGING

    def test_enum_invalid_value_raises(self):
        with pytest.raises(ValueError):
            Environment("nonexistent")


# ---------------------------------------------------------------------------
# TestFeatureFlagManagerInit
# ---------------------------------------------------------------------------

class TestFeatureFlagManagerInit:
    """Tests for FeatureFlagManager initialization."""

    def test_init_with_missing_config_uses_defaults(self, tmp_path):
        cfg = tmp_path / "no_such_file.json"
        mgr = FeatureFlagManager(config_path=cfg)
        assert "features" in mgr.config
        assert len(mgr.config["features"]) > 0

    def test_init_with_valid_config_file(self, tmp_path):
        data = _minimal_config()
        cfg = _write_config(tmp_path, data)
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.config["features"]["alpha"]["enabled"] is True

    def test_init_stores_config_path(self, tmp_path):
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.config_path == cfg

    def test_init_detects_environment(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "staging")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.environment is Environment.STAGING

    def test_init_bad_env_var_falls_back_to_development(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "invalid_env")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.environment is Environment.DEVELOPMENT

    def test_init_bad_json_uses_defaults(self, tmp_path):
        cfg = tmp_path / "bad.json"
        cfg.write_text("{ not valid json", encoding="utf-8")
        mgr = FeatureFlagManager(config_path=cfg)
        assert "features" in mgr.config

    def test_init_non_dict_json_uses_defaults(self, tmp_path):
        cfg = tmp_path / "list.json"
        cfg.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        mgr = FeatureFlagManager(config_path=cfg)
        assert isinstance(mgr.config, dict)
        assert "features" in mgr.config


# ---------------------------------------------------------------------------
# TestIsFeatureEnabled
# ---------------------------------------------------------------------------

class TestIsFeatureEnabled:
    """Tests for is_feature_enabled / list_enabled_features."""

    def test_enabled_feature_in_matching_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "development")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.is_feature_enabled("alpha") is True

    def test_disabled_feature_returns_false(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "development")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.is_feature_enabled("beta") is False

    def test_unknown_feature_returns_false(self, tmp_path):
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.is_feature_enabled("does_not_exist") is False

    def test_enabled_feature_wrong_env_returns_false(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "production")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        # alpha only allowed in development
        assert mgr.is_feature_enabled("alpha") is False

    def test_format2_env_specific_flag(self, tmp_path, monkeypatch):
        """Format 2 schema: environment keys instead of 'enabled'."""
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "development")
        data = {
            "features": {
                "legacy_flag": {
                    "default": False,
                    "development": True,
                    "production": False,
                }
            },
            "acl": {},
        }
        cfg = _write_config(tmp_path, data)
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.is_feature_enabled("legacy_flag") is True

    def test_list_enabled_features_returns_list(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "development")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        enabled = mgr.list_enabled_features()
        assert isinstance(enabled, list)
        assert "alpha" in enabled
        assert "beta" not in enabled


# ---------------------------------------------------------------------------
# TestEnableDisableFeature
# ---------------------------------------------------------------------------

class TestEnableDisableFeature:
    """Tests for enable_feature / disable_feature runtime toggles."""

    def test_enable_feature_persists_to_disk(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "development")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        result = mgr.enable_feature("beta", environments=["development"])
        assert result is True
        assert mgr.is_feature_enabled("beta") is True

        # Reload from disk to confirm persistence
        mgr2 = FeatureFlagManager(config_path=cfg)
        assert mgr2.is_feature_enabled("beta") is True

    def test_disable_feature_persists_to_disk(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "development")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        result = mgr.disable_feature("alpha")
        assert result is True
        assert mgr.is_feature_enabled("alpha") is False

    def test_enable_nonexistent_feature_returns_false(self, tmp_path):
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.enable_feature("ghost_feature") is False

    def test_disable_nonexistent_feature_returns_false(self, tmp_path):
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.disable_feature("ghost_feature") is False


# ---------------------------------------------------------------------------
# TestGetFeatureDescription
# ---------------------------------------------------------------------------

class TestGetFeatureDescription:
    """Tests for get_feature_description."""

    def test_known_feature_returns_description(self, tmp_path):
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        desc = mgr.get_feature_description("alpha")
        assert desc == "Alpha feature"

    def test_unknown_feature_returns_none(self, tmp_path):
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.get_feature_description("nonexistent") is None


# ---------------------------------------------------------------------------
# TestGetStatusReport
# ---------------------------------------------------------------------------

class TestGetStatusReport:
    """Tests for get_status_report."""

    def test_status_report_structure(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "development")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        report = mgr.get_status_report()

        assert "environment" in report
        assert "config_path" in report
        assert "enabled_features" in report
        assert "total_features" in report
        assert "acl_enabled" in report

    def test_status_report_environment_matches(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "staging")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        report = mgr.get_status_report()
        assert report["environment"] == "staging"

    def test_status_report_total_features_count(self, tmp_path):
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        report = mgr.get_status_report()
        # _minimal_config has 2 features
        assert report["total_features"] == 2

    def test_status_report_acl_enabled_false_by_default(self, tmp_path):
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        report = mgr.get_status_report()
        assert report["acl_enabled"] is False


# ---------------------------------------------------------------------------
# TestAclBehavior
# ---------------------------------------------------------------------------

class TestAclBehavior:
    """Tests for ACL-gated features."""

    def test_feature_requiring_acl_denied_when_acl_disabled(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NUSYQ_ENVIRONMENT", "development")
        data = _minimal_config(
            extra_features={
                "secure_op": {
                    "enabled": True,
                    "description": "Secure op",
                    "environments": ["development"],
                    "requires_acl": True,
                }
            }
        )
        cfg = _write_config(tmp_path, data)
        mgr = FeatureFlagManager(config_path=cfg)
        # No ACL mapping for 'secure_op' → denied
        assert mgr.is_feature_enabled("secure_op") is False

    def test_acl_enabled_env_var_sets_global_acl(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ACL_ENABLED", "1")
        cfg = _write_config(tmp_path, _minimal_config())
        mgr = FeatureFlagManager(config_path=cfg)
        assert mgr.config["acl"]["global_acl"]["enabled"] is True
        # Restore: remove env so other tests aren't affected
        monkeypatch.delenv("ACL_ENABLED", raising=False)


# ---------------------------------------------------------------------------
# TestModuleLevelConvenienceFunctions
# ---------------------------------------------------------------------------

class TestModuleLevelConvenienceFunctions:
    """Tests for module-level get_feature_flag_manager / is_feature_enabled."""

    def test_get_feature_flag_manager_returns_instance(self):
        mgr = get_feature_flag_manager()
        assert isinstance(mgr, FeatureFlagManager)

    def test_get_feature_flag_manager_is_singleton(self):
        mgr1 = get_feature_flag_manager()
        mgr2 = get_feature_flag_manager()
        assert mgr1 is mgr2

    def test_module_is_feature_enabled_returns_bool(self):
        result = is_feature_enabled("quantum_resolver_enabled")
        assert isinstance(result, bool)

    def test_module_is_feature_enabled_unknown_returns_false(self):
        assert is_feature_enabled("__totally_unknown_flag__") is False


# ---------------------------------------------------------------------------
# TestDefaultConfig
# ---------------------------------------------------------------------------

class TestDefaultConfig:
    """Tests against the built-in safe defaults."""

    def test_default_config_has_known_flags(self, tmp_path):
        cfg = tmp_path / "missing.json"  # Does not exist → defaults
        mgr = FeatureFlagManager(config_path=cfg)
        features = mgr.config["features"]
        assert "chatdev_mcp_enabled" in features
        assert "quantum_resolver_enabled" in features
        assert "testing_chamber_enabled" in features

    def test_default_config_safe_defaults_disabled(self, tmp_path):
        """Sensitive flags must default to disabled."""
        cfg = tmp_path / "missing.json"
        mgr = FeatureFlagManager(config_path=cfg)
        features = mgr.config["features"]
        assert features["chatdev_mcp_enabled"]["enabled"] is False
        assert features["sandbox_runner_enabled"]["enabled"] is False

    def test_default_config_acl_disabled(self, tmp_path):
        cfg = tmp_path / "missing.json"
        mgr = FeatureFlagManager(config_path=cfg)
        acl = mgr.config["acl"]
        assert acl["global_acl"]["enabled"] is False
        assert acl["mcp_management"]["enabled"] is False

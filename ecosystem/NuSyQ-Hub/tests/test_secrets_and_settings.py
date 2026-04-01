import json
import os

import pytest
from KILO_Core import secrets
from src.utils.settings import load_settings


def test_secrets_manager_singleton():
    a = secrets.get_secrets_manager()
    b = secrets.get_secrets_manager()
    assert a is b


def test_get_api_key_none_by_default():
    # ensure env is not set for the test
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    assert secrets.get_api_key("openai") is None


def test_get_ai_service_config_contains_keys():
    manager = secrets.get_secrets_manager()
    config = manager.get_ai_service_config()
    assert "openai_api_key" in config
    assert "ollama_host" in config


def test_load_settings_merges_defaults(tmp_path):
    tmp_file = tmp_path / "tmp_settings.json"
    sample = {
        "ollama": {"host": "http://example.local"},
        "feature_flags": {"enable_chatdev": False},
    }
    tmp_file.write_text(json.dumps(sample), encoding="utf-8")

    merged = load_settings(str(tmp_file))
    assert isinstance(merged, dict)
    # default settings are preserved, ollama host is overridden
    assert merged["ollama"]["host"] == "http://example.local"
    assert merged["feature_flags"]["enable_chatdev"] is False


if __name__ == "__main__":
    pytest.main([__file__])

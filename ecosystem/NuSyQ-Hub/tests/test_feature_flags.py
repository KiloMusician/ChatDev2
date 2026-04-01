import importlib

from src.system import feature_flags


def test_chatdev_autofix_default_disabled(monkeypatch):
    monkeypatch.delenv("NUSYQ_ENV", raising=False)
    importlib.reload(feature_flags)
    assert not feature_flags.is_feature_enabled("chatdev_autofix")


def test_chatdev_autofix_staging_enabled(monkeypatch):
    monkeypatch.setenv("NUSYQ_ENV", "staging")
    importlib.reload(feature_flags)
    assert feature_flags.is_feature_enabled("chatdev_autofix")

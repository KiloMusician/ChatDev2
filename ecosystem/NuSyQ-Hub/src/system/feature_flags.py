"""Feature flag management utilities for NuSyQ-Hub.

Provides helpers to determine whether experimental capabilities should
be enabled. Flags are defined in ``config/feature_flags.json`` with a
``default`` state and optional environment overrides (e.g., ``staging``).

Environment selection is driven by the ``NUSYQ_ENV`` environment
variable. If unset, ``production`` is assumed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "feature_flags.json"


def _load_flags(path: Path) -> dict[str, dict[str, Any]]:
    """Load flag definitions from ``feature_flags.json``."""
    if not path.exists():  # pragma: no cover - configuration must exist
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data
    return {}


_FLAGS: dict[str, dict[str, Any]] = _load_flags(_CONFIG_PATH)


def is_feature_enabled(name: str, environment: str | None = None) -> bool:
    """Return ``True`` if the feature ``name`` is enabled.

    Parameters
    ----------
    name:
        Name of the feature flag.
    environment:
        Optional explicit environment name. If ``None`` the value of the
        ``NUSYQ_ENV`` environment variable is used. ``production`` is the
        default environment.

    """
    flag = _FLAGS.get(name, {})
    env_base = environment if environment is not None else os.getenv("NUSYQ_ENV") or "production"
    env = env_base.lower()
    return bool(flag.get(env, flag.get("default", False)))


def get_flag_default(name: str) -> bool:
    """Return the default value for ``name``."""
    return bool(_FLAGS.get(name, {}).get("default", False))


def list_flags() -> dict[str, dict[str, Any]]:
    """Return the raw flag configuration."""
    return _FLAGS.copy()


def get_feature_flag(name: str, default: bool = False) -> bool:
    """Get the current value of a feature flag.

    Alias for is_feature_enabled for backwards compatibility.

    Parameters
    ----------
    name:
        Name of the feature flag.
    default:
        Default value if flag is not found.

    Returns:
    -------
    bool
        True if the feature is enabled, False otherwise.
    """
    if name not in _FLAGS:
        return default
    return is_feature_enabled(name)


def set_feature_flag_value(name: str, enabled: bool, environment: str | None = None) -> bool:
    """Set a feature flag value and persist to config file.

    Parameters
    ----------
    name:
        Name of the feature flag.
    enabled:
        Whether to enable or disable the flag.
    environment:
        Optional environment name. If None, sets the default value.

    Returns:
    -------
    bool
        True if successful, False otherwise.
    """
    # Ensure flag exists
    if name not in _FLAGS:
        _FLAGS[name] = {"default": False}

    # Set the value
    env_key = environment.lower() if environment else "default"
    _FLAGS[name][env_key] = enabled

    # Persist to file
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(_FLAGS, f, indent=2)
        return True
    except Exception:
        return False

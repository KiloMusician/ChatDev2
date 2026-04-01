"""Configuration loader for NuSyQ-Hub.

Loads and validates settings from a YAML file. The loader ensures required
configuration keys are present and of the expected types.
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml

# Default path to repository configuration
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"

# Schema definition: section -> key -> expected type
REQUIRED_SCHEMA = {
    "context_server": {
        "host": str,
        "port": int,
    },
    "ollama": {
        "host": str,
    },
}


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load and validate configuration.

    Parameters
    ----------
    path: Path | None
        Optional path to the YAML configuration file. If omitted, the
        environment variable ``NUSYQ_CONFIG`` is checked first, falling back
        to ``config/settings.yaml`` relative to the repository root.

    Returns:
    -------
    Dict[str, Any]
        Parsed configuration dictionary.

    Raises:
    ------
    FileNotFoundError
        If the configuration file does not exist.
    ValueError
        If required sections or keys are missing, or if a value has an
        unexpected type.
    """
    config_path = Path(path or os.getenv("NUSYQ_CONFIG") or DEFAULT_CONFIG_PATH)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    for section, keys in REQUIRED_SCHEMA.items():
        if section not in data:
            raise ValueError(f"Missing required section '{section}' in {config_path}")
        for key, expected_type in keys.items():
            if key not in data[section]:
                raise ValueError(f"Missing required key '{section}.{key}' in {config_path}")
            if not isinstance(data[section][key], expected_type):
                raise ValueError(
                    f"Invalid type for '{section}.{key}': expected {expected_type.__name__}"
                )

    return data

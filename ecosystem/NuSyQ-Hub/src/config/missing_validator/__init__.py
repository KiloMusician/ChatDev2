"""Lightweight config schema validator.

Minimal, dependency-light validator used as a safe fallback for basic
configuration checks. Prefers ``jsonschema`` if available, otherwise performs
simple required-key and type checks.

API:
    validate_config(schema: dict, config: dict) -> (bool, list[str])
    validate_yaml_file(schema: dict, path: str|Path) -> (bool, list[str])
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

# jsonschema is optional; import at runtime in `validate_config` when available

logger = logging.getLogger(__name__)


def _simple_check(schema: Any, config: dict[str, Any]) -> tuple[bool, list[str]]:
    """Perform a minimal required-key and type check.

    Schema format (simple form):
      {"required": ["a", "b"], "types": {"a": str, "b": int}}
    """
    errors: list[str] = []

    if not isinstance(schema, dict):
        return False, ["Schema must be a dict for simple checks"]

    required = schema.get("required", [])
    types = schema.get("types", {})

    for key in required:
        if key not in config:
            errors.append(f"Missing required key: {key}")

    if isinstance(types, dict):
        for key, expected in types.items():
            if key in config and not isinstance(config[key], expected):
                expected_name = getattr(expected, "__name__", str(expected))
                errors.append(
                    f"Key {key} expected type {expected_name}, got {type(config[key]).__name__}"
                )

    return (len(errors) == 0, errors)


def validate_config(schema: dict[str, Any], config: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a configuration mapping against a schema.

    If jsonschema is available and the provided schema looks like a jsonschema
    dict, it will be used for full validation. Otherwise the simple validator
    is applied.
    """
    # Prefer jsonschema if available at runtime for full validation
    if isinstance(schema, dict):
        try:
            import jsonschema  # optional runtime dependency

            try:
                jsonschema.validate(instance=config, schema=schema)
                return True, []
            except Exception as exc:  # keep error message simple
                return False, [str(exc)]
        except ImportError:
            # jsonschema not installed; fall back to simple checks
            pass

    return _simple_check(schema, config)


def validate_yaml_file(schema: dict[str, Any], yaml_path: str | Path) -> tuple[bool, list[str]]:
    """Load YAML from `yaml_path` and validate it against `schema`.

    Returns (ok, errors). Requires PyYAML to be installed.
    """
    try:
        yaml_module = importlib.import_module("yaml")
        safe_load = getattr(yaml_module, "safe_load", None)
        if not callable(safe_load):
            return False, ["PyYAML safe_load not available"]
    except ImportError:
        return False, ["PyYAML not installed; cannot validate YAML files"]

    try:
        content = Path(yaml_path).read_text(encoding="utf-8")
        data = safe_load(content)
    except Exception as exc:
        return False, [f"Failed to load YAML: {exc}"]

    return validate_config(schema, data or {})


__all__ = ["validate_config", "validate_yaml_file"]

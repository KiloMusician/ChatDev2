"""Centralized input validation utilities for NuSyQ-Hub."""

from typing import Any


def is_nonempty_string(val: Any) -> bool:
    return isinstance(val, str) and bool(val.strip())


def is_positive_int(val: Any) -> bool:
    return isinstance(val, int) and val > 0


def is_dict_with_keys(val: Any, keys) -> bool:
    return isinstance(val, dict) and all(k in val for k in keys)

"""Runtime package exports with lazy loading to avoid import cycles."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["WorkflowMetaInfo", "WorkflowRunResult", "run_workflow"]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    sdk = import_module("runtime.sdk")
    return getattr(sdk, name)

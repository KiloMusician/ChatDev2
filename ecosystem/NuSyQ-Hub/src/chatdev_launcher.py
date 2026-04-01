"""Compatibility shim for ChatDev / chatdev launcher.

Attempts to forward to the real ChatDev launcher under the `NuSyQ` workspace
when available. Otherwise exposes a `launch` function that raises a clear
runtime error if invoked.
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = ["launch"]


def _load_real_launcher() -> Any | None:
    candidates = ["NuSyQ.chatdev_launcher", "NuSyQ.ChatDev.launcher"]
    for module_name in candidates:
        try:
            module = importlib.import_module(module_name)
            launcher = getattr(module, "launch", None)
            if callable(launcher):
                return launcher
        except Exception:
            continue
    return None


def launch(*args, **kwargs):
    launcher = _load_real_launcher()
    if launcher is None:
        raise RuntimeError(
            "NuSyQ ChatDev launcher is not importable; add the NuSyQ workspace to PYTHONPATH"
        )
    return launcher(*args, **kwargs)

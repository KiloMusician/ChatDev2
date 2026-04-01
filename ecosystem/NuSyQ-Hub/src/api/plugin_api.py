# DEPRECATED: This router is NOT wired into src/api/main.py (Phase 1 canonical entry point).
# It is an unwired legacy stub. Canonical API entry point: src/api/main.py
"""Plugin Registry API endpoints."""

from typing import Any

from fastapi import APIRouter, Query

try:
    from src.plugins.plugin_registry import PluginRegistry
except ImportError:
    PluginRegistry = None

router = APIRouter()

_registry = PluginRegistry() if PluginRegistry else None


@router.get("/plugins/list")
def list_plugins() -> dict[str, Any]:
    if not _registry:
        return {"error": "PluginRegistry not available"}
    return {"plugins": _registry.list_plugins()}


@router.post("/plugins/register")
def register_plugin(name: str = Query(...)) -> dict[str, Any]:
    if not _registry:
        return {"error": "PluginRegistry not available"}
    # For demo: register a dummy plugin
    _registry.register(name, object())
    return {"success": True, "plugin": name}

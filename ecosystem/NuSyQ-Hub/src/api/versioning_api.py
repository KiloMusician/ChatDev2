# DEPRECATED: This router is NOT wired into src/api/main.py (Phase 1 canonical entry point).
# It is an unwired scaffold stub. Canonical API entry point: src/api/main.py
"""API Versioning and Multi-Tenancy endpoints (scaffold)."""

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/version")
def get_version() -> dict[str, Any]:
    return {"version": "1.0.0", "multi_tenancy": True}


@router.get("/tenant/{tenant_id}")
def get_tenant_info(tenant_id: str) -> dict[str, Any]:
    # Placeholder for tenant-specific info
    return {"tenant_id": tenant_id, "status": "active"}

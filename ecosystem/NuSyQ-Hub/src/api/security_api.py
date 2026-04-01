"""Security API endpoints for secure API key management."""

from typing import Any

from fastapi import APIRouter, Query

try:
    from src.security.secure_api_manager import SecureAPIManager
except ImportError:
    SecureAPIManager = None

router = APIRouter()


@router.post("/security/store_key")
def store_key(provider: str = Query(...), api_key: str = Query(...)) -> dict[str, Any]:
    if not SecureAPIManager:
        return {"error": "SecureAPIManager not available"}
    mgr = SecureAPIManager()
    ok = mgr.store_api_key(provider, api_key)
    return {"success": ok}


@router.get("/security/get_key")
def get_key(provider: str = Query(...)) -> dict[str, Any]:
    if not SecureAPIManager:
        return {"error": "SecureAPIManager not available"}
    mgr = SecureAPIManager()
    key = mgr.get_api_key(provider)
    return {"api_key": key}


@router.get("/security/list_providers")
def list_providers() -> dict[str, Any]:
    if not SecureAPIManager:
        return {"error": "SecureAPIManager not available"}
    mgr = SecureAPIManager()
    return {"providers": mgr.list_stored_providers()}

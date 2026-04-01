#!/usr/bin/env python3
"""NuSyQ-Hub FastAPI Server - Reactive System State APIs.

This replaces static report generation with queryable HTTP endpoints.

Agents (Copilot, Claude, ChatDev, Ollama) can query:
- GET /api/status - System heartbeat and health
- GET /api/problems - Current problems without file generation
- GET /api/health - Unified health check
- GET /api/snapshots - Historical snapshots (on-demand)

Run with:
    python -m src.api.main
    # Or with uvicorn
    uvicorn src.api.main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import importlib
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    if TYPE_CHECKING:
        from fastapi import FastAPI, HTTPException, Query
        from fastapi.responses import JSONResponse
    else:
        FastAPI = None
        Query = None
        HTTPException = None
        JSONResponse = None

try:
    from src.system.status import STATUS_FILE, get_system_status
    from src.system.status import heartbeat as update_heartbeat
    from src.system.status import is_system_on, set_system_status
except ImportError:
    # Fallback implementations
    def get_system_status() -> dict[str, Any]:
        return {"status": "unknown", "error": "Status module not available"}

    def is_system_on() -> bool:
        return False

    def set_system_status(*_args: Any, **_kwargs: Any) -> None:
        # Fallback stub: intentionally empty, used when src.system.status is unavailable
        pass

    def update_heartbeat(run_id: str | None = None, details: dict[str, Any] | None = None) -> None:
        # Fallback stub: intentionally empty, used when src.system.status is unavailable
        pass

    STATUS_FILE = Path("state") / "system_status.json"


try:
    _problems_module = importlib.import_module("src.api.problems_api")
    get_problems_api = getattr(_problems_module, "get_problems_api", None)
except ImportError:
    get_problems_api = None


import logging

from src.api import systems

logger = logging.getLogger(__name__)

app: FastAPI | None
HEARTBEAT_INTERVAL_SECONDS = 30


def _status_health(status: dict[str, Any] | Any) -> str:
    if not isinstance(status, dict):
        return "unknown"
    details = status.get("details", {})
    if isinstance(details, dict):
        return details.get("health", status.get("health", "unknown"))
    return status.get("health", "unknown")


async def _heartbeat_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        current = get_system_status()
        details = dict(current.get("details", {})) if isinstance(current, dict) else {}
        details.setdefault("health", "healthy")
        details["service"] = "reactive-api"
        details["last_heartbeat"] = datetime.now().isoformat()
        if "started_at" not in details:
            details["started_at"] = datetime.now().isoformat()

        update_heartbeat(
            run_id=(current.get("run_id") if isinstance(current, dict) else None) or "reactive-api",
            details=details,
        )

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=HEARTBEAT_INTERVAL_SECONDS)
        except TimeoutError:
            continue


if not FASTAPI_AVAILABLE:
    logger.warning("⚠️  FastAPI not installed. Install with: pip install fastapi uvicorn")
    logger.info("    Or run: pip install -r requirements.txt")
    app = None
else:
    app = FastAPI(
        title="NuSyQ-Hub Reactive API",
        description="Real-time system state without file bloat",
        version="1.0.0",
    )

    # CORS — required for WebSocket upgrade from external clients (Dev-Mentor, SimVerse)
    # Starlette's CORSMiddleware intercepts WebSocket upgrade if origin is not allowed.
    # allow_origins=["*"] is safe for a local-only development API.
    try:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    except ImportError:
        pass

    # Mount systems API
    app.include_router(systems.router, prefix="/api")
    # Mount RAG API
    try:
        from src.api import rag_api

        app.include_router(rag_api.router, prefix="/api")
    except Exception as e:
        logger.warning(f"RAG API not available: {e}")
    # Mount Observability API
    try:
        from src.api import observability_api

        app.include_router(observability_api.router, prefix="/api")
    except Exception as e:
        logger.warning(f"Observability API not available: {e}")
    # Mount Security API
    try:
        from src.api import security_api

        app.include_router(security_api.router, prefix="/api")
    except Exception as e:
        logger.warning(f"Security API not available: {e}")
    # Mount Test API
    try:
        from src.api import test_api

        app.include_router(test_api.router, prefix="/api")
    except Exception as e:
        logger.warning(f"Test API not available: {e}")
    # Mount GitNexus API
    try:
        from src.orchestration.gitnexus import router as gitnexus_router

        if gitnexus_router is not None:
            app.include_router(gitnexus_router)
    except Exception as e:
        logger.warning(f"GitNexus API not available: {e}")
    # Mount Agents API (Phase 1: AgentCommunicationHub + AgentOrchestrationHub over HTTP)
    try:
        from fastapi import WebSocket as _WS

        from src.api import agents_api

        app.include_router(agents_api.router, prefix="/api")

        # Register WebSocket directly on app (APIRouter WebSocket + prefix has known
        # Starlette routing quirks that produce 403 on upgrade handshake)
        @app.websocket("/api/agents/ws")
        async def _agents_ws_direct(websocket: _WS) -> None:
            await agents_api.agent_ws(websocket)

    except Exception as e:
        logger.warning(f"Agents API not available: {e}")

    @app.on_event("startup")
    async def startup_status() -> None:
        # Mark the reactive API as the current live system authority.
        set_system_status(
            "on",
            run_id="reactive-api",
            details={
                "health": "healthy",
                "service": "reactive-api",
                "started_at": datetime.now().isoformat(),
                "last_heartbeat": datetime.now().isoformat(),
            },
        )
        app.state.heartbeat_stop = asyncio.Event()
        app.state.heartbeat_task = asyncio.create_task(_heartbeat_loop(app.state.heartbeat_stop))

    @app.on_event("shutdown")
    async def shutdown_status() -> None:
        task = getattr(app.state, "heartbeat_task", None)
        stop_event = getattr(app.state, "heartbeat_stop", None)
        if stop_event is not None:
            stop_event.set()
        if task is not None:
            try:
                await asyncio.wait_for(task, timeout=2)
            except Exception:
                task.cancel()

        current = get_system_status()
        details = dict(current.get("details", {}))
        details["health"] = "unknown"
        details["service"] = "reactive-api"
        details["stopped_at"] = datetime.now().isoformat()
        set_system_status("off", run_id=current.get("run_id"), details=details)

    @app.get("/")
    async def root() -> dict[str, Any]:
        # Root endpoint with API overview.
        return {
            "service": "NuSyQ-Hub Reactive API",
            "version": "1.0.0",
            "status": "operational" if is_system_on() else "offline",
            "endpoints": {
                "status": "/api/status",
                "problems": "/api/problems",
                "health": "/api/health",
                "docs": "/docs",
                "openapi": "/openapi.json",
            },
            "documentation": "Visit /docs for interactive API documentation",
        }

    @app.get("/api/status")
    async def get_status() -> dict[str, Any]:
        # Get current system status (heartbeat).
        # Replaces: Reading state/system_status.json directly
        # Benefits: HTTP-queryable, includes agent_check helpers
        if not is_system_on():
            raise HTTPException(
                status_code=503,
                detail="System is offline. Start with: python scripts/start_nusyq.py",
            )

        status = get_system_status()
        if not isinstance(status, dict):
            return {"status": "unknown", "error": "Invalid status payload"}
        health = _status_health(status)

        # Add convenience fields for agents
        status["agent_check"] = {
            "is_on": status.get("status") == "on",
            "is_healthy": health == "healthy",
            "heartbeat_stale": _is_heartbeat_stale(status),
            "safe_to_proceed": (
                status.get("status") == "on"
                and health in ("healthy", "degraded")
                and not _is_heartbeat_stale(status)
            ),
        }

        return status

    @app.get("/api/problems")
    async def get_problems(
        repo: str | None = Query(
            None, description="Filter by repo: nusyq-hub, nusyq, simulated-verse"
        ),
        source: Literal["vscode", "ruff", "mypy", "all"] = Query(
            "all", description="Problem source"
        ),
        include_details: bool = Query(False, description="Include detailed breakdown"),
    ) -> dict[str, Any]:
        # Get current problems across repos without generating files.
        # Replaces: src/diagnostics/problem_signal_snapshot.py
        # Benefits: Real-time, no file bloat, queryable, filterable
        if not is_system_on():
            raise HTTPException(status_code=503, detail="System is offline")

        if not callable(get_problems_api):
            raise HTTPException(status_code=501, detail="Problems API not available")

        problems_api = get_problems_api()
        if problems_api is None:
            raise HTTPException(status_code=501, detail="Problems API not initialized")
        raw_problems = problems_api.get_current_problems(
            repo=repo, source=source, include_details=include_details
        )
        if isinstance(raw_problems, dict):
            return dict(raw_problems)
        return {"error": "Invalid problems payload"}

    @app.post("/api/problems/snapshot")
    async def create_problem_snapshot(
        format_: Literal["json", "markdown"] = Query("markdown", description="Snapshot format"),
    ) -> dict[str, Any]:
        # Explicitly create an archival problem snapshot.
        # Note: This generates a file, but ONLY when explicitly requested.
        # Not automatic like the old system.
        if not callable(get_problems_api):
            raise HTTPException(status_code=501, detail="Problems API not available")

        problems_api = get_problems_api()
        if problems_api is None:
            raise HTTPException(status_code=501, detail="Problems API not initialized")
        snapshot_path = problems_api.generate_snapshot_file(format_=format_)

        return {
            "message": "Snapshot created",
            "path": str(snapshot_path),
            "format": format_,
            "timestamp": datetime.now().isoformat(),
        }

    @app.get("/api/health")
    async def health_check() -> dict[str, Any]:
        # Unified health check endpoint.
        # Consolidates:
        # - system_health_assessor.py
        # - ai_health_probe.py
        # - integrated_health_orchestrator.py
        status = get_system_status()
        details = status.get("details", {}) if isinstance(status, dict) else {}
        overall_status = details.get("health", "unknown")

        health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "system": {
                "status": status.get("status", "unknown"),
                "uptime_seconds": details.get("uptime", 0),
                "last_heartbeat": details.get("last_heartbeat"),
            },
            "components": {
                "api_server": "healthy",
                "status_file": "healthy" if _status_file_exists() else "missing",
            },
        }

        # Check for problems
        if callable(get_problems_api):
            try:
                problems_api = get_problems_api()
                if problems_api is not None:
                    problems = problems_api.get_current_problems()
                    health["problems"] = {
                        "total": problems["total_counts"]["total"],
                        "errors": problems["total_counts"]["errors"],
                        "warnings": problems["total_counts"]["warnings"],
                        "health_assessment": problems["health_assessment"],
                    }
            except Exception:
                health["problems"] = {"error": "Could not fetch problems"}

        try:
            from src.system.agent_awareness import emit as _emit

            _overall = health.get("overall_status", "unknown")
            _lvl = "WARNING" if _overall not in ("healthy", "unknown") else "INFO"
            _emit(
                "system",
                f"API health: status={_overall} api=healthy",
                level=_lvl,
                source="api_main",
            )
        except Exception:
            pass

        return health

    @app.get("/api/heartbeat")
    async def heartbeat() -> dict[str, Any]:
        # Simple heartbeat endpoint - proves system is alive.
        # Unlike /api/status, this is lightweight and never fails.
        current = get_system_status()
        details = dict(current.get("details", {}))
        details.setdefault("health", "healthy")
        details["last_heartbeat"] = datetime.now().isoformat()
        details["service"] = "reactive-api"
        update_heartbeat(run_id=current.get("run_id"), details=details)

        return {"alive": True, "timestamp": datetime.now().isoformat(), "service": "nusyq-hub"}

    @app.post("/api/status/set")
    async def set_status(
        status: Literal["on", "off", "starting", "stopping", "error"],
        health: Literal["healthy", "degraded", "critical", "unknown"] = "healthy",
        message: str | None = None,
    ) -> dict[str, Any]:
        # Manually set system status (admin only).
        # Use for testing or manual interventions.
        set_system_status(
            status,
            run_id="manual-api",
            details={
                "health": health,
                "message": message,
                "last_heartbeat": datetime.now().isoformat(),
                "service": "reactive-api",
            },
        )

        return {
            "message": "Status updated",
            "status": status,
            "health": health,
            "timestamp": datetime.now().isoformat(),
        }

    def _is_heartbeat_stale(status: dict[str, Any], threshold_seconds: int = 60) -> bool:
        # Check if heartbeat is stale (system might be frozen).
        last_heartbeat = status.get("details", {}).get("last_heartbeat")
        if not last_heartbeat:
            return True

        try:
            heartbeat_time = datetime.fromisoformat(last_heartbeat)
            age = (datetime.now() - heartbeat_time).total_seconds()
            return age > threshold_seconds
        except Exception:
            return True

    def _status_file_exists() -> bool:
        # Check if system status file exists.
        return STATUS_FILE.exists()

    # Phase 2 brownfield audit status
    @app.get("/api/phase2/status")
    async def phase2_status() -> dict[str, Any]:
        """Phase 2 brownfield consolidation audit status.

        Returns the canonical orchestrators, deprecated stubs identified during
        the Phase 2 audit, and a count of remaining TBN compliance issues.
        """
        return {
            "phase": 2,
            "audit_date": "2026-03-25",
            "canonical_orchestrators": [
                "src/api/agents_api.py",
                "src/agents/agent_orchestration_hub.py",
                "src/integration/consciousness_bridge.py",
            ],
            "deprecated_stubs": [
                # ConsciousnessBridge duplicates
                "src/agents/bridges/consciousness_bridge_bridge.py",
                "src/system/dictionary/consciousness_bridge.py",
                "src/orchestration/bridges/consciousness_bridge_integration.py",
                "src/orchestration/bridges/orchestration_bridges.py (ConsciousnessBridge class only)",
                # Duplicate orchestrator
                "src/orchestration/agent_orchestration_hub.py",
                # Unwired API routers (not included in main.py)
                "src/api/routes.py",
                "src/api/hacking_api.py",
                "src/api/plugin_api.py",
                "src/api/versioning_api.py",
                "src/api/publishing_api.py",
                "src/api/generators_api.py",
            ],
            "tbn_issues": 0,
            "notes": (
                "Phase 2 complete: deprecation markers added to all stubs. "
                "No files deleted — all kept for backward-compat imports. "
                "Phase 3 target: remove ConsciousnessBridge inline copy from "
                "orchestration_bridges.py and merge advanced methods from "
                "src/orchestration/agent_orchestration_hub.py into canonical."
            ),
        }

    # Health check for load balancers
    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        # Kubernetes-style health endpoint.
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> Any:  # JSONResponse when available
        # Kubernetes-style readiness endpoint.
        if not is_system_on():
            return JSONResponse(
                status_code=503, content={"status": "not_ready", "reason": "System offline"}
            )
        status = get_system_status()
        if _status_health(status) == "unknown":
            return JSONResponse(
                status_code=503, content={"status": "not_ready", "reason": "Unknown health"}
            )
        return JSONResponse(status_code=200, content={"status": "ready"})


if __name__ == "__main__":
    if not FASTAPI_AVAILABLE or app is None:
        logger.error("❌ FastAPI not available. Install with: pip install fastapi uvicorn")
        exit(1)

    import uvicorn

    logger.info("🚀 Starting NuSyQ-Hub Reactive API Server...")
    logger.info("📍 API will be available at: http://localhost:8000")
    logger.info("📚 Docs available at: http://localhost:8000/docs")
    logger.info("")
    logger.info("🔍 Key Endpoints:")
    logger.info("   GET  /api/status      - System heartbeat")
    logger.info("   GET  /api/problems    - Current problems (no files!)")
    logger.info("   GET  /api/health      - Health check")
    logger.info("   POST /api/problems/snapshot - Create archival snapshot")
    logger.info("")

    uvicorn.run(app, host="0.0.0.0", port=8000)

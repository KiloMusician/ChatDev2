from fastapi import APIRouter

from utils.structured_logger import get_server_logger, LogType

router = APIRouter()


@router.get("/health")
async def health_check():
    logger = get_server_logger()
    logger.info("Health check requested", log_type=LogType.REQUEST)
    return {"status": "healthy"}


@router.get("/health/live")
async def liveness_check():
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check():
    return {"status": "ready"}


@router.get("/api/health")
async def api_health_check():
    """Alias for /health — satisfies Dev-Mentor autoboot probe."""
    return {"status": "healthy", "service": "chatdev-2.0"}


@router.get("/api/game/state")
async def api_game_state():
    """Stub — Dev-Mentor autoboot probes this route."""
    return {"state": "stub", "service": "chatdev-2.0"}


@router.get("/api/state")
async def api_state():
    """Stub — Dev-Mentor autoboot probes this route."""
    return {"state": "running", "service": "chatdev-2.0"}

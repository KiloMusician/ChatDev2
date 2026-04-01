#!/usr/bin/env python3
"""NuSyQ Bridge: Connects Dev-Mentor ↔ NuSyQ Hub ↔ ChatDev
Bi-directional API orchestration and state synchronization
"""

import asyncio
import hashlib
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

import aiohttp
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ============================================================================
# CONFIGURATION
# ============================================================================

NUSYQ_HUB_URL = os.getenv("NUSYQ_HUB_URL", "http://localhost:8000")
DEV_MENTOR_URL = os.getenv("DEV_MENTOR_URL", "http://dev-mentor:7337")
CHATDEV_URL = os.getenv("CHATDEV_URL", "http://chatdev-orchestrator:7338")
REDIS_URL = os.getenv("REDIS_URL", "redis://nusyq-redis:6379/0")
MCP_URL = os.getenv("MCP_URL", os.getenv("MCP_SERVER_URL", "http://mcp-server:8765"))
ENDPOINT_TIMEOUT_S = float(os.getenv("NUSYQ_BRIDGE_ENDPOINT_TIMEOUT_S", "8"))

SCRIPT_PATH = Path(__file__).resolve()
BASE_DIR = (
    SCRIPT_PATH.parent.parent
    if SCRIPT_PATH.parent.name == "scripts"
    else SCRIPT_PATH.parent
)
STATE_DIR = BASE_DIR / "state"
TASKS_DIR = BASE_DIR / "tasks"
FILE_TASKS_DIR = TASKS_DIR / "legacy_runtime"
STATE_DIR.mkdir(exist_ok=True)
TASKS_DIR.mkdir(exist_ok=True)
FILE_TASKS_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_STATE_FILE = STATE_DIR / "bridge_runtime_state.json"
BRIDGE_RESTORED_STATE_FILE = STATE_DIR / "bridge_restored_state.json"
BRIDGE_STATE_DIFF_FILE = STATE_DIR / "bridge_state_diff.json"
BRIDGE_REBUILD_QUEUE_FILE = STATE_DIR / "bridge_rebuild_queue.jsonl"
BRIDGE_RUNTIME_QUEUE_KEY = "runtime:bridge:rebuild_queue"
VOLATILE_STATE_KEYS = {
    "timestamp",
    "ts",
    "updated_at",
    "created_at",
    "last_updated",
    "last_seen",
    "last_heartbeat",
    "started_at",
    "uptime",
    "uptime_s",
    "captured_at",
}
HOST_FALLBACKS: dict[str, tuple[str, ...]] = {
    "nusyq-hub": ("nusyq-hub-dev",),
}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
if "NUSYQ_HUB_URL" not in os.environ:
    logger.warning("NUSYQ_HUB_URL not set; defaulting to %s", NUSYQ_HUB_URL)

# ============================================================================
# FASTAPI APP
# ============================================================================


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global redis_client
    try:
        redis_client = await redis.from_url(REDIS_URL)
        await redis_client.ping()
        logger.info("✓ Redis connected")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
    await _restore_bridge_runtime()
    yield
    await _persist_pre_restart_state()
    if redis_client:
        await redis_client.close()


app = FastAPI(title="NuSyQ Bridge", version="1.0.0", lifespan=_lifespan)

# Redis client
redis_client: redis.Redis | None = None

# ============================================================================
# MODELS
# ============================================================================


class TaskRequest(BaseModel):
    description: str
    task_type: str
    priority: int = 1
    agent_type: str = "auto"
    context: dict[str, Any] | None = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


class HealthStatus(BaseModel):
    status: str
    connections: dict[str, bool]
    timestamp: str
    ready: bool
    restoration_complete: bool
    state_hash: str | None = None
    previous_state_hash: str | None = None
    unexpected_state_change: bool = False
    rebuild_task_id: str | None = None


bridge_runtime: dict[str, Any] = {
    "restoration_started_at": None,
    "restoration_completed_at": None,
    "restoration_complete": False,
    "state_hash": None,
    "previous_state_hash": None,
    "unexpected_state_change": False,
    "rebuild_task_id": None,
    "restored_states": {},
}

# ============================================================================
# INITIALIZATION
# ============================================================================


def _now() -> str:
    return datetime.utcnow().isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _normalize_state(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, inner in value.items():
            if key in VOLATILE_STATE_KEYS:
                continue
            normalized[key] = _normalize_state(inner)
        return normalized
    if isinstance(value, list):
        return [_normalize_state(item) for item in value]
    return value


def _hash_payload(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _candidate_base_urls(base_url: str) -> list[str]:
    normalized = base_url.rstrip("/")
    candidates = [normalized]
    parsed = urlsplit(normalized)
    if not parsed.hostname:
        return candidates

    for fallback_host in HOST_FALLBACKS.get(parsed.hostname, ()):
        netloc = fallback_host
        if parsed.port:
            netloc = f"{fallback_host}:{parsed.port}"
        fallback_url = urlunsplit(
            (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
        ).rstrip("/")
        if fallback_url not in candidates:
            candidates.append(fallback_url)
    return candidates


def _flatten_state(value: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, inner in value.items():
            path = f"{prefix}.{key}" if prefix else key
            flat.update(_flatten_state(inner, path))
        return flat
    if isinstance(value, list):
        for index, inner in enumerate(value):
            path = f"{prefix}[{index}]"
            flat.update(_flatten_state(inner, path))
        return flat
    flat[prefix or "$"] = value
    return flat


def _diff_hash_inputs(
    previous: dict[str, Any], current: dict[str, Any]
) -> list[dict[str, Any]]:
    old_flat = _flatten_state(previous)
    new_flat = _flatten_state(current)
    changes: list[dict[str, Any]] = []
    for key in sorted(set(old_flat) | set(new_flat)):
        if key not in old_flat:
            changes.append({"path": key, "change": "added", "current": new_flat[key]})
        elif key not in new_flat:
            changes.append(
                {"path": key, "change": "removed", "previous": old_flat[key]}
            )
        elif old_flat[key] != new_flat[key]:
            changes.append(
                {
                    "path": key,
                    "change": "changed",
                    "previous": old_flat[key],
                    "current": new_flat[key],
                }
            )
    return changes


async def _fetch_json(session: aiohttp.ClientSession, url: str) -> Any | None:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if 200 <= response.status < 300:
                return await response.json()
    except Exception:
        return None
    return None


async def _fetch_json_candidates(
    session: aiohttp.ClientSession, base_url: str, path: str
) -> Any | None:
    for candidate in _candidate_base_urls(base_url):
        payload = await _fetch_json(session, f"{candidate}{path}")
        if payload is not None:
            return payload
    return None


async def _collect_restored_states() -> dict[str, Any]:
    states: dict[str, Any] = {}
    async with aiohttp.ClientSession() as session:
        dev_state = await _fetch_json_candidates(session, DEV_MENTOR_URL, "/api/state")
        if dev_state is not None:
            states["dev-mentor"] = dev_state

        nusyq_state = await _fetch_json_candidates(session, NUSYQ_HUB_URL, "/api/state")
        if nusyq_state is not None:
            states["nusyq-hub"] = nusyq_state
    return states


def _build_state_snapshot(restored_states: dict[str, Any]) -> dict[str, Any]:
    hash_inputs = {
        "config": {
            "NUSYQ_HUB_URL": NUSYQ_HUB_URL,
            "DEV_MENTOR_URL": DEV_MENTOR_URL,
            "CHATDEV_URL": CHATDEV_URL,
            "MCP_URL": MCP_URL,
            "REDIS_URL": REDIS_URL,
        },
        "restored_services": sorted(restored_states.keys()),
        "restored_state": _normalize_state(restored_states),
    }
    return {
        "captured_at": _now(),
        "hash_inputs": hash_inputs,
        "state_hash": _hash_payload(hash_inputs),
    }


async def _queue_rebuild_task(diff_payload: dict[str, Any]) -> str | None:
    task_id = f"bridge_rebuild_{int(datetime.utcnow().timestamp() * 1000)}"
    created_at = _now()
    task = {
        "id": task_id,
        "title": "Rebuild nusyq-bridge after unexpected state drift",
        "type": "fix",
        "details": (
            "NuSyQ bridge startup state drift detected after restart. "
            f"Compare hashes {diff_payload['previous_state_hash']} -> {diff_payload['current_state_hash']} "
            f"and inspect {BRIDGE_STATE_DIFF_FILE.name}."
        ),
        "target": "nusyq-bridge",
        "priority": 1,
        "status": "pending",
        "created_at": created_at,
        "updated_at": created_at,
        "result": "",
        "metadata": {
            "source": "nusyq_bridge",
            "state_diff_file": str(BRIDGE_STATE_DIFF_FILE.relative_to(BASE_DIR)),
            "previous_state_hash": diff_payload["previous_state_hash"],
            "current_state_hash": diff_payload["current_state_hash"],
        },
    }

    task_path = FILE_TASKS_DIR / f"{task_id}.json"
    task_path.write_text(json.dumps(task, indent=2), encoding="utf-8")
    with BRIDGE_REBUILD_QUEUE_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(task) + "\n")

    if redis_client:
        try:
            await redis_client.rpush(BRIDGE_RUNTIME_QUEUE_KEY, json.dumps(task))
            await redis_client.set(f"task:{task_id}", json.dumps(task), ex=86400)
            await redis_client.publish(
                "lattice.task.created",
                json.dumps(
                    {
                        **task,
                        "_ts": created_at,
                        "source": "nusyq_bridge",
                    }
                ),
            )
        except Exception as exc:
            logger.warning(f"Failed to publish rebuild task to Redis: {exc}")

    logger.warning(f"Queued bridge rebuild task: {task_id}")
    return task_id


async def _restore_bridge_runtime() -> None:
    bridge_runtime["restoration_started_at"] = _now()
    bridge_runtime["restoration_complete"] = False
    bridge_runtime["unexpected_state_change"] = False
    bridge_runtime["rebuild_task_id"] = None

    previous_snapshot = _read_json(BRIDGE_STATE_FILE)
    bridge_runtime["previous_state_hash"] = (
        previous_snapshot.get("state_hash") if previous_snapshot else None
    )

    restored_states = await _collect_restored_states()
    snapshot = _build_state_snapshot(restored_states)
    _write_json(
        BRIDGE_RESTORED_STATE_FILE,
        {
            **snapshot,
            "restored_states": restored_states,
        },
    )

    if redis_client:
        try:
            await redis_client.set("system:state", json.dumps(restored_states), ex=3600)
        except Exception as exc:
            logger.warning(f"Failed to restore system:state to Redis: {exc}")

    bridge_runtime["restored_states"] = restored_states
    bridge_runtime["state_hash"] = snapshot["state_hash"]

    if (
        previous_snapshot
        and previous_snapshot.get("state_hash") != snapshot["state_hash"]
    ):
        diff_payload = {
            "detected_at": _now(),
            "previous_state_hash": previous_snapshot.get("state_hash"),
            "current_state_hash": snapshot["state_hash"],
            "changes": _diff_hash_inputs(
                previous_snapshot.get("hash_inputs", {}),
                snapshot.get("hash_inputs", {}),
            ),
            "previous_snapshot": previous_snapshot,
            "current_snapshot": snapshot,
        }
        _write_json(BRIDGE_STATE_DIFF_FILE, diff_payload)
        bridge_runtime["unexpected_state_change"] = True
        bridge_runtime["rebuild_task_id"] = await _queue_rebuild_task(diff_payload)
    elif BRIDGE_STATE_DIFF_FILE.exists():
        BRIDGE_STATE_DIFF_FILE.unlink()

    bridge_runtime["restoration_completed_at"] = _now()
    bridge_runtime["restoration_complete"] = True


async def _persist_pre_restart_state() -> None:
    restored_states = bridge_runtime.get("restored_states", {})
    snapshot = _build_state_snapshot(restored_states)
    snapshot["persisted_for_restart_at"] = _now()
    _write_json(BRIDGE_STATE_FILE, snapshot)


async def _check_endpoint(session: aiohttp.ClientSession, url: str) -> bool:
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=ENDPOINT_TIMEOUT_S)
        ) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


async def _check_endpoint_candidates(
    session: aiohttp.ClientSession, base_url: str, path: str
) -> bool:
    for candidate in _candidate_base_urls(base_url):
        if await _check_endpoint(session, f"{candidate}{path}"):
            return True
    return False


async def _request_json_candidates(
    session: aiohttp.ClientSession,
    method: str,
    base_url: str,
    path: str,
    **kwargs: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    last_error: str | None = None
    for candidate in _candidate_base_urls(base_url):
        try:
            async with session.request(
                method, f"{candidate}{path}", **kwargs
            ) as response:
                if response.status == 200:
                    return await response.json(), None
                last_error = f"{response.status} from {candidate}"
        except Exception as exc:
            last_error = f"{candidate}: {exc}"
    return None, last_error


async def _redis_ready() -> bool:
    if redis_client is None:
        return False
    try:
        return bool(await redis_client.ping())
    except Exception:
        return False


async def _build_health_status() -> HealthStatus:
    connections: dict[str, bool] = {}

    async with aiohttp.ClientSession() as session:
        connections["nusyq-hub"] = await _check_endpoint_candidates(
            session, NUSYQ_HUB_URL, "/api/health"
        )
        connections["dev-mentor"] = await _check_endpoint_candidates(
            session, DEV_MENTOR_URL, "/api/health"
        )
        connections["chatdev"] = await _check_endpoint_candidates(
            session, CHATDEV_URL, "/health"
        )
        connections["mcp-server"] = await _check_endpoint_candidates(
            session, MCP_URL, "/health"
        )

    connections["redis"] = await _redis_ready()
    status = "healthy" if all(connections.values()) else "degraded"
    ready = bool(
        bridge_runtime["restoration_complete"]
        and not bridge_runtime["unexpected_state_change"]
        and connections["redis"]
    )

    if not connections["nusyq-hub"]:
        logger.warning(
            "NuSyQ Hub unreachable at %s; bridge remains ready in degraded mode",
            NUSYQ_HUB_URL,
        )
    return HealthStatus(
        status=status,
        connections=connections,
        timestamp=_now(),
        ready=ready,
        restoration_complete=bool(bridge_runtime["restoration_complete"]),
        state_hash=bridge_runtime["state_hash"],
        previous_state_hash=bridge_runtime["previous_state_hash"],
        unexpected_state_change=bool(bridge_runtime["unexpected_state_change"]),
        rebuild_task_id=bridge_runtime["rebuild_task_id"],
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Readiness check for all required downstream services."""
    payload = await _build_health_status()
    if payload.status != "healthy":
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload


@app.get("/livez")
async def livez():
    return {
        "status": "alive",
        "timestamp": _now(),
        "restoration_complete": bridge_runtime["restoration_complete"],
        "state_hash": bridge_runtime["state_hash"],
    }


@app.get("/readyz", response_model=HealthStatus)
async def readyz():
    payload = await _build_health_status()
    if not payload.ready:
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload


# ============================================================================
# TASK ROUTING
# ============================================================================


@app.post("/api/v1/task", response_model=TaskResponse)
async def submit_task(task: TaskRequest) -> TaskResponse:
    """Submit task to appropriate orchestrator
    - CODE_GENERATION → ChatDev
    - DATA_ANALYSIS → Jupyter/Dev-Mentor
    - WORKFLOW → n8n
    - GENERAL → NuSyQ Hub
    """
    try:
        task_id = f"task_{int(datetime.utcnow().timestamp() * 1000)}"

        # Store task in Redis
        task_data = {
            "id": task_id,
            "description": task.description,
            "type": task.task_type,
            "status": "submitted",
            "created_at": datetime.utcnow().isoformat(),
            "context": task.context or {},
        }

        if redis_client:
            await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=86400)

        logger.info(f"✓ Task submitted: {task_id} ({task.task_type})")

        # Route to appropriate service
        result = await route_task(task, task_id)

        return TaskResponse(task_id=task_id, status="accepted", result=result)

    except Exception as e:
        logger.error(f"✗ Task submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str) -> TaskResponse:
    """Get task status and results"""
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis unavailable")

        task_data = await redis_client.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")

        task = json.loads(task_data)
        return TaskResponse(**task)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TASK ROUTING LOGIC
# ============================================================================


async def route_task(task: TaskRequest, task_id: str) -> dict[str, Any]:
    """Route task to appropriate service based on type"""
    async with aiohttp.ClientSession() as session:

        if task.task_type == "CODE_GENERATION":
            # Route to ChatDev
            logger.info(f"  → Routing to ChatDev: {task_id}")
            try:
                async with session.post(
                    f"{CHATDEV_URL}/api/v1/tasks",
                    json={
                        "description": task.description,
                        "agents": 5,
                        "model": "qwen2.5-coder:14b",
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as r:
                    if r.status == 200:
                        return await r.json()
                    else:
                        logger.error(f"ChatDev returned {r.status}")
                        return {
                            "status": "error",
                            "message": f"ChatDev error: {r.status}",
                        }
            except Exception as e:
                logger.error(f"ChatDev routing failed: {e}")
                return {"status": "error", "message": str(e)}

        elif task.task_type == "DATA_ANALYSIS":
            # Route to Dev-Mentor
            logger.info(f"  → Routing to Dev-Mentor: {task_id}")
            try:
                async with session.post(
                    f"{DEV_MENTOR_URL}/api/analyze",
                    json={"task": task.description, "context": task.context},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as r:
                    if r.status == 200:
                        return await r.json()
                    else:
                        return {
                            "status": "error",
                            "message": f"Dev-Mentor error: {r.status}",
                        }
            except Exception as e:
                logger.error(f"Dev-Mentor routing failed: {e}")
                return {"status": "error", "message": str(e)}

        elif task.task_type == "WORKFLOW":
            # Route to n8n
            logger.info(f"  → Routing to n8n: {task_id}")
            return {"status": "pending", "message": "Workflow execution pending"}

        else:
            # Default: Route to NuSyQ Hub
            logger.info(f"  → Routing to NuSyQ Hub: {task_id}")
            try:
                payload, error = await _request_json_candidates(
                    session,
                    "POST",
                    NUSYQ_HUB_URL,
                    "/api/orchestrate",
                    json={"description": task.description, "context": task.context},
                    timeout=aiohttp.ClientTimeout(total=30),
                )
                if payload is not None:
                    return payload
                return {
                    "status": "error",
                    "message": f"NuSyQ Hub error: {error or 'unreachable'}",
                }
            except Exception as e:
                logger.error(f"NuSyQ Hub routing failed: {e}")
                return {"status": "error", "message": str(e)}


# ============================================================================
# STATE SYNCHRONIZATION
# ============================================================================


@app.post("/api/v1/sync")
async def sync_state():
    """Synchronize state between Dev-Mentor ↔ NuSyQ Hub ↔ ChatDev"""
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis unavailable")

        async with aiohttp.ClientSession() as session:
            # Fetch state from each service
            states = {}

            # Dev-Mentor state
            try:
                payload = await _fetch_json_candidates(
                    session, DEV_MENTOR_URL, "/api/state"
                )
                if payload is not None:
                    states["dev-mentor"] = payload
            except:
                logger.warning("Failed to fetch Dev-Mentor state")

            # NuSyQ Hub state
            try:
                payload = await _fetch_json_candidates(
                    session, NUSYQ_HUB_URL, "/api/state"
                )
                if payload is not None:
                    states["nusyq-hub"] = payload
            except:
                logger.warning("Failed to fetch NuSyQ Hub state")

            # Store merged state
            await redis_client.set("system:state", json.dumps(states), ex=3600)

            logger.info(f"✓ State synchronized: {list(states.keys())}")
            return {"status": "synced", "services": list(states.keys())}

    except Exception as e:
        logger.error(f"State sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9876, log_level="info")

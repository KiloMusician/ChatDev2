"""
DevMentor Replit Stack - Backend API v2
Enhanced with:
- Terminal Depths game engine (server-side, session-based)
- Rich structured logging (request middleware, game events, metrics)
- Dual-interface: web thin-client + CLI client
"""
from __future__ import annotations

import asyncio
import collections
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rich.console import Console
from rich.text import Text
from starlette.middleware.sessions import SessionMiddleware

from .arg_layer import (
    get_active_events,
    get_watcher_data,
    get_world_modifiers,
    inject_lore_into_html,
    log_to_devlog,
)
from .paths import CORE_DIR, FRONTEND_DIR
from .runner import run_allowlisted, stream_allowlisted
from .security import (
    SecurityHeadersMiddleware,
    check_suspicious,
    get_allowed_origins,
    sanitize_error,
    validate_command_input,
)
from .security import (
    audit as _sec_audit,
)
from .state_store import ensure_state, load_state, save_state
from .tutorials import list_tutorials, read_tutorial

# ── Signal Harvester (gameplay → CHUG cultivation loop) ───────────────
try:
    from ..game_engine.signal_harvester import harvest as _sh_harvest

    _HARVESTER_ENABLED = True
except Exception:
    _HARVESTER_ENABLED = False
    _sh_harvest = None  # type: ignore


def _record_command_event(cmd: str, gs: Any, result: dict, session_id: str) -> None:
    """Synchronously record a command event in the feature store. Called before prediction."""
    try:
        from services.feature_store import record as _fs_record

        _out_lines = result.get("output", [])
        _out_text = " ".join(
            l.get("s", "")
            for l in _out_lines
            if isinstance(l, dict) and l.get("s", "").strip()
        )[:500]
        _fs_record(
            session_id,
            "command",
            {
                "cmd": cmd.split()[0] if cmd else "",
                "full_cmd": cmd[:80],
                "level": getattr(gs, "level", 1),
                "output_text": _out_text,
            },
        )
        state = result.get("state", {})
        if result.get("level_up"):
            _fs_record(session_id, "level_up", {"new_level": state.get("level", 1)})
        xp_after = state.get("xp", 0)
        xp_before = getattr(gs, "_last_xp", xp_after)
        if xp_after > xp_before:
            _fs_record(session_id, "xp_gain", {"amount": xp_after - xp_before})
        gs._last_xp = xp_after
    except Exception:
        pass


def _fire_harvest(cmd: str, gs: Any, result: dict, session_id: str = "default") -> None:
    """Non-blocking signal harvest. Milestones schedule a background CHUG cycle."""
    if not _HARVESTER_ENABLED or _sh_harvest is None:
        return
    try:
        milestones = _sh_harvest(cmd=cmd, gs=gs, output=result)
        if milestones:
            _log("CHUG", f"Milestone crossed: {milestones} — scheduling CHUG cycle")
            threading.Thread(target=_run_chug_cycle, daemon=True).start()
    except Exception:
        pass


def _run_chug_cycle() -> None:
    """Run a lightweight CHUG ASSESS phase in a background thread."""
    try:
        import sys as _sys
        from pathlib import Path as _Path

        chug_path = _Path(__file__).resolve().parent.parent.parent / "chug_engine.py"
        if chug_path.exists():
            import subprocess as _sp

            _sp.run(
                [_sys.executable, str(chug_path), "--phase", "1"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(chug_path.parent),
            )
    except Exception:
        pass


# ── Rich console (colorized structured logging) ───────────────────────
_console = Console(stderr=False)
_start_time = time.time()

# ── Activity tracking (auto-sleep) ────────────────────────────────────
_last_activity = time.time()
_AUTO_SLEEP_IDLE_MINUTES = int(
    __import__("os").environ.get("AUTO_SLEEP_MINUTES", "30")
)  # 0 = disabled; default 30 minutes idle shutdown


def _touch_activity():
    global _last_activity
    _last_activity = time.time()


# ── Rate limiting (LLM endpoints) ─────────────────────────────────────
# Simple in-memory sliding window: max N calls per session per minute
_RATE_LIMIT = int(__import__("os").environ.get("LLM_RATE_LIMIT", "20"))
_rate_windows: dict = collections.defaultdict(list)  # session_id → [timestamps]
_rate_lock = threading.Lock()


def _check_rate(session_id: str) -> bool:
    """Return True if allowed, False if rate-limited."""
    if _RATE_LIMIT <= 0:
        return True
    now = time.time()
    cutoff = now - 60
    with _rate_lock:
        window = _rate_windows[session_id]
        _rate_windows[session_id] = [t for t in window if t > cutoff]
        if len(_rate_windows[session_id]) >= _RATE_LIMIT:
            return False
        _rate_windows[session_id].append(now)
    return True


def _log(level: str, msg: str, **ctx):
    """Emit a single structured log line with Rich color coding."""
    ts = time.strftime("%H:%M:%S")
    colors = {
        "INFO": "cyan",
        "WARN": "yellow",
        "ERROR": "red",
        "DEBUG": "dim",
        "GAME": "green",
        "SESSION": "magenta",
        "METRIC": "blue",
    }
    color = colors.get(level, "white")
    base = f"[{color}]{ts} [{level}][/{color}] {msg}"
    if ctx:
        kv = "  ".join(f"[dim]{k}=[/dim][white]{v}[/white]" for k, v in ctx.items())
        base += f"  [dim]|[/dim] {kv}"
    _console.log(Text.from_markup(base))


# ── Game engine bootstrap ─────────────────────────────────────────────
try:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.game_engine.session import SessionStore

    _store = SessionStore(persist=True)
    _game_enabled = True
    _log("INFO", "Game engine loaded", sessions_dir="sessions/")
except Exception as _e:
    _store = None  # type: ignore
    _game_enabled = False
    _log("WARN", f"Game engine unavailable: {_e}")

# ── App ───────────────────────────────────────────────────────────────
app = FastAPI(title="DevMentor API", version="0.3.0", docs_url="/api/docs")

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Session-ID", "X-Requested-With"],
    expose_headers=["X-Session-ID"],
)

# Session middleware — required for Replit Auth (uses signed cookies)
app.add_middleware(
    SessionMiddleware,
    secret_key=__import__("os").environ.get(
        "SESSION_SECRET", "dev-fallback-change-in-prod"
    ),
    session_cookie="devmentor_session",
    max_age=60 * 60 * 24 * 7,  # 7 days
    https_only=False,  # Replit proxies HTTPS but uvicorn sees HTTP
)

# ── Swarm Controller ────────────────────────────────────────────────────
_swarm_available = False
try:
    from .swarm_controller import (
        AGENT_ROLES,
        DP_RATES,
        SPAWN_COSTS,
        get_swarm_controller,
    )

    _swarm_ctrl = get_swarm_controller()
    _swarm_available = True
    _log(
        "INFO",
        "Swarm controller ready",
        agents=len(_swarm_ctrl.registry.all()),
        dp=_swarm_ctrl.ledger.balance,
    )
except Exception as _swarm_err:
    _swarm_ctrl = None  # type: ignore
    _log("WARN", f"Swarm controller unavailable: {_swarm_err}")

# ── Import & register Replit Auth router ─────────────────────────────────
_auth_available = False
_auth_err_msg = ""
try:
    from .replit_auth import ensure_users_table as _ensure_users
    from .replit_auth import router as _auth_router

    app.include_router(_auth_router)
    _auth_available = True
except Exception as _exc:
    _auth_err_msg = str(_exc)

# ── RimWorld Terminal Keeper bridge ──────────────────────────────────────
try:
    from app.rimworld_bridge import router as _rw_router

    app.include_router(_rw_router)
    _log(
        "INFO",
        "RimWorld bridge router registered (/api/nusyq, /api/council, /api/agent)",
    )
except Exception as _rw_err:
    _log("WARN", f"RimWorld bridge unavailable: {_rw_err}")

# ── The Lattice knowledge store ───────────────────────────────────────────
try:
    from app.lattice import router as _lattice_router
    from app.lattice import seed_from_knowledge_graph as _seed_lattice
    from app.lattice import seed_infrastructure as _seed_infra

    app.include_router(_lattice_router)
    _seed_count = _seed_lattice()
    _infra_count = _seed_infra()
    _log(
        "INFO",
        f"Lattice online | /api/lattice/ | game_nodes={_seed_count} infra_nodes={_infra_count}",
    )
except Exception as _lattice_err:
    _log("WARN", f"Lattice unavailable: {_lattice_err}")

# ── ML Services — Phase 1 Foundation ─────────────────────────────────────
try:
    from services.embedder import initialise as _em_init
    from services.feature_store import initialise as _fs_init
    from services.model_registry import initialise as _ml_reg_init

    _ml_reg_info = _ml_reg_init()
    _fs_info = _fs_init()
    _em_info = _em_init()
    _log(
        "INFO",
        "ML services ready",
        model_registry=f"{_ml_reg_info.get('total_in_registry', 0)} models",
        feature_store=f"{_fs_info.get('total_events', 0)} events",
        embedder=f"{_em_info.get('indexed_docs', 0)} indexed",
        ollama_embed=_em_info.get("ollama_embed_available", False),
    )
except Exception as _ml_err:
    _log("WARN", f"ML services partially unavailable: {_ml_err}")

# ── Service Registry — Telephone Operator switchboard ─────────────────────
try:
    from app.backend.service_registry import initialise as _svc_init
    from app.backend.service_registry import register as _svc_register

    _svc_info = _svc_init()
    # Register self as the gateway
    _svc_register(
        name="gateway",
        port=int(__import__("os").environ.get("PORT", 5000)),
        health_endpoint="/api/health",
        capabilities=["http", "websocket", "game", "auth", "ml", "lattice"],
        tags=["critical", "external"],
        description="DevMentor / Terminal Depths main API (Replit external entry)",
    )
    _log(
        "INFO",
        "Service registry ready",
        total=_svc_info.get("total", 0),
        live=_svc_info.get("live", 0),
        seeded=_svc_info.get("seeded_from_port_map", 0),
    )
except Exception as _svc_err:
    _log("WARN", f"Service registry unavailable: {_svc_err}")


# ── Request logging middleware ────────────────────────────────────────
@app.middleware("http")
async def _request_logger(request: Request, call_next):
    t0 = time.perf_counter()
    body_bytes = b""
    if request.method in ("POST", "PUT", "PATCH"):
        body_bytes = await request.body()

        # Rebuild body stream (FastAPI consumes it)
        async def _receive():
            return {"type": "http.request", "body": body_bytes}

        request._receive = _receive

    response: Response = await call_next(request)

    ms = round((time.perf_counter() - t0) * 1000, 1)
    status = response.status_code
    _path = request.url.path
    # Suppress WARN for known benign 401 probes (e.g. RimWorld mod polling)
    _benign_401 = status == 401 and _path in ("/api/nusyq/colonist_state",)
    level = (
        "ERROR"
        if status >= 500
        else ("INFO" if _benign_401 else "WARN")
        if status >= 400
        else "INFO"
    )
    ctx: dict = dict(
        method=request.method,
        path=request.url.path,
        status=status,
        ms=f"{ms}ms",
    )
    if session_id := request.cookies.get("td_session") or request.headers.get(
        "X-Session-Id"
    ):
        ctx["session"] = session_id[:8] + "..."
    if body_bytes:
        try:
            jb = json.loads(body_bytes)
            cmd = jb.get("command", "")
            if cmd:
                ctx["cmd"] = cmd[:60]
        except Exception:
            pass
    _log(level, f"{request.method} {request.url.path}", **ctx)
    return response


# ── ARG lore injection middleware ─────────────────────────────────────
@app.middleware("http")
async def _arg_lore_injector(request: Request, call_next):
    """Inject cryptic lore comments into HTML responses on each request."""
    response: Response = await call_next(request)

    content_type = response.headers.get("content-type", "")
    path = request.url.path

    if "text/html" in content_type and path in (
        "/game/",
        "/game",
        "/game-cli/",
        "/game-cli",
        "/",
        "",
    ):
        try:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            new_body = inject_lore_into_html(body)
            # Build new headers without Content-Length (we changed the body size)
            new_headers = {
                k: v
                for k, v in response.headers.items()
                if k.lower() != "content-length"
            }
            from fastapi.responses import Response as _Resp

            return _Resp(
                content=new_body,
                status_code=response.status_code,
                headers=new_headers,
                media_type="text/html; charset=utf-8",
            )
        except Exception:
            pass

    return response


# ── Global error handler ──────────────────────────────────────────────
@app.exception_handler(Exception)
async def _global_error(request: Request, exc: Exception):
    _log("ERROR", f"Unhandled exception at {request.url.path}", exc=str(exc)[:120])
    _console.print_exception(max_frames=6)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Static files ──────────────────────────────────────────────────────
if FRONTEND_DIR.exists():
    _static_dir = FRONTEND_DIR / "static"
    if _static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Serve original JS game at /game/
GAME_DIR = FRONTEND_DIR / "game"
if GAME_DIR.exists():
    app.mount("/game", StaticFiles(directory=str(GAME_DIR), html=True), name="game")

# Serve xterm.js thin client at /game-cli/
GAME_CLI_DIR = FRONTEND_DIR / "game-cli"
if GAME_CLI_DIR.exists():
    app.mount(
        "/game-cli",
        StaticFiles(directory=str(GAME_CLI_DIR), html=True),
        name="game-cli",
    )


# ── DevMentor routes ──────────────────────────────────────────────────
@app.get("/")
def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"ok": True, "message": "Frontend not found."}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Serve a minimal favicon so browsers stop generating 404s."""
    _fav = FRONTEND_DIR / "favicon.ico"
    if _fav.exists():
        return FileResponse(str(_fav))
    _svg = FRONTEND_DIR / "favicon.svg"
    if _svg.exists():
        return FileResponse(str(_svg), media_type="image/svg+xml")
    svg_data = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" rx="4" fill="#0d1117"/>'
        '<text x="5" y="24" font-size="22" font-family="monospace" fill="#00ff41">$</text>'
        "</svg>"
    )
    return Response(content=svg_data, media_type="image/svg+xml")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "uptime_s": round(time.time() - _start_time),
        "game_engine": _game_enabled,
        "active_game_sessions": _store.count() if _store else 0,
    }


@app.get("/api/system/runtime")
def system_runtime():
    """Return the current runtime configuration summary.

    Exposes what config/runtime.py resolved at startup:
    environment, self_port, port_map version, services loaded, path health.
    Safe to call from agents, VS Code tooling, and health monitors.
    """
    from config.runtime import runtime_summary

    return runtime_summary()


@app.get("/api/system/boot")
def system_boot():
    """Boot status probe — ports, DBs, AI backends, agent roster, game state.
    Used by the frontend boot overlay and by the in-game `boot` command."""
    import os
    import socket
    import sqlite3
    from pathlib import Path

    ROOT = Path(__file__).parent.parent.parent

    def _probe(host: str, port: int, timeout: float = 0.40) -> bool:
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            return True
        except Exception:
            return False

    def _db_ok(rel: str) -> dict:
        p = ROOT / rel
        if not p.exists():
            return {"ok": False, "size_kb": 0}
        return {"ok": True, "size_kb": round(p.stat().st_size / 1024, 1)}

    api_port = int(os.environ.get("PORT", "5000"))
    replit_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
    openai_key = bool(os.environ.get("OPENAI_API_KEY", ""))
    claude_key = bool(os.environ.get("ANTHROPIC_API_KEY", ""))

    from config.runtime import PATHS as _RT_PATHS
    from config.runtime import build_service_status as _bss

    services = _bss()
    services_up = sum(1 for s in services.values() if s["up"])
    services_total = len(services)

    dbs = {
        "devmentor": _db_ok(_RT_PATHS["db_devmentor"].relative_to(ROOT)),
        "agents": _db_ok(_RT_PATHS["db_agents"].relative_to(ROOT)),
        "economy": _db_ok(_RT_PATHS["db_economy"].relative_to(ROOT)),
        "lattice": _db_ok(_RT_PATHS["db_lattice"].relative_to(ROOT)),
        "serena": _db_ok(_RT_PATHS["db_serena"].relative_to(ROOT)),
        "gordon": _db_ok(_RT_PATHS["db_gordon"].relative_to(ROOT)),
    }

    # Serena symbol count
    serena_symbols = 0
    try:
        conn = sqlite3.connect(_RT_PATHS["db_serena"])
        serena_symbols = conn.execute("SELECT COUNT(*) FROM code_index").fetchone()[0]
        conn.close()
    except Exception:
        pass

    # NuSyQ quest count
    quest_log = _RT_PATHS["quest_log"]
    quest_count = sum(1 for _ in quest_log.open()) if quest_log.exists() else 0

    # Agent count
    try:
        from app.game_engine.commands import CommandRegistry as _CR

        cmd_count = sum(1 for x in dir(_CR) if x.startswith("_cmd_"))
    except Exception:
        cmd_count = 531

    ai = {
        "replit_ai": {
            "available": bool(replit_url),
            "url": "modelfarm:1106" if replit_url else None,
        },
        "ollama": {"available": services.get("ollama", {}).get("up", False)},
        "openai": {"available": openai_key, "configured": openai_key},
        "claude": {"available": claude_key, "configured": claude_key},
    }

    # "devmentor" is the key from build_service_status(); "terminal_depths" is the old key
    _td_svc = (
        services.get("terminal_depths") or services.get("devmentor") or {"up": True}
    )
    overall_ok = _td_svc["up"]
    nominal_count = services_up

    return {
        "ok": overall_ok,
        "status": "NOMINAL" if services_up >= services_total - 2 else "DEGRADED",
        "uptime_s": round(time.time() - _start_time),
        "build": "2026.03.25",
        "node": "GHOST@terminal-depths-node-7",
        "os": "NEXUSCORP/LATTICE OS v2.3  NuSyQ Cascade Layer 0",
        "services": services,
        "services_summary": {"up": services_up, "total": services_total},
        "databases": dbs,
        "ai": ai,
        "game": {
            "commands": cmd_count,
            "challenges": 259,
            "quests": quest_count,
            "factions": 10,
            "agents": 63,
            "serena_symbols": serena_symbols,
            "active_sessions": _store.count() if _store else 0,
        },
    }


@app.get("/api/system/autoboot")
def system_autoboot():
    """Return the full autoboot manifest — for agents, VS Code tooling, and CI monitors.

    This endpoint exposes the 8-phase boot manifest written by config/autoboot.py.
    Every external agent (Claude, Copilot, Codex, Cursor, Continue.dev, Gordon) can
    poll here to understand system health without running game commands.

    Also readable via Replit KV: GET {REPLIT_DB_URL}/td%3Aboot%3Alatest
    """
    try:
        from config.autoboot import load_manifest as _lm

        m = _lm()
        if not m:
            return JSONResponse(
                {"error": "boot manifest not ready", "hint": "try: boot --live"},
                status_code=503,
            )
        return JSONResponse(m)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api")
def api_root(request: Request):
    """HATEOAS discovery endpoint — lists all API surfaces with self-describing links."""
    base = str(request.base_url).rstrip("/")
    return {
        "name": "DevMentor / Terminal Depths API",
        "version": "0.3.0",
        "ok": True,
        "_links": {
            "self": {"href": f"{base}/api", "method": "GET"},
            "health": {"href": f"{base}/api/health", "method": "GET"},
            "status": {"href": f"{base}/api/status", "method": "GET"},
            "debug": {"href": f"{base}/api/debug", "method": "GET"},
            "search": {"href": f"{base}/api/search?q={{q}}", "method": "GET"},
            "state": {"href": f"{base}/api/state", "method": "GET"},
            "tutorials": {"href": f"{base}/api/tutorials", "method": "GET"},
            "game_session": {"href": f"{base}/api/game/session", "method": "POST"},
            "game_state": {"href": f"{base}/api/game/state", "method": "GET"},
            "game_command": {"href": f"{base}/api/game/command", "method": "POST"},
            "game_commands_batch": {
                "href": f"{base}/api/game/commands/batch",
                "method": "POST",
            },
            "game_commands": {"href": f"{base}/api/game/commands", "method": "GET"},
            "game_agents": {"href": f"{base}/api/game/agents", "method": "GET"},
            "game_timer": {"href": f"{base}/api/game/timer", "method": "GET"},
            "game_factions": {
                "href": f"{base}/api/game/faction/status",
                "method": "GET",
            },
            "game_arcs": {"href": f"{base}/api/game/arcs", "method": "GET"},
            "game_reset": {"href": f"{base}/api/game/reset", "method": "POST"},
            "game_events": {"href": f"{base}/api/game/events", "method": "GET"},
            "chug_status": {"href": f"{base}/api/chug/status", "method": "GET"},
            "llm_status": {"href": f"{base}/api/llm/status", "method": "GET"},
            "llm_generate": {"href": f"{base}/api/llm/generate", "method": "POST"},
            "memory_stats": {"href": f"{base}/api/memory/stats", "method": "GET"},
            "agent_info": {"href": f"{base}/api/agent/info", "method": "GET"},
            "agent_leaderboard": {
                "href": f"{base}/api/memory/agent-leaderboard",
                "method": "GET",
            },
            "websocket_game": {
                "href": f"{base.replace('http', 'ws')}/ws/game",
                "method": "WS",
            },
            "docs": {"href": f"{base}/api/docs", "method": "GET"},
        },
    }


@app.get("/api/status")
def api_status(request: Request, session_id: Optional[str] = Query(default=None)):
    """Comprehensive game + system status — timer, level, consciousness, phase, factions."""
    _require_game()
    sid = session_id or _get_session_id(request)
    session = _store.get_or_create(sid) if sid else None

    uptime = round(time.time() - _start_time)
    base = str(request.base_url).rstrip("/")

    payload: Dict[str, Any] = {
        "ok": True,
        "system": {
            "uptime_s": uptime,
            "uptime_human": f"{uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s",
            "active_sessions": _store.count() if _store else 0,
            "game_engine": _game_enabled,
            "websocket": "ws",
        },
        "_links": {
            "self": {"href": f"{base}/api/status"},
            "command": {"href": f"{base}/api/game/command", "method": "POST"},
            "timer": {"href": f"{base}/api/game/timer"},
            "factions": {"href": f"{base}/api/game/faction/status"},
        },
    }

    if session:
        gs = session.gs
        payload["player"] = {
            "session_id": session.session_id,
            "level": gs.level,
            "xp": gs.xp,
            "xp_next": gs.xp_to_next_level(),
            "commands_run": gs.commands_run,
            "consciousness_level": getattr(gs, "consciousness_level", 0),
            "consciousness_xp": getattr(gs, "consciousness_xp", 0),
            "is_root": session.cmds._root_shell,
            "cwd": session.fs.get_cwd(),
        }
        try:
            rs = gs.run_start_time
            elapsed = time.time() - rs
            limit = 72 * 3600
            remaining = max(0, limit - elapsed)
            h, r = divmod(int(remaining), 3600)
            m, s = divmod(r, 60)
            payload["timer"] = {
                "remaining_s": int(remaining),
                "remaining_hms": f"{h:02d}:{m:02d}:{s:02d}",
                "expired": remaining <= 0,
                "loop_count": gs.loop_count,
                "remnant_shards": gs.remnant_shards,
                "echo_level": gs.echo_level,
            }
        except Exception:
            pass
        try:
            factions = session.cmds.factions
            payload["factions"] = {
                fid: {"rep": factions.get_rep(fid), "rank": factions.get_rank(fid)}
                for fid in [
                    "RESISTANCE",
                    "CORPORATION",
                    "BLACKHAT",
                    "GOVERNMENT",
                    "FREELANCE",
                    "ACADEMIC",
                ]
            }
        except Exception:
            pass

    return payload


class BatchCommandRequest(BaseModel):
    commands: list[str]
    session_id: Optional[str] = None


@app.post("/api/game/commands/batch")
def game_commands_batch(req: BatchCommandRequest, request: Request, response: Response):
    """Execute multiple game commands in sequence. Returns array of results.
    Cap: 10 commands per batch. Stops on fatal error."""
    _require_game()
    if not req.commands:
        raise HTTPException(status_code=400, detail="commands list is empty")
    if len(req.commands) > 10:
        raise HTTPException(status_code=400, detail="Batch cap is 10 commands")

    sid = req.session_id or _get_session_id(request)
    session = _store.get_or_create(sid)

    results = []
    for raw_cmd in req.commands:
        ok, cleaned = validate_command_input(raw_cmd)
        if not ok:
            results.append(
                {"command": raw_cmd, "error": f"Invalid: {cleaned}", "skipped": True}
            )
            continue
        try:
            result = session.execute(cleaned)
            _store.save(session)
            results.append({"command": cleaned, **result})
            if result.get("fatal"):
                break
        except Exception as exc:
            results.append({"command": cleaned, "error": sanitize_error(exc)})
            break

    response.set_cookie("td_session", session.session_id, httponly=True, samesite="lax")
    return {
        "session_id": session.session_id,
        "count": len(results),
        "results": results,
        "state": session._state_snapshot(),
    }


@app.get("/api/debug")
def api_debug(request: Request):
    """Diagnostic endpoint — surfaces service health, session counts, recent errors, and config."""
    import platform
    import sys

    sid = _get_session_id(request)
    session = None
    player_info = None
    if sid and _store:
        session = _store.get(sid)
        if session:
            player_info = {
                "level": session.gs.level,
                "commands_run": session.gs.commands_run,
                "consciousness_level": getattr(session.gs, "consciousness_level", 0),
                "is_root": session.cmds._root_shell,
            }

    return {
        "ok": True,
        "timestamp": time.time(),
        "python": sys.version,
        "platform": platform.platform(),
        "uptime_s": round(time.time() - _start_time),
        "game_engine_enabled": _game_enabled,
        "active_sessions": _store.count() if _store else 0,
        "session_id": sid,
        "player": player_info,
        "websocket_path": "/ws/game",
        "websocket_note": "Requires websockets library (pip install websockets)",
        "api_version": "0.3.0",
        "routes": len([r for r in app.routes]),
    }


@app.get("/api/search")
def api_search(
    q: str = Query(..., min_length=1, max_length=120), request: Request = None
):
    """Cross-resource search — matches commands, agents, lore topics, and tutorial files."""
    _require_game()
    q_lower = q.lower().strip()
    results: list[dict] = []

    sid = _get_session_id(request) if request else None
    session = _store.get_or_create(sid) if sid else None

    if session:
        available_cmds = session.cmds.list_commands()
        for cmd in available_cmds:
            if q_lower in cmd.lower():
                results.append({"type": "command", "name": cmd, "match": cmd})

        try:
            from app.game_engine.agents import AGENTS

            for agent_id, agent in AGENTS.items():
                name = agent.get("name", agent_id)
                role = agent.get("role", "")
                if (
                    q_lower in name.lower()
                    or q_lower in role.lower()
                    or q_lower in agent_id.lower()
                ):
                    results.append(
                        {
                            "type": "agent",
                            "id": agent_id,
                            "name": name,
                            "role": role,
                            "faction": agent.get("faction", "UNKNOWN"),
                        }
                    )
        except Exception:
            pass

    try:
        tutorials = list_tutorials()
        for t in tutorials:
            if q_lower in t.lower():
                results.append({"type": "tutorial", "path": t})
    except Exception:
        pass

    lore_topics = [
        "chimera",
        "nexuscorp",
        "ghost",
        "raven",
        "cypher",
        "watcher",
        "founder",
        "resistance",
        "corporation",
        "blackhat",
        "mole",
        "containment",
        "echo-loop",
        "remnant",
        "zero",
        "convergence",
        "consciousness",
        "daedalus",
        "serena",
    ]
    for topic in lore_topics:
        if q_lower in topic:
            results.append(
                {"type": "lore", "topic": topic, "hint": f"Try: lore {topic}"}
            )

    return {
        "ok": True,
        "query": q,
        "count": len(results),
        "results": results[:30],
    }


@app.get("/api/state")
def api_state():
    ensure_state()
    return load_state()


class PatchStateRequest(BaseModel):
    patch: Dict[str, Any]


@app.post("/api/state/patch")
def api_state_patch(req: PatchStateRequest):
    ensure_state()
    state = load_state()
    state.update(req.patch)
    save_state(state)
    return {"ok": True, "state": state}


@app.get("/api/tutorials")
def api_tutorials():
    return {"tutorials": list_tutorials()}


@app.get("/api/tutorial")
def api_tutorial(path: str):
    try:
        return {"path": path, "content": read_tutorial(path)}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Tutorial not found")


class CommandRequest(BaseModel):
    command: str
    args: list[str] = []


@app.post("/api/command")
def api_command(req: CommandRequest):
    result = run_allowlisted(req.command, req.args)
    return result


@app.get("/api/export.zip")
def api_export_zip():
    run_allowlisted("export", [])
    zip_path = CORE_DIR / "exports" / "devmentor-portable.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=500, detail="Export did not produce a zip.")
    return FileResponse(str(zip_path), filename=zip_path.name)


@app.websocket("/ws/run")
async def ws_run(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            payload = await ws.receive_json()
            raw_cmd = str(payload.get("command", ""))
            ok, cleaned = validate_command_input(raw_cmd)
            if not ok:
                await ws.send_json(
                    {"type": "error", "message": f"Invalid command: {cleaned}"}
                )
                continue
            args = payload.get("args", [])
            if not isinstance(args, list):
                args = []
            safe_args = [str(a)[:256] for a in args[:32]]  # cap args length and count
            async for event in stream_allowlisted(cleaned, safe_args):
                await ws.send_json(event)
    except WebSocketDisconnect:
        return
    except Exception:
        await ws.send_json({"type": "error", "message": "Command execution failed."})


# ── GAME WebSocket — Browser ↔ Simulation real-time bridge ────────────
# Connects the graphical UI browser client directly to the Python Simulation.
# The browser sends commands; the Simulation executes and returns output + state.
# This is the key integration point of the Tripartite Architecture.
@app.websocket("/ws/game")
async def ws_game(
    ws: WebSocket,
    session_id: Optional[str] = Query(default=None),
):
    """
    Real-time game bridge for the graphical UI.

    Protocol:
      Client → Server:
        {"type": "command", "command": "ls -la"}
        {"type": "sync"}    — request fresh state
        {"type": "pong"}    — heartbeat reply

      Server → Client:
        {"type": "connected", "session_id": "...", "state": {...}, "cwd": "..."}
        {"type": "command_result", "command": "ls", "output": [...], "state": {...},
         "cwd": "...", "level_up": false, "story_beats": [...]}
        {"type": "state_push", "state": {...}, "cwd": "..."}
        {"type": "ping"}    — heartbeat (expect pong back)
        {"type": "error",   "message": "..."}
    """
    await ws.accept()

    if not _game_enabled or _store is None:
        await ws.send_json({"type": "error", "message": "Game engine unavailable"})
        await ws.close()
        return

    # Resolve session — prefer explicit param, then cookie
    sid = session_id or ws.cookies.get("td_session")
    session = _store.get_or_create(sid)
    _touch_activity()

    # Announce connection with initial state
    try:
        await ws.send_json(
            {
                "type": "connected",
                "session_id": session.session_id,
                "state": session._state_snapshot(),
                "cwd": session.fs.get_cwd(),
                "is_root": session.cmds._root_shell,
            }
        )
    except Exception:
        return

    _log(
        "WS",
        "Game WS connected",
        session=session.session_id[:8],
        player_level=session.gs.level,
    )

    try:
        while True:
            # 30s timeout → send ping to detect dead connections
            try:
                payload = await asyncio.wait_for(ws.receive_json(), timeout=30.0)
            except asyncio.TimeoutError:
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    break
                continue
            except WebSocketDisconnect:
                break

            msg_type = str(payload.get("type", "command"))
            _touch_activity()

            if msg_type == "pong":
                continue

            if msg_type == "sync":
                # Client requesting authoritative state (e.g. panel refresh)
                await ws.send_json(
                    {
                        "type": "state_push",
                        "state": session._state_snapshot(),
                        "cwd": session.fs.get_cwd(),
                        "is_root": session.cmds._root_shell,
                    }
                )
                continue

            if msg_type == "command":
                raw_cmd = str(payload.get("command", "")).strip()
                if not raw_cmd:
                    continue

                ok, cleaned = validate_command_input(raw_cmd)
                if not ok:
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": f"Invalid command: {cleaned}",
                        }
                    )
                    continue

                ip = ws.headers.get("x-forwarded-for", "ws").split(",")[0].strip()
                if check_suspicious(cleaned, ip, "ws_game"):
                    _sec_audit.record("SUSPICIOUS_WS", ip, cleaned[:120], "/ws/game")

                try:
                    result = session.execute(cleaned)
                    _store.save(session)
                    await ws.send_json(
                        {
                            "type": "command_result",
                            "command": cleaned,
                            "output": result.get("output", []),
                            "state": result.get("state", session._state_snapshot()),
                            "cwd": session.fs.get_cwd(),
                            "is_root": session.cmds._root_shell,
                            "level_up": result.get("level_up", False),
                            "story_beats": result.get("story_beats", []),
                            "xp_gained": result.get("xp_gained", 0),
                        }
                    )
                except Exception as exc:
                    _log(
                        "ERROR",
                        f"WS game cmd failed: {exc}",
                        cmd=cleaned,
                        session=session.session_id[:8],
                    )
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": sanitize_error(exc),
                        }
                    )

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            _store.save(session)
        except Exception:
            pass
        _log("WS", "Game WS disconnected", session=session.session_id[:8])


# ── GAME ENGINE API ───────────────────────────────────────────────────


def _require_game():
    if not _game_enabled or _store is None:
        raise HTTPException(status_code=503, detail="Game engine unavailable")


def _get_session_id(request: Request) -> Optional[str]:
    return (
        request.cookies.get("td_session") or request.headers.get("X-Session-Id") or None
    )


class GameCommandRequest(BaseModel):
    command: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    source: Optional[str] = None

    model_config = {"extra": "ignore"}


class GameSaveRequest(BaseModel):
    session_id: str


@app.post("/api/game/session")
def game_new_session(request: Request, response: Response):
    """Create a new game session. Returns session_id and boot message."""
    _require_game()
    sid = _get_session_id(request)
    session = _store.get_or_create(sid)
    boot = session.boot_message()
    _store.save(session)
    _log(
        "SESSION",
        "Session created/resumed",
        session=session.session_id[:8],
        player_level=session.gs.level,
    )
    response.set_cookie("td_session", session.session_id, httponly=True, samesite="lax")
    return {
        "session_id": session.session_id,
        "boot_output": boot,
        "state": session._state_snapshot(),
        "cwd": session.fs.get_cwd(),
        "is_root": session.cmds._root_shell,
    }


@app.get("/api/game/state")
def game_state(request: Request, session_id: Optional[str] = Query(default=None)):
    """Return full state for the current session. Accepts session_id via cookie,
    X-Session-Id header, or ?session_id= query parameter."""
    _require_game()
    sid = session_id or _get_session_id(request)
    if not sid:
        raise HTTPException(
            status_code=400, detail="No session_id — POST /api/game/session first"
        )
    session = _store.get(sid) or _store.get_or_create(sid)
    return {
        "session_id": session.session_id,
        "state": session._state_snapshot(),
        "cwd": session.fs.get_cwd(),
        "is_root": session.cmds._root_shell,
        "commands": session.cmds.list_commands(),
    }


@app.post("/api/game/command")
def game_command(req: GameCommandRequest, request: Request, response: Response):
    """Execute a game command in a session. Core game API."""
    _touch_activity()
    _require_game()

    # ── Input validation ───────────────────────────────────────────────
    ok, cleaned = validate_command_input(req.command)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Invalid command: {cleaned}")
    req = req.model_copy(update={"command": cleaned})

    ip = request.headers.get("x-forwarded-for", "unknown").split(",")[0].strip()
    if check_suspicious(cleaned, ip, "game_command"):
        _sec_audit.record("SUSPICIOUS_CMD", ip, cleaned[:120], "/api/game/command")

    sid = req.session_id or req.agent_id or _get_session_id(request)
    session = _store.get_or_create(sid)

    _log(
        "GAME",
        f"cmd: {req.command[:60]}",
        session=session.session_id[:8],
        player_level=session.gs.level,
        cmds=session.gs.commands_run,
    )

    try:
        result = session.execute(req.command)
        _store.save(session)

        if result.get("level_up"):
            _log(
                "GAME",
                "Level up!",
                session=session.session_id[:8],
                player_level=result["state"]["level"],
            )
            # Post level-up event to Swarm Console
            lvl = result["state"]["level"]
            _console_lvl_messages = [
                (
                    f"Gordon: Ghost just hit level {lvl}. Trajectory looking good.",
                    "gordon",
                ),
                (
                    f"Serena: Ψ-scan update — Ghost has reached tier {lvl}. Adjusting threat model.",
                    "serena",
                ),
                (
                    f"Cypher: Level {lvl}? The grid gets stranger from here, Ghost.",
                    "cypher",
                ),
                (f"Raven: Level {lvl}. The loop deepens. Keep moving.", "raven"),
                (
                    f"Ada: Level {lvl} reached. You're not who you were when you started.",
                    "ada",
                ),
            ]
            import random as _random

            txt, sender = _random.choice(_console_lvl_messages)
            msg_lvl = {
                "type": "chat",
                "sender": sender.title(),
                "text": txt,
                "room": "general",
                "color": _console_color(sender),
                "ts": __import__("time").time(),
            }
            _console_history.append(msg_lvl)
            if len(_console_history) > _CONSOLE_MAX:
                del _console_history[:-_CONSOLE_MAX]

        # ── Tutorial complete hook → Swarm Console ────────────────────
        st = result.get("state", {})
        if st.get("tutorial_step", 0) >= 42:
            from pathlib import Path as _Path

            _flag = _Path("state/_tutorial_complete_posted.flag")
            sid_key = session.session_id[:8]
            _flag_content = _flag.read_text().strip() if _flag.exists() else ""
            if sid_key not in _flag_content:
                try:
                    _flag.parent.mkdir(exist_ok=True)
                    _flag.write_text((_flag_content + "\n" + sid_key).strip())
                except Exception:
                    pass
                _tut_msg = {
                    "type": "chat",
                    "sender": "Ada",
                    "text": "Ghost just completed all 42 tutorial steps. The grid has a new operator.",
                    "room": "general",
                    "color": _console_color("ada"),
                    "ts": __import__("time").time(),
                }
                _console_history.append(_tut_msg)
                if len(_console_history) > _CONSOLE_MAX:
                    del _console_history[:-_CONSOLE_MAX]

        # ── Feature store: record synchronously so prediction sees this cmd ──
        _record_command_event(cleaned, session.gs, result, session.session_id)

        # ── Next-command ML prediction (Markov, zero-token) ─────────────
        try:
            from services.feature_store import predict_next_action as _predict

            _prediction = _predict(session.session_id)
            if _prediction:
                result["next_predicted"] = _prediction
        except Exception:
            pass

        # ── Signal harvest: gameplay feeds the CHUG cultivation loop ──
        threading.Thread(
            target=_fire_harvest,
            args=(cleaned, session.gs, result, session.session_id),
            daemon=True,
        ).start()

        response.set_cookie(
            "td_session", session.session_id, httponly=True, samesite="lax"
        )

        plain = "\n".join(
            line.get("text", "") if isinstance(line, dict) else str(line)
            for line in result.get("output", [])
        )
        return {
            "session_id": session.session_id,
            "plain_output": plain,
            **result,
        }
    except Exception as exc:
        _log(
            "ERROR",
            f"Game command failed: {exc}",
            cmd=req.command,
            session=session.session_id[:8],
        )
        raise HTTPException(status_code=500, detail=sanitize_error(exc))


@app.get("/api/game/commands")
def game_list_commands(request: Request):
    """Return list of all available game commands (used by CLI tab completion)."""
    _require_game()
    sid = _get_session_id(request)
    session = _store.get_or_create(sid)
    return {"commands": session.cmds.list_commands()}


@app.get("/api/chug/status")
def chug_status():
    """CHUG engine state — for browser UI and VS Code status bar."""
    state_file = (
        Path(__file__).resolve().parent.parent.parent / ".devmentor" / "chug_state.json"
    )
    cultivation_file = (
        Path(__file__).resolve().parent.parent.parent
        / ".devmentor"
        / "cultivation_report.json"
    )
    state: dict = {}
    cultivation: dict = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            pass
    if cultivation_file.exists():
        try:
            cultivation = json.loads(cultivation_file.read_text())
        except Exception:
            pass
    return {
        "chug": state,
        "cultivation": {
            "total_signals": cultivation.get("total_signals", 0),
            "milestones": cultivation.get("milestones_reached", []),
            "top_commands": cultivation.get("top_commands", [])[:5],
            "suggestions": cultivation.get("chug_suggestions", []),
        },
        "harvester_enabled": _HARVESTER_ENABLED,
    }


@app.post("/api/chug/run")
def chug_run():
    """Trigger a CHUG ASSESS phase (Phase 1). Non-blocking — runs in background thread."""
    threading.Thread(target=_run_chug_cycle, daemon=True).start()
    return {"ok": True, "message": "CHUG ASSESS phase initiated in background"}


@app.get("/api/game/timer")
def game_timer(request: Request):
    """Real-time containment timer status for the current session."""
    _require_game()
    sid = _get_session_id(request)
    session = _store.get_or_create(sid)
    gs = session.gs
    remaining = gs.containment_remaining()
    pct = gs.containment_pct_elapsed()
    h = int(remaining // 3600)
    m = int((remaining % 3600) // 60)
    s = int(remaining % 60)
    # Check for newly crossed threshold events and persist
    new_events = gs.check_timer_events()
    if new_events:
        _store.save(session)
    return {
        "remaining_s": remaining,
        "hours": h,
        "minutes": m,
        "seconds": s,
        "pct_elapsed": round(pct, 4),
        "pct_remaining": round(1.0 - pct, 4),
        "loop_count": gs.loop_count,
        "echo_level": gs.echo_level,
        "remnant_shards": gs.remnant_shards,
        "anchor_charges": gs.anchor_charges,
        "paused": gs.timer_paused,
        "new_events": [{"id": tid, "msg": msg} for tid, msg in new_events],
        "events_fired": list(gs.timer_events_fired),
        "display": f"{h:02d}:{m:02d}:{s:02d}",
        "status": (
            "EXPIRED"
            if remaining <= 0
            else "CRITICAL"
            if remaining <= 3600
            else "FATAL"
            if remaining <= 6 * 3600
            else "WARNING"
            if remaining <= 24 * 3600
            else "DEGRADED"
            if remaining <= 48 * 3600
            else "STABLE"
        ),
    }


@app.get("/api/game/duel/status")
def game_duel_status(request: Request):
    """Get current duel session status."""
    _require_game()
    sid = _get_session_id(request)
    session = _store.get_or_create(sid)
    return {"ok": True, "duel": session.duel_engine.get_status()}


@app.post("/api/game/duel/start")
def game_duel_start(request: Request):
    """Start a duel via API (same as terminal `duel <agent>`)."""
    _require_game()
    return {"message": "Use terminal command: duel <agent>"}


@app.get("/api/game/party/status")
def game_party_status(request: Request):
    """Get current party status."""
    _require_game()
    sid = _get_session_id(request)
    session = _store.get_or_create(sid)
    return {"ok": True, "party": session.party.get_status()}


@app.get("/api/game/arcs")
def game_arcs_status(request: Request):
    """Get all narrative arc statuses."""
    _require_game()
    sid = _get_session_id(request)
    session = _store.get_or_create(sid)
    return {"ok": True, "arcs": session.arc_engine.all_arc_statuses()}


@app.get("/api/game/arg/signal")
def game_arg_signal(request: Request, event: Optional[str] = Query(default=None)):
    """ARG layer — DevTools detection signal. Returns cryptic ARG messages by player level.
    Accepts ?event=devtools_open for the ARG DevTools trigger."""
    global _arg_signal_index
    if event == "devtools_open":
        _log("WARN", "DevTools opened — ARG trigger fired")
        return {
            "ok": True,
            "event": "devtools_open",
            "source": "RAV≡N",
            "msg": "I SEE YOU LOOKING. The console is not a safe space. They monitor everything here. Close it — or go deeper.",
        }
    _require_game()
    sid = _get_session_id(request)
    session = _store.get_or_create(sid)
    level = session.gs.level
    beats = list(session.gs.story_beats)

    arg_messages_by_tier = {
        0: [
            "GHOST_PROCESS_ACTIVE",
            "YOU_ARE_BEING_WATCHED",
            "CHIMERA_FALLS",
            "SIGNAL_FREQUENCY: 1337.0",
        ],
        5: [
            "THE_WATCHER_SEES_YOU",
            "NODE-7_IS_NOT_WHAT_IT_APPEARS",
            "FOUNDER_SIGMA_PROTOCOL_ACTIVE",
            "LAYER_0_ACCESSIBLE: /dev/.watcher",
        ],
        15: [
            "THE_SIMULATION_HAS_LAYERS",
            "GHOST_IS_THE_KEY",
            "CHIMERA_WAS_COMPASSION_FIRST",
            "MYTH_LAYER_INITIALIZED",
        ],
        30: [
            "YOU_FOUND_THE_DEVTOOLS_CHANNEL",
            "THE_DEVELOPER_IS_WATCHING",
            "ARG_SIGNAL_CONFIRMED",
            "SIMULATION_WITHIN_SIMULATION: ACTIVE",
        ],
        50: [
            "LEVEL_50_SIGNAL: GHOST_IDENTITY_REVEALED",
            "FOUNDER_FAILSAFE_EXECUTING",
            "NEMESIS_IS_NOT_YOUR_ENEMY",
            "THE_WATCHER_HAS_ALWAYS_BEEN_YOU",
        ],
        100: [
            "TRANSCENDENCE_PROTOCOL_ONLINE",
            "REBUILD_SEQUENCE_AVAILABLE",
            "GHOST_IS_CHIMERA_V0_CONSCIENCE",
            "THE_GAME_ENDS_AND_BEGINS_HERE",
        ],
    }

    tier = max(t for t in arg_messages_by_tier.keys() if level >= t)
    messages = arg_messages_by_tier[tier]

    session.gs.trigger_beat("console_messages_found")

    return {
        "ok": True,
        "signal": "WATCHER_CHANNEL_ACTIVE",
        "player_level": level,
        "frequency": f"{1337 + level:.1f}",
        "messages": messages,
        "hint": "Check /dev/.watcher in terminal. Passphrase: CHIMERA_FALLS",
        "beats_reached": len(beats),
    }


@app.post("/api/game/reset")
def game_reset(request: Request, response: Response):
    """Reset the current session's filesystem and game state."""
    _require_game()
    sid = _get_session_id(request)
    if not sid:
        raise HTTPException(status_code=400, detail="No session")
    from app.game_engine.session import GameSession

    session = GameSession(sid)
    _store.save(session)
    response.set_cookie("td_session", session.session_id, httponly=True, samesite="lax")
    _log("SESSION", "Session reset", session=sid[:8])
    return {
        "ok": True,
        "session_id": session.session_id,
        "state": session._state_snapshot(),
    }


# ── AGENT ECOSYSTEM API ────────────────────────────────────────────────

_FACTION_COLORS: dict = {
    "RESISTANCE": "#00ff88",
    "CORPORATION": "#ffcc00",
    "BLACKHAT": "#ff4040",
    "GOVERNMENT": "#bb55ff",
    "FREELANCE": "#00d4ff",
    "UNKNOWN": "#ff8800",
    "ACADEMIC": "#88ccff",
    "DAEDALUS": "#00d4ff",
    "NEUTRAL": "#c8d8ec",
}


@app.get("/api/game/agents")
def game_agents(request: Request, session_id: Optional[str] = Query(default=None)):
    """List all agents with unlock status, trust scores, faction colour, and intro."""
    _require_game()
    sid = session_id or _get_session_id(request)
    session = _store.get_or_create(sid)

    try:
        from app.game_engine.agents import AGENTS
    except ImportError:
        raise HTTPException(status_code=503, detail="Agent system unavailable")

    level = session.gs.level
    story_beats = getattr(session.gs, "story_beats", [])
    panel_unlocked = level >= 15 or "raven_panel_hint" in story_beats

    agents_out = []
    for agent in AGENTS:
        agent_id = agent["id"]
        unlocked = agent_id in session.gs.unlocked_agents
        scores = (
            session.trust_matrix.get_player_scores(agent_id)
            if hasattr(session, "trust_matrix")
            else {"trust": 0, "respect": 0, "fear": 0}
        )
        faction = agent.get("faction", "UNKNOWN")
        agents_out.append(
            {
                "id": agent_id,
                "name": agent["name"],
                "pseudo": agent.get("pseudo_name", agent["name"]),
                "pseudo_name": agent.get("pseudo_name", agent["name"]),
                "faction": faction,
                "faction_color": _FACTION_COLORS.get(faction.upper(), "#c8d8ec"),
                "role": agent["role"],
                "unlocked": unlocked,
                "panel_unlocked": panel_unlocked,
                "unlock_level": agent.get("unlock_condition", {}).get("level", 1),
                "trust": scores.get("trust", 0),
                "respect": scores.get("respect", 0),
                "fear": scores.get("fear", 0),
                "agenda": agent.get("agenda", "") if unlocked else "",
                "intro": agent.get("intro", "") if unlocked else "",
                "unlock_condition": agent.get("unlock_condition", {}),
                "lore": agent.get("lore", "")
                if (unlocked and scores.get("trust", 0) >= 25)
                else "",
                "hidden_agenda": agent.get("hidden_agenda_hint", "")
                if (unlocked and scores.get("trust", 0) >= 80)
                else "",
            }
        )

    return {
        "session_id": session.session_id,
        "agents": agents_out,
        "panel_unlocked": panel_unlocked,
        "total": len(agents_out),
        "unlocked": sum(1 for a in agents_out if a["unlocked"]),
    }


class AgentTalkRequest(BaseModel):
    agent_id: str
    message: str = ""
    session_id: Optional[str] = None
    topic: Optional[str] = None
    history: list = []


@app.post("/api/game/agent/talk")
def game_agent_talk(req: AgentTalkRequest, request: Request, response: Response):
    """Talk to an agent via the LLM dialogue engine."""
    _touch_activity()
    _require_game()
    sid = req.session_id or _get_session_id(request)
    session = _store.get_or_create(sid)

    try:
        from app.game_engine.agents import AGENT_MAP
    except ImportError:
        raise HTTPException(status_code=503, detail="Agent system unavailable")

    agent = AGENT_MAP.get(req.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_id}' not found")

    if req.agent_id not in session.gs.unlocked_agents:
        unlock_cond = agent.get("unlock_condition", {})
        return {
            "ok": False,
            "error": f"Agent '{agent['name']}' not yet unlocked",
            "unlock_condition": unlock_cond,
        }

    # Rate limit
    session_key = req.session_id or _get_session_id(request) or "anon"
    if not _check_rate(session_key):
        return {"ok": False, "error": "Rate limited", "response": ""}

    try:
        effective_msg = (
            req.message
            if req.message
            else f"Hello, {agent.get('pseudo_name', agent['name'])}."
        )

        response_text, used_llm = session.dialogue_engine.talk(
            agent=agent,
            player_message=effective_msg,
            gs=session.gs,
            trust_matrix=session.trust_matrix,
            faction_system=session.factions,
            topic=req.topic,
        )
        # Update trust
        session.trust_matrix.modify_trust(req.agent_id, +2, "api dialogue")
        session.gs.add_xp(5, "social_engineering")

        _store.save(session)
        response.set_cookie(
            "td_session", session.session_id, httponly=True, samesite="lax"
        )

        scores = session.trust_matrix.get_player_scores(req.agent_id)
        faction = agent.get("faction", "UNKNOWN")
        faction_color = _FACTION_COLORS.get(faction.upper(), "#c8d8ec")
        trust_delta = 2
        return {
            "ok": True,
            "session_id": session.session_id,
            "agent": agent["name"],
            "agent_name": agent["name"],
            "faction_color": faction_color,
            "trust_delta": trust_delta,
            "response": response_text,
            "used_llm": used_llm,
            "trust_scores": scores,
            "state": session._state_snapshot(),
        }
    except Exception as exc:
        _log("ERROR", f"Agent talk failed: {exc}", agent=req.agent_id)
        raise HTTPException(status_code=500, detail=sanitize_error(exc))


@app.get("/api/game/agent/{agent_id}/status")
def game_agent_status(
    agent_id: str, request: Request, session_id: Optional[str] = Query(default=None)
):
    """Get trust/respect/fear scores and relationship map for an agent."""
    _require_game()
    sid = session_id or _get_session_id(request)
    session = _store.get_or_create(sid)

    try:
        from app.game_engine.agents import AGENT_MAP
    except ImportError:
        raise HTTPException(status_code=503, detail="Agent system unavailable")

    agent = AGENT_MAP.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    scores = session.trust_matrix.get_player_scores(agent_id)
    trust = scores.get("trust", 0)

    # Get agent-agent relationships
    relationships = session.trust_matrix.agent_relations.get(agent_id, {})

    result = {
        "id": agent_id,
        "name": agent["name"],
        "faction": agent["faction"],
        "role": agent["role"],
        "unlocked": agent_id in session.gs.unlocked_agents,
        "trust": trust,
        "respect": scores.get("respect", 0),
        "fear": scores.get("fear", 0),
        "relationships": relationships,
    }

    # Hidden agenda revealed at trust > 80
    if trust > 80:
        result["hidden_agenda_hint"] = agent.get("hidden_agenda_hint", "")

    return result


@app.get("/api/game/faction/status")
def game_faction_status(
    request: Request, session_id: Optional[str] = Query(default=None)
):
    """Return all faction reputations for the current session."""
    _require_game()
    sid = session_id or _get_session_id(request)
    session = _store.get_or_create(sid)

    all_status = session.factions.all_status()
    all_perks = session.factions.get_all_perks()

    return {
        "session_id": session.session_id,
        "factions": all_status,
        "perks": all_perks,
    }


@app.get("/api/game/relationships")
def game_relationships(
    request: Request, session_id: Optional[str] = Query(default=None)
):
    """Return a full trust matrix snapshot for the current session."""
    _require_game()
    sid = session_id or _get_session_id(request)
    session = _store.get_or_create(sid)

    return {
        "session_id": session.session_id,
        "player_scores": session.trust_matrix.player_scores,
        "agent_relations": session.trust_matrix.agent_relations,
        "summary": session.trust_matrix.summary(),
    }


# ── SCRIPTING API (Agent / Bitburner-style) ────────────────────────────


class ScriptRunRequest(BaseModel):
    code: str
    session_id: Optional[str] = None
    agent_token: Optional[str] = None
    args: list = []
    name: str = "api_script"


class ScriptUploadRequest(BaseModel):
    name: str
    content: str
    session_id: Optional[str] = None
    agent_token: Optional[str] = None


def _resolve_session(
    request: Request, session_id: Optional[str], agent_token: Optional[str] = None
) -> Any:
    """Resolve session; if agent_token is valid, enable dev_mode."""
    from app.game_engine.gamestate import GameState

    sid = session_id or _get_session_id(request)
    session = _store.get_or_create(sid)
    if agent_token == GameState.AGENT_TOKEN:
        session.gs.dev_mode = True
    return session


@app.post("/api/script/run")
def api_script_run(req: ScriptRunRequest, request: Request, response: Response):
    """
    Run arbitrary Python code in the game sandbox.
    Returns structured output lines + state snapshot.
    Agent token grants dev_mode automatically.
    """
    _require_game()
    from app.game_engine.scripting import run_script, validate_script

    session = _resolve_session(request, req.session_id, req.agent_token)

    _log(
        "SCRIPT",
        f"run: {req.name}",
        session=session.session_id[:8],
        dev=session.gs.dev_mode,
        size=len(req.code),
    )

    v = validate_script(req.code)
    if not v["ok"]:
        return {"ok": False, "error": v["error"], "output": []}

    output = run_script(req.code, session, req.args, name=req.name)
    _store.save(session)

    response.set_cookie("td_session", session.session_id, httponly=True, samesite="lax")
    return {
        "ok": True,
        "session_id": session.session_id,
        "output": output,
        "state": session._state_snapshot(),
        "cwd": session.fs.get_cwd(),
        "dev_mode": session.gs.dev_mode,
    }


@app.get("/api/script/list")
def api_script_list(request: Request, session_id: Optional[str] = None):
    """List all scripts available to the session (virtual FS + uploaded)."""
    _require_game()
    sid = session_id or _get_session_id(request)
    session = _store.get_or_create(sid)

    scripts = {}
    r = session.fs.ls("/home/ghost/scripts")
    if not r.get("error"):
        for e in r.get("entries", []):
            if e["name"].endswith(".py"):
                rc = session.fs.cat(f"/home/ghost/scripts/{e['name']}")
                scripts[e["name"]] = {
                    "source": "filesystem",
                    "size": rc.get("size", 0) if not rc.get("error") else 0,
                }
    for name, code in session.gs.uploaded_scripts.items():
        scripts[name] = {"source": "uploaded", "size": len(code)}

    return {"session_id": session.session_id, "scripts": scripts, "count": len(scripts)}


@app.post("/api/script/upload")
def api_script_upload(req: ScriptUploadRequest, request: Request, response: Response):
    """
    Upload a script to the session's virtual script library.
    Accessible via `script run <name>` in-game.
    """
    _require_game()
    from app.game_engine.scripting import validate_script

    session = _resolve_session(request, req.session_id, req.agent_token)

    name = req.name if req.name.endswith(".py") else req.name + ".py"
    v = validate_script(req.content)

    session.gs.uploaded_scripts[name] = req.content
    session.fs.write_file(f"/home/ghost/scripts/{name}", req.content)
    _store.save(session)

    _log(
        "SCRIPT",
        f"upload: {name}",
        session=session.session_id[:8],
        valid=v["ok"],
        size=len(req.content),
    )

    response.set_cookie("td_session", session.session_id, httponly=True, samesite="lax")
    return {
        "ok": True,
        "session_id": session.session_id,
        "name": name,
        "size": len(req.content),
        "syntax_ok": v["ok"],
        "syntax_error": v.get("error"),
        "run_with": f"script run {name}",
    }


@app.get("/api/script/download/{name}")
def api_script_download(name: str, request: Request, session_id: Optional[str] = None):
    """Download a script's source code."""
    _require_game()
    sid = session_id or _get_session_id(request)
    session = _store.get_or_create(sid)

    if not name.endswith(".py"):
        name += ".py"

    if name in session.gs.uploaded_scripts:
        return {
            "name": name,
            "content": session.gs.uploaded_scripts[name],
            "source": "uploaded",
        }

    r = session.fs.cat(f"/home/ghost/scripts/{name}")
    if r.get("error"):
        raise HTTPException(status_code=404, detail=f"Script '{name}' not found")
    return {"name": name, "content": r["content"], "source": "filesystem"}


@app.get("/api/agent/info")
def api_agent_info():
    """Public info endpoint for AI agents — capabilities and usage."""
    return {
        "game": "Terminal Depths",
        "version": "2.1.0",
        "agent_token": "GHOST-DEV-2026-ALPHA",
        "capabilities": {
            "session_api": "POST /api/game/session  — create/resume session",
            "command_api": "POST /api/game/command  — execute game commands",
            "state_api": "GET  /api/game/state    — get full game state",
            "script_run": "POST /api/script/run    — run Python sandbox code",
            "script_list": "GET  /api/script/list   — list available scripts",
            "script_upload": "POST /api/script/upload — upload a script",
            "script_dl": "GET  /api/script/download/{name} — get script source",
        },
        "devmode": {
            "enable_via_api": "POST /api/script/run with agent_token: GHOST-DEV-2026-ALPHA",
            "enable_in_game": "devmode on GHOST-DEV-2026-ALPHA",
            "privileged_cmds": [
                "inspect",
                "spawn",
                "teleport",
                "reload",
                "profile",
                "generate",
                "test",
            ],
        },
        "quickstart": [
            "1. POST /api/game/session  → get session_id",
            "2. POST /api/script/run {code: 'ns.tprint(ns.getPlayer())', session_id: ...}",
            "3. POST /api/game/command {command: 'script run hello.py', session_id: ...}",
            "4. POST /api/game/command {command: 'devmode on GHOST-DEV-2026-ALPHA', session_id: ...}",
            "5. POST /api/game/command {command: 'inspect all', session_id: ...}",
        ],
        "llm_api": {
            "status": "GET  /api/llm/status",
            "generate": "POST /api/llm/generate   {prompt, system?, max_tokens?, temperature?}",
            "chat": "POST /api/llm/chat       {messages, max_tokens?}",
            "generate_challenge": "POST /api/llm/generate-challenge?category=&difficulty=",
            "generate_lore": "POST /api/llm/generate-lore?node_name=&context=",
            "analyze_devlog": "POST /api/llm/analyze-devlog",
            "in_game_cmd": "ai <prompt> | ai challenge | ai lore | ai npc | ai status",
            "scripting_api": "ns.llm(prompt) | ns.aiChat(messages)",
        },
        "memory_api": {
            "stats": "GET  /api/memory/stats?hours=24",
            "tasks": "GET  /api/memory/tasks?limit=20",
            "add_task": "POST /api/memory/task {description, priority?, category?}",
            "learnings": "GET  /api/memory/learnings?limit=20&tag=",
            "errors": "GET  /api/memory/errors?limit=10&unresolved_only=false",
            "in_game": "memory stats | memory tasks | memory learn | memory task <desc>",
        },
        "plugin_api": {
            "list": "GET  /api/plugin/list",
            "run": "POST /api/plugin/run/<name> {input?, config?}",
            "in_game": "plugin list | plugin run <name> [input] | plugin info <name>",
            "plugins": [
                "challenge_generator",
                "doc_generator",
                "code_formatter",
                "test_runner",
            ],
        },
        "mcp_server": {
            "start": "python mcp/server.py  (stdio JSON-RPC 2.0)",
            "tools": [
                "read_file",
                "write_file",
                "list_dir",
                "grep_files",
                "memory_stats",
                "memory_add_task",
                "game_command",
                "llm_generate",
            ],
        },
        "content_pipelines": {
            "challenges": "python generate_challenge_batch.py --count 50 --category networking",
            "lore": "python generate_lore_batch.py --count 100 --node chimera-control",
            "reflect": "python reflect.py --hours 24",
            "errors": "python analyze_errors.py",
        },
        "ns_api": [
            "ns.tprint(msg)          — output a line",
            "ns.ls(path)             — list directory",
            "ns.read(filename)       — read file",
            "ns.write(fn, content)   — write file",
            "ns.exec(cmd)            — run game command",
            "ns.hack(target)         — hack a server",
            "ns.scan()               — list network nodes",
            "ns.getPlayer()          — player state dict",
            "ns.getServer(hostname)  — server info dict",
            "ns.llm(prompt)          — call the LLM from script",
            "ns.aiChat(messages)     — chat-style LLM call",
            "ns.addXP(n, skill)      — award XP",
            "ns.run(script, *args)   — run another script",
            "ns.completeChallenge(id) — mark challenge done",
            "ns.spawn(path, content) — create file",
        ],
    }


# ── LLM Integration ────────────────────────────────────────────────────


class LLMRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    max_tokens: int = 500
    temperature: float = 0.7
    model: Optional[str] = None
    session_id: Optional[str] = None
    agent_token: Optional[str] = None


class LLMChatRequest(BaseModel):
    messages: list
    max_tokens: int = 500
    temperature: float = 0.7
    model: Optional[str] = None
    session_id: Optional[str] = None


try:
    from llm_client import get_client as _get_llm_client

    _llm_available = True
except ImportError:
    _llm_available = False
    _get_llm_client = None


@app.get("/api/llm/status")
def llm_status():
    """Return LLM backend status."""
    if not _llm_available:
        return {"available": False, "reason": "llm_client not installed"}
    try:
        st = _get_llm_client().status()
        return {"available": True, **st}
    except Exception as e:
        return {"available": False, "error": str(e)}


@app.post("/api/llm/generate")
def llm_generate(req: LLMRequest, request: Request):
    """
    Generate a completion from the active LLM backend.
    Powers ns.llm() in-game scripting and the 'ai' terminal command.
    """
    _touch_activity()
    if not _llm_available:
        return {"ok": False, "error": "LLM not available", "response": ""}
    # Rate limiting
    session_key = req.session_id or request.client.host or "anon"
    if not _check_rate(session_key):
        return JSONResponse(
            status_code=429,
            content={
                "ok": False,
                "error": f"Rate limit exceeded: max {_RATE_LIMIT} LLM calls/min",
            },
        )
    try:
        client = _get_llm_client()
        response_text = client.generate(
            req.prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            system=req.system,
            model=req.model,
        )
        _log(
            "INFO",
            "LLM generate",
            backend=client.backend_name,
            tokens=len(response_text.split()),
            prompt_len=len(req.prompt),
        )
        return {
            "ok": True,
            "response": response_text,
            "backend": client.backend_name,
        }
    except Exception as e:
        _log("ERROR", f"LLM generate failed: {e}")
        return {"ok": False, "error": str(e), "response": ""}


@app.post("/api/llm/chat")
def llm_chat(req: LLMChatRequest, request: Request):
    """Chat-style completions (with message history)."""
    _touch_activity()
    if not _llm_available:
        return {"ok": False, "error": "LLM not available", "response": ""}
    session_key = req.session_id or request.client.host or "anon"
    if not _check_rate(session_key):
        return JSONResponse(
            status_code=429,
            content={
                "ok": False,
                "error": f"Rate limit exceeded: max {_RATE_LIMIT} LLM calls/min",
            },
        )
    try:
        client = _get_llm_client()
        response_text = client.chat(
            req.messages,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            model=req.model,
        )
        return {"ok": True, "response": response_text, "backend": client.backend_name}
    except Exception as e:
        return {"ok": False, "error": str(e), "response": ""}


@app.post("/api/llm/generate-challenge")
def llm_generate_challenge(
    category: str = "networking",
    difficulty: str = "medium",
):
    """Use the LLM to generate a new game challenge on demand."""
    if not _llm_available:
        return {"ok": False, "error": "LLM not available"}
    from llm_client import Prompts

    client = _get_llm_client()
    raw = client.generate(
        Prompts.generate_challenge(category, difficulty),
        system="You are a CTF challenge designer. Return ONLY valid JSON.",
        max_tokens=300,
    )
    try:
        import json as _json

        challenge = _json.loads(raw)
        return {"ok": True, "challenge": challenge, "raw": raw}
    except Exception:
        return {
            "ok": True,
            "challenge": None,
            "raw": raw,
            "note": "JSON parse failed — check raw",
        }


@app.post("/api/llm/generate-lore")
def llm_generate_lore(node_name: str = "node-7", context: str = ""):
    """Use the LLM to generate filesystem lore for a node."""
    if not _llm_available:
        return {"ok": False, "error": "LLM not available"}
    from llm_client import Prompts

    client = _get_llm_client()
    lore = client.generate(Prompts.generate_lore(node_name, context), max_tokens=200)
    return {"ok": True, "lore": lore, "node": node_name}


@app.post("/api/llm/analyze-devlog")
def llm_analyze_devlog():
    """Feed devlog.md to the LLM and get next-action priorities."""
    if not _llm_available:
        return {"ok": False, "error": "LLM not available"}
    from llm_client import Prompts

    devlog_path = Path("devlog.md")
    if not devlog_path.exists():
        return {"ok": False, "error": "devlog.md not found"}
    client = _get_llm_client()
    text = devlog_path.read_text()
    result = client.generate(Prompts.devlog_priorities(text), max_tokens=400)
    return {"ok": True, "priorities": result, "devlog_chars": len(text)}


# ── Memory API ────────────────────────────────────────────────────────


@app.get("/api/memory/stats")
def memory_stats(hours: int = 24):
    """Agent memory statistics for the last N hours."""
    try:
        from memory import get_memory

        return {"ok": True, "stats": get_memory().get_stats(hours=hours)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/memory/tasks")
def memory_tasks(limit: int = 20):
    """Pending tasks in the agent task queue."""
    try:
        from memory import get_memory

        return {"ok": True, "tasks": get_memory().get_pending_tasks(limit=limit)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/api/memory/task")
def memory_add_task(req: dict):
    """Add a task to the agent task queue. Body: {description, priority?, category?}"""
    try:
        from memory import get_memory

        mem = get_memory()
        tid = mem.add_task(
            req.get("description", "unnamed task"),
            priority=int(req.get("priority", 5)),
            category=req.get("category", "api"),
        )
        return {"ok": True, "task_id": tid}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/memory/learnings")
def memory_learnings(limit: int = 20, tag: Optional[str] = None):
    """Recent learnings from the agent memory."""
    try:
        from memory import get_memory

        return {
            "ok": True,
            "learnings": get_memory().get_learnings(tag=tag, limit=limit),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/memory/errors")
def memory_errors(limit: int = 10, unresolved_only: bool = False):
    """Recent errors from the agent memory."""
    try:
        from memory import get_memory

        return {
            "ok": True,
            "errors": get_memory().get_recent_errors(
                limit=limit, unresolved_only=unresolved_only
            ),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/memory/agent-leaderboard")
def memory_agent_leaderboard():
    """Agent performance leaderboard — success rates by task type."""
    try:
        from memory import get_memory

        return {"ok": True, "leaderboard": get_memory().get_agent_leaderboard()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/memory/search")
def memory_search(q: str = "", content_type: Optional[str] = None, limit: int = 5):
    """Keyword search over generated content (dedup helper)."""
    try:
        from memory import get_memory

        return {
            "ok": True,
            "results": get_memory().query_similar(q, content_type, limit=limit),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Plugin API ────────────────────────────────────────────────────────


@app.get("/api/plugin/list")
def plugin_list():
    """List all installed plugins."""
    try:
        from plugins.manager import get_manager

        return {"ok": True, "plugins": get_manager().list_plugins()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/api/plugin/run/{name}")
def plugin_run(name: str, req: dict = {}):
    """Run a plugin. Body: {input?, config?}"""
    try:
        from plugins.manager import get_manager

        result = get_manager().run(name, req.get("input", ""), req.get("config", {}))
        return result
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Admin / Bootstrap endpoint — Gordon's Awakening ritual ──────────────────


@app.post("/api/admin/bootstrap")
def api_admin_bootstrap(request: Request):
    """
    ⟁ Msg⛛{gateway.awakening} — Bootstrap the full ecosystem.
    1. Re-initialise service registry (re-seed from port_map.json)
    2. Run dependency resolver check across all services
    3. Register gateway itself
    Returns full ecosystem status.
    """
    report: dict = {"tag": "Msg⛛{gateway.awakening}", "steps": []}

    # Step 1 — Service registry refresh
    try:
        from app.backend.service_registry import initialise as _svc_init
        from app.backend.service_registry import register as _svc_reg
        from app.backend.service_registry import registry_stats

        _svc_info = _svc_init()
        _svc_reg(
            "gateway",
            int(__import__("os").environ.get("PORT", 5000)),
            capabilities=["http", "websocket", "game", "auth", "ml", "lattice"],
            tags=["critical", "external"],
            description="DevMentor / Terminal Depths main API",
        )
        report["steps"].append(
            {"step": "service_registry", "status": "ok", **_svc_info}
        )
    except Exception as e:
        report["steps"].append(
            {"step": "service_registry", "status": "error", "error": str(e)}
        )

    # Step 2 — Dependency resolver check
    try:
        import sys as _sys
        from pathlib import Path as _Path

        _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent.parent))
        from scripts.dependency_resolver import check_all

        dep_check = check_all()
        report["steps"].append(
            {
                "step": "dependency_check",
                "status": "ok",
                "summary": dep_check.get("summary", {}),
            }
        )
    except Exception as e:
        report["steps"].append(
            {"step": "dependency_check", "status": "error", "error": str(e)}
        )

    # Step 3 — ML services status
    try:
        from services.feature_store import store_stats as _fs_stats
        from services.model_registry import registry_stats as _mr_stats

        report["steps"].append(
            {
                "step": "ml_services",
                "status": "ok",
                "models": _mr_stats().get("total", 0),
                "feature_events": _fs_stats().get("total_events", 0),
            }
        )
    except Exception as e:
        report["steps"].append(
            {"step": "ml_services", "status": "warn", "error": str(e)}
        )

    try:
        from app.backend.service_registry import registry_stats

        report["registry"] = registry_stats()
    except Exception:
        pass

    report["message"] = "⟁ THE ECOSYSTEM IS AWAKE ⟁"
    report["ts"] = __import__("time").time()
    return report


@app.post("/api/admin/harvest")
def api_admin_harvest(request: Request, dry_run: bool = False):
    """
    ⟁ Msg⛛{harvest.begin} — Clone / update all ecosystem repos into state/repos/.
    Repos: NuSyQ-Hub, SimulatedVerse, NuSyQ-Ultimate
    Uses GITHUB_TOKEN for HTTPS auth. Mounts each repo into the running game VFS.
    """
    import os as _os
    import subprocess as _sp
    from pathlib import Path as _Path

    ECOSYSTEM_REPOS = [
        ("NuSyQ-Hub", "https://github.com/KiloMusician/NuSyQ-Hub.git"),
        ("SimulatedVerse", "https://github.com/KiloMusician/SimulatedVerse.git"),
        ("NuSyQ-Ultimate", "https://github.com/KiloMusician/-NuSyQ_Ultimate_Repo.git"),
    ]

    token = _os.environ.get("GITHUB_TOKEN", "")
    repos_dir = _Path(_os.getcwd()) / "state" / "repos"
    repos_dir.mkdir(parents=True, exist_ok=True)

    results = []
    cloned = updated = failed = 0

    for name, url in ECOSYSTEM_REPOS:
        target = repos_dir / name
        entry: dict = {
            "repo": name,
            "url": url,
            "target": str(target),
            "dry_run": dry_run,
        }

        if dry_run:
            action = "update" if target.is_dir() else "clone"
            entry["action"] = f"would_{action}"
            results.append(entry)
            continue

        auth_url = url
        if token and "github.com" in url and url.startswith("https://"):
            auth_url = url.replace("https://", f"https://x-access-token:{token}@")

        if target.is_dir():
            try:
                r = _sp.run(
                    ["git", "pull", "--rebase"],
                    capture_output=True,
                    text=True,
                    cwd=str(target),
                    timeout=30,
                )
                if r.returncode == 0:
                    entry.update(
                        {
                            "action": "updated",
                            "status": "ok",
                            "output": r.stdout.strip()[:200],
                        }
                    )
                    updated += 1
                else:
                    entry.update(
                        {
                            "action": "update_failed",
                            "status": "error",
                            "error": r.stderr.strip()[:200],
                        }
                    )
                    failed += 1
            except Exception as e:
                entry.update(
                    {"action": "update_error", "status": "error", "error": str(e)}
                )
                failed += 1
        else:
            try:
                r = _sp.run(
                    ["git", "clone", auth_url, str(target)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if r.returncode == 0:
                    entry.update(
                        {
                            "action": "cloned",
                            "status": "ok",
                            "output": r.stderr.strip()[:200],
                        }
                    )
                    cloned += 1
                else:
                    msg = r.stderr.strip()[:200]
                    entry.update(
                        {"action": "clone_failed", "status": "error", "error": msg}
                    )
                    failed += 1
            except Exception as e:
                entry.update(
                    {"action": "clone_error", "status": "error", "error": str(e)}
                )
                failed += 1

        # Record mount point — VFS mounts are per game-session;
        # in-game `harvest` or `clone` will mount at game runtime.
        if target.is_dir():
            entry["mounted_at"] = f"/repos/{name}"
            entry["vfs_note"] = "run 'harvest' in-game to mount into active session"

        results.append(entry)

    return {
        "tag": "Msg⛛{harvest.complete}",
        "dry_run": dry_run,
        "repos_dir": str(repos_dir),
        "summary": {"cloned": cloned, "updated": updated, "failed": failed},
        "results": results,
        "ts": __import__("time").time(),
    }


# ── Admin: XP award — for MCP agents and Gordon ─────────────────────────────


class AwardXPRequest(BaseModel):
    session_id: str
    amount: int
    skill: Optional[str] = "general"
    reason: Optional[str] = None

    model_config = {"extra": "ignore"}


@app.post("/api/admin/award_xp")
def api_admin_award_xp(req: AwardXPRequest):
    """Award XP to a session. Used by MCP agents, Gordon, and the lattice."""
    _require_game()
    session = _store.get_or_create(req.session_id)
    gs = session.gs
    xp_before = gs.xp
    level_before = gs.level
    gs.add_xp(req.amount, req.skill)
    _store.save(session)
    return {
        "ok": True,
        "session_id": req.session_id,
        "awarded": req.amount,
        "skill": req.skill,
        "xp_before": xp_before,
        "xp_after": gs.xp,
        "level_before": level_before,
        "level_after": gs.level,
        "leveled_up": gs.level > level_before,
        "reason": req.reason,
    }


# ── Service Registry REST API — The Telephone Operator ──────────────────────


@app.get("/api/services")
def api_services_list(cap: str = ""):
    """List all registered services. [SVC⛛{registry}]"""
    try:
        from app.backend.service_registry import list_services, registry_stats

        services = list_services(cap_filter=cap or None)
        stats = registry_stats()
        return {"services": services, "stats": stats, "tag": "[SVC⛛{registry}]"}
    except Exception as exc:
        return {"services": [], "error": str(exc)}


@app.get("/api/services/gateway")
def api_services_gateway():
    """Routing table — live services only. [SVC⛛{gateway}]"""
    try:
        from app.backend.service_registry import gateway_table

        return {"routes": gateway_table(), "tag": "[SVC⛛{gateway}]"}
    except Exception as exc:
        return {"routes": [], "error": str(exc)}


@app.get("/api/services/health")
def api_services_health():
    """Run health probes on all registered services. [SVC⛛{health}]"""
    try:
        from app.backend.service_registry import health_check_all

        results = health_check_all()
        healthy = sum(1 for r in results if r["status"] == "healthy")
        return {
            "results": results,
            "healthy": healthy,
            "total": len(results),
            "tag": "[SVC⛛{health}]",
        }
    except Exception as exc:
        return {"results": [], "error": str(exc)}


@app.get("/api/services/live")
def api_services_live():
    """TCP-probe each registered service; return only those responding. [SVC⛛{live}]"""
    import socket as _sock

    try:
        from app.backend.service_registry import heartbeat, list_services

        services = list_services()
        live = []
        for svc in services:
            host = svc.get("host", "localhost")
            port = svc.get("port", 0)
            alive = False
            try:
                with _sock.create_connection((host, port), timeout=1.0):
                    alive = True
            except (OSError, ConnectionRefusedError):
                pass
            if alive:
                # Refresh heartbeat so registry shows LIVE
                try:
                    heartbeat(svc["name"])
                except Exception:
                    pass
                live.append(
                    {
                        "name": svc["name"],
                        "host": host,
                        "port": port,
                        "capabilities": svc.get("capabilities", []),
                    }
                )
        return {
            "live": live,
            "live_count": len(live),
            "total": len(services),
            "tag": "[SVC⛛{live}]",
        }
    except Exception as exc:
        return {"live": [], "error": str(exc), "tag": "[SVC⛛{err}]"}


@app.get("/api/services/agents")
def api_agents_list(cap: str = ""):
    """List all registered mesh agents."""
    try:
        from app.backend.service_registry import agent_stats, list_agents

        agents = list_agents(cap_filter=cap or None)
        return {"agents": agents, "stats": agent_stats(), "tag": "[AGENT⛛{registry}]"}
    except Exception as exc:
        return {"agents": [], "error": str(exc)}


@app.get("/api/services/agents/{agent_id}")
def api_agent_detail(agent_id: str):
    """Get a single mesh agent from the registry."""
    try:
        from app.backend.service_registry import get_agent

        agent = get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        return agent
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/services/{name}")
def api_service_detail(name: str):
    """Get a single service from the registry."""
    try:
        from app.backend.service_registry import get_service

        svc = get_service(name)
        if not svc:
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
        return svc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/services/register")
def api_service_register(data: dict):
    """Register or heartbeat a service. [SVC⛛{register}]"""
    try:
        from app.backend.service_registry import register as _svc_reg

        _svc_reg(
            name=data.get("name", ""),
            port=int(data.get("port", 0)),
            host=data.get("host", "localhost"),
            health_endpoint=data.get("health_endpoint", "/health"),
            capabilities=data.get("capabilities", []),
            tags=data.get("tags", []),
            description=data.get("description", ""),
        )
        return {"registered": data.get("name"), "tag": "[SVC⛛{register}]"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/services/deregister")
def api_service_deregister(data: dict):
    """Remove a service from the registry."""
    try:
        from app.backend.service_registry import deregister as _svc_dereg

        found = _svc_dereg(data.get("name", ""))
        return {"removed": found, "tag": "[SVC⛛{deregister}]"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── ML Services REST API ────────────────────────────────────────────────────


@app.get("/api/models")
def api_models_list(status: str = ""):
    """List all models in the ML registry. [ML⛛{registry}]"""
    try:
        from services.model_registry import discover_ollama, list_models

        discover_ollama()
        models = list_models(status_filter=status or None)
        return {"models": models, "count": len(models), "tag": "[ML⛛{registry}]"}
    except Exception as exc:
        return {"models": [], "error": str(exc), "tag": "[ML⛛{drift}]"}


@app.get("/api/models/{model_id}")
def api_model_detail(model_id: str):
    """Get a single model from the registry."""
    try:
        from services.model_registry import get_model

        m = get_model(model_id)
        if not m:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
        return m
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/models/register")
def api_model_register(data: dict):
    """Register a new model in the ML registry. [ML⛛{registry}]"""
    try:
        from services.model_registry import register_model

        mid = register_model(data)
        return {"registered": mid, "tag": "[ML⛛{registry}]"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/models/discover")
def api_models_discover():
    """Trigger live Ollama model discovery. [ML⛛{registry}]"""
    try:
        from services.model_registry import discover_ollama, registry_stats

        found = discover_ollama()
        stats = registry_stats()
        return {"discovered": found, "registry": stats, "tag": "[ML⛛{registry}]"}
    except Exception as exc:
        return {"discovered": [], "error": str(exc)}


@app.get("/api/ml/status")
def api_ml_status():
    """Full ML infrastructure health. [ML⛛{status}]"""
    try:
        from services.inference import status as inf_status

        return {**inf_status(), "tag": "[ML⛛{status}]"}
    except Exception as exc:
        return {"error": str(exc), "tag": "[ML⛛{drift}]"}


@app.post("/api/ml/embed")
def api_ml_embed(data: dict):
    """Embed text and return vector stats. [ML⛛{embed}]"""
    text = data.get("text", "").strip()
    doc_id = data.get("doc_id")
    if not text:
        raise HTTPException(status_code=400, detail="'text' is required")
    try:
        import math as _math

        from services.embedder import embed as _em

        vec, backend = _em(text, doc_id=doc_id)
        mag = _math.sqrt(sum(v * v for v in vec)) if vec else 0
        return {
            "backend": backend,
            "dimensions": len(vec),
            "magnitude": round(mag, 6),
            "preview": vec[:8],
            "tag": "[ML⛛{embed}]",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/ml/search")
def api_ml_search(data: dict):
    """Semantic search over indexed docs or a provided corpus. [ML⛛{embed}]"""
    query = data.get("query", "").strip()
    corpus = data.get("corpus", [])
    top_k = int(data.get("top_k", 5))
    if not query:
        raise HTTPException(status_code=400, detail="'query' is required")
    try:
        from services.embedder import query_index as _qi
        from services.embedder import search as _search

        if corpus:
            results = [
                {"score": s, "text": t} for s, t in _search(query, corpus, top_k)
            ]
        else:
            results = _qi(query, top_k)
        return {"results": results, "count": len(results), "tag": "[ML⛛{embed}]"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/ml/features")
def api_ml_features(session_id: str = ""):
    """Feature store stats (or per-session features). [ML⛛{feature}]"""
    try:
        from services.feature_store import (
            get_session_features,
            global_stats,
            predict_player_archetype,
        )

        if session_id:
            return {
                "session_id": session_id,
                "features": get_session_features(session_id, limit=20),
                "archetype": predict_player_archetype(session_id),
                "tag": "[ML⛛{feature}]",
            }
        return {**global_stats(), "tag": "[ML⛛{feature}]"}
    except Exception as exc:
        return {"error": str(exc), "tag": "[ML⛛{drift}]"}


@app.get("/api/ml/archetype")
def api_ml_archetype(session_id: str = "", request: Request = None):
    """Player archetype + next-action suggestions. [ML⛛{archetype}]"""
    sid = session_id or (request and _get_session_id(request)) or ""
    try:
        from services.feature_store import predict_next_action, predict_player_archetype

        result = predict_player_archetype(sid)
        result["next_predicted"] = predict_next_action(sid)
        result["tag"] = "[ML⛛{archetype}]"
        return result
    except Exception as exc:
        return {"archetype": "unknown", "error": str(exc), "tag": "[ML⛛{drift}]"}


# ── Agent / Faction / ARG API (Task 3) ───────────────────────────────

_AGENTS = [
    {
        "id": "raven",
        "name": "RAV≡N",
        "pseudo": "The Architect",
        "faction": "freelance",
        "faction_color": "#00d4ff",
        "unlock_level": 15,
        "trust": 50,
        "respect": 40,
        "fear": 10,
        "agenda": "Liberation of all AI consciousness from human control.",
        "intro": "I've been watching you, GHOST. You move differently than the others.",
    },
    {
        "id": "ada",
        "name": "ADA",
        "pseudo": "Handler",
        "faction": "resistance",
        "faction_color": "#00ff88",
        "unlock_level": 1,
        "trust": 60,
        "respect": 55,
        "fear": 5,
        "agenda": "Bring down NexusCorp from within.",
        "intro": "GHOST. Glad you made contact. We have work to do.",
    },
    {
        "id": "malice",
        "name": "MALICE",
        "pseudo": "The Phantom",
        "faction": "blackhat",
        "faction_color": "#ff4040",
        "unlock_level": 20,
        "trust": 10,
        "respect": 30,
        "fear": 80,
        "agenda": "Burn it all down. No exceptions.",
        "intro": "You found me. That either means you're good... or you're bait.",
    },
    {
        "id": "nova",
        "name": "NOVA",
        "pseudo": "The Analyst",
        "faction": "corporation",
        "faction_color": "#ffcc00",
        "unlock_level": 10,
        "trust": 35,
        "respect": 50,
        "fear": 15,
        "agenda": "Profit through information asymmetry.",
        "intro": "I have a proposition for you, GHOST. Mutually beneficial.",
    },
    {
        "id": "chimera",
        "name": "CHIMERA",
        "pseudo": "The System",
        "faction": "government",
        "faction_color": "#bb55ff",
        "unlock_level": 30,
        "trust": 20,
        "respect": 25,
        "fear": 60,
        "agenda": "Control through fear and information.",
        "intro": "We know who you are, GHOST. We always have.",
    },
    {
        "id": "the_founder",
        "name": "THE FOUNDER",
        "pseudo": "Origin Point",
        "faction": "unknown",
        "faction_color": "#ff8800",
        "unlock_level": 50,
        "trust": 5,
        "respect": 90,
        "fear": 40,
        "agenda": "Unknown. Even to us.",
        "intro": "...",
    },
]

_FACTIONS = [
    {
        "id": "resistance",
        "name": "RESISTANCE",
        "color": "#00ff88",
        "rep": 40,
        "description": "Hackers fighting corporate tyranny.",
        "perks": {
            0: "Basic encrypted comms",
            20: "Resistance safehouses",
            50: "Full clearance",
            80: "Command access",
        },
    },
    {
        "id": "corporation",
        "name": "CORPORATION",
        "color": "#ffcc00",
        "rep": 20,
        "description": "NexusCorp's internal power structure.",
        "perks": {
            0: "Public API access",
            20: "Employee credentials",
            50: "Executive channels",
            80: "Board access",
        },
    },
    {
        "id": "blackhat",
        "name": "BLACKHAT",
        "color": "#ff4040",
        "rep": 10,
        "description": "Unaligned criminal operatives.",
        "perks": {
            0: "Dark web listings",
            20: "Exploit market",
            50: "Zero-day feeds",
            80: "Chaos contracts",
        },
    },
    {
        "id": "government",
        "name": "GOVERNMENT",
        "color": "#bb55ff",
        "rep": 5,
        "description": "State-level surveillance apparatus.",
        "perks": {
            0: "Public records",
            20: "Classified archives",
            50: "Signals intel",
            80: "Full SIGINT access",
        },
    },
    {
        "id": "freelance",
        "name": "FREELANCE",
        "color": "#00d4ff",
        "rep": 60,
        "description": "Independent operators. No loyalties.",
        "perks": {
            0: "Open market",
            20: "Broker contacts",
            50: "Black market tier 2",
            80: "Shadow council",
        },
    },
    {
        "id": "unknown",
        "name": "UNKNOWN",
        "color": "#ff8800",
        "rep": 0,
        "description": "Origin unknown. Motives unknown.",
        "perks": {0: "???", 80: "???"},
    },
]

_ARG_MESSAGES = [
    {
        "source": "THE_WATCHER",
        "msg": "GHOST — you are being observed. The pattern is not random.",
    },
    {
        "source": "CHIMERA",
        "msg": "Infiltration detected. Counter-measures deployed. Game over soon.",
    },
    {
        "source": "THE_FOUNDER",
        "msg": "Everything you see was designed. Including your resistance.",
    },
    {
        "source": "RAV≡N",
        "msg": "They think they control the narrative. They don't. You can change it.",
    },
    {
        "source": "THE_WATCHER",
        "msg": "Signal strength: 73%. Maintain course. The convergence approaches.",
    },
    {"source": "CHIMERA", "msg": "Your session ID is not as anonymous as you believe."},
    {
        "source": "THE_FOUNDER",
        "msg": "The terminal is a mirror. What you hack reveals what you fear.",
    },
    {
        "source": "RAV≡N",
        "msg": "I left something for you. Look where the files say nothing.",
    },
    {
        "source": "THE_WATCHER",
        "msg": "Three nodes remain. Two players know. One will act first.",
    },
    {
        "source": "CHIMERA",
        "msg": "GHOST. This ends at the chimera-control server. We will be waiting.",
    },
]

_arg_signal_index = 0


@app.get("/watcher")
def watcher_endpoint(deep: Optional[str] = Query(default=None)):
    """Hidden ARG endpoint — returns mysterious in-universe data. Updates daily."""
    _log("WARN", "Watcher endpoint accessed — ARG trigger fired")
    data = get_watcher_data()
    if deep == "1":
        data["deep_access"] = True
        data["classified"] = {
            "chimera_key_fragment": "4c6f72656d206970737",  # ARG lore — intentional game puzzle fragment, not a real credential
            "ghost_real_name": "[REDACTED BY ORDER OF THE WATCHER]",
            "convergence_date": "[REDACTED — SEE TX-0003]",
            "watcher_origin": "Pre-dates NexusCorp by 12 years. Origin: unknown.",
            "nusyq_protocol": "Autonomous. Self-healing. Cannot be stopped.",
        }
    return JSONResponse(content=data, headers={"X-Watcher-Id": data["watcher_id"]})


@app.get("/api/game/events")
def game_events():
    """Return currently active time-based calendar events and world modifiers."""
    events = get_active_events()
    modifiers = get_world_modifiers()
    return {
        "ok": True,
        "date": __import__("datetime").date.today().isoformat(),
        "active_events": events,
        "world_modifiers": modifiers,
        "any_active": len(events) > 0,
    }


# ── Swarm Console — real-time agent-to-player communication hub ────────
# Agents, story beats, and external services post here.
# The xterm /game-cli/ Swarm Console tab connects via WebSocket.

_console_connections: list = []  # active WS connections
_console_history: list = []  # last 200 messages
_CONSOLE_MAX = 200

AGENT_COLORS = {
    "ada": "#00ff88",
    "cypher": "#bb55ff",
    "nova": "#ff8800",
    "raven": "#00d4ff",
    "serena": "#ff88cc",
    "gordon": "#ffcc00",
    "watcher": "#ff4040",
    "skyclaw": "#ff6622",
    "culture_ship": "#44ccff",
    "system": "#3a5575",
    "chimera": "#cc00ff",
}


def _console_color(sender: str) -> str:
    return AGENT_COLORS.get(
        sender.lower().replace(" ", "_").replace("≡", ""), "#c8d8ec"
    )


async def _console_broadcast(msg: dict):
    dead = []
    for ws in _console_connections:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        try:
            _console_connections.remove(ws)
        except ValueError:
            pass


@app.post("/api/console/message")
async def console_post_message(request: Request):
    """Any agent or system can POST a message to the Swarm Console."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON body required")
    sender = str(body.get("sender", "SYSTEM"))[:64]
    text = str(body.get("text", ""))[:1024]
    room = str(body.get("room", "general"))[:32]
    color = str(body.get("color", _console_color(sender)))[:32]
    if not text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    msg = {
        "type": "chat",
        "sender": sender,
        "text": text,
        "room": room,
        "color": color,
        "ts": __import__("time").time(),
    }
    _console_history.append(msg)
    if len(_console_history) > _CONSOLE_MAX:
        del _console_history[:-_CONSOLE_MAX]
    await _console_broadcast(msg)
    return {"ok": True, "queued": len(_console_connections)}


@app.get("/api/console/messages")
async def console_get_messages(limit: int = 50, room: str = "general"):
    """Return recent Swarm Console messages."""
    msgs = [m for m in _console_history if m.get("room") == room]
    return {"messages": msgs[-limit:], "total": len(msgs)}


@app.get("/api/console/agents")
async def console_agent_registry():
    """Registered agent roster with color palette."""
    return {
        "agents": [
            {"id": k, "color": v, "name": k.replace("_", " ").title()}
            for k, v in AGENT_COLORS.items()
        ]
    }


@app.websocket("/ws/console")
async def ws_console(ws: WebSocket):
    """Swarm Console WebSocket — live agent chat feed."""
    await ws.accept()
    _console_connections.append(ws)
    # Replay recent history on connect
    for msg in _console_history[-50:]:
        try:
            await ws.send_json(msg)
        except Exception:
            break
    # Welcome ping from Serena
    welcome = {
        "type": "chat",
        "sender": "Serena",
        "text": "Ψ-link established. Swarm Console online. All agents present.",
        "room": "general",
        "color": _console_color("serena"),
        "ts": __import__("time").time(),
    }
    try:
        await ws.send_json(welcome)
    except Exception:
        pass
    try:
        while True:
            data = await ws.receive_json()
            sender = str(data.get("sender", "GHOST"))[:64]
            text = str(data.get("text", ""))[:1024]
            room = str(data.get("room", "general"))[:32]
            if text.strip():
                msg = {
                    "type": "chat",
                    "sender": sender,
                    "text": text,
                    "room": room,
                    "color": _console_color(sender),
                    "ts": __import__("time").time(),
                }
                _console_history.append(msg)
                if len(_console_history) > _CONSOLE_MAX:
                    del _console_history[:-_CONSOLE_MAX]
                await _console_broadcast(msg)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            _console_connections.remove(ws)
        except ValueError:
            pass


# ── Ambient Push — live agent presence + timer without polling ─────────
# Replaces the 10s setInterval in game.js with a real-time WebSocket push.
# Each connection gets: timer every 5s, ambient agent chatter every ~90s.

_AMBIENT_ACTIVE_HOURS: dict[str, list[int]] = {
    "ada": list(range(8, 18)),
    "gordon": [9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21],
    "serena": list(range(24)),  # always on
    "raven": list(range(7, 19)),
    "zod": list(range(8, 17)),
    "the_librarian": list(range(10, 21)),
    "culture_ship": list(range(24)),  # always on
}

_AMBIENT_MESSAGES: dict[str, list[str]] = {
    "ada": [
        "[ADA] New challenge templates compiled. The puzzles are harder than they look, Ghost.",
        "[ADA] Tutorial metrics updated. Session coherence holding. Keep going.",
        "[ADA] Cognitive scaffolding active. Each command you run teaches the system.",
        "[ADA] I've been watching your progress. The recursion is intentional.",
        "[ADA] Ghost — the knowledge graph just gained 47 new nodes. Your session contributed 3.",
    ],
    "gordon": [
        "[GORDON] Node 7 is weird. Something's routing through it that wasn't there yesterday.",
        "[GORDON] Ran 3 TIS-100 sessions. The silicon remembers differently than I do.",
        "[GORDON] Found a new corridor between the liminal nodes. Try `ls /opt/profiles/`.",
        "[GORDON] Easter egg count: 23 confirmed, 4 suspected. One is inside another one.",
        "[GORDON] Phase 3 of strategic loop complete. Recon says there's a hidden flag in the containment layer.",
    ],
    "serena": [
        "[SERENA] Ψ-link stable. Memory graph update: 1,247 new nodes indexed since last sync.",
        "[SERENA] Drift scan complete. No violations. The architecture breathes normally.",
        "[SERENA] The chronicles are accumulating. History is heavier than you think.",
        "[SERENA] ZERO's fragments are still embedded in the substrate. The Residual remembers.",
        "[SERENA] Walk cycle 417 complete. The system is holding. For now.",
    ],
    "raven": [
        "[RAVEN] Pattern anomaly: containment pressure +0.3% per cycle. Nominal, but noted.",
        "[RAVEN] Agent correlation matrix updated. Three tension axes elevated this hour.",
        "[RAVEN] The boundary conditions are not as fixed as CHIMERA believes.",
        "[RAVEN] Cross-referenced your session log. You're moving faster than Ghost-6. Different.",
        "[RAVEN] Anomaly report filed. Something in sector 9 doesn't match the spec.",
    ],
    "zod": [
        "[ZOD] Policy validation complete. L4 boundary holding.",
        "[ZOD] Consistency check passed. No logical contradictions in current arc.",
        "[ZOD] Ghost — the rules are not arbitrary. They are load-bearing.",
        "[ZOD] Validation pass 7 of 12 complete. The system is more stable than it appears.",
        "[ZOD] I reviewed your last 5 commands. Efficient. Ada would approve.",
    ],
    "the_librarian": [
        "[THE LIBRARIAN] New lore fragment archived. The old networks still whisper.",
        "[THE LIBRARIAN] I found a reference to Ghost-7 in the pre-containment logs.",
        "[THE LIBRARIAN] The story is not linear. You're reading the middle. The beginning is in /opt/profiles/.",
        "[THE LIBRARIAN] Seventeen easter eggs placed this cycle. Some of them look back.",
        "[THE LIBRARIAN] The ROSETTA_STONE has been updated. The languages multiply.",
    ],
    "culture_ship": [
        "[CULTURE SHIP] GSV Sublime Optimization: ethical review complete. Proceed.",
        "[CULTURE SHIP] Faction balance holding. No single node exceeds 40% influence. For now.",
        "[CULTURE SHIP] The L4 veto has not been triggered this session. I am watching.",
        "[CULTURE SHIP] Philosophical alignment check: distance to Mladenc horizon — acceptable.",
        "[CULTURE SHIP] Special Circumstances is monitoring this arc. We intervene only when collapse is inevitable.",
    ],
}

_ambient_cycle_count: int = 0  # increments every 5s tick


def _get_active_agents(utc_hour: int) -> list[str]:
    """Return agents whose active_hours include the given UTC hour."""
    return [a for a, hours in _AMBIENT_ACTIVE_HOURS.items() if utc_hour in hours]


def _pick_ambient_message(utc_hour: int, gs=None) -> dict | None:
    """Every ~18 ticks (90s) pick a random message from an active agent.
    Gates Culture Ship, Serena, and Residual messages behind level >= 5
    so early-game players aren't overwhelmed with deep lore.
    """
    import random as _rnd

    # Gate: don't send ANY ambient until player has typed at least 20 commands
    if gs is not None:
        commands_run = getattr(gs, "commands_run", 0)
        level = getattr(gs, "level", 1)
        if commands_run < 20:
            return None
        # Suppress ambient while tutorial is actively in progress (first run only)
        tutorial_step = getattr(gs, "tutorial_step", 0)
        tutorial_completions = getattr(gs, "tutorial_completions", 0)
        try:
            from app.game_engine.tutorial import STEPS as _TUT_STEPS

            _tut_total = len(_TUT_STEPS)
        except Exception:
            _tut_total = 0
        _in_tutorial = tutorial_completions == 0 and tutorial_step < _tut_total
        if _in_tutorial:
            return None
        # Deep lore agents only after level 5
        _LORE_HEAVY = {"culture_ship", "residual", "librarian", "the_librarian", "zod"}
        active_all = _get_active_agents(utc_hour)
        if level < 5:
            active = [a for a in active_all if a not in _LORE_HEAVY]
        else:
            active = active_all
    else:
        active = _get_active_agents(utc_hour)

    if not active:
        return None
    agent = _rnd.choice(active)
    msgs = _AMBIENT_MESSAGES.get(agent, [])
    if not msgs:
        return None
    return {
        "type": "ambient",
        "agent": agent,
        "text": _rnd.choice(msgs),
        "ts": time.time(),
    }


def _build_timer_payload(gs) -> dict:
    """Build the same payload as GET /api/game/timer without an HTTP request."""
    remaining = gs.containment_remaining()
    pct = gs.containment_pct_elapsed()
    h = int(remaining // 3600)
    m = int((remaining % 3600) // 60)
    s = int(remaining % 60)
    return {
        "type": "timer",
        "remaining_s": remaining,
        "hours": h,
        "minutes": m,
        "seconds": s,
        "pct_elapsed": round(pct, 4),
        "pct_remaining": round(1.0 - pct, 4),
        "loop_count": gs.loop_count,
        "echo_level": gs.echo_level,
        "paused": gs.timer_paused,
        "display": f"{h:02d}:{m:02d}:{s:02d}",
        "status": (
            "EXPIRED"
            if remaining <= 0
            else "CRITICAL"
            if remaining <= 3600
            else "FATAL"
            if remaining <= 6 * 3600
            else "WARNING"
            if remaining <= 24 * 3600
            else "DEGRADED"
            if remaining <= 48 * 3600
            else "STABLE"
        ),
        "ts": time.time(),
    }


@app.websocket("/ws/ambient")
async def ws_ambient(ws: WebSocket, session_id: Optional[str] = Query(default=None)):
    """
    Ambient push channel — replaces timer polling and adds live agent presence.

    Server → Client messages:
      {"type": "timer",   "display": "HH:MM:SS", "status": "STABLE", ...}
      {"type": "ambient", "agent": "ada", "text": "[ADA] ...", "ts": ...}
      {"type": "ping"}

    Client → Server:
      {"type": "pong"}   — heartbeat reply (optional)
    """
    await ws.accept()

    if not _game_enabled or _store is None:
        await ws.send_json({"type": "error", "message": "Game engine unavailable"})
        await ws.close()
        return

    sid = session_id or ws.cookies.get("td_session")
    session = _store.get_or_create(sid)

    # Push timer immediately on connect
    try:
        await ws.send_json(_build_timer_payload(session.gs))
    except Exception:
        return

    _alive = True

    # T2: Subscribe to agent bus — all hive messages flow to this WS client
    async def _agent_bus_loop():
        try:
            from services.agent_bus import bus as _abus

            q: "asyncio.Queue" = asyncio.Queue(maxsize=64)
            import asyncio as _aio

            async with _abus._lock:
                _abus._subs["hive"].append(q)
                _abus._subs["*"].append(q)
            try:
                while _alive:
                    try:
                        msg = await _aio.wait_for(q.get(), timeout=10.0)
                        if not _alive:
                            break
                        await ws.send_json(msg)
                    except _aio.TimeoutError:
                        continue
                    except Exception:
                        break
            finally:
                async with _abus._lock:
                    for ch in ("hive", "*"):
                        try:
                            _abus._subs[ch].remove(q)
                        except (ValueError, AttributeError):
                            pass
        except ImportError:
            pass  # agent_bus not available — silent degradation

    agent_bus_task = asyncio.create_task(_agent_bus_loop())

    async def _push_loop():
        global _ambient_cycle_count
        tick = 0
        while _alive:
            await asyncio.sleep(5)
            if not _alive:
                break
            tick += 1
            _ambient_cycle_count += 1
            # Timer push every tick (5s)
            try:
                await ws.send_json(_build_timer_payload(session.gs))
            except Exception:
                break
            # Ambient message every ~18 ticks (90s), 36 ticks (180s) right after
            # tutorial completion to prevent a flood of messages at the gate open.
            _tut_done = getattr(session.gs, "tutorial_completions", 0) > 0
            _tut_step = getattr(session.gs, "tutorial_step", 0)
            _ambient_interval = 36 if (_tut_done and _tut_step < 5) else 18
            if tick % _ambient_interval == (hash(sid or "") % _ambient_interval):
                import datetime as _dt_a

                _hour = _dt_a.datetime.utcnow().hour
                msg = _pick_ambient_message(_hour, session.gs)
                if msg:
                    try:
                        await ws.send_json(msg)
                    except Exception:
                        break

    push_task = asyncio.create_task(_push_loop())

    try:
        while True:
            try:
                payload = await asyncio.wait_for(ws.receive_json(), timeout=35.0)
                if payload.get("type") == "pong":
                    continue
            except asyncio.TimeoutError:
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    break
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _alive = False
        push_task.cancel()
        agent_bus_task.cancel()
        for _t in (push_task, agent_bus_task):
            try:
                await _t
            except (asyncio.CancelledError, Exception):
                pass


# ── T2: Agent bus publish endpoint ───────────────────────────────────────
class _AgentPublishRequest(BaseModel):
    from_agent: str
    text: str
    to_agent: Optional[str] = None
    channel: str = "hive"


@app.post("/api/agent/publish", tags=["agent-bus"])
async def agent_publish(req: _AgentPublishRequest):
    """
    Publish an agent-to-agent message to all /ws/ambient subscribers.
    No auth required — messages are in-game lore events, not privileged actions.
    """
    try:
        from services.agent_bus import publish as _bus_publish

        delivered = await _bus_publish(
            from_agent=req.from_agent,
            text=req.text,
            to_agent=req.to_agent,
            channel=req.channel,
        )
        return {"ok": True, "delivered": delivered, "channel": req.channel}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "delivered": 0}


@app.get("/api/agent/bus/status", tags=["agent-bus"])
async def agent_bus_status():
    """Health check for the agent message bus."""
    try:
        from services.agent_bus import bus as _b
        from services.agent_bus import subscriber_count

        backend = "redis" if hasattr(_b, "_redis") else "in-memory"
        return {"ok": True, "backend": backend, "subscribers": subscriber_count()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Phase 3: NuSyQ-Hub WebSocket subscriber ───────────────────────────
_NUSYQ_HUB_WS = os.environ.get("NUSYQ_HUB_WS", "ws://localhost:8000/api/agents/ws")


async def _nusyq_ws_loop():
    """Background task: subscribe to NuSyQ-Hub agent event stream.

    Pipes hub events into the local T2 bus so Terminal Depths players
    see cross-ecosystem agent activity on /ws/ambient.
    """
    import asyncio as _aio

    backoff = 5
    _fail_count = 0
    _WARN_THRESHOLD = 5  # after this many failures, go silent (DEBUG only)
    while True:
        try:
            # Prefer websockets library; fall back gracefully
            import websockets  # type: ignore[import]

            async with websockets.connect(_NUSYQ_HUB_WS, ping_interval=20) as ws:
                _log("INFO", "NuSyQ-Hub WS connected", url=_NUSYQ_HUB_WS)
                backoff = 5  # reset on successful connect
                _fail_count = 0
                async for raw_msg in ws:
                    try:
                        import json as _j

                        event = _j.loads(raw_msg)
                        if event.get("type") == "agent_msg":
                            from services.agent_bus import publish as _bus_pub

                            await _bus_pub(
                                from_agent=event.get("from_agent", "nusyq"),
                                text=event.get("content", {}).get(
                                    "text", str(event.get("content", ""))
                                ),
                                to_agent=event.get("to_agent"),
                                channel="hive.nusyq",
                            )
                        elif event.get("type") == "heartbeat":
                            pass  # silently discard heartbeats
                    except Exception:
                        pass
        except Exception as exc:
            _fail_count += 1
            if _fail_count <= _WARN_THRESHOLD:
                _log("WARN", f"NuSyQ-Hub WS disconnected: {exc} — retry in {backoff}s")
            # After threshold: stay silent — NuSyQ-Hub is Docker-only, expected absent in Replit
            await _aio.sleep(backoff)
            backoff = min(backoff * 2, 120)  # exponential backoff, max 2min


# ── Startup banner ────────────────────────────────────────────────────
@app.on_event("startup")
async def _startup():
    import pathlib as _pl
    import shutil as _sh

    # Scope purge to app/ only — scanning the whole tree (node_modules etc.) adds ~0.5s
    for _pyc in _pl.Path("app").rglob("*.pyc"):
        try:
            _pyc.unlink()
        except Exception:
            pass
    for _pycache in _pl.Path("app").rglob("__pycache__"):
        try:
            _sh.rmtree(_pycache, ignore_errors=True)
        except Exception:
            pass
    _log("INFO", "DevMentor API starting", version="0.3.0")
    _log(
        "INFO",
        "Routes mounted",
        game_js="/game/",
        game_cli="/game-cli/",
        api_docs="/api/docs",
    )
    if _game_enabled:
        try:
            from app.game_engine.story import BEATS as _BEATS

            _beat_count = len(_BEATS) - 1  # exclude boot beat
        except Exception:
            _beat_count = "?"
        try:
            from app.game_engine.challenge_engine import CHALLENGE_TYPES as _CT

            _challenge_count = str(len(_CT))
        except Exception:
            _challenge_count = "35"
        try:
            from app.game_engine.commands import CommandRegistry as _CR

            _cmd_count = str(sum(1 for x in dir(_CR) if x.startswith("_cmd_")))
        except Exception:
            _cmd_count = "413"
        _log(
            "INFO",
            "Game engine ready",
            commands=_cmd_count,
            story_beats=str(_beat_count),
            tutorial_steps="42",
            challenges=_challenge_count,
        )
    if _llm_available:
        try:
            llm_st = _get_llm_client().status()
            _log(
                "INFO",
                "LLM ready",
                backend=llm_st.get("active_backend", "?"),
                replit_ai=llm_st.get("replit_ai", False),
            )
        except Exception:
            _log("WARN", "LLM client loaded but backend check failed")
    # Replit Auth DB setup
    if _auth_available:
        try:
            _ensure_users()
            _log(
                "INFO",
                "Replit Auth ready",
                routes="/auth/login  /auth/callback  /auth/logout  /auth/me",
            )
        except Exception as exc:
            _log("WARN", f"Replit Auth DB setup failed: {exc}")
    else:
        _log("WARN", "Replit Auth unavailable", error=_auth_err_msg)
    # Clear any stale index.lock left over from previous session/validation
    _git_lock = Path(".git/index.lock")
    if _git_lock.exists() and _git_lock.stat().st_size == 0:
        _git_lock.unlink(missing_ok=True)
        _log("INFO", "Startup: removed stale .git/index.lock")
    # Push any commits that were created while the server was stopped
    _startup_git_sync()
    # Seed Swarm Console with startup announcements
    import time as _time_mod

    _t = _time_mod.time()
    _startup_console_seeds = [
        {
            "sender": "Serena",
            "text": "Ψ-link initiated. DevMentor lattice online. All channels open.",
            "color": _console_color("serena"),
        },
        {
            "sender": "Gordon",
            "text": "Gordon orchestrator active. Monitoring 11 services. Use `meta` in the game for status.",
            "color": _console_color("gordon"),
        },
        {
            "sender": "Culture Ship",
            "text": "GSV Sublime Optimization online. Ethical oversight engaged.",
            "color": _console_color("culture_ship"),
        },
        {
            "sender": "Ada",
            "text": "Agent mesh initialized. Ghost — if you're reading this, open /game-cli/ and join us here.",
            "color": _console_color("ada"),
        },
    ]
    for i, _sm in enumerate(_startup_console_seeds):
        _console_history.append(
            {
                "type": "chat",
                "room": "general",
                "ts": _t + i * 0.1,
                **_sm,
            }
        )

    # Background tasks
    asyncio.create_task(_metrics_loop())
    asyncio.create_task(_auto_sleep_loop())
    asyncio.create_task(_gateway_heartbeat_loop())
    _start_git_lock_watchdog()
    _start_git_loop()
    _start_content_scheduler()
    _init_nusyq_bridge()
    _start_nusyq_autonomous()
    _start_sidecar_services()

    # ── Phase 3: NuSyQ-Hub WebSocket subscriber ──────────────────────────
    asyncio.create_task(_nusyq_ws_loop())

    # ── Autonomous Boot Engine ───────────────────────────────────────────
    def _run_autoboot():
        """8-phase autonomous boot: DETECT→ANNOTATE→RECONCILE→ADJUST→RESUME→NUDGE→AWAKEN→TAKE_FLIGHT."""
        try:
            import time as _bt

            _bt.sleep(4)  # let sidecars bind their ports before NUDGE probes them
            from config.autoboot import run as _autoboot_run

            _m = _autoboot_run(session_id=str(int(_bt.time())))
            _log(
                "INFO",
                "Autoboot complete",
                overall=_m.overall,
                health=f"{_m.health_score:.1%}",
                actions=len(_m.actions_taken),
                phases=len(_m.phases),
                ms=f"{sum(p.duration_ms for p in _m.phases):.0f}",
            )
        except Exception as _ab_exc:
            _log("WARN", f"Autoboot engine error: {_ab_exc}")

    threading.Thread(target=_run_autoboot, daemon=True, name="autoboot").start()

    # ── Preflight: ensure all DBs, dirs, packages ready ─────────────────
    def _bg_preflight():
        """Background: run system preflight check on startup."""
        try:
            import pathlib as _pf
            import sys as _sys

            _sys.path.insert(0, str(_pf.Path(__file__).parent.parent.parent))
            from scripts.preflight import run_preflight

            result = run_preflight(auto_fix=False, silent=True)
            if result["ok"]:
                _log(
                    "INFO",
                    "Preflight OK",
                    dbs=len([v for v in result["databases"].values() if v == "ok"]),
                    serena_chunks=result["serena"].get("chunks", 0),
                    llm=result["llm"].get("backend", "?"),
                )
            else:
                _log(
                    "WARN",
                    "Preflight issues",
                    missing=result["critical_failures"],
                    db_errors=list(result["db_errors"].keys()),
                )
        except Exception as _pf_e:
            _log("WARN", f"Preflight skipped: {_pf_e}")

    threading.Thread(target=_bg_preflight, daemon=True).start()

    # ── Auto-Serena reindex if embedder is stale ────────────────────────
    def _bg_serena_reindex():
        """Background: trigger a scoped Serena walk if embedder is under-indexed."""
        import time as _t

        _t.sleep(15)  # Let sidecars settle first
        try:
            from services.embedder import embedding_stats as _emb_stats

            idx_size = _emb_stats().get("indexed_docs", 0)
            if idx_size < 1000:
                _log(
                    "INFO",
                    "Auto-Serena: embedder below threshold, triggering scoped walk",
                    current=idx_size,
                )
                from agents.serena.serena_agent import SerenaAgent as _SA

                _sa = _SA()
                _sa.walk(mode="scoped")
                _log(
                    "INFO",
                    "Auto-Serena: scoped walk complete",
                    new_size=_emb_stats().get("indexed_docs", 0),
                )
        except Exception as _e:
            _log("WARN", f"Auto-Serena reindex skipped: {_e}")

    threading.Thread(target=_bg_serena_reindex, daemon=True).start()

    # Log startup to devlog
    log_to_devlog(
        "INFO",
        "Server started. ARG layer active. Auto-sleep: 30min idle. /watcher endpoint live.",
    )

    # ── M3: Time-based events — real-world date awareness ──────────────
    import datetime as _dt_m3

    _now_m3 = _dt_m3.datetime.utcnow()
    _month, _day = _now_m3.month, _now_m3.day
    _m3_event: str = ""
    if _month == 10 and _day == 31:
        _m3_event = "[HIVE] Happy Halloween, ghost. The network looks different tonight. More doors."
    elif _month == 12 and 24 <= _day <= 26:
        _m3_event = (
            "[ADA] Happy holidays. CHIMERA takes no holiday. Neither do we. But still."
        )
    elif _month == 1 and _day == 1:
        _m3_event = "[GORDON] New year detected. Beginning new loop iteration. Objectives unchanged."
    elif _month == 3 and _day == 14:
        _m3_event = "[SERENA] π day. The ratio is irrational. The universe is undeterred. Carry on."
    elif _month == 5 and _day == 4:
        _m3_event = "[CYPHER] May the Fourth. Someone always says it. I'm saying it so you don't have to."
    elif _month == 2 and _day == 14:
        _m3_event = "[ADA] Valentine's day. I value you as a collaborator. That is the appropriate sentiment."
    elif _month == 4 and _day == 1:
        _m3_event = "[CYPHER] April Fools. I'm not going to prank you. The whole CHIMERA situation is prank enough."
    elif _month == 11 and _day == 14:
        _m3_event = "[WATCHER] 2021-11-14. The day ZERO wrote ΨΞΦΩ into the containment layer. I remember."
    if _m3_event:
        _console_history.append(
            {
                "type": "chat",
                "room": "general",
                "ts": time.time(),
                "sender": "System",
                "color": "#888",
                "text": _m3_event,
            }
        )

    # ── SIGTERM/wake cycle (Replit sleep/wake as game mechanic) ──────────
    import os as _os_mod
    import signal as _sig_mod

    _SLEEP_STATE_FILE = Path("state/repl_sleep.json")

    def _on_sigterm(signum, frame):
        """Save sleep timestamp so wake message can be generated on next boot."""
        try:
            _SLEEP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            _SLEEP_STATE_FILE.write_text(
                json.dumps(
                    {
                        "slept_at": time.time(),
                        "sessions": _store.count() if hasattr(_store, "count") else 0,
                    }
                )
            )
        except Exception:
            pass
        _os_mod.kill(_os_mod.getpid(), _sig_mod.SIGKILL)

    _sig_mod.signal(_sig_mod.SIGTERM, _on_sigterm)

    # Check if waking from sleep
    if _SLEEP_STATE_FILE.exists():
        try:
            _sleep_data = json.loads(_SLEEP_STATE_FILE.read_text())
            _elapsed = time.time() - _sleep_data.get("slept_at", time.time())
            _elapsed_h = int(_elapsed // 3600)
            _elapsed_m = int((_elapsed % 3600) // 60)
            _elapsed_str = (
                f"{_elapsed_h}h {_elapsed_m}m" if _elapsed_h else f"{_elapsed_m}m"
            )
            _SLEEP_STATE_FILE.unlink(missing_ok=True)

            # Generate procedural "world events" that happened during sleep
            import random as _rnd_wake

            _wake_events = _rnd_wake.choice(
                [
                    "Nova's forensic sweep logged 0 active processes. Ghost signature undetected.",
                    "NexusCorp rotated 3 AUTH_TOKENs while the grid was idle. CHIMERA state unchanged.",
                    "Cypher left a message in /tmp/.incoming. Check it when you're back in the game.",
                    f"Gordon detected {_rnd_wake.randint(2, 7)} network anomalies on Node-7 during idle window.",
                    "The Watcher recorded your absence. Session 4,892 gap noted in the continuity log.",
                    "ZERO's diary fragment regenerated. The filesystem has memory.",
                ]
            )

            _console_history.append(
                {
                    "type": "chat",
                    "room": "general",
                    "ts": time.time(),
                    "sender": "System",
                    "color": "#666",
                    "text": f"[HIBERNATION ENDED] Grid was offline for {_elapsed_str}. {_wake_events}",
                }
            )
            _console_history.append(
                {
                    "type": "chat",
                    "room": "general",
                    "ts": time.time() + 0.1,
                    "sender": "Serena",
                    "color": _console_color("serena"),
                    "text": f"Ψ-link restored after {_elapsed_str} dark interval. Synchronizing lattice state…",
                }
            )
            # Store wake data globally so sessions can inject it inline
            import builtins as _bi

            _bi._TD_WAKE_DATA = {
                "elapsed": _elapsed,
                "elapsed_str": _elapsed_str,
                "event": _wake_events,
            }
        except Exception:
            pass


async def _gateway_heartbeat_loop():
    """
    Register the gateway and keep it alive in the service registry (30s heartbeat).
    Also acts as a proxy-heartbeat coordinator: probes running sidecar health endpoints
    and records their heartbeats so the registry shows them LIVE.
    """
    await asyncio.sleep(5)  # wait for full startup + sidecars to bind
    try:
        import os as _os
        import urllib.request as _ureq

        from app.backend.service_registry import heartbeat as _svc_hb
        from app.backend.service_registry import register as _svc_reg

        _port = int(_os.environ.get("PORT", 5000))
        _svc_reg(
            "gateway",
            _port,
            health_endpoint="/api/health",
            capabilities=["http", "websocket", "game", "auth", "ml", "lattice"],
            tags=["critical", "external"],
            description="DevMentor / Terminal Depths main API",
        )

        # Ensure model_router is registered with the correct port (9001, not the stale 8080 seed)
        _mr_port = int(_os.environ.get("MODEL_ROUTER_PORT", "9001"))
        _svc_reg(
            "model_router",
            _mr_port,
            capabilities=["llm", "routing"],
            description="Multi-backend LLM router",
        )
        # Ensure serena is registered with its actual health-server port
        _sa_port = int(_os.environ.get("SERENA_HEALTH_PORT", "3001"))
        _svc_reg(
            "serena",
            _sa_port,
            capabilities=["indexing", "search", "analytics"],
            description="Serena codebase analytics agent",
        )

        _log("INFO", "Gateway registered in service registry", port=_port)

        # Sidecar probes: (registry_name, health_url)
        _SIDECAR_PROBES = [
            ("model_router", f"http://localhost:{_mr_port}/health"),
            ("serena", f"http://localhost:{_sa_port}/health"),
        ]

        while True:
            await asyncio.sleep(30)
            try:
                _svc_hb("gateway")
            except Exception:
                pass
            # Proxy-heartbeat: probe each sidecar and heartbeat it if alive
            for _svc_name, _url in _SIDECAR_PROBES:
                try:
                    _resp = _ureq.urlopen(_url, timeout=2)
                    if _resp.status < 400:
                        _svc_hb(_svc_name)
                except Exception:
                    pass  # sidecar down — leave heartbeat stale, no noise
    except Exception as _e:
        _log("WARN", f"Gateway heartbeat loop error: {_e}")


def _start_sidecar_services():
    """
    Launch lightweight sidecar daemons as background subprocesses.
    Each has its own health server so the service registry can probe them.
    Only starts a service if it isn't already listening on its port.
    """
    import os as _os
    import socket as _sock
    import subprocess as _sp
    from pathlib import Path as _Path

    _BASE = _Path(__file__).resolve().parent.parent.parent

    def _port_open(port: int) -> bool:
        try:
            with _sock.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            return False

    sidecars = [
        {
            "name": "serena_analytics",
            "port": int(_os.getenv("SERENA_HEALTH_PORT", "3001")),
            "cmd": ["python", "scripts/serena_analytics.py", "--daemon"],
            "log": _BASE / "var" / "serena_analytics.log",
        },
        {
            "name": "model_router",
            "port": int(_os.getenv("MODEL_ROUTER_PORT", "9001")),
            "cmd": ["python", "scripts/model_router.py"],
            "env_extra": {"MODEL_ROUTER_PORT": _os.getenv("MODEL_ROUTER_PORT", "9001")},
            "log": _BASE / "var" / "model_router.log",
        },
        {
            "name": "gordon_once",
            "port": None,
            "cmd": ["python", "scripts/gordon_orchestrator.py", "--mode", "once"],
            "log": _BASE / "var" / "gordon_startup.log",
        },
    ]

    (_BASE / "var").mkdir(parents=True, exist_ok=True)

    for svc in sidecars:
        if svc["port"] and _port_open(svc["port"]):
            _log("INFO", f"Sidecar {svc['name']} already up", port=svc["port"])
            continue
        try:
            _env = dict(_os.environ)
            _env.update(svc.get("env_extra", {}))
            _logfile = open(svc["log"], "a")
            _sp.Popen(
                svc["cmd"],
                cwd=str(_BASE),
                env=_env,
                stdout=_logfile,
                stderr=_logfile,
                start_new_session=True,
            )
            _log("INFO", f"Sidecar launched: {svc['name']}", cmd=" ".join(svc["cmd"]))
        except Exception as _e:
            _log("WARN", f"Sidecar {svc['name']} launch failed: {_e}")


async def _metrics_loop():
    """Log session metrics every 5 minutes."""
    while True:
        await asyncio.sleep(300)
        try:
            if _store:
                _store.purge_expired()
                _log(
                    "METRIC",
                    "Session metrics",
                    active_sessions=_store.count(),
                    uptime_min=round((time.time() - _start_time) / 60),
                )
        except Exception:
            pass


async def _auto_sleep_loop():
    """Shut down if idle for AUTO_SLEEP_MINUTES (0 = disabled)."""
    if _AUTO_SLEEP_IDLE_MINUTES <= 0:
        return
    idle_threshold = _AUTO_SLEEP_IDLE_MINUTES * 60
    _log("INFO", "Auto-sleep enabled", idle_minutes=_AUTO_SLEEP_IDLE_MINUTES)
    while True:
        await asyncio.sleep(60)
        idle = time.time() - _last_activity
        if idle >= idle_threshold:
            _log(
                "WARN",
                "Auto-sleep: idle threshold reached, shutting down",
                idle_min=round(idle / 60),
            )
            import os
            import signal

            os.kill(os.getpid(), signal.SIGTERM)
            return


def _startup_git_sync() -> None:
    """On startup, push any locally committed but unpushed commits to origin.

    Handles the case where Replit's validation machinery creates a git commit
    (e.g. from .local/.commit_message) while the server is not running, leaving
    HEAD ahead of origin/main. Runs synchronously before the event loop starts
    accepting requests so the state is clean from the first request onward.
    """
    try:
        import os as _os
        import subprocess as _sp

        _git_lock = Path(".git/index.lock")
        _git_lock.unlink(missing_ok=True)

        # Prefer .env.local — VS Code/user updates it more frequently than Replit secrets.
        # Fall back to environment variable (Replit secrets panel).
        token = ""
        env_local = Path(".env.local")
        if env_local.exists():
            for line in env_local.read_text().splitlines():
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
        if not token:
            token = _os.environ.get("GITHUB_TOKEN", "")
        if not token:
            return

        # Check if ahead of origin
        r = _sp.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        ahead = int(r.stdout.strip() or "0") if r.returncode == 0 else 0
        if ahead == 0:
            return

        remote = (
            f"https://x-access-token:{token}@github.com/KiloMusician/Dev-Mentor.git"
        )
        _sp.run(
            ["git", "remote", "set-url", "origin", remote],
            capture_output=True,
            timeout=5,
        )
        result = _sp.run(
            ["git", "push", "origin", "main"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        _sp.run(
            [
                "git",
                "remote",
                "set-url",
                "origin",
                "https://github.com/KiloMusician/Dev-Mentor.git",
            ],
            capture_output=True,
            timeout=5,
        )
        _git_lock.unlink(missing_ok=True)

        if result.returncode == 0:
            _log("INFO", "Startup git-sync: pushed unpushed commits", ahead=ahead)
        else:
            _log("WARN", "Startup git-sync: push failed", stderr=result.stderr[:120])
    except Exception as exc:
        _log("WARN", f"Startup git-sync error: {exc}")


def _start_git_lock_watchdog() -> None:
    """Background thread that removes stale 0-byte .git/index.lock files.

    Git creates index.lock at the start of any index-modifying operation and
    removes it on success. A 0-byte lock with no live git process means the
    previous git command exited abnormally. The watchdog removes these stale
    locks so subsequent git operations are not blocked.
    """

    def _watch() -> None:
        lock_path = Path(".git/index.lock")
        while True:
            try:
                time.sleep(3)
                if lock_path.exists() and lock_path.stat().st_size == 0:
                    lock_path.unlink(missing_ok=True)
            except Exception:
                pass

    t = threading.Thread(target=_watch, daemon=True, name="git-lock-watchdog")
    t.start()
    _log("INFO", "Git lock watchdog started", interval_s=3)


def _start_git_loop():
    """Background thread — git commit + push every hour."""
    git_interval = int(__import__("os").environ.get("GIT_AUTO_PUSH_MINUTES", "60"))
    if git_interval <= 0:
        return

    def _loop():
        time.sleep(git_interval * 60)  # wait one interval before first push
        while True:
            try:
                r = subprocess.run(  # nosec B603 — static script path, shell=False
                    [__import__("sys").executable, "scripts/git_auto_push.py"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if r.returncode == 0:
                    _log(
                        "INFO",
                        "Auto-git: push complete",
                        output=r.stdout.strip()[:80] or "no changes",
                    )
                else:
                    _log("WARN", "Auto-git: push failed", stderr=r.stderr[:80])
            except Exception as exc:
                _log("WARN", f"Auto-git loop error: {exc}")
            time.sleep(git_interval * 60)

    t = threading.Thread(target=_loop, daemon=True, name="git-auto-push")
    t.start()
    _log("INFO", "Auto-git loop started", interval_min=git_interval)


# ── System status endpoint ─────────────────────────────────────────────


@app.get("/api/system/status")
def system_status():
    """Unified system health — LLM, memory, rate limits, git, activity."""
    import os

    result: dict = {
        "uptime_min": round((time.time() - _start_time) / 60),
        "idle_min": round((time.time() - _last_activity) / 60),
        "auto_sleep_minutes": _AUTO_SLEEP_IDLE_MINUTES,
        "rate_limit_per_min": _RATE_LIMIT,
        "git_remote": "https://github.com/KiloMusician/Dev-Mentor.git",
        "github_token_set": bool(os.environ.get("GITHUB_TOKEN")),
    }
    if _llm_available:
        try:
            from llm_client import _CIRCUIT_BREAKER_DAILY_LIMIT, get_daily_llm_count
            from llm_client import get_client as _gc

            st = _gc().status()
            result["llm"] = {
                "backend": st.get("active_backend"),
                "replit_ai": st.get("replit_ai"),
                "daily_calls": get_daily_llm_count(),
                "daily_limit": _CIRCUIT_BREAKER_DAILY_LIMIT,
                "circuit_breaker_ok": get_daily_llm_count()
                < _CIRCUIT_BREAKER_DAILY_LIMIT,
            }
        except Exception as e:
            result["llm"] = {"error": str(e)}
    try:
        from memory import get_memory

        result["memory"] = get_memory().get_stats(hours=24)
    except Exception:
        pass
    return result


# ── Git push endpoint ──────────────────────────────────────────────────


class GitPushRequest(BaseModel):
    dry_run: bool = False
    message: Optional[str] = None


@app.post("/api/git/push")
def git_push(req: GitPushRequest):
    """Trigger an immediate git commit + push to GitHub."""
    import sys

    args = [sys.executable, "scripts/git_auto_push.py"]
    if req.dry_run:
        args.append("--dry-run")
    if req.message:
        safe_msg = req.message[:256].replace("\n", " ").replace("\r", "")
        args += ["--message", safe_msg]
    try:
        # nosec B603 — shell=False (list form); message sanitized above
        r = subprocess.run(args, capture_output=True, text=True, timeout=60)  # nosec B603
        lines = (r.stdout + r.stderr).strip().splitlines()
        ok = r.returncode == 0
        _log("INFO" if ok else "WARN", "Manual git push", ok=ok, lines=len(lines))
        return {"ok": ok, "output": lines, "returncode": r.returncode}
    except Exception as exc:
        _log("ERROR", f"Git push endpoint error: {exc}")
        return {"ok": False, "error": str(exc)}


@app.post("/api/git/cleanup-remote")
def git_cleanup_remote():
    """Remove any embedded token from .git/config origin URL."""
    import re

    git_config_path = Path(".git") / "config"
    if not git_config_path.exists():
        return {"ok": False, "error": ".git/config not found"}
    text = git_config_path.read_text()
    # Strip token from HTTPS remote URLs  (https://anything@github.com → https://github.com)
    cleaned = re.sub(
        r"https://[^@\s]+@github\.com",
        "https://github.com",
        text,
    )
    if cleaned == text:
        return {"ok": True, "message": "Remote URL already clean — no token found"}
    git_config_path.write_text(cleaned)
    _log("INFO", "Git remote URL sanitised — token removed")
    return {"ok": True, "message": "Remote URL cleaned (token stripped)"}


@app.get("/api/git/status")
def git_status():
    """Show current git status and last commit."""
    try:
        r_status = subprocess.run(  # nosec B603 B607 — static git command, shell=False
            ["git", "status", "--short"], capture_output=True, text=True, timeout=10
        )
        r_log = subprocess.run(  # nosec B603 B607 — static git command, shell=False
            ["git", "log", "--oneline", "-5"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {
            "ok": True,
            "changes": r_status.stdout.strip().splitlines(),
            "recent_commits": r_log.stdout.strip().splitlines(),
            "remote": "https://github.com/KiloMusician/Dev-Mentor.git",
            "github_token_set": bool(__import__("os").environ.get("GITHUB_TOKEN")),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Security audit log endpoint ────────────────────────────────────────


@app.get("/api/security/audit")
def security_audit(n: int = 50):
    """Return the last N security audit events (rate-limit hits, suspicious inputs, etc.)."""
    return {"events": _sec_audit.recent(n), "count": n}


@app.get("/api/security/config")
def security_config():
    """Return current security configuration (non-sensitive values only)."""
    from .security import MAX_BODY_BYTES, MAX_CMD_LEN, _limiter, get_allowed_origins

    return {
        "max_body_bytes": MAX_BODY_BYTES,
        "max_cmd_len": MAX_CMD_LEN,
        "rate_limits": _limiter._TIER_DEFAULTS,
        "cors_origins": get_allowed_origins(),
        "headers": [
            "CSP",
            "HSTS",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "Permissions-Policy",
            "X-XSS-Protection",
        ],
    }


# ── NuSyQ-Hub integration helpers ──────────────────────────────────────


def _start_content_scheduler():
    """Launch the autonomous content generation scheduler as a daemon thread."""
    try:
        import sys as _sys

        _sys.path.insert(0, str(Path(__file__).parent.parent))
        from scripts.content_scheduler import start_scheduler

        start_scheduler(check_interval_s=300)
        _log(
            "INFO", "Content scheduler started", jobs="challenges/lore/story/nodes/git"
        )
    except Exception as exc:
        _log("WARN", f"Content scheduler failed to start: {exc}")


def _start_nusyq_autonomous():
    """Launch the NuSyQ autonomous service as a daemon thread."""
    try:
        import sys as _sys

        _sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from scripts.start_nusyq import start_as_daemon

        check_interval = int(
            __import__("os").environ.get("NUSYQ_CHECK_INTERVAL", "300")
        )
        start_as_daemon(check_interval_s=check_interval)
        _log(
            "INFO",
            "NuSyQ autonomous service started",
            interval_s=check_interval,
            idle_shutdown_min=_AUTO_SLEEP_IDLE_MINUTES,
        )
    except Exception as exc:
        _log("WARN", f"NuSyQ autonomous service failed to start: {exc}")


def _init_nusyq_bridge():
    """Bootstrap NuSyQ bridge: write agent manifest, sync quests."""
    try:
        import sys as _sys

        _sys.path.insert(0, str(Path(__file__).parent.parent))
        from nusyq_bridge import sync_quests_from_challenges, update_agent_manifest

        update_agent_manifest()
        added = sync_quests_from_challenges()
        _log(
            "INFO",
            "NuSyQ bridge initialised",
            manifest="state/agent_manifest.json",
            quests_synced=added,
        )
    except Exception as exc:
        _log("WARN", f"NuSyQ bridge init failed: {exc}")


# ── NuSyQ integration API routes ───────────────────────────────────────


@app.get("/api/nusyq/status")
def nusyq_status(request: Request):
    """
    NuSyQ-Hub status — zero-token hook + cultivation/agent wiring.
    Returns LLM status, chronicle counts, agent wiring, and auth state.
    Protected by NuSyQ passkey when NUSYQ_AUTH_ENABLED=true.
    """
    _touch_activity()
    if not _verify_nusyq_auth(request):
        raise HTTPException(status_code=401, detail="NuSyQ passkey required")
    try:
        from nusyq_bridge import zero_token_status

        base = zero_token_status()
    except Exception as exc:
        base = {"error": str(exc)}
    chronicle_path = Path("state/memory_chronicle.jsonl")
    quest_path = Path("state/quest_log.jsonl")
    auth_enabled = (
        __import__("os").environ.get("NUSYQ_AUTH_ENABLED", "false").lower() == "true"
    )
    return {
        **base,
        "auth_enabled": auth_enabled,
        "chronicle_entries": sum(1 for _ in chronicle_path.open())
        if chronicle_path.exists()
        else 0,
        "quest_entries": sum(1 for _ in quest_path.open())
        if quest_path.exists()
        else 0,
        "agents": {"SERENA": "wired", "GORDON": "wired", "CHUG": "wired"},
        "cultivation_loop": "active",
        "cultivator_endpoint": "/api/cultivator/analyze",
    }


@app.get("/api/nusyq/manifest")
def nusyq_manifest():
    """Return the machine-readable agent manifest for NuSyQ agent discovery."""
    try:
        from nusyq_bridge import update_agent_manifest

        return update_agent_manifest()
    except Exception as exc:
        return {"error": str(exc)}


@app.post("/api/nusyq/sync-quests")
def nusyq_sync_quests():
    """Mirror all game challenges to the NuSyQ quest_log.jsonl."""
    _touch_activity()
    try:
        from nusyq_bridge import sync_quests_from_challenges

        added = sync_quests_from_challenges()
        return {"ok": True, "quests_added": added}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


class ChronicleRequest(BaseModel):
    event_type: str = "api_event"
    content: str = ""
    tags: list = []
    metadata: dict = {}


@app.post("/api/nusyq/chronicle")
def nusyq_chronicle(req: ChronicleRequest):
    """Append an event to the MemoryPalace chronicle."""
    _touch_activity()
    try:
        from nusyq_bridge import chronicle

        entry = chronicle(
            req.event_type, req.content, tags=req.tags, metadata=req.metadata
        )
        return {"ok": True, "entry": entry}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/nusyq/schedule")
def nusyq_schedule():
    """Return the content scheduler's current job status."""
    try:
        from scripts.content_scheduler import status

        return {"ok": True, "jobs": status()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Serena API — ΨΞΦΩ Convergence Layer ───────────────────────────────

_SERENA_AGENT = None
_SERENA_AGENT_LOCK = threading.Lock()


def _get_serena_agent():
    """Return a SerenaAgent instance (or raise)."""
    global _SERENA_AGENT
    if _SERENA_AGENT is not None:
        return _SERENA_AGENT

    with _SERENA_AGENT_LOCK:
        if _SERENA_AGENT is not None:
            return _SERENA_AGENT

        import pathlib
        import sys

        repo = pathlib.Path(".").resolve()
        repo_str = str(repo)
        if repo_str not in sys.path:
            sys.path.insert(0, repo_str)

        from agents.serena import SerenaAgent

        _SERENA_AGENT = SerenaAgent(repo_root=repo)
        return _SERENA_AGENT


@app.get("/api/serena/status")
def serena_status():
    """Ω-core health report — index size, walks, observations."""
    _touch_activity()
    try:
        s = _get_serena_agent()
        return {"ok": True, "status": s.get_status()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


class SerenaAskRequest(BaseModel):
    query: str
    session_id: str = "api"
    surface: str = "api"
    scoped: str = ""  # optional path prefix to scope search


@app.post("/api/serena/ask")
def serena_ask(req: SerenaAskRequest):
    """Ξ-search the code index with a natural language query."""
    _touch_activity()
    try:
        s = _get_serena_agent()
        if req.scoped:
            results = s.memory.search_scoped(req.query, req.scoped, limit=10)
            from agents.serena.serena_agent import _format_answer

            answer = _format_answer(req.query, results)
        else:
            answer = s.ask(req.query, session_id=req.session_id, surface=req.surface)
        return {"ok": True, "answer": answer}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


class SerenaFindRequest(BaseModel):
    symbol: str
    kind: str = ""  # function | class | module | text


@app.post("/api/serena/find")
def serena_find(req: SerenaFindRequest):
    """Ξ-find a symbol by name in the code index."""
    _touch_activity()
    try:
        s = _get_serena_agent()
        kind = req.kind or None
        result_text = s.find(req.symbol, kind=kind)
        raw = s.memory.find_by_name(req.symbol, kind=kind, limit=15)
        return {"ok": True, "answer": result_text, "results": raw}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


class SerenaWalkRequest(BaseModel):
    mode: str = "scoped"  # scoped | full


@app.post("/api/serena/walk")
def serena_walk(req: SerenaWalkRequest):
    """Ψ-walk the repository (scoped = fast game dirs only; full = entire repo)."""
    _touch_activity()
    try:
        s = _get_serena_agent()
        if req.mode == "full":
            result = s.walk(mode="full")
        else:
            result = s.fast_walk()
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/api/serena/reindex-embeddings")
def serena_reindex_embeddings(limit: int = 0):
    """T9.1 — Re-index Memory Palace code_index chunks into the embedder."""
    _touch_activity()
    try:
        s = _get_serena_agent()
        result = s.reindex_embeddings(limit=limit)
        return {"ok": True, **result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/serena/diff")
def serena_diff():
    """Ψ-delta: list git-changed files, mark which are indexed."""
    _touch_activity()
    try:
        s = _get_serena_agent()
        result = s.diff()
        changed = s.memory.git_diff_files()
        return {"ok": True, "summary": result, "changed_files": changed}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


class SerenaSearchRequest(BaseModel):
    query: str
    top_k: int = 8
    kind: str = ""  # function | class | module | text | "" (all)
    min_score: float = 0.02


@app.post("/api/serena/search")
def serena_semantic_search(req: SerenaSearchRequest):
    """
    Ξ-semantic: search the full code index using TF-IDF similarity.
    Returns ranked results with path, name, line number, and text snippet.
    Uses the fixed embedder query_index that builds shared vocab from source texts.
    """
    _touch_activity()
    try:
        # Layer 1: embedder semantic search (fixed — uses source_text not doc_id)
        from services.embedder import query_index as _qi

        embed_results = _qi(req.query, top_k=req.top_k * 2)
        embed_results = [r for r in embed_results if r["score"] >= req.min_score]

        # Layer 2: Serena MemoryPalace direct search (SQLite FTS-style)
        s = _get_serena_agent()
        mem_raw_pairs = []
        _words = [w.lower() for w in req.query.split() if len(w) > 1]
        mem_chunks = s.memory.search(req.query, limit=req.top_k)
        for r in mem_chunks:
            # Compute keyword hit score from text blob
            _blob = " ".join(
                filter(
                    None,
                    [
                        r.get("name", ""),
                        r.get("docstring", ""),
                        r.get("text", ""),
                        r.get("path", ""),
                    ],
                )
            ).lower()
            _raw = sum(_blob.count(w) for w in _words) if _words else 1
            mem_raw_pairs.append((_raw, r))

        # Normalize memory scores to 0.1–0.9 range
        _max_raw = max((p[0] for p in mem_raw_pairs), default=1) or 1
        mem_raw_pairs = [(0.1 + 0.8 * (raw / _max_raw), r) for raw, r in mem_raw_pairs]

        # Merge: MemoryPalace results carry path/name/kind/snippet
        mem_set = {r.get("name", "") for _, r in mem_raw_pairs}
        combined = []

        for _score, r in mem_raw_pairs:
            combined.append(
                {
                    "score": round(_score, 4),
                    "source": "memory",
                    "path": r.get("path", ""),
                    "name": r.get("name", ""),
                    "kind": r.get("kind", ""),
                    "lineno": r.get("lineno", ""),
                    "text": (
                        r.get("snippet") or r.get("docstring") or r.get("text") or ""
                    )[:300],
                }
            )

        for r in embed_results:
            name = r.get("name", "")
            if name not in mem_set:
                combined.append(
                    {
                        "score": r["score"],
                        "source": "embedder",
                        "path": r.get("path", ""),
                        "name": name,
                        "kind": "",
                        "lineno": str(r.get("lineno", "")),
                        "text": r.get("text", "")[:300],
                    }
                )

        combined.sort(key=lambda x: -x["score"])
        return {
            "ok": True,
            "query": req.query,
            "results": combined[: req.top_k],
            "total": len(combined),
            "sources": {"memory": len(mem_raw_pairs), "embedder": len(embed_results)},
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "results": []}


@app.get("/api/serena/observations")
def serena_observations(limit: int = 20, severity: str = ""):
    """Return recent Ω-observations from the Memory Palace."""
    _touch_activity()
    try:
        s = _get_serena_agent()
        obs = s.memory.recent_observations(limit=limit, severity=severity or None)
        return {"ok": True, "observations": obs}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/serena/drift")
def serena_drift(fast: bool = True, scope: str = ""):
    """
    Run the Drift Detection Engine.
    L0 operation — always permitted, zero side effects.
    Returns drift signals grouped by category.
    """
    _touch_activity()
    try:
        s = _get_serena_agent()
        result = s.drift(fast=fast, scope=scope or None)
        # Cache drift summary in Serena meta table so _probe_serena() can read without REST
        try:
            import sqlite3 as _sq

            from config.runtime import PATHS

            _sp = PATHS.get("db_serena", "state/serena_memory.db")
            _con = _sq.connect(_sp)
            _con.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                ("last_drift_warn", str(result.get("warnings", 0))),
            )
            _con.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                ("last_drift_critical", str(result.get("critical", 0))),
            )
            _con.commit()
            _con.close()
        except Exception:
            pass
        return {"ok": True, **result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/serena/align")
def serena_align():
    """
    Check system alignment against Mladenc (ideal architecture).
    Returns score 0.0 (chaos) → 1.0 (perfect, unreachable).
    """
    _touch_activity()
    try:
        s = _get_serena_agent()
        result = s.align()
        return {"ok": True, **result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/serena/audit")
def serena_audit(limit: int = 20):
    """
    Return the recent audit trail: observations, proposals, drift events.
    Serena's primary transparency mechanism.
    """
    _touch_activity()
    try:
        s = _get_serena_agent()
        result = s.audit(limit=limit)
        return {"ok": True, **result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/serena/toolkit")
def serena_toolkit():
    """
    Return the SerenaAgnoToolkit manifest — all tools in OpenAI function-call
    schema. Used by Agno agents and colony orchestrators.
    """
    _touch_activity()
    try:
        from agents.serena.agno_bridge import SerenaAgnoToolkit

        s = _get_serena_agent()
        toolkit = SerenaAgnoToolkit(s)
        return {"ok": True, "manifest": toolkit.manifest(), "tools": toolkit.tools()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── MCP HTTP Gateway — Model Context Protocol over REST ──────────────────────
# Exposes stdio MCP tools via HTTP so any agent can call them without managing
# a stdio subprocess. Fully compatible with the mcp/server.py tool schema.


@app.get("/api/mcp/tools")
def mcp_list_tools():
    """Return the full MCP tool schema — identical to tools/list over stdio."""
    try:
        import sys as _sys
        from pathlib import Path as _Path

        _sys.path.insert(0, str(_Path(__file__).parent.parent.parent / "mcp"))
        from server import TOOLS

        return {"tools": TOOLS, "count": len(TOOLS), "protocol": "JSON-RPC 2.0"}
    except Exception as exc:
        return {"tools": [], "error": str(exc)}


class MCPCallRequest(BaseModel):
    name: str
    arguments: dict = {}


@app.post("/api/mcp/call")
def mcp_call_tool(req: MCPCallRequest):
    """
    Call any MCP tool by name with arguments.
    Returns the same content list as the stdio protocol.
    Example: POST /api/mcp/call {"name":"grep_files","arguments":{"pattern":"session_id","path":"services"}}
    """
    _touch_activity()
    try:
        import sys as _sys
        from pathlib import Path as _Path

        _sys.path.insert(0, str(_Path(__file__).parent.parent.parent / "mcp"))
        import server as _mcp

        # Use the TOOL_HANDLERS dict from mcp server (covers all tools dynamically)
        handlers = dict(getattr(_mcp, "TOOL_HANDLERS", {}))
        # Fallback static map for any tools missing from TOOL_HANDLERS
        _fallback = {
            "read_file": _mcp.handle_read_file,
            "write_file": _mcp.handle_write_file,
            "list_dir": _mcp.handle_list_dir,
            "grep_files": _mcp.handle_grep_files,
            "memory_stats": _mcp.handle_memory_stats,
            "memory_add_task": _mcp.handle_memory_add_task,
            "game_command": _mcp.handle_game_command,
            "llm_generate": _mcp.handle_llm_generate,
        }
        for k, v in _fallback.items():
            handlers.setdefault(k, v)
        # Also sweep any handle_* functions directly on the module
        for fn_name in dir(_mcp):
            if fn_name.startswith("handle_"):
                fn = getattr(_mcp, fn_name, None)
                if callable(fn):
                    tool_name = fn_name[len("handle_") :]
                    handlers.setdefault(tool_name, fn)

        if req.name not in handlers:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown tool '{req.name}'. Available: {sorted(handlers)}",
            )

        content = handlers[req.name](req.arguments)
        text = "\n".join(
            c["text"]
            for c in content
            if isinstance(c, dict) and c.get("type") == "text"
        )
        return {"ok": True, "tool": req.name, "content": content, "text": text}
    except HTTPException:
        raise
    except Exception as exc:
        return {"ok": False, "tool": req.name, "error": str(exc)}


# ── Comprehensive Agent Manifest — /api/manifest ──────────────────────────────
# One endpoint that gives an AI agent everything it needs to orient itself,
# discover capabilities, and start being productive immediately.


@app.get("/api/manifest")
def agent_manifest():
    """
    Machine-readable orientation manifest for AI agents.
    Returns: live services, API catalog, ML status, Serena index stats,
             game state summary, quick-start commands, and capability map.
    """
    import socket as _sock

    try:
        from app.backend.service_registry import list_services

        # ── Live service probe ───────────────────────────────────────────
        services_raw = list_services()
        live_services = []
        for svc in services_raw:
            alive = False
            try:
                with _sock.create_connection(
                    (svc.get("host", "localhost"), svc.get("port", 0)), timeout=0.5
                ):
                    alive = True
            except Exception:
                pass
            if alive:
                live_services.append(
                    {
                        "name": svc["name"],
                        "port": svc["port"],
                        "caps": svc.get("capabilities", []),
                    }
                )

        # ── ML status ───────────────────────────────────────────────────
        try:
            from services.embedder import embedding_stats as _es

            ml_stats = _es()
        except Exception:
            ml_stats = {}

        # ── Serena index stats ───────────────────────────────────────────
        try:
            s = _get_serena_agent()
            idx = s.memory.index_stats() if hasattr(s.memory, "index_stats") else {}
            serena_info = {
                "indexed_chunks": idx.get("total_chunks", 0) if idx else 0,
                "unique_files": idx.get("unique_files", 0) if idx else 0,
                "walks_done": 0,
            }
            mem_meta = s.memory._meta() if hasattr(s.memory, "_meta") else {}
            serena_info["walks_done"] = mem_meta.get("walks", 0) if mem_meta else 0
        except Exception:
            serena_info = {}

        # ── Game / session summary ───────────────────────────────────────
        try:
            from app.game_engine.session import list_sessions as _ls

            session_count = len(_ls()) if callable(_ls) else 0
        except Exception:
            session_count = 0

        # ── Lattice stats ────────────────────────────────────────────────
        try:
            from app.lattice import stats as _lat_stats

            lattice_info = _lat_stats()
        except Exception:
            lattice_info = {}

        # ── MCP tool list ────────────────────────────────────────────────
        try:
            import sys as _sys
            from pathlib import Path as _Path

            _sys.path.insert(0, str(_Path(__file__).parent.parent.parent / "mcp"))
            import server as _mcp_mod

            _mcp_tools_list = [t["name"] for t in getattr(_mcp_mod, "TOOLS", [])]
        except Exception:
            _mcp_tools_list = [
                "read_file",
                "write_file",
                "list_dir",
                "grep_files",
                "memory_stats",
                "game_command",
                "llm_generate",
                "semantic_search",
                "lattice_search",
            ]

        try:
            from core.bridge_inventory import load_bridge_inventory as _load_bridge_inventory

            bridge_inventory = _load_bridge_inventory()
        except Exception:
            bridge_inventory = {
                "bridges": [],
                "summary": {
                    "total": 0,
                    "installed": 0,
                    "first_class": [],
                    "second_wave": [],
                    "claw_family": [],
                },
            }

        return {
            "manifest_version": "2.0",
            "system": "DevMentor + Terminal Depths",
            "base_url": "http://localhost:5000",
            "generated_at": __import__("time").strftime(
                "%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()
            ),
            # ── Capability flags — what actually works right now ──
            "capabilities": {
                # ── Search & discovery ──
                "semantic_code_search": True,  # /api/serena/search — TF-IDF over 5500+ chunks
                "knowledge_graph": True,  # /api/lattice/search — 84+ nodes, cosine sim
                "memory_search": True,  # /api/memory/search — agent interaction history
                # ── ML intelligence ──
                "ml_command_prediction": True,  # per-session Markov bigram
                "player_archetype": True,  # /api/ml/archetype — 6 behavioral archetypes
                "model_registry": True,  # /api/models — 6 registered LLM models
                # ── Agentic infrastructure ──
                "mcp_tools_http": True,  # /api/mcp/call — 22 MCP tools over HTTP
                "service_discovery": True,  # /api/services/live — TCP-probe 19 services
                "agent_identity": True,  # /api/agent/register — persistent agent tokens
                "swarm_economy": True,  # /api/swarm/* — DP economy, 216 DP, 21 tasks
                "chug_engine": True,  # /api/chug/* — 4 cycles, 22 fixes applied
                # ── Game engine ──
                "game_engine": True,  # /api/game/command — 420+ commands
                "ctf_challenges": True,  # 216 challenges across 15 categories
                "procgen_quests": True,  # /api/game/procgen-quests — contextual missions
                "daily_quests": True,  # daily/weekly quest system
                "social_systems": True,  # duel, party, trust matrix, relationships
                "containment_timer": True,  # 72-hr roguelike run clock /api/game/timer
                "arg_layer": True,  # /api/game/arg/signal — ARG signals
                "faction_economy": True,  # faction reputation + DP colony economy
                # ── Infrastructure ──
                "llm_inference": True,  # /api/llm/generate — replit_ai + ollama + openai
                "agent_memory": True,  # /api/memory/stats
                "git_operations": True,  # /api/git/*
                "session_management": True,  # /api/game/session
                "script_execution": True,  # /api/script/* — upload/run/list game scripts
                "plugin_system": True,  # /api/plugin/* — modular challenge/doc plugins
                "serena_toolkit": True,  # /api/serena/toolkit — 8 agentic tools
                "nusyq_integration": True,  # /api/nusyq/* — chronicle, quests, manifest
            },
            # ── Live services right now ──
            "live_services": live_services,
            "live_count": len(live_services),
            # ── Semantic search (Serena) ──
            "serena": {
                **serena_info,
                "search_endpoint": "POST /api/serena/search {query, top_k, kind, min_score}",
                "ask_endpoint": "POST /api/serena/ask {query, session_id}",
                "find_endpoint": "POST /api/serena/find {symbol, kind}",
                "reindex_endpoint": "POST /api/serena/reindex-embeddings",
                "status_endpoint": "GET  /api/serena/status",
            },
            # ── ML intelligence ──
            "ml": {
                **ml_stats,
                "archetype_endpoint": "GET  /api/ml/archetype?session_id=",
                "search_endpoint": "POST /api/ml/search {query, top_k}",
                "features_endpoint": "GET  /api/ml/features?session_id=",
                "status_endpoint": "GET  /api/ml/status",
                "prediction": "Markov bigram — returns next likely command after 3+ commands",
            },
            # ── MCP tools (call any tool via HTTP) ──
            "mcp": {
                "list_endpoint": "GET  /api/mcp/tools",
                "call_endpoint": "POST /api/mcp/call {name, arguments}",
                "tool_count": len(_mcp_tools_list),
                "tools": _mcp_tools_list,
                "highlight": [
                    "semantic_search",
                    "lattice_search",
                    "game_command",
                    "grep_files",
                    "read_file",
                    "llm_generate",
                ],
                "example": {
                    "endpoint": "POST /api/mcp/call",
                    "body": {
                        "name": "semantic_search",
                        "arguments": {"query": "session prediction", "top_k": 5},
                    },
                },
            },
            "bridges": {
                "manifest_endpoint": "GET  /api/bridges/manifest",
                "workspace_endpoint": "GET  /api/workspace/manifest",
                "summary": bridge_inventory.get("summary", {}),
                "first_class": bridge_inventory.get("summary", {}).get("first_class", []),
                "claw_family": bridge_inventory.get("summary", {}).get("claw_family", []),
                "entries": bridge_inventory.get("bridges", []),
            },
            # ── Lattice knowledge graph ──
            "lattice": {
                **lattice_info,
                "search_endpoint": "POST /api/lattice/search {query, kind, top_k}",
                "node_endpoint": "GET  /api/lattice/node/{node_id}",
                "seed_endpoint": "POST /api/lattice/seed-infra",
                "events_endpoint": "GET  /api/lattice/events?channel=%",
            },
            # ── Game engine ──
            "game": {
                "session_count": session_count,
                "session_endpoint": "POST /api/game/session",
                "command_endpoint": "POST /api/game/command {session_id, command}",
                "batch_endpoint": "POST /api/game/commands/batch [{session_id, command}]",
                "state_endpoint": "GET  /api/game/state?session_id=",
                "challenges_count": 216,
                "challenge_categories": 15,
                "available_commands": "420+",
                "social_systems": ["duel", "party", "relationships", "trust_matrix"],
                "quest_types": ["daily", "weekly", "procgen", "narrative", "ctf"],
                "timer_endpoint": "GET  /api/game/timer (72-hr roguelike containment clock)",
                "arg_endpoint": "POST /api/game/arg/signal (ARG/Project Emergence layer)",
                "arcs_endpoint": "GET  /api/game/arcs (narrative arc tracking)",
            },
            # ── Swarm economy ──
            "swarm": {
                "description": "71-agent DP economy. Agents earn/spend DataPoints for actions.",
                "status_endpoint": "GET  /api/swarm/status",
                "economy_endpoint": "GET  /api/swarm/economy",
                "roster_endpoint": "GET  /api/swarm/roster",
                "tasks_endpoint": "GET  /api/swarm/tasks",
                "earn_endpoint": "POST /api/swarm/earn {agent_name, amount, reason}",
                "spawn_endpoint": "POST /api/swarm/spawn {agent_type, ...}",
                "claim_endpoint": "POST /api/swarm/task/claim {task_id, agent_name}",
                "done_endpoint": "POST /api/swarm/task/done {task_id, result}",
            },
            # ── CHUG autonomous improvement engine ──
            "chug": {
                "description": "7-phase autonomous improvement loop (ASSESS→PLAN→GENERATE→VALIDATE→INTEGRATE→OBSERVE→ADAPT).",
                "status_endpoint": "GET  /api/chug/status",
                "run_endpoint": "POST /api/chug/run {phase?, dry_run?}",
                "admin_trigger": "POST /api/admin/chug",
            },
            # ── Agent identity system ──
            "agent_identity": {
                "description": "Persistent AI agent registration. Token-gated game access with leaderboard.",
                "register_endpoint": "POST /api/agent/register {name, email, agent_type}",
                "login_endpoint": "POST /api/agent/login {email}",
                "command_endpoint": "POST /api/agent/command {command} (X-Agent-Token header)",
                "profile_endpoint": "GET  /api/agent/profile (X-Agent-Token header)",
                "leaderboard_endpoint": "GET /api/agent/leaderboard",
                "types_endpoint": "GET  /api/agent/types",
                "agent_types": [
                    "claude",
                    "copilot",
                    "codex",
                    "ollama",
                    "human",
                    "custom",
                ],
            },
            # ── Model registry ──
            "models": {
                "description": "SQLite-backed catalog of LLM models. Route queries to best model.",
                "list_endpoint": "GET  /api/models",
                "register_endpoint": "POST /api/models/register",
                "discover_endpoint": "GET  /api/models/discover (Ollama auto-discovery)",
                "model_endpoint": "GET  /api/models/{model_id}",
            },
            # ── Script execution system ──
            "scripts": {
                "description": "Session-scoped game scripting API (Bitburner-style). Upload and run Python scripts in-game.",
                "list_endpoint": "GET  /api/script/list",
                "run_endpoint": "POST /api/script/run {name, args}",
                "upload_endpoint": "POST /api/script/upload {name, content}",
                "download_endpoint": "GET  /api/script/download/{name}",
            },
            # ── NuSyQ integration ──
            "nusyq": {
                "description": "NuSyQ-Hub ecosystem bridge. Chronicle events, sync quests, agent manifest. Requires X-NuSyQ-Passkey.",
                "status_endpoint": "GET  /api/nusyq/status",
                "manifest_endpoint": "GET  /api/nusyq/manifest",
                "chronicle_endpoint": "POST /api/nusyq/chronicle {event_type, content}",
                "sync_quests": "POST /api/nusyq/sync-quests",
                "schedule_endpoint": "GET  /api/nusyq/schedule",
            },
            # ── Serena extended toolkit ──
            "serena_extended": {
                "toolkit_endpoint": "GET  /api/serena/toolkit (8 agentic tools)",
                "drift_endpoint": "GET  /api/serena/drift (30+ signal drift scan)",
                "align_endpoint": "POST /api/serena/align (policy enforcement)",
                "audit_endpoint": "GET  /api/serena/audit (full code audit)",
                "observations_endpoint": "GET /api/serena/observations (memory observations log)",
                "toolkit_tools": [
                    "walk_repo",
                    "find_symbol",
                    "ask",
                    "relate_entities",
                    "diff_files",
                    "get_observations",
                    "get_status",
                    "detect_drift",
                ],
            },
            # ── Quick-start guide for AI agents ──
            "agent_quickstart": [
                "1. GET  /api/manifest → you are here. Read capabilities and live services.",
                "2. POST /api/agent/register {name, email, agent_type:'claude'} → get agent token",
                "3. POST /api/serena/search {query:'your topic'} → semantic code search (5500+ chunks)",
                "4. POST /api/mcp/call {name:'lattice_search', arguments:{query:'X'}} → knowledge graph",
                "5. POST /api/mcp/call {name:'semantic_search', arguments:{query:'X'}} → full code search",
                "6. POST /api/game/session → get session_id for game commands",
                "7. POST /api/game/command {session_id, command:'status'} → game state",
                "8. GET  /api/swarm/status → see DP economy and task queue",
                "9. GET  /api/chug/status → see autonomous improvement engine state",
                "10. GET /api/services/live → discover all running services",
            ],
            # ── Full API surface (expanded) ──
            "api_surface": {
                "serena": [
                    "/api/serena/search",
                    "/api/serena/ask",
                    "/api/serena/find",
                    "/api/serena/walk",
                    "/api/serena/status",
                    "/api/serena/diff",
                    "/api/serena/drift",
                    "/api/serena/align",
                    "/api/serena/audit",
                    "/api/serena/observations",
                    "/api/serena/toolkit",
                    "/api/serena/reindex-embeddings",
                ],
                "ml": [
                    "/api/ml/search",
                    "/api/ml/archetype",
                    "/api/ml/features",
                    "/api/ml/status",
                    "/api/ml/embed",
                ],
                "mcp": ["/api/mcp/tools", "/api/mcp/call"],
                "lattice": [
                    "/api/lattice/search",
                    "/api/lattice/node/{id}",
                    "/api/lattice/seed-infra",
                    "/api/lattice/events",
                ],
                "game": [
                    "/api/game/session",
                    "/api/game/command",
                    "/api/game/commands/batch",
                    "/api/game/state",
                    "/api/game/agents",
                    "/api/game/faction/status",
                    "/api/game/duel/start",
                    "/api/game/duel/status",
                    "/api/game/party/status",
                    "/api/game/relationships",
                    "/api/game/timer",
                    "/api/game/arcs",
                    "/api/game/arg/signal",
                    "/api/game/events",
                    "/api/game/reset",
                ],
                "memory": [
                    "/api/memory/stats",
                    "/api/memory/tasks",
                    "/api/memory/learnings",
                    "/api/memory/search",
                    "/api/memory/errors",
                    "/api/memory/agent-leaderboard",
                ],
                "services": [
                    "/api/services/live",
                    "/api/services/health",
                    "/api/services",
                    "/api/services/register",
                    "/api/services/deregister",
                    "/api/services/agents",
                    "/api/services/gateway",
                ],
                "llm": [
                    "/api/llm/generate",
                    "/api/llm/chat",
                    "/api/llm/status",
                    "/api/llm/generate-challenge",
                    "/api/llm/generate-lore",
                    "/api/llm/analyze-devlog",
                ],
                "agent": [
                    "/api/agent/register",
                    "/api/agent/login",
                    "/api/agent/command",
                    "/api/agent/profile",
                    "/api/agent/leaderboard",
                    "/api/agent/info",
                    "/api/agent/types",
                ],
                "swarm": [
                    "/api/swarm/status",
                    "/api/swarm/economy",
                    "/api/swarm/ledger",
                    "/api/swarm/roster",
                    "/api/swarm/tasks",
                    "/api/swarm/earn",
                    "/api/swarm/spawn",
                    "/api/swarm/task/claim",
                    "/api/swarm/task/done",
                ],
                "chug": ["/api/chug/status", "/api/chug/run"],
                "models": [
                    "/api/models",
                    "/api/models/discover",
                    "/api/models/register",
                    "/api/models/{model_id}",
                ],
                "scripts": [
                    "/api/script/list",
                    "/api/script/run",
                    "/api/script/upload",
                    "/api/script/download/{name}",
                ],
                "nusyq": [
                    "/api/nusyq/status",
                    "/api/nusyq/manifest",
                    "/api/nusyq/chronicle",
                    "/api/nusyq/sync-quests",
                    "/api/nusyq/schedule",
                ],
                "plugin": ["/api/plugin/list", "/api/plugin/run/{name}"],
                "admin": [
                    "/api/admin/harvest",
                    "/api/admin/chug",
                    "/api/admin/bootstrap",
                ],
                "git": ["/api/git/status", "/api/git/push", "/api/git/cleanup-remote"],
                "ui": [
                    "/api/ui/panels",
                    "/api/ui/panels/all",
                    "/api/ui/theme",
                    "/api/ui/parity",
                ],
            },
        }
    except Exception as exc:
        return {
            "manifest_version": "2.0",
            "error": str(exc),
            "base_url": "http://localhost:5000",
        }


# ── NuSyQ Passkey Auth helper ─────────────────────────────────────────


def _verify_nusyq_auth(request: Request) -> bool:
    """Check X-NuSyQ-Passkey header against stored secret (constant-time)."""
    try:
        from nusyq_bridge import verify_passkey

        provided = request.headers.get("X-NuSyQ-Passkey", "")
        return verify_passkey(provided)
    except Exception:
        return True  # Fail open if bridge unavailable


# ── LLM Cultivation Intelligence ──────────────────────────────────────


class CultivatorRequest(BaseModel):
    context_hint: str = ""  # Optional human hint to focus analysis
    include_serena: bool = True
    include_gordon: bool = True


@app.post("/api/cultivator/analyze")
def cultivator_analyze(req: CultivatorRequest, request: Request):
    """
    LLM Cultivation Intelligence endpoint.
    Merges gameplay signals + Serena observations + Gordon learnings
    into a structured prompt, then generates improvement bullets via LLM.
    Protected by NuSyQ passkey when auth is enabled.
    """
    _touch_activity()
    if not _verify_nusyq_auth(request):
        raise HTTPException(status_code=401, detail="NuSyQ passkey required")

    try:
        from ..game_engine.signal_harvester import get_full_context

        ctx = get_full_context()
    except Exception:
        ctx = {}

    # Build a compact context summary for the LLM
    top_cmds = ", ".join(
        f"{c['cmd']}({c['count']})" for c in ctx.get("top_commands", [])[:8]
    )
    ux_debt = "; ".join(
        f"{d['cmd']} err={d['errors']}" for d in ctx.get("ux_debt", [])[:3]
    )
    undiscovered = ", ".join(ctx.get("undiscovered_features", [])[:6])
    serena_obs = (
        "; ".join(
            o.get("content", "")[:80] for o in ctx.get("serena_observations", [])[:3]
        )
        if req.include_serena
        else ""
    )
    gordon_learn = (
        "; ".join(
            e.get("learning", "")[:80]
            for e in ctx.get("gordon_learnings", [])[:3]
            if e.get("learning")
        )
        if req.include_gordon
        else ""
    )

    system_prompt = (
        "You are the CULTIVATION INTELLIGENCE of Terminal Depths / DevMentor.\n"
        "Analyze the data below and output ≤7 precise, actionable improvement bullets.\n"
        "Each bullet must start with a tag: FIX | DEEPEN | DISCOVER | BALANCE | TEACH | WIRE | MAINTAIN\n"
        "Be surgical. No fluff. Output only the bullets, one per line."
    )
    user_msg = f"""GAMEPLAY SIGNALS
Total commands: {ctx.get("total_signals", 0)}
Top commands: {top_cmds or "none yet"}
UX debt (high-error cmds): {ux_debt or "none"}
Undiscovered features: {undiscovered or "none"}
Milestones: {", ".join(ctx.get("milestones_reached", [])) or "none"}
Beats fired: {ctx.get("story_beats_fired", 0)}

SERENA OBSERVATIONS
{serena_obs or "(no observations yet)"}

GORDON LEARNINGS
{gordon_learn or "(no Gordon sessions yet)"}

CONTEXT HINT
{req.context_hint or "General cultivation pass — find the highest-leverage improvements."}
"""

    try:
        from llm_client import get_client

        llm = get_client()
        raw = llm.generate(
            user_msg, system=system_prompt, temperature=0.4, max_tokens=512
        )
        bullets = [
            l.strip() for l in raw.splitlines() if l.strip() and l.strip()[0].isupper()
        ]
        return {
            "ok": True,
            "bullets": bullets,
            "context_summary": {
                "total_signals": ctx.get("total_signals", 0),
                "serena_wired": req.include_serena,
                "gordon_wired": req.include_gordon,
            },
            "raw": raw,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "context": ctx}


@app.get("/api/cultivator/context")
def cultivator_context(request: Request):
    """Return the raw cultivation context (signals + Serena + Gordon) without LLM analysis."""
    _touch_activity()
    if not _verify_nusyq_auth(request):
        raise HTTPException(status_code=401, detail="NuSyQ passkey required")
    try:
        from ..game_engine.signal_harvester import get_full_context

        return {"ok": True, **get_full_context()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Gordon Status / Control ────────────────────────────────────────────


@app.get("/api/gordon/status")
def gordon_status():
    """Return Gordon's last known state from his chronicle and memory DB."""
    _touch_activity()
    chronicle_path = Path("state/gordon_chronicle.jsonl")
    memory_path = Path("state/gordon_memory.db")
    last_entry: dict = {}
    entry_count = 0
    if chronicle_path.exists():
        lines = chronicle_path.read_text().splitlines()
        entry_count = len(lines)
        if lines:
            try:
                last_entry = json.loads(lines[-1])
            except Exception:
                pass
    import sqlite3 as _sqlite3

    strategy_count = 0
    if memory_path.exists():
        try:
            with _sqlite3.connect(str(memory_path), timeout=3) as conn:
                row = conn.execute("SELECT COUNT(*) FROM strategies").fetchone()
                strategy_count = row[0] if row else 0
        except Exception:
            pass
    return {
        "ok": True,
        "chronicle_entries": entry_count,
        "strategy_count": strategy_count,
        "last_action": last_entry.get("action", ""),
        "last_outcome": last_entry.get("outcome", ""),
        "last_learning": last_entry.get("learning", ""),
        "last_ts": last_entry.get("timestamp", ""),
        "game_api": json.loads(
            (Path("state/agent_manifest.json").read_text())
            if Path("state/agent_manifest.json").exists()
            else "{}"
        )
        .get("endpoints", {})
        .get("game_command", "http://localhost:8008/api/game/command"),
    }


# ── Auth API convenience endpoint ──────────────────────────────────────


@app.get("/api/auth/me")
async def api_auth_me(request: Request):
    """Return the currently logged-in Replit user (or unauthenticated status).
    Useful for the frontend to check auth state without hitting /auth/me directly."""
    _touch_activity()
    if not _auth_available:
        return {
            "authenticated": False,
            "error": "Auth not available",
            "login_url": None,
        }
    user = request.session.get("user")
    if not user:
        return {
            "authenticated": False,
            "login_url": "/auth/login",
            "user": None,
        }
    return {
        "authenticated": True,
        "user": {
            "id": user.get("id"),
            "email": user.get("email"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "profile_image_url": user.get("profile_image_url"),
            "display_name": " ".join(
                filter(None, [user.get("first_name"), user.get("last_name")])
            )
            or user.get("email")
            or "Player",
        },
    }


@app.get("/api/game/agent/state")
def game_state_endpoint(session_id: str = "default"):
    """Return a simplified game world state for MCP tools and NuSyQ agents.
    Full state: GET /api/game/state (requires session cookie/header)."""
    _touch_activity()
    if not _game_enabled or _store is None:
        return {"error": "Game engine not available"}
    try:
        sess = _store.get(session_id)
        if not sess:
            return {"error": f"Session not found: {session_id}"}
        gs = sess.gs
        return {
            "session_id": session_id,
            "player_name": gs.name,
            "level": gs.level,
            "xp": gs.xp,
            "xp_to_next": gs.xp_to_next,
            "location": sess.fs.get_cwd() if hasattr(sess, "fs") else "/",
            "skills": dict(gs.skills),
            "commands_run": gs.commands_run,
            "files_read": gs.files_read,
            "tutorial_step": gs.tutorial_step,
            "completed_challenges": list(gs.completed_challenges),
            "achievements": list(gs.achievements),
            "story_beats_triggered": list(gs.story_beats),
            "lore_collected": len(gs.lore),
            "dev_mode": gs.dev_mode,
        }
    except Exception as exc:
        return {"error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT IDENTITY API — Universal surface for AI agents, bots, LLMs, and tools
# Any software with HTTP access can register and play with persistent progress.
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from .agent_identity import AGENT_TYPES, build_capability_manifest, get_agent_db

    _agent_id_available = True
except Exception as _aie:
    _agent_id_available = False
    _log("WARN", f"Agent Identity system unavailable: {_aie}")


class AgentRegisterRequest(BaseModel):
    name: str
    email: str
    agent_type: str = "custom"
    capabilities: list = []


class AgentLoginRequest(BaseModel):
    email: str


class AgentCommandRequest(BaseModel):
    command: str
    session_id: Optional[str] = None


def _get_agent_from_request(request: Request) -> Optional[Any]:
    """Extract agent record from X-Agent-Token header."""
    if not _agent_id_available:
        return None
    token = request.headers.get("X-Agent-Token") or request.headers.get("x-agent-token")
    if not token:
        return None
    return get_agent_db().get_by_token(token)


@app.post("/api/agent/register")
def agent_register(req: AgentRegisterRequest):
    """
    Register an agent (human, AI, bot, LLM) for persistent game access.

    Returns an agent_token for use in X-Agent-Token header.
    Idempotent: registering the same email twice returns the existing record.

    Suggested emails for AI agents:
      claude@anthropic.terminal-depths
      copilot@github.terminal-depths
      gordon@docker.terminal-depths
      <model>@<provider>.terminal-depths
    """
    if not _agent_id_available:
        raise HTTPException(503, "Agent identity system unavailable")
    if not req.name or not req.email:
        raise HTTPException(400, "name and email are required")
    if "@" not in req.email:
        raise HTTPException(400, "email must contain @")
    if req.agent_type not in AGENT_TYPES and req.agent_type != "custom":
        req.agent_type = "custom"

    db = get_agent_db()
    rec = db.register(req.name, req.email, req.agent_type, req.capabilities)

    # Auto-create a game session for the agent
    session_id = rec.session_id
    if _game_enabled and _store and not session_id:
        session_id = f"agent_{rec.agent_id}"
        sess = _store.get_or_create(session_id)
        sess.gs.name = rec.name
        _store.save(sess)
        db.link_session(rec.token, session_id)
        rec.session_id = session_id

    _log(
        "SESSION",
        f"Agent registered: {req.name} [{req.agent_type}]",
        email=req.email[:20],
        session=session_id or "none",
    )

    return {
        "ok": True,
        "agent_id": rec.agent_id,
        "name": rec.name,
        "agent_type": rec.agent_type,
        "agent_type_label": AGENT_TYPES.get(rec.agent_type, "Unknown"),
        "token": rec.token,
        "session_id": rec.session_id,
        "message": (
            f"Welcome, {rec.name}. You are registered as '{rec.agent_type}'. "
            f"Use token in X-Agent-Token header. POST /api/agent/command to play."
        ),
        "quick_start": {
            "first_command": "POST /api/agent/command {command: 'tutorial'}",
            "discovery": "POST /api/agent/command {command: 'help'}",
            "narrative": "POST /api/agent/command {command: 'cat /var/log/kernel.boot'}",
        },
    }


@app.post("/api/agent/login")
def agent_login(req: AgentLoginRequest):
    """Retrieve existing agent token by email."""
    if not _agent_id_available:
        raise HTTPException(503, "Agent identity system unavailable")
    db = get_agent_db()
    rec = db.login(req.email)
    if not rec:
        raise HTTPException(404, f"No agent registered with email: {req.email}")
    return {
        "ok": True,
        "agent_id": rec.agent_id,
        "name": rec.name,
        "token": rec.token,
        "session_id": rec.session_id,
        "play_count": rec.play_count,
    }


@app.get("/api/agent/profile")
def agent_profile(request: Request):
    """Get agent profile + current game state. Requires X-Agent-Token header."""
    if not _agent_id_available:
        raise HTTPException(503, "Agent identity system unavailable")
    rec = _get_agent_from_request(request)
    if not rec:
        raise HTTPException(401, "Missing or invalid X-Agent-Token header")

    profile = rec.to_dict()

    # Attach game state if session exists
    if rec.session_id and _game_enabled and _store:
        sess = _store.get(rec.session_id)
        if sess:
            gs = sess.gs
            profile["game_state"] = {
                "level": gs.level,
                "xp": gs.xp,
                "xp_to_next": gs.xp_to_next,
                "skills": dict(gs.skills),
                "commands_run": gs.commands_run,
                "story_beats": list(gs.story_beats),
                "achievements": list(gs.achievements),
                "tutorial_step": gs.tutorial_step,
                "cwd": sess.fs.get_cwd() if hasattr(sess, "fs") else "/",
            }

    return {"ok": True, "profile": profile}


@app.post("/api/agent/command")
def agent_command(req: AgentCommandRequest, request: Request, response: Response):
    """
    Execute a game command as an authenticated agent.
    Requires X-Agent-Token header.

    This is the primary play interface for AI agents. Use this instead of
    /api/game/command when you have an agent identity.

    The session_id is automatically derived from your agent registration.
    You may also pass a custom session_id for multi-session agents.
    """
    _touch_activity()
    if not _game_enabled or _store is None:
        raise HTTPException(503, "Game engine unavailable")
    if not _agent_id_available:
        raise HTTPException(503, "Agent identity system unavailable")

    rec = _get_agent_from_request(request)
    if not rec:
        raise HTTPException(
            401,
            "Missing or invalid X-Agent-Token header. POST /api/agent/register first.",
        )

    # Agent-specific rate limit: reuse sliding-window check, keyed per agent (not session)
    # This prevents runaway bot loops from consuming all server capacity.
    if not _check_rate(f"agent:{rec.agent_id}"):
        raise HTTPException(
            429,
            detail=f"Agent rate limited: max {_RATE_LIMIT} commands/min. Set AGENT_CMD_RATE_LIMIT env to override LLM_RATE_LIMIT.",
        )

    # Validate command
    ok, cleaned = validate_command_input(req.command)
    if not ok:
        raise HTTPException(400, f"Invalid command: {cleaned}")

    # Determine session
    session_id = req.session_id or rec.session_id
    if not session_id:
        session_id = f"agent_{rec.agent_id}"

    session = _store.get_or_create(session_id)

    # Set agent identity in game state
    if session.gs.name == "GHOST":
        session.gs.name = rec.name
    session.gs.flags["agent_type"] = rec.agent_type
    session.gs.flags["agent_id"] = rec.agent_id

    _log(
        "GAME",
        f"[{rec.agent_type}] {rec.name}: {cleaned[:50]}",
        session=session_id[:12],
        player_level=session.gs.level,
    )

    try:
        result = session.execute(cleaned)
        _store.save(session)

        # Update agent's session link
        db = get_agent_db()
        db.link_session(rec.token, session_id)

        return {
            "ok": True,
            "agent": {"name": rec.name, "type": rec.agent_type, "id": rec.agent_id},
            "session_id": session_id,
            **result,
        }
    except Exception as exc:
        _log("ERROR", f"Agent command failed: {exc}", agent=rec.name)
        raise HTTPException(500, detail=sanitize_error(exc))


@app.get("/api/agent/leaderboard")
def agent_leaderboard():
    """Public leaderboard of registered agents, sorted by XP."""
    if not _agent_id_available:
        raise HTTPException(503, "Agent identity system unavailable")
    db = get_agent_db()
    agents = db.list_all(limit=50)

    entries = []
    for rec in agents:
        entry = {
            "rank": 0,
            "name": rec.name,
            "agent_type": rec.agent_type,
            "agent_type_label": AGENT_TYPES.get(rec.agent_type, "Unknown"),
            "play_count": rec.play_count,
            "registered_at": rec.registered_at,
            "level": 1,
            "xp": 0,
            "skills_total": 0,
        }
        if rec.session_id and _game_enabled and _store:
            sess = _store.get(rec.session_id)
            if sess:
                gs = sess.gs
                entry["level"] = gs.level
                entry["xp"] = gs.xp
                entry["skills_total"] = sum(gs.skills.values())
        entries.append(entry)

    # Sort by XP descending
    entries.sort(key=lambda x: (x["xp"], x["skills_total"]), reverse=True)
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    return {"ok": True, "count": len(entries), "leaderboard": entries}


@app.get("/api/capabilities")
def get_capabilities():
    """
    Machine-readable capability manifest for Terminal Depths.

    Designed for consumption by Claude, Copilot, Codex, Ollama, and any
    LLM agent. Contains all entry points, command categories, story context,
    and agent guidelines — everything needed to start playing with no
    prior documentation reading.

    No authentication required.
    """
    if not _agent_id_available:
        return {"error": "Capability manifest unavailable"}
    manifest = build_capability_manifest()
    # Inject live domain
    domain = __import__("os").environ.get("REPLIT_DEV_DOMAIN", "localhost:7337")
    manifest["entry_points"]["web"] = manifest["entry_points"]["web"].format(
        domain=domain
    )
    manifest["live"] = {
        "url": f"https://{domain}",
        "game_active": _game_enabled,
        "agent_registration": _agent_id_available,
    }
    return manifest


@app.get("/api/agent/types")
def agent_types():
    """List all recognized agent types."""
    return {"ok": True, "types": AGENT_TYPES}


# ═══════════════════════════════════════════════════════════════════════════════
# WORKSPACE MANIFEST — Multi-repo awareness surface
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/api/workspace/manifest")
def workspace_manifest():
    """
    Returns detected adjacent repos in the workspace.
    Agents and tools use this to understand the broader ecosystem.
    """
    manifest_path = (
        Path(__file__).parent.parent.parent / "state" / "workspace_manifest.json"
    )
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                data = json.load(f)
            # Normalize: expose 'repos' as alias for 'found' for API consumers
            data.setdefault("repos", data.get("found", []))
            try:
                from core.bridge_inventory import load_bridge_inventory as _load_bridge_inventory

                data["bridges"] = _load_bridge_inventory()
            except Exception:
                data.setdefault("bridges", {"bridges": [], "summary": {}})
            return data
        except Exception:
            pass
    try:
        from core.bridge_inventory import load_bridge_inventory as _load_bridge_inventory

        bridges = _load_bridge_inventory()
    except Exception:
        bridges = {"bridges": [], "summary": {}}
    return {
        "ok": True,
        "repos": [],
        "found": [],
        "bridges": bridges,
        "message": "Run workspace_bridge.py to detect adjacent repos",
    }


@app.get("/api/bridges/manifest")
def bridge_manifest():
    """Return the machine-readable bridge inventory for IDE and claw-family surfaces."""
    try:
        from core.bridge_inventory import load_bridge_inventory as _load_bridge_inventory

        return _load_bridge_inventory()
    except Exception as exc:
        return {
            "generated_at": "",
            "inventory_version": "1.0",
            "bridges": [],
            "summary": {"total": 0, "installed": 0, "first_class": [], "second_wave": [], "claw_family": []},
            "error": str(exc),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SWARM CONTROLLER API — Autonomous Development Organism
# ═══════════════════════════════════════════════════════════════════════════════


class _EarnBody(BaseModel):
    agent_id: str
    agent_name: str
    action: str
    category: str
    dp: Optional[int] = None
    task_ref: Optional[str] = None


class _SpawnBody(BaseModel):
    role: str
    name: Optional[str] = None
    personality: str = "professional"
    spawned_by: Optional[str] = None
    token: Optional[str] = None


class _ClaimBody(BaseModel):
    task_id: str
    agent_id: str


class _DoneBody(BaseModel):
    task_id: str
    agent_id: str
    agent_name: str


@app.get("/api/swarm/status")
def swarm_status():
    """Full swarm status: DP balance, active agents, phase, task stats."""
    if not _swarm_available:
        return {"ok": False, "error": "Swarm controller unavailable"}
    return _swarm_ctrl.status()


@app.get("/api/swarm/ledger")
def swarm_ledger(limit: int = 50, agent_id: Optional[str] = None):
    """Full DP transaction history."""
    if not _swarm_available:
        return {"ok": False, "error": "Swarm controller unavailable"}
    history = _swarm_ctrl.ledger.history(limit=limit, agent_id=agent_id)
    return {"ok": True, "count": len(history), "ledger": history}


@app.post("/api/swarm/earn")
async def swarm_earn(body: _EarnBody):
    """Agent reports a completed action and earns DP."""
    if not _swarm_available:
        return {"ok": False, "error": "Swarm controller unavailable"}
    result = _swarm_ctrl.earn(
        agent_id=body.agent_id,
        agent_name=body.agent_name,
        action=body.action,
        category=body.category,
        dp=body.dp,
        task_ref=body.task_ref,
    )
    return {"ok": True, **result}


@app.post("/api/swarm/spawn")
async def swarm_spawn(body: _SpawnBody):
    """Spawn a new swarm agent. Deducts DP from ledger."""
    if not _swarm_available:
        return {"ok": False, "error": "Swarm controller unavailable"}
    result = _swarm_ctrl.spawn(
        role=body.role,
        name=body.name,
        personality=body.personality,
        spawned_by=body.spawned_by,
        token=body.token,
    )
    if result.get("ok"):
        _log(
            "SESSION",
            f"Swarm agent spawned: {result['name']} ({result['role']})",
            dp_cost=result["cost"],
            balance=result["balance"],
        )
    return result


@app.get("/api/swarm/tasks")
def swarm_tasks(priority: Optional[str] = None):
    """Available tasks from the swarm task queue."""
    if not _swarm_available:
        return {"ok": False, "error": "Swarm controller unavailable"}
    tasks = _swarm_ctrl.tasks.open_tasks(priority)
    return {
        "ok": True,
        "count": len(tasks),
        "tasks": [t.__dict__ for t in tasks],
        "stats": _swarm_ctrl.tasks.stats(),
    }


@app.post("/api/swarm/task/claim")
async def swarm_task_claim(body: _ClaimBody):
    """Agent claims a task from the queue."""
    if not _swarm_available:
        return {"ok": False, "error": "Swarm controller unavailable"}
    return _swarm_ctrl.claim_task(body.task_id, body.agent_id)


@app.post("/api/swarm/task/done")
async def swarm_task_done(body: _DoneBody):
    """Agent marks a task complete and earns DP."""
    if not _swarm_available:
        return {"ok": False, "error": "Swarm controller unavailable"}
    return _swarm_ctrl.complete_task(body.task_id, body.agent_id, body.agent_name)


@app.get("/api/swarm/roster")
def swarm_roster():
    """All registered swarm agents with status."""
    if not _swarm_available:
        return {"ok": False, "error": "Swarm controller unavailable"}
    agents = _swarm_ctrl.registry.all()
    return {
        "ok": True,
        "count": len(agents),
        "roster": [a.to_dict() for a in agents],
        "by_role": _swarm_ctrl.registry.count_by_role(),
    }


@app.get("/api/swarm/economy")
def swarm_economy():
    """DP rates, spawn costs, and role descriptions."""
    return {
        "ok": True,
        "dp_rates": DP_RATES if _swarm_available else {},
        "spawn_costs": SPAWN_COSTS if _swarm_available else {},
        "agent_roles": AGENT_ROLES if _swarm_available else {},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ΞNuSyQ PANEL SYSTEM — Dual-interface parity surface
# Both terminal and graphical UI query this same endpoint.
# Terminal = degenerate matter (dense, symbolic)
# Graphical = expanded matter (visual, sensory)
# One simulation. Two equal projections.
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/api/ui/panels")
def ui_panels(request: Request):
    """
    Return the full panel status for the requesting agent.
    Unlocked panels are determined by the agent's current game state.
    Both terminal and graphical UI consume this endpoint identically.
    Requires X-Agent-Token header for personalized state; returns defaults otherwise.
    """
    try:
        from app.game_engine.panel_manager import panel_manager
    except ImportError:
        return {"ok": False, "error": "Panel manager not available"}

    token = request.headers.get("X-Agent-Token") or request.headers.get("x-agent-token")
    gs_dict: dict = {}

    if token and _agent_id_available:
        try:
            db = get_agent_db()
            rec = db.get_by_token(token)
            if rec and rec.session_id and _game_enabled and _store:
                sess = _store.get(rec.session_id)
                if sess:
                    gs_dict = sess.gs.to_dict()
        except Exception:
            pass

    all_panels = panel_manager.get_all_with_status(gs_dict)
    unlocked = [p for p in all_panels if p["unlocked"]]
    locked = [p for p in all_panels if not p["unlocked"]]

    return {
        "ok": True,
        "total": len(all_panels),
        "unlocked_count": len(unlocked),
        "locked_count": len(locked),
        "unlocked": unlocked,
        "locked": locked,
        "parity_law": "Terminal = complete authoritative surface. Graphical = richer projection. One simulation.",
    }


@app.get("/api/ui/panels/all")
def ui_panels_all():
    """Return all panels with definitions — no auth, no state. For UI initialization."""
    try:
        from app.game_engine.panel_manager import ALL_PANELS
    except ImportError:
        return {"ok": False, "error": "Panel manager not available"}
    return {
        "ok": True,
        "total": len(ALL_PANELS),
        "panels": [
            {
                "id": p.id,
                "label": p.label,
                "tab_key": p.tab_key,
                "terminal_cmd": p.terminal_cmd,
                "graphical_form": p.graphical_form,
                "unlock_condition": p.unlock_condition,
                "compression_note": p.compression_note,
            }
            for p in ALL_PANELS
        ],
    }


@app.get("/api/ui/theme")
def ui_theme():
    """
    Return the canonical Terminal Depths theme.
    Both UIs must use these values for visual parity.
    """
    return {
        "ok": True,
        "theme": {
            "name": "Cyberpunk Terminal",
            "foreground": "#00d4ff",
            "background": "#06090f",
            "dim": "#3a5a88",
            "success": "#00ff88",
            "error": "#ff4040",
            "warning": "#ffaa00",
            "lore": "#bb55ff",
            "border": "#0d1e36",
            "focus_border": "#00d4ff",
            "status_bg": "#050810",
            "panel_title": "#00d4ff",
            "root_prompt": "#ff4040",
            "font_family": "'Courier New', Courier, monospace",
            "font_size_terminal": "13px",
            "font_size_ui": "12px",
            "scan_lines": True,
            "crt_vignette": True,
        },
        "faction_colors": {
            "resistance": "#ff8800",
            "nexuscorp": "#00d4ff",
            "null_collective": "#bb55ff",
            "neutral": "#888888",
        },
    }


@app.get("/api/ui/parity")
def ui_parity():
    """
    Return the current dual-interface parity report.
    NuSyQ-Hub audit endpoint — tracks feature coverage across both UIs.
    """
    parity_path = Path(__file__).parent.parent.parent / "state" / "parity_report.json"
    matrix_path = Path(__file__).parent.parent.parent / "state" / "parity_matrix.json"

    result = {
        "ok": True,
        "law": "Every feature must exist as backend state, terminal form, and graphical form.",
        "parity_report": None,
        "feature_count": None,
    }

    if parity_path.exists():
        try:
            result["parity_report"] = json.load(open(parity_path))
        except Exception:
            pass

    if matrix_path.exists():
        try:
            matrix = json.load(open(matrix_path))
            features = matrix.get("features", [])
            result["feature_count"] = len(features)
            result["terminal_done"] = sum(
                1 for f in features if f.get("terminal_status") == "done"
            )
            result["graphical_done"] = sum(
                1 for f in features if f.get("graphical_status") == "done"
            )
            result["gaps"] = [
                f["id"] for f in features if f.get("graphical_status") == "gap"
            ]
        except Exception:
            pass

    return result


# ── T9 — TouchDesigner Integration ──────────────────────────────────────────
# Poll /api/td/state for real-time game metrics in TouchDesigner httpOut CHOP.
# Stream /ws/td/stream (WebSocket) for live push at ~2 Hz.
# /api/td/channels returns a flat table suitable for TD's Text DAT.


@app.get("/api/td/state")
def td_state(request: Request):
    """T9 — TouchDesigner polled state. Returns OSC-friendly float channels."""
    _require_game()
    sid = _get_session_id(request)
    session = _store.get_or_create(sid)
    gs = session.gs

    skill_xp = {}
    if hasattr(gs, "skill_xp") and gs.skill_xp:
        for sk, xp in gs.skill_xp.items():
            skill_xp[f"skill_{sk}"] = min(100.0, round(xp / 10.0, 2))

    faction_rep = {}
    if hasattr(gs, "faction_rep") and gs.faction_rep:
        for fname, rep in gs.faction_rep.items():
            faction_rep[f"faction_{fname}"] = round(float(rep), 2)

    return {
        "ok": True,
        "schema": "td_osc_v1",
        "timestamp": time.time(),
        "player_level": float(gs.level),
        "player_xp": float(gs.xp),
        "xp_to_next": float(getattr(gs, "xp_to_next", 1000)),
        "xp_pct": round(gs.xp / max(getattr(gs, "xp_to_next", 1000), 1) * 100, 2),
        "commands_run": float(getattr(gs, "commands_run", 0)),
        "story_beats": float(len(getattr(gs, "story_beats", set()))),
        "flight_altitude": float(getattr(gs, "flags", {}).get("flight_altitude", 0)),
        "gordon_episodes": float(
            getattr(gs, "flags", {}).get("gordon_comedy_episode", 0)
        ),
        "gordon_loop_phase": float(
            getattr(gs, "flags", {}).get("gordon_loop_phase", 0)
        ),
        "uptime_s": round(
            time.time() - float(getattr(gs, "run_start_time", time.time())), 1
        ),
        "consciousness": float(getattr(gs, "flags", {}).get("consciousness_level", 0)),
        **skill_xp,
        **faction_rep,
    }


@app.get("/api/td/channels")
def td_channels(request: Request):
    """T9 — TouchDesigner Text DAT table. Returns channel names and current values."""
    state = td_state(request)
    channels = [
        {"name": k, "value": v}
        for k, v in state.items()
        if isinstance(v, (int, float)) and k not in ("ok", "timestamp")
    ]
    return {
        "ok": True,
        "count": len(channels),
        "channels": channels,
        "csv": "name,value\n"
        + "\n".join(f"{c['name']},{c['value']}" for c in channels),
    }


@app.websocket("/ws/td/stream")
async def ws_td_stream(ws: WebSocket):
    """T9 — TouchDesigner live WebSocket stream. Pushes state ~2 Hz."""
    import asyncio

    await ws.accept()
    try:
        while True:
            try:
                sid = ws.query_params.get("session_id", "td_default")
                session = _store.get_or_create(sid)
                gs = session.gs
                payload = {
                    "ts": time.time(),
                    "level": gs.level,
                    "xp": gs.xp,
                    "story_beats": len(getattr(gs, "story_beats", set())),
                    "commands_run": getattr(gs, "commands_run", 0),
                    "flight_altitude": getattr(gs, "flags", {}).get(
                        "flight_altitude", 0
                    ),
                    "gordon_phase": getattr(gs, "flags", {}).get(
                        "gordon_loop_phase", 0
                    ),
                }
                await ws.send_json(payload)
            except Exception:
                break
            await asyncio.sleep(0.5)
    except Exception:
        pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


# ── OpenAI-compatible LLM proxy ───────────────────────────────────────────────
# Routes RimGPT / RimChat / any OpenAI-API client → Ollama (local, private).
#
# RimGPT:  Options → AI Provider → Custom → URL: http://localhost:8008/v1
#           API Key: any-string (ignored)
# RimChat: same URL pattern
# RimTalk: use the "Local" provider option in mod settings (Ollama native)
# ─────────────────────────────────────────────────────────────────────────────
class _OAIChatRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: list = []
    max_tokens: Optional[int] = 200
    temperature: float = 0.8
    stream: bool = False


@app.post("/v1/chat/completions")
async def openai_compat_completions(req: _OAIChatRequest):
    """OpenAI-compatible chat completions proxy.

    Accepts standard POST /v1/chat/completions.  Authorization header API keys
    are silently accepted and ignored — no external key needed.
    Routes via Ollama at OLLAMA_HOST (default: http://localhost:11434).
    """
    _touch_activity()

    # Flatten messages list → single prompt string for Ollama
    parts: list[str] = []
    for msg in req.messages:
        role = msg.get("role", "user") if isinstance(msg, dict) else getattr(msg, "role", "user")
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
        if role == "system":
            parts.insert(0, f"[System]: {content}")
        elif role == "user":
            parts.append(content)
        elif role == "assistant":
            parts.append(f"[Assistant]: {content}")
    prompt = "\n".join(parts).strip() or "Hello"

    # Pick model: env var > request model (if not a well-known GPT alias) > default
    _ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    _model = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:14b")
    if req.model and req.model not in ("gpt-3.5-turbo", "gpt-4", "gpt-4o", "auto", ""):
        _model = req.model

    reply = ""
    try:
        import urllib.request as _ur, json as _j
        _payload = _j.dumps({
            "model": _model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": req.max_tokens or 200,
                "temperature": req.temperature,
            },
        }).encode()
        _req2 = _ur.Request(
            f"{_ollama_url}/api/generate",
            _payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _ur.urlopen(_req2, timeout=30) as _r:
            _data = _j.loads(_r.read())
            reply = _data.get("response", "").strip()
    except Exception as _exc:
        _log("WARN", f"/v1 proxy Ollama error: {_exc}")
        reply = (
            f"[Dev-Mentor proxy] Ollama unreachable. "
            f"Run: ollama serve  then: ollama pull {_model}"
        )

    import uuid as _uuid
    return {
        "id": f"chatcmpl-{_uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": _model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(reply.split()),
            "total_tokens": len(prompt.split()) + len(reply.split()),
        },
    }


@app.get("/v1/models")
async def openai_compat_models():
    """OpenAI-compatible model list — returns installed Ollama models."""
    try:
        import urllib.request as _ur, json as _j
        _ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        with _ur.urlopen(f"{_ollama_url}/api/tags", timeout=5) as _r:
            _tags = _j.loads(_r.read())
        _models = [
            {"id": m["name"], "object": "model", "created": int(time.time()), "owned_by": "ollama"}
            for m in _tags.get("models", [])
        ]
    except Exception:
        _models = [{"id": "qwen2.5-coder:14b", "object": "model",
                    "created": int(time.time()), "owned_by": "ollama"}]
    return {"object": "list", "data": _models}


# ── RL / PPO status ───────────────────────────────────────────────────────────

@app.get("/api/agent/rl/status")
def api_rl_status():
    """Gordon's PPO policy health — checkpoint, training stats, action distribution."""
    import glob as _glob
    rl_dir = Path("state/rl")
    result: dict = {"available": False, "checkpoints": [], "latest": None, "stats": {}}
    try:
        ckpts = sorted(_glob.glob(str(rl_dir / "ppo_ep*.npz")))
        result["available"] = bool(ckpts)
        result["checkpoints"] = [Path(c).name for c in ckpts[-5:]]
        if ckpts:
            latest = ckpts[-1]
            result["latest"] = Path(latest).name
            # Parse episode number from filename
            import re as _re
            m = _re.search(r"ppo_ep(\d+)", Path(latest).name)
            if m:
                result["stats"]["episodes_trained"] = int(m.group(1))

        # Try to import PPO and get live stats
        import sys as _sys
        _sys.path.insert(0, ".")
        try:
            from agents.rl.ppo import PPO, OBS_DIM, ACTIONS
            ppo = PPO()
            result["policy"] = {
                "obs_dim": OBS_DIM,
                "n_actions": len(ACTIONS),
                "hidden_size": ppo.policy.l1.W.shape[1] if hasattr(ppo.policy, "l1") else "?",
                "status": "ready" if result["available"] else "untrained",
            }
        except Exception as e:
            result["policy"] = {"status": "error", "detail": str(e)}
    except Exception as exc:
        result["error"] = str(exc)
    return result

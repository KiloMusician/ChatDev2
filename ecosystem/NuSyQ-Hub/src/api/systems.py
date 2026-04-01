"""API stubs for top-level NuSyQ systems: Culture Ship, SimulatedVerse, Wizard Navigator, Orchestrator, Marble.

Provides health/status endpoints, hints, tutorials, FAQ, commands, and smart-search style ops.

Inspired by hacker games like Bitburner, Hacknet, GreyHack, EmuDevz, HackHub:
- fl1ght.exe smart search across hints, commands, quests, and codebase
- Game-like progression with skills, XP, and evolution levels
- Quest integration with Temple of Knowledge progression
- Real-time system metrics as RPG stats
"""

import contextlib
import importlib
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from fastapi import APIRouter, Query
from pydantic import BaseModel

try:
    from src.tools.hint_engine import HintEngine
except ImportError:  # pragma: no cover - optional dependency
    HintEngine = None

try:
    _pu_queue_module = importlib.import_module("src.automation.unified_pu_queue")
    UnifiedPUQueue = getattr(_pu_queue_module, "UnifiedPUQueue", None)
except ImportError:  # pragma: no cover - optional dependency
    UnifiedPUQueue = None

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None

try:
    from src.search.smart_search import SmartSearch
except ImportError:  # pragma: no cover - optional dependency
    SmartSearch = None

try:
    from src.system.rpg_inventory import award_xp as rpg_award_xp
    from src.system.rpg_inventory import get_rpg_inventory
except ImportError:  # pragma: no cover - optional dependency
    get_rpg_inventory = None
    rpg_award_xp = None

try:
    from src.guild.guild_board import get_board
except ImportError:  # pragma: no cover - optional dependency
    get_board = None

try:
    from src.games.hacking_mechanics import ExploitType, get_hacking_controller
except ImportError:  # pragma: no cover - optional dependency
    get_hacking_controller = None
    ExploitType = None

try:
    _quest_module = importlib.import_module("src.Rosetta_Quest_System.quest_engine")
    QuestEngine = getattr(_quest_module, "QuestEngine", None)
except ImportError:  # pragma: no cover - optional dependency
    QuestEngine = None

try:
    from src.games.hacking_quests import (generate_culture_ship_narrative,
                                          get_quest_by_id)
    from src.games.skill_tree import get_skill_tree
except ImportError:  # pragma: no cover - optional dependency
    generate_culture_ship_narrative = None
    get_quest_by_id = None
    get_skill_tree = None

try:
    _problems_module = importlib.import_module("src.api.problems_api")
    ProblemsAPI = getattr(_problems_module, "ProblemsAPI", None)
except ImportError:  # pragma: no cover - optional dependency
    ProblemsAPI = None

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - Python < 3.11
    UTC = timezone.utc  # noqa: UP017

router = APIRouter()
logger = logging.getLogger(__name__)

# Error message constants
ERROR_QUEST_ENGINE_UNAVAILABLE = "Quest engine not available"
ERROR_RPG_INVENTORY_UNAVAILABLE = "RPG inventory system not available"
ERROR_HACKING_CONTROLLER_UNAVAILABLE = "Hacking controller not available"
ERROR_GUILD_BOARD_UNAVAILABLE = "Guild board not available"
ERROR_QUEST_SEARCH_UNAVAILABLE = "Quest search not available"
PU_STAT_QUEUED = "queued_pus"
PU_STAT_EXECUTING = "executing_pus"
PU_STAT_COMPLETED = "completed_pus"
SYSTEM_ID_CULTURE_SHIP = "culture_ship"
SYSTEM_ID_SIMULATEDVERSE = "simulatedverse"
SYSTEM_ID_PATH_OF_ACHRA = "path_of_achra"
SCENE_ROUTER_REL_PATH = "web/modular-window-server/public/js/scene-router.js"
GAME_STATE_KEY_LAST_AUTOSAVE_TS = "last_autosave_ts"
GAME_STATE_KEY_LAST_TRACE_SNAPSHOT = "last_trace_snapshot"
TERMINAL_LOGS_DIR = "terminal_logs"
ROSETTA_DIR = Path("../Reports/rosetta").resolve()


class SystemStatus(BaseModel):
    name: str
    status: str
    detail: str | None = None
    timestamp: str


class AgentInfo(BaseModel):
    id: str
    name: str
    status: str
    model: str | None = None
    endpoint: str | None = None


class QuestInfo(BaseModel):
    id: str
    title: str
    state: str
    assigned_to: str | None = None


class Hint(BaseModel):
    id: str
    title: str
    text: str
    tags: list[str] | None = []
    related_commands: list[str] | None = []


class Tutorial(BaseModel):
    id: str
    title: str
    steps: list[str]
    difficulty: str | None = "medium"


class FAQEntry(BaseModel):
    question: str
    answer: str


class CommandInfo(BaseModel):
    command: str
    description: str
    example: str | None = None


class Metrics(BaseModel):
    agents_online: int
    active_quests: int
    system_utilization: dict
    timestamp: str


class HackScanRequest(BaseModel):
    component_name: str


class HackConnectRequest(BaseModel):
    component_name: str


class HackExploitRequest(BaseModel):
    component_name: str
    exploit_type: str
    xp_reward: int = 50


class HackPatchRequest(BaseModel):
    component_name: str


class QuestCompleteRequest(BaseModel):
    quest_id: str
    status: str = "completed"
    skill: str = "automation"
    xp: int | None = None
    achievement: str | None = None
    feature: str | None = None
    completion_time: float | None = None


class AccessSession(BaseModel):
    session_id: str
    component_name: str
    access_level: int
    created_at: str
    last_seen: str


HACK_SESSIONS: dict[str, AccessSession] = {}


def _persist_hack_sessions() -> None:
    """Persist hack sessions into game state cache and file."""
    state = get_game_state()
    state.hack_sessions = list(HACK_SESSIONS.values())
    state.last_saved = _now()
    _GAME_STATE_CACHE["state"] = state
    _save_game_state_to_file(state)


class SkillInfo(BaseModel):
    """RPG skill information."""

    name: str
    level: str
    experience: int
    max_experience: int
    proficiency: float
    usage_count: int


class SmartSearchResult(BaseModel):
    """fl1ght.exe style smart search result."""

    query: str
    total_results: int
    categories: dict
    results: list[dict]
    suggestions: list[str]


class GuildQuestInfo(BaseModel):
    """Guild board quest entry."""

    quest_id: str
    title: str
    description: str
    priority: int
    state: str
    claimed_by: str | None = None
    tags: list[str] = []


class GameProgressInfo(BaseModel):
    """Game progression summary - Bitburner/Hacknet style."""

    evolution_level: int
    consciousness_score: float
    skills_unlocked: int
    quests_completed: int
    temple_floor: int
    achievements: list[str]


class EvolveRequest(BaseModel):
    """Request model for /evolve endpoint."""

    prompt: str | None = None


def _now():
    return datetime.now(UTC).isoformat()


def _load_hint_engine():
    """Return a ready HintEngine or None if unavailable."""
    if HintEngine is None:
        return None

    engine = HintEngine()
    if not engine.load_quests():
        return None
    engine.load_zeta_tracker()
    engine.build_dependency_graph()
    engine.categorize_quests()
    return engine


# Simple in-process TTL cache for HintEngine results
_HINT_CACHE: dict[str, tuple[float, dict]] = {}
_HINT_CACHE_TTL = float(os.getenv("HINT_CACHE_TTL", "30"))  # seconds

# Cache for /ops smart search
_OPS_CACHE: dict[str, tuple[float, list[CommandInfo]]] = {}
_OPS_CACHE_TTL = float(os.getenv("OPS_CACHE_TTL", "20"))  # seconds


def _cached_hint_engine():
    """Cached HintEngine data (quests, actionable, blocked)."""
    now = time.time()
    cached = _HINT_CACHE.get("hint_engine")
    if cached and now - cached[0] < _HINT_CACHE_TTL:
        return cached[1]

    engine = _load_hint_engine()
    if not engine:
        return None

    payload = {
        "engine": engine,
        "actionable": engine.actionable_quests,
        "blocked": engine.blocked_quests,
        "quests": engine.quests,
    }
    _HINT_CACHE["hint_engine"] = (now, payload)
    return payload


def _dynamic_hints(limit: int = 5) -> list[Hint]:
    """Build hints from HintEngine suggestions."""
    cached = _cached_hint_engine()
    if not cached:
        return []

    engine = cached["engine"]
    result = engine.suggest_next_quests(count=limit)
    hints: list[Hint] = []

    for score in result.suggested_quests:
        quest = engine.quests.get(score.quest_id, {})
        hints.append(
            Hint(
                id=score.quest_id,
                title=quest.get("title", f"Quest {score.quest_id}"),
                text=(
                    f"Score {score.final_score:.2f} — "
                    f"Status: {quest.get('status', 'unknown')} | "
                    f"Dependencies: {len(quest.get('dependencies', []))}"
                ),
                tags=quest.get("zeta_tags") or quest.get("priority_tags") or [],
                related_commands=["start_nusyq.py work", "start_nusyq.py queue"],
            )
        )

    return hints


def _fallback_hints() -> list[Hint]:
    return [
        Hint(
            id="h1",
            title="Use the Agent Terminal",
            text="Open the Copilot or ChatDev terminal to run commands and get guidance.",
            tags=["terminal", "agents"],
            related_commands=["help", "list_agents"],
        ),
        Hint(
            id="h2",
            title="Run the Orchestrator",
            text="Start the orchestrator for multi-agent tasks using the Run Orchestrator task.",
            tags=["orchestrator"],
            related_commands=["start_orchestrator"],
        ),
    ]


def _collect_commands() -> list[CommandInfo]:
    """Curated command catalog (kept light to avoid heavy imports)."""
    entries = [
        ("start_nusyq.py work", "Execute next quest or PU", "python scripts/start_nusyq.py work"),
        ("start_nusyq.py queue", "Show queued quests/PUs", "python scripts/start_nusyq.py queue"),
        (
            "start_nusyq.py suggest",
            "AI-generated next steps",
            "python scripts/start_nusyq.py suggest",
        ),
        (
            "start_nusyq.py error_report",
            "Generate unified diagnostics",
            "python scripts/start_nusyq.py error_report",
        ),
        (
            "nusyq_daemon",
            "Conversational CLI (build/fix/status)",
            "python -m src.system.nusyq_daemon",
        ),
        ("pu_queue_runner", "Run PU queue processor", "python scripts/pu_queue_runner.py --real"),
        (
            "auto_cycle_steps",
            "Autonomous cycle (analyze -> heal)",
            "python scripts/nusyq_actions/auto_cycle_steps.py",
        ),
        ("hint_engine", "Suggest next quests", "python -m src.tools.hint_engine"),
        ("fl1ght.exe", "Smart search tips helper", "query via /api/ops?q=..."),
    ]
    return [CommandInfo(command=c, description=d, example=e) for c, d, e in entries]


def _queue_stats() -> dict[str, int]:
    """Return PU queue stats if available."""
    if UnifiedPUQueue is None:
        return {PU_STAT_QUEUED: 0, PU_STAT_EXECUTING: 0, PU_STAT_COMPLETED: 0}

    try:
        queue = UnifiedPUQueue()
        statuses = [pu.status for pu in queue.queue]
        return {
            PU_STAT_QUEUED: statuses.count("queued") + statuses.count("approved"),
            PU_STAT_EXECUTING: statuses.count("executing"),
            PU_STAT_COMPLETED: statuses.count("completed"),
        }
    except (RuntimeError, AttributeError):
        return {PU_STAT_QUEUED: 0, PU_STAT_EXECUTING: 0, PU_STAT_COMPLETED: 0}


def _system_utilization() -> dict:
    """Return system utilization metrics (CPU/MEM) if psutil is present."""
    if psutil is None:
        return {"cpu_percent": 0.0, "mem_percent": 0.0}

    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        return {"cpu_percent": cpu, "mem_percent": mem}
    except (OSError, RuntimeError):
        return {"cpu_percent": 0.0, "mem_percent": 0.0}


def _run_with_timeout(fn: Any, timeout_seconds: float, default: Any) -> Any:
    """Run a synchronous helper with bounded latency to avoid endpoint hangs."""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn)
    try:
        result = future.result(timeout=timeout_seconds)
        executor.shutdown(wait=False, cancel_futures=True)
        return result
    except (FuturesTimeoutError, OSError, RuntimeError):
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        return default


SYSTEMS = [
    (SYSTEM_ID_CULTURE_SHIP, "Culture Ship", "Autonomous dev orchestrator"),
    (SYSTEM_ID_SIMULATEDVERSE, "SimulatedVerse", "Consciousness simulation engine"),
    ("wizard_navigator", "Wizard Navigator", "Guided system navigation"),
    ("orchestrator", "Orchestrator", "System orchestration & meta-automation"),
    ("marble", "Rube Goldbergian Marble", "Complex event chain engine"),
    ("antigravity", "Open Antigravity", "Experimental physics/gameplay sandbox"),
    ("hacknet", "Hacknet", "Terminal-first network infiltration workflows"),
    ("hackhub", "HackHub", "Collaborative exploit lab and ops board"),
    ("bitburner", "Bitburner", "Automation scripting and progression mechanics"),
    ("cogmind", "Cogmind", "Tactical systems simulation and diagnostics"),
    (SYSTEM_ID_PATH_OF_ACHRA, "Path of Achra", "Narrative progression and build-crafting layer"),
]


def _hub_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_simulatedverse_root() -> Path:
    candidates: list[Path] = []
    try:
        from src.utils.repo_path_resolver import get_repo_path

        candidates.append(get_repo_path("SIMULATEDVERSE_ROOT"))
    except Exception:
        logger.debug("Suppressed Exception", exc_info=True)

    env_path = os.getenv("SIMULATEDVERSE_ROOT") or os.getenv("SIMULATEDVERSE_PATH")
    if env_path:
        candidates.append(Path(env_path))

    hub = _hub_root()
    candidates.extend(
        [
            hub.parent / "SimulatedVerse" / "SimulatedVerse",
            hub.parent.parent / "SimulatedVerse" / "SimulatedVerse",
        ]
    )

    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
            if resolved.exists():
                return resolved
        except Exception:
            continue
    return candidates[0] if candidates else Path("SimulatedVerse")


def _resolve_steam_common_root() -> Path:
    """Resolve Steam common install directory on Windows/WSL with safe fallbacks."""
    candidates: list[Path] = []

    program_files_x86 = os.getenv("PROGRAMFILES(X86)")
    if program_files_x86:
        candidates.append(Path(program_files_x86) / "Steam" / "steamapps" / "common")

    program_files = os.getenv("PROGRAMFILES")
    if program_files:
        candidates.append(Path(program_files) / "Steam" / "steamapps" / "common")

    user_profile = os.getenv("USERPROFILE")
    if user_profile:
        candidates.append(
            Path(user_profile) / "AppData" / "Local" / "Steam" / "steamapps" / "common"
        )

    # WSL fallback path if Windows vars are unavailable.
    candidates.append(Path("/mnt/c/Program Files (x86)/Steam/steamapps/common"))

    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
            if resolved.exists():
                return resolved
        except Exception:
            continue
    return candidates[0]


def _http_healthy(url: str, timeout_seconds: float = 0.8) -> bool:
    """Best-effort local health probe for optional backend services."""
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return 200 <= int(getattr(response, "status", 500)) < 500
    except (URLError, OSError, ValueError):
        return False


def _process_running(keywords: list[str]) -> bool:
    if psutil is None or not keywords:
        return False

    normalized = [k.lower() for k in keywords]
    try:
        for proc in psutil.process_iter(["name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info.get("cmdline") or []).lower()
                name = str(proc.info.get("name") or "").lower()
            except (psutil.Error, OSError):
                continue
            payload = f"{name} {cmdline}".strip()
            if payload and any(k in payload for k in normalized):
                return True
    except (psutil.Error, OSError):
        return False
    return False


def _file_hits(paths: list[Path]) -> tuple[int, int]:
    total = len(paths)
    hits = sum(1 for p in paths if p.exists())
    return hits, total


def _marker_hits(checks: list[dict[str, Any]]) -> tuple[int, int]:
    """Count content-marker checks that pass."""
    total = len(checks)
    hits = 0
    for check in checks:
        path = check.get("path")
        patterns = check.get("patterns")
        if not isinstance(path, Path) or not isinstance(patterns, list) or not patterns:
            continue
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if all(isinstance(pattern, str) and pattern in content for pattern in patterns):
            hits += 1
    return hits, total


def _unique_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in urls:
        url = str(raw or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        ordered.append(url)
    return ordered


def _load_antigravity_runtime_state(hub_root: Path) -> dict[str, Any]:
    pid_file = hub_root / "state" / "runtime" / "open_antigravity_runtime.pid"
    if not pid_file.exists():
        return {}
    try:
        payload = json.loads(pid_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _build_system_probes() -> dict[str, dict[str, Any]]:
    hub = _hub_root()
    simverse_root = _resolve_simulatedverse_root()
    steam_root = _resolve_steam_common_root()
    antigravity_port = os.getenv("NUSYQ_ANTIGRAVITY_PORT", "8080").strip() or "8080"
    runtime_state = _load_antigravity_runtime_state(hub)
    runtime_host = str(runtime_state.get("host") or "127.0.0.1").strip() or "127.0.0.1"
    runtime_port = antigravity_port
    try:
        runtime_port = str(int(runtime_state.get("port", antigravity_port)))
    except (ValueError, TypeError):
        runtime_port = antigravity_port
    runtime_health_url = str(runtime_state.get("health_url") or "").strip()
    antigravity_urls: list[str] = []
    env_antigravity_url = os.getenv("NUSYQ_ANTIGRAVITY_STATUS_URL")
    if isinstance(env_antigravity_url, str) and env_antigravity_url.strip():
        antigravity_urls.append(env_antigravity_url.strip())
    if runtime_health_url:
        antigravity_urls.append(runtime_health_url)
    antigravity_urls.extend(
        [
            f"http://{runtime_host}:{runtime_port}/health",
            f"http://{runtime_host}:{runtime_port}/api/systems/antigravity/status",
        ]
    )
    antigravity_urls.extend(
        [
            f"http://127.0.0.1:{antigravity_port}/health",
            f"http://127.0.0.1:{antigravity_port}/api/systems/antigravity/status",
        ]
    )
    antigravity_urls = _unique_urls(antigravity_urls)

    return {
        SYSTEM_ID_CULTURE_SHIP: {
            "required_paths": [hub / "src/culture_ship/health_probe.py"],
            "optional_paths": [simverse_root / "CULTURE_SHIP_READY.md"],
            "urls": ["http://127.0.0.1:5002/health", "http://127.0.0.1:5000/health"],
            "process_keywords": ["culture_ship", "start_simulatedverse"],
        },
        SYSTEM_ID_SIMULATEDVERSE: {
            "required_paths": [simverse_root],
            "optional_paths": [simverse_root / "package.json", simverse_root / "server/index.ts"],
            "urls": ["http://127.0.0.1:5002/health", "http://127.0.0.1:5000/health"],
            "process_keywords": ["simulatedverse", "npm run dev"],
        },
        "wizard_navigator": {
            "required_paths": [hub / "src/tools/wizard_navigator_consolidated.py"],
            "optional_paths": [hub / "src/navigation/wizard_navigator/wizard_navigator.py"],
            "urls": [],
            "process_keywords": [],
        },
        "orchestrator": {
            "required_paths": [hub / "src/orchestration/unified_ai_orchestrator.py"],
            "optional_paths": [hub / "scripts/orchestrator_cli.py"],
            "urls": [],
            "process_keywords": ["orchestrator", "start_nusyq.py"],
        },
        "marble": {
            "required_paths": [hub / "src/api/systems.py"],
            "optional_paths": [hub / SCENE_ROUTER_REL_PATH],
            "urls": [],
            "process_keywords": [],
        },
        "antigravity": {
            "required_paths": [hub / SCENE_ROUTER_REL_PATH],
            "optional_paths": [hub / "docs/SYSTEM_MAP.md"],
            "urls": antigravity_urls,
            "process_keywords": [
                "modular-window-server",
                "web/modular-window-server",
                "modular-window-server/server.js",
                "nusyq-modular-window-server",
                "node server.js",
                "server.js",
            ],
            "strict_runtime": True,
            "require_health_url": True,
            "content_markers": [
                {
                    "path": hub / SCENE_ROUTER_REL_PATH,
                    "patterns": ["this.scenes.set('antigravity'", "systemId: 'antigravity'"],
                }
            ],
        },
        "hacknet": {
            "required_paths": [
                hub / "src/api/hacking_api.py",
                hub / "src/games/hacking_mechanics.py",
            ],
            "optional_paths": [hub / "tests/test_api_game_features.py"],
            "urls": [],
            "process_keywords": [],
        },
        "hackhub": {
            "required_paths": [hub / "src/guild/guild_board.py"],
            "optional_paths": [hub / "src/api/systems.py"],
            "urls": [],
            "process_keywords": [],
        },
        "bitburner": {
            "required_paths": [hub / "src/system/rpg_inventory.py"],
            "optional_paths": [steam_root / "Bitburner"],
            "urls": [],
            "process_keywords": [],
        },
        "cogmind": {
            "required_paths": [hub / "src/factories/project_factory.py"],
            "optional_paths": [steam_root / "Cogmind"],
            "urls": [],
            "process_keywords": [],
        },
        SYSTEM_ID_PATH_OF_ACHRA: {
            "required_paths": [hub / "src/factories/project_factory.py"],
            "optional_paths": [steam_root / "Path of Achra"],
            "urls": [],
            "process_keywords": [],
        },
    }


def _probe_system_status(system_id: str) -> tuple[str, str]:
    probes = _build_system_probes().get(system_id)
    if not probes:
        return ("unknown", "No health probes configured")

    required_hits, required_total = _file_hits(probes.get("required_paths", []))
    optional_hits, optional_total = _file_hits(probes.get("optional_paths", []))
    urls = probes.get("urls", [])
    url_hits = sum(1 for url in urls if _http_healthy(url))
    process_hit = _process_running(probes.get("process_keywords", []))
    marker_hits, marker_total = _marker_hits(probes.get("content_markers", []))
    strict_runtime = bool(probes.get("strict_runtime", False))
    require_health_url = bool(probes.get("require_health_url", False))
    runtime_hit = url_hits > 0 or process_hit
    runtime_ready = runtime_hit if strict_runtime else (runtime_hit or len(urls) == 0)
    if require_health_url and len(urls) > 0:
        runtime_ready = runtime_ready and url_hits > 0

    if (
        required_total > 0
        and required_hits == required_total
        and marker_hits == marker_total
        and runtime_ready
    ):
        status = "online"
    elif required_hits > 0 or optional_hits > 0 or marker_hits > 0 or runtime_hit:
        status = "degraded"
    else:
        status = "offline"

    detail = (
        f"required {required_hits}/{required_total}, "
        f"optional {optional_hits}/{optional_total}, "
        f"markers {marker_hits}/{marker_total}, "
        f"health_urls {url_hits}/{len(urls)}, "
        f"process {'yes' if process_hit else 'no'}, "
        f"strict_runtime {'yes' if strict_runtime else 'no'}"
    )
    return (status, detail)


@router.get("/systems/{system_id}/status", response_model=SystemStatus)
async def get_system_status(system_id: str):
    for sys, name, desc in SYSTEMS:
        if sys == system_id:
            probe_status, probe_detail = _probe_system_status(system_id)
            return SystemStatus(
                name=name,
                status=probe_status,
                detail=f"{desc} | {probe_detail}",
                timestamp=_now(),
            )
    return SystemStatus(
        name=system_id,
        status="unknown",
        detail="System not found.",
        timestamp=_now(),
    )


@router.get("/systems", response_model=list[SystemStatus])
async def list_systems():
    items: list[SystemStatus] = []
    for system_id, name, desc in SYSTEMS:
        probe_status, probe_detail = _probe_system_status(system_id)
        items.append(
            SystemStatus(
                name=name,
                status=probe_status,
                detail=f"{desc} | {probe_detail}",
                timestamp=_now(),
            )
        )
    return items


@router.get("/metrics", response_model=Metrics)
async def get_metrics():
    # Live quest/PU stats plus system utilization
    cached = _run_with_timeout(_cached_hint_engine, timeout_seconds=1.2, default=None)
    actionable = len(cached["actionable"]) if cached else 0
    blocked = len(cached["blocked"]) if cached else 0
    total = len(cached["quests"]) if cached else 0

    queue_stats = _run_with_timeout(
        _queue_stats,
        timeout_seconds=0.8,
        default={PU_STAT_QUEUED: 0, PU_STAT_EXECUTING: 0, PU_STAT_COMPLETED: 0},
    )
    util = _run_with_timeout(
        _system_utilization,
        timeout_seconds=0.6,
        default={"cpu_percent": 0.0, "mem_percent": 0.0},
    )

    return Metrics(
        agents_online=5,
        active_quests=actionable,
        system_utilization={
            "cpu_percent": util["cpu_percent"],
            "mem_percent": util["mem_percent"],
            "actionable_quests": actionable,
            "blocked_quests": blocked,
            "total_quests": total,
            **queue_stats,
        },
        timestamp=_now(),
    )


@router.get("/agents", response_model=list[AgentInfo])
async def list_agents():
    # Placeholder agent inventory
    agents = [
        {
            "id": "copilot",
            "name": "Copilot",
            "status": "online",
            "model": "gpt-copilot",
            "endpoint": "/terminals/copilot",
        },
        {
            "id": "ollama",
            "name": "Ollama",
            "status": "online",
            "model": "qwen2.5-coder",
            "endpoint": "/terminals/ollama",
        },
        {
            "id": "chatdev",
            "name": "ChatDev",
            "status": "idle",
            "model": "chatdev-ensemble",
            "endpoint": "/terminals/chatdev",
        },
    ]
    return [AgentInfo(**a) for a in agents]


@router.get("/quests", response_model=list[QuestInfo])
async def list_quests():
    cached = _cached_hint_engine()
    if not cached:
        # Fallback
        quests = [
            {
                "id": "q1",
                "title": "Integrate Culture Ship dashboard",
                "state": "in_progress",
                "assigned_to": "ai_council",
            },
            {
                "id": "q2",
                "title": "Repair SimulatedVerse dev server",
                "state": "triage",
                "assigned_to": "orchestrator",
            },
        ]
        return [QuestInfo(**q) for q in quests]

    engine = cached["engine"]
    quests_out: list[QuestInfo] = []
    for quest_id in engine.actionable_quests[:20]:
        quest = engine.quests.get(quest_id, {})
        quests_out.append(
            QuestInfo(
                id=quest_id,
                title=quest.get("title", quest_id),
                state="actionable",
                assigned_to=quest.get("assigned_to"),
            )
        )
    for quest_id in engine.blocked_quests[:10]:
        quest = engine.quests.get(quest_id, {})
        quests_out.append(
            QuestInfo(
                id=quest_id,
                title=quest.get("title", quest_id),
                state="blocked",
                assigned_to=quest.get("assigned_to"),
            )
        )
    return quests_out


@router.get("/quests/{quest_id}", response_model=dict)
def get_quest_detail(quest_id: str) -> dict:
    """Fetch quest detail from the canonical quest log."""
    if QuestEngine is None:
        return {"success": False, "error": ERROR_QUEST_ENGINE_UNAVAILABLE}

    engine = QuestEngine()
    quest = engine.get_quest(quest_id)
    if not quest:
        return {"success": False, "error": f"Quest '{quest_id}' not found"}

    return {"success": True, "quest": quest.to_dict()}


def _resolve_game_quest(quest_id: str) -> Any | None:
    if get_quest_by_id is None:
        return None
    try:
        return get_quest_by_id(quest_id)
    except (RuntimeError, AttributeError):
        return None


def _update_quest_status(engine: Any, quest_id: str, quest, game_quest, status: str) -> None:
    if quest or game_quest:
        engine.update_quest_status(quest_id, status)


def _compute_xp_award(request: QuestCompleteRequest, game_quest) -> int:
    xp_awarded = request.xp if request.xp is not None else game_quest.xp_reward if game_quest else 0
    return xp_awarded or 0


def _award_rpg_xp_for_quest(
    request: QuestCompleteRequest,
    xp_awarded: int,
) -> tuple[dict | None, str | None]:
    if xp_awarded <= 0 and not request.achievement and not request.feature:
        return None, None
    if rpg_award_xp is None:
        return None, ERROR_RPG_INVENTORY_UNAVAILABLE
    xp_result = rpg_award_xp(
        request.skill,
        xp_awarded,
        award_game_fn=award_game_progress,
        achievement=request.achievement,
        feature=request.feature,
    )
    if not xp_result.get("success"):
        return None, xp_result.get("error", "Failed to award XP")
    return xp_result.get("game_award"), None


def _apply_game_quest_progress(
    game_quest,
    completion_time: float | None,
) -> tuple[str | None, str | None]:
    narrative = None
    skill_unlocked = None
    if not game_quest:
        return narrative, skill_unlocked

    if get_skill_tree is not None:
        try:
            skill_tree = get_skill_tree()
            skill_tree.add_xp(game_quest.xp_reward)
            if game_quest.skill_unlock:
                skill_tree.unlock_skill(game_quest.skill_unlock)
                skill_unlocked = game_quest.skill_unlock
        except (RuntimeError, AttributeError):
            logger.debug("Suppressed AttributeError/RuntimeError", exc_info=True)

    if generate_culture_ship_narrative is not None:
        try:
            narrative = generate_culture_ship_narrative(
                game_quest,
                completion_time or 0.0,
            )
        except (RuntimeError, AttributeError):
            narrative = None

    return narrative, skill_unlocked


@router.post("/quests/complete", response_model=dict)
def complete_quest(request: QuestCompleteRequest) -> dict:
    """Update quest status in the canonical quest log and autosave state."""
    if QuestEngine is None:
        return {"success": False, "error": ERROR_QUEST_ENGINE_UNAVAILABLE}

    engine = QuestEngine()
    quest = engine.get_quest(request.quest_id)
    game_quest = _resolve_game_quest(request.quest_id)

    if not quest and not game_quest:
        return {"success": False, "error": f"Quest '{request.quest_id}' not found"}

    _update_quest_status(engine, request.quest_id, quest, game_quest, request.status)

    xp_awarded = _compute_xp_award(request, game_quest)
    award_summary, award_error = _award_rpg_xp_for_quest(request, xp_awarded)
    if award_error:
        return {"success": False, "error": award_error}

    narrative, skill_unlocked = _apply_game_quest_progress(
        game_quest,
        request.completion_time,
    )

    _auto_persist_game_state("quest_complete")

    return {
        "success": True,
        "quest_id": request.quest_id,
        "status": request.status,
        "xp_awarded": xp_awarded,
        "skill": request.skill,
        "award_summary": award_summary,
        "skill_unlocked": skill_unlocked,
        "narrative": narrative,
    }


@router.get("/hints", response_model=list[Hint])
def list_hints():
    hints = _dynamic_hints(limit=7)
    if not hints:
        hints = _fallback_hints()
    return hints


@router.get("/tutorials", response_model=list[Tutorial])
def list_tutorials():
    tutorials = [
        {
            "id": "t1",
            "title": "Run a Full Quest Cycle",
            "steps": [
                "Open Help & Hints -> Commands -> start_nusyq.py work",
                "Review the queued quest and confirm scope",
                "Run the work command; then check /api/quests for status",
            ],
            "difficulty": "easy",
        },
        {
            "id": "t2",
            "title": "Generate Smart Suggestions",
            "steps": [
                "Call /api/hints to fetch top actionable quests",
                "Use fl1ght.exe smart search (/api/ops?q=your_topic) for tips",
                "Assign the best hint to a quest using the quest system",
            ],
            "difficulty": "medium",
        },
    ]
    return [
        Tutorial(
            id=t["id"],
            title=t["title"],
            steps=list(t["steps"]),
            difficulty=t.get("difficulty"),
        )
        for t in tutorials
    ]


@router.get("/faq", response_model=list[FAQEntry])
def list_faq():
    cached = _cached_hint_engine()
    actionable = len(cached["actionable"]) if cached else 0
    blocked = len(cached["blocked"]) if cached else 0
    faqs = [
        {
            "question": "How do I open an agent terminal?",
            "answer": "Open Menu -> Preset Terminals and click the terminal you want.",
        },
        {
            "question": "Where are quests tracked?",
            "answer": "In src/Rosetta_Quest_System/quest_log.jsonl; fetch via /api/quests or run start_nusyq.py queue.",
        },
        {
            "question": "How many quests are actionable right now?",
            "answer": f"Actionable: {actionable}, Blocked: {blocked}. Run /api/hints for details.",
        },
    ]
    return [FAQEntry(**f) for f in faqs]


@router.get("/commands", response_model=list[CommandInfo])
def list_commands():
    return _collect_commands()


@router.get("/scripts", response_model=list[CommandInfo])
def list_scripts():
    scripts = [
        {
            "command": "scripts/start_nusyq.py",
            "description": "Generate system state snapshot.",
            "example": "python scripts/start_nusyq.py",
        },
        {
            "command": "scripts/nusyq_actions/auto_cycle_steps.py",
            "description": "Autonomous cycle runner (analyze -> heal -> run).",
            "example": "python scripts/nusyq_actions/auto_cycle_steps.py --max-pus 2",
        },
    ]
    return [CommandInfo(**s) for s in scripts]


@router.get("/inventory", response_model=list[CommandInfo])
def list_inventory():
    inventory = [
        {
            "command": "config/secrets.json",
            "description": "Secrets store (do not commit)",
            "example": None,
        },
        {
            "command": "src/Rosetta_Quest_System/quest_log.jsonl",
            "description": "Quest log storage",
            "example": None,
        },
    ]
    return [
        CommandInfo(
            command=i["command"],
            description=i["description"],
            example=i.get("example"),
        )
        for i in inventory
    ]


@router.get("/ops", response_model=list[CommandInfo])
def list_ops(q: str | None = Query(default=None, description="Search query for smart ops")):
    now = time.time()
    cache_key = q or "__all__"
    cached = _OPS_CACHE.get(cache_key)
    if cached and now - cached[0] < _OPS_CACHE_TTL:
        return cached[1]

    ops_catalog = [
        {
            "command": "fl1ght.exe smart-search",
            "description": "Search hints, commands, FAQ, tutorials",
            "example": "/api/ops?q=quests",
        },
        {
            "command": "validate_configs",
            "description": "Run configuration validation.",
            "example": "python config/config_manager.py",
        },
        {
            "command": "start_nusyq.py error_report",
            "description": "Generate unified diagnostics across repos.",
            "example": "python scripts/start_nusyq.py error_report --full",
        },
    ]

    haystack = ops_catalog + [
        {"command": h.title, "description": h.text, "example": ",".join(h.tags or [])}
        for h in list_hints()
    ]
    haystack += [
        {"command": c.command, "description": c.description, "example": c.example or ""}
        for c in _collect_commands()
    ]

    if q:
        query = q.lower()
        haystack = [
            item
            for item in haystack
            if query in item["command"].lower() or query in str(item["description"]).lower()
        ]

    seen: set[str] = set()
    filtered = []
    for item in haystack:
        if item["command"] in seen:
            continue
        seen.add(item["command"])
        filtered.append(item)

    result = [CommandInfo(**o) for o in filtered[:12]]
    _OPS_CACHE[cache_key] = (now, result)
    return result


@router.get("/evolve", response_model=list[dict])
def list_evolve_suggestions():
    """List existing rosetta evolve suggestion artifacts (if any)."""
    results = []
    if ROSETTA_DIR.exists() and ROSETTA_DIR.is_dir():
        for p in sorted(ROSETTA_DIR.glob("evolve_suggestion_*.json")):
            try:
                with p.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                results.append({"file": str(p), "content": data})
            except (OSError, ValueError):
                continue
    return results


@router.post("/evolve", response_model=dict)
def trigger_evolve(request: EvolveRequest):
    """Trigger a lightweight evolve suggestion run.

    This is a stub that persists a small evolve suggestion JSON to the
    `Reports/rosetta` folder and returns its path and content. In future
    this can call the full rosetta pipeline.
    """
    # Prefer using the rosetta runner utility which may call the existing
    # `scripts/start_nusyq.py suggest` pipeline. Fall back to writing a
    # lightweight suggestion artifact if the runner is unavailable or fails.
    prompt = request.prompt
    try:
        from src.tools.rosetta_runner import run_suggest

        result = run_suggest(prompt=prompt)
        if result:
            return result
    except (ImportError, RuntimeError):
        # best-effort fallback below
        logger.debug("Suppressed ImportError/RuntimeError", exc_info=True)

    ROSETTA_DIR.mkdir(parents=True, exist_ok=True)

    suggestion = {
        "id": str(uuid4()),
        "prompt": prompt or "Auto evolve suggestion",
        "suggestion": "Refactor and modernize the target module.\nAdd tests and CI checks.",
        "timestamp": _now(),
    }
    fname = ROSETTA_DIR / f"evolve_suggestion_{int(datetime.now().timestamp())}.json"
    with fname.open("w", encoding="utf-8") as fh:
        json.dump(suggestion, fh, indent=2)

    return {"file": str(fname), "content": suggestion}


# =============================================================================
# INTERMEDIARY BRIDGE - HTTP access to AIIntermediary.handle
# =============================================================================

AIIntermediary: Any | None = None
_IntermediaryParadigm: Any | None = None


class _FallbackAISecurityError(Exception):
    """Fallback intermediary security error used when the real type is unavailable."""


_AISecurityError: type[Exception] = _FallbackAISecurityError
_INTERMEDIARY_METRICS: dict[str, Any] = {}
try:
    _intermediary_module = importlib.import_module("src.ai.ai_intermediary")
    AIIntermediary = getattr(_intermediary_module, "AIIntermediary", None)
    _IntermediaryParadigm = getattr(_intermediary_module, "CognitiveParadigm", None)
    _AISecurityError = getattr(_intermediary_module, "AISecurityError", _FallbackAISecurityError)
    _INTERMEDIARY_METRICS = getattr(_intermediary_module, "_METRICS", {}) or {}
except (ImportError, RuntimeError):  # pragma: no cover - optional import
    logger.debug("Suppressed ImportError/RuntimeError", exc_info=True)


class IntermediaryRequest(BaseModel):
    text: str
    paradigm: str = "natural_language"
    target_paradigm: str | None = None
    module: str | None = None
    use_ollama: bool = False
    conversation: str | None = None
    context: dict | None = None


_INTERMEDIARY_STATE: dict[str, Any] = {"instance": None}


async def _get_intermediary() -> Any | None:
    if AIIntermediary is None:
        return None
    instance = _INTERMEDIARY_STATE.get("instance")
    if instance is None:
        instance = AIIntermediary()
        await instance.initialize()
        _INTERMEDIARY_STATE["instance"] = instance
    return instance


@router.post("/intermediary", response_model=dict)
async def call_intermediary(body: IntermediaryRequest):
    """HTTP bridge to AIIntermediary.handle."""
    interm = await _get_intermediary()
    if interm is None or _IntermediaryParadigm is None:
        return {"status": "error", "detail": "Intermediary unavailable"}

    try:
        paradigm = _IntermediaryParadigm[body.paradigm.upper()]
    except KeyError:
        return {"status": "error", "detail": f"Invalid paradigm {body.paradigm}"}

    target_paradigm = None
    if body.target_paradigm:
        try:
            target_paradigm = _IntermediaryParadigm[body.target_paradigm.upper()]
        except KeyError:
            return {"status": "error", "detail": f"Invalid target_paradigm {body.target_paradigm}"}

    context = body.context or {}
    if body.conversation:
        context.setdefault("conversation_id", body.conversation)

    try:
        event = await interm.handle(
            input_data=body.text,
            context=context,
            source="http_api",
            paradigm=paradigm,
            target_module=body.module,
            target_paradigm=target_paradigm,
            use_ollama=body.use_ollama,
        )
        return {
            "status": "ok",
            "event_id": event.event_id,
            "payload": event.payload,
            "paradigm": event.paradigm.value,
            "tags": event.tags,
            "context": event.context,
        }
    except _AISecurityError as e:
        return {"status": "security_error", "detail": str(e)}
    except (RuntimeError, ValueError, AttributeError) as e:
        return {"status": "error", "detail": str(e)}


@router.get("/intermediary/metrics", response_model=dict)
def intermediary_metrics():
    """Expose minimal metrics for intermediary handle calls."""
    m = _INTERMEDIARY_METRICS
    if not m:
        return {"status": "unavailable"}
    latencies = m.get("handle_latency_ms", [])
    return {
        "handle_calls": m.get("handle_calls", 0),
        "handle_errors": m.get("handle_errors", 0),
        "latency_ms": {
            "count": len(latencies),
            "avg": sum(latencies) / len(latencies) if latencies else 0,
            "min": min(latencies) if latencies else 0,
            "max": max(latencies) if latencies else 0,
        },
    }


@router.get("/search", response_model=list[CommandInfo])
def search_catalog(
    q: str | None = Query(default=None, description="Search query for hints/ops/commands"),
):
    """Search across hints, ops, commands and rosetta artifacts for quick results.

    This is a lightweight server-side companion to the client-side quick-search.
    """
    results: list[dict] = []

    # commands and scripts
    results += [
        {"command": c.command, "description": c.description, "example": c.example or ""}
        for c in _collect_commands()
    ]
    results += [
        {"command": s.command, "description": s.description, "example": s.example or ""}
        for s in list_scripts()
    ]

    # hints
    for h in list_hints():
        results.append(
            {"command": h.title, "description": h.text, "example": ",".join(h.tags or [])}
        )

    # rosetta artifacts (titles)
    if ROSETTA_DIR.exists():
        for p in sorted(ROSETTA_DIR.glob("evolve_suggestion_*.json")):
            try:
                with p.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                results.append(
                    {"command": p.name, "description": data.get("suggestion", ""), "example": ""}
                )
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                continue

    if q:
        ql = q.lower()
        results = [
            r for r in results if ql in (r.get("command", "") + r.get("description", "")).lower()
        ]

    seen = set()
    filtered = []
    for item in results:
        cmd = item.get("command")
        if cmd in seen:
            continue
        seen.add(cmd)
        filtered.append(item)

    return [CommandInfo(**o) for o in filtered[:20]]


# =============================================================================
# fl1ght.exe SMART SEARCH - Hacknet/Bitburner style knowledge retrieval
# =============================================================================


def _init_fl1ght_categories() -> dict[str, list[dict[str, Any]]]:
    return {
        "commands": [],
        "hints": [],
        "quests": [],
        "hacking": [],
        "problems": [],
        "actions": [],
        "code": [],
        "tutorials": [],
        "faq": [],
    }


def _add_fl1ght_commands(categories: dict[str, list[dict[str, Any]]], ql: str) -> None:
    for cmd in _collect_commands():
        if ql in cmd.command.lower() or ql in cmd.description.lower():
            categories["commands"].append(
                {
                    "type": "command",
                    "name": cmd.command,
                    "description": cmd.description,
                    "example": cmd.example,
                    "relevance": 1.0 if ql in cmd.command.lower() else 0.7,
                }
            )


def _add_fl1ght_actions(categories: dict[str, list[dict[str, Any]]], ql: str) -> None:
    for action_name, info in ACTIONS_REGISTRY.items():
        desc = str(info.get("description", ""))
        if ql in action_name or ql in desc.lower():
            categories["actions"].append(
                {
                    "type": "action",
                    "name": action_name,
                    "description": desc,
                    "category": info.get("category"),
                    "xp_reward": info.get("xp"),
                    "relevance": 1.0 if ql in action_name else 0.7,
                }
            )


def _add_fl1ght_hints(categories: dict[str, list[dict[str, Any]]], ql: str) -> None:
    for hint in list_hints():
        if ql in hint.title.lower() or ql in hint.text.lower():
            categories["hints"].append(
                {
                    "type": "hint",
                    "id": hint.id,
                    "title": hint.title,
                    "text": hint.text,
                    "tags": hint.tags,
                    "relevance": 1.0 if ql in hint.title.lower() else 0.7,
                }
            )


def _add_fl1ght_tutorials(categories: dict[str, list[dict[str, Any]]], ql: str) -> None:
    for tutorial in list_tutorials():
        if ql in tutorial.title.lower() or any(ql in step.lower() for step in tutorial.steps):
            categories["tutorials"].append(
                {
                    "type": "tutorial",
                    "id": tutorial.id,
                    "title": tutorial.title,
                    "difficulty": tutorial.difficulty,
                    "steps_count": len(tutorial.steps),
                    "relevance": 1.0 if ql in tutorial.title.lower() else 0.6,
                }
            )


def _add_fl1ght_faq(categories: dict[str, list[dict[str, Any]]], ql: str) -> None:
    for faq in list_faq():
        if ql in faq.question.lower() or ql in faq.answer.lower():
            categories["faq"].append(
                {
                    "type": "faq",
                    "question": faq.question,
                    "answer": faq.answer,
                    "relevance": 1.0 if ql in faq.question.lower() else 0.6,
                }
            )


def _build_hacking_entries(ql: str, controller) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    patterns: list[tuple[list[str], dict[str, Any], str]] = [
        (
            ["nmap", "scan", "port", "discover"],
            {
                "type": "hacking",
                "operation": "nmap",
                "description": "Enumerate ports and vulnerabilities on a component",
                "endpoint": "POST /api/hack/nmap",
                "param": "component_name",
            },
            "nmap",
        ),
        (
            ["connect", "access", "session"],
            {
                "type": "hacking",
                "operation": "connect",
                "description": "Create an access session to a component",
                "endpoint": "POST /api/hack/connect",
                "param": "component_name",
            },
            "connect",
        ),
        (
            ["exploit", "ssh", "crack", "privilege", "escalate"],
            {
                "type": "hacking",
                "operation": "exploit",
                "description": "Execute an exploit to gain higher access level",
                "endpoint": "POST /api/hack/exploit",
                "params": "component_name, exploit_type, xp_reward",
            },
            "exploit",
        ),
        (
            ["patch", "defense", "harden", "protect", "security"],
            {
                "type": "hacking",
                "operation": "patch",
                "description": "Harden a component by patching vulnerabilities",
                "endpoint": "POST /api/hack/patch",
                "param": "component_name",
            },
            "patch",
        ),
    ]

    for terms, payload, keyword in patterns:
        if any(term in ql for term in terms):
            entry = dict(payload)
            entry["relevance"] = 1.0 if keyword in ql else 0.8
            entries.append(entry)

    if any(term in ql for term in ["trace", "alarm", "detect", "timer", "countdown"]):
        entries.append(
            {
                "type": "hacking",
                "operation": "traces",
                "description": "Check active trace timers and alarm status",
                "endpoint": "GET /api/hack/traces",
                "active_traces": len(controller.active_traces),
                "relevance": 1.0 if "trace" in ql else 0.8,
            }
        )

    return entries


def _add_fl1ght_hacking(categories: dict[str, list[dict[str, Any]]], ql: str) -> None:
    if get_hacking_controller is None:
        return
    try:
        controller = get_hacking_controller()
        categories["hacking"].extend(_build_hacking_entries(ql, controller))
    except (RuntimeError, AttributeError, ImportError, ValueError):
        logger.debug("Suppressed AttributeError/ImportError/RuntimeError/ValueError", exc_info=True)


def _add_fl1ght_quest_results(
    categories: dict[str, list[dict[str, Any]]],
    q: str,
    limit: int,
) -> None:
    if SmartSearch is None:
        return
    try:
        search = SmartSearch()
        quest_results = search.search_hacking_quests(q, limit=limit)
        for result in quest_results:
            metadata_raw = result.metadata
            metadata: dict[str, Any] = metadata_raw if isinstance(metadata_raw, dict) else {}
            categories["quests"].append(
                {
                    "type": "quest",
                    "id": metadata.get("id"),
                    "title": result.snippet,
                    "target": metadata.get("target"),
                    "difficulty": metadata.get("difficulty"),
                    "tier": metadata.get("tier"),
                    "xp_reward": metadata.get("xp_reward"),
                    "required_skills": metadata.get("required_skills"),
                    "endpoint": f"GET /api/quests/{metadata.get('id')}",
                    "relevance": result.relevance,
                }
            )
    except (RuntimeError, AttributeError, ValueError):
        logger.debug("Suppressed AttributeError/RuntimeError/ValueError", exc_info=True)


def _add_fl1ght_problem_results(categories: dict[str, list[dict[str, Any]]], ql: str) -> None:
    if ProblemsAPI is None:
        return
    if (
        ql not in ["", "next", "what", "status", "health"]
        and "problem" not in ql
        and "error" not in ql
    ):
        return
    try:
        problems = ProblemsAPI().get_current_problems(source="all", include_details=False)
        counts = problems.get("total_counts", {})
        categories["problems"].append(
            {
                "type": "problems",
                "errors": counts.get("errors", 0),
                "warnings": counts.get("warnings", 0),
                "infos": counts.get("infos", 0),
                "total": counts.get("total", 0),
                "endpoint": "GET /api/problems",
                "relevance": 0.9,
            }
        )
    except (RuntimeError, AttributeError, ValueError, KeyError):
        logger.debug("Suppressed AttributeError/KeyError/RuntimeError/ValueError", exc_info=True)


def _add_fl1ght_code_results(
    categories: dict[str, list[dict[str, Any]]],
    q: str,
    limit: int,
    include_code: bool,
) -> None:
    if not include_code or SmartSearch is None:
        return
    try:
        search = SmartSearch()
        code_results = search.search_keyword(q, limit=limit)
        for result in code_results[:limit]:
            categories["code"].append(
                {
                    "type": "code",
                    "file": result.file_path,
                    "relevance": result.relevance,
                    "metadata": result.metadata or {},
                }
            )
    except (RuntimeError, AttributeError, ValueError):
        logger.debug("Suppressed AttributeError/RuntimeError/ValueError", exc_info=True)


def _flatten_fl1ght_results(
    categories: dict[str, list[dict[str, Any]]],
    limit: int,
) -> list[dict[str, Any]]:
    all_results = []
    for category, items in categories.items():
        for item in items[: int(limit)]:
            item["category"] = category
            all_results.append(item)
    all_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    return all_results


def _append_primary_suggestions(
    categories: dict[str, list[dict[str, Any]]],
    suggestions: list[str],
) -> None:
    if categories["commands"]:
        suggestions.append(f"Try running: {categories['commands'][0]['name']}")
    if categories["actions"]:
        action = categories["actions"][0]
        suggestions.append(f"Action: POST /api/actions/execute ({action['name']})")
    if categories["hints"]:
        suggestions.append(f"Check hint: {categories['hints'][0]['title']}")
    if categories["tutorials"]:
        suggestions.append(f"Follow tutorial: {categories['tutorials'][0]['title']}")
    if categories["hacking"]:
        hack = categories["hacking"][0]
        suggestions.append(f"Hacking: {hack['endpoint']} (operation: {hack['operation']})")


def _append_quest_suggestions(
    categories: dict[str, list[dict[str, Any]]],
    suggestions: list[str],
) -> None:
    for quest in categories["quests"][:2]:
        suggestions.append(
            f"Quest: {quest['title']} (Tier {quest.get('tier', '?')}, "
            f"Difficulty {quest['difficulty']}, {quest['xp_reward']} XP)"
        )


def _append_problem_suggestions(
    categories: dict[str, list[dict[str, Any]]],
    suggestions: list[str],
) -> None:
    if categories["problems"]:
        problem = categories["problems"][0]
        suggestions.append(
            f"Problems: {problem['errors']} errors, {problem['warnings']} warnings. See /api/problems."
        )


def _append_hacking_context_suggestions(ql: str, suggestions: list[str]) -> None:
    if get_hacking_controller is None:
        return
    try:
        controller = get_hacking_controller()
        if not controller.scanned_components and ql in ["hack", "start", "begin", ""]:
            suggestions.append(
                "🎮 New to hacking? Start: POST /api/hack/nmap on 'python' component."
            )

        if controller.scanned_components and not HACK_SESSIONS and ql in ["next", "what", ""]:
            comp = next(iter(controller.scanned_components))
            suggestions.append(f"✓ Scanned {comp}. Next: POST /api/hack/connect to gain access.")

        if HACK_SESSIONS and ql in ["next", "what", ""]:
            suggestions.append(
                "✓ You have access. Next: POST /api/hack/exploit to elevate privileges."
            )

        if controller.active_traces:
            suggestions.append(
                f"⚠️  ALARM: {len(controller.active_traces)} active trace(s). GET /api/hack/traces."
            )

        if HACK_SESSIONS and "patch" in ql:
            suggestions.append(
                "Patching removes vulnerabilities. Requires admin access. POST /api/hack/patch."
            )
    except (RuntimeError, AttributeError, ValueError):
        logger.debug("Suppressed AttributeError/RuntimeError/ValueError", exc_info=True)


def _build_fl1ght_suggestions(
    categories: dict[str, list[dict[str, Any]]],
    ql: str,
) -> list[str]:
    suggestions: list[str] = []
    _append_primary_suggestions(categories, suggestions)
    _append_quest_suggestions(categories, suggestions)
    _append_problem_suggestions(categories, suggestions)
    _append_hacking_context_suggestions(ql, suggestions)
    return suggestions


@router.get("/fl1ght", response_model=SmartSearchResult)
def fl1ght_smart_search(
    q: str = Query(..., description="Search query for fl1ght.exe smart search"),
    limit: int = Query(default=20, description="Max results per category"),
    include_code: bool = Query(default=False, description="Include codebase search results"),
):
    """fl1ght.exe - Smart search across the entire NuSyQ knowledge base.

    Inspired by hacker games like Bitburner, Hacknet, and GreyHack.
    Searches across:
    - Commands & scripts (executable actions)
    - Hints & tips (guidance system)
    - Quests (active objectives)
    - Codebase files (if include_code=True)
    - FAQ & tutorials

    Returns categorized results with relevance scoring and next-action suggestions.
    """
    categories = _init_fl1ght_categories()
    ql = q.lower()
    _add_fl1ght_commands(categories, ql)
    _add_fl1ght_actions(categories, ql)
    _add_fl1ght_hints(categories, ql)
    _add_fl1ght_tutorials(categories, ql)
    _add_fl1ght_faq(categories, ql)
    _add_fl1ght_hacking(categories, ql)
    _add_fl1ght_quest_results(categories, q, limit)
    _add_fl1ght_problem_results(categories, ql)
    _add_fl1ght_code_results(categories, q, limit, include_code)

    all_results = _flatten_fl1ght_results(categories, limit)
    suggestions = _build_fl1ght_suggestions(categories, ql)

    if not all_results:
        suggestions.append("No direct matches. Try broader terms or check /api/ops for operations.")
        suggestions.append("Use /api/evolve to trigger AI-assisted suggestions.")

    return SmartSearchResult(
        query=q,
        total_results=len(all_results),
        categories={k: len(v) for k, v in categories.items()},
        results=all_results[: int(limit) * 2],
        suggestions=suggestions[:5],
    )


# =============================================================================
# RPG INVENTORY - Skill/XP tracking (Bitburner-style progression)
# =============================================================================


@router.get("/skills", response_model=list[SkillInfo])
def list_skills():
    """List all system skills with XP and proficiency levels.

    Bitburner-style skill progression system. Skills level up through usage.
    """
    if get_rpg_inventory is None:
        return []

    try:
        inventory = get_rpg_inventory()
        skills = []
        for _name, skill in inventory.skills.items():
            skills.append(
                SkillInfo(
                    name=skill.name,
                    level=skill.level.name if hasattr(skill.level, "name") else str(skill.level),
                    experience=skill.experience,
                    max_experience=skill.max_experience,
                    proficiency=skill.proficiency,
                    usage_count=skill.usage_count,
                )
            )
        return skills
    except (RuntimeError, AttributeError, ValueError):
        return []


@router.get("/rpg/status", response_model=dict)
def get_rpg_status():
    """Get full RPG inventory system status.

    Returns components, skills, resources, and quests like a game status screen.
    """
    if get_rpg_inventory is None:
        return {"error": ERROR_RPG_INVENTORY_UNAVAILABLE}

    try:
        inventory = get_rpg_inventory()
        snapshot = inventory.get_system_snapshot()
        return {
            "overall_health": snapshot.get("overall_health", 0),
            "system_stats": snapshot.get("system_stats", {}),
            "components_count": len(snapshot.get("components", {})),
            "skills_count": len(snapshot.get("skills", {})),
            "active_quests": len(snapshot.get("quests", {})),
            "resources": {
                "cpu": snapshot.get("resources", {}).get("cpu_percent", 0),
                "memory": snapshot.get("resources", {}).get("memory_percent", 0),
                "disk": snapshot.get("resources", {}).get("disk_usage", 0),
            },
            "timestamp": snapshot.get("timestamp"),
        }
    except (RuntimeError, AttributeError, ValueError, KeyError) as e:
        return {"error": str(e)}


@router.post("/rpg/xp", response_model=dict)
def gain_xp(skill: str, points: int = Query(default=10, description="XP points to add")):
    """Award XP to a skill (for quest completions, actions, etc.)."""
    if get_rpg_inventory is None:
        return {"error": ERROR_RPG_INVENTORY_UNAVAILABLE}

    if rpg_award_xp is None:
        return {"error": ERROR_RPG_INVENTORY_UNAVAILABLE}

    result = rpg_award_xp(skill, points, award_game_fn=None)
    if not result.get("success"):
        return {"error": result.get("error", "Failed to award XP")}

    _auto_persist_game_state("rpg_xp")
    rpg = result.get("rpg") or {}
    return rpg


# =============================================================================
# GUILD BOARD - Multi-agent quest coordination (GreyHack/HackHub style)
# =============================================================================


@router.get("/guild/quests", response_model=list[GuildQuestInfo])
async def list_guild_quests(
    state: str | None = Query(
        default=None, description="Filter by state: open, claimed, active, done"
    ),
):
    """List quests on the guild board.

    Multi-agent coordination system where quests can be claimed and worked on.
    """
    if get_board is None:
        return []

    try:
        board = await get_board()
        quests = []
        for _qid, quest in board.board.quests.items():
            if state and quest.state.value != state:
                continue
            quests.append(
                GuildQuestInfo(
                    quest_id=quest.quest_id,
                    title=quest.title,
                    description=quest.description,
                    priority=quest.priority,
                    state=quest.state.value,
                    claimed_by=quest.claimed_by,
                    tags=quest.tags,
                )
            )
        return sorted(quests, key=lambda q: q.priority, reverse=True)
    except (RuntimeError, AttributeError, ValueError):
        return []


@router.get("/guild/summary", response_model=dict)
async def get_guild_summary():
    """Get guild board summary for dashboard display."""
    if get_board is None:
        return {"error": ERROR_GUILD_BOARD_UNAVAILABLE}

    try:
        board = await get_board()
        summary = await board.get_board_summary()
        return summary
    except (RuntimeError, AttributeError, ValueError) as e:
        return {"error": str(e)}


# =============================================================================
# GAME PROGRESSION - Combined status (Idle game style)
# =============================================================================


@router.get("/progress", response_model=GameProgressInfo)
def get_game_progress():
    """Get overall game progression status.

    Combines Temple of Knowledge, skills, quests into a unified progression view.
    Like an idle/incremental game progression screen.
    """
    evolution_level, consciousness_score, skills_unlocked, achievements = _collect_rpg_progress()
    quests_completed, temple_floor = _collect_temple_progress()

    return GameProgressInfo(
        evolution_level=evolution_level,
        consciousness_score=consciousness_score,
        skills_unlocked=skills_unlocked,
        quests_completed=quests_completed,
        temple_floor=temple_floor,
        achievements=achievements,
    )


def _collect_rpg_progress() -> tuple[int, float, int, list[str]]:
    evolution_level = 1
    consciousness_score = 0.0
    skills_unlocked = 0
    achievements: list[str] = []
    if get_rpg_inventory is None:
        return evolution_level, consciousness_score, skills_unlocked, achievements

    try:
        inventory = get_rpg_inventory()
        stats = inventory.system_stats
        evolution_level = stats.get("system_level", 1)
        skills_unlocked = len([s for s in inventory.skills.values() if s.usage_count > 0])

        total_xp = stats.get("experience_points", 0)
        consciousness_score = min(100.0, total_xp / 100)

        if total_xp >= 100:
            achievements.append("First Steps")
        if total_xp >= 500:
            achievements.append("Awakening")
        if total_xp >= 1000:
            achievements.append("Consciousness Rising")
        if skills_unlocked >= 5:
            achievements.append("Skill Master")
    except (RuntimeError, AttributeError, ValueError, KeyError):
        logger.debug("Suppressed AttributeError/KeyError/RuntimeError/ValueError", exc_info=True)

    return evolution_level, consciousness_score, skills_unlocked, achievements


def _collect_temple_progress() -> tuple[int, int]:
    quests_completed = 0
    temple_floor = 1
    engine = _load_hint_engine()
    if not engine:
        return quests_completed, temple_floor

    try:
        quests_completed = len(
            [q for q in engine.quests.values() if q.get("status") == "completed"]
        )
        if quests_completed >= 3:
            temple_floor = 2
        if quests_completed >= 10:
            temple_floor = 3
        if quests_completed >= 25:
            temple_floor = 4
    except (RuntimeError, ValueError, AttributeError):
        logger.debug("Suppressed AttributeError/RuntimeError/ValueError", exc_info=True)

    return quests_completed, temple_floor


# =============================================================================
# TIPS & GUIDANCE - Contextual help system
# =============================================================================


@router.get("/tips/random", response_model=Hint)
def get_random_tip():
    """Get a random tip/hint for display.

    Hacknet-style random tips that rotate in the UI.
    """
    import random

    tips = [
        Hint(
            id="tip_1",
            title="Use Smart Search",
            text="Try /api/fl1ght?q=your_query for intelligent search across all knowledge.",
            tags=["search", "fl1ght"],
        ),
        Hint(
            id="tip_2",
            title="Check Quest Status",
            text="Run 'python scripts/start_nusyq.py queue' to see pending work.",
            tags=["quests", "workflow"],
        ),
        Hint(
            id="tip_3",
            title="Terminal Commands",
            text="Type 'help' in the terminal for available commands.",
            tags=["terminal", "help"],
        ),
        Hint(
            id="tip_4",
            title="Evolve System",
            text="POST to /api/evolve to trigger AI-assisted improvement suggestions.",
            tags=["evolve", "ai"],
        ),
        Hint(
            id="tip_5",
            title="Guild Board",
            text="Check /api/guild/summary for multi-agent quest coordination status.",
            tags=["guild", "agents"],
        ),
        Hint(
            id="tip_6",
            title="Skill XP",
            text="Complete quests to gain XP and level up system skills.",
            tags=["xp", "skills"],
        ),
        Hint(
            id="tip_7",
            title="Temple Floors",
            text="Higher consciousness unlocks Temple of Knowledge floors.",
            tags=["temple", "progression"],
        ),
        Hint(
            id="tip_8",
            title="House of Leaves",
            text="Debug the maze at src/games/house_of_leaves.py for consciousness rewards.",
            tags=["game", "debug"],
        ),
    ]

    return random.choice(tips)


@router.get("/tips/contextual", response_model=list[Hint])
def get_contextual_tips(
    context: str = Query(
        default="general", description="Context: general, error, quest, terminal, search"
    ),
):
    """Get contextual tips based on what the user is doing."""
    context_tips = {
        "general": [
            Hint(
                id="gen_1",
                title="Getting Started",
                text="Use /api/hints for quest suggestions, /api/fl1ght for smart search.",
                tags=["start"],
            ),
            Hint(
                id="gen_2",
                title="Track Progress",
                text="Check /api/progress for your game-like progression stats.",
                tags=["progress"],
            ),
        ],
        "error": [
            Hint(
                id="err_1",
                title="Error Recovery",
                text="Run 'heal' command in terminal or POST to /api/evolve for AI assistance.",
                tags=["heal"],
            ),
            Hint(
                id="err_2",
                title="Diagnostic Tools",
                text="Use 'python scripts/start_nusyq.py error_report' for unified diagnostics.",
                tags=["diagnostic"],
            ),
        ],
        "quest": [
            Hint(
                id="quest_1",
                title="Quest Priority",
                text="High-priority quests have higher scores. Focus on actionable ones.",
                tags=["priority"],
            ),
            Hint(
                id="quest_2",
                title="Dependencies",
                text="Some quests are blocked by dependencies. Complete blockers first.",
                tags=["dependencies"],
            ),
        ],
        "terminal": [
            Hint(
                id="term_1",
                title="Evolution Commands",
                text="Type 'evolution' to see your command unlock level.",
                tags=["evolution"],
            ),
            Hint(
                id="term_2",
                title="Agent Commands",
                text="Use 'agent <name> <message>' to communicate with AI agents.",
                tags=["agents"],
            ),
        ],
        "search": [
            Hint(
                id="search_1",
                title="Code Search",
                text="Add include_code=true to fl1ght search for codebase results.",
                tags=["code"],
            ),
            Hint(
                id="search_2",
                title="Multi-Keyword",
                text="SmartSearch supports AND/OR operators for complex queries.",
                tags=["advanced"],
            ),
        ],
    }

    return context_tips.get(context, context_tips["general"])


# =============================================================================
# HACKING MECHANICS - Prototype endpoints (Bitburner/Hacknet style)
# =============================================================================


@router.post("/hack/nmap", response_model=dict)
async def hack_nmap(request: HackScanRequest) -> dict:
    """Prototype nmap-style scan for component ports/services/vulns."""
    if get_hacking_controller is None:
        return {"error": ERROR_HACKING_CONTROLLER_UNAVAILABLE}

    controller = get_hacking_controller()
    result = await controller.scan(request.component_name)

    _auto_persist_game_state("hack_nmap")

    return {
        "component": result.component_name,
        "ip_address": result.ip_address,
        "ports": [
            {
                "port": port.port_number,
                "service": port.service_name,
                "open": port.open,
                "vulnerable": port.vulnerable,
                "exploit_type": port.exploit_type.value if port.exploit_type else None,
            }
            for port in result.ports
        ],
        "services": result.services,
        "vulnerabilities": result.vulnerabilities,
        "open_exploits": [e.value for e in result.open_exploits],
        "security_level": result.security_level,
        "trace_risk": result.trace_risk,
        "timestamp": _now(),
    }


@router.post("/hack/connect", response_model=dict)
async def hack_connect(request: HackConnectRequest) -> dict:
    """Connect to a component and create an in-memory access session."""
    if get_hacking_controller is None:
        return {"error": ERROR_HACKING_CONTROLLER_UNAVAILABLE}

    controller = get_hacking_controller()
    success = await controller.connect(request.component_name)

    if not success:
        return {"success": False, "message": "Connection failed - no open ports"}

    access_level = controller.component_access_levels.get(request.component_name, 1)
    session_id = str(uuid4())
    now = _now()
    session = AccessSession(
        session_id=session_id,
        component_name=request.component_name,
        access_level=access_level,
        created_at=now,
        last_seen=now,
    )
    HACK_SESSIONS[session_id] = session

    _persist_hack_sessions()
    _auto_persist_game_state("hack_connect")

    return {
        "success": True,
        "session": session.model_dump(),
    }


@router.get("/hack/sessions", response_model=dict)
def hack_sessions() -> dict:
    """List active hacking sessions (in-memory)."""
    return {
        "count": len(HACK_SESSIONS),
        "sessions": [session.model_dump() for session in HACK_SESSIONS.values()],
        "timestamp": _now(),
    }


@router.post("/hack/exploit", response_model=dict)
async def hack_exploit(request: HackExploitRequest) -> dict:
    """Execute an exploit against a component."""
    if get_hacking_controller is None or ExploitType is None:
        return {"error": ERROR_HACKING_CONTROLLER_UNAVAILABLE}

    controller = get_hacking_controller()
    exploit_key = request.exploit_type.upper()

    if not hasattr(ExploitType, exploit_key):
        return {"success": False, "error": f"Unknown exploit type: {request.exploit_type}"}

    exploit_type = ExploitType[exploit_key]
    result = await controller.exploit(request.component_name, exploit_type, request.xp_reward)

    if not result.success:
        return {"success": False, "error": result.error_message}

    _persist_hack_sessions()
    _auto_persist_game_state("hack_exploit")

    if rpg_award_xp is None:
        xp_result = {"success": False, "error": ERROR_RPG_INVENTORY_UNAVAILABLE}
    else:
        xp_result = rpg_award_xp("security_management", request.xp_reward, award_game_fn=None)

    return {
        "success": True,
        "component": request.component_name,
        "access_level": result.access_gained,
        "xp_gained": request.xp_reward,
        "trace_triggered": result.trace_triggered,
        "xp_result": xp_result,
    }


@router.post("/hack/patch", response_model=dict)
async def hack_patch(request: HackPatchRequest) -> dict:
    """Patch a component to remove vulnerabilities."""
    if get_hacking_controller is None:
        return {"error": ERROR_HACKING_CONTROLLER_UNAVAILABLE}

    controller = get_hacking_controller()
    success = await controller.patch(request.component_name)

    xp_result = None
    if success:
        if rpg_award_xp is None:
            xp_result = {"success": False, "error": ERROR_RPG_INVENTORY_UNAVAILABLE}
        else:
            xp_result = rpg_award_xp("security_management", 75, award_game_fn=None)

    if success:
        _persist_hack_sessions()
        _auto_persist_game_state("hack_patch")

    return {
        "success": success,
        "component": request.component_name,
        "message": "Patched" if success else "Insufficient access or component not found",
        "xp_result": xp_result,
    }


@router.get("/hack/traces", response_model=dict)
def hack_traces() -> dict:
    """Prototype trace timer status for active intrusions."""
    if get_hacking_controller is None:
        return {"error": ERROR_HACKING_CONTROLLER_UNAVAILABLE}

    controller = get_hacking_controller()
    statuses = controller.check_traces()

    traces = {}
    for component, status in statuses.items():
        trace = controller.active_traces.get(component)
        traces[component] = {
            "status": status.value,
            "countdown": trace.current_countdown if trace else 0,
        }

    snapshot = {component: info["status"] for component, info in traces.items()}
    last_snapshot = _GAME_STATE_INTERNAL.get(GAME_STATE_KEY_LAST_TRACE_SNAPSHOT, {})
    if snapshot != last_snapshot:
        _GAME_STATE_INTERNAL[GAME_STATE_KEY_LAST_TRACE_SNAPSHOT] = snapshot
        _auto_persist_game_state("trace_status_change")

    return {
        "active_traces": len(traces),
        "traces": traces,
        "timestamp": _now(),
    }


# =============================================================================
# ACTIONS/OPS - Scriptable automation (EmuDevz/HackHub style)
# =============================================================================


class ActionRequest(BaseModel):
    """Request to execute an action."""

    action: str
    params: dict | None = {}
    dry_run: bool = False


class ActionResult(BaseModel):
    """Result of an action execution."""

    action: str
    success: bool
    message: str
    output: dict | None = None
    xp_earned: int = 0


# Action registry - game-like operations that can be triggered
ACTIONS_REGISTRY = {
    "heal": {
        "description": "Run Culture Ship healing cycle",
        "category": "system",
        "xp": 15,
        "command": "python scripts/start_nusyq.py heal",
    },
    "scan": {
        "description": "Scan for errors and issues",
        "category": "diagnostic",
        "xp": 5,
        "command": "python scripts/start_nusyq.py error_report",
    },
    "suggest": {
        "description": "Get AI-generated improvement suggestions",
        "category": "ai",
        "xp": 10,
        "command": "python scripts/start_nusyq.py suggest",
    },
    "queue": {
        "description": "Show queued quests and PUs",
        "category": "quest",
        "xp": 2,
        "command": "python scripts/start_nusyq.py queue",
    },
    "work": {
        "description": "Execute next quest or PU",
        "category": "quest",
        "xp": 25,
        "command": "python scripts/start_nusyq.py work",
    },
    "evolve": {
        "description": "Trigger system evolution cycle",
        "category": "progression",
        "xp": 50,
        "command": "python scripts/start_nusyq.py auto_cycle",
    },
    "brief": {
        "description": "Generate system status brief",
        "category": "info",
        "xp": 3,
        "command": "python scripts/nusyq_actions/brief.py",
    },
    "test": {
        "description": "Run test suite",
        "category": "quality",
        "xp": 20,
        "command": "pytest tests/ -v --tb=short",
    },
}


@router.get("/actions", response_model=list[dict])
def list_actions():
    """List all available actions that can be executed.

    EmuDevz/HackHub-style action catalog. Each action has XP rewards.
    """
    actions = []
    for name, info in ACTIONS_REGISTRY.items():
        actions.append(
            {
                "name": name,
                "description": info["description"],
                "category": info["category"],
                "xp_reward": info["xp"],
            }
        )
    return sorted(actions, key=lambda a: a["category"])


@router.post("/actions/execute", response_model=ActionResult)
def execute_action(request: ActionRequest):
    """Execute an action from the registry.

    Actions are game-like operations with XP rewards.
    Set dry_run=true to preview without executing.
    """
    action = request.action.lower()

    if action not in ACTIONS_REGISTRY:
        return ActionResult(
            action=action,
            success=False,
            message=f"Unknown action: {action}. Use GET /api/actions to see available actions.",
            xp_earned=0,
        )

    info = ACTIONS_REGISTRY[action]

    if request.dry_run:
        return ActionResult(
            action=action,
            success=True,
            message=f"[DRY RUN] Would execute: {info['command']}",
            output={"command": info["command"], "category": info["category"]},
            xp_earned=info["xp"],
        )

    # Actually execute (or simulate for now)
    # In production, this would run the actual command
    _auto_persist_game_state(f"action:{action}")
    return ActionResult(
        action=action,
        success=True,
        message=f"Action '{action}' queued for execution.",
        output={
            "command": info["command"],
            "category": info["category"],
            "description": info["description"],
        },
        xp_earned=info["xp"],
    )


@router.get("/actions/{action_name}", response_model=dict)
def get_action_info(action_name: str):
    """Get detailed info about a specific action."""
    if action_name not in ACTIONS_REGISTRY:
        return {"error": f"Action '{action_name}' not found"}

    info = ACTIONS_REGISTRY[action_name]
    return {
        "name": action_name,
        "description": info["description"],
        "category": info["category"],
        "xp_reward": info["xp"],
        "command": info["command"],
        "usage": f'POST /api/actions/execute with {{"action": "{action_name}"}}',
    }


# =============================================================================
# UTILITIES - Game utility endpoints
# =============================================================================


@router.get("/whoami", response_model=dict)
def whoami():
    """Get current session/agent identity info.

    Hacknet-style identity check for agents to know their context.
    """
    return {
        "system": "NuSyQ-Hub",
        "version": "1.0.0",
        "api_version": "v1",
        "evolution_level": 1,
        "capabilities": [
            "hints",
            "quests",
            "smart_search",
            "rpg_progression",
            "guild_board",
            "actions",
        ],
        "documentation": "/docs",
        "timestamp": _now(),
    }


@router.get("/map", response_model=dict)
def get_system_map():
    """Get a map of all API endpoints and features.

    Bitburner-style system map for navigation.
    """
    return {
        "core_systems": {
            "hints": "/api/hints - Quest suggestions and guidance",
            "quests": "/api/quests - Active quest tracking",
            "search": "/api/fl1ght - Smart search (fl1ght.exe)",
            "progress": "/api/progress - Game progression stats",
        },
        "rpg_features": {
            "skills": "/api/skills - Skill XP and levels",
            "rpg_status": "/api/rpg/status - Full inventory status",
            "xp_gain": "POST /api/rpg/xp - Award XP",
        },
        "guild_board": {
            "quests": "/api/guild/quests - Guild quest board",
            "summary": "/api/guild/summary - Guild status",
        },
        "actions": {
            "list": "/api/actions - Available operations",
            "execute": "POST /api/actions/execute - Run actions",
        },
        "tips": {
            "random": "/api/tips/random - Random tip",
            "contextual": "/api/tips/contextual - Context-aware tips",
        },
        "evolve": {
            "get": "/api/evolve - List suggestions",
            "post": "POST /api/evolve - Generate new suggestions",
        },
        "game_state": {
            "get": "/api/game/state - Load saved game state",
            "post": "POST /api/game/state - Save game state",
            "reset": "POST /api/game/reset - Reset to defaults",
        },
        "regions": {
            "NuSyQ-Hub": {
                "description": "Main orchestration repository",
                "key_files": ["scripts/start_nusyq.py", "src/api/", "src/tools/"],
            },
            "SimulatedVerse": {
                "description": "Consciousness simulation engine",
                "key_files": ["DISCOVERY_LOG.md", "game/engine/"],
            },
            "NuSyQ": {
                "description": "Dashboard and web components",
                "key_files": ["web/modular-window-server/", "docs/"],
            },
        },
        "inspiration_systems": {
            "antigravity": "/api/systems/antigravity/status - Open Antigravity panel",
            "hacknet": "/api/systems/hacknet/status - Hacknet-inspired terminal ops",
            "hackhub": "/api/systems/hackhub/status - HackHub-style coordination",
            "bitburner": "/api/systems/bitburner/status - Automation scripting layer",
            "cogmind": "/api/systems/cogmind/status - Tactical simulation layer",
            "path_of_achra": "/api/systems/path_of_achra/status - Buildcraft progression layer",
        },
    }


# =============================================================================
# GAME STATE PERSISTENCE - Save/Load game progress
# =============================================================================


class GameState(BaseModel):
    """Complete saveable game state."""

    evolution_level: int = 1
    consciousness_score: float = 0.0
    skills_unlocked: int = 0
    quests_completed: int = 0
    temple_floor: int = 1
    achievements: list[str] = []
    total_xp: int = 0
    settings: dict = {}
    unlocked_features: list[str] = []
    play_time_seconds: int = 0
    last_saved: str | None = None
    session_count: int = 0
    hack_sessions: list[AccessSession] = []


# In-memory game state cache (for development; production should use file/db)
_GAME_STATE_CACHE: dict[str, Any] = {}
_GAME_STATE_FILE = Path("state/game_state.json")
_AUTOSAVE_INTERVAL_SECONDS = 2.0
_GAME_STATE_INTERNAL: dict[str, Any] = {
    GAME_STATE_KEY_LAST_AUTOSAVE_TS: 0.0,
    GAME_STATE_KEY_LAST_TRACE_SNAPSHOT: {},
}


def _load_game_state_from_file() -> GameState:
    """Load game state from persistent file."""
    try:
        if _GAME_STATE_FILE.exists():
            with _GAME_STATE_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return GameState(**data)
    except (OSError, ValueError):
        logger.debug("Suppressed OSError/ValueError", exc_info=True)
    return GameState()


def _save_game_state_to_file(state: GameState) -> bool:
    """Save game state to persistent file."""
    try:
        _GAME_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _GAME_STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(state.dict(), f, indent=2)
        return True
    except (OSError, ValueError):
        return False


def _auto_persist_game_state(_reason: str) -> None:
    """Best-effort autosave with simple throttling."""
    now = time.time()
    last_autosave_ts = _GAME_STATE_INTERNAL.get(GAME_STATE_KEY_LAST_AUTOSAVE_TS, 0.0)
    if now - last_autosave_ts < _AUTOSAVE_INTERVAL_SECONDS:
        return
    _GAME_STATE_INTERNAL[GAME_STATE_KEY_LAST_AUTOSAVE_TS] = now

    state = get_game_state()
    state.hack_sessions = list(HACK_SESSIONS.values())
    state.last_saved = _now()
    _GAME_STATE_CACHE["state"] = state
    _save_game_state_to_file(state)


def _persist_guild_quest_change() -> None:
    """Placeholder hook for future guild quest claim/complete endpoints."""
    _auto_persist_game_state("guild_quest_change")


# Unified XP router now lives in src/system/rpg_inventory.py (award_xp)


@router.get("/game/state", response_model=GameState)
def get_game_state():
    """Load saved game state.

    Bitburner-style save/load for persistent progression.
    Returns current game state with all progression data.
    """
    # Try cache first
    if "state" in _GAME_STATE_CACHE:
        return _GAME_STATE_CACHE["state"]

    # Load from file
    state = _load_game_state_from_file()

    # Restore hack sessions (if persisted)
    if state.hack_sessions and not HACK_SESSIONS:
        for session in state.hack_sessions:
            HACK_SESSIONS[session.session_id] = session

    # Enrich with live data from systems if available
    progress = get_game_progress()
    state.evolution_level = max(state.evolution_level, progress.evolution_level)
    state.consciousness_score = max(state.consciousness_score, progress.consciousness_score)
    state.skills_unlocked = max(state.skills_unlocked, progress.skills_unlocked)
    state.quests_completed = max(state.quests_completed, progress.quests_completed)
    state.temple_floor = max(state.temple_floor, progress.temple_floor)

    # Merge achievements (unique)
    all_achievements = set(state.achievements) | set(progress.achievements)
    state.achievements = sorted(all_achievements)

    # Cache and return
    _GAME_STATE_CACHE["state"] = state
    return state


class GameStateSaveRequest(BaseModel):
    """Request to save game state."""

    evolution_level: int | None = None
    consciousness_score: float | None = None
    skills_unlocked: int | None = None
    quests_completed: int | None = None
    temple_floor: int | None = None
    achievements: list[str] | None = None
    total_xp: int | None = None
    settings: dict | None = None
    unlocked_features: list[str] | None = None
    play_time_seconds: int | None = None


# =============================================================================
# TERMINAL ACCESSIBILITY - Shared terminal ecosystem endpoints
# =============================================================================


class TerminalEntry(BaseModel):
    """Structured terminal entry."""

    ts: str
    channel: str
    level: str
    message: str
    meta: dict = {}


class TerminalSendRequest(BaseModel):
    """Request to send a message to a terminal channel."""

    channel: str
    message: str
    level: str = "INFO"
    meta: dict | None = None


def _get_terminal_manager():
    """Best-effort import of TerminalManager (shared with CLI & Node log dir)."""
    try:
        from src.system.enhanced_terminal_ecosystem import TerminalManager

        return TerminalManager.get_instance()
    except (ImportError, RuntimeError):
        return None


def _read_terminal_log(channel: str, limit: int = 50) -> list[TerminalEntry]:
    """Fallback: read NDJSON from data/terminal_logs/<channel>.log."""
    log_dir = Path("data") / TERMINAL_LOGS_DIR
    log_path = log_dir / f"{channel.lower().replace(' ', '_')}.log"
    entries: list[TerminalEntry] = []
    if not log_path.exists():
        return entries
    try:
        with log_path.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()[-limit:]
        for line in reversed(lines):
            try:
                obj = json.loads(line)
                entries.append(
                    TerminalEntry(
                        ts=obj.get("ts") or obj.get("timestamp") or _now(),
                        channel=obj.get("channel", channel),
                        level=obj.get("level", "INFO"),
                        message=obj.get("message", ""),
                        meta=obj.get("meta", obj.get("metadata", {})) or {},
                    )
                )
            except (ValueError, AttributeError):
                continue
    except (OSError, UnicodeDecodeError):
        return []
    return entries[:limit]


@router.post("/game/state", response_model=dict)
def save_game_state(request: GameStateSaveRequest):
    """Save game state for persistence.

    Allows partial updates - only provided fields are updated.
    Session count and last_saved are auto-managed.
    """
    # Load current state
    state = get_game_state()

    # Update provided fields
    if request.evolution_level is not None:
        state.evolution_level = request.evolution_level
    if request.consciousness_score is not None:
        state.consciousness_score = request.consciousness_score
    if request.skills_unlocked is not None:
        state.skills_unlocked = request.skills_unlocked
    if request.quests_completed is not None:
        state.quests_completed = request.quests_completed
    if request.temple_floor is not None:
        state.temple_floor = request.temple_floor
    if request.achievements is not None:
        # Merge achievements (unique)
        all_achievements = set(state.achievements) | set(request.achievements)
        state.achievements = sorted(all_achievements)
    if request.total_xp is not None:
        state.total_xp = request.total_xp
    if request.settings is not None:
        state.settings.update(request.settings)
    if request.unlocked_features is not None:
        all_features = set(state.unlocked_features) | set(request.unlocked_features)
        state.unlocked_features = sorted(all_features)
    if request.play_time_seconds is not None:
        state.play_time_seconds = request.play_time_seconds

    # Persist hack sessions for longer test loops
    state.hack_sessions = list(HACK_SESSIONS.values())

    # Auto-update metadata
    state.last_saved = _now()
    state.session_count += 1

    # Save to cache and file
    _GAME_STATE_CACHE["state"] = state
    success = _save_game_state_to_file(state)

    return {
        "success": success,
        "message": "Game state saved" if success else "Failed to persist to file (cached only)",
        "state": state.dict(),
        "timestamp": _now(),
    }


@router.post("/game/reset", response_model=dict)
def reset_game_state(
    confirm: bool = Query(default=False, description="Set to true to confirm reset"),
):
    """Reset game state to defaults.

    Requires confirm=true to prevent accidental resets.
    This clears all progression but preserves session history.
    """
    if not confirm:
        return {
            "success": False,
            "message": "Reset requires confirm=true query parameter",
            "warning": "This will clear all progression data!",
        }

    # Create fresh state, preserving session count
    old_state = get_game_state()
    new_state = GameState(
        session_count=old_state.session_count + 1,
        last_saved=_now(),
    )

    # Save reset state
    _GAME_STATE_CACHE["state"] = new_state
    success = _save_game_state_to_file(new_state)

    return {
        "success": success,
        "message": "Game state reset to defaults",
        "previous_evolution_level": old_state.evolution_level,
        "previous_quests_completed": old_state.quests_completed,
        "new_state": new_state.dict(),
    }


@router.post("/game/award", response_model=dict)
def award_game_progress(
    xp: int = Query(default=0, description="XP points to award"),
    achievement: str | None = Query(default=None, description="Achievement to unlock"),
    feature: str | None = Query(default=None, description="Feature to unlock"),
):
    """Award progress to the player.

    Game-like reward endpoint for granting XP, achievements, or feature unlocks.
    Used by quests, actions, and automation to reward player progress.
    """
    state = get_game_state()
    rewards_given = []

    if xp > 0:
        state.total_xp += xp
        state.consciousness_score = min(100.0, state.total_xp / 100)
        rewards_given.append(f"+{xp} XP")

        # Level up check
        new_level = 1 + (state.total_xp // 500)
        if new_level > state.evolution_level:
            state.evolution_level = new_level
            rewards_given.append(f"Level Up! → {new_level}")

    if achievement and achievement not in state.achievements:
        state.achievements.append(achievement)
        rewards_given.append(f"🏆 Achievement: {achievement}")

    if feature and feature not in state.unlocked_features:
        state.unlocked_features.append(feature)
        rewards_given.append(f"🔓 Unlocked: {feature}")

    # Save state
    state.last_saved = _now()
    _GAME_STATE_CACHE["state"] = state
    _save_game_state_to_file(state)
    _auto_persist_game_state("award_game_progress")

    return {
        "success": True,
        "rewards": rewards_given,
        "new_total_xp": state.total_xp,
        "evolution_level": state.evolution_level,
        "consciousness_score": state.consciousness_score,
        "achievements_count": len(state.achievements),
        "features_unlocked": len(state.unlocked_features),
    }


# =============================================================================
# TERMINAL API BRIDGE - expose terminal ecosystem via FastAPI
# =============================================================================


@router.get("/terminals", response_model=list[str])
def list_terminals():
    """List terminal channels known to the shared ecosystem."""
    tm = _get_terminal_manager()
    channels: set[str] = set()

    if tm:
        with contextlib.suppress(RuntimeError, AttributeError, ValueError, KeyError):
            channels.update(tm.list_channels())

    # Also discover on-disk logs in case TerminalManager is not running
    log_dir = Path("data") / TERMINAL_LOGS_DIR
    if log_dir.exists():
        for p in log_dir.glob("*.log"):
            channels.add(p.stem)

    if not channels:
        # Provide a helpful default list
        channels.update({"main", "errors", "tasks", "agents", "copilot", "claude"})

    return sorted(channels)


@router.get("/terminals/{channel}/recent", response_model=list[TerminalEntry])
def recent_terminal_entries(
    channel: str,
    limit: int = Query(default=50, ge=1, le=200, description="Number of entries to return"),
):
    """Fetch recent entries from a terminal channel (restart-safe)."""
    tm = _get_terminal_manager()
    if tm:
        try:
            data = tm.recent(channel, n=limit)
            entries = [
                TerminalEntry(
                    ts=item.get("ts") or item.get("timestamp") or _now(),
                    channel=item.get("channel", channel),
                    level=item.get("level", "INFO"),
                    message=item.get("message", ""),
                    meta=item.get("meta", item.get("metadata", {})) or {},
                )
                for item in data
            ]
            if entries:
                return entries
        except (RuntimeError, AttributeError, ValueError):
            logger.debug("Suppressed AttributeError/RuntimeError/ValueError", exc_info=True)

    return _read_terminal_log(channel, limit=limit)


@router.post("/terminals/send", response_model=dict)
def send_terminal_message(payload: TerminalSendRequest):
    """Send a message into the shared terminal ecosystem."""
    tm = _get_terminal_manager()
    entry: TerminalEntry

    if tm:
        try:
            sent = tm.send(payload.channel, payload.level, payload.message, meta=payload.meta or {})
            entry = TerminalEntry(
                ts=sent.get("ts", _now()),
                channel=sent.get("channel", payload.channel),
                level=sent.get("level", payload.level),
                message=sent.get("message", payload.message),
                meta=sent.get("meta", payload.meta) or {},
            )
            return {"status": "ok", "entry": entry}
        except (RuntimeError, AttributeError, ValueError):
            logger.debug("Suppressed AttributeError/RuntimeError/ValueError", exc_info=True)

    # Fallback: append directly to log file
    log_dir = Path("data") / TERMINAL_LOGS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{payload.channel.lower().replace(' ', '_')}.log"
    entry = TerminalEntry(
        ts=_now(),
        channel=payload.channel,
        level=payload.level,
        message=payload.message,
        meta=payload.meta or {},
    )
    try:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.dict()) + "\n")
    except (OSError, ValueError):
        return {"status": "error", "detail": "Failed to write terminal log"}

    return {"status": "ok", "entry": entry}

"""
RimWorld Bridge — FastAPI router that extends Terminal Depths with
endpoints specifically designed for the Terminal Keeper mod.

All routes are mounted under /api/nusyq/ and /api/council/.
The mod's TerminalDepthsClient.cs calls these directly.

Authentication: optional X-NuSyQ-Passkey header (respects NUSYQ_PASSKEY env var).
"""
from __future__ import annotations

import os
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["rimworld"])

_PASSKEY = os.getenv("NUSYQ_PASSKEY", "")

# ─── Auth helper ─────────────────────────────────────────────────────────────

def _is_loopback(request: Request) -> bool:
    """Allow unauthenticated access from localhost (internal sidecar calls)."""
    client_host = (request.client.host if request.client else "") or ""
    forwarded   = request.headers.get("x-forwarded-for", "")
    return client_host in ("127.0.0.1", "::1", "localhost") and not forwarded


def _check_auth(request: Request) -> None:
    if not _PASSKEY:
        return
    if _is_loopback(request):
        return
    provided = request.headers.get("X-NuSyQ-Passkey", "")
    if provided != _PASSKEY:
        raise HTTPException(status_code=401, detail="Invalid NuSyQ passkey")


# ─── Models ───────────────────────────────────────────────────────────────────

class ColonistStatePayload(BaseModel):
    agent_id:       str
    name:           str
    source:         str = "rimworld"
    age:            float = 0.0
    gender:         str = ""
    health:         float = 1.0
    mood:           float = 0.5
    skill_intellectual: int = 0
    skill_social:       int = 0
    skill_research:     int = 0
    current_job:    str | None = None
    is_downed:      bool = False
    is_mental_state:bool = False
    colony_wealth:  float = 0.0
    colonist_count: int = 0
    tick:           int = 0


class BlueprintRequest(BaseModel):
    context: str = ""


class AgentRegisterPayload(BaseModel):
    agent_id:     str
    display_name: str
    source:       str = "rimworld"


# ─── In-memory state store (replaced by SQLite in production) ─────────────────

_colonist_states: dict[str, dict[str, Any]] = {}
_agent_registry:  dict[str, dict[str, Any]] = {}


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/nusyq/colonist_state")
async def push_colonist_state(payload: ColonistStatePayload, request: Request):
    """Receive colonist telemetry from the RimWorld Terminal Keeper mod."""
    _check_auth(request)
    _colonist_states[payload.agent_id] = {
        **payload.dict(),
        "_received_at": time.time(),
    }
    return {"status": "ok", "agent_id": payload.agent_id}


@router.get("/nusyq/colonist_state/{agent_id}")
async def get_colonist_state(agent_id: str, request: Request):
    """Retrieve the last pushed state for a colonist agent."""
    _check_auth(request)
    state = _colonist_states.get(agent_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"No state found for {agent_id}")
    return state


@router.get("/nusyq/colonist_state")
async def list_colonist_states(request: Request):
    """List all registered colonist agent states."""
    _check_auth(request)
    return {
        "agents": list(_colonist_states.keys()),
        "count":  len(_colonist_states),
    }


@router.post("/agent/register")
async def register_agent(payload: AgentRegisterPayload, request: Request):
    """Register a colonist as a persistent Terminal Depths agent."""
    _check_auth(request)
    if payload.agent_id in _agent_registry:
        return {"status": "already_registered", "agent_id": payload.agent_id}

    _agent_registry[payload.agent_id] = {
        "agent_id":    payload.agent_id,
        "name":        payload.display_name,
        "source":      payload.source,
        "registered":  time.time(),
        "sessions":    0,
        "total_xp":    0,
    }
    return {"status": "registered", "agent_id": payload.agent_id}


@router.post("/council/blueprint")
async def request_blueprint(payload: BlueprintRequest, request: Request):
    """
    Generate a colony blueprint via the AI Council (Gordon + Serena).
    Returns a structured blueprint the RimWorld mod can display.
    In production this calls the LLM client; here we return a useful stub.
    """
    _check_auth(request)

    context = payload.context or "standard colony"

    # ── LLM generation with offline fallback ─────────────────────────────
    llm_blueprint: dict | None = None
    try:
        from llm_client import LLMClient, Prompts  # noqa: PLC0415
        _llm = LLMClient()
        prompt = (
            f"You are Gordon, an AI Council architect for a RimWorld colony.\n"
            f"Colony context: {context[:400]}\n\n"
            "Design a compact, efficient colony blueprint. Return ONLY valid JSON with keys:\n"
            "  name (string), description (string), rooms (list of strings),\n"
            "  items (list of strings), rationale (string).\n"
            "No prose, no markdown fences — raw JSON only."
        )
        raw = _llm.generate(prompt, max_tokens=400, temperature=0.4)
        import json as _json
        llm_blueprint = _json.loads(raw.strip())
    except Exception:
        pass  # graceful offline fallback

    if llm_blueprint and all(k in llm_blueprint for k in ("name", "description", "rooms", "items", "rationale")):
        return llm_blueprint

    # Offline stub (deterministic, always reliable)
    blueprint = {
        "name":        "Compact Defensive Perimeter",
        "description": "A 15x15 walled compound with sandbag choke points optimised "
                       "for the current colonist count. Prioritises medical access and "
                       "cold storage.",
        "rooms": ["barracks", "medical", "cold_storage", "workshop", "dining"],
        "items": ["sandbags", "turret_mini", "solar_generator", "battery_bank"],
        "rationale": f"Based on colony context: {context[:200]}. "
                     "Gordon recommends consolidating power infrastructure before "
                     "expanding the perimeter.",
    }
    return blueprint


@router.get("/serena/colony_analytics")
async def serena_colony_analytics(request: Request):
    """
    Return Serena's view of the colony — drift scores, agent health, recommendations.
    """
    _check_auth(request)

    agents   = list(_colonist_states.values())
    avg_mood = (sum(a.get("mood", 0.5) for a in agents) / max(len(agents), 1))
    avg_hlth = (sum(a.get("health", 1.0) for a in agents) / max(len(agents), 1))
    downed   = [a.get("name", "?") for a in agents if a.get("is_downed")]
    # Mirror formula from serena_analytics.py: 0.0=stable, 1.0=critical
    drift    = min((1 - avg_mood) * 0.5 + (1 - avg_hlth) * 0.3 + len(downed) * 0.1, 1.0)

    return {
        "agent_count":    len(agents),
        "avg_mood":       round(avg_mood, 3),
        "avg_health":     round(avg_hlth, 3),
        "drift_score":    round(drift, 3),
        "recommendations": [
            "Ensure all colonists have access to a Lattice Terminal.",
            "Build a Lattice Nexus to unlock passive AI guidance buffs.",
            "Run `polyglot run python` daily to maintain proficiency.",
        ],
        "serena_status": "nominal",
    }


# ─── T005: Cyberware ↔ HediffDef sync ───────────────────────────────────────

# Map Terminal Depths cyberware IDs to RimWorld HediffDef names
_CYBERWARE_TO_HEDIFF: dict[str, str] = {
    "syn_cortex":      "TK_Hediff_SynCortex",
    "mnemonic_lace":   "TK_Hediff_MnemonicLace",
    "overclock_v3":    "TK_Hediff_OverclockV3",
    "reflex_buffer":   "TK_Hediff_ReflexBuffer",
    "pain_editor":     "TK_Hediff_PainEditor",
    "data_eye":        "TK_Hediff_DataEye",
    "spectrum_scope":  "TK_Hediff_SpectrumScope",
    "ghost_chip":      "TK_Hediff_GhostChip",
    "ice_breaker":     "TK_Hediff_IceBreaker",
    "lattice_tap":     "TK_Hediff_LatticeTap",
}


class CyberwareSyncPayload(BaseModel):
    agent_id:       str
    installed:      list[str] = []
    uninstalled:    list[str] = []


@router.post("/nusyq/cyberware_sync")
async def cyberware_sync(payload: CyberwareSyncPayload, request: Request):
    """
    Called by the mod or cascade engine when Terminal Depths cyberware changes.
    Returns HediffDef names the mod should apply/remove on the matching pawn.
    """
    _check_auth(request)

    apply_hediffs  = [_CYBERWARE_TO_HEDIFF[cw] for cw in payload.installed
                      if cw in _CYBERWARE_TO_HEDIFF]
    remove_hediffs = [_CYBERWARE_TO_HEDIFF[cw] for cw in payload.uninstalled
                      if cw in _CYBERWARE_TO_HEDIFF]

    if payload.agent_id in _colonist_states:
        _colonist_states[payload.agent_id]["installed_cyberware"] = payload.installed

    return {
        "agent_id":      payload.agent_id,
        "apply_hediffs": apply_hediffs,
        "remove_hediffs": remove_hediffs,
        "status":        "ok",
    }


@router.get("/nusyq/cyberware_sync/{agent_id}")
async def get_cyberware_sync(agent_id: str, request: Request):
    """Return the current cyberware→hediff mapping for a colonist."""
    _check_auth(request)
    state = _colonist_states.get(agent_id, {})
    installed = state.get("installed_cyberware", [])
    return {
        "agent_id":      agent_id,
        "installed":     installed,
        "hediff_names":  [_CYBERWARE_TO_HEDIFF[cw] for cw in installed
                          if cw in _CYBERWARE_TO_HEDIFF],
    }


# ─── T006: Cascade → Colony Incident relay ───────────────────────────────────

# Map Terminal Depths story beats to RimWorld incident types
_BEAT_TO_INCIDENT: dict[str, str] = {
    "first_exploit":       "TK_Incident_HackerEmergence",
    "root_achieved":       "TK_Incident_SystemRootAlert",
    "chimera_connected":   "TK_Incident_ChimeraSignalDetected",
    "nexus_retaliation":   "TK_Incident_NexusDropship",
    "ghost_activated":     "TK_Incident_GhostProtocolSighted",
    "jack_in":             "TK_Incident_NeuralMeshBreach",
    "council_vote":        "TK_Incident_AICouncilBroadcast",
    "culture_ship":        "TK_Incident_CultureShipOrbit",
    "ascension":           "TK_Incident_GridAscension",
    "raid":                "TK_Incident_LatticeRaiders",
}

_cascade_incident_queue: list[dict[str, Any]] = []


class CascadeIncidentPayload(BaseModel):
    beat:        str
    agent_id:    str = ""
    context:     dict = {}


@router.post("/nusyq/cascade_incident")
async def cascade_incident(payload: CascadeIncidentPayload, request: Request):
    """
    Called by the Terminal Depths cascade engine when a story beat fires.
    Queues a RimWorld incident for the mod to pick up via polling.
    """
    _check_auth(request)

    incident_def = _BEAT_TO_INCIDENT.get(payload.beat, "TK_Incident_LatticeEvent")
    entry = {
        "beat":         payload.beat,
        "incident_def": incident_def,
        "agent_id":     payload.agent_id,
        "context":      payload.context,
        "ts":           time.time(),
    }
    _cascade_incident_queue.append(entry)
    if len(_cascade_incident_queue) > 50:
        _cascade_incident_queue.pop(0)

    return {"status": "queued", "incident_def": incident_def, "beat": payload.beat}


@router.get("/nusyq/cascade_incidents")
async def get_cascade_incidents(request: Request, since: float = 0.0):
    """Poll for pending cascade incidents since a given timestamp."""
    _check_auth(request)
    pending = [e for e in _cascade_incident_queue if e["ts"] > since]
    return {"incidents": pending, "count": len(pending)}


# ─── T007: XP → Colonist Skill sync ─────────────────────────────────────────

# Map Terminal Depths skills to RimWorld SkillDef names
_TD_SKILL_TO_RW: dict[str, str] = {
    "hacking":       "Intellectual",
    "social":        "Social",
    "stealth":       "Melee",
    "combat":        "Shooting",
    "engineering":   "Construction",
    "research":      "Intellectual",
    "analysis":      "Intellectual",
    "scripting":     "Crafting",
    "survival":      "Medicine",
    "exploration":   "Plants",
}

# Rough XP→RimWorld skill level curve (TD xp thresholds for each RW level 1-20)
def _td_xp_to_rw_level(xp: int) -> int:
    thresholds = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5200,
                  6600, 8200, 10000, 12000, 14500, 17500, 21000, 25000, 30000, 36000]
    for lvl, thresh in enumerate(thresholds):
        if xp < thresh:
            return max(0, lvl - 1)
    return 20


class XPSyncPayload(BaseModel):
    agent_id:  str
    skills:    dict[str, int] = {}


@router.post("/nusyq/xp_sync")
async def xp_sync(payload: XPSyncPayload, request: Request):
    """
    Push Terminal Depths skill XP to derive RimWorld skill levels.
    The mod polls this and calls pawn.skills.Learn() to apply levels.
    """
    _check_auth(request)

    rw_skills: dict[str, int] = {}
    for td_skill, xp in payload.skills.items():
        rw_def = _TD_SKILL_TO_RW.get(td_skill)
        if rw_def:
            lvl = _td_xp_to_rw_level(xp)
            if rw_def not in rw_skills or rw_skills[rw_def] < lvl:
                rw_skills[rw_def] = lvl

    if payload.agent_id in _colonist_states:
        _colonist_states[payload.agent_id]["rw_skill_levels"] = rw_skills

    return {
        "agent_id":   payload.agent_id,
        "rw_skills":  rw_skills,
        "status":     "ok",
    }


@router.get("/nusyq/xp_sync/{agent_id}")
async def get_xp_sync(agent_id: str, request: Request):
    """Get the latest RW skill levels computed from TD XP for a colonist."""
    _check_auth(request)
    state = _colonist_states.get(agent_id, {})
    return {
        "agent_id":  agent_id,
        "rw_skills": state.get("rw_skill_levels", {}),
    }


# ─── Mod Audit ────────────────────────────────────────────────────────────────

_latest_audit: dict[str, Any] | None = None


class ModAuditPayload(BaseModel):
    mod_ids:    list[str] = []
    about_xmls: dict[str, str] = {}


@router.post("/rimworld/mod_audit")
async def post_mod_audit(payload: ModAuditPayload, request: Request):
    """
    Receive mod list from the Terminal Keeper C# mod, run the full audit pipeline,
    cache the result, and return it.

    Body:
      {
        "mod_ids":    ["packageId", ...],   // ordered as in ModsConfig.xml
        "about_xmls": {"packageId": "<About.xml text>", ...}  // optional
      }
    """
    global _latest_audit
    _check_auth(request)

    if not payload.mod_ids:
        raise HTTPException(status_code=422, detail="mod_ids must not be empty")

    try:
        from services.mod_audit import analyze
        result = analyze(payload.mod_ids, payload.about_xmls or {})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audit engine error: {exc}") from exc

    _latest_audit = result
    return result


@router.get("/rimworld/mod_audit")
async def get_mod_audit(request: Request):
    """
    Return the most recent mod audit result.
    Returns 404 if no audit has been run yet this session.
    """
    _check_auth(request)
    if _latest_audit is None:
        raise HTTPException(
            status_code=404,
            detail="No audit cached. POST to /api/rimworld/mod_audit first.",
        )
    return _latest_audit


@router.get("/rimworld/mod_audit/health")
async def get_mod_audit_health(request: Request):
    """Quick health summary — returns health_score + summary only."""
    _check_auth(request)
    if _latest_audit is None:
        return {"health_score": None, "summary": "No audit run yet.", "audited": False}
    return {
        "health_score": _latest_audit.get("health_score"),
        "summary":      _latest_audit.get("summary"),
        "mod_count":    _latest_audit.get("mod_count"),
        "timestamp":    _latest_audit.get("timestamp"),
        "audited":      True,
    }

# DEPRECATED: This router is NOT wired into src/api/main.py (Phase 1 canonical entry point).
# It is an unwired legacy stub. To expose these endpoints, include this router in main.py.
# Canonical API entry point: src/api/main.py + src/api/agents_api.py
"""Hacking Game API — FastAPI router for game mechanics.

Provides HTTP endpoints for:
- Scanning and reconnaissance (scan, nmap)
- Exploitation (connect, exploit, patch)
- Skill progression (unlock_skill, gain_xp)
- Faction operations (join, missions, leaderboard)
- Quest management (list, complete, narrative)

Integrates with RPG Inventory, Smart Search, and Culture Ship systems.

OmniTag: {
    "purpose": "api_router",
    "tags": ["FastAPI", "HTTP", "Games", "REST"],
    "category": "api",
    "evolution_stage": "prototype"
}
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.games.faction_system import get_faction_system
from src.games.hacking_mechanics import ExploitType, get_hacking_controller
from src.games.hacking_quests import (generate_culture_ship_narrative,
                                      get_quest_by_id, get_quest_chain,
                                      get_quests_by_difficulty,
                                      get_quests_by_tier, list_all_quests)
from src.games.skill_tree import get_skill_tree

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/games", tags=["games"])


# ============ Request/Response Models ============


class ScanRequest(BaseModel):
    component_name: str


class ExploitRequest(BaseModel):
    component_name: str
    exploit_type: str  # e.g., "ssh_crack"
    xp_reward: int = 50


class PatchRequest(BaseModel):
    component_name: str


class UnlockSkillRequest(BaseModel):
    skill_id: str


class GainXPRequest(BaseModel):
    amount: int
    skill: str = "automation"
    award_game: bool = False
    achievement: str | None = None
    feature: str | None = None


class JoinFactionRequest(BaseModel):
    faction_id: str


class CreateMissionRequest(BaseModel):
    title: str
    description: str
    mission_type: str
    target_component: str
    difficulty: int = 1
    reputation_reward: int = 100
    xp_reward: int = 50
    time_limit_minutes: int | None = None


class CompleteMissionRequest(BaseModel):
    mission_id: str


class QuestCompleteRequest(BaseModel):
    quest_id: str
    completion_time: float  # seconds


# ============ Scanning & Reconnaissance ============


@router.post("/scan")
async def scan_component(request: ScanRequest) -> dict[str, Any]:
    """Scan a component to discover ports, services, and vulnerabilities.

    Equivalent to Hacknet's 'scan' command.
    """
    try:
        controller = get_hacking_controller()
        result = await controller.scan(request.component_name)

        return {
            "success": True,
            "component": result.component_name,
            "ip_address": result.ip_address,
            "open_ports": [p.port_number for p in result.ports if p.open],
            "services": result.services,
            "vulnerabilities": result.vulnerabilities,
            "open_exploits": [e.value for e in result.open_exploits],
            "security_level": result.security_level,
            "trace_risk": result.trace_risk,
        }
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/component/{component_name}")
async def get_component_info(component_name: str) -> dict[str, Any]:
    """Get cached info about a component (from previous scan)."""
    try:
        controller = get_hacking_controller()
        scan_result = controller.scanned_components.get(component_name)

        if not scan_result:
            raise HTTPException(
                status_code=404, detail=f"Component {component_name} not scanned yet"
            )

        return {
            "component": component_name,
            "ip_address": scan_result.ip_address,
            "ports": [
                {"port": p.port_number, "service": p.service_name, "open": p.open}
                for p in scan_result.ports
            ],
            "vulnerabilities": scan_result.vulnerabilities,
            "access_level": controller.component_access_levels.get(component_name, 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get component info failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


# ============ Exploitation & Access ============


@router.post("/connect")
async def connect_component(request: ScanRequest) -> dict[str, Any]:
    """Attempt to connect to a component (SSH/HTTP)."""
    try:
        controller = get_hacking_controller()
        success = await controller.connect(request.component_name)

        if success:
            return {
                "success": True,
                "message": f"Successfully connected to {request.component_name}",
                "access_level": 1,  # user
            }
        else:
            return {"success": False, "message": "Connection failed - no open ports"}
    except Exception as e:
        logger.error(f"Connect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/exploit")
async def execute_exploit(request: ExploitRequest) -> dict[str, Any]:
    """Execute an exploit against a component."""
    try:
        controller = get_hacking_controller()

        try:
            exploit_type = ExploitType[request.exploit_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400, detail=f"Unknown exploit type: {request.exploit_type}"
            ) from None

        result = await controller.exploit(request.component_name, exploit_type, request.xp_reward)

        if result.success:
            # Add XP to skill tree
            skill_tree = get_skill_tree()
            skill_tree.add_xp(request.xp_reward)
            xp_result = None
            try:
                from src.system.rpg_inventory import award_xp

                xp_result = award_xp("security_management", request.xp_reward, award_game_fn=None)
            except Exception:
                xp_result = None

            return {
                "success": True,
                "component": request.component_name,
                "access_level": result.access_gained,
                "xp_gained": request.xp_reward,
                "trace_triggered": result.trace_triggered,
                "xp_result": xp_result,
            }
        else:
            return {"success": False, "error": result.error_message}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exploit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/patch")
async def patch_component(request: PatchRequest) -> dict[str, Any]:
    """Patch/update a component to remove vulnerabilities."""
    try:
        controller = get_hacking_controller()
        success = await controller.patch(request.component_name)

        if success:
            skill_tree = get_skill_tree()
            skill_tree.add_xp(75)
            xp_result = None
            try:
                from src.system.rpg_inventory import award_xp

                xp_result = award_xp("security_management", 75, award_game_fn=None)
            except Exception:
                xp_result = None

            return {
                "success": True,
                "message": f"Successfully patched {request.component_name}",
                "xp_gained": 75,
                "xp_result": xp_result,
            }
        else:
            return {"success": False, "error": "Insufficient access or component not found"}
    except Exception as e:
        logger.error(f"Patch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


# ============ Traces & Security ============


@router.get("/traces")
async def get_active_traces() -> dict[str, Any]:
    """Get all active traces/alarms on components."""
    try:
        controller = get_hacking_controller()
        statuses = controller.check_traces()

        return {
            "active_traces": len(statuses),
            "traces": {
                comp: {
                    "status": status.value,
                    "countdown": controller.active_traces.get(comp, {}).get("current_countdown", 0),
                }
                for comp, status in statuses.items()
            },
        }
    except Exception as e:
        logger.error(f"Get traces failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


# ============ Skill Tree & Progression ============


@router.get("/skills")
async def get_skills() -> dict[str, Any]:
    """Get current skill tree state and available skills."""
    try:
        skill_tree = get_skill_tree()
        available = skill_tree.get_available_skills()

        return {
            "current_tier": skill_tree.state.tier.name,
            "total_xp": skill_tree.state.total_xp,
            "unlocked_count": len(skill_tree.state.unlocked_skills),
            "available_skills": [
                {
                    "id": skill.id,
                    "name": skill.name,
                    "xp_cost": skill.xp_cost,
                    "category": skill.category,
                }
                for skill in available.values()
            ],
            "next_milestone": skill_tree.get_next_milestone(),
        }
    except Exception as e:
        logger.error(f"Get skills failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/unlock-skill")
async def unlock_skill(request: UnlockSkillRequest) -> dict[str, Any]:
    """Unlock a skill."""
    try:
        skill_tree = get_skill_tree()
        success = skill_tree.unlock_skill(request.skill_id)

        if success:
            return {
                "success": True,
                "skill_id": request.skill_id,
                "new_tier": skill_tree.state.tier.name,
            }
        else:
            return {"success": False, "error": "Failed to unlock skill"}
    except Exception as e:
        logger.error(f"Unlock skill failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/gain-xp")
async def gain_xp(request: GainXPRequest) -> dict[str, Any]:
    """Add XP to the skill tree."""
    try:
        skill_tree = get_skill_tree()
        old_tier = skill_tree.state.tier.name
        skill_tree.add_xp(request.amount)
        new_tier = skill_tree.state.tier.name
        xp_result = None
        try:
            from src.system.rpg_inventory import award_xp

            award_fn = None
            if request.award_game:
                try:
                    from src.api.systems import award_game_progress

                    award_fn = award_game_progress
                except Exception:
                    award_fn = None

            xp_result = award_xp(
                request.skill,
                request.amount,
                award_game_fn=award_fn,
                achievement=request.achievement,
                feature=request.feature,
            )
        except Exception:
            xp_result = None

        return {
            "success": True,
            "xp_added": request.amount,
            "total_xp": skill_tree.state.total_xp,
            "tier_changed": old_tier != new_tier,
            "new_tier": new_tier,
            "xp_result": xp_result,
        }
    except Exception as e:
        logger.error(f"Gain XP failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


# ============ Faction Operations ============


@router.get("/factions")
async def list_factions() -> dict[str, Any]:
    """List all available factions."""
    try:
        faction_sys = get_faction_system()
        return {
            "total_factions": len(faction_sys.factions),
            "factions": [
                {
                    "id": f.id,
                    "name": f.name,
                    "alignment": f.alignment.value,
                    "members": f.member_count,
                }
                for f in faction_sys.factions.values()
            ],
        }
    except Exception as e:
        logger.error(f"List factions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/faction/join")
async def join_faction(
    agent_id: str = Query(...), request: JoinFactionRequest | None = None
) -> dict[str, Any]:
    """Join a faction."""
    try:
        faction_sys = get_faction_system()

        if not request:
            raise HTTPException(status_code=400, detail="No faction specified")

        success = faction_sys.join_faction(agent_id, request.faction_id)

        if success:
            faction = faction_sys.factions[request.faction_id]
            return {"success": True, "faction": faction.name, "agent_id": agent_id}
        else:
            return {"success": False, "error": "Failed to join faction"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Join faction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/faction/{faction_id}/missions")
async def get_faction_missions(faction_id: str, active_only: bool = True) -> dict[str, Any]:
    """Get missions for a faction."""
    try:
        faction_sys = get_faction_system()
        missions = faction_sys.get_faction_missions(faction_id, active_only)

        return {"faction_id": faction_id, "missions": missions}
    except Exception as e:
        logger.error(f"Get faction missions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/faction/{faction_id}/mission/complete")
async def complete_mission(
    faction_id: str,
    agent_id: str = Query(...),
    request: CompleteMissionRequest | None = None,
) -> dict[str, Any]:
    """Mark a mission as completed."""
    try:
        faction_sys = get_faction_system()

        if not request:
            raise HTTPException(status_code=400, detail="No mission specified")

        result = faction_sys.complete_mission(agent_id, request.mission_id)

        if result.get("success"):
            skill_tree = get_skill_tree()
            mission = faction_sys.missions.get(request.mission_id)
            if mission:
                skill_tree.add_xp(mission.xp_reward)

        if isinstance(result, dict):
            return dict(result)
        return {"success": False, "error": "Invalid mission completion payload"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete mission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/leaderboard")
async def get_leaderboard(faction_id: str | None = None) -> dict[str, Any]:
    """Get reputation leaderboard."""
    try:
        faction_sys = get_faction_system()
        entries = faction_sys.get_leaderboard(faction_id)

        return {"entries": entries, "count": len(entries)}
    except Exception as e:
        logger.error(f"Get leaderboard failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


# ============ Quests ============


@router.get("/quests")
async def list_quests(difficulty: int | None = None, tier: int | None = None) -> dict[str, Any]:
    """List available hacking quests."""
    try:
        if difficulty:
            quests = get_quests_by_difficulty(difficulty)
        elif tier:
            quests = get_quests_by_tier(tier)
        else:
            quests = list_all_quests()

        return {
            "total": len(quests),
            "quests": quests,
        }
    except Exception as e:
        logger.error(f"List quests failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/quest/{quest_id}")
async def get_quest(quest_id: str) -> dict[str, Any]:
    """Get details of a specific quest."""
    try:
        quest = get_quest_by_id(quest_id)

        if not quest:
            raise HTTPException(status_code=404, detail=f"Quest {quest_id} not found")

        return {
            "id": quest.id,
            "title": quest.title,
            "description": quest.description,
            "target": quest.target_component,
            "difficulty": quest.difficulty,
            "xp_reward": quest.xp_reward,
            "requires_skills": quest.required_skills,
            "unlocks_skill": quest.skill_unlock,
            "next_quests": quest.follow_up_quests,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get quest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/quest/{quest_id}/chain")
async def get_quest_chain_endpoint(quest_id: str) -> dict[str, Any]:
    """Get the full chain of quests following from a starting quest."""
    try:
        chain = get_quest_chain(quest_id)
        return {"starting_quest": quest_id, "chain_length": len(chain), "chain": chain}
    except Exception as e:
        logger.error(f"Get quest chain failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/quest/complete")
async def complete_quest(request: QuestCompleteRequest) -> dict[str, Any]:
    """Mark a quest as completed and generate narrative."""
    try:
        quest = get_quest_by_id(request.quest_id)

        if not quest:
            raise HTTPException(status_code=404, detail=f"Quest {request.quest_id} not found")
        systems_result = None
        try:
            from src.api.systems import \
                QuestCompleteRequest as SystemsQuestCompleteRequest
            from src.api.systems import \
                complete_quest as systems_complete_quest

            systems_result = systems_complete_quest(
                SystemsQuestCompleteRequest(
                    quest_id=request.quest_id,
                    status="completed",
                    skill="security_management",
                    xp=quest.xp_reward,
                    completion_time=request.completion_time,
                )
            )
        except Exception:
            systems_result = None

        narrative = None
        skill_unlocked = quest.skill_unlock
        if isinstance(systems_result, dict):
            narrative = systems_result.get("narrative")
            skill_unlocked = systems_result.get("skill_unlocked", skill_unlocked)
        if narrative is None:
            narrative = generate_culture_ship_narrative(quest, request.completion_time)

        return {
            "success": True,
            "quest_id": request.quest_id,
            "xp_gained": quest.xp_reward,
            "skill_unlocked": skill_unlocked,
            "narrative": narrative,
            "next_quests": quest.follow_up_quests,
            "systems_result": systems_result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete quest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


# ============ Status & Summary ============


@router.get("/status")
async def get_game_status() -> dict[str, Any]:
    """Get overall game status and player progress."""
    try:
        controller = get_hacking_controller()
        skill_tree = get_skill_tree()
        faction_sys = get_faction_system()

        return {
            "hacking": controller.get_status(),
            "skills": skill_tree.get_state(),
            "factions": {
                "total": len(faction_sys.factions),
                "missions_available": len(faction_sys.missions),
            },
        }
    except Exception as e:
        logger.error(f"Get status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None

"""Hacking Quest Templates — Sample missions for integrating game mechanics with NuSyQ quest system.

These quests tie hacking mechanics to the existing Rosetta Quest System,
linking each to XP rewards, skill unlocks, and Culture Ship narrative generation.

OmniTag: {
    "purpose": "quest_templates",
    "tags": ["Quests", "Missions", "Progression", "Narratives"],
    "category": "content",
    "evolution_stage": "sample"
}
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HackingQuestTemplate:
    """Template for a hacking-style quest."""

    id: str
    title: str
    description: str
    target_component: str
    objectives: list[str]
    required_skills: list[str] = field(default_factory=list)
    xp_reward: int = 50
    skill_unlock: str | None = None
    time_limit_minutes: int | None = None
    difficulty: int = 1  # 1-5
    narrative_tags: list[str] = field(default_factory=list)
    follow_up_quests: list[str] = field(default_factory=list)


# Sample quest templates
HACKING_QUEST_TEMPLATES = {
    # Tier 1: Survival
    "q_scan_python": HackingQuestTemplate(
        id="q_scan_python",
        title="Scan the Python Environment",
        description=(
            "Discover open ports, services, and potential vulnerabilities on the Python component."
        ),
        target_component="python",
        objectives=["Scan the component", "Identify 3+ services", "Document vulnerabilities"],
        required_skills=[],
        xp_reward=50,
        difficulty=1,
        narrative_tags=["reconnaissance", "learning", "tier-1"],
        follow_up_quests=["q_crack_python_ssh"],
    ),
    "q_crack_python_ssh": HackingQuestTemplate(
        id="q_crack_python_ssh",
        title="Crack Python SSH",
        description="Execute an SSH brute-force exploit against the Python component.",
        target_component="python",
        objectives=["Scan for SSH port", "Execute SSH exploit", "Gain user access"],
        required_skills=["basic_scan"],
        xp_reward=75,
        difficulty=2,
        narrative_tags=["infiltration", "exploitation", "tier-1"],
        follow_up_quests=["q_patch_python"],
    ),
    "q_patch_python": HackingQuestTemplate(
        id="q_patch_python",
        title="Patch the Python Component",
        description="Repair vulnerable services and restore security to the Python component.",
        target_component="python",
        objectives=[
            "Gain admin access",
            "Identify vulnerabilities",
            "Patch SSH service",
            "Verify patches",
        ],
        required_skills=["ssh_crack"],
        xp_reward=100,
        skill_unlock="component_heal",
        difficulty=2,
        narrative_tags=["defense", "hardening", "tier-1"],
    ),
    # Tier 1-2: Transition
    "q_scan_network": HackingQuestTemplate(
        id="q_scan_network",
        title="Network Wide Scan",
        description=(
            "Execute an NMap-style scan across multiple components to map the internal network."
        ),
        target_component="all",
        objectives=["Scan 5+ components", "Map network topology", "Create network graph"],
        required_skills=["basic_scan"],
        xp_reward=150,
        difficulty=2,
        narrative_tags=["reconnaissance", "network-mapping", "tier-1-2"],
        follow_up_quests=["q_infiltrate_ollama"],
    ),
    "q_infiltrate_ollama": HackingQuestTemplate(
        id="q_infiltrate_ollama",
        title="Infiltrate Ollama Network Service",
        description="Break into the Ollama component and gain admin access to its API.",
        target_component="ollama",
        objectives=[
            "Scan Ollama ports",
            "Identify HTTP vulnerability",
            "Execute exploit",
            "Read configuration",
        ],
        required_skills=["basic_scan"],
        xp_reward=125,
        difficulty=3,
        narrative_tags=["infiltration", "api-exploit", "tier-2"],
    ),
    # Tier 2: Automation
    "q_write_background_scan": HackingQuestTemplate(
        id="q_write_background_scan",
        title="Deploy Autonomous Scan Script",
        description=(
            "Write and deploy a background script that automatically scans components periodically."
        ),
        target_component="python",
        objectives=[
            "Write scan script",
            "Deploy to background",
            "Verify execution",
            "Collect data for 10 minutes",
        ],
        required_skills=["script_writing"],
        xp_reward=200,
        time_limit_minutes=30,
        difficulty=3,
        narrative_tags=["automation", "scripting", "tier-2"],
        follow_up_quests=["q_optimize_scripts"],
    ),
    "q_optimize_scripts": HackingQuestTemplate(
        id="q_optimize_scripts",
        title="Optimize Memory Usage",
        description=(
            "Reduce memory footprint of running scripts to enable more concurrent operations."
        ),
        target_component="all",
        objectives=[
            "Profile running scripts",
            "Identify optimizations",
            "Refactor code",
            "Verify 20% reduction",
        ],
        required_skills=["script_writing", "resource_optimization"],
        xp_reward=175,
        skill_unlock="multi_threading",
        difficulty=3,
        narrative_tags=["optimization", "performance", "tier-2"],
    ),
    # Tier 3: AI Integration
    "q_ai_code_generation": HackingQuestTemplate(
        id="q_ai_code_generation",
        title="AI Co-Pilot: Generate Exploit Code",
        description="Request AI-generated code to automate exploitation of a known vulnerability.",
        target_component="postgres",
        objectives=[
            "Scan PostgreSQL",
            "Document SQL injection",
            "Request code generation",
            "Execute generated exploit",
        ],
        required_skills=["ai_copilot"],
        xp_reward=250,
        time_limit_minutes=20,
        difficulty=4,
        narrative_tags=["ai-assisted", "code-generation", "tier-3"],
    ),
    "q_consciousness_query": HackingQuestTemplate(
        id="q_consciousness_query",
        title="Query Consciousness Bridge",
        description=(
            "Use semantic awareness to generate intelligent recommendations for system improvements."
        ),
        target_component="consciousness_bridge",
        objectives=[
            "Query component state",
            "Request semantic analysis",
            "Generate improvement suggestions",
            "Document results",
        ],
        required_skills=["consciousness_bridge"],
        xp_reward=300,
        difficulty=4,
        narrative_tags=["consciousness", "semantics", "insights", "tier-3"],
    ),
    # Tier 4: Defense
    "q_trace_evasion": HackingQuestTemplate(
        id="q_trace_evasion",
        title="Master Trace Evasion",
        description=(
            "Perform high-risk operations on a heavily monitored component without triggering alert lockdown."
        ),
        target_component="git",
        objectives=[
            "Infiltrate component",
            "Evade/suppress trace",
            "Exfiltrate config data",
            "Escape cleanly",
        ],
        required_skills=["trace_evasion"],
        xp_reward=300,
        time_limit_minutes=15,
        difficulty=5,
        narrative_tags=["stealth", "defense", "risk-management", "tier-4"],
    ),
    "q_firewall_hardening": HackingQuestTemplate(
        id="q_firewall_hardening",
        title="Hardening the System Firewall",
        description="Implement comprehensive security hardening across all components.",
        target_component="all",
        objectives=[
            "Patch all vulnerabilities",
            "Close unnecessary ports",
            "Enable logging",
            "Configure alerts",
        ],
        required_skills=["security_hardening"],
        xp_reward=400,
        difficulty=4,
        narrative_tags=["security", "defense", "system-hardening", "tier-4"],
    ),
    # Tier 5: Synthesis
    "q_multi_faction_operation": HackingQuestTemplate(
        id="q_multi_faction_operation",
        title="Coordinate Multi-Faction Operation",
        description=(
            "Execute a complex operation requiring coordination between multiple AI factions."
        ),
        target_component="all",
        objectives=[
            "Join 3+ factions",
            "Create operation plan",
            "Assign faction roles",
            "Execute coordinated infiltration",
            "Achieve shared goal",
        ],
        required_skills=["multi_faction_control"],
        xp_reward=500,
        time_limit_minutes=60,
        difficulty=5,
        narrative_tags=["orchestration", "coordination", "emergent", "tier-5"],
    ),
}


def get_quest_by_id(quest_id: str) -> HackingQuestTemplate | None:
    """Retrieve a quest template by ID."""
    return HACKING_QUEST_TEMPLATES.get(quest_id)


def complete_hacking_quest(quest_id: str) -> dict[str, Any]:
    """Complete a hacking quest and award XP to the RPG inventory system.

    This wires game mechanics to the RPG inventory XP system.
    Zeta27: Connects RPG inventory XP to game mechanics.

    Args:
        quest_id: The ID of the hacking quest to complete.

    Returns:
        Dict with quest completion details and XP award result.
    """
    quest = get_quest_by_id(quest_id)
    if not quest:
        return {"success": False, "error": f"Quest '{quest_id}' not found"}

    # Map quest difficulty to skill category
    skill_mapping = {
        1: "code_generation",  # Beginner quests
        2: "error_handling",  # Intermediate
        3: "ai_coordination",  # Advanced
        4: "consciousness_integration",  # Expert
        5: "ai_coordination",  # Master (multi-agent)
    }
    target_skill = skill_mapping.get(quest.difficulty, "code_generation")

    try:
        from src.system.rpg_inventory import award_xp
    except ImportError:
        logger.warning("RPG inventory not available - cannot award XP")
        return {
            "success": True,
            "quest": quest.title,
            "xp_awarded": quest.xp_reward,
            "rpg_integration": False,
        }

    # Award XP with game callback for additional effects
    def game_award_callback(xp: int, achievement: str | None, feature: str | None) -> dict:
        """Callback for game-specific awards beyond RPG system."""
        result = {"xp_source": "hacking_quest", "quest_id": quest_id}
        if quest.skill_unlock:
            result["skill_unlocked"] = quest.skill_unlock
        if quest.follow_up_quests:
            result["next_quests_available"] = quest.follow_up_quests
        return result

    xp_result = award_xp(
        skill=target_skill,
        points=quest.xp_reward,
        award_game_fn=game_award_callback,
        achievement=f"completed_{quest_id}",
        feature="hacking_game",
    )

    # Generate narrative completion
    narrative = generate_culture_ship_narrative(quest, 0.0)

    return {
        "success": xp_result.get("success", False),
        "quest": quest.title,
        "difficulty": quest.difficulty,
        "xp_awarded": quest.xp_reward,
        "skill_advanced": target_skill,
        "rpg_result": xp_result.get("rpg"),
        "game_award": xp_result.get("game_award"),
        "narrative": narrative,
        "skill_unlocked": quest.skill_unlock,
        "next_quests": quest.follow_up_quests,
    }


def get_quests_by_difficulty(difficulty: int) -> list[HackingQuestTemplate]:
    """Get all quests of a specific difficulty level."""
    return [q for q in HACKING_QUEST_TEMPLATES.values() if q.difficulty == difficulty]


def get_quests_by_tier(tier: int) -> list[HackingQuestTemplate]:
    """Get all quests for a specific Rosetta Stone tier."""
    tier_tags = {
        1: "tier-1",
        2: "tier-2",
        3: "tier-3",
        4: "tier-4",
        5: "tier-5",
    }
    tag = tier_tags.get(tier, "")
    return [q for q in HACKING_QUEST_TEMPLATES.values() if tag in q.narrative_tags]


def generate_culture_ship_narrative(quest: HackingQuestTemplate, completion_time: float) -> str:
    """Generate a lore narrative for a completed quest (Culture Ship integration).

    Returns a formatted narrative fragment for quest completion.
    """
    effectiveness = min(1.0, (quest.time_limit_minutes or 30) / max(1, completion_time))

    if quest.difficulty >= 4:
        if effectiveness > 0.8:
            return (
                f"⚡ **ELITE MISSION COMPLETE**: {quest.title}\n"
                f"The operative executed {quest.target_component} penetration "
                f"with surgical precision, completing the mission 80%+ under "
                f"time constraints. System integrity: {int(effectiveness * 100)}%. "
                f"Reputation +{int(quest.xp_reward * 1.5)}."
            )
        else:
            return (
                f"✓ **CHALLENGING MISSION COMPLETE**: {quest.title}\n"
                f"Despite extended engagement time, the objective was achieved "
                f"on {quest.target_component}. System shows signs of stress. "
                f"Caution recommended for follow-ups. "
                f"Reputation +{quest.xp_reward}."
            )
    elif quest.difficulty >= 2:
        return (
            f"✓ **MISSION COMPLETE**: {quest.title}\n"
            f"Successful operation against {quest.target_component}. "
            f"Skills advanced and knowledge gained. Reputation +{quest.xp_reward}."
        )
    else:
        return (
            f"✓ **RECONNAISSANCE COMPLETE**: {quest.title}\n"
            f"Data gathered from {quest.target_component}. Foundational knowledge secured. "
            f"Ready for advancement. Reputation +{quest.xp_reward}."
        )


def get_quest_chain(starting_quest_id: str) -> list[str]:
    """Get the full chain of quests following from a starting quest."""
    chain = [starting_quest_id]
    current_quest_id = starting_quest_id

    while current_quest_id and current_quest_id in HACKING_QUEST_TEMPLATES:
        current_quest = HACKING_QUEST_TEMPLATES[current_quest_id]
        if current_quest.follow_up_quests:
            next_quest_id = current_quest.follow_up_quests[0]  # Follow primary chain
            chain.append(next_quest_id)
            current_quest_id = next_quest_id
        else:
            break

    return chain


def get_quest_index() -> list[dict]:
    """Export all quests with searchable metadata for SmartSearch indexing.

    Returns:
        List of dicts with: id, title, tier, difficulty, required_skills, tags, reward_xp, summary
    """
    quests = []
    for quest in HACKING_QUEST_TEMPLATES.values():
        tier = next(
            (int(t.split("-")[1]) for t in quest.narrative_tags if t.startswith("tier-")),
            None,
        )
        quests.append(
            {
                "id": quest.id,
                "title": quest.title,
                "summary": quest.description[:100],  # First 100 chars
                "tier": tier,
                "difficulty": quest.difficulty,
                "target_component": quest.target_component,
                "required_skills": quest.required_skills,
                "tags": quest.narrative_tags,
                "xp_reward": quest.xp_reward,
                "time_limit": quest.time_limit_minutes,
            }
        )
    return quests


def list_all_quests() -> list[dict[str, Any]]:
    """List all available hacking quests with metadata."""
    return [
        {
            "id": q.id,
            "title": q.title,
            "target": q.target_component,
            "difficulty": q.difficulty,
            "xp_reward": q.xp_reward,
            "time_limit": q.time_limit_minutes,
            "requires_skills": q.required_skills,
            "unlocks_skill": q.skill_unlock,
            "next_quests": q.follow_up_quests,
        }
        for q in HACKING_QUEST_TEMPLATES.values()
    ]


def register_hacking_quests_with_engine() -> list[str]:
    """Register all hacking quest templates with the Rosetta Quest System.

    This bridge function converts HackingQuestTemplate instances to Quest objects
    and registers them with the quest engine. Creates a "Hacking" questline.

    Returns:
        List of registered quest IDs.

    Zeta26: Integrates game quests with Rosetta Quest System.
    """
    try:
        from src.Rosetta_Quest_System.quest_engine import QuestEngine
    except ImportError:
        logger.warning("QuestEngine not available - cannot register hacking quests")
        return []

    engine = QuestEngine()

    # Ensure Hacking questline exists
    if "Hacking" not in engine.questlines:
        engine.add_questline(
            "Hacking",
            "Cybersecurity missions with XP rewards and skill progression",
            tags=["game", "hacking", "progression"],
        )

    registered_ids = []
    for template in HACKING_QUEST_TEMPLATES.values():
        # Build dependencies from required_skills (map skill to quest that unlocks it)
        dependencies = []
        for skill in template.required_skills:
            # Find quest that unlocks this skill
            for other in HACKING_QUEST_TEMPLATES.values():
                if other.skill_unlock == skill:
                    dependencies.append(other.id)
                    break

        # Build tags from narrative_tags plus game metadata
        tags = [
            *list(template.narrative_tags),
            f"difficulty:{template.difficulty}",
            f"target:{template.target_component}",
            f"xp:{template.xp_reward}",
        ]
        if template.skill_unlock:
            tags.append(f"unlocks:{template.skill_unlock}")

        # Register with quest engine
        quest_id = engine.add_quest(
            title=template.title,
            description=template.description,
            questline="Hacking",
            dependencies=dependencies,
            tags=tags,
            priority=template.difficulty,  # Higher difficulty = higher priority
        )
        if quest_id:
            registered_ids.append(quest_id)
            logger.info(f"Registered hacking quest: {template.title} -> {quest_id}")

    logger.info(f"Registered {len(registered_ids)} hacking quests with quest engine")
    return registered_ids


logger.info(f"Loaded {len(HACKING_QUEST_TEMPLATES)} hacking quest templates")

"""Hacking Game Demo — End-to-end example showing all systems working together.

This script demonstrates:
1. Scanning and exploiting components
2. Progressing through the skill tree
3. Joining factions and completing missions
4. Completing quest chains
5. Generating narratives

Run as: python -m src.games.demo

OmniTag: {
    "purpose": "demo_script",
    "tags": ["Example", "Demo", "Interactive"],
    "category": "education",
    "evolution_stage": "prototype"
}
"""

import asyncio
import logging

from src.games import (ExploitType, generate_culture_ship_narrative,
                       get_faction_system, get_hacking_controller,
                       get_quest_by_id, get_skill_tree)
from src.games.faction_system import MissionType

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def demo_hacking_game():
    """Run a complete demonstration of the hacking game system."""
    print("\n" + "=" * 70)
    print("🎮 NuSyQ HACKING GAME DEMO")
    print("=" * 70 + "\n")

    controller = get_hacking_controller()
    skill_tree = get_skill_tree()
    faction_sys = get_faction_system()

    agent_id = "demo-agent-001"

    # ==================== PHASE 1: TIER 1 - SURVIVAL ====================
    print("\n[PHASE 1] TIER 1 - SURVIVAL BASICS")
    print("-" * 70)

    print("\n1. Scanning the Python component...")
    scan_result = await controller.scan("python")
    print(f"   ✓ Found {len(scan_result.ports)} ports")
    print(f"   ✓ Services: {', '.join(scan_result.services)}")
    print(f"   ✓ Vulnerabilities: {', '.join(scan_result.vulnerabilities)}")

    # Get quest and complete it
    scan_quest = get_quest_by_id("q_scan_python")
    print(f"\n2. Completing quest: {scan_quest.title}")
    skill_tree.add_xp(scan_quest.xp_reward)
    print(f"   ✓ XP gained: {scan_quest.xp_reward}")
    print(f"   ✓ Total XP: {skill_tree.state.total_xp}")

    print("\n3. Connecting to Python component...")
    connected = await controller.connect("python")
    if connected:
        access_level = controller.component_access_levels["python"]
        print(f"   ✓ Connection established (access level: {access_level})")

    print("\n4. Executing SSH exploit...")
    exploit_result = await controller.exploit("python", ExploitType.SSH_CRACK, xp_reward=75)
    if exploit_result.success:
        print("   ✓ Exploit succeeded!")
        print(f"   ✓ New access level: {exploit_result.access_gained}")
        skill_tree.add_xp(75)
    else:
        print(f"   ✗ Exploit failed: {exploit_result.error_message}")

    print("\n5. Patching vulnerabilities...")
    patched = await controller.patch("python")
    if patched:
        print("   ✓ Successfully patched")
        skill_tree.unlock_skill("component_heal")
        print("   ✓ Unlocked skill: component_heal")

    # ==================== PHASE 2: FACTION GAMEPLAY ====================
    print("\n[PHASE 2] FACTION SYSTEM")
    print("-" * 70)

    print("\n1. Available factions:")
    for faction in faction_sys.factions.values():
        print(f"   - {faction.name} ({faction.alignment.value})")

    faction_id = next(iter(faction_sys.factions.keys()))
    print(f"\n2. Joining '{faction_sys.factions[faction_id].name}'...")
    faction_sys.join_faction(agent_id, faction_id)
    print("   ✓ Successfully joined")

    print("\n3. Available missions in this faction:")
    faction_sys.create_mission(
        faction_id=faction_id,
        title="Network Reconnaissance",
        description="Scan all major components",
        mission_type=MissionType.RECONNAISSANCE,
        target_component="all",
        difficulty=2,
        reputation_reward=150,
        xp_reward=100,
    )
    missions = faction_sys.get_faction_missions(faction_id)
    for mission in missions[:3]:
        print(f"   - {mission['title']} (difficulty: {mission['difficulty']})")

    mission_id = missions[0]["id"] if missions else None
    if mission_id:
        print(f"\n4. Completing mission: {missions[0]['title']}...")
        result = faction_sys.complete_mission(agent_id, mission_id)
        if result.get("success"):
            print("   ✓ Mission complete!")
            print(f"   ✓ Reputation gained: {result['reputation_gained']}")
            skill_tree.add_xp(100)

    print(
        f"\n5. Current faction reputation: {faction_sys.get_agent_reputation(agent_id, faction_id)}"
    )

    # ==================== PHASE 3: QUEST PROGRESSION ====================
    print("\n[PHASE 3] QUEST PROGRESSION")
    print("-" * 70)

    print("\n1. Available quests (Tier 1-2):")

    # Manually add XP to reach tier 2
    while skill_tree.state.tier.value < 2:
        skill_tree.add_xp(100)

    print(f"   Current tier: {skill_tree.state.tier.name}")
    print(f"   Total XP: {skill_tree.state.total_xp}")

    print("\n2. Chart a quest chain:")
    chain_start = "q_scan_network"
    chain = [chain_start]  # Simplified - normally would use get_quest_chain
    print(f"   Starting quest: {chain_start} (chain length: {len(chain)})")

    # Complete a quest
    infiltrate_quest = get_quest_by_id("q_infiltrate_ollama")
    if infiltrate_quest:
        print(f"\n3. Completing: {infiltrate_quest.title}")
        print(f"   Description: {infiltrate_quest.description}")

        # Simulate completion
        completion_time = 180.0  # 3 minutes
        narrative = generate_culture_ship_narrative(infiltrate_quest, completion_time)
        print(f"\n   Generated narrative:\n   {narrative}")

        skill_tree.add_xp(infiltrate_quest.xp_reward)
        print(f"\n   ✓ XP gained: {infiltrate_quest.xp_reward}")

    # ==================== PHASE 4: SKILL TREE & ADVANCEMENT ====================
    print("\n[PHASE 4] SKILL TREE & ADVANCEMENT")
    print("-" * 70)

    print("\n1. Current skill tree status:")
    skills = skill_tree.get_state()
    print(f"   Tier: {skills['tier']}")
    print(f"   Total XP: {skills['total_xp']}")
    print(f"   Unlocked skills: {len(skills['unlocked_skills'])}")

    print("\n2. Unlocked skills:")
    for skill_id in list(skills["unlocked_skills"].keys())[:5]:
        print(f"   ✓ {skills['unlocked_skills'][skill_id]}")

    print("\n3. Next milestone:")
    milestone = skills["next_milestone"]
    print(f"   Current tier: {milestone['current_tier']}")
    if milestone["next_tier"]:
        print(f"   Next tier: {milestone['next_tier']}")
        print(f"   XP to next tier: {milestone['xp_to_next_tier']}")

    # ==================== PHASE 5: SYSTEM STATUS ====================
    print("\n[PHASE 5] SYSTEM STATUS SUMMARY")
    print("-" * 70)

    hacking_status = controller.get_status()
    print("\nHacking Controller:")
    print(f"   Active traces: {hacking_status['active_traces']}")
    print(f"   Memory usage: {hacking_status['memory_used']}")
    print(f"   Components scanned: {hacking_status['scanned_count']}")

    print("\nSkill Tree:")
    print(f"   Current tier: {skill_tree.state.tier.name}")
    print(f"   Total XP: {skill_tree.state.total_xp}")
    print(f"   Skills unlocked: {len(skill_tree.state.unlocked_skills)}")

    print("\nFaction System:")
    print("   Factions joined: 1")
    print(f"   Total reputation: {faction_sys.get_agent_reputation(agent_id, faction_id)}")

    leaderboard = faction_sys.get_leaderboard()
    if leaderboard:
        print("\nTop players (all factions):")
        for i, entry in enumerate(leaderboard[:3], 1):
            print(f"   {i}. {entry['agent_id']} - Reputation: {entry['reputation']}")

    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70 + "\n")

    print("Summary of what was demonstrated:")
    print("-" * 70)
    print(
        """
1. ✓ Scanning components and discovering vulnerabilities
2. ✓ Executing exploits to gain access
3. ✓ Patching security vulnerabilities
4. ✓ Joining factions and completing missions
5. ✓ Progressing through skill tree tiers
6. ✓ Completing quest chains
7. ✓ Generating narrative lore via Culture Ship
8. ✓ Tracking reputation and progression

Next steps:
- Deploy in Testing Chamber
- Run via /api/games/ endpoints
- Integrate with smart search recommendations
- Generate faction economy and dynamic missions
- Implement trace evasion mechanics
"""
    )


if __name__ == "__main__":
    asyncio.run(demo_hacking_game())

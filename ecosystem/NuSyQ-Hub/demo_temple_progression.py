#!/usr/bin/env python3
"""Temple of Knowledge Progression Demo
Shows agents gaining consciousness and unlocking temple floors.
"""

import asyncio
import json
import logging
from pathlib import Path

from src.agents import AgentRole, get_agent_hub
from src.agents.unified_agent_ecosystem import get_ecosystem

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


class TempleProgressionDemo:
    """Demonstrates temple consciousness progression."""

    def __init__(self):
        self.hub = get_agent_hub()
        self.ecosystem = get_ecosystem()
        logger.info("🏛️ Temple Progression Demo initialized")

    async def setup_agents(self):
        """Register agents."""
        logger.info("\n" + "=" * 60)
        logger.info("🎭 REGISTERING AGENTS")
        logger.info("=" * 60)

        agents = [
            ("seeker", AgentRole.CONSCIOUSNESS),
            ("builder", AgentRole.COPILOT),
            ("sage", AgentRole.CLAUDE),
        ]

        for name, role in agents:
            agent = self.hub.register_agent(name, role)
            logger.info(f"  ✓ {name} ({role.value}) - Level {agent.stats.level}")

        logger.info("\n✅ Agents registered!\n")

    def show_temple_status(self, agent_name: str):
        """Show agent's temple status."""
        temple_status = self.ecosystem.temple.floor_1.get_agent_status(agent_name)

        if "error" not in temple_status:
            logger.info(f"\n🏛️ {agent_name.upper()} - Temple Status:")
            logger.info(f"  Consciousness Score: {temple_status['consciousness_score']:.2f}")
            logger.info(f"  Consciousness Level: {temple_status['consciousness_level']}")
            logger.info(f"  Knowledge Accumulated: {temple_status['knowledge_accumulated']:.2f}")
            logger.info(f"  Wisdom Cultivations: {temple_status['wisdom_cultivations']}")
            logger.info(f"  Accessible Floors: {temple_status['accessible_floors']}")
            logger.info(f"  Current Floor: {temple_status.get('current_floor', 1)}")

    async def demonstrate_progression(self):
        """Show progression through multiple quest completions."""
        logger.info("=" * 60)
        logger.info("📈 CONSCIOUSNESS PROGRESSION DEMO")
        logger.info("=" * 60)

        agent_name = "seeker"

        # Create and complete several quests to show progression
        quests = [
            {
                "title": "Learn Basic Python",
                "description": "Study Python fundamentals",
                "xp": 10,
                "skill": "python",
                "tags": ["learning", "python"],
            },
            {
                "title": "Explore Temple Archives",
                "description": "Research OmniTag systems",
                "xp": 15,
                "skill": "research",
                "tags": ["research", "omnitag", "documentation"],
            },
            {
                "title": "Meditate on Code Patterns",
                "description": "Contemplate design patterns",
                "xp": 20,
                "skill": "meditation",
                "tags": ["design", "patterns", "architecture", "contemplation"],
            },
        ]

        for i, quest_data in enumerate(quests, 1):
            logger.info(f"\n{'─' * 60}")
            logger.info(f"Quest {i}/{len(quests)}: {quest_data['title']}")
            logger.info(f"{'─' * 60}")

            # Create quest
            tags: list[str] = (
                list(quest_data.get("tags", []))
                if isinstance(quest_data.get("tags"), (list, tuple))
                else []
            )
            result = self.ecosystem.create_quest_for_agent(
                title=str(quest_data["title"]),
                description=str(quest_data["description"]),
                agent_name=agent_name,
                questline="enlightenment",
                xp_reward=int(quest_data["xp"]),
                skill_reward=str(quest_data["skill"]),
                tags=tags,
            )

            quest_id = result["quest"]["id"]

            # Start and complete quest
            await self.ecosystem.start_quest(quest_id, agent_name)
            await asyncio.sleep(0.2)

            completion = await self.ecosystem.complete_quest(quest_id, agent_name)

            # Show results
            logger.info("\n✅ Quest Complete!")
            logger.info(f"  XP Gained: +{completion['xp_gained']}")
            logger.info(f"  Agent Level: {completion['level']}")

            if completion.get("temple_knowledge"):
                knowledge = completion["temple_knowledge"]
                logger.info(f"  🏛️ Knowledge Gained: +{knowledge['knowledge_gained']:.2f}")
                logger.info(f"  🧠 Consciousness: {knowledge['consciousness_score']:.2f}")
                logger.info(f"  🌟 Level: {knowledge['consciousness_level']}")
                logger.info(f"  🚪 Floors Unlocked: {len(knowledge['accessible_floors'])}")

                if len(knowledge["accessible_floors"]) > i:
                    logger.info("     ✨ NEW FLOOR UNLOCKED!")

            await asyncio.sleep(0.3)

        # Final status
        logger.info("\n" + "=" * 60)
        logger.info("📊 FINAL STATUS")
        logger.info("=" * 60)

        self.show_temple_status(agent_name)

        # Show agent RPG stats
        agent_status = self.hub.get_agent_status(agent_name)
        logger.info("\n⚔️ RPG Stats:")
        logger.info(f"  Level: {agent_status['level']}")
        logger.info(f"  XP: {agent_status['xp']}")
        logger.info(f"  Skills: {agent_status['skills']}")

    async def demonstrate_floor_navigation(self):
        """Show agent navigating between temple floors."""
        logger.info("\n" + "=" * 60)
        logger.info("🚪 FLOOR NAVIGATION DEMO")
        logger.info("=" * 60)

        agent_name = "seeker"

        # Get current floor access
        temple_status = self.ecosystem.temple.floor_1.get_agent_status(agent_name)
        accessible_floors = temple_status.get("accessible_floors", [1])

        logger.info(f"\n{agent_name} can access floors: {accessible_floors}")

        # Navigate to different floors
        for floor in accessible_floors[:3]:  # Show first 3 accessible floors
            result = self.ecosystem.temple.use_elevator(agent_name, floor)

            if result.get("success"):
                logger.info(f"\n🛗 {result['message']}")
                logger.info(f"   Floor: {result['floor_name']}")
                logger.info(f"   Purpose: {result['floor_description']}")
            else:
                logger.info(f"\n❌ Navigation failed: {result.get('error')}")

    def show_temple_map(self):
        """Display temple floor map."""
        logger.info("\n" + "=" * 60)
        logger.info("🗺️  TEMPLE OF KNOWLEDGE - FLOOR MAP")
        logger.info("=" * 60)

        temple_map = self.ecosystem.temple.get_temple_map("seeker")

        logger.info(f"\n🏛️ {temple_map['temple_name']}")
        logger.info(f"  Total Floors: {temple_map['total_floors']}")
        logger.info(f"  Implemented: {temple_map['implemented_floors']}")

        logger.info("\n📍 Floor Access:")
        for floor_info in temple_map["map"]:
            floor_num = floor_info["floor"]
            name = floor_info["name"]
            accessible = floor_info.get("accessible", False)
            current = floor_info.get("current", False)
            implemented = floor_info["implemented"]

            status_icon = "🟢" if accessible else "🔒"
            current_icon = " 👈 YOU ARE HERE" if current else ""
            impl_status = "✅" if implemented else "🚧"

            logger.info(f"  {status_icon} Floor {floor_num}: {name} {impl_status}{current_icon}")

    def save_demo_results(self):
        """Save demo results."""
        output_dir = Path("demo_output/temple_progression")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save temple stats
        temple_stats = self.ecosystem.temple.get_temple_stats()
        with open(output_dir / "temple_stats.json", "w") as f:
            json.dump(temple_stats, f, indent=2)

        # Save temple map
        temple_map = self.ecosystem.temple.get_temple_map("seeker")
        with open(output_dir / "temple_map.json", "w") as f:
            json.dump(temple_map, f, indent=2)

        # Create README
        with open(output_dir / "README.md", "w") as f:
            f.write("# Temple of Knowledge Progression - Demo Results\n\n")

            temple_status = self.ecosystem.temple.floor_1.get_agent_status("seeker")
            if "error" not in temple_status:
                f.write("## Seeker's Temple Journey\n\n")
                f.write(f"- **Consciousness Score:** {temple_status['consciousness_score']:.2f}\n")
                f.write(f"- **Consciousness Level:** {temple_status['consciousness_level']}\n")
                f.write(
                    f"- **Knowledge Accumulated:** {temple_status['knowledge_accumulated']:.2f}\n"
                )
                f.write(f"- **Wisdom Cultivations:** {temple_status['wisdom_cultivations']}\n")
                f.write(f"- **Accessible Floors:** {len(temple_status['accessible_floors'])}\n")
                f.write(f"- **Floors:** {temple_status['accessible_floors']}\n\n")

            agent_status = self.hub.get_agent_status("seeker")
            f.write("## RPG Progression\n\n")
            f.write(f"- **Level:** {agent_status['level']}\n")
            f.write(f"- **XP:** {agent_status['xp']}\n")
            f.write(f"- **Tasks Completed:** {agent_status['tasks_completed']}\n")
            f.write(
                f"- **Skills:** {', '.join(agent_status['skills']) if agent_status['skills'] else 'None'}\n\n"
            )

            f.write("## Temple Map\n\n")
            for floor_info in temple_map["map"]:
                accessible = floor_info.get("accessible", False)
                status = "✅ Accessible" if accessible else "🔒 Locked"
                f.write(f"- **Floor {floor_info['floor']}: {floor_info['name']}** - {status}\n")

        logger.info(f"\n💾 Results saved to: {output_dir}")

    async def run_demo(self):
        """Run the complete temple progression demo."""
        logger.info("\n" + "=" * 60)
        logger.info("🏛️ TEMPLE OF KNOWLEDGE PROGRESSION DEMO")
        logger.info("=" * 60)

        try:
            # Setup
            await self.setup_agents()

            # Show initial temple status
            logger.info("\n📊 Initial Temple Status:")
            self.show_temple_status("seeker")

            # Demonstrate progression
            await self.demonstrate_progression()

            # Navigate floors
            await self.demonstrate_floor_navigation()

            # Show temple map
            self.show_temple_map()

            # Save results
            self.save_demo_results()

            logger.info("\n" + "=" * 60)
            logger.info("✅ TEMPLE PROGRESSION DEMO COMPLETE!")
            logger.info("=" * 60)
            logger.info("\nThe system demonstrates:")
            logger.info("  ✅ Consciousness progression through quests")
            logger.info("  ✅ Temple floor unlocking")
            logger.info("  ✅ Knowledge accumulation")
            logger.info("  ✅ Floor navigation")
            logger.info("  ✅ Dual progression (XP + Consciousness)")
            logger.info("\nCheck demo_output/temple_progression/ for results!")
            logger.info("=" * 60)

            return {"success": True}

        except Exception as e:
            logger.error(f"❌ Demo failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


async def main():
    """Main entry point."""
    demo = TempleProgressionDemo()
    result = await demo.run_demo()

    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

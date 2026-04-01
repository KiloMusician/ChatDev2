#!/usr/bin/env python3
"""Unified Agent Ecosystem Demo
Shows the complete integrated system with quests, agents, and progression.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, TypedDict

from src.agents import AgentRole, get_agent_hub
from src.agents.unified_agent_ecosystem import get_ecosystem

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class QuestSeed(TypedDict):
    title: str
    description: str
    agent: str
    questline: str
    xp: int
    skill: str
    tags: list[str]


class UnifiedEcosystemDemo:
    """Demonstrates the full integrated ecosystem."""

    def __init__(self):
        self.ecosystem = get_ecosystem()
        self.hub = get_agent_hub()
        logger.info("🌐 Unified Ecosystem Demo initialized")

    async def setup_agents(self):
        """Register all agents."""
        logger.info("\n" + "=" * 60)
        logger.info("⚔️  ASSEMBLING AGENT PARTY")
        logger.info("=" * 60)

        agents = [
            ("copilot", AgentRole.COPILOT),
            ("claude", AgentRole.CLAUDE),
            ("ollama", AgentRole.OLLAMA),
            ("chatdev", AgentRole.CHATDEV),
            ("culture_ship", AgentRole.CULTURE_SHIP),
        ]

        for name, role in agents:
            agent = self.hub.register_agent(name, role)
            logger.info(f"  ✓ {name} ({role.value}) - Level {agent.stats.level}")

        logger.info("\n✅ Party assembled!\n")

    async def create_sample_quests(self):
        """Create sample quests for the demo."""
        logger.info("=" * 60)
        logger.info("📜 CREATING QUEST SYSTEM")
        logger.info("=" * 60)

        quests: list[QuestSeed] = [
            {
                "title": "Fix Import Errors",
                "description": "Resolve all import-related errors in the codebase",
                "agent": "copilot",
                "questline": "code_quality",
                "xp": 20,
                "skill": "syntax",
                "tags": ["imports", "syntax", "cleanup"],
            },
            {
                "title": "Generate API Documentation",
                "description": "Create comprehensive API documentation using AI",
                "agent": "claude",
                "questline": "documentation",
                "xp": 30,
                "skill": "documentation",
                "tags": ["docs", "api", "architecture"],
            },
            {
                "title": "Implement User Authentication",
                "description": "Generate secure authentication system with JWT",
                "agent": "ollama",
                "questline": "features",
                "xp": 50,
                "skill": "code_generation",
                "tags": ["security", "authentication", "backend"],
            },
            {
                "title": "Create Test Suite",
                "description": "Develop comprehensive unit and integration tests",
                "agent": "chatdev",
                "questline": "testing",
                "xp": 40,
                "skill": "testing",
                "tags": ["testing", "quality", "automation"],
            },
            {
                "title": "Optimize Database Queries",
                "description": "Analyze and optimize all database query patterns",
                "agent": "culture_ship",
                "questline": "performance",
                "xp": 60,
                "skill": "optimization",
                "tags": ["performance", "database", "optimization"],
            },
        ]

        created_quests: list[dict[str, Any]] = []
        for quest_data in quests:
            result = self.ecosystem.create_quest_for_agent(
                title=quest_data["title"],
                description=quest_data["description"],
                agent_name=quest_data["agent"],
                questline=quest_data["questline"],
                xp_reward=quest_data["xp"],
                skill_reward=quest_data["skill"],
                tags=quest_data["tags"],
            )

            if result["success"]:
                created_quests.append(result)
                logger.info(f"  📋 Created: {quest_data['title']} → {quest_data['agent']}")

        logger.info(f"\n✅ Created {len(created_quests)} quests!\n")
        return created_quests

    async def execute_quest_workflow(self, quest_id: str, agent_name: str):
        """Execute complete quest workflow: start → work → complete."""
        # Start quest
        logger.info(f"\n🎯 {agent_name} starting quest...")
        await self.ecosystem.start_quest(quest_id, agent_name)

        # Simulate work (in real system, this would be actual task execution)
        await asyncio.sleep(0.5)

        # Complete quest
        logger.info(f"🔨 {agent_name} working on quest...")
        result = await self.ecosystem.complete_quest(quest_id, agent_name)

        if result["success"]:
            logger.info(f"✅ Quest complete! +{result['xp_gained']} XP")

            if result["leveled_up"]:
                logger.info(f"   🎉 LEVEL UP! {agent_name} is now Level {result['level']}!")
            else:
                logger.info(f"   Level {result['level']} | {result['agent_status']['xp']} XP")

        return result

    async def demo_quest_progression(self, created_quests):
        """Demo agents completing quests and leveling up."""
        logger.info("=" * 60)
        logger.info("🗺️  QUEST PROGRESSION")
        logger.info("=" * 60)

        for quest_result in created_quests[:3]:  # First 3 quests
            quest = quest_result["quest"]
            agent = quest_result["agent"]

            await self.execute_quest_workflow(quest["id"], agent)
            await asyncio.sleep(0.3)

    def show_quest_board(self):
        """Display quest board showing all agent assignments."""
        logger.info("\n" + "=" * 60)
        logger.info("📋 QUEST BOARD")
        logger.info("=" * 60)

        summary = self.ecosystem.get_party_quest_summary()

        logger.info(f"\nTotal Quests: {summary['total_quests']}")
        logger.info(f"  Pending: {summary['quests_by_status']['pending']}")
        logger.info(f"  Active: {summary['quests_by_status']['active']}")
        logger.info(f"  Complete: {summary['quests_by_status']['complete']}")

        logger.info("\n📊 Agent Quest Status:")
        logger.info("-" * 60)

        for agent_name, agent_summary in summary["agents"].items():
            if agent_summary["total"] == 0:
                continue

            logger.info(f"\n{agent_name.upper()}")
            logger.info(f"  Total: {agent_summary['total']}")
            logger.info(f"  Pending: {agent_summary['pending']}")
            logger.info(f"  Active: {agent_summary['active']}")
            logger.info(f"  Complete: {agent_summary['complete']}")

            # Show quests
            for quest in agent_summary["quests"][:3]:  # First 3
                status_icon = {
                    "pending": "⏳",
                    "active": "🔥",
                    "complete": "✅",
                    "blocked": "🚫",
                    "archived": "📦",
                }.get(quest["status"], "❓")

                logger.info(
                    f"    {status_icon} {quest['title']} (+{quest['assignment']['xp_reward']} XP)"
                )

    def show_party_status(self):
        """Display party-wide statistics."""
        logger.info("\n" + "=" * 60)
        logger.info("👥 PARTY STATUS")
        logger.info("=" * 60)

        party = self.hub.get_party_status()

        logger.info(f"\nActive Agents: {party['active_agents']}/{party['total_agents']}")
        logger.info(f"Combined Level: {party['total_level']}")
        logger.info(f"Total XP: {party['total_xp']}")
        logger.info(f"Tasks Completed: {party['total_tasks']}")

        logger.info("\n📊 Individual Stats:")
        logger.info("-" * 60)

        for agent_name, status in party["agents"].items():
            if not status.get("active"):
                continue

            logger.info(f"\n{agent_name.upper()} ({status['role']})")
            logger.info(
                f"  Level: {status['level']} | XP: {status['xp']}/{status['xp'] + status['xp_to_next_level']}"
            )
            logger.info(f"  Current Task: {status['current_task'] or 'None'}")

            if status["skills"]:
                logger.info(f"  Skills: {', '.join(status['skills'])}")

    async def demo_quest_suggestions(self):
        """Demo quest suggestion system."""
        logger.info("\n" + "=" * 60)
        logger.info("💡 QUEST SUGGESTIONS")
        logger.info("=" * 60)

        for agent_name in ["copilot", "claude", "ollama"]:
            suggestion = self.ecosystem.suggest_next_quest(agent_name)

            if suggestion:
                quest = suggestion["quest"]
                logger.info(f"\n{agent_name.upper()}: Suggested quest")
                logger.info(f"  📜 {quest['title']}")
                logger.info(
                    f"  ⭐ {suggestion['suggested_xp']} XP | Skill: {suggestion['suggested_skill']}"
                )
            else:
                logger.info(f"\n{agent_name.upper()}: No available quests")

    def save_ecosystem_state(self):
        """Save complete ecosystem state."""
        output_dir = Path("demo_output/unified_ecosystem")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save quest summary
        quest_summary = self.ecosystem.get_party_quest_summary()
        with open(output_dir / "quest_summary.json", "w") as f:
            json.dump(quest_summary, f, indent=2)

        # Save party status
        party_status = self.hub.get_party_status()
        with open(output_dir / "party_status.json", "w") as f:
            json.dump(party_status, f, indent=2)

        # Create README
        with open(output_dir / "README.md", "w") as f:
            f.write("# Unified Agent Ecosystem - Session Report\n\n")
            f.write(f"**Generated:** {party_status.get('timestamp', 'N/A')}\n\n")

            f.write("## Quest Summary\n\n")
            f.write(f"- **Total Quests:** {quest_summary['total_quests']}\n")
            f.write(f"- **Complete:** {quest_summary['quests_by_status']['complete']}\n")
            f.write(f"- **Active:** {quest_summary['quests_by_status']['active']}\n")
            f.write(f"- **Pending:** {quest_summary['quests_by_status']['pending']}\n\n")

            f.write("## Party Status\n\n")
            f.write(f"- **Active Agents:** {party_status['active_agents']}\n")
            f.write(f"- **Combined Level:** {party_status['total_level']}\n")
            f.write(f"- **Total XP:** {party_status['total_xp']}\n")
            f.write(f"- **Tasks Completed:** {party_status['total_tasks']}\n\n")

            f.write("## Agent Details\n\n")
            for agent_name, status in party_status["agents"].items():
                if not status.get("active"):
                    continue

                f.write(f"### {agent_name.upper()}\n\n")
                f.write(f"- **Level:** {status['level']}\n")
                f.write(f"- **XP:** {status['xp']}\n")
                f.write(f"- **Tasks:** {status['tasks_completed']}\n")
                f.write(f"- **Current Task:** {status['current_task'] or 'None'}\n")

                if status["skills"]:
                    f.write(f"- **Skills:** {', '.join(status['skills'])}\n")

                f.write("\n")

        logger.info(f"\n💾 State saved to: {output_dir}")

    async def run_demo(self):
        """Run the complete demo."""
        logger.info("\n" + "=" * 60)
        logger.info("🌐 UNIFIED AGENT ECOSYSTEM DEMO")
        logger.info("=" * 60)

        try:
            # Setup
            await self.setup_agents()

            # Create quests
            created_quests = await self.create_sample_quests()

            # Execute quests
            await self.demo_quest_progression(created_quests)

            # Show results
            self.show_quest_board()
            self.show_party_status()

            # Suggestions
            await self.demo_quest_suggestions()

            # Save state
            self.save_ecosystem_state()

            logger.info("\n" + "=" * 60)
            logger.info("✅ DEMO COMPLETE!")
            logger.info("=" * 60)
            logger.info("\nThe system now has:")
            logger.info("  ✅ Agents with levels and skills")
            logger.info("  ✅ Quest system with assignments")
            logger.info("  ✅ Progression tracking")
            logger.info("  ✅ Persistent state")
            logger.info("\nCheck demo_output/unified_ecosystem/ for reports!")
            logger.info("\n" + "=" * 60)

            return {"success": True}

        except Exception as e:
            logger.error(f"❌ Demo failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


async def main():
    """Main entry point."""
    demo = UnifiedEcosystemDemo()
    result = await demo.run_demo()

    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

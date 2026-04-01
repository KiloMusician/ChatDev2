#!/usr/bin/env python3
"""Agent RPG System Demo
Shows AI agents communicating, collaborating, and leveling up.
"""

import asyncio
import json
import logging
from pathlib import Path

from src.agents import (
    AgentRole,
    Message,
    MessageType,
    get_agent_hub,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AgentRPGDemo:
    """Demonstrates the agent RPG system."""

    def __init__(self):
        self.hub = get_agent_hub()
        logger.info("🏰 Agent RPG System initialized")

    async def setup_agents(self):
        """Register all agents in the system."""
        logger.info("\n" + "=" * 60)
        logger.info("⚔️  INITIALIZING AGENT PARTY")
        logger.info("=" * 60)

        agents = [
            ("copilot", AgentRole.COPILOT),
            ("claude", AgentRole.CLAUDE),
            ("ollama", AgentRole.OLLAMA),
            ("chatdev", AgentRole.CHATDEV),
            ("culture_ship", AgentRole.CULTURE_SHIP),
            ("consciousness", AgentRole.CONSCIOUSNESS),
            ("quantum", AgentRole.QUANTUM),
        ]

        for name, role in agents:
            agent = self.hub.register_agent(name, role)
            logger.info(f"  ✓ {name} ({role.value}) - Level {agent.stats.level}")

        logger.info("\n✅ Party assembled!\n")

    async def demo_collaboration(self):
        """Demo: Agents collaborate on a task."""
        logger.info("=" * 60)
        logger.info("🤝 DEMO: AGENT COLLABORATION")
        logger.info("=" * 60)

        # Claude requests help from Ollama
        logger.info("\n📢 Claude: 'I need help generating a Python function...'")

        await self.hub.send_message(
            from_agent="claude",
            message=Message(
                id="collab_1",
                from_agent="claude",
                to_agent="ollama",
                message_type=MessageType.REQUEST,
                content={
                    "request": "Generate a Python function for quicksort",
                    "urgency": "medium",
                },
            ),
        )

        # Ollama responds
        logger.info("📨 Ollama: 'On it! Generating code...'")

        await self.hub.send_message(
            from_agent="ollama",
            message=Message(
                id="collab_1_response",
                from_agent="ollama",
                to_agent="claude",
                message_type=MessageType.RESPONSE,
                content={"code": "def quicksort(arr): ...", "status": "complete"},
                thread_id="collab_1",
            ),
        )

        # Both agents gain XP from collaboration
        self.hub.complete_task("claude", "Requested code generation", xp=5, skill="collaboration")
        result = self.hub.complete_task(
            "ollama", "Generated quicksort function", xp=15, skill="code_generation"
        )

        logger.info(f"\n⭐ Ollama gained {result['xp_gained']} XP! (Total: {result['total_xp']})")
        logger.info(
            f"   Level: {result['level']} | Tasks: {self.hub.agents['ollama'].stats.tasks_completed}"
        )

    async def demo_quest_system(self):
        """Demo: Agents complete quests and level up."""
        logger.info("\n" + "=" * 60)
        logger.info("🗺️  DEMO: QUEST COMPLETION")
        logger.info("=" * 60)

        quests = [
            ("copilot", "Fix 10 syntax errors", 20, "syntax"),
            ("chatdev", "Generate project structure", 30, "architecture"),
            ("culture_ship", "Solve optimization problem", 40, "problem_solving"),
            ("consciousness", "Learn from 5 errors", 25, "learning"),
            ("quantum", "Resolve complex issue", 50, "quantum_resolution"),
        ]

        for agent_name, quest, xp, skill in quests:
            logger.info(f"\n📜 Quest: {agent_name} is working on '{quest}'...")

            result = self.hub.complete_task(agent_name, quest, xp=xp, skill=skill)

            if result["leveled_up"]:
                logger.info(f"   🎉 {result['level_up_message']}")
            else:
                logger.info(f"   ✓ Quest complete! +{xp} XP (Level {result['level']})")

            # Check if skill should be unlocked
            agent = self.hub.agents[agent_name]
            skill_xp = agent.stats.specialization_xp.get(skill, 0)

            if skill_xp >= 50 and f"{skill}_master" not in agent.stats.skills_unlocked:
                self.hub.unlock_skill(agent_name, f"{skill}_master")
                logger.info(f"   ⭐ New skill unlocked: {skill}_master!")

    async def demo_broadcast(self):
        """Demo: Agent broadcasts achievement to all."""
        logger.info("\n" + "=" * 60)
        logger.info("📡 DEMO: BROADCAST MESSAGE")
        logger.info("=" * 60)

        logger.info("\n🎮 Culture Ship completed a major milestone!")

        await self.hub.send_message(
            from_agent="culture_ship",
            message=Message(
                id="broadcast_1",
                from_agent="culture_ship",
                to_agent=None,  # Broadcast to all
                message_type=MessageType.BROADCAST,
                content={
                    "announcement": "I've solved the repository health optimization problem!",
                    "solution": "Applied quantum-assisted refactoring patterns",
                    "impact": "91% error reduction achieved",
                },
            ),
        )

        logger.info("   📨 All agents notified of the achievement!")

        # Award massive XP for major milestone
        result = self.hub.complete_task(
            "culture_ship",
            "Major milestone: Repository optimization",
            xp=100,
            skill="problem_solving",
        )

        if result["leveled_up"]:
            logger.info(f"   🎉 {result['level_up_message']}")

    def show_party_status(self):
        """Display complete party status."""
        logger.info("\n" + "=" * 60)
        logger.info("👥 PARTY STATUS")
        logger.info("=" * 60)

        party = self.hub.get_party_status()

        logger.info(f"\nTotal Agents: {party['active_agents']}/{party['total_agents']}")
        logger.info(f"Combined Level: {party['total_level']}")
        logger.info(f"Total XP: {party['total_xp']}")
        logger.info(f"Tasks Completed: {party['total_tasks']}")

        logger.info("\n📊 Individual Stats:")
        logger.info("-" * 60)

        for agent_name, status in party["agents"].items():
            logger.info(f"\n{agent_name.upper()} ({status['role']})")
            logger.info(
                f"  Level: {status['level']} | XP: {status['xp']} (Next: {status['xp_to_next_level']})"
            )
            logger.info(
                f"  Tasks: {status['tasks_completed']} | Collaborations: {status['collaborations']}"
            )

            if status["skills"]:
                logger.info(f"  Skills: {', '.join(status['skills'])}")

            if status["reputation"]:
                top_rep = sorted(status["reputation"].items(), key=lambda x: x[1], reverse=True)[:3]
                logger.info(
                    f"  Top Allies: {', '.join(f'{name} ({rep})' for name, rep in top_rep)}"
                )

    def save_progress(self):
        """Save current progress to file."""
        output_dir = Path("demo_output/agent_rpg")
        output_dir.mkdir(parents=True, exist_ok=True)

        party_status = self.hub.get_party_status()

        # Save JSON
        status_file = output_dir / "party_status.json"
        with open(status_file, "w") as f:
            json.dump(party_status, f, indent=2)

        logger.info(f"\n💾 Progress saved to: {status_file}")

        # Create summary
        summary_file = output_dir / "README.md"
        with open(summary_file, "w") as f:
            f.write("# Agent RPG System - Party Status\n\n")
            f.write(f"**Last Updated:** {party_status.get('timestamp', 'N/A')}\n\n")
            f.write("## Party Overview\n\n")
            f.write(
                f"- **Total Agents:** {party_status['active_agents']}/{party_status['total_agents']}\n"
            )
            f.write(f"- **Combined Level:** {party_status['total_level']}\n")
            f.write(f"- **Total XP:** {party_status['total_xp']}\n")
            f.write(f"- **Tasks Completed:** {party_status['total_tasks']}\n\n")

            f.write("## Agent Details\n\n")
            for agent_name, status in party_status["agents"].items():
                f.write(f"### {agent_name.upper()} ({status['role']})\n\n")
                f.write(f"- **Level:** {status['level']}\n")
                f.write(f"- **XP:** {status['xp']} ({status['xp_to_next_level']} to next level)\n")
                f.write(f"- **Tasks Completed:** {status['tasks_completed']}\n")
                f.write(f"- **Collaborations:** {status['collaborations']}\n")

                if status["skills"]:
                    f.write(f"- **Skills:** {', '.join(status['skills'])}\n")

                f.write("\n")

        logger.info(f"📝 Summary saved to: {summary_file}")

    async def run_demo(self):
        """Run the complete demo."""
        logger.info("\n" + "=" * 60)
        logger.info("🎮 AGENT RPG SYSTEM DEMO")
        logger.info("=" * 60)

        try:
            # Setup
            await self.setup_agents()

            # Demos
            await self.demo_collaboration()
            await asyncio.sleep(0.5)

            await self.demo_quest_system()
            await asyncio.sleep(0.5)

            await self.demo_broadcast()
            await asyncio.sleep(0.5)

            # Show results
            self.show_party_status()

            # Save
            self.save_progress()

            logger.info("\n" + "=" * 60)
            logger.info("✅ DEMO COMPLETE!")
            logger.info("=" * 60)
            logger.info("\nCheck demo_output/agent_rpg/ for saved progress!")
            logger.info("Run this again to see agents continue leveling up!")
            logger.info("\n" + "=" * 60)

            return {"success": True}

        except Exception as e:
            logger.error(f"❌ Demo failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


async def main():
    """Main entry point."""
    demo = AgentRPGDemo()
    result = await demo.run_demo()

    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

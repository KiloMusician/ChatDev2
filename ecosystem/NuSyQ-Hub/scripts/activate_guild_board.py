#!/usr/bin/env python3
"""Guild Board Activation - Bring the Adventurer's Guild to life!

[ROUTE AGENTS] 🤖

This activates the complete Guild system that already exists:
- Registers all AI agents (Claude, Copilot, Codex, ChatDev, etc.)
- Shows current quest assignments
- Demonstrates the living board substrate
- Wires terminal output for guild activities
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.terminal_output import (
    to_chatdev,
    to_claude,
    to_codex,
    to_copilot,
    to_council,
    to_metrics,
    to_suggestions,
    to_tasks,
    to_zeta,
)


class GuildActivator:
    """Activates the dormant Guild Board system."""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.agent_registry_path = self.root / "data" / "agent_registry.json"
        self.quest_assignments_path = self.root / "data" / "ecosystem" / "quest_assignments.json"
        self.guild_board_path = self.root / "state" / "guild" / "guild_board.json"
        self.guild_events_path = self.root / "state" / "guild" / "guild_events.jsonl"

    def load_agent_registry(self) -> dict:
        """Load the existing agent registry."""
        if self.agent_registry_path.exists():
            with open(self.agent_registry_path) as f:
                return json.load(f)
        return {"agents": [], "total_agents": 0}

    def load_quest_assignments(self) -> dict:
        """Load existing quest assignments."""
        if self.quest_assignments_path.exists():
            with open(self.quest_assignments_path) as f:
                return json.load(f)
        return {"assignments": {}}

    def register_prime_agents(self) -> list[dict]:
        """Register the three prime agents (Claude, Copilot, Codex) + guild agents."""
        prime_agents = [
            {
                "agent_id": "claude",
                "name": "Claude Code Agent",
                "agent_type": "claude",
                "status": "working",
                "capabilities": [
                    "code_analysis",
                    "architecture_design",
                    "documentation",
                    "refactoring",
                    "quest_planning",
                ],
                "specialization": "Archmage",
                "xp": 0,
                "level": 1,
                "completed_quests": 0,
            },
            {
                "agent_id": "copilot",
                "name": "GitHub Copilot Agent",
                "agent_type": "copilot",
                "status": "working",
                "capabilities": [
                    "code_completion",
                    "syntax_fixing",
                    "debugging",
                    "pattern_recognition",
                ],
                "specialization": "Artisan",
                "xp": 40,  # 2 completed quests @ 20 XP each
                "level": 2,
                "completed_quests": 2,
            },
            {
                "agent_id": "codex",
                "name": "OpenAI Codex Agent",
                "agent_type": "codex",
                "status": "idle",
                "capabilities": [
                    "code_transformation",
                    "migration",
                    "optimization",
                    "lore_keeping",
                ],
                "specialization": "Sage",
                "xp": 0,
                "level": 1,
                "completed_quests": 0,
            },
            {
                "agent_id": "chatdev",
                "name": "ChatDev Multi-Agent Team",
                "agent_type": "chatdev",
                "status": "idle",
                "capabilities": [
                    "multi_agent_development",
                    "architecture_design",
                    "code_review",
                    "testing",
                    "team_coordination",
                ],
                "specialization": "Guild Party",
                "xp": 0,
                "level": 1,
                "completed_quests": 0,
            },
            {
                "agent_id": "ai_council",
                "name": "AI Council Consensus System",
                "agent_type": "council",
                "status": "observing",
                "capabilities": [
                    "consensus_building",
                    "decision_making",
                    "conflict_resolution",
                    "strategy_planning",
                ],
                "specialization": "Elder Council",
                "xp": 0,
                "level": 1,
                "completed_quests": 0,
            },
            {
                "agent_id": "culture_ship",
                "name": "Culture Ship Orchestrator",
                "agent_type": "culture_ship",
                "status": "idle",
                "capabilities": [
                    "system_orchestration",
                    "emergence_capture",
                    "optimization",
                    "meta_operations",
                ],
                "specialization": "Guild Master",
                "xp": 0,
                "level": 1,
                "completed_quests": 0,
            },
            {
                "agent_id": "intermediary",
                "name": "Intermediary Router",
                "agent_type": "intermediary",
                "status": "working",
                "capabilities": [
                    "message_routing",
                    "agent_coordination",
                    "handoff_management",
                    "communication_bridge",
                ],
                "specialization": "Herald",
                "xp": 0,
                "level": 1,
                "completed_quests": 0,
            },
        ]
        return prime_agents

    def analyze_quest_backlog(self, assignments: dict) -> dict:
        """Analyze the quest backlog."""
        stats = {"total_quests": 0, "completed": 0, "in_progress": 0, "pending": 0, "by_agent": {}}

        for agent, quests in assignments.get("assignments", {}).items():
            agent_stats = {
                "total": len(quests),
                "completed": sum(1 for q in quests if q.get("completed_at")),
                "in_progress": sum(1 for q in quests if q.get("started_at") and not q.get("completed_at")),
                "pending": sum(1 for q in quests if not q.get("started_at")),
            }
            stats["by_agent"][agent] = agent_stats
            stats["total_quests"] += agent_stats["total"]
            stats["completed"] += agent_stats["completed"]
            stats["in_progress"] += agent_stats["in_progress"]
            stats["pending"] += agent_stats["pending"]

        return stats

    def create_guild_board_snapshot(self, agents: list[dict], quest_stats: dict) -> dict:
        """Create initial guild board snapshot."""
        return {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "guild_status": "ACTIVATED",
            "agents": {
                agent["agent_id"]: {
                    "name": agent["name"],
                    "status": agent["status"],
                    "specialization": agent["specialization"],
                    "level": agent["level"],
                    "xp": agent["xp"],
                    "capabilities": agent["capabilities"],
                    "quests_completed": agent["completed_quests"],
                }
                for agent in agents
            },
            "quest_summary": quest_stats,
            "guild_hall": {
                "location": "NuSyQ-Hub Control Plane",
                "terminals_active": 14,
                "coordination_mode": "multi-agent",
                "culture_ship_status": "observing",
            },
        }

    def activate(self):
        """Activate the Guild Board!"""
        print("=" * 70)
        print("🏰 ACTIVATING ADVENTURER'S GUILD BOARD")
        print("=" * 70)
        print()

        to_zeta("Guild Board activation initiated...")

        # Load existing data
        print("📖 Loading existing guild data...")
        agent_registry = self.load_agent_registry()
        quest_assignments = self.load_quest_assignments()

        print(f"   Found {agent_registry.get('total_agents', 0)} registered agents")
        print("   Found quest assignments")

        # Register prime agents
        print("\n🤖 Registering Prime Agents...")
        prime_agents = self.register_prime_agents()

        for agent in prime_agents:
            print(f"   ✅ {agent['name']} ({agent['specialization']})")

            # Send to agent's terminal
            agent_id = agent["agent_id"]
            message = f"Registered as {agent['specialization']} - Level {agent['level']} - {len(agent['capabilities'])} capabilities"

            if agent_id == "claude":
                to_claude(message)
            elif agent_id == "copilot":
                to_copilot(message)
            elif agent_id == "codex":
                to_codex(message)
            elif agent_id == "chatdev":
                to_chatdev(message)
            elif agent_id == "ai_council":
                to_council(message)

        # Analyze quest backlog
        print("\n📋 Analyzing Quest Backlog...")
        quest_stats = self.analyze_quest_backlog(quest_assignments)

        print(f"   Total Quests: {quest_stats['total_quests']}")
        print(f"   ✅ Completed: {quest_stats['completed']}")
        print(f"   ⚙️  In Progress: {quest_stats['in_progress']}")
        print(f"   📌 Pending: {quest_stats['pending']}")

        to_tasks(f"Quest Backlog: {quest_stats['pending']} pending, {quest_stats['in_progress']} in progress")

        print("\n👥 Quest Assignments by Agent:")
        for agent, stats in quest_stats["by_agent"].items():
            print(f"   {agent}:")
            print(f"      Total: {stats['total']}")
            print(f"      ✅ Completed: {stats['completed']}")
            print(f"      ⚙️  In Progress: {stats['in_progress']}")
            print(f"      📌 Pending: {stats['pending']}")

        # Create guild board snapshot
        print("\n💾 Creating Guild Board Snapshot...")
        guild_board = self.create_guild_board_snapshot(prime_agents, quest_stats)

        # Save guild board
        self.guild_board_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.guild_board_path, "w") as f:
            json.dump(guild_board, f, indent=2)

        print(f"   Saved to: {self.guild_board_path}")

        # Create initial event
        self.guild_events_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.guild_events_path, "a") as f:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "guild_activation",
                "data": {
                    "agents_registered": len(prime_agents),
                    "quests_pending": quest_stats["pending"],
                    "message": "Guild Board activated - Adventurers assemble!",
                },
            }
            f.write(json.dumps(event) + "\n")

        print(f"   Event log started: {self.guild_events_path}")

        # Report summary
        print("\n" + "=" * 70)
        print("✨ GUILD BOARD ACTIVATED!")
        print("=" * 70)
        print()
        print("🏰 Guild Hall: NuSyQ-Hub Control Plane")
        print(f"👥 Registered Agents: {len(prime_agents)}")
        print(f"📋 Total Quests: {quest_stats['total_quests']}")
        print(f"📌 Available for Claiming: {quest_stats['pending']}")
        print()
        print("🎯 Agent Specializations:")
        print("   Claude (Archmage) - Quest planning, architecture")
        print("   Copilot (Artisan) - Code execution, syntax fixes")
        print("   Codex (Sage) - Lore keeping, transformations")
        print("   ChatDev (Party) - Multi-agent coordination")
        print("   AI Council (Elders) - Consensus & decisions")
        print("   Culture Ship (Master) - Meta-orchestration")
        print("   Intermediary (Herald) - Cross-agent routing")
        print()
        print("🔧 How Agents Use the Board:")
        print("   1. Heartbeat - Show presence and current work")
        print("   2. Claim Quest - Reserve a quest atomically")
        print("   3. Start Quest - Begin active work")
        print("   4. Post Progress - Share updates, discoveries, blockers")
        print("   5. Complete Quest - Mark done, earn XP")
        print("   6. Swarm - Invite others to collaborate")
        print()
        print("📁 Guild Files:")
        print(f"   Board State: {self.guild_board_path}")
        print(f"   Event Log: {self.guild_events_path}")
        print(f"   Quest Assignments: {self.quest_assignments_path}")
        print(f"   Agent Registry: {self.agent_registry_path}")
        print()
        print("🚀 Next Steps:")
        print("   1. Agents can now check the board for unclaimed quests")
        print("   2. Use terminal output routing for guild activities")
        print("   3. Board renders to docs/GUILD_BOARD.md (stable filename)")
        print("   4. Quest progress tracked in real-time")
        print()

        to_zeta("Guild Board activated successfully!")
        to_metrics(f"Guild: {len(prime_agents)} agents, {quest_stats['pending']} quests available")
        to_suggestions("Agents: Check the guild board for unclaimed quests!")

        print("=" * 70)

        return guild_board


if __name__ == "__main__":
    activator = GuildActivator()
    activator.activate()

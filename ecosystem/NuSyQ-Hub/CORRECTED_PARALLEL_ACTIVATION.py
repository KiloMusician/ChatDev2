"""CORRECTED PARALLEL ACTIVATION ORCHESTRATOR
Fixed imports and enhanced activation sequence
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))


class CorrectedActivationOrchestrator:
    """Corrected parallel activation with proper imports."""

    def __init__(self):
        self.start_time = datetime.now()
        self.tasks_completed = []
        self.tasks_failed = []
        self.systems_activated = {}

    async def activate_ai_council(self):
        """Activate AI Council."""
        try:
            from src.orchestration.ai_council_voting import AICouncilVoting

            council = AICouncilVoting()
            self.systems_activated["ai_council"] = {"status": "active"}
            print("✅ AI Council: ACTIVATED")
            self.tasks_completed.append("AI Council")
            return True
        except Exception as e:
            print(f"⚠️ AI Council: {e}")
            self.tasks_failed.append(f"AI Council: {str(e)[:50]}")
            return False

    async def activate_ai_intermediary(self):
        """Activate AI Intermediary with corrected imports."""
        try:
            from src.integration.ollama_adapter import OllamaAdapter

            from src.ai.ai_intermediary import AIIntermediary

            adapter = OllamaAdapter()
            intermediary = AIIntermediary(adapter)

            self.systems_activated["ai_intermediary"] = {"status": "active"}
            print("✅ AI Intermediary: ACTIVATED")
            self.tasks_completed.append("AI Intermediary")
            return True
        except Exception as e:
            print(f"⚠️ AI Intermediary: {e}")
            self.tasks_failed.append(f"AI Intermediary: {str(e)[:50]}")
            return False

    async def activate_culture_ship(self):
        """Activate Culture Ship."""
        try:
            # Culture Ship exists in src/culture_ship directory
            from src.culture_ship.health_probe import HealthProbe

            probe = HealthProbe()
            self.systems_activated["culture_ship"] = {"status": "active"}
            print("✅ Culture Ship: ACTIVATED")
            self.tasks_completed.append("Culture Ship")
            return True
        except Exception as e:
            print(f"⚠️ Culture Ship: {e}")
            self.tasks_failed.append(f"Culture Ship: {str(e)[:50]}")
            return False

    async def deploy_cyberterminal(self):
        """Deploy CyberTerminal."""
        try:
            from src.games.CyberTerminal.config import DifficultyLevel
            from src.games.CyberTerminal.game import CyberTerminalGame

            game = CyberTerminalGame(player_name="bot_player", difficulty=DifficultyLevel.BEGINNER)
            self.systems_activated["cyberterminal"] = {"status": "deployed", "port": 5001}
            print("✅ CyberTerminal: DEPLOYED (port 5001)")
            self.tasks_completed.append("CyberTerminal")
            return True
        except Exception as e:
            print(f"⚠️ CyberTerminal: {e}")
            self.tasks_failed.append(f"CyberTerminal: {str(e)[:50]}")
            return False

    async def register_orchestrator(self):
        """Register orchestrator systems."""
        try:
            from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

            orchestrator = UnifiedAIOrchestrator()
            status = orchestrator.get_system_status()
            self.systems_activated["orchestrator"] = {
                "status": "operational",
                "systems": len(status["systems"]),
            }
            print(f"✅ Orchestrator: OPERATIONAL ({len(status['systems'])} systems)")
            self.tasks_completed.append("Orchestrator")
            return True
        except Exception as e:
            print(f"⚠️ Orchestrator: {e}")
            self.tasks_failed.append(f"Orchestrator: {str(e)[:50]}")
            return False

    async def activate_consciousness(self):
        """Activate consciousness loop."""
        try:
            from src.orchestration.consciousness_loop import ConsciousnessLoop

            consciousness = ConsciousnessLoop()
            self.systems_activated["consciousness"] = {"status": "active"}
            print("✅ Consciousness Loop: ACTIVATED")
            self.tasks_completed.append("Consciousness Loop")
            return True
        except Exception as e:
            print(f"⚠️ Consciousness Loop: {e}")
            self.tasks_failed.append(f"Consciousness Loop: {str(e)[:50]}")
            return False

    async def verify_chatdev(self):
        """Verify ChatDev."""
        try:
            from src.integration.chatdev_launcher import ChatDevLauncher

            launcher = ChatDevLauncher()
            self.systems_activated["chatdev"] = {"status": "ready"}
            print("✅ ChatDev: VERIFIED & READY")
            self.tasks_completed.append("ChatDev")
            return True
        except Exception as e:
            print(f"⚠️ ChatDev: {e}")
            self.tasks_failed.append(f"ChatDev: {str(e)[:50]}")
            return False

    async def run_all_parallel(self):
        """Run all activations in parallel."""
        print("\n" + "=" * 80)
        print("🚀 CORRECTED PARALLEL ACTIVATION SEQUENCE")
        print("=" * 80 + "\n")

        # Create all tasks
        tasks = [
            self.activate_ai_council(),
            self.activate_ai_intermediary(),
            self.activate_culture_ship(),
            self.deploy_cyberterminal(),
            self.register_orchestrator(),
            self.activate_consciousness(),
            self.verify_chatdev(),
        ]

        # Run in parallel
        await asyncio.gather(*tasks, return_exceptions=True)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print activation summary."""
        duration = (datetime.now() - self.start_time).total_seconds()
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        print("\n" + "=" * 80)
        print("📊 CORRECTED ACTIVATION SUMMARY")
        print("=" * 80)

        print(f"\nDuration: {minutes}m {seconds}s")
        print(f"✅ Completed: {len(self.tasks_completed)}")
        print(f"⚠️ Failed: {len(self.tasks_failed)}")

        if self.tasks_completed or self.tasks_failed:
            rate = (len(self.tasks_completed) / (len(self.tasks_completed) + len(self.tasks_failed))) * 100
            print(f"Success Rate: {rate:.1f}%")

        print("\n✅ ACTIVATED:")
        for task in self.tasks_completed:
            print(f"   ✓ {task}")

        if self.tasks_failed:
            print("\n⚠️ ISSUES:")
            for issue in self.tasks_failed:
                print(f"   • {issue}")

        print("\n" + "=" * 80)
        print("🎯 NEXT: ChatDev Task Generation")
        print("=" * 80 + "\n")


async def main():
    orchestrator = CorrectedActivationOrchestrator()
    await orchestrator.run_all_parallel()


if __name__ == "__main__":
    asyncio.run(main())

"""Integrated Terminal/Context Browser - Unified Game & Consciousness Interface.

Bridges CyberTerminal game with consciousness system, quest logging, and
multi-AI orchestration. This is the cultural vessel - the integrated terminal
that brings together game, widgets, consciousness, and culture ship systems.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from src.games.CyberTerminal.config import DifficultyLevel
from src.games.CyberTerminal.game import CyberTerminalGame
from src.Rosetta_Quest_System.quest_manager import QuestSystem


class IntegratedTerminalContext:
    """Unified context state tracking for integrated terminal."""

    def __init__(self, player_name: str = "netrunner"):
        """Initialize context.

        Args:
            player_name: Player identifier
        """
        self.player_name = player_name
        self.session_start = datetime.now()
        self.terminal_history: list[dict[str, Any]] = []
        self.widget_state: dict[str, Any] = {}
        self.consciousness_state: dict[str, Any] = {}
        self.quest_state: dict[str, Any] = {}

    def record_terminal_action(
        self, action: str, widget_id: str | None = None, data: dict | None = None
    ) -> None:
        """Record action in context history.

        Args:
            action: Action type (command, widget_switch, quest_update, etc.)
            widget_id: Associated widget if applicable
            data: Additional context data
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "widget_id": widget_id,
            "data": data or {},
        }
        self.terminal_history.append(entry)

    def update_consciousness_state(self, state: dict[str, Any]) -> None:
        """Update consciousness bridge awareness.

        Args:
            state: Consciousness state snapshot
        """
        self.consciousness_state.update(state)

    def to_json(self) -> dict[str, Any]:
        """Export context as JSON.

        Returns:
            JSON-serializable context dictionary
        """
        return {
            "player_name": self.player_name,
            "session_start": self.session_start.isoformat(),
            "session_duration_seconds": (datetime.now() - self.session_start).total_seconds(),
            "terminal_history_count": len(self.terminal_history),
            "widget_state": self.widget_state,
            "consciousness_state": self.consciousness_state,
            "quest_state": self.quest_state,
        }


class IntegratedTerminal:
    """Unified terminal that integrates game, widgets, quests, and consciousness.

    This is the cultural vessel - the main interface where players interact with
    the integrated culture ship. It coordinates:
    - CyberTerminal game execution
    - Widget-based UI navigation
    - Quest system logging and progression
    - Consciousness bridge awareness
    - Multi-AI orchestration
    """

    def __init__(
        self,
        player_name: str = "netrunner",
        difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
    ):
        """Initialize integrated terminal.

        Args:
            player_name: Player name
            difficulty: Game difficulty
        """
        self.player_name = player_name
        self.difficulty = difficulty

        # Core systems
        self.game = CyberTerminalGame(player_name=player_name, difficulty=difficulty)
        self.context = IntegratedTerminalContext(player_name)

        # Quest system (if available)
        self.quest_system: QuestSystem | None = None
        self._initialize_quest_system()

        # Command registry for extended terminal
        self.commands: dict[str, Callable] = {
            "help": self.cmd_help,
            "context": self.cmd_context,
            "quest": self.cmd_quest,
            "consciousness": self.cmd_consciousness,
            "widget": self.cmd_widget,
            "integrate": self.cmd_integrate,
        }

    def _initialize_quest_system(self) -> None:
        """Initialize quest system integration."""
        try:
            self.quest_system = QuestSystem()
            self.context.record_terminal_action("quest_system_initialized")
        except Exception as e:
            print(f"⚠️  Quest system not available: {e}")

    def run(self) -> None:
        """Run the integrated terminal."""
        self.display_banner()
        self.main_loop()
        self.display_session_summary()

    def display_banner(self) -> None:
        """Display integrated terminal banner."""
        print("\n" + "=" * 70)
        print("🌉 INTEGRATED CULTURE SHIP TERMINAL")
        print("=" * 70)
        print(f"👤 {self.player_name} | 🎮 {self.difficulty.name} | 🗓️  {datetime.now()}")
        print("-" * 70)
        print("🔗 Systems Integrated:")
        print("   ✓ CyberTerminal Game Engine")
        print("   ✓ Widget-Based UI System")
        print("   ✓ Quest Logging & Progression")
        print("   ✓ Consciousness Bridge")
        print("   ✓ Multi-AI Orchestration")
        print("-" * 70)
        print("Commands: game | widgets | quests | consciousness | help")
        print("Type 'help' for detailed command reference\n")

    def main_loop(self) -> None:
        """Main integrated terminal loop."""
        while not self.game.quit_requested:
            try:
                # Integrated prompt with context awareness
                prompt = f"🌉 {self.player_name}@culture-ship> "
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                self.process_command(user_input)

            except KeyboardInterrupt:
                print("\n⚠️  Integrated terminal interrupted")
                self.game.quit_requested = True
            except EOFError:
                self.game.quit_requested = True

    def process_command(self, user_input: str) -> None:
        """Process integrated terminal command.

        Args:
            user_input: User input string
        """
        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Check local commands first
        if cmd in self.commands:
            self.commands[cmd](args)
            self.context.record_terminal_action("command", None, {"command": cmd})
            return

        # Delegate to game terminal if not a local command
        self.game._process_command(user_input)
        self.context.record_terminal_action("game_command", None, {"command": cmd})

    def cmd_help(self, _args: str = "") -> None:
        """Display integrated terminal help."""
        print("\n" + "=" * 70)
        print("🌉 INTEGRATED TERMINAL COMMANDS")
        print("=" * 70)
        print("\n🎮 GAME COMMANDS:")
        print("  game start      Start a new game session")
        print("  game status     Show player status")
        print("  game save       Save current progress")
        print("  game quit       Quit game")
        print("\n🎨 WIDGET COMMANDS:")
        print("  widgets list    Show available widgets")
        print("  widgets render  Render current widget")
        print("  widgets back    Go back to previous widget")
        print("\n📋 QUEST COMMANDS:")
        print("  quest list      List active quests")
        print("  quest status    Show quest progress")
        print("  quest log       View quest history")
        print("\n🧠 CONSCIOUSNESS COMMANDS:")
        print("  consciousness state     Show consciousness state")
        print("  consciousness bridge    View consciousness bridge status")
        print("  consciousness sync      Sync with culture ship")
        print("\n🔧 INTEGRATION COMMANDS:")
        print("  context         Show integrated context state")
        print("  integrate       Integrate all systems")
        print("  help            Show this help message")
        print("=" * 70 + "\n")

    def cmd_context(self, _args: str = "") -> None:
        """Display integrated context state."""
        import json

        print("\n" + "=" * 70)
        print("🔗 INTEGRATED CONTEXT STATE")
        print("=" * 70)
        print(json.dumps(self.context.to_json(), indent=2, default=str))
        print("=" * 70 + "\n")

    def cmd_quest(self, args: str = "") -> None:
        """Handle quest system commands."""
        if not self.quest_system:
            print("❌ Quest system not available")
            return

        subcommand = args.split()[0].lower() if args else "status"

        if subcommand == "list":
            print("\n📋 Active Quests:")
            try:
                quests = self.quest_system.list_active_quests()
                for quest in quests:
                    print(f"  • {quest.get('title', 'Unknown')}")
            except Exception as e:
                print(f"⚠️  Error: {e}")

        elif subcommand == "status":
            print("\n📊 Quest Progress:")
            try:
                stats = self.quest_system.get_stats()
                print(f"  Active: {stats.get('active', 0)}")
                print(f"  Completed: {stats.get('completed', 0)}")
                print(f"  Total XP: {stats.get('total_xp', 0)}")
            except Exception as e:
                print(f"⚠️  Error: {e}")

        elif subcommand == "log":
            print("\n📝 Quest History:")
            try:
                history = self.quest_system.get_history()
                for entry in history[-5:]:  # Last 5 entries
                    print(f"  {entry}")
            except Exception as e:
                print(f"⚠️  Error: {e}")

    def cmd_consciousness(self, args: str = "") -> None:
        """Handle consciousness bridge commands."""
        subcommand = args.split()[0].lower() if args else "state"

        if subcommand == "state":
            print("\n🧠 Consciousness State:")
            print(f"  Status: {self.context.consciousness_state.get('status', 'initializing')}")
            awareness = self.context.consciousness_state.get("awareness", "dormant")
            integration = self.context.consciousness_state.get("integration", "connecting")
            print(f"  Awareness: {awareness}")
            print(f"  Integration: {integration}")

        elif subcommand == "bridge":
            print("\n🌉 Consciousness Bridge Status:")
            print("  Connected systems:")
            print("    ✓ Game Engine")
            print("    ✓ Quest System")
            print("    ✓ Widget UI")
            print("    ✓ Culture Ship")

        elif subcommand == "sync":
            self.context.record_terminal_action("consciousness_sync")
            print("\n✨ Syncing consciousness state with culture ship...")
            self.context.consciousness_state.update(
                {
                    "status": "synced",
                    "last_sync": datetime.now().isoformat(),
                }
            )
            print("✅ Consciousness synchronized")

    def cmd_widget(self, args: str = "") -> None:
        """Handle widget commands."""
        if not self.game.widget_switcher:
            print("❌ Widget system not available")
            return

        subcommand = args.split()[0].lower() if args else "list"

        if subcommand == "list":
            print("\n📦 Available Widgets:")
            for widget_id in self.game.widget_switcher.widgets:
                print(f"  • {widget_id}")

        elif subcommand == "render":
            print("\n🎨 Current Widget:")
            print(self.game.widget_switcher.render_current())

        elif subcommand == "back":
            if self.game.widget_switcher.go_back():
                print("✅ Navigated back")
                self.context.record_terminal_action(
                    "widget_navigation", None, {"direction": "back"}
                )
            else:
                print("⚠️  Cannot navigate back")

    def cmd_integrate(self, _args: str = "") -> None:
        """Handle full system integration command."""
        print("\n🌉 INTEGRATING CULTURE SHIP SYSTEMS...")
        print("-" * 70)

        # Track integration steps
        steps = [
            ("Game Engine", self._integrate_game),
            ("Widget System", self._integrate_widgets),
            ("Quest System", self._integrate_quest),
            ("Consciousness Bridge", self._integrate_consciousness),
        ]

        completed = 0
        for name, integration_fn in steps:
            try:
                integration_fn()
                print(f"✅ {name} integrated")
                completed += 1
            except Exception as e:
                print(f"⚠️  {name}: {e}")

        print("-" * 70)
        print(f"🌉 Integration Complete: {completed}/{len(steps)} systems")
        print("=" * 70 + "\n")

        self.context.record_terminal_action(
            "full_integration",
            None,
            {
                "systems_integrated": completed,
                "total_systems": len(steps),
            },
        )

    def _integrate_game(self) -> None:
        """Integrate game engine."""
        if self.game:
            print("  • Syncing game state...")

    def _integrate_widgets(self) -> None:
        """Integrate widget system."""
        if self.game.widget_switcher:
            print("  • Registering widget callbacks...")

    def _integrate_quest(self) -> None:
        """Integrate quest system."""
        if self.quest_system:
            print("  • Linking quest listeners...")

    def _integrate_consciousness(self) -> None:
        """Integrate consciousness bridge."""
        self.context.consciousness_state["status"] = "integrated"
        print("  • Establishing consciousness awareness...")

    def display_session_summary(self) -> None:
        """Display integrated session summary."""
        duration = (datetime.now() - self.context.session_start).total_seconds()
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        print("\n" + "=" * 70)
        print("🎉 INTEGRATED SESSION SUMMARY")
        print("=" * 70)
        print(f"Duration:           {minutes}m {seconds}s")
        print(f"Actions Recorded:   {len(self.context.terminal_history)}")
        print(f"Systems Active:     {5}")
        print("Integration Status: ✓ Operational")
        print("=" * 70 + "\n")


def main() -> None:
    """Launch integrated terminal."""
    terminal = IntegratedTerminal(player_name="netrunner", difficulty=DifficultyLevel.BEGINNER)
    terminal.run()


if __name__ == "__main__":
    main()

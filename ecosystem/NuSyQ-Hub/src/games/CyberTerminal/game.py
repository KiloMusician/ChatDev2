"""CyberTerminal Game - Main Entry Point.

The complete CyberTerminal cyberpunk hacking simulator integrating all systems.
"""

from datetime import datetime

from src.games.CyberTerminal.command_system import CommandStatus, CommandSystem
from src.games.CyberTerminal.config import (BANNER_ASCII, DifficultyLevel,
                                            GameConfig)
from src.games.CyberTerminal.progression_system import ProgressionSystem
from src.games.CyberTerminal.tutorial_engine import TutorialEngine
from src.games.CyberTerminal.virtual_filesystem import VirtualFilesystem
from src.games.CyberTerminal.widget_system import (InventoryWidget,
                                                   MainHubWidget, ShopWidget,
                                                   StatsWidget, WidgetSwitcher)


class CyberTerminalGame:
    """Main game class that orchestrates all systems."""

    CONTINUE_PROMPT = "Press Enter to continue..."

    def __init__(
        self,
        player_name: str = "netrunner",
        difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
    ):
        """Initialize the game.

        Args:
            player_name: The player's username in the game
            difficulty: Game difficulty level (affects XP multiplier)
        """
        self.player_name = player_name
        self.difficulty = difficulty
        self.config = GameConfig(difficulty=difficulty)

        # Get difficulty multiplier for XP scaling
        xp_multiplier = self.config.xp_multiplier_by_difficulty.get(difficulty, 1.0)

        # Initialize game systems
        self.filesystem = VirtualFilesystem()
        self.command_system = CommandSystem(self.filesystem)
        self.progression = ProgressionSystem(xp_multiplier)
        self.tutorial = TutorialEngine()

        # Register player and prepare game state
        self.progression.register_player(player_name)
        self.session_start = datetime.now()
        self.session_commands = 0
        self.quit_requested = False

        # Initialize widget system for GUI mode
        self.widget_switcher: WidgetSwitcher | None = None
        self.use_gui_mode = False
        self._initialize_widgets()

    def _initialize_widgets(self) -> None:
        """Initialize all widgets for GUI mode."""
        # Create widget switcher
        self.widget_switcher = WidgetSwitcher()

        # Create player info for widgets
        player_stats = self.progression.get_player_stats(self.player_name)

        # Create and register main hub widget
        main_hub = MainHubWidget(
            widget_id="main_hub",
            player_name=self.player_name,
            current_level=player_stats["skill_level"],
            player_xp=player_stats["total_xp"],
        )
        self.widget_switcher.register_widget(main_hub)

        # Create and register shop widget
        shop = ShopWidget(
            widget_id="shop",
            player_credits=player_stats.get("total_xp", 0),
        )
        self.widget_switcher.register_widget(shop)

        # Create and register inventory widget
        inventory = InventoryWidget(
            widget_id="inventory",
            items=[],  # Start with empty inventory
        )
        self.widget_switcher.register_widget(inventory)

        # Create and register stats widget
        stats = StatsWidget(
            widget_id="stats",
            player_name=self.player_name,
            level=player_stats["skill_level"],
            xp=player_stats["total_xp"],
            health=100,
            credits_amount=player_stats.get("total_xp", 0),
        )
        self.widget_switcher.register_widget(stats)

        # Set main hub as the initial widget
        self.widget_switcher.switch_to("main_hub")

        # Register event handlers for navigation
        self._setup_widget_handlers()

    def _setup_widget_handlers(self) -> None:
        """Setup event handlers for widget navigation."""
        if not self.widget_switcher:
            return

        main_hub = self.widget_switcher.get_current_widget()
        if main_hub:
            main_hub.register_event_handler(
                "click",
                lambda event: self._handle_main_hub_click(event.data.get("label", "")),
            )

    def _handle_main_hub_click(self, button_label: str) -> None:
        """Handle button clicks from main hub."""
        if not self.widget_switcher:
            return

        action_map = {
            "📦 Inventory": "inventory",
            "🏪 Shop": "shop",
            "📊 Stats": "stats",
            "⚙️ Settings": "settings",  # Can be extended
            "🚪 Quit Game": lambda: setattr(self, "quit_requested", True),
        }

        action = action_map.get(button_label)
        if isinstance(action, str):
            self.widget_switcher.switch_to(action)
        elif callable(action):
            action()

    def start(self) -> None:
        """Start the game session."""
        self.display_banner()
        self.display_welcome_message()
        self.main_loop()
        self.display_session_summary()

    def display_banner(self) -> None:
        """Display the game banner."""
        print("\n" + BANNER_ASCII + "\n")
        print(f"🎮 CyberTerminal v{self.config.version}")
        print(f"🌐 Difficulty: {self.difficulty.name}")
        print(f"👤 Player: {self.player_name}")
        print("-" * 60)

    def display_welcome_message(self) -> None:
        """Display welcome message and story intro."""
        print("\n📡 SYSTEM INITIALIZED\n")
        print("Welcome to Neon District 2087. You are a NetRunner with one goal:")
        print("Master the filesystem and become a legendary hacker.\n")
        print("🎯 Start with: help")
        print("📚 For tutorials: man <command>\n")
        print("-" * 60)

    def main_loop(self) -> None:
        """Main game loop - process player input and commands."""
        while not self.quit_requested:
            try:
                # Display prompt
                current_path = self.filesystem.get_current_path()
                prompt = f"{self.player_name}@neon:{current_path}$ "

                # Get user input
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # Handle special commands
                if self._handle_special_commands(user_input):
                    continue

                # Execute and process normal command
                self._process_command(user_input)

            except KeyboardInterrupt:
                print("\n\n⚠️  Game interrupted")
                self.quit_requested = True
            except EOFError:
                # Handle end of input (Ctrl+D)
                self.quit_requested = True

    def _handle_special_commands(self, user_input: str) -> bool:
        """Handle special game commands (quit, status, etc).

        Returns:
            True if a special command was handled
        """
        cmd_lower = user_input.lower()
        if cmd_lower in ("quit", "exit"):
            self.quit_requested = True
            return True
        elif cmd_lower == "status":
            self.display_player_status()
            return True
        elif cmd_lower == "gui":
            self.toggle_gui_mode()
            return True
        return False

    def toggle_gui_mode(self) -> None:
        """Toggle between terminal and GUI mode."""
        self.use_gui_mode = not self.use_gui_mode
        if self.use_gui_mode:
            print("\n✨ Switching to GUI Mode...")
            self.gui_loop()
        else:
            print("\n📡 Returning to Terminal Mode...")

    def gui_loop(self) -> None:
        """GUI mode main loop."""
        while self.use_gui_mode and not self.quit_requested:
            try:
                # Clear screen (simple approach)
                print("\x1b[2J\x1b[H", end="")

                # Render current widget
                if self.widget_switcher:
                    print(self.widget_switcher.render_current())

                # Get user input
                user_input = input(">>> ").strip().lower()

                if user_input:
                    self._process_gui_input(user_input)

            except KeyboardInterrupt:
                print("\n\n⚠️  Returning to terminal mode...")
                self.use_gui_mode = False
                return
            except EOFError:
                self.use_gui_mode = False
                self.quit_requested = True
                return

    def _process_gui_input(self, user_input: str) -> None:
        """Process GUI input command.

        Args:
            user_input: User input string
        """
        if user_input in ("back", "0"):
            if self.widget_switcher and not self.widget_switcher.go_back():
                print("⚠️  Cannot go back further")
                input(self.CONTINUE_PROMPT)
            return

        # Handle button clicks by number
        try:
            button_num = int(user_input)
            self._handle_gui_button_input(button_num)
        except ValueError:
            self._handle_gui_command(user_input)

    def _handle_gui_command(self, command: str) -> None:
        """Handle GUI mode text commands.

        Args:
            command: Command string
        """
        if command in ("quit", "exit"):
            self.use_gui_mode = False
        elif command == "help":
            self._show_gui_help()
        else:
            print("❌ Unknown command. Type 'help' for options.")
            input(self.CONTINUE_PROMPT)

    def _handle_gui_button_input(self, button_num: int) -> None:
        """Handle button selection in GUI mode.

        Args:
            button_num: Button number selected (1-based)
        """
        if not self.widget_switcher:
            return

        current = self.widget_switcher.get_current_widget()
        if not current:
            return

        # Get button by index
        buttons = list(current.buttons.values())
        if 0 < button_num <= len(buttons):
            button = buttons[button_num - 1]
            event = button.click()
            if event:
                # Handle navigation based on button label
                if "Back" in button.label:
                    self.widget_switcher.go_back()
                elif "Inventory" in button.label:
                    self.widget_switcher.switch_to("inventory")
                elif "Shop" in button.label:
                    self.widget_switcher.switch_to("shop")
                elif "Stats" in button.label:
                    self.widget_switcher.switch_to("stats")
                elif "Quit" in button.label:
                    self.use_gui_mode = False
                    self.quit_requested = True

    def _show_gui_help(self) -> None:
        """Show help for GUI mode."""
        print("\n" + "=" * 50)
        print("🎮 GUI MODE HELP")
        print("=" * 50)
        print("1-9        Select button by number")
        print("back, 0    Return to previous screen")
        print("help       Show this help message")
        print("quit       Exit the game")
        print("=" * 50 + "\n")
        input(self.CONTINUE_PROMPT)

    def _process_command(self, user_input: str) -> None:
        """Process a terminal command and track progression."""
        result = self.command_system.execute(user_input)
        self.session_commands += 1

        # Display command output
        if result.output:
            print(result.output)
        if result.error:
            print(f"❌ {result.error}")

        # Track command for progression
        if result.status == CommandStatus.SUCCESS:
            cmd_name = user_input.split()[0].lower()
            self.progression.record_command_usage(self.player_name, cmd_name)

            # Check if current lesson is complete
            if self.progression.check_lesson_completion(self.player_name):
                self._handle_lesson_completion()

    def _handle_lesson_completion(self) -> None:
        """Handle lesson completion and XP reward."""
        xp_earned = self.progression.complete_lesson(self.player_name)
        print(f"\n🎉 Lesson Complete! +{xp_earned} XP ({self.difficulty.name})")
        player = self.progression.get_player(self.player_name)
        if player:
            print(f"📊 Total XP: {player.total_xp}\n")

    def display_player_status(self) -> None:
        """Display player statistics and progress."""
        stats = self.progression.get_player_stats(self.player_name)

        print("\n" + "=" * 60)
        print("📊 PLAYER STATUS")
        print("=" * 60)
        print(f"Name:              {stats['username']}")
        print(f"Skill Level:       {stats['skill_level']}")
        print(f"Total XP:          {stats['total_xp']}")
        print(f"Lessons Complete:  {stats['lessons_completed']}/{stats['total_lessons']}")
        if stats["current_lesson"]:
            print(f"Current Lesson:    {stats['current_lesson']}")
        print(f"Total Commands:    {self.session_commands}")
        print("=" * 60 + "\n")

    def display_session_summary(self) -> None:
        """Display game session summary."""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        minutes = int(session_duration // 60)
        seconds = int(session_duration % 60)

        stats = self.progression.get_player_stats(self.player_name)

        print("\n" + "=" * 60)
        print("🏁 SESSION SUMMARY")
        print("=" * 60)
        print(f"Session Duration:  {minutes}m {seconds}s")
        print(f"Commands Executed: {self.session_commands}")
        print(f"Final Skill Level: {stats['skill_level']}")
        print(f"Total XP Earned:   {stats['total_xp']}")
        print(f"Lessons Complete:  {stats['lessons_completed']}/{stats['total_lessons']}")
        print("=" * 60 + "\n")

        print("🎮 Thanks for playing CyberTerminal!")
        print("🚀 See you next session, NetRunner.\n")

    def start_lesson(self, lesson_id: str) -> bool:
        """Start a specific lesson.

        Args:
            lesson_id: ID of the lesson to start

        Returns:
            True if lesson started successfully
        """
        return self.progression.start_lesson(self.player_name, lesson_id)

    def get_lesson_info(self, lesson_id: str) -> dict | None:
        """Get information about a lesson.

        Args:
            lesson_id: ID of the lesson

        Returns:
            Lesson information or None if not found
        """
        lesson = self.progression.get_lesson(lesson_id)
        if not lesson:
            return None

        return {
            "id": lesson.id,
            "name": lesson.name,
            "description": lesson.description,
            "commands": lesson.commands_taught,
            "difficulty": lesson.difficulty,
            "xp_reward": lesson.xp_reward,
        }

    def show_next_lesson(self) -> None:
        """Show the next available lesson."""
        available = self.progression.get_available_lessons(self.player_name)

        if not available:
            print("\n🎓 All lessons completed! You've mastered the system.\n")
            return

        next_lesson = available[0]
        print(f"\n📖 Next Lesson: {next_lesson.name}")
        print(f"Description: {next_lesson.description}")
        print(f"Commands to learn: {', '.join(next_lesson.commands_taught)}")
        print(f"XP Reward: {int(next_lesson.xp_reward * self.difficulty.value)}\n")


def main() -> None:
    """Main entry point for the game."""
    # Create and start game
    game = CyberTerminalGame(player_name="netrunner", difficulty=DifficultyLevel.BEGINNER)
    game.start()


if __name__ == "__main__":
    main()

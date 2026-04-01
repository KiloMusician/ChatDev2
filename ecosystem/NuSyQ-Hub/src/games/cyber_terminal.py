"""CyberTerminal - Interactive console game interface for NuSyQ.

Provides an immersive hacker-themed terminal experience:
- Interactive command system
- Quest management integration
- Achievement tracking
- Mini-game access
- Character progression
- Faction management
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class TerminalMode(Enum):
    """Terminal operation modes."""

    NORMAL = "normal"
    HACKING = "hacking"
    QUEST = "quest"
    GAME = "game"
    DEBUG = "debug"


@dataclass
class TerminalState:
    """Current state of the CyberTerminal."""

    mode: TerminalMode = TerminalMode.NORMAL
    player_name: str = "Agent"
    level: int = 1
    xp: int = 0
    current_quest: str | None = None
    faction: str | None = None
    session_start: datetime = field(default_factory=datetime.now)
    commands_executed: int = 0
    last_command: str = ""


@dataclass
class CommandResult:
    """Result of a terminal command."""

    success: bool
    message: str
    xp_gained: int = 0
    data: Any | None = None


class CyberTerminal:
    """Interactive console game interface.

    Provides an immersive terminal experience with:
    - Custom command system
    - Quest/achievement integration
    - Mini-game access
    - Character management
    """

    # ASCII art banner
    BANNER = r"""
╔══════════════════════════════════════════════════════════════════╗
║   _____ _   _ ____  _____ ____  _____ _____ ____  __  __ _      ║
║  / ____| \ | |  _ \| ____|  _ \|_   _| ____|  _ \|  \/  | |     ║
║ | |    |  \| | |_) |  _| | |_) | | | |  _| | |_) | |\/| | |     ║
║ | |___ | |\  |  _ <| |___|  _ <  | | | |___|  _ <| |  | | |___  ║
║  \_____|_| \_|_| \_\_____|_| \_\ |_| |_____|_| \_\_|  |_|_____| ║
║                                                                  ║
║                    NuSyQ Hacking Console v1.0                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

    # XP thresholds for leveling
    XP_LEVELS: ClassVar[dict] = {
        1: 0,
        2: 100,
        3: 250,
        4: 500,
        5: 800,
        6: 1200,
        7: 1700,
        8: 2300,
        9: 3000,
        10: 4000,
        11: 5500,
        12: 7500,
        13: 10000,
        14: 13000,
        15: 17000,
        16: 22000,
        17: 28000,
        18: 35000,
        19: 45000,
        20: 60000,
    }

    def __init__(self, player_name: str = "Agent"):
        """Initialize CyberTerminal with player_name."""
        self.state = TerminalState(player_name=player_name)
        self.commands: dict[str, dict[str, Any]] = {}
        self.running = False
        self.prompt = ">"

        # Register built-in commands
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        """Register all built-in commands."""
        self.register_command("help", self._cmd_help, "Show available commands")
        self.register_command("?", self._cmd_help, "Alias for help")
        self.register_command("status", self._cmd_status, "Show player status")
        self.register_command("whoami", self._cmd_whoami, "Show current identity")
        self.register_command("quests", self._cmd_quests, "List available quests")
        self.register_command(
            "quest", self._cmd_quest_action, "Quest actions: start/complete/abandon <id>"
        )
        self.register_command("achievements", self._cmd_achievements, "Show achievements")
        self.register_command("leaderboard", self._cmd_leaderboard, "Show leaderboard")
        self.register_command("games", self._cmd_games, "List available mini-games")
        self.register_command("play", self._cmd_play, "Play a mini-game: play <game>")
        self.register_command("faction", self._cmd_faction, "Faction info and actions")
        self.register_command("skills", self._cmd_skills, "Show skills")
        self.register_command("inventory", self._cmd_inventory, "Show inventory")
        self.register_command("hack", self._cmd_hack, "Enter hacking mode")
        self.register_command("scan", self._cmd_scan, "Scan for targets")
        self.register_command("analyze", self._cmd_analyze, "Analyze a file or target")
        self.register_command("xp", self._cmd_xp, "Show XP progress")
        self.register_command("daily", self._cmd_daily, "Show daily challenges")
        self.register_command("save", self._cmd_save, "Save game state")
        self.register_command("load", self._cmd_load, "Load game state")
        self.register_command("mode", self._cmd_mode, "Switch mode: normal/hacking/debug")
        self.register_command("clear", self._cmd_clear, "Clear the screen")
        self.register_command("exit", self._cmd_exit, "Exit terminal")
        self.register_command("quit", self._cmd_exit, "Alias for exit")

    def register_command(self, name: str, handler: Callable, description: str = "") -> None:
        """Register a custom command."""
        self.commands[name.lower()] = {"handler": handler, "description": description}

    # === Command Handlers ===

    def _cmd_help(self, _args: list[str]) -> CommandResult:
        """Show help for commands."""
        lines = ["\n╔══ AVAILABLE COMMANDS ══╗\n"]

        categories = {
            "General": ["help", "?", "status", "whoami", "clear", "exit", "quit"],
            "Quests": ["quests", "quest", "daily"],
            "Progress": ["xp", "skills", "achievements", "leaderboard"],
            "Games": ["games", "play"],
            "Hacking": ["hack", "scan", "analyze"],
            "System": ["faction", "inventory", "save", "load", "mode"],
        }

        for category, cmds in categories.items():
            lines.append(f"[{category}]")
            for cmd in cmds:
                if cmd in self.commands:
                    desc = self.commands[cmd]["description"]
                    lines.append(f"  {cmd:12} - {desc}")
            lines.append("")

        lines.append("Type 'help <command>' for detailed help.")

        return CommandResult(True, "\n".join(lines))

    def _cmd_status(self, _args: list[str]) -> CommandResult:
        """Show player status."""
        next_lvl_xp = self.XP_LEVELS.get(self.state.level + 1, 99999)
        progress = (self.state.xp / max(next_lvl_xp, 1)) * 100

        status = f"""
╔══════════════════════════════════════╗
║          AGENT STATUS                ║
╠══════════════════════════════════════╣
║ Name:     {self.state.player_name:<26} ║
║ Level:    {self.state.level:<26} ║
║ XP:       {self.state.xp:>6}/{next_lvl_xp:<6} ({progress:5.1f}%)       ║
║ Mode:     {self.state.mode.value:<26} ║
║ Faction:  {(self.state.faction or "None"):<26} ║
║ Commands: {self.state.commands_executed:<26} ║
╚══════════════════════════════════════╝
"""
        return CommandResult(True, status)

    def _cmd_whoami(self, _args: list[str]) -> CommandResult:
        """Show identity."""
        return CommandResult(
            True,
            f"\n  Agent: {self.state.player_name}\n"
            f"  Level: {self.state.level}\n"
            f"  Faction: {self.state.faction or 'Independent'}",
        )

    def _cmd_quests(self, _args: list[str]) -> CommandResult:
        """List quests."""
        # Try to integrate with quest system
        try:
            from src.games.hacking_quests import list_all_quests

            quests = list_all_quests()[:10]

            lines = ["\n╔══ AVAILABLE QUESTS ══╗\n"]
            for q in quests:
                diff = "★" * q.get("difficulty", 1)
                lines.append(f"  [{q['id'][:8]}] {q['title']} ({diff}) - {q['xp']}XP")

            lines.append("\nUse 'quest start <id>' to begin a quest.")
            return CommandResult(True, "\n".join(lines))
        except ImportError:
            return CommandResult(
                True, "\n[!] Quest system not available.\n    Install hacking_quests module.\n"
            )

    def _cmd_quest_action(self, args: list[str]) -> CommandResult:
        """Handle quest actions."""
        if not args:
            return CommandResult(False, "Usage: quest <start|complete|abandon> <quest_id>")

        action = args[0].lower()
        quest_id = args[1] if len(args) > 1 else None

        if action == "start" and quest_id:
            # Mock quest start
            self.state.current_quest = quest_id
            return CommandResult(
                True,
                f"\n[+] Quest '{quest_id}' started!\n    Check status with 'quests'\n",
                xp_gained=5,
            )
        elif action == "complete":
            if self.state.current_quest:
                old_quest = self.state.current_quest
                self.state.current_quest = None
                xp = 50  # Base XP
                return CommandResult(
                    True, f"\n[✓] Quest '{old_quest}' completed!\n    +{xp} XP\n", xp_gained=xp
                )
            return CommandResult(False, "No active quest.")
        elif action == "abandon":
            self.state.current_quest = None
            return CommandResult(True, "[!] Quest abandoned.")
        else:
            return CommandResult(False, f"Unknown action: {action}")

    def _cmd_achievements(self, _args: list[str]) -> CommandResult:
        """Show achievements."""
        try:
            from .achievements import (  # type: ignore[import-not-found]
                ACHIEVEMENTS, AchievementManager)

            mgr = AchievementManager()  # Uses default achievements file
            unlocked = mgr.get_unlocked()  # Returns list[Achievement]

            lines = ["\n╔══ ACHIEVEMENTS ══╗\n"]
            for aid, ach in list(ACHIEVEMENTS.items())[:10]:
                icon = "🏆" if aid in {u.id for u in unlocked} else "🔒"
                lines.append(f"  {icon} {ach.name} ({ach.points}pts)")
                lines.append(f"     {ach.description}")

            total = mgr.get_total_points()
            lines.append(f"\n  Total Points: {total}")
            return CommandResult(True, "\n".join(lines))
        except ImportError:
            return CommandResult(True, "\n[!] Achievement system not available.\n")

    def _cmd_leaderboard(self, _args: list[str]) -> CommandResult:
        """Show leaderboard."""
        try:
            from .achievements import \
                LeaderboardManager  # type: ignore[import-not-found]

            mgr = LeaderboardManager()
            top = mgr.get_top("general", 10)  # category first, then limit

            lines = ["\n╔══ LEADERBOARD ══╗\n"]
            medals = ["🥇", "🥈", "🥉"]
            for i, entry in enumerate(top):
                medal = medals[i] if i < 3 else f"#{i + 1}"
                highlight = "→" if entry.player_id == self.state.player_name else " "
                lines.append(f"  {highlight}{medal} {entry.player_id}: {entry.score}")

            return CommandResult(True, "\n".join(lines))
        except ImportError:
            return CommandResult(True, "\n[!] Leaderboard not available.\n")

    def _cmd_games(self, _args: list[str]) -> CommandResult:
        """List mini-games."""
        try:
            from .mini_games import \
                list_games  # type: ignore[import-not-found]

            games = list_games()  # Returns list[dict[str, str]]

            lines = ["\n╔══ MINI-GAMES ══╗\n"]
            for game_info in games:  # Iterate over list of dicts
                lines.append(f"  🎮 {game_info.get('name', game_info.get('id', 'Unknown'))}")
                lines.append(f"     {game_info.get('description', 'No description')}")

            lines.append("\nUse 'play <game>' to start.")
            return CommandResult(True, "\n".join(lines))
        except ImportError:
            return CommandResult(True, "\n[!] Mini-games not available.\n")

    def _cmd_play(self, args: list[str]) -> CommandResult:
        """Start a mini-game."""
        if not args:
            return CommandResult(False, "Usage: play <game_name>")

        game_name = args[0].lower()
        try:
            from .mini_games import \
                create_game  # type: ignore[import-not-found]

            game = create_game(game_name)
            if game:
                self.state.mode = TerminalMode.GAME
                # Game objects have start() method - check before calling
                intro = game.start() if hasattr(game, "start") else f"Starting {game_name}..."  # type: ignore[union-attr]
                return CommandResult(True, f"\n{intro}\n\nType your answer or 'exit' to quit.")
            else:
                return CommandResult(False, f"Unknown game: {game_name}")
        except ImportError:
            return CommandResult(True, f"\n[!] Cannot start game '{game_name}'.\n")

    def _cmd_faction(self, args: list[str]) -> CommandResult:
        """Faction commands."""
        factions = ["Digital Nomads", "Shadow Collective", "Binary Order", "Chaos Agents"]

        if not args:
            lines = ["\n╔══ FACTIONS ══╗\n"]
            for f in factions:
                current = " ← YOU" if f == self.state.faction else ""
                lines.append(f"  • {f}{current}")
            lines.append("\nUse 'faction join <name>' to join.")
            return CommandResult(True, "\n".join(lines))

        if args[0].lower() == "join" and len(args) > 1:
            faction_name = " ".join(args[1:])
            if any(f.lower() == faction_name.lower() for f in factions):
                self.state.faction = faction_name
                return CommandResult(True, f"\n[+] Joined faction: {faction_name}\n", xp_gained=25)

        return CommandResult(False, "Invalid faction command.")

    def _cmd_skills(self, _args: list[str]) -> CommandResult:
        """Show skills."""
        skills = [
            ("Hacking", 3, 10),
            ("Analysis", 2, 10),
            ("Programming", 4, 10),
            ("Security", 1, 10),
            ("Social Engineering", 0, 10),
        ]

        lines = ["\n╔══ SKILLS ══╗\n"]
        for name, level, max_lvl in skills:
            bar = "█" * level + "░" * (max_lvl - level)
            lines.append(f"  {name:20} [{bar}] {level}/{max_lvl}")

        return CommandResult(True, "\n".join(lines))

    def _cmd_inventory(self, _args: list[str]) -> CommandResult:
        """Show inventory."""
        items = [
            ("Keylogger v1.0", "Basic keystroke capture tool"),
            ("Firewall Bypass", "Circumvents basic security"),
            ("Decryption Key", "Unlocks encrypted files"),
        ]

        lines = ["\n╔══ INVENTORY ══╗\n"]
        for name, desc in items:
            lines.append(f"  📦 {name}")
            lines.append(f"     {desc}")

        return CommandResult(True, "\n".join(lines))

    def _cmd_hack(self, _args: list[str]) -> CommandResult:
        """Enter hacking mode."""
        self.state.mode = TerminalMode.HACKING
        self.prompt = "HACK>"
        return CommandResult(
            True,
            "\n[!] Hacking mode activated.\n    Available: scan, analyze, exploit\n    Type 'mode normal' to exit.",
        )

    def _cmd_scan(self, _args: list[str]) -> CommandResult:
        """Scan for targets."""
        targets = [
            ("192.168.1.1", "Router", "Low"),
            ("10.0.0.50", "Database Server", "High"),
            ("172.16.0.100", "Web Server", "Medium"),
        ]

        lines = ["\n[*] Scanning network...\n"]
        for ip, name, security in targets:
            lines.append(f"  [{security:6}] {ip:15} - {name}")

        return CommandResult(True, "\n".join(lines), xp_gained=5)

    def _cmd_analyze(self, args: list[str]) -> CommandResult:
        """Analyze a target."""
        if not args:
            return CommandResult(False, "Usage: analyze <target>")

        target = args[0]
        return CommandResult(
            True,
            f"\n[*] Analyzing {target}...\n"
            f"    Status: Online\n"
            f"    Vulnerabilities: 3 found\n"
            f"    Recommended: Buffer overflow exploit\n",
            xp_gained=10,
        )

    def _cmd_xp(self, _args: list[str]) -> CommandResult:
        """Show XP progress."""
        current = self.state.xp
        level = self.state.level
        next_lvl = self.XP_LEVELS.get(level + 1, 99999)
        prev_lvl = self.XP_LEVELS.get(level, 0)

        progress_in_level = current - prev_lvl
        needed = next_lvl - prev_lvl
        pct = (progress_in_level / max(needed, 1)) * 100

        bar_width = 20
        filled = int((pct / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)

        return CommandResult(
            True,
            f"\n  Level {level} [{bar}] Level {level + 1}\n"
            f"  XP: {current}/{next_lvl} ({pct:.1f}%)\n"
            f"  Next level: {next_lvl - current} XP needed\n",
        )

    def _cmd_daily(self, _args: list[str]) -> CommandResult:
        """Show daily challenges."""
        dailies = [
            ("Complete 3 quests", "100 XP", "1/3"),
            ("Win mini-game", "50 XP", "0/1"),
            ("Analyze 5 files", "75 XP", "2/5"),
        ]

        lines = ["\n╔══ DAILY CHALLENGES ══╗\n"]
        for task, reward, progress in dailies:
            done = "✓" if progress.startswith(progress.split("/")[1]) else "○"
            lines.append(f"  {done} {task} [{progress}] → {reward}")

        return CommandResult(True, "\n".join(lines))

    def _cmd_save(self, args: list[str]) -> CommandResult:
        """Save game state."""
        try:
            from src.games.game_state import (GameState, PlayerProgress,
                                              save_game)

            slot = args[0] if args else "quicksave"
            player = PlayerProgress(
                player_id=self.state.player_name, total_xp=self.state.xp, level=self.state.level
            )
            state = GameState(save_id=slot, save_name=f"Save: {slot}", player=player)

            save_game(state)
            return CommandResult(True, f"\n[✓] Game saved to slot '{slot}'\n")
        except ImportError:
            return CommandResult(True, "\n[!] Save system not available.\n")

    def _cmd_load(self, args: list[str]) -> CommandResult:
        """Load game state."""
        try:
            from src.games.game_state import load_game

            slot = args[0] if args else "quicksave"
            state = load_game(slot)

            if state:
                self.state.xp = state.player.total_xp
                self.state.level = state.player.level
                return CommandResult(True, f"\n[✓] Game loaded from slot '{slot}'\n")
            return CommandResult(False, f"Save slot '{slot}' not found.")
        except ImportError:
            return CommandResult(True, "\n[!] Save system not available.\n")

    def _cmd_mode(self, args: list[str]) -> CommandResult:
        """Switch terminal mode."""
        if not args:
            return CommandResult(
                True,
                f"Current mode: {self.state.mode.value}\nAvailable: normal, hacking, debug",
            )

        mode_name = args[0].lower()
        mode_map = {
            "normal": TerminalMode.NORMAL,
            "hacking": TerminalMode.HACKING,
            "debug": TerminalMode.DEBUG,
        }

        if mode_name in mode_map:
            self.state.mode = mode_map[mode_name]
            prompts = {
                TerminalMode.NORMAL: ">",
                TerminalMode.HACKING: "HACK>",
                TerminalMode.DEBUG: "DEBUG>",
            }
            self.prompt = prompts.get(self.state.mode, ">")
            return CommandResult(True, f"\n[*] Mode changed to: {mode_name}\n")

        return CommandResult(False, f"Unknown mode: {mode_name}")

    def _cmd_clear(self, _args: list[str]) -> CommandResult:
        """Clear screen."""
        print("\033[2J\033[H", end="")
        return CommandResult(True, "")

    def _cmd_exit(self, _args: list[str]) -> CommandResult:
        """Exit terminal."""
        self.running = False
        return CommandResult(True, "\n[*] Disconnecting...\n    Thanks for playing!\n")

    # === Core Methods ===

    def add_xp(self, amount: int) -> bool:
        """Add XP and check for level up."""
        self.state.xp += amount

        # Check level up
        next_level = self.state.level + 1
        if next_level in self.XP_LEVELS and self.state.xp >= self.XP_LEVELS[next_level]:
            self.state.level = next_level
            print(f"\n🎊 LEVEL UP! You are now level {next_level}!")
            return True
        return False

    def execute_command(self, input_str: str) -> CommandResult | None:
        """Execute a command string."""
        input_str = input_str.strip()
        if not input_str:
            return None

        parts = input_str.split()
        cmd = parts[0].lower()
        args = parts[1:]

        self.state.commands_executed += 1
        self.state.last_command = input_str

        if cmd in self.commands:
            handler = self.commands[cmd]["handler"]
            result = handler(args)

            if result.xp_gained > 0:
                self.add_xp(result.xp_gained)
                print(f"  ⭐ +{result.xp_gained} XP")

            return result
        else:
            return CommandResult(
                False,
                f"\n[!] Unknown command: {cmd}\n    Type 'help' for available commands.\n",
            )

    def run(self) -> None:
        """Run the interactive terminal loop."""
        self.running = True

        print(self.BANNER)
        print(f"  Welcome, {self.state.player_name}!")
        print("  Type 'help' for available commands.\n")

        while self.running:
            try:
                user_input = input(f"{self.prompt} ").strip()
                result = self.execute_command(user_input)

                if result and result.message:
                    print(result.message)

            except KeyboardInterrupt:
                print("\n\n[!] Use 'exit' to quit properly.")
            except EOFError:
                break

        print("\n[*] Session ended.")


# === Module-level convenience ===


def start_terminal(player_name: str = "Agent") -> None:
    """Start the CyberTerminal."""
    terminal = CyberTerminal(player_name)
    terminal.run()


def create_terminal(player_name: str = "Agent") -> CyberTerminal:
    """Create a CyberTerminal instance."""
    return CyberTerminal(player_name)


if __name__ == "__main__":
    # Demo mode - show a few commands without interactive loop
    print("CyberTerminal Demo Mode")
    print("=" * 40)

    terminal = CyberTerminal("TestAgent")

    # Execute demo commands
    demo_commands = ["status", "xp", "skills", "scan"]
    for cmd in demo_commands:
        print(f"\n> {cmd}")
        result = terminal.execute_command(cmd)
        if result:
            print(result.message)

    print("\n✅ CyberTerminal ready! Use start_terminal() for interactive mode.")

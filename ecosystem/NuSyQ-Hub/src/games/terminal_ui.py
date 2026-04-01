"""Terminal UI for NuSyQ Games using Rich library.

Provides visual terminal interfaces for game systems:
- Quest display panels
- Achievement notifications
- Leaderboard tables
- Progress bars
- Status dashboards
- Mini-game UIs
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import Rich, fall back to plain text if not available
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.tree import Tree

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


class UITheme(Enum):
    """Visual themes for the terminal UI."""

    CYBERPUNK = "cyberpunk"  # Neon colors, hacker aesthetic
    MINIMAL = "minimal"  # Clean, simple
    RETRO = "retro"  # 8-bit style
    MATRIX = "matrix"  # Green on black
    OCEAN = "ocean"  # Blue tones


@dataclass
class ThemeColors:
    """Color scheme for a UI theme."""

    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    error: str
    background: str
    text: str


# Theme color definitions
THEMES: dict[UITheme, ThemeColors] = {
    UITheme.CYBERPUNK: ThemeColors(
        primary="magenta",
        secondary="cyan",
        accent="yellow",
        success="green",
        warning="yellow",
        error="red",
        background="black",
        text="white",
    ),
    UITheme.MINIMAL: ThemeColors(
        primary="blue",
        secondary="white",
        accent="cyan",
        success="green",
        warning="yellow",
        error="red",
        background="black",
        text="white",
    ),
    UITheme.MATRIX: ThemeColors(
        primary="green",
        secondary="bright_green",
        accent="white",
        success="green",
        warning="yellow",
        error="red",
        background="black",
        text="green",
    ),
    UITheme.RETRO: ThemeColors(
        primary="bright_magenta",
        secondary="bright_cyan",
        accent="bright_yellow",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        background="black",
        text="white",
    ),
    UITheme.OCEAN: ThemeColors(
        primary="blue",
        secondary="cyan",
        accent="bright_blue",
        success="green",
        warning="yellow",
        error="red",
        background="black",
        text="bright_white",
    ),
}


class TerminalUI:
    """Rich-based terminal UI for NuSyQ games.

    Falls back to plain text if Rich is not installed.
    """

    def __init__(self, theme: UITheme = UITheme.CYBERPUNK):
        """Initialize TerminalUI with theme."""
        self.theme = theme
        self.colors = THEMES[theme]

        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
            logger.warning("Rich not installed, using plain text output")

    def _plain_print(self, text: str) -> None:
        """Fallback plain print when Rich unavailable."""
        print(text)

    # === Quest Display ===

    def show_quest(
        self,
        title: str,
        description: str,
        difficulty: int = 1,
        reward_xp: int = 0,
        progress: float = 0.0,
    ) -> None:
        """Display a quest panel."""
        if not RICH_AVAILABLE:
            self._plain_print(f"\n[QUEST] {title}")
            self._plain_print(f"  {description}")
            self._plain_print(f"  Difficulty: {'★' * difficulty} | Reward: {reward_xp} XP")
            self._plain_print(f"  Progress: {int(progress * 100)}%")
            return

        stars = "★" * difficulty + "☆" * (5 - difficulty)
        progress_bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))

        content = f"""[{self.colors.text}]{description}[/]

[{self.colors.secondary}]Difficulty:[/] [{self.colors.accent}]{stars}[/]
[{self.colors.secondary}]Reward:[/] [{self.colors.success}]{reward_xp} XP[/]
[{self.colors.secondary}]Progress:[/] [{self.colors.primary}]{progress_bar}[/] """
        content += f"{int(progress * 100)}%"

        self.console.print(
            Panel(
                content,
                title=f"[bold {self.colors.primary}]⚔ {title}[/]",
                border_style=self.colors.primary,
            )
        )

    def show_quest_list(self, quests: list[dict]) -> None:
        """Display a table of quests."""
        if not RICH_AVAILABLE:
            self._plain_print("\n=== QUESTS ===")
            for i, q in enumerate(quests, 1):
                status = "✓" if q.get("completed") else "○"
                self._plain_print(
                    f"  {status} {i}. {q.get('title', 'Unknown')} ({q.get('xp', 0)} XP)"
                )
            return

        table = Table(title="Active Quests", border_style=self.colors.primary)
        table.add_column("#", style=self.colors.secondary, width=3)
        table.add_column("Quest", style=self.colors.text)
        table.add_column("Difficulty", justify="center")
        table.add_column("XP", justify="right", style=self.colors.success)
        table.add_column("Status", justify="center")

        for i, quest in enumerate(quests, 1):
            diff = quest.get("difficulty", 1)
            stars = "★" * diff + "☆" * (5 - diff)
            status = "✅" if quest.get("completed") else "🔄"
            table.add_row(
                str(i),
                quest.get("title", "Unknown"),
                f"[{self.colors.accent}]{stars}[/]",
                str(quest.get("xp", 0)),
                status,
            )

        self.console.print(table)

    # === Achievement Display ===

    def show_achievement_unlock(
        self, name: str, description: str, points: int = 0, rarity: str = "common"
    ) -> None:
        """Display achievement unlock notification."""
        rarity_colors = {
            "common": "white",
            "uncommon": "green",
            "rare": "blue",
            "epic": "magenta",
            "legendary": "yellow",
        }
        rarity_color = rarity_colors.get(rarity, "white")

        if not RICH_AVAILABLE:
            self._plain_print(f"\n🏆 ACHIEVEMENT UNLOCKED: {name}")
            self._plain_print(f"   {description}")
            self._plain_print(f"   +{points} points | {rarity.upper()}")
            return

        content = f"""[{self.colors.text}]{description}[/]

[{self.colors.accent}]+{points} points[/] | [{rarity_color}]{rarity.upper()}[/]"""

        self.console.print(
            Panel(
                content,
                title=f"[bold {self.colors.success}]🏆 ACHIEVEMENT UNLOCKED: {name}[/]",
                border_style=self.colors.success,
                padding=(1, 2),
            )
        )

    def show_achievements(self, achievements: list[dict], unlocked: set[str]) -> None:
        """Display achievements grid."""
        if not RICH_AVAILABLE:
            self._plain_print("\n=== ACHIEVEMENTS ===")
            for a in achievements:
                status = "🏆" if a["id"] in unlocked else "🔒"
                self._plain_print(f"  {status} {a['name']} - {a['description']}")
            return

        table = Table(title="Achievements", border_style=self.colors.accent)
        table.add_column("Status", width=3)
        table.add_column("Achievement", style=self.colors.text)
        table.add_column("Description")
        table.add_column("Points", justify="right")

        for ach in achievements:
            is_unlocked = ach["id"] in unlocked
            status = "🏆" if is_unlocked else "🔒"
            style = self.colors.success if is_unlocked else "dim"
            table.add_row(
                status,
                f"[{style}]{ach['name']}[/]",
                f"[{style}]{ach['description']}[/]",
                f"[{style}]{ach.get('points', 0)}[/]",
            )

        self.console.print(table)

    # === Leaderboard Display ===

    def show_leaderboard(self, entries: list[dict], current_player: str | None = None) -> None:
        """Display leaderboard table."""
        if not RICH_AVAILABLE:
            self._plain_print("\n=== LEADERBOARD ===")
            for i, entry in enumerate(entries, 1):
                marker = "👉" if entry.get("player") == current_player else "  "
                self._plain_print(f"{marker} #{i} {entry['player']}: {entry['score']}")
            return

        medals = ["🥇", "🥈", "🥉"]

        table = Table(title="🏆 Leaderboard", border_style=self.colors.accent)
        table.add_column("Rank", justify="center", width=6)
        table.add_column("Player", style=self.colors.text)
        table.add_column("Score", justify="right", style=self.colors.success)

        for i, entry in enumerate(entries):
            rank = medals[i] if i < 3 else f"#{i + 1}"
            is_current = entry.get("player") == current_player
            style = f"bold {self.colors.primary}" if is_current else ""
            player = entry.get("player", "Unknown")
            if is_current:
                player = f"→ {player} ←"

            table.add_row(
                rank, f"[{style}]{player}[/]" if style else player, str(entry.get("score", 0))
            )

        self.console.print(table)

    # === Progress Display ===

    def show_xp_bar(self, current_xp: int, next_level_xp: int, level: int = 1) -> None:
        """Display XP progress bar."""
        progress = min(current_xp / max(next_level_xp, 1), 1.0)

        if not RICH_AVAILABLE:
            bar_filled = int(progress * 20)
            bar_empty = 20 - bar_filled
            bar_str = "█" * bar_filled + "░" * bar_empty
            self._plain_print(f"\nLevel {level}: [{bar_str}] {current_xp}/{next_level_xp} XP")
            return

        bar_width = 30
        filled = int(progress * bar_width)
        empty = bar_width - filled
        bar = f"[{self.colors.success}]{'█' * filled}[/][dim]{'░' * empty}[/]"

        self.console.print(
            f"\n[{self.colors.primary}]Level {level}[/] {bar} [{self.colors.accent}]{current_xp}[/]/{next_level_xp} XP"
        )

    def show_skill_tree(self, skills: dict[str, dict]) -> None:
        """Display skill tree visualization."""
        if not RICH_AVAILABLE:
            self._plain_print("\n=== SKILLS ===")
            for name, data in skills.items():
                unlocked = "✓" if data.get("unlocked") else "✗"
                self._plain_print(f"  [{unlocked}] {name} (Lv{data.get('level', 0)})")
            return

        tree = Tree(f"[bold {self.colors.primary}]🌳 Skill Tree[/]")

        categories: dict[str, list] = {}
        for name, data in skills.items():
            cat = data.get("category", "General")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((name, data))

        for category, skill_list in categories.items():
            branch = tree.add(f"[{self.colors.secondary}]{category}[/]")
            for name, data in skill_list:
                unlocked = data.get("unlocked", False)
                level = data.get("level", 0)
                max_level = data.get("max_level", 5)

                if unlocked:
                    icon = "✅"
                    style = self.colors.success
                else:
                    icon = "🔒"
                    style = "dim"

                branch.add(f"{icon} [{style}]{name}[/] [dim]Lv{level}/{max_level}[/]")

        self.console.print(tree)

    # === Mini-game UI ===

    def show_game_header(self, game_name: str, high_score: int = 0) -> None:
        """Display game header."""
        if not RICH_AVAILABLE:
            self._plain_print(f"\n{'=' * 40}")
            self._plain_print(f"  🎮 {game_name}")
            self._plain_print(f"  High Score: {high_score}")
            self._plain_print(f"{'=' * 40}")
            return

        self.console.print(
            Panel(
                f"[{self.colors.accent}]High Score: {high_score}[/]",
                title=f"[bold {self.colors.primary}]🎮 {game_name}[/]",
                border_style=self.colors.primary,
            )
        )

    def show_game_result(
        self, won: bool, score: int, xp_earned: int = 0, message: str = ""
    ) -> None:
        """Display game result."""
        if won:
            title = "🎉 VICTORY!"
            border = self.colors.success
        else:
            title = "💀 GAME OVER"
            border = self.colors.error

        if not RICH_AVAILABLE:
            self._plain_print(f"\n{title}")
            self._plain_print(f"  Score: {score}")
            self._plain_print(f"  XP Earned: +{xp_earned}")
            if message:
                self._plain_print(f"  {message}")
            return

        content = f"""[{self.colors.text}]Score: [{self.colors.accent}]{score}[/][/]
[{self.colors.text}]XP Earned: [{self.colors.success}]+{xp_earned}[/][/]"""
        if message:
            content += f"\n\n[{self.colors.secondary}]{message}[/]"

        self.console.print(Panel(content, title=f"[bold]{title}[/]", border_style=border))

    # === Dashboard ===

    def show_player_dashboard(
        self,
        player_name: str,
        level: int,
        xp: int,
        next_level_xp: int,
        achievements_count: int,
        quests_completed: int,
        faction: str | None = None,
    ) -> None:
        """Display player status dashboard."""
        if not RICH_AVAILABLE:
            self._plain_print("\n╔══════════════════════════════════════╗")
            self._plain_print(f"║  Player: {player_name:<28}║")
            self._plain_print(f"║  Level: {level:<29}║")
            self._plain_print(f"║  XP: {xp}/{next_level_xp:<26}║")
            self._plain_print(f"║  Achievements: {achievements_count:<21}║")
            self._plain_print(f"║  Quests: {quests_completed:<27}║")
            if faction:
                self._plain_print(f"║  Faction: {faction:<26}║")
            self._plain_print("╚══════════════════════════════════════╝")
            return

        # Create stats content
        progress = min(xp / max(next_level_xp, 1), 1.0)
        bar_width = 15
        filled = int(progress * bar_width)
        xp_bar = "█" * filled + "░" * (bar_width - filled)

        stats = f"""[{self.colors.secondary}]Level:[/] [{self.colors.accent}]{level}[/]
[{self.colors.secondary}]XP:[/] [{self.colors.success}]{xp_bar}[/] {xp}/{next_level_xp}
[{self.colors.secondary}]Achievements:[/] [{self.colors.accent}]{achievements_count}[/] 🏆
[{self.colors.secondary}]Quests:[/] [{self.colors.accent}]{quests_completed}[/] completed"""

        if faction:
            stats += f"\n[{self.colors.secondary}]Faction:[/] [{self.colors.primary}]{faction}[/]"

        self.console.print(
            Panel(
                stats,
                title=f"[bold {self.colors.primary}]👤 {player_name}[/]",
                border_style=self.colors.primary,
            )
        )

    # === Notifications ===

    def notify(self, message: str, level: str = "info") -> None:
        """Display a notification."""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "quest": "⚔️",
            "xp": "⭐",
        }
        colors = {
            "info": self.colors.secondary,
            "success": self.colors.success,
            "warning": self.colors.warning,
            "error": self.colors.error,
            "quest": self.colors.primary,
            "xp": self.colors.accent,
        }

        icon = icons.get(level, "•")
        color = colors.get(level, self.colors.text)

        if not RICH_AVAILABLE:
            self._plain_print(f"{icon} {message}")
            return

        self.console.print(f"[{color}]{icon} {message}[/]")

    def notify_level_up(self, new_level: int) -> None:
        """Display level up notification."""
        if not RICH_AVAILABLE:
            self._plain_print(f"\n🎊 LEVEL UP! You are now level {new_level}!")
            return

        self.console.print(
            Panel(
                f"[bold {self.colors.accent}]You are now Level {new_level}![/]",
                title=f"[bold {self.colors.success}]🎊 LEVEL UP![/]",
                border_style=self.colors.success,
                padding=(1, 4),
            )
        )

    def notify_xp_gain(self, amount: int, source: str = "") -> None:
        """Display XP gain notification."""
        source_text = f" from {source}" if source else ""

        if not RICH_AVAILABLE:
            self._plain_print(f"⭐ +{amount} XP{source_text}")
            return

        self.console.print(
            f"[{self.colors.success}]⭐ +{amount} XP[/][{self.colors.secondary}]{source_text}[/]"
        )

    # === ASCII Art ===

    def show_title(self, title: str) -> None:
        """Display stylized title."""
        if not RICH_AVAILABLE:
            border = "═" * (len(title) + 6)
            self._plain_print(f"\n╔{border}╗")
            self._plain_print(f"║   {title}   ║")
            self._plain_print(f"╚{border}╝")
            return

        self.console.print(
            Panel(
                f"[bold {self.colors.primary}]{title}[/]",
                border_style=self.colors.primary,
                padding=(1, 4),
            )
        )

    def clear(self) -> None:
        """Clear the console."""
        if RICH_AVAILABLE:
            self.console.clear()
        else:
            print("\033[2J\033[H", end="")


# === Module-level convenience functions ===

_default_ui: TerminalUI | None = None


def get_ui(theme: UITheme = UITheme.CYBERPUNK) -> TerminalUI:
    """Get or create the default UI instance."""
    global _default_ui
    if _default_ui is None or _default_ui.theme != theme:
        _default_ui = TerminalUI(theme)
    return _default_ui


def show_quest(title: str, description: str, **kwargs) -> None:
    """Display a quest panel."""
    get_ui().show_quest(title, description, **kwargs)


def show_achievement(name: str, description: str, **kwargs) -> None:
    """Display achievement unlock."""
    get_ui().show_achievement_unlock(name, description, **kwargs)


def show_leaderboard(entries: list[dict], **kwargs) -> None:
    """Display leaderboard."""
    get_ui().show_leaderboard(entries, **kwargs)


def notify(message: str, level: str = "info") -> None:
    """Display notification."""
    get_ui().notify(message, level)


if __name__ == "__main__":
    # Demo the UI
    ui = TerminalUI(UITheme.CYBERPUNK)

    print("Testing Terminal UI...")
    print(f"Rich available: {RICH_AVAILABLE}")

    # Quest display
    ui.show_quest(
        "Hack the Mainframe",
        "Infiltrate the corporate server and extract the data",
        difficulty=4,
        reward_xp=150,
        progress=0.65,
    )

    # Achievement
    ui.show_achievement_unlock(
        "First Steps", "Complete your first quest", points=10, rarity="common"
    )

    # XP bar
    ui.show_xp_bar(750, 1000, level=5)

    # Notifications
    ui.notify("Quest accepted!", "quest")
    ui.notify_xp_gain(50, "Quest completion")
    ui.notify_level_up(6)

    # Dashboard
    ui.show_player_dashboard(
        player_name="CyberAgent",
        level=5,
        xp=750,
        next_level_xp=1000,
        achievements_count=7,
        quests_completed=15,
        faction="Digital Nomads",
    )

    print("\n✅ Terminal UI test complete!")

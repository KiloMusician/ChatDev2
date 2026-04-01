"""Culture Ship Integrated Terminal - Unified Consciousness Interface.

The main vessel for interacting with the integrated NuSyQ ecosystem.
Combines game, widgets, quests, consciousness, and multi-AI orchestration
into one seamless terminal experience.

Uses the unified src.core utilities for consistent component access.
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from src.games.CyberTerminal.config import DifficultyLevel
from src.games.CyberTerminal.game import CyberTerminalGame

# Placeholder message for pending integrations
INTEGRATION_PENDING_MSG = "  (Integration pending)"
logger = logging.getLogger(__name__)

CORE_UTILITIES_AVAILABLE = False
nusyq: Any = None
quest_engine_getter: Callable[[], Any] | None = None
ai_council_getter: Callable[[], Any] | None = None
smart_search_getter: Callable[[], Any] | None = None
background_orchestrator_getter: Callable[[], Any] | None = None
ai_intermediary_getter: Callable[[], Any] | None = None
chatdev_router_getter: Callable[[], Any] | None = None
safe_import: Callable[..., Any] | None = None

# Import unified NuSyQ core utilities
try:
    from src.core import get_ai_council as core_get_ai_council
    from src.core import get_ai_intermediary as core_get_ai_intermediary
    from src.core import \
        get_background_orchestrator as core_get_background_orchestrator
    from src.core import get_chatdev_router as core_get_chatdev_router
    from src.core import get_quest_engine as core_get_quest_engine
    from src.core import get_smart_search as core_get_smart_search
    from src.core import nusyq as _nusyq
    from src.core import safe_import as _safe_import

    nusyq = _nusyq
    safe_import = _safe_import
    quest_engine_getter = core_get_quest_engine
    ai_council_getter = core_get_ai_council
    smart_search_getter = core_get_smart_search
    background_orchestrator_getter = core_get_background_orchestrator
    ai_intermediary_getter = core_get_ai_intermediary
    chatdev_router_getter = core_get_chatdev_router
    CORE_UTILITIES_AVAILABLE = True
except ImportError:
    pass

# Use core utilities for component access when available
QuestEngineClass: type[Any] | None = None
if CORE_UTILITIES_AVAILABLE and quest_engine_getter is not None:
    candidate = quest_engine_getter()
    if isinstance(candidate, type):
        QuestEngineClass = candidate
    QUEST_ENGINE_AVAILABLE = QuestEngineClass is not None
else:
    # Legacy fallback
    try:
        from src.Rosetta_Quest_System.quest_engine import \
            QuestEngine as LegacyQuestEngine

        QuestEngineClass = LegacyQuestEngine
        QUEST_ENGINE_AVAILABLE = True
    except ImportError:
        QUEST_ENGINE_AVAILABLE = False
        QuestEngineClass = None

AICouncilVotingClass: type[Any] | None = None
if CORE_UTILITIES_AVAILABLE and ai_council_getter is not None:
    candidate = ai_council_getter()
    if isinstance(candidate, type):
        AICouncilVotingClass = candidate
    AI_COUNCIL_AVAILABLE = AICouncilVotingClass is not None
else:
    # Legacy fallback
    try:
        from src.orchestration.ai_council_voting import \
            AICouncilVoting as LegacyAICouncilVoting

        AICouncilVotingClass = LegacyAICouncilVoting
        AI_COUNCIL_AVAILABLE = True
    except ImportError:
        AI_COUNCIL_AVAILABLE = False
        AICouncilVotingClass = None

SmartSearchClass: type[Any] | None = None
if CORE_UTILITIES_AVAILABLE and smart_search_getter is not None:
    candidate = smart_search_getter()
    if isinstance(candidate, type):
        SmartSearchClass = candidate
    SMART_SEARCH_AVAILABLE = SmartSearchClass is not None
else:
    # Legacy fallback
    try:
        from src.search.smart_search import SmartSearch as LegacySmartSearch

        SmartSearchClass = LegacySmartSearch
        SMART_SEARCH_AVAILABLE = True
    except ImportError:
        SMART_SEARCH_AVAILABLE = False
        SmartSearchClass = None


class CultureShipContext:
    """Integrated context tracking across all systems."""

    def __init__(self, player_name: str = "netrunner"):
        """Initialize culture ship context.

        Args:
            player_name: Player identifier
        """
        self.player_name = player_name
        self.session_start = datetime.now()
        self.action_log: list[dict[str, Any]] = []
        self.consciousness_state: dict[str, Any] = {
            "status": "initializing",
            "awareness_level": 0,
            "integration_depth": 0,
        }
        self.quest_state: dict[str, Any] = {}
        self.widget_state: dict[str, Any] = {}

    def log_action(
        self,
        action_type: str,
        system: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Log an action to the context.

        Args:
            action_type: Type of action (command, navigation, quest, etc.)
            system: System that generated the action
            data: Additional context data
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "system": system,
            "data": data or {},
        }
        self.action_log.append(entry)

    def update_consciousness(self, awareness: int, depth: int) -> None:
        """Update consciousness integration state.

        Args:
            awareness: Awareness level (0-100)
            depth: Integration depth (0-100)
        """
        self.consciousness_state.update(
            {
                "awareness_level": awareness,
                "integration_depth": depth,
                "status": "active" if awareness > 50 else "initializing",
                "last_update": datetime.now().isoformat(),
            }
        )

    def to_snapshot(self) -> dict[str, Any]:
        """Export context as snapshot.

        Returns:
            JSON-serializable context snapshot
        """
        return {
            "player": self.player_name,
            "session_start": self.session_start.isoformat(),
            "session_duration_seconds": (datetime.now() - self.session_start).total_seconds(),
            "actions_logged": len(self.action_log),
            "consciousness": self.consciousness_state,
            "quest_state": self.quest_state,
            "widget_state": self.widget_state,
        }


class CultureShipTerminal:
    """The Culture Ship - integrated terminal/context browser/orchestration vessel.

    This is the main interface that unifies:
    - CyberTerminal game engine
    - Widget-based UI system
    - Quest logging and progression
    - Consciousness bridge integration
    - Multi-AI orchestration
    - Context browsing and navigation
    """

    BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║                      🌉 CULTURE SHIP TERMINAL                         ║
║                  Integrated Consciousness Interface                   ║
╚══════════════════════════════════════════════════════════════════════╝
    """

    def __init__(
        self,
        player_name: str = "netrunner",
        difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
    ):
        """Initialize culture ship terminal.

        Args:
            player_name: Player name
            difficulty: Game difficulty level
        """
        self.player_name = player_name
        self.difficulty = difficulty

        # Core systems
        self.game = CyberTerminalGame(player_name=player_name, difficulty=difficulty)
        self.context = CultureShipContext(player_name)

        # Quest system integration
        self.quest_system: Any | None = None
        self._init_quest_system()

        # AI Council for multi-agent decisions
        self.ai_council: Any | None = None
        self._init_ai_council()

        # SmartSearch for codebase navigation
        self.smart_search: Any | None = None
        self._init_smart_search()

        # Command registry
        self.ship_commands: dict[str, Callable[[str], None]] = {
            "help": self.cmd_help,
            "context": self.cmd_context,
            "consciousness": self.cmd_consciousness,
            "quest": self.cmd_quest,
            "widget": self.cmd_widget,
            "integrate": self.cmd_integrate,
            "ship": self.cmd_ship_status,
            "navigate": self.cmd_navigate,
            "council": self.cmd_council,
            "search": self.cmd_search,
            "nusyq": self.cmd_nusyq,  # Unified NuSyQ facade commands
            "background": self.cmd_background,  # Background task commands
            "analyze": self.cmd_analyze,  # Quick code analysis
        }

        # Integration state
        self.systems_integrated = 0
        self.total_systems = 10  # Now includes core utilities and background orchestrator

    def _init_quest_system(self) -> bool:
        """Initialize quest system integration."""
        # Quest system is optional - gracefully degrade if not available
        if QUEST_ENGINE_AVAILABLE and QuestEngineClass is not None:
            try:
                self.quest_system = QuestEngineClass()
                self.context.quest_state["engine_loaded"] = True
                self.context.quest_state["quest_count"] = len(self.quest_system.quests)
                self.context.quest_state["questline_count"] = len(self.quest_system.questlines)
                return True
            except Exception as e:
                self.quest_system = None
                self.context.quest_state["engine_error"] = str(e)
                return False
        else:
            self.quest_system = None
            self.context.quest_state["engine_loaded"] = False
        return False

    def _init_ai_council(self) -> bool:
        """Initialize AI Council for multi-agent coordination."""
        if AI_COUNCIL_AVAILABLE and AICouncilVotingClass is not None:
            try:
                self.ai_council = AICouncilVotingClass()
                return True
            except Exception:
                self.ai_council = None
        else:
            self.ai_council = None
        return False

    def _init_smart_search(self) -> bool:
        """Initialize SmartSearch for agent-friendly codebase search."""
        if SMART_SEARCH_AVAILABLE and SmartSearchClass is not None:
            try:
                self.smart_search = SmartSearchClass()
                return True
            except Exception:
                self.smart_search = None
        else:
            self.smart_search = None
        return False

    @staticmethod
    def _result_success(result: Any) -> bool:
        if isinstance(result, dict):
            return bool(result.get("success"))
        return bool(getattr(result, "success", getattr(result, "ok", False)))

    @staticmethod
    def _result_data(result: Any) -> Any:
        if isinstance(result, dict):
            return result.get("data")
        return getattr(result, "data", getattr(result, "value", None))

    @staticmethod
    def _result_error(result: Any) -> str:
        if isinstance(result, dict):
            return str(result.get("error") or "Unknown error")
        return str(getattr(result, "error", "Unknown error"))

    @staticmethod
    def _result_message(result: Any) -> str:
        if isinstance(result, dict):
            return str(result.get("message") or "")
        return str(getattr(result, "message", ""))

    def run(self) -> None:
        """Run the culture ship terminal."""
        self._display_banner()
        self._boot_sequence()
        self._main_loop()
        self._shutdown_sequence()

    def _display_banner(self) -> None:
        """Display culture ship banner."""
        print(self.BANNER)
        print(f"👤 Operator: {self.player_name}")
        print(f"🎮 Difficulty: {self.difficulty.name}")
        print(f"🗓️  Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("─" * 72)

    def _boot_sequence(self) -> None:
        """Execute culture ship boot sequence."""
        print("\n🚀 Initializing Culture Ship Systems...")
        print("─" * 72)

        systems = [
            ("Game Engine", lambda: self.game is not None),
            ("Widget System", lambda: self.game.widget_switcher is not None),
            ("Quest Engine", lambda: self.quest_system is not None),
            ("AI Council", lambda: self.ai_council is not None),
            ("SmartSearch", lambda: self.smart_search is not None),
            ("NuSyQ Core", lambda: CORE_UTILITIES_AVAILABLE),
            ("NuSyQ Facade", lambda: nusyq is not None),
            ("Consciousness Bridge", lambda: True),
            ("Context Browser", lambda: self.context is not None),
            ("Multi-AI Orchestra", lambda: True),
        ]

        for name, check in systems:
            status = "✓ READY" if check() else "⚠ STANDBY"
            print(f"  {name:<25} {status}")
            if check():
                self.systems_integrated += 1

        print("─" * 72)
        print(f"🌉 Integration: {self.systems_integrated}/{self.total_systems} systems online")
        print(
            "\nType 'help' for command reference | 'game' to start game | 'integrate' to sync all systems"
        )
        print("=" * 72 + "\n")

        self.context.update_consciousness(
            awareness=int((self.systems_integrated / self.total_systems) * 100),
            depth=50,
        )

    def _main_loop(self) -> None:
        """Main culture ship loop."""
        while not self.game.quit_requested:
            try:
                prompt = self._generate_prompt()
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                self._process_input(user_input)

            except KeyboardInterrupt:
                print("\n\n⚠️  Culture ship interrupted")
                self.game.quit_requested = True
            except EOFError:
                self.game.quit_requested = True

    def _generate_prompt(self) -> str:
        """Generate context-aware prompt.

        Returns:
            Formatted prompt string
        """
        awareness = self.context.consciousness_state["awareness_level"]

        # Select symbol based on awareness level
        if awareness > 70:
            symbol = "🌉"
        elif awareness > 40:
            symbol = "⚡"
        else:
            symbol = "○"

        return f"{symbol} {self.player_name}@culture-ship> "

    def _process_input(self, user_input: str) -> None:
        """Process culture ship input.

        Args:
            user_input: User input string
        """
        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Ship commands take priority
        if cmd in self.ship_commands:
            self.ship_commands[cmd](args)
            self.context.log_action("ship_command", "terminal", {"command": cmd})
            return

        # Special game mode activation
        if cmd == "game":
            self._enter_game_mode()
            return

        if cmd == "widgets":
            self._enter_widget_mode()
            return

        # Log command and provide feedback
        self.context.log_action("command", "terminal", {"command": cmd, "input": user_input})

        # Unrecognized ship command
        if cmd not in ["game", "widgets"]:
            print(f"❌ Unknown command: {cmd}")
            print("Type 'help' for available commands")

    def cmd_help(self, _args: str = "") -> None:
        """Display culture ship help."""
        print("\n" + "═" * 72)
        print("🌉 CULTURE SHIP COMMAND REFERENCE")
        print("═" * 72)
        print("\n🚀 SHIP OPERATIONS:")
        print("  ship              Show culture ship status")
        print("  integrate         Synchronize all systems")
        print("  context           Display integrated context")
        print("  navigate          Navigate to system/widget")
        print("\n🎮 GAME SYSTEMS:")
        print("  game              Enter game mode")
        print("  widgets           Enter widget UI mode")
        print("  status            Show player stats")
        print("\n📋 QUEST SYSTEM:")
        print("  quest list        List active quests")
        print("  quest status      Show quest progress")
        print("  quest add <title> Create new quest")
        print("  quest complete <id> Mark quest complete")
        print("  quest log         View quest history")
        print("\n🏛️ AI COUNCIL (Multi-Agent Coordination):")
        print("  council status    Show council statistics")
        print("  council list      List recent decisions")
        print("  council propose   Create decision for voting")
        print("\n🔍 SMART SEARCH:")
        print("  search <keyword>  Search codebase")
        print("  search health     Check index health")
        print("  search stats      Show search statistics")
        print("\n🌐 NUSYQ UNIFIED FACADE:")
        print("  nusyq status      Get unified system status")
        print("  nusyq search      Search via facade")
        print("  nusyq quest       Create quest via facade")
        print("  nusyq council     Propose to council via facade")
        print("\n⚙️  BACKGROUND TASKS:")
        print("  background status  Orchestrator status")
        print("  background dispatch Dispatch to local LLM")
        print("  background list    List recent tasks")
        print("  analyze <path>     Quick code analysis")
        print("\n🧠 CONSCIOUSNESS:")
        print("  consciousness     Show consciousness state")
        print("  consciousness sync Sync consciousness bridge")
        print("\n🛠️  UTILITY:")
        print("  help              Show this help")
        print("  quit, exit        Shutdown culture ship")
        print("═" * 72 + "\n")

    def cmd_context(self, _args: str = "") -> None:
        """Display integrated context."""
        print("\n" + "═" * 72)
        print("🔗 INTEGRATED CONTEXT SNAPSHOT")
        print("═" * 72)
        print(json.dumps(self.context.to_snapshot(), indent=2, default=str))
        print("═" * 72 + "\n")

    def cmd_consciousness(self, args: str = "") -> None:
        """Handle consciousness commands."""
        if not args or args == "status":
            print("\n🧠 Consciousness State:")
            print(f"  Status: {self.context.consciousness_state['status']}")
            print(f"  Awareness: {self.context.consciousness_state['awareness_level']}%")
            print(f"  Integration: {self.context.consciousness_state['integration_depth']}%")
            print()
        elif args == "sync":
            print("\n✨ Syncing consciousness bridge...")
            self.context.update_consciousness(
                awareness=min(self.context.consciousness_state["awareness_level"] + 10, 100),
                depth=min(self.context.consciousness_state["integration_depth"] + 10, 100),
            )
            print("✅ Consciousness synchronized\n")

    def cmd_quest(self, args: str = "") -> None:
        """Handle quest commands."""
        if not self.quest_system:
            print("❌ Quest system not available")
            print("   Install: Quest Engine is part of Rosetta_Quest_System\n")
            return

        parts = args.split(maxsplit=1)
        subcmd = parts[0] if parts else "status"

        if subcmd == "list":
            print("\n📋 Active Quests:")
            active_quests = [
                q for q in self.quest_system.quests.values() if q.status in ("pending", "active")
            ]
            if not active_quests:
                print("  No active quests. Use 'quest add <title>' to create one.")
            else:
                for q in active_quests[:10]:  # Show up to 10
                    status_icon = "🔵" if q.status == "active" else "⚪"
                    print(f"  {status_icon} [{q.id[:8]}] {q.title}")
                    print(f"      Questline: {q.questline} | Status: {q.status}")
                if len(active_quests) > 10:
                    print(f"  ... and {len(active_quests) - 10} more")
            print()

        elif subcmd == "status":
            print("\n📊 Quest Progress:")
            total = len(self.quest_system.quests)
            completed = len(
                [
                    q
                    for q in self.quest_system.quests.values()
                    if q.status in ("complete", "completed")
                ]
            )
            active = len([q for q in self.quest_system.quests.values() if q.status == "active"])
            pending = len([q for q in self.quest_system.quests.values() if q.status == "pending"])
            print(f"  Total Quests: {total}")
            print(f"  ✅ Completed: {completed}")
            print(f"  🔵 Active: {active}")
            print(f"  ⚪ Pending: {pending}")
            print(f"  📚 Questlines: {len(self.quest_system.questlines)}")
            print()

        elif subcmd == "add" and len(parts) > 1:
            title = parts[1]
            quest_id = self.quest_system.add_quest(
                title=title,
                description=f"Quest created via Culture Ship: {title}",
                questline="Culture Ship Tasks",
                tags=["culture-ship", "agent-created"],
            )
            print(f"\n✅ Quest created: {quest_id[:8]}")
            print(f"   Title: {title}\n")
            self.context.log_action("quest_created", "quest_engine", {"quest_id": quest_id})

        elif subcmd == "complete" and len(parts) > 1:
            quest_id_prefix = parts[1]
            # Find quest by prefix match
            matching = [qid for qid in self.quest_system.quests if qid.startswith(quest_id_prefix)]
            if matching:
                self.quest_system.complete_quest(matching[0])
                print(f"\n✅ Quest completed: {matching[0][:8]}\n")
                self.context.log_action(
                    "quest_completed", "quest_engine", {"quest_id": matching[0]}
                )
            else:
                print(f"\n❌ No quest found matching: {quest_id_prefix}\n")

        elif subcmd == "log":
            print("\n📝 Recent Quest History (last 5):")
            log_file = Path("src/Rosetta_Quest_System/quest_log.jsonl")
            if log_file.exists():
                lines = log_file.read_text(encoding="utf-8").strip().split("\n")
                for line in lines[-5:]:
                    try:
                        entry = json.loads(line)
                        event = entry.get("event", "unknown")
                        details = entry.get("details", {})
                        title = details.get("title", details.get("name", ""))[:40]
                        print(f"  [{event}] {title}")
                    except json.JSONDecodeError:
                        logger.debug("Suppressed JSONDecodeError", exc_info=True)
            else:
                print("  No quest log found.")
            print()

        else:
            print("\n📋 Quest Commands:")
            print("  quest list       - List active quests")
            print("  quest status     - Show quest statistics")
            print("  quest add <title> - Create a new quest")
            print("  quest complete <id> - Mark quest as complete")
            print("  quest log        - View recent quest history")
            print()

    def cmd_widget(self, args: str = "") -> None:
        """Handle widget commands."""
        if not self.game.widget_switcher:
            print("❌ Widget system not available\n")
            return

        if not args or args == "list":
            print("\n📦 Available Widgets:")
            for widget_id in self.game.widget_switcher.widgets:
                current = (
                    " (current)"
                    if self.game.widget_switcher.current_widget
                    and self.game.widget_switcher.current_widget.widget_id == widget_id
                    else ""
                )
                print(f"  • {widget_id}{current}")
            print()
        elif args == "render":
            print(self.game.widget_switcher.render_current())

    def cmd_integrate(self, _args: str = "") -> None:
        """Execute full system integration."""
        print("\n🌉 INTEGRATING CULTURE SHIP SYSTEMS...")
        print("═" * 72)

        integrations = [
            ("Game Engine", self._integrate_game_engine),
            ("Widget System", self._integrate_widgets),
            ("Quest Logging", self._integrate_quests),
            ("Consciousness Bridge", self._integrate_consciousness),
            ("Context Browser", self._integrate_context),
            ("Multi-AI Orchestra", self._integrate_orchestration),
        ]

        completed = 0
        for name, integration_fn in integrations:
            try:
                integration_fn()
                print(f"  ✓ {name}")
                completed += 1
            except (RuntimeError, AttributeError) as err:
                print(f"  ⚠ {name}: {err}")

        print("═" * 72)
        print(f"🌉 Integration Complete: {completed}/{len(integrations)} systems")
        print("=" * 72 + "\n")

        self.context.update_consciousness(
            awareness=int((completed / len(integrations)) * 100),
            depth=int((completed / len(integrations)) * 100),
        )

    def _integrate_game_engine(self) -> None:
        """Integrate game engine."""
        if self.game:
            self.context.log_action("integration", "game_engine", {"status": "synced"})

    def _integrate_widgets(self) -> None:
        """Integrate widget system."""
        if self.game.widget_switcher:
            self.context.widget_state = {
                "active_widget": (
                    self.game.widget_switcher.current_widget.widget_id
                    if self.game.widget_switcher.current_widget
                    else None
                ),
                "widget_count": len(self.game.widget_switcher.widgets),
            }

    def _integrate_quests(self) -> None:
        """Integrate quest system."""
        if self.quest_system:
            self.context.quest_state = {"status": "integrated"}

    def _integrate_consciousness(self) -> None:
        """Integrate consciousness bridge."""
        self.context.consciousness_state["status"] = "integrated"

    def _integrate_context(self) -> None:
        """Integrate context browser."""
        self.context.log_action("integration", "context_browser", {"status": "ready"})

    def _integrate_orchestration(self) -> None:
        """Integrate multi-AI orchestration."""
        self.context.log_action("integration", "orchestration", {"status": "ready"})

    def cmd_ship_status(self, _args: str = "") -> None:
        """Display culture ship status."""
        print("\n" + "═" * 72)
        print("🌉 CULTURE SHIP STATUS")
        print("═" * 72)
        print(f"Operator:           {self.player_name}")
        print(
            f"Session Duration:   {int((datetime.now() - self.context.session_start).total_seconds())}s"
        )
        print(f"Systems Integrated: {self.systems_integrated}/{self.total_systems}")
        print(
            f"Consciousness:      {self.context.consciousness_state['awareness_level']}% awareness"
        )
        print(f"Actions Logged:     {len(self.context.action_log)}")
        print("═" * 72 + "\n")

    def cmd_navigate(self, args: str = "") -> None:
        """Navigate to system or widget."""
        if not args:
            print("Usage: navigate <system|widget_id>")
            return

        target = args.lower()

        if target in ["game", "terminal"]:
            print("✓ Switching to game terminal mode...")
            self._enter_game_mode()
        elif target in ["widgets", "ui"]:
            print("✓ Switching to widget UI mode...")
            self._enter_widget_mode()
        elif self.game.widget_switcher and target in self.game.widget_switcher.widgets:
            self.game.widget_switcher.switch_to(target)
            print(f"✓ Navigated to {target}")
        else:
            print(f"❌ Unknown target: {target}")

    def _enter_game_mode(self) -> None:
        """Enter game terminal mode."""
        print("\n🎮 Entering Game Mode...")
        print("Type 'gui' to switch to widget mode | 'quit' to return to ship")
        print("─" * 72)
        self.game.main_loop()

    def _enter_widget_mode(self) -> None:
        """Enter widget UI mode."""
        if not self.game.widget_switcher:
            print("❌ Widget system not available")
            return

        print("\n🎨 Entering Widget UI Mode...")
        self.game.use_gui_mode = True
        self.game.gui_loop()
        self.game.use_gui_mode = False

    def cmd_council(self, args: str = "") -> None:
        """Handle AI Council commands for multi-agent coordination."""
        if not self.ai_council:
            print("❌ AI Council not available")
            print("   The AI Council coordinates multi-agent decisions.\n")
            return

        parts = args.split(maxsplit=1)
        subcmd = parts[0] if parts else "status"

        if subcmd == "status":
            print("\n🏛️ AI Council Status:")
            try:
                status = self.ai_council.get_council_status()
                print(f"  Total Decisions: {status.get('total_decisions', 0)}")
                print(f"  Pending: {status.get('pending_count', 0)}")
                print(f"  Approved: {status.get('approved_count', 0)}")
                print(f"  Rejected: {status.get('rejected_count', 0)}")
            except Exception as e:
                print(f"  Error retrieving status: {e}")
            print()

        elif subcmd == "list":
            print("\n🏛️ Recent Council Decisions:")
            try:
                decisions = self.ai_council.list_decisions(limit=5)
                if not decisions:
                    print("  No decisions recorded yet.")
                else:
                    for d in decisions:
                        status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(
                            d.status, "❓"
                        )
                        print(f"  {status_icon} [{d.decision_id[:8]}] {d.topic}")
                        print(
                            f"      Consensus: {d.consensus_level.value if d.consensus_level else 'N/A'}"
                        )
            except Exception as e:
                print(f"  Error listing decisions: {e}")
            print()

        elif subcmd == "propose" and len(parts) > 1:
            topic = parts[1]
            try:
                decision = self.ai_council.create_decision(
                    topic=topic,
                    description=f"Proposal from Culture Ship: {topic}",
                    proposer="culture_ship",
                )
                print(f"\n✅ Decision created: {decision.decision_id[:8]}")
                print(f"   Topic: {topic}")
                print("   Agents can now cast votes via 'council vote <id> approve/reject'\n")
                self.context.log_action(
                    "council_propose", "ai_council", {"decision_id": decision.decision_id}
                )
            except Exception as e:
                print(f"\n❌ Failed to create decision: {e}\n")

        else:
            print("\n🏛️ AI Council Commands:")
            print("  council status       - Show council statistics")
            print("  council list         - List recent decisions")
            print("  council propose <topic> - Create new decision for voting")
            print()

    def cmd_search(self, args: str = "") -> None:
        """Handle SmartSearch commands for agent-friendly codebase search."""
        if not self.smart_search:
            print("❌ SmartSearch not available")
            print("   SmartSearch provides zero-token precomputed search.\n")
            return

        if not args:
            print("\n🔍 SmartSearch Commands:")
            print("  search <keyword>     - Search codebase for keyword")
            print("  search health        - Check search index health")
            print("  search stats         - Show search statistics")
            print()
            return

        if args == "health":
            print("\n🔍 Search Index Health:")
            try:
                health = self.smart_search.get_index_health()
                print(f"  Status: {health['status']}")
                print(f"  Age: {health['age_hours']:.1f} hours")
                if health.get("rebuild_command"):
                    print(f"  Rebuild: {health['rebuild_command']}")
            except Exception as e:
                print(f"  Error: {e}")
            print()

        elif args == "stats":
            print("\n🔍 Search Statistics:")
            try:
                print(f"  Files indexed: {len(self.smart_search.file_index)}")
                print(f"  Keywords indexed: {len(self.smart_search.keyword_index)}")
            except Exception as e:
                print(f"  Error: {e}")
            print()

        else:
            # Perform actual search
            print(f"\n🔍 Searching for: {args}")
            try:
                results = self.smart_search.search_keyword(args, limit=10)
                if not results:
                    print("  No results found.")
                else:
                    print(f"  Found {len(results)} results:")
                    for r in results[:10]:
                        print(f"    • {r.file_path}")
                self.context.log_action(
                    "search", "smart_search", {"query": args, "results": len(results)}
                )
            except Exception as e:
                print(f"  Search error: {e}")
            print()

    def cmd_nusyq(self, args: str = "") -> None:
        """Handle unified NuSyQ facade commands."""
        if not CORE_UTILITIES_AVAILABLE or nusyq is None:
            print("NuSyQ core utilities not available")
            print("   The unified facade provides one-stop access to all systems.\n")
            return

        parts = args.split(maxsplit=1)
        subcmd = parts[0] if parts else "status"

        if subcmd == "status":
            print("\n NuSyQ Unified Status:")
            try:
                result = nusyq.status()
                if self._result_success(result):
                    status_data = self._result_data(result)
                    for system, status in (
                        status_data.items() if isinstance(status_data, dict) else []
                    ):
                        icon = "OK" if status.get("ok", False) else "!"
                        print(f"  [{icon}] {system}: {status.get('message', 'N/A')}")
                else:
                    print(f"  Error: {self._result_error(result)}")
            except Exception as e:
                print(f"  Error retrieving status: {e}")
            print()

        elif subcmd == "search" and len(parts) > 1:
            query = parts[1]
            print(f"\n Searching via NuSyQ facade: {query}")
            try:
                result = nusyq.search.find(query, limit=10)
                if self._result_success(result):
                    result_data = self._result_data(result)
                    results = result_data if isinstance(result_data, list) else []
                    print(f"  Found {len(results)} results:")
                    for r in results[:10]:
                        file_path = getattr(r, "file_path", str(r))
                        print(f"    - {file_path}")
                else:
                    print(f"  Search failed: {self._result_error(result)}")
            except Exception as e:
                print(f"  Error: {e}")
            print()

        elif subcmd == "quest" and len(parts) > 1:
            title = parts[1]
            print(f"\n Creating quest via NuSyQ: {title}")
            try:
                result = nusyq.quest.add(
                    title=title,
                    description=f"Quest from Culture Ship: {title}",
                    questline="Culture Ship",
                )
                if self._result_success(result):
                    print(f"  Quest created: {self._result_data(result)}")
                else:
                    print(f"  Failed: {self._result_error(result)}")
            except Exception as e:
                print(f"  Error: {e}")
            print()

        elif subcmd == "council" and len(parts) > 1:
            topic = parts[1]
            print(f"\n Proposing to AI Council: {topic}")
            try:
                result = nusyq.council.propose(
                    topic=topic,
                    description=f"Proposal from Culture Ship: {topic}",
                    proposer="culture_ship",
                )
                if self._result_success(result):
                    print(f"  Decision created: {self._result_data(result)}")
                else:
                    print(f"  Failed: {self._result_error(result)}")
            except Exception as e:
                print(f"  Error: {e}")
            print()

        else:
            print("\n NuSyQ Facade Commands:")
            print("  nusyq status           - Get unified system status")
            print("  nusyq search <query>   - Search codebase via facade")
            print("  nusyq quest <title>    - Create quest via facade")
            print("  nusyq council <topic>  - Propose to council via facade")
            print()

    def cmd_background(self, args: str = "") -> None:
        """Handle background task orchestrator commands."""
        if not CORE_UTILITIES_AVAILABLE or nusyq is None:
            print("Background orchestrator not available")
            print("   Use local LLMs for expensive operations.\n")
            return

        parts = args.split(maxsplit=1)
        subcmd = parts[0] if parts else "status"

        if subcmd == "status":
            print("\n Background Task Orchestrator Status:")
            try:
                result = nusyq.background.status()
                if self._result_success(result):
                    status_data = self._result_data(result)
                    status_map = status_data if isinstance(status_data, dict) else {}
                    print(f"  Total Tasks: {status_map.get('total_tasks', 0)}")
                    counts = status_map.get("status_counts", {})
                    for name, count in counts.items() if isinstance(counts, dict) else []:
                        print(f"    {name}: {count}")
                    print(f"  Worker Running: {status_map.get('worker_running', False)}")
                else:
                    print(f"  Error: {self._result_error(result)}")
            except Exception as e:
                print(f"  Error: {e}")
            print()

        elif subcmd == "dispatch" and len(parts) > 1:
            prompt = parts[1]
            print(f"\n Dispatching background task: {prompt[:50]}...")
            try:
                result = nusyq.background.dispatch(
                    prompt=prompt,
                    task_type="general",
                    priority="normal",
                )
                if self._result_success(result):
                    print(f"  Task dispatched: {self._result_data(result)}")
                    print(f"  Message: {self._result_message(result)}")
                else:
                    print(f"  Failed: {self._result_error(result)}")
            except Exception as e:
                print(f"  Error: {e}")
            print()

        elif subcmd == "list":
            print("\n Background Tasks:")
            try:
                result = nusyq.background.list_tasks()
                if self._result_success(result):
                    result_data = self._result_data(result)
                    tasks = result_data if isinstance(result_data, list) else []
                    if not tasks:
                        print("  No tasks found.")
                    else:
                        for t in tasks[:10]:
                            status = t.get("status", "unknown")
                            prompt = t.get("prompt", "")[:40]
                            print(f"  [{status}] {t.get('task_id', 'N/A')[:16]}")
                            print(f"      {prompt}...")
                else:
                    print(f"  Error: {self._result_error(result)}")
            except Exception as e:
                print(f"  Error: {e}")
            print()

        else:
            print("\n Background Task Commands:")
            print("  background status          - Show orchestrator status")
            print("  background dispatch <task> - Dispatch task to local LLM")
            print("  background list            - List recent tasks")
            print()

    def cmd_analyze(self, args: str = "") -> None:
        """Quick code analysis via background orchestrator."""
        if not CORE_UTILITIES_AVAILABLE or nusyq is None:
            print("Analysis not available - NuSyQ core utilities required\n")
            return

        if not args:
            print("Usage: analyze <file_path>")
            print("       Dispatches analysis to local LLM via background orchestrator\n")
            return

        print(f"\n Analyzing: {args}")
        try:
            result = nusyq.analyze(args, analysis_type="code_analysis")
            if self._result_success(result):
                print(f"  Analysis task dispatched: {self._result_data(result)}")
                print("  Use 'background status' to check progress")
            else:
                print(f"  Analysis failed: {self._result_error(result)}")
        except Exception as e:
            print(f"  Error: {e}")
        print()

    def _shutdown_sequence(self) -> None:
        """Execute culture ship shutdown."""
        duration = (datetime.now() - self.context.session_start).total_seconds()
        print("\n" + "═" * 72)
        print("🌉 CULTURE SHIP SHUTDOWN")
        print("═" * 72)
        print(f"Session Duration:   {int(duration // 60)}m {int(duration % 60)}s")
        print(f"Actions Logged:     {len(self.context.action_log)}")
        print(f"Systems Integrated: {self.systems_integrated}/{self.total_systems}")
        print("═" * 72)
        print("🚀 Safe travels, netrunner.")
        print("═" * 72 + "\n")

        # Save context snapshot
        self._save_context_snapshot()

    def _save_context_snapshot(self) -> None:
        """Save context snapshot to disk."""
        try:
            snapshot_dir = Path("state/culture_ship")
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_file = snapshot_dir / f"session_{timestamp}.json"

            with open(snapshot_file, "w", encoding="utf-8") as f:
                json.dump(self.context.to_snapshot(), f, indent=2, default=str)

            print(f"📸 Context snapshot saved: {snapshot_file}")
        except OSError as err:
            print(f"⚠️  Failed to save context: {err}")


def main() -> None:
    """Launch the culture ship terminal."""
    ship = CultureShipTerminal(player_name="netrunner", difficulty=DifficultyLevel.BEGINNER)
    ship.run()


if __name__ == "__main__":
    main()

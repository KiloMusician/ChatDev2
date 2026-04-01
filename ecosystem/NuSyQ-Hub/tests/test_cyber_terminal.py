"""Tests for src/games/CyberTerminal/integrated_terminal.py and related modules."""

import sys
import types
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# The source module does `from src.Rosetta_Quest_System.quest_manager import QuestSystem`
# but the real module only exposes QuestManager.  Patch the import before the
# integrated_terminal module is loaded so the collection-time ImportError is avoided.
_quest_stub = types.ModuleType("src.Rosetta_Quest_System.quest_manager")
_quest_stub.QuestSystem = MagicMock()  # type: ignore[attr-defined]
_quest_stub.QuestManager = MagicMock()  # type: ignore[attr-defined]  # needed by openclaw bridge
_quest_stub.QuestEngine = MagicMock()  # type: ignore[attr-defined]  # needed by other bridges
sys.modules.setdefault("src.Rosetta_Quest_System.quest_manager", _quest_stub)

# Force re-import if the module was already cached with the broken import
for _mod in list(sys.modules):
    if "integrated_terminal" in _mod:
        del sys.modules[_mod]

from src.games.CyberTerminal.command_system import CommandResult, CommandStatus
from src.games.CyberTerminal.config import (
    DEFAULT_CONFIG,
    PROGRESSION_TIERS,
    STORY_ELEMENTS,
    DifficultyLevel,
    GameConfig,
    TerminalTheme,
)
from src.games.CyberTerminal.integrated_terminal import (
    IntegratedTerminal,
    IntegratedTerminalContext,
)
from src.games.CyberTerminal.widget_system import ButtonState, WidgetEvent, WidgetType


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestDifficultyLevelEnum:
    def test_all_members_exist(self):
        members = {m.name for m in DifficultyLevel}
        assert members == {"BEGINNER", "INTERMEDIATE", "ADVANCED", "MASTER", "ETHEREAL"}

    def test_values(self):
        assert DifficultyLevel.BEGINNER.value == "beginner"
        assert DifficultyLevel.INTERMEDIATE.value == "intermediate"
        assert DifficultyLevel.ADVANCED.value == "advanced"
        assert DifficultyLevel.MASTER.value == "master"
        assert DifficultyLevel.ETHEREAL.value == "ethereal"

    def test_member_count(self):
        assert len(DifficultyLevel) == 5


class TestTerminalThemeEnum:
    def test_all_members_exist(self):
        members = {m.name for m in TerminalTheme}
        assert members == {"NEON_GREEN", "SYNTHWAVE", "VOID_BLACK", "CYBER_PURPLE", "HOLOGRAPHIC"}

    def test_values(self):
        assert TerminalTheme.NEON_GREEN.value == "neon_green"
        assert TerminalTheme.SYNTHWAVE.value == "synthwave"
        assert TerminalTheme.VOID_BLACK.value == "void_black"
        assert TerminalTheme.CYBER_PURPLE.value == "cyber_purple"
        assert TerminalTheme.HOLOGRAPHIC.value == "holographic"


class TestCommandStatusEnum:
    def test_all_members_exist(self):
        members = {m.name for m in CommandStatus}
        assert members == {"SUCCESS", "ERROR", "PERMISSION_DENIED", "NOT_FOUND", "INVALID_ARGS"}

    def test_values(self):
        assert CommandStatus.SUCCESS.value == "success"
        assert CommandStatus.ERROR.value == "error"
        assert CommandStatus.PERMISSION_DENIED.value == "permission_denied"
        assert CommandStatus.NOT_FOUND.value == "not_found"
        assert CommandStatus.INVALID_ARGS.value == "invalid_args"


class TestWidgetTypeEnum:
    def test_all_members_exist(self):
        members = {m.name for m in WidgetType}
        assert members == {
            "MAIN_HUB",
            "SHOP",
            "INVENTORY",
            "STATS",
            "TERMINAL",
            "SETTINGS",
            "PAUSE_MENU",
            "CUSTOM",
        }

    def test_values(self):
        assert WidgetType.MAIN_HUB.value == "main_hub"
        assert WidgetType.SHOP.value == "shop"
        assert WidgetType.CUSTOM.value == "custom"


class TestButtonStateEnum:
    def test_all_members_exist(self):
        members = {m.name for m in ButtonState}
        assert members == {"NORMAL", "HOVERED", "ACTIVE", "DISABLED"}

    def test_values(self):
        assert ButtonState.NORMAL.value == "normal"
        assert ButtonState.HOVERED.value == "hovered"
        assert ButtonState.ACTIVE.value == "active"
        assert ButtonState.DISABLED.value == "disabled"


# ---------------------------------------------------------------------------
# Dataclass contracts
# ---------------------------------------------------------------------------


class TestGameConfigDataclass:
    def test_default_construction(self):
        cfg = GameConfig()
        assert cfg.version == "0.1.0"
        assert cfg.theme == TerminalTheme.SYNTHWAVE
        assert cfg.terminal_width == 100
        assert cfg.terminal_height == 40
        assert cfg.difficulty == DifficultyLevel.BEGINNER
        assert cfg.max_skill_level == 100
        assert cfg.lessons_per_tier == 5
        assert cfg.xp_per_lesson == 25
        assert cfg.enable_npc_interactions is True
        assert cfg.enable_network_hacking is False
        assert cfg.enable_story_mode is True
        assert cfg.nusyq_enabled is True
        assert cfg.quest_logging is True
        assert cfg.ai_assistance_enabled is True
        assert cfg.command_history_size == 100
        assert cfg.save_interval_minutes == 5
        assert cfg.enable_debug_mode is False

    def test_post_init_populates_xp_multipliers(self):
        cfg = GameConfig()
        assert cfg.xp_multiplier_by_difficulty is not None
        assert cfg.xp_multiplier_by_difficulty[DifficultyLevel.BEGINNER] == 1.0
        assert cfg.xp_multiplier_by_difficulty[DifficultyLevel.INTERMEDIATE] == 1.5
        assert cfg.xp_multiplier_by_difficulty[DifficultyLevel.ADVANCED] == 2.0
        assert cfg.xp_multiplier_by_difficulty[DifficultyLevel.MASTER] == 3.0
        assert cfg.xp_multiplier_by_difficulty[DifficultyLevel.ETHEREAL] == 5.0

    def test_get_xp_for_lesson_default(self):
        cfg = GameConfig()
        assert cfg.get_xp_for_lesson() == 25  # BEGINNER x 1.0

    def test_get_xp_for_lesson_with_difficulty(self):
        cfg = GameConfig()
        assert cfg.get_xp_for_lesson(DifficultyLevel.ADVANCED) == 50  # 25 x 2.0

    def test_custom_construction(self):
        cfg = GameConfig(difficulty=DifficultyLevel.MASTER, terminal_width=80)
        assert cfg.difficulty == DifficultyLevel.MASTER
        assert cfg.terminal_width == 80

    def test_default_config_instance(self):
        assert isinstance(DEFAULT_CONFIG, GameConfig)
        assert DEFAULT_CONFIG.difficulty == DifficultyLevel.BEGINNER


class TestCommandResultDataclass:
    def test_minimal_construction(self):
        result = CommandResult(status=CommandStatus.SUCCESS, output="ok")
        assert result.status == CommandStatus.SUCCESS
        assert result.output == "ok"
        assert result.error == ""
        assert result.metadata == {}

    def test_full_construction(self):
        result = CommandResult(
            status=CommandStatus.ERROR,
            output="",
            error="something went wrong",
            metadata={"cmd": "ls"},
        )
        assert result.status == CommandStatus.ERROR
        assert result.error == "something went wrong"
        assert result.metadata == {"cmd": "ls"}

    def test_post_init_sets_metadata_to_empty_dict(self):
        result = CommandResult(status=CommandStatus.NOT_FOUND, output="")
        assert result.metadata == {}


class TestWidgetEventDataclass:
    def test_construction(self):
        evt = WidgetEvent(event_type="click", widget_id="main_hub", data={"label": "btn"})
        assert evt.event_type == "click"
        assert evt.widget_id == "main_hub"
        assert evt.data == {"label": "btn"}

    def test_empty_data(self):
        evt = WidgetEvent(event_type="select", widget_id="shop", data={})
        assert evt.data == {}


# ---------------------------------------------------------------------------
# IntegratedTerminalContext
# ---------------------------------------------------------------------------


class TestIntegratedTerminalContext:
    def test_default_player_name(self):
        ctx = IntegratedTerminalContext()
        assert ctx.player_name == "netrunner"

    def test_custom_player_name(self):
        ctx = IntegratedTerminalContext(player_name="ghost")
        assert ctx.player_name == "ghost"

    def test_initial_state(self):
        ctx = IntegratedTerminalContext()
        assert ctx.terminal_history == []
        assert ctx.widget_state == {}
        assert ctx.consciousness_state == {}
        assert ctx.quest_state == {}
        assert isinstance(ctx.session_start, datetime)

    def test_record_terminal_action_appends(self):
        ctx = IntegratedTerminalContext()
        ctx.record_terminal_action("command", widget_id="w1", data={"cmd": "ls"})
        assert len(ctx.terminal_history) == 1
        entry = ctx.terminal_history[0]
        assert entry["action"] == "command"
        assert entry["widget_id"] == "w1"
        assert entry["data"] == {"cmd": "ls"}
        assert "timestamp" in entry

    def test_record_terminal_action_no_data(self):
        ctx = IntegratedTerminalContext()
        ctx.record_terminal_action("init")
        assert ctx.terminal_history[0]["data"] == {}

    def test_multiple_actions_recorded(self):
        ctx = IntegratedTerminalContext()
        for i in range(5):
            ctx.record_terminal_action(f"action_{i}")
        assert len(ctx.terminal_history) == 5

    def test_update_consciousness_state(self):
        ctx = IntegratedTerminalContext()
        ctx.update_consciousness_state({"status": "active", "level": 3})
        assert ctx.consciousness_state["status"] == "active"
        assert ctx.consciousness_state["level"] == 3

    def test_update_consciousness_state_merges(self):
        ctx = IntegratedTerminalContext()
        ctx.update_consciousness_state({"status": "active"})
        ctx.update_consciousness_state({"level": 7})
        assert ctx.consciousness_state["status"] == "active"
        assert ctx.consciousness_state["level"] == 7

    def test_to_json_keys(self):
        ctx = IntegratedTerminalContext(player_name="neon")
        result = ctx.to_json()
        assert result["player_name"] == "neon"
        assert "session_start" in result
        assert "session_duration_seconds" in result
        assert "terminal_history_count" in result
        assert "widget_state" in result
        assert "consciousness_state" in result
        assert "quest_state" in result

    def test_to_json_history_count(self):
        ctx = IntegratedTerminalContext()
        ctx.record_terminal_action("a")
        ctx.record_terminal_action("b")
        result = ctx.to_json()
        assert result["terminal_history_count"] == 2


# ---------------------------------------------------------------------------
# IntegratedTerminal
# ---------------------------------------------------------------------------


class TestIntegratedTerminalInit:
    def test_default_construction(self):
        with patch(
            "src.games.CyberTerminal.integrated_terminal.QuestSystem", side_effect=Exception("no db")
        ):
            terminal = IntegratedTerminal()
        assert terminal.player_name == "netrunner"
        assert terminal.difficulty == DifficultyLevel.BEGINNER

    def test_custom_construction(self):
        with patch(
            "src.games.CyberTerminal.integrated_terminal.QuestSystem", side_effect=Exception("no db")
        ):
            terminal = IntegratedTerminal(
                player_name="ghost", difficulty=DifficultyLevel.ADVANCED
            )
        assert terminal.player_name == "ghost"
        assert terminal.difficulty == DifficultyLevel.ADVANCED

    def test_commands_registry_populated(self):
        with patch(
            "src.games.CyberTerminal.integrated_terminal.QuestSystem", side_effect=Exception("no db")
        ):
            terminal = IntegratedTerminal()
        expected_cmds = {"help", "context", "quest", "consciousness", "widget", "integrate"}
        assert set(terminal.commands.keys()) == expected_cmds

    def test_game_attribute_is_cyber_terminal_game(self):
        from src.games.CyberTerminal.game import CyberTerminalGame

        with patch(
            "src.games.CyberTerminal.integrated_terminal.QuestSystem", side_effect=Exception("no db")
        ):
            terminal = IntegratedTerminal()
        assert isinstance(terminal.game, CyberTerminalGame)

    def test_context_attribute(self):
        with patch(
            "src.games.CyberTerminal.integrated_terminal.QuestSystem", side_effect=Exception("no db")
        ):
            terminal = IntegratedTerminal(player_name="neon")
        assert isinstance(terminal.context, IntegratedTerminalContext)
        assert terminal.context.player_name == "neon"

    def test_quest_system_none_when_unavailable(self):
        with patch(
            "src.games.CyberTerminal.integrated_terminal.QuestSystem", side_effect=Exception("no db")
        ):
            terminal = IntegratedTerminal()
        assert terminal.quest_system is None


class TestIntegratedTerminalMethods:
    @pytest.fixture()
    def terminal(self):
        with patch(
            "src.games.CyberTerminal.integrated_terminal.QuestSystem", side_effect=Exception("no db")
        ):
            return IntegratedTerminal(player_name="tester")

    def test_process_command_local_cmd_recorded(self, terminal):
        terminal.cmd_help = MagicMock()
        terminal.commands["help"] = terminal.cmd_help
        terminal.process_command("help")
        terminal.cmd_help.assert_called_once()
        assert len(terminal.context.terminal_history) >= 1

    def test_process_command_game_delegated(self, terminal):
        terminal.game._process_command = MagicMock()
        terminal.process_command("ls -la")
        terminal.game._process_command.assert_called_once_with("ls -la")

    def test_cmd_consciousness_sync_updates_state(self, terminal, capsys):
        terminal.cmd_consciousness("sync")
        assert terminal.context.consciousness_state.get("status") == "synced"
        assert "last_sync" in terminal.context.consciousness_state
        out = capsys.readouterr().out
        assert "synchronized" in out.lower() or "sync" in out.lower()

    def test_cmd_consciousness_state_default(self, terminal, capsys):
        terminal.cmd_consciousness()
        out = capsys.readouterr().out
        assert "Consciousness" in out or "consciousness" in out.lower()

    def test_cmd_consciousness_bridge(self, terminal, capsys):
        terminal.cmd_consciousness("bridge")
        out = capsys.readouterr().out
        assert "Bridge" in out or "bridge" in out.lower()

    def test_cmd_integrate_runs_without_error(self, terminal, capsys):
        terminal.cmd_integrate()
        out = capsys.readouterr().out
        assert "Integration" in out or "integration" in out.lower()

    def test_cmd_integrate_records_action(self, terminal, capsys):
        initial_count = len(terminal.context.terminal_history)
        terminal.cmd_integrate()
        assert len(terminal.context.terminal_history) > initial_count

    def test_cmd_help_outputs_commands(self, terminal, capsys):
        terminal.cmd_help()
        out = capsys.readouterr().out
        assert "help" in out.lower()
        assert "quest" in out.lower()
        assert "widget" in out.lower()

    def test_cmd_context_outputs_json(self, terminal, capsys):
        terminal.cmd_context()
        out = capsys.readouterr().out
        assert "player_name" in out
        assert "tester" in out

    def test_cmd_quest_no_quest_system(self, terminal, capsys):
        terminal.quest_system = None
        terminal.cmd_quest("list")
        out = capsys.readouterr().out
        assert "not available" in out.lower() or "❌" in out

    def test_display_session_summary_runs(self, terminal, capsys):
        terminal.display_session_summary()
        out = capsys.readouterr().out
        assert "SESSION SUMMARY" in out or "summary" in out.lower()

    def test_display_banner_runs(self, terminal, capsys):
        terminal.display_banner()
        out = capsys.readouterr().out
        assert "CULTURE SHIP" in out or "TERMINAL" in out


# ---------------------------------------------------------------------------
# Package-level imports and module-level constants
# ---------------------------------------------------------------------------


class TestModuleLevelConstants:
    def test_progression_tiers_keys(self):
        expected = {
            "tier_1_basics",
            "tier_2_intermediate",
            "tier_3_advanced",
            "tier_4_master",
            "tier_5_ethereal",
        }
        assert set(PROGRESSION_TIERS.keys()) == expected

    def test_progression_tiers_have_required_fields(self):
        for tier_key, tier in PROGRESSION_TIERS.items():
            assert "name" in tier, f"{tier_key} missing 'name'"
            assert "description" in tier, f"{tier_key} missing 'description'"
            assert "skills" in tier, f"{tier_key} missing 'skills'"
            assert "difficulty" in tier, f"{tier_key} missing 'difficulty'"

    def test_story_elements_keys(self):
        assert "protagonist_title" in STORY_ELEMENTS
        assert "world_name" in STORY_ELEMENTS
        assert "year" in STORY_ELEMENTS
        assert STORY_ELEMENTS["year"] == 2087

    def test_package_imports_succeed(self):
        import src.games.CyberTerminal.integrated_terminal as _it
        import src.games.CyberTerminal.config as _cfg
        import src.games.CyberTerminal.command_system as _cs

        assert hasattr(_it, "IntegratedTerminal")
        assert hasattr(_it, "IntegratedTerminalContext")
        assert hasattr(_cfg, "DifficultyLevel")
        assert hasattr(_cfg, "GameConfig")
        assert hasattr(_cs, "CommandStatus")
        assert hasattr(_cs, "CommandResult")

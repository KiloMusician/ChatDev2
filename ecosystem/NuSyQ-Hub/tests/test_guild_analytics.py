"""Tests for GuildAnalytics and AgentGuildProtocols."""

from __future__ import annotations

from dataclasses import asdict, fields
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from src.guild.guild_analytics import AgentPerformanceMetrics, GuildAnalytics, QuestAnalytics
from src.guild.guild_board import (
    AgentHeartbeat,
    AgentStatus,
    BoardPost,
    GuildBoard,
    GuildBoardState,
    QuestEntry,
    QuestId,
    QuestState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_board(tmp_path: Path) -> GuildBoard:
    """Create an isolated GuildBoard backed by tmp_path."""
    board = GuildBoard(
        state_dir=tmp_path / "guild",
        data_dir=tmp_path / "data",
    )
    board.auto_release_claim_on_heartbeat_timeout = False
    return board


def _make_quest(
    quest_id: str = "q-001",
    title: str = "Test Quest",
    state: QuestState = QuestState.OPEN,
    tags: list[str] | None = None,
    priority: int = 3,
    claimed_by: str | None = None,
) -> QuestEntry:
    now = datetime.now().isoformat()
    return QuestEntry(
        quest_id=quest_id,
        title=title,
        description="A test quest",
        priority=priority,
        safety_tier="safe",
        state=state,
        tags=tags or [],
        created_at=now,
        claimed_by=claimed_by,
    )


def _make_analytics(tmp_path: Path) -> GuildAnalytics:
    board = _make_board(tmp_path)
    return GuildAnalytics(guild_board=board)


# ---------------------------------------------------------------------------
# Package-level import tests
# ---------------------------------------------------------------------------


class TestPackageImports:
    """Verify public symbols are importable from expected modules."""

    def test_guild_analytics_importable(self) -> None:
        from src.guild import guild_analytics

        assert guild_analytics is not None

    def test_agent_guild_protocols_importable(self) -> None:
        from src.guild import agent_guild_protocols

        assert agent_guild_protocols is not None

    def test_guild_init_exports(self) -> None:
        import src.guild as guild_pkg

        for name in [
            "AgentStatus",
            "QuestState",
            "GuildBoard",
            "get_board",
            "agent_heartbeat",
            "agent_claim",
        ]:
            assert hasattr(guild_pkg, name), f"Missing export: {name}"

    def test_agentguildprotocols_class_importable(self) -> None:
        from src.guild.agent_guild_protocols import AgentGuildProtocols

        assert AgentGuildProtocols is not None


# ---------------------------------------------------------------------------
# Dataclass / enum type tests
# ---------------------------------------------------------------------------


class TestDataclasses:
    """Verify exported dataclasses and enums have the expected fields."""

    def test_agent_performance_metrics_fields(self) -> None:
        field_names = {f.name for f in fields(AgentPerformanceMetrics)}
        expected = {
            "agent_id",
            "quests_claimed",
            "quests_completed",
            "quests_abandoned",
            "average_completion_time",
            "success_rate",
            "collaboration_count",
            "specialty_tags",
            "last_active",
        }
        assert expected <= field_names

    def test_agent_performance_metrics_defaults(self) -> None:
        m = AgentPerformanceMetrics(agent_id="alice")
        assert m.quests_claimed == 0
        assert m.quests_completed == 0
        assert m.success_rate == 0.0
        assert m.specialty_tags == []
        assert m.last_active is None

    def test_quest_analytics_fields(self) -> None:
        field_names = {f.name for f in fields(QuestAnalytics)}
        expected = {
            "total_quests",
            "open_quests",
            "active_quests",
            "completed_quests",
            "abandoned_quests",
            "blocked_quests",
            "average_time_to_claim",
            "average_completion_time",
            "most_common_tags",
            "bottleneck_quests",
        }
        assert expected <= field_names

    def test_quest_analytics_defaults(self) -> None:
        qa = QuestAnalytics()
        assert qa.total_quests == 0
        assert qa.most_common_tags == []
        assert qa.bottleneck_quests == []

    def test_agent_performance_metrics_asdict(self) -> None:
        m = AgentPerformanceMetrics(agent_id="bob", quests_claimed=5, quests_completed=3)
        d = asdict(m)
        assert d["agent_id"] == "bob"
        assert d["quests_claimed"] == 5

    def test_quest_state_enum_values(self) -> None:
        assert QuestState.OPEN.value == "open"
        assert QuestState.ACTIVE.value == "active"
        assert QuestState.DONE.value == "done"
        assert QuestState.ABANDONED.value == "abandoned"
        assert QuestState.BLOCKED.value == "blocked"

    def test_agent_status_enum_values(self) -> None:
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.WORKING.value == "working"
        assert AgentStatus.BLOCKED.value == "blocked"
        assert AgentStatus.OFFLINE.value == "offline"


# ---------------------------------------------------------------------------
# GuildAnalytics initialization
# ---------------------------------------------------------------------------


class TestGuildAnalyticsInit:
    """Test GuildAnalytics initialization."""

    def test_init_with_explicit_board(self, tmp_path: Path) -> None:
        board = _make_board(tmp_path)
        ga = GuildAnalytics(guild_board=board)
        assert ga.board is board

    def test_analytics_dir_created(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        assert ga.analytics_dir.is_dir()

    def test_board_attribute_set(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        assert isinstance(ga.board, GuildBoard)


# ---------------------------------------------------------------------------
# analyze_quests — empty board
# ---------------------------------------------------------------------------


class TestAnalyzeQuestsEmpty:
    """QuestAnalytics on a board with no quests."""

    def test_returns_quest_analytics_type(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        result = ga.analyze_quests()
        assert isinstance(result, QuestAnalytics)

    def test_totals_zero_on_empty_board(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        qa = ga.analyze_quests()
        assert qa.total_quests == 0
        assert qa.open_quests == 0
        assert qa.completed_quests == 0

    def test_average_times_zero_on_empty_board(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        qa = ga.analyze_quests()
        assert qa.average_time_to_claim == 0.0
        assert qa.average_completion_time == 0.0


# ---------------------------------------------------------------------------
# analyze_quests — board with quests
# ---------------------------------------------------------------------------


class TestAnalyzeQuestsWithData:
    """QuestAnalytics on a board populated with quest entries."""

    def _ga_with_quests(self, tmp_path: Path) -> GuildAnalytics:
        board = _make_board(tmp_path)
        board.board.quests["q-open"] = _make_quest("q-open", state=QuestState.OPEN)
        board.board.quests["q-active"] = _make_quest("q-active", state=QuestState.ACTIVE)
        board.board.quests["q-done"] = _make_quest("q-done", state=QuestState.DONE)
        board.board.quests["q-abandoned"] = _make_quest(
            "q-abandoned", state=QuestState.ABANDONED
        )
        board.board.quests["q-blocked"] = _make_quest("q-blocked", state=QuestState.BLOCKED)
        return GuildAnalytics(guild_board=board)

    def test_total_count(self, tmp_path: Path) -> None:
        ga = self._ga_with_quests(tmp_path)
        assert ga.analyze_quests().total_quests == 5

    def test_state_counts(self, tmp_path: Path) -> None:
        ga = self._ga_with_quests(tmp_path)
        qa = ga.analyze_quests()
        assert qa.open_quests == 1
        assert qa.active_quests == 1
        assert qa.completed_quests == 1
        assert qa.abandoned_quests == 1
        assert qa.blocked_quests == 1

    def test_most_common_tags(self, tmp_path: Path) -> None:
        board = _make_board(tmp_path)
        board.board.quests["q1"] = _make_quest("q1", tags=["python", "backend"])
        board.board.quests["q2"] = _make_quest("q2", tags=["python", "frontend"])
        board.board.quests["q3"] = _make_quest("q3", tags=["python"])
        ga = GuildAnalytics(guild_board=board)
        qa = ga.analyze_quests()
        tag_map = dict(qa.most_common_tags)
        assert tag_map.get("python") == 3
        assert tag_map.get("backend") == 1

    def test_bottleneck_quests_old_open(self, tmp_path: Path) -> None:
        board = _make_board(tmp_path)
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        q = _make_quest("q-old", state=QuestState.OPEN)
        q.created_at = old_time
        board.board.quests["q-old"] = q
        ga = GuildAnalytics(guild_board=board)
        qa = ga.analyze_quests()
        assert "q-old" in qa.bottleneck_quests

    def test_recent_open_not_bottleneck(self, tmp_path: Path) -> None:
        board = _make_board(tmp_path)
        board.board.quests["q-new"] = _make_quest("q-new", state=QuestState.OPEN)
        ga = GuildAnalytics(guild_board=board)
        qa = ga.analyze_quests()
        assert "q-new" not in qa.bottleneck_quests


# ---------------------------------------------------------------------------
# analyze_agent_performance
# ---------------------------------------------------------------------------


class TestAnalyzeAgentPerformance:
    """AgentPerformanceMetrics returned for registered agents."""

    def test_returns_dict(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        result = ga.analyze_agent_performance()
        assert isinstance(result, dict)

    def test_empty_board_no_agents(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        assert ga.analyze_agent_performance() == {}

    def test_agent_in_result(self, tmp_path: Path) -> None:
        board = _make_board(tmp_path)
        board.board.agents["agent-x"] = AgentHeartbeat(
            agent_id="agent-x", status=AgentStatus.IDLE
        )
        ga = GuildAnalytics(guild_board=board)
        metrics = ga.analyze_agent_performance()
        assert "agent-x" in metrics
        assert isinstance(metrics["agent-x"], AgentPerformanceMetrics)

    def test_metrics_computed_from_events(self, tmp_path: Path) -> None:
        """Events file with claim/complete entries drives metric counters."""
        board = _make_board(tmp_path)
        board.board.agents["agent-y"] = AgentHeartbeat(
            agent_id="agent-y", status=AgentStatus.IDLE
        )
        events = [
            {"agent_id": "agent-y", "event_type": "quest_claimed"},
            {"agent_id": "agent-y", "event_type": "quest_claimed"},
            {"agent_id": "agent-y", "event_type": "quest_completed"},
        ]
        board.events_file.parent.mkdir(parents=True, exist_ok=True)
        import json

        with open(board.events_file, "w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")

        ga = GuildAnalytics(guild_board=board)
        metrics = ga.analyze_agent_performance()
        m = metrics["agent-y"]
        assert m.quests_claimed == 2
        assert m.quests_completed == 1
        assert m.success_rate == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# recommend_agent_for_quest
# ---------------------------------------------------------------------------


class TestRecommendAgentForQuest:
    """Recommendations return empty list when quest absent or no agents."""

    def test_unknown_quest_returns_empty(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        result = ga.recommend_agent_for_quest("non-existent-id")
        assert result == []

    def test_returns_sorted_list(self, tmp_path: Path) -> None:
        board = _make_board(tmp_path)
        board.board.quests["q1"] = _make_quest("q1", state=QuestState.OPEN, tags=["python"])
        board.board.agents["agent-a"] = AgentHeartbeat(
            agent_id="agent-a", status=AgentStatus.IDLE
        )
        board.board.agents["agent-b"] = AgentHeartbeat(
            agent_id="agent-b", status=AgentStatus.WORKING
        )
        ga = GuildAnalytics(guild_board=board)
        result = ga.recommend_agent_for_quest("q1")
        assert isinstance(result, list)
        scores = [score for _, score in result]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# detect_collaboration_opportunities
# ---------------------------------------------------------------------------


class TestDetectCollaborationOpportunities:
    """Collaboration detector returns list."""

    def test_empty_board_returns_list(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        result = ga.detect_collaboration_opportunities()
        assert isinstance(result, list)

    def test_high_priority_open_quest_eligible(self, tmp_path: Path) -> None:
        board = _make_board(tmp_path)
        board.board.quests["q-hp"] = _make_quest("q-hp", state=QuestState.OPEN, priority=5)
        # Two agents so >=2 recommendations are possible
        board.board.agents["agent-1"] = AgentHeartbeat(
            agent_id="agent-1", status=AgentStatus.IDLE
        )
        board.board.agents["agent-2"] = AgentHeartbeat(
            agent_id="agent-2", status=AgentStatus.IDLE
        )
        ga = GuildAnalytics(guild_board=board)
        opps = ga.detect_collaboration_opportunities()
        quest_ids = [o["quest_id"] for o in opps]
        assert "q-hp" in quest_ids


# ---------------------------------------------------------------------------
# generate_daily_report
# ---------------------------------------------------------------------------


class TestGenerateDailyReport:
    """Daily report returns a non-empty markdown string."""

    def test_report_is_string(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        report = ga.generate_daily_report()
        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_contains_header(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        report = ga.generate_daily_report()
        assert "Guild Analytics Daily Report" in report

    def test_report_file_written(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        ga.generate_daily_report()
        reports = list(ga.analytics_dir.glob("daily_report_*.md"))
        assert len(reports) >= 1


# ---------------------------------------------------------------------------
# export_metrics
# ---------------------------------------------------------------------------


class TestExportMetrics:
    """export_metrics returns a JSON-serialisable dict."""

    def test_returns_dict(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        result = ga.export_metrics()
        assert isinstance(result, dict)

    def test_has_required_keys(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        result = ga.export_metrics()
        assert "timestamp" in result
        assert "agents" in result
        assert "quests" in result
        assert "recommendations" in result

    def test_timestamp_is_iso(self, tmp_path: Path) -> None:
        ga = _make_analytics(tmp_path)
        result = ga.export_metrics()
        # Should be parseable as ISO datetime
        datetime.fromisoformat(result["timestamp"])


# ---------------------------------------------------------------------------
# AgentGuildProtocols — static structure (no async invocation)
# ---------------------------------------------------------------------------


class TestAgentGuildProtocolsStructure:
    """Verify protocol class exposes expected static methods."""

    def test_static_methods_present(self) -> None:
        from src.guild.agent_guild_protocols import AgentGuildProtocols

        for name in [
            "heartbeat",
            "claim",
            "start",
            "post",
            "complete",
            "add_quest",
            "close_quest",
            "yield_quest",
            "swarm",
            "get_available_quests",
        ]:
            assert hasattr(AgentGuildProtocols, name), f"Missing method: {name}"

    def test_convenience_functions_present(self) -> None:
        import src.guild.agent_guild_protocols as proto

        for name in [
            "agent_heartbeat",
            "agent_claim",
            "agent_start",
            "agent_post",
            "agent_complete",
            "agent_yield",
            "agent_available_quests",
            "agent_add_quest",
            "agent_close_quest",
        ]:
            assert hasattr(proto, name), f"Missing convenience fn: {name}"

    def test_methods_are_coroutine_functions(self) -> None:
        import asyncio

        from src.guild.agent_guild_protocols import AgentGuildProtocols

        for name in ["heartbeat", "claim", "complete"]:
            fn = getattr(AgentGuildProtocols, name)
            assert asyncio.iscoroutinefunction(fn), f"{name} should be a coroutine function"

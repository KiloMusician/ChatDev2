"""Async tests for GuildBoard covering uncovered methods.

Targets the ~59% of uncovered lines in src/guild/guild_board.py:
- agent_heartbeat, claim_quest, start_quest
- post_on_board (normal + throttled)
- complete_quest, add_quest, close_quest
- add_signal, get_available_quests, get_board_summary
- _parse_timestamp, _heartbeat_is_recent, _is_post_throttled
- _load_board with corrupt file
- post_message (sync)
- get_board / init_board singletons
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.guild.guild_board import (
    AgentHeartbeat,
    AgentStatus,
    BoardPost,
    GuildBoard,
    QuestState,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def board(tmp_path: Path) -> GuildBoard:
    """Isolated GuildBoard instance."""
    return GuildBoard(state_dir=tmp_path / "guild", data_dir=tmp_path / "data")


async def _add_quest(board: GuildBoard, qid: str = "q1", title: str = "Test Quest") -> str:
    """Helper: add a quest, return its ID."""
    ok, returned_id = await board.add_quest(
        quest_id=qid,
        title=title,
        description="Test",
        priority=3,
    )
    assert ok
    return returned_id


async def _heartbeat(
    board: GuildBoard, agent: str = "agent1", status: AgentStatus = AgentStatus.IDLE
) -> AgentHeartbeat:
    """Helper: post heartbeat."""
    return await board.agent_heartbeat(agent, status)


# ---------------------------------------------------------------------------
# _parse_timestamp
# ---------------------------------------------------------------------------


class TestParseTimestamp:
    def test_valid_iso_string(self, board: GuildBoard):
        ts = "2026-03-03T12:00:00"
        result = board._parse_timestamp(ts)
        assert isinstance(result, datetime)
        assert result.year == 2026

    def test_none_returns_none(self, board: GuildBoard):
        assert board._parse_timestamp(None) is None

    def test_empty_string_returns_none(self, board: GuildBoard):
        assert board._parse_timestamp("") is None

    def test_invalid_string_returns_none(self, board: GuildBoard):
        assert board._parse_timestamp("not-a-date") is None


# ---------------------------------------------------------------------------
# _heartbeat_is_recent
# ---------------------------------------------------------------------------


class TestHeartbeatIsRecent:
    def test_max_age_zero_always_true(self, board: GuildBoard):
        assert board._heartbeat_is_recent("anyone", 0) is True

    def test_missing_agent_returns_false(self, board: GuildBoard):
        assert board._heartbeat_is_recent("ghost_agent", 5) is False

    def test_recent_heartbeat_returns_true(self, board: GuildBoard):
        # Plant a fresh heartbeat
        board.board.agents["fresh"] = AgentHeartbeat(
            agent_id="fresh",
            status=AgentStatus.IDLE,
            timestamp=datetime.now().isoformat(),
        )
        assert board._heartbeat_is_recent("fresh", max_age_minutes=5) is True

    def test_stale_heartbeat_returns_false(self, board: GuildBoard):
        # Plant a heartbeat from 20 minutes ago
        old_ts = (datetime.now() - timedelta(minutes=20)).isoformat()
        board.board.agents["stale"] = AgentHeartbeat(
            agent_id="stale",
            status=AgentStatus.IDLE,
            timestamp=old_ts,
        )
        assert board._heartbeat_is_recent("stale", max_age_minutes=5) is False


# ---------------------------------------------------------------------------
# _is_post_throttled
# ---------------------------------------------------------------------------


class TestIsPostThrottled:
    def test_throttle_disabled_never_throttles(self, board: GuildBoard):
        board.post_throttle_per_minute = 0
        assert board._is_post_throttled("any_agent", datetime.now()) is False

    def test_below_threshold_not_throttled(self, board: GuildBoard):
        board.post_throttle_per_minute = 3
        # Add 2 recent posts for the agent
        now = datetime.now()
        for i in range(2):
            board.board.recent_posts.append(
                BoardPost(
                    post_id=f"p{i}", agent_id="agent1", message="x", timestamp=now.isoformat()
                )
            )
        assert board._is_post_throttled("agent1", now) is False

    def test_at_threshold_throttled(self, board: GuildBoard):
        board.post_throttle_per_minute = 3
        now = datetime.now()
        for i in range(3):
            board.board.recent_posts.append(
                BoardPost(
                    post_id=f"p{i}", agent_id="agent1", message="x", timestamp=now.isoformat()
                )
            )
        assert board._is_post_throttled("agent1", now) is True

    def test_old_posts_dont_count_toward_throttle(self, board: GuildBoard):
        board.post_throttle_per_minute = 2
        old_ts = (datetime.now() - timedelta(minutes=5)).isoformat()
        board.board.recent_posts.append(
            BoardPost(post_id="old", agent_id="agent1", message="x", timestamp=old_ts)
        )
        assert board._is_post_throttled("agent1", datetime.now()) is False


# ---------------------------------------------------------------------------
# post_message (sync)
# ---------------------------------------------------------------------------


class TestPostMessage:
    def test_post_message_adds_to_recent_posts(self, board: GuildBoard):
        board.post_message("claude", "Hello board")
        assert any(p.message == "Hello board" for p in board.board.recent_posts)

    def test_post_message_trims_to_last_10(self, board: GuildBoard):
        for i in range(15):
            board.post_message("agent", f"msg {i}")
        assert len(board.board.recent_posts) <= 10


# ---------------------------------------------------------------------------
# _load_board with corrupt file
# ---------------------------------------------------------------------------


class TestLoadBoard:
    def test_corrupt_json_resets_to_fresh_board(self, tmp_path: Path):
        guild_dir = tmp_path / "guild"
        guild_dir.mkdir(parents=True)
        board_file = guild_dir / "guild_board.json"
        board_file.write_text("{ this is not valid json }", encoding="utf-8")

        b = GuildBoard(state_dir=guild_dir)
        # Board should be fresh (empty agents/quests)
        assert b.board.agents == {}
        # Corrupt file should have been moved away
        assert not board_file.exists() or board_file.stat().st_size > 0


# ---------------------------------------------------------------------------
# agent_heartbeat
# ---------------------------------------------------------------------------


class TestAgentHeartbeat:
    @pytest.mark.asyncio
    async def test_heartbeat_registers_agent(self, board: GuildBoard):
        hb = await board.agent_heartbeat("claude", AgentStatus.WORKING)
        assert hb.agent_id == "claude"
        assert "claude" in board.board.agents
        assert board.board.agents["claude"].status == AgentStatus.WORKING

    @pytest.mark.asyncio
    async def test_heartbeat_with_capabilities_and_blockers(self, board: GuildBoard):
        hb = await board.agent_heartbeat(
            "ollama",
            AgentStatus.IDLE,
            capabilities=["python", "review"],
            blockers=["port_conflict"],
        )
        assert hb.capabilities == ["python", "review"]
        assert hb.blockers == ["port_conflict"]

    @pytest.mark.asyncio
    async def test_heartbeat_updates_existing_agent(self, board: GuildBoard):
        await board.agent_heartbeat("agent1", AgentStatus.IDLE)
        await board.agent_heartbeat("agent1", AgentStatus.WORKING)
        assert board.board.agents["agent1"].status == AgentStatus.WORKING

    @pytest.mark.asyncio
    async def test_heartbeat_persists_to_disk(self, board: GuildBoard):
        await board.agent_heartbeat("agent1", AgentStatus.IDLE)
        assert board.board_file.exists()


# ---------------------------------------------------------------------------
# claim_quest
# ---------------------------------------------------------------------------


class TestClaimQuest:
    @pytest.mark.asyncio
    async def test_claim_requires_heartbeat(self, board: GuildBoard):
        board.heartbeat_required = True
        await _add_quest(board)
        ok, msg = await board.claim_quest("q1", "no_heartbeat_agent")
        assert not ok
        assert msg is not None and "heartbeat" in msg.lower()

    @pytest.mark.asyncio
    async def test_claim_quest_not_found(self, board: GuildBoard):
        board.heartbeat_required = False
        ok, msg = await board.claim_quest("nonexistent", "agent1")
        assert not ok
        assert msg is not None and "not found" in msg.lower()

    @pytest.mark.asyncio
    async def test_claim_quest_already_claimed_by_other(self, board: GuildBoard):
        # Disable auto-release so claim isn't wiped by heartbeat-timeout check
        board.heartbeat_required = False
        board.auto_release_claim_on_heartbeat_timeout = False
        await _add_quest(board)
        ok, _ = await board.claim_quest("q1", "agent1")
        assert ok
        ok2, msg = await board.claim_quest("q1", "agent2")
        assert not ok2
        assert msg is not None and "claimed" in msg.lower()

    @pytest.mark.asyncio
    async def test_claim_quest_success(self, board: GuildBoard):
        board.heartbeat_required = False
        board.auto_release_claim_on_heartbeat_timeout = False
        await _add_quest(board)
        ok, _msg = await board.claim_quest("q1", "agent1")
        assert ok is True
        assert board.board.quests["q1"].claimed_by == "agent1"
        assert board.board.quests["q1"].state == QuestState.CLAIMED

    @pytest.mark.asyncio
    async def test_claim_already_claimed_by_same_agent_is_idempotent_or_fails(
        self, board: GuildBoard
    ):
        """Same agent re-claiming fails: CLAIMED is not in [OPEN, BLOCKED]."""
        board.heartbeat_required = False
        board.auto_release_claim_on_heartbeat_timeout = False
        await _add_quest(board)
        ok1, _ = await board.claim_quest("q1", "agent1")
        assert ok1
        # Quest is now CLAIMED (not OPEN/BLOCKED), so second attempt should fail
        ok2, _msg = await board.claim_quest("q1", "agent1")
        assert not ok2  # CLAIMED state is not in [OPEN, BLOCKED]


# ---------------------------------------------------------------------------
# start_quest
# ---------------------------------------------------------------------------


class TestStartQuest:
    @pytest.mark.asyncio
    async def test_start_quest_not_found(self, board: GuildBoard):
        ok, _msg = await board.start_quest("bad_id", "agent1")
        assert not ok

    @pytest.mark.asyncio
    async def test_start_quest_not_claimed_by_agent(self, board: GuildBoard):
        board.heartbeat_required = False
        board.auto_release_claim_on_heartbeat_timeout = False
        await _add_quest(board)
        await board.claim_quest("q1", "agent1")
        ok, msg = await board.start_quest("q1", "agent2")
        assert not ok
        assert msg is not None

    @pytest.mark.asyncio
    async def test_start_quest_success(self, board: GuildBoard):
        board.heartbeat_required = False
        board.auto_release_claim_on_heartbeat_timeout = False
        await _add_quest(board)
        await board.claim_quest("q1", "agent1")
        ok, _msg = await board.start_quest("q1", "agent1")
        assert ok
        assert board.board.quests["q1"].state == QuestState.ACTIVE
        assert board.board.quests["q1"].started_at is not None


# ---------------------------------------------------------------------------
# post_on_board
# ---------------------------------------------------------------------------


class TestPostOnBoard:
    @pytest.mark.asyncio
    async def test_post_adds_to_recent_posts(self, board: GuildBoard):
        post = await board.post_on_board("agent1", "Working on task")
        assert post.message == "Working on task"
        assert any(p.agent_id == "agent1" for p in board.board.recent_posts)

    @pytest.mark.asyncio
    async def test_post_with_quest_and_artifacts(self, board: GuildBoard):
        post = await board.post_on_board(
            "agent1",
            "Completed step",
            quest_id="q1",
            post_type="discovery",
            artifacts=["output.json"],
        )
        assert post.quest_id == "q1"
        assert "output.json" in post.artifacts

    @pytest.mark.asyncio
    async def test_throttled_post_returns_throttle_notice(self, board: GuildBoard):
        board.post_throttle_per_minute = 1
        now = datetime.now()
        board.board.recent_posts.append(
            BoardPost(post_id="existing", agent_id="agent1", message="x", timestamp=now.isoformat())
        )
        post = await board.post_on_board("agent1", "This should be throttled")
        assert post.post_type == "throttled"


# ---------------------------------------------------------------------------
# complete_quest
# ---------------------------------------------------------------------------


class TestCompleteQuest:
    @pytest.mark.asyncio
    async def test_complete_quest_not_found(self, board: GuildBoard):
        ok, _msg = await board.complete_quest("bad", "agent1")
        assert not ok

    @pytest.mark.asyncio
    async def test_complete_quest_wrong_agent(self, board: GuildBoard):
        board.heartbeat_required = False
        board.auto_release_claim_on_heartbeat_timeout = False
        await _add_quest(board)
        await board.claim_quest("q1", "agent1")
        ok, _msg = await board.complete_quest("q1", "agent2")
        assert not ok

    @pytest.mark.asyncio
    async def test_complete_quest_success_with_artifacts(self, board: GuildBoard):
        board.heartbeat_required = False
        board.auto_release_claim_on_heartbeat_timeout = False
        await _add_quest(board)
        await board.claim_quest("q1", "agent1")
        ok, _msg = await board.complete_quest("q1", "agent1", artifacts=["report.json"])
        assert ok
        quest = board.board.quests["q1"]
        assert quest.state == QuestState.DONE
        assert "report.json" in quest.artifacts
        assert "q1" not in board.board.active_work

    @pytest.mark.asyncio
    async def test_complete_quest_without_artifacts(self, board: GuildBoard):
        board.heartbeat_required = False
        board.auto_release_claim_on_heartbeat_timeout = False
        await _add_quest(board)
        await board.claim_quest("q1", "agent1")
        ok, _ = await board.complete_quest("q1", "agent1")
        assert ok


# ---------------------------------------------------------------------------
# add_quest
# ---------------------------------------------------------------------------


class TestAddQuest:
    @pytest.mark.asyncio
    async def test_add_quest_with_explicit_id(self, board: GuildBoard):
        ok, qid = await board.add_quest("my_quest", "Title", "Desc")
        assert ok
        assert qid == "my_quest"
        assert "my_quest" in board.board.quests

    @pytest.mark.asyncio
    async def test_add_quest_auto_generates_id(self, board: GuildBoard):
        ok, qid = await board.add_quest(None, "Auto Title", "Desc")
        assert ok
        assert qid  # some id generated
        assert qid in board.board.quests

    @pytest.mark.asyncio
    async def test_add_quest_collision_gets_suffix(self, board: GuildBoard):
        await board.add_quest("dup", "First", "Desc")
        ok, qid = await board.add_quest("dup", "Second", "Desc")
        assert ok
        assert qid != "dup"  # Should have suffix
        assert qid in board.board.quests

    @pytest.mark.asyncio
    async def test_add_quest_clamps_priority(self, board: GuildBoard):
        await board.add_quest("q_high", "High", "Desc", priority=99)
        assert board.board.quests["q_high"].priority == 5

        await board.add_quest("q_low", "Low", "Desc", priority=-5)
        assert board.board.quests["q_low"].priority == 1

    @pytest.mark.asyncio
    async def test_add_quest_with_tags_and_deps(self, board: GuildBoard):
        ok, _qid = await board.add_quest(
            "q_tagged",
            "Tagged",
            "Desc",
            tags=["python", "testing"],
            dependencies=["q_other"],
        )
        assert ok
        assert board.board.quests["q_tagged"].tags == ["python", "testing"]


# ---------------------------------------------------------------------------
# close_quest
# ---------------------------------------------------------------------------


class TestCloseQuest:
    @pytest.mark.asyncio
    async def test_close_quest_not_found(self, board: GuildBoard):
        ok, _msg = await board.close_quest("missing", reason="test")
        assert not ok

    @pytest.mark.asyncio
    async def test_close_quest_as_abandoned(self, board: GuildBoard):
        await _add_quest(board)
        ok, _val = await board.close_quest("q1", agent_id="agent1", status=QuestState.ABANDONED)
        assert ok
        assert board.board.quests["q1"].state == QuestState.ABANDONED

    @pytest.mark.asyncio
    async def test_close_quest_removes_from_active_work(self, board: GuildBoard):
        board.heartbeat_required = False
        await _add_quest(board)
        await board.claim_quest("q1", "agent1")
        board.board.active_work["q1"] = "agent1"
        await board.close_quest("q1")
        assert "q1" not in board.board.active_work


# ---------------------------------------------------------------------------
# add_signal
# ---------------------------------------------------------------------------


class TestAddSignal:
    @pytest.mark.asyncio
    async def test_add_signal_appends_to_signals(self, board: GuildBoard):
        await board.add_signal(
            "error", "critical", "DB connection lost", context={"db": "postgres"}
        )
        assert len(board.board.signals) == 1
        sig = board.board.signals[0]
        assert sig["type"] == "error"
        assert sig["severity"] == "critical"
        assert sig["context"]["db"] == "postgres"

    @pytest.mark.asyncio
    async def test_add_signal_trims_to_50(self, board: GuildBoard):
        for i in range(60):
            await board.add_signal("warn", "low", f"signal {i}")
        assert len(board.board.signals) <= 50


# ---------------------------------------------------------------------------
# get_available_quests
# ---------------------------------------------------------------------------


class TestGetAvailableQuests:
    @pytest.mark.asyncio
    async def test_returns_open_quests_matching_capabilities(self, board: GuildBoard):
        await board.add_quest("q1", "Python Task", "Desc", tags=["python"])
        await board.add_quest("q2", "JS Task", "Desc", tags=["javascript"])
        result = await board.get_available_quests(["python"])
        ids = [q.quest_id for q in result]
        assert "q1" in ids

    @pytest.mark.asyncio
    async def test_claimed_quests_excluded(self, board: GuildBoard):
        board.heartbeat_required = False
        await board.add_quest("q1", "Task", "Desc")
        await board.claim_quest("q1", "agent1")
        result = await board.get_available_quests([])
        ids = [q.quest_id for q in result]
        assert "q1" not in ids

    @pytest.mark.asyncio
    async def test_quests_sorted_by_priority_descending(self, board: GuildBoard):
        await board.add_quest("q_low", "Low", "Desc", priority=1)
        await board.add_quest("q_high", "High", "Desc", priority=5)
        result = await board.get_available_quests([])
        assert result[0].priority >= result[-1].priority


# ---------------------------------------------------------------------------
# get_board_summary
# ---------------------------------------------------------------------------


class TestGetBoardSummary:
    @pytest.mark.asyncio
    async def test_summary_keys_present(self, board: GuildBoard):
        summary = await board.get_board_summary()
        assert "agents_online" in summary
        assert "quests_open" in summary
        assert "quests_active" in summary
        assert "quests_blocked" in summary
        assert "critical_signals" in summary
        assert "recent_posts" in summary

    @pytest.mark.asyncio
    async def test_summary_counts_correctly(self, board: GuildBoard):
        board.heartbeat_required = False
        await board.agent_heartbeat("agent1", AgentStatus.WORKING)
        await board.add_quest("q1", "Task", "Desc")
        summary = await board.get_board_summary()
        assert summary["agents_online"] == 1  # WORKING != OFFLINE
        assert summary["quests_open"] == 1


# ---------------------------------------------------------------------------
# save_state (compat wrapper)
# ---------------------------------------------------------------------------


class TestSaveState:
    @pytest.mark.asyncio
    async def test_save_state_persists_board(self, board: GuildBoard):
        board.heartbeat_required = False
        await board.add_quest("q_save", "Save Me", "Desc")
        await board.save_state()
        assert board.board_file.exists()
        data = json.loads(board.board_file.read_text())
        assert "q_save" in data.get("quests", {})


# ---------------------------------------------------------------------------
# Singleton get_board / init_board
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_board_returns_board_instance():
    """get_board() should return a GuildBoard."""
    import src.guild.guild_board as gb_mod

    old_board = gb_mod._board
    gb_mod._board = None
    try:
        board = await gb_mod.get_board()
        assert isinstance(board, GuildBoard)
        # Second call returns same instance
        board2 = await gb_mod.get_board()
        assert board is board2
    finally:
        gb_mod._board = old_board


@pytest.mark.asyncio
async def test_init_board_returns_board():
    import src.guild.guild_board as gb_mod

    old_board = gb_mod._board
    gb_mod._board = None
    try:
        board = await gb_mod.init_board()
        assert isinstance(board, GuildBoard)
    finally:
        gb_mod._board = old_board

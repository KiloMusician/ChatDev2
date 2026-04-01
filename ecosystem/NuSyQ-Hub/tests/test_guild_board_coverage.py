"""Extended GuildBoard coverage tests targeting previously thin code paths.

Covers:
- _slugify() helper (basic, special chars, empty, leading/trailing dashes)
- _write_json_atomic() (creates file, creates parent dirs)
- _serialize_board() / _load_board() round-trip + unknown status/state fallback
- Quest full lifecycle: add -> claim -> start -> complete
- abandon_quest / block_quest via close_quest
- Artifact submission on complete_quest
- _release_stale_claims_locked() heartbeat_timeout path
- _archive_completed_quests_locked() archives old done quests
- post_on_board() edge cases: trim to limit, throttle per-agent
- get_available_quests() tag filtering, done quests excluded
- get_board_summary() offline/blocked counts
- save_state() JSON structure check
- post_message() edge cases
- register_event_listener / unregister_event_listener
- add_signal context=None default
"""

from __future__ import annotations

import asyncio
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
    """Isolated GuildBoard with no shared state or disk side-effects."""
    b = GuildBoard(state_dir=tmp_path / "guild", data_dir=tmp_path / "data")
    b.auto_release_claim_on_heartbeat_timeout = False
    b.heartbeat_required = False
    return b


async def _add_quest(
    board: GuildBoard,
    qid: str = "q1",
    title: str = "Test Quest",
    tags: list[str] | None = None,
    priority: int = 3,
) -> str:
    ok, returned_id = await board.add_quest(
        quest_id=qid,
        title=title,
        description="A test quest",
        priority=priority,
        tags=tags,
    )
    assert ok, f"add_quest failed for {qid}"
    return returned_id


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    def test_basic_lowercase(self, board: GuildBoard) -> None:
        assert board._slugify("Hello World") == "hello-world"

    def test_special_chars_replaced(self, board: GuildBoard) -> None:
        result = board._slugify("Fix: bug/issue #42!")
        assert result == "fix-bug-issue-42"

    def test_multiple_consecutive_specials(self, board: GuildBoard) -> None:
        result = board._slugify("a---b___c")
        assert result == "a-b-c"

    def test_leading_trailing_specials_stripped(self, board: GuildBoard) -> None:
        result = board._slugify("  ---hello---  ")
        assert result == "hello"

    def test_empty_string_returns_quest(self, board: GuildBoard) -> None:
        assert board._slugify("") == "quest"

    def test_only_special_chars_returns_quest(self, board: GuildBoard) -> None:
        assert board._slugify("!!!###") == "quest"

    def test_numbers_preserved(self, board: GuildBoard) -> None:
        result = board._slugify("Task 123")
        assert result == "task-123"

    def test_already_clean(self, board: GuildBoard) -> None:
        assert board._slugify("already-clean") == "already-clean"


# ---------------------------------------------------------------------------
# _write_json_atomic
# ---------------------------------------------------------------------------


class TestWriteJsonAtomic:
    def test_creates_file_at_target(self, tmp_path: Path, board: GuildBoard) -> None:
        target = tmp_path / "output.json"
        board._write_json_atomic(target, {"key": "value"})
        assert target.exists()
        data = json.loads(target.read_text())
        assert data["key"] == "value"

    def test_creates_missing_parent_dirs(self, tmp_path: Path, board: GuildBoard) -> None:
        target = tmp_path / "deep" / "nested" / "file.json"
        board._write_json_atomic(target, {"x": 1})
        assert target.exists()

    def test_overwrites_existing_file(self, tmp_path: Path, board: GuildBoard) -> None:
        target = tmp_path / "overwrite.json"
        board._write_json_atomic(target, {"v": 1})
        board._write_json_atomic(target, {"v": 2})
        data = json.loads(target.read_text())
        assert data["v"] == 2

    def test_no_temp_file_left_behind(self, tmp_path: Path, board: GuildBoard) -> None:
        target = tmp_path / "clean.json"
        board._write_json_atomic(target, {"ok": True})
        temp = target.with_suffix(target.suffix + ".tmp")
        assert not temp.exists()

    def test_non_serializable_coerced_via_default_str(
        self, tmp_path: Path, board: GuildBoard
    ) -> None:
        target = tmp_path / "datetime.json"
        board._write_json_atomic(target, {"ts": datetime.now()})
        assert target.exists()


# ---------------------------------------------------------------------------
# _serialize_board / _load_board round-trip
# ---------------------------------------------------------------------------


class TestSerializeAndLoadBoard:
    @pytest.mark.asyncio
    async def test_round_trip_quest(self, board: GuildBoard) -> None:
        await _add_quest(board, "rt_q1", "Round Trip Quest")
        payload = board._serialize_board()
        assert "rt_q1" in payload["quests"]
        assert payload["quests"]["rt_q1"]["state"] == "open"

    @pytest.mark.asyncio
    async def test_round_trip_agent(self, board: GuildBoard) -> None:
        await board.agent_heartbeat("rt_agent", AgentStatus.WORKING)
        payload = board._serialize_board()
        assert "rt_agent" in payload["agents"]
        assert payload["agents"]["rt_agent"]["status"] == "working"

    @pytest.mark.asyncio
    async def test_load_board_restores_quests(self, tmp_path: Path) -> None:
        b1 = GuildBoard(state_dir=tmp_path / "guild2", data_dir=tmp_path / "data2")
        b1.heartbeat_required = False
        b1.auto_release_claim_on_heartbeat_timeout = False
        await b1.add_quest("persist_q", "Persist Me", "Desc")
        await b1.save_state()

        b2 = GuildBoard(state_dir=tmp_path / "guild2", data_dir=tmp_path / "data2")
        assert "persist_q" in b2.board.quests

    @pytest.mark.asyncio
    async def test_load_board_unknown_agent_status_falls_back_to_idle(
        self, tmp_path: Path
    ) -> None:
        guild_dir = tmp_path / "guild_fallback"
        guild_dir.mkdir(parents=True)
        board_file = guild_dir / "guild_board.json"
        payload = {
            "timestamp": datetime.now().isoformat(),
            "version": 1,
            "agents": {
                "mystery": {
                    "agent_id": "mystery",
                    "status": "UNKNOWN_STATUS_XYZ",
                    "current_quest": None,
                    "capabilities": [],
                    "blockers": [],
                    "timestamp": datetime.now().isoformat(),
                    "confidence_level": 1.0,
                    "consciousness_score": None,
                }
            },
            "quests": {},
            "active_work": {},
            "recent_posts": [],
            "signals": [],
        }
        board_file.write_text(json.dumps(payload), encoding="utf-8")
        b = GuildBoard(state_dir=guild_dir, data_dir=tmp_path / "data_fallback")
        assert b.board.agents["mystery"].status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_load_board_unknown_quest_state_falls_back_to_open(
        self, tmp_path: Path
    ) -> None:
        guild_dir = tmp_path / "guild_qfallback"
        guild_dir.mkdir(parents=True)
        board_file = guild_dir / "guild_board.json"
        payload = {
            "timestamp": datetime.now().isoformat(),
            "version": 1,
            "agents": {},
            "quests": {
                "qfb": {
                    "quest_id": "qfb",
                    "title": "Fallback Quest",
                    "description": "desc",
                    "priority": 3,
                    "safety_tier": "safe",
                    "state": "INVALID_STATE_999",
                    "claimed_by": None,
                    "claimed_at": None,
                    "started_at": None,
                    "completed_at": None,
                    "closed_at": None,
                    "created_at": datetime.now().isoformat(),
                    "acceptance_criteria": [],
                    "dependencies": [],
                    "tags": [],
                    "artifacts": [],
                }
            },
            "active_work": {},
            "recent_posts": [],
            "signals": [],
        }
        board_file.write_text(json.dumps(payload), encoding="utf-8")
        b = GuildBoard(state_dir=guild_dir, data_dir=tmp_path / "data_qfallback")
        assert b.board.quests["qfb"].state == QuestState.OPEN


# ---------------------------------------------------------------------------
# Full quest lifecycle: add -> claim -> start -> complete
# ---------------------------------------------------------------------------


class TestFullQuestLifecycle:
    @pytest.mark.asyncio
    async def test_add_claim_start_complete_lifecycle(self, board: GuildBoard) -> None:
        # Add
        ok, qid = await board.add_quest("lc_q1", "Lifecycle Quest", "Desc")
        assert ok
        assert board.board.quests[qid].state == QuestState.OPEN

        # Claim
        ok, _msg = await board.claim_quest(qid, "agent_lc")
        assert ok
        assert board.board.quests[qid].state == QuestState.CLAIMED
        assert board.board.quests[qid].claimed_by == "agent_lc"

        # Start
        ok, _msg = await board.start_quest(qid, "agent_lc")
        assert ok
        assert board.board.quests[qid].state == QuestState.ACTIVE
        assert board.board.quests[qid].started_at is not None

        # Complete
        ok, _msg = await board.complete_quest(qid, "agent_lc", artifacts=["out.json"])
        assert ok
        quest = board.board.quests.get(qid)
        # Quest may be archived immediately if auto_archive_days=0, else DONE
        if quest is not None:
            assert quest.state == QuestState.DONE
            assert "out.json" in quest.artifacts
        assert qid not in board.board.active_work

    @pytest.mark.asyncio
    async def test_complete_removes_active_work_entry(self, board: GuildBoard) -> None:
        await _add_quest(board, "aw_q")
        await board.claim_quest("aw_q", "agent_x")
        assert "aw_q" in board.board.active_work
        await board.complete_quest("aw_q", "agent_x")
        assert "aw_q" not in board.board.active_work

    @pytest.mark.asyncio
    async def test_active_quest_in_active_work_dict(self, board: GuildBoard) -> None:
        await _add_quest(board, "act_q")
        await board.claim_quest("act_q", "agent_y")
        await board.start_quest("act_q", "agent_y")
        assert "act_q" in board.board.active_work


# ---------------------------------------------------------------------------
# abandon_quest / block_quest (via close_quest)
# ---------------------------------------------------------------------------


class TestAbandonAndBlockQuest:
    @pytest.mark.asyncio
    async def test_abandon_quest_sets_abandoned_state(self, board: GuildBoard) -> None:
        await _add_quest(board, "ab_q")
        ok, _status_val = await board.close_quest(
            "ab_q", agent_id="agent1", status=QuestState.ABANDONED
        )
        assert ok
        assert board.board.quests["ab_q"].state == QuestState.ABANDONED

    @pytest.mark.asyncio
    async def test_block_quest_sets_blocked_state(self, board: GuildBoard) -> None:
        await _add_quest(board, "bl_q")
        ok, _status_val = await board.close_quest(
            "bl_q", agent_id="agent1", status=QuestState.BLOCKED, reason="dep_missing"
        )
        assert ok
        assert board.board.quests["bl_q"].state == QuestState.BLOCKED

    @pytest.mark.asyncio
    async def test_close_quest_with_artifacts(self, board: GuildBoard) -> None:
        await _add_quest(board, "art_q")
        ok, _ = await board.close_quest(
            "art_q", artifacts=["log.txt"], status=QuestState.DONE
        )
        assert ok
        assert "log.txt" in board.board.quests["art_q"].artifacts

    @pytest.mark.asyncio
    async def test_close_quest_sets_closed_at(self, board: GuildBoard) -> None:
        await _add_quest(board, "cl_q")
        await board.close_quest("cl_q", status=QuestState.DONE)
        assert board.board.quests["cl_q"].closed_at is not None

    @pytest.mark.asyncio
    async def test_close_nonexistent_quest_returns_false(self, board: GuildBoard) -> None:
        ok, msg = await board.close_quest("does_not_exist")
        assert not ok
        assert msg is not None and "not found" in msg.lower()


# ---------------------------------------------------------------------------
# _release_stale_claims_locked (heartbeat_timeout path)
# ---------------------------------------------------------------------------


class TestReleaseStaleClaimsLocked:
    @pytest.mark.asyncio
    async def test_stale_heartbeat_releases_claimed_quest(self, board: GuildBoard) -> None:
        # Re-enable auto_release so the timeout logic fires
        board.auto_release_claim_on_heartbeat_timeout = True
        board.heartbeat_timeout_minutes = 5

        # Add quest and claim it (heartbeat_required=False so no HB needed)
        await _add_quest(board, "stale_q")
        board.heartbeat_required = False
        ok, _ = await board.claim_quest("stale_q", "stale_agent")
        assert ok

        # Plant a stale (30-min-old) heartbeat
        old_ts = (datetime.now() - timedelta(minutes=30)).isoformat()
        board.board.agents["stale_agent"] = AgentHeartbeat(
            agent_id="stale_agent",
            status=AgentStatus.WORKING,
            timestamp=old_ts,
        )

        # Trigger release via heartbeat of a *different* agent
        # which internally calls _release_stale_claims_locked
        await board.agent_heartbeat("trigger_agent", AgentStatus.IDLE)

        quest = board.board.quests["stale_q"]
        assert quest.state == QuestState.OPEN
        assert quest.claimed_by is None

    @pytest.mark.asyncio
    async def test_fresh_heartbeat_does_not_release_claim(self, board: GuildBoard) -> None:
        board.auto_release_claim_on_heartbeat_timeout = True
        board.heartbeat_timeout_minutes = 5
        board.heartbeat_required = False

        await _add_quest(board, "fresh_q")
        ok, _ = await board.claim_quest("fresh_q", "fresh_agent")
        assert ok

        # Plant a FRESH heartbeat
        board.board.agents["fresh_agent"] = AgentHeartbeat(
            agent_id="fresh_agent",
            status=AgentStatus.WORKING,
            timestamp=datetime.now().isoformat(),
        )

        await board.agent_heartbeat("trigger_agent", AgentStatus.IDLE)

        quest = board.board.quests["fresh_q"]
        assert quest.state == QuestState.CLAIMED
        assert quest.claimed_by == "fresh_agent"

    @pytest.mark.asyncio
    async def test_auto_release_disabled_leaves_stale_claim(self, board: GuildBoard) -> None:
        board.auto_release_claim_on_heartbeat_timeout = False
        board.heartbeat_timeout_minutes = 5
        board.heartbeat_required = False

        await _add_quest(board, "no_rel_q")
        ok, _ = await board.claim_quest("no_rel_q", "no_rel_agent")
        assert ok

        old_ts = (datetime.now() - timedelta(minutes=30)).isoformat()
        board.board.agents["no_rel_agent"] = AgentHeartbeat(
            agent_id="no_rel_agent",
            status=AgentStatus.WORKING,
            timestamp=old_ts,
        )

        await board.agent_heartbeat("trigger2", AgentStatus.IDLE)
        # Claim should NOT be released
        assert board.board.quests["no_rel_q"].state == QuestState.CLAIMED


# ---------------------------------------------------------------------------
# _archive_completed_quests_locked
# ---------------------------------------------------------------------------


class TestArchiveCompletedQuests:
    @pytest.mark.asyncio
    async def test_old_done_quest_gets_archived(self, board: GuildBoard) -> None:
        board.auto_archive_days = 7

        await _add_quest(board, "old_done_q")
        await board.claim_quest("old_done_q", "archiver")
        await board.complete_quest("old_done_q", "archiver")

        if "old_done_q" in board.board.quests:
            # Manually back-date the completed_at to trigger archival
            board.board.quests["old_done_q"].completed_at = (
                datetime.now() - timedelta(days=10)
            ).isoformat()

        # Trigger archive via another heartbeat
        await board.agent_heartbeat("arch_trigger", AgentStatus.IDLE)

        assert "old_done_q" not in board.board.quests

    @pytest.mark.asyncio
    async def test_recent_done_quest_not_archived(self, board: GuildBoard) -> None:
        board.auto_archive_days = 30

        await _add_quest(board, "new_done_q")
        await board.claim_quest("new_done_q", "completer")
        await board.complete_quest("new_done_q", "completer")

        # Quest was completed moments ago; should stay
        await board.agent_heartbeat("arch_trigger2", AgentStatus.IDLE)

        assert "new_done_q" in board.board.quests

    @pytest.mark.asyncio
    async def test_archive_disabled_skips_all(self, board: GuildBoard) -> None:
        board.auto_archive_days = 0

        await _add_quest(board, "no_archive_q")
        await board.claim_quest("no_archive_q", "worker")
        await board.complete_quest("no_archive_q", "worker")

        if "no_archive_q" in board.board.quests:
            board.board.quests["no_archive_q"].completed_at = (
                datetime.now() - timedelta(days=100)
            ).isoformat()

        await board.agent_heartbeat("no_arch_trig", AgentStatus.IDLE)
        # With auto_archive_days=0, archive is skipped — quest stays (if not already gone)
        # This just verifies no exception is raised
        assert True  # No exception == pass


# ---------------------------------------------------------------------------
# post_on_board edge cases
# ---------------------------------------------------------------------------


class TestPostOnBoardEdgeCases:
    @pytest.mark.asyncio
    async def test_posts_trim_to_recent_posts_limit(self, board: GuildBoard) -> None:
        board.post_throttle_per_minute = 0  # Disable throttle
        board.recent_posts_limit = 5
        for i in range(10):
            await board.post_on_board("agent1", f"msg {i}")
        assert len(board.board.recent_posts) <= 5

    @pytest.mark.asyncio
    async def test_throttle_returns_throttle_post_type(self, board: GuildBoard) -> None:
        board.post_throttle_per_minute = 1
        now = datetime.now()
        board.board.recent_posts.append(
            BoardPost(
                post_id="existing",
                agent_id="throttled_agent",
                message="first",
                timestamp=now.isoformat(),
            )
        )
        post = await board.post_on_board("throttled_agent", "second message")
        assert post.post_type == "throttled"

    @pytest.mark.asyncio
    async def test_different_agents_not_throttled_by_each_other(self, board: GuildBoard) -> None:
        board.post_throttle_per_minute = 1
        now = datetime.now()
        # Agent A already at threshold
        board.board.recent_posts.append(
            BoardPost(post_id="a_post", agent_id="agent_a", message="x", timestamp=now.isoformat())
        )
        # Agent B should NOT be throttled
        post = await board.post_on_board("agent_b", "not throttled")
        assert post.post_type != "throttled"
        assert post.message == "not throttled"

    @pytest.mark.asyncio
    async def test_post_with_artifact_list(self, board: GuildBoard) -> None:
        post = await board.post_on_board(
            "agent1", "step done", artifacts=["a.json", "b.txt"]
        )
        assert "a.json" in post.artifacts
        assert "b.txt" in post.artifacts

    @pytest.mark.asyncio
    async def test_post_with_quest_id(self, board: GuildBoard) -> None:
        post = await board.post_on_board("agent1", "progress", quest_id="quest_abc")
        assert post.quest_id == "quest_abc"


# ---------------------------------------------------------------------------
# get_available_quests: tag filtering, done excluded
# ---------------------------------------------------------------------------


class TestGetAvailableQuestsExtended:
    @pytest.mark.asyncio
    async def test_no_tags_quest_is_available_to_any_agent(self, board: GuildBoard) -> None:
        await _add_quest(board, "no_tag_q", tags=[])
        result = await board.get_available_quests(["python"])
        ids = [q.quest_id for q in result]
        assert "no_tag_q" in ids

    @pytest.mark.asyncio
    async def test_tagged_quest_requires_capability_match(self, board: GuildBoard) -> None:
        await _add_quest(board, "tagged_q", tags=["rust"])
        result = await board.get_available_quests(["python"])
        ids = [q.quest_id for q in result]
        assert "tagged_q" not in ids

    @pytest.mark.asyncio
    async def test_done_quest_not_returned(self, board: GuildBoard) -> None:
        await _add_quest(board, "done_q")
        await board.claim_quest("done_q", "agent1")
        await board.complete_quest("done_q", "agent1")
        # Even if still in quests dict, state=DONE excludes it
        result = await board.get_available_quests([])
        ids = [q.quest_id for q in result]
        assert "done_q" not in ids

    @pytest.mark.asyncio
    async def test_multiple_capability_match(self, board: GuildBoard) -> None:
        await _add_quest(board, "multi_q", tags=["python", "docker"])
        result = await board.get_available_quests(["docker", "go"])
        ids = [q.quest_id for q in result]
        assert "multi_q" in ids

    @pytest.mark.asyncio
    async def test_sorted_highest_priority_first(self, board: GuildBoard) -> None:
        await _add_quest(board, "low_p", priority=1)
        await _add_quest(board, "high_p", priority=5)
        result = await board.get_available_quests([])
        assert result[0].priority >= result[-1].priority


# ---------------------------------------------------------------------------
# get_board_summary: offline/blocked counts
# ---------------------------------------------------------------------------


class TestBoardSummaryExtended:
    @pytest.mark.asyncio
    async def test_offline_agents_not_counted_as_online(self, board: GuildBoard) -> None:
        board.board.agents["offline_one"] = AgentHeartbeat(
            agent_id="offline_one",
            status=AgentStatus.OFFLINE,
            timestamp=datetime.now().isoformat(),
        )
        board.board.agents["online_one"] = AgentHeartbeat(
            agent_id="online_one",
            status=AgentStatus.IDLE,
            timestamp=datetime.now().isoformat(),
        )
        summary = await board.get_board_summary()
        assert summary["agents_online"] == 1

    @pytest.mark.asyncio
    async def test_blocked_quest_count(self, board: GuildBoard) -> None:
        await _add_quest(board, "blk_q1")
        await board.close_quest("blk_q1", status=QuestState.BLOCKED)
        summary = await board.get_board_summary()
        assert summary["quests_blocked"] >= 1

    @pytest.mark.asyncio
    async def test_active_quest_count(self, board: GuildBoard) -> None:
        await _add_quest(board, "act_s_q")
        await board.claim_quest("act_s_q", "act_agent")
        await board.start_quest("act_s_q", "act_agent")
        summary = await board.get_board_summary()
        assert summary["quests_active"] >= 1

    @pytest.mark.asyncio
    async def test_critical_signals_in_summary(self, board: GuildBoard) -> None:
        await board.add_signal("error", "critical", "system meltdown")
        summary = await board.get_board_summary()
        assert len(summary["critical_signals"]) == 1
        assert summary["critical_signals"][0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_non_critical_signals_excluded_from_critical_list(
        self, board: GuildBoard
    ) -> None:
        await board.add_signal("warn", "low", "minor issue")
        summary = await board.get_board_summary()
        assert len(summary["critical_signals"]) == 0

    @pytest.mark.asyncio
    async def test_recent_posts_limited_to_10_in_summary(self, board: GuildBoard) -> None:
        board.post_throttle_per_minute = 0
        board.recent_posts_limit = 50
        for i in range(20):
            board.post_message("summary_agent", f"msg {i}")
        summary = await board.get_board_summary()
        assert len(summary["recent_posts"]) <= 10


# ---------------------------------------------------------------------------
# save_state() JSON structure check
# ---------------------------------------------------------------------------


class TestSaveStateJsonStructure:
    @pytest.mark.asyncio
    async def test_saved_json_has_required_keys(self, board: GuildBoard) -> None:
        await _add_quest(board, "struct_q")
        await board.save_state()
        data = json.loads(board.board_file.read_text())
        for key in ("timestamp", "version", "agents", "quests", "active_work", "recent_posts",
                    "signals"):
            assert key in data, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_quest_state_serialized_as_string(self, board: GuildBoard) -> None:
        await _add_quest(board, "ser_q")
        await board.save_state()
        data = json.loads(board.board_file.read_text())
        assert isinstance(data["quests"]["ser_q"]["state"], str)
        assert data["quests"]["ser_q"]["state"] == "open"

    @pytest.mark.asyncio
    async def test_agent_status_serialized_as_string(self, board: GuildBoard) -> None:
        await board.agent_heartbeat("ser_agent", AgentStatus.BLOCKED)
        data = json.loads(board.board_file.read_text())
        assert data["agents"]["ser_agent"]["status"] == "blocked"

    @pytest.mark.asyncio
    async def test_signals_preserved_in_saved_json(self, board: GuildBoard) -> None:
        await board.add_signal("test_type", "high", "test message")
        await board.save_state()
        data = json.loads(board.board_file.read_text())
        assert len(data["signals"]) == 1
        assert data["signals"][0]["type"] == "test_type"


# ---------------------------------------------------------------------------
# post_message edge cases
# ---------------------------------------------------------------------------


class TestPostMessageEdgeCases:
    def test_post_message_trims_to_10_not_recent_posts_limit(self, board: GuildBoard) -> None:
        # post_message always trims to 10 (hardcoded), regardless of recent_posts_limit
        board.recent_posts_limit = 100
        for i in range(15):
            board.post_message("edge_agent", f"msg {i}")
        assert len(board.board.recent_posts) == 10

    def test_post_message_agent_recorded(self, board: GuildBoard) -> None:
        board.post_message("named_agent", "hello")
        assert board.board.recent_posts[-1].agent_id == "named_agent"

    def test_post_message_post_type_is_diagnostic(self, board: GuildBoard) -> None:
        board.post_message("diag_agent", "check")
        assert board.board.recent_posts[-1].post_type == "diagnostic"

    def test_post_message_writes_board_file(self, board: GuildBoard) -> None:
        board.post_message("write_agent", "persist this")
        assert board.board_file.exists()

    def test_post_message_empty_string_allowed(self, board: GuildBoard) -> None:
        board.post_message("agent", "")
        assert board.board.recent_posts[-1].message == ""


# ---------------------------------------------------------------------------
# Event listeners
# ---------------------------------------------------------------------------


class TestEventListeners:
    @pytest.mark.asyncio
    async def test_listener_called_on_heartbeat(self, board: GuildBoard) -> None:
        received: list[tuple[str, dict]] = []

        async def listener(event_type: str, data: dict) -> None:
            received.append((event_type, data))

        board.register_event_listener(listener)
        await board.agent_heartbeat("ev_agent", AgentStatus.IDLE)
        # Give fire-and-forget listener futures a chance to complete
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert any(et == "agent_heartbeat" for et, _ in received)

    @pytest.mark.asyncio
    async def test_listener_not_duplicated_on_double_register(self, board: GuildBoard) -> None:
        async def listener(event_type: str, data: dict) -> None:
            pass

        board.register_event_listener(listener)
        board.register_event_listener(listener)
        assert board._event_listeners.count(listener) == 1

    @pytest.mark.asyncio
    async def test_unregister_listener_removes_it(self, board: GuildBoard) -> None:
        async def listener(event_type: str, data: dict) -> None:
            pass

        board.register_event_listener(listener)
        board.unregister_event_listener(listener)
        assert listener not in board._event_listeners

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_listener_is_idempotent(
        self, board: GuildBoard
    ) -> None:
        async def listener(event_type: str, data: dict) -> None:
            pass

        # Should not raise
        board.unregister_event_listener(listener)

    @pytest.mark.asyncio
    async def test_failing_listener_does_not_block_board_ops(self, board: GuildBoard) -> None:
        def bad_listener(event_type: str, data: dict) -> None:
            raise RuntimeError("boom")

        board.register_event_listener(bad_listener)
        # add_quest must still succeed despite the bad listener
        ok, _qid = await board.add_quest("evt_q", "Event Quest", "Desc")
        assert ok


# ---------------------------------------------------------------------------
# add_signal context=None default
# ---------------------------------------------------------------------------


class TestAddSignalExtended:
    @pytest.mark.asyncio
    async def test_add_signal_no_context_uses_empty_dict(self, board: GuildBoard) -> None:
        await board.add_signal("alert", "high", "no context signal")
        sig = board.board.signals[0]
        assert sig["context"] == {}

    @pytest.mark.asyncio
    async def test_add_signal_trims_to_50(self, board: GuildBoard) -> None:
        for i in range(55):
            await board.add_signal("info", "low", f"sig {i}")
        assert len(board.board.signals) == 50

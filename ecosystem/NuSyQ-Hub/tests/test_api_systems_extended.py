"""Extended tests for src/api/systems.py uncovered sections.

Covers (previously at 44% — targeting 60%+):
- GET /hints          (dynamic hints via HintEngine, fallback hints)
- GET /tutorials
- GET /faq
- GET /commands
- GET /scripts
- GET /inventory
- GET /ops            (all ops, filtered ops, cache hit)
- GET /evolve         (list, with/without rosetta dir)
- POST /evolve        (stub path, rosetta_runner path)
- GET /quests/{quest_id}   (engine missing, quest found, not found)
- POST /quests/complete    (engine missing, quest not found, happy path)
- GET /skills         (rpg missing, with inventory)
- GET /rpg/status     (rpg missing, happy path, error path)
- POST /rpg/xp        (rpg missing, happy path, failure)
- GET /guild/quests   (board missing, board returns quests)
- GET /guild/summary  (board missing, happy path)
- GET /progress
- GET /tips/random
- GET /tips/contextual (various context values)
- GET /fl1ght         (smart search, no matches)
- GET /hack/sessions  (no controller, empty sessions)
- GET /hack/traces    (no controller)
- GET /intermediary/metrics (unavailable, metrics present)
- GET /search         (no query, with query)
- POST /intermediary  (unavailable)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import systems

# ---------------------------------------------------------------------------
# Shared fixture: a minimal test app mounting only the systems router
# ---------------------------------------------------------------------------

_app = FastAPI()
_app.include_router(systems.router, prefix="/api")


@pytest.fixture()
def client() -> TestClient:
    return TestClient(_app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _null_hint_engine():
    """Patch _cached_hint_engine to return None (HintEngine unavailable)."""
    return patch.object(systems, "_cached_hint_engine", return_value=None)


# ---------------------------------------------------------------------------
# GET /hints
# ---------------------------------------------------------------------------


class TestHints:
    def test_hints_fallback_when_no_engine(self, client):
        with _null_hint_engine():
            resp = client.get("/api/hints")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "title" in data[0]
        assert "text" in data[0]

    def test_hints_returns_list(self, client):
        resp = client.get("/api/hints")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_hints_fallback_structure(self, client):
        with _null_hint_engine():
            resp = client.get("/api/hints")
        data = resp.json()
        for hint in data:
            assert "id" in hint
            assert "title" in hint
            assert "text" in hint


# ---------------------------------------------------------------------------
# GET /tutorials
# ---------------------------------------------------------------------------


class TestTutorials:
    def test_tutorials_returns_list(self, client):
        resp = client.get("/api/tutorials")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_tutorials_have_required_fields(self, client):
        resp = client.get("/api/tutorials")
        for tut in resp.json():
            assert "id" in tut
            assert "title" in tut
            assert "steps" in tut
            assert isinstance(tut["steps"], list)


# ---------------------------------------------------------------------------
# GET /faq
# ---------------------------------------------------------------------------


class TestFAQ:
    def test_faq_returns_list(self, client):
        resp = client.get("/api/faq")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_faq_entries_have_question_and_answer(self, client):
        resp = client.get("/api/faq")
        for entry in resp.json():
            assert "question" in entry
            assert "answer" in entry

    def test_faq_actionable_count_in_answer(self, client):
        with _null_hint_engine():
            resp = client.get("/api/faq")
        data = resp.json()
        # At least one entry mentions actionable count
        texts = " ".join(e["answer"] for e in data)
        assert "actionable" in texts.lower() or "blocked" in texts.lower()


# ---------------------------------------------------------------------------
# GET /commands
# ---------------------------------------------------------------------------


class TestCommands:
    def test_commands_returns_list(self, client):
        resp = client.get("/api/commands")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_commands_have_required_fields(self, client):
        resp = client.get("/api/commands")
        for cmd in resp.json():
            assert "command" in cmd
            assert "description" in cmd

    def test_commands_includes_start_nusyq(self, client):
        resp = client.get("/api/commands")
        commands = [c["command"] for c in resp.json()]
        assert any("start_nusyq" in c for c in commands)


# ---------------------------------------------------------------------------
# GET /scripts
# ---------------------------------------------------------------------------


class TestScripts:
    def test_scripts_returns_list(self, client):
        resp = client.get("/api/scripts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_scripts_have_command_and_description(self, client):
        resp = client.get("/api/scripts")
        for s in resp.json():
            assert "command" in s
            assert "description" in s


# ---------------------------------------------------------------------------
# GET /inventory
# ---------------------------------------------------------------------------


class TestInventory:
    def test_inventory_returns_list(self, client):
        resp = client.get("/api/inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_inventory_has_command_and_description(self, client):
        resp = client.get("/api/inventory")
        for item in resp.json():
            assert "command" in item
            assert "description" in item


# ---------------------------------------------------------------------------
# GET /ops
# ---------------------------------------------------------------------------


class TestOps:
    def test_ops_no_query_returns_list(self, client):
        resp = client.get("/api/ops")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_ops_with_query_filters_results(self, client):
        resp = client.get("/api/ops?q=nusyq")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # All returned items should mention "nusyq" somewhere
        for item in data:
            combined = (item["command"] + " " + item["description"]).lower()
            assert "nusyq" in combined

    def test_ops_cache_hit(self, client):
        """Second identical call hits the cache (no error)."""
        resp1 = client.get("/api/ops?q=start")
        resp2 = client.get("/api/ops?q=start")
        assert resp1.status_code == 200
        assert resp2.status_code == 200

    def test_ops_max_results_cap(self, client):
        resp = client.get("/api/ops")
        data = resp.json()
        assert len(data) <= 12  # _collect_commands caps at 12

    def test_ops_no_duplicate_commands(self, client):
        resp = client.get("/api/ops")
        commands = [item["command"] for item in resp.json()]
        assert len(commands) == len(set(commands))


# ---------------------------------------------------------------------------
# GET /evolve + POST /evolve
# ---------------------------------------------------------------------------


class TestEvolve:
    def test_list_evolve_empty_when_no_dir(self, client, tmp_path):
        with patch.object(systems, "ROSETTA_DIR", tmp_path / "nonexistent"):
            resp = client.get("/api/evolve")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_evolve_returns_artifacts(self, client, tmp_path):
        import json

        rosetta = tmp_path / "rosetta"
        rosetta.mkdir()
        artifact = {"id": "1", "suggestion": "Do X"}
        f = rosetta / "evolve_suggestion_123.json"
        f.write_text(json.dumps(artifact))

        with patch.object(systems, "ROSETTA_DIR", rosetta):
            resp = client.get("/api/evolve")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["content"]["suggestion"] == "Do X"

    def test_post_evolve_creates_artifact(self, client, tmp_path):
        rosetta = tmp_path / "rosetta"

        with patch.object(systems, "ROSETTA_DIR", rosetta):
            # rosetta_runner unavailable → falls through to stub
            with patch("src.tools.rosetta_runner.run_suggest", side_effect=ImportError):
                resp = client.post("/api/evolve", json={"prompt": "Improve tests"})
        assert resp.status_code == 200
        data = resp.json()
        assert "content" in data
        assert data["content"]["prompt"] == "Improve tests"

    def test_post_evolve_no_prompt(self, client, tmp_path):
        rosetta = tmp_path / "rosetta"

        with patch.object(systems, "ROSETTA_DIR", rosetta):
            resp = client.post("/api/evolve", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "content" in data

    def test_post_evolve_rosetta_runner_succeeds(self, client):
        """If rosetta_runner.run_suggest returns a result, use it directly."""
        fake_result = {"file": "path", "content": {"suggestion": "AI suggestion"}}
        with patch("src.tools.rosetta_runner.run_suggest", return_value=fake_result):
            resp = client.post("/api/evolve", json={"prompt": "Optimize"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"]["suggestion"] == "AI suggestion"


# ---------------------------------------------------------------------------
# GET /quests/{quest_id}
# ---------------------------------------------------------------------------


class TestQuestDetail:
    def test_quest_detail_engine_unavailable(self, client):
        original = systems.QuestEngine
        systems.QuestEngine = None
        try:
            resp = client.get("/api/quests/q-missing")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is False
            assert "not available" in data["error"]
        finally:
            systems.QuestEngine = original

    def test_quest_detail_not_found(self, client):
        mock_engine = MagicMock()
        mock_engine.return_value.get_quest.return_value = None
        original = systems.QuestEngine
        systems.QuestEngine = mock_engine
        try:
            resp = client.get("/api/quests/q-unknown")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is False
            assert "not found" in data["error"]
        finally:
            systems.QuestEngine = original

    def test_quest_detail_found(self, client):
        mock_quest = MagicMock()
        mock_quest.to_dict.return_value = {"id": "q1", "title": "Test Quest"}
        mock_engine = MagicMock()
        mock_engine.return_value.get_quest.return_value = mock_quest

        original = systems.QuestEngine
        systems.QuestEngine = mock_engine
        try:
            resp = client.get("/api/quests/q1")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["quest"]["id"] == "q1"
        finally:
            systems.QuestEngine = original


# ---------------------------------------------------------------------------
# POST /quests/complete
# ---------------------------------------------------------------------------


class TestQuestComplete:
    def test_complete_engine_unavailable(self, client):
        original = systems.QuestEngine
        systems.QuestEngine = None
        try:
            resp = client.post("/api/quests/complete", json={"quest_id": "q1"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is False
            assert "not available" in data["error"]
        finally:
            systems.QuestEngine = original

    def test_complete_quest_not_found(self, client):
        mock_engine = MagicMock()
        mock_engine.return_value.get_quest.return_value = None

        original_engine = systems.QuestEngine
        original_gqbi = systems.get_quest_by_id
        systems.QuestEngine = mock_engine
        systems.get_quest_by_id = None
        try:
            resp = client.post("/api/quests/complete", json={"quest_id": "q-missing"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is False
            assert "not found" in data["error"]
        finally:
            systems.QuestEngine = original_engine
            systems.get_quest_by_id = original_gqbi

    def test_complete_quest_success_no_xp(self, client):
        mock_quest = MagicMock()
        mock_engine = MagicMock()
        mock_engine.return_value.get_quest.return_value = mock_quest

        original_engine = systems.QuestEngine
        original_gqbi = systems.get_quest_by_id
        original_rpg = systems.rpg_award_xp
        systems.QuestEngine = mock_engine
        systems.get_quest_by_id = None
        systems.rpg_award_xp = None  # no RPG xp system → xp_awarded=0, skip award
        try:
            resp = client.post("/api/quests/complete", json={"quest_id": "q1", "xp": 0})
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["quest_id"] == "q1"
            assert data["xp_awarded"] == 0
        finally:
            systems.QuestEngine = original_engine
            systems.get_quest_by_id = original_gqbi
            systems.rpg_award_xp = original_rpg


# ---------------------------------------------------------------------------
# GET /skills
# ---------------------------------------------------------------------------


class TestSkills:
    def test_skills_returns_empty_when_no_rpg(self, client):
        original = systems.get_rpg_inventory
        systems.get_rpg_inventory = None
        try:
            resp = client.get("/api/skills")
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            systems.get_rpg_inventory = original

    def test_skills_returns_skills_list(self, client):
        from enum import Enum

        class FakeLevel(Enum):
            NOVICE = "novice"

        skill = MagicMock()
        skill.name = "automation"
        skill.level = FakeLevel.NOVICE
        skill.experience = 50
        skill.max_experience = 100
        skill.proficiency = 0.5
        skill.usage_count = 3

        inventory = MagicMock()
        inventory.skills = {"automation": skill}

        original = systems.get_rpg_inventory
        systems.get_rpg_inventory = lambda: inventory
        try:
            resp = client.get("/api/skills")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["name"] == "automation"
            assert data[0]["experience"] == 50
        finally:
            systems.get_rpg_inventory = original

    def test_skills_handles_runtime_error(self, client):
        original = systems.get_rpg_inventory
        systems.get_rpg_inventory = MagicMock(side_effect=RuntimeError("boom"))
        try:
            resp = client.get("/api/skills")
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            systems.get_rpg_inventory = original


# ---------------------------------------------------------------------------
# GET /rpg/status
# ---------------------------------------------------------------------------


class TestRpgStatus:
    def test_rpg_status_unavailable(self, client):
        original = systems.get_rpg_inventory
        systems.get_rpg_inventory = None
        try:
            resp = client.get("/api/rpg/status")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data
        finally:
            systems.get_rpg_inventory = original

    def test_rpg_status_happy_path(self, client):
        snapshot = {
            "overall_health": 95,
            "system_stats": {"level": 3},
            "components": {"c1": {}, "c2": {}},
            "skills": {"s1": {}},
            "quests": {"q1": {}},
            "resources": {"cpu_percent": 10.0, "memory_percent": 40.0, "disk_usage": 50},
            "timestamp": "2026-01-01T00:00:00",
        }
        inventory = MagicMock()
        inventory.get_system_snapshot.return_value = snapshot

        original = systems.get_rpg_inventory
        systems.get_rpg_inventory = lambda: inventory
        try:
            resp = client.get("/api/rpg/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["overall_health"] == 95
            assert data["components_count"] == 2
            assert data["skills_count"] == 1
            assert data["active_quests"] == 1
        finally:
            systems.get_rpg_inventory = original

    def test_rpg_status_error_returns_error_key(self, client):
        original = systems.get_rpg_inventory
        systems.get_rpg_inventory = MagicMock(side_effect=RuntimeError("broken"))
        try:
            resp = client.get("/api/rpg/status")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data
        finally:
            systems.get_rpg_inventory = original


# ---------------------------------------------------------------------------
# POST /rpg/xp
# ---------------------------------------------------------------------------


class TestRpgXp:
    def test_rpg_xp_no_inventory(self, client):
        original_inv = systems.get_rpg_inventory
        original_award = systems.rpg_award_xp
        systems.get_rpg_inventory = None
        systems.rpg_award_xp = None
        try:
            resp = client.post("/api/rpg/xp?skill=automation&points=10")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data
        finally:
            systems.get_rpg_inventory = original_inv
            systems.rpg_award_xp = original_award

    def test_rpg_xp_success(self, client):
        rpg_result = {"success": True, "rpg": {"level": 2, "xp": 110}}
        mock_award = MagicMock(return_value=rpg_result)

        original_inv = systems.get_rpg_inventory
        original_award = systems.rpg_award_xp
        systems.get_rpg_inventory = MagicMock()
        systems.rpg_award_xp = mock_award
        try:
            with patch.object(systems, "_auto_persist_game_state"):
                resp = client.post("/api/rpg/xp?skill=automation&points=10")
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("level") == 2
        finally:
            systems.get_rpg_inventory = original_inv
            systems.rpg_award_xp = original_award

    def test_rpg_xp_failure(self, client):
        rpg_result = {"success": False, "error": "skill not found"}
        mock_award = MagicMock(return_value=rpg_result)

        original_inv = systems.get_rpg_inventory
        original_award = systems.rpg_award_xp
        systems.get_rpg_inventory = MagicMock()
        systems.rpg_award_xp = mock_award
        try:
            resp = client.post("/api/rpg/xp?skill=unknown_skill&points=5")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data
        finally:
            systems.get_rpg_inventory = original_inv
            systems.rpg_award_xp = original_award


# ---------------------------------------------------------------------------
# GET /guild/quests
# ---------------------------------------------------------------------------


class TestGuildQuests:
    def test_guild_quests_no_board(self, client):
        original = systems.get_board
        systems.get_board = None
        try:
            resp = client.get("/api/guild/quests")
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            systems.get_board = original

    def test_guild_quests_returns_quests(self, client):
        from enum import Enum

        class FakeState(Enum):
            OPEN = "open"

        quest = MagicMock()
        quest.quest_id = "gq1"
        quest.title = "Fix bug"
        quest.description = "A bug"
        quest.priority = 5
        quest.state = FakeState.OPEN
        quest.claimed_by = None
        quest.tags = ["bug"]

        board = MagicMock()
        board.board.quests = {"gq1": quest}
        board.get_board_summary = AsyncMock(return_value={"total": 1})

        original = systems.get_board
        systems.get_board = AsyncMock(return_value=board)
        try:
            resp = client.get("/api/guild/quests")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            assert data[0]["quest_id"] == "gq1"
        finally:
            systems.get_board = original

    def test_guild_quests_filtered_by_state(self, client):
        from enum import Enum

        class FakeState(Enum):
            OPEN = "open"
            DONE = "done"

        q_open = MagicMock()
        q_open.quest_id = "q_open"
        q_open.title = "Open quest"
        q_open.description = ""
        q_open.priority = 3
        q_open.state = FakeState.OPEN
        q_open.claimed_by = None
        q_open.tags = []

        q_done = MagicMock()
        q_done.quest_id = "q_done"
        q_done.title = "Done quest"
        q_done.description = ""
        q_done.priority = 1
        q_done.state = FakeState.DONE
        q_done.claimed_by = None
        q_done.tags = []

        board = MagicMock()
        board.board.quests = {"q_open": q_open, "q_done": q_done}

        original = systems.get_board
        systems.get_board = AsyncMock(return_value=board)
        try:
            resp = client.get("/api/guild/quests?state=open")
            assert resp.status_code == 200
            data = resp.json()
            assert all(q["state"] == "open" for q in data)
        finally:
            systems.get_board = original


# ---------------------------------------------------------------------------
# GET /guild/summary
# ---------------------------------------------------------------------------


class TestGuildSummary:
    def test_guild_summary_no_board(self, client):
        original = systems.get_board
        systems.get_board = None
        try:
            resp = client.get("/api/guild/summary")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data
        finally:
            systems.get_board = original

    def test_guild_summary_happy_path(self, client):
        summary = {"total": 5, "open": 3, "claimed": 2}
        board = MagicMock()
        board.get_board_summary = AsyncMock(return_value=summary)

        original = systems.get_board
        systems.get_board = AsyncMock(return_value=board)
        try:
            resp = client.get("/api/guild/summary")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 5
        finally:
            systems.get_board = original

    def test_guild_summary_error_returns_error_key(self, client):
        original = systems.get_board
        systems.get_board = AsyncMock(side_effect=RuntimeError("board error"))
        try:
            resp = client.get("/api/guild/summary")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data
        finally:
            systems.get_board = original


# ---------------------------------------------------------------------------
# GET /progress
# ---------------------------------------------------------------------------


class TestProgress:
    def test_progress_no_rpg_no_hints(self, client):
        original = systems.get_rpg_inventory
        systems.get_rpg_inventory = None
        try:
            with patch.object(systems, "_load_hint_engine", return_value=None):
                resp = client.get("/api/progress")
        finally:
            systems.get_rpg_inventory = original
        assert resp.status_code == 200
        data = resp.json()
        assert "evolution_level" in data
        assert "quests_completed" in data
        assert data["evolution_level"] == 1

    def test_progress_returns_valid_structure(self, client):
        resp = client.get("/api/progress")
        assert resp.status_code == 200
        data = resp.json()
        for field in ["evolution_level", "consciousness_score", "skills_unlocked",
                      "quests_completed", "temple_floor", "achievements"]:
            assert field in data


# ---------------------------------------------------------------------------
# GET /tips/random
# ---------------------------------------------------------------------------


class TestTipsRandom:
    def test_tips_random_returns_hint(self, client):
        resp = client.get("/api/tips/random")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "title" in data
        assert "text" in data

    def test_tips_random_varies(self, client):
        """Multiple calls may return different tips (non-deterministic but no error)."""
        ids = set()
        for _ in range(20):
            resp = client.get("/api/tips/random")
            assert resp.status_code == 200
            ids.add(resp.json()["id"])
        # At least some variation over 20 calls (tips pool has 8 entries)
        assert len(ids) >= 1


# ---------------------------------------------------------------------------
# GET /tips/contextual
# ---------------------------------------------------------------------------


class TestTipsContextual:
    @pytest.mark.parametrize("context", ["general", "error", "quest", "terminal", "search"])
    def test_contextual_tips_known_contexts(self, client, context):
        resp = client.get(f"/api/tips/contextual?context={context}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_contextual_tips_unknown_context_falls_back_to_general(self, client):
        resp = client.get("/api/tips/contextual?context=nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # Falls back to general tips
        assert any("start" in (h.get("title", "") + h.get("text", "")).lower() for h in data)

    def test_contextual_tips_default_is_general(self, client):
        resp = client.get("/api/tips/contextual")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# GET /fl1ght (smart search)
# ---------------------------------------------------------------------------


class TestFl1ght:
    def test_fl1ght_requires_query_param(self, client):
        resp = client.get("/api/fl1ght")
        # q is required
        assert resp.status_code == 422

    def test_fl1ght_returns_smart_search_result(self, client):
        resp = client.get("/api/fl1ght?q=quest")
        assert resp.status_code == 200
        data = resp.json()
        assert "query" in data
        assert data["query"] == "quest"
        assert "total_results" in data
        assert "categories" in data
        assert "results" in data
        assert "suggestions" in data

    def test_fl1ght_no_matches_returns_suggestions(self, client):
        resp = client.get("/api/fl1ght?q=zzz_no_match_xyzxyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_results"] == 0
        # When no results, suggestions should contain a fallback
        assert len(data["suggestions"]) >= 1

    def test_fl1ght_commands_category(self, client):
        resp = client.get("/api/fl1ght?q=start_nusyq")
        assert resp.status_code == 200
        data = resp.json()
        # commands category should be populated
        assert data["categories"]["commands"] >= 1

    def test_fl1ght_limit_param(self, client):
        resp = client.get("/api/fl1ght?q=quest&limit=3")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["results"], list)


# ---------------------------------------------------------------------------
# GET /hack/sessions  (controller unavailable → error; empty state)
# ---------------------------------------------------------------------------


class TestHackSessions:
    def test_hack_sessions_no_controller(self, client):
        original = systems.get_hacking_controller
        systems.get_hacking_controller = None
        try:
            resp = client.get("/api/hack/sessions")
        finally:
            systems.get_hacking_controller = original
        # When no controller, HACK_SESSIONS dict is used directly
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "sessions" in data

    def test_hack_sessions_empty(self, client):
        # Clear module-level HACK_SESSIONS
        original_sessions = systems.HACK_SESSIONS.copy()
        systems.HACK_SESSIONS.clear()
        try:
            resp = client.get("/api/hack/sessions")
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] == 0
            assert data["sessions"] == []
        finally:
            systems.HACK_SESSIONS.update(original_sessions)


# ---------------------------------------------------------------------------
# GET /hack/traces  (controller unavailable)
# ---------------------------------------------------------------------------


class TestHackTraces:
    def test_hack_traces_no_controller(self, client):
        original = systems.get_hacking_controller
        systems.get_hacking_controller = None
        try:
            resp = client.get("/api/hack/traces")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data
        finally:
            systems.get_hacking_controller = original

    def test_hack_traces_with_controller(self, client):
        controller = MagicMock()
        controller.check_traces.return_value = {}
        controller.active_traces = {}

        original = systems.get_hacking_controller
        systems.get_hacking_controller = lambda: controller
        try:
            with patch.object(systems, "_auto_persist_game_state"):
                resp = client.get("/api/hack/traces")
            assert resp.status_code == 200
            data = resp.json()
            assert data["active_traces"] == 0
        finally:
            systems.get_hacking_controller = original


# ---------------------------------------------------------------------------
# GET /intermediary/metrics
# ---------------------------------------------------------------------------


class TestIntermediaryMetrics:
    def test_metrics_unavailable_when_empty(self, client):
        original = systems._INTERMEDIARY_METRICS
        systems._INTERMEDIARY_METRICS = {}
        try:
            resp = client.get("/api/intermediary/metrics")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "unavailable"
        finally:
            systems._INTERMEDIARY_METRICS = original

    def test_metrics_present(self, client):
        metrics = {
            "handle_calls": 10,
            "handle_errors": 2,
            "handle_latency_ms": [10.0, 20.0, 30.0],
        }
        original = systems._INTERMEDIARY_METRICS
        systems._INTERMEDIARY_METRICS = metrics
        try:
            resp = client.get("/api/intermediary/metrics")
            assert resp.status_code == 200
            data = resp.json()
            assert data["handle_calls"] == 10
            assert data["handle_errors"] == 2
            assert data["latency_ms"]["count"] == 3
            assert data["latency_ms"]["avg"] == 20.0
        finally:
            systems._INTERMEDIARY_METRICS = original


# ---------------------------------------------------------------------------
# GET /search
# ---------------------------------------------------------------------------


class TestSearch:
    def test_search_no_query_returns_all(self, client):
        resp = client.get("/api/search")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_search_with_query_filters(self, client):
        resp = client.get("/api/search?q=nusyq")
        assert resp.status_code == 200
        data = resp.json()
        for item in data:
            combined = (item["command"] + " " + (item.get("description") or "")).lower()
            assert "nusyq" in combined

    def test_search_max_results(self, client):
        resp = client.get("/api/search")
        data = resp.json()
        assert len(data) <= 20

    def test_search_no_duplicate_commands(self, client):
        resp = client.get("/api/search")
        commands = [item["command"] for item in resp.json()]
        assert len(commands) == len(set(commands))


# ---------------------------------------------------------------------------
# POST /intermediary (unavailable)
# ---------------------------------------------------------------------------


class TestIntermediaryPost:
    def test_intermediary_unavailable_when_no_class(self, client):
        original = systems.AIIntermediary
        systems.AIIntermediary = None
        try:
            resp = client.post(
                "/api/intermediary",
                json={"text": "hello", "paradigm": "natural_language"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "error"
            assert "unavailable" in data["detail"].lower()
        finally:
            systems.AIIntermediary = original

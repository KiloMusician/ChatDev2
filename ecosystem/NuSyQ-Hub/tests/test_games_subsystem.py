"""Tests for src/games/ — NarrativeEngine and AchievementManager."""

import pytest


class TestNarrativeToneTheme:
    """Tests for NarrativeTone and NarrativeTheme enums."""

    def test_tone_has_cyberpunk(self):
        from src.games.narrative_engine import NarrativeTone
        assert NarrativeTone.CYBERPUNK is not None

    def test_tone_values_are_strings(self):
        from src.games.narrative_engine import NarrativeTone
        for tone in NarrativeTone:
            assert isinstance(tone.value, str)

    def test_theme_has_hacking(self):
        from src.games.narrative_engine import NarrativeTheme
        assert NarrativeTheme.HACKING is not None

    def test_theme_count(self):
        from src.games.narrative_engine import NarrativeTheme
        assert len(list(NarrativeTheme)) >= 3


class TestNarrativeContext:
    """Tests for NarrativeContext dataclass."""

    def test_default_context(self):
        from src.games.narrative_engine import NarrativeContext, NarrativeTone, NarrativeTheme
        ctx = NarrativeContext()
        assert ctx.tone == NarrativeTone.CYBERPUNK
        assert ctx.theme == NarrativeTheme.HACKING
        assert ctx.player_name == "Operator"

    def test_custom_context(self):
        from src.games.narrative_engine import NarrativeContext, NarrativeTone, NarrativeTheme
        ctx = NarrativeContext(
            tone=NarrativeTone.DRAMATIC,
            theme=NarrativeTheme.COMBAT,
            player_name="HackerX",
            player_level=5,
        )
        assert ctx.player_name == "HackerX"
        assert ctx.player_level == 5


class TestNarrativeEngine:
    """Tests for NarrativeEngine generation."""

    @pytest.fixture
    def engine(self):
        from src.games.narrative_engine import NarrativeEngine
        return NarrativeEngine(seed=42)

    def test_instantiation(self, engine):
        assert engine is not None

    def test_generate_returns_string(self, engine):
        result = engine.generate("quest_start", {"quest_name": "Test Quest"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_quest_complete(self, engine):
        result = engine.generate("quest_complete", {"quest_name": "Test Quest"})
        assert isinstance(result, str)

    def test_seeded_determinism(self):
        from src.games.narrative_engine import NarrativeEngine
        e1 = NarrativeEngine(seed=99)
        e2 = NarrativeEngine(seed=99)
        r1 = e1.generate("quest_start", {"quest_name": "Quest"})
        r2 = e2.generate("quest_start", {"quest_name": "Quest"})
        assert r1 == r2

    def test_different_seeds_multiple_calls(self):
        from src.games.narrative_engine import NarrativeEngine
        engine = NarrativeEngine(seed=1)
        results = []
        for _ in range(3):
            results.append(engine.generate("quest_start", {"quest_name": "Q"}))
        assert all(isinstance(r, str) for r in results)


class TestNarrativeModuleFunctions:
    """Tests for module-level narrative helper functions."""

    def test_narrate_quest_start(self):
        from src.games.narrative_engine import narrate_quest_start
        result = narrate_quest_start("Deploy Module", xp=100)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_narrate_quest_complete(self):
        from src.games.narrative_engine import narrate_quest_complete
        result = narrate_quest_complete("Deploy Module", xp=100)
        assert isinstance(result, str)

    def test_narrate_achievement(self):
        from src.games.narrative_engine import narrate_achievement
        result = narrate_achievement("First Blood", "Complete first quest", points=50)
        assert isinstance(result, str)

    def test_narrate_level_up(self):
        from src.games.narrative_engine import narrate_level_up
        result = narrate_level_up(level=5)
        assert isinstance(result, str)

    def test_get_engine_returns_instance(self):
        from src.games.narrative_engine import NarrativeEngine, get_engine
        engine = get_engine()
        assert isinstance(engine, NarrativeEngine)


class TestAchievementDataclasses:
    """Tests for Achievement, UnlockedAchievement, LeaderboardEntry dataclasses."""

    def test_achievement_defaults(self):
        from src.games.achievements import Achievement
        a = Achievement(id="first_quest", name="First Quest", description="Complete a quest")
        assert a.id == "first_quest"
        assert a.points == 10
        assert a.icon == "🏆"
        assert a.hidden is False

    def test_achievement_custom(self):
        from src.games.achievements import Achievement
        a = Achievement(
            id="elite", name="Elite", description="Top tier", points=500, hidden=True
        )
        assert a.points == 500
        assert a.hidden is True

    def test_unlocked_achievement(self):
        from src.games.achievements import UnlockedAchievement
        ua = UnlockedAchievement(
            achievement_id="first_quest", unlocked_at="2026-01-01T00:00:00"
        )
        assert ua.achievement_id == "first_quest"
        assert ua.player_id == "default"

    def test_leaderboard_entry_has_timestamp(self):
        from src.games.achievements import LeaderboardEntry
        entry = LeaderboardEntry(
            player_id="p1", player_name="Alice", score=9999, category="general"
        )
        assert entry.score == 9999
        assert entry.recorded_at is not None


class TestAchievementManager:
    """Tests for AchievementManager with tmp_path isolation."""

    @pytest.fixture
    def mgr(self, tmp_path):
        from src.games.achievements import AchievementManager
        return AchievementManager(achievements_file=tmp_path / "achievements.json")

    def test_instantiation(self, mgr):
        assert mgr is not None

    def test_has_built_in_achievements(self, mgr):
        all_a = mgr.get_locked() + mgr.get_unlocked()
        assert len(all_a) >= 1

    def test_unlock_known_achievement(self, mgr):
        locked = mgr.get_locked()
        if locked:
            a = mgr.unlock(locked[0].id)
            assert a is not None

    def test_unlock_unknown_returns_none(self, mgr):
        result = mgr.unlock("nonexistent_achievement_xyz")
        assert result is None

    def test_get_total_points_is_int(self, mgr):
        assert isinstance(mgr.get_total_points(), int)

    def test_get_completion_percentage_is_float(self, mgr):
        pct = mgr.get_completion_percentage()
        assert isinstance(pct, float)
        assert 0.0 <= pct <= 100.0


class TestCheckAchievementFunctions:
    """Tests for module-level achievement check functions."""

    def test_check_quest_achievements_empty(self):
        from src.games.achievements import check_quest_achievements
        results = check_quest_achievements(0)
        assert isinstance(results, list)

    def test_check_quest_achievements_high_count(self):
        from src.games.achievements import check_quest_achievements
        results = check_quest_achievements(100)
        assert isinstance(results, list)

    def test_check_xp_achievements(self):
        from src.games.achievements import check_xp_achievements
        results = check_xp_achievements(total_xp=1000)
        assert isinstance(results, list)

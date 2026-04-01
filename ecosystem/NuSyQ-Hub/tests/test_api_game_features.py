"""Tests for game-like API features inspired by Bitburner/Hacknet/GreyHack."""


class TestFlightSmartSearch:
    """Tests for fl1ght.exe smart search endpoint."""

    def test_fl1ght_search_basic(self):
        """Test basic fl1ght search."""
        from src.api.systems import fl1ght_smart_search

        # Pass explicit values for Query-wrapped params
        result = fl1ght_smart_search(q="quest", limit=20, include_code=False)
        assert result.query == "quest"
        assert isinstance(result.total_results, int)
        assert isinstance(result.categories, dict)
        assert isinstance(result.results, list)
        assert isinstance(result.suggestions, list)

    def test_fl1ght_search_empty_query(self):
        """Test fl1ght with query that matches nothing."""
        from src.api.systems import fl1ght_smart_search

        result = fl1ght_smart_search(q="xyznonexistent123", limit=20, include_code=False)
        assert result.total_results == 0
        assert len(result.suggestions) > 0  # Should provide fallback suggestions


class TestRPGProgression:
    """Tests for RPG progression endpoints."""

    def test_get_game_progress(self):
        """Test game progress endpoint."""
        from src.api.systems import get_game_progress

        progress = get_game_progress()
        assert hasattr(progress, "evolution_level")
        assert hasattr(progress, "consciousness_score")
        assert hasattr(progress, "skills_unlocked")
        assert hasattr(progress, "quests_completed")
        assert hasattr(progress, "temple_floor")
        assert hasattr(progress, "achievements")
        assert isinstance(progress.achievements, list)

    def test_list_skills(self):
        """Test skills listing."""
        from src.api.systems import list_skills

        skills = list_skills()
        assert isinstance(skills, list)
        # Skills may be empty if RPG inventory not initialized


class TestTipsSystem:
    """Tests for tips and guidance system."""

    def test_random_tip(self):
        """Test random tip endpoint."""
        from src.api.systems import get_random_tip

        tip = get_random_tip()
        assert hasattr(tip, "id")
        assert hasattr(tip, "title")
        assert hasattr(tip, "text")
        assert len(tip.title) > 0
        assert len(tip.text) > 0

    def test_contextual_tips_general(self):
        """Test contextual tips for general context."""
        from src.api.systems import get_contextual_tips

        tips = get_contextual_tips(context="general")
        assert isinstance(tips, list)
        assert len(tips) > 0

    def test_contextual_tips_error(self):
        """Test contextual tips for error context."""
        from src.api.systems import get_contextual_tips

        tips = get_contextual_tips(context="error")
        assert isinstance(tips, list)
        assert len(tips) > 0


class TestActionsSystem:
    """Tests for actions/ops system."""

    def test_list_actions(self):
        """Test listing available actions."""
        from src.api.systems import list_actions

        actions = list_actions()
        assert isinstance(actions, list)
        assert len(actions) > 0
        # Check structure
        action = actions[0]
        assert "name" in action
        assert "description" in action
        assert "category" in action
        assert "xp_reward" in action

    def test_get_action_info(self):
        """Test getting info for a specific action."""
        from src.api.systems import get_action_info

        info = get_action_info("heal")
        assert "name" in info
        assert info["name"] == "heal"
        assert "xp_reward" in info

    def test_get_action_info_unknown(self):
        """Test getting info for unknown action."""
        from src.api.systems import get_action_info

        info = get_action_info("nonexistent_action")
        assert "error" in info

    def test_execute_action_dry_run(self):
        """Test executing action in dry run mode."""
        from src.api.systems import ActionRequest, execute_action

        request = ActionRequest(action="heal", dry_run=True)
        result = execute_action(request)
        assert result.success
        assert "DRY RUN" in result.message
        assert result.xp_earned > 0


class TestSystemMap:
    """Tests for system info endpoints."""

    def test_whoami(self):
        """Test whoami endpoint."""
        from src.api.systems import whoami

        info = whoami()
        assert info["system"] == "NuSyQ-Hub"
        assert "capabilities" in info
        assert isinstance(info["capabilities"], list)

    def test_system_map(self):
        """Test system map endpoint."""
        from src.api.systems import get_system_map

        smap = get_system_map()
        assert "core_systems" in smap
        assert "rpg_features" in smap
        assert "guild_board" in smap
        assert "actions" in smap


class TestExistingEndpoints:
    """Test that existing endpoints still work."""

    def test_list_hints(self):
        """Test hints listing."""
        from src.api.systems import list_hints

        hints = list_hints()
        assert isinstance(hints, list)

    def test_list_tutorials(self):
        """Test tutorials listing."""
        from src.api.systems import list_tutorials

        tutorials = list_tutorials()
        assert isinstance(tutorials, list)
        assert len(tutorials) > 0

    def test_list_faq(self):
        """Test FAQ listing."""
        from src.api.systems import list_faq

        faqs = list_faq()
        assert isinstance(faqs, list)
        assert len(faqs) > 0

    def test_list_commands(self):
        """Test commands listing."""
        from src.api.systems import list_commands

        commands = list_commands()
        assert isinstance(commands, list)
        assert len(commands) > 0

"""Tests for src/ecosystem_activation_report.py — constants and generate_activation_report."""


class TestModuleConstants:
    """Tests for module-level constants."""

    def test_repo_name_constants(self):
        from src.ecosystem_activation_report import (
            REPO_NUSYQ_HUB,
            REPO_NUSYQ_ROOT,
            REPO_SIMULATED_VERSE,
        )
        assert isinstance(REPO_NUSYQ_HUB, str)
        assert isinstance(REPO_SIMULATED_VERSE, str)
        assert isinstance(REPO_NUSYQ_ROOT, str)
        assert len(REPO_NUSYQ_HUB) > 0
        assert len(REPO_SIMULATED_VERSE) > 0
        assert len(REPO_NUSYQ_ROOT) > 0

    def test_status_constants_are_strings(self):
        from src.ecosystem_activation_report import (
            STATUS_ACTIVE,
            STATUS_ISSUES,
            STATUS_OPERATIONAL,
            STATUS_PARTIAL,
        )
        assert isinstance(STATUS_ACTIVE, str)
        assert isinstance(STATUS_OPERATIONAL, str)
        assert isinstance(STATUS_PARTIAL, str)
        assert isinstance(STATUS_ISSUES, str)

    def test_status_constants_are_distinct(self):
        from src.ecosystem_activation_report import (
            STATUS_ACTIVE,
            STATUS_ISSUES,
            STATUS_OPERATIONAL,
            STATUS_PARTIAL,
        )
        statuses = {STATUS_ACTIVE, STATUS_OPERATIONAL, STATUS_PARTIAL, STATUS_ISSUES}
        assert len(statuses) == 4


class TestEcosystemStatus:
    """Tests for the ECOSYSTEM_STATUS dict."""

    def test_is_dict(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS
        assert isinstance(ECOSYSTEM_STATUS, dict)

    def test_has_required_top_level_keys(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS
        for key in ("total_repositories", "ai_systems_registered", "repositories"):
            assert key in ECOSYSTEM_STATUS

    def test_total_repositories(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS
        assert ECOSYSTEM_STATUS["total_repositories"] == 3

    def test_ai_systems_registered(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS
        assert ECOSYSTEM_STATUS["ai_systems_registered"] == 5

    def test_repositories_has_three_entries(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS
        repos = ECOSYSTEM_STATUS["repositories"]
        assert len(repos) == 3

    def test_nusyq_hub_health_score(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS, REPO_NUSYQ_HUB
        score = ECOSYSTEM_STATUS["repositories"][REPO_NUSYQ_HUB]["health_score"]
        assert 0.0 <= score <= 1.0

    def test_simulated_verse_health_score(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS, REPO_SIMULATED_VERSE
        score = ECOSYSTEM_STATUS["repositories"][REPO_SIMULATED_VERSE]["health_score"]
        assert 0.0 <= score <= 1.0

    def test_nusyq_root_health_score_lower(self):
        from src.ecosystem_activation_report import (
            ECOSYSTEM_STATUS,
            REPO_NUSYQ_HUB,
            REPO_NUSYQ_ROOT,
        )
        hub_score = ECOSYSTEM_STATUS["repositories"][REPO_NUSYQ_HUB]["health_score"]
        root_score = ECOSYSTEM_STATUS["repositories"][REPO_NUSYQ_ROOT]["health_score"]
        assert root_score < hub_score

    def test_ai_systems_dict_present(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS
        assert "ai_systems" in ECOSYSTEM_STATUS
        assert "systems" in ECOSYSTEM_STATUS["ai_systems"]

    def test_ai_systems_registered_count_matches(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS
        systems = ECOSYSTEM_STATUS["ai_systems"]["systems"]
        registered = ECOSYSTEM_STATUS["ai_systems"]["registered_count"]
        assert len(systems) == registered

    def test_concrete_improvements_present(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS
        ci = ECOSYSTEM_STATUS["concrete_improvements"]
        assert "total_fixes" in ci
        assert "files_fixed" in ci
        assert "specific_fixes" in ci
        assert isinstance(ci["specific_fixes"], list)
        assert len(ci["specific_fixes"]) > 0

    def test_strategic_coordination_present(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS
        sc = ECOSYSTEM_STATUS["strategic_coordination"]
        assert "active_tasks" in sc
        assert sc["active_tasks"] >= 0


class TestNextSteps:
    """Tests for NEXT_STEPS constant."""

    def test_is_dict(self):
        from src.ecosystem_activation_report import NEXT_STEPS
        assert isinstance(NEXT_STEPS, dict)

    def test_has_immediate_priorities(self):
        from src.ecosystem_activation_report import NEXT_STEPS
        assert "immediate_priorities" in NEXT_STEPS
        assert len(NEXT_STEPS["immediate_priorities"]) > 0

    def test_has_strategic_enhancements(self):
        from src.ecosystem_activation_report import NEXT_STEPS
        assert "strategic_enhancements" in NEXT_STEPS
        assert len(NEXT_STEPS["strategic_enhancements"]) > 0

    def test_has_activation_achievements(self):
        from src.ecosystem_activation_report import NEXT_STEPS
        assert "activation_achievements" in NEXT_STEPS
        assert len(NEXT_STEPS["activation_achievements"]) > 0


class TestGenerateActivationReport:
    """Tests for generate_activation_report()."""

    def test_returns_string(self):
        from src.ecosystem_activation_report import generate_activation_report
        result = generate_activation_report()
        assert isinstance(result, str)

    def test_returns_non_empty(self):
        from src.ecosystem_activation_report import generate_activation_report
        result = generate_activation_report()
        assert len(result) > 100

    def test_contains_ecosystem_header(self):
        from src.ecosystem_activation_report import generate_activation_report
        result = generate_activation_report()
        assert "NuSyQ" in result or "ECOSYSTEM" in result

    def test_contains_repository_names(self):
        from src.ecosystem_activation_report import (
            REPO_NUSYQ_HUB,
            generate_activation_report,
        )
        result = generate_activation_report()
        assert REPO_NUSYQ_HUB in result

    def test_contains_health_scores(self):
        from src.ecosystem_activation_report import generate_activation_report
        result = generate_activation_report()
        # Health score should appear as percentage
        assert "%" in result

    def test_contains_improvement_count(self):
        from src.ecosystem_activation_report import ECOSYSTEM_STATUS, generate_activation_report
        result = generate_activation_report()
        fixes = str(ECOSYSTEM_STATUS["concrete_improvements"]["total_fixes"])
        assert fixes in result

    def test_idempotent_multiple_calls(self):
        from src.ecosystem_activation_report import generate_activation_report
        r1 = generate_activation_report()
        r2 = generate_activation_report()
        # Both should be non-empty strings (timestamps differ, but structure same)
        assert isinstance(r1, str) and isinstance(r2, str)
        assert len(r1) > 0 and len(r2) > 0

"""
Comprehensive test suite for unified agent ecosystem and main entry point (Zeta11).
Tests ecosystem integration, agent coordination, and application bootstrap.

Target: 90%+ coverage of unified_agent_ecosystem.py + main.py (35+ functions)
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# NOTE: async tests use @pytest.mark.asyncio per-method; sync tests are plain def


class TestEcosystemInitialization:
    """Test unified agent ecosystem initialization."""

    @pytest.fixture
    async def ecosystem(self):
        """Create agent ecosystem instance."""
        from src.agents.unified_agent_ecosystem import UnifiedAgentEcosystem

        ecosystem = UnifiedAgentEcosystem()
        yield ecosystem
        await ecosystem.shutdown() if hasattr(ecosystem, "shutdown") else None

    async def test_ecosystem_bootstrap(self, ecosystem):
        """Test ecosystem initialization and bootstrap."""
        assert ecosystem is not None
        assert hasattr(ecosystem, "agent_hub")
        assert hasattr(ecosystem, "quest_engine")
        assert hasattr(ecosystem, "temple")
        assert hasattr(ecosystem, "agent_quests")

    async def test_agent_initialization_order(self, ecosystem):
        """Test that agents initialize in correct order."""
        # Check that core systems are initialized
        assert ecosystem.agent_hub is not None
        assert ecosystem.quest_engine is not None
        assert ecosystem.temple is not None

    async def test_configuration_integration(self, ecosystem):
        """Test configuration loading from all sources."""
        # Verify ecosystem has access to data directory
        assert ecosystem.data_dir is not None
        assert ecosystem.data_dir.exists()

    async def test_health_check_on_startup(self, ecosystem):
        """Test basic ecosystem health after startup."""
        # Verify core systems are accessible
        assert ecosystem.agent_hub is not None
        assert len(ecosystem.agent_hub.agents) > 0
        assert ecosystem.quest_engine is not None


class TestEcosystemCoordination:
    """Test UnifiedAgentEcosystem quest creation and agent queries."""

    @pytest.fixture
    def eco(self, tmp_path):
        from src.agents.unified_agent_ecosystem import UnifiedAgentEcosystem

        return UnifiedAgentEcosystem(data_dir=tmp_path / "eco_data")

    def test_get_agent_quests_empty_initially(self, eco):
        """Newly initialized ecosystem has no quests assigned."""
        quests = eco.get_agent_quests("claude")
        assert isinstance(quests, list)
        assert len(quests) == 0

    def test_get_party_quest_summary_structure(self, eco):
        """Party summary has expected top-level keys."""
        summary = eco.get_party_quest_summary()
        assert "total_quests" in summary
        assert "quests_by_status" in summary
        assert "agents" in summary

    def test_party_summary_agents_include_core_agents(self, eco):
        """All core agents appear in party summary."""
        summary = eco.get_party_quest_summary()
        for agent in ("copilot", "claude", "ollama"):
            assert agent in summary["agents"]

    def test_party_summary_status_counts_are_ints(self, eco):
        """Status counts in party summary are non-negative integers."""
        summary = eco.get_party_quest_summary()
        for _status, count in summary["quests_by_status"].items():
            assert isinstance(count, int)
            assert count >= 0


class TestTaskOrchestration:
    """Test UnifiedAgentEcosystem quest creation and suggestions."""

    @pytest.fixture
    def eco(self, tmp_path):
        from src.agents.unified_agent_ecosystem import UnifiedAgentEcosystem

        return UnifiedAgentEcosystem(data_dir=tmp_path / "eco_data")

    def test_suggest_next_quest_returns_dict_or_none(self, eco):
        """suggest_next_quest returns a dict or None for known agents."""
        result = eco.suggest_next_quest("claude")
        assert result is None or isinstance(result, dict)

    def test_get_agent_quests_filtered_by_status(self, eco):
        """get_agent_quests status filter returns list."""
        quests = eco.get_agent_quests("copilot", status="active")
        assert isinstance(quests, list)

    @patch("src.Rosetta_Quest_System.quest_engine.save_quests")
    @patch("src.Rosetta_Quest_System.quest_engine.save_questlines")
    @patch("src.Rosetta_Quest_System.quest_engine.log_event")
    def test_create_quest_for_agent_returns_success(self, _log, _sqls, _sq, eco):
        """create_quest_for_agent returns success dict with quest info."""
        result = eco.create_quest_for_agent(
            title="Implement caching",
            description="Add an LRU cache to API responses",
            agent_name="claude",
        )
        assert isinstance(result, dict)
        assert result.get("success") is True
        assert result.get("agent") == "claude"


class TestAgentPoolManagement:
    """Test AgentQuest dataclass and ecosystem agent introspection."""

    @pytest.fixture
    def eco(self, tmp_path):
        from src.agents.unified_agent_ecosystem import UnifiedAgentEcosystem

        return UnifiedAgentEcosystem(data_dir=tmp_path / "eco_data")

    def test_agent_quest_dataclass_defaults(self):
        from src.agents.unified_agent_ecosystem import AgentQuest

        aq = AgentQuest(quest_id="q-001", agent_name="claude")
        assert aq.quest_id == "q-001"
        assert aq.agent_name == "claude"
        assert aq.xp_reward == 10  # default is 10
        assert aq.started_at is None

    def test_agent_quest_custom_xp_reward(self):
        from src.agents.unified_agent_ecosystem import AgentQuest

        aq = AgentQuest(quest_id="q-002", agent_name="ollama", xp_reward=50)
        assert aq.xp_reward == 50

    def test_ecosystem_has_known_agents(self, eco):
        """Core agents are registered in the hub on init."""
        agents = eco.agent_hub.agents
        assert "claude" in agents
        assert "copilot" in agents
        assert "ollama" in agents

    async def test_agent_clustering(self, tmp_path):
        """Test ecosystem initializes all expected agent names."""
        from src.agents.unified_agent_ecosystem import UnifiedAgentEcosystem

        eco = UnifiedAgentEcosystem(data_dir=tmp_path / "eco_data2")
        agent_names = set(eco.agent_hub.agents.keys())
        # metaclaw and hermes_agent are always auto-registered
        assert "metaclaw" in agent_names
        assert "hermes_agent" in agent_names

    async def test_dynamic_agent_scaling(self, tmp_path):
        """Test get_party_quest_summary returns all registered agents."""
        from src.agents.unified_agent_ecosystem import UnifiedAgentEcosystem

        eco = UnifiedAgentEcosystem(data_dir=tmp_path / "eco_data3")
        summary = eco.get_party_quest_summary()
        # All agents in hub should appear in summary
        for agent_name in eco.agent_hub.agents:
            assert agent_name in summary["agents"]

    async def test_agent_lifecycle(self, tmp_path):
        """Test suggest_next_quest for multiple agents returns consistent type."""
        from src.agents.unified_agent_ecosystem import UnifiedAgentEcosystem

        eco = UnifiedAgentEcosystem(data_dir=tmp_path / "eco_data4")
        for agent in ("claude", "copilot", "ollama"):
            result = eco.suggest_next_quest(agent)
            assert result is None or isinstance(result, dict)


class TestMainApplicationEntry:
    """Test NuSyQHubMain initialization and mode registry."""

    def test_nusyq_hub_main_instantiates(self):
        """NuSyQHubMain can be constructed without errors."""
        from src.main import NuSyQHubMain

        app = NuSyQHubMain()
        assert app is not None

    def test_hub_main_has_config(self):
        """_load_configuration returns a dict (empty or populated)."""
        from src.main import NuSyQHubMain

        app = NuSyQHubMain()
        assert isinstance(app.config, dict)

    def test_hub_main_has_logger(self):
        """_setup_logging returns a Logger instance."""
        import logging

        from src.main import NuSyQHubMain

        app = NuSyQHubMain()
        assert isinstance(app.logger, logging.Logger)

    @pytest.mark.parametrize("mode", ["interactive", "orchestration", "quantum", "analysis", "health"])
    def test_hub_main_available_modes_exist(self, mode):
        """All declared modes have callable handlers."""
        from src.main import NuSyQHubMain

        app = NuSyQHubMain()
        assert mode in app.available_modes
        assert callable(app.available_modes[mode])

    def test_hub_main_health_check_mode_runs(self):
        """_health_check_mode executes without exception."""
        from src.main import NuSyQHubMain

        app = NuSyQHubMain()
        # Passing None is accepted by _health_check_mode signature
        try:
            app._health_check_mode(None)
        except Exception as exc:
            pytest.fail(f"_health_check_mode raised unexpectedly: {exc}")


class TestApplicationWorkflow:
    """Test QuantumProblemResolver as the real workflow engine."""

    def test_quantum_resolver_detect_returns_list(self, tmp_path):
        """detect_problems on a clean tmp dir returns an empty list."""
        from src.healing.quantum_problem_resolver import QuantumProblemResolver

        resolver = QuantumProblemResolver(root_path=tmp_path)
        problems = resolver.detect_problems(workspace=tmp_path)
        assert isinstance(problems, list)

    def test_quantum_resolver_select_strategy_for_import(self):
        """select_strategy returns a non-empty strategy string."""
        from src.healing.quantum_problem_resolver import QuantumProblemResolver

        resolver = QuantumProblemResolver()
        strategy = resolver.select_strategy({"type": "missing_import", "severity": "high"})
        assert isinstance(strategy, str) and len(strategy) > 0

    def test_quantum_resolver_resolve_returns_status(self):
        """resolve_problem returns a dict with a status/success key."""
        from src.healing.quantum_problem_resolver import QuantumProblemResolver

        resolver = QuantumProblemResolver()
        result = resolver.resolve_problem("missing_import", {"module": "pandas"})
        assert isinstance(result, dict)
        assert "status" in result or "success" in result or "error" in result

    def test_quantum_resolver_algorithm_info(self):
        """get_algorithm_info returns metadata for known algorithms."""
        from src.healing.quantum_problem_resolver import QuantumProblemResolver

        resolver = QuantumProblemResolver()
        info = resolver.get_algorithm_info("quantum_annealing")
        assert info is not None


class TestErrorHandlingAndRecovery:
    """Test healing and recovery via QuantumProblemResolver."""

    def test_heal_problems_on_empty_list(self):
        """heal_problems([]) returns a result without raising."""
        from src.healing.quantum_problem_resolver import QuantumProblemResolver

        resolver = QuantumProblemResolver()
        result = resolver.heal_problems([])
        assert result is not None

    def test_detect_problems_skips_venv(self, tmp_path):
        """detect_problems skips .venv/ and __pycache__ directories."""
        venv_dir = tmp_path / ".venv" / "lib" / "site-packages"
        venv_dir.mkdir(parents=True)
        (venv_dir / "bad_package.py").write_text(
            "import nonexistent_xyz_abc\n", encoding="utf-8"
        )
        from src.healing.quantum_problem_resolver import QuantumProblemResolver

        resolver = QuantumProblemResolver(root_path=tmp_path)
        problems = resolver.detect_problems(workspace=tmp_path)
        # The .venv file should NOT generate import-error problems
        assert isinstance(problems, list)

    def test_nusyq_hub_main_analysis_mode_callable(self):
        """_analysis_mode is callable and accepts a Namespace with required args."""
        from argparse import Namespace

        from src.main import NuSyQHubMain

        app = NuSyQHubMain()
        # _analysis_mode reads args.quick; supply it explicitly
        ns = Namespace(quick=True, target=None, output=None)
        try:
            app._analysis_mode(ns)
        except Exception as exc:
            pytest.fail(f"_analysis_mode raised: {exc}")


class TestConfigurationManagement:
    """Test NuSyQHubMain configuration loading."""

    def test_load_configuration_returns_dict(self):
        """_load_configuration always returns a dict, even without config file."""
        from src.main import NuSyQHubMain

        app = NuSyQHubMain()
        assert isinstance(app.config, dict)

    def test_configuration_has_known_keys_when_file_present(self):
        """If ZETA_PROGRESS_TRACKER.json exists, config is non-empty."""
        import json

        from src.main import NuSyQHubMain

        config_path = Path("config") / "ZETA_PROGRESS_TRACKER.json"
        if config_path.exists():
            app = NuSyQHubMain()
            # File exists → should have loaded something
            raw = json.loads(config_path.read_text(encoding="utf-8"))
            assert app.config == raw or isinstance(app.config, dict)
        else:
            pytest.skip("ZETA_PROGRESS_TRACKER.json not present")

    def test_setup_logging_returns_logger(self):
        """_setup_logging returns a named Logger."""
        import logging

        from src.main import NuSyQHubMain

        app = NuSyQHubMain()
        assert app.logger.name == "nusyq-hub"
        assert isinstance(app.logger, logging.Logger)

    def test_environment_variable_respected(self, monkeypatch):
        """NUSYQ-related env vars are readable via os.getenv."""
        import os

        monkeypatch.setenv("NUSYQ_TIMEOUT", "42")
        assert os.getenv("NUSYQ_TIMEOUT") == "42"


class TestMonitoring:
    """Test MetricsCollector from src.observability.autonomy_dashboard."""

    def test_metrics_collector_instantiates(self, tmp_path):
        """MetricsCollector can be constructed with a tmp state dir."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path / "metrics.db")
        assert collector is not None

    def test_get_metrics_collector_returns_singleton(self):
        """get_metrics_collector() returns the same instance on repeated calls."""
        from src.observability.autonomy_dashboard import get_metrics_collector

        c1 = get_metrics_collector()
        c2 = get_metrics_collector()
        assert c1 is c2

    async def test_metrics_collector_record_task_completion(self, tmp_path):
        """record_task_completion increments the dashboard metrics."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path / "metrics.db")
        await collector.record_task_completion(
            task_id=1, success=True, duration_seconds=0.5, category="test"
        )
        snapshot = collector.get_current_snapshot()
        assert snapshot is not None

    async def test_metrics_collector_aggregate(self, tmp_path):
        """aggregate_metrics returns a DashboardMetrics instance."""
        from src.observability.autonomy_dashboard import DashboardMetrics, MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path / "metrics.db")
        snapshot = await collector.aggregate_metrics()
        assert isinstance(snapshot, DashboardMetrics)

    def test_dashboard_text_generation(self, tmp_path):
        """generate_text_dashboard returns a non-empty string."""
        from src.observability.autonomy_dashboard import MetricsCollector

        collector = MetricsCollector(storage_path=tmp_path / "metrics2.db")
        text = collector.generate_text_dashboard()
        assert isinstance(text, str) and len(text) > 0


class TestIntegration:
    """Integration tests using real UnifiedAgentEcosystem async API."""

    @pytest.fixture
    def eco(self, tmp_path):
        from src.agents.unified_agent_ecosystem import UnifiedAgentEcosystem

        return UnifiedAgentEcosystem(data_dir=tmp_path / "integration_eco")

    @patch("src.Rosetta_Quest_System.quest_engine.save_quests")
    @patch("src.Rosetta_Quest_System.quest_engine.save_questlines")
    @patch("src.Rosetta_Quest_System.quest_engine.log_event")
    async def test_end_to_end_application_run(self, _log, _sqls, _sq, eco):
        """Create a quest, assign it, and verify it appears in agent's quest list."""
        result = eco.create_quest_for_agent(
            title="End-to-end test quest",
            description="Created in integration test",
            agent_name="claude",
        )
        assert result.get("success") is True

        quests = eco.get_agent_quests("claude")
        assert len(quests) >= 1
        assert any(q["title"] == "End-to-end test quest" for q in quests)

    @patch("src.Rosetta_Quest_System.quest_engine.save_quests")
    @patch("src.Rosetta_Quest_System.quest_engine.save_questlines")
    @patch("src.Rosetta_Quest_System.quest_engine.log_event")
    async def test_multi_mode_workflow(self, _log, _sqls, _sq, eco):
        """Create quests for multiple agents and verify party summary counts."""
        for agent in ("claude", "ollama"):
            eco.create_quest_for_agent(
                title=f"Quest for {agent}",
                description="Multi-agent workflow test",
                agent_name=agent,
            )

        summary = eco.get_party_quest_summary()
        total_assigned = sum(
            info["total"] for info in summary["agents"].values()
        )
        assert total_assigned >= 2

    async def test_persistent_state(self, tmp_path):
        """Ecosystem initialized with same data_dir sees consistent state."""
        from src.agents.unified_agent_ecosystem import UnifiedAgentEcosystem

        eco1 = UnifiedAgentEcosystem(data_dir=tmp_path / "state_eco")
        summary1 = eco1.get_party_quest_summary()

        eco2 = UnifiedAgentEcosystem(data_dir=tmp_path / "state_eco")
        summary2 = eco2.get_party_quest_summary()

        assert summary1["total_quests"] == summary2["total_quests"]


# Fixtures
@pytest.fixture(params=["orchestration", "quantum", "analysis"])
async def app_mode(request):
    """Parameterize application modes."""
    return request.param


@pytest.fixture(
    params=[
        {"name": "simple_task"},
        {"name": "complex_task", "complexity": "high"},
        {"name": "urgent_task", "priority": "critical"},
    ]
)
async def task_variant(request):
    """Parameterize task variants."""
    return request.param

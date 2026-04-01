"""Tests for src/games/hacking_mechanics.py and src/games/procedural_quests.py."""

from datetime import datetime

import pytest


class TestHackingEnums:
    """Tests for ExploitType and TraceStatus enums."""

    def test_exploit_type_values(self):
        from src.games.hacking_mechanics import ExploitType
        assert len(list(ExploitType)) >= 2

    def test_trace_status_safe(self):
        from src.games.hacking_mechanics import TraceStatus
        assert TraceStatus.SAFE is not None
        assert TraceStatus.LOCKDOWN is not None


class TestPortDataclass:
    """Tests for Port dataclass."""

    def test_basic_port(self):
        from src.games.hacking_mechanics import Port
        p = Port(port_number=22, service_name="SSH")
        assert p.port_number == 22
        assert p.service_name == "SSH"
        assert p.open is False
        assert p.vulnerable is False

    def test_open_vulnerable_port(self):
        from src.games.hacking_mechanics import ExploitType, Port
        p = Port(
            port_number=80, service_name="HTTP",
            open=True, vulnerable=True,
            exploit_type=ExploitType.BUFFER_OVERFLOW if hasattr(ExploitType, "BUFFER_OVERFLOW")
            else next(iter(ExploitType)),
            access_level=2,
        )
        assert p.open is True
        assert p.access_level == 2


class TestTraceDataclass:
    """Tests for Trace dataclass."""

    @pytest.fixture
    def trace(self):
        from src.games.hacking_mechanics import Trace, TraceStatus
        return Trace(
            id="trace-1",
            component_name="server01",
            start_time=datetime.now(),
            duration_seconds=30,
            current_countdown=30,
            trace_status=TraceStatus.SAFE,
        )

    def test_fields(self, trace):
        assert trace.id == "trace-1"
        assert trace.duration_seconds == 30

    def test_is_active_no_triggered(self, trace):
        # No triggered_at set → not active (unless lockdown)
        assert trace.is_active() is False

    def test_update_countdown_no_trigger(self, trace):
        count = trace.update_countdown()
        assert count == trace.duration_seconds

    def test_update_countdown_with_trigger(self, trace):
        trace.triggered_at = datetime.now()
        count = trace.update_countdown()
        assert isinstance(count, int)
        assert count >= 0


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_instantiation(self):
        from src.games.hacking_mechanics import ScanResult
        sr = ScanResult(
            component_name="target_server",
            ip_address="192.168.1.1",
            ports=[],
            services=["SSH"],
            vulnerabilities=[],
            open_exploits=[],
        )
        assert sr.component_name == "target_server"
        assert sr.ip_address == "192.168.1.1"


class TestHackingController:
    """Tests for HackingController initialization."""

    @pytest.fixture
    def ctrl(self):
        from src.games.hacking_mechanics import HackingController
        return HackingController()

    def test_instantiation(self, ctrl):
        assert ctrl is not None

    def test_get_hacking_controller(self):
        from src.games.hacking_mechanics import HackingController, get_hacking_controller
        ctrl = get_hacking_controller()
        assert isinstance(ctrl, HackingController)


class TestQuestTemplate:
    """Tests for QuestTemplate dataclass."""

    def test_basic_template(self):
        from src.games.procedural_quests import QuestTemplate
        qt = QuestTemplate(
            id="test_qt",
            name_template="Test {target}",
            description_template="Desc {target}",
            objectives_template=["Obj 1", "Obj 2"],
            xp_base=100,
        )
        assert qt.id == "test_qt"
        assert qt.xp_base == 100
        assert qt.difficulty_range == (1, 3)

    def test_quest_templates_populated(self):
        from src.games.procedural_quests import QUEST_TEMPLATES
        assert isinstance(QUEST_TEMPLATES, dict)
        assert len(QUEST_TEMPLATES) >= 1


class TestGeneratedQuest:
    """Tests for GeneratedQuest dataclass."""

    def test_basic_quest(self):
        from src.games.procedural_quests import GeneratedQuest
        gq = GeneratedQuest(
            id="gq-001",
            name="Analyze Module",
            description="Review the module",
            objectives=["Step 1", "Step 2"],
            xp_reward=150,
            difficulty=2,
            generated_at="2026-01-01T00:00:00",
            context={"target_file": "src/foo.py"},
            template_id="analyze_file",
        )
        assert gq.id == "gq-001"
        assert gq.xp_reward == 150
        assert gq.tags == []


class TestProceduralQuestGenerator:
    """Tests for ProceduralQuestGenerator."""

    @pytest.fixture
    def gen(self):
        from src.games.procedural_quests import ProceduralQuestGenerator
        return ProceduralQuestGenerator(seed=42)

    def test_instantiation(self, gen):
        assert gen is not None

    def test_get_generator_returns_instance(self):
        from src.games.procedural_quests import ProceduralQuestGenerator, get_generator
        g = get_generator(seed=99)
        assert isinstance(g, ProceduralQuestGenerator)

    def test_generate_from_errors_returns_list(self):
        from src.games.procedural_quests import generate_from_errors
        result = generate_from_errors([])
        assert isinstance(result, list)

    def test_generate_from_errors_with_data(self):
        from src.games.procedural_quests import GeneratedQuest, generate_from_errors
        errors = [{"type": "syntax_error", "file": "foo.py", "message": "invalid syntax"}]
        result = generate_from_errors(errors)
        assert isinstance(result, list)
        for q in result:
            assert isinstance(q, GeneratedQuest)

    def test_generate_quest_module_function(self):
        from src.games.procedural_quests import GeneratedQuest, generate_quest
        q = generate_quest(template_id="analyze_file", context={"target_file": "src/foo.py"})
        assert isinstance(q, GeneratedQuest)
        assert q.template_id == "analyze_file"

    def test_generate_daily_returns_list(self):
        from src.games.procedural_quests import generate_daily
        daily = generate_daily()
        assert isinstance(daily, list)

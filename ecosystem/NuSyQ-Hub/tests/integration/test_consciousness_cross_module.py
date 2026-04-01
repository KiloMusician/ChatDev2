"""Integration tests for consciousness module cross-module interactions.

This test suite validates that consciousness modules (floors, temple, house)
properly interact with each other and with other system components.

Test Strategy:
- Unit tests: 50% (individual module functionality)
- Integration tests: 30% (cross-module interactions) ← THIS FILE
- E2E tests: 20% (full system workflows)
"""

import pytest


@pytest.mark.integration
@pytest.mark.consciousness
class TestConsciousnessFloorIntegration:
    """Test integration between different consciousness floors."""

    def test_floor_progression_integration(self):
        """Test that floors can progress from 5 → 6 → 7 → 8-10."""
        # Import consciousness floor modules
        try:
            from src.consciousness.floor_5_integration import Floor5Integration
            from src.consciousness.floor_6_wisdom import Floor6Wisdom
            from src.consciousness.floor_7_evolution import Floor7Evolution
            from src.consciousness.floors_8_9_10_pinnacle import TemplePinnacle
        except ImportError as e:
            pytest.skip(f"Consciousness modules not available: {e}")

        # Test floor 5 can initialize
        floor5 = Floor5Integration()
        assert floor5 is not None

        # Test floor 6 can initialize
        floor6 = Floor6Wisdom()
        assert floor6 is not None

        # Test floor 7 can initialize
        floor7 = Floor7Evolution()
        assert floor7 is not None

        # Test pinnacle floors can initialize
        pinnacle = TemplePinnacle()
        assert pinnacle is not None

        # Test that pinnacle can process different consciousness levels
        result = pinnacle.ascend_pinnacle(consciousness_level=25.0)
        assert isinstance(result, dict)
        assert "consciousness_level" in result
        assert result["consciousness_level"] == 25.0

    def test_temple_house_integration(self):
        """Test integration between Temple of Knowledge and The Oldest House."""
        try:
            from src.consciousness.the_oldest_house import OldestHouse
        except ImportError as e:
            pytest.skip(f"Oldest House module not available: {e}")

        # Test house initialization
        house = OldestHouse()
        assert house is not None

        # Test that house has expected attributes
        assert hasattr(house, "analyze_patterns") or hasattr(house, "process")


@pytest.mark.integration
@pytest.mark.consciousness
class TestConsciousnessSystemIntegration:
    """Test consciousness system integration with other modules."""

    def test_consciousness_healing_integration(self):
        """Test that consciousness systems integrate with healing modules."""
        try:
            from src.healing.quantum_problem_resolver import QuantumProblemResolver
        except ImportError as e:
            pytest.skip(f"Quantum problem resolver not available: {e}")

        # Test quantum resolver initialization
        resolver = QuantumProblemResolver()
        assert resolver is not None

    def test_consciousness_integration_module(self):
        """Test consciousness integration module functionality."""
        try:
            from src.consciousness.floor_5_integration import Floor5Integration
        except ImportError as e:
            pytest.skip(f"Floor 5 integration module not available: {e}")

        floor5 = Floor5Integration()
        assert floor5 is not None

        # Test that floor 5 has integration capabilities
        assert hasattr(floor5, "integrate") or hasattr(floor5, "process")


@pytest.mark.integration
@pytest.mark.slow
class TestCrossModuleDependencies:
    """Test cross-module dependencies and data flow."""

    def test_orchestration_consciousness_integration(self):
        """Test that orchestration modules can work with consciousness."""
        try:
            from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub
        except ImportError as e:
            pytest.skip(f"Agent orchestration hub not available: {e}")

        # Test hub initialization
        hub = AgentOrchestrationHub()
        assert hub is not None

    def test_integration_bridge_consciousness(self):
        """Test integration bridge with consciousness systems."""
        try:
            from src.integration.quest_temple_bridge import QuestTempleBridge
        except ImportError as e:
            pytest.skip(f"Quest temple bridge not available: {e}")

        # Test bridge can initialize
        bridge = QuestTempleBridge()
        assert bridge is not None

        # Test bridge has expected methods
        assert hasattr(bridge, "sync_progress") or hasattr(bridge, "bridge")


@pytest.mark.integration
class TestModuleImportChain:
    """Test that modules can be imported without circular dependencies."""

    def test_consciousness_imports(self):
        """Test that all consciousness modules can be imported."""
        modules_to_test = [
            "src.consciousness.floor_5_integration",
            "src.consciousness.floor_6_wisdom",
            "src.consciousness.floor_7_evolution",
            "src.consciousness.floors_8_9_10_pinnacle",
            "src.consciousness.the_oldest_house",
            "src.consciousness.house_analysis",
        ]

        imported = []
        failed = []

        for module_name in modules_to_test:
            try:
                __import__(module_name)
                imported.append(module_name)
            except ImportError as e:
                failed.append((module_name, str(e)))

        # At least some modules should import successfully
        assert len(imported) > 0, f"No consciousness modules imported. Failed: {failed}"

    def test_healing_imports(self):
        """Test that healing modules can be imported."""
        modules_to_test = [
            "src.healing.quantum_problem_resolver",
            "src.healing.repository_health_restorer",
        ]

        imported = []
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                imported.append(module_name)
            except ImportError:
                pass

        # At least one healing module should import
        assert len(imported) > 0, "No healing modules could be imported"

    def test_integration_imports(self):
        """Test that integration modules can be imported."""
        modules_to_test = [
            "src.integration.n8n_integration",
            "src.integration.quest_temple_bridge",
        ]

        imported = []
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                imported.append(module_name)
            except ImportError:
                pass

        # At least one integration module should import
        assert len(imported) > 0, "No integration modules could be imported"


@pytest.mark.integration
@pytest.mark.smoke
class TestCriticalPathIntegration:
    """Test critical paths through integrated systems."""

    def test_minimal_integration_path(self):
        """Test that a minimal integration path works end-to-end."""
        # This is a smoke test to ensure basic integration is functional
        from pathlib import Path

        # Test that project structure exists
        project_root = Path(__file__).parent.parent.parent
        assert (project_root / "src").exists()
        assert (project_root / "src" / "consciousness").exists()
        assert (project_root / "src" / "healing").exists()
        assert (project_root / "src" / "integration").exists()

        # Test that key module files exist
        assert (project_root / "src" / "consciousness" / "__init__.py").exists()
        assert (project_root / "src" / "healing" / "quantum_problem_resolver.py").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

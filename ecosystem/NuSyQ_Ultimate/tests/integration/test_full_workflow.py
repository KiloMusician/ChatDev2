"""
Integration Tests for ΞNuSyQ Multi-Agent System
Tests end-to-end workflows and component integration

Version: 1.0.0
Date: 2025-10-07
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.agent_router import (  # noqa: E402
    AgentRouter,
    Task,
    TaskComplexity,
    TaskType,
)
from config.config_manager import ConfigManager  # noqa: E402


class TestConfigManagerIntegration(unittest.TestCase):
    """Test ConfigManager loading and validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = ConfigManager()

    def test_manifest_loads_successfully(self):
        """Verify nusyq.manifest.yaml loads without errors"""
        manifest = self.config_manager.load_manifest()
        self.assertIsNotNone(manifest)
        self.assertIn("winget_packages", manifest)
        self.assertIn("ollama_models", manifest)

    def test_knowledge_base_loads_successfully(self):
        """Verify knowledge-base.yaml loads without errors"""
        kb = self.config_manager.load_knowledge_base()
        self.assertIsNotNone(kb)
        self.assertIn("completions", kb)

    def test_ai_ecosystem_loads_successfully(self):
        """Verify ai-ecosystem.yaml loads without errors"""
        ecosystem = self.config_manager.load_ai_ecosystem()
        self.assertIsNotNone(ecosystem)

    def test_tasks_config_loads_successfully(self):
        """Verify tasks.yaml loads without errors"""
        tasks = self.config_manager.load_tasks()
        self.assertIsNotNone(tasks)

    def test_all_configs_valid(self):
        """Verify all configurations validate successfully"""
        results = self.config_manager.validate_all()
        self.assertTrue(results["all_valid"])
        self.assertEqual(len(results["errors"]), 0)


class TestAgentRouterIntegration(unittest.TestCase):
    """Test AgentRouter routing decisions"""

    def setUp(self):
        """Set up test fixtures"""
        self.router = AgentRouter()

    def test_simple_task_routes_to_free_agent(self):
        """Simple tasks should route to free Ollama agents"""
        task = Task(
            description="Add docstring",
            task_type=TaskType.DOCSTRING,
            complexity=TaskComplexity.SIMPLE,
        )

        decision = self.router.route_task(task)

        # Should be a free agent (Ollama)
        self.assertTrue(self.router._is_free_agent(decision.agent))
        self.assertEqual(decision.estimated_cost, 0.0)

    def test_critical_task_uses_appropriate_pattern(self):
        """Critical tasks should use consensus or high-quality agent"""
        task = Task(
            description="Security audit",
            task_type=TaskType.SECURITY_AUDIT,
            complexity=TaskComplexity.CRITICAL,
            requires_security=True,
        )

        decision = self.router.route_task(task)

        # Should use critical_decision pattern
        self.assertEqual(decision.coordination_pattern, "critical_decision")

    def test_full_feature_routes_to_chatdev(self):
        """Full features should route to ChatDev multi-agent"""
        task = Task(
            description="Create auth system",
            task_type=TaskType.FULL_FEATURE,
            complexity=TaskComplexity.COMPLEX,
            files_affected=5,
        )

        decision = self.router.route_task(task)

        # Should route to ChatDev
        self.assertIn("chatdev", decision.agent.name)
        self.assertEqual(decision.coordination_pattern, "full_project")

    def test_cost_report_shows_savings(self):
        """Cost report should show significant savings from Ollama"""
        report = self.router.get_cost_report()

        self.assertGreater(report["free_agents"], 10)  # At least 10 free
        self.assertEqual(report["paid_agents"], 1)  # Only Claude Code paid
        self.assertEqual(report["estimated_monthly_savings"], 880.0)


class TestMultiAgentCoordination(unittest.TestCase):
    """Test coordination between multiple agents"""

    def setUp(self):
        """Set up test fixtures"""
        self.router = AgentRouter()
        self.config_manager = ConfigManager()

    def test_ollama_models_available(self):
        """Verify Ollama models from manifest are accessible"""
        manifest = self.config_manager.load_manifest()
        ollama_models = manifest.get("ollama_models", [])

        # Should have at least 7 models configured
        self.assertGreaterEqual(len(ollama_models), 7)

        # Key models should be present
        model_names = [
            m if isinstance(m, str) else m.get("name") for m in ollama_models
        ]
        self.assertIn("qwen2.5-coder:7b", model_names)
        self.assertIn("qwen2.5-coder:14b", model_names)

    def test_agent_registry_complete(self):
        """Verify agent registry has all expected agents"""
        agents = self.router.list_agents()

        # Should have 14+ agents
        self.assertGreaterEqual(len(agents), 14)

        # Key agents should be present
        agent_names = [a.name for a in agents]
        self.assertIn("claude_code", agent_names)
        self.assertIn("ollama_qwen_7b", agent_names)
        self.assertIn("ollama_qwen_14b", agent_names)
        self.assertIn("chatdev_ceo", agent_names)

    def test_routing_preferences_configured(self):
        """Verify routing preferences are loaded"""
        # Router should have preferences
        self.assertGreater(len(self.router.routing_preferences), 0)

        # Key preferences should exist
        self.assertIn("simple_docstring", self.router.routing_preferences)
        self.assertIn("complex_code", self.router.routing_preferences)


class TestOmniTagIntegration(unittest.TestCase):
    """Test OmniTag search integration"""

    def test_search_utility_exists(self):
        """Verify search_omnitags.py exists and is executable"""
        search_script = Path("scripts/search_omnitags.py")
        self.assertTrue(search_script.exists())

    def test_tagged_files_discoverable(self):
        """Verify tagged files can be discovered"""
        # This would import and run search_omnitags
        # For now, just verify the script exists
        from tools.search_omnitags import search_omnitags

        # Should be able to search
        results = search_omnitags(Path("."))

        # Should find at least 17 tagged files
        self.assertGreaterEqual(len(results), 17)


class TestAdaptiveWorkflow(unittest.TestCase):
    """Test Adaptive Workflow Protocol integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.router = AgentRouter()

    def test_detect_phase_classifies_tasks(self):
        """DETECT: Different task types are classified correctly"""
        tasks = [
            (TaskType.DOCSTRING, TaskComplexity.SIMPLE),
            (TaskType.SECURITY_AUDIT, TaskComplexity.CRITICAL),
            (TaskType.FULL_FEATURE, TaskComplexity.COMPLEX),
        ]

        for task_type, complexity in tasks:
            task = Task(
                description="Test task", task_type=task_type, complexity=complexity
            )
            decision = self.router.route_task(task)

            # Should get a valid routing decision
            self.assertIsNotNone(decision.agent)
            self.assertIsNotNone(decision.coordination_pattern)

    def test_classify_phase_routes_optimally(self):
        """CLASSIFY: Tasks route to optimal agents"""
        # Simple task → free agent
        simple_task = Task(
            description="Add comment",
            task_type=TaskType.DOCSTRING,
            complexity=TaskComplexity.SIMPLE,
        )
        simple_decision = self.router.route_task(simple_task)
        self.assertTrue(self.router._is_free_agent(simple_decision.agent))

        # Critical task → may use paid for quality
        critical_task = Task(
            description="Security audit",
            task_type=TaskType.SECURITY_AUDIT,
            complexity=TaskComplexity.CRITICAL,
            prefer_free=False,
        )
        critical_decision = self.router.route_task(critical_task)
        # May use Claude for critical decisions
        self.assertIsNotNone(critical_decision.agent)

    def test_execute_phase_has_coordination(self):
        """EXECUTE: Coordination patterns are defined"""
        patterns = self.router.coordination_patterns

        # Should have coordination patterns
        self.assertIn("simple_task", patterns)
        self.assertIn("complex_task", patterns)
        self.assertIn("critical_decision", patterns)
        self.assertIn("full_project", patterns)

    def test_verify_phase_cost_tracking(self):
        """VERIFY: Cost tracking works"""
        task = Task(
            description="Test",
            task_type=TaskType.CODE_GENERATION,
            complexity=TaskComplexity.MODERATE,
        )

        decision = self.router.route_task(task)

        # Should have cost estimate
        self.assertIsNotNone(decision.estimated_cost)
        self.assertGreaterEqual(decision.estimated_cost, 0.0)


def run_integration_tests():
    """Run all integration tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentRouterIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiAgentCoordination))
    suite.addTests(loader.loadTestsFromTestCase(TestOmniTagIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveWorkflow))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)

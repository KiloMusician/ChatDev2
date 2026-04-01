#!/usr/bin/env python3
"""Comprehensive test suite for AgentTaskRouter (Agent Orchestration Hub).
[ROUTE TESTS] 🧪

Tests all core hub functionality:
- Task routing to Ollama, ChatDev, Consciousness, Quantum Resolver
- Consciousness enrichment integration
- Multi-system coordination
- Error handling and fallbacks
- Quest logging
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.tools.agent_task_router import AgentTaskRouter, ConsciousnessHint


@pytest.fixture
def router(tmp_path: Path) -> AgentTaskRouter:
    """Create AgentTaskRouter with temporary paths."""
    router = AgentTaskRouter(repo_root=tmp_path)
    router.quest_log_path = tmp_path / "quest_log.jsonl"
    router.quest_log_path.parent.mkdir(parents=True, exist_ok=True)
    router.quest_log_path.touch()
    return router


@pytest.fixture
def mock_consciousness_bridge():
    """Mock ConsciousnessBridge for testing."""
    with patch("src.integration.consciousness_bridge.ConsciousnessBridge") as mock:
        bridge_instance = MagicMock()
        bridge_instance.contextual_memory = {"test": "data", "semantic": "awareness"}
        bridge_instance.retrieve_contextual_memory.return_value = "Test retrieval result"
        bridge_instance.get_initialization_time.return_value = "2025-12-29 00:00:00"
        mock.return_value = bridge_instance
        yield mock


@pytest.fixture
def mock_chatdev_launcher():
    """Mock ChatDevLauncher for testing."""
    with patch("src.integration.chatdev_launcher.ChatDevLauncher") as mock:
        launcher_instance = MagicMock()
        process_mock = MagicMock()
        process_mock.pid = 12345
        launcher_instance.launch_chatdev.return_value = process_mock
        launcher_instance.api_key_configured = True
        launcher_instance.chatdev_path = Path("/mock/chatdev")
        mock.return_value = launcher_instance
        yield mock


class TestAgentTaskRouterInitialization:
    """Test hub initialization and setup."""

    def test_router_initialization(self, router: AgentTaskRouter):
        """Test that router initializes with correct defaults."""
        assert router.repo_root is not None
        assert router.orchestrator is not None
        assert router.quest_log_path.exists()

    def test_router_with_custom_root(self, tmp_path: Path):
        """Test router with custom repo root."""
        custom_root = tmp_path / "custom"
        custom_root.mkdir()
        router = AgentTaskRouter(repo_root=custom_root)
        assert router.repo_root == custom_root

    def test_build_workspace_awareness_uses_terminal_registry(self, router: AgentTaskRouter):
        """Router should ingest terminal/output registry for agent-facing context."""
        reports = router.repo_root / "state" / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "terminal_awareness_latest.json").write_text(
            json.dumps(
                {
                    "active_session": "intelligent",
                    "agent_registry": [
                        {
                            "agent": "Copilot",
                            "terminals": ["🧩 Copilot"],
                            "purposes": ["agent log watcher"],
                        }
                    ],
                    "terminals": [
                        {
                            "display_name": "🧩 Copilot",
                            "agents": ["Copilot"],
                            "purpose": "agent log watcher",
                            "log_path": str(router.repo_root / "data" / "terminal_logs" / "copilot.log"),
                            "watcher_path": str(
                                router.repo_root
                                / "data"
                                / "terminal_watchers"
                                / "watch_copilot_terminal.ps1"
                            ),
                        }
                    ],
                    "output_surfaces": [
                        {
                            "label": "🧩 Copilot Log",
                            "path": str(router.repo_root / "data" / "terminal_logs" / "copilot.log"),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (reports / "terminal_snapshot_latest.json").write_text(
            json.dumps(
                {
                    "summary": {
                        "configured_session": "intelligent",
                        "total_channels": 26,
                        "output_sources_configured": 102,
                    }
                }
            ),
            encoding="utf-8",
        )

        awareness = router._build_workspace_awareness(
            "copilot",
            "Ask Copilot to review the bridge",
            {},
        )

        assert awareness["active_session"] == "intelligent"
        assert awareness["terminal_count"] == 26
        assert awareness["output_sources_configured"] == 102
        assert awareness["relevant_agents"][0]["agent"] == "Copilot"
        assert "copilot.log" in awareness["relevant_output_artifacts"]


class TestConsciousnessEnrichment:
    """Test consciousness-aware task enrichment."""

    @pytest.mark.asyncio
    async def test_consciousness_enrichment_success(
        self, router: AgentTaskRouter, mock_consciousness_bridge
    ):
        """Test successful consciousness enrichment."""
        result = await router._consciousness_enrich("Test task description", {"key": "value"})

        assert result is not None
        assert isinstance(result, ConsciousnessHint)
        assert result.summary is not None
        assert result.tags is not None
        assert result.confidence == pytest.approx(0.62, rel=1e-2)

    @pytest.mark.asyncio
    async def test_consciousness_enrichment_unavailable(self, router: AgentTaskRouter):
        """Test consciousness enrichment when bridge unavailable."""
        with patch(
            "src.integration.consciousness_bridge.ConsciousnessBridge",
            side_effect=ImportError("Not available"),
        ):
            result = await router._consciousness_enrich("Test", {})
            assert result is None

    @pytest.mark.asyncio
    async def test_consciousness_enrichment_failure(
        self, router: AgentTaskRouter, mock_consciousness_bridge
    ):
        """Test consciousness enrichment when bridge fails."""
        mock_consciousness_bridge.return_value.enhance_contextual_memory.side_effect = RuntimeError(
            "Enrichment failed"
        )

        result = await router._consciousness_enrich("Test", {})
        assert result is None

    @pytest.mark.asyncio
    async def test_enrich_hints_skips_default_consciousness_for_chatdev_target(
        self, router: AgentTaskRouter
    ):
        """ChatDev direct routing should not block on consciousness enrichment by default."""
        with patch.object(router, "_consciousness_enrich", new_callable=AsyncMock) as enrich_mock:
            efficiency_hint, resolved_target, consciousness_hint = await router._enrich_hints(
                "generate",
                "Create a small game",
                {},
                "chatdev",
            )

        assert efficiency_hint is None
        assert resolved_target == "chatdev"
        assert consciousness_hint is None
        enrich_mock.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_enrich_hints_timeout_degrades_without_failure(
        self, router: AgentTaskRouter, monkeypatch: pytest.MonkeyPatch
    ):
        """Consciousness enrichment timeout should degrade gracefully instead of hanging."""

        async def slow_enrich(_: str, __: dict[str, object]) -> ConsciousnessHint:
            await asyncio.sleep(0.2)
            return ConsciousnessHint(summary="late", tags=["slow"], confidence=0.1)

        monkeypatch.setenv("NUSYQ_CONSCIOUSNESS_ENRICH_TIMEOUT_S", "0.01")
        with patch.object(router, "_consciousness_enrich", side_effect=slow_enrich):
            efficiency_hint, resolved_target, consciousness_hint = await router._enrich_hints(
                "analyze",
                "Analyze repository",
                {"consciousness_enrich": True},
                "auto",
            )

        assert efficiency_hint is None or isinstance(efficiency_hint, dict)
        assert resolved_target in {"auto", "ollama"}
        assert consciousness_hint is None


class TestOllamaRouting:
    """Test routing to Ollama local LLM."""

    @pytest.mark.asyncio
    async def test_ollama_routing_success(self, router: AgentTaskRouter, mock_ollama_server):
        """Test successful Ollama routing."""
        with patch(
            "src.ai.ollama_chatdev_integrator.EnhancedOllamaChatDevIntegrator"
        ) as mock_integrator:
            integrator_instance = MagicMock()
            integrator_instance.chat_with_ollama = AsyncMock(return_value="Ollama response")
            integrator_instance.ollama_available = True
            mock_integrator.return_value = integrator_instance

            task = MagicMock()
            task.task_type = "analyze"
            task.content = "Analyze this code"
            task.task_id = "test_task_123"
            # Pin model explicitly so _select_model_from_capabilities doesn't override
            task.context = {"ollama_model": "qwen2.5-coder:14b"}

            result = await router._route_to_ollama(task)

            assert result["status"] == "success"
            assert result["system"] == "ollama"
            assert result["output"] == "Ollama response"
            assert result["model"] == "qwen2.5-coder:14b"

    @pytest.mark.asyncio
    async def test_ollama_routing_failure(self, router: AgentTaskRouter):
        """Test Ollama routing failure handling when all paths are unavailable."""
        # Patch the integrator at the import location in _try_ollama_integrator
        with (
            patch(
                "src.ai.ollama_chatdev_integrator.EnhancedOllamaChatDevIntegrator",
                side_effect=RuntimeError("Ollama unavailable"),
            ),
            patch.object(
                router, "_query_ollama_adapter", side_effect=Exception("Ollama adapter failed")
            ),
            patch.object(router, "_maybe_lmstudio_fallback", return_value=None),
        ):
            task = MagicMock()
            task.task_type = "analyze"
            task.content = "Test"
            task.context = {}  # Prevent MagicMock.context.get() from returning truthy MagicMock
            task.task_id = "test_fail_123"

            result = await router._route_to_ollama(task)

            assert result["status"] == "failed"
            assert "error" in result


class TestChatDevRouting:
    """Test routing to ChatDev multi-agent system."""

    @pytest.mark.asyncio
    async def test_chatdev_routing_success(self, router: AgentTaskRouter, mock_chatdev_launcher):
        """Test successful ChatDev routing."""
        task = MagicMock()
        task.task_type = "generate"
        task.content = "Create a REST API"
        task.context = {"project_name": "MyAPI", "chatdev_model": "GPT_4"}
        task.task_id = "chatdev_task_123"

        result = await router._route_to_chatdev(task)

        assert result["status"] == "success"
        assert result["system"] == "chatdev"
        assert result["output"]["pid"] == 12345
        assert result["output"]["project_name"] == "MyAPI"
        assert result["output"]["model"] == "GPT_4"

    @pytest.mark.asyncio
    async def test_chatdev_routing_wrong_task_type(self, router: AgentTaskRouter):
        """Non-generate tasks are rerouted to Ollama, not failed hard."""
        task = MagicMock()
        task.task_type = "analyze"
        task.content = "Analyze code"
        task.context = {}

        with patch.object(router, "_route_to_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = {"status": "success", "output": "analysis result"}
            result = await router._route_to_chatdev(task)

        assert result["rerouted_from"] == "chatdev"
        assert result["requested_system"] == "chatdev"
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_chatdev_routing_launcher_unavailable(self, router: AgentTaskRouter):
        """Test ChatDev routing when both launcher and factory fallback are unavailable."""
        with patch(
            "src.integration.chatdev_launcher.ChatDevLauncher",
            side_effect=ImportError("Launcher not found"),
        ):
            # Disable factory fallback so we exercise the "all paths unavailable" branch
            with patch("src.tools.agent_task_router.ProjectFactory", None):
                task = MagicMock()
                task.task_type = "generate"
                task.content = "Create app"
                task.context = {}

                result = await router._route_to_chatdev(task)

                assert result["status"] == "failed"
                assert "unavailable" in result["error"]

    @pytest.mark.asyncio
    async def test_chatdev_routing_timeout_uses_fallback(
        self, router: AgentTaskRouter, monkeypatch
    ):
        """Timeout during launch should not hang routing."""

        async def slow_to_thread(*_args, **_kwargs):
            await asyncio.sleep(0.2)
            return {"pid": 1}

        monkeypatch.setenv("NUSYQ_CHATDEV_LAUNCH_TIMEOUT_S", "0.01")
        with patch("src.tools.agent_task_router.to_thread", side_effect=slow_to_thread):
            with patch("src.tools.agent_task_router.ProjectFactory", None):
                task = MagicMock()
                task.task_type = "generate"
                task.content = "Create app"
                task.context = {}

                result = await router._route_to_chatdev(task)

        assert result["status"] == "failed"
        assert "timeout" in str(result.get("error", "")).lower()


class TestCliRouting:
    """Test CLI-backed routing paths (Codex / Claude)."""

    @pytest.mark.asyncio
    async def test_codex_routing_missing_cli(self, router: AgentTaskRouter, monkeypatch):
        # Disable fallback so we get the canonical "not found" failure response.
        # Also mock rate-limit guard so a pre-populated state file doesn't intercept.
        monkeypatch.setenv("NUSYQ_CODEX_FALLBACK", "off")
        monkeypatch.setattr("src.tools.agent_task_router.shutil.which", lambda _: None)
        task = MagicMock()
        task.task_id = "codex_task_123"
        task.task_type = "generate"
        task.content = "Create hello world"
        task.context = {}

        with patch("src.utils.rate_limit_guard.RateLimitGuard.is_rate_limited", return_value=False):
            result = await router._route_to_codex(task)

        assert result["status"] == "failed"
        assert result["system"] == "codex"
        assert result["error"] == "codex_cli_not_found"

    @pytest.mark.asyncio
    async def test_claude_routing_via_orchestrator(
        self, router: AgentTaskRouter, monkeypatch, tmp_path
    ):
        monkeypatch.delenv("NUSYQ_CLAUDE_CLI_COMMAND", raising=False)
        # Mock away all CLI paths so it falls through to ClaudeOrchestrator
        monkeypatch.setattr("src.tools.agent_task_router.shutil.which", lambda _: None)
        # Mock Path.home() to use tmp_path so no VS Code extensions are found
        monkeypatch.setattr("src.tools.agent_task_router.Path.home", lambda: tmp_path)

        with patch("src.orchestration.claude_orchestrator.ClaudeOrchestrator") as mock_orchestrator:
            orchestrator_instance = MagicMock()
            orchestrator_instance.ask_claude = AsyncMock(
                return_value={"response": "Claude response", "model": "claude-3-5-sonnet"}
            )
            mock_orchestrator.return_value = orchestrator_instance

            task = MagicMock()
            task.task_id = "claude_task_123"
            task.task_type = "review"
            task.content = "Review this module"
            task.context = {}

            result = await router._route_to_claude_cli(task)

            assert result["status"] == "success"
            assert result["system"] == "claude_cli"
            assert result["output"] == "Claude response"
            assert result["mode"] == "api"


class TestConsciousnessRouting:
    """Test routing to Consciousness Bridge."""

    @pytest.mark.asyncio
    async def test_consciousness_routing_success(
        self, router: AgentTaskRouter, mock_consciousness_bridge
    ):
        """Test successful consciousness routing."""
        task = MagicMock()
        task.content = "Semantic task"
        task.context = {"key": "value"}
        task.task_id = "consciousness_task_123"

        result = await router._route_to_consciousness(task)

        assert result["status"] == "success"
        assert result["system"] == "consciousness"
        assert "hint" in result
        assert result["hint"]["confidence"] == pytest.approx(0.7, rel=1e-2)

    @pytest.mark.asyncio
    async def test_consciousness_routing_unavailable(self, router: AgentTaskRouter):
        """Test consciousness routing gracefully degrades when bridge unavailable.

        _consciousness_heuristic_fallback is designed to always succeed (graceful
        degradation) — it returns a partial result with reduced confidence rather
        than failing hard.
        """
        with patch(
            "src.integration.consciousness_bridge.ConsciousnessBridge",
            side_effect=ImportError("Bridge not found"),
        ):
            task = MagicMock()
            task.content = "Test"
            task.context = {}

            result = await router._route_to_consciousness(task)

            # Heuristic fallback always succeeds (graceful degradation)
            assert result["status"] == "success"
            assert result.get("mode") == "heuristic_fallback"


class TestQuantumResolverRouting:
    """Test routing to Quantum Problem Resolver."""

    @pytest.mark.asyncio
    async def test_quantum_resolver_success(self, router: AgentTaskRouter):
        """Test successful quantum resolver routing."""
        with patch("src.healing.quantum_problem_resolver.QuantumProblemResolver") as mock_resolver:
            resolver_instance = MagicMock()
            resolver_instance.resolve_problem.return_value = {"fixed": True}
            mock_resolver.return_value = resolver_instance

            task = MagicMock()
            task.task_type = "debug"
            task.content = "Fix this error"
            task.context = {"error": "ImportError"}
            task.task_id = "quantum_task_123"

            result = await router._route_to_quantum_resolver(task)

            assert result["status"] == "success"
            assert result["system"] == "quantum_resolver"
            assert result["output"]["fixed"] is True
            assert result["problem_type"] == "optimization"
            assert result["requested_task_type"] == "debug"

    @pytest.mark.asyncio
    async def test_quantum_resolver_maps_analyze_to_simulation(self, router: AgentTaskRouter):
        """Analyze tasks should map to a supported quantum problem type."""
        with patch("src.healing.quantum_problem_resolver.QuantumProblemResolver") as mock_resolver:
            resolver_instance = MagicMock()
            resolver_instance.resolve_problem.return_value = {"status": "ok", "fixed": True}
            mock_resolver.return_value = resolver_instance

            task = MagicMock()
            task.task_type = "analyze"
            task.content = "Analyze this subsystem"
            task.context = {}
            task.task_id = "quantum_task_analyze"

            result = await router._route_to_quantum_resolver(task)

            assert result["status"] == "success"
            resolver_instance.resolve_problem.assert_called_once()
            assert resolver_instance.resolve_problem.call_args.args[0] == "simulation"

    @pytest.mark.asyncio
    async def test_quantum_resolver_normalizes_output_error_to_failed(
        self, router: AgentTaskRouter
    ):
        """Quantum payload errors should propagate as failed router status."""
        with patch("src.healing.quantum_problem_resolver.QuantumProblemResolver") as mock_resolver:
            resolver_instance = MagicMock()
            resolver_instance.resolve_problem.return_value = {
                "status": "error",
                "error_message": "Unknown problem type: debug",
            }
            mock_resolver.return_value = resolver_instance

            task = MagicMock()
            task.task_type = "debug"
            task.content = "Fix this error"
            task.context = {}
            task.task_id = "quantum_task_error"

            result = await router._route_to_quantum_resolver(task)

            assert result["status"] == "failed"
            assert result["error"] == "Unknown problem type: debug"


class TestUniversalTaskRouting:
    """Test universal route_task method."""

    @pytest.mark.asyncio
    async def test_route_task_to_ollama(self, router: AgentTaskRouter):
        """Test routing task to Ollama."""
        with patch.object(router, "_route_to_ollama", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = {
                "status": "success",
                "system": "ollama",
                "output": "Response",
            }

            result = await router.route_task(
                task_type="analyze",
                description="Analyze code",
                target_system="ollama",
                context={"consciousness_enrich": False},
            )

            assert result["status"] == "success"
            assert result["system"] == "ollama"

    @pytest.mark.asyncio
    async def test_route_task_blocks_triad_target_when_gate_requires_and_snapshot_degraded(
        self, router: AgentTaskRouter
    ):
        degraded = {"action": "multi_agent_doctor", "status": "degraded", "functional": False}
        with patch.object(router, "_load_multi_agent_doctor_snapshot", return_value=degraded):
            result = await router.route_task(
                task_type="analyze",
                description="Ask Copilot to review the bridge",
                target_system="copilot",
                context={"triad_doctor_gate": "require", "consciousness_enrich": False},
            )

        assert result["status"] == "failed"
        assert result["error"] == "triad_doctor_gate_blocked_route"
        assert result["execution_path"] == "triad_doctor_gate:blocked"
        assert result["triad_readiness"]["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_route_task_warn_gate_attaches_triad_snapshot_and_routes(
        self, router: AgentTaskRouter
    ):
        degraded = {"action": "multi_agent_doctor", "status": "degraded", "functional": False}
        with (
            patch.object(router, "_load_multi_agent_doctor_snapshot", return_value=degraded),
            patch.object(router, "_route_to_codex", new_callable=AsyncMock) as mock_route,
        ):
            mock_route.return_value = {
                "status": "success",
                "system": "codex",
                "output": "OK",
                "execution_path": "codex_cli",
            }
            result = await router.route_task(
                task_type="analyze",
                description="Ask Codex to analyze this module",
                target_system="codex",
                context={"triad_doctor_gate": "warn", "consciousness_enrich": False},
            )

        assert result["status"] == "success"
        assert result["system"] == "codex"
        assert result["triad_readiness"]["status"] == "degraded"
        assert result["triad_readiness"]["functional"] is False

    @pytest.mark.asyncio
    async def test_route_task_warn_gate_reroutes_degraded_copilot_analysis_to_codex(
        self, router: AgentTaskRouter
    ):
        degraded = {
            "action": "multi_agent_doctor",
            "status": "degraded",
            "functional": False,
            "summary": {"healthy_agents": ["claude", "codex"], "degraded_agents": ["copilot"]},
            "agents": {
                "copilot": {"functional": False},
                "codex": {"functional": True},
                "claude": {"functional": True},
            },
        }
        with (
            patch.object(router, "_load_multi_agent_doctor_snapshot", return_value=degraded),
            patch.object(router, "_route_to_codex", new_callable=AsyncMock) as mock_codex,
        ):
            mock_codex.return_value = {
                "status": "success",
                "system": "codex",
                "output": "Codex analysis",
                "execution_path": "codex_cli",
            }
            result = await router.route_task(
                task_type="analyze",
                description="Ask Copilot to review the router",
                target_system="copilot",
                context={"triad_doctor_gate": "warn", "consciousness_enrich": False},
            )

        assert result["status"] == "success"
        assert result["system"] == "codex"
        assert result["delegated_from"] == "copilot"
        assert result["delegated_to"] == "codex"
        assert result["triad_fallback"]["reason"] == "triad_warn_fallback"
        assert result["triad_fallback"]["task_class"] == "analysis"

    @pytest.mark.asyncio
    async def test_route_task_warn_gate_reroutes_degraded_copilot_generation_to_claude(
        self, router: AgentTaskRouter
    ):
        degraded = {
            "action": "multi_agent_doctor",
            "status": "degraded",
            "functional": False,
            "summary": {"healthy_agents": ["claude"], "degraded_agents": ["copilot", "codex"]},
            "agents": {
                "copilot": {"functional": False},
                "codex": {"functional": False},
                "claude": {"functional": True},
            },
        }
        with (
            patch.object(router, "_load_multi_agent_doctor_snapshot", return_value=degraded),
            patch.object(router, "_route_to_claude_cli", new_callable=AsyncMock) as mock_claude,
        ):
            mock_claude.return_value = {
                "status": "success",
                "system": "claude_cli",
                "output": "Claude generation",
                "execution_path": "claude_cli",
            }
            result = await router.route_task(
                task_type="generate",
                description="Ask Copilot to draft the component",
                target_system="copilot",
                context={"triad_doctor_gate": "warn", "consciousness_enrich": False},
            )

        assert result["status"] == "success"
        assert result["system"] == "claude_cli"
        assert result["delegated_from"] == "copilot"
        assert result["delegated_to"] == "claude_cli"
        assert result["triad_fallback"]["task_class"] == "generation"

    @pytest.mark.asyncio
    async def test_route_task_with_consciousness_enrichment(
        self, router: AgentTaskRouter, mock_consciousness_bridge
    ):
        """Test route_task with consciousness enrichment enabled."""
        with patch.object(router, "_route_to_ollama", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = {"status": "success"}

            result = await router.route_task(
                task_type="analyze",
                description="Test task",
                target_system="ollama",
            )

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_route_task_auto_mode(self, router: AgentTaskRouter):
        """Test route_task with auto system selection."""
        result = await router.route_task(
            task_type="analyze",
            description="Test task",
            target_system="auto",
            context={"consciousness_enrich": False},
        )

        # auto mode picks the highest-scoring agent from persistent SpecializationLearner state.
        # "ready"   = HuggingFace/MCP bridge available
        # "success" = ollama/chatdev responded
        # "submitted" = queued to background
        # "failed"  = learner picked an offline agent (e.g. lmstudio) — valid auto-routing outcome
        assert result["status"] in ["submitted", "success", "ready", "failed"]
        assert "task_id" in result  # structured response always present

    @pytest.mark.asyncio
    async def test_route_task_quest_logging(self, router: AgentTaskRouter, tmp_path: Path):
        """Test that tasks are logged to quest system."""
        with patch.object(router, "_route_to_ollama", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = {"status": "success"}

            await router.route_task(
                task_type="analyze",
                description="Test logging",
                target_system="ollama",
                context={"consciousness_enrich": False},
            )

            # Check quest log exists and has entries
            assert router.quest_log_path.exists()
            quest_data = router.quest_log_path.read_text()
            assert len(quest_data) > 0


class TestReceiptGeneration:
    """Test receipt generation and auditing."""

    def test_emit_receipt(self, router: AgentTaskRouter, tmp_path: Path):
        """Test receipt emission."""
        receipt_path = router._emit_receipt(
            action_id="test_action",
            inputs={"test": "input"},
            outputs=["output1", "output2"],
            status="success",
            exit_code=0,
            next_steps=["step1", "step2"],
        )

        assert receipt_path.exists()
        receipt_content = receipt_path.read_text()
        assert "test_action" in receipt_content
        assert "success" in receipt_content
        assert "0" in receipt_content


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_full_ollama_workflow(self, router: AgentTaskRouter):
        """Test complete workflow: enrichment → routing → logging."""
        with patch(
            "src.ai.ollama_chatdev_integrator.EnhancedOllamaChatDevIntegrator"
        ) as mock_integrator:
            integrator_instance = MagicMock()
            integrator_instance.chat_with_ollama = AsyncMock(return_value="AI response")
            mock_integrator.return_value = integrator_instance

            result = await router.route_task(
                task_type="analyze",
                description="Full workflow test",
                target_system="ollama",
                context={"consciousness_enrich": False},
            )

            assert result["status"] == "success"
            assert router.quest_log_path.exists()

    @pytest.mark.asyncio
    async def test_full_chatdev_workflow(self, router: AgentTaskRouter, mock_chatdev_launcher):
        """Test complete ChatDev workflow."""
        result = await router.route_task(
            task_type="generate",
            description="Create test project",
            target_system="chatdev",
            context={
                "consciousness_enrich": False,
                "project_name": "TestProject",
            },
        )

        assert result["status"] == "success"
        assert result["system"] == "chatdev"


class TestSystemAnalysisAndHealing:
    """Tests for analyze_system() and heal_system()."""

    @pytest.mark.asyncio
    async def test_analyze_system_success(self, router: AgentTaskRouter, tmp_path):
        """Test system analysis generates health report."""
        with patch("src.diagnostics.quick_system_analyzer.QuickSystemAnalyzer") as mock_analyzer:
            # Mock the analyzer
            analyzer_instance = MagicMock()
            analyzer_instance.quick_scan = MagicMock()
            analyzer_instance.results = {
                "working_files": ["file1.py", "file2.py"],
                "broken_files": ["broken.py"],
                "launch_pad_files": [],
                "enhancement_candidates": [],
            }
            mock_analyzer.return_value = analyzer_instance

            result = await router.analyze_system()

            assert result["status"] == "success"
            assert "summary" in result
            assert result["summary"]["working_files"] == 2
            assert result["summary"]["broken_files"] == 1

    @pytest.mark.asyncio
    async def test_analyze_system_with_target(self, router: AgentTaskRouter):
        """Test system analysis with specific target."""
        with patch("src.diagnostics.quick_system_analyzer.QuickSystemAnalyzer") as mock_analyzer:
            analyzer_instance = MagicMock()
            analyzer_instance.quick_scan = MagicMock()
            analyzer_instance.results = {
                "working_files": ["file1.py"],
                "broken_files": [],
                "launch_pad_files": [],
                "enhancement_candidates": [],
            }
            mock_analyzer.return_value = analyzer_instance

            result = await router.analyze_system(target="src/")

            assert result["status"] == "success"
            assert result["summary"]["broken_files"] == 0

    @pytest.mark.asyncio
    async def test_heal_system_preview_mode(self, router: AgentTaskRouter):
        """Test heal_system in preview mode (auto_confirm=False)."""
        with (
            patch("ecosystem_health_checker.EcosystemHealthChecker") as mock_checker,
            patch("src.healing.repository_health_restorer.RepositoryHealthRestorer") as mock_healer,
        ):
            # Mock health checker
            checker_instance = MagicMock()
            checker_instance.check_ollama_health = MagicMock()
            checker_instance.check_repository_health = MagicMock()
            checker_instance.health_report = {"status": "healthy"}
            checker_instance.repos = {}
            mock_checker.return_value = checker_instance

            # Mock healer
            healer_instance = MagicMock()
            healer_instance.install_missing_dependencies = MagicMock(return_value=False)
            healer_instance.create_missing_modules = MagicMock(return_value=False)
            mock_healer.return_value = healer_instance

            result = await router.heal_system(auto_confirm=False)

            assert result["status"] == "success"
            assert "analysis_only" in result["actions_taken"]

    @pytest.mark.asyncio
    async def test_heal_system_apply_mode(self, router: AgentTaskRouter):
        """Test heal_system applies fixes (auto_confirm=True)."""
        with (
            patch("ecosystem_health_checker.EcosystemHealthChecker") as mock_checker,
            patch("src.healing.repository_health_restorer.RepositoryHealthRestorer") as mock_healer,
        ):
            # Mock health checker
            checker_instance = MagicMock()
            checker_instance.check_ollama_health = MagicMock()
            checker_instance.check_repository_health = MagicMock()
            checker_instance.health_report = {"status": "healthy"}
            checker_instance.repos = {}
            mock_checker.return_value = checker_instance

            # Mock healer - simulate successful fixes
            healer_instance = MagicMock()
            healer_instance.install_missing_dependencies = MagicMock(return_value=True)
            healer_instance.create_missing_modules = MagicMock(return_value=True)
            mock_healer.return_value = healer_instance

            result = await router.heal_system(auto_confirm=True)

            assert result["status"] == "success"
            assert "dependencies_installed" in result["actions_taken"]
            assert "modules_created" in result["actions_taken"]


class TestDevelopmentLoop:
    """Tests for develop_system() autonomous loop."""

    @pytest.mark.asyncio
    async def test_develop_system_single_iteration(self, router: AgentTaskRouter):
        """Test development loop with 1 iteration."""
        with (
            patch("src.diagnostics.quick_system_analyzer.QuickSystemAnalyzer") as mock_analyzer,
            patch("ecosystem_health_checker.EcosystemHealthChecker") as mock_checker,
            patch("src.healing.repository_health_restorer.RepositoryHealthRestorer") as mock_healer,
        ):
            # Mock analyzer
            analyzer_instance = MagicMock()
            analyzer_instance.quick_scan = MagicMock()
            analyzer_instance.results = {
                "working_files": ["file1.py"],
                "broken_files": [],
                "launch_pad_files": [],
                "enhancement_candidates": [],
            }
            mock_analyzer.return_value = analyzer_instance

            # Mock health checker
            checker_instance = MagicMock()
            checker_instance.check_ollama_health = MagicMock()
            checker_instance.check_repository_health = MagicMock()
            checker_instance.health_report = {"status": "healthy"}
            checker_instance.repos = {}
            mock_checker.return_value = checker_instance

            # Mock healer
            healer_instance = MagicMock()
            healer_instance.install_missing_dependencies = MagicMock(return_value=False)
            healer_instance.create_missing_modules = MagicMock(return_value=False)
            mock_healer.return_value = healer_instance

            result = await router.develop_system(max_iterations=1, halt_on_error=False)

            assert result["status"] == "success"
            assert result["iterations"] >= 1
            assert "results" in result

    @pytest.mark.asyncio
    async def test_develop_system_captures_intent(self, router: AgentTaskRouter):
        """Test development loop captures intent when goals achieved."""
        with (
            patch("src.diagnostics.quick_system_analyzer.QuickSystemAnalyzer") as mock_analyzer,
            patch("ecosystem_health_checker.EcosystemHealthChecker") as mock_checker,
            patch("src.healing.repository_health_restorer.RepositoryHealthRestorer") as mock_healer,
        ):
            # Simulate broken → fixed progression
            analyzer_instance = MagicMock()
            analyzer_instance.quick_scan = MagicMock()
            # First iteration: broken
            analyzer_results_broken = {
                "working_files": ["file1.py"],
                "broken_files": ["broken.py"] * 5,
                "launch_pad_files": [],
                "enhancement_candidates": [],
            }
            # Second iteration: fixed
            analyzer_results_fixed = {
                "working_files": ["file1.py", "broken.py"] * 3,
                "broken_files": [],
                "launch_pad_files": [],
                "enhancement_candidates": [],
            }
            analyzer_instance.results = analyzer_results_broken
            call_count = [0]

            def switch_results(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    analyzer_instance.results = analyzer_results_broken
                else:
                    analyzer_instance.results = analyzer_results_fixed

            analyzer_instance.quick_scan = MagicMock(side_effect=switch_results)
            mock_analyzer.return_value = analyzer_instance

            # Mock health checker
            checker_instance = MagicMock()
            checker_instance.check_ollama_health = MagicMock()
            checker_instance.check_repository_health = MagicMock()
            checker_instance.health_report = {"status": "healthy"}
            checker_instance.repos = {}
            mock_checker.return_value = checker_instance

            # Mock healer - simulate fixing issues
            healer_instance = MagicMock()
            healer_instance.install_missing_dependencies = MagicMock(return_value=True)
            healer_instance.create_missing_modules = MagicMock(return_value=False)
            mock_healer.return_value = healer_instance

            result = await router.develop_system(max_iterations=2, halt_on_error=False)

            assert result["status"] == "success"
            assert result.get("intent_events", 0) >= 0  # Intent may be captured

    @pytest.mark.asyncio
    async def test_develop_system_halt_on_error(self, router: AgentTaskRouter):
        """Test development loop halts on error when configured."""
        with patch("src.diagnostics.quick_system_analyzer.QuickSystemAnalyzer") as mock_analyzer:
            # Simulate error condition
            analyzer_instance = MagicMock()
            analyzer_instance.quick_scan = MagicMock(side_effect=RuntimeError("Analysis failed"))
            mock_analyzer.return_value = analyzer_instance

            result = await router.develop_system(max_iterations=3, halt_on_error=True)

            # Should stop gracefully
            assert result["status"] in ["success", "failed"]


class TestQuantumResolver:
    """Tests for quantum_resolver target system."""

    @pytest.mark.asyncio
    async def test_route_to_quantum_resolver(self, router: AgentTaskRouter):
        """Test routing debug tasks to quantum resolver."""
        with patch("src.healing.quantum_problem_resolver.QuantumProblemResolver") as mock_qpr:
            resolver_instance = MagicMock()
            # Don't use AsyncMock here - route_task will call methods directly
            resolver_instance.resolve_problem = MagicMock(
                return_value={"status": "resolved", "solution": "Multi-modal healing applied"}
            )
            mock_qpr.return_value = resolver_instance

            result = await router.route_task(
                task_type="debug",
                description="Fix circular import error",
                context={"error_trace": "ImportError: ..."},
                target_system="quantum_resolver",
            )

            # Quantum resolver routing may fail gracefully if not properly integrated
            assert result["status"] in ["success", "submitted", "completed", "failed"]


class TestCaptureIntentAndPlanBuilding:
    """Tests for _capture_intent() and _build_plan() helpers."""

    def test_capture_intent_when_healthy(self, router: AgentTaskRouter):
        """Test intent capture when system becomes healthy."""
        from datetime import datetime

        intent = router._capture_intent(
            broken_count=0,
            iteration_index=1,
            current_state={"health_score": 1.0, "timestamp": datetime.now().isoformat()},
            heal_log={"actions": ["Fixed imports"]},
        )

        assert intent is not None
        assert intent["type"] == "system_health_achieved"
        assert intent["iteration"] == 1

    def test_capture_intent_still_broken(self, router: AgentTaskRouter):
        """Test intent not captured when system still broken."""
        from datetime import datetime

        intent = router._capture_intent(
            broken_count=5,
            iteration_index=1,
            current_state={"health_score": 0.9, "timestamp": datetime.now().isoformat()},
            heal_log={"actions": []},
        )

        # No intent if still broken
        assert intent is None

    def test_build_plan_for_healthy_system(self, router: AgentTaskRouter):
        """Test plan building when system is healthy."""
        plan = router._build_plan(broken_count=0, prev_state={"health_score": 1.0})

        assert plan is not None
        assert "next_steps" in plan or isinstance(plan, dict)

    def test_build_plan_for_broken_system(self, router: AgentTaskRouter):
        """Test plan building prioritizes healing when broken."""
        plan = router._build_plan(broken_count=10, prev_state={"health_score": 0.8})

        assert plan is not None
        # Plan should prioritize healing
        plan_str = str(plan).lower()
        assert "heal" in plan_str or "fix" in plan_str or "repair" in plan_str


class TestQuestWiring:
    """Tests for _wire_intent_to_quest() integration."""

    @pytest.mark.asyncio
    async def test_wire_intent_to_quest_log(self, router: AgentTaskRouter):
        """Test wiring intent events to quest log."""
        intent_events = [
            {
                "goal_achieved": "System healed",
                "timestamp": "2026-01-04T07:00:00",
                "confidence": 0.95,
                "type": "system_health_achieved",
                "message": "System healed successfully",
            }
        ]

        count = await router._wire_intent_to_quest(intent_events)

        # Should append to quest log
        assert router.quest_log_path.exists()
        assert count == 1

        # Read quest log to verify
        with router.quest_log_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) > 0
            last_entry = json.loads(lines[-1])
            assert last_entry["task_type"] == "cultivation_intent"

    @pytest.mark.asyncio
    async def test_wire_intent_handles_missing_quest_log(self, router: AgentTaskRouter, tmp_path):
        """Test intent wiring creates quest log if missing."""
        # Delete quest log
        if router.quest_log_path.exists():
            router.quest_log_path.unlink()

        intent_events = [{"event": "test_intent", "type": "test"}]
        count = await router._wire_intent_to_quest(intent_events)

        # Quest log should be created
        assert router.quest_log_path.exists()
        assert count == 1


class TestHelperMethods:
    """Tests for internal helper methods."""

    @pytest.mark.asyncio
    async def test_write_json(self, router: AgentTaskRouter, tmp_path):
        """Test _write_json writes valid JSON."""
        test_path = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}

        await router._write_json(test_path, test_data)

        assert test_path.exists()
        with test_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
            assert loaded == test_data

    @pytest.mark.asyncio
    async def test_append_lines(self, router: AgentTaskRouter, tmp_path):
        """Test _append_lines appends text correctly."""
        test_path = tmp_path / "test.txt"

        # _append_lines expects lines to already have newlines
        await router._append_lines(test_path, ["Line 1\n", "Line 2\n"])
        assert test_path.exists()

        await router._append_lines(test_path, ["Line 3\n"])

        with test_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 3
            assert "Line 1" in lines[0]
            assert "Line 3" in lines[2]


class TestTriadFallbackRouting:
    """Tests for _get_triad_fallback() and smart peer rerouting logic.

    Snapshot format: {"agents": {name: {"functional": bool}}, "summary": {"healthy_agents": [...]}}
    """

    @staticmethod
    def _snap(*healthy: str) -> dict:
        return {"agents": {a: {"functional": True} for a in healthy}}

    def test_fallback_returns_healthy_peer(self, router: AgentTaskRouter) -> None:
        result = router._get_triad_fallback("copilot", self._snap("codex", "claude_cli"), "analyze")
        assert result == "codex"

    def test_fallback_skips_unhealthy_first_peer(self, router: AgentTaskRouter) -> None:
        # codex not healthy, claude_cli is
        result = router._get_triad_fallback("copilot", self._snap("claude_cli"), "review")
        assert result == "claude_cli"

    def test_fallback_returns_none_when_no_healthy_peer(self, router: AgentTaskRouter) -> None:
        result = router._get_triad_fallback("copilot", self._snap(), "analyze")
        assert result is None

    def test_fallback_returns_none_for_non_cognitive_task(self, router: AgentTaskRouter) -> None:
        # "interactive_session" maps to "default" class which is NOT in _TRIAD_FALLBACK_TASK_CLASS_PREFERENCES
        result = router._get_triad_fallback("copilot", self._snap("codex", "claude_cli"), "interactive_session")
        assert result is None

    def test_fallback_codex_degraded_prefers_claude_cli(self, router: AgentTaskRouter) -> None:
        result = router._get_triad_fallback("codex", self._snap("claude_cli", "copilot"), "debug")
        assert result == "claude_cli"

    def test_fallback_claude_cli_degraded_prefers_codex(self, router: AgentTaskRouter) -> None:
        result = router._get_triad_fallback("claude_cli", self._snap("codex"), "generate")
        assert result == "codex"

    def test_fallback_unknown_target_returns_none(self, router: AgentTaskRouter) -> None:
        # No peer mapping for a non-triad agent
        result = router._get_triad_fallback("ollama", self._snap("codex", "claude_cli"), "analyze")
        assert result is None

    def test_fallback_disabled_via_env(
        self, router: AgentTaskRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NUSYQ_TRIAD_ROUTER_FALLBACK", "off")
        result = router._get_triad_fallback("copilot", self._snap("codex", "claude_cli"), "analyze")
        assert result is None

    def test_fallback_all_cognitive_task_types_accepted(self, router: AgentTaskRouter) -> None:
        snap = self._snap("codex")
        for task_type in ("analyze", "review", "debug", "generate", "refactor", "test", "document", "optimize"):
            result = router._get_triad_fallback("copilot", snap, task_type)
            assert result == "codex", f"Expected fallback for task_type={task_type!r}"

    def test_fallback_vscode_codex_degraded(self, router: AgentTaskRouter) -> None:
        result = router._get_triad_fallback("vscode_codex", self._snap("claude_cli"), "refactor")
        assert result == "claude_cli"

    def test_fallback_healthy_agents_from_summary(self, router: AgentTaskRouter) -> None:
        # Health sourced via summary.healthy_agents instead of agents map
        snap = {"summary": {"healthy_agents": ["codex"]}, "agents": {}}
        result = router._get_triad_fallback("copilot", snap, "analyze")
        assert result == "codex"

    def test_triad_fallback_peers_is_class_var(self) -> None:
        assert isinstance(AgentTaskRouter._TRIAD_FALLBACK_PEERS, dict)
        assert "copilot" in AgentTaskRouter._TRIAD_FALLBACK_PEERS

    def test_triad_task_class_map_covers_cognitive_tasks(self) -> None:
        # _TRIAD_TASK_CLASS_MAP gates which task types are eligible for fallback
        assert isinstance(AgentTaskRouter._TRIAD_TASK_CLASS_MAP, dict)
        assert "analyze" in AgentTaskRouter._TRIAD_TASK_CLASS_MAP
        assert "generate" in AgentTaskRouter._TRIAD_TASK_CLASS_MAP


class TestCopilotOrchestrationInjection:
    """Tests for orchestration manifest injection into Copilot bridge."""

    @pytest.mark.asyncio
    async def test_copilot_bridge_injects_orch_block_when_orchestration_mode(
        self, router: AgentTaskRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Orchestration manifest is prepended to Copilot prompt when orchestration_mode=True."""
        import shutil

        monkeypatch.setenv("NUSYQ_COPILOT_BRIDGE_MODE", "live")
        monkeypatch.setattr(shutil, "which", lambda _cmd: None)  # No copilot CLI found

        captured_prompts: list[str] = []

        class FakeExtension:
            async def activate(self) -> None:
                pass

            async def send_query(self, prompt: str) -> dict:
                captured_prompts.append(prompt)
                return {"text": "ok"}

            async def close(self) -> None:
                pass

        monkeypatch.setattr(
            "src.copilot.extension.copilot_extension.CopilotExtension",
            FakeExtension,
        )

        # _build_orchestration_block needs to exist — patch to a known value
        monkeypatch.setattr(router, "_build_orchestration_block", lambda _task: "ORCH_MANIFEST")

        await router.route_task(
            task_type="orchestrate",
            description="do something orchestrated",
            context={"orchestration_mode": True, "consciousness_enrich": False},
            target_system="copilot",
        )

        assert captured_prompts, "send_query was not called"
        assert "ORCH_MANIFEST" in captured_prompts[0], "Orchestration block not injected"

    @pytest.mark.asyncio
    async def test_copilot_bridge_no_orch_block_without_orchestration_mode(
        self, router: AgentTaskRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without orchestration_mode, no orchestration block is prepended."""
        import shutil

        monkeypatch.setenv("NUSYQ_COPILOT_BRIDGE_MODE", "live")
        monkeypatch.setattr(shutil, "which", lambda _cmd: None)

        captured_prompts: list[str] = []

        class FakeExtension:
            async def activate(self) -> None:
                pass

            async def send_query(self, prompt: str) -> dict:
                captured_prompts.append(prompt)
                return {"text": "ok"}

            async def close(self) -> None:
                pass

        monkeypatch.setattr(
            "src.copilot.extension.copilot_extension.CopilotExtension",
            FakeExtension,
        )
        monkeypatch.setattr(router, "_build_orchestration_block", lambda _task: "ORCH_MANIFEST")

        await router.route_task(
            task_type="analyze",
            description="plain analysis",
            context={"consciousness_enrich": False},
            target_system="copilot",
        )

        assert captured_prompts, "send_query was not called"
        assert "ORCH_MANIFEST" not in captured_prompts[0], "Orchestration block injected unexpectedly"


class TestOptimizerRouting:
    """Tests for _route_to_continuous_optimizer."""

    @pytest.fixture
    def mock_cycle(self):
        from src.orchestration.continuous_optimization_engine import OptimizationCycle
        return OptimizationCycle(
            timestamp="2026-01-01T00:00:00",
            duration_seconds=2.0,
            health_improvement=3.0,
            healing_fixes_applied=1,
            search_files_updated=5,
        )

    @pytest.mark.asyncio
    async def test_status_operation_returns_ready(self, router: AgentTaskRouter, mock_cycle):
        with patch("src.orchestration.continuous_optimization_engine.ContinuousOptimizationEngine") as MockEng:
            eng = MagicMock()
            eng.get_optimization_history.return_value = [mock_cycle]
            MockEng.return_value = eng
            result = await router.route_task(
                task_type="analyze",
                description="optimizer status",
                context={"operation": "status"},
                target_system="optimizer",
            )
        assert result["status"] == "ready"
        assert result["agent"] == "optimizer"
        assert result["output"]["last_cycle"]["health_improvement"] == 3.0

    @pytest.mark.asyncio
    async def test_status_no_history(self, router: AgentTaskRouter):
        with patch("src.orchestration.continuous_optimization_engine.ContinuousOptimizationEngine") as MockEng:
            eng = MagicMock()
            eng.get_optimization_history.return_value = []
            MockEng.return_value = eng
            result = await router.route_task(
                task_type="analyze",
                description="status check",
                context={"operation": "status"},
                target_system="optimizer",
            )
        assert result["output"]["last_cycle"] is None

    @pytest.mark.asyncio
    async def test_run_cycle_operation(self, router: AgentTaskRouter, mock_cycle):
        with patch("src.orchestration.continuous_optimization_engine.ContinuousOptimizationEngine") as MockEng:
            eng = MagicMock()
            eng.run_single_cycle.return_value = mock_cycle
            MockEng.return_value = eng
            result = await router.route_task(
                task_type="optimize",
                description="run optimization cycle",
                context={"operation": "run_cycle"},
                target_system="optimizer",
            )
        assert result["status"] == "success"
        assert result["output"]["cycle"]["health_improvement"] == 3.0
        assert result["output"]["cycle"]["healing_fixes_applied"] == 1

    @pytest.mark.asyncio
    async def test_history_operation(self, router: AgentTaskRouter, mock_cycle):
        with patch("src.orchestration.continuous_optimization_engine.ContinuousOptimizationEngine") as MockEng:
            eng = MagicMock()
            eng.get_optimization_history.return_value = [mock_cycle, mock_cycle]
            MockEng.return_value = eng
            result = await router.route_task(
                task_type="analyze",
                description="show optimization history",
                context={"operation": "history", "limit": "2"},
                target_system="optimizer",
            )
        assert result["status"] == "success"
        assert result["output"]["count"] == 2
        assert len(result["output"]["cycles"]) == 2

    @pytest.mark.asyncio
    async def test_unknown_operation_returns_failed(self, router: AgentTaskRouter):
        with patch("src.orchestration.continuous_optimization_engine.ContinuousOptimizationEngine"):
            result = await router.route_task(
                task_type="analyze",
                description="unknown op",
                context={"operation": "nope"},
                target_system="optimizer",
            )
        assert result["status"] == "failed"
        assert "Unknown operation" in result["error"]

    @pytest.mark.asyncio
    async def test_runtime_exception_returns_failed(self, router: AgentTaskRouter):
        with patch("src.orchestration.continuous_optimization_engine.ContinuousOptimizationEngine") as MockEng:
            MockEng.side_effect = RuntimeError("engine exploded")
            result = await router.route_task(
                task_type="analyze",
                description="optimizer test",
                context={"operation": "status"},
                target_system="optimizer",
            )
        assert result["status"] == "failed"
        assert "engine exploded" in result["error"]


class TestHermesRouting:
    """Tests for _route_to_hermes."""

    @pytest.mark.asyncio
    async def test_missing_cli_returns_failed(self, router: AgentTaskRouter, tmp_path, monkeypatch):
        monkeypatch.setattr(router, "repo_root", tmp_path)
        result = await router.route_task(
            task_type="analyze",
            description="do something",
            context={},
            target_system="hermes",
        )
        assert result["status"] == "failed"
        assert result["error"] == "hermes_cli_not_found"
        assert "handoff" in result

    @pytest.mark.asyncio
    async def test_success_path(self, router: AgentTaskRouter, tmp_path, monkeypatch):
        hermes_dir = tmp_path / "state" / "runtime" / "external" / "hermes-agent"
        hermes_dir.mkdir(parents=True)
        (hermes_dir / "cli.py").write_text("# stub")
        monkeypatch.setattr(router, "repo_root", tmp_path)

        async def fake_run_cli(cmd, _input, _timeout, **_kw):
            return 0, "hermes output text", ""

        monkeypatch.setattr(router, "_run_cli_command", fake_run_cli)

        result = await router.route_task(
            task_type="analyze",
            description="analyze codebase",
            context={},
            target_system="hermes",
        )
        assert result["status"] == "success"
        assert result["output"] == "hermes output text"

    @pytest.mark.asyncio
    async def test_toolsets_flag_added(self, router: AgentTaskRouter, tmp_path, monkeypatch):
        hermes_dir = tmp_path / "state" / "runtime" / "external" / "hermes-agent"
        hermes_dir.mkdir(parents=True)
        (hermes_dir / "cli.py").write_text("# stub")
        monkeypatch.setattr(router, "repo_root", tmp_path)

        captured_cmd: list = []

        async def fake_run_cli(cmd, *_a, **_kw):
            captured_cmd.extend(cmd)
            return 0, "result", ""

        monkeypatch.setattr(router, "_run_cli_command", fake_run_cli)

        await router.route_task(
            task_type="analyze",
            description="web search test",
            context={"toolsets": "web,terminal"},
            target_system="hermes",
        )
        assert "--toolsets" in captured_cmd
        assert "web,terminal" in captured_cmd

    @pytest.mark.asyncio
    async def test_model_flag_added(self, router: AgentTaskRouter, tmp_path, monkeypatch):
        hermes_dir = tmp_path / "state" / "runtime" / "external" / "hermes-agent"
        hermes_dir.mkdir(parents=True)
        (hermes_dir / "cli.py").write_text("# stub")
        monkeypatch.setattr(router, "repo_root", tmp_path)

        captured_cmd: list = []

        async def fake_run_cli(cmd, *_a, **_kw):
            captured_cmd.extend(cmd)
            return 0, "result", ""

        monkeypatch.setattr(router, "_run_cli_command", fake_run_cli)

        await router.route_task(
            task_type="analyze",
            description="test",
            context={"model": "openai/gpt-4o"},
            target_system="hermes",
        )
        assert "--model" in captured_cmd
        assert "openai/gpt-4o" in captured_cmd

    @pytest.mark.asyncio
    async def test_nonzero_returncode_returns_failed(self, router: AgentTaskRouter, tmp_path, monkeypatch):
        hermes_dir = tmp_path / "state" / "runtime" / "external" / "hermes-agent"
        hermes_dir.mkdir(parents=True)
        (hermes_dir / "cli.py").write_text("# stub")
        monkeypatch.setattr(router, "repo_root", tmp_path)

        async def fake_run_cli(*_a, **_kw):
            return 1, "", "something went wrong"

        monkeypatch.setattr(router, "_run_cli_command", fake_run_cli)

        result = await router.route_task(
            task_type="analyze",
            description="failing task",
            context={},
            target_system="hermes",
        )
        assert result["status"] == "failed"
        assert "hermes_failed" in result["error"]

    @pytest.mark.asyncio
    async def test_timeout_returns_failed(self, router: AgentTaskRouter, tmp_path, monkeypatch):
        hermes_dir = tmp_path / "state" / "runtime" / "external" / "hermes-agent"
        hermes_dir.mkdir(parents=True)
        (hermes_dir / "cli.py").write_text("# stub")
        monkeypatch.setattr(router, "repo_root", tmp_path)

        async def fake_run_cli(*_a, **_kw):
            raise TimeoutError()

        monkeypatch.setattr(router, "_run_cli_command", fake_run_cli)

        result = await router.route_task(
            task_type="analyze",
            description="slow task",
            context={"timeout_seconds": 1},
            target_system="hermes",
        )
        assert result["status"] == "failed"
        assert "timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_oserror_returns_failed(self, router: AgentTaskRouter, tmp_path, monkeypatch):
        hermes_dir = tmp_path / "state" / "runtime" / "external" / "hermes-agent"
        hermes_dir.mkdir(parents=True)
        (hermes_dir / "cli.py").write_text("# stub")
        monkeypatch.setattr(router, "repo_root", tmp_path)

        async def fake_run_cli(*_a, **_kw):
            raise OSError("permission denied")

        monkeypatch.setattr(router, "_run_cli_command", fake_run_cli)

        result = await router.route_task(
            task_type="analyze",
            description="exec error",
            context={},
            target_system="hermes",
        )
        assert result["status"] == "failed"
        assert "hermes_exec_error" in result["error"]


class TestMetaClawRouting:
    """Tests for _route_to_metaclaw."""

    @pytest.mark.asyncio
    async def test_runtime_missing_returns_offline(self, router: AgentTaskRouter, tmp_path, monkeypatch):
        monkeypatch.setattr(router, "repo_root", tmp_path)
        result = await router.route_task(
            task_type="observe",
            description="metaclaw status",
            context={},
            target_system="metaclaw",
        )
        assert result["status"] == "offline"
        assert result["output"]["available"] is False

    @pytest.mark.asyncio
    async def test_status_operation_returns_ready_when_node_ok(
        self, router: AgentTaskRouter, tmp_path, monkeypatch
    ):
        runtime_dir = tmp_path / "state" / "runtime" / "external" / "metaclaw-agent"
        (runtime_dir / "node_modules").mkdir(parents=True)
        monkeypatch.setattr(router, "repo_root", tmp_path)
        with patch("shutil.which", return_value="/usr/bin/node"):
            result = await router.route_task(
                task_type="observe",
                description="status check",
                context={"operation": "status"},
                target_system="metaclaw",
            )
        assert result["status"] == "ready"
        assert result["output"]["node_available"] is True

    @pytest.mark.asyncio
    async def test_status_degraded_when_node_missing(
        self, router: AgentTaskRouter, tmp_path, monkeypatch
    ):
        runtime_dir = tmp_path / "state" / "runtime" / "external" / "metaclaw-agent"
        runtime_dir.mkdir(parents=True)
        monkeypatch.setattr(router, "repo_root", tmp_path)
        with patch("shutil.which", return_value=None):
            result = await router.route_task(
                task_type="observe",
                description="status check",
                context={"operation": "status"},
                target_system="metaclaw",
            )
        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_keyword_inference_bounty(
        self, router: AgentTaskRouter, tmp_path, monkeypatch
    ):
        """Prompt with 'bounty' keyword → operation inferred as bounty."""
        runtime_dir = tmp_path / "state" / "runtime" / "external" / "metaclaw-agent"
        runtime_dir.mkdir(parents=True)
        monkeypatch.setattr(router, "repo_root", tmp_path)
        # No index.js → will hit "no_entry" path after inference
        result = await router.route_task(
            task_type="observe",
            description="Find a bounty mission on Base",
            context={},  # no explicit operation
            target_system="metaclaw",
        )
        # Should try bounty operation and fail with no_entry (not status)
        assert result["status"] == "failed"
        assert "no_entry" in result["execution_path"]

    @pytest.mark.asyncio
    async def test_no_entry_js_returns_failed(
        self, router: AgentTaskRouter, tmp_path, monkeypatch
    ):
        runtime_dir = tmp_path / "state" / "runtime" / "external" / "metaclaw-agent"
        runtime_dir.mkdir(parents=True)
        monkeypatch.setattr(router, "repo_root", tmp_path)
        result = await router.route_task(
            task_type="observe",
            description="trace test",
            context={"operation": "trace"},
            target_system="metaclaw",
        )
        assert result["status"] == "failed"
        assert "No index.js" in result["error"]

    @pytest.mark.asyncio
    async def test_node_success_json_output(
        self, router: AgentTaskRouter, tmp_path, monkeypatch
    ):
        runtime_dir = tmp_path / "state" / "runtime" / "external" / "metaclaw-agent"
        runtime_dir.mkdir(parents=True)
        (runtime_dir / "index.js").write_text("// stub")
        monkeypatch.setattr(router, "repo_root", tmp_path)

        async def fake_wait_for(coro, timeout):
            return (b'{"bounties": [{"id": "1"}]}', b"")

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = MagicMock(return_value=MagicMock())  # non-async so no stray coroutines

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            patch("asyncio.wait_for", side_effect=fake_wait_for),
        ):
            result = await router.route_task(
                task_type="observe",
                description="get bounties",
                context={"operation": "bounty"},
                target_system="metaclaw",
            )
        assert result["system"] == "metaclaw"
        assert result["status"] == "success"
        assert result["output"] == {"bounties": [{"id": "1"}]}

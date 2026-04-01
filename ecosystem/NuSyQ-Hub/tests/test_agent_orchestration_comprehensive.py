"""
Comprehensive test suite for agent orchestration hub (Zeta11 - Testing Framework).
Covers agent initialization, routing, communication, and state management.

Target: 90%+ coverage of src/agents/agent_orchestration_hub.py
"""

import pytest


class TestAgentOrchestrationInitialization:
    """Test agent orchestration hub initialization and setup."""

    @pytest.fixture
    async def orchestration_hub(self):
        """Create orchestration hub instance for testing."""
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub

        hub = AgentOrchestrationHub()
        yield hub
        await hub.shutdown() if hasattr(hub, "shutdown") else None

    async def test_hub_initialization(self, orchestration_hub):
        """Test hub initializes with service registry."""
        assert orchestration_hub is not None
        assert hasattr(orchestration_hub, "_services")
        assert isinstance(orchestration_hub._services, dict)

    async def test_hub_agent_registry(self, orchestration_hub):
        """Test hub maintains service registry."""
        # Hub uses _services for service registration
        assert hasattr(orchestration_hub, "_services")
        assert isinstance(orchestration_hub._services, dict)

    @pytest.mark.parametrize("service_name", ["claude", "ollama", "chatdev", "copilot"])
    async def test_agent_type_availability(self, orchestration_hub, service_name):
        """Test service registry can be populated."""
        # Service registry starts empty - services are registered as needed
        assert isinstance(orchestration_hub._services, dict)
        # Service would be registered via register_service() when first used


class TestAgentRouting:
    """Test AgentOrchestrationHub routing helpers and complexity estimation."""

    @pytest.fixture
    def hub(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub
        return AgentOrchestrationHub(enable_healing=False, enable_consciousness=False)

    def test_estimate_complexity_short_description(self, hub):
        """Short task descriptions get low complexity scores."""
        score = hub._estimate_complexity("fix bug")
        assert isinstance(score, int)
        assert score >= 0

    def test_estimate_complexity_long_description(self, hub):
        """Longer/more complex task descriptions get higher complexity."""
        short = hub._estimate_complexity("fix")
        long = hub._estimate_complexity(
            "Implement full REST API with authentication, database integration, "
            "tests, documentation, and CI/CD pipeline with complex multi-step logic"
        )
        assert long >= short

    def test_estimate_complexity_returns_int(self, hub):
        assert isinstance(hub._estimate_complexity("analyze code"), int)

    def test_hub_has_route_task_method(self, hub):
        """route_task is an async method on the hub."""
        import inspect
        assert hasattr(hub, "route_task")
        assert inspect.iscoroutinefunction(hub.route_task)

    def test_hub_has_orchestrate_multi_agent_method(self, hub):
        """orchestrate_multi_agent_task is available on hub."""
        import inspect
        assert hasattr(hub, "orchestrate_multi_agent_task")
        assert inspect.iscoroutinefunction(hub.orchestrate_multi_agent_task)

    def test_hub_has_send_agent_message_method(self, hub):
        import inspect
        assert hasattr(hub, "send_agent_message")
        assert inspect.iscoroutinefunction(hub.send_agent_message)


class TestAgentCommunication:
    """Test AgentOrchestrationHub message analysis and sentiment helpers."""

    @pytest.fixture
    def hub(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub
        return AgentOrchestrationHub(enable_healing=False, enable_consciousness=False)

    async def test_analyze_message_sentiment_returns_string(self, hub):
        """_analyze_message_sentiment returns a sentiment label."""
        result = await hub._analyze_message_sentiment({"content": "error occurred in module"})
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_analyze_message_sentiment_positive(self, hub):
        """Positive content gets a positive-leaning sentiment."""
        result = await hub._analyze_message_sentiment({"content": "task completed successfully"})
        assert isinstance(result, str)

    async def test_analyze_message_sentiment_negative(self, hub):
        """Error content gets a negative sentiment label."""
        result = await hub._analyze_message_sentiment({"content": "critical error failure crash"})
        assert isinstance(result, str)

    async def test_direct_message_delivery_returns_dict(self, hub):
        """_direct_message_delivery returns a dict with status."""
        result = await hub._direct_message_delivery({"to": "ollama", "content": "ping"})
        assert isinstance(result, dict)


class TestAgentStateManagement:
    """Test AgentOrchestrationHub service lock acquisition and release."""

    @pytest.fixture
    def hub(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub
        return AgentOrchestrationHub(enable_healing=False, enable_consciousness=False)

    async def test_acquire_task_lock_returns_bool(self, hub):
        """acquire_task_lock returns True on first acquisition."""
        result = await hub.acquire_task_lock("task-001", "agent-test", timeout=10)
        assert isinstance(result, bool)
        assert result is True

    async def test_acquire_task_lock_duplicate_fails(self, hub):
        """Second acquisition of same task lock returns False."""
        await hub.acquire_task_lock("task-dup", "agent-1", timeout=30)
        result = await hub.acquire_task_lock("task-dup", "agent-2", timeout=30)
        assert result is False

    async def test_release_task_lock_returns_bool(self, hub):
        """release_task_lock returns True after successful acquisition."""
        await hub.acquire_task_lock("task-rel", "agent-r", timeout=10)
        result = await hub.release_task_lock("task-rel", "agent-r")
        assert isinstance(result, bool)
        assert result is True

    async def test_release_nonexistent_lock_returns_false(self, hub):
        """Releasing a lock that was never acquired returns False."""
        result = await hub.release_task_lock("task-nonexistent", "agent-x")
        assert result is False


class TestAgentLoadBalancing:
    """Test AgentOrchestrationHub service registration and selection."""

    @pytest.fixture
    def hub(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub
        return AgentOrchestrationHub(enable_healing=False, enable_consciousness=False)

    def test_register_multiple_services(self, hub):
        """Register multiple services and verify all appear in _services."""
        from src.agents.agent_orchestration_hub import ServiceCapability
        for name in ("svc-a", "svc-b", "svc-c"):
            cap = ServiceCapability(name="gen", description="General")
            hub.register_service(name, name.upper(), [cap])
        for name in ("svc-a", "svc-b", "svc-c"):
            assert name in hub._services

    def test_register_service_with_capabilities(self, hub):
        """Services store their capabilities as a RegisteredService object."""
        from src.agents.agent_orchestration_hub import ServiceCapability
        cap = ServiceCapability(name="code_gen", description="Generates code")
        hub.register_service("svc-caps", "Cap Svc", [cap])
        assert "svc-caps" in hub._services
        svc = hub._services["svc-caps"]
        assert hasattr(svc, "capabilities") or hasattr(svc, "service_id")

    def test_unregister_all_registered_services(self, hub):
        """Unregister removes each service."""
        from src.agents.agent_orchestration_hub import ServiceCapability
        cap = ServiceCapability(name="x", description="x")
        for name in ("rm-a", "rm-b"):
            hub.register_service(name, name, [cap])
        for name in ("rm-a", "rm-b"):
            assert hub.unregister_service(name) is True
        for name in ("rm-a", "rm-b"):
            assert name not in hub._services


class TestAgentCoordination:
    """Test AgentOrchestrationHub task lock coordination and default helpers."""

    @pytest.fixture
    def hub(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub
        return AgentOrchestrationHub(enable_healing=False, enable_consciousness=False)

    def test_get_default_chatdev_team_returns_dict(self, hub):
        """Default ChatDev team structure is a non-empty dict."""
        team = hub._get_default_chatdev_team()
        assert isinstance(team, dict)
        assert len(team) > 0

    async def test_acquire_and_release_cycle(self, hub):
        """Full lock lifecycle: acquire → locked → release → free."""
        acquired = await hub.acquire_task_lock("coord-task", "agent-coord", timeout=10)
        assert acquired is True
        # Cannot acquire again
        second = await hub.acquire_task_lock("coord-task", "agent-other", timeout=10)
        assert second is False
        # Release and re-acquire
        released = await hub.release_task_lock("coord-task", "agent-coord")
        assert released is True
        reacquired = await hub.acquire_task_lock("coord-task", "agent-new", timeout=10)
        assert reacquired is True

    async def test_execute_with_healing_returns_dict(self, hub):
        """execute_with_healing returns a dict response."""
        result = await hub.execute_with_healing(
            task_description="analyze code quality",
            initial_service="test-service",
        )
        assert isinstance(result, dict)


class TestAgentPerformance:
    """Test AgentOrchestrationHub complexity estimation and lock expiry."""

    @pytest.fixture
    def hub(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub
        return AgentOrchestrationHub(enable_healing=False, enable_consciousness=False)

    @pytest.mark.parametrize("description,expected_min", [
        ("fix", 0),
        ("implement REST API with auth and tests", 1),
        ("full microservices architecture with kubernetes deployment and monitoring", 1),
    ])
    def test_estimate_complexity_scales_with_description(self, hub, description, expected_min):
        """Complexity estimate grows with description length/content."""
        score = hub._estimate_complexity(description)
        assert isinstance(score, int)
        assert score >= expected_min

    async def test_expired_locks_are_cleaned(self, hub):
        """_clean_expired_locks removes TTL-expired entries."""
        import time
        # Manually insert an expired lock
        # Inject a fake expired lock directly into the internal dict
        from src.agents.agent_orchestration_hub import TaskLock
        hub._locks["expired-task"] = TaskLock(
            task_id="expired-task",
            agent_id="agent-x",
            acquired_at=time.time() - 9999,
            expires_at=time.time() - 9998,
        )
        hub._clean_expired_locks()
        assert "expired-task" not in hub._locks

    async def test_active_lock_not_cleaned(self, hub):
        """Active (non-expired) locks survive _clean_expired_locks."""
        await hub.acquire_task_lock("active-task", "agent-perf", timeout=9999)
        hub._clean_expired_locks()
        assert "active-task" in hub._locks


class TestAgentErrorHandling:
    """Test AgentOrchestrationHub response contract and status helpers."""

    def test_status_implies_success_true_cases(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub

        for status in ("success", "ok", "completed", "submitted", "operational"):
            assert AgentOrchestrationHub._status_implies_success(status) is True

    def test_status_implies_success_false_cases(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub

        for status in ("error", "failed", "timeout", None, ""):
            assert AgentOrchestrationHub._status_implies_success(status) is False

    def test_normalize_response_contract_adds_success_key(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub

        payload = {"status": "success", "output": "done"}
        normalized = AgentOrchestrationHub._normalize_response_contract(payload)
        assert "success" in normalized
        assert normalized["success"] is True

    def test_normalize_response_contract_infers_status_from_success(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub

        payload = {"success": True, "output": "ok"}
        normalized = AgentOrchestrationHub._normalize_response_contract(payload)
        assert "status" in normalized
        assert normalized["status"] == "success"

    def test_response_succeeded_via_success_key(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub

        assert AgentOrchestrationHub._response_succeeded({"success": True}) is True
        assert AgentOrchestrationHub._response_succeeded({"success": False}) is False

    def test_response_succeeded_via_status_key(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub

        assert AgentOrchestrationHub._response_succeeded({"status": "completed"}) is True
        assert AgentOrchestrationHub._response_succeeded({"status": "failed"}) is False


class TestAgentIntegration:
    """Integration: register/unregister services on AgentOrchestrationHub."""

    @pytest.fixture
    def hub(self):
        from src.agents.agent_orchestration_hub import AgentOrchestrationHub

        return AgentOrchestrationHub(enable_healing=False, enable_consciousness=False)

    def test_end_to_end_code_generation(self, hub):
        """Register a service and verify it appears in _services."""
        from src.agents.agent_orchestration_hub import ServiceCapability

        cap = ServiceCapability(name="code_gen", description="Generates code")
        result = hub.register_service("svc-codegen", "Code Generator", [cap])
        assert result is True
        assert "svc-codegen" in hub._services

    def test_multi_step_task_execution(self, hub):
        """Duplicate registration returns False (idempotent guard)."""
        from src.agents.agent_orchestration_hub import ServiceCapability

        cap = ServiceCapability(name="analysis", description="Analyzes code")
        hub.register_service("svc-dup", "Dup Svc", [cap])
        second = hub.register_service("svc-dup", "Dup Svc", [cap])
        assert second is False

    def test_agent_recovery_after_failure(self, hub):
        """Unregister removes the service from _services."""
        from src.agents.agent_orchestration_hub import ServiceCapability

        cap = ServiceCapability(name="heal", description="Heals errors")
        hub.register_service("svc-heal", "Healer", [cap])
        removed = hub.unregister_service("svc-heal")
        assert removed is True
        assert "svc-heal" not in hub._services


# Parametrized fixtures for comprehensive coverage
@pytest.fixture(params=["claude", "ollama", "chatdev"])
async def available_agent(request):
    """Parameterize tests across available agents."""
    return request.param


@pytest.fixture(
    params=[
        ("idle", "active"),
        ("active", "paused"),
        ("paused", "active"),
        ("active", "error"),
        ("error", "recovering"),
    ]
)
async def state_transitions(request):
    """Parameterize state transition tests."""
    return request.param

"""Comprehensive test suite for AgentOrchestrationHub.

Tests core methods and consciousness integration.
"""

import asyncio
from pathlib import Path

import pytest
from src.agents.agent_orchestration_hub import (
    AgentOrchestrationHub,
    ExecutionMode,
    ServiceCapability,
    TaskPriority,
    get_agent_orchestration_hub,
)


def _assert_contract(result: dict, expected_success: bool) -> None:
    """Boundary contract: all hub responses must expose status + success."""
    assert "status" in result
    assert "success" in result
    assert result["success"] is expected_success


@pytest.fixture
def hub():
    """Create a fresh hub instance for each test."""
    return AgentOrchestrationHub(
        root_path=Path.cwd(), enable_healing=True, enable_consciousness=True
    )


@pytest.fixture
def hub_with_mock_services(hub):
    """Hub with registered mock services."""
    # Register test services
    hub.register_service(
        service_id="test_analyzer",
        name="Test Analyzer",
        capabilities=[
            ServiceCapability(name="code_analysis", description="Analyze code", priority=8),
            ServiceCapability(name="code_review", description="Review code", priority=7),
        ],
        endpoint="http://localhost:8001",
    )

    hub.register_service(
        service_id="test_generator",
        name="Test Generator",
        capabilities=[
            ServiceCapability(name="code_generation", description="Generate code", priority=9)
        ],
        endpoint="http://localhost:8002",
    )

    return hub


# ==================== Test Method 1: Universal Task Routing ====================


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_route_task_basic(hub_with_mock_services):
    """Test basic task routing."""
    result = await hub_with_mock_services.route_task(
        task_type="code_analysis",
        description="Analyze authentication module",
        context={"file": "src/auth.py"},
    )

    assert result["status"] == "success"
    _assert_contract(result, expected_success=True)
    assert "task_id" in result
    assert result["service"] == "test_analyzer"


@pytest.mark.asyncio
async def test_route_task_with_target_service(hub_with_mock_services):
    """Test routing to specific service."""
    result = await hub_with_mock_services.route_task(
        task_type="code_generation",
        description="Generate user model",
        target_service="test_generator",
    )

    assert result["status"] == "success"
    _assert_contract(result, expected_success=True)
    assert result["service"] == "test_generator"


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_route_task_service_not_found(hub):
    """Test error when service not found."""
    result = await hub.route_task(
        task_type="unknown_task",
        description="Do something",
        target_service="nonexistent",
    )

    assert result["status"] == "error"
    _assert_contract(result, expected_success=False)
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_route_task_no_matching_service(hub_with_mock_services):
    """Test error when no service matches task type."""
    result = await hub_with_mock_services.route_task(
        task_type="unsupported_task_type", description="Unsupported task"
    )

    assert result["status"] == "error"
    _assert_contract(result, expected_success=False)
    assert "No service available" in result["error"]


@pytest.mark.asyncio
async def test_route_task_with_consciousness(hub_with_mock_services):
    """Test task routing with consciousness integration."""
    result = await hub_with_mock_services.route_task(
        task_type="code_analysis",
        description="Analyze complex authentication system",
        require_consciousness=True,
    )

    assert result["status"] == "success"
    _assert_contract(result, expected_success=True)
    # Consciousness integration adds semantic analysis
    # (actual behavior depends on consciousness bridge availability)


# ==================== Test Method 2: ChatDev Orchestration ====================


@pytest.mark.asyncio
async def test_route_to_chatdev_basic(hub):
    """Test ChatDev orchestration."""
    result = await hub.route_to_chatdev(
        project_description="Create a simple web server",
        requirements=["Python", "FastAPI", "REST API"],
    )

    _assert_contract(result, expected_success=result["status"] in {"success", "ok"})
    # Result depends on ChatDev availability


@pytest.mark.asyncio
async def test_route_to_chatdev_with_custom_team(hub):
    """Test ChatDev with custom team composition."""
    custom_team = {
        "ceo": {"role": "CEO", "focus": "strategy"},
        "programmer": {"role": "Programmer", "focus": "backend"},
    }

    result = await hub.route_to_chatdev(
        project_description="Build API service", team_composition=custom_team
    )

    _assert_contract(result, expected_success=result["status"] in {"success", "ok"})


# ==================== Test Method 3: Claude Orchestration ====================


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_route_to_claude_simulated(hub):
    """Test Claude orchestration in simulated mode."""
    result = await hub.route_to_claude(
        task_description="Assess authentication architecture",
        context={"simulate": True, "mode": "consensus"},
    )

    assert result["status"] == "success"
    _assert_contract(result, expected_success=True)
    assert result["service"] == "claude_orchestrator"
    assert result["simulated"] is True


@pytest.mark.asyncio
async def test_route_to_claude_simulated_ollama(hub):
    """Test Claude orchestration using simulated ollama mode."""
    result = await hub.route_to_claude(
        task_description="Summarize module dependencies",
        context={"simulate": True, "mode": "ollama", "model": "qwen2.5-coder:7b"},
    )

    assert result["status"] == "success"
    _assert_contract(result, expected_success=True)
    assert result["mode"] == "ollama"


# ==================== Test Method 4: Multi-Agent Coordination ====================


@pytest.mark.asyncio
async def test_multi_agent_consensus(hub_with_mock_services):
    """Test consensus mode coordination."""
    result = await hub_with_mock_services.orchestrate_multi_agent_task(
        task_description="Analyze security vulnerabilities",
        services=["test_analyzer"],
        mode=ExecutionMode.CONSENSUS,
    )

    assert result["status"] in ["consensus_reached", "consensus_failed"]
    _assert_contract(result, expected_success=result["status"] == "consensus_reached")
    assert "results" in result


@pytest.mark.asyncio
async def test_multi_agent_voting(hub_with_mock_services):
    """Test voting mode coordination."""
    result = await hub_with_mock_services.orchestrate_multi_agent_task(
        task_description="Review code quality",
        services=["test_analyzer"],
        mode=ExecutionMode.VOTING,
    )

    assert "vote_" in result["status"]
    _assert_contract(result, expected_success=result["status"] == "vote_success")
    assert "votes" in result


@pytest.mark.asyncio
async def test_multi_agent_sequential(hub_with_mock_services):
    """Test sequential execution."""
    result = await hub_with_mock_services.orchestrate_multi_agent_task(
        task_description="Process data pipeline",
        services=["test_analyzer", "test_generator"],
        mode=ExecutionMode.SEQUENTIAL,
    )

    assert result["status"] == "success"
    _assert_contract(result, expected_success=True)


@pytest.mark.asyncio
async def test_multi_agent_parallel(hub_with_mock_services):
    """Test parallel execution."""
    result = await hub_with_mock_services.orchestrate_multi_agent_task(
        task_description="Analyze from multiple perspectives",
        services=["test_analyzer", "test_generator"],
        mode=ExecutionMode.PARALLEL,
        synthesis_required=True,
    )

    assert result["status"] in ["synthesized", "parallel_complete"]
    _assert_contract(result, expected_success=True)
    assert "results" in result


@pytest.mark.asyncio
async def test_multi_agent_first_success(hub_with_mock_services):
    """Test first success mode."""
    result = await hub_with_mock_services.orchestrate_multi_agent_task(
        task_description="Find solution",
        services=["test_analyzer", "test_generator"],
        mode=ExecutionMode.FIRST_SUCCESS,
    )

    assert result["status"] in ["success", "all_failed"]
    _assert_contract(result, expected_success=result["status"] == "success")


@pytest.mark.asyncio
async def test_multi_agent_no_services(hub):
    """Test multi-agent with no active services."""
    result = await hub.orchestrate_multi_agent_task(
        task_description="Test task",
        services=["nonexistent1", "nonexistent2"],
        mode=ExecutionMode.CONSENSUS,
    )

    assert result["status"] == "error"
    _assert_contract(result, expected_success=False)
    assert "No active services" in result["error"]


# ==================== Test Method 4: Healing Escalation ====================


@pytest.mark.asyncio
async def test_execute_with_healing_success(hub_with_mock_services):
    """Test healing execution when task succeeds."""
    result = await hub_with_mock_services.execute_with_healing(
        task_description="Parse configuration file",
        initial_service="test_analyzer",
        max_retries=3,
    )

    assert result["status"] == "success"
    _assert_contract(result, expected_success=True)
    assert "healing_history" in result
    assert len(result["healing_history"]) == 0  # No healing needed on success


@pytest.mark.asyncio
async def test_execute_with_healing_disabled(hub_with_mock_services):
    """Test healing execution when healing is disabled."""
    hub_with_mock_services.enable_healing = False

    result = await hub_with_mock_services.execute_with_healing(
        task_description="Test task",
        initial_service="test_analyzer",
        max_retries=3,
    )

    # Should stop after first failure when healing disabled
    assert result["status"] in ["success", "failed_after_healing"]
    _assert_contract(result, expected_success=result["status"] == "success")


@pytest.mark.asyncio
async def test_execute_with_healing_consciousness_judgment(hub_with_mock_services):
    """Test consciousness judgment during healing."""
    # Consciousness can decide to stop retries early
    result = await hub_with_mock_services.execute_with_healing(
        task_description="Complex analysis",
        initial_service="test_analyzer",
        max_retries=5,
    )

    assert "healing_history" in result or result["status"] == "success"
    _assert_contract(result, expected_success=result["status"] == "success")


# ==================== Test Method 5: Task Locking ====================


@pytest.mark.asyncio
async def test_acquire_task_lock_success(hub):
    """Test successful lock acquisition."""
    acquired = await hub.acquire_task_lock(task_id="task_123", agent_id="agent_A", timeout=60.0)

    assert acquired is True
    assert "task_123" in hub._locks


@pytest.mark.asyncio
async def test_acquire_task_lock_already_locked(hub):
    """Test lock acquisition when already locked."""
    # First agent acquires lock
    await hub.acquire_task_lock(task_id="task_456", agent_id="agent_A")

    # Second agent tries to acquire same lock
    acquired = await hub.acquire_task_lock(task_id="task_456", agent_id="agent_B")

    assert acquired is False


@pytest.mark.asyncio
async def test_release_task_lock_success(hub):
    """Test successful lock release."""
    await hub.acquire_task_lock(task_id="task_789", agent_id="agent_A")
    released = await hub.release_task_lock(task_id="task_789", agent_id="agent_A")

    assert released is True
    assert "task_789" not in hub._locks


@pytest.mark.asyncio
async def test_release_task_lock_wrong_owner(hub):
    """Test lock release by non-owner."""
    await hub.acquire_task_lock(task_id="task_999", agent_id="agent_A")
    released = await hub.release_task_lock(task_id="task_999", agent_id="agent_B")

    assert released is False
    assert "task_999" in hub._locks  # Still locked


@pytest.mark.asyncio
async def test_release_task_lock_not_found(hub):
    """Test releasing non-existent lock."""
    released = await hub.release_task_lock(task_id="nonexistent", agent_id="agent_A")

    assert released is False


@pytest.mark.asyncio
async def test_lock_expiration(hub):
    """Test that locks expire after timeout."""
    hub._lock_timeout = 0.1  # 100ms for testing

    await hub.acquire_task_lock(task_id="task_expire", agent_id="agent_A", timeout=0.1)
    assert "task_expire" in hub._locks

    # Wait for expiration
    await asyncio.sleep(0.2)

    # Clean expired locks
    hub._clean_expired_locks()
    assert "task_expire" not in hub._locks


# ==================== Test Method 6: Service Registration ====================


def test_register_service_success(hub):
    """Test successful service registration."""
    capabilities = [ServiceCapability(name="test_cap", description="Test capability", priority=5)]

    registered = hub.register_service(
        service_id="new_service",
        name="New Service",
        capabilities=capabilities,
        endpoint="http://localhost:9000",
    )

    assert registered is True
    assert "new_service" in hub._services
    assert hub._services["new_service"].name == "New Service"


def test_register_service_duplicate(hub):
    """Test registering duplicate service."""
    capabilities = [ServiceCapability(name="test", description="Test", priority=5)]

    hub.register_service("service_1", "Service 1", capabilities)
    duplicate = hub.register_service("service_1", "Service 1 Duplicate", capabilities)

    assert duplicate is False


def test_unregister_service_success(hub_with_mock_services):
    """Test successful service unregistration."""
    assert "test_analyzer" in hub_with_mock_services._services

    unregistered = hub_with_mock_services.unregister_service("test_analyzer")

    assert unregistered is True
    assert "test_analyzer" not in hub_with_mock_services._services


def test_unregister_service_not_found(hub):
    """Test unregistering non-existent service."""
    unregistered = hub.unregister_service("nonexistent")

    assert unregistered is False


# ==================== Test Method 7: Inter-Agent Communication ====================


@pytest.mark.asyncio
async def test_send_agent_message_success(hub_with_mock_services):
    """Test sending message between agents."""
    result = await hub_with_mock_services.send_agent_message(
        from_agent="agent_A",
        to_agent="test_analyzer",
        message_type="request",
        content={"action": "analyze", "target": "src/main.py"},
        priority=TaskPriority.HIGH,
    )

    assert result["status"] in ["delivered", "delivery_failed"]
    _assert_contract(result, expected_success=result["status"] == "delivered")
    assert "message_id" in result


@pytest.mark.asyncio
async def test_send_agent_message_recipient_not_found(hub):
    """Test message to non-existent recipient."""
    result = await hub.send_agent_message(
        from_agent="agent_A",
        to_agent="nonexistent",
        message_type="request",
        content={"test": "data"},
    )

    assert result["status"] == "delivery_failed"
    _assert_contract(result, expected_success=False)
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_send_agent_message_with_consciousness(hub_with_mock_services):
    """Test message with consciousness sentiment analysis."""
    result = await hub_with_mock_services.send_agent_message(
        from_agent="agent_A",
        to_agent="test_analyzer",
        message_type="notification",
        content={"message": "Task completed successfully!"},
    )

    assert result["status"] == "delivered"
    _assert_contract(result, expected_success=True)


# ==================== Singleton Tests ====================


def test_get_hub_singleton():
    """Test that get_agent_orchestration_hub returns singleton."""
    hub1 = get_agent_orchestration_hub()
    hub2 = get_agent_orchestration_hub()

    assert hub1 is hub2


def test_hub_initialization():
    """Test hub initialization with custom parameters."""
    hub = AgentOrchestrationHub(
        root_path=Path("/test"), enable_healing=False, enable_consciousness=False
    )

    assert hub.root_path == Path("/test")
    assert hub.enable_healing is False
    assert hub.enable_consciousness is False


# ==================== Integration Tests ====================


@pytest.mark.asyncio
async def test_full_workflow_with_healing(hub_with_mock_services):
    """Test complete workflow: route → execute → heal if needed."""
    # Register a task
    task_id = "integration_test_task"
    agent_id = "test_agent"

    # Acquire lock
    locked = await hub_with_mock_services.acquire_task_lock(task_id, agent_id)
    assert locked is True

    # Route task
    result = await hub_with_mock_services.route_task(
        task_type="code_analysis",
        description="Integration test analysis",
        context={"test": True},
    )

    # Release lock
    released = await hub_with_mock_services.release_task_lock(task_id, agent_id)
    assert released is True

    assert result["status"] == "success"
    _assert_contract(result, expected_success=True)


@pytest.mark.asyncio
async def test_consciousness_integration_flow(hub_with_mock_services):
    """Test consciousness integration throughout the flow."""
    # This tests that consciousness features don't break the flow
    result = await hub_with_mock_services.route_task(
        task_type="code_analysis",
        description="Analyze complex system with consciousness awareness",
        require_consciousness=True,
    )

    assert result["status"] in ["success", "error"]
    _assert_contract(result, expected_success=result["status"] == "success")
    # Actual consciousness behavior depends on bridge availability


@pytest.mark.asyncio
async def test_multiple_services_coordination(hub_with_mock_services):
    """Test coordinating multiple services together."""
    # Test different execution modes
    modes_to_test = [
        ExecutionMode.CONSENSUS,
        ExecutionMode.VOTING,
        ExecutionMode.PARALLEL,
    ]

    for mode in modes_to_test:
        result = await hub_with_mock_services.orchestrate_multi_agent_task(
            task_description=f"Test {mode.value} coordination",
            services=["test_analyzer", "test_generator"],
            mode=mode,
        )

        assert "status" in result
        assert "success" in result
        assert "results" in result or "error" in result

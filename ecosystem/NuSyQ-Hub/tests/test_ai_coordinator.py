"""
Tests for AICoordinator — routing logic, fallback chains, performance metrics.
All external provider calls are mocked; no network/Ollama/OpenAI required.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def patch_imports(monkeypatch):
    """Patch heavy external deps before the coordinator module loads."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake")
    fake_secrets = MagicMock()
    fake_secrets._secrets_cache = {}
    fake_secrets.get_config = MagicMock(return_value="http://localhost:11435")
    with patch("src.ai.ai_coordinator.SecretsManager", return_value=fake_secrets), \
         patch("src.ai.ai_coordinator.KILOOllamaIntegration", MagicMock()), \
         patch("src.ai.ai_coordinator.get_ollama_instance", MagicMock()):
        yield


@pytest.fixture
def coordinator():
    from src.ai.ai_coordinator import AICoordinator, OllamaProvider, OpenAIProvider, CopilotProvider, AIProvider
    coord = AICoordinator.__new__(AICoordinator)
    coord.task_history = []
    coord.performance_metrics = {}
    coord.providers = {
        AIProvider.OLLAMA: MagicMock(spec=OllamaProvider),
        AIProvider.OPENAI: MagicMock(spec=OpenAIProvider),
        AIProvider.COPILOT: MagicMock(spec=CopilotProvider),
    }
    for p in coord.providers.values():
        p.is_available.return_value = False
        p.get_capabilities.return_value = []
        p.estimate_cost.return_value = 0.0
    return coord


@pytest.fixture
def task_request():
    from src.ai.ai_coordinator import TaskRequest, TaskType, AIProvider, Priority
    return TaskRequest(
        content="Write a hello world function",
        task_type=TaskType.CODE_GENERATION,
        preferred_provider=AIProvider.AUTO,
        priority=Priority.MEDIUM,
        requires_privacy=False,
        context={},
    )


@pytest.fixture
def task_response_ok():
    from src.ai.ai_coordinator import TaskResponse, AIProvider
    return TaskResponse(
        content="def hello(): return 'world'",
        provider=AIProvider.OLLAMA,
        confidence=0.9,
        execution_time=0.5,
        error=None,
    )


@pytest.fixture
def task_response_error():
    from src.ai.ai_coordinator import TaskResponse, AIProvider
    return TaskResponse(
        content="",
        provider=AIProvider.OLLAMA,
        confidence=0.0,
        execution_time=0.1,
        error="Connection refused",
    )


# ── TaskType / AIProvider enums ───────────────────────────────────────────────

def test_task_type_enum_has_core_values():
    from src.ai.ai_coordinator import TaskType
    assert TaskType.CODE_GENERATION.value == "code_generation"
    assert TaskType.DEBUGGING.value == "debugging"
    assert TaskType.SECURITY_REVIEW.value == "security_review"


def test_ai_provider_enum_has_all_providers():
    from src.ai.ai_coordinator import AIProvider
    assert AIProvider.OLLAMA in AIProvider
    assert AIProvider.OPENAI in AIProvider
    assert AIProvider.COPILOT in AIProvider
    assert AIProvider.AUTO in AIProvider


# ── Provider selection ────────────────────────────────────────────────────────

def test_select_provider_privacy_prefers_ollama(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider
    task_request.requires_privacy = True
    coordinator.providers[AIProvider.OLLAMA].is_available.return_value = True
    result = coordinator._select_optimal_provider(task_request)
    assert result == AIProvider.OLLAMA


def test_select_provider_privacy_falls_back_to_copilot_when_ollama_down(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider
    task_request.requires_privacy = True
    coordinator.providers[AIProvider.OLLAMA].is_available.return_value = False
    result = coordinator._select_optimal_provider(task_request)
    assert result == AIProvider.COPILOT


def test_select_provider_critical_priority_prefers_openai(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider, Priority
    task_request.priority = Priority.CRITICAL
    coordinator.providers[AIProvider.OPENAI].is_available.return_value = True
    result = coordinator._select_optimal_provider(task_request)
    assert result == AIProvider.OPENAI


def test_select_provider_critical_falls_back_to_ollama(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider, Priority
    task_request.priority = Priority.CRITICAL
    coordinator.providers[AIProvider.OPENAI].is_available.return_value = False
    coordinator.providers[AIProvider.OLLAMA].is_available.return_value = True
    result = coordinator._select_optimal_provider(task_request)
    assert result == AIProvider.OLLAMA


def test_select_provider_code_generation_prefers_copilot(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider, TaskType
    task_request.task_type = TaskType.CODE_GENERATION
    coordinator.providers[AIProvider.COPILOT].is_available.return_value = True
    result = coordinator._select_optimal_provider(task_request)
    assert result == AIProvider.COPILOT


def test_select_provider_planning_prefers_openai(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider, TaskType
    task_request.task_type = TaskType.PLANNING
    coordinator.providers[AIProvider.OPENAI].is_available.return_value = True
    result = coordinator._select_optimal_provider(task_request)
    assert result == AIProvider.OPENAI


def test_select_provider_all_unavailable_falls_back_to_copilot(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider
    result = coordinator._select_optimal_provider(task_request)
    assert result == AIProvider.COPILOT


# ── Fallback chain ────────────────────────────────────────────────────────────

def test_fallback_openai_to_ollama(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider
    coordinator.providers[AIProvider.OLLAMA].is_available.return_value = True
    result = coordinator._get_fallback_provider(AIProvider.OPENAI, task_request)
    assert result == AIProvider.OLLAMA


def test_fallback_ollama_to_copilot(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider
    coordinator.providers[AIProvider.COPILOT].is_available.return_value = True
    result = coordinator._get_fallback_provider(AIProvider.OLLAMA, task_request)
    assert result == AIProvider.COPILOT


def test_fallback_copilot_returns_none(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider
    result = coordinator._get_fallback_provider(AIProvider.COPILOT, task_request)
    assert result is None


def test_fallback_unavailable_returns_none(coordinator, task_request):
    from src.ai.ai_coordinator import AIProvider
    coordinator.providers[AIProvider.OLLAMA].is_available.return_value = False
    result = coordinator._get_fallback_provider(AIProvider.OPENAI, task_request)
    assert result is None


# ── Performance metrics ───────────────────────────────────────────────────────

def test_record_performance_increments_total(coordinator, task_request, task_response_ok):
    coordinator._record_performance(task_request, task_response_ok)
    key_p = task_response_ok.provider.value
    key_t = task_request.task_type.value
    assert coordinator.performance_metrics[key_p][key_t]["total_requests"] == 1
    assert coordinator.performance_metrics[key_p][key_t]["successful_requests"] == 1


def test_record_performance_error_not_counted_as_success(coordinator, task_request, task_response_error):
    coordinator._record_performance(task_request, task_response_error)
    key_p = task_response_error.provider.value
    key_t = task_request.task_type.value
    assert coordinator.performance_metrics[key_p][key_t]["total_requests"] == 1
    assert coordinator.performance_metrics[key_p][key_t]["successful_requests"] == 0


def test_task_history_capped_at_100(coordinator, task_request, task_response_ok):
    for _ in range(105):
        coordinator._record_performance(task_request, task_response_ok)
    assert len(coordinator.task_history) == 100


# ── System status ─────────────────────────────────────────────────────────────

def test_get_system_status_structure(coordinator):
    from src.ai.ai_coordinator import AIProvider
    coordinator.providers[AIProvider.OLLAMA].is_available.return_value = True
    coordinator.providers[AIProvider.OLLAMA].get_capabilities.return_value = []
    status = coordinator.get_system_status()
    assert "providers" in status
    assert "performance" in status
    assert "recent_tasks" in status
    assert "ollama" in status["providers"]


def test_get_system_status_reflects_availability(coordinator):
    from src.ai.ai_coordinator import AIProvider
    coordinator.providers[AIProvider.OLLAMA].is_available.return_value = True
    coordinator.providers[AIProvider.OPENAI].is_available.return_value = False
    status = coordinator.get_system_status()
    assert status["providers"]["ollama"]["available"] is True
    assert status["providers"]["openai"]["available"] is False


# ── Health check ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check_true_when_one_provider_available(coordinator):
    from src.ai.ai_coordinator import AIProvider
    coordinator.providers[AIProvider.COPILOT].is_available.return_value = True
    assert await coordinator.health_check() is True


@pytest.mark.asyncio
async def test_health_check_false_when_all_unavailable(coordinator):
    assert await coordinator.health_check() is False


# ── process_request routing ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_request_uses_selected_provider(coordinator, task_request, task_response_ok):
    from src.ai.ai_coordinator import AIProvider
    coordinator.providers[AIProvider.COPILOT].is_available.return_value = True
    coordinator.providers[AIProvider.COPILOT].process_task = AsyncMock(return_value=task_response_ok)
    response = await coordinator.process_request(task_request)
    assert response.content == task_response_ok.content
    coordinator.providers[AIProvider.COPILOT].process_task.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_request_triggers_fallback_on_error(coordinator, task_request, task_response_error, task_response_ok):
    from src.ai.ai_coordinator import AIProvider
    task_request.preferred_provider = AIProvider.OLLAMA
    coordinator.providers[AIProvider.OLLAMA].process_task = AsyncMock(return_value=task_response_error)
    coordinator.providers[AIProvider.COPILOT].is_available.return_value = True
    coordinator.providers[AIProvider.COPILOT].process_task = AsyncMock(return_value=task_response_ok)
    response = await coordinator.process_request(task_request)
    coordinator.providers[AIProvider.COPILOT].process_task.assert_awaited_once()

import pytest
from src.ai.ai_coordinator import AICoordinator


@pytest.fixture
def coordinator():
    return AICoordinator()


def test_coordinator_initialization(coordinator):
    assert isinstance(coordinator, AICoordinator)
    assert coordinator.providers == {}


def test_provider_registration(coordinator):
    provider_name = "Provider1"
    capabilities = {"type": "NLP", "priority": 2}
    coordinator.register_provider(provider_name, capabilities)

    assert provider_name in coordinator.providers
    assert coordinator.providers[provider_name] == capabilities


def test_task_routing_to_appropriate_provider(coordinator):
    coordinator.register_provider("Provider1", {"type": "NLP", "priority": 2})
    coordinator.register_provider("Provider2", {"type": "Vision", "priority": 1})

    task_type = "NLP"
    content = "Analyze this text."
    priority = 3
    provider_name, assigned_task = coordinator.route_task((task_type, content, priority))

    assert provider_name == "Provider1"
    assert assigned_task == (task_type, content, priority)


def test_error_handling_for_missing_provider(coordinator):
    with pytest.raises(Exception) as exc_info:
        task_type = "NLP"
        content = "Analyze this text."
        priority = 3
        coordinator.route_task((task_type, content, priority))

    assert str(exc_info.value) == "No provider available for the given task type."


def test_priority_queue_behavior(coordinator):
    coordinator.register_provider("Provider1", {"type": "NLP", "priority": 2})
    coordinator.register_provider("Provider2", {"type": "Vision", "priority": 1})

    # Higher priority task should be routed to Provider1
    higher_priority_task = ("NLP", "Analyze this text.", 3)
    provider_name, assigned_task = coordinator.route_task(higher_priority_task)

    assert provider_name == "Provider1"
    assert assigned_task == higher_priority_task

    # Lower priority task should be routed to Provider2
    lower_priority_task = ("Vision", "Recognize objects in the image.", 1)
    provider_name, assigned_task = coordinator.route_task(lower_priority_task)

    assert provider_name == "Provider2"
    assert assigned_task == lower_priority_task

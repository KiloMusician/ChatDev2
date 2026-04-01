"""Tests for agent_orchestration_types."""

import time

from src.agents.agent_orchestration_types import (
    ExecutionMode,
    RegisteredService,
    ServiceCapability,
    TaskLock,
    TaskPriority,
)


def test_taskpriority_values():
    assert TaskPriority.CRITICAL.value == 1
    assert TaskPriority.HIGH.value == 2
    assert TaskPriority.NORMAL.value == 3
    assert TaskPriority.LOW.value == 4
    assert TaskPriority.BACKGROUND.value == 5


def test_executionmode_values():
    assert ExecutionMode.CONSENSUS.value == "consensus"
    assert ExecutionMode.VOTING.value == "voting"
    assert ExecutionMode.SEQUENTIAL.value == "sequential"
    assert ExecutionMode.PARALLEL.value == "parallel"
    assert ExecutionMode.FIRST_SUCCESS.value == "first_success"


def test_tasklock_instantiation():
    now = time.time()
    lock = TaskLock(
        task_id="t-1",
        agent_id="agent-a",
        acquired_at=now,
        expires_at=now + 30.0,
    )
    assert lock.task_id == "t-1"
    assert lock.agent_id == "agent-a"
    assert lock.metadata == {}


def test_servicecapability_instantiation():
    cap = ServiceCapability(name="code_review", description="Reviews code quality")
    assert cap.name == "code_review"
    assert cap.priority == 5
    assert not cap.requires_consciousness


def test_registeredservice_instantiation():
    cap = ServiceCapability(name="analyze", description="Analyzes tasks")
    svc = RegisteredService(
        service_id="svc-1",
        name="Ollama",
        capabilities=[cap],
        endpoint="http://localhost:11434",
    )
    assert svc.service_id == "svc-1"
    assert svc.active is True
    assert len(svc.capabilities) == 1
    assert svc.registered_at > 0

"""Unit tests for src.orchestration.consensus_integrator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ORCHESTRATION_DIR = Path(__file__).resolve().parents[1] / "src" / "orchestration"
if str(ORCHESTRATION_DIR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATION_DIR))

from src.orchestration import consensus_integrator as ci


@pytest.mark.asyncio
async def test_get_agent_responses_returns_stubbed_mapping(tmp_path, monkeypatch):
    monkeypatch.setattr(ci, "PROFILES_FILE", tmp_path / "profiles.json")
    integrator = ci.ConsensusIntegrator()

    responses = await integrator._get_agent_responses(
        task="Investigate module",
        agents=["alpha", "beta"],
        timeout=0.01,
    )
    assert set(responses.keys()) == {"alpha", "beta"}
    assert responses["alpha"].startswith("Response from alpha:")


@pytest.mark.asyncio
async def test_run_consensus_task_calls_save_profiles(tmp_path, monkeypatch):
    monkeypatch.setattr(ci, "PROFILES_FILE", tmp_path / "profiles.json")
    integrator = ci.ConsensusIntegrator()

    called = {"save": False}

    def _save_profiles() -> None:
        called["save"] = True

    monkeypatch.setattr(integrator, "save_profiles", _save_profiles)

    result = await integrator.run_consensus_task(
        task_description="Review this change",
        agents=["agent1", "agent2"],
        task_type="code_review",
    )
    assert called["save"] is True
    assert isinstance(result.selected_response, str)
    assert result.confidence >= 0.0


def test_record_validation_updates_metrics_and_recommendations(tmp_path, monkeypatch):
    monkeypatch.setattr(ci, "PROFILES_FILE", tmp_path / "profiles.json")
    integrator = ci.ConsensusIntegrator()

    integrator.record_validation("agent1", "code_review", True, 10.0, 120)
    integrator.record_validation("agent2", "code_review", False, 20.0, 240)

    metrics = integrator.get_agent_metrics("agent1")
    assert metrics is not None
    assert metrics["total_attempts"] >= 1
    assert metrics["avg_latency"] > 0

    recommendations = integrator.get_recommendations("code_review")
    assert isinstance(recommendations, list)
    assert "agent1" in recommendations or "agent2" in recommendations


def test_load_profiles_restores_saved_agent_data(tmp_path, monkeypatch):
    profiles_file = tmp_path / "agent_profiles.json"
    profiles_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00",
                "agents": [
                    {
                        "agent_name": "persisted_agent",
                        "total_attempts": 4,
                        "successful_votes": 3,
                        "total_latency": 20.0,
                        "total_tokens": 400,
                        "specializations": {"code_review": 2},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ci, "PROFILES_FILE", profiles_file)

    integrator = ci.ConsensusIntegrator()
    metrics = integrator.get_agent_metrics("persisted_agent")

    assert metrics is not None
    assert metrics["total_attempts"] == 4
    assert metrics["accuracy"] == 0.75
    assert metrics["avg_tokens"] == 100
    assert metrics["specializations"].get("code_review") == 2


def test_get_agent_metrics_unknown_agent_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(ci, "PROFILES_FILE", tmp_path / "profiles.json")
    integrator = ci.ConsensusIntegrator()
    assert integrator.get_agent_metrics("does_not_exist") is None

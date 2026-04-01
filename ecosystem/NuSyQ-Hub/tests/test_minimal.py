#!/usr/bin/env python3
"""Minimal test suite for NuSyQ-Hub autonomous integration.

Tests basic functionality without external dependencies.
"""


# OmniTag: {"purpose": "Comprehensive minimal test suite for autonomous integration",
#           "tags": ["Python", "Testing", "Async", "Integration"],
#           "category": "test",
#           "evolution_stage": "v2.0"}
import sys
from pathlib import Path

import pytest

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def test_repo_structure():
    """Test that critical repository structure exists."""
    assert (repo_root / "src").exists(), "src directory must exist"
    assert (repo_root / "src" / "orchestration").exists(), "orchestration directory must exist"
    assert (repo_root / "config").exists(), "config directory must exist"


def test_autonomous_integration_engine_import():
    """Test autonomous integration engine can be imported."""
    from src.orchestration.autonomous_integration_engine import (
        AutonomousIntegrationEngine,
    )

    engine = AutonomousIntegrationEngine()
    assert engine is not None
    assert hasattr(engine, "initialize_systems")
    assert hasattr(engine, "start_autonomous_workflow")


def test_unified_ai_orchestrator_import():
    """Test unified AI orchestrator can be imported."""
    from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

    orchestrator = UnifiedAIOrchestrator()
    assert orchestrator is not None
    assert len(orchestrator.ai_systems) > 0


def test_config_loading():
    """Test configuration system."""
    from src.orchestration.autonomous_integration_engine import (
        AutonomousIntegrationEngine,
    )

    engine = AutonomousIntegrationEngine()
    config = engine.config

    assert config is not None
    assert "repositories" in config
    assert "integration_mode" in config


@pytest.mark.asyncio
async def test_workflow_creation():
    """Test autonomous workflow creation."""
    from src.orchestration.autonomous_integration_engine import (
        AutonomousIntegrationEngine,
    )

    engine = AutonomousIntegrationEngine()
    workflow_id = await engine.start_autonomous_workflow(
        workflow_type="testing", description="Test workflow creation"
    )

    assert workflow_id is not None
    assert workflow_id in engine.active_workflows

    workflow = engine.get_workflow_status(workflow_id)
    assert workflow["type"] == "testing"
    assert workflow["status"] in ["initialized", "completed"]


def test_bootstrap_report_exists():
    """Test that bootstrap report can be generated."""
    report_path = repo_root / "bootstrap_report.json"

    # Report should exist from bootstrap run
    if report_path.exists():
        import json

        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        assert "chatdev_available" in report
        assert "ollama_available" in report
        assert "status" in report

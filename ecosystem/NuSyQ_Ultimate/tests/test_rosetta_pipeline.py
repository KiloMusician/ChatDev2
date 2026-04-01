"""Unit tests for RosettaStone pipeline stages.

Tests RS normalization, OT encoding, routing, evolution suggestions,
and end-to-end pipeline persistence without model calls.

cSpell:ignore nsyq omnitag
"""

import sys
from pathlib import Path

# pylint: disable=wrong-import-position, invalid-name, redefined-outer-name
# Ensure project root on sys.path for imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.agent_router import (  # noqa: E402
    TaskComplexity,
    TaskType,
)
from src.pipeline.rosetta_stone import (  # noqa: E402
    catalyst_evolve,
    nsyq_route,
    ot_encode,
    rs_normalize,
    run_pipeline,
)
from src.telemetry.omnitag import log_event  # noqa: E402


def test_rs_normalize_trims_and_hash():
    """Test RosettaStone normalization trims keys/values and adds hash."""
    payload = {" key ": " value\r\n", "x": 1}
    norm = rs_normalize(payload)
    assert norm["key"] == "value\n"
    assert norm["x"] == 1
    assert "content_hash" in norm and isinstance(norm["content_hash"], str)


def test_ot_encode_basic_attributes():
    """Test OT encoding includes task_preview and attributes."""
    norm = {"a": 1, "content_hash": "h"}
    enc = ot_encode("some task description", norm)
    assert "task_preview" in enc and isinstance(enc["task_preview"], str)
    assert enc["attributes"]["has_hash"] is True


def test_nsyq_route_shape():
    """Test NuSyQ routing returns expected keys."""
    route = nsyq_route(
        "Check routing for a simple bug fix",
        TaskType.BUG_FIX,
        TaskComplexity.SIMPLE,
    )
    assert set(
        ["primary_agent", "alternatives", "coordination", "estimated_cost", "rationale"]
    ).issubset(route.keys())


def test_catalyst_evolve_thresholds():
    """Test catalyst evolution suggests switch at <50% success rate."""
    routing = {"primary_agent": "foo", "alternatives": ["bar", "baz"]}
    good_stats = {"agents": {"foo": {"success_rate": 60.0}}}
    bad_stats = {"agents": {"foo": {"success_rate": 40.0}}}

    keep = catalyst_evolve(routing, good_stats)
    switch = catalyst_evolve(routing, bad_stats)

    assert keep["action"] == "keep"
    assert switch["action"] == "consider_switch"
    assert switch["candidate"] == "bar"


def test_run_pipeline_persists_files(tmp_path, monkeypatch):
    """Test end-to-end pipeline persists all artifacts and gates pass."""
    # Ensure Reports/rosetta writes work even if CWD changes
    monkeypatch.chdir(tmp_path)
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))

    res = run_pipeline(
        "Minimal pipeline run",
        task_type=TaskType.BUG_FIX,
        complexity=TaskComplexity.SIMPLE,
    )

    # Ensure required artifacts and paths exist
    paths = res.persisted_paths
    for key in ["normalized", "encoded", "routing", "evolve", "summary"]:
        assert key in paths
        assert Path(paths[key]).exists()

    # Agent trends export is best-effort; if present, should exist
    if "agent_trends" in paths:
        assert Path(paths["agent_trends"]).exists()

    # Gate should be present and passed
    assert res.gates.get("passed") is True


def test_run_pipeline_gate_verification():
    """Test gate enforcement verifies artifact existence and schema.

    Integration test that verifies ProofGateVerifier is properly wired into
    the RosettaStone pipeline, checking that gate_enforce() validates:
    - Rosetta directory exists
    - Persisted artifacts (normalized, encoded, routing, evolve) exist
    - Gate results include verification_count and evidence

    This ensures the proof system isn't stubbed (always passing) but actually
    verifies real artifacts.
    """
    res = run_pipeline(
        "Gate verification test",
        task_type=TaskType.CODE_GENERATION,
        complexity=TaskComplexity.SIMPLE,
    )

    # Gates should have been evaluated
    gates = res.gates
    assert gates is not None, "Gates should be present in pipeline result"
    assert "passed" in gates, "Gates result should have 'passed' key"
    assert "checks" in gates, (
        "Gates result should have 'checks' key (verification list)"
    )
    assert "verification_count" in gates, "Gates should report verification_count"
    assert "evidence" in gates, "Gates should include verification evidence"
    assert "timestamp" in gates, "Gates should include ISO timestamp"

    # Check counts are sensible
    assert isinstance(gates["checks"], list)
    assert len(gates["checks"]) > 0, "Should have at least one gate check"
    assert gates["verification_count"] == len(gates["checks"])
    assert len(gates["evidence"]) > 0, "Should have evidence for each check"

    # All artifact files should exist (gates verified this)
    paths = res.persisted_paths
    existing_artifacts = 0
    for key, path_str in paths.items():
        if key != "agent_trends_error" and path_str:
            if Path(path_str).exists():
                existing_artifacts += 1

    # At minimum, normalized, encoded, routing, evolve should exist
    # (summary + agent_trends are best-effort)
    assert existing_artifacts >= 4, (
        f"Expected at least 4 core artifacts to exist, found {existing_artifacts}"
    )

    # Log results for trend analysis
    log_event(
        component="test_rosetta_pipeline",
        action="gate_verification",
        payload={
            "passed": gates["passed"],
            "verification_count": gates["verification_count"],
            "checks_passed": sum(1 for c in gates["checks"] if "✓" in c),
        },
        outcome="success" if gates["passed"] else "failure",
    )

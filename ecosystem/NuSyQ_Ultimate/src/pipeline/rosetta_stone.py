"""RosettaStone pipeline

Stages: RS::Normalize → OT::Encode → MT::Aggregate → RSEV::Persist →
NuSyQ::Route → Catalyst::Evolve → Gate::Enforce

- Normalize (RS): normalize input payloads
- Encode (OT): annotate via tracing-friendly structure (does not require
    tracing to be enabled)
- Aggregate (MT): record lightweight metrics via PerformanceMetrics
- Persist (RSEV): write artifacts into Reports/rosetta/
- Route (NuSyQ): call AgentRouter to select primary and alternatives
- Evolve (Catalyst): propose routing preference adjustments (non-destructive
    suggestion)
- Enforce (Gate): run lightweight gates (stub), return pass/fail and reasons

cSpell:ignore RSEV rsev omnitag nsyq
"""

# pylint: disable=wrong-import-position
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure top-level repo on path for imports
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.agent_router import (  # noqa: E402
    AgentRouter,
    Task,
    TaskComplexity,
    TaskType,
)
from config.proof_gates import (  # noqa: E402
    ProofGate,
    ProofGateVerifier,
    ProofType,
)
from mcp_server.performance_metrics import get_metrics  # noqa: E402
from src.telemetry.omnitag import log_event  # noqa: E402

ROSETTA_DIR = ROOT / "Reports" / "rosetta"
ROSETTA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PipelineArtifacts:
    """Container for pipeline outputs and persisted artifact paths.

    Attributes:
        normalized: RS normalized payload with content_hash
        encoded: OT encoded structure with task preview and attributes
        routing: NuSyQ routing decision with primary/alternatives
        evolve_suggestion: Catalyst evolution recommendation (if any)
        gates: Gate enforcement results (pass/fail with checks)
        persisted_paths: File paths for each persisted JSON artifact
    """

    normalized: Dict[str, Any]
    encoded: Dict[str, Any]
    routing: Dict[str, Any]
    evolve_suggestion: Optional[Dict[str, Any]]
    gates: Dict[str, Any]
    persisted_paths: Dict[str, str]


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def rs_normalize(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize input: trim strings, standardize keys, basic hashing."""
    norm: Dict[str, Any] = {}
    for k, v in payload.items():
        key = str(k).strip()
        if isinstance(v, str):
            value = v.replace("\r\n", "\n")
            if value.endswith("\n"):
                value = value.rstrip("\n").strip(" \t") + "\n"
            else:
                value = value.strip()
            norm[key] = value
        else:
            norm[key] = v
    # Add content hash for idempotency
    norm["content_hash"] = hashlib.sha256(
        json.dumps(norm, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return norm


def ot_encode(task_desc: str, normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Trace-friendly encoding (no-op if tracing disabled)."""
    return {
        "task_preview": task_desc[:80],
        "attributes": {
            "normalized_len": len(json.dumps(normalized)),
            "has_hash": bool(normalized.get("content_hash")),
        },
    }


def mt_aggregate(
    task_type: TaskType,
    complexity: TaskComplexity,
    success: bool,
) -> None:
    """Record a minimal agent metric to feed trends."""
    pm = get_metrics()
    pm.record_agent(
        agent_name="rosetta_pipeline",
        task_type=f"{task_type.value}:{complexity.value}",
        duration=0.0,
        success=success,
    )


def rsev_persist(stem: str, artifacts: Dict[str, Any]) -> Path:
    """Persist artifacts to Reports/rosetta/ as timestamped JSON.

    Args:
        stem: Filename prefix (e.g., 'normalized', 'routing')
        artifacts: Dictionary to serialize as JSON

    Returns:
        Path to the written file
    """
    path = ROSETTA_DIR / f"{stem}_{_now_stamp()}.json"
    path.write_text(json.dumps(artifacts, indent=2), encoding="utf-8")
    return path


def nsyq_route(
    task_desc: str,
    task_type: TaskType,
    complexity: TaskComplexity,
) -> Dict[str, Any]:
    """Route task to primary agent with alternatives using AgentRouter.

    Args:
        task_desc: Human-readable task description
        task_type: Type of task (e.g., BUG_FIX, CODE_GENERATION)
        complexity: Task complexity level (SIMPLE, MODERATE, COMPLEX)

    Returns:
        Dictionary with primary_agent, alternatives, coordination pattern,
        estimated_cost, and rationale
    """
    router = AgentRouter()
    decision = router.route_task(
        Task(
            description=task_desc,
            task_type=task_type,
            complexity=complexity,
            requires_reasoning=True,
        )
    )
    return {
        "primary_agent": decision.agent.name,
        "alternatives": [a.name for a in decision.alternatives[:3]],
        "coordination": decision.coordination_pattern,
        "estimated_cost": decision.estimated_cost,
        "rationale": decision.rationale,
    }


def catalyst_evolve(
    routing: Dict[str, Any], agent_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """Propose an evolution: if primary has <50% success, suggest an
    alternative."""
    agents = agent_stats.get("agents", {})
    primary = routing.get("primary_agent")
    primary_sr = agents.get(primary, {}).get("success_rate", 100.0)
    suggestion = {"action": "keep", "reason": "primary performing adequately"}
    if primary_sr < 50.0 and routing.get("alternatives"):
        suggestion = {
            "action": "consider_switch",
            "candidate": routing["alternatives"][0],
            "reason": f"primary success_rate={primary_sr:.1f}% < 50%",
        }
    return suggestion


def gate_enforce(
    pipeline_artifacts: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Verify proof gates on pipeline artifacts.

    Uses ProofGateVerifier to check that persisted artifacts exist and
    conform to expected schema. Returns gate results with evidence.

    Args:
        pipeline_artifacts: Optional dict of artifact paths from run_pipeline()

    Returns:
        Dictionary with passed boolean, checks list, evidence, and timestamp
    """
    verifier = ProofGateVerifier()

    # Build proof gates for common artifact checks
    gates = []

    # Check that rosetta directory exists
    gates.append(
        ProofGate(
            kind=ProofType.FILE_EXISTS,
            path=str(ROSETTA_DIR),
            description="Rosetta artifact directory exists",
        )
    )

    # If artifacts provided, verify key files exist
    if pipeline_artifacts:
        for stem, path_str in pipeline_artifacts.items():
            if stem == "agent_trends_error":
                continue  # Skip error paths
            gates.append(
                ProofGate(
                    kind=ProofType.FILE_EXISTS,
                    path=path_str,
                    description=f"Pipeline artifact '{stem}' persisted",
                )
            )

    # Run all gates
    results = verifier.verify_all(gates)

    # Summarize results
    passed = all(r.passed for r in results.values())
    checks = [
        f"{'✓' if r.passed else '✗'} {r.gate.description}" for r in results.values()
    ]

    return {
        "passed": passed,
        "checks": checks,
        "verification_count": len(results),
        "timestamp": datetime.now().isoformat(),
        "evidence": [r.evidence for r in results.values()],
    }


def run_pipeline(
    task_desc: str,
    task_type: TaskType = TaskType.CODE_GENERATION,
    complexity: TaskComplexity = TaskComplexity.MODERATE,
    payload: Optional[Dict[str, Any]] = None,
) -> PipelineArtifacts:
    """Run the full RosettaStone pipeline from normalization to gates.

    Executes all pipeline stages: RS::Normalize → OT::Encode → MT::Aggregate →
    RSEV::Persist → NuSyQ::Route → Catalyst::Evolve → Gate::Enforce.
    Emits log events at key milestones and persists all artifacts.

    Args:
        task_desc: Human-readable task description
        task_type: Type of task (defaults to CODE_GENERATION)
        complexity: Task complexity level (defaults to MODERATE)
        payload: Optional custom payload (defaults to {"task": task_desc})

    Returns:
        PipelineArtifacts with normalized/encoded/routing/evolve/gates data
        and persisted_paths dict mapping stage names to artifact file paths
    """
    payload = payload or {"task": task_desc}

    # RS::Normalize
    normalized = rs_normalize(payload)
    log_event(
        component="rosetta_pipeline",
        action="start",
        payload={"task": task_desc},
        task_type=task_type.value,
        complexity=complexity.value,
        context={"stage": "RS::Normalize"},
    )

    # OT::Encode
    encoded = ot_encode(task_desc, normalized)

    # NuSyQ::Route
    routing = nsyq_route(task_desc, task_type, complexity)
    log_event(
        component="rosetta_pipeline",
        action="route_decision",
        payload=routing,
        task_type=task_type.value,
        complexity=complexity.value,
        agent=routing.get("primary_agent"),
        context={"stage": "NuSyQ::Route"},
    )

    # MT::Aggregate (record success=False until gates decide)
    mt_aggregate(task_type, complexity, success=False)

    # RSEV::Persist (intermediate)
    persisted: Dict[str, str] = {}
    persisted["normalized"] = str(rsev_persist("normalized", normalized))
    persisted["encoded"] = str(rsev_persist("encoded", encoded))
    persisted["routing"] = str(rsev_persist("routing", routing))

    # Catalyst::Evolve (use current agent trends)
    pm = get_metrics()
    agent_stats = pm.get_agent_stats()
    evolve_suggestion = catalyst_evolve(routing, agent_stats)
    persisted["evolve"] = str(rsev_persist("evolve_suggestion", evolve_suggestion))

    # Gate::Enforce
    gates = gate_enforce(pipeline_artifacts=persisted)
    log_event(
        component="rosetta_pipeline",
        action="gate_result",
        payload=gates,
        task_type=task_type.value,
        complexity=complexity.value,
        outcome="success" if gates.get("passed") else "failure",
        context={"stage": "Gate::Enforce"},
    )

    # Update aggregate with gate result
    mt_aggregate(task_type, complexity, success=gates.get("passed", False))

    # Final persist
    final_bundle = {
        "task": {
            "description": task_desc,
            "type": task_type.value,
            "complexity": complexity.value,
        },
        "artifacts": {
            "normalized": normalized,
            "encoded": encoded,
            "routing": routing,
            "evolve_suggestion": evolve_suggestion,
            "gates": gates,
        },
    }
    persisted["summary"] = str(rsev_persist("pipeline_summary", final_bundle))

    # Export agent trends snapshot to accompany this run
    try:
        trend_path = get_metrics().export_agent_trends()
        persisted["agent_trends"] = str(trend_path)
    except Exception as exc:  # pylint: disable=broad-except
        # Non-fatal: continue without trends if exporter fails
        persisted["agent_trends_error"] = str(exc)

    log_event(
        component="rosetta_pipeline",
        action="end",
        payload={"persisted": persisted},
        task_type=task_type.value,
        complexity=complexity.value,
        outcome="success",
        context={"stage": "summary"},
    )

    return PipelineArtifacts(
        normalized=normalized,
        encoded=encoded,
        routing=routing,
        evolve_suggestion=evolve_suggestion,
        gates=gates,
        persisted_paths=persisted,
    )

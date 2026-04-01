"""System subsystem — task queuing, policy, lifecycle, and path utilities.

Core system-level infrastructure for NuSyQ-Hub:
- TaskQueue: background task management and status tracking
- Policy enforcement: PII detection, safety pre-flight checks
- RunProtocol: run IDs, directory management, manifest writing
- LifecycleManager: service state machine (starting → running → stopping)
- EcosystemPaths: cross-repo root discovery and validation

OmniTag: {
    "purpose": "system_subsystem",
    "tags": ["System", "TaskQueue", "Policy", "Lifecycle", "RunProtocol"],
    "category": "infrastructure",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

from .task_queue import TaskQueue, task_queue

__all__ = [
    # Lifecycle manager (lazy)
    "LifecycleManager",
    # Run protocol (lazy)
    "RunPaths",
    "Service",
    "ServiceState",
    # Task queue (direct import — lightweight, no side effects)
    "TaskQueue",
    "build_claims_evidence",
    "build_handoff_template",
    # Policy (lazy)
    "detect_pii",
    "enforce_policy",
    "generate_run_id",
    # Ecosystem paths (lazy)
    "get_ecosystem_root",
    "get_repo_roots",
    "init_run_paths",
    "materialize_run_bundle",
    "safety_preflight",
    "task_queue",
    "validate_ecosystem",
]


def __getattr__(name: str) -> object:
    if name in ("detect_pii", "enforce_policy", "safety_preflight"):
        from src.system.policy import (detect_pii, enforce_policy,
                                       safety_preflight)

        return locals()[name]
    if name in (
        "RunPaths",
        "generate_run_id",
        "init_run_paths",
        "build_claims_evidence",
        "build_handoff_template",
        "materialize_run_bundle",
    ):
        from src.system.run_protocol import (RunPaths, build_claims_evidence,
                                             build_handoff_template,
                                             generate_run_id, init_run_paths,
                                             materialize_run_bundle)

        return locals()[name]
    if name in ("LifecycleManager", "Service", "ServiceState"):
        from src.system.lifecycle_manager import (LifecycleManager, Service,
                                                  ServiceState)

        return locals()[name]
    if name in ("get_ecosystem_root", "get_repo_roots", "validate_ecosystem"):
        from src.system.ecosystem_paths import (get_ecosystem_root,
                                                get_repo_roots,
                                                validate_ecosystem)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

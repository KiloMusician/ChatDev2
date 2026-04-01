"""Coordination subsystem — multi-repository autonomy coordination.

Coordinates autonomous development across NuSyQ ecosystem repositories
(NuSyQ-Hub, SimulatedVerse, NuSyQ Root): cross-repository task routing,
unified quest log, shared autonomy governance, and synchronized state.

OmniTag: {
    "purpose": "coordination_subsystem",
    "tags": ["MultiRepo", "Coordination", "Autonomy", "Phase3"],
    "category": "orchestration",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.coordination.multi_repo_coordinator import (CrossRepoTask,
                                                         MultiRepoCoordinator,
                                                         Repository,
                                                         RepositoryConfig)

__all__ = [
    "CrossRepoTask",
    "MultiRepoCoordinator",
    "Repository",
    "RepositoryConfig",
]


def __getattr__(name: str):
    if name in ("Repository", "RepositoryConfig", "CrossRepoTask", "MultiRepoCoordinator"):
        from src.coordination.multi_repo_coordinator import (
            CrossRepoTask, MultiRepoCoordinator, Repository, RepositoryConfig)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

"""Publishing subsystem — Docker, PyPI, NPM, and VS Code extension publishing.

Orchestrates publishing workflows for NuSyQ components across multiple
registries. Supports Docker image builds, PyPI package publishing,
NPM module releases, and VS Code extension deployment.

OmniTag: {
    "purpose": "publishing_subsystem",
    "tags": ["Publishing", "Docker", "PyPI", "NPM", "VSCode"],
    "category": "devops",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = [
    "DockerBuilder",
    # Docker
    "DockerConfig",
    "DockerfileGenerator",
    "NPMMetadata",
    "NPMPublisher",
    "PublishConfig",
    "PublishResult",
    "PublishTarget",
    "PublishingOrchestrator",
    # Registry publishers
    "PyPIMetadata",
    "PyPIPublisher",
    # Orchestrator
    "RegistryType",
    "VSCodeMetadata",
    "VSCodePublisher",
]


def __getattr__(name: str):
    if name in ("DockerConfig", "DockerfileGenerator", "DockerBuilder"):
        from src.publishing.docker_builder import (DockerBuilder, DockerConfig,
                                                   DockerfileGenerator)

        return locals()[name]
    if name in (
        "RegistryType",
        "PublishTarget",
        "PublishConfig",
        "PublishResult",
        "PublishingOrchestrator",
    ):
        from src.publishing.orchestrator import (PublishConfig,
                                                 PublishingOrchestrator,
                                                 PublishResult, PublishTarget,
                                                 RegistryType)

        return locals()[name]
    if name in (
        "PyPIMetadata",
        "PyPIPublisher",
        "NPMMetadata",
        "NPMPublisher",
        "VSCodeMetadata",
        "VSCodePublisher",
    ):
        from src.publishing.registry_publishers import (NPMMetadata,
                                                        NPMPublisher,
                                                        PyPIMetadata,
                                                        PyPIPublisher,
                                                        VSCodeMetadata,
                                                        VSCodePublisher)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

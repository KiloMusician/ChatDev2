# DEPRECATED: This router is NOT wired into src/api/main.py (Phase 1 canonical entry point).
# It is an unwired legacy stub. Canonical API entry point: src/api/main.py
"""Publishing API - FastAPI endpoints for publishing workflow.

Endpoints:
- POST /api/publishing/publish - Trigger publishing workflow
- GET /api/publishing/history/{project_id} - Get publishing history
- GET /api/publishing/status/{project_id} - Get latest publish status
- GET /api/publishing/registries - List available registries
"""

import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .orchestrator import (PublishConfig, PublishingOrchestrator,
                           PublishTarget, RegistryType)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/publishing", tags=["publishing"])


class RegistryInfo(str, Enum):
    """Available registries."""

    PYPI = "pypi"
    NPM = "npm"
    VSCODE = "vscode"
    DOCKER = "docker"
    GITHUB = "github"


class PublishRequest(BaseModel):
    """Request to publish a project."""

    project_id: str = Field(..., description="Unique project identifier")
    project_name: str = Field(..., description="Human-readable project name")
    version: str = Field(default="0.1.0", description="Semantic version")
    description: str = Field("", description="Short project description")
    author: str = Field("Unknown", description="Author name")
    author_email: str = Field("", description="Author email address")
    license_type: str = Field(default="MIT", description="License (MIT, Apache-2.0, GPL-3.0, etc.)")

    # Publishing targets
    registries: list[str] = Field(default_factory=lambda: ["pypi"], description="Target registries")

    # Credentials (should come from environment in production)
    pypi_token: str | None = Field(None, description="PyPI API token")
    npm_token: str | None = Field(None, description="NPM token")
    vscode_token: str | None = Field(None, description="VSCode marketplace token")
    docker_username: str | None = Field(None, description="Docker Hub username")
    docker_password: str | None = Field(None, description="Docker Hub password")

    # Metadata
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    repository_url: str | None = Field(None, description="Git repository URL")
    documentation_url: str | None = Field(None, description="Documentation website URL")


class PublishResponse(BaseModel):
    """Response from publish endpoint."""

    status: str = Field(..., description="success, failed, in_progress")
    project_id: str = Field(..., description="Project identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    results: dict[str, Any] = Field(default_factory=dict, description="Per-registry results")
    error: str | None = Field(None, description="Error message if failed")


class PublishHistoryItem(BaseModel):
    """Single publish history entry."""

    timestamp: str
    status: str
    version: str
    registries: list[str]
    error: str | None = None


class PublishStatus(BaseModel):
    """Current publish status for a project."""

    project_id: str
    project_name: str
    latest_version: str | None
    latest_status: str
    last_publish_time: str | None
    registry_status: dict[str, str] = Field(default_factory=dict)


class RegistryDetails(BaseModel):
    """Details about available registry."""

    name: str
    registry_type: str
    description: str
    website: str
    authentication_required: bool


# Initialize orchestrator
_orchestrator: PublishingOrchestrator | None = None


def get_orchestrator() -> PublishingOrchestrator:
    """Get or initialize PublishingOrchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PublishingOrchestrator()
    return _orchestrator


@router.post("/publish", response_model=PublishResponse)
async def publish_project(request: PublishRequest) -> PublishResponse:
    """Publish a project to specified registries.

    Args:
        request: PublishRequest with project and registry details

    Returns:
        PublishResponse with status and per-registry results
    """
    try:
        logger.info(f"Publishing project: {request.project_name} v{request.version}")

        # Create PublishConfig
        pypi_only = len(request.registries) == 1 and "pypi" in request.registries
        npm_only = len(request.registries) == 1 and "npm" in request.registries
        vscode_only = len(request.registries) == 1 and "vscode" in request.registries
        docker_only = len(request.registries) == 1 and "docker" in request.registries

        # Determine PublishTarget
        if pypi_only:
            publish_target = PublishTarget.PYPI_ONLY
        elif npm_only:
            publish_target = PublishTarget.NPM_ONLY
        elif vscode_only:
            publish_target = PublishTarget.VSCODE_ONLY
        elif docker_only:
            publish_target = PublishTarget.DOCKER_ONLY
        else:
            publish_target = PublishTarget.MULTI

        # Create config
        config = PublishConfig(
            project_id=request.project_id,
            project_name=request.project_name,
            version=request.version,
            description=request.description,
            author=request.author,
            author_email=request.author_email,
            license_type=request.license_type,
            targets=[RegistryType(r) for r in request.registries],
            publish_target=publish_target,
            pypi_token=request.pypi_token,
            npm_token=request.npm_token,
            vscode_token=request.vscode_token,
            docker_username=request.docker_username,
            docker_password=request.docker_password,
            repository_url=request.repository_url,
            documentation_url=request.documentation_url,
            keywords=request.keywords,
        )

        # Execute publishing
        orchestrator = get_orchestrator()
        result = orchestrator.publish(config, project_path=Path("."))

        return PublishResponse(
            status=result.status,
            project_id=request.project_id,
            timestamp=datetime.now().isoformat(),
            results={
                "pypi": result.pypi_result if hasattr(result, "pypi_result") else None,
                "npm": result.npm_result if hasattr(result, "npm_result") else None,
                "vscode": result.vscode_result if hasattr(result, "vscode_result") else None,
                "docker": result.docker_result if hasattr(result, "docker_result") else None,
            },
        )

    except Exception as e:
        logger.error(f"Publishing failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Publishing failed: {e!s}") from e


@router.get("/history/{project_id}", response_model=list[PublishHistoryItem])
async def get_publish_history(
    project_id: str,
    limit: int = Query(10, ge=1, le=100, description="Max results"),
) -> list[PublishHistoryItem]:
    """Get publishing history for a project.

    Args:
        project_id: Project identifier
        limit: Maximum number of history items to return

    Returns:
        List of publish history items
    """
    try:
        orchestrator = get_orchestrator()

        # Load publish history from logs (simplified version)
        history = orchestrator.get_publish_history(project_id, limit=limit)

        return [
            PublishHistoryItem(
                timestamp=item.get("timestamp", ""),
                status=item.get("status", "unknown"),
                version=item.get("version", ""),
                registries=item.get("registries", []),
                error=item.get("error"),
            )
            for item in history
        ]

    except Exception as e:
        logger.error(f"Failed to retrieve history: {e!s}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {e!s}") from e


@router.get("/status/{project_id}", response_model=PublishStatus)
async def get_publish_status(project_id: str) -> PublishStatus:
    """Get latest publish status for a project.

    Args:
        project_id: Project identifier

    Returns:
        Current publish status
    """
    try:
        orchestrator = get_orchestrator()

        # Get status from history
        status_info = orchestrator.get_publish_status(project_id)

        return PublishStatus(
            project_id=project_id,
            project_name=status_info.get("project_name", "Unknown"),
            latest_version=status_info.get("latest_version"),
            latest_status=status_info.get("latest_status", "unknown"),
            last_publish_time=status_info.get("last_publish_time"),
            registry_status=status_info.get("registry_status", {}),
        )

    except Exception as e:
        logger.error(f"Failed to retrieve status: {e!s}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve status: {e!s}") from e


@router.get("/registries", response_model=list[RegistryDetails])
async def list_registries() -> list[RegistryDetails]:
    """List all available registries.

    Returns:
        List of registry details
    """
    return [
        RegistryDetails(
            name="PyPI",
            registry_type="pypi",
            description="Python Package Index - for sharing Python libraries and tools",
            website="https://pypi.org",
            authentication_required=True,
        ),
        RegistryDetails(
            name="NPM",
            registry_type="npm",
            description="Node Package Manager - for sharing JavaScript and Node.js packages",
            website="https://www.npmjs.com",
            authentication_required=True,
        ),
        RegistryDetails(
            name="VS Code Marketplace",
            registry_type="vscode",
            description="VS Code extension marketplace for sharing editor extensions",
            website="https://marketplace.visualstudio.com",
            authentication_required=True,
        ),
        RegistryDetails(
            name="Docker Hub",
            registry_type="docker",
            description="Container image registry for sharing Docker images",
            website="https://hub.docker.com",
            authentication_required=True,
        ),
        RegistryDetails(
            name="GitHub Releases",
            registry_type="github",
            description="GitHub platform for releasing binaries and source archives",
            website="https://github.com",
            authentication_required=True,
        ),
    ]


@router.get("/health")
async def publishing_health() -> dict[str, Any]:
    """Health check endpoint for publishing API."""
    try:
        get_orchestrator()
        return {
            "status": "healthy",
            "service": "publishing",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e!s}")
        return {
            "status": "unhealthy",
            "service": "publishing",
            "error": str(e),
        }

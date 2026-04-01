# DEPRECATED: This router is NOT wired into src/api/main.py (Phase 1 canonical entry point).
# It is an unwired legacy stub. Canonical API entry point: src/api/main.py
"""API endpoints for Universal Project Generator.

REST API interface for project generation, template discovery, and management.

Note: This API uses the consolidated factory-based generators (Sprint 3).
Legacy imports from src.generators are maintained for backward compatibility.
"""

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from src.factories.generators.specialized.universal_project_generator import \
    UniversalProjectGenerator
# Use factory-based canonical imports (migrated Sprint 3)
from src.generators.template_definitions import (ProjectType, get_template,
                                                 list_templates)

# New factory-based generators are available via the consolidated factories package.

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class TemplateInfo(BaseModel):
    """Template information for API responses."""

    template_id: str
    name: str
    type: str
    language: str
    description: str
    complexity: int
    estimated_generation_time: str
    primary_ai_provider: str
    ai_enhancement_available: bool
    tags: list[str] = []
    prerequisites: list[str] = []


class GenerateProjectRequest(BaseModel):
    """Request to generate a new project."""

    template_id: str = Field(..., description="Template ID to use")
    project_name: str = Field(..., description="Name for the generated project")
    project_type: str | None = Field(None, description="Project type override")
    options: dict[str, Any] = Field(default_factory=dict, description="Customization options")


class GenerateProjectResponse(BaseModel):
    """Response from project generation."""

    project_id: str
    project_name: str
    status: str  # "success" or "failed"
    output_path: str
    ai_provider: str
    generation_time: float
    created_at: str
    metadata: dict[str, Any] = {}
    error_message: str | None = None


class GeneratorHealthResponse(BaseModel):
    """Health check response."""

    status: str  # "healthy", "degraded", "error"
    upg_available: bool
    registry_status: str
    templates_available: int
    projects_generated: int


# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(prefix="/api/generators", tags=["generators"])

_CREATE_PROJECT_BODY = Body(..., description="Project generation parameters")

# Global UPG instance
_upg_instance: UniversalProjectGenerator | None = None


def get_upg() -> UniversalProjectGenerator:
    """Get or create UPG instance."""
    global _upg_instance
    if _upg_instance is None:
        _upg_instance = UniversalProjectGenerator()
    return _upg_instance


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/health", response_model=GeneratorHealthResponse)
async def health_check() -> GeneratorHealthResponse:
    """Check generator health and status."""
    try:
        upg = get_upg()
        templates = upg.list_templates()
        projects = upg.list_generated_projects()

        return GeneratorHealthResponse(
            status="healthy",
            upg_available=True,
            registry_status="operational",
            templates_available=len(templates),
            projects_generated=len(projects),
        )
    except Exception:
        return GeneratorHealthResponse(
            status="error",
            upg_available=False,
            registry_status="error",
            templates_available=0,
            projects_generated=0,
        )


@router.get("/templates", response_model=list[TemplateInfo])
async def list_all_templates(
    project_type: str | None = Query(None, description="Filter by project type"),
    complexity_min: int = Query(1, ge=1, le=10, description="Minimum complexity"),
    complexity_max: int = Query(10, ge=1, le=10, description="Maximum complexity"),
) -> list[TemplateInfo]:
    """List all available templates.

    Query Parameters:
    - project_type: Optional filter (game, webapp, package, extension, cli, library)
    - complexity_min/max: Filter by complexity range (1-10)
    """
    try:
        # Filter by type
        ptype = None
        if project_type:
            try:
                ptype = ProjectType[project_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid project type: {project_type}"
                ) from None

        templates = list_templates(ptype)

        # Filter by complexity
        templates = [t for t in templates if complexity_min <= t.complexity <= complexity_max]

        return [
            TemplateInfo(
                template_id=t.template_id,
                name=t.name,
                type=t.type.value,
                language=t.language.value,
                description=t.description,
                complexity=t.complexity,
                estimated_generation_time=t.estimated_generation_time,
                primary_ai_provider=t.primary_ai_provider.value,
                ai_enhancement_available=t.ai_enhancement_available,
                tags=t.tags,
                prerequisites=t.prerequisites,
            )
            for t in templates
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/templates/{template_id}", response_model=TemplateInfo)
async def get_template_info(template_id: str) -> TemplateInfo:
    """Get detailed information about a specific template."""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    return TemplateInfo(
        template_id=template.template_id,
        name=template.name,
        type=template.type.value,
        language=template.language.value,
        description=template.description,
        complexity=template.complexity,
        estimated_generation_time=template.estimated_generation_time,
        primary_ai_provider=template.primary_ai_provider.value,
        ai_enhancement_available=template.ai_enhancement_available,
        tags=template.tags,
        prerequisites=template.prerequisites,
    )


@router.post("/create", response_model=GenerateProjectResponse)
async def create_project(
    request: GenerateProjectRequest = _CREATE_PROJECT_BODY,
) -> GenerateProjectResponse:
    """Generate a new project from template.

    This is the main endpoint for creating new projects. It:
    1. Validates the template
    2. Selects appropriate AI provider
    3. Generates starter files
    4. Registers the artifact
    5. Logs to quest system
    """
    try:
        upg = get_upg()

        # Validate template exists
        template = upg.get_template(request.template_id)
        if not template:
            raise HTTPException(
                status_code=404, detail=f"Template not found: {request.template_id}"
            )

        # Generate project
        result = upg.generate(
            template_id=request.template_id,
            project_name=request.project_name,
            project_type=request.project_type,
            options=request.options,
        )

        if result.status != "success":
            raise HTTPException(
                status_code=400, detail=f"Generation failed: {result.error_message}"
            )

        return GenerateProjectResponse(
            project_id=result.project_id,
            project_name=result.project_name,
            status=result.status,
            output_path=result.output_path,
            ai_provider=result.ai_provider,
            generation_time=result.generation_time,
            created_at=result.created_at,
            metadata=result.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/projects/{project_id}")
async def get_project_status(project_id: str):
    """Get status and metadata for a generated project."""
    upg = get_upg()
    project = upg.get_project_info(project_id)

    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    return project


@router.get("/projects")
async def list_projects():
    """List all generated projects."""
    upg = get_upg()
    projects = upg.list_generated_projects()
    return {"total": len(projects), "projects": projects}


@router.get("/complexity-info/{template_id}")
async def get_complexity_info(template_id: str):
    """Get complexity and AI provider information for a template."""
    upg = get_upg()
    info = upg.get_template_complexity_info(template_id)

    if not info:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    return info


# ============================================================================
# BATCH OPERATIONS (Advanced)
# ============================================================================


class BatchGenerateRequest(BaseModel):
    """Request to generate multiple projects."""

    projects: list[GenerateProjectRequest]


@router.post("/batch-create")
async def batch_create_projects(request: BatchGenerateRequest):
    """Generate multiple projects in batch.

    Note: Projects are generated sequentially, not in parallel.
    """
    upg = get_upg()
    results = []
    failed = 0

    for project_req in request.projects:
        try:
            result = upg.generate(
                template_id=project_req.template_id,
                project_name=project_req.project_name,
                project_type=project_req.project_type,
                options=project_req.options,
            )

            results.append(
                {
                    "project_name": project_req.project_name,
                    "status": result.status,
                    "project_id": result.project_id if result.status == "success" else None,
                    "error": result.error_message if result.status != "success" else None,
                }
            )

            if result.status != "success":
                failed += 1

        except Exception as e:
            results.append(
                {
                    "project_name": project_req.project_name,
                    "status": "failed",
                    "project_id": None,
                    "error": str(e),
                }
            )
            failed += 1

    return {
        "total": len(request.projects),
        "successful": len(request.projects) - failed,
        "failed": failed,
        "results": results,
    }


# ============================================================================
# STATISTICS & ANALYTICS
# ============================================================================


@router.get("/stats")
async def get_statistics():
    """Get generator statistics."""
    upg = get_upg()
    templates = upg.list_templates()
    projects = upg.list_generated_projects()

    # Group by template
    template_usage: dict[str, int] = {}
    for project in projects:
        tid = project.get("template_id")
        template_usage[tid] = template_usage.get(tid, 0) + 1

    # Group by AI provider
    provider_usage: dict[str, int] = {}
    for project in projects:
        provider = project.get("ai_provider")
        provider_usage[provider] = provider_usage.get(provider, 0) + 1

    # Complexity distribution
    complexity_dist: dict[str, int] = {}
    for t in templates:
        complexity_dist[str(t.complexity)] = complexity_dist.get(str(t.complexity), 0) + 1

    return {
        "total_templates": len(templates),
        "total_projects_generated": len(projects),
        "template_usage": template_usage,
        "ai_provider_usage": provider_usage,
        "template_complexity_distribution": complexity_dist,
    }

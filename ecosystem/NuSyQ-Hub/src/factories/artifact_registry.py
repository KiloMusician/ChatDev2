"""Artifact Registry - Flexible versioning for factory outputs.

Tracks ChatDev WareHouse outputs, manual edits, AI provider metadata.
Uses YAML manifests (not rigid database) for contextual flexibility.

Registry Structure:
    state/registry/
        projects.yaml           # Index of all projects
        <project_name>/
            manifest.yaml       # Project metadata + versions
            v1.0.0/            # Versioned snapshots
                metadata.yaml
                src/
                tests/
            v1.1.0/
                ...
"""

import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import]


@dataclass
class ProjectVersion:
    """Single version of a project."""

    version: str
    created_at: str
    ai_provider: str  # "chatdev", "ollama", "claude", "manual"
    chatdev_warehouse_path: str | None = None  # Link to original ChatDev output
    token_cost: float = 0.0  # Estimated token cost
    model_used: str | None = None  # e.g., "qwen2.5-coder:7b"
    description: str = ""
    files_changed: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectManifest:
    """Manifest for a single project (all versions)."""

    name: str
    type: str  # "game", "cli", "library"
    created_at: str
    updated_at: str
    current_version: str
    versions: list[ProjectVersion] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ArtifactRegistry:
    """Manages versioned project artifacts from factory."""

    def __init__(self, registry_root: Path | None = None):
        """Initialize registry."""
        if registry_root is None:
            # Default to NuSyQ-Hub/state/registry
            registry_root = Path(__file__).parent.parent.parent / "state" / "registry"

        self.registry_root = Path(registry_root)
        self.registry_root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.registry_root / "projects.yaml"

        # Create index if not exists
        if not self.index_path.exists():
            self._save_index({})

    def _compute_files_changed(
        self,
        name: str,
        source_path: Path,
        previous_version: str | None = None,
    ) -> list[str]:
        """Compute list of changed files between versions.

        Args:
            name: Project name
            source_path: Path to new version's files
            previous_version: Previous version to compare against

        Returns:
            List of relative file paths that changed (added, modified, or removed)
        """
        # Collect files in new version
        new_files: set[str] = set()
        for f in source_path.rglob("*"):
            if f.is_file():
                new_files.add(str(f.relative_to(source_path)))

        if not previous_version:
            # First version - all files are "changed" (added)
            return sorted(new_files)

        # Get previous version path
        prev_dir = self.registry_root / name / previous_version
        if not prev_dir.exists():
            return sorted(new_files)

        # Collect files in previous version
        old_files: set[str] = set()
        for f in prev_dir.rglob("*"):
            if f.is_file() and f.name != "metadata.yaml":
                old_files.add(str(f.relative_to(prev_dir)))

        # Compute changes: added + removed + modified
        added = new_files - old_files
        removed = old_files - new_files
        common = new_files & old_files

        # Check for content changes in common files
        modified: set[str] = set()
        for rel_path in common:
            new_content = (source_path / rel_path).read_bytes()
            old_content = (prev_dir / rel_path).read_bytes()
            if new_content != old_content:
                modified.add(rel_path)

        return sorted(added | removed | modified)

    def _load_index(self) -> dict[str, str]:
        """Load project index (name → manifest path)."""
        if not self.index_path.exists():
            return {}

        with open(self.index_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _save_index(self, index: dict[str, str]) -> None:
        """Save project index."""
        with open(self.index_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(index, f, default_flow_style=False)

    def register(
        self,
        name: str,
        project_type: str,
        version: str,
        source_path: Path,
        ai_provider: str = "chatdev",
        chatdev_warehouse_path: str | None = None,
        token_cost: float = 0.0,
        model_used: str | None = None,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Register a new project version in the registry.

        Args:
            name: Project name
            project_type: "game", "cli", "library"
            version: Version string (e.g., "1.0.0")
            source_path: Path to generated project files
            ai_provider: "chatdev", "ollama", "claude", "manual"
            chatdev_warehouse_path: Link to ChatDev WareHouse output
            token_cost: Estimated token cost
            model_used: AI model name
            description: Version description
            metadata: Additional metadata

        Returns:
            Path to registered version directory
        """
        now = datetime.now().isoformat()
        project_dir = self.registry_root / name
        project_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = project_dir / "manifest.yaml"

        # Load or create manifest
        if manifest_path.exists():
            with open(manifest_path, encoding="utf-8") as f:
                manifest_data = yaml.safe_load(f)
            # yaml.safe_load returns versions as plain dicts; convert to dataclasses
            manifest_data["versions"] = [
                ProjectVersion(**v) if isinstance(v, dict) else v
                for v in manifest_data.get("versions") or []
            ]
            manifest = ProjectManifest(**manifest_data)
            manifest.updated_at = now
            manifest.current_version = version
        else:
            manifest = ProjectManifest(
                name=name,
                type=project_type,
                created_at=now,
                updated_at=now,
                current_version=version,
                metadata=metadata or {},
            )

        # Compute files changed from previous version
        existing_versions = [v.version for v in manifest.versions]
        previous_version = existing_versions[-1] if existing_versions else None
        files_changed = self._compute_files_changed(name, source_path, previous_version)

        # Create version entry
        version_entry = ProjectVersion(
            version=version,
            created_at=now,
            ai_provider=ai_provider,
            chatdev_warehouse_path=chatdev_warehouse_path,
            token_cost=token_cost,
            model_used=model_used,
            description=description,
            files_changed=files_changed,
            metadata=metadata or {},
        )

        # Add version to manifest (if not already present)
        if version not in existing_versions:
            manifest.versions.append(version_entry)

        # Save manifest
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(asdict(manifest), f, default_flow_style=False)

        # Copy project files to versioned directory
        version_dir = project_dir / version
        if version_dir.exists():
            shutil.rmtree(version_dir)
        shutil.copytree(source_path, version_dir)

        # Save version metadata
        version_meta_path = version_dir / "metadata.yaml"
        with open(version_meta_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(asdict(version_entry), f, default_flow_style=False)

        # Update index
        index = self._load_index()
        index[name] = str(manifest_path.relative_to(self.registry_root))
        self._save_index(index)

        return version_dir

    def list_projects(self) -> list[str]:
        """List all registered projects."""
        index = self._load_index()
        return list(index.keys())

    def get_manifest(self, name: str) -> ProjectManifest | None:
        """Get project manifest."""
        index = self._load_index()
        if name not in index:
            return None

        manifest_path = self.registry_root / index[name]
        if not manifest_path.exists():
            return None

        with open(manifest_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # yaml.safe_load returns versions as plain dicts; convert to dataclasses
        data["versions"] = [
            ProjectVersion(**v) if isinstance(v, dict) else v for v in data.get("versions") or []
        ]
        return ProjectManifest(**data)

    def get_version_path(self, name: str, version: str | None = None) -> Path | None:
        """Get path to specific version (or current if version=None)."""
        manifest = self.get_manifest(name)
        if not manifest:
            return None

        target_version = version or manifest.current_version
        version_dir = self.registry_root / name / target_version

        if not version_dir.exists():
            return None

        return version_dir

    def list_versions(self, name: str) -> list[str]:
        """List all versions of a project."""
        manifest = self.get_manifest(name)
        if not manifest:
            return []

        return [v.version for v in manifest.versions]

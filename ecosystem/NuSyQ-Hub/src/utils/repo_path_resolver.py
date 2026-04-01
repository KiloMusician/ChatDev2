"""🗺️ Centralized Repository Path Resolver.

Provides centralized, configurable path resolution for the multi-repository NuSyQ ecosystem.
Reads from nusyq.manifest.yaml with environment variable overrides for portability.

OmniTag: {
    "purpose": "Centralized multi-repository path resolution",
    "dependencies": ["pathlib", "os", "yaml"],
    "context": "Eliminates hardcoded paths, improves portability",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "PathResolver",
    "integration_points": ["nusyq_manifest", "environment_variables", "cross_repo"],
    "related_tags": ["Configuration", "Portability", "SystemIntegration"]
}

RSHTS: ΞΨΩΣ∞⟨PATH-RESOLVER⟩→ΦΣΣ⟨MULTI-REPO⟩→∞⟨PORTABILITY⟩
"""

import contextlib
import importlib
import os
import re
import warnings
from pathlib import Path
from typing import ClassVar, Optional

try:
    yaml = importlib.import_module("yaml")
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    warnings.warn(
        "PyYAML not available. Using fallback defaults for path resolution.",
        stacklevel=2,
    )


class RepositoryPathResolver:
    """🗺️ Multi-Repository Path Resolver.

    Resolves repository paths with this priority:
    1. Environment variables (NUSYQ_ROOT, NUSYQ_HUB_ROOT, SIMULATEDVERSE_ROOT)
    2. nusyq.manifest.yaml repository_paths section
    3. Portable defaults (home-based conventional layout)

    Usage:
        from src.utils.repo_path_resolver import get_repo_path

        hub_path = get_repo_path('NUSYQ_HUB_ROOT')
        nusyq_path = get_repo_path('NUSYQ_ROOT')
        sim_path = get_repo_path('SIMULATEDVERSE_ROOT')
    """

    # Singleton instance
    _instance: Optional["RepositoryPathResolver"] = None

    # Repository keys managed by this resolver
    REPO_KEYS = ("NUSYQ_ROOT", "NUSYQ_HUB_ROOT", "SIMULATEDVERSE_ROOT")

    # Baseline fallback paths (portable, home-based)
    DEFAULT_PATHS: ClassVar[dict[str, str]] = {
        "NUSYQ_ROOT": str(Path.home() / "NuSyQ"),
        "NUSYQ_HUB_ROOT": str(Path.home() / "Desktop" / "Legacy" / "NuSyQ-Hub"),
        "SIMULATEDVERSE_ROOT": str(Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"),
    }

    def __init__(self, manifest_path: Path | None = None) -> None:
        """Initialize path resolver with optional manifest path."""
        self._paths: dict[str, Path] = {}
        self._manifest_path = manifest_path or self._find_manifest()
        self._load_paths()

    @classmethod
    def get_instance(cls, manifest_path: Path | None = None) -> "RepositoryPathResolver":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(manifest_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (useful for testing)."""
        cls._instance = None

    def _find_manifest(self) -> Path | None:
        """Find nusyq.manifest.yaml in standard locations."""
        hub_from_module = Path(__file__).resolve().parents[2]
        user_root = hub_from_module.parents[2] if len(hub_from_module.parents) > 2 else Path.home()

        # Check common locations
        search_paths = [
            hub_from_module / "nusyq.manifest.yaml",
            user_root / "NuSyQ" / "nusyq.manifest.yaml",
            Path(self.DEFAULT_PATHS["NUSYQ_ROOT"]) / "nusyq.manifest.yaml",
            Path.home() / "NuSyQ" / "nusyq.manifest.yaml",
            Path.cwd() / "nusyq.manifest.yaml",
        ]

        for manifest_path in search_paths:
            if manifest_path.exists():
                return manifest_path

        return None

    @staticmethod
    def _pick_existing_path(candidates: list[Path], fallback: Path) -> Path:
        """Return first existing candidate path, otherwise fallback."""
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return fallback

    def _compute_default_paths(self) -> dict[str, Path]:
        """Compute dynamic defaults from workspace topology before env overrides."""
        defaults = {key: Path(value) for key, value in self.DEFAULT_PATHS.items()}

        hub_from_module = Path(__file__).resolve().parents[2]
        if (hub_from_module / "src").exists() and (hub_from_module / "scripts").exists():
            defaults["NUSYQ_HUB_ROOT"] = hub_from_module

            user_root = (
                hub_from_module.parents[2] if len(hub_from_module.parents) > 2 else Path.home()
            )
            sim_candidates = [
                hub_from_module.parent / "SimulatedVerse" / "SimulatedVerse",
                hub_from_module.parent / "SimulatedVerse",
                hub_from_module.parent.parent / "SimulatedVerse" / "SimulatedVerse",
                hub_from_module.parent.parent / "SimulatedVerse",
                user_root / "Desktop" / "SimulatedVerse" / "SimulatedVerse",
                user_root / "Desktop" / "SimulatedVerse",
            ]
            defaults["SIMULATEDVERSE_ROOT"] = self._pick_existing_path(
                sim_candidates,
                defaults["SIMULATEDVERSE_ROOT"],
            )

            nusyq_candidates = [
                hub_from_module.parent / "NuSyQ",
                hub_from_module.parent.parent / "NuSyQ",
                user_root / "NuSyQ",
            ]
            defaults["NUSYQ_ROOT"] = self._pick_existing_path(
                nusyq_candidates, defaults["NUSYQ_ROOT"]
            )

        return defaults

    @staticmethod
    def _expand_cross_shell_env(path_value: str) -> str:
        """Expand POSIX, Windows (%VAR%), and PowerShell ($env:VAR) variables."""
        expanded = os.path.expandvars(path_value)
        expanded = re.sub(
            r"%([^%]+)%",
            lambda match: os.getenv(match.group(1), match.group(0)),
            expanded,
        )
        expanded = re.sub(
            r"\$env:([A-Za-z_][A-Za-z0-9_]*)",
            lambda match: os.getenv(match.group(1), match.group(0)),
            expanded,
        )
        return expanded

    @staticmethod
    def _windows_path_to_wsl(path_value: str) -> str:
        """Convert Windows drive paths to WSL mount paths (WSL/Linux only)."""
        import sys

        if sys.platform == "win32":
            return path_value
        match = re.match(r"^([A-Za-z]):[\\/](.*)$", path_value)
        if not match:
            return path_value
        drive = match.group(1).lower()
        remainder = match.group(2).replace("\\", "/")
        return f"/mnt/{drive}/{remainder}"

    @staticmethod
    def _has_unresolved_tokens(path_value: str) -> bool:
        """Detect unresolved shell variable markers in path strings."""
        return bool(re.search(r"%[^%]+%|\$env:[A-Za-z_][A-Za-z0-9_]*", path_value))

    @staticmethod
    def _infer_userprofile_path() -> Path | None:
        """Infer Windows user profile path from current workspace when available."""
        hub_from_module = Path(__file__).resolve().parents[2]
        if len(hub_from_module.parents) > 2:
            return hub_from_module.parents[2]
        return None

    def _normalize_path_value(self, path_value: str) -> Path | None:
        """Normalize cross-shell path values into concrete local paths."""
        expanded = self._expand_cross_shell_env(path_value).strip().strip("\"'")
        inferred_userprofile = self._infer_userprofile_path()
        if inferred_userprofile is not None:
            expanded = expanded.replace("%USERPROFILE%", str(inferred_userprofile))
            expanded = re.sub(
                r"\$env:USERPROFILE",
                lambda _match: str(inferred_userprofile),
                expanded,
                flags=re.IGNORECASE,
            )
        expanded = self._windows_path_to_wsl(expanded)
        candidate = Path(expanded).expanduser()
        if self._has_unresolved_tokens(expanded) and not candidate.exists():
            return None
        return candidate

    def _load_paths(self) -> None:
        """Load paths from environment, manifest, and defaults."""
        # Step 1: Load defaults
        defaults = self._compute_default_paths()
        for key, default_path in defaults.items():
            self._paths[key] = default_path

        # Step 2: Load from manifest (if available)
        if self._manifest_path and YAML_AVAILABLE:
            with contextlib.suppress(
                Exception
            ):  # manifest loading optional; fallback to env/defaults
                self._load_from_manifest()

        # Step 3: Override with environment variables (highest priority)
        for key in self.REPO_KEYS:
            env_value = os.getenv(key)
            if env_value:
                candidate = self._normalize_path_value(env_value)
                if candidate is not None:
                    self._paths[key] = candidate

    def _load_from_manifest(self) -> None:
        """Load repository paths from nusyq.manifest.yaml."""
        if not self._manifest_path or not self._manifest_path.exists():
            return

        try:
            with open(self._manifest_path, encoding="utf-8") as f:
                manifest = yaml.safe_load(f)

            # Check for repository_paths section
            repo_paths = manifest.get("repository_paths", {})
            for key, path_value in repo_paths.items():
                if isinstance(path_value, str):
                    candidate = self._normalize_path_value(path_value)
                    if candidate is not None:
                        self._paths[key] = candidate

        except (OSError, yaml.YAMLError) as e:
            warnings.warn(f"Error reading manifest {self._manifest_path}: {e}", stacklevel=2)

    def get_path(self, repo_key: str) -> Path:
        """Get resolved path for a repository.

        Args:
            repo_key: Repository identifier (NUSYQ_ROOT, NUSYQ_HUB_ROOT, SIMULATEDVERSE_ROOT)

        Returns:
            Resolved Path object

        Raises:
            KeyError: If repo_key is not recognized

        """
        if repo_key not in self._paths:
            msg = f"Unknown repository key: {repo_key}. Valid keys: {', '.join(self.REPO_KEYS)}"
            raise KeyError(
                msg,
            )

        return self._paths[repo_key].resolve()

    def get_path_str(self, repo_key: str) -> str:
        """Get resolved path as string."""
        return str(self.get_path(repo_key))

    def all_paths(self) -> dict[str, Path]:
        """Get all configured repository paths."""
        return {key: path.resolve() for key, path in self._paths.items()}

    def validate_paths(self) -> dict[str, bool]:
        """Validate that all repository paths exist.

        Returns:
            dict mapping repo_key to existence status

        """
        return {key: path.exists() for key, path in self._paths.items()}

    def get_manifest_path(self) -> Path | None:
        """Get the path to the loaded manifest file."""
        return self._manifest_path

    def __repr__(self) -> str:
        """String representation showing configured paths."""
        lines = ["RepositoryPathResolver:"]
        for key, path in sorted(self._paths.items()):
            exists = "✓" if path.exists() else "✗"
            lines.append(f"  {exists} {key}: {path}")
        return "\n".join(lines)


# Singleton accessor functions (convenience API)


def get_repo_path(repo_key: str) -> Path:
    r"""Get resolved repository path (convenience function).

    Args:
        repo_key: Repository identifier (NUSYQ_ROOT, NUSYQ_HUB_ROOT, SIMULATEDVERSE_ROOT)

    Returns:
        Resolved Path object

    Example:
        >>> from src.utils.repo_path_resolver import get_repo_path
        >>> hub_path = get_repo_path('NUSYQ_HUB_ROOT')
        >>> print(hub_path)
        C:\Users\YourUser\Desktop\Legacy\NuSyQ-Hub

    """
    resolver = RepositoryPathResolver.get_instance()
    return resolver.get_path(repo_key)


def get_repo_path_str(repo_key: str) -> str:
    """Get resolved repository path as string (convenience function)."""
    return str(get_repo_path(repo_key))


def validate_all_paths() -> dict[str, bool]:
    """Validate all repository paths exist (convenience function)."""
    resolver = RepositoryPathResolver.get_instance()
    return resolver.validate_paths()


def get_all_paths() -> dict[str, Path]:
    """Get all configured repository paths (convenience function)."""
    resolver = RepositoryPathResolver.get_instance()
    return resolver.all_paths()


def print_paths() -> None:
    """Print all configured paths with validation status."""
    RepositoryPathResolver.get_instance()


# CLI usage for diagnostics
if __name__ == "__main__":
    resolver = RepositoryPathResolver.get_instance()

    # Show manifest location
    manifest = resolver.get_manifest_path()
    if manifest:
        pass
    else:
        pass

    # Show all paths

    # Validation summary
    validation = resolver.validate_paths()
    valid_count = sum(validation.values())
    total_count = len(validation)

    # Environment variable check
    for key in resolver.REPO_KEYS:
        env_value = os.getenv(key)
        if env_value:
            pass
        else:
            pass

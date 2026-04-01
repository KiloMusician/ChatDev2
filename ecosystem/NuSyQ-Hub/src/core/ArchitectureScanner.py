#!/usr/bin/env python3
"""KILO-FOOLISH Architecture Scanner.

Scans repository structure and generates architecture documentation.

OmniTag: {
    "purpose": "Repository architecture analysis",
    "dependencies": ["pathlib", "json"],
    "context": "System diagnostics and documentation",
    "evolution_stage": "v1.0"
}
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class KILOArchitectureScanner:
    """Scans repository and generates architecture maps."""

    def __init__(self, repo_root: str | None = None) -> None:
        """Initialize KILOArchitectureScanner with repo_root."""
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.architecture: dict[str, Any] = {}

    def run_full_scan(self) -> dict[str, Any]:
        """Run full repository architecture scan."""
        self.architecture = {
            "timestamp": datetime.now().isoformat(),
            "repo_root": str(self.repo_root),
            "structure": self._scan_directory(self.repo_root),
            "summary": self._generate_summary(),
        }

        # Save results
        output_file = self.repo_root / "architecture_map.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.architecture, f, indent=2)

        return self.architecture

    def _scan_directory(self, directory: Path, level: int = 0) -> dict[str, Any]:
        """Recursively scan directory structure."""
        if level > 5:  # Limit recursion depth
            return {}

        if not directory.is_dir():
            return {}

        structure = {
            "type": "directory",
            "name": directory.name,
            "path": str(directory.relative_to(self.repo_root)),
            "files": [],
            "subdirs": {},
        }

        try:
            for item in directory.iterdir():
                # Skip common ignored directories
                if item.name in {
                    ".git",
                    "__pycache__",
                    ".venv",
                    "node_modules",
                    ".pytest_cache",
                }:
                    continue

                if item.is_file():
                    files_list: list[dict[str, Any]] = structure["files"]  # type: ignore[assignment]
                    files_list.append(
                        {
                            "name": item.name,
                            "size": item.stat().st_size,
                            "suffix": item.suffix,
                        },
                    )
                elif item.is_dir():
                    structure["subdirs"][item.name] = self._scan_directory(item, level + 1)
        except PermissionError:
            logger.debug("Suppressed PermissionError", exc_info=True)

        return structure

    def _generate_summary(self) -> dict[str, Any]:
        """Generate summary statistics."""
        return {
            "total_files": self._count_files(self.architecture.get("structure", {})),
            "python_files": self._count_files_by_ext(self.architecture.get("structure", {}), ".py"),
            "directories": self._count_directories(self.architecture.get("structure", {})),
        }

    def _count_files(self, structure: dict) -> int:
        """Count total files in structure."""
        if not structure:
            return 0
        count = len(structure.get("files", []))
        for subdir in structure.get("subdirs", {}).values():
            count += self._count_files(subdir)
        return count

    def _count_files_by_ext(self, structure: dict, ext: str) -> int:
        """Count files by extension."""
        if not structure:
            return 0
        count = sum(1 for f in structure.get("files", []) if f.get("suffix") == ext)
        for subdir in structure.get("subdirs", {}).values():
            count += self._count_files_by_ext(subdir, ext)
        return count

    def _count_directories(self, structure: dict) -> int:
        """Count total directories."""
        if not structure:
            return 0
        count = len(structure.get("subdirs", {}))
        for subdir in structure.get("subdirs", {}).values():
            count += self._count_directories(subdir)
        return count


if __name__ == "__main__":
    scanner = KILOArchitectureScanner()
    result = scanner.run_full_scan()

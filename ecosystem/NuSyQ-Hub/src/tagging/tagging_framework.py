from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

"""Simple tagging helper used by Culture Ship components and diagnostics."""


@dataclass(frozen=True)
class TaggingFrameworkConfig:
    rules_path: str
    default_category: str = "Miscellaneous"


class TaggingFramework:
    def __init__(self, config: TaggingFrameworkConfig | Mapping[str, Any]) -> None:
        """Initialize TaggingFramework with config, Any]."""
        if isinstance(config, Mapping):
            self.config = TaggingFrameworkConfig(
                rules_path=str(config.get("rules_path", config.get("rules", ""))),
                default_category=str(config.get("default_category", "Miscellaneous")),
            )
        else:
            self.config = config

        self.tagged_files: dict[str, set[str]] = {}
        self.categorized_files: dict[str, set[str]] = {}

    def tag_file(self, file_path: str, tags: Iterable[str]) -> None:
        """Tag a file with the specified tags."""
        self.tagged_files.setdefault(file_path, set()).update(tags)

    def categorize_file(self, file_path: str, category: str) -> None:
        """Assign a file to a human-readable category."""
        self.categorized_files.setdefault(category, set()).add(file_path)

    def process_files(self, files: Iterable[str]) -> None:
        """Process a collection of files, assigning tags and categories."""
        for file_path in files:
            tags = self.get_tags(file_path)
            category = self.get_category(file_path)
            self.tag_file(file_path, tags)
            self.categorize_file(file_path, category)

    def get_tags(self, file_path: str) -> set[str]:
        """Infer a small tag set from the file path metadata."""
        tags: set[str] = set()
        if "README" in file_path:
            tags.add("Documentation")
        if file_path.endswith(".py"):
            tags.add("Python")
        if "config" in file_path:
            tags.add("Configuration")
        return tags

    def get_category(self, file_path: str) -> str:
        """Infer an ordering-friendly category name for reporting."""
        if "test" in file_path:
            return "Testing"
        if "config" in file_path:
            return "Configuration"
        return self.config.default_category

    def summarize(self) -> dict[str, int]:
        """Return counts of tags per file for lightweight reporting."""
        return {path: len(tags) for path, tags in self.tagged_files.items()}

    def display_results(self, *, as_dict: bool = False) -> dict[str, dict[str, list[str]]]:
        """Render the tagging state either via print or dict payload."""
        tag_summary = {path: sorted(tags) for path, tags in self.tagged_files.items()}
        category_summary = {
            category: sorted(paths) for category, paths in self.categorized_files.items()
        }

        if not as_dict:
            logger.info("Tagging results:")
            for path, tags in tag_summary.items():
                logger.info(f"  {path}: {tags}")
            logger.info("Category summary:")
            for category, paths in category_summary.items():
                logger.info(f"  {category}: {paths}")

        return {"tags": tag_summary, "categories": category_summary}


if __name__ == "__main__":
    config = TaggingFrameworkConfig(rules_path="docs/Core/megatag_specifications.md")
    framework = TaggingFramework(config)
    files = ["src/core/ArchitectureWatcher.py", "docs/README.md", "config/launch.json"]
    framework.process_files(files)
    framework.display_results()

"""KILO-FOOLISH Repository Pandas Library.

Provides a DataFrame-based interface for repository structure,
metadata, tagging, and agent/LLM interaction.

OmniTag/MegaTag compatible. Integrates with .snapshots for
versioned context.
"""

import os
from pathlib import Path
from typing import Any

import pandas as pd


class RepositoryPandasLibrary:
    """DataFrame-powered repository explorer and interaction layer."""

    def __init__(self, root: str = ".", snapshots_dir: str = ".snapshots") -> None:
        """Initialize RepositoryPandasLibrary with root, snapshots_dir."""
        self.root = Path(root)
        self.snapshots_dir = Path(snapshots_dir)
        self.df = self._scan_repository()
        self.tags: dict[str, list[str]] = {}  # {filepath: [tags]}
        self.comments: dict[str, list[str]] = {}  # {filepath: [comments]}
        self.snapshots = self._load_snapshots()

    def _scan_repository(self) -> pd.DataFrame:
        """Scan repository and build DataFrame of files and metadata."""
        files: list[Any] = []
        for dirpath, _, filenames in os.walk(self.root):
            for fname in filenames:
                fpath = Path(dirpath) / fname
                files.append(
                    {
                        "path": str(fpath.relative_to(self.root)),
                        "name": fname,
                        "ext": fpath.suffix,
                        "size": fpath.stat().st_size,
                        "modified": fpath.stat().st_mtime,
                        "tags": [],
                        "comments": [],
                    }
                )
        return pd.DataFrame(files)

    def _load_snapshots(self) -> pd.DataFrame:
        """Load .snapshots metadata into DataFrame."""
        snap_files = list(self.snapshots_dir.glob("*.md")) + list(self.snapshots_dir.glob("*.json"))
        snap_data: list[Any] = []
        for snap in snap_files:
            snap_data.append(
                {
                    "snapshot": snap.name,
                    "path": str(snap),
                    "size": snap.stat().st_size,
                    "type": snap.suffix,
                }
            )
        return pd.DataFrame(snap_data)

    def tag_file(self, filepath: str, tag: str) -> None:
        """Assign an OmniTag/MegaTag to a file."""
        self.tags.setdefault(filepath, []).append(tag)
        idx = self.df[self.df["path"] == filepath].index
        if len(idx) > 0:
            self.df.at[idx[0], "tags"] = self.tags[filepath]

    def comment_file(self, filepath: str, comment: str) -> None:
        """Add a comment to a file."""
        self.comments.setdefault(filepath, []).append(comment)
        idx = self.df[self.df["path"] == filepath].index
        if len(idx) > 0:
            self.df.at[idx[0], "comments"] = self.comments[filepath]

    def get_file_info(self, filepath: str) -> dict[str, Any]:
        """Get metadata, tags, and comments for a file."""
        row = self.df[self.df["path"] == filepath]
        if not row.empty:
            result: dict[str, Any] = row.iloc[0].to_dict()
            return result
        return {}

    def search(self, query: str, by: str = "name") -> pd.DataFrame:
        """Search files by name, tag, or comment."""
        if by == "name":
            return self.df[self.df["name"].str.contains(query, case=False)]
        if by == "tag":
            return self.df[self.df["tags"].apply(lambda tags: query in tags if tags else False)]
        if by == "comment":
            return self.df[
                self.df["comments"].apply(lambda comments: query in comments if comments else False)
            ]
        return pd.DataFrame()

    def snapshot_summary(self) -> pd.DataFrame:
        """Return summary of .snapshots for LLM/Copilot context."""
        return self.snapshots

    def to_json(self, path: str | None = None) -> list[dict[str, Any]]:
        """Export repository DataFrame to JSON."""
        data: list[dict[str, Any]] = self.df.to_dict(orient="records")
        if path:
            with open(path, "w") as f:
                import json

                json.dump(data, f, indent=2)
        return data

    # Integration hooks for ChatDev/Ollama/Copilot
    def get_context_for_agent(self, agent_name: str, file_query: str) -> dict[str, Any]:
        """Provide context for agent/LLM based on file query."""
        results = self.search(file_query)
        return {
            "agent": agent_name,
            "results": results.to_dict(orient="records"),
            "tags": self.tags.get(file_query, []),
            "comments": self.comments.get(file_query, []),
        }


# Example usage
if __name__ == "__main__":
    repo_lib = RepositoryPandasLibrary(root=".")
    AI_INTERMEDIARY_PATH = "src/core/ai_intermediary.py"
    repo_lib.tag_file(AI_INTERMEDIARY_PATH, "AI")
    repo_lib.comment_file(AI_INTERMEDIARY_PATH, "Handles cognitive bridge logic.")

    # Basic validation tests
    # 1. Verify search by name returns expected file
    search_results = repo_lib.search("Repository-Pandas-Library.py")
    # 2. Export repository metadata to JSON
    export_path = "repo_structure_export.json"
    repo_lib.to_json(export_path)
    # 3. Display snapshot summary head

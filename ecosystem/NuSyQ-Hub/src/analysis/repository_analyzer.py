"""Minimal stub for RepositoryCompendium to enable Interactive Context Browser.

OmniTag: [context_analysis, repository_compendium, stub]
MegaTag: [INTEGRATION, CONTEXT_PROPAGATION].
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class RepositoryCompendium:
    def __init__(self, repo_path) -> None:
        """Initialize RepositoryCompendium with repo_path."""
        self.repo_path = Path(repo_path)

    def analyze_repository(self) -> dict[str, Any]:
        """Analyze the repository and return metrics dataframes.

        metrics, files, functions, classes, imports, structure.
        """
        import ast

        file_records: list[Any] = []
        func_records: list[Any] = []
        class_records: list[Any] = []
        import_records: list[Any] = []
        dir_levels: list[Any] = []
        total_size = 0.0
        total_lines = 0

        for path in self.repo_path.rglob("*"):
            if path.is_file():
                rel = path.relative_to(self.repo_path)
                size = path.stat().st_size / 1024.0
                total_size += size
                try:
                    with open(path, encoding="utf-8") as f:
                        lines = f.readlines()
                except (FileNotFoundError, UnicodeDecodeError, OSError):
                    lines = []
                line_count = len(lines)
                total_lines += line_count
                file_records.append(
                    {
                        "file_path": str(rel),
                        "file_type": path.suffix.lstrip("."),
                        "size_kb": round(size, 2),
                        "line_count": line_count,
                        "modified_time": path.stat().st_mtime,
                    }
                )
                dir_levels.append(len(rel.parts) - 1)

                if path.suffix == ".py":
                    try:
                        tree = ast.parse("".join(lines))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                func_records.append(
                                    {
                                        "function_name": node.name,
                                        "file_path": str(rel),
                                        "line_count": len(node.body),
                                    }
                                )
                            elif isinstance(node, ast.ClassDef):
                                class_records.append(
                                    {
                                        "class_name": node.name,
                                        "file_path": str(rel),
                                        "method_count": sum(
                                            isinstance(n, ast.FunctionDef) for n in node.body
                                        ),
                                    }
                                )
                        for node in tree.body:
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    import_records.append(
                                        {
                                            "module": alias.name,
                                            "is_standard_library": True,
                                        }
                                    )
                            elif isinstance(node, ast.ImportFrom):
                                import_records.append(
                                    {
                                        "module": node.module or "",
                                        "is_standard_library": True,
                                    }
                                )
                    except SyntaxError:
                        logger.debug("Suppressed SyntaxError", exc_info=True)

        metrics = pd.DataFrame(
            [
                {
                    "total_files": len(file_records),
                    "python_files": sum(1 for f in file_records if f["file_type"] == "py"),
                    "total_lines": total_lines,
                    "total_functions": len(func_records),
                    "total_size_kb": round(total_size, 2),
                    "total_classes": len(class_records),
                    "avg_lines_per_function": (
                        round(
                            sum(f["line_count"] for f in func_records) / len(func_records),
                            2,
                        )
                        if func_records
                        else 0
                    ),
                    "deepest_directory_level": max(dir_levels) if dir_levels else 0,
                }
            ]
        )

        files_df = pd.DataFrame(file_records)
        functions_df = pd.DataFrame(func_records)
        classes_df = pd.DataFrame(class_records)
        imports_df = pd.DataFrame(import_records)
        # generate directory structure counts
        structure_counts: dict[str, Any] = {}
        for rec in file_records:
            dir_name = rec["file_path"].split("/")[0]
            structure_counts[dir_name] = structure_counts.get(dir_name, 0) + 1
        structure_df = pd.DataFrame(
            [{"directory": d, "file_count": c} for d, c in structure_counts.items()]
        )

        return {
            "metrics": metrics,
            "files": files_df,
            "functions": functions_df,
            "classes": classes_df,
            "imports": imports_df,
            "structure": structure_df,
        }

    def export_context_package(self, output_name: str = "context_package") -> str:
        """Package the repository into a zip archive and return its path."""
        import shutil

        base_name = str(self.repo_path / output_name)
        return shutil.make_archive(base_name, "zip", root_dir=str(self.repo_path))

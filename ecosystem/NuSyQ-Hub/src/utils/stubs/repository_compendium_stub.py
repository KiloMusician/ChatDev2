"""RepositoryCompendium stub - centralized under utils/stubs."""

# mypy: ignore-errors

import ast
import datetime
import logging
from pathlib import Path
from typing import Any

import pandas as pd


class RepositoryCompendium:
    """RepositoryCompendium performs static analysis of a Python repository.

    Extracts metrics, functions, classes, and imports.
    """

    def __init__(self, repo_path: str) -> None:
        """Initialize with path to repository."""
        self.repo_path = Path(repo_path)
        logging.basicConfig(level=logging.INFO)

    def _analyze_file(self, fpath: Path, repo_path: Path) -> dict[str, Any]:
        """Analyze a single file and return file info and lines."""
        try:
            size_kb = fpath.stat().st_size / 1024
            mtime = datetime.datetime.fromtimestamp(fpath.stat().st_mtime).strftime("%Y-%m-%d")
        except Exception as e:
            logging.warning(f"Could not stat file {fpath}: {e}")
            size_kb = 0
            mtime = ""
        try:
            with open(fpath, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            logging.warning(f"Could not read file {fpath}: {e}")
            lines: list[Any] = []
        file_type = "python" if fpath.suffix.lower() == ".py" else fpath.suffix.lstrip(".")
        return {
            "file_path": str(fpath.relative_to(repo_path)),
            "file_type": file_type,
            "size_kb": round(size_kb, 2),
            "line_count": len(lines),
            "modified_time": mtime,
        }, lines

    def _analyze_python_ast(
        self, lines, fpath: Path, repo_path: Path
    ) -> tuple[list[Any], list[Any], set[Any], list[Any]]:
        """Analyze Python AST for functions, classes, and imports.

        Returns extracted data and metrics.
        """
        function_data: list[Any] = []
        class_data: list[Any] = []
        import_data = set()
        function_complexities: list[Any] = []
        try:
            tree = ast.parse("".join(lines), filename=str(fpath))
            function_data, function_complexities = self._extract_functions(tree, fpath, repo_path)
            class_data = self._extract_classes(tree, fpath, repo_path)
            import_data = self._extract_imports(tree)
        except Exception as e:
            logging.warning(f"AST parse failed for {fpath}: {e}")
        return function_data, class_data, import_data, function_complexities

    def _extract_functions(self, tree, fpath: Path, repo_path: Path) -> tuple[list[Any], list[Any]]:
        """Extract function definitions, docstrings, decorators.

        Also extract cyclomatic complexity from AST.
        """
        function_data: list[Any] = []
        function_complexities: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = (
                    sum(
                        isinstance(
                            n,
                            (
                                ast.If,
                                ast.For,
                                ast.While,
                                ast.With,
                                ast.Try,
                                ast.ExceptHandler,
                            ),
                        )
                        for n in ast.walk(node)
                    )
                    + 1
                )
                function_complexities.append(complexity)
                decorators = [
                    d.id if isinstance(d, ast.Name) else ast.dump(d) for d in node.decorator_list
                ]
                docstring = ast.get_docstring(node)
                function_data.append(
                    {
                        "function_name": node.name,
                        "file_path": str(fpath.relative_to(repo_path)),
                        "complexity": complexity,
                        "parameter_count": len(node.args.args),
                        "decorators": decorators,
                        "docstring": docstring,
                        "lineno": getattr(node, "lineno", None),
                    }
                )
        return function_data, function_complexities

    def _extract_classes(self, tree, fpath: Path, repo_path: Path) -> list[Any]:
        """Extract class definitions, base classes, docstrings.

        Also extract method counts from AST.
        """
        class_data: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                base_classes = [
                    b.id if isinstance(b, ast.Name) else ast.dump(b) for b in node.bases
                ]
                docstring = ast.get_docstring(node)
                class_data.append(
                    {
                        "class_name": node.name,
                        "file_path": str(fpath.relative_to(repo_path)),
                        "method_count": method_count,
                        "base_classes": base_classes,
                        "docstring": docstring,
                        "lineno": getattr(node, "lineno", None),
                    }
                )
        return class_data

    def _extract_imports(self, tree) -> set[Any]:
        """Extract import statements from AST, including stdlib detection."""
        import_data = set()
        std_libs = {"os", "sys", "datetime", "json", "re", "ast"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                import_data.update(self._handle_import_node(node, std_libs))
            elif isinstance(node, ast.ImportFrom):
                import_data.update(self._handle_importfrom_node(node, std_libs))
        return import_data

    def _handle_import_node(self, node, std_libs) -> set[Any]:
        result = set()
        for alias in node.names:
            result.add((alias.name, alias.name in std_libs, getattr(alias, "asname", None)))
        return result

    def _handle_importfrom_node(self, node, std_libs) -> set[Any]:
        result = set()
        mod = node.module if node.module else ""
        is_std = mod in std_libs
        for alias in node.names:
            result.add(
                (
                    f"{mod}.{alias.name}" if mod else alias.name,
                    is_std,
                    getattr(alias, "asname", None),
                    node.level,
                )
            )
        return result

    def analyze_repository(self) -> dict[str, Any]:
        """Analyze the repository and return comprehensive metrics.

        Returns:
            dict: Dictionary with 'metrics', 'files', 'functions',
                'classes', 'imports', 'structure' as DataFrames.
        """
        import os
        from collections import defaultdict

        repo_path = self.repo_path
        file_data: list[Any] = []
        function_data: list[Any] = []
        class_data: list[Any] = []
        import_data = set()
        structure_data: dict[str, int] = defaultdict(int)
        total_lines = 0
        total_size = 0
        function_complexities: list[Any] = []
        max_depth = 0

        for root, _dirs, files in os.walk(repo_path):
            rel_dir = os.path.relpath(root, repo_path)
            depth = rel_dir.count(os.sep)
            if rel_dir != ".":
                max_depth = max(max_depth, depth)
            structure_data[rel_dir] += len(files)
            for fname in files:
                fpath = Path(root) / fname
                file_info, lines = self._analyze_file(fpath, repo_path)
                file_data.append(file_info)
                total_lines += file_info["line_count"]
                total_size += file_info["size_kb"]
                if file_info["file_type"] == "python":
                    fdata, cdata, idata, fcomplex = self._analyze_python_ast(
                        lines, fpath, repo_path
                    )
                    function_data.extend(fdata)
                    class_data.extend(cdata)
                    import_data.update(idata)
                    function_complexities.extend(fcomplex)

        metrics = pd.DataFrame(
            [
                {
                    "total_files": len(file_data),
                    "python_files": sum(1 for f in file_data if f["file_type"] == "python"),
                    "total_lines": total_lines,
                    "total_functions": len(function_data),
                    "total_size_kb": round(total_size, 2),
                    "total_classes": len(class_data),
                    "avg_function_complexity": (
                        round(sum(function_complexities) / len(function_complexities), 2)
                        if function_complexities
                        else 0
                    ),
                    "deepest_directory_level": max_depth,
                    "docstring_coverage": (
                        round(
                            100
                            * sum(1 for f in function_data if f["docstring"])
                            / len(function_data),
                            1,
                        )
                        if function_data
                        else 0
                    ),
                }
            ]
        )
        files = pd.DataFrame(file_data)
        functions = pd.DataFrame(function_data)
        classes = pd.DataFrame(class_data)
        imports = pd.DataFrame(
            [{"module": mod, "is_standard_library": is_std} for mod, is_std, *_ in import_data]
        )
        structure = pd.DataFrame(
            [{"directory": k, "file_count": v} for k, v in structure_data.items()]
        )
        return {
            "metrics": metrics,
            "files": files,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "structure": structure,
        }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run RepositoryCompendium stub analysis")
    parser.add_argument(
        "--root",
        "-r",
        type=str,
        default=".",
        help="Repository root to analyze (default: .)",
    )
    parser.add_argument(
        "--out-json",
        "-o",
        type=str,
        default="repo_compendium_summary.json",
        help="Path to write summary JSON",
    )
    parser.add_argument(
        "--csv-dir",
        type=str,
        default=None,
        help="Optional directory to export CSVs for detailed tables",
    )
    args = parser.parse_args()

    comp = RepositoryCompendium(args.root)
    result = comp.analyze_repository()

    # Build a compact summary JSON
    summary = {
        "root": str(Path(args.root).resolve()),
        "metrics": (
            result["metrics"].to_dict(orient="records")[0] if not result["metrics"].empty else {}
        ),
        "counts": {
            "files": len(result["files"]) if hasattr(result["files"], "__len__") else 0,
            "functions": (
                len(result["functions"]) if hasattr(result["functions"], "__len__") else 0
            ),
            "classes": (len(result["classes"]) if hasattr(result["classes"], "__len__") else 0),
            "imports": (len(result["imports"]) if hasattr(result["imports"], "__len__") else 0),
            "structure_entries": (
                len(result["structure"]) if hasattr(result["structure"], "__len__") else 0
            ),
        },
    }

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if args.csv_dir:
        csv_dir = Path(args.csv_dir)
        csv_dir.mkdir(parents=True, exist_ok=True)
        try:
            result["files"].to_csv(csv_dir / "files.csv", index=False)
            result["functions"].to_csv(csv_dir / "functions.csv", index=False)
            result["classes"].to_csv(csv_dir / "classes.csv", index=False)
            result["imports"].to_csv(csv_dir / "imports.csv", index=False)
            result["structure"].to_csv(csv_dir / "structure.csv", index=False)
        except Exception as e:
            logging.warning(f"CSV export failed: {e}")

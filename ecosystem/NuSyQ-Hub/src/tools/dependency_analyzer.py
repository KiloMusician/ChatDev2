#!/usr/bin/env python3
"""🔍 Multi-Repository Dependency Analyzer.

Analyzes dependencies across all 3 NuSyQ repos (Hub, SimulatedVerse, Root)
Identifies critical files, circular dependencies, orphaned modules
Outputs to Mermaid, GraphViz, and JSON formats.

Terminal Routing: 🤖 Agents
"""

from __future__ import annotations

import ast
import json
import logging
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import chain, islice
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    from datetime import UTC
except ImportError:  # pragma: no cover - Python 3.10
    UTC = timezone.utc  # noqa: UP017

try:
    import networkx as nx
except ImportError:  # pragma: no cover - optional dependency fallback
    nx = None

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a source file."""

    path: str
    repo: str  # 'hub', 'simverse', 'nusyq'
    language: str  # 'python', 'typescript', 'javascript'
    imports: set[str] = field(default_factory=set)
    dependents: set[str] = field(default_factory=set)
    lines_of_code: int = 0
    complexity: int = 0  # Cyclomatic complexity estimate
    is_critical: bool = False
    fan_in: int = 0  # Number of files depending on this
    fan_out: int = 0  # Number of files this depends on


class DependencyAnalyzer:
    """Analyzes dependencies across Python and JavaScript/TypeScript files."""

    def __init__(self, repos: dict[str, Path] | None = None, max_files_per_repo: int | None = None):
        """Initialize DependencyAnalyzer."""
        self.files: dict[str, FileInfo] = {}
        self.repos = repos or {
            "hub": Path("c:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub\\src"),
            "simverse": Path("c:\\Users\\keath\\Desktop\\SimulatedVerse\\SimulatedVerse\\src"),
            "nusyq": Path("c:\\Users\\keath\\NuSyQ"),
        }
        self.max_files_per_repo = max_files_per_repo
        self.repo_scan_counts: dict[str, int] = {}
        self.circular_deps: list[list[str]] = []

    def emit_route(self, channel: str, emoji: str) -> None:
        """Emit terminal routing hint."""
        print(f"[ROUTE {channel}] {emoji}")

    def analyze_all(self) -> None:
        """Main analysis entry point."""
        self.emit_route("AGENTS", "🤖")
        print("\n" + "=" * 70)
        print("🔍 Multi-Repository Dependency Analysis")
        print("=" * 70)

        for repo_name, repo_path in self.repos.items():
            if repo_path.exists():
                print(f"\n📦 Analyzing {repo_name.upper()}...")
                self._analyze_repo(repo_name, repo_path)
            else:
                print(f"⚠️  Skipped {repo_name}: path not found")

        # Post-processing
        self._identify_critical_files()
        self._find_circular_dependencies()
        self._calculate_metrics()

        print("\n" + "=" * 70)
        print("✅ Analysis Complete")
        print(f"   Files scanned: {len(self.files)}")
        print(f"   Circular dependencies: {len(self.circular_deps)}")
        print("=" * 70)

        try:
            from src.system.agent_awareness import emit as _emit

            _lvl = "WARNING" if self.circular_deps else "INFO"
            _emit(
                "system",
                f"Dep analysis: files={len(self.files)} circular={len(self.circular_deps)} repos={len(self.repos)}",
                level=_lvl,
                source="dependency_analyzer",
            )
        except Exception:
            pass

    def _analyze_repo(self, repo_name: str, repo_path: Path) -> None:
        """Analyze a single repository."""
        scanned = 0

        def _limit_reached() -> bool:
            return self.max_files_per_repo is not None and scanned >= self.max_files_per_repo

        # Scan Python files
        if self.max_files_per_repo is None:
            python_files = list(self._iter_repo_files(repo_path, ["*.py"]))
            print(f"   Python files: {len(python_files)}")
        else:
            python_files = self._iter_repo_files(repo_path, ["*.py"])
            print(f"   Python files: streaming (cap {self.max_files_per_repo})")
        for py_file in python_files:
            if _limit_reached():
                break
            if self._should_skip_file(py_file):
                continue
            self._analyze_python_file(py_file, repo_name)
            scanned += 1

        # Scan TypeScript/JavaScript files
        if self.max_files_per_repo is None:
            ts_files = list(self._iter_repo_files(repo_path, ["*.ts", "*.tsx"]))
            js_files = list(self._iter_repo_files(repo_path, ["*.js", "*.jsx"]))
            print(f"   TypeScript files: {len(ts_files)}")
            print(f"   JavaScript files: {len(js_files)}")
            ts_js_iter = ts_files + js_files
        else:
            print(f"   TypeScript files: streaming (cap {self.max_files_per_repo})")
            print(f"   JavaScript files: streaming (cap {self.max_files_per_repo})")
            ts_js_iter = chain(
                self._iter_repo_files(repo_path, ["*.ts"]),
                self._iter_repo_files(repo_path, ["*.tsx"]),
                self._iter_repo_files(repo_path, ["*.js"]),
                self._iter_repo_files(repo_path, ["*.jsx"]),
            )

        for ts_file in ts_js_iter:
            if _limit_reached():
                break
            if self._should_skip_file(ts_file):
                continue
            lang = "typescript" if ts_file.suffix in [".ts", ".tsx"] else "javascript"
            self._analyze_ts_file(ts_file, repo_name, lang)
            scanned += 1

        self.repo_scan_counts[repo_name] = scanned

    def _iter_repo_files(self, repo_path: Path, patterns: list[str]):
        """Yield repo files, preferring ripgrep for speed on large workspaces."""
        rg_path = shutil.which("rg")
        if rg_path:
            cmd = [rg_path, "--files", str(repo_path)]
            for pattern in patterns:
                cmd.extend(["-g", pattern])
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    check=False,
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if line.strip():
                            yield Path(line.strip())
                    return
            except OSError:
                pass

        for pattern in patterns:
            yield from repo_path.rglob(pattern)

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            ".venv",
            "__pycache__",
            "node_modules",
            ".git",
            "dist",
            "build",
            "coverage",
            ".next",
            ".pytest_cache",
            "*.test.",
            "*.spec.",
            ".min.js",
        ]
        path_str = str(file_path).lower()
        return any(pattern.lower() in path_str for pattern in skip_patterns)

    def _analyze_python_file(self, file_path: Path, repo_name: str) -> None:
        """Analyze a Python file for dependencies."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)

            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])

            relative_path = file_path.relative_to(file_path.parent.parent.parent)
            file_info = FileInfo(
                path=str(relative_path),
                repo=repo_name,
                language="python",
                imports=imports,
                lines_of_code=len(content.split("\n")),
                complexity=self._estimate_complexity(tree),
            )
            self.files[str(relative_path)] = file_info

        except SyntaxError as e:
            print(f"   ⚠️  Error analyzing {file_path.name}: {e}")

    def _analyze_ts_file(self, file_path: Path, repo_name: str, language: str) -> None:
        """Analyze a TypeScript/JavaScript file for dependencies."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            imports = set()

            # Match import statements
            import_pattern = r"(?:import|require)\s+(?:.*from\s+)?['\"]([^'\"]+)['\"]"
            for match in re.finditer(import_pattern, content):
                module = match.group(1).split("/")[0]
                if not module.startswith("."):
                    imports.add(module)

            relative_path = file_path.relative_to(file_path.parent.parent.parent)
            file_info = FileInfo(
                path=str(relative_path),
                repo=repo_name,
                language=language,
                imports=imports,
                lines_of_code=len(content.split("\n")),
                complexity=self._estimate_complexity_ts(content),
            )
            self.files[str(relative_path)] = file_info

        except Exception as e:
            print(f"   ⚠️  Error analyzing {file_path.name}: {e}")

    def _estimate_complexity(self, tree: ast.AST) -> int:
        """Estimate cyclomatic complexity of Python code."""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def _estimate_complexity_ts(self, content: str) -> int:
        """Estimate cyclomatic complexity of TypeScript/JavaScript code."""
        complexity = 1
        complexity += len(re.findall(r"\b(if|while|for|catch|case)\b", content))
        complexity += len(re.findall(r"(\?\s*:|\|\||\&\&)", content))
        return complexity

    def _identify_critical_files(self) -> None:
        """Identify critical files based on dependency metrics."""
        # Calculate fan-in/fan-out
        for file_path, file_info in self.files.items():
            # Count dependents (fan-in)
            file_info.fan_in = sum(
                1 for other in self.files.values() if any(file_path in imp for imp in other.imports)
            )
            # Fan-out already captured in imports
            file_info.fan_out = len(file_info.imports)

            # Critical if: high fan-in, high fan-out, high complexity
            score = (
                (file_info.fan_in * 2) + (file_info.fan_out * 1.5) + (file_info.complexity * 0.5)
            )
            file_info.is_critical = score > 10

    def _find_circular_dependencies(
        self, visited: set[str] | None = None, path: list[str] | None = None
    ) -> None:
        """Find circular dependencies using DFS."""
        if visited is None:
            visited = set()
            path = []

        for file_path, file_info in self.files.items():
            if file_path in visited:
                continue

            visited.add(file_path)
            if path is not None:
                path.append(file_path)

            for imp in file_info.imports:
                # Try to find matching file in repo
                matching_files = [f for f in self.files if imp in f]
                for match in matching_files:
                    if path is not None and match in path:
                        cycle = [*path[path.index(match) :], match]
                        if cycle not in self.circular_deps:
                            self.circular_deps.append(cycle)
                    else:
                        new_path = ([*path, match]) if path is not None else [match]
                        self._find_circular_dependencies(visited, new_path)

            if path is not None and path:
                path.pop()

    def _calculate_metrics(self) -> None:
        """Calculate aggregate metrics."""
        total_loc = sum(f.lines_of_code for f in self.files.values())
        avg_complexity = (
            sum(f.complexity for f in self.files.values()) / len(self.files) if self.files else 0
        )
        critical_count = sum(1 for f in self.files.values() if f.is_critical)

        # User-facing CLI output — intentional print() for terminal display
        print("\n📊 Metrics:")
        print(f"   Total lines of code: {total_loc:,}")
        print(f"   Average complexity: {avg_complexity:.1f}")
        print(f"   Critical files: {critical_count}")

    def export_mermaid(self, output_path: Path) -> None:
        """Export dependency graph as Mermaid diagram."""
        print(f"\n📝 Exporting Mermaid diagram to {output_path.name}...")

        lines = ["graph TD", ""]

        # Add nodes
        for file_path, file_info in self.files.items():
            emoji = "🔴" if file_info.is_critical else "🔵"
            label = Path(file_path).stem
            lines.append(f'    {label}["{emoji} {label}<br/>({file_info.repo})"]')

        lines.append("")

        # Add edges for dependencies
        edge_count = 0
        for file_path, file_info in self.files.items():
            for imp in file_info.imports:
                for other_path in self.files:
                    if imp in other_path and edge_count < 50:  # Limit to prevent huge diagram
                        source = Path(file_path).stem
                        target = Path(other_path).stem
                        lines.append(f"    {source} -->|imports| {target}")
                        edge_count += 1

        output_path.write_text("\n".join(lines))
        print("✅ Mermaid diagram created")

    def export_json(self, output_path: Path) -> None:
        """Export analysis results as JSON."""
        print(f"\n📊 Exporting JSON report to {output_path.name}...")

        data = {
            "summary": {
                "total_files": len(self.files),
                "total_lines": sum(f.lines_of_code for f in self.files.values()),
                "critical_files": sum(1 for f in self.files.values() if f.is_critical),
                "circular_dependencies": len(self.circular_deps),
            },
            "critical_files": [
                {
                    "path": path,
                    "repo": info.repo,
                    "fan_in": info.fan_in,
                    "fan_out": info.fan_out,
                    "complexity": info.complexity,
                    "loc": info.lines_of_code,
                }
                for path, info in sorted(
                    self.files.items(),
                    key=lambda x: x[1].fan_in,
                    reverse=True,
                )[:20]
            ],
            "circular_dependencies": self.circular_deps,
            "graph_learning": self.generate_graph_learning_report(),
        }

        output_path.write_text(json.dumps(data, indent=2))
        print("✅ JSON report created")

    def _iter_internal_dependency_edges(self) -> list[tuple[str, str, str]]:
        """Resolve internal file-to-file import edges for graph analysis."""
        edges: list[tuple[str, str, str]] = []
        seen: set[tuple[str, str, str]] = set()

        for file_path, file_info in self.files.items():
            for imported_name in sorted(file_info.imports):
                for other_path in self.files:
                    if other_path == file_path or imported_name not in other_path:
                        continue
                    edge = (file_path, other_path, imported_name)
                    if edge in seen:
                        continue
                    seen.add(edge)
                    edges.append(edge)

        return edges

    def build_import_graph(self) -> Any:
        """Build an internal dependency graph from scanned files."""
        edges = self._iter_internal_dependency_edges()
        if nx is None:
            return {
                "nodes": sorted(self.files.keys()),
                "edges": [
                    {"source": source, "target": target, "import_name": imported_name}
                    for source, target, imported_name in edges
                ],
            }

        graph = nx.DiGraph()
        for file_path, file_info in self.files.items():
            graph.add_node(
                file_path,
                repo=file_info.repo,
                language=file_info.language,
                complexity=file_info.complexity,
                fan_in=file_info.fan_in,
                fan_out=file_info.fan_out,
            )

        for source, target, imported_name in edges:
            graph.add_edge(source, target, import_name=imported_name)

        return graph

    def generate_graph_learning_report(self, top_k: int = 10) -> dict[str, Any]:
        """Generate graph-based impact and topology signals from dependency data."""
        self._identify_critical_files()
        graph = self.build_import_graph()
        repo_breakdown = Counter(info.repo for info in self.files.values())
        top_k = max(1, top_k)

        if nx is None:
            self.circular_deps = []
            if len(self.files) <= 25:
                self._find_circular_dependencies()
            impact_nodes = sorted(
                self.files.items(),
                key=lambda item: (item[1].fan_in * 2) + item[1].fan_out + item[1].complexity,
                reverse=True,
            )[:top_k]
            return {
                "generated_at": datetime.now(UTC).isoformat(),
                "status": "ok" if self.files else "empty",
                "backend": "builtin",
                "summary": {
                    "node_count": len(self.files),
                    "edge_count": len(graph["edges"]),
                    "scanned_file_count": sum(self.repo_scan_counts.values()),
                    "critical_file_count": sum(
                        1 for info in self.files.values() if info.is_critical
                    ),
                    "cycle_count": len(self.circular_deps),
                    "repo_breakdown": dict(repo_breakdown),
                    "repo_scan_counts": dict(self.repo_scan_counts),
                },
                "top_central_nodes": [
                    {
                        "path": path,
                        "repo": info.repo,
                        "fan_in": info.fan_in,
                        "fan_out": info.fan_out,
                        "complexity": info.complexity,
                    }
                    for path, info in impact_nodes
                ],
                "top_bridge_nodes": [],
                "top_impact_nodes": [
                    {
                        "path": path,
                        "impact_score": round(
                            (info.fan_in * 2) + info.fan_out + info.complexity, 3
                        ),
                        "repo": info.repo,
                    }
                    for path, info in impact_nodes
                ],
                "communities": [],
                "cycles": self.circular_deps[:top_k],
            }

        pagerank = nx.pagerank(graph) if graph.number_of_nodes() else {}
        betweenness = nx.betweenness_centrality(graph) if graph.number_of_nodes() else {}
        components = list(nx.weakly_connected_components(graph)) if graph.number_of_nodes() else []
        cycles = (
            [[*cycle, cycle[0]] for cycle in islice(nx.simple_cycles(graph), top_k)]
            if graph.number_of_nodes()
            else []
        )
        self.circular_deps = cycles

        def _node_payload(node: str, score: float, metric_name: str) -> dict[str, Any]:
            file_info = self.files[node]
            return {
                "path": node,
                "repo": file_info.repo,
                "fan_in": file_info.fan_in,
                "fan_out": file_info.fan_out,
                "complexity": file_info.complexity,
                metric_name: round(score, 6),
            }

        central_nodes = sorted(
            pagerank.items(),
            key=lambda item: (item[1], self.files[item[0]].fan_in, self.files[item[0]].fan_out),
            reverse=True,
        )[:top_k]
        bridge_nodes = sorted(
            betweenness.items(),
            key=lambda item: (item[1], self.files[item[0]].fan_in, self.files[item[0]].fan_out),
            reverse=True,
        )[:top_k]
        impact_nodes = sorted(
            self.files.items(),
            key=lambda item: (
                (item[1].fan_in * 2.0)
                + item[1].fan_out
                + item[1].complexity
                + (pagerank.get(item[0], 0.0) * 10.0)
            ),
            reverse=True,
        )[:top_k]

        communities = sorted(components, key=len, reverse=True)[:top_k]

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "ok" if self.files else "empty",
            "backend": "networkx",
            "summary": {
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "scanned_file_count": sum(self.repo_scan_counts.values()),
                "critical_file_count": sum(1 for info in self.files.values() if info.is_critical),
                "cycle_count": len(self.circular_deps),
                "community_count": len(components),
                "repo_breakdown": dict(repo_breakdown),
                "repo_scan_counts": dict(self.repo_scan_counts),
            },
            "top_central_nodes": [
                _node_payload(node, score, "pagerank") for node, score in central_nodes
            ],
            "top_bridge_nodes": [
                _node_payload(node, score, "betweenness") for node, score in bridge_nodes
            ],
            "top_impact_nodes": [
                {
                    "path": path,
                    "repo": info.repo,
                    "impact_score": round(
                        (info.fan_in * 2.0)
                        + info.fan_out
                        + info.complexity
                        + (pagerank.get(path, 0.0) * 10.0),
                        6,
                    ),
                }
                for path, info in impact_nodes
            ],
            "communities": [
                {
                    "size": len(component),
                    "sample_nodes": sorted(component)[:5],
                }
                for component in communities
            ],
            "cycles": cycles,
        }

    def export_graph_learning_json(self, output_path: Path, top_k: int = 10) -> dict[str, Any]:
        """Export graph-learning analysis as JSON."""
        print(f"\n🧠 Exporting graph-learning report to {output_path.name}...")
        report = self.generate_graph_learning_report(top_k=top_k)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("✅ Graph-learning report created")
        return report

    def print_critical_files(self) -> None:
        """Print critical files to terminal."""
        critical = sorted(
            [(p, i) for p, i in self.files.items() if i.is_critical],
            key=lambda x: x[1].fan_in,
            reverse=True,
        )

        if critical:
            print("\n🔴 CRITICAL FILES (high impact):")
            print("-" * 70)
            for path, info in critical[:15]:
                print(f"   {path}")
                print(
                    f"      Fan-in: {info.fan_in} | Fan-out: {info.fan_out} | Complexity: {info.complexity}"
                )


def main():
    """Main entry point."""
    analyzer = DependencyAnalyzer()

    # Run analysis
    analyzer.analyze_all()

    # Export results
    output_dir = Path("c:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub\\docs\\dependency-analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer.print_critical_files()
    analyzer.export_json(output_dir / "dependency-analysis.json")
    analyzer.export_mermaid(output_dir / "dependency-graph.mmd")
    analyzer.export_graph_learning_json(output_dir / "dependency-graph-learning.json")

    print(f"\n📂 Analysis saved to: {output_dir}")
    print("💡 View Mermaid diagram in VS Code markdown preview")


if __name__ == "__main__":
    main()

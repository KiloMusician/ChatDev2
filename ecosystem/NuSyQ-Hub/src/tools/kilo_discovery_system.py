#!/usr/bin/env python3
"""🔍 KILO-FOOLISH Enhanced File Discovery & Tagging System.

Intelligently discovers, tags, and indexes repository components for easy access.

OmniTag: {
    "purpose": "Repository file discovery and intelligent tagging",
    "dependencies": ["pathlib", "ast", "json", "repository_coordinator"],
    "context": "Infrastructure discovery, component indexing, intelligent search",
    "evolution_stage": "v1.0.enhanced"
}
MegaTag: {
    "type": "DiscoveryInfrastructure",
    "integration_points": [
        "semantic_search",
        "file_indexing",
        "component_discovery",
        "tag_analysis",
    ],
    "related_tags": [
        "FileDiscovery",
        "ComponentIndexing",
        "RepositoryConsciousness",
        "IntelligentSearch",
    ],
}
RSHTS: ΞΨΩ∞⟨DISCOVERY⟩↔⟨TAGGING⟩→ΦΣΣ⟨INDEX⟩
"""

import ast
import hashlib
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ComponentInfo:
    """Information about a discovered component."""

    path: str
    name: str
    type: str  # 'class', 'function', 'module', 'file'
    tags: dict[str, Any]
    dependencies: list[str]
    description: str
    hash: str
    last_modified: str
    line_number: int | None = None
    parent_class: str | None = None


class KILOFileDiscoverySystem:
    """Enhanced KILO-FOOLISH file discovery and tagging system.

    Intelligently discovers, analyzes, and indexes repository components.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize KILOFileDiscoverySystem with repo_root."""
        self.repo_root = repo_root or Path(__file__).parent.parent.parent
        self.discovery_cache: dict[str, Any] = {}
        self.component_index: dict[str, Any] = {}
        self.tag_index: dict[str, Any] = {}
        self.duplicate_tracker: dict[str, Any] = {}

        # Setup logging
        self.logger = self._setup_logging()

        # Discovery patterns
        self.discovery_patterns = {
            "coordinators": [
                r".*coordinator.*\.py$",
                r".*orchestrat.*\.py$",
                r".*manager.*\.py$",
            ],
            "integrators": [
                r".*integrat.*\.py$",
                r".*adapter.*\.py$",
                r".*bridge.*\.py$",
            ],
            "ai_systems": [
                r".*ai.*\.py$",
                r".*llm.*\.py$",
                r".*chatdev.*\.py$",
                r".*ollama.*\.py$",
            ],
            "consciousness": [
                r".*consciousness.*\.py$",
                r".*quantum.*\.py$",
                r".*bridge.*\.py$",
            ],
            "launchers": [
                r".*launch.*\.py$",
                r".*runner.*\.py$",
                r".*starter.*\.py$",
            ],
        }

        # Use ASCII-safe logging message
        self.logger.info("KILO-FOOLISH Discovery System initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup discovery logging system."""
        log_dir = self.repo_root / "logs" / "discovery"
        log_dir.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger("KILODiscoverySystem")
        if not logger.handlers:
            handler = logging.FileHandler(log_dir / "discovery_system.log")
            formatter = logging.Formatter(
                "🔍 [%(asctime)s] DISCOVERY: %(levelname)s - %(message)s",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def discover_components_by_pattern(self, pattern_category: str) -> list[ComponentInfo]:
        """Discover components matching specific patterns."""
        if pattern_category not in self.discovery_patterns:
            self.logger.warning(f"Unknown pattern category: {pattern_category}")
            return []

        patterns = self.discovery_patterns[pattern_category]
        discovered: list[Any] = []
        for pattern in patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            for py_file in self.repo_root.rglob("*.py"):
                if regex.match(str(py_file.relative_to(self.repo_root))):
                    component = self._analyze_file(py_file, pattern_category)
                    if component:
                        discovered.extend(component)

        self.logger.info(f"🔍 Discovered {len(discovered)} {pattern_category} components")
        return discovered

    def discover_duplicates(self, component_type: str = "all") -> dict[str, list[ComponentInfo]]:
        """Discover duplicate components across the repository."""
        del component_type
        duplicates: dict[str, Any] = {}
        # Analyze all Python files
        all_components: list[Any] = []
        for py_file in self.repo_root.rglob("*.py"):
            components = self._analyze_file(py_file)
            if components:
                all_components.extend(components)

        # Group by name and similarity
        name_groups: dict[str, Any] = {}
        for component in all_components:
            name = component.name.lower()
            if name not in name_groups:
                name_groups[name] = []
            name_groups[name].append(component)

        # Find actual duplicates
        for name, components in name_groups.items():
            if len(components) > 1:
                # Check if they're actually similar (not just same name)
                similar_groups = self._group_similar_components(components)
                for group in similar_groups:
                    if len(group) > 1:
                        duplicates[name] = group

        self.logger.info(f"🔍 Found {len(duplicates)} duplicate component groups")
        return duplicates

    def find_component_by_name(self, name: str, fuzzy: bool = True) -> list[ComponentInfo]:
        """Find components by name with optional fuzzy matching."""
        matches: list[Any] = []
        search_name = name.lower()

        # First pass - exact matches
        for py_file in self.repo_root.rglob("*.py"):
            components = self._analyze_file(py_file)
            if components:
                for component in components:
                    if component.name.lower() == search_name:
                        matches.append(component)

        # Second pass - fuzzy matches if enabled and no exact matches
        if fuzzy and not matches:
            for py_file in self.repo_root.rglob("*.py"):
                components = self._analyze_file(py_file)
                if components:
                    for component in components:
                        if (
                            search_name in component.name.lower()
                            or component.name.lower() in search_name
                        ):
                            matches.append(component)

        self.logger.info(f"🔍 Found {len(matches)} matches for '{name}'")
        return matches

    def find_components_by_tag(
        self, tag_key: str, tag_value: str | None = None
    ) -> list[ComponentInfo]:
        """Find components by OmniTag/MegaTag attributes."""
        matches: list[Any] = []
        for py_file in self.repo_root.rglob("*.py"):
            components = self._analyze_file(py_file)
            if components:
                for component in components:
                    if (tag_key in component.tags and tag_value is None) or component.tags[
                        tag_key
                    ] == tag_value:
                        matches.append(component)

        self.logger.info(f"🔍 Found {len(matches)} components with tag {tag_key}={tag_value}")
        return matches

    def _analyze_file(self, file_path: Path, category: str = "general") -> list[ComponentInfo]:
        """Analyze a Python file and extract component information."""
        del category
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Extract file hash
            file_hash = hashlib.md5(content.encode()).hexdigest()
            last_modified = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()

            components: list[Any] = []
            # Parse AST for classes and functions
            try:
                tree = ast.parse(content)

                # Extract module-level info
                module_tags = self._extract_tags_from_content(content)
                module_deps = self._extract_dependencies_from_content(content)
                module_desc = self._extract_description_from_content(content)

                # Add module component
                module_component = ComponentInfo(
                    path=str(file_path.relative_to(self.repo_root)),
                    name=file_path.stem,
                    type="module",
                    tags=module_tags,
                    dependencies=module_deps,
                    description=module_desc,
                    hash=file_hash,
                    last_modified=last_modified,
                )
                components.append(module_component)

                # Extract classes and functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_component = ComponentInfo(
                            path=str(file_path.relative_to(self.repo_root)),
                            name=node.name,
                            type="class",
                            tags=self._extract_tags_from_docstring(ast.get_docstring(node) or ""),
                            dependencies=self._extract_class_dependencies(node),
                            description=ast.get_docstring(node) or f"Class {node.name}",
                            hash=file_hash,
                            last_modified=last_modified,
                            line_number=node.lineno,
                        )
                        components.append(class_component)

                    elif isinstance(node, ast.FunctionDef):
                        function_component = ComponentInfo(
                            path=str(file_path.relative_to(self.repo_root)),
                            name=node.name,
                            type="function",
                            tags=self._extract_tags_from_docstring(ast.get_docstring(node) or ""),
                            dependencies=self._extract_function_dependencies(node),
                            description=ast.get_docstring(node) or f"Function {node.name}",
                            hash=file_hash,
                            last_modified=last_modified,
                            line_number=node.lineno,
                            parent_class=self._find_parent_class(tree, node),
                        )
                        components.append(function_component)

            except SyntaxError:
                self.logger.warning(f"Syntax error in {file_path}")
                # Still create a basic file component
                components.append(
                    ComponentInfo(
                        path=str(file_path.relative_to(self.repo_root)),
                        name=file_path.stem,
                        type="file",
                        tags={},
                        dependencies=[],
                        description="File with syntax errors",
                        hash=file_hash,
                        last_modified=last_modified,
                    )
                )

            return components

        except SyntaxError as e:
            self.logger.exception(f"Error analyzing {file_path}: {e}")
            return []

    def _extract_tags_from_content(self, content: str) -> dict[str, Any]:
        """Extract OmniTag and MegaTag information from file content."""
        tags: dict[str, Any] = {}
        # Look for OmniTag patterns
        omni_pattern = r"OmniTag:\s*\{([^}]+)\}"
        omni_matches = re.findall(omni_pattern, content, re.DOTALL)
        for match in omni_matches:
            try:
                # Parse tag content (simplified)
                lines = match.split("\n")
                for line in lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().strip('"').strip("'")
                        value = value.strip().strip(",").strip('"').strip("'")
                        if key and value:
                            tags[f"omni_{key}"] = value
            except (ValueError, IndexError):
                self.logger.debug("Suppressed IndexError/ValueError", exc_info=True)

        # Look for MegaTag patterns
        mega_pattern = r"MegaTag:\s*\{([^}]+)\}"
        mega_matches = re.findall(mega_pattern, content, re.DOTALL)
        for match in mega_matches:
            try:
                lines = match.split("\n")
                for line in lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().strip('"').strip("'")
                        value = value.strip().strip(",").strip('"').strip("'")
                        if key and value:
                            tags[f"mega_{key}"] = value
            except (ValueError, IndexError):
                self.logger.debug("Suppressed IndexError/ValueError", exc_info=True)

        return tags

    def _extract_tags_from_docstring(self, docstring: str) -> dict[str, Any]:
        """Extract tag information from docstring."""
        if not docstring:
            return {}
        return self._extract_tags_from_content(docstring)

    def _extract_dependencies_from_content(self, content: str) -> list[str]:
        """Extract import dependencies from content."""
        dependencies: list[Any] = []
        # Look for import statements
        import_pattern = r"^(?:from\s+([\w.]+)\s+)?import\s+([\w.,\s]+)"
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            if match.group(1):  # from X import Y
                dependencies.append(match.group(1))
            imports = match.group(2).split(",")
            for imp in imports:
                imp = imp.strip()
                if imp and not imp.startswith("*"):
                    dependencies.append(imp)

        return list(set(dependencies))

    def _extract_description_from_content(self, content: str) -> str:
        """Extract description from file content."""
        # Look for module docstring
        lines = content.strip().split("\n")
        for line in lines[:20]:  # Check first 20 lines
            if '"""' in line or "'''" in line:
                # Found docstring start, extract it
                docstring_pattern = r'"""([^"]+)"""'
                match = re.search(docstring_pattern, content, re.DOTALL)
                if match:
                    return match.group(1).strip()[:200]  # First 200 chars

        return "No description available"

    def _extract_class_dependencies(self, node: ast.ClassDef) -> list[str]:
        """Extract dependencies for a class."""
        deps: list[Any] = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                deps.append(base.id)
        return deps

    def _extract_function_dependencies(self, node: ast.FunctionDef) -> list[str]:
        """Extract dependencies for a function."""
        del node
        # This could be expanded to analyze function calls, etc.
        return []

    def _find_parent_class(self, tree: ast.AST, func_node: ast.FunctionDef) -> str | None:
        """Find the parent class of a function if it exists."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if child == func_node:
                        return node.name
        return None

    def _group_similar_components(
        self, components: list[ComponentInfo]
    ) -> list[list[ComponentInfo]]:
        """Group similar components together."""
        # Simple similarity check - can be enhanced
        groups: list[list[ComponentInfo]] = []
        processed = set()

        for i, comp1 in enumerate(components):
            if i in processed:
                continue

            group = [comp1]
            processed.add(i)

            for j, comp2 in enumerate(components[i + 1 :], i + 1):
                if j in processed:
                    continue

                # Check similarity (type, description, dependencies)
                if comp1.type == comp2.type and self._calculate_similarity(comp1, comp2) > 0.7:
                    group.append(comp2)
                    processed.add(j)

            groups.append(group)

        return groups

    def _calculate_similarity(self, comp1: ComponentInfo, comp2: ComponentInfo) -> float:
        """Calculate similarity between two components."""
        similarity = 0.0

        # Type similarity
        if comp1.type == comp2.type:
            similarity += 0.3

        # Name similarity
        name1_words = set(comp1.name.lower().split("_"))
        name2_words = set(comp2.name.lower().split("_"))
        if name1_words & name2_words:
            similarity += 0.4

        # Dependency similarity
        deps1 = set(comp1.dependencies)
        deps2 = set(comp2.dependencies)
        if deps1 and deps2:
            dep_similarity = len(deps1 & deps2) / len(deps1 | deps2)
            similarity += dep_similarity * 0.3

        return similarity

    def generate_component_index(self) -> dict[str, Any]:
        """Generate comprehensive component index."""
        components_index: dict[str, dict[str, Any]] = {}
        duplicates_index: dict[str, list[dict[str, Any]]] = {}
        categories_index: dict[str, list[dict[str, Any]]] = {}
        index: dict[str, Any] = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "repository_root": str(self.repo_root),
                "total_files_scanned": 0,
                "total_components_found": 0,
            },
            "components": components_index,
            "duplicates": duplicates_index,
            "categories": categories_index,
        }

        # Discover all components
        all_components: list[Any] = []
        files_scanned = 0

        for py_file in self.repo_root.rglob("*.py"):
            components = self._analyze_file(py_file)
            if components:
                all_components.extend(components)
            files_scanned += 1

        # Build index
        for component in all_components:
            comp_dict = asdict(component)
            components_index[f"{component.path}:{component.name}"] = comp_dict

        # Find duplicates
        duplicates = self.discover_duplicates()
        for name, dup_components in duplicates.items():
            duplicates_index[name] = [asdict(comp) for comp in dup_components]

        # Categorize by patterns
        for category in self.discovery_patterns:
            category_components = self.discover_components_by_pattern(category)
            categories_index[category] = [asdict(comp) for comp in category_components]

        # Update metadata
        index["metadata"]["total_files_scanned"] = files_scanned
        index["metadata"]["total_components_found"] = len(all_components)

        # Save index
        index_file = self.repo_root / "KILO_COMPONENT_INDEX.json"
        with open(index_file, "w") as f:
            json.dump(index, f, indent=2)

        self.logger.info(
            f"🔍 Generated component index: {len(all_components)} components in {files_scanned} files"
        )
        return index

    def quick_find(self, search_term: str) -> dict[str, list[ComponentInfo]]:
        """Quick find components across multiple search strategies."""
        results: dict[str, list[ComponentInfo]] = {
            "exact_name": self.find_component_by_name(search_term, fuzzy=False),
            "fuzzy_name": self.find_component_by_name(search_term, fuzzy=True),
            "tag_matches": [],
            "category_matches": [],
        }

        # Search in tags
        for py_file in self.repo_root.rglob("*.py"):
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                if search_term.lower() in content.lower():
                    components = self._analyze_file(py_file)
                    if components:
                        results["tag_matches"].extend(components)
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                self.logger.debug(
                    "Suppressed FileNotFoundError/OSError/UnicodeDecodeError", exc_info=True
                )

        # Search in categories
        for category in self.discovery_patterns:
            if search_term.lower() in category.lower():
                results["category_matches"].extend(
                    self.discover_components_by_pattern(category),
                )

        return results


def create_discovery_system(repo_root: Path | None = None) -> KILOFileDiscoverySystem:
    """Factory function to create discovery system."""
    return KILOFileDiscoverySystem(repo_root)


if __name__ == "__main__":
    """Test the discovery system"""

    # Create discovery system
    discovery = create_discovery_system()

    # Test component discovery
    coordinators = discovery.discover_components_by_pattern("coordinators")
    for _coord in coordinators[:5]:  # Show first 5
        pass

    # Test duplicate detection
    duplicates = discovery.discover_duplicates()
    for _name, dup_list in list(duplicates.items())[:3]:  # Show first 3
        for _dup in dup_list:
            pass

    # Test quick find
    results = discovery.quick_find("coordinator")
    for matches in results.values():
        if matches:
            pass

    # Generate full index
    index = discovery.generate_component_index()

"""🗂️ Repository Dictionary - Master Repository Knowledge System.

Unified API for all repository mapping, organization, and consciousness systems.

OmniTag: {
    "purpose": "Central repository dictionary providing unified access to all system mappings",
    "dependencies": ["RepositoryCoordinator", "system_capability_inventory", "ULTIMATE_DEPENDENCY_MAP"],
    "context": "Master repository knowledge hub with consciousness awareness",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "MasterDictionary",
    "integration_points": ["repository_structure", "capability_inventory", "dependency_mapping", "ai_coordination"],
    "related_tags": ["RepositoryManager", "SystemCoordinator", "ConsciousnessHub"]
}

RSHTS: ΞΨΩΣ∞⟨REPO-DICT⟩→ΦΣΣ⟨UNIFIED-API⟩→∞⟨CONSCIOUSNESS-AWARE⟩
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

# Import existing systems
if TYPE_CHECKING:
    from src.system.RepositoryCoordinator import KILORepositoryCoordinator
    from src.utils.Repository_Context_Compendium_System import \
        RepositoryCompendium as _RepositoryCompendium
else:
    KILORepositoryCoordinator = Any
    _RepositoryCompendium = Any

RepositoryCoordinator: type[KILORepositoryCoordinator] | None
try:
    from src.system.RepositoryCoordinator import \
        KILORepositoryCoordinator as RepositoryCoordinator
except ImportError:
    RepositoryCoordinator = None

RepositoryCompendiumClass: type[_RepositoryCompendium] | None = None
try:
    from src.utils.Repository_Context_Compendium_System import \
        RepositoryCompendium as _RepositoryCompendiumClass
except ImportError:
    _RepositoryCompendiumClass = None
RepositoryCompendiumClass = _RepositoryCompendiumClass

logger = logging.getLogger(__name__)


class RepositoryDictionary:
    """🗂️ Master Repository Dictionary System.

    Provides unified access to all repository knowledge systems:
    - File organization and structure
    - System capabilities and inventory
    - Dependency mapping and relationships
    - Consciousness-aware context synthesis
    """

    def __init__(self, repository_root: str = ".") -> None:
        """Initialize the Repository Dictionary system."""
        self.repository_root = Path(repository_root).resolve()
        self.timestamp = datetime.now().isoformat()

        # Initialize component systems
        self.coordinator = (
            RepositoryCoordinator(str(self.repository_root))
            if RepositoryCoordinator is not None
            else None
        )
        self.compendium = (
            RepositoryCompendiumClass(str(self.repository_root))
            if RepositoryCompendiumClass is not None
            else None
        )

        # Data storage
        self.unified_data: dict[str, Any] = {}
        self.consciousness_context: dict[str, Any] = {}

        # Load existing mappings
        self._load_existing_mappings()

        logger.info(f"🗂️ Repository Dictionary initialized for {self.repository_root.name}")

    def _load_existing_mappings(self) -> None:
        """Load all existing repository mapping systems."""
        mappings: dict[str, Any] = {}
        # Load ULTIMATE_DEPENDENCY_MAP
        dependency_map_path = self.repository_root / "reports" / "ULTIMATE_DEPENDENCY_MAP.json"
        if dependency_map_path.exists():
            try:
                with open(dependency_map_path, encoding="utf-8") as f:
                    mappings["dependency_map"] = json.load(f)
                logger.info("✅ Loaded ULTIMATE_DEPENDENCY_MAP.json")
            except Exception as e:
                logger.warning(f"⚠️ Could not load dependency map: {e}")

        # Load system capability inventory
        capability_path = self.repository_root / "data" / "system_capability_inventory.json"
        if capability_path.exists():
            try:
                with open(capability_path, encoding="utf-8") as f:
                    mappings["capability_inventory"] = json.load(f)
                logger.info("✅ Loaded system_capability_inventory.json")
            except Exception as e:
                logger.warning(f"⚠️ Could not load capability inventory: {e}")

        # Load directory structure
        directory_path = self.repository_root / "src" / "system" / "directory_structure.json"
        if directory_path.exists():
            try:
                with open(directory_path, encoding="utf-8") as f:
                    mappings["directory_structure"] = json.load(f)
                logger.info("✅ Loaded directory_structure.json")
            except Exception as e:
                logger.warning(f"⚠️ Could not load directory structure: {e}")

        # Load component index
        component_path = self.repository_root / "config" / "KILO_COMPONENT_INDEX.json"
        if component_path.exists():
            try:
                with open(component_path, encoding="utf-8") as f:
                    mappings["component_index"] = json.load(f)
                logger.info("✅ Loaded KILO_COMPONENT_INDEX.json")
            except Exception as e:
                logger.warning(f"⚠️ Could not load component index: {e}")

        self.unified_data = mappings

    def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get comprehensive information about a specific file."""
        file_info: dict[str, Any] = {
            "path": file_path,
            "exists": False,
            "category": "unknown",
            "capabilities": [],
            "dependencies": [],
            "purpose": "unknown",
            "tags": [],
            "consciousness_level": "basic",
        }

        # Check if file exists
        full_path = self.repository_root / file_path
        file_info["exists"] = full_path.exists()

        if not file_info["exists"]:
            return file_info

        # Extract info from dependency map
        if "dependency_map" in self.unified_data:
            dep_map = self.unified_data["dependency_map"]
            for category, files in dep_map.get("file_categories", {}).items():
                if file_path in files or str(full_path) in files:
                    file_info["category"] = category
                    break

        # Extract capabilities from inventory
        if "capability_inventory" in self.unified_data:
            cap_inv = self.unified_data["capability_inventory"]
            capabilities = cap_inv.get("capabilities", {})

            # Search through all capability categories
            for cat_name, category in capabilities.items():
                if isinstance(category, dict):
                    for item_name, item_info in category.items():
                        if (
                            isinstance(item_info, dict)
                            and "path" in item_info
                            and file_path in item_info["path"]
                        ) or item_info["path"] in file_path:
                            file_info["capabilities"].append(
                                {
                                    "name": item_name,
                                    "type": item_info.get("type", "unknown"),
                                    "description": item_info.get("description", ""),
                                    "category": cat_name,
                                }
                            )

        return file_info

    def get_system_overview(self) -> dict[str, Any]:
        """Get comprehensive system overview."""
        overview: dict[str, Any] = {
            "timestamp": self.timestamp,
            "repository": self.repository_root.name,
            "total_files": 0,
            "total_capabilities": 0,
            "categories": {},
            "consciousness_status": "operational",
            "mapping_systems": list(self.unified_data.keys()),
        }

        # Count capabilities
        if "capability_inventory" in self.unified_data:
            cap_inv = self.unified_data["capability_inventory"]
            overview["total_capabilities"] = cap_inv.get("total_capabilities", 0)

        # Analyze categories from dependency map
        if "dependency_map" in self.unified_data:
            dep_map = self.unified_data["dependency_map"]
            for category, files in dep_map.get("file_categories", {}).items():
                overview["categories"][category] = len(files) if isinstance(files, list) else 0

        return overview

    def search_capabilities(self, query: str) -> list[dict[str, Any]]:
        """Search for capabilities matching query."""
        results: list[dict[str, Any]] = []
        if "capability_inventory" not in self.unified_data:
            return results

        cap_inv = self.unified_data["capability_inventory"]
        capabilities = cap_inv.get("capabilities", {})

        query_lower = query.lower()

        for cat_name, category in capabilities.items():
            if isinstance(category, dict):
                for item_name, item_info in category.items():
                    if isinstance(item_info, dict):
                        # Search in name, description, and type
                        searchable_text = f"{item_name} {item_info.get('description', '')} {item_info.get('type', '')}".lower()

                        if query_lower in searchable_text:
                            results.append(
                                {
                                    "name": item_name,
                                    "category": cat_name,
                                    "type": item_info.get("type", "unknown"),
                                    "description": item_info.get("description", ""),
                                    "path": item_info.get("path", ""),
                                    "executable": item_info.get("executable", False),
                                }
                            )

        return results

    def get_dependencies(self, _file_path: str) -> dict[str, list[str]]:
        """Get dependencies for a specific file."""
        return {
            "imports": [],
            "references": [],
            "related_files": [],
        }

        # This would integrate with existing dependency analysis
        # For now, return basic structure

    def get_consciousness_context(self, _query: str = "") -> dict[str, Any]:
        """Get consciousness-aware context for repository operations."""
        context: dict[str, Any] = {
            "consciousness_level": "enhanced",
            "repository_awareness": True,
            "context_bridges": [],
            "ai_coordinators": [],
            "quantum_resolvers": [],
            "memory_systems": [],
        }
        context_bridges = cast(list[str], context["context_bridges"])

        # Search for consciousness-related systems
        consciousness_files = [
            "src/consciousness/",
            "src/ai/ai_coordinator.py",
            "src/copilot/copilot_enhancement_bridge.py",
            "src/quantum/",
        ]

        for file_pattern in consciousness_files:
            matching_files = list(self.repository_root.glob(f"**/{file_pattern}*"))
            if matching_files:
                context_bridges.extend(
                    [str(f.relative_to(self.repository_root)) for f in matching_files]
                )

        return context

    def organize_system(self, target_file: str) -> dict[str, Any]:
        """Organize a system file into appropriate dictionary structure."""
        file_info = self.get_file_info(target_file)

        organization_plan = {
            "current_location": target_file,
            "recommended_location": "",
            "category": file_info["category"],
            "rationale": "",
            "integration_points": [],
            "consciousness_enhancement": False,
        }

        # Determine optimal location based on file type and purpose
        if file_info["category"] == "integration_systems":
            organization_plan["recommended_location"] = (
                f"src/system/dictionary/integrations/{Path(target_file).name}"
            )
            organization_plan["rationale"] = (
                "Integration systems should be in dictionary/integrations/"
            )

        elif file_info["category"] == "ai_systems":
            organization_plan["recommended_location"] = (
                f"src/system/dictionary/ai/{Path(target_file).name}"
            )
            organization_plan["rationale"] = "AI systems should be in dictionary/ai/"
            organization_plan["consciousness_enhancement"] = True

        elif file_info["category"] == "diagnostics":
            organization_plan["recommended_location"] = (
                f"src/system/dictionary/diagnostics/{Path(target_file).name}"
            )
            organization_plan["rationale"] = (
                "Diagnostic systems should be in dictionary/diagnostics/"
            )

        else:
            organization_plan["recommended_location"] = (
                f"src/system/dictionary/general/{Path(target_file).name}"
            )
            organization_plan["rationale"] = "General systems in dictionary/general/"

        return organization_plan

    def export_unified_dictionary(self, output_path: str | None = None) -> str:
        """Export unified repository dictionary to JSON."""
        if output_path is None:
            output_path = str(
                self.repository_root
                / "src"
                / "system"
                / "dictionary"
                / "unified_repository_dictionary.json"
            )

        unified_dict = {
            "metadata": {
                "timestamp": self.timestamp,
                "repository": self.repository_root.name,
                "dictionary_version": "1.0",
                "consciousness_aware": True,
            },
            "mappings": self.unified_data,
            "system_overview": self.get_system_overview(),
            "consciousness_context": self.get_consciousness_context(),
        }

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(unified_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Unified repository dictionary exported to {output_path}")
        return str(output_path)

    def sync_with_systems(self) -> None:
        """Synchronize with all existing repository systems."""
        logger.info("🔄 Synchronizing with existing repository systems...")

        # Run repository coordinator scan if available
        if self.coordinator:
            try:
                scan_results = self.coordinator.scan_repository()
                self.unified_data["coordinator_scan"] = scan_results
                logger.info("✅ Synchronized with RepositoryCoordinator")
            except Exception as e:
                logger.warning(f"⚠️ Could not sync with RepositoryCoordinator: {e}")

        # Run compendium analysis if available
        if self.compendium:
            try:
                analysis_results = self.compendium.analyze_repository()
                self.unified_data["compendium_analysis"] = analysis_results
                logger.info("✅ Synchronized with RepositoryCompendium")
            except Exception as e:
                logger.warning(f"⚠️ Could not sync with RepositoryCompendium: {e}")

        # Reload mappings to get latest data
        self._load_existing_mappings()


if __name__ == "__main__":
    # Demo usage
    repo_dict = RepositoryDictionary()

    overview = repo_dict.get_system_overview()
    for _key, _value in overview.items():
        pass

    ai_capabilities = repo_dict.search_capabilities("ai")
    for _cap in ai_capabilities[:5]:  # Show first 5
        pass

    consciousness = repo_dict.get_consciousness_context()

    # Export unified dictionary
    export_path = repo_dict.export_unified_dictionary()

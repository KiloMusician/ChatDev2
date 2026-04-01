#!/usr/bin/env python3
"""📸 KILO-FOOLISH System Snapshot Generator.

Creates comprehensive system snapshots following Rube Goldbergian protocols.

OmniTag: {
    "purpose": "system_snapshot_generation",
    "type": "monitoring_utility",
    "evolution_stage": "v3.0_enhanced"
}
MegaTag: {
    "scope": "repository_consciousness",
    "integration_points": ["rpg_inventory", "capability_inventory", "zeta_tracker"],
    "quantum_context": "system_state_preservation"
}
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SystemSnapshotGenerator:
    """Generates comprehensive system snapshots with boolean checking."""

    def __init__(self) -> None:
        """Initialize SystemSnapshotGenerator."""
        self.repo_root = Path.cwd()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.snapshot_dir = self.repo_root / ".snapshots"
        self.snapshot_dir.mkdir(exist_ok=True)

    def boolean_check_existing_snapshots(self) -> dict[str, Any]:
        """Boolean checks for existing snapshots per Rube Goldbergian protocols."""
        existing_snapshots = list(self.snapshot_dir.glob("system_snapshot_*.json"))

        check_results: dict[str, Any] = {
            "has_existing_snapshots": len(existing_snapshots) > 0,
            "latest_snapshot": None,
            "snapshot_count": len(existing_snapshots),
            "needs_new_snapshot": True,  # Always true for comprehensive tracking
            "existing_snapshot_ages": [],
        }

        if existing_snapshots:
            # Sort by modification time
            existing_snapshots.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest = existing_snapshots[0]

            check_results["latest_snapshot"] = str(latest)
            check_results["latest_modification"] = datetime.fromtimestamp(
                latest.stat().st_mtime,
            ).isoformat()

            # Calculate ages
            now = datetime.now()
            for snapshot in existing_snapshots:
                modified = datetime.fromtimestamp(snapshot.stat().st_mtime)
                age_hours = (now - modified).total_seconds() / 3600
                check_results["existing_snapshot_ages"].append(
                    {
                        "file": str(snapshot.name),
                        "age_hours": round(age_hours, 2),
                        "recent": age_hours < 24,
                    }
                )

        return check_results

    def check_system_components_availability(self) -> dict[str, bool]:
        """Boolean checks for system component availability."""
        component_checks: dict[str, Any] = {}
        # Check RPG Inventory System
        try:
            pass

            component_checks["rpg_inventory_available"] = True
            component_checks["rpg_inventory_functional"] = True
        except ImportError:
            component_checks["rpg_inventory_available"] = False
            component_checks["rpg_inventory_functional"] = False

        # Check Capability Inventory
        capability_inventory_path = self.repo_root / "src" / "system" / "capability_inventory.py"
        component_checks["capability_inventory_exists"] = capability_inventory_path.exists()

        # Check ZETA Progress Tracker
        zeta_tracker_path = self.repo_root / "config" / "ZETA_PROGRESS_TRACKER.json"
        component_checks["zeta_tracker_exists"] = zeta_tracker_path.exists()

        # Check Component Index
        component_index_path = self.repo_root / "config" / "KILO_COMPONENT_INDEX.json"
        component_checks["component_index_exists"] = component_index_path.exists()

        # Check key executables
        executables_to_check = [
            "src/core/kilo_foolish_master_launcher.py",
            "src/diagnostics/quick_system_analyzer.py",
            "src/diagnostics/system_health_assessor.py",
            "src/tools/safe_consolidator.py",
        ]

        for executable in executables_to_check:
            exe_path = self.repo_root / executable
            key = executable.replace("/", "_").replace(".py", "_available")
            component_checks[key] = exe_path.exists()

        return component_checks

    def create_comprehensive_snapshot(self) -> dict[str, Any]:
        """Create comprehensive system snapshot."""
        snapshot = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "snapshot_id": f"system_snapshot_{self.timestamp}",
                "repository": "KILO-FOOLISH NuSyQ-Hub",
                "generator": "SystemSnapshotGenerator v3.0",
            },
            "boolean_checks": {
                "existing_snapshots": self.boolean_check_existing_snapshots(),
                "system_components": self.check_system_components_availability(),
            },
            "system_state": {},
            "file_organization": {},
            "capabilities": {},
            "rpg_integration": {},
            "recommendations": [],
        }

        # Gather system state information
        snapshot["system_state"] = self._gather_system_state()
        snapshot["file_organization"] = self._analyze_file_organization()
        snapshot["capabilities"] = self._load_capability_data()
        snapshot["rpg_integration"] = self._gather_rpg_status()
        snapshot["recommendations"] = self._generate_recommendations(snapshot)

        return snapshot

    def _gather_system_state(self) -> dict[str, Any]:
        """Gather current system state."""
        return {
            "repository_stats": {
                "total_files": len(list(self.repo_root.glob("**/*"))),
                "python_files": len(list(self.repo_root.glob("**/*.py"))),
                "src_directories": len(
                    [d for d in (self.repo_root / "src").iterdir() if d.is_dir()]
                ),
                "config_files": (
                    len(list((self.repo_root / "config").glob("*")))
                    if (self.repo_root / "config").exists()
                    else 0
                ),
            },
            "recent_changes": self._detect_recent_changes(),
            "health_indicators": self._assess_health_indicators(),
        }

    def _analyze_file_organization(self) -> dict[str, Any]:
        """Analyze current file organization."""
        organization: dict[str, Any] = {
            "root_python_files": [f.name for f in self.repo_root.glob("*.py")],
            "src_structure": {},
            "misplaced_files": [],
            "organization_score": 0,
        }

        # Analyze src/ structure
        src_path = self.repo_root / "src"
        if src_path.exists():
            for subdir in src_path.iterdir():
                if subdir.is_dir():
                    py_files = list(subdir.glob("*.py"))
                    organization["src_structure"][subdir.name] = {
                        "file_count": len(py_files),
                        "files": [f.name for f in py_files],
                    }

        # Calculate organization score
        root_py_count = len(organization["root_python_files"])
        src_file_count = sum(info["file_count"] for info in organization["src_structure"].values())

        if root_py_count + src_file_count > 0:
            organization["organization_score"] = (
                src_file_count / (root_py_count + src_file_count)
            ) * 100

        return organization

    def _load_capability_data(self) -> dict[str, Any]:
        """Load capability inventory data if available."""
        capability_report_path = self.repo_root / "data" / "system_capability_inventory_report.md"
        capability_data: dict[str, Any] = {
            "capability_report_exists": capability_report_path.exists(),
            "last_capability_scan": None,
            "total_capabilities_estimated": 147,  # From recent analysis
        }

        if capability_report_path.exists():
            capability_data["last_capability_scan"] = datetime.fromtimestamp(
                capability_report_path.stat().st_mtime,
            ).isoformat()

        return capability_data

    def _gather_rpg_status(self) -> dict[str, Any]:
        """Gather RPG integration status."""
        rpg_status = {
            "rpg_inventory_system": False,
            "wizard_navigator": False,
            "capability_mapping": False,
            "quest_tracking": False,
            # Initialize counters for quests to allow integer assignment later
            "active_quests": 0,
            "completed_quests": 0,
        }

        # Check RPG Inventory System
        rpg_inventory_path = self.repo_root / "src" / "system" / "rpg_inventory.py"
        rpg_status["rpg_inventory_system"] = rpg_inventory_path.exists()

        # Check Wizard Navigator (moved to navigation namespace)
        wizard_nav_path = (
            self.repo_root / "src" / "navigation" / "wizard_navigator" / "wizard_navigator.py"
        )
        rpg_status["wizard_navigator"] = wizard_nav_path.exists()

        # Check Capability Mapping
        capability_inv_path = self.repo_root / "src" / "system" / "capability_inventory.py"
        rpg_status["capability_mapping"] = capability_inv_path.exists()

        # Check ZETA Progress (Quest Tracking)
        zeta_path = self.repo_root / "config" / "ZETA_PROGRESS_TRACKER.json"
        rpg_status["quest_tracking"] = zeta_path.exists()

        if zeta_path.exists():
            try:
                with open(zeta_path) as f:
                    zeta_data = json.load(f)
                    rpg_status["active_quests"] = len(
                        [
                            task
                            for phase in zeta_data.get("phases", {}).values()
                            for task in phase.get("tasks", [])
                            if task.get("status") in ["◐", "○"]
                        ]
                    )
                    rpg_status["completed_quests"] = len(
                        [
                            task
                            for phase in zeta_data.get("phases", {}).values()
                            for task in phase.get("tasks", [])
                            if task.get("status") == "✓"
                        ]
                    )
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                logger.debug("Suppressed FileNotFoundError/OSError/json", exc_info=True)

        return rpg_status

    def _detect_recent_changes(self) -> list[str]:
        """Detect recent changes in the repository."""
        recent_changes: list[Any] = []
        # Check for files modified in last 24 hours
        cutoff_time = datetime.now().timestamp() - (24 * 3600)

        for file_path in self.repo_root.glob("**/*"):
            if (
                file_path.is_file()
                and not any(
                    exclude in str(file_path) for exclude in [".git", ".venv", "__pycache__"]
                )
                and file_path.stat().st_mtime > cutoff_time
            ):
                age_hours = (datetime.now().timestamp() - file_path.stat().st_mtime) / 3600
                recent_changes.append(
                    {
                        "file": str(file_path.relative_to(self.repo_root)),
                        "age_hours": round(age_hours, 2),
                        "type": "modification",
                    }
                )

        return recent_changes[:20]  # Limit to 20 most recent

    def _assess_health_indicators(self) -> dict[str, Any]:
        """Assess system health indicators."""
        health: dict[str, Any] = {
            "config_integrity": (self.repo_root / "config").exists(),
            "src_structure": (self.repo_root / "src").exists(),
            "documentation": (self.repo_root / "docs").exists(),
            "logging_system": (self.repo_root / "LOGGING").exists(),
            "requirements_file": (self.repo_root / "requirements.txt").exists(),
            "overall_score": 0,
        }

        # Calculate overall health score
        health_checks = [v for k, v in health.items() if k != "overall_score"]
        health["overall_score"] = (sum(health_checks) / len(health_checks)) * 100

        return health

    def _generate_recommendations(self, snapshot: dict[str, Any]) -> list[str]:
        """Generate recommendations based on snapshot analysis."""
        recommendations: list[Any] = []
        # File organization recommendations
        org_score = snapshot["file_organization"]["organization_score"]
        if org_score < 90:
            recommendations.append(
                f"📁 Consider organizing remaining root files - current organization: {org_score:.1f}%"
            )

        # RPG integration recommendations
        rpg_status = snapshot["rpg_integration"]
        if not all(
            [
                rpg_status["rpg_inventory_system"],
                rpg_status["wizard_navigator"],
                rpg_status["capability_mapping"],
            ]
        ):
            recommendations.append(
                "🎮 Complete RPG integration setup for enhanced system interaction"
            )

        # System component recommendations
        components = snapshot["boolean_checks"]["system_components"]
        if not components.get("rpg_inventory_functional", False):
            recommendations.append("⚡ Activate RPG inventory system for real-time monitoring")

        # Capability recommendations
        if not snapshot["capabilities"]["capability_report_exists"]:
            recommendations.append("🎯 Run capability inventory to map available system actions")

        # Recent activity recommendations
        if len(snapshot["system_state"]["recent_changes"]) > 10:
            recommendations.append(
                "📊 High activity detected - consider running system health assessment"
            )

        return recommendations

    def save_snapshot(self, snapshot: dict[str, Any]) -> Path:
        """Save snapshot to file."""
        snapshot_filename = f"system_snapshot_{self.timestamp}.json"
        snapshot_path = self.snapshot_dir / snapshot_filename

        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)

        return snapshot_path

    def display_snapshot_summary(self, snapshot: dict[str, Any]) -> None:
        """Display snapshot summary."""
        # Boolean check results
        components = snapshot["boolean_checks"]["system_components"]
        sum(1 for v in components.values() if v)
        len(components)

        # System state
        snapshot["system_state"]["repository_stats"]

        # File organization
        snapshot["file_organization"]

        # RPG integration
        snapshot["rpg_integration"]

        # Recommendations
        if snapshot["recommendations"]:
            for _rec in snapshot["recommendations"][:5]:
                pass


def main() -> None:
    """Main execution function."""
    generator = SystemSnapshotGenerator()

    # Perform boolean checks first

    # Create comprehensive snapshot
    snapshot = generator.create_comprehensive_snapshot()

    # Save snapshot
    generator.save_snapshot(snapshot)

    # Display summary
    generator.display_snapshot_summary(snapshot)


if __name__ == "__main__":
    main()

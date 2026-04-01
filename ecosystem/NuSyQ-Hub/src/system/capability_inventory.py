#!/usr/bin/env python3
"""🎮 KILO-FOOLISH System Capabilities Inventory & RPG Integration.

Maps all available commands, actions, and capabilities as RPG-style equipment and skills.

OmniTag: {
    "purpose": "system_capability_mapping",
    "type": "rpg_integration_core",
    "evolution_stage": "v4.0_enhanced"
}
MegaTag: {
    "scope": "repository_consciousness",
    "integration_points": ["rpg_inventory", "wizard_navigator", "component_index"],
    "quantum_context": "system_mastery_tracking"
}
RSHTS: ΞΨΩ∞⟨CAPABILITIES⟩→ΦΣΣ
"""

import builtins
import contextlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SystemCapabilityInventory:
    """Maps system capabilities as RPG-style actions, passives, and equipment."""

    def __init__(self) -> None:
        """Initialize SystemCapabilityInventory."""
        self.repo_root = Path.cwd()
        self.capabilities: dict[str, Any] = {
            "actions": {},  # Active commands/functions
            "passives": {},  # Automated systems/monitors
            "equipment": {},  # Tools and utilities
            "skills": {},  # Learned capabilities
            "quests": {},  # Active objectives
            "achievements": {},  # Completed milestones
        }
        self.load_existing_capabilities()

    def load_existing_capabilities(self) -> None:
        """Load capabilities from existing systems."""
        try:
            # Load from RPG inventory if available
            from src.system.rpg_inventory import get_system_status

            rpg_status = get_system_status()
            self.capabilities["skills"] = rpg_status.get("skills", {})
            self.capabilities["quests"] = rpg_status.get("quests", {})

            # Load from component index
            component_index_path = self.repo_root / "config" / "KILO_COMPONENT_INDEX.json"
            if component_index_path.exists():
                with open(component_index_path) as f:
                    component_data = json.load(f)
                    self._map_components_to_equipment(component_data)

        except (FileNotFoundError, json.JSONDecodeError, OSError):
            logger.debug("Suppressed FileNotFoundError/OSError/json", exc_info=True)

    def _map_components_to_equipment(self, components: dict) -> None:
        """Map component index entries to RPG equipment."""
        for component_key, component_info in components.items():
            if isinstance(component_info, dict):
                component_type = component_info.get("type", "unknown")
                component_name = component_info.get("name", component_key)
                component_path = component_info.get("path", "")

                # Categorize by function type
                if component_type == "function":
                    if "test" in component_name.lower():
                        category = "equipment"  # Testing tools
                        subcategory = "testing_tools"
                    elif any(
                        keyword in component_name.lower()
                        for keyword in ["monitor", "watch", "track"]
                    ):
                        category = "passives"  # Monitoring systems
                        subcategory = "monitoring_systems"
                    else:
                        category = "actions"  # Active functions
                        subcategory = "core_functions"
                elif component_type == "class":
                    category = "equipment"  # Classes as equipment/tools
                    subcategory = "system_classes"
                else:
                    category = "equipment"
                    subcategory = "utilities"

                if category not in self.capabilities:
                    self.capabilities[category] = {}
                if subcategory not in self.capabilities[category]:
                    self.capabilities[category][subcategory] = {}

                self.capabilities[category][subcategory][component_name] = {
                    "path": component_path,
                    "type": component_type,
                    "description": component_info.get("description", ""),
                    "dependencies": component_info.get("dependencies", []),
                    "last_modified": component_info.get("last_modified", ""),
                    "equipped": True,  # Available for use
                    "proficiency": "novice",  # Default skill level
                    "usage_count": 0,
                }

    def scan_repository_actions(self) -> None:
        """Scan repository for all available actions/commands."""
        # Scan Python files for executable functions
        self._scan_python_actions()

        # Scan shell scripts and batch files
        self._scan_script_actions()

        # Scan VS Code tasks
        self._scan_vscode_tasks()

        # Scan documentation for procedures
        self._scan_documentation_procedures()

    def _scan_python_actions(self) -> None:
        """Scan Python files for executable functions."""
        if "python_functions" not in self.capabilities["actions"]:
            self.capabilities["actions"]["python_functions"] = {}

        # Focus on main executable scripts in root and src/
        executables: list[Any] = []
        # Root level scripts
        for py_file in self.repo_root.glob("*.py"):
            if py_file.name.startswith(("main", "launch", "run", "start", "quick_", "system_")):
                executables.append(py_file)

        # Key src/ directories
        for src_dir in ["src/core", "src/tools", "src/system"]:
            src_path = self.repo_root / src_dir
            if src_path.exists():
                executables.extend(src_path.glob("*.py"))

        for py_file in executables:
            self._analyze_python_file(py_file)

    def _analyze_python_file(self, py_file: Path) -> None:
        """Analyze a Python file for capabilities."""
        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            # Check if it's an executable script
            if 'if __name__ == "__main__"' in content:
                self.capabilities["actions"]["python_functions"][py_file.name] = {
                    "type": "executable_script",
                    "path": str(py_file.relative_to(self.repo_root)),
                    "description": self._extract_docstring(content),
                    "executable": True,
                    "command": f"python {py_file.name}",
                    "category": self._categorize_script(py_file.name),
                }

            # Extract main classes and functions
            functions = self._extract_functions(content)
            for func_name, func_info in functions.items():
                key = f"{py_file.stem}.{func_name}"
                self.capabilities["actions"]["python_functions"][key] = {
                    "type": "function",
                    "path": str(py_file.relative_to(self.repo_root)),
                    "description": func_info.get("docstring", ""),
                    "executable": func_info.get("executable", False),
                    "parameters": func_info.get("parameters", []),
                }

        except (FileNotFoundError, UnicodeDecodeError, AttributeError):
            logger.debug(
                "Suppressed AttributeError/FileNotFoundError/UnicodeDecodeError", exc_info=True
            )

    def _scan_script_actions(self) -> None:
        """Scan for shell scripts and batch files."""
        if "shell_scripts" not in self.capabilities["actions"]:
            self.capabilities["actions"]["shell_scripts"] = {}

        # PowerShell scripts
        for ps_file in self.repo_root.glob("**/*.ps1"):
            if not any(exclude in str(ps_file) for exclude in [".venv", "__pycache__", ".git"]):
                self.capabilities["actions"]["shell_scripts"][ps_file.name] = {
                    "type": "powershell_script",
                    "path": str(ps_file.relative_to(self.repo_root)),
                    "description": self._extract_ps_description(ps_file),
                    "executable": True,
                    "command": f"powershell -File {ps_file.name}",
                }

    def _scan_vscode_tasks(self) -> None:
        """Scan VS Code tasks.json for available tasks."""
        if "vscode_tasks" not in self.capabilities["actions"]:
            self.capabilities["actions"]["vscode_tasks"] = {}

        tasks_file = self.repo_root / ".vscode" / "tasks.json"
        if tasks_file.exists():
            try:
                with open(tasks_file) as f:
                    tasks_data = json.load(f)

                for task in tasks_data.get("tasks", []):
                    task_label = task.get("label", "unnamed_task")
                    self.capabilities["actions"]["vscode_tasks"][task_label] = {
                        "type": "vscode_task",
                        "command": task.get("command", ""),
                        "args": task.get("args", []),
                        "description": f"VS Code task: {task_label}",
                        "executable": True,
                        "group": task.get("group", ""),
                    }
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                logger.debug("Suppressed FileNotFoundError/OSError/json", exc_info=True)

    def _scan_documentation_procedures(self) -> None:
        """Scan documentation for procedures and guides."""
        if "documentation_procedures" not in self.capabilities["actions"]:
            self.capabilities["actions"]["documentation_procedures"] = {}

        # Scan key documentation files
        doc_files: list[Any] = []
        # Key documentation directories
        for doc_dir in ["docs", "guidance", ".github/instructions"]:
            doc_path = self.repo_root / doc_dir
            if doc_path.exists():
                doc_files.extend(doc_path.glob("**/*.md"))

        # Root level documentation
        doc_files.extend(self.repo_root.glob("*.md"))

        for doc_file in doc_files:
            if "instructions" in doc_file.name.lower() or "guide" in doc_file.name.lower():
                self.capabilities["actions"]["documentation_procedures"][doc_file.name] = {
                    "type": "documentation_procedure",
                    "path": str(doc_file.relative_to(self.repo_root)),
                    "description": f"Procedure guide: {doc_file.stem.replace('_', ' ').title()}",
                    "executable": False,
                    "category": "guidance",
                }

    def identify_monitoring_systems(self) -> None:
        """Identify passive monitoring and automated systems."""
        if "monitoring_systems" not in self.capabilities["passives"]:
            self.capabilities["passives"]["monitoring_systems"] = {}

        # Look for monitoring-related files
        monitoring_patterns = [
            "*watcher*",
            "*monitor*",
            "*health*",
            "*status*",
            "*tracker*",
        ]

        for pattern in monitoring_patterns:
            for py_file in self.repo_root.glob(f"**/{pattern}.py"):
                if not any(exclude in str(py_file) for exclude in [".venv", "__pycache__", ".git"]):
                    system_name = py_file.stem
                    self.capabilities["passives"]["monitoring_systems"][system_name] = {
                        "type": "monitoring_system",
                        "path": str(py_file.relative_to(self.repo_root)),
                        "description": f"Automated monitoring: {system_name.replace('_', ' ').title()}",
                        "auto_start": True,
                        "status": "available",
                    }

    def create_system_snapshot(self) -> dict[str, Any]:
        """Create a comprehensive system snapshot."""
        return {
            "timestamp": datetime.now().isoformat(),
            "repository": "KILO-FOOLISH NuSyQ-Hub",
            "total_capabilities": sum(
                len(category.get(sub, {}))
                for category in self.capabilities.values()
                for sub in category
                if isinstance(category, dict)
            ),
            "capabilities": self.capabilities,
            "system_stats": {
                "total_actions": len(self.capabilities.get("actions", {})),
                "total_passives": len(self.capabilities.get("passives", {})),
                "total_equipment": len(self.capabilities.get("equipment", {})),
                "total_skills": len(self.capabilities.get("skills", {})),
                "active_quests": len(self.capabilities.get("quests", {})),
            },
            "quick_commands": self._generate_quick_commands(),
            "status": "operational",
        }

    def _generate_quick_commands(self) -> dict[str, Any]:
        """Generate list of most useful quick commands."""
        quick_commands: dict[str, Any] = {}
        # From Python executables
        for script_name, script_info in (
            self.capabilities.get("actions", {}).get("python_functions", {}).items()
        ):
            if script_info.get("executable", False):
                quick_commands[script_name] = {
                    "command": script_info.get("command", f"python {script_name}"),
                    "description": script_info.get("description", ""),
                    "category": script_info.get("category", "utility"),
                }

        # From VS Code tasks
        for task_name, task_info in (
            self.capabilities.get("actions", {}).get("vscode_tasks", {}).items()
        ):
            quick_commands[f"task:{task_name}"] = {
                "command": f"Run VS Code task: {task_name}",
                "description": task_info.get("description", ""),
                "category": "vscode_task",
            }

        return quick_commands

    def save_inventory(self, filepath: str | Path | None = None) -> Path:
        """Save capability inventory to file."""
        if not filepath:
            final_path: Path = self.repo_root / "data" / "system_capability_inventory.json"
        else:
            final_path = Path(filepath)

        final_path.parent.mkdir(parents=True, exist_ok=True)

        snapshot = self.create_system_snapshot()

        with open(final_path, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)

        return final_path

    def generate_rpg_integration_report(self) -> dict[str, Any]:
        """Generate report for RPG system integration."""
        report: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "rpg_integration_status": "active",
            "available_equipment": {},
            "skill_progression": {},
            "active_quests": {},
            "recommended_actions": [],
        }

        # Map capabilities to RPG concepts
        for category, items in self.capabilities.items():
            if category == "actions":
                report["available_equipment"]["weapons"] = items  # Commands as weapons
            elif category == "passives":
                report["available_equipment"]["armor"] = items  # Monitoring as protection
            elif category == "equipment":
                report["available_equipment"]["tools"] = items  # Utilities as tools

        # Recommend actions based on current state
        report["recommended_actions"] = [
            "Run system health assessment to check all equipment status",
            "Execute monitoring systems to maintain passive defenses",
            "Update skill proficiency through regular capability usage",
            "Complete active quests to gain experience points",
        ]

        return report

    # Helper methods
    def _extract_docstring(self, content: str) -> str:
        """Extract module docstring."""
        lines = content.split("\n")
        in_docstring = False
        docstring_lines: list[Any] = []
        for line in lines:
            if '"""' in line and not in_docstring:
                in_docstring = True
                if line.count('"""') == 2:  # Single line docstring
                    return line.split('"""')[1].strip()
                docstring_lines.append(line.split('"""')[1])
            elif '"""' in line and in_docstring:
                docstring_lines.append(line.split('"""')[0])
                break
            elif in_docstring:
                docstring_lines.append(line.strip())

        return " ".join(docstring_lines).strip()

    def _extract_functions(self, content: str) -> dict:
        """Extract function information."""
        functions: dict[str, Any] = {}
        # Simple extraction - could be enhanced with AST parsing
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and not line.strip().startswith("def _"):
                func_name = line.split("def ")[1].split("(")[0].strip()
                functions[func_name] = {
                    "docstring": self._extract_function_docstring(lines, i),
                    "executable": "if __name__" in content,
                    "parameters": [],  # Could be enhanced
                }
        return functions

    def _extract_function_docstring(self, lines: list[str], start_idx: int) -> str:
        """Extract function docstring."""
        for i in range(start_idx + 1, min(start_idx + 10, len(lines))):
            if '"""' in lines[i]:
                return lines[i].split('"""')[1].split('"""')[0].strip()
        return ""

    def _categorize_script(self, filename: str) -> str:
        """Categorize script by name."""
        if any(keyword in filename.lower() for keyword in ["health", "monitor", "status"]):
            return "monitoring"
        if any(keyword in filename.lower() for keyword in ["quick", "system", "analysis"]):
            return "analysis"
        if any(keyword in filename.lower() for keyword in ["consolidat", "organiz"]):
            return "maintenance"
        return "utility"

    def _extract_ps_description(self, ps_file: Path) -> str:
        """Extract PowerShell script description."""
        try:
            with open(ps_file, encoding="utf-8") as f:
                first_lines = f.read(500)  # Read first 500 chars
                if "<#" in first_lines:
                    return first_lines.split("<#")[1].split("#>")[0].strip()
        except (FileNotFoundError, UnicodeDecodeError, OSError, IndexError):
            logger.debug(
                "Suppressed FileNotFoundError/IndexError/OSError/UnicodeDecodeError", exc_info=True
            )
        return f"PowerShell script: {ps_file.stem.replace('_', ' ').title()}"


def main() -> None:
    """Main execution function."""
    inventory = SystemCapabilityInventory()

    # Scan for all capabilities
    inventory.scan_repository_actions()
    inventory.identify_monitoring_systems()

    # Create and save snapshot
    inventory.save_inventory()

    # Generate RPG integration report
    rpg_report = inventory.generate_rpg_integration_report()
    rpg_report_path = inventory.repo_root / "reports" / "rpg_integration_status.json"
    rpg_report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(rpg_report_path, "w") as f:
        json.dump(rpg_report, f, indent=2, default=str)

    # Display summary
    snapshot = inventory.create_system_snapshot()

    for _cmd_name, _cmd_info in list(snapshot["quick_commands"].items())[:5]:
        pass

    # Gain experience for running this analysis
    with contextlib.suppress(builtins.BaseException):
        from src.system.rpg_inventory import award_xp

        award_xp("monitoring", 25, award_game_fn=None)


if __name__ == "__main__":
    main()

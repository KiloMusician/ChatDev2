"""KILO-FOOLISH Repository Coordinator.

Intelligent file organization, duplicate detection, and repository maintenance system.
"""

import ast
import hashlib
import json
import logging
import os
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


class AutoOrganizeResult(TypedDict):
    moved: list[dict[str, str]]
    failed: list[dict[str, str]]
    dry_run: bool


class KILORepositoryCoordinator:
    def __init__(self, repo_root: str | None = None) -> None:
        """Initialize KILORepositoryCoordinator with repo_root."""
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent.parent
        self.config_file = self.repo_root / "src" / "core" / "coordinator_config.json"
        self.rules_file = self.repo_root / "src" / "core" / "organization_rules.json"
        self.log_file = self.repo_root / "data" / "logs" / "coordinator.log"

        # Ensure directories exist
        os.makedirs(self.log_file.parent, exist_ok=True)
        os.makedirs(self.config_file.parent, exist_ok=True)

        self.load_configuration()
        self.file_registry: dict[str, Any] = {}
        self.duplicates_found: list[Any] = []
        self.move_suggestions: list[Any] = []
        self.cleanup_tasks: list[Any] = []

    def load_configuration(self) -> None:
        """Load coordinator configuration and rules."""
        # Default configuration
        default_config = {
            "auto_organize": True,
            "safe_mode": True,
            "backup_before_move": True,
            "scan_frequency": "real-time",
            "excluded_directories": [
                ".git",
                "__pycache__",
                "node_modules",
                ".vscode",
                "venv",
            ],
            "file_size_threshold_mb": 100,
            "duplicate_action": "prompt",  # prompt, move, delete
            "organization_strictness": "medium",  # low, medium, high
        }

        # Default organization rules
        default_rules = {
            "directory_structure": {
                "src/": {
                    "purpose": "Source code and main modules",
                    "allowed_extensions": [".py", ".ps1", ".psm1", ".psd1"],
                    "subdirectories": {
                        "core/": "Core system components",
                        "config/": "Configuration and settings",
                        "ai/": "AI integration modules",
                        "utils/": "Utility functions and helpers",
                        "interfaces/": "External interfaces and APIs",
                    },
                },
                "docs/": {
                    "purpose": "Documentation and guides",
                    "allowed_extensions": [".md", ".txt", ".rst", ".pdf"],
                    "subdirectories": {
                        "api/": "API documentation",
                        "guides/": "User and developer guides",
                        "architecture/": "System architecture docs",
                    },
                },
                "data/": {
                    "purpose": "Data storage and processing",
                    "allowed_extensions": [".json", ".csv", ".txt", ".log"],
                    "subdirectories": {
                        "logs/storage/": "Unified log file storage",
                        "cache/": "Temporary cache files",
                        "backups/": "Backup files",
                    },
                },
                "tests/": {
                    "purpose": "Testing and validation",
                    "allowed_extensions": [".py", ".ps1"],
                    "subdirectories": {
                        "unit/": "Unit tests",
                        "integration/": "Integration tests",
                        "fixtures/": "Test data and fixtures",
                    },
                },
                "scripts/": {
                    "purpose": "Standalone scripts and utilities",
                    "allowed_extensions": [".py", ".ps1", ".sh", ".bat"],
                },
            },
            "file_naming_patterns": {
                "python_modules": "^[a-z_][a-z0-9_]*\\.py$",
                "powershell_scripts": "^[A-Z][a-zA-Z0-9]*\\.ps1$",
                "config_files": "^[a-z_][a-z0-9_]*\\.(json|yaml|yml|ini|conf)$",
                "documentation": "^[A-Z][a-zA-Z0-9_-]*\\.md$",
            },
            "duplicate_detection": {
                "ignore_extensions": [".log", ".tmp", ".cache"],
                "size_threshold_bytes": 1024,
                "content_similarity_threshold": 0.95,
            },
        }

        # Load or create configuration
        if self.config_file.exists():
            with open(self.config_file, encoding="utf-8") as f:
                self.config = {**default_config, **json.load(f)}
        else:
            self.config = default_config
            self.save_configuration()

        # Load or create rules
        if self.rules_file.exists():
            with open(self.rules_file, encoding="utf-8") as f:
                self.rules = {**default_rules, **json.load(f)}
        else:
            self.rules = default_rules
            self.save_rules()

    def save_configuration(self) -> None:
        """Save current configuration."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def save_rules(self) -> None:
        """Save organization rules."""
        with open(self.rules_file, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, indent=2)

    def log_action(self, action: str, details: str = "", level: str = "INFO") -> None:
        """Log coordinator actions."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {action}: {details}\n"

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        # Also print to console

    def scan_repository(self) -> dict[str, Any]:
        """Comprehensive repository scan."""
        self.log_action("Repository Scan", "Starting comprehensive scan")

        scan_results: dict[str, Any] = {
            "files_scanned": 0,
            "directories_analyzed": 0,
            "misplaced_files": [],
            "duplicates": [],
            "naming_violations": [],
            "large_files": [],
            "orphaned_files": [],
            "suggestions": [],
        }

        # Scan all files
        for root, dirs, files in os.walk(self.repo_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.config["excluded_directories"]]

            current_path = Path(root)
            current_path.relative_to(self.repo_root)

            scan_results["directories_analyzed"] += 1

            for file in files:
                if file.startswith("."):
                    continue

                file_path = current_path / file
                rel_file_path = file_path.relative_to(self.repo_root)

                scan_results["files_scanned"] += 1

                # Analyze file
                file_info = self.analyze_file(file_path)
                self.file_registry[str(rel_file_path)] = file_info

                # Check for misplacement
                if self.is_file_misplaced(file_path, file_info):
                    scan_results["misplaced_files"].append(
                        {
                            "current_path": str(rel_file_path),
                            "suggested_path": self.suggest_correct_location(file_path, file_info),
                            "reason": file_info.get("misplacement_reason", "Unknown"),
                        }
                    )

                # Check naming conventions
                if not self.follows_naming_convention(file_path):
                    scan_results["naming_violations"].append(
                        {
                            "file": str(rel_file_path),
                            "suggested_name": self.suggest_better_name(file_path),
                            "violation_type": self.get_naming_violation_type(file_path),
                        }
                    )

                # Check file size
                if file_info["size_mb"] > self.config["file_size_threshold_mb"]:
                    scan_results["large_files"].append(
                        {
                            "file": str(rel_file_path),
                            "size_mb": file_info["size_mb"],
                            "suggestion": "Consider compression or archival",
                        }
                    )

        # Detect duplicates
        scan_results["duplicates"] = self.detect_duplicates()

        # Find orphaned files
        scan_results["orphaned_files"] = self.find_orphaned_files()

        # Generate intelligent suggestions
        scan_results["suggestions"] = self.generate_suggestions(scan_results)

        self.log_action(
            "Repository Scan",
            f"Completed - {scan_results['files_scanned']} files analyzed",
            "SUCCESS",
        )
        return scan_results

    def analyze_file(self, file_path: Path) -> dict:
        """Analyze individual file properties."""
        return {
            "name": file_path.name,
            "extension": file_path.suffix.lower(),
            "size_bytes": file_path.stat().st_size,
            "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
            "file_type": self.classify_file_type(file_path),
            "purpose": self.infer_file_purpose(file_path),
            "complexity": self.calculate_complexity(file_path),
            "dependencies": self.extract_dependencies(file_path),
            "hash": self.calculate_file_hash(file_path),
        }

    def classify_file_type(self, file_path: Path) -> str:
        """Classify file type based on extension and content."""
        ext = file_path.suffix.lower()

        type_mapping = {
            ".py": "python_module",
            ".ps1": "powershell_script",
            ".psm1": "powershell_module",
            ".psd1": "powershell_data",
            ".md": "documentation",
            ".json": "configuration",
            ".yaml": "configuration",
            ".yml": "configuration",
            ".txt": "text_file",
            ".log": "log_file",
            ".csv": "data_file",
            ".bat": "batch_script",
            ".sh": "shell_script",
        }

        return type_mapping.get(ext, "unknown")

    def infer_file_purpose(self, file_path: Path) -> str:
        """Infer file purpose from name and content."""
        name_lower = file_path.name.lower()

        # Special files
        if name_lower in ["readme.md", "license", "changelog.md"]:
            return "project_documentation"
        if name_lower in ["setup.py", "requirements.txt", "pyproject.toml"]:
            return "project_configuration"
        if "test" in name_lower:
            return "testing"
        if "config" in name_lower or "setting" in name_lower:
            return "configuration"
        if "secret" in name_lower:
            return "security"
        if name_lower.endswith(("manager.py", "manager.ps1")):
            return "system_management"
        if "coordinator" in name_lower:
            return "coordination"
        if "scanner" in name_lower or "analyzer" in name_lower:
            return "analysis"
        return "general_purpose"

    def calculate_complexity(self, file_path: Path) -> int:
        """Calculate file complexity score."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = len(content.splitlines())

            # Base complexity on lines
            complexity = min(lines // 10, 10)  # 0-10 scale

            # Adjust based on file type
            if file_path.suffix == ".py":
                # Count functions and classes
                try:
                    tree = ast.parse(content)
                    functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                    classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
                    complexity += (functions + classes * 2) // 5
                except (AttributeError, TypeError):
                    logger.debug("Suppressed AttributeError/TypeError", exc_info=True)

            elif file_path.suffix == ".ps1":
                # Count PowerShell functions
                function_count = len(re.findall(r"function\s+\w+", content, re.IGNORECASE))
                complexity += function_count // 2

            return min(complexity, 10)

        except (UnicodeDecodeError, OSError):
            return 1

    def extract_dependencies(self, file_path: Path) -> list[str]:
        """Extract file dependencies."""
        dependencies: list[Any] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            if file_path.suffix == ".py":
                # Python imports
                import_patterns = [
                    r"from\s+(\S+)\s+import",
                    r"import\s+(\S+)",
                    r"from\s+\.(\S+)\s+import",
                ]

                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    dependencies.extend(matches)

            elif file_path.suffix == ".ps1":
                # PowerShell imports
                ps_patterns = [
                    r"Import-Module\s+(\S+)",
                    r'\.\s+["\']([^"\']+\.ps1)["\']',
                    r'&\s+["\']([^"\']+\.ps1)["\']',
                ]

                for pattern in ps_patterns:
                    matches = re.findall(pattern, content)
                    dependencies.extend(matches)

        except (UnicodeDecodeError, OSError):
            logger.debug("Suppressed OSError/UnicodeDecodeError", exc_info=True)

        return list(set(dependencies))  # Remove duplicates

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for duplicate detection."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except (OSError, ValueError) as e:
            self.log_action("Hash Error", f"Could not hash {file_path}: {e}", "WARNING")
            return ""

    def is_file_misplaced(self, file_path: Path, file_info: dict) -> bool:
        """Check if file is in the wrong location."""
        rel_path = file_path.relative_to(self.repo_root)
        current_dir = str(rel_path.parent)
        file_type = file_info["file_type"]
        purpose = file_info["purpose"]

        # Check against directory structure rules
        for dir_pattern, rules in self.rules["directory_structure"].items():
            if current_dir.startswith(dir_pattern.rstrip("/")):
                # File is in this directory - check if it belongs
                allowed_extensions = rules.get("allowed_extensions", [])
                if allowed_extensions and file_info["extension"] not in allowed_extensions:
                    file_info["misplacement_reason"] = (
                        f"Extension {file_info['extension']} not allowed in {dir_pattern}"
                    )
                    return True
                return False

        # File is not in any structured directory - might be misplaced
        if purpose in ["configuration", "security"] and not current_dir.startswith("src/config"):
            file_info["misplacement_reason"] = "Configuration file should be in src/config/"
            return True
        if purpose == "testing" and not current_dir.startswith("tests"):
            file_info["misplacement_reason"] = "Test file should be in tests/"
            return True
        if purpose == "project_documentation" and current_dir != ".":
            file_info["misplacement_reason"] = "Project documentation should be in root"
            return True
        if file_type in [
            "python_module",
            "powershell_script",
        ] and not current_dir.startswith("src"):
            file_info["misplacement_reason"] = "Source code should be in src/"
            return True

        return False

    def suggest_correct_location(self, file_path: Path, file_info: dict) -> str:
        """Suggest correct location for misplaced file."""
        purpose = file_info["purpose"]
        file_type = file_info["file_type"]

        # Mapping based on purpose and type
        SYSTEM_MGMT_PATH = "src/core/"
        location_map = {
            "configuration": "src/config/",
            "security": "src/config/",
            "testing": "tests/",
            "project_documentation": "./",
            "system_management": SYSTEM_MGMT_PATH,
            "coordination": SYSTEM_MGMT_PATH,
            "analysis": SYSTEM_MGMT_PATH,
            "general_purpose": "src/",
        }

        base_location = location_map.get(purpose, "src/")

        # Refine based on file type
        if file_type == "python_module" and purpose == "general_purpose":
            base_location = "src/utils/"
        elif file_type == "documentation":
            base_location = "docs/"
        elif file_type == "log_file":
            base_location = "logs/storage/"
        elif file_type == "data_file":
            base_location = "data/"

        return base_location + file_path.name

    def follows_naming_convention(self, file_path: Path) -> bool:
        """Check if file follows naming conventions."""
        file_type = self.classify_file_type(file_path)
        filename = file_path.name

        patterns = self.rules["file_naming_patterns"]

        if file_type == "python_module" and "python_modules" in patterns:
            return re.match(patterns["python_modules"], filename) is not None
        if file_type == "powershell_script" and "powershell_scripts" in patterns:
            return re.match(patterns["powershell_scripts"], filename) is not None
        if file_type == "configuration" and "config_files" in patterns:
            return re.match(patterns["config_files"], filename) is not None
        if file_type == "documentation" and "documentation" in patterns:
            return re.match(patterns["documentation"], filename) is not None

        return True  # No specific rule, assume it's fine

    def suggest_better_name(self, file_path: Path) -> str:
        """Suggest better filename following conventions."""
        file_type = self.classify_file_type(file_path)
        current_name = file_path.stem
        extension = file_path.suffix

        if file_type == "python_module":
            # Convert to snake_case
            suggested = re.sub(r"([A-Z])", r"_\1", current_name).lower().strip("_")
            return f"{suggested}{extension}"
        if file_type == "powershell_script":
            # Convert to PascalCase
            words = re.split(r"[_\-\s]+", current_name.lower())
            suggested = "".join(word.capitalize() for word in words if word)
            return f"{suggested}{extension}"
        if file_type == "documentation":
            # Ensure starts with capital
            suggested = current_name[0].upper() + current_name[1:] if current_name else "Document"
            return f"{suggested}{extension}"

        return file_path.name

    def get_naming_violation_type(self, file_path: Path) -> str:
        """Get type of naming violation."""
        file_type = self.classify_file_type(file_path)
        filename = file_path.name

        if file_type == "python_module":
            if re.search(r"[A-Z]", filename):
                return "Should use snake_case"
            if re.search(r"[^a-z0-9_.]", filename):
                return "Contains invalid characters"
        elif file_type == "powershell_script":
            if not filename[0].isupper():
                return "Should start with capital letter"
            if re.search(r"[_\-]", filename):
                return "Should use PascalCase"

        return "Naming convention violation"

    def detect_duplicates(self) -> list[dict]:
        """Detect duplicate files."""
        duplicates: list[Any] = []
        hash_groups = defaultdict(list)

        # Group files by hash
        for file_path, info in self.file_registry.items():
            if (
                info["hash"]
                and info["extension"] not in self.rules["duplicate_detection"]["ignore_extensions"]
            ) and info["size_bytes"] >= self.rules["duplicate_detection"]["size_threshold_bytes"]:
                hash_groups[info["hash"]].append(file_path)

        # Find groups with multiple files
        for file_hash, files in hash_groups.items():
            if len(files) > 1:
                duplicates.append(
                    {
                        "hash": file_hash,
                        "files": files,
                        "size_bytes": self.file_registry[files[0]]["size_bytes"],
                        "action_suggestion": self.suggest_duplicate_action(files),
                    }
                )

        return duplicates

    def suggest_duplicate_action(self, duplicate_files: list[str]) -> str:
        """Suggest action for duplicate files."""
        # Prefer keeping files in proper locations
        for file_path in duplicate_files:
            info = self.file_registry[file_path]
            if not self.is_file_misplaced(self.repo_root / file_path, info):
                return f"Keep {file_path}, remove others"

        # If all are misplaced, suggest keeping the newest
        newest_file = max(duplicate_files, key=lambda f: self.file_registry[f]["modified"])
        return f"Keep {newest_file} (newest), remove others"

    def find_orphaned_files(self) -> list[dict]:
        """Find files that don't seem to belong anywhere."""
        orphaned: list[Any] = []
        for file_path, info in self.file_registry.items():
            # Check if file has any dependencies or is depended upon
            if (
                not info["dependencies"]
                and info["purpose"] == "general_purpose"
                and info["complexity"] <= 2
                and not any(
                    file_path in other_info["dependencies"]
                    for other_info in self.file_registry.values()
                )
            ):
                orphaned.append(
                    {
                        "file": file_path,
                        "reason": "No clear purpose or dependencies",
                        "suggestion": "Review for deletion or better organization",
                    }
                )

        return orphaned

    def generate_suggestions(self, scan_results: dict) -> list[dict]:
        """Generate intelligent improvement suggestions."""
        suggestions: list[Any] = []
        # Organization suggestions
        if scan_results["misplaced_files"]:
            suggestions.append(
                {
                    "type": "organization",
                    "priority": "high",
                    "title": f"Reorganize {len(scan_results['misplaced_files'])} misplaced files",
                    "description": "Move files to their appropriate directories",
                    "action": "auto_organize_files",
                }
            )

        # Duplicate cleanup
        if scan_results["duplicates"]:
            total_duplicates = sum(len(d["files"]) - 1 for d in scan_results["duplicates"])
            suggestions.append(
                {
                    "type": "cleanup",
                    "priority": "medium",
                    "title": f"Remove {total_duplicates} duplicate files",
                    "description": "Clean up duplicate files to save space",
                    "action": "remove_duplicates",
                }
            )

        # Naming improvements
        if scan_results["naming_violations"]:
            suggestions.append(
                {
                    "type": "naming",
                    "priority": "low",
                    "title": f"Fix {len(scan_results['naming_violations'])} naming violations",
                    "description": "Rename files to follow conventions",
                    "action": "fix_naming",
                }
            )

        # Large file optimization
        if scan_results["large_files"]:
            suggestions.append(
                {
                    "type": "optimization",
                    "priority": "low",
                    "title": f"Optimize {len(scan_results['large_files'])} large files",
                    "description": "Consider compressing or archiving large files",
                    "action": "optimize_large_files",
                }
            )

        return suggestions

    def auto_organize_files(
        self, scan_results: dict[str, Any], is_dry_run: bool = True
    ) -> AutoOrganizeResult:
        """Automatically organize misplaced files."""
        org_results: AutoOrganizeResult = {
            "moved": [],
            "failed": [],
            "dry_run": is_dry_run,
        }

        for misplaced in scan_results["misplaced_files"]:
            current_path = self.repo_root / misplaced["current_path"]
            suggested_path = self.repo_root / misplaced["suggested_path"]

            if is_dry_run:
                org_results["moved"].append(
                    {
                        "from": misplaced["current_path"],
                        "to": misplaced["suggested_path"],
                        "reason": misplaced["reason"],
                    }
                )
            else:
                try:
                    # Create target directory if needed
                    os.makedirs(suggested_path.parent, exist_ok=True)

                    # Backup if configured
                    if self.config["backup_before_move"]:
                        backup_path = (
                            self.repo_root / "data" / "backups" / f"{current_path.name}.backup"
                        )
                        shutil.copy2(current_path, backup_path)

                    # Move file
                    shutil.move(str(current_path), str(suggested_path))

                    org_results["moved"].append(
                        {
                            "from": misplaced["current_path"],
                            "to": misplaced["suggested_path"],
                            "reason": misplaced["reason"],
                        }
                    )

                    self.log_action(
                        "File Moved",
                        f"{misplaced['current_path']} -> {misplaced['suggested_path']}",
                        "SUCCESS",
                    )

                except (OSError, ValueError) as e:
                    org_results["failed"].append(
                        {
                            "file": misplaced["current_path"],
                            "error": str(e),
                        }
                    )

                    self.log_action("Move Failed", f"{misplaced['current_path']}: {e}", "ERROR")

        return org_results

    def generate_report(self, scan_results: dict) -> str:
        """Generate comprehensive repository report."""
        report = f"""# 🗂️ KILO-FOOLISH Repository Coordination Report
*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

## 📊 Repository Overview

- **Files Scanned**: {scan_results["files_scanned"]:,}
- **Directories Analyzed**: {scan_results["directories_analyzed"]:,}
- **Organization Score**: {self.calculate_organization_score(scan_results)}/100

## 🎯 Issues Found

### 🚚 Misplaced Files ({len(scan_results["misplaced_files"])})
"""

        for misplaced in scan_results["misplaced_files"][:10]:  # Show first 10
            report += f"- `{misplaced['current_path']}` → `{misplaced['suggested_path']}`\n"
            report += f"  *Reason: {misplaced['reason']}*\n"

        if len(scan_results["misplaced_files"]) > 10:
            report += f"- *...and {len(scan_results['misplaced_files']) - 10} more*\n"

        report += f"""
### 🔄 Duplicate Files ({len(scan_results["duplicates"])})
"""

        for duplicate in scan_results["duplicates"][:5]:  # Show first 5
            report += (
                f"- **{len(duplicate['files'])} copies** ({duplicate['size_bytes']:,} bytes each)\n"
            )
            for file in duplicate["files"]:
                report += f"  - `{file}`\n"

        report += f"""
### 📝 Naming Violations ({len(scan_results["naming_violations"])})
"""

        for violation in scan_results["naming_violations"][:10]:
            report += f"- `{violation['file']}` → `{violation['suggested_name']}`\n"
            report += f"  *{violation['violation_type']}*\n"

        report += """
## 🚀 Recommendations

"""

        for suggestion in scan_results["suggestions"]:
            priority_icon = {"high": "🔥", "medium": "⚡", "low": "💡"}[suggestion["priority"]]
            report += f"### {priority_icon} {suggestion['title']}\n"
            report += f"{suggestion['description']}\n\n"

        report += """
---
*Use the Repository Coordinator to automatically apply these improvements.*
"""

        return report

    def calculate_organization_score(self, scan_results: dict) -> int:
        """Calculate repository organization score (0-100)."""
        total_files = scan_results["files_scanned"]
        if total_files == 0:
            return 100

        # Deduct points for issues
        score = 100
        score -= min(30, (len(scan_results["misplaced_files"]) / total_files) * 100)
        score -= min(20, (len(scan_results["duplicates"]) / total_files) * 100)
        score -= min(15, (len(scan_results["naming_violations"]) / total_files) * 100)
        score -= min(10, (len(scan_results["large_files"]) / total_files) * 100)
        score -= min(10, (len(scan_results["orphaned_files"]) / total_files) * 100)

        return max(0, int(score))

    def run_coordination(self, should_autofix: bool = False) -> dict:
        """Run full repository coordination."""
        self.log_action("Repository Coordination", "Starting comprehensive coordination", "INFO")

        # Scan repository
        scan_results = self.scan_repository()

        # Generate report
        report = self.generate_report(scan_results)
        report_file = self.repo_root / "COORDINATION_REPORT.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        # Auto-fix if requested
        if should_autofix and not self.config.get("safe_mode", True):
            organization_results = self.auto_organize_files(scan_results, is_dry_run=False)
            scan_results["organization_results"] = organization_results

        self.log_action("Repository Coordination", "Completed successfully", "SUCCESS")
        return scan_results


if __name__ == "__main__":
    import sys

    # Handle command line arguments
    auto_fix = "--auto-fix" in sys.argv
    dry_run = "--dry-run" in sys.argv
    continuous = "--continuous" in sys.argv

    coordinator = KILORepositoryCoordinator()

    if continuous:
        # Add continuous monitoring logic here
        results = coordinator.run_coordination(should_autofix=False)
    else:
        results = coordinator.run_coordination(should_autofix=auto_fix)

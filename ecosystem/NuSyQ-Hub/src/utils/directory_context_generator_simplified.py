#!/usr/bin/env python3
"""🏗️ KILO-FOOLISH Directory Context Generator (Simplified).

Advanced context file generation using repository analysis.

OmniTag: [🏗️→ DirectoryContext, Infrastructure, Documentation]
MegaTag: [UTILS⨳DIRECTORY⦾CONTEXT→∞]
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DirectoryContextGenerator:
    """Directory context file generator for KILO-FOOLISH infrastructure."""

    def __init__(self, repository_root: str | None = None) -> None:
        """Initialize DirectoryContextGenerator with repository_root."""
        self.repository_root = Path(repository_root or os.getcwd())

        # Context generation templates based on directory purpose
        self.context_templates = {
            "ai": "AI_SYSTEMS_CONTEXT.md",
            "analysis": "ANALYSIS_SYSTEMS_CONTEXT.md",
            "blockchain": "BLOCKCHAIN_SYSTEMS_CONTEXT.md",
            "cloud": "CLOUD_SYSTEMS_CONTEXT.md",
            "consciousness": "CONSCIOUSNESS_SYSTEMS_CONTEXT.md",
            "copilot": "COPILOT_SYSTEMS_CONTEXT.md",
            "core": "CORE_SYSTEMS_CONTEXT.md",
            "diagnostics": "DIAGNOSTICS_SYSTEMS_CONTEXT.md",
            "enhancements": "ENHANCEMENT_SYSTEMS_CONTEXT.md",
            "healing": "HEALING_SYSTEMS_CONTEXT.md",
            "integration": "INTEGRATION_SYSTEMS_CONTEXT.md",
            "interface": "INTERFACE_SYSTEMS_CONTEXT.md",
            "logging": "LOGGING_SYSTEMS_CONTEXT.md",
            "memory": "MEMORY_SYSTEMS_CONTEXT.md",
            "ml": "ML_SYSTEMS_CONTEXT.md",
            "orchestration": "ORCHESTRATION_SYSTEMS_CONTEXT.md",
            "quantum": "QUANTUM_SYSTEMS_CONTEXT.md",
            "security": "SECURITY_SYSTEMS_CONTEXT.md",
            "setup": "SETUP_SYSTEMS_CONTEXT.md",
            "spine": "SPINE_SYSTEMS_CONTEXT.md",
            "system": "SYSTEM_MANAGEMENT_CONTEXT.md",
            "tagging": "TAGGING_SYSTEMS_CONTEXT.md",
            "tools": "DEVELOPMENT_TOOLS_CONTEXT.md",
            "ui": "USER_INTERFACE_CONTEXT.md",
            "utils": "UTILITY_SYSTEMS_CONTEXT.md",
            "tests": "TESTING_SYSTEMS_CONTEXT.md",
            "docs": "DOCUMENTATION_SYSTEMS_CONTEXT.md",
            "config": "CONFIGURATION_SYSTEMS_CONTEXT.md",
            "data": "DATA_MANAGEMENT_CONTEXT.md",
            "reports": "REPORTING_SYSTEMS_CONTEXT.md",
            "web": "WEB_INTERFACE_CONTEXT.md",
            "Rosetta_Quest_System": "ROSETTA_QUEST_CONTEXT.md",
        }

        # Load existing infrastructure data
        self.load_existing_data()

    def load_existing_data(self) -> None:
        """Load existing repository data."""
        try:
            # Load KILO Component Index if available
            component_index_path = self.repository_root / "config" / "KILO_COMPONENT_INDEX.json"
            if component_index_path.exists():
                with open(component_index_path, encoding="utf-8") as f:
                    self.component_index = json.load(f)
            else:
                self.component_index = {}

        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.component_index = {}

    def scan_directories(self) -> list[dict[str, Any]]:
        """Scan all directories for context file needs."""
        directories_needing_context: list[Any] = []

        # Scan src/ directory and subdirectories
        src_path = self.repository_root / "src"
        if src_path.exists():
            self.scan_directory_recursive(src_path, directories_needing_context)

        # Scan other important directories
        for dir_name in ["tests", "docs", "config", "data", "reports", "web"]:
            dir_path = self.repository_root / dir_name
            if dir_path.exists():
                self.scan_directory_recursive(dir_path, directories_needing_context)

        return directories_needing_context

    def scan_directory_recursive(self, directory: Path, results: list[dict[str, Any]]) -> None:
        """Recursively scan directory for context needs."""
        if not directory.is_dir():
            return

        # Skip system directories
        if any(
            skip in str(directory)
            for skip in [".git", "__pycache__", ".venv", "node_modules", ".obsidian"]
        ):
            return

        relative_path = directory.relative_to(self.repository_root)

        # Check if directory has context files
        context_files = list(directory.glob("*CONTEXT*.md"))
        readme_files = list(directory.glob("README.md")) + list(directory.glob("readme.md"))

        if not context_files:
            # Get directory analysis
            analysis = self.analyze_directory(directory)

            results.append(
                {
                    "path": str(relative_path),
                    "absolute_path": str(directory),
                    "suggested_filename": self.generate_context_filename(relative_path),
                    "has_readme": len(readme_files) > 0,
                    "readme_files": [
                        str(f.relative_to(self.repository_root)) for f in readme_files
                    ],
                    "priority": self.calculate_priority(directory),
                    "analysis": analysis,
                }
            )

        # Scan subdirectories
        for subdir in directory.iterdir():
            if subdir.is_dir():
                self.scan_directory_recursive(subdir, results)

    def analyze_directory(self, directory: Path) -> dict[str, Any]:
        """Analyze directory contents and purpose."""
        files = list(directory.glob("*"))
        py_files = [f for f in files if f.suffix == ".py" and f.is_file()]
        subdirs = [f for f in files if f.is_dir() and not f.name.startswith(".")]
        other_files = [f for f in files if f.is_file() and f.suffix != ".py"]

        # Determine primary purpose based on files
        purpose = self.determine_directory_purpose(directory, py_files, subdirs, other_files)

        return {
            "total_files": len(files),
            "python_files": len(py_files),
            "subdirectories": len(subdirs),
            "other_files": len(other_files),
            "purpose": purpose,
            "key_files": [f.name for f in py_files[:5]],  # Top 5 Python files
        }

    def determine_directory_purpose(
        self,
        directory: Path,
        _py_files: list[Path],
        _subdirs: list[Path],
        _other_files: list[Path],
    ) -> str:
        """Determine directory purpose based on contents and name."""
        dir_name = directory.name.lower()

        purpose_mapping = {
            "ai": "Artificial Intelligence systems and coordination",
            "analysis": "Data analysis and repository examination tools",
            "blockchain": "Blockchain integration and quantum consciousness systems",
            "cloud": "Cloud orchestration and distributed systems",
            "consciousness": "Consciousness modeling and cognitive frameworks",
            "copilot": "GitHub Copilot enhancement and integration systems",
            "core": "Core system components and fundamental infrastructure",
            "diagnostics": "System diagnostics and health monitoring tools",
            "enhancements": "System enhancement and optimization modules",
            "healing": "System healing, recovery, and self-repair mechanisms",
            "integration": "System integration bridges and adapters",
            "interface": "User interface and interaction components",
            "logging": "Logging infrastructure and monitoring systems",
            "memory": "Memory management and contextual storage systems",
            "ml": "Machine learning and AI model integration",
            "orchestration": "Multi-system orchestration and workflow management",
            "quantum": "Quantum computing integration and problem resolution",
            "security": "Security management and API key handling",
            "setup": "Installation, configuration, and setup scripts",
            "spine": "Transcendent spine and civilization orchestration",
            "system": "System management and coordination utilities",
            "tagging": "Semantic tagging and organizational systems",
            "tools": "Development tools and utility scripts",
            "ui": "User interface components and frameworks",
            "utils": "Utility functions and helper modules",
            "tests": "Testing infrastructure and validation systems",
            "docs": "Documentation and knowledge management",
            "config": "Configuration files and system settings",
            "data": "Data storage and management systems",
            "reports": "Reporting and analytics systems",
            "web": "Web interface and browser-based components",
            "rosetta_quest_system": "Quest management and progression tracking",
        }

        return purpose_mapping.get(
            dir_name, f"{directory.name.title()} system components and functionality"
        )

    def generate_context_filename(self, directory_path: Path) -> str:
        """Generate appropriate context filename."""
        dir_name = directory_path.name.lower()

        if dir_name in self.context_templates:
            return self.context_templates[dir_name]
        # Generate based on directory name
        clean_name = dir_name.replace("-", "_").replace(" ", "_").upper()
        return f"{clean_name}_SYSTEMS_CONTEXT.md"

    def calculate_priority(self, directory: Path) -> int:
        """Calculate priority for context file creation (1=highest, 5=lowest)."""
        dir_name = directory.name.lower()

        # Critical system directories
        critical = ["core", "ai", "integration", "quantum", "consciousness"]
        high = ["orchestration", "tools", "utils", "diagnostics", "healing"]
        medium = ["interface", "logging", "memory", "security", "setup"]
        low = ["tests", "docs", "config", "data", "reports"]

        if dir_name in critical:
            return 1
        if dir_name in high:
            return 2
        if dir_name in medium:
            return 3
        if dir_name in low:
            return 4
        return 5

    def generate_context_content(self, directory_info: dict[str, Any]) -> str:
        """Generate comprehensive context content."""
        directory = Path(directory_info["absolute_path"])
        relative_path = Path(directory_info["path"])
        analysis = directory_info["analysis"]

        # Generate context content
        context_content = f"""# 🏗️ {relative_path.name.title()} Systems Context

**Directory**: `{relative_path}`
**Purpose**: {analysis["purpose"]}
**Function**: System component management and integration

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Context Version**: v1.0

---

## 📊 Directory Overview

### **Core Function**
{analysis["purpose"]}

### **Directory Statistics**
- **Total Files**: {analysis["total_files"]}
- **Python Modules**: {analysis["python_files"]}
- **Subdirectories**: {analysis["subdirectories"]}
- **Other Files**: {analysis["other_files"]}

### **Key Components**
"""

        # Add key files
        if analysis["key_files"]:
            for key_file in analysis["key_files"]:
                file_path = directory / key_file
                file_info = self.get_file_info(file_path)
                context_content += f"- **`{key_file}`** - {file_info}\n"
        else:
            context_content += "- Configuration and utility files\n"

        # Add directory structure
        context_content += f"""

### **Directory Structure**
```
{relative_path}/
"""

        try:
            items = sorted(directory.iterdir())
            for item in items:
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    context_content += f"├── {item.name}/\n"
                else:
                    context_content += f"├── {item.name}\n"
        except (OSError, PermissionError):
            context_content += "├── [Directory contents]\n"

        context_content += "```\n\n"

        # Add system relationships
        context_content += f"""### **System Relationships**
**Integrates With**: Core infrastructure, Repository architecture, System coordination
**Depends On**: Base system components, Configuration management
**Provides To**: System functionality, Component integration, Development workflow

---

## 🏷️ Semantic Tags

### **OmniTag**
```yaml
purpose: {relative_path.name}_context_documentation
dependencies:
  - repository_structure
  - system_documentation
  - component_integration
context: Context documentation for {relative_path} directory
evolution_stage: v1.0
metadata:
  directory: {relative_path}
  component_count: {analysis["python_files"]}
  generated_timestamp: {datetime.now().isoformat()}
```

### **MegaTag**
```yaml
type: DirectoryContext
integration_points:
  - documentation_system
  - repository_architecture
  - component_mapping
related_tags:
  - SystemDocumentation
  - RepositoryStructure
  - ComponentMapping
quantum_state: ΞΨΩ∞⟨{relative_path.name.upper()}⟩→ΦΣΣ⟨CONTEXT⟩
meta_properties:
  directory_depth: {len(relative_path.parts)}
  system_importance: medium
  evolution_stage: v1.0
```

---

## 📈 Development Context

### **Evolution Stage**
v1.0 - Active Development and Integration

### **Documentation References**
- Internal component documentation
- System integration guides
- Architecture specifications
- Development workflows

### **Related Systems**
- **Core Infrastructure**: `src/core/`
- **Integration Layer**: `src/integration/`
- **Utility Functions**: `src/utils/`
- **Documentation**: `docs/`

---

## 🔧 Development Notes

### **Key Implementation Details**
Component-specific implementation focusing on {analysis["purpose"].lower()}. Integration with KILO-FOOLISH infrastructure through standardized interfaces and protocols.

### **Integration Points**
- System coordination and management
- Component discovery and indexing
- Configuration and setup integration
- Development workflow enhancement

### **Future Enhancements**
- Enhanced component integration
- Improved documentation and context
- Advanced system coordination
- Expanded functionality and features

---

*Generated by KILO-FOOLISH Directory Context Generator v1.0*
*OmniTag: [🏗️→ {relative_path.name.title()}Context, Documentation, SystemMapping]*
*MegaTag: [{relative_path.name.upper()}⨳CONTEXT⦾DOCUMENTATION→∞]*
"""

        return context_content

    def get_file_info(self, file_path: Path) -> str:
        """Get basic information about a file."""
        if not file_path.exists():
            return "File component"

        # Check component index for detailed info
        for component_key, component_data in self.component_index.items():
            if str(file_path.name) in component_key:
                return component_data.get("description", "Python module")  # type: ignore[no-any-return]

        # Generate basic description
        if file_path.suffix == ".py":
            return f"Python module - {file_path.stem.replace('_', ' ').title()}"
        if file_path.suffix == ".ps1":
            return f"PowerShell script - {file_path.stem.replace('_', ' ').title()}"
        if file_path.suffix == ".md":
            return f"Documentation - {file_path.stem.replace('_', ' ').title()}"
        return f"System file - {file_path.suffix[1:].upper()} format"

    def create_context_files(self, directories: list[dict[str, Any]]) -> list[str]:
        """Create context files for directories."""
        created_files: list[Any] = []
        # Sort by priority
        directories = sorted(directories, key=lambda x: x["priority"])

        for dir_info in directories:
            try:
                directory_path = Path(dir_info["absolute_path"])
                context_filename = dir_info["suggested_filename"]
                context_file_path = directory_path / context_filename

                # Generate content
                context_content = self.generate_context_content(dir_info)

                # Write file
                with open(context_file_path, "w", encoding="utf-8") as f:
                    f.write(context_content)

                created_files.append(str(context_file_path.relative_to(self.repository_root)))

            except (FileNotFoundError, OSError):
                logger.debug("Suppressed FileNotFoundError/OSError", exc_info=True)

        return created_files

    def update_readme_files(self, directories: list[dict[str, Any]]) -> list[str]:
        """Update README files with contextual names."""
        updated_files: list[Any] = []
        for dir_info in directories:
            if not dir_info["has_readme"]:
                continue

            try:
                for readme_path_str in dir_info["readme_files"]:
                    readme_path = self.repository_root / readme_path_str

                    if not readme_path.exists():
                        continue

                    # Generate new contextual name
                    directory_path = readme_path.parent
                    relative_dir = directory_path.relative_to(self.repository_root)
                    new_filename = self.generate_context_filename(relative_dir)
                    new_file_path = directory_path / new_filename

                    # Read existing content
                    with open(readme_path, encoding="utf-8") as f:
                        existing_content = f.read()

                    # Enhance content
                    enhanced_content = self.enhance_existing_content(existing_content, relative_dir)

                    # Rename and update
                    readme_path.rename(new_file_path)

                    with open(new_file_path, "w", encoding="utf-8") as f:
                        f.write(enhanced_content)

                    updated_files.append(
                        f"{readme_path_str} → {new_file_path.relative_to(self.repository_root)}"
                    )

            except (OSError, PermissionError, UnicodeEncodeError):
                logger.debug("Suppressed OSError/PermissionError/UnicodeEncodeError", exc_info=True)

        return updated_files

    def enhance_existing_content(self, existing_content: str, directory_path: Path) -> str:
        """Enhance existing README content."""
        return f"""# 🏗️ {directory_path.name.title()} Systems Context

**Enhanced Documentation** - *Updated by KILO-FOOLISH Context Generator*

---

{existing_content}

---

## 🏷️ Enhanced Context Information

**Directory**: `{directory_path}`
**Last Enhanced**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### **System Integration**
This directory integrates with the KILO-FOOLISH infrastructure through:
- Component indexing and discovery
- Semantic tagging and organization
- Repository architecture mapping
- Advanced development workflows

### **Semantic Tags**
- **OmniTag**: `{directory_path.name}_enhanced_context`
- **MegaTag**: `{directory_path.name.upper()}⨳ENHANCED⦾CONTEXT→∞`

---

*Enhanced by KILO-FOOLISH Directory Context Generator v1.0*
"""

    def run_comprehensive_generation(self) -> str:
        """Run comprehensive directory context generation."""
        directories = self.scan_directories()

        created_files = self.create_context_files(directories)

        updated_files = self.update_readme_files(directories)

        # Generate report
        report_content = f"""# 🏗️ Directory Context Generation Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Repository**: KILO-FOOLISH NuSyQ-Hub
**Operation**: Comprehensive Directory Context Enhancement

---

## 📊 Analysis Summary

### **Repository Structure**
- **Directories Analyzed**: {len(directories)}
- **Context Files Created**: {len(created_files)}
- **README Files Enhanced**: {len(updated_files)}

---

## 📁 Created Context Files

"""

        for created_file in created_files:
            report_content += f"✅ `{created_file}`\n"

        report_content += "\n## 🔄 Enhanced README Files\n\n"

        for updated_file in updated_files:
            report_content += f"🔄 `{updated_file}`\n"

        report_content += """

---

## 🎯 Infrastructure Integration

### **Enhancement Features**
- **Contextual Naming**: Descriptive, purpose-driven filenames
- **Semantic Tagging**: OmniTag and MegaTag integration
- **Component Discovery**: Automated component identification
- **System Analysis**: Purpose-driven directory analysis
- **Documentation Enhancement**: Comprehensive context documentation

### **Quality of Life Improvements**
- **No More Generic Names**: All README files now have descriptive context names
- **Comprehensive Documentation**: Every directory has contextual information
- **Semantic Organization**: Tagged and categorized for easy discovery
- **Integration Ready**: Compatible with KILO-FOOLISH infrastructure

---

## 📈 Next Steps

1. **Review Generated Context Files**: Validate accuracy and completeness
2. **Update System Documentation**: Integrate new context files
3. **Enhance Search Capabilities**: Leverage new contextual information
4. **Implement Continuous Updates**: Automate context maintenance
5. **Expand Integration**: Connect with existing infrastructure systems

---

*Generated by KILO-FOOLISH Directory Context Generator v1.0*
*Mission: Complete elimination of generic README.md confusion*
*Result: Comprehensive, contextual, and semantically organized documentation*
"""

        return report_content


if __name__ == "__main__":
    generator = DirectoryContextGenerator()
    report = generator.run_comprehensive_generation()

    # Save report
    report_path = Path("docs/DIRECTORY_CONTEXT_GENERATION_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

import logging

logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""🏗️ KILO-FOOLISH Directory Context Generator.

Advanced context file generation using existing infrastructure.

OmniTag: [DirectoryContext, Infrastructure, Documentation]
MegaTag: [UTILS⨳DIRECTORY⦾CONTEXT→∞]
"""

import importlib.util
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ..copilot.megatag_processor import MegaTagProcessor
# Import our existing tagging infrastructure
from ..copilot.omnitag_system import OmniTagSystem

try:
    from .Repository_Pandas_Library import RepositoryPandasLibrary
except ImportError:
    # Legacy module kept hyphenated on disk; load it dynamically as a fallback.
    legacy_module_path = Path(__file__).with_name("Repository-Pandas-Library.py")
    spec = importlib.util.spec_from_file_location(
        "repository_pandas_library_legacy", legacy_module_path
    )
    if spec is None or spec.loader is None:
        raise
    legacy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_module)
    RepositoryPandasLibrary = legacy_module.RepositoryPandasLibrary


class DirectoryContextGenerator:
    """Advanced directory context file generator using KILO-FOOLISH infrastructure.

    OmniTag: [ContextGeneration, Automation, Documentation]
    MegaTag: [AUTOMATION⨳CONTEXT⦾GENERATION→∞]
    """

    def __init__(self, repository_root: str | None = None) -> None:
        """Initialize DirectoryContextGenerator with repository_root."""
        self.repository_root = Path(repository_root or os.getcwd())

        # Initialize our existing systems
        self.omnitag_system = OmniTagSystem()
        self.megatag_processor = MegaTagProcessor()
        self.pandas_lib = RepositoryPandasLibrary(str(self.repository_root))

        # Load existing configuration
        self.load_infrastructure_config()

        # Context generation templates
        self.context_templates = {
            "src": "SOURCE_CODE_SYSTEMS_CONTEXT.md",
            "tests": "TESTING_SYSTEMS_CONTEXT.md",
            "docs": "DOCUMENTATION_SYSTEMS_CONTEXT.md",
            "config": "CONFIGURATION_SYSTEMS_CONTEXT.md",
            "data": "DATA_MANAGEMENT_CONTEXT.md",
            "logs": "LOGGING_SYSTEMS_CONTEXT.md",
            "reports": "REPORTING_SYSTEMS_CONTEXT.md",
            "web": "WEB_INTERFACE_CONTEXT.md",
        }

    def load_infrastructure_config(self) -> None:
        """Load existing infrastructure configuration."""
        try:
            # Load KILO Component Index
            component_index_path = self.repository_root / "config" / "KILO_COMPONENT_INDEX.json"
            if component_index_path.exists():
                with open(component_index_path, encoding="utf-8") as component_file:
                    self.component_index = json.load(component_file)
            else:
                self.component_index = {}

            # Load Repository Architecture Codex
            codex_path = self.repository_root / "REPOSITORY_ARCHITECTURE_CODEX.yaml"
            if codex_path.exists():
                with open(codex_path, encoding="utf-8") as codex_file:
                    self.architecture_codex = yaml.safe_load(codex_file)
            else:
                self.architecture_codex = {}

        except (FileNotFoundError, OSError, yaml.YAMLError):
            self.component_index = {}
            self.architecture_codex = {}

    def scan_repository_structure(self) -> dict[str, Any]:
        """Scan repository structure using Pandas analysis."""
        structure_data: dict[str, Any] = {
            "directories": [],
            "missing_context_files": [],
            "existing_context_files": [],
            "file_analysis": {},
        }

        # Use pandas library for comprehensive analysis
        self.pandas_lib.get_files_dataframe()
        df_dirs = self.pandas_lib.get_directory_structure()

        # Identify directories and their context needs
        for _, row in df_dirs.iterrows():
            dir_path = Path(row["path"])
            relative_path = dir_path.relative_to(self.repository_root)

            # Skip system directories
            if any(
                skip in str(relative_path)
                for skip in [".git", "__pycache__", ".venv", "node_modules"]
            ):
                continue

            structure_data["directories"].append(
                {
                    "path": str(relative_path),
                    "absolute_path": str(dir_path),
                    "file_count": row.get("file_count", 0),
                    "subdirectory_count": row.get("subdirectory_count", 0),
                }
            )

            # Check for existing context files
            context_files = list(dir_path.glob("*CONTEXT*.md"))
            readme_files = list(dir_path.glob("README.md")) + list(dir_path.glob("readme.md"))

            if context_files:
                structure_data["existing_context_files"].extend(
                    [str(f.relative_to(self.repository_root)) for f in context_files]
                )
            elif not readme_files:
                # Directory needs a context file
                suggested_name = self.generate_context_filename(relative_path)
                structure_data["missing_context_files"].append(
                    {
                        "directory": str(relative_path),
                        "suggested_filename": suggested_name,
                        "priority": self.calculate_context_priority(dir_path),
                    }
                )

        return structure_data

    def generate_context_filename(self, directory_path: Path) -> str:
        """Generate appropriate context filename based on directory purpose."""
        dir_name = directory_path.name.upper()
        parent_context = ""

        # Add parent context for nested directories
        if len(directory_path.parts) > 1:
            parent_context = directory_path.parts[-2].upper() + "_"

        # Use our template mapping or generate contextual name
        if directory_path.name in self.context_templates:
            return self.context_templates[directory_path.name]
        return f"{parent_context}{dir_name}_SYSTEMS_CONTEXT.md"

    def calculate_context_priority(self, directory_path: Path) -> int:
        """Calculate priority for context file creation (1=highest, 5=lowest)."""
        # High priority directories
        high_priority = ["src", "tests", "docs", "config", "core", "ai", "integration"]
        medium_priority = ["tools", "utils", "scripts", "data", "logs"]

        dir_name = directory_path.name.lower()

        if dir_name in high_priority:
            return 1
        if dir_name in medium_priority:
            return 2
        if directory_path.suffix in [".py", ".js", ".ts", ".md"]:
            return 3
        return 4

    def generate_context_content(self, directory_path: Path) -> str:
        """Generate comprehensive context content for directory."""
        relative_path = directory_path.relative_to(self.repository_root)

        # Analyze directory contents
        files = list(directory_path.glob("*"))
        py_files = list(directory_path.glob("*.py"))

        # Extract information from component index
        component_info = self.extract_component_info(str(relative_path))

        # Extract architecture information
        arch_info = self.extract_architecture_info(str(relative_path))

        # Generate OmniTag and MegaTag
        omnitag_data = self.generate_omnitag(relative_path, component_info)
        megatag_data = self.generate_metatag(relative_path, arch_info)

        # Build context content
        context_content = f"""# 🏗️ {relative_path.name.title()} Systems Context

**Directory**: `{relative_path}`
**Purpose**: {arch_info.get("purpose", "System component directory")}
**Function**: {arch_info.get("function", "Component functionality and integration")}

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Context Version**: v1.0

---

## 📊 Directory Overview

### **Core Function**
{arch_info.get("function", f"{relative_path.name.title()} system components and functionality")}

### **Key Components**
"""

        # Add key components
        if arch_info.get("key_components"):
            for component in arch_info["key_components"]:
                context_content += f"- **{component}**\n"
        elif py_files:
            for py_file in py_files[:5]:  # Limit to top 5
                file_info = component_info.get(py_file.name, {})
                desc = file_info.get("description", "Python module")
                context_content += f"- **`{py_file.name}`** - {desc}\n"
        else:
            context_content += "- Configuration and utility files\n"

        context_content += f"""

### **Directory Structure**
```
{relative_path}/
"""

        # Add structure
        for item in sorted(files):
            if item.is_dir() and not item.name.startswith("."):
                context_content += f"├── {item.name}/\n"
            elif not item.name.startswith("."):
                context_content += f"├── {item.name}\n"

        context_content += "```\n\n"

        # Add relationships
        if arch_info.get("relationships"):
            context_content += "### **System Relationships**\n"
            relationships = arch_info["relationships"]

            if relationships.get("integrates_with"):
                integrates = ", ".join(relationships["integrates_with"])
                context_content += f"**Integrates With**: {integrates}\n"
            if relationships.get("depends_on"):
                depends = ", ".join(relationships["depends_on"])
                context_content += f"**Depends On**: {depends}\n"
            if relationships.get("provides_to"):
                provides = ", ".join(relationships["provides_to"])
                context_content += f"**Provides To**: {provides}\n"

            context_content += "\n"

        # Add OmniTag
        context_content += f"""## 🏷️ Semantic Tags

### **OmniTag**
```yaml
{yaml.dump(omnitag_data, default_flow_style=False)}```

### **MegaTag**
```yaml
{yaml.dump(megatag_data, default_flow_style=False)}```

---

## 📈 Development Context

### **Evolution Stage**
{arch_info.get("evolution_stage", "v1.0 - Initial Implementation")}

### **Documentation References**
"""

        if arch_info.get("documentation"):
            for doc in arch_info["documentation"]:
                context_content += f"- {doc}\n"
        else:
            context_content += "- Internal component documentation\n- System integration guides\n"

        context_content += f"""

### **Related Systems**
- **Core Infrastructure**: `src/core/`
- **Integration Layer**: `src/integration/`
- **Utility Functions**: `src/utils/`
- **Documentation**: `docs/`

---

## 🔧 Development Notes

### **Key Implementation Details**
{component_info.get("implementation_notes", "Component-specific implementation and integration details.")}

### **Integration Points**
{component_info.get("integration_points", "System integration and dependency management.")}

### **Future Enhancements**
- Enhanced component integration
- Improved documentation and context
- Advanced system coordination

---

*Generated by KILO-FOOLISH Directory Context Generator v1.0*
*OmniTag: [🏗️→ {relative_path.name.title()}Context, Documentation, SystemMapping]*
*MegaTag: [{relative_path.name.upper()}⨳CONTEXT⦾DOCUMENTATION→∞]*
"""

        return context_content

    def extract_component_info(self, directory_path: str) -> dict[str, Any]:
        """Extract component information from KILO Component Index."""
        relevant_components: dict[str, Any] = {}
        for component_data in self.component_index.values():
            if directory_path in component_data.get("path", ""):
                relevant_components[Path(component_data["path"]).name] = component_data

        return relevant_components

    def extract_architecture_info(self, directory_path: str) -> dict[str, Any]:
        """Extract architecture information from Repository Architecture Codex."""
        # Look for directory in architecture codex
        codex_sections = self.architecture_codex.get("architecture", {}).get("directories", {})

        for section_name, section_data in codex_sections.items():
            if section_name in directory_path or directory_path in section_data.get("path", ""):
                return dict(section_data)

        # Return default structure
        return {
            "purpose": f"{Path(directory_path).name.title()} system components",
            "function": "Component functionality and system integration",
            "evolution_stage": "v1.0 - Active Development",
        }

    def generate_omnitag(self, directory_path: Path, component_info: dict) -> dict[str, Any]:
        """Generate OmniTag for directory."""
        return {
            "purpose": f"{directory_path.name}_context_documentation",
            "dependencies": ["repository_structure", "system_documentation"],
            "context": f"Context documentation for {directory_path} directory",
            "evolution_stage": "v1.0",
            "metadata": {
                "directory": str(directory_path),
                "component_count": len(component_info),
                "generated_timestamp": datetime.now().isoformat(),
            },
        }

    def generate_metatag(self, directory_path: Path, arch_info: dict) -> dict[str, Any]:
        """Generate MegaTag for directory."""
        return {
            "type": "DirectoryContext",
            "integration_points": [
                "documentation_system",
                "repository_architecture",
                "component_mapping",
            ],
            "related_tags": [
                "SystemDocumentation",
                "RepositoryStructure",
                "ComponentMapping",
            ],
            "quantum_state": f"ΞΨΩ∞⟨{directory_path.name.upper()}⟩→ΦΣΣ⟨CONTEXT⟩",
            "meta_properties": {
                "directory_depth": len(directory_path.parts),
                "system_importance": arch_info.get("importance", "medium"),
                "evolution_stage": arch_info.get("evolution_stage", "v1.0"),
            },
        }

    def create_missing_context_files(self, structure_data: dict[str, Any]) -> list[str]:
        """Create missing context files."""
        created_files: list[Any] = []
        # Sort by priority
        missing_files = sorted(
            structure_data["missing_context_files"],
            key=lambda x: x["priority"],
        )

        for missing_file in missing_files:
            directory_path = Path(missing_file["directory"])
            full_directory_path = self.repository_root / directory_path

            context_filename = missing_file["suggested_filename"]
            context_file_path = full_directory_path / context_filename

            # Generate content
            context_content = self.generate_context_content(full_directory_path)

            # Write file
            try:
                with open(context_file_path, "w", encoding="utf-8") as context_handle:
                    context_handle.write(context_content)

                created_files.append(str(context_file_path.relative_to(self.repository_root)))

            except (OSError, FileNotFoundError):
                logger.debug("Suppressed FileNotFoundError/OSError", exc_info=True)

        return created_files

    def update_existing_readme_files(self) -> list[str]:
        """Find and update generic README.md files with contextual names."""
        updated_files: list[Any] = []
        # Find all README.md files
        readme_files = list(self.repository_root.glob("**/README.md"))
        readme_files.extend(list(self.repository_root.glob("**/readme.md")))

        for readme_file in readme_files:
            # Skip root README
            if readme_file.parent == self.repository_root:
                continue

            relative_path = readme_file.relative_to(self.repository_root)
            directory_path = readme_file.parent

            # Generate new contextual name
            new_filename = self.generate_context_filename(
                directory_path.relative_to(self.repository_root)
            )
            new_file_path = directory_path / new_filename

            try:
                # Read existing content
                with open(readme_file, encoding="utf-8") as readme_handle:
                    existing_content = readme_handle.read()

                # Generate enhanced content
                enhanced_content = self.enhance_existing_content(existing_content, directory_path)

                # Move and enhance file
                readme_file.rename(new_file_path)

                with open(new_file_path, "w", encoding="utf-8") as new_file_handle:
                    new_file_handle.write(enhanced_content)

                updated_files.append(
                    f"{relative_path} → {new_file_path.relative_to(self.repository_root)}"
                )

            except (OSError, FileNotFoundError):
                logger.debug("Suppressed FileNotFoundError/OSError", exc_info=True)

        return updated_files

    def enhance_existing_content(self, existing_content: str, directory_path: Path) -> str:
        """Enhance existing content with our infrastructure."""
        # Add header enhancement
        relative_path = directory_path.relative_to(self.repository_root)

        return f"""# 🏗️ {relative_path.name.title()} Systems Context

**Enhanced Documentation** - *Updated by KILO-FOOLISH Context Generator*

---

{existing_content}

---

## 🏷️ Enhanced Context Information

**Directory**: `{relative_path}`
**Last Enhanced**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### **System Integration**
This directory integrates with the KILO-FOOLISH infrastructure through:
- Component indexing and discovery
- Semantic tagging and organization
- Repository architecture mapping
- Advanced development workflows

### **Semantic Tags**
- **OmniTag**: `{relative_path.name}_enhanced_context`
- **MegaTag**: `{relative_path.name.upper()}⨳ENHANCED⦾CONTEXT→∞`

---

*Enhanced by KILO-FOOLISH Directory Context Generator v1.0*
"""

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive directory context analysis report."""
        structure_data = self.scan_repository_structure()

        created_files = self.create_missing_context_files(structure_data)

        updated_files = self.update_existing_readme_files()

        # Generate report
        report_content = f"""# 🏗️ Directory Context Generation Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Repository**: KILO-FOOLISH NuSyQ-Hub
**Operation**: Comprehensive Directory Context Enhancement

---

## 📊 Analysis Summary

### **Repository Structure**
- **Total Directories Analyzed**: {len(structure_data["directories"])}
- **Existing Context Files**: {len(structure_data["existing_context_files"])}
- **Missing Context Files**: {len(structure_data["missing_context_files"])}

### **Operation Results**
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

### **Systems Utilized**
- **OmniTag System**: Semantic tagging and organization
- **MegaTag Processor**: Advanced contextual relationships
- **Repository Pandas Library**: Data-driven analysis
- **KILO Component Index**: Component discovery and mapping
- **Repository Architecture Codex**: System architecture integration

### **Enhancement Features**
- **Contextual Naming**: Descriptive, purpose-driven filenames
- **Semantic Tagging**: OmniTag and MegaTag integration
- **Architecture Mapping**: Integration with repository codex
- **Component Discovery**: Automated component identification
- **Relationship Mapping**: System interdependency analysis

---

## 📈 Next Steps

1. **Review Generated Context Files**: Validate accuracy and completeness
2. **Update System Documentation**: Integrate new context files
3. **Enhance Component Index**: Update with new contextual information
4. **Extend Architecture Codex**: Include new directory mappings
5. **Implement Continuous Updates**: Automate context maintenance

---

*Generated by KILO-FOOLISH Directory Context Generator v1.0*
*OmniTag: [🏗️→ DirectoryContextReport, Documentation, SystemEnhancement]*
*MegaTag: [UTILS⨳DIRECTORY⦾CONTEXT→REPORT∞]*
"""

        return report_content


if __name__ == "__main__":
    # Initialize and run directory context generation
    generator = DirectoryContextGenerator()

    # Generate comprehensive report and create context files
    report = generator.generate_comprehensive_report()

    # Save report
    report_path = Path("docs/DIRECTORY_CONTEXT_GENERATION_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(report)

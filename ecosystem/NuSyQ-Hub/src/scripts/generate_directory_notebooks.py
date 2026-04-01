#!/usr/bin/env python3
"""🎯 KILO-FOOLISH Directory Notebook Generator.

Automatically generates comprehensive Jupyter notebooks for each directory.

OmniTag: {
    "purpose": "notebook_generation_system",
    "type": "automation_tool",
    "evolution_stage": "v1.0_comprehensive"
}
"""

import builtins
import contextlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DirectoryNotebookGenerator:
    """Generate comprehensive notebooks for each directory."""

    def __init__(self, repo_root: str) -> None:
        """Initialize DirectoryNotebookGenerator with repo_root."""
        self.repo_root = Path(repo_root)
        self.notebooks_dir = self.repo_root / "docs" / "notebooks" / "directory_notebooks"
        self.notebooks_dir.mkdir(parents=True, exist_ok=True)

    def _build_header_source(
        self, directory_name: str, directory_path: Path, dir_info: dict[str, Any]
    ) -> list[str]:
        """Build markdown header source lines for notebook."""
        header_intro = f"# 📁 {directory_name.upper()} Directory Overview\n\n"
        omni_tag = (
            f'**OmniTag**: {{"type": "directory_analysis", '
            f'"target": "{directory_name}", '
            f'"quantum_context": "directory_consciousness"}}\n\n'
        )
        mega_tag = (
            '**MegaTag**: {"scope": "directory_management", '
            '"integration_points": ["file_analysis", "module_tracking"], '
            '"enhancement_stage": "comprehensive_mapping"}\n\n'
        )
        rshts = f"**RSHTS**: ΞΨΩ∞⟨{directory_name.upper()}⟩→ΦΣΣΔ\n\n"
        mission = (
            f"## 🎯 Directory Mission\n\n"
            f"Interactive analysis and management system for the "
            f"`{directory_name}` directory.\n\n"
        )
        stats = (
            f"**Path**: `{directory_path}`\n"
            f"**Files**: {dir_info['file_count']} files\n"
            f"**Subdirectories**: {dir_info['subdir_count']} subdirectories\n"
            f"**Total Size**: {dir_info['total_size_mb']:.2f} MB"
        )
        return [header_intro + omni_tag + mega_tag + rshts + mission + stats]

    def create_notebook_template(self, directory_name: str, directory_path: Path) -> dict[str, Any]:
        """Create notebook template for a directory."""
        # Analyze directory contents
        dir_info = self.analyze_directory(directory_path)

        return {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        (
                            f"# 📁 {directory_name.upper()} Directory Overview\\n\\n"
                            f'**OmniTag**: {{"type": "directory_analysis", "target": "{directory_name}", '
                            f'"quantum_context": "directory_consciousness"}}\\n\\n'
                            f'**MegaTag**: {{"scope": "directory_management", "integration_points": ["file_analysis", "module_tracking"], '
                            f'"enhancement_stage": "comprehensive_mapping"}}\\n\\n'
                            f"**RSHTS**: ΞΨΩ∞⟨{directory_name.upper()}⟩→ΦΣΣΔ\\n\\n"
                            f"## 🎯 Directory Mission\\n\\n"
                            f"Interactive analysis and management system for the `{directory_name}` directory.\\n\\n"
                            f"**Path**: `{directory_path}`\\n"
                            f"**Files**: {dir_info['file_count']} files\\n"
                            f"**Subdirectories**: {dir_info['subdir_count']} subdirectories\\n"
                            f"**Total Size**: {dir_info['total_size_mb']:.2f} MB"
                        ),
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        f"# 🔄 {directory_name.upper()} Directory Analysis System\\n",
                        "import os\\n",
                        "import json\\n",
                        "import subprocess\\n",
                        "from pathlib import Path\\n",
                        "from datetime import datetime\\n",
                        "from collections import defaultdict\\n",
                        "import time\\n\\n",
                        "# Directory paths\\n",
                        f"repo_root = Path(os.getenv('NU_SYQ_REPO_ROOT', '{self.repo_root.as_posix()}'))\\n",
                        f"target_dir = repo_root / '{directory_name}'\\n",
                        "os.chdir(repo_root)\\n\\n",
                        "# Analysis tracking\\n",
                        (
                            f"{directory_name}_analysis = {{\\n"
                            f"    'timestamp': datetime.now().isoformat(),\\n"
                            f"    'directory': '{directory_name}',\\n"
                        ),
                        ("    'path': str(target_dir),\\n    'files': {},\\n"),
                        ("    'subdirectories': {},\\n    'analysis_results': {},\\n"),
                        f"    'quantum_context': '{directory_name}_consciousness_tracking'\\n",
                        "}\\n\\n",
                        f"print(f'📁 {directory_name.upper()} DIRECTORY ANALYSIS')\\n",
                        "print('=' * 60)\\n",
                        "print(f'📂 Target Directory: {target_dir}')\\n",
                        (
                            f"print(f'⏰ Analysis Time: {{{directory_name}_analysis[\"timestamp\"]}}')\\n"
                        ),
                        (
                            f"print(f'🧠 Quantum Context: {{{directory_name}_analysis[\"quantum_context\"]}}')\\n"
                        ),
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        f"# Comprehensive directory structure analysis\\n"
                        f"def analyze_{directory_name}_structure():\\n"
                        f'    \\"\\"\\"Analyze {directory_name} directory structure and contents\\"\\"\\"\\n'
                        f"    print(f'🔍 Analyzing {{target_dir}} structure...')\\n\\n"
                        f"    if not target_dir.exists():\\n"
                        f"        print(f'❌ Directory {{target_dir}} does not exist')\\n"
                        f"        return {{}}\\n\\n"
                        f"    structure_info = {{\\n"
                        f"        'files': [],\\n"
                        f"        'subdirectories': [],\\n"
                        f"        'file_types': defaultdict(int),\\n"
                        f"        'total_files': 0,\\n"
                        f"        'total_size': 0\\n"
                        f"    }}\\n\\n"
                        f"    try:\\n"
                        f"        # Analyze files and subdirectories\\n"
                        f"        for item in sorted(target_dir.rglob('*')):\\n"
                        f"            if item.is_file():\\n"
                        f"                try:\\n"
                        f"                    file_size = item.stat().st_size\\n"
                        f"                    relative_path = item.relative_to(target_dir)\\n"
                        f"                    \\n"
                        f"                    file_info = {{\\n"
                        f"                        'name': item.name,\\n"
                        f"                        'path': str(relative_path),\\n"
                        f"                        'full_path': str(item),\\n"
                        f"                        'size': file_size,\\n"
                        f"                        'extension': item.suffix,\\n"
                        f"                        'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()\\n"
                        f"                    }}\\n"
                        f"                    \\n"
                        f"                    structure_info['files'].append(file_info)\\n"
                        f"                    structure_info['file_types'][item.suffix] += 1\\n"
                        f"                    structure_info['total_files'] += 1\\n"
                        f"                    structure_info['total_size'] += file_size\\n"
                        f"                    \\n"
                        f"                except (PermissionError, FileNotFoundError):\\n"
                        f"                    continue\\n"
                        f"            \\n"
                        f"            elif item.is_dir():\\n"
                        f"                relative_path = item.relative_to(target_dir)\\n"
                        f"                if str(relative_path) != '.' and not any(part.startswith('.') for part in relative_path.parts):\\n"
                        f"                    structure_info['subdirectories'].append({{\\n"
                        f"                        'name': item.name,\\n"
                        f"                        'path': str(relative_path),\\n"
                        f"                        'full_path': str(item)\\n"
                        f"                    }})\\n\\n"
                        f'        print(f\'✅ Analysis complete: {{structure_info["total_files"]}} files, {{len(structure_info["subdirectories"])}} subdirectories\')\\n'
                        f"        \\n"
                        f"    except Exception as e:\\n"
                        f"        print(f'❌ Analysis failed: {{e}}')\\n"
                        f"        return {{}}\\n\\n"
                        f"    # Store results\\n"
                        f"    {directory_name}_analysis['analysis_results'] = structure_info\\n"
                        f"    return structure_info\\n\\n"
                        f"# Execute analysis\\n"
                        f"structure_results = analyze_{directory_name}_structure()\\n\\n"
                        f"# Display results\n"
                        f"if structure_results:\n"
                        f"    print(f'\\n📊 STRUCTURE ANALYSIS RESULTS:')\n"
                        f'    total_files = structure_results["total_files"]\n'
                        f'    subdirs_count = len(structure_results["subdirectories"])\n'
                        f'    total_size_mb = structure_results["total_size"] / (1024*1024)\n'
                        f"    print(f'📄 Total Files: {{total_files}}')\n"
                        f"    print(f'📁 Subdirectories: {{subdirs_count}}')\n"
                        f"    print(f'💾 Total Size: {{total_size_mb:.2f}} MB')\n"
                        f"    \n"
                        f"    if structure_results['file_types']:\n"
                        f"        print(f'\\n🏷️ File Types:')\n"
                        f"        top_types = sorted(structure_results['file_types'].items(), key=lambda x: x[1], reverse=True)[:10]\n"
                        f"        for ext, count in top_types:\n"
                        f"            ext_display = ext if ext else '(no extension)'\n"
                        f"            print(f'  📋 {{ext_display:<15}} : {{count}} files')\n"
                        f"    \n"
                        f"    if structure_results['subdirectories']:\n"
                        f"        print(f'\\n📁 Subdirectories:')\n"
                        f"        for subdir in structure_results['subdirectories'][:20]:\n"
                        f"            print(f'  🔹 {{subdir[\"path\"]}}')\n"
                        f"        if len(structure_results['subdirectories']) > 20:\n"
                        f"            print(f'  ... and {{len(structure_results[\"subdirectories\"]) - 20}} more')",
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        f"# Interactive file exploration\\n"
                        f"def explore_{directory_name}_file(file_path: str, max_lines: int = 50):\\n"
                        f'    \\"\\"\\"Explore specific file in {directory_name} directory\\"\\"\\"\\n'
                        f"    full_path = target_dir / file_path\\n"
                        f"    \\n"
                        f"    if not full_path.exists():\\n"
                        f"        print(f'❌ File {{file_path}} not found in {{target_dir}}')\\n"
                        f"        return\\n"
                        f"    \\n"
                        f"    try:\\n"
                        f"        print(f'📄 File: {{file_path}}')\\n"
                        f"        print(f'📂 Full Path: {{full_path}}')\\n"
                        f"        print(f'💾 Size: {{full_path.stat().st_size}} bytes')\\n"
                        f"        print(f'📅 Modified: {{datetime.fromtimestamp(full_path.stat().st_mtime)}}')\\n"
                        f"        \\n"
                        f"        # Read file content\\n"
                        f"        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:\\n"
                        f"            lines = f.readlines()\\n"
                        f"        \\n"
                        f"        print(f'\\\\n📝 Content Preview (first {{min(max_lines, len(lines))}} lines):')\\n"
                        f"        print('-' * 50)\\n"
                        f"        \\n"
                        f"        for i, line in enumerate(lines[:max_lines], 1):\\n"
                        f"            print(f'{{i:3d}}: {{line.rstrip()}}')\\n"
                        f"        \\n"
                        f"        if len(lines) > max_lines:\\n"
                        f"            print(f'... ({{len(lines) - max_lines}} more lines)')\\n"
                        f"        \\n"
                        f"        print('-' * 50)\\n"
                        f"        print(f'📊 Total Lines: {{len(lines)}}')\\n"
                        f"        \\n"
                        f"    except Exception as e:\\n"
                        f"        print(f'❌ Error reading file: {{e}}')\\n\\n"
                        f"def list_{directory_name}_files_by_type(file_extension: str = '.py'):\\n"
                        f'    \\"\\"\\"List files of specific type in {directory_name}\\"\\"\\"\\n'
                        f"    if not structure_results:\\n"
                        f"        print('❌ Run structure analysis first')\\n"
                        f"        return\\n"
                        f"    \\n"
                        f"    matching_files = [f for f in structure_results['files'] if f['extension'] == file_extension]\\n"
                        f"    \\n"
                        f"    print(f'🔍 Files with extension {{file_extension}} in {directory_name}:')\\n"
                        f"    print(f'📊 Found {{len(matching_files)}} files')\\n"
                        f"    \\n"
                        f"    for file_info in sorted(matching_files, key=lambda x: x['size'], reverse=True)[:20]:\\n"
                        f"        size_kb = file_info['size'] / 1024\\n"
                        f"        print(f'  📄 {{file_info[\"path\"]:<40}} ({{size_kb:.1f}} KB)')\\n"
                        f"    \\n"
                        f"    if len(matching_files) > 20:\\n"
                        f"        print(f'  ... and {{len(matching_files) - 20}} more files')\\n\\n"
                        f"# Interactive exploration examples\\n"
                        f"print(f'\\\\n🎯 Interactive Exploration Functions Available:')\\n"
                        f"print(f'  📄 explore_{directory_name}_file(\"relative/path/to/file.ext\") - View file content')\\n"
                        f"print(f'  🔍 list_{directory_name}_files_by_type(\".py\") - List files by extension')\\n"
                        f"print(f'  📊 {directory_name}_analysis - Complete analysis data dictionary')\\n\\n"
                        f"# Example usage:\\n"
                        f"if structure_results and structure_results['files']:\\n"
                        f"    example_file = structure_results['files'][0]\\n"
                        f"    print(f'\\\\n📝 Example - Viewing first file: {{example_file[\"path\"]}}')\\n"
                        f"    explore_{directory_name}_file(example_file['path'], max_lines=10)",
                    ],
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"## 🎮 {directory_name.upper()} Quest Integration\\n\\n"
                        f"### 🏆 Directory Quests\\n"
                        f"- **📊 Analysis Quest**: Complete comprehensive directory analysis\\n"
                        f"- **🔍 Exploration Quest**: Explore at least 5 files in the directory\\n"
                        f"- **🏷️ Tagging Quest**: Apply OmniTag/MegaTag to all major components\\n"
                        f"- **🧠 Consciousness Quest**: Integrate findings with repository consciousness\\n\\n"
                        f"### 📈 Progress Tracking\\n"
                        f"- **Files Analyzed**: 0/{dir_info['file_count']}\\n"
                        f"- **Subdirectories Explored**: 0/{dir_info['subdir_count']}\\n"
                        f"- **Integration Status**: 🔄 In Progress\\n"
                        f"- **Consciousness Sync**: 🔄 Pending\\n\\n"
                        f"### 🎯 Next Actions\\n"
                        f"1. Run comprehensive structure analysis\\n"
                        f"2. Explore key files and modules\\n"
                        f"3. Update consciousness bridge with findings\\n"
                        f"4. Integrate with master navigation system\\n\\n"
                        f"### 🔗 Navigation Links\\n"
                        f"- 🏠 [Root Overview](root_level_overview.ipynb)\\n"
                        f"- 🎯 [Master Notebook](../MASTER_KILO_FOOLISH_NOTEBOOK.ipynb)\\n"
                        f"- 🧠 [Consciousness Tracker](../consciousness_tracker.ipynb)\\n"
                        f"- 🎮 [Quest Progress](../quest_progress.ipynb)",
                    ],
                },
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {
                    "codemirror_mode": {
                        "name": "ipython",
                        "version": 3,
                    },
                    "file_extension": ".py",
                    "mimetype": "text/x-python",
                    "name": "python",
                    "nbconvert_exporter": "python",
                    "pygments_lexer": "ipython3",
                    "version": "3.11.0",
                },
            },
            "nbformat": 4,
            "nbformat_minor": 4,
        }

    def analyze_directory(self, directory_path: Path) -> dict[str, Any]:
        """Analyze directory for metadata."""
        if not directory_path.exists():
            return {"file_count": 0, "subdir_count": 0, "total_size_mb": 0}

        file_count = 0
        subdir_count = 0
        total_size = 0

        try:
            for item in directory_path.rglob("*"):
                if item.is_file():
                    file_count += 1
                    with contextlib.suppress(builtins.BaseException):
                        total_size += item.stat().st_size
                elif item.is_dir() and item != directory_path:
                    subdir_count += 1
        except (OSError, PermissionError):
            logger.debug("Suppressed OSError/PermissionError", exc_info=True)

        return {
            "file_count": file_count,
            "subdir_count": subdir_count,
            "total_size_mb": total_size / (1024 * 1024),
        }

    def generate_all_notebooks(self) -> None:
        """Generate notebooks for all directories."""
        generated_notebooks: list[Any] = []
        # Get all directories in repo root
        for item in sorted(self.repo_root.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                notebook_content = self.create_notebook_template(item.name, item)
                notebook_path = self.notebooks_dir / f"{item.name.lower()}_overview.ipynb"

                # Write notebook
                with open(notebook_path, "w", encoding="utf-8") as f:
                    json.dump(notebook_content, f, indent=2)

                generated_notebooks.append(
                    {
                        "directory": item.name,
                        "notebook_path": str(notebook_path),
                        "directory_path": str(item),
                    }
                )

        return generated_notebooks


def main():
    """Main execution function."""
    repo_root = Path(os.getenv("NU_SYQ_REPO_ROOT", Path(__file__).resolve().parents[2]))
    generator = DirectoryNotebookGenerator(str(repo_root))

    # Generate all notebooks
    notebooks = generator.generate_all_notebooks()

    # Save generation report
    report = {
        "timestamp": datetime.now().isoformat(),
        "generator_version": "1.0",
        "repo_root": repo_root,
        "notebooks_generated": len(notebooks),
        "notebooks": notebooks,
    }

    report_path = Path(repo_root) / "docs" / "notebooks" / "notebook_generation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return notebooks


if __name__ == "__main__":
    notebooks = main()

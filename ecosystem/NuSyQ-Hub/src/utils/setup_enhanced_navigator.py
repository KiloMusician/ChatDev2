# setup_enhanced_navigator.py
"""Setup script for Enhanced Wizard Navigator."""

import subprocess
import sys
from pathlib import Path


def install_requirements() -> None:
    """Install required packages."""
    requirements = [
        "rich>=13.0.0",
        "pandas>=2.0.0",
        "requests>=2.31.0",
        "jupyter-client>=8.0.0",
        "ollama-python>=0.1.0",
    ]

    for package in requirements:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=False)


def setup_directories() -> None:
    """Create necessary directories."""
    dirs = [
        "obsidian_vault",
        "godot_projects",
        "chatdev_projects",
        "spell_crafting",
    ]

    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)


if __name__ == "__main__":
    install_requirements()
    setup_directories()

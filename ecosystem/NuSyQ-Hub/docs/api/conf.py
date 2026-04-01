"""Sphinx configuration for API documentation."""

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

project = "NuSyQ-Hub"
author = "NuSyQ-Hub Contributors"
copyright_text = f"{datetime.now():%Y}, {author}"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

html_theme = "alabaster"

# Mock heavy optional dependencies during doc build
autodoc_mock_imports = [
    "openai",
    "anthropic",
    "pandas",
    "requests",
    "numpy",
    "torch",
    "tensorflow",
]

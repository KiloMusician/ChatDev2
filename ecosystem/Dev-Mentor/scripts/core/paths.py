"""Centralized path management for DevMentor.

All paths are relative to the repository root, ensuring portability.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

VSCODE_DIR = ROOT / ".vscode"
SCRIPTS_DIR = ROOT / "scripts"
TUTORIALS_DIR = ROOT / "tutorials"
CHALLENGES_DIR = ROOT / "challenges"
DOCS_DIR = ROOT / "docs"
REPORTS_DIR = ROOT / "reports"
EXPORTS_DIR = ROOT / "exports"
DEVMENTOR_DIR = ROOT / ".devmentor"

STATE_JSON = DEVMENTOR_DIR / "state.json"
SETTINGS_JSON = VSCODE_DIR / "settings.json"
TASKS_JSON = VSCODE_DIR / "tasks.json"
EXTENSIONS_JSON = VSCODE_DIR / "extensions.json"

README = ROOT / "README.md"
START_HERE = ROOT / "START_HERE.md"

DEVMENTOR_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

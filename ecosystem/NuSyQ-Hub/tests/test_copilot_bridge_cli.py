"""Smoke tests for the Copilot enhancement bridge CLI and import path.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure src is on path for module resolution when running subprocess
SRC_PATH = Path(__file__).resolve().parents[1] / "src"

pytestmark = pytest.mark.no_cov


def test_bridge_cli_runs():
    """CLI command should execute and report initialization."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_PATH)
    result = subprocess.run(
        [sys.executable, "-m", "copilot.bridge_cli"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "Initialized CopilotEnhancementBridge" in result.stdout


def test_bridge_class_import():
    """The bridge should be importable and produce a context summary."""
    sys.path.insert(0, str(SRC_PATH))
    from copilot.copilot_enhancement_bridge import CopilotEnhancementBridge

    bridge = CopilotEnhancementBridge()
    summary = bridge.get_consciousness_summary()
    assert "consciousness_level" in summary

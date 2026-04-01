"""Tests for agent_context_cli registration logic (non-networking).

This test ensures a local file can be registered into the AgentContextManager.
"""

import subprocess
import sys
from pathlib import Path


def test_cli_register(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    sample = repo / "note.txt"
    sample.write_text("Sample context content", encoding="utf-8")

    # Run the CLI against the temporary repo
    cmd = [
        sys.executable,
        str(Path.cwd() / "scripts" / "agent_context_cli.py"),
        "--namespace",
        "testns",
        "--path",
        str(sample),
    ]
    # Run within tmp_path as cwd
    res = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    assert "Registered:" in res.stdout

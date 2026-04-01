import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_cov


def test_generate_prune_plan_autocommit_guard():
    script = Path("scripts/generate_prune_plan.py")
    assert script.exists()
    env = os.environ.copy()
    # Ensure Python can import src package
    env["PYTHONPATH"] = str(Path.cwd())
    env["PRUNE_AUTOCOMMIT"] = "true"
    # Ensure token is not set
    env.pop("GITHUB_TOKEN", None)
    env.pop("GITHUB_REPOSITORY", None)
    proc = subprocess.run(["python", str(script)], capture_output=True, text=True, env=env)
    assert proc.returncode in (0, 1)
    # Confirm message indicates PRUNE_AUTOCOMMIT enabled but no token
    assert "PRUNE_AUTOCOMMIT enabled" in proc.stdout or "PRUNE_AUTOCOMMIT enabled" in proc.stderr

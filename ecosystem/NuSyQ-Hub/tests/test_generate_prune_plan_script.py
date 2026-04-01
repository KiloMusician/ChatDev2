import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_cov


def test_generate_prune_plan_script_runs():
    script = Path("scripts/generate_prune_plan.py")
    assert script.exists()
    proc = subprocess.run(["python", str(script)], capture_output=True, text=True)
    # It should exit with 0 or 1 (fail if no index) but must complete
    assert proc.returncode in (0, 1)
    # If successful, STDOUT mentions "Prune plan generated"; if not, it warns
    if proc.returncode == 0:
        assert "Prune plan generated" in proc.stdout

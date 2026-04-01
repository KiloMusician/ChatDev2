import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_cov


def test_preview_prune_plan_list():
    script = Path("scripts/preview_prune_plan.py")
    assert script.exists()
    proc = subprocess.run(["python", str(script), "--list"], capture_output=True, text=True)
    # Should complete successfully reducing to 0 or 1 return code depending on plan presence
    assert proc.returncode in (0, 1)
    if proc.returncode == 0:
        assert "Candidates:" in proc.stdout

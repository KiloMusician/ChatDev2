import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_cov


def test_maintenance_runner_preview(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    runner = root / "scripts" / "maintenance_runner.py"
    # Run maintenance runner with index+generate+preview; do not perform archival
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = str(root)
    proc = subprocess.run(
        ["python", str(runner), "--index", "--generate-plan", "--preview"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0
    # Expect at least one of the maintenance messages in stdout/stderr
    assert (
        "Prune plan generated" in proc.stdout
        or "Previewing prune plan" in proc.stdout
        or "Retrieval engine built successfully" in proc.stdout
    )

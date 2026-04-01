#!/usr/bin/env python3
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
branch = "feature/batch-014"
files = [
    "tests/e2e/test_complete_journeys.py",
    "tests/integration/test_copilot_chatdev_pipeline.py",
    "tests/llm_testing/simple_test.py",
    "tests/quantum_system_test.py",
    "tests/smoke/test_unified_clis_smoke.py",
    "tests/test_agent_task_router.py",
    "tests/test_auto_fix_validation.py",
    "tests/test_chatdev_integration.py",
    "tests/test_culture_ship_strategic_advisor.py",
    "tests/test_heartbeat_smoke.py",
    "tests/test_imports_expanded.py",
    "tests/test_multi_ai_integration.py",
    "tests/test_nusyq_snapshots.py",
    "tests/test_orchestration_comprehensive.py",
    "tests/test_quantum_problem_resolver_light.py",
    "tests/test_quick_imports.py",
    "tests/test_repository_compendium.py",
]


def run(cmd):
    print("RUN:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(repo))
    if res.returncode != 0:
        raise SystemExit(res.returncode)


run(["git", "-C", str(repo), "checkout", "-b", branch])
for f in files:
    run(["git", "-C", str(repo), "add", f])
run(["git", "-C", str(repo), "commit", "-m", "batched(commit): add 17 files from batch 014"])
run(["git", "-C", str(repo), "push", "-u", "origin", branch])
print("Batch", branch, "pushed")

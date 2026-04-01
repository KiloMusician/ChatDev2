#!/usr/bin/env python3
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
branch = "feature/batch-001"
files = [
    "ACTIVATE_SYSTEM.py",
    "AI_AGENT_COORDINATION_MASTER.py",
    "FULL_SYSTEM_INTEGRATION_TEST.py",
    "activate_zen_engine.py",
    "analyze_errors.py",
    "autonomous_dev.py",
    "check_maze_results.py",
    "create_incremental_td_rpg.py",
    "demo_ai_game_creation.py",
    "final_health_check.py",
    "log_batch3_quest.py",
    "nusyq_clean_clone",
    "perpetual_progress.py",
    "run_phase_2_integration.py",
    "run_phase_3_collaboration.py",
    "start-all-servers.ps1",
    "test_fixes_validation.py",
    "test_import_ollama.py",
    "test_integration_complete.py",
    "test_observability_stack.py",
    "test_parse.py",
    "test_phase_1_simple.py",
    "test_repository_systems.py",
    "test_temple_enhancements.py",
    "validate_hub.py",
    "verify_system.py",
    ".venv-adapter/",
]


def run(cmd):
    print("RUN:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(repo))
    if res.returncode != 0:
        raise SystemExit(res.returncode)


run(["git", "-C", str(repo), "checkout", "-b", branch])
for f in files:
    run(["git", "-C", str(repo), "add", f])
run(["git", "-C", str(repo), "commit", "-m", "batched(commit): add 27 files from batch 001"])
run(["git", "-C", str(repo), "push", "-u", "origin", branch])
print("Batch", branch, "pushed")

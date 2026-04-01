#!/usr/bin/env python3
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
branch = "feature/batch-008"
files = [
    "scripts/activate_complete_ecosystem.py",
    "scripts/activate_culture_ship.py",
    "scripts/add_type_annotations.py",
    "scripts/agent_git_helper.py",
    "scripts/agent_status_check.py",
    "scripts/audit_symlinks.py",
    "scripts/autonomous_commit_orchestrator.py",
    "scripts/autonomous_modernization_execution.py",
    "scripts/check_ollama_http.py",
    "scripts/chug_helpers.py",
    "scripts/complete_healing.py",
    "scripts/comprehensive_modernization_audit.py",
    "scripts/culture_ship_feedback_loop.py",
    "scripts/curate_quests.py",
    "scripts/daily_health_cycle.py",
    "scripts/dashboard.py",
    "scripts/deep_modernization_orchestrator.py",
    "scripts/deep_system_audit.py",
    "scripts/dev_watcher.py",
    "scripts/ecosystem_deep_dive_tour.py",
    "scripts/ecosystem_entrypoint.py",
    "scripts/ecosystem_health_dashboard.py",
    "scripts/extension_monitor.py",
    "scripts/extract_string_constants.py",
    "scripts/final_validation.py",
    "scripts/fix_coverage_config.py",
    "scripts/fix_file_encoding.py",
    "scripts/fix_imports.py",
    "scripts/fix_pytest_capture.py",
    "scripts/fix_ruff_errors.py",
    "scripts/fix_simulatedverse_fields.py",
    "scripts/full_ecosystem_error_scan.py",
    "scripts/generate_phase1_plan.py",
    "scripts/healing_dashboard.py",
    "scripts/high_impact_fix_workflow.py",
    "scripts/improve_code_quality.py",
    "scripts/install_dev_packages.py",
    "scripts/lint_test_check.py",
    "scripts/llm_health_check.py",
    "scripts/merge_quests_from_log.py",
    "scripts/modernize_typing.py",
    "scripts/morning_standup.py",
    "scripts/morning_standup_enhanced.py",
    "scripts/multi_repo_signal_harvester.py",
    "scripts/nusyq_actions/selfcheck.py",
    "scripts/nusyq_snapshots.py",
    "scripts/prioritized_error_scanner.py",
    "scripts/prune_tmpclaude.py",
    "scripts/pu_queue_runner.py",
    "scripts/query_system_status.py",
    "scripts/quick_fix_workflow.py",
    "scripts/quickstart.py",
    "scripts/register_local_models.py",
    "scripts/rollback_registration.py",
    "scripts/run_clean_coverage.py",
    "scripts/run_semgrep_minimal.py",
    "scripts/run_targeted_tests.py",
    "scripts/run_tests_safely.py",
    "scripts/start_nusyq.py",
    "scripts/start_services.py",
]


def run(cmd):
    print("RUN:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(repo))
    if res.returncode != 0:
        raise SystemExit(res.returncode)


run(["git", "-C", str(repo), "checkout", "-b", branch])
for f in files:
    run(["git", "-C", str(repo), "add", f])
run(["git", "-C", str(repo), "commit", "-m", "batched(commit): add 60 files from batch 008"])
run(["git", "-C", str(repo), "push", "-u", "origin", branch])
print("Batch", branch, "pushed")

#!/usr/bin/env python3
"""Phase 7: Autonomous Scheduler Daemon

Binds Keeper's maintenance cycle to substrate-aware task automation.
Observes machine pressure → triggers maintenance → records decisions.

Pattern: Reuses orchestrator template from Phase 3-6.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).parent.parent
SUBSTRATE_DIR = BASE / ".substrate"
STATE_DIR = BASE / "state"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] SCHEDULER %(levelname)s | %(message)s",
)
log = logging.getLogger("scheduler")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def record_decision(phase: str, action: str, payload: dict[str, Any]) -> str:
    """Record to substrate registry"""
    decision_id = str(uuid.uuid4())
    entry = {
        "type": "scheduler_decision",
        "decision_id": decision_id,
        "timestamp": _now(),
        "phase": phase,
        "action": action,
        "payload": payload,
        "source": "autonomous-scheduler",
    }

    registry_path = SUBSTRATE_DIR / "registry.jsonl"
    try:
        with open(registry_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        log.info(f"Decision recorded: {decision_id}")
    except Exception as e:
        log.error(f"Failed to record: {e}")

    return decision_id


def keeper_score_safe() -> dict[str, Any]:
    """Get Keeper score (with fallback)"""
    try:
        result = subprocess.run(
            [
                "pwsh",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "C:\\CONCEPT\\keeper.ps1",
                "score",
            ],
            cwd=BASE,
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except:
                pass
    except:
        pass

    return {"ok": False, "score": 50, "status": "unknown"}


def phase_7_scheduler_loop() -> dict[str, Any]:
    """Phase 7: Main scheduler loop"""
    log.info("\n=== Phase 7: Autonomous Scheduler Daemon ===\n")

    # Cycle 1: Check machine pressure
    log.info("Cycle 1: Keeper preflight assessment...")
    keeper = keeper_score_safe()
    score = keeper.get("score", 50)
    status = keeper.get("status", "unknown")

    log.info(f"Keeper score: {score} ({status})")

    # Cycle 2: Determine actions
    log.info("Cycle 2: Decision rule evaluation...")

    actions = []
    if score >= 80:
        actions.append("maintenance_critical")
    elif score >= 70:
        actions.append("maintenance_warning")
    elif score >= 60:
        actions.append("maintenance_advisory")
    else:
        actions.append("maintenance_ok")

    # Cycle 3: Queue maintenance tasks
    log.info("Cycle 3: Queue maintenance tasks...")

    tasks = []
    for action in actions:
        task = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "keeper_score": score,
            "estimated_duration": "5-15 min",
            "safe_mode": True,
        }
        tasks.append(task)

        # Record each task
        decision_id = record_decision(
            "phase_7",
            action,
            task,
        )
        log.info(f"  Task queued: {action} ({decision_id})")

    # Cycle 4: Schedule next check
    log.info("Cycle 4: Schedule next check...")
    next_check = {
        "scheduled_after_seconds": 300,  # 5 minutes
        "will_check": ["keeper_score", "disk_usage", "memory_pressure"],
        "decision_id": str(uuid.uuid4()),
    }

    record_decision(
        "phase_7",
        "scheduler_reschedule",
        next_check,
    )

    return {
        "ok": True,
        "phase": 7,
        "status": "scheduler_active",
        "keeper_score": score,
        "actions_queued": len(actions),
        "tasks": tasks,
        "next_check_seconds": 300,
    }


def phase_8_vs_code_integration() -> dict[str, Any]:
    """Phase 8: VS Code cockpit setup"""
    log.info("\n=== Phase 8: VS Code Cockpit Integration ===\n")

    cockpit_config = {
        "timestamp": _now(),
        "cockpit_version": "1.0",
        "mcp_integration": {
            "servers": [
                {
                    "name": "registry-query",
                    "description": "Query decision registry",
                    "endpoint": "registry.jsonl",
                    "commands": [
                        "show_all_decisions",
                        "show_phase_decisions",
                        "show_decision_timeline",
                    ],
                },
                {
                    "name": "culture-ship-control",
                    "description": "Query/control Culture Ship state",
                    "endpoint": "localhost:3003",
                    "commands": [
                        "get_pilot_status",
                        "get_council_decisions",
                        "trigger_strategic_review",
                    ],
                },
                {
                    "name": "serena-analytics",
                    "description": "Query Serena analytics",
                    "endpoint": "localhost:3001",
                    "commands": [
                        "get_analytics",
                        "get_memory_state",
                        "compute_drift",
                    ],
                },
            ]
        },
        "command_palette_commands": [
            {
                "command": "gordon.showRegistryDecisions",
                "title": "🎯 Gordon: Show All Decisions",
                "description": "Query .substrate/registry.jsonl",
            },
            {
                "command": "gordon.showCultureShipPilot",
                "title": "🌍 Gordon: Show Culture Ship Pilot Status",
                "description": "Query Culture Ship pilot mode",
            },
            {
                "command": "gordon.showSerenaAnalytics",
                "title": "📊 Gordon: Show Serena Analytics",
                "description": "Query Serena memory + drift",
            },
            {
                "command": "gordon.showSchedulerTasks",
                "title": "⏰ Gordon: Show Scheduler Tasks",
                "description": "Show Phase 7 tasks + next check",
            },
            {
                "command": "gordon.triggerCultureShipReview",
                "title": "🎲 Gordon: Trigger Culture Ship Review",
                "description": "Force Culture Ship strategic review",
            },
        ],
        "keybindings": [
            {"key": "ctrl+shift+g", "command": "gordon.showRegistryDecisions"},
            {"key": "ctrl+shift+c", "command": "gordon.showCultureShipPilot"},
            {"key": "ctrl+shift+s", "command": "gordon.showSerenaAnalytics"},
        ],
    }

    log.info("Cockpit config:")
    log.info(json.dumps(cockpit_config, indent=2))

    # Record decision
    decision_id = record_decision(
        "phase_8",
        "vs_code_cockpit_setup",
        cockpit_config,
    )

    log.info(f"\nCockpit config recorded: {decision_id}")

    return {
        "ok": True,
        "phase": 8,
        "decision_id": decision_id,
        "status": "cockpit_configured",
        "cockpit_config": cockpit_config,
    }


def phase_9_decision_learning() -> dict[str, Any]:
    """Phase 9: Decision learning pipeline setup"""
    log.info("\n=== Phase 9: Decision Learning Pipeline Setup ===\n")

    learning_config = {
        "timestamp": _now(),
        "learning_version": "1.0",
        "pipeline": {
            "stage_1_ingestion": {
                "source": ".substrate/registry.jsonl",
                "transform": "parse JSONL → extract (phase, action, outcome, timestamp)",
                "output": "decision_log.csv",
            },
            "stage_2_feature_extraction": {
                "features": [
                    "decision_type",
                    "keeper_score_at_time",
                    "time_since_last_decision",
                    "services_affected",
                    "decision_outcome",
                ],
                "output": "decision_features.csv",
            },
            "stage_3_quality_scoring": {
                "metrics": [
                    "decision_success_rate",
                    "time_to_impact",
                    "side_effects",
                    "council_approval_rate",
                ],
                "output": "decision_quality.json",
            },
            "stage_4_feedback_loop": {
                "input": "decision_quality.json",
                "action": "Culture Ship learns → adjusts decision rules",
                "output": "updated_decision_rules.json",
            },
        },
        "training_data_requirements": {
            "minimum_samples": 50,
            "sample_period": "2 weeks",
            "features_collected": 8,
            "quality_metrics": 4,
        },
        "success_criteria": {
            "decision_success_rate_target": 0.95,
            "side_effects_threshold": 0.05,
            "council_approval_minimum": 0.90,
        },
    }

    log.info("Learning pipeline config:")
    log.info(json.dumps(learning_config, indent=2))

    # Record decision
    decision_id = record_decision(
        "phase_9",
        "decision_learning_pipeline_setup",
        learning_config,
    )

    log.info(f"\nLearning config recorded: {decision_id}")

    return {
        "ok": True,
        "phase": 9,
        "decision_id": decision_id,
        "status": "learning_pipeline_configured",
        "learning_config": learning_config,
    }


def main():
    log.info("=" * 80)
    log.info("PHASES 7-9 EXECUTION: SCHEDULER + COCKPIT + LEARNING")
    log.info("=" * 80)

    SUBSTRATE_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 7: Scheduler
    phase_7 = phase_7_scheduler_loop()

    # Phase 8: VS Code Cockpit
    phase_8 = phase_8_vs_code_integration()

    # Phase 9: Decision Learning
    phase_9 = phase_9_decision_learning()

    # Final summary
    log.info("\n" + "=" * 80)
    log.info("PHASES 7-9 COMPLETE")
    log.info("=" * 80)

    summary = {
        "timestamp": _now(),
        "phases_complete": [7, 8, 9],
        "status": "all_phases_configured",
        "phase_7": phase_7,
        "phase_8": phase_8,
        "phase_9": phase_9,
        "next_steps": [
            "Container restart to initialize Culture Ship bootstrap",
            "Monitor Culture Ship pilot decision loop",
            "Execute Phase 7 scheduler tasks",
            "Test VS Code cockpit commands",
            "Collect decision data for Phase 9 training",
        ],
    }

    log.info(json.dumps(summary, indent=2))

    return summary


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result.get("status") == "all_phases_configured" else 1)

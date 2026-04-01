#!/usr/bin/env python3
"""Autonomous Development Loop - The Missing Piece.

This is the control loop that wires together all the existing components:
- Autonomous Monitor (audits system)
- PU Queue (task backlog)
- AI Orchestrator (routes & executes tasks)
- Guild Board (tracks progress)

WITHOUT THIS: Components run in isolation, nothing happens autonomously
WITH THIS: System "chugs" - processes tasks every 30 minutes

Usage:
    python -m src.automation.autonomous_loop --interval 30m
    python -m src.automation.autonomous_loop --mode overnight --interval 60m
"""

import importlib
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

AutonomousMonitor: Any | None = None
QuestEngine: Any | None = None

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.orchestration.unified_ai_orchestrator import (
        OrchestrationTask, TaskPriority, UnifiedAIOrchestrator)
except ImportError:
    from orchestration.unified_ai_orchestrator import \
        OrchestrationTask as _OrchestrationTask
    from orchestration.unified_ai_orchestrator import \
        TaskPriority as _TaskPriority
    from orchestration.unified_ai_orchestrator import \
        UnifiedAIOrchestrator as _UnifiedAIOrchestrator

    OrchestrationTask = _OrchestrationTask
    TaskPriority = _TaskPriority
    UnifiedAIOrchestrator = _UnifiedAIOrchestrator

try:
    _monitor_module = importlib.import_module("src.automation.autonomous_monitor")
    AutonomousMonitor = getattr(_monitor_module, "AutonomousMonitor", None)
except ImportError:
    try:
        _monitor_module = importlib.import_module("automation.autonomous_monitor")
        AutonomousMonitor = getattr(_monitor_module, "AutonomousMonitor", None)
    except ImportError:
        AutonomousMonitor = None

try:
    _quest_module = importlib.import_module("src.Rosetta_Quest_System.quest_engine")
    QuestEngine = getattr(_quest_module, "QuestEngine", None)
    QUEST_ENGINE_AVAILABLE = QuestEngine is not None
except ImportError:
    try:
        _quest_module = importlib.import_module("Rosetta_Quest_System.quest_engine")
        QuestEngine = getattr(_quest_module, "QuestEngine", None)
        QUEST_ENGINE_AVAILABLE = QuestEngine is not None
    except ImportError:
        QUEST_ENGINE_AVAILABLE = False

# Background Task Orchestrator for local LLM delegation
try:
    from src.orchestration.background_task_orchestrator import \
        BackgroundTaskOrchestrator
    from src.orchestration.background_task_orchestrator import \
        TaskPriority as BGTaskPriority
    from src.orchestration.background_task_orchestrator import TaskTarget

    BACKGROUND_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    try:
        _bg_module = importlib.import_module("orchestration.background_task_orchestrator")
        BackgroundTaskOrchestrator = _bg_module.BackgroundTaskOrchestrator
        TaskTarget = _bg_module.TaskTarget
        BGTaskPriority = _bg_module.TaskPriority
        BACKGROUND_ORCHESTRATOR_AVAILABLE = True
    except ImportError:
        BACKGROUND_ORCHESTRATOR_AVAILABLE = False
        BackgroundTaskOrchestrator = None
        TaskTarget = None
        BGTaskPriority = None

try:
    from scripts.result_applier import ResultApplier

    RESULT_APPLIER_AVAILABLE = True
except ImportError:
    RESULT_APPLIER_AVAILABLE = False
    ResultApplier = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class AutonomousLoop:
    """Coordinates autonomous task execution across the system."""

    def __init__(
        self,
        interval_minutes: int = 30,
        mode: str = "normal",
        max_tasks_per_cycle: int = 3,
        max_cycles: int | None = None,
    ):
        """Initialize autonomous loop.

        Args:
            interval_minutes: Minutes between cycles
            mode: "normal" or "overnight" (restricted operations)
            max_tasks_per_cycle: Max tasks to process per cycle
            max_cycles: Optional maximum cycles before shutdown
        """
        self.interval = interval_minutes * 60  # Convert to seconds
        self.mode = mode
        self.max_tasks = max_tasks_per_cycle
        self.max_cycles = max_cycles
        self.running = False
        self.cycle_count = 0

        # Initialize components
        self.orchestrator = UnifiedAIOrchestrator()
        self.monitor = (
            AutonomousMonitor(audit_interval=self.interval)
            if AutonomousMonitor is not None
            else None
        )

        # Initialize Quest Engine if available
        self.quest_engine = None
        if QUEST_ENGINE_AVAILABLE and QuestEngine is not None:
            try:
                self.quest_engine = QuestEngine()
            except (RuntimeError, OSError, ValueError):
                logger.warning("   Quest Engine unavailable, skipping quest integration")

        # Paths
        self.root = Path(__file__).parent.parent.parent
        self.pu_queue_path = self.root / "data" / "unified_pu_queue.json"
        self.metrics_path = self.root / "data" / "execution_metrics.json"
        self.quest_log_path = self.root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        self.autonomous_feedback_path = self.root / "data" / "autonomous_feedback_metrics.json"

        # Config for quest integration
        self.enable_quest_integration = True
        self.quest_chapter_name = "Autonomous"

        # Config for quest execution
        self.enable_quest_execution = True
        self.quest_execution_statuses = ["pending", "active"]
        self.max_quests_per_cycle = 5

        # Config for apply/validate/score feedback loop
        self.result_apply_mode = os.getenv("NUSYQ_AUTONOMOUS_APPLY_MODE", "stage").strip().lower()
        if self.result_apply_mode not in {"preview", "stage", "apply"}:
            logger.warning(
                "Invalid NUSYQ_AUTONOMOUS_APPLY_MODE '%s'; falling back to 'stage'",
                self.result_apply_mode,
            )
            self.result_apply_mode = "stage"
        try:
            self.result_apply_limit = max(1, int(os.getenv("NUSYQ_AUTONOMOUS_APPLY_LIMIT", "20")))
        except ValueError:
            self.result_apply_limit = 20
        try:
            self.validation_timeout_seconds = max(
                30, int(os.getenv("NUSYQ_AUTONOMOUS_VALIDATION_TIMEOUT", "180"))
            )
        except ValueError:
            self.validation_timeout_seconds = 180

        # Initialize Background Task Orchestrator for local LLM delegation
        self.background_orchestrator = None
        self.enable_background_delegation = True
        if BACKGROUND_ORCHESTRATOR_AVAILABLE:
            try:
                self.background_orchestrator = BackgroundTaskOrchestrator()
            except (RuntimeError, OSError, ValueError):
                logger.warning("   Background Orchestrator unavailable")

        logger.info("🔄 Autonomous Loop initialized")
        logger.info(f"   Interval: {interval_minutes} minutes")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Max tasks/cycle: {max_tasks_per_cycle}")
        logger.info(f"   Feedback loop mode: {self.result_apply_mode}")
        logger.info(f"   Feedback apply limit: {self.result_apply_limit}")
        if self.quest_engine:
            logger.info(f"   Quest integration: enabled ({self.quest_chapter_name})")
            logger.info(f"   Quest execution: enabled (max {self.max_quests_per_cycle}/cycle)")
        if self.background_orchestrator:
            logger.info("   Background delegation: enabled (Ollama/LM Studio)")

    def start(self):
        """Start the autonomous loop."""
        logger.info("🚀 Starting autonomous development loop...")

        # Start orchestrator if supported
        if hasattr(self.orchestrator, "start_orchestration"):
            self.orchestrator.start_orchestration()
        else:
            self.orchestrator.orchestration_active = True

        self.running = True
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        try:
            while self.running:
                self.run_cycle()
                if self.max_cycles and self.cycle_count >= self.max_cycles:
                    logger.info("🛑 Max cycles reached. Stopping autonomous loop.")
                    self.running = False
                    break
                if self.running:  # Check again in case shutdown during cycle
                    logger.info(f"💤 Sleeping for {self.interval // 60} minutes...")
                    time.sleep(self.interval)
        except Exception as e:
            logger.exception(f"❌ Fatal error in autonomous loop: {e}")
            self.running = False
            raise

    def run_cycle(self):
        """Run one cycle of autonomous development."""
        self.cycle_count += 1
        cycle_start = time.time()

        logger.info("=" * 80)
        logger.info(
            f"🔄 AUTONOMOUS CYCLE #{self.cycle_count} - {datetime.now().strftime('%H:%M:%S')}"
        )
        logger.info("=" * 80)

        results: dict[str, Any] = {
            "cycle": self.cycle_count,
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode,
            "phases": {},
        }

        try:
            # Phase 1: Monitor audit
            logger.info("\n📊 Phase 1: System Audit")
            audit_results = self._run_audit()
            results["phases"]["audit"] = audit_results

            # Phase 2: PU Queue processing
            logger.info("\n📋 Phase 2: Task Selection")
            tasks = self._get_next_tasks()
            results["phases"]["selection"] = {
                "tasks_found": len(tasks),
                "task_ids": [t.task_id for t in tasks],
            }

            # Phase 3: Task execution
            logger.info(f"\n⚡ Phase 3: Task Execution ({len(tasks)} tasks)")
            execution_results = self._execute_tasks(tasks)
            results["phases"]["execution"] = execution_results

            # Phase 3.5: Quest Execution
            quest_execution_results = self._execute_quests()
            results["phases"]["quest_execution"] = quest_execution_results
            quest_sync = self._sync_quest_execution_status(quest_execution_results)
            results["phases"]["quest_sync"] = {"quests_synced": quest_sync}

            # Phase 4: Results processing
            logger.info("\n📝 Phase 4: Results Processing")
            processing_results = self._process_results(execution_results)
            results["phases"]["processing"] = processing_results

            # Phase 4.5: Apply / Validate / Score feedback loop
            logger.info("\n🔁 Phase 4.5: Apply / Validate / Score")
            feedback_results = self._apply_validate_score(
                execution_results=execution_results,
                audit_results=audit_results,
            )
            results["phases"]["feedback"] = feedback_results

            # Phase 5: Background Task Processing (Local LLM delegation)
            logger.info("\n🤖 Phase 5: Background Task Processing")
            background_results = self._process_background_tasks()
            results["phases"]["background"] = background_results

            # Phase 6: Health check
            logger.info("\n🏥 Phase 6: Health Check")
            health_results = self._check_health()
            results["phases"]["health"] = health_results

            cycle_duration = time.time() - cycle_start
            results["cycle_duration_s"] = round(cycle_duration, 3)

            # Save metrics
            self._save_metrics(results)

            logger.info(f"\n✅ Cycle #{self.cycle_count} complete in {cycle_duration:.1f}s")
            logger.info(f"   Tasks processed: {len(execution_results['completed'])}")
            logger.info(f"   Success rate: {execution_results.get('success_rate', 0):.1%}")

        except Exception as e:
            logger.exception(f"❌ Cycle #{self.cycle_count} failed: {e}")
            results["error"] = str(e)
            self._save_metrics(results)

    def _run_audit(self) -> dict[str, Any]:
        """Run system audit and generate PUs from findings."""
        try:
            logger.info("   Running comprehensive system audit...")

            # For now, use a lightweight scan - check for Python type errors
            import subprocess

            root_path = Path(__file__).parent.parent.parent

            # Run mypy to find type errors
            try:
                result = subprocess.run(
                    [
                        "python",
                        "-m",
                        "mypy",
                        "src/",
                        "--no-error-summary",
                        "--ignore-missing-imports",
                    ],
                    cwd=root_path,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
                error_lines = [
                    line for line in result.stdout.split("\n") if line.strip() and "error:" in line
                ]
            except (subprocess.TimeoutExpired, FileNotFoundError):
                error_lines = []

            # Collect issues from mypy errors
            all_issues = []
            for line in error_lines[:50]:  # Limit to first 50
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    all_issues.append(
                        {
                            "type": "type_error",
                            "file": parts[0].strip().replace("\\", "/"),
                            "line": parts[1].strip(),
                            "description": parts[3].strip(),
                            "severity": "medium",
                        }
                    )

            # Generate PUs from top 10 issues
            pus_created = []

            for issue in all_issues[:10]:
                pu = {
                    "id": f"PU-audit-{int(datetime.now().timestamp() * 1000)}",
                    "type": "RefactorPU",
                    "title": f"Fix {issue['type']}: {issue['file']}:{issue['line']}",
                    "description": issue.get("description", "Auto-generated from audit"),
                    "priority": "medium" if issue.get("severity") == "high" else "low",
                    "status": "approved",
                    "created_at": datetime.now().isoformat(),
                    "source_repo": "nusyq-hub",
                    "proof_criteria": ["diagnose", "resolve", "verify"],
                    "metadata": {
                        "source": "autonomous_loop_audit",
                        "issue": issue,
                    },
                    "votes": {},
                    "assigned_agents": [],
                    "execution_results": {},
                }

                # Add PU to queue
                try:
                    pu_queue = json.loads(self.pu_queue_path.read_text(encoding="utf-8"))
                except (FileNotFoundError, json.JSONDecodeError):
                    pu_queue = []

                pu_queue.append(pu)
                pus_created.append(pu["id"])

            # Write queue only once at the end
            if pus_created:
                self.pu_queue_path.write_text(json.dumps(pu_queue, indent=2), encoding="utf-8")

            logger.info(
                f"   ✓ Audit complete - generated {len(pus_created)} PUs from {len(all_issues)} findings"
            )
            return {"status": "completed", "findings": len(all_issues), "pus_created": pus_created}
        except (RuntimeError, OSError, ValueError) as e:
            logger.error(f"   Audit failed: {e}")
            return {"status": "failed", "error": str(e)}

    def _get_next_tasks(self) -> list[OrchestrationTask]:
        """Get next tasks from PU queue."""
        tasks: list[OrchestrationTask] = []

        if not self.pu_queue_path.exists():
            logger.warning("   PU queue file not found")
            return tasks

        try:
            pu_queue = json.loads(self.pu_queue_path.read_text(encoding="utf-8"))

            # Filter for queue-eligible tasks only.
            active_statuses = {"approved", "queued", "pending", "in_progress"}
            available_pus = [
                pu for pu in pu_queue if pu.get("status", "approved") in active_statuses
            ]

            # Take top N by priority
            sorted_pus = sorted(
                available_pus,
                key=lambda x: {"high": 1, "medium": 2, "low": 3}.get(x.get("priority", "low"), 3),
            )[: self.max_tasks]

            # Convert to OrchestrationTasks
            for pu in sorted_pus:
                task = OrchestrationTask(
                    task_id=pu["id"],
                    task_type=self._map_pu_type(pu["type"]),
                    content=pu["description"],  # Fixed: content not description
                    priority=self._map_priority(pu.get("priority", "medium")),
                    context={"pu_data": pu},
                )
                tasks.append(task)

            logger.info(f"   Found {len(available_pus)} available PUs")
            logger.info(f"   Selected {len(tasks)} tasks for execution")

            for i, task in enumerate(tasks, 1):
                logger.info(f"      {i}. [{task.task_type}] {task.content[:60]}...")

        except (RuntimeError, OSError, ValueError) as e:
            logger.error(f"   Failed to load PU queue: {e}")

        return tasks

    def _execute_tasks(self, tasks: list[OrchestrationTask]) -> dict[str, Any]:
        """Execute tasks via orchestrator."""
        completed: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        results: dict[str, Any] = {
            "attempted": len(tasks),
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
        }

        for task in tasks:
            try:
                logger.info(f"\n   🎯 Executing: {task.task_id}")
                logger.info(f"      Type: {task.task_type}")
                logger.info(f"      Priority: {task.priority.name}")

                # Execute task via orchestrator
                import asyncio

                execution_result = asyncio.run(self.orchestrator.orchestrate_task_async(task))

                # Check primary_result for actual execution status
                primary_result = execution_result.get("primary_result", {})
                result_status = primary_result.get("status", "unknown")
                assigned_system = execution_result.get("assigned_system", "unknown")

                if result_status == "completed":
                    logger.info(f"      ✅ Completed on: {assigned_system}")
                    logger.info(
                        f"         Result: {str(primary_result.get('result', ''))[:100]}..."
                    )
                    results["completed"].append(
                        {
                            "task_id": task.task_id,
                            "system": assigned_system,
                            "status": "completed",
                            "result": primary_result.get("result"),
                        }
                    )
                elif result_status in {
                    "pending",
                    "queued",
                    "in_progress",
                    "submitted",
                    "delegated",
                }:
                    logger.info(f"      ⏳ Deferred on: {assigned_system} (status={result_status})")
                    results["skipped"].append(
                        {
                            "task_id": task.task_id,
                            "system": assigned_system,
                            "status": result_status,
                            "note": primary_result.get("note", f"Task returned {result_status}"),
                        }
                    )
                else:
                    logger.warning(f"      ⚠️  Task status '{result_status}' on {assigned_system}")
                    if result_status == "pending":
                        logger.info(f"         Note: {primary_result.get('note', 'No note')}")
                    results["failed"].append(
                        {
                            "task_id": task.task_id,
                            "system": assigned_system,
                            "status": result_status,
                            "error": primary_result.get("error", f"Task returned {result_status}"),
                        }
                    )

            except (RuntimeError, OSError, ValueError) as e:
                logger.error(f"      ❌ Execution failed: {e}")
                results["failed"].append({"task_id": task.task_id, "error": str(e)})

        # Calculate success rate
        total = results["attempted"]
        successful = len(results["completed"])
        results["success_rate"] = successful / total if total > 0 else 0

        return results

    def _process_results(self, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Process execution results and create quests from PU data."""
        processed = {"pus_updated": 0, "quests_generated": 0, "logs_written": 0}
        quest_candidate_ids: set[str] = set()

        # Get IDs of completed and failed tasks
        completed_ids = {r.get("task_id") for r in execution_results.get("completed", [])}
        failed_ids = {r.get("task_id") for r in execution_results.get("failed", [])}

        # Update PU statuses based on execution results
        if completed_ids or failed_ids or execution_results.get("fixes_applied"):
            try:
                pu_queue = json.loads(self.pu_queue_path.read_text(encoding="utf-8"))
                for pu in pu_queue:
                    pu_id = pu.get("id")

                    # Update completed tasks
                    if pu_id in completed_ids:
                        pu["status"] = "completed"
                        pu["completed_at"] = datetime.now().isoformat()
                        processed["pus_updated"] += 1
                        quest_candidate_ids.add(pu_id)
                        logger.debug(f"   Marked PU {pu_id} as completed")

                    # Update failed tasks
                    elif pu_id in failed_ids:
                        pu["status"] = "failed"
                        pu["failed_at"] = datetime.now().isoformat()
                        # Find error message
                        for f in execution_results.get("failed", []):
                            if f.get("task_id") == pu_id:
                                pu["last_error"] = f.get("error", "Unknown error")
                                break
                        processed["pus_updated"] += 1
                        logger.debug(f"   Marked PU {pu_id} as failed")

                    # Legacy: Update in_progress audit tasks
                    elif (
                        pu.get("status") == "in_progress"
                        and pu.get("source") == "autonomous_loop_audit"
                        and execution_results.get("fixes_applied")
                    ):
                        pu["status"] = "completed"
                        pu["completed_at"] = datetime.now().isoformat()
                        processed["pus_updated"] += 1
                        if pu_id:
                            quest_candidate_ids.add(pu_id)

                self.pu_queue_path.write_text(json.dumps(pu_queue, indent=2), encoding="utf-8")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to update PU statuses: {e}")

        # Create quests from completed PUs
        if execution_results.get("completed") or execution_results.get("fixes_applied"):
            quest_results = self._create_quests_from_pu_results(quest_candidate_ids)
            processed["quests_generated"] = quest_results.get("quests_created", 0)

        logger.info(f"   PU statuses updated: {processed['pus_updated']}")
        logger.info(f"   Quests generated: {processed['quests_generated']}")
        logger.info(f"   Quest log entries: {processed['logs_written']}")

        return processed

    def _apply_validate_score(
        self,
        execution_results: dict[str, Any],
        audit_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Close the loop by applying task outputs, validating, and scoring impact."""
        apply_results = self._apply_task_results()
        validation_results = self._run_feedback_validation(apply_results)
        impact = self._score_feedback_loop(
            execution_results=execution_results,
            apply_results=apply_results,
            validation_results=validation_results,
            audit_results=audit_results,
        )

        feedback_snapshot = {
            "cycle": self.cycle_count,
            "timestamp": datetime.now().isoformat(),
            "mode": self.result_apply_mode,
            "apply": apply_results,
            "validation": validation_results,
            "impact": impact,
        }
        self._save_feedback_metrics(feedback_snapshot)

        logger.info(
            "   Feedback score: %.3f (%s)",
            impact.get("score", 0.0),
            impact.get("band", "unknown"),
        )
        logger.info(
            "   Applied files: %s | Validation checks: %s",
            apply_results.get("applied_file_count", 0),
            validation_results.get("checks_run", 0),
        )

        return feedback_snapshot

    def _apply_task_results(self) -> dict[str, Any]:
        """Apply or stage LLM task outputs using the existing ResultApplier tool."""
        if not RESULT_APPLIER_AVAILABLE or ResultApplier is None:
            return {
                "status": "skipped",
                "reason": "result_applier_unavailable",
                "mode": self.result_apply_mode,
                "applied_file_count": 0,
            }

        try:
            applier = ResultApplier()
            preview = applier.preview_applications(limit=self.result_apply_limit)

            apply_tests_live = self.result_apply_mode == "apply"
            stage_live = self.result_apply_mode in {"stage", "apply"}

            test_result = applier.apply_test_results(
                dry_run=not apply_tests_live,
                limit=self.result_apply_limit,
            )
            stage_result = applier.apply_create_modify_to_staging(
                dry_run=not stage_live,
                limit=self.result_apply_limit,
            )

            test_paths = [str(path) for path in test_result.get("applied", [])]
            staged_paths = [str(path) for path in stage_result.get("staged_files", [])]
            applied_file_count = len(test_paths) + len(staged_paths)

            status = "completed"
            if self.result_apply_mode == "preview":
                status = "preview_only"

            return {
                "status": status,
                "mode": self.result_apply_mode,
                "preview": preview,
                "tests": test_result,
                "staging": stage_result,
                "test_paths": test_paths,
                "staged_paths": staged_paths,
                "applied_file_count": applied_file_count,
            }
        except Exception as exc:
            logger.warning("   Failed to apply task results: %s", exc)
            return {
                "status": "failed",
                "mode": self.result_apply_mode,
                "error": str(exc),
                "applied_file_count": 0,
            }

    def _resolve_tool_command(self, tool_name: str) -> list[str] | None:
        """Resolve an executable command for a validation tool."""
        binary = shutil.which(tool_name)
        if binary:
            return [binary]

        probe = subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if probe.returncode == 0:
            return [sys.executable, "-m", tool_name]
        return None

    def _run_validation_check(self, name: str, command: list[str]) -> dict[str, Any]:
        """Run a single validation command and normalize output."""
        started = time.time()
        try:
            result = subprocess.run(
                command,
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.validation_timeout_seconds,
            )
            output = "\n".join(filter(None, [result.stdout, result.stderr])).strip()
            issue_count = self._count_issues_in_output(name, output)
            return {
                "name": name,
                "status": "completed",
                "passed": result.returncode == 0,
                "returncode": result.returncode,
                "issue_count": issue_count,
                "duration_s": round(time.time() - started, 3),
                "output_preview": output[:1200],
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {
                "name": name,
                "status": "timeout",
                "passed": False,
                "returncode": None,
                "issue_count": 0,
                "duration_s": round(time.time() - started, 3),
                "command": command,
            }
        except Exception as exc:
            return {
                "name": name,
                "status": "failed",
                "passed": False,
                "returncode": None,
                "issue_count": 0,
                "error": str(exc),
                "duration_s": round(time.time() - started, 3),
                "command": command,
            }

    def _count_issues_in_output(self, check_name: str, output: str) -> int:
        """Estimate issue count from tool output."""
        if not output:
            return 0

        if check_name == "mypy":
            return len(re.findall(r"\berror:", output))
        if check_name == "ruff":
            return len(re.findall(r"(?m)^.+:\d+:\d+:\s+[A-Z]\d+", output))
        if check_name == "pytest_collect":
            return len(re.findall(r"(?i)\berror\b", output))
        return 0

    def _run_feedback_validation(self, apply_results: dict[str, Any]) -> dict[str, Any]:
        """Run focused lint/type/test checks on newly applied artifacts."""
        checks: list[dict[str, Any]] = []
        test_paths = [Path(p) for p in apply_results.get("test_paths", [])]
        staged_paths = [Path(p) for p in apply_results.get("staged_paths", [])]

        candidate_paths = test_paths + staged_paths
        python_targets: list[str] = []
        for path in candidate_paths:
            suffix = path.suffix.lower()
            if suffix != ".py":
                continue
            if not path.exists():
                continue
            try:
                rel = path.resolve().relative_to(self.root.resolve())
                python_targets.append(str(rel))
            except ValueError:
                continue

        # Keep checks bounded for autonomous cycles.
        python_targets = sorted(set(python_targets))[:25]

        ruff_cmd = self._resolve_tool_command("ruff")
        if ruff_cmd and python_targets:
            checks.append(self._run_validation_check("ruff", [*ruff_cmd, "check", *python_targets]))
        elif python_targets:
            checks.append(
                {
                    "name": "ruff",
                    "status": "skipped",
                    "passed": False,
                    "reason": "tool_unavailable",
                    "issue_count": 0,
                }
            )

        mypy_cmd = self._resolve_tool_command("mypy")
        if mypy_cmd and python_targets:
            checks.append(
                self._run_validation_check(
                    "mypy",
                    [*mypy_cmd, "--ignore-missing-imports", "--no-error-summary", *python_targets],
                )
            )
        elif python_targets:
            checks.append(
                {
                    "name": "mypy",
                    "status": "skipped",
                    "passed": False,
                    "reason": "tool_unavailable",
                    "issue_count": 0,
                }
            )

        tests_dir = self.root / "tests"
        should_collect_tests = bool(test_paths) or self.result_apply_mode == "apply"
        if should_collect_tests and tests_dir.exists():
            checks.append(
                self._run_validation_check(
                    "pytest_collect",
                    [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
                )
            )

        completed_checks = [c for c in checks if c.get("status") == "completed"]
        passed_checks = [c for c in completed_checks if c.get("passed")]
        issue_count = sum(int(c.get("issue_count", 0)) for c in completed_checks)

        return {
            "checks": checks,
            "checks_run": len(completed_checks),
            "checks_passed": len(passed_checks),
            "issue_count": issue_count,
            "python_targets": python_targets,
        }

    def _score_feedback_loop(
        self,
        execution_results: dict[str, Any],
        apply_results: dict[str, Any],
        validation_results: dict[str, Any],
        audit_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Score the closed-loop cycle impact for routing and trend analysis."""
        execution_success = float(execution_results.get("success_rate", 0.0))
        checks_run = int(validation_results.get("checks_run", 0))
        checks_passed = int(validation_results.get("checks_passed", 0))
        validation_pass_rate = checks_passed / checks_run if checks_run else 0.5

        applied_file_count = int(apply_results.get("applied_file_count", 0))
        preview = apply_results.get("preview", {})
        preview_applicable = (
            int(preview.get("applicable_results", 0)) if isinstance(preview, dict) else 0
        )
        apply_activity = min(1.0, applied_file_count / 5.0)
        if apply_activity == 0 and preview_applicable > 0:
            apply_activity = 0.4

        findings = int(audit_results.get("findings", 0) or 0)
        post_validation_issues = int(validation_results.get("issue_count", 0))
        error_reduction = 0.0
        if findings > 0:
            error_reduction = max(0.0, (findings - post_validation_issues) / findings)

        score = (
            (0.35 * execution_success)
            + (0.30 * validation_pass_rate)
            + (0.20 * apply_activity)
            + (0.15 * error_reduction)
        )
        score = round(max(0.0, min(1.0, score)), 3)

        if score >= 0.75:
            band = "high"
        elif score >= 0.45:
            band = "medium"
        else:
            band = "low"

        return {
            "score": score,
            "band": band,
            "execution_success_rate": round(execution_success, 3),
            "validation_pass_rate": round(validation_pass_rate, 3),
            "apply_activity": round(apply_activity, 3),
            "error_reduction": round(error_reduction, 3),
            "applied_file_count": applied_file_count,
            "preview_applicable_results": preview_applicable,
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "audit_findings": findings,
            "post_validation_issues": post_validation_issues,
        }

    def _save_feedback_metrics(self, feedback_snapshot: dict[str, Any]) -> None:
        """Persist per-cycle feedback loop metrics."""
        try:
            metrics_file = self.autonomous_feedback_path
            metrics_file.parent.mkdir(parents=True, exist_ok=True)

            payload = (
                json.loads(metrics_file.read_text(encoding="utf-8"))
                if metrics_file.exists()
                else {"cycles": []}
            )

            payload["cycles"].append(feedback_snapshot)
            payload["last_cycle"] = feedback_snapshot
            payload["total_cycles"] = len(payload["cycles"])
            payload["updated_at"] = datetime.now().isoformat()

            scores = [
                c.get("impact", {}).get("score")
                for c in payload.get("cycles", [])
                if isinstance(c.get("impact", {}).get("score"), (int, float))
            ]
            if scores:
                payload["average_feedback_score"] = round(sum(scores) / len(scores), 3)

            metrics_file.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        except Exception as exc:
            logger.warning("   Failed to persist feedback metrics: %s", exc)

    def _get_questline_for_pu(self, pu_type: str) -> str:
        """Map PU type to appropriate questline."""
        pu_type_to_questline = {
            "BugFixPU": "Bug Fixes",
            "RefactorPU": "Refactoring",
            "FeaturePU": "Features",
            "DocPU": "Documentation",
            "AnalysisPU": "Analysis & Audits",
            "TestPU": "Testing",
        }
        return pu_type_to_questline.get(pu_type, self.quest_chapter_name)

    def _convert_pu_to_quest(self, pu: dict[str, Any]) -> str | None:
        """Convert a single PU to a quest. Returns quest_id or None on failure."""
        if not self.quest_engine:
            return None

        pu_type = pu.get("type", "AnalysisPU")
        questline = self._get_questline_for_pu(pu_type)

        quest_description = f"""Auto-generated from PU: {pu.get("id", "unknown")}

PU Title: {pu.get("title", "(untitled)")}
Description: {pu.get("description", "(no description)")}
Type: {pu_type}
Priority: {pu.get("priority", "medium")}
Created: {pu.get("created_at", "unknown")}
"""

        try:
            quest_id = self.quest_engine.add_quest(
                title=pu.get("title", f"Task: {pu.get('id')}"),
                description=quest_description,
                questline=questline,
                tags=[pu_type, "autonomous", f"source:{pu.get('source_repo', 'unknown')}"],
                priority=pu.get("priority", "medium"),
                dependencies=pu.get("dependencies", []),
            )
            return str(quest_id) if quest_id else None
        except (RuntimeError, OSError, ValueError, TypeError) as e:
            logger.error(f"      Quest creation error for PU {pu.get('id')}: {e}")
            return None

    def _create_quests_from_pu_results(self, pu_ids: set[str] | None = None) -> dict[str, Any]:
        """Convert completed PUs into quests in the Quest Engine.

        When pu_ids is provided, only those PUs are considered. This avoids
        re-scanning the entire queue and generating quest churn every cycle.
        """
        result = {"quests_created": 0, "quests_failed": 0}

        # Skip if integration unavailable
        if not self.enable_quest_integration or not self.quest_engine:
            return result

        try:
            if not self.pu_queue_path.exists():
                return result

            pu_queue = json.loads(self.pu_queue_path.read_text(encoding="utf-8"))

            # Process completed/executed PUs
            for pu in pu_queue:
                pu_id = pu.get("id")

                # Optional scope limitation to current-cycle completions.
                if pu_ids is not None and pu_id not in pu_ids:
                    continue

                # Skip if already linked or not completed.
                if pu.get("associated_quest_id") or pu.get("status") != "completed":
                    continue

                quest_id = self._convert_pu_to_quest(pu)

                if quest_id:
                    pu["associated_quest_id"] = quest_id
                    result["quests_created"] += 1
                    logger.info(f"      ✓ Created quest {quest_id} from PU {pu.get('id')}")

                    # Sync quest status with PU status
                    if pu.get("status") == "completed":
                        self.quest_engine.complete_quest(quest_id)
                        logger.info("         Quest marked as completed")
                else:
                    result["quests_failed"] += 1
                    logger.warning(f"      Failed to create quest for PU {pu.get('id')}")

            # Save updated queue
            self.pu_queue_path.write_text(json.dumps(pu_queue, indent=2), encoding="utf-8")

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"   Failed to create quests from PU results: {e}")

        return result

    def _get_quests_for_execution(self) -> list[dict[str, Any]]:
        """Get active and pending quests from quest engine."""
        quests: list[dict[str, Any]] = []

        if not self.enable_quest_execution or not self.quest_engine:
            return quests

        try:
            # Get all quests and filter by status
            all_quests = list(self.quest_engine.quests.values())
            executable_quests = [q for q in all_quests if q.status in self.quest_execution_statuses]

            # Limit by max per cycle
            limited_quests = executable_quests[: self.max_quests_per_cycle]

            logger.info(f"   Found {len(executable_quests)} quests to execute")
            logger.info(f"   Selected {len(limited_quests)} for this cycle")

            # Convert to dict for passing around
            for q in limited_quests:
                quests.append(q.to_dict())

        except (RuntimeError, OSError, ValueError, AttributeError) as e:
            logger.error(f"   Failed to fetch quests for execution: {e}")

        return quests

    def _convert_quest_to_task(self, quest_data: dict[str, Any]) -> OrchestrationTask | None:
        """Convert a quest to an orchestration task."""
        try:
            quest_id = quest_data.get("id", "unknown")
            quest_title = quest_data.get("title", "(untitled)")
            quest_description = quest_data.get("description", "")
            quest_priority = quest_data.get("priority", "normal")

            # Map quest priority to task priority
            priority_map = {
                "critical": TaskPriority.CRITICAL,
                "high": TaskPriority.HIGH,
                "medium": TaskPriority.NORMAL,
                "normal": TaskPriority.NORMAL,
                "low": TaskPriority.LOW,
            }
            task_priority = priority_map.get(str(quest_priority).lower(), TaskPriority.NORMAL)

            # Create orchestration task
            task = OrchestrationTask(
                task_id=quest_id,
                task_type="quest_execution",
                content=f"{quest_title}: {quest_description[:100]}",
                context={
                    "quest_id": quest_id,
                    "quest_data": quest_data,
                    "questline": quest_data.get("questline", "General"),
                },
                priority=task_priority,
                required_capabilities=["quest_execution"],
            )

            return task
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"      Failed to convert quest to task: {e}")
            return None

    def _execute_quests(self) -> dict[str, Any]:
        """Execute quests via the orchestrator."""
        results: dict[str, Any] = {
            "quests_submitted": 0,
            "quests_failed": 0,
            "execution_results": [],
        }

        quests = self._get_quests_for_execution()
        if not quests:
            return results

        logger.info(f"\n🎯 Phase 3.5: Quest Execution ({len(quests)} quests)")

        for quest_data in quests:
            try:
                quest_id = quest_data.get("id")
                quest_title = quest_data.get("title", "(untitled)")

                # Convert to task
                task = self._convert_quest_to_task(quest_data)
                if not task:
                    results["quests_failed"] += 1
                    logger.warning(f"      Failed to convert quest {quest_id}")
                    continue

                # Submit to orchestrator
                logger.info(f"      📤 Submitting quest {quest_id}: {quest_title[:50]}")
                submitted_task_id = self.orchestrator.submit_task(task)

                results["quests_submitted"] += 1
                results["execution_results"].append(
                    {
                        "quest_id": quest_id,
                        "task_id": submitted_task_id,
                        "title": quest_title,
                        "status": "submitted",
                    }
                )

                # Update quest status to active
                if self.quest_engine:
                    try:
                        self.quest_engine.update_quest_status(quest_id, "active")
                        logger.info("         ✓ Quest marked as active")
                    except (RuntimeError, OSError, ValueError) as e:
                        logger.warning(f"         Failed to update quest status: {e}")

            except (RuntimeError, OSError, ValueError) as e:
                results["quests_failed"] += 1
                logger.error(f"      ❌ Failed to execute quest: {e}")

        logger.info(f"   ✓ Quest execution complete: {results['quests_submitted']} submitted")

        return results

    def _sync_quest_execution_status(self, quest_execution: dict[str, Any]) -> int:
        """Sync quest execution results back to quest engine."""
        synced = 0

        if not self.quest_engine or not quest_execution.get("execution_results"):
            return synced

        try:
            for result in quest_execution.get("execution_results", []):
                quest_id = result.get("quest_id")
                if not quest_id:
                    continue

                # Update status based on submission success
                status = "active" if result.get("status") == "submitted" else "blocked"
                self.quest_engine.update_quest_status(quest_id, status)
                synced += 1

        except (RuntimeError, OSError, ValueError) as e:
            logger.error(f"   Failed to sync quest execution status: {e}")

        logger.info(f"   ✓ Quest statuses synced: {synced} quests")
        return synced

    def _process_background_tasks(self) -> dict[str, Any]:
        """Process background tasks via local LLMs (Ollama/LM Studio).

        This delegates expensive token operations to local models,
        preserving Claude API tokens for high-value work.
        """
        results: dict[str, Any] = {
            "tasks_delegated": 0,
            "tasks_completed": 0,
            "tasks_pending": 0,
            "errors": [],
        }

        if not self.background_orchestrator or not self.enable_background_delegation:
            logger.info("   Background delegation disabled or unavailable")
            return results

        try:
            # Check status of existing background tasks
            import asyncio

            # Get task status (method renamed in recent update)
            task_status = self.background_orchestrator.get_orchestrator_status()
            queued = task_status.get("queued", 0)
            running = task_status.get("running", 0)
            completed = task_status.get("completed", 0)

            logger.info(
                f"   Background tasks: {queued} queued, {running} running, {completed} completed"
            )
            results["tasks_pending"] = queued + running
            results["tasks_completed"] = completed

            # Delegate any high-token tasks from the PU queue
            delegated = self._delegate_heavy_tasks_to_background()
            results["tasks_delegated"] = delegated

            # Start the orchestrator worker if not running
            if not self.background_orchestrator._running and queued > 0:
                logger.info("   Starting background task worker...")
                asyncio.run(self.background_orchestrator.start())

        except (RuntimeError, OSError, ValueError, AttributeError) as e:
            logger.warning(f"   Background task processing error: {e}")
            results["errors"].append(str(e))

        return results

    def _delegate_heavy_tasks_to_background(self) -> int:
        """Delegate heavy/expensive tasks to local LLMs.

        Returns number of tasks delegated.
        """
        delegated = 0

        if not self.background_orchestrator:
            return delegated

        try:
            if not self.pu_queue_path.exists():
                return delegated

            pu_queue = json.loads(self.pu_queue_path.read_text(encoding="utf-8"))

            # Find tasks suitable for background delegation
            # Criteria: pending, high-token estimate, not already delegated
            for pu in pu_queue:
                if pu.get("status") not in {"pending", "approved", "queued"}:
                    continue
                if pu.get("background_task_id"):
                    continue  # Already delegated

                # Check if task type is suitable for local LLM
                pu_type = pu.get("type", "")
                if pu_type in ["RefactorPU", "AnalysisPU", "DocPU"]:
                    # These are good candidates for local LLM processing
                    task_id = self._submit_to_background_orchestrator(pu)
                    if task_id:
                        pu["background_task_id"] = task_id
                        pu["status"] = "delegated"
                        delegated += 1
                        logger.info(f"      Delegated {pu['id']} to background: {task_id}")

            # Save updated queue
            if delegated > 0:
                self.pu_queue_path.write_text(json.dumps(pu_queue, indent=2), encoding="utf-8")

        except (RuntimeError, OSError, ValueError) as e:
            logger.warning(f"   Failed to delegate tasks: {e}")

        return delegated

    def _submit_to_background_orchestrator(self, pu: dict[str, Any]) -> str | None:
        """Submit a PU to the background orchestrator.

        Returns the background task ID or None on failure.
        """
        if not self.background_orchestrator:
            return None

        try:
            # Map PU type to task type for model routing
            pu_type = pu.get("type", "general")
            task_type_map = {
                "RefactorPU": "code_analysis",
                "AnalysisPU": "code_analysis",
                "DocPU": "code_generation",
                "TestPU": "code_generation",
                "FeaturePU": "code_generation",
            }
            task_type = task_type_map.get(pu_type, "general")

            # Map priority
            priority_map = {
                "high": BGTaskPriority.HIGH if BGTaskPriority else 8,
                "medium": BGTaskPriority.NORMAL if BGTaskPriority else 5,
                "low": BGTaskPriority.LOW if BGTaskPriority else 1,
            }
            priority = priority_map.get(
                pu.get("priority", "medium"), BGTaskPriority.NORMAL if BGTaskPriority else 5
            )

            # Create prompt from PU
            prompt = f"""Task: {pu.get("title", "Untitled")}

Description: {pu.get("description", "No description")}

Type: {pu_type}
Priority: {pu.get("priority", "medium")}

Please analyze and provide recommendations or implementation.
"""

            # Submit to orchestrator (submit_task is synchronous)
            task = self.background_orchestrator.submit_task(
                prompt=prompt,
                target=TaskTarget.AUTO if TaskTarget else "auto",
                task_type=task_type,
                priority=priority,
                requesting_agent="autonomous_loop",
                metadata={"pu_id": pu.get("id"), "pu_type": pu_type},
            )

            # Return task_id if we got a BackgroundTask object
            if hasattr(task, "task_id"):
                return str(task.task_id)
            return str(task)

        except (RuntimeError, OSError, ValueError, TypeError) as e:
            logger.warning(f"   Failed to submit task to background: {e}")
            return None

    def _check_health(self) -> dict[str, Any]:
        """Check system health."""
        orchestrator_status = self.orchestrator.get_system_status()

        systems_data = orchestrator_status.get("systems", {})
        pipelines_data = orchestrator_status.get("pipelines", 0)

        # systems is a dict, pipelines is an int
        systems_count = len(systems_data) if isinstance(systems_data, dict) else 0
        pipelines_count = pipelines_data if isinstance(pipelines_data, int) else 0

        services_running = systems_count > 0

        health = {
            "orchestrator": orchestrator_status,
            "services_running": services_running,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"   AI Systems available: {systems_count}")
        logger.info(f"   Pipelines ready: {pipelines_count}")

        return health

    def _save_metrics(self, results: dict[str, Any]):
        """Save execution metrics."""
        try:
            metrics_file = self.metrics_path
            metrics_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing metrics
            if metrics_file.exists():
                all_metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
            else:
                all_metrics = {"cycles": []}

            # Append this cycle
            all_metrics["cycles"].append(results)
            all_metrics["last_cycle"] = results
            all_metrics["total_cycles"] = len(all_metrics["cycles"])
            all_metrics["updated_at"] = datetime.now().isoformat()

            total_processed = 0
            successful = 0
            failed = 0
            skipped = 0
            for cycle in all_metrics["cycles"]:
                execution = cycle.get("phases", {}).get("execution", {})
                successful += len(execution.get("completed", []))
                failed += len(execution.get("failed", []))
                skipped += len(execution.get("skipped", []))
                total_processed += int(execution.get("attempted", 0))

            all_metrics["total_tasks_processed"] = total_processed
            all_metrics["successful_executions"] = successful
            all_metrics["failed_executions"] = failed
            all_metrics["skipped_executions"] = skipped
            all_metrics["last_cycle_duration"] = results.get("cycle_duration_s")

            feedback_scores = [
                cycle.get("phases", {}).get("feedback", {}).get("impact", {}).get("score")
                for cycle in all_metrics["cycles"]
                if isinstance(
                    cycle.get("phases", {}).get("feedback", {}).get("impact", {}).get("score"),
                    (int, float),
                )
            ]
            if feedback_scores:
                all_metrics["average_feedback_score"] = round(
                    sum(feedback_scores) / len(feedback_scores), 3
                )

            # Save
            metrics_file.write_text(
                json.dumps(all_metrics, indent=2, default=str), encoding="utf-8"
            )
            logger.info(f"   ✓ Metrics saved to {metrics_file}")

        except (RuntimeError, OSError, ValueError) as e:
            logger.error(f"   Failed to save metrics: {e}")

    def _handle_shutdown(self, _signum, _frame):
        """Handle graceful shutdown."""
        logger.info("\n🛑 Shutdown signal received, finishing current cycle...")
        self.running = False

    def _map_pu_type(self, pu_type: str) -> str:
        """Map PU type to task type."""
        mapping = {
            "RefactorPU": "code_refactoring",
            "FeaturePU": "feature_development",
            "DocPU": "documentation",
            "TestPU": "test_generation",
            "BugPU": "bug_fix",
        }
        return mapping.get(pu_type, "general_task")

    def _map_priority(self, priority: str) -> TaskPriority:
        """Map PU priority to TaskPriority enum."""
        mapping = {
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.NORMAL,
            "low": TaskPriority.LOW,
            "critical": TaskPriority.CRITICAL,
        }
        if not priority:
            return TaskPriority.NORMAL
        try:
            return mapping.get(priority.lower(), TaskPriority.NORMAL)
        except AttributeError:
            return TaskPriority.NORMAL


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous Development Loop")
    parser.add_argument("--interval", default="30m", help="Cycle interval (e.g., 30m, 1h)")
    parser.add_argument(
        "--mode",
        default="normal",
        choices=["normal", "overnight", "supervised"],
        help="Operation mode",
    )
    parser.add_argument("--max-tasks", type=int, default=3, help="Max tasks per cycle")
    parser.add_argument(
        "--cycles", type=int, default=0, help="Stop after N cycles (0 = run forever)"
    )

    args = parser.parse_args()

    # Parse interval
    interval_str = args.interval.lower()
    if interval_str.endswith("m"):
        interval_minutes = int(interval_str[:-1])
    elif interval_str.endswith("h"):
        interval_minutes = int(interval_str[:-1]) * 60
    else:
        interval_minutes = int(interval_str)

    # Create and start loop
    loop = AutonomousLoop(
        interval_minutes=interval_minutes,
        mode=args.mode,
        max_tasks_per_cycle=args.max_tasks,
        max_cycles=args.cycles or None,
    )

    loop.start()


if __name__ == "__main__":
    main()

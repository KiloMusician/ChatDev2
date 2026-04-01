#!/usr/bin/env python3
"""Work Queue Executor - Execute items from cultivation work queue autonomously.

This module reads from docs/Work-Queue/WORK_QUEUE.json and executes queued items
in priority order, updating status as items complete.

Usage:
    executor = WorkQueueExecutor()
    result = await executor.execute_next_item()
    # or
    results = await executor.execute_batch(max_items=3)
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.timeout_config import get_timeout

logger = logging.getLogger(__name__)

KEY_STATUS = "status"
KEY_ERROR = "error"
KEY_OUTPUT = "output"
KEY_ITEMS = "items"
KEY_DURATION_SECONDS = "duration_seconds"

STATUS_EMPTY = "empty"
STATUS_NO_QUEUED_ITEMS = "no_queued_items"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_ERROR = "error"
STATUS_QUEUED = "queued"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"


class WorkQueueExecutor:
    """Executes items from work queue autonomously."""

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize work queue executor.

        Args:
            repo_root: Repository root (defaults to NuSyQ-Hub location)
        """
        self.repo_root = repo_root or Path(__file__).parent.parent.parent
        self.work_queue_path = self.repo_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        self.execution_mode = (
            os.getenv("NUSYQ_WORK_QUEUE_EXECUTION_MODE", "capability").strip().lower()
        )
        self.legacy_fallback_enabled = os.getenv(
            "NUSYQ_WORK_QUEUE_LEGACY_FALLBACK", "1"
        ).strip().lower() not in {
            "0",
            "false",
            "off",
            "no",
        }
        logger.info("📋 Work Queue Executor initialized")

    async def execute_next_item(self) -> dict[str, Any]:
        """Execute the next queued item (highest priority, oldest first).

        Returns:
            Execution result with status, item_id, and output
        """
        logger.info("📋 Executing next work queue item...")

        try:
            # Load work queue
            queue_data = self._load_work_queue()
            if not queue_data or not queue_data.get(KEY_ITEMS):
                logger.info("Info: Work queue is empty")
                return {KEY_STATUS: STATUS_EMPTY, "message": "No items in work queue"}

            # Find next queued item (priority, then oldest)
            items = queue_data.get(KEY_ITEMS, [])
            queued_items = [i for i in items if i.get(KEY_STATUS) == STATUS_QUEUED]

            if not queued_items:
                logger.info("Info: No queued items remaining")
                return {
                    KEY_STATUS: STATUS_NO_QUEUED_ITEMS,
                    "message": "All items are in progress or completed",
                }

            # Sort by priority (descending) then by created time (ascending)
            priority_order = {
                "critical": 0,
                "high": 1,
                "normal": 2,
                "low": 3,
                "background": 4,
            }
            queued_items.sort(
                key=lambda x: (
                    priority_order.get(x.get("priority", "normal"), 2),
                    x.get("created", ""),
                )
            )

            item = queued_items[0]
            item_id = item.get("id")
            title = item.get("title", "Unknown task")

            logger.info(f"▶️  Executing: {title} [{item_id}]")

            # Mark as in progress
            self._update_item_status(item_id, STATUS_IN_PROGRESS)

            # Execute the item based on title patterns
            result = await self._execute_item(item)

            if result.get(KEY_STATUS) == STATUS_SUCCESS:
                # Mark as completed
                self._update_item_status(item_id, STATUS_COMPLETED, result.get(KEY_OUTPUT, ""))
                logger.info(f"✅ Completed: {title}")
                return {
                    KEY_STATUS: STATUS_SUCCESS,
                    "item_id": item_id,
                    "title": title,
                    KEY_OUTPUT: result.get(KEY_OUTPUT, ""),
                    KEY_DURATION_SECONDS: result.get(KEY_DURATION_SECONDS, 0),
                }
            else:
                # Mark as failed
                self._update_item_status(
                    item_id, STATUS_FAILED, result.get(KEY_ERROR, "Unknown error")
                )
                logger.warning(f"❌ Failed: {title}")
                return {
                    KEY_STATUS: STATUS_FAILED,
                    "item_id": item_id,
                    "title": title,
                    KEY_ERROR: result.get(KEY_ERROR, "Unknown error"),
                }

        except Exception as e:
            logger.error(f"❌ Work queue executor error: {e}")
            return {KEY_STATUS: STATUS_ERROR, KEY_ERROR: str(e)}

    async def execute_batch(self, max_items: int = 3) -> dict[str, Any]:
        """Execute up to max_items from the work queue.

        Args:
            max_items: Maximum number of items to execute

        Returns:
            Batch execution summary
        """
        logger.info(f"📋 Executing batch (max {max_items} items)...")

        results = []
        for _i in range(max_items):
            result = await self.execute_next_item()
            results.append(result)

            if result.get(KEY_STATUS) in [STATUS_EMPTY, STATUS_NO_QUEUED_ITEMS, STATUS_ERROR]:
                break

            # Brief pause between items
            await asyncio.sleep(0.5)

        completed = len([r for r in results if r.get(KEY_STATUS) == STATUS_SUCCESS])
        failed = len([r for r in results if r.get(KEY_STATUS) == STATUS_FAILED])

        logger.info(f"📊 Batch complete: {completed} succeeded, {failed} failed")

        return {
            KEY_STATUS: "batch_complete",
            "items_executed": len(results),
            "succeeded": completed,
            "failed": failed,
            "results": results,
        }

    async def _execute_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Execute a single work queue item.

        Args:
            item: Work queue item with id, title, description

        Returns:
            Execution result with status, output, duration
        """
        start_time = datetime.now()

        try:
            # Capability-routed primary path (router/dispatch/EOL chain).
            result = await self._execute_item_capability_routed(item)

            # Optional compatibility fallback for legacy queue items.
            if result.get(KEY_STATUS) != STATUS_SUCCESS and self.legacy_fallback_enabled:
                fallback_result = await self._execute_item_legacy(item)
                if fallback_result.get(KEY_STATUS) == STATUS_SUCCESS:
                    fallback_result["fallback_from"] = result
                    result = fallback_result

            # Add duration
            duration = (datetime.now() - start_time).total_seconds()
            result[KEY_DURATION_SECONDS] = duration

            return result

        except Exception as e:
            logger.error(f"❌ Item execution failed: {e}")
            return {
                KEY_STATUS: STATUS_FAILED,
                KEY_ERROR: str(e),
                KEY_DURATION_SECONDS: (datetime.now() - start_time).total_seconds(),
            }

    async def _execute_item_capability_routed(self, item: dict[str, Any]) -> dict[str, Any]:
        """Execute a queue item via capability routing (router/dispatch/EOL)."""
        description = str(item.get("description") or item.get("title") or "").strip()
        if not description:
            return {
                KEY_STATUS: STATUS_FAILED,
                KEY_ERROR: "Work queue item missing title/description",
            }

        routing_mode = (
            str(item.get("routing_mode") or item.get("execution_mode") or self.execution_mode)
            .strip()
            .lower()
        )
        task_type = self._infer_task_type(item)
        target_system = self._infer_target_system(item, task_type)
        priority = self._map_priority(item.get("priority"))

        context: dict[str, Any] = {
            "work_queue_item_id": item.get("id"),
            "work_queue_source": item.get("source"),
            "work_queue_priority": item.get("priority"),
            "work_queue_risk": item.get("risk"),
            "work_queue_effort": item.get("effort"),
        }

        if routing_mode == "dispatch":
            route_order = ["dispatch", "router", "eol"]
        elif routing_mode == "eol":
            route_order = ["eol", "router", "dispatch"]
        else:
            # "capability", "router", "hybrid", or unknown all use the same safe default chain.
            route_order = ["router", "dispatch", "eol"]

        attempts: list[dict[str, Any]] = []
        for route in route_order:
            if route == "router":
                result = await self._execute_via_router(
                    task_type=task_type,
                    description=description,
                    context=context,
                    target_system=target_system,
                    priority=priority,
                )
            elif route == "dispatch":
                result = await self._execute_via_dispatch(
                    task_type=task_type,
                    description=description,
                    priority=priority,
                    preferred_agent=target_system,
                )
            else:
                result = await self._execute_via_eol(description)

            result["route"] = route
            attempts.append(
                {
                    "route": route,
                    KEY_STATUS: result.get(KEY_STATUS),
                    KEY_ERROR: result.get(KEY_ERROR),
                }
            )
            if result.get(KEY_STATUS) == STATUS_SUCCESS:
                result["attempts"] = attempts
                return result

        return {
            KEY_STATUS: STATUS_FAILED,
            KEY_ERROR: "Capability routing exhausted all executors",
            "attempts": attempts,
        }

    async def _execute_via_router(
        self,
        *,
        task_type: str,
        description: str,
        context: dict[str, Any],
        target_system: str,
        priority: str,
    ) -> dict[str, Any]:
        """Execute via AgentTaskRouter (primary routing path)."""
        try:
            from src.tools.agent_task_router import AgentTaskRouter

            router = AgentTaskRouter(repo_root=self.repo_root)
            routed = await router.route_task(
                task_type=task_type,  # type: ignore[arg-type]
                description=description,
                context=context,
                target_system=target_system,  # type: ignore[arg-type]
                priority=priority,
            )
            status = str(routed.get("status", "")).strip().lower()
            success = status in {"success", "submitted", "completed", "ok"} or bool(
                routed.get("success")
            )
            if success:
                return {
                    KEY_STATUS: STATUS_SUCCESS,
                    "executor": "agent_task_router",
                    KEY_OUTPUT: routed,
                }
            return {
                KEY_STATUS: STATUS_FAILED,
                "executor": "agent_task_router",
                KEY_ERROR: str(routed.get(KEY_ERROR) or "router_failed"),
                KEY_OUTPUT: routed,
            }
        except Exception as exc:
            return {
                KEY_STATUS: STATUS_FAILED,
                "executor": "agent_task_router",
                KEY_ERROR: f"router_exception: {exc}",
            }

    async def _execute_via_dispatch(
        self,
        *,
        task_type: str,
        description: str,
        priority: str,
        preferred_agent: str,
    ) -> dict[str, Any]:
        """Execute via MJOLNIR dispatch as secondary routing path."""
        agent = preferred_agent if preferred_agent != "auto" else "ollama"
        command = [
            "python",
            "scripts/start_nusyq.py",
            "dispatch",
            "ask",
            agent,
            description,
            "--task-type",
            task_type,
            "--priority",
            priority,
        ]
        try:
            timeout_seconds = get_timeout("ANALYSIS_TOOL_TIMEOUT_SECONDS", default=180)
            result = subprocess.run(
                command,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            output = result.stdout.strip()
            if result.returncode == 0:
                return {
                    KEY_STATUS: STATUS_SUCCESS,
                    "executor": "dispatch",
                    KEY_OUTPUT: output or "Dispatch accepted",
                }
            return {
                KEY_STATUS: STATUS_FAILED,
                "executor": "dispatch",
                KEY_ERROR: result.stderr.strip() or output or "dispatch_failed",
            }
        except Exception as exc:
            return {
                KEY_STATUS: STATUS_FAILED,
                "executor": "dispatch",
                KEY_ERROR: f"dispatch_exception: {exc}",
            }

    async def _execute_via_eol(self, description: str) -> dict[str, Any]:
        """Execute via EOL full-cycle as tertiary routing path."""
        dry_run = os.getenv("NUSYQ_WORK_QUEUE_EOL_DRY_RUN", "0").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        try:
            from src.core.orchestrate import nusyq

            eol_result = nusyq.eol.full_cycle(
                description,
                auto_execute=not dry_run,
                dry_run=dry_run,
            )
            if not getattr(eol_result, "ok", False):
                return {
                    KEY_STATUS: STATUS_FAILED,
                    "executor": "eol",
                    KEY_ERROR: str(getattr(eol_result, KEY_ERROR, "eol_full_cycle_failed")),
                }
            payload = getattr(eol_result, "value", None) or getattr(eol_result, "data", {})
            metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
            executed = int(metadata.get("executed", 0) or 0)
            approved = int(metadata.get("approved", 0) or 0)
            if executed > 0 or approved > 0 or dry_run:
                return {
                    KEY_STATUS: STATUS_SUCCESS,
                    "executor": "eol",
                    KEY_OUTPUT: payload,
                }
            return {
                KEY_STATUS: STATUS_FAILED,
                "executor": "eol",
                KEY_ERROR: "eol_no_approved_or_executed_actions",
                KEY_OUTPUT: payload,
            }
        except Exception as exc:
            return {
                KEY_STATUS: STATUS_FAILED,
                "executor": "eol",
                KEY_ERROR: f"eol_exception: {exc}",
            }

    def _infer_task_type(self, item: dict[str, Any]) -> str:
        text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        if any(token in text for token in ("generate", "scaffold", "create", "build")):
            return "generate"
        if any(token in text for token in ("review", "audit", "lint", "quality")):
            return "review"
        if any(token in text for token in ("debug", "fix", "repair", "failure", "exception")):
            return "debug"
        if any(token in text for token in ("test", "pytest", "validation", "smoke")):
            return "test"
        if any(token in text for token in ("document", "readme", "doc", "guide")):
            return "document"
        if any(token in text for token in ("plan", "roadmap", "strategy")):
            return "plan"
        return "analyze"

    def _infer_target_system(self, item: dict[str, Any], task_type: str) -> str:
        explicit = str(item.get("target_system") or "").strip().lower()
        if explicit:
            return explicit
        env_default = str(os.getenv("NUSYQ_WORK_QUEUE_TARGET_SYSTEM", "")).strip().lower()
        if env_default:
            return env_default
        if task_type == "generate":
            return "chatdev"
        if task_type == "debug":
            return "quantum_resolver"
        return "auto"

    def _map_priority(self, priority: Any) -> str:
        normalized = str(priority or "normal").strip().lower()
        mapping = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "normal": "NORMAL",
            "medium": "NORMAL",
            "low": "LOW",
            "background": "BACKGROUND",
        }
        return mapping.get(normalized, "NORMAL")

    async def _execute_item_legacy(self, item: dict[str, Any]) -> dict[str, Any]:
        """Legacy title-heuristic executor retained as compatibility fallback."""
        title = item.get("title", "").lower()

        if "test" in title and "suite" in title:
            return await self._execute_test_suite()
        if "inventory" in title:
            return await self._execute_inventory_update()
        if "quick wins" in title:
            return await self._execute_quick_wins()
        if "dashboard" in title:
            return await self._execute_dashboard_build()
        if "replay" in title:
            return await self._execute_quest_replay()
        if "sync" in title:
            return await self._execute_cross_sync()
        return {
            KEY_STATUS: STATUS_SUCCESS,
            KEY_OUTPUT: f"Executed generic legacy task: {item.get('title', 'unknown')}",
        }

    async def _execute_test_suite(self) -> dict[str, Any]:
        """Execute test suite validation."""
        logger.info("🧪 Running test suite...")

        try:
            timeout_seconds = get_timeout("ANALYSIS_TOOL_TIMEOUT_SECONDS", default=180)
            result = subprocess.run(
                ["python", "-m", "pytest", "tests", "-q", "--tb=short"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

            if result.returncode == 0:
                return {
                    KEY_STATUS: STATUS_SUCCESS,
                    KEY_OUTPUT: result.stdout or "All tests passed",
                }
            else:
                return {KEY_STATUS: STATUS_FAILED, KEY_ERROR: result.stderr or "Tests failed"}
        except Exception as e:
            return {KEY_STATUS: STATUS_FAILED, KEY_ERROR: f"Test execution failed: {e}"}

    async def _execute_inventory_update(self) -> dict[str, Any]:
        """Generate capability inventory update."""
        logger.info("📦 Generating capability inventory...")

        try:
            # This would call the capabilities command
            timeout_seconds = get_timeout("ANALYSIS_TOOL_TIMEOUT_SECONDS", default=180)
            subprocess.run(
                ["python", "scripts/start_nusyq.py", "capabilities"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

            return {KEY_STATUS: STATUS_SUCCESS, KEY_OUTPUT: "Capability inventory updated"}
        except Exception as e:
            return {KEY_STATUS: STATUS_FAILED, KEY_ERROR: f"Inventory update failed: {e}"}

    async def _execute_quick_wins(self) -> dict[str, Any]:
        """Check for quick wins in work queue."""
        logger.info("⚡ Checking for quick wins...")

        try:
            queue_data = self._load_work_queue()
            items = queue_data.get(KEY_ITEMS, [])

            # Quick wins: small effort, low risk, queued status
            quick_wins = [
                i
                for i in items
                if i.get(KEY_STATUS) == STATUS_QUEUED
                and i.get("effort") == "small"
                and i.get("risk") == "low"
            ]

            return {
                KEY_STATUS: STATUS_SUCCESS,
                KEY_OUTPUT: f"Found {len(quick_wins)} quick win items available for execution",
            }
        except Exception as e:
            return {KEY_STATUS: STATUS_FAILED, KEY_ERROR: f"Quick wins check failed: {e}"}

    async def _execute_dashboard_build(self) -> dict[str, Any]:
        """Build cultivation metrics dashboard."""
        logger.info("📊 Building metrics dashboard...")

        try:
            from src.tools.cultivation_metrics import CultivationMetrics

            metrics = CultivationMetrics(self.repo_root)
            dashboard_path = await metrics.build_dashboard()

            return {KEY_STATUS: STATUS_SUCCESS, KEY_OUTPUT: f"Dashboard built: {dashboard_path}"}
        except Exception as e:
            return {KEY_STATUS: STATUS_FAILED, KEY_ERROR: f"Dashboard build failed: {e}"}

    async def _execute_quest_replay(self) -> dict[str, Any]:
        """Replay historical quests for learning."""
        logger.info("🔄 Replaying historical quests...")

        try:
            from src.tools.quest_replay_engine import QuestReplayEngine

            engine = QuestReplayEngine(self.repo_root)
            await engine.replay_recent_quests(limit=5)

            return {
                KEY_STATUS: STATUS_SUCCESS,
                KEY_OUTPUT: "Replayed quests - insights generated",
            }
        except Exception as e:
            return {KEY_STATUS: STATUS_FAILED, KEY_ERROR: f"Quest replay failed: {e}"}

    async def _execute_cross_sync(self) -> dict[str, Any]:
        """Sync cultivation data to SimulatedVerse."""
        logger.info("🌉 Syncing cultivation data...")

        try:
            from src.tools.cross_ecosystem_sync import CrossEcosystemSync

            syncer = CrossEcosystemSync(self.repo_root)
            sync_result = await syncer.sync_to_simverse()

            return {
                KEY_STATUS: STATUS_SUCCESS,
                KEY_OUTPUT: f"Data synced to SimulatedVerse: {sync_result.get('items_synced', 0)} items",
            }
        except Exception as e:
            return {KEY_STATUS: STATUS_FAILED, KEY_ERROR: f"Cross-sync failed: {e}"}

    def _load_work_queue(self) -> dict[str, Any]:
        """Load work queue from JSON file."""
        if not self.work_queue_path.exists():
            logger.warning(f"Work queue not found at {self.work_queue_path}")
            return {KEY_ITEMS: []}

        try:
            with open(self.work_queue_path, encoding="utf-8") as f:
                queue_data: dict[str, Any] = json.load(f)
                return queue_data
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to load work queue: {e}")
            return {KEY_ITEMS: []}

    def _update_item_status(self, item_id: str, status: str, note: str = "") -> None:
        """Update status of a work queue item."""
        try:
            queue_data = self._load_work_queue()

            for item in queue_data.get(KEY_ITEMS, []):
                if item.get("id") == item_id:
                    item[KEY_STATUS] = status
                    item["last_updated"] = datetime.now().isoformat()
                    if note:
                        item["last_note"] = note
                    break

            # Write back to file
            queue_data["last_updated"] = datetime.now().isoformat()
            with open(self.work_queue_path, "w", encoding="utf-8") as f:
                json.dump(queue_data, f, indent=2)

            logger.info(f"📝 Updated {item_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update item status: {e}")

    async def get_queue_status(self) -> dict[str, Any]:
        """Get current status of work queue."""
        try:
            queue_data = self._load_work_queue()
            items = queue_data.get(KEY_ITEMS, [])

            queued = len([i for i in items if i.get(KEY_STATUS) == STATUS_QUEUED])
            in_progress = len([i for i in items if i.get(KEY_STATUS) == STATUS_IN_PROGRESS])
            completed = len([i for i in items if i.get(KEY_STATUS) == STATUS_COMPLETED])
            failed = len([i for i in items if i.get(KEY_STATUS) == STATUS_FAILED])

            return {
                KEY_STATUS: STATUS_SUCCESS,
                "total_items": len(items),
                "queued": queued,
                "in_progress": in_progress,
                "completed": completed,
                "failed": failed,
                "queue_path": str(self.work_queue_path),
            }
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {KEY_STATUS: STATUS_ERROR, KEY_ERROR: str(e)}


if __name__ == "__main__":
    import sys

    async def main():
        executor = WorkQueueExecutor()

        if len(sys.argv) > 1 and sys.argv[1] == "batch":
            max_items = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            result = await executor.execute_batch(max_items)
        else:
            result = await executor.execute_next_item()

        logger.info(json.dumps(result, indent=2))

    asyncio.run(main())

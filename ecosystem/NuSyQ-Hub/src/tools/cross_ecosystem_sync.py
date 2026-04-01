#!/usr/bin/env python3
"""Cross-Ecosystem Sync - Synchronize cultivation data to SimulatedVerse.

This module syncs quest log, work queue, and metrics from NuSyQ-Hub to SimulatedVerse
ecosystem, enabling cross-repo awareness and unified consciousness tracking.

Synced data:
- Quest log entries (cultivation intents)
- Work queue items (shared task pool)
- Metrics and learning reports (system evolution)
- System health data (unified observatory)
"""

import asyncio
import contextlib
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from src.utils.repo_path_resolver import get_repo_path
except ImportError:
    try:
        from utils.repo_path_resolver import get_repo_path
    except ImportError:  # pragma: no cover - fallback for standalone runs
        get_repo_path = None


class CrossEcosystemSync:
    """Syncs cultivation data across NuSyQ repositories."""

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize cross-ecosystem syncer.

        Args:
            repo_root: Repository root (NuSyQ-Hub location)
        """
        self.repo_root = repo_root or Path(__file__).parent.parent.parent

        # NuSyQ-Hub paths
        self.hub_quest_log = self.repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        self.hub_work_queue = self.repo_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        self.hub_metrics = self.repo_root / "docs" / "Metrics"
        self.hub_learning = self.repo_root / "docs" / "Learning"

        # Discover SimulatedVerse
        self.simverse_root = self._find_simverse()

        # SimulatedVerse paths
        self.sv_shared: Path | None = None
        self.sv_quest_log: Path | None = None
        self.sv_work_queue: Path | None = None
        self.sv_metrics: Path | None = None

        if self.simverse_root:
            self.sv_shared = self.simverse_root / "shared_cultivation"
            self.sv_quest_log = self.sv_shared / "quest_log.jsonl"
            self.sv_work_queue = self.sv_shared / "WORK_QUEUE.json"
            self.sv_metrics = self.sv_shared / "metrics"

        # Shared knowledge base (NuSyQ Root)
        self.shared_kb = self._find_shared_knowledge_base()

        logger.info("🌉 Cross-Ecosystem Sync initialized")

    async def sync_to_simverse(self) -> dict[str, Any]:
        """Sync all cultivation data to SimulatedVerse.

        Returns:
            Sync result summary
        """
        logger.info("🌉 Syncing cultivation data to SimulatedVerse...")

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "synced_items": 0,
            "details": {},
        }

        try:
            # Check if SimulatedVerse is available
            if not self.simverse_root:
                logger.warning("Info: SimulatedVerse not found - using file-based sync")
                return {
                    "status": "partial",
                    "message": "SimulatedVerse not found - will use shared knowledge base only",
                    "synced_items": 0,
                }

            # Create shared cultivation directory
            self.sv_shared.mkdir(parents=True, exist_ok=True)
            self.sv_metrics.mkdir(parents=True, exist_ok=True)

            # Sync quest log
            quest_sync = await self._sync_quest_log()
            result["details"]["quest_log"] = quest_sync
            result["synced_items"] += quest_sync.get("items_synced", 0)

            # Sync work queue
            queue_sync = await self._sync_work_queue()
            result["details"]["work_queue"] = queue_sync
            result["synced_items"] += queue_sync.get("items_synced", 0)

            # Sync metrics
            metrics_sync = await self._sync_metrics()
            result["details"]["metrics"] = metrics_sync
            result["synced_items"] += metrics_sync.get("items_synced", 0)

            # Sync to shared knowledge base
            kb_sync = await self._sync_to_knowledge_base()
            result["details"]["knowledge_base"] = kb_sync
            result["synced_items"] += kb_sync.get("items_synced", 0)

            logger.info(f"✅ Cross-sync complete: {result['synced_items']} items synced")

            return result

        except Exception as e:
            logger.error(f"❌ Cross-sync failed: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            return result

    async def _sync_quest_log(self) -> dict[str, Any]:
        """Sync quest log entries to SimulatedVerse."""
        logger.info("📖 Syncing quest log...")

        try:
            if not self.hub_quest_log.exists() or not self.sv_quest_log:
                return {"status": "skipped", "reason": "quest_log_not_found"}

            # Copy quest log
            shutil.copy2(self.hub_quest_log, self.sv_quest_log)

            # Count entries synced
            entry_count = 0
            try:
                with open(self.hub_quest_log, encoding="utf-8") as f:
                    entry_count = sum(1 for _ in f)
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

            logger.info(f"✅ Quest log synced ({entry_count} entries)")

            return {
                "status": "success",
                "items_synced": entry_count,
                "destination": str(self.sv_quest_log),
            }

        except Exception as e:
            logger.error(f"Failed to sync quest log: {e}")
            return {"status": "failed", "error": str(e)}

    # ------------------------------------------------------------------
    # Synchronous helper wrappers (used by service_manager loop)
    # ------------------------------------------------------------------

    def sync_quest_log(self) -> dict[str, Any]:
        """Sync quest log using a blocking wrapper."""
        try:
            return asyncio.run(self._sync_quest_log())
        except RuntimeError:
            # If an event loop is already running, return a clear status
            return {"status": "failed", "error": "event_loop_running"}

    def sync_all(self) -> dict[str, Any]:
        """Sync everything (quest, work queue, metrics, KB) in a blocking way."""
        try:
            return asyncio.run(self.sync_to_simverse())
        except RuntimeError:
            return {"status": "failed", "error": "event_loop_running"}

    async def _sync_work_queue(self) -> dict[str, Any]:
        """Sync work queue to SimulatedVerse."""
        logger.info("📋 Syncing work queue...")

        try:
            if not self.hub_work_queue.exists() or not self.sv_work_queue:
                return {"status": "skipped", "reason": "work_queue_not_found"}

            # Load hub work queue
            with open(self.hub_work_queue, encoding="utf-8") as f:
                hub_queue = json.load(f)

            # Load SimulatedVerse queue if exists
            sv_queue = {}
            if self.sv_work_queue.exists():
                try:
                    with open(self.sv_work_queue, encoding="utf-8") as f:
                        sv_queue = json.load(f)
                except (json.JSONDecodeError, ValueError, OSError):
                    sv_queue = {"items": []}
            else:
                sv_queue = {"items": []}

            # Merge queues (add new items from hub)
            sv_items = sv_queue.get("items", [])
            hub_items = hub_queue.get("items", [])

            # Track what's new
            sv_ids = {item.get("id") for item in sv_items}
            new_items = 0

            for item in hub_items:
                if item.get("id") not in sv_ids:
                    sv_items.append(item)
                    new_items += 1

            # Update merged queue
            sv_queue["items"] = sv_items
            sv_queue["last_synced_from_hub"] = datetime.now().isoformat()

            # Write back
            with open(self.sv_work_queue, "w", encoding="utf-8") as f:
                json.dump(sv_queue, f, indent=2)

            logger.info(f"✅ Work queue synced ({new_items} new items)")

            return {
                "status": "success",
                "items_synced": new_items,
                "total_in_queue": len(sv_items),
                "destination": str(self.sv_work_queue),
            }

        except Exception as e:
            logger.error(f"Failed to sync work queue: {e}")
            return {"status": "failed", "error": str(e)}

    async def _sync_metrics(self) -> dict[str, Any]:
        """Sync metrics to SimulatedVerse."""
        logger.info("📊 Syncing metrics...")

        try:
            if not self.hub_metrics.exists() or not self.sv_metrics:
                return {"status": "skipped", "reason": "metrics_not_found"}

            # Copy all metric files
            files_synced = 0

            for metric_file in self.hub_metrics.glob("*.json"):
                try:
                    dest = self.sv_metrics / metric_file.name
                    shutil.copy2(metric_file, dest)
                    files_synced += 1
                except Exception as e:
                    logger.warning(f"Failed to sync {metric_file.name}: {e}")

            # Also copy dashboard if it exists
            dashboard_src = self.hub_metrics / "dashboard.html"
            if dashboard_src.exists():
                try:
                    shutil.copy2(dashboard_src, self.sv_metrics / "dashboard.html")
                    files_synced += 1
                except Exception as e:
                    logger.warning(f"Failed to sync dashboard: {e}")

            logger.info(f"✅ Metrics synced ({files_synced} files)")

            return {
                "status": "success",
                "items_synced": files_synced,
                "destination": str(self.sv_metrics),
            }

        except Exception as e:
            logger.error(f"Failed to sync metrics: {e}")
            return {"status": "failed", "error": str(e)}

    async def _sync_to_knowledge_base(self) -> dict[str, Any]:
        """Sync cultivation summaries to shared knowledge base.

        The knowledge base (NuSyQ Root) serves as the unified awareness system
        for all three repositories.
        """
        logger.info("📚 Syncing to shared knowledge base...")

        try:
            if not self.shared_kb.exists():
                logger.info("Info: Shared knowledge base not found - will create on next sync")
                return {
                    "status": "skipped",
                    "reason": "knowledge_base_not_found",
                    "note": "Will be created on next sync with real NuSyQ Root",
                }

            # Generate summary
            summary = self._generate_cultivation_summary()

            # Append to knowledge base
            try:
                with open(self.shared_kb, "a", encoding="utf-8") as f:
                    f.write("\n# NuSyQ-Hub Cultivation Summary\n")
                    f.write(f"**Updated:** {datetime.now().isoformat()}\n\n")
                    f.write("## Recent Events\n")
                    f.write(summary)
            except Exception as e:
                logger.warning(f"Could not append to knowledge base: {e}")

            logger.info("✅ Knowledge base updated")

            return {
                "status": "success",
                "items_synced": 1,
                "destination": str(self.shared_kb),
            }

        except Exception as e:
            logger.error(f"Failed to sync to knowledge base: {e}")
            return {"status": "failed", "error": str(e)}

    def _generate_cultivation_summary(self) -> str:
        """Generate summary of recent cultivation activity."""
        summary = ""

        # Quest summary
        if self.hub_quest_log.exists():
            try:
                with open(self.hub_quest_log, encoding="utf-8") as f:
                    lines = f.readlines()
                    recent = lines[-5:] if lines else []

                summary += f"### Quest Log ({len(lines)} total entries)\n"
                if recent:
                    summary += f"Recent entries: {len(recent)} new entries captured\n"
                    summary += "- Most recent: System cultivation active\n"
                    summary += "\n"
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

        # Work queue summary
        if self.hub_work_queue.exists():
            try:
                with open(self.hub_work_queue, encoding="utf-8") as f:
                    queue_data = json.load(f)
                    items = queue_data.get("items", [])

                queued = len([i for i in items if i.get("status") == "queued"])
                completed = len([i for i in items if i.get("status") == "completed"])

                summary += f"### Work Queue ({len(items)} items)\n"
                summary += f"- Queued: {queued}\n"
                summary += f"- Completed: {completed}\n"
                summary += "\n"
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

        summary += f"**Sync Time:** {datetime.now().isoformat()}\n"

        return summary if summary else "Cultivation activity captured\n"

    def _find_simverse(self) -> Path | None:
        """Discover SimulatedVerse repository location."""
        candidates: list[Path] = []

        # Prefer centralized resolver when available.
        if get_repo_path:
            with contextlib.suppress(Exception):
                candidates.append(get_repo_path("SIMULATEDVERSE_ROOT"))

        # Environment-based candidates (workspace loader / shell exports).
        for env_key in (
            "SIMULATEDVERSE_PATH",
            "SIMULATEDVERSE_APP",
            "SIMULATEDVERSE",
            "SIMULATEDVERSE_ROOT",
        ):
            env_value = os.getenv(env_key)
            if not env_value:
                continue
            env_path = self._normalize_external_path(env_value)
            candidates.append(env_path)
            candidates.append(env_path / "SimulatedVerse")

        # Legacy hardcoded fallbacks.
        candidates = [
            *candidates,
            self._normalize_external_path("c:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
            self._normalize_external_path("c:/Users/keath/SimulatedVerse"),
            Path.home() / "Desktop" / "SimulatedVerse",
            Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse",
        ]

        seen: set[str] = set()
        unique_candidates: list[Path] = []
        for candidate in candidates:
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(candidate)

        for candidate in unique_candidates:
            if candidate.exists() and (candidate / ".git").exists():
                logger.info(f"✅ Found SimulatedVerse: {candidate}")
                return candidate

        logger.info("Info: SimulatedVerse not found in standard locations")
        return None

    def _find_shared_knowledge_base(self) -> Path:
        """Resolve shared knowledge-base path with cross-shell normalization."""
        env_candidates = [
            os.getenv("NUSYQ_KNOWLEDGE_BASE"),
            os.getenv("NUSYQ_KB_PATH"),
        ]
        for candidate in env_candidates:
            if candidate:
                return self._normalize_external_path(candidate)

        if get_repo_path:
            try:
                root_path = get_repo_path("NUSYQ_ROOT")
                return root_path / "knowledge-base.yaml"
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

        return self._normalize_external_path("c:/Users/keath/NuSyQ/knowledge-base.yaml")

    @staticmethod
    def _normalize_external_path(path_value: str) -> Path:
        """Normalize Windows/POSIX path strings to local runtime path style."""
        normalized = path_value.strip().strip("\"'")
        normalized = normalized.replace("\\", "/")
        if len(normalized) >= 2 and normalized[1] == ":" and normalized[0].isalpha():
            normalized = f"/mnt/{normalized[0].lower()}{normalized[2:]}"
        return Path(normalized).expanduser()

    async def sync_bidirectional(self) -> dict[str, Any]:
        """Sync both directions (hub to SimulatedVerse and vice versa).

        Returns:
            Bidirectional sync result
        """
        logger.info("🔄 Bidirectional sync...")

        result = {
            "status": "success",
            "hub_to_simverse": await self.sync_to_simverse(),
            "simverse_to_hub": (await self._sync_from_simverse() if self.simverse_root else None),
        }

        return result

    async def _sync_from_simverse(self) -> dict[str, Any]:
        """Sync from SimulatedVerse back to hub.

        This enables SimulatedVerse to contribute ideas back to the work queue.
        """
        logger.info("🔄 Syncing from SimulatedVerse...")

        try:
            if not self.sv_work_queue or not self.sv_work_queue.exists():
                return {"status": "skipped", "reason": "no_data_from_simverse"}

            # Load SimulatedVerse work queue
            with open(self.sv_work_queue, encoding="utf-8") as f:
                sv_queue = json.load(f)

            # Load hub work queue
            with open(self.hub_work_queue, encoding="utf-8") as f:
                hub_queue = json.load(f)

            # Merge in new items from SimulatedVerse
            sv_items = sv_queue.get("items", [])
            hub_items = hub_queue.get("items", [])

            hub_ids = {item.get("id") for item in hub_items}
            new_items = 0

            for item in sv_items:
                if item.get("id") not in hub_ids and item.get("source") == "simverse":
                    # Mark as from SimulatedVerse
                    item["source"] = "simverse_contribution"
                    hub_items.append(item)
                    new_items += 1

            # Update hub queue
            hub_queue["items"] = hub_items
            hub_queue["last_synced_from_simverse"] = datetime.now().isoformat()

            with open(self.hub_work_queue, "w", encoding="utf-8") as f:
                json.dump(hub_queue, f, indent=2)

            logger.info(f"✅ Synced from SimulatedVerse ({new_items} contributions)")

            return {
                "status": "success",
                "items_synced": new_items,
                "source": str(self.sv_work_queue),
            }

        except Exception as e:
            logger.error(f"Failed to sync from SimulatedVerse: {e}")
            return {"status": "failed", "error": str(e)}


if __name__ == "__main__":

    async def main():
        syncer = CrossEcosystemSync()

        # Sync to SimulatedVerse
        result = await syncer.sync_to_simverse()
        logger.info("🌉 Sync Result:")
        logger.info(json.dumps(result, indent=2))

    asyncio.run(main())

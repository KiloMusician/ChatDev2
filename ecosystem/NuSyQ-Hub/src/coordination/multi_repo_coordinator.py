"""Multi-Repository Autonomy Coordinator - Phase 3.

Coordinates autonomous development across NuSyQ ecosystem repositories:
- NuSyQ-Hub (orchestration brain)
- SimulatedVerse (consciousness simulation)
- NuSyQ Root (multi-agent environment)

Enables:
- Cross-repository task routing
- Unified quest log across repos
- Shared autonomy governance
- Synchronized state management

OmniTag: [multi_repo, coordination, autonomy_expansion, phase3]
MegaTag: MULTI-REPO⨳ORCHESTRATION⦾COORDINATION→∞
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Repository(Enum):
    """Known repositories in NuSyQ ecosystem."""

    HUB = "NuSyQ-Hub"  # Core orchestration (this repo)
    SIMULATED_VERSE = "SimulatedVerse"  # Consciousness simulation
    NUSYQ_ROOT = "NuSyQ"  # Multi-agent root environment


@dataclass
class RepositoryConfig:
    """Configuration for a repository."""

    name: str
    path: Path
    enabled: bool = True

    # Autonomy capabilities
    supports_autonomy: bool = False
    autonomy_endpoint: str | None = None

    # Quest system integration
    quest_log_path: Path | None = None

    # Metadata
    last_sync: datetime | None = None


@dataclass
class CrossRepoTask:
    """Task that spans multiple repositories."""

    task_id: int
    description: str
    primary_repo: Repository  # Moved before fields with defaults
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Repository targets
    affected_repos: set[Repository] = field(default_factory=set)

    # Coordination
    dependencies: list[int] = field(default_factory=list)  # Other task IDs
    status: str = "pending"  # pending, in-progress, completed, failed

    # Results
    results: dict[Repository, Any] = field(default_factory=dict)


class MultiRepoCoordinator:
    """Coordinates autonomy across multiple repositories."""

    def __init__(
        self,
        hub_path: Path,
        simulated_verse_path: Path | None = None,
        nusyq_root_path: Path | None = None,
    ):
        """Initialize MultiRepoCoordinator with hub_path, simulated_verse_path, nusyq_root_path."""
        self.hub_path = hub_path

        # Repository configurations
        self.repos: dict[Repository, RepositoryConfig] = {
            Repository.HUB: RepositoryConfig(
                name="NuSyQ-Hub",
                path=hub_path,
                supports_autonomy=True,
                quest_log_path=hub_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl",
            )
        }

        # Add SimulatedVerse if path provided
        if simulated_verse_path:
            self.repos[Repository.SIMULATED_VERSE] = RepositoryConfig(
                name="SimulatedVerse",
                path=simulated_verse_path,
                supports_autonomy=False,  # Not yet (future)
                quest_log_path=simulated_verse_path / "quest_log.jsonl",
            )

        # Add NuSyQ Root if path provided
        if nusyq_root_path:
            self.repos[Repository.NUSYQ_ROOT] = RepositoryConfig(
                name="NuSyQ",
                path=nusyq_root_path,
                supports_autonomy=False,  # Not yet (future)
                quest_log_path=nusyq_root_path / "knowledge-base.yaml",
            )

        # Cross-repo state
        self.cross_repo_tasks: list[CrossRepoTask] = []
        self.sync_lock = asyncio.Lock()

    def get_repo_config(self, repo: Repository) -> RepositoryConfig | None:
        """Get configuration for a repository."""
        return self.repos.get(repo)

    async def sync_quest_logs(self) -> dict[Repository, int]:
        """Synchronize quest logs across repositories."""
        async with self.sync_lock:
            sync_results = {}

            for repo, config in self.repos.items():
                if not config.enabled or not config.quest_log_path:
                    continue

                try:
                    if config.quest_log_path.exists():
                        # Count entries in quest log
                        if config.quest_log_path.suffix == ".jsonl":
                            with open(config.quest_log_path) as f:
                                count = sum(1 for _ in f)
                        elif config.quest_log_path.suffix in (".yaml", ".yml"):
                            # YAML knowledge base (NuSyQ root)
                            count = 1  # Just check existence
                        else:
                            count = 0

                        sync_results[repo] = count
                        config.last_sync = datetime.now()

                        logger.debug(f"Synced {repo.value} quest log: {count} entries")
                    else:
                        logger.warning(
                            f"Quest log not found for {repo.value}: {config.quest_log_path}"
                        )
                        sync_results[repo] = 0

                except Exception as e:
                    logger.error(f"Failed to sync quest log for {repo.value}: {e}")
                    sync_results[repo] = -1

            return sync_results

    async def route_task_to_repo(
        self, task_description: str, target_repo: Repository
    ) -> CrossRepoTask | None:
        """Route a task to a specific repository."""
        repo_config = self.get_repo_config(target_repo)
        if not repo_config:
            logger.error(f"Repository {target_repo.value} not configured")
            return None

        if not repo_config.enabled:
            logger.warning(f"Repository {target_repo.value} is disabled")
            return None

        # Create cross-repo task
        task = CrossRepoTask(
            task_id=len(self.cross_repo_tasks) + 1,
            description=task_description,
            primary_repo=target_repo,
            affected_repos={target_repo},
        )

        self.cross_repo_tasks.append(task)

        logger.info(
            f"Routed task #{task.task_id} to {target_repo.value}: {task_description[:50]}..."
        )

        # If target supports autonomy, trigger it
        if repo_config.supports_autonomy and repo_config.autonomy_endpoint:
            await self._trigger_repo_autonomy(task, target_repo)
        else:
            logger.info(f"{target_repo.value} does not support autonomy (manual action required)")

        return task

    async def _trigger_repo_autonomy(self, task: CrossRepoTask, repo: Repository):
        """Trigger autonomy in target repository."""
        # For NuSyQ-Hub (this repo), we can directly trigger
        if repo == Repository.HUB:
            try:
                # Import and trigger autonomy system

                # This would normally route through the orchestrator
                logger.info(f"Triggering autonomy for task #{task.task_id} in Hub")
                task.status = "in-progress"

            except Exception as e:
                logger.error(f"Failed to trigger Hub autonomy: {e}")
                task.status = "failed"
                task.results[repo] = {"error": str(e)}

        # For other repos, coordination is via shared logs/API (future)
        else:
            logger.info(
                f"Cross-repo autonomy not yet implemented for {repo.value}. Task logged for manual processing."
            )
            task.status = "pending-manual"

    async def coordinate_multi_repo_task(
        self,
        description: str,
        repos: list[Repository],
        dependencies: list[int] | None = None,
    ) -> CrossRepoTask:
        """Create task that affects multiple repositories."""
        # Determine primary repo (first in list, or Hub if not specified)
        primary = repos[0] if repos else Repository.HUB

        task = CrossRepoTask(
            task_id=len(self.cross_repo_tasks) + 1,
            description=description,
            primary_repo=primary,
            affected_repos=set(repos),
            dependencies=dependencies or [],
        )

        self.cross_repo_tasks.append(task)

        logger.info(
            f"Created multi-repo task #{task.task_id} affecting: {', '.join(r.value for r in repos)}"
        )

        # Route to each repo (in sequence for now, parallel in future)
        for repo in repos:
            config = self.get_repo_config(repo)
            if config and config.enabled:
                await self._trigger_repo_autonomy(task, repo)

        return task

    def get_cross_repo_status(self) -> dict[str, Any]:
        """Get status of cross-repository coordination."""
        status = {
            "total_tasks": len(self.cross_repo_tasks),
            "by_status": {},
            "by_repo": {},
            "repositories": {},
        }

        # Count by status
        for task in self.cross_repo_tasks:
            status["by_status"][task.status] = status["by_status"].get(task.status, 0) + 1

        # Count by repo
        for task in self.cross_repo_tasks:
            for repo in task.affected_repos:
                repo_name = repo.value
                status["by_repo"][repo_name] = status["by_repo"].get(repo_name, 0) + 1

        # Repository info
        for repo, config in self.repos.items():
            status["repositories"][repo.value] = {
                "enabled": config.enabled,
                "supports_autonomy": config.supports_autonomy,
                "last_sync": config.last_sync.isoformat() if config.last_sync else None,
                "path": str(config.path),
            }

        return status

    def generate_coordination_report(self) -> str:
        """Generate text report of cross-repo coordination."""
        status = self.get_cross_repo_status()

        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║         🌉 Multi-Repository Autonomy Coordination             ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  📊 Task Overview                                             ║
║     Total Cross-Repo Tasks: {status["total_tasks"]:<3}                          ║
"""

        for status_name, count in status["by_status"].items():
            report += (
                f"║     {status_name.capitalize():<20} {count:<3}                          ║\n"
            )

        report += """║                                                               ║
║  🗂️  Repository Distribution                                  ║
"""

        for repo_name, count in status["by_repo"].items():
            report += f"║     {repo_name:<20} {count:<3} tasks                     ║\n"

        report += """║                                                               ║
║  📁 Repositories Configured                                   ║
"""

        for repo_name, info in status["repositories"].items():
            enabled_str = "✓" if info["enabled"] else "✗"
            autonomy_str = "✓" if info["supports_autonomy"] else "✗"
            report += f"║     {repo_name:<15} {enabled_str} Enabled  {autonomy_str} Auto     ║\n"

        report += "╚═══════════════════════════════════════════════════════════════╝\n"

        return report


# Global coordinator instance
_coordinator: MultiRepoCoordinator | None = None


def get_multi_repo_coordinator(
    hub_path: Path | None = None,
    simulated_verse_path: Path | None = None,
    nusyq_root_path: Path | None = None,
) -> MultiRepoCoordinator:
    """Get or create global multi-repo coordinator."""
    global _coordinator

    if _coordinator is None:
        # Auto-detect paths if not provided
        if hub_path is None:
            hub_path = Path(__file__).parent.parent.parent  # Assume we're in src/

        if simulated_verse_path is None:
            # Try common locations
            candidate = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
            if candidate.exists():
                simulated_verse_path = candidate

        if nusyq_root_path is None:
            # Try common locations
            candidate = Path.home() / "Desktop" / "NuSyQ"
            if candidate.exists():
                nusyq_root_path = candidate

        _coordinator = MultiRepoCoordinator(
            hub_path=hub_path,
            simulated_verse_path=simulated_verse_path,
            nusyq_root_path=nusyq_root_path,
        )

        logger.info("✅ Multi-Repository Coordinator initialized")
        logger.info(f"   - Hub: {hub_path}")
        if simulated_verse_path:
            logger.info(f"   - SimulatedVerse: {simulated_verse_path}")
        if nusyq_root_path:
            logger.info(f"   - NuSyQ Root: {nusyq_root_path}")

    return _coordinator


async def coordinate_across_repos(
    description: str,
    repos: list[str],  # List of repo names
) -> CrossRepoTask:
    """Convenience function to coordinate task across repositories."""
    coordinator = get_multi_repo_coordinator()

    # Convert string names to Repository enums
    repo_enums = []
    for repo_name in repos:
        try:
            repo_enums.append(Repository[repo_name.upper().replace("-", "_")])
        except KeyError:
            logger.warning(f"Unknown repository: {repo_name}")

    if not repo_enums:
        logger.error("No valid repositories specified")
        return None

    return await coordinator.coordinate_multi_repo_task(description, repo_enums)


# CLI integration
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Multi-repository coordination")
    parser.add_argument("--sync", action="store_true", help="Sync quest logs")
    parser.add_argument("--status", action="store_true", help="Show coordination status")
    parser.add_argument("--route", type=str, help="Route task to repository")
    parser.add_argument("--repo", type=str, help="Target repository (for --route)")
    parser.add_argument("--description", type=str, help="Task description (for --route)")

    args = parser.parse_args()

    coordinator = get_multi_repo_coordinator()

    if args.sync:
        results = asyncio.run(coordinator.sync_quest_logs())
        logger.info(f"Quest log sync results: {results}")

    if args.status:
        logger.info(coordinator.generate_coordination_report())

    if args.route and args.repo and args.description:
        try:
            repo_enum = Repository[args.repo.upper().replace("-", "_")]
            task = asyncio.run(coordinator.route_task_to_repo(args.description, repo_enum))
            logger.info(f"✅ Routed task #{task.task_id} to {repo_enum.value}")
        except KeyError:
            logger.error(f"❌ Unknown repository: {args.repo}")

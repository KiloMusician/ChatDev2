"""Unified PU Queue - Centralized Task Management Across 3 Repositories.

Integrates:
- NuSyQ-Hub: Repository analysis, quantum tasks, evolution tracking
- NuSyQ Root: Ollama inference, ChatDev workflows, MCP coordination
- SimulatedVerse: 9 proof-gated agents, PU generation, validation

Features:
- Council-based priority voting
- Cross-repository task submission
- Execution tracking and status reporting
- Temple knowledge storage integration
"""

import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Add NuSyQ-Hub src to path
HUB_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(HUB_PATH / "src"))

logger = logging.getLogger(__name__)

try:
    from integration.simulatedverse_unified_bridge import SimulatedVerseBridge
except ImportError:
    try:
        from integration.simulatedverse_unified_bridge import \
            SimulatedVerseUnifiedBridge as SimulatedVerseBridge
    except ImportError:
        logger.info("  SimulatedVerseBridge not found, using standalone mode")
        SimulatedVerseBridge = None

try:
    from utils.repo_path_resolver import get_repo_path
except ImportError:  # pragma: no cover - fallback for standalone runs
    get_repo_path = None


@dataclass
class PU:
    """Processing Unit - Cross-repository task."""

    id: str
    type: str  # RefactorPU, DocPU, FeaturePU, BugFixPU, AnalysisPU
    title: str
    description: str
    source_repo: str  # nusyq-hub, nusyq-root, simulatedverse
    priority: str  # low, medium, high, critical
    proof_criteria: list[str]
    metadata: dict[str, Any]
    status: str  # queued, voting, approved, executing, completed, failed
    created_at: str = ""
    votes: dict[str, int] = field(default_factory=dict)  # Council voting results
    assigned_agents: list[str] = field(default_factory=list)
    execution_results: dict[str, Any] = field(default_factory=dict)
    completed_at: str = ""
    failed_at: str = ""
    last_error: str = ""
    associated_quest_id: str = ""
    background_task_id: str = ""
    dependencies: list[str] = field(default_factory=list)


class UnifiedPUQueue:
    """Centralized task queue for 22-agent ecosystem."""

    def __init__(self) -> None:
        """Initialize UnifiedPUQueue."""
        self.queue_file = HUB_PATH / "data" / "unified_pu_queue.json"
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize SimulatedVerse bridge if available
        self.sv_bridge = None
        if SimulatedVerseBridge:
            if get_repo_path:
                try:
                    sv_path = get_repo_path("SIMULATEDVERSE_ROOT")
                except Exception:
                    sv_path = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
            else:
                sv_path = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
            if sv_path.exists():
                self.sv_bridge = SimulatedVerseBridge(str(sv_path))

        self.queue: list[PU] = self._load_queue()

    def _load_queue(self) -> list[PU]:
        """Load existing queue from disk."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        return []

                    queue: list[PU] = []
                    valid_fields = set(PU.__dataclass_fields__.keys())
                    dropped = 0

                    for raw_item in data:
                        if not isinstance(raw_item, dict):
                            dropped += 1
                            continue

                        item = dict(raw_item)
                        if "source" in item and "source_repo" not in item:
                            item["source_repo"] = item.pop("source")

                        normalized: dict[str, Any] = {k: item[k] for k in valid_fields if k in item}
                        normalized.setdefault("id", "")
                        normalized.setdefault("type", "AnalysisPU")
                        normalized.setdefault("title", "(untitled)")
                        normalized.setdefault("description", "")
                        normalized.setdefault("source_repo", "nusyq-hub")
                        normalized.setdefault("priority", "medium")
                        normalized.setdefault("proof_criteria", ["diagnose", "resolve", "verify"])
                        normalized.setdefault("metadata", {})
                        normalized.setdefault("status", "queued")
                        normalized.setdefault("created_at", "")
                        normalized.setdefault("votes", {})
                        normalized.setdefault("assigned_agents", [])
                        normalized.setdefault("execution_results", {})
                        normalized.setdefault("completed_at", "")
                        normalized.setdefault("failed_at", "")
                        normalized.setdefault("last_error", "")
                        normalized.setdefault("associated_quest_id", "")
                        normalized.setdefault("background_task_id", "")
                        normalized.setdefault("dependencies", [])

                        queue.append(PU(**normalized))

                    if dropped:
                        logger.info("  Dropped %s invalid queue entries during load", dropped)
                    return queue
            except Exception as e:
                logger.info(f"  Error loading queue: {e}")
        return []

    def _save_queue(self) -> None:
        """Persist queue to disk."""
        try:
            existing_raw: list[dict[str, Any]] = []
            if self.queue_file.exists():
                try:
                    with open(self.queue_file, encoding="utf-8") as f:
                        loaded = json.load(f)
                        if isinstance(loaded, list):
                            existing_raw = [entry for entry in loaded if isinstance(entry, dict)]
                except Exception:
                    existing_raw = []

            existing_by_id = {
                str(entry.get("id")): entry
                for entry in existing_raw
                if isinstance(entry.get("id"), str) and entry.get("id")
            }

            merged_records: list[dict[str, Any]] = []
            seen_ids: set[str] = set()

            for pu in self.queue:
                record = asdict(pu)
                pu_id = record.get("id")
                if isinstance(pu_id, str) and pu_id and pu_id in existing_by_id:
                    merged = dict(existing_by_id[pu_id])
                    merged.update(record)
                    merged_records.append(merged)
                    seen_ids.add(pu_id)
                else:
                    merged_records.append(record)
                    if isinstance(pu_id, str) and pu_id:
                        seen_ids.add(pu_id)

            # Preserve entries not currently loaded in-memory to avoid truncation from
            # mixed writers that include extra schema fields.
            for pu_id, entry in existing_by_id.items():
                if pu_id not in seen_ids:
                    merged_records.append(entry)

            with open(self.queue_file, "w", encoding="utf-8") as f:
                json.dump(merged_records, f, indent=2)
        except Exception as e:
            logger.info(f"  Error saving queue: {e}")

    def submit_pu(self, pu: PU) -> str:
        """Submit a new PU to the queue."""
        pu.id = f"PU-{len(self.queue) + 1}-{int(time.time())}"
        pu.created_at = datetime.now().isoformat()
        pu.status = "queued"

        self.queue.append(pu)
        self._save_queue()

        logger.info(f" PU Submitted: {pu.id}")
        logger.info(f"   Type: {pu.type}")
        logger.info(f"   Title: {pu.title}")
        logger.info(f"   Source: {pu.source_repo}")
        logger.info(f"   Priority: {pu.priority}")

        return pu.id

    def request_council_vote(self, pu_id: str, timeout: int = 30) -> dict[str, int]:
        """Request Council to vote on PU priority."""
        pu = self._find_pu(pu_id)
        if not pu:
            return {}

        if not self.sv_bridge:
            # Simulate voting without SimulatedVerse
            logger.info("  SimulatedVerse unavailable, using simulated voting")
            pu.votes = {"approve": 7, "reject": 0, "abstain": 2}
            pu.status = "approved"
            self._save_queue()
            return pu.votes

        logger.info(f"  Requesting Council vote for {pu_id}...")

        try:
            task_id = self.sv_bridge.submit_task(
                "council",
                "Vote on PU priority and viability",
                {
                    "pu": asdict(pu),
                    "vote_options": ["approve", "reject", "defer"],
                    "criteria": pu.proof_criteria,
                },
            )

            result = self.sv_bridge.check_result(task_id, timeout=timeout)

            if result and "effects" in result and "stateDelta" in result["effects"]:
                votes_data = result["effects"]["stateDelta"]
                pu.votes = votes_data.get("votes", {"approve": 5, "reject": 0, "defer": 4})

                # Approve if majority vote
                if pu.votes.get("approve", 0) > pu.votes.get("reject", 0):
                    pu.status = "approved"
                else:
                    pu.status = "rejected"

                self._save_queue()

                logger.info(f" Council Vote Complete: {pu.votes}")
                return pu.votes
            logger.info("  Council timeout, using default approval")
            pu.votes = {"approve": 5, "reject": 0, "defer": 4}
            pu.status = "approved"
            self._save_queue()
            return pu.votes

        except Exception as e:
            logger.info(f"  Council vote error: {e}")
            pu.votes = {"approve": 5, "reject": 0, "defer": 4}
            pu.status = "approved"
            self._save_queue()
            return pu.votes

    def assign_agents(self, pu_id: str, complexity: str = "auto") -> list[str]:
        """Assign appropriate agents based on PU type and complexity."""
        pu = self._find_pu(pu_id)
        if not pu:
            return []

        # Agent assignment logic based on PU type
        agent_map = {
            "RefactorPU": ["zod", "redstone", "culture-ship"],
            "DocPU": ["librarian", "zod"],
            "FeaturePU": ["party", "council", "zod", "redstone"],
            "BugFixPU": ["alchemist", "zod", "redstone"],
            "AnalysisPU": ["council", "redstone", "culture-ship"],
        }

        agents = agent_map.get(pu.type, ["party"])

        # Add Ollama models for code generation
        if pu.type in ["FeaturePU", "BugFixPU", "RefactorPU"]:
            if complexity == "low" or pu.priority == "low":
                agents.insert(0, "ollama:phi3.5")
            elif complexity == "medium" or pu.priority == "medium":
                agents.insert(0, "ollama:qwen2.5-coder:7b")
            else:
                agents.insert(0, "ollama:llama3.1:8b")

        # Add ChatDev for complex workflows
        if pu.type == "FeaturePU" and pu.priority in ["high", "critical"]:
            agents.insert(0, "chatdev:full-team")

        pu.assigned_agents = agents
        self._save_queue()

        logger.info(f" Assigned Agents: {', '.join(agents)}")
        return agents

    def _execute_real_agents(self, pu: PU) -> dict[str, Any]:
        """Execute PU through real ChatDev/Ollama agents.

        Args:
            pu: PU to execute

        Returns:
            Dictionary with execution results for real agents
        """
        results: dict[str, Any] = {}

        for agent in pu.assigned_agents:
            if agent.startswith("chatdev:"):
                results[agent] = self._execute_chatdev_agent(pu, agent)
            elif agent.startswith("ollama:"):
                results[agent] = self._execute_ollama_agent(pu, agent)

        return results

    def _execute_chatdev_agent(self, pu: PU, agent: str) -> str:
        """Execute PU through ChatDev agent.

        Args:
            pu: PU to execute
            agent: ChatDev agent identifier (e.g., "chatdev:full-team")

        Returns:
            Execution result status
        """
        try:
            from src.orchestration.chatdev_autonomous_router import \
                ChatDevAutonomousRouter

            logger.info(f"    {agent}...")

            router = ChatDevAutonomousRouter()
            if not router.chatdev_available:
                logger.warning("      ChatDev not available, skipping")
                return "skipped_unavailable"

            # Create ChatDev task from PU
            task_result = router.route_task(
                task_description=f"{pu.title}\n\n{pu.description}",
                codebase_issues=pu.metadata.get("issues", []),
                priority=pu.priority,
            )

            if task_result and task_result.get("status") == "completed":
                logger.info(f"      {agent} completed")
                return "completed"
            else:
                logger.warning(f"      {agent} failed or timeout")
                return "failed"

        except ImportError:
            logger.warning("      ChatDev router not available")
            return "skipped_import_error"
        except Exception as e:
            logger.error(f"      {agent} error: {e}")
            return f"error: {e}"

    def _execute_ollama_agent(self, pu: PU, agent: str) -> str:
        """Execute PU through Ollama agent.

        Args:
            pu: PU to execute
            agent: Ollama agent identifier (e.g., "ollama:qwen2.5-coder:7b")

        Returns:
            Execution result status
        """
        try:
            from src.integration.ollama_integration import EnhancedOllamaHub

            logger.info(f"    {agent}...")

            # Extract model name from agent string
            model_name = agent.split(":", 1)[1] if ":" in agent else "mistral"

            # Create Ollama hub
            hub = EnhancedOllamaHub()

            # Create prompt from PU
            prompt = f"""Task: {pu.title}

Description:
{pu.description}

Type: {pu.type}
Priority: {pu.priority}

Please analyze this task and provide implementation guidance or code.
Focus on: {", ".join(pu.proof_criteria[:3])}
"""

            # Execute via Ollama (using basic requests since EnhancedOllamaHub uses async)
            import requests

            response = requests.post(
                f"{hub.base_url}/api/generate",
                json={"model": model_name, "prompt": prompt, "stream": False},
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"      {agent} completed")
                # Store Ollama response in PU metadata
                if "ollama_responses" not in pu.metadata:
                    pu.metadata["ollama_responses"] = {}
                pu.metadata["ollama_responses"][agent] = result.get("response", "")
                return "completed"
            else:
                logger.warning(f"      {agent} failed (status {response.status_code})")
                return "failed"

        except ImportError:
            logger.warning("      Ollama integration not available")
            return "skipped_import_error"
        except Exception as e:
            logger.error(f"      {agent} error: {e}")
            return f"error: {e}"

    def execute_pu(
        self, pu_id: str, _auto_execute: bool = False, real_mode: bool = False
    ) -> dict[str, Any]:
        """Execute PU through assigned agents.

        Args:
            pu_id: PU identifier
            auto_execute: Automatically execute without confirmation
            real_mode: If True, actually execute through ChatDev/Ollama agents.
                      If False (default), skip real agent execution (simulation mode).

        Returns:
            Dictionary with execution results per agent
        """
        pu = self._find_pu(pu_id)
        if not pu:
            return {"error": "PU not found"}

        if pu.status != "approved":
            logger.info(f"  PU not approved (status: {pu.status})")
            return {"error": "PU not approved"}

        if not pu.assigned_agents:
            self.assign_agents(pu_id)

        logger.info(f" Executing {pu_id}...")
        logger.info(f"   Agents: {', '.join(pu.assigned_agents)}")
        logger.info(f"   Mode: {'REAL' if real_mode else 'SIMULATED'}")

        pu.status = "executing"
        self._save_queue()

        results: dict[str, Any] = {}

        # Execute through real agents if real_mode enabled
        if real_mode:
            results.update(self._execute_real_agents(pu))

        # Execute through SimulatedVerse agents
        for agent in pu.assigned_agents:
            if agent.startswith(("ollama:", "chatdev:")):
                # Skip if already handled by real mode, or if real_mode is disabled
                if not real_mode:
                    logger.info(f"  Skipping {agent} (real_mode disabled)")
                continue

            if not self.sv_bridge:
                logger.info(f"  SimulatedVerse unavailable, skipping {agent}")
                continue

            logger.info(f"    {agent}...")
            try:
                task_id = self.sv_bridge.submit_task(
                    agent,
                    f"Execute {pu.type}: {pu.title}",
                    {"pu": asdict(pu), "proof_criteria": pu.proof_criteria},
                )

                result = self.sv_bridge.check_result(task_id, timeout=30)
                if result:
                    results[agent] = "completed"
                    logger.info(f"    {agent} completed")
                else:
                    results[agent] = "timeout"
                    logger.info(f"     {agent} timeout")
            except Exception as e:
                results[agent] = f"error: {e}"
                logger.info(f"    {agent} error: {e}")

        pu.execution_results = results

        # Check if all agents succeeded
        success_count = sum(1 for r in results.values() if r == "completed")
        total_agents = len(pu.assigned_agents)

        if success_count >= total_agents * 0.7:  # 70% success threshold
            pu.status = "completed"
            logger.info(f" PU Completed: {success_count}/{total_agents} agents succeeded")
        else:
            pu.status = "failed"
            logger.info(f" PU Failed: Only {success_count}/{total_agents} agents succeeded")

        self._save_queue()
        return results

    def get_status(self, filter_status: str | None = None) -> list[PU]:
        """Get queue status, optionally filtered by status."""
        if filter_status:
            return [pu for pu in self.queue if pu.status == filter_status]
        return self.queue

    def get_statistics(self) -> dict[str, Any]:
        """Get queue statistics."""
        total = len(self.queue)
        by_status: dict[str, Any] = {}
        by_repo: dict[str, Any] = {}
        by_type: dict[str, Any] = {}
        for pu in self.queue:
            by_status[pu.status] = by_status.get(pu.status, 0) + 1
            by_repo[pu.source_repo] = by_repo.get(pu.source_repo, 0) + 1
            by_type[pu.type] = by_type.get(pu.type, 0) + 1

        return {
            "total_pus": total,
            "by_status": by_status,
            "by_repository": by_repo,
            "by_type": by_type,
            "completion_rate": (by_status.get("completed", 0) / total if total > 0 else 0),
        }

    def _find_pu(self, pu_id: str) -> PU | None:
        """Find PU by ID."""
        for pu in self.queue:
            if pu.id == pu_id:
                return pu
        return None

    def display_queue(self) -> None:
        """Display formatted queue."""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"{'UNIFIED PU QUEUE':^80}")
        logger.info(f"{'=' * 80}\n")

        stats = self.get_statistics()
        logger.info(f" Total PUs: {stats['total_pus']}")
        logger.info("   Completion Rate: %.1f%%", stats["completion_rate"] * 100)
        logger.info("\n By Status:")
        for status, count in stats["by_status"].items():
            logger.info(f"   {status}: {count}")

        logger.info("\n  By Repository:")
        for repo, count in stats["by_repository"].items():
            logger.info(f"   {repo}: {count}")

        logger.info("\n  By Type:")
        for pu_type, count in stats["by_type"].items():
            logger.info(f"   {pu_type}: {count}")

        logger.info(f"\n{'=' * 80}")
        logger.info("RECENT PUs (Last 10):")
        logger.info(f"{'=' * 80}\n")

        for pu in self.queue[-10:]:
            status_icon = {
                "queued": "",
                "voting": "",
                "approved": "",
                "executing": "",
                "completed": "",
                "failed": "",
                "rejected": "",
            }.get(pu.status, "")

            logger.info(f"{status_icon} {pu.id} - {pu.title}")
            logger.info(f"   Type: {pu.type} | Source: {pu.source_repo} | Priority: {pu.priority}")
            logger.info(f"   Status: {pu.status} | Agents: {len(pu.assigned_agents)}")
            if pu.votes:
                logger.info(f"   Votes: {pu.votes}")

    def generate_report(self, include_recent: int = 10) -> dict[str, Any]:
        """Generate a structured report of the queue.

        Args:
            include_recent: Number of recent PUs to include in the report.

        Returns:
            A dictionary report containing statistics and recent PU summaries.
        """
        stats = self.get_statistics()
        recent = []
        for pu in self.queue[-include_recent:]:
            recent.append(
                {
                    "id": pu.id,
                    "title": pu.title,
                    "type": pu.type,
                    "source_repo": pu.source_repo,
                    "priority": pu.priority,
                    "status": pu.status,
                }
            )

        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "recent": recent,
        }

        # Persist a receipt for CLI/tests if needed
        try:
            receipts_dir = HUB_PATH / "state" / "receipts" / "pu_queue"
            receipts_dir.mkdir(parents=True, exist_ok=True)
            out_file = receipts_dir / f"queue_report_{int(time.time())}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except Exception:
            # Non-fatal: don't break report generation on IO issues
            logger.debug("Suppressed Exception", exc_info=True)

        return report


def demo_unified_queue() -> "UnifiedPUQueue":
    """Demonstrate unified PU queue functionality."""
    logger.info("Unified PU Queue Demo\n")

    queue = UnifiedPUQueue()

    # Create sample PUs from different repositories
    pus = [
        PU(
            id="",
            type="RefactorPU",
            title="Remove console spam statements",
            description="Remove 93 console.log/print statements cluttering output",
            source_repo="nusyq-hub",
            priority="medium",
            proof_criteria=[
                "All spam statements removed",
                "No functional code affected",
                "Tests still pass",
            ],
            metadata={"files_affected": 12, "statements": 93},
            status="queued",
        ),
        PU(
            id="",
            type="DocPU",
            title="Document Ollama model usage patterns",
            description="Create comprehensive guide for 8 Ollama models",
            source_repo="nusyq-root",
            priority="high",
            proof_criteria=[
                "All 8 models documented",
                "Usage examples provided",
                "Performance benchmarks included",
            ],
            metadata={"models": 8},
            status="queued",
        ),
        PU(
            id="",
            type="FeaturePU",
            title="Add Culture-Ship auto-audit scheduler",
            description="Schedule automatic theater audits every 30 minutes",
            source_repo="simulatedverse",
            priority="high",
            proof_criteria=[
                "Scheduler implemented",
                "Configurable interval",
                "Results logged to Temple",
            ],
            metadata={"interval": "30min"},
            status="queued",
        ),
    ]

    # Submit PUs
    logger.info("Submitting PUs...\n")
    pu_ids: list[Any] = []
    for pu in pus:
        pu_id = queue.submit_pu(pu)
        pu_ids.append(pu_id)

    # Request Council votes
    logger.info("\nRequesting Council Votes...\n")
    for pu_id in pu_ids[:2]:  # Vote on first 2
        votes = queue.request_council_vote(pu_id)
        logger.info(f"   {pu_id}: {votes}\n")

    # Assign agents
    logger.info("\nAssigning Agents...\n")
    for pu_id in pu_ids[:2]:
        queue.assign_agents(pu_id, complexity="medium")

    # Display queue
    queue.display_queue()

    return queue


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "demo":
            demo_unified_queue()
        elif command == "status":
            queue = UnifiedPUQueue()
            queue.display_queue()
        elif command == "execute":
            if len(sys.argv) > 2:
                queue = UnifiedPUQueue()
                pu_id = sys.argv[2]
                queue.execute_pu(pu_id)
            else:
                logger.info("Usage: python unified_pu_queue.py execute <PU-ID>")
        else:
            logger.info(f"Unknown command: {command}")
            logger.info("Available commands: demo, status, execute <PU-ID>")
    else:
        demo_unified_queue()

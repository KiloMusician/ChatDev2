"""Quest-Driven Execution - Turn quests into automated actions.

Parses quest_log.jsonl to find actionable tasks and automatically
executes safe actions using the action catalog.

Workflow:
1. Parse active quests from quest_log.jsonl
2. Match quest type to actions in action_catalog.json
3. Filter for SAFE actions only
4. Execute action
5. Log result back to quest_log.jsonl
6. Update ZETA progress if applicable
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Quest:
    """Parsed quest from quest_log.jsonl."""

    timestamp: str
    task_type: str  # analyze, review, debug, test, etc.
    description: str
    status: str  # active, completed, failed, blocked
    result: dict[str, Any] | None = None

    @classmethod
    def from_jsonl_line(cls, line: str) -> Quest | None:
        """Parse quest from JSONL line."""
        try:
            data = json.loads(line.strip())
            return cls(
                timestamp=data.get("timestamp", ""),
                task_type=data.get("task_type", ""),
                description=data.get("description", ""),
                status=data.get("status", "unknown"),
                result=data.get("result"),
            )
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.debug("Failed to parse quest line: %s (error: %s)", line[:80], exc)
            return None


@dataclass
class Action:
    """Executable action from action_catalog.json."""

    name: str
    invocation: str  # Command template
    safety_level: str  # safe, moderate, risky
    description: str
    expected_outputs: list[str]


class QuestExecutor:
    """Executes quests automatically using action catalog."""

    def __init__(self, hub_path: Path) -> None:
        """Initialize executor.

        Args:
            hub_path: NuSyQ-Hub root directory
        """
        self.hub_path = hub_path
        self.quest_log_path = hub_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        self.catalog_path = hub_path / "config" / "action_catalog.json"
        self.zeta_path = hub_path / "config" / "ZETA_PROGRESS_TRACKER.json"

    def load_active_quests(self) -> list[Quest]:
        """Load all active quests from quest_log.jsonl.

        Returns:
            List of active quests
        """
        if not self.quest_log_path.exists():
            return []

        quests = []
        lines = self.quest_log_path.read_text(encoding="utf-8").splitlines()

        for line in reversed(lines):  # Most recent first
            quest = Quest.from_jsonl_line(line)
            if quest and quest.status in ["active", "in_progress"]:
                quests.append(quest)

        return quests

    def load_action_catalog(self) -> dict[str, Action]:
        """Load action catalog.

        Returns:
            Dict mapping action name to Action object
        """
        if not self.catalog_path.exists():
            return {}

        try:
            data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
            actions = {}

            # Parse wired actions
            for name, info in data.get("wired_actions", {}).items():
                actions[name] = Action(
                    name=name,
                    invocation=f"python scripts/start_nusyq.py {name}",
                    safety_level=info.get("safety", "moderate"),
                    description=info.get("desc", ""),
                    expected_outputs=info.get("outputs", []),
                )

            return actions
        except (json.JSONDecodeError, TypeError, KeyError, OSError) as exc:
            logger.warning("Failed to load action catalog: %s", exc)
            return {}

    def match_quest_to_action(self, quest: Quest, actions: dict[str, Action]) -> Action | None:
        """Match a quest to an executable action.

        Args:
            quest: Quest to match
            actions: Available actions

        Returns:
            Matched action, or None
        """
        # Direct match by task type
        if quest.task_type in actions:
            return actions[quest.task_type]

        # Fuzzy match by description keywords
        desc_lower = quest.description.lower()
        for name, action in actions.items():
            if name in desc_lower or action.description.lower() in desc_lower:
                return action

        return None

    def execute_action(self, action: Action, quest: Quest) -> dict[str, Any]:
        """Execute an action safely.

        Args:
            action: Action to execute
            quest: Quest that triggered the action

        Returns:
            Execution result
        """
        # Build command
        cmd = action.invocation.split()

        # Add quest-specific args if needed
        if action.name in ["analyze", "review"] and "file" in quest.description.lower():
            # Extract file path from description (simple heuristic)
            words = quest.description.split()
            for word in words:
                if "/" in word or "\\" in word or word.endswith(".py"):
                    cmd.append(word)
                    break

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                cwd=self.hub_path,
                check=False,
            )

            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "stdout": result.stdout[:1000],  # Truncate for logging
                "stderr": result.stderr[:500],
                "action": action.name,
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "error": "Timeout exceeded (120s)",
                "action": action.name,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "action": action.name,
            }

    def log_quest_result(self, quest: Quest, result: dict[str, Any]) -> None:
        """Log quest execution result back to quest_log.jsonl.

        Args:
            quest: Original quest
            result: Execution result
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task_type": quest.task_type,
            "description": f"AUTO-EXECUTED: {quest.description}",
            "status": result["status"],
            "result": result,
            "automated": True,
        }

        with open(self.quest_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def execute_next_safe_quest(self) -> dict[str, Any] | None:
        """Find and execute next safe quest.

        Returns:
            Execution result, or None if no safe quests
        """
        quests = self.load_active_quests()
        actions = self.load_action_catalog()

        if not quests:
            return {"status": "no_quests", "message": "No active quests found"}

        if not actions:
            return {"status": "no_actions", "message": "Action catalog not loaded"}

        # Find first safe quest
        for quest in quests:
            action = self.match_quest_to_action(quest, actions)
            if action and action.safety_level == "safe":
                logger.info(f"🎯 Executing quest: {quest.task_type} - {quest.description[:60]}...")
                logger.info(f"   Action: {action.name} ({action.safety_level})")

                result = self.execute_action(action, quest)
                self.log_quest_result(quest, result)

                if result["status"] == "completed":
                    logger.info("   ✅ Completed")
                else:
                    logger.error(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

                return {
                    "status": "executed",
                    "quest": quest.description,
                    "action": action.name,
                    "result": result,
                }

        return {
            "status": "no_safe_quests",
            "message": f"Found {len(quests)} active quests, but none are safe to auto-execute",
        }


def main() -> int:
    """CLI entrypoint for quest execution."""
    hub_path = Path(__file__).resolve().parents[2]  # Go up to NuSyQ-Hub root

    executor = QuestExecutor(hub_path)
    result = executor.execute_next_safe_quest()

    if result is None:
        logger.error('{"status": "error", "message": "No result returned"}')
        return 1

    logger.info(json.dumps(result, indent=2))
    return 0 if result["status"] in ["executed", "no_quests"] else 1


if __name__ == "__main__":
    sys.exit(main())

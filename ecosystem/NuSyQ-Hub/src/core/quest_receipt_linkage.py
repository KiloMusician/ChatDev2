"""Quest-Receipt Linkage System.

Bridges the action receipt ledger with the quest system, enabling:
- Action receipts linked to quest completion
- Quest status updates triggered by receipts
- Audit trail connecting decisions → quests → actions → outcomes

This is the **memory substrate** that connects consciousness (the decision cycle)
with persistence (the quest log and receipt ledger).

Usage:
    from src.core.quest_receipt_linkage import link_receipt_to_quest

    # When an action completes, link it to a quest
    link_receipt_to_quest(receipt, quest_id, world_state)
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

QUEST_RECEIPT_LINK_FILE = Path("src/Rosetta_Quest_System/quest_receipt_links.jsonl")
QUEST_LOG_FILE = Path("src/Rosetta_Quest_System/quest_log.jsonl")
EVENT_INDEX_FILE = Path("state/event_index.jsonl")


def _resolve_path(path: Path, workspace_root: Path) -> Path:
    if path.is_absolute():
        return path
    return workspace_root / path


def ensure_link_file(workspace_root: Path = Path(".")) -> Path:
    """Ensure the quest-receipt linkage file exists."""
    resolved = _resolve_path(QUEST_RECEIPT_LINK_FILE, workspace_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    if not resolved.exists():
        resolved.touch()
    return resolved


def _ensure_event_index_file(workspace_root: Path = Path(".")) -> Path:
    resolved = _resolve_path(EVENT_INDEX_FILE, workspace_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    if not resolved.exists():
        resolved.touch()
    return resolved


def append_quest_log_event(
    event: str,
    details: dict[str, Any],
    workspace_root: Path = Path("."),
) -> dict[str, Any]:
    """Append an event record to quest_log.jsonl."""
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event,
        "details": details,
    }
    quest_log = _resolve_path(QUEST_LOG_FILE, workspace_root)
    quest_log.parent.mkdir(parents=True, exist_ok=True)
    with open(quest_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")
    return payload


def _append_event_index(
    entry_type: str,
    refs: dict[str, Any],
    workspace_root: Path = Path("."),
) -> dict[str, Any]:
    """Append a generic cross-reference event index entry."""
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "type": entry_type,
        "refs": refs,
    }
    index_file = _ensure_event_index_file(workspace_root)
    with open(index_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")
    return payload


def link_receipt_to_quest(
    receipt: dict[str, Any],
    quest_id: str,
    world_state: dict[str, Any] | None = None,
    workspace_root: Path = Path("."),
) -> dict[str, Any]:
    """Link an action receipt to a quest.

    Args:
        receipt: ActionReceipt dict (from action_receipt_ledger.py)
        quest_id: ID of the quest this action contributes to
        world_state: Current world state (for context)
        workspace_root: Root directory for locating the link file.

    Returns:
        Link record (appended to quest_receipt_links.jsonl)
    """
    link_file = ensure_link_file(workspace_root)

    link = {
        "link_id": f"{receipt.get('receipt_id', 'unknown')}→{quest_id}",
        "timestamp": datetime.now(UTC).isoformat(),
        "receipt_id": receipt.get("receipt_id"),
        "action_id": receipt.get("action_id"),
        "quest_id": quest_id,
        "action_status": receipt.get("status"),
        "agent": receipt.get("agent"),
        "task_type": receipt.get("task_type"),
        "duration_s": receipt.get("duration_s"),
        "contributed_to_completion": False,  # Will be set to True if action completes quest
        "metadata": {
            "decision_epoch": world_state.get("decision_epoch") if world_state else None,
            "policy_category": receipt.get("metadata", {}).get("policy_category"),
            "risk_score": receipt.get("metadata", {}).get("risk_score"),
        },
    }

    # Append to linkage file
    try:
        with open(link_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(link, default=str) + "\n")
        logger.info(f"Linked receipt {receipt.get('receipt_id')[:8]}... to quest {quest_id}")
        append_quest_log_event(
            "action_receipt_linked",
            {
                "receipt_id": receipt.get("receipt_id"),
                "action_id": receipt.get("action_id"),
                "quest_id": quest_id,
                "status": receipt.get("status"),
                "agent": receipt.get("agent"),
                "task_type": receipt.get("task_type"),
            },
            workspace_root=workspace_root,
        )
        _append_event_index(
            "quest_receipt_link",
            {
                "receipt_id": receipt.get("receipt_id"),
                "action_id": receipt.get("action_id"),
                "quest_id": quest_id,
            },
            workspace_root=workspace_root,
        )
    except Exception as e:
        logger.error(f"Failed to link receipt to quest: {e}")

    return link


def update_quest_from_receipt(
    quest_engine: Any,  # QuestEngine instance
    receipt: dict[str, Any],
    quest_id: str,
) -> None:
    """Update a quest's status based on action receipt.

    Args:
        quest_engine: The quest engine instance
        receipt: ActionReceipt dict
        quest_id: ID of the quest to update
    """
    try:
        quest = quest_engine.quests.get(quest_id)
        if not quest:
            logger.warning(f"Quest {quest_id} not found")
            return

        # Update quest based on receipt status
        receipt_status = receipt.get("status")

        if receipt_status == "SUCCESS":
            # Mark quest as complete if it was the final step
            if quest.status == "active":
                quest_engine.complete_quest(quest_id)
                logger.info(f"Completed quest {quest_id} based on successful receipt")

        elif receipt_status == "FAILED":
            # Block quest and log the failure
            quest.status = "blocked"
            quest.history.append(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "event": "action_failed",
                    "receipt_id": receipt.get("receipt_id"),
                    "error": receipt.get("error_message", "Unknown error"),
                }
            )
            logger.warning(f"Quest {quest_id} blocked due to action failure")

        elif receipt_status == "PARTIAL":
            # Keep quest active but log partial success
            quest.history.append(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "event": "action_partial_success",
                    "receipt_id": receipt.get("receipt_id"),
                }
            )
            logger.info(f"Quest {quest_id} partially completed; still waiting on other steps")

    except Exception as e:
        logger.error(f"Failed to update quest {quest_id}: {e}")


def get_quest_action_history(
    quest_id: str, workspace_root: Path = Path(".")
) -> list[dict[str, Any]]:
    """Retrieve all actions linked to a quest.

    Args:
        quest_id: ID of the quest
        workspace_root: Root directory for locating the link file.

    Returns:
        List of link records in order of execution
    """
    link_file = ensure_link_file(workspace_root)

    history = []
    try:
        with open(link_file, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    link = json.loads(line)
                    if link.get("quest_id") == quest_id:
                        history.append(link)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Failed to read quest action history: {e}")

    # Sort by timestamp (oldest first)
    history.sort(key=lambda x: x.get("timestamp", ""), reverse=False)
    return history


def get_quests_for_epoch(
    world_state: dict[str, Any], workspace_root: Path = Path(".")
) -> list[str]:
    """Get active quests during a specific decision epoch.

    Args:
        world_state: World state dict (contains decision_epoch)
        workspace_root: Root directory for locating the link file.

    Returns:
        List of active quest IDs during that epoch
    """
    epoch = world_state.get("decision_epoch", 0)
    link_file = ensure_link_file(workspace_root)

    quests_in_epoch = set()
    try:
        with open(link_file, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    link = json.loads(line)
                    if link.get("metadata", {}).get("decision_epoch") == epoch:
                        quests_in_epoch.add(link.get("quest_id"))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Failed to get quests for epoch {epoch}: {e}")

    return list(quests_in_epoch)


def stats(workspace_root: Path = Path(".")) -> dict[str, Any]:
    """Compute statistics over quest-receipt linkage.

    Returns:
        {
            "total_links": int,
            "successful_actions": int,
            "failed_actions": int,
            "partial_actions": int,
            "unique_quests": int,
            "by_agent": dict
        }
    """
    link_file = ensure_link_file(workspace_root)

    total = 0
    successful = 0
    failed = 0
    partial = 0
    quests = set()
    by_agent = {}

    try:
        with open(link_file, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    link = json.loads(line)
                    total += 1

                    status = link.get("action_status")
                    if status == "SUCCESS":
                        successful += 1
                    elif status == "FAILED":
                        failed += 1
                    elif status == "PARTIAL":
                        partial += 1

                    quests.add(link.get("quest_id"))

                    agent = link.get("agent")
                    if agent not in by_agent:
                        by_agent[agent] = {"link_count": 0, "successful": 0}
                    by_agent[agent]["link_count"] += 1
                    if status == "SUCCESS":
                        by_agent[agent]["successful"] += 1

                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Failed to compute stats: {e}")

    return {
        "total_links": total,
        "successful_actions": successful,
        "failed_actions": failed,
        "partial_actions": partial,
        "unique_quests": len(quests),
        "by_agent": by_agent,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test: Show stats
    logger.info("Quest-Receipt Linkage Stats:")
    logger.info(json.dumps(stats(), indent=2))

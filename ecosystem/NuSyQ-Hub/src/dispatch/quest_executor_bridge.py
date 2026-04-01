"""Quest-to-Execution Bridge — Drains GuildBoard quests through MJOLNIR.

Connects two existing systems that were never wired together:
- GuildBoard.get_available_quests() → retrieves OPEN quests
- MjolnirProtocol.ask() → routes to the appropriate agent

The bridge claims quests atomically, executes them via MJOLNIR's ask(),
and marks them complete/failed on the guild board.

Usage:
    bridge = QuestExecutorBridge()
    results = await bridge.drain(limit=5)
    # results: [{"quest_id": "...", "success": True, "result": {...}}, ...]
"""

from __future__ import annotations

import logging
from typing import Any

from src.dispatch.mjolnir import (AGENT_ALIASES, MjolnirProtocol,
                                  _infer_task_type)

logger = logging.getLogger(__name__)

# Reverse map: priority int → string name
_PRIORITY_INT_TO_STR: dict[int, str] = {
    1: "CRITICAL",
    2: "HIGH",
    3: "NORMAL",
    4: "LOW",
    5: "BACKGROUND",
}

# Known agent names for tag extraction
_KNOWN_AGENTS: set[str] = set(AGENT_ALIASES.values()) - {"auto"}


def _extract_target_from_tags(tags: list[str]) -> str:
    """Extract agent target from quest tags.

    Scans tags for known agent names. Returns "auto" if none found.

    Examples:
        ["mjolnir", "ollama"] → "ollama"
        ["culture-ship", "escalation"] → "auto"
        ["mjolnir", "delegate", "codex"] → "codex"
    """
    for tag in tags:
        normalized = tag.strip().lower()
        if normalized in _KNOWN_AGENTS:
            return normalized
    return "auto"


def _quest_priority_to_string(priority: int) -> str:
    """Map quest priority int (1-5) to string name."""
    return _PRIORITY_INT_TO_STR.get(priority, "NORMAL")


class QuestExecutorBridge:
    """Drains OPEN quests from GuildBoard → MjolnirProtocol execution."""

    def __init__(self, protocol: MjolnirProtocol | None = None) -> None:
        """Initialize QuestExecutorBridge with protocol."""
        self._protocol = protocol

    def _get_protocol(self) -> MjolnirProtocol:
        """Lazy-init MjolnirProtocol."""
        if self._protocol is None:
            self._protocol = MjolnirProtocol()
        return self._protocol

    async def drain(self, limit: int = 5) -> list[dict[str, Any]]:
        """Pull up to `limit` OPEN quests, execute, and update guild state.

        Each quest is:
        1. Retrieved via get_available_quests()
        2. Claimed atomically (prevents double-processing)
        3. Routed through MjolnirProtocol.ask() with inferred target + task_type
        4. Marked complete or abandoned on the guild board

        Args:
            limit: Maximum number of quests to process in this drain cycle.

        Returns:
            List of result dicts, one per quest attempted:
            [{"quest_id": str, "success": bool, "agent": str, "result": dict}, ...]
        """
        try:
            from src.guild.guild_board import GuildBoard
        except ImportError:
            logger.error("GuildBoard not available — cannot drain quests")
            return []

        guild = GuildBoard()
        protocol = self._get_protocol()
        results: list[dict[str, Any]] = []

        # 1. Fetch available quests
        try:
            quests = await guild.get_available_quests(agent_capabilities=["mjolnir", "drain"])
        except Exception as exc:
            logger.error("Failed to fetch available quests: %s", exc)
            return []

        if not quests:
            logger.info("No OPEN quests to drain")
            return []

        logger.info("Found %d OPEN quests, draining up to %d", len(quests), limit)

        # 2. Process quests up to limit
        for quest in quests[:limit]:
            quest_result = await self._execute_quest(guild, protocol, quest)
            results.append(quest_result)

        drained = sum(1 for r in results if r["success"])
        logger.info("Drained %d/%d quests successfully", drained, len(results))
        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "agents",
                f"QuestExecutorBridge drained {drained}/{len(results)} quests",
                level="INFO",
                source="quest_executor_bridge",
            )
        except Exception:
            pass
        return results

    async def _execute_quest(
        self, guild: Any, protocol: MjolnirProtocol, quest: Any
    ) -> dict[str, Any]:
        """Execute a single quest: claim → route → complete/abandon."""
        quest_id = quest.quest_id

        # Claim quest atomically
        try:
            ok, msg = await guild.claim_quest(quest_id, agent_id="mjolnir-drain")
            if not ok:
                logger.debug("Quest %s claim failed: %s", quest_id, msg)
                return {
                    "quest_id": quest_id,
                    "success": False,
                    "agent": "none",
                    "error": f"Claim failed: {msg}",
                }
        except Exception as exc:
            logger.warning("Quest %s claim error: %s", quest_id, exc)
            return {
                "quest_id": quest_id,
                "success": False,
                "agent": "none",
                "error": str(exc),
            }

        # Determine target agent and task type from quest metadata
        target = _extract_target_from_tags(quest.tags)
        task_type = _infer_task_type(quest.title)
        priority_str = _quest_priority_to_string(quest.priority)

        # Execute through MJOLNIR
        try:
            envelope = await protocol.ask(
                target,
                quest.description,
                task_type=task_type,
                no_guild=True,  # Don't create a new quest for the execution
                priority=priority_str,
            )

            # Update guild state
            if envelope.success:
                try:
                    await guild.complete_quest(quest_id, agent_id="mjolnir-drain")
                except Exception as exc:
                    logger.debug("Quest %s complete update failed: %s", quest_id, exc)
            # Note: failed quests remain CLAIMED — can be manually abandoned later

            _level = "INFO" if envelope.success else "WARNING"
            _status = "complete" if envelope.success else "failed"
            try:
                from src.system.agent_awareness import emit as _emit

                _emit(
                    "agents",
                    f"Quest {quest_id} {_status} via {target} ({task_type})",
                    level=_level,
                    source="quest_executor_bridge",
                )
            except Exception:
                pass

            return {
                "quest_id": quest_id,
                "success": envelope.success,
                "agent": target,
                "task_type": task_type,
                "result": envelope.to_dict(),
            }

        except Exception as exc:
            logger.error("Quest %s execution failed: %s", quest_id, exc)
            try:
                from src.system.agent_awareness import emit as _emit

                _emit(
                    "agents",
                    f"Quest {quest_id} execution error: {exc}",
                    level="ERROR",
                    source="quest_executor_bridge",
                )
            except Exception:
                pass
            return {
                "quest_id": quest_id,
                "success": False,
                "agent": target,
                "error": str(exc),
            }

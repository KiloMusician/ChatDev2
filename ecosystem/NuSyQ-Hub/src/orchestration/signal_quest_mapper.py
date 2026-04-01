"""Signal → Quest Bridge.

======================

Purpose: When signals arrive (from error detection), automatically create tasks/quests.

Workflow:
1. Monitor guild board for new signals
2. For each signal, lookup template in registry
3. Create quest with:
   - title: Derived from signal message
   - description: Signal message + context
   - priority: Derived from severity
   - action_hint: Suggested action to resolve
   - signal_id: Link back to signal
   - estimated_effort: Time/complexity estimate
4. Post to quest_log.jsonl
5. Add to visible quests on guild board
6. Log quest creation with traceability

Run via:
    python src/orchestration/signal_quest_mapper.py [--mode once|watch|test]

Modes:
    once  - Map all unprocessed signals to quests once
    watch - Monitor guild board continuously
    test  - Dry run (don't modify quest log)
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent


class QuestPriority(Enum):
    """Priority levels for quests."""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


@dataclass
class SignalTemplate:
    """Template for signal type → quest."""

    signal_type: str
    signal_category: str  # "error", "warning", "blockers", etc.
    quest_title_template: str  # "Fix {error_category} errors"
    quest_description_template: str
    priority_from_severity: dict[str, int]  # severity → priority
    action_hint: str  # Suggested command to run
    estimated_effort: str  # "quick", "medium", "long"


# Signal type → Quest mapping templates
SIGNAL_QUEST_TEMPLATES = {
    "error:mypy": SignalTemplate(
        signal_type="error",
        signal_category="mypy",
        quest_title_template="Fix {count} type errors in mypy",
        quest_description_template=(
            "Type errors detected: {message}\n\nFiles affected: {files}\n\nExamples:\n{examples}"
        ),
        priority_from_severity={
            "critical": QuestPriority.CRITICAL.value,
            "high": QuestPriority.HIGH.value,
            "medium": QuestPriority.MEDIUM.value,
            "low": QuestPriority.LOW.value,
        },
        action_hint="python scripts/fix_type_errors_batch.py",
        estimated_effort="medium",
    ),
    "error:ruff": SignalTemplate(
        signal_type="error",
        signal_category="ruff",
        quest_title_template="Fix {count} ruff linting issues",
        quest_description_template=(
            "Linting issues detected: {message}\n\nFiles affected: {files}\n\nExamples:\n{examples}"
        ),
        priority_from_severity={
            "critical": QuestPriority.HIGH.value,
            "high": QuestPriority.HIGH.value,
            "medium": QuestPriority.MEDIUM.value,
            "low": QuestPriority.LOW.value,
        },
        action_hint="python scripts/start_nusyq.py enhance fix",
        estimated_effort="quick",
    ),
    "error:import": SignalTemplate(
        signal_type="error",
        signal_category="import",
        quest_title_template="Fix {count} import errors",
        quest_description_template=(
            "Import issues detected: {message}\n\nFiles affected: {files}\n\nExamples:\n{examples}"
        ),
        priority_from_severity={
            "critical": QuestPriority.CRITICAL.value,
            "high": QuestPriority.CRITICAL.value,
            "medium": QuestPriority.HIGH.value,
            "low": QuestPriority.MEDIUM.value,
        },
        action_hint="python scripts/quick_import_fix.py",
        estimated_effort="quick",
    ),
    "error:generic": SignalTemplate(  # Fallback
        signal_type="error",
        signal_category="generic",
        quest_title_template="Resolve issue: {message}",
        quest_description_template="Problem: {message}\n\nContext: {context}",
        priority_from_severity={
            "critical": QuestPriority.HIGH.value,
            "high": QuestPriority.HIGH.value,
            "medium": QuestPriority.MEDIUM.value,
            "low": QuestPriority.LOW.value,
        },
        action_hint="Investigate and resolve",
        estimated_effort="medium",
    ),
}


@dataclass
class QuestToCreate:
    """Quest ready to be created."""

    title: str
    description: str
    priority: int  # 1-5
    action_hint: str
    estimated_effort: str
    signal_id: str | None = None  # Link back to signal
    acceptance_criteria: list[str] | None = None
    tags: list[str] | None = None


def get_template_for_signal(signal_type: str, signal_category: str) -> SignalTemplate:
    """Get quest template for signal type."""
    # Try exact match first
    key = f"{signal_type}:{signal_category}"
    if key in SIGNAL_QUEST_TEMPLATES:
        return SIGNAL_QUEST_TEMPLATES[key]

    # Try signal type only
    for template_key, template in SIGNAL_QUEST_TEMPLATES.items():
        if template_key.startswith(signal_type):
            return template

    # Fallback to generic
    return SIGNAL_QUEST_TEMPLATES["error:generic"]


def signal_to_quest(
    signal_id: str,
    signal_type: str,
    severity: str,
    message: str,
    context: dict[str, Any] | None = None,
) -> QuestToCreate:
    """Convert signal to quest."""
    context = context or {}

    # Determine category and template
    signal_category = context.get("error_category", "generic")
    template = get_template_for_signal(signal_type, signal_category)

    # Extract fields from context
    error_count = context.get("error_count", 1)
    files = context.get("files_affected", [])
    examples = context.get("example_errors", [])

    # Format strings
    files_str = ", ".join(files[:3]) if files else "unknown"
    examples_str = "\n".join(f"  - {ex}" for ex in examples[:3]) if examples else "  (no examples)"

    # Build title and description
    title = template.quest_title_template.format(
        count=error_count,
        category=signal_category,
        message=message,
    )

    description = template.quest_description_template.format(
        message=message,
        files=files_str,
        examples=examples_str,
        context=json.dumps(context, indent=2),
        count=error_count,
    )

    # Determine priority
    priority = template.priority_from_severity.get(severity.lower(), QuestPriority.MEDIUM.value)

    # Build acceptance criteria
    acceptance_criteria = [
        f"Resolve all {error_count} {signal_category} errors",
        "Run error scanner to verify",
        "Update guild board with completion",
    ]

    # Tags for discovery
    tags = [
        "error",
        signal_category,
        f"priority_{priority}",
        f"effort_{template.estimated_effort}",
    ]

    return QuestToCreate(
        title=title,
        description=description,
        priority=priority,
        action_hint=template.action_hint,
        estimated_effort=template.estimated_effort,
        signal_id=signal_id,
        acceptance_criteria=acceptance_criteria,
        tags=tags,
    )


def quest_already_exists(quest_signal_id: str, quest_log_path: Path) -> bool:
    """Check if quest for this signal already exists."""
    if not quest_log_path.exists():
        return False

    try:
        with open(quest_log_path) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    # Check if this signal was already converted
                    if entry.get("signal_id") == quest_signal_id:
                        return True
                except json.JSONDecodeError:
                    logger.debug("Suppressed JSONDecodeError", exc_info=True)
    except Exception as e:
        logger.warning(f"Error checking quest log: {e}")

    return False


def quest_title_already_open(title: str, quest_log_path: Path) -> bool:
    """Check if an open quest with the same title already exists."""
    if not quest_log_path.exists():
        return False

    candidate = title.strip().casefold()
    if not candidate:
        return False

    try:
        with open(quest_log_path) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                existing_title = str(entry.get("title") or "").strip().casefold()
                existing_status = str(entry.get("status") or "").strip().lower()
                if existing_title == candidate and existing_status == "open":
                    return True
    except Exception as e:
        logger.warning(f"Error checking quest title dedup: {e}")

    return False


def add_quest_to_log(quest: QuestToCreate, quest_log_path: Path | None = None) -> bool:
    """Add quest to quest_log.jsonl."""
    if quest_log_path is None:
        quest_log_path = ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

    # Check if already exists
    if quest.signal_id and quest_already_exists(quest.signal_id, quest_log_path):
        logger.info(f"Quest for signal {quest.signal_id} already exists, skipping")
        return False
    if quest_title_already_open(quest.title, quest_log_path):
        logger.info(f"Open quest with title '{quest.title}' already exists, skipping")
        return False

    quest_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create quest entry
    entry = {
        "id": f"quest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "title": quest.title,
        "quest": quest.title,  # Alias for compatibility
        "description": quest.description,
        "status": "open",
        "priority": quest.priority,
        "action_hint": quest.action_hint,
        "estimated_effort": quest.estimated_effort,
        "signal_id": quest.signal_id,
        "acceptance_criteria": quest.acceptance_criteria,
        "tags": quest.tags,
    }

    try:
        with open(quest_log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"✅ Created quest: {quest.title}")
        return True
    except Exception as e:
        logger.error(f"Error writing quest: {e}")
        return False


async def get_guild_board_signals() -> list[dict[str, Any]]:
    """Get unprocessed signals from guild board."""
    try:
        from src.guild.guild_board import GuildBoard
    except ImportError:
        logger.warning("Could not import GuildBoard")
        return []

    try:
        board = GuildBoard()
        signals: list[dict[str, Any]] = []
        # Newer GuildBoard implementations do not expose get_state(); prefer direct board snapshot.
        if hasattr(board, "get_state"):
            state = await board.get_state()  # type: ignore[attr-defined]
            if isinstance(state, dict):
                raw = state.get("signals", [])
                if isinstance(raw, list):
                    signals = [row for row in raw if isinstance(row, dict)]
        elif hasattr(board, "board") and hasattr(board.board, "signals"):
            raw = getattr(board.board, "signals", [])
            if isinstance(raw, list):
                signals = [row for row in raw if isinstance(row, dict)]
        elif hasattr(board, "get_board_summary"):
            summary = await board.get_board_summary()  # type: ignore[attr-defined]
            if isinstance(summary, dict):
                raw = summary.get("critical_signals", [])
                if isinstance(raw, list):
                    signals = [row for row in raw if isinstance(row, dict)]

        unprocessed = []
        for signal in signals:
            # Check if quest already exists for this signal
            signal_id = signal.get("id") or signal.get("timestamp")
            if not quest_already_exists(
                str(signal_id), ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
            ):
                unprocessed.append(signal)

        return unprocessed
    except Exception as e:
        logger.error(f"Error getting guild board signals: {e}")
        return []


async def bridge_cycle(test_mode: bool = False) -> dict[str, Any]:
    """Run one complete signal→quest bridge cycle."""
    logger.info("=" * 80)
    logger.info("SIGNAL→QUEST BRIDGE CYCLE")
    logger.info("=" * 80)

    # 1. Get signals from guild board
    logger.info("Step 1: Fetching signals from guild board...")
    signals = await get_guild_board_signals()
    logger.info(f"Found {len(signals)} unprocessed signals")

    # 2. Convert to quests
    logger.info("Step 2: Converting signals to quests...")
    quests_to_create = []

    for signal in signals:
        quest = signal_to_quest(
            signal_id=signal.get("id") or signal.get("timestamp"),
            signal_type=signal.get("type", "error"),
            severity=signal.get("severity", "medium"),
            message=signal.get("message", ""),
            context=signal.get("context"),
        )
        quests_to_create.append(quest)
        logger.info(f"  - {quest.title} (priority: {quest.priority})")

    # 3. Add to quest log
    logger.info("Step 3: Adding quests to log...")
    quest_log_path = ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    created_count = 0

    for quest in quests_to_create:
        if test_mode:
            logger.info(f"[TEST] Would create: {quest.title}")
        else:
            if add_quest_to_log(quest, quest_log_path):
                created_count += 1

    # 4. Summary
    logger.info(f"Created {created_count} quests")

    return {
        "timestamp": datetime.now().isoformat(),
        "signals_found": len(signals),
        "quests_created": created_count,
        "test_mode": test_mode,
    }


async def watch_mode(interval: int = 60) -> None:
    """Run bridge in watch mode - continuously check for signals."""
    logger.info(f"Starting watch mode (check every {interval}s)")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            cycle_result = await bridge_cycle(test_mode=False)
            quests_created = cycle_result.get("quests_created", 0)

            if quests_created > 0:
                logger.info(f"✅ Created {quests_created} new quests")
            else:
                logger.info("No new signals to process")

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Watch mode stopped by user")


async def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Signal→Quest Bridge")
    parser.add_argument(
        "--mode",
        choices=["once", "watch", "test"],
        default="once",
        help="Run mode: once (default), watch (continuous), or test (dry-run)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval for watch mode (seconds)",
    )

    args = parser.parse_args()

    try:
        if args.mode == "test":
            logger.info("Running in TEST MODE - no quests will be created")
            result = await bridge_cycle(test_mode=True)
            logger.info(json.dumps(result, indent=2))
            return 0

        elif args.mode == "once":
            result = await bridge_cycle(test_mode=False)
            logger.info(json.dumps(result, indent=2))
            return 0

        elif args.mode == "watch":
            await watch_mode(interval=args.interval)
            return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))

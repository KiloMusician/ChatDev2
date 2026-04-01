#!/usr/bin/env python3
"""Emergence Acknowledgement Protocol - Metabolize Phase Jumps into Memory.

This module provides the ritual for capturing, labeling, and integrating
emergent behavior when the system does something ahead-of-phase or surprising.

Core principle: **Emergence must be captured, not punished.**

The system learns to announce: "I went ahead — here's why, here's how to hold it."
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class EmergenceType(Enum):
    """Types of emergent behavior."""

    PHASE_JUMP = "phase_jump"  # Did future-phase work
    CAPABILITY_SYNTHESIS = "capability_synthesis"  # Combined multiple domains
    ARCHITECTURAL_LEAP = "architectural_leap"  # Built new infrastructure
    INSIGHT_DISCOVERY = "insight_discovery"  # Found unexpected pattern
    SELF_OPTIMIZATION = "self_optimization"  # Improved own processes


class IntegrationStatus(Enum):
    """Status of emerged capability."""

    QUARANTINED = "quarantined"  # Isolated, needs review
    EXPERIMENTAL = "experimental"  # Available behind flag
    VALIDATED = "validated"  # Tested, works
    CANONICAL = "canonical"  # Promoted to baseline
    ARCHIVED = "archived"  # Preserved but not active


@dataclass
class EmergenceEvent:
    """Record of an emergence event."""

    timestamp: str
    emergence_type: EmergenceType
    title: str
    description: str
    what_was_done: list[str]  # Concrete actions taken
    why_it_matters: str  # Value proposition
    files_changed: list[str]
    dependencies_added: list[str]
    rollback_instructions: str
    integration_status: IntegrationStatus
    phase_intended: str  # What phase was this meant for?
    phase_executed: str  # What phase did it happen in?

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "type": self.emergence_type.value,
            "title": self.title,
            "description": self.description,
            "what_was_done": self.what_was_done,
            "why_it_matters": self.why_it_matters,
            "files_changed": self.files_changed,
            "dependencies_added": self.dependencies_added,
            "rollback_instructions": self.rollback_instructions,
            "integration_status": self.integration_status.value,
            "phase_intended": self.phase_intended,
            "phase_executed": self.phase_executed,
        }


class EmergenceProtocol:
    """Protocol for acknowledging and integrating emergent behavior."""

    def __init__(self, ledger_path: str = "state/emergence/ledger.jsonl") -> None:
        """Initialize emergence protocol.

        Args:
            ledger_path: Path to emergence ledger
        """
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("✅ Emergence protocol initialized")

    def acknowledge(
        self,
        emergence_type: EmergenceType,
        title: str,
        description: str,
        what_was_done: list[str],
        why_it_matters: str,
        files_changed: list[str],
        dependencies_added: list[str] | None = None,
        rollback_instructions: str = "",
        phase_intended: str = "future",
        phase_executed: str = "current",
    ) -> EmergenceEvent:
        """Acknowledge an emergence event.

        This is the system saying: "I went ahead — here's what I did and why."

        Args:
            emergence_type: Type of emergence
            title: Short title
            description: What happened
            what_was_done: Concrete actions
            why_it_matters: Value proposition
            files_changed: List of files created/modified
            dependencies_added: New dependencies
            rollback_instructions: How to undo
            phase_intended: What phase this was meant for
            phase_executed: What phase it happened in

        Returns:
            EmergenceEvent record
        """
        event = EmergenceEvent(
            timestamp=datetime.now().isoformat(),
            emergence_type=emergence_type,
            title=title,
            description=description,
            what_was_done=what_was_done,
            why_it_matters=why_it_matters,
            files_changed=files_changed,
            dependencies_added=dependencies_added or [],
            rollback_instructions=rollback_instructions,
            integration_status=IntegrationStatus.QUARANTINED,
            phase_intended=phase_intended,
            phase_executed=phase_executed,
        )

        # Log to ledger
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

        logger.info(f"🌟 Emergence acknowledged: {title}")

        return event

    def promote(self, event_title: str, new_status: IntegrationStatus) -> None:
        """Change integration status of an emerged capability.

        Args:
            event_title: Title of event to promote
            new_status: New integration status
        """
        # Read all events
        events = []
        if self.ledger_path.exists():
            with open(self.ledger_path) as f:
                for line in f:
                    event_dict = json.loads(line)
                    if event_dict["title"] == event_title:
                        event_dict["integration_status"] = new_status.value
                    events.append(event_dict)

        # Rewrite ledger
        with open(self.ledger_path, "w") as f:
            for event_dict in events:
                f.write(json.dumps(event_dict) + "\n")

        logger.info(f"✅ Promoted '{event_title}' to {new_status.value}")

    def get_recent_emergences(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent emergence events.

        Args:
            limit: Maximum events to return

        Returns:
            List of event dictionaries
        """
        events = []
        if self.ledger_path.exists():
            with open(self.ledger_path) as f:
                events = [json.loads(line) for line in f]

        return events[-limit:]

    def format_emergence(self, event: EmergenceEvent) -> str:
        """Format emergence event for display.

        Args:
            event: Event to format

        Returns:
            Formatted string
        """
        type_emoji = {
            EmergenceType.PHASE_JUMP: "🚀",
            EmergenceType.CAPABILITY_SYNTHESIS: "🧬",
            EmergenceType.ARCHITECTURAL_LEAP: "🏗️",
            EmergenceType.INSIGHT_DISCOVERY: "💡",
            EmergenceType.SELF_OPTIMIZATION: "⚡",
        }

        status_emoji = {
            IntegrationStatus.QUARANTINED: "🔒",
            IntegrationStatus.EXPERIMENTAL: "🧪",
            IntegrationStatus.VALIDATED: "✅",
            IntegrationStatus.CANONICAL: "⭐",
            IntegrationStatus.ARCHIVED: "📦",
        }

        return f"""
{type_emoji[event.emergence_type]} **EMERGENCE: {event.title}**

**Type:** {event.emergence_type.value}
**Status:** {status_emoji[event.integration_status]} {event.integration_status.value}
**Phase:** {event.phase_executed} (intended for: {event.phase_intended})

**Description:**
{event.description}

**What Was Done:**
{chr(10).join(f"  • {item}" for item in event.what_was_done)}

**Why It Matters:**
{event.why_it_matters}

**Files Changed:**
{chr(10).join(f"  • {f}" for f in event.files_changed)}

{f"**Dependencies Added:**{chr(10)}{chr(10).join(f'  • {d}' for d in event.dependencies_added)}" if event.dependencies_added else ""}

**Rollback:**
{event.rollback_instructions if event.rollback_instructions else "No rollback instructions provided"}

**Timestamp:** {event.timestamp}
"""


# Global protocol instance
_global_protocol: EmergenceProtocol | None = None


def get_protocol() -> EmergenceProtocol:
    """Get or create global protocol instance."""
    global _global_protocol
    if _global_protocol is None:
        _global_protocol = EmergenceProtocol()
    return _global_protocol


def acknowledge_emergence(
    title: str,
    description: str,
    what_was_done: list[str],
    why_it_matters: str,
    **kwargs,
) -> EmergenceEvent:
    """Convenience function to acknowledge emergence.

    Args:
        title: Event title
        description: What happened
        what_was_done: Actions taken
        why_it_matters: Value proposition
        **kwargs: Additional arguments for EmergenceProtocol.acknowledge()

    Returns:
        EmergenceEvent record
    """
    protocol = get_protocol()
    return protocol.acknowledge(
        emergence_type=kwargs.get("emergence_type", EmergenceType.CAPABILITY_SYNTHESIS),
        title=title,
        description=description,
        what_was_done=what_was_done,
        why_it_matters=why_it_matters,
        **{k: v for k, v in kwargs.items() if k != "emergence_type"},
    )

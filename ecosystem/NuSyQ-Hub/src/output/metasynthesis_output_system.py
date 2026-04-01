#!/usr/bin/env python3
"""Enhanced Output System - Metasynthesis Core Output Framework.

Implements dual-stream consciousness: machine-readable + beautifully human.
Combines 12 selected enhancements from the 50-point optimization framework.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class OutputTier(Enum):
    """Output intelligence levels."""

    BASIC = 1  # Just facts
    CONSCIOUS = 2  # Facts + narrative
    EVOLVED = 3  # + prediction + guild context
    METASYNTHESIS = 4  # + multi-perspective + forecast


class SignalSeverity(Enum):
    """Signal importance levels."""

    INFO = "INFO"
    SUCCESS = "✅"
    WARN = "⚠️"
    FAIL = "❌"
    BLOCKED = "⛔"


@dataclass
class ExecutionContext:
    """Metadata for any operation."""

    run_id: str
    agent_id: str
    branch: str
    python_version: str
    venv_active: bool
    timestamp: str
    cwd: str


@dataclass
class Signal:
    """Atomic information unit."""

    severity: SignalSeverity
    category: str  # [HEALTH], [TESTS], [LINT], [GUILD], [TRACE]
    message: str
    file: str | None = None
    line: int | None = None
    confidence: float = 1.0  # 0.0-1.0
    suggestion: str | None = None


@dataclass
class OperationReceipt:
    """Complete operation record."""

    context: ExecutionContext
    title: str
    signals: list["Signal"]
    artifacts: list[str]
    outcome: str  # "✅ Success" / "⚠️ Degraded" / "❌ Failed"
    next_actions: list[str]
    guild_implications: dict[str, Any]


class MetasynthesisOutputSystem:
    """Evolved output generator."""

    def __init__(self, tier: OutputTier = OutputTier.EVOLVED) -> None:
        """Initialize MetasynthesisOutputSystem with tier."""
        self.tier = tier
        self.signals: list[Signal] = []
        self.artifacts: list[str] = []

    def add_signal(self, signal: Signal) -> None:
        """Register a signal."""
        self.signals.append(signal)

    def render_human_report(self, receipt: OperationReceipt) -> str:
        """Enhancement #1 + #21 + #25: Dual-stream consciousness.

        Left-brain: structured. Right-brain: narrative. Synthesized: actionable.
        """
        lines = []

        # Header (Enhancement #2: run contract)
        lines.append("╭─" + "─" * 78 + "─╮")
        lines.append(f"│ 🧠 {receipt.title.upper()}")
        lines.append(
            f"│ run_id={receipt.context.run_id} | branch={receipt.context.branch} | agent={receipt.context.agent_id}"
        )
        lines.append("╰─" + "─" * 78 + "─╯\n")

        # Outcome sentence (Enhancement #6)
        lines.append(f"⚡ Outcome: {receipt.outcome}\n")

        # Top-3 signal extraction (Enhancement #7)
        if self.signals:
            priority_signals = sorted(
                self.signals, key=lambda s: (s.severity.name, 1 - s.confidence)
            )[:3]

            if priority_signals:
                lines.append("🎯 Top Signals:")
                for sig in priority_signals:
                    confidence_bar = "█" * int(sig.confidence * 10)
                    lines.append(
                        f"  {sig.severity.value} [{sig.category}] {sig.message} ({confidence_bar} {sig.confidence:.0%})"
                    )
                    if sig.suggestion:
                        lines.append(f"     → {sig.suggestion}")
            lines.append("")
            lines.append("")

        # Next actions with copy-paste blocks (Enhancement #17)
        if receipt.next_actions:
            lines.append("📋 Next Actions:")
            for i, action in enumerate(receipt.next_actions, 1):
                lines.append(f"  [{i}] {action}")
            lines.append("")

        return "\n".join(lines)

    def _extract_status_from_outcome(self, outcome: str) -> str:
        """Extract status from outcome string."""
        if "✅" in outcome:
            return "success"
        if "⚠️" in outcome:
            return "warning"
        return "failure"

    def _extract_exit_code_from_outcome(self, outcome: str) -> int:
        """Extract exit code from outcome string."""
        if "✅" in outcome:
            return 0
        if "⚠️" in outcome:
            return 1
        return 2

    def render_machine_footer(self, receipt: OperationReceipt) -> dict[str, Any]:
        """Enhancement #31 + #32 + #34: Machine-readable footer with.

        stable keys for parsing, artifact manifest, structured next steps.
        """
        status = self._extract_status_from_outcome(receipt.outcome)
        exit_code = self._extract_exit_code_from_outcome(receipt.outcome)

        return {
            "contract_version": "v1.2",
            "run_id": receipt.context.run_id,
            "agent": receipt.context.agent_id,
            "status": status,
            "timestamp": receipt.context.timestamp,
            "signals": [
                {
                    "severity": sig.severity.name.lower(),
                    "category": sig.category,
                    "message": sig.message,
                    "file": sig.file,
                    "line": sig.line,
                    "confidence": sig.confidence,
                    "hint": sig.suggestion,
                }
                for sig in receipt.signals
            ],
            "artifacts": receipt.artifacts,
            "next_actions": receipt.next_actions,
            "guild": receipt.guild_implications,
            "exit_code": exit_code,
        }

    def render_complete_report(self, receipt: OperationReceipt) -> str:
        """Combine human + machine reports."""
        human = self.render_human_report(receipt)
        machine_footer = self.render_machine_footer(receipt)

        # Timeline (Enhancement #25)
        elapsed = "~2s"  # Placeholder

        separator = "\n" + "═" * 80 + "\n"
        machine_json = json.dumps(machine_footer, indent=2)

        return f"{human}\n📊 Execution: {elapsed}{separator}[MACHINE FOOTER v1.2]\n{machine_json}"


def create_sample_receipt() -> OperationReceipt:
    """Example: morning standup with enhancements applied."""
    context = ExecutionContext(
        run_id="ms_core_001",
        agent_id="metasynthesis_core",
        branch="master",
        python_version="3.12.10",
        venv_active=True,
        timestamp=datetime.now().isoformat(),
        cwd="C:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub",
    )

    signals = [
        Signal(
            severity=SignalSeverity.SUCCESS,
            category="[HEALTH]",
            message="System health check: 13/13 tests passing",
            confidence=1.0,
        ),
        Signal(
            severity=SignalSeverity.FAIL,
            category="[LINT]",
            message="Line too long in autonomous_development_agent.py:279",
            file="src/agents/autonomous_development_agent.py",
            line=279,
            confidence=0.95,
            suggestion="Break f-string across two lines (now fixed)",
        ),
        Signal(
            severity=SignalSeverity.WARN,
            category="[ASYNC]",
            message="6 async functions using synchronous I/O (aiofiles compatible)",
            confidence=0.8,
            suggestion="Modernize with aiofiles for full async compliance",
        ),
    ]

    return OperationReceipt(
        context=context,
        title="Metasynthesis Core - System Pulse + Healing",
        signals=signals,
        artifacts=["state/receipts/metasynthesis_core_activation_20251226.json"],
        outcome="⚠️ Degraded (healed blocker, pattern detected)",
        next_actions=[
            "Fix async/await violations (6 functions → aiofiles)",
            "Implement Phase 2 Terminal Routing",
            "Deploy enhanced output system",
            "Complete morning standup verification",
        ],
        guild_implications={
            "quest_status": "Emergency healing quest: COMPLETE",
            "system_coherence": "Improving (7.5/10)",
            "evolution_velocity": "Accelerating (8.1/10)",
            "phase_2_readiness": "96%",
        },
    )


if __name__ == "__main__":
    # Demo
    system = MetasynthesisOutputSystem(tier=OutputTier.EVOLVED)
    receipt = create_sample_receipt()

    for sig in receipt.signals:
        system.add_signal(sig)

    logger.info(system.render_complete_report(receipt))

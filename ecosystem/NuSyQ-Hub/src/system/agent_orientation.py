#!/usr/bin/env python3
"""ΞNuSyQ Agent Orientation System.

================================
Ensures every agent (Claude, Copilot, Codex, ChatDev) receives the canonical
system brief before performing any action.

This module is invoked automatically by:
- src/main.py (CLI entry)
- .vscode/settings.json (Copilot/Codex context)
- Pre-commit hooks
- Agent orchestrators

Usage:
    from src.system.agent_orientation import orient_agent
    orient_agent()  # Prints system brief to stdout/logs
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_BRIEF_PATH = REPO_ROOT / "docs" / "ΞNuSyQ_SYSTEM_BRIEF.md"


def get_system_brief() -> str:
    """Load the canonical system brief."""
    if SYSTEM_BRIEF_PATH.exists():
        return SYSTEM_BRIEF_PATH.read_text(encoding="utf-8")
    else:
        return """
⚠️  CRITICAL: System brief not found at {SYSTEM_BRIEF_PATH}
ΞNuSyQ agents must read docs/ΞNuSyQ_SYSTEM_BRIEF.md before acting.
""".strip()


def orient_agent(silent: bool = False, return_only: bool = False) -> str | None:
    """Display the ΞNuSyQ system brief to the current agent.

    Args:
        silent: If True, don't print to stdout (useful for testing)
        return_only: If True, return the brief as a string instead of printing

    Returns:
        The system brief text if return_only=True, else None
    """
    brief = get_system_brief()

    header = """
╔════════════════════════════════════════════════════════════════════════╗
║                    ΞNuSyQ AGENT ORIENTATION                            ║
║                                                                        ║
║  You are working within the ΞNuSyQ Tripartite System.                 ║
║  Read the following brief BEFORE taking any action.                   ║
║                                                                        ║
║  Ground Truth: Use this as your canonical understanding of:           ║
║    - What ΞNuSyQ is (production AI-assisted software ecosystem)       ║
║    - Your role within it (action-oriented stewardship)                ║
║    - Expected behaviors (incremental, tool-using, non-destructive)    ║
║    - System topology (NuSyQ-Hub, NuSyQ, SimulatedVerse)               ║
╚════════════════════════════════════════════════════════════════════════╝
""".strip()

    footer = """
╔════════════════════════════════════════════════════════════════════════╗
║                    END ORIENTATION                                     ║
║                                                                        ║
║  Remember:                                                             ║
║    ✓ Optimize for ACTION, not explanation                             ║
║    ✓ Use existing tools/utilities FIRST                               ║
║    ✓ Preserve architecture (incremental change > replacement)         ║
║    ✓ Produce tangible artifacts (code, configs, diffs)                ║
║    ✓ Avoid exploratory wandering                                      ║
║                                                                        ║
║  Proceed with your task, grounded in this context.                    ║
╚════════════════════════════════════════════════════════════════════════╝
""".strip()

    full_text = f"{header}\n\n{brief}\n\n{footer}"

    if return_only:
        return full_text

    if not silent:
        logger.info(full_text, file=sys.stdout)

    return None


def inject_copilot_context() -> dict[str, list[dict[str, str]]]:
    """Generate context injection for .vscode/settings.json.

    Returns a dict suitable for github.copilot.chat.codeGeneration.instructions.
    """
    brief = get_system_brief()
    return {
        "github.copilot.chat.codeGeneration.instructions": [
            {"text": f"MANDATORY CONTEXT: You are working in ΞNuSyQ. {brief[:500]}..."}
        ]
    }


if __name__ == "__main__":
    # CLI usage: python -m src.system.agent_orientation
    orient_agent(silent=False)

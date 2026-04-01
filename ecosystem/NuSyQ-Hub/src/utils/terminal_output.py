#!/usr/bin/env python3
"""Terminal Output Router - WIRED INTEGRATION.

Routes output to agent-specific and operational terminals in real-time.
"""

import json
import logging
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TerminalType(Enum):
    """Terminal categories."""

    CLAUDE = "claude"
    COPILOT = "copilot"
    CODEX = "codex"
    CHATDEV = "chatdev"
    AI_COUNCIL = "ai_council"
    INTERMEDIARY = "intermediary"
    ERRORS = "errors"
    SUGGESTIONS = "suggestions"
    TASKS = "tasks"
    TESTS = "tests"
    ZETA = "zeta"
    METRICS = "metrics"
    ANOMALIES = "anomalies"
    FUTURE = "future"
    MAIN = "main"


class TerminalRouter:
    """Routes output to the correct terminal based on content and agent."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).parent.parent.parent
        self.routing_config = self._load_routing_config()
        self.ecosystem_defaults = self._load_defaults(
            self.root / "config" / "ecosystem_defaults.json"
        )
        self.orchestration_defaults = self._load_defaults(
            self.root / "config" / "orchestration_defaults.json"
        )

        terminal_defaults = self.ecosystem_defaults.get("terminal_orchestration", {})
        terminal_arch = self.ecosystem_defaults.get("terminal_architecture", {})
        routing_defaults = self.orchestration_defaults.get("terminal_routing", {})

        self.auto_tag_agent_ids = bool(terminal_defaults.get("auto_tag_agent_ids", False))
        self.agent_id_format = str(routing_defaults.get("agent_id_format", "[{agent_id}]"))
        self.audit_log_enabled = bool(terminal_arch.get("per_message_audit_log", False))
        audit_path = routing_defaults.get("audit_log_path", "state/terminals/audit.jsonl")
        audit_path = Path(audit_path)
        self.audit_log_path = audit_path if audit_path.is_absolute() else (self.root / audit_path)

    def _load_defaults(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _load_routing_config(self) -> dict[str, Any]:
        """Load routing configuration."""
        config_path = self.root / "data" / "terminal_routing.json"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {"routing_keywords": {}, "terminals": {}}
        return {"routing_keywords": {}, "terminals": {}}

    def route(self, message: str, agent: TerminalType | None = None, level: str = "INFO") -> str:
        """Route a message to the appropriate terminal.

        Args:
            message: The message to output
            agent: Specific agent terminal (CLAUDE, COPILOT, etc.)
            level: Log level (INFO, ERROR, WARNING, etc.)

        Returns:
            The terminal ID where the message was routed
        """
        # Determine target terminal
        if agent:
            terminal_id = agent.value
        elif level == "ERROR":
            terminal_id = "errors"
        else:
            terminal_id = self._route_by_content(message)

        # Get terminal info
        terminal_info = self.routing_config.get("terminals", {}).get(terminal_id, {})
        terminal_name = terminal_info.get("name", terminal_id)

        # Format and output message
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        tagged_message = message
        if agent and self.auto_tag_agent_ids:
            tag = self.agent_id_format.format(agent_id=agent.value)
            if not message.startswith(tag):
                tagged_message = f"{tag} {message}"
        formatted = f"[{timestamp}] [{terminal_name}] {tagged_message}"

        # Log to logger and also print to stdout
        logger.info(formatted)
        print(formatted, file=sys.stdout, flush=True)

        # Also log to file for persistence (NDJSON for colorized watcher display)
        self._log_to_file(terminal_id, tagged_message, level=level, agent=agent)
        self._audit_log(terminal_id, agent, level, message, tagged_message)

        return terminal_id

    def _route_by_content(self, content: str) -> str:
        """Route based on content keywords."""
        content_lower = content.lower()
        keywords = self.routing_config.get("routing_keywords", {})
        if not isinstance(keywords, dict):
            return "main"

        for keyword, terminal_id in keywords.items():
            if isinstance(keyword, str) and keyword in content_lower:
                if isinstance(terminal_id, str):
                    return terminal_id
                return str(terminal_id)

        return "main"

    def _log_to_file(
        self,
        terminal_id: str,
        message: str,
        level: str = "INFO",
        agent: "TerminalType | None" = None,
    ) -> None:
        """Persist output to terminal-specific log file as NDJSON.

        Writing as NDJSON means the PowerShell watcher scripts (watch_*_terminal.ps1)
        will parse and colorize by level instead of displaying raw text.
        """
        import json as _json

        log_dir = self.root / "data" / "terminal_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{terminal_id}.log"
        record = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "level": level.upper(),
            "source": agent.value if agent else terminal_id,
            "message": message,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(_json.dumps(record) + "\n")

    def _audit_log(
        self,
        terminal_id: str,
        agent: TerminalType | None,
        level: str,
        raw_message: str,
        formatted_message: str,
    ) -> None:
        if not self.audit_log_enabled:
            return
        payload = {
            "timestamp": datetime.now().isoformat(),
            "terminal_id": terminal_id,
            "agent": agent.value if agent else None,
            "level": level,
            "raw_message": raw_message,
            "formatted_message": formatted_message,
        }
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def claude(self, message: str) -> None:
        """Output to Claude terminal."""
        self.route(message, agent=TerminalType.CLAUDE)

    def copilot(self, message: str) -> None:
        """Output to Copilot terminal."""
        self.route(message, agent=TerminalType.COPILOT)

    def codex(self, message: str) -> None:
        """Output to Codex terminal."""
        self.route(message, agent=TerminalType.CODEX)

    def chatdev(self, message: str) -> None:
        """Output to ChatDev terminal."""
        self.route(message, agent=TerminalType.CHATDEV)

    def council(self, message: str) -> None:
        """Output to AI Council terminal."""
        self.route(message, agent=TerminalType.AI_COUNCIL)

    def intermediary(self, message: str) -> None:
        """Output to Intermediary terminal."""
        self.route(message, agent=TerminalType.INTERMEDIARY)

    def error(self, message: str) -> None:
        """Output to Errors terminal."""
        self.route(message, agent=TerminalType.ERRORS, level="ERROR")

    def suggest(self, message: str) -> None:
        """Output to Suggestions terminal."""
        self.route(message, agent=TerminalType.SUGGESTIONS)

    def task(self, message: str) -> None:
        """Output to Tasks terminal."""
        self.route(message, agent=TerminalType.TASKS)

    def test(self, message: str) -> None:
        """Output to Tests terminal."""
        self.route(message, agent=TerminalType.TESTS)

    def zeta(self, message: str) -> None:
        """Output to Zeta terminal."""
        self.route(message, agent=TerminalType.ZETA)

    def metric(self, message: str) -> None:
        """Output to Metrics terminal."""
        self.route(message, agent=TerminalType.METRICS)

    def anomaly(self, message: str) -> None:
        """Output to Anomalies terminal."""
        self.route(message, agent=TerminalType.ANOMALIES)

    def future(self, message: str) -> None:
        """Output to Future terminal."""
        self.route(message, agent=TerminalType.FUTURE)


# Global router instance
_router = None


def get_router() -> TerminalRouter:
    """Get or create the global terminal router."""
    global _router
    if _router is None:
        _router = TerminalRouter()
    return _router


# Convenience functions
def to_claude(message: str) -> None:
    """Send message to Claude terminal."""
    get_router().claude(message)


def to_copilot(message: str) -> None:
    """Send message to Copilot terminal."""
    get_router().copilot(message)


def to_codex(message: str) -> None:
    """Send message to Codex terminal."""
    get_router().codex(message)


def to_chatdev(message: str) -> None:
    """Send message to ChatDev terminal."""
    get_router().chatdev(message)


def to_council(message: str) -> None:
    """Send message to AI Council terminal."""
    get_router().council(message)


def to_intermediary(message: str) -> None:
    """Send message to Intermediary terminal."""
    get_router().intermediary(message)


def to_errors(message: str) -> None:
    """Send message to Errors terminal."""
    get_router().error(message)


def to_suggestions(message: str) -> None:
    """Send message to Suggestions terminal."""
    get_router().suggest(message)


def to_tasks(message: str) -> None:
    """Send message to Tasks terminal."""
    get_router().task(message)


def to_tests(message: str) -> None:
    """Send message to Tests terminal."""
    get_router().test(message)


def to_zeta(message: str) -> None:
    """Send message to Zeta terminal."""
    get_router().zeta(message)


def to_metrics(message: str) -> None:
    """Send message to Metrics terminal."""
    get_router().metric(message)


def to_anomalies(message: str) -> None:
    """Send message to Anomalies terminal."""
    get_router().anomaly(message)


def to_future(message: str) -> None:
    """Send message to Future terminal."""
    get_router().future(message)


# Example usage
if __name__ == "__main__":
    router = get_router()

    logger.info("=" * 70)
    logger.info("TERMINAL OUTPUT ROUTER - DEMONSTRATION")
    logger.info("=" * 70)

    # Agent terminals
    to_claude("Claude Code analyzing codebase structure...")
    to_copilot("Copilot suggesting code completion for function signature...")
    to_codex("Codex transforming legacy code to modern patterns...")
    to_chatdev("ChatDev CEO: Let's build a task management system!")
    to_council("AI Council voting on architectural decision: 3 for, 1 against, 1 abstain")
    to_intermediary("Routing message from Claude to Copilot...")

    # Operational terminals
    to_errors("ERROR: Failed to connect to database")
    to_suggestions("SUGGESTION: Consider adding type hints to improve code quality")
    to_tasks("Processing PU #42: Analyze quantum entanglement patterns")
    to_zeta("Zeta autonomous cycle #15 complete - 23 PUs processed")
    to_metrics("System health: CPU 23%, Memory 1.2GB, Uptime 4h 23m")
    to_anomalies("ANOMALY: Orphaned Python process detected (PID 12345)")
    to_future("ROADMAP: Add support for multi-modal reasoning in Q2 2026")

    logger.info("\n✅ Demonstration complete!")
    logger.info(f"📁 Logs saved to: {router.root / 'data' / 'terminal_logs'}")
    logger.info("\n" + "=" * 70)

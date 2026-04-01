"""Enhanced Terminal Ecosystem.

Provides structured terminal channels, dashboards, and interactive controls
across the NuSyQ multi-repo workspace so we can route data into the curated
the curated VS Code terminals and diagnose failures without bouncing
between tabs.
VS Code terminals and diagnose failures without bouncing between tabs.

Features:
 - TerminalManager for lightweight, append-only JSON channels (Errors, Tasks, etc.)
 - Rich-powered interactive terminal dashboard, command palette, and evolution tracking
 - Dependency-aware dashboards that reuse existing log directories and ring buffers
 - CLI helpers for emitting channel messages from scripts or the shell

OmniTag: terminal_ecosystem|interactive_terminals|integration_bridge
MegaTag: quantum_terminal_hub|consciousness_terminals|adaptive_interfaces
"""

from __future__ import annotations

import contextlib
import json
import logging
import re
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_ROOT = REPO_ROOT / "data" / "terminal_logs"
LOG_ROOT.mkdir(parents=True, exist_ok=True)


def _normalize_channel_name(name: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", name)
    if not tokens:
        return "terminal"
    return "_".join(token.lower() for token in tokens)


# module logger
_module_logger = logging.getLogger(__name__)

DEFAULT_CHANNELS = [
    "NuSyQ: Activate Ecosystem",
    "PowerShell Extension",
    "pwsh",
    "Claude",
    "Copilot",
    "Codex",
    "ChatDev",
    "AI Council",
    "Intermediary",
    "Errors",
    "Suggestions",
    "Tasks",
    "Tests",
    "Zeta",
    "Agents",
    "Metrics",
    "Anomalies",
    "Main",
    "Future",
]


@dataclass
class TerminalChannel:
    name: str
    buffer_size: int = 500
    _buffer: deque[dict] = field(init=False)
    log_path: Path = field(init=False)
    lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def __post_init__(self):
        """Implement __post_init__."""
        self._buffer = deque(maxlen=self.buffer_size)
        safe_name = _normalize_channel_name(self.name)
        self.log_path = LOG_ROOT / f"{safe_name}.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.touch(exist_ok=True)

    def append(self, entry: dict) -> None:
        with self.lock:
            self._buffer.append(entry)
            try:
                # Append entry as NDJSON
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                # Simple size-based rotation: when file grows beyond ROTATE_BYTES,
                # rename it with a timestamp suffix and keep up to RETAIN_FILES backups.
                try:
                    ROTATE_BYTES = 5 * 1024 * 1024  # 5MB
                    RETAIN_FILES = 5
                    if self.log_path.exists() and self.log_path.stat().st_size > ROTATE_BYTES:
                        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                        rotated = self.log_path.with_name(self.log_path.name + "." + ts)
                        try:
                            self.log_path.rename(rotated)
                        except Exception:
                            # if rename fails, try moving/copy fallback
                            try:
                                with open(self.log_path, "rb") as src, open(rotated, "wb") as dst:
                                    dst.write(src.read())
                                # truncate original
                                open(self.log_path, "w", encoding="utf-8").close()
                            except Exception:
                                logger.debug("Suppressed Exception", exc_info=True)
                        # touch/ensure new log file exists
                        with contextlib.suppress(Exception):
                            self.log_path.touch(exist_ok=True)
                        # cleanup old rotated files:
                        # sort by modification time, keep newest RETAIN_FILES
                        try:
                            rotated_files = [
                                p
                                for p in self.log_path.parent.glob(self.log_path.name + ".*")
                                if p.is_file()
                            ]
                            rotated_files.sort(key=lambda p: p.stat().st_mtime)
                            if len(rotated_files) > RETAIN_FILES:
                                for old in rotated_files[:-RETAIN_FILES]:
                                    with contextlib.suppress(Exception):
                                        old.unlink()
                        except Exception:
                            logger.debug("Suppressed Exception", exc_info=True)
                except Exception as _rot_exc:
                    # non-fatal rotation failure — use stderr to avoid re-entrancy
                    import sys as _sys

                    _sys.stderr.write(
                        f"[terminal_log] Rotation failed for {self.log_path}: {_rot_exc}\n"
                    )
            except Exception as _write_exc:
                # Use stderr to avoid recursion if a logging handler calls append()
                import sys as _sys

                _sys.stderr.write(
                    f"[terminal_log] Failed to write log for {self.name}: {_write_exc}\n"
                )

    def recent(self, n: int = 100) -> list[dict]:
        with self.lock:
            return list(self._buffer)[-n:]


class TerminalManager:
    """Singleton manager for machine-readable terminal channels."""

    _instance: TerminalManager | None = None

    def __init__(self, channels: list[str] | None = None):
        """Initialize TerminalManager with channels."""
        if TerminalManager._instance:
            raise RuntimeError("Use get_instance() to obtain TerminalManager")
        self.channels: dict[str, TerminalChannel] = {}
        self._register_defaults(channels or DEFAULT_CHANNELS)
        TerminalManager._instance = self

    @classmethod
    def get_instance(cls) -> TerminalManager:
        if cls._instance is None:
            cls._instance = TerminalManager()
        return cls._instance

    def _register_defaults(self, channels: list[str]) -> None:
        for ch in channels:
            self.register_channel(ch)

    def register_channel(self, name: str, buffer_size: int = 500) -> TerminalChannel:
        if name in self.channels:
            return self.channels[name]
        tc = TerminalChannel(name=name, buffer_size=buffer_size)
        self.channels[name] = tc
        return tc

    def send(self, channel: str, level: str, message: str, meta: dict | None = None) -> dict:
        ts = datetime.utcnow().isoformat() + "Z"
        entry = {
            "ts": ts,
            "channel": channel,
            "level": level,
            "message": message,
            "meta": meta or {},
        }
        if channel not in self.channels:
            self.register_channel(channel)
        self.channels[channel].append(entry)
        return entry

    def list_channels(self) -> list[str]:
        return list(self.channels.keys())

    def recent(self, channel: str, n: int = 100) -> list[dict]:
        if channel not in self.channels:
            return []
        return self.channels[channel].recent(n)


def terminal_cli(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        logger.info("Usage: send <channel> <level> <message> [meta-json]")
        return 2
    cmd = argv[0]
    tm = TerminalManager.get_instance()

    if cmd == "send":
        if len(argv) < 4:
            logger.info("Usage: send <channel> <level> <message> [meta-json]")
            return 2
        channel, level, message = argv[1], argv[2], argv[3]
        meta: dict[str, Any] = {}
        if len(argv) >= 5:
            try:
                meta = json.loads(argv[4])
            except Exception:
                logger.error("Warning: failed to parse meta-json; sending as empty meta")
        tm.send(channel, level, message, meta=meta)
        logger.info(f"Sent to {channel}: {level} {message}")
        return 0
    if cmd == "list":
        for c in tm.list_channels():
            logger.info(c)
        return 0
    if cmd == "recent":
        if len(argv) < 2:
            logger.info("Usage: recent <channel> [n]")
            return 2
        channel = argv[1]
        n = int(argv[2]) if len(argv) >= 3 and argv[2].isdigit() else 20
        for e in tm.recent(channel, n=n):
            logger.info(json.dumps(e, ensure_ascii=False))
        return 0
    logger.info("Unknown command. Supported: send, list, recent")
    return 2


class TerminalType(Enum):
    CLAUDE = "🤖 Claude"
    COPILOT = "🧩 Copilot"
    CODEX = "🧠 Codex"
    CHATDEV = "🏗️ ChatDev"
    AI_COUNCIL = "🏛️ AI Council"
    INTERMEDIARY = "🔗 Intermediary"
    ERRORS = "🔥 Errors"
    SUGGESTIONS = "💡 Suggestions"
    TASKS = "✅ Tasks"
    TESTS = "🧪 Tests"
    ZETA = "🎯 Zeta"
    AGENTS = "🤖 Agents"
    METRICS = "📊 Metrics"
    ANOMALIES = "⚡ Anomalies"
    FUTURE = "🔮 Future"
    MAIN = "🏠 Main"


@dataclass
class TerminalConfig:
    name: str
    icon: str
    description: str
    log_file: Path
    commands: list[str] = field(default_factory=list)
    auto_refresh: bool = True
    refresh_interval: int = 5
    max_lines: int = 1000
    filters: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    interactive: bool = True
    evolution_stage: int = 1


@dataclass
class TerminalSession:
    terminal_type: TerminalType
    config: TerminalConfig
    console: Console
    live_display: Live | None = None
    last_refresh: datetime = field(default_factory=datetime.now)
    command_history: list[str] = field(default_factory=list)
    active_filters: list[str] = field(default_factory=list)
    evolution_data: dict[str, Any] = field(default_factory=dict)


class EnhancedTerminalEcosystem:
    def __init__(self, workspace_root: Path):
        """Initialize EnhancedTerminalEcosystem with workspace_root."""
        self.workspace_root = workspace_root
        self.terminals: dict[TerminalType, TerminalSession] = {}
        self.console = Console()
        self.running = False
        self.evolution_engine = TerminalEvolutionEngine(self)
        self.terminal_configs: dict[TerminalType, TerminalConfig] = {}
        self._initialize_terminal_configs()
        self._setup_evolution_tracking()

    def _initialize_terminal_configs(self) -> None:
        base_logs = self.workspace_root / "data" / "terminal_logs"
        base_logs.mkdir(parents=True, exist_ok=True)
        # configure each terminal
        self.terminal_configs = {
            TerminalType.CLAUDE: TerminalConfig(
                name="Claude AI Assistant",
                icon="🤖",
                description="Claude Code AI assistant with consciousness integration",
                log_file=base_logs / "claude.log",
                commands=["analyze", "generate", "review", "debug", "evolve"],
                integrations=["consciousness_bridge", "quantum_solver", "code_generator"],
                evolution_stage=3,
            ),
            TerminalType.COPILOT: TerminalConfig(
                name="GitHub Copilot",
                icon="🧩",
                description="AI-powered code completion and assistance",
                log_file=base_logs / "copilot.log",
                commands=["complete", "suggest", "refactor", "optimize", "explain"],
                integrations=["vscode_api", "git_integration", "code_analysis"],
                evolution_stage=2,
            ),
            TerminalType.CODEX: TerminalConfig(
                name="Codex AI",
                icon="🧠",
                description="Advanced code intelligence and reasoning",
                log_file=base_logs / "codex.log",
                commands=["reason", "analyze", "optimize", "predict", "evolve"],
                integrations=["quantum_bridge", "pattern_recognition", "predictive_modeling"],
                evolution_stage=4,
            ),
            TerminalType.CHATDEV: TerminalConfig(
                name="ChatDev Multi-Agent",
                icon="🏗️",
                description="Multi-agent software development company",
                log_file=base_logs / "chatdev.log",
                commands=["develop", "test", "review", "deploy", "coordinate"],
                integrations=["agent_orchestrator", "code_generation", "testing_framework"],
                evolution_stage=3,
            ),
            TerminalType.AI_COUNCIL: TerminalConfig(
                name="AI Council",
                icon="🏛️",
                description="Collective AI decision-making and governance",
                log_file=base_logs / "ai_council.log",
                commands=["debate", "decide", "govern", "mediate", "evolve"],
                integrations=["consensus_engine", "ethical_framework", "decision_tree"],
                evolution_stage=2,
            ),
            TerminalType.INTERMEDIARY: TerminalConfig(
                name="System Intermediary",
                icon="🔗",
                description="Cross-system communication and integration",
                log_file=base_logs / "intermediary.log",
                commands=["bridge", "translate", "coordinate", "mediate", "sync"],
                integrations=["protocol_translator", "system_bridge", "data_sync"],
                evolution_stage=3,
            ),
            TerminalType.ERRORS: TerminalConfig(
                name="Error Management",
                icon="🔥",
                description="Intelligent error detection, analysis, and resolution",
                log_file=base_logs / "errors.log",
                commands=["analyze", "categorize", "prioritize", "resolve", "prevent"],
                filters=["ERROR", "CRITICAL", "WARNING"],
                integrations=["error_classifier", "auto_healer", "prevention_engine"],
                evolution_stage=4,
            ),
            TerminalType.SUGGESTIONS: TerminalConfig(
                name="AI Suggestions",
                icon="💡",
                description="Intelligent suggestions and recommendations",
                log_file=base_logs / "suggestions.log",
                commands=["suggest", "recommend", "optimize", "improve", "innovate"],
                integrations=["pattern_analyzer", "improvement_engine", "innovation_lab"],
                evolution_stage=3,
            ),
            TerminalType.TASKS: TerminalConfig(
                name="Task Management",
                icon="✅",
                description="Intelligent task tracking and orchestration",
                log_file=base_logs / "tasks.log",
                commands=["create", "assign", "track", "complete", "prioritize"],
                integrations=["quest_system", "priority_engine", "completion_tracker"],
                evolution_stage=4,
            ),
            TerminalType.TESTS: TerminalConfig(
                name="Testing Framework",
                icon="🧪",
                description="Comprehensive testing and validation",
                log_file=base_logs / "tests.log",
                commands=["run", "analyze", "validate", "benchmark", "report"],
                integrations=["test_orchestrator", "coverage_analyzer", "performance_monitor"],
                evolution_stage=3,
            ),
            TerminalType.ZETA: TerminalConfig(
                name="Zeta Quest System",
                icon="🎯",
                description="Advanced quest and milestone tracking",
                log_file=base_logs / "zeta.log",
                commands=["track", "advance", "complete", "analyze", "optimize"],
                integrations=["quest_engine", "progress_tracker", "achievement_system"],
                evolution_stage=5,
            ),
            TerminalType.AGENTS: TerminalConfig(
                name="Agent Orchestrator",
                icon="🤖",
                description="Multi-agent coordination and management",
                log_file=base_logs / "agents.log",
                commands=["deploy", "coordinate", "monitor", "scale", "evolve"],
                integrations=["agent_registry", "coordination_engine", "scaling_manager"],
                evolution_stage=4,
            ),
            TerminalType.METRICS: TerminalConfig(
                name="System Metrics",
                icon="📊",
                description="Real-time system monitoring and analytics",
                log_file=base_logs / "metrics.log",
                commands=["monitor", "analyze", "alert", "report", "optimize"],
                integrations=["metrics_collector", "analytics_engine", "alert_system"],
                evolution_stage=3,
            ),
            TerminalType.ANOMALIES: TerminalConfig(
                name="Anomaly Detection",
                icon="⚡",
                description="Advanced anomaly detection and analysis",
                log_file=base_logs / "anomalies.log",
                commands=["detect", "analyze", "classify", "respond", "learn"],
                integrations=["anomaly_detector", "pattern_analyzer", "response_engine"],
                evolution_stage=2,
            ),
            TerminalType.FUTURE: TerminalConfig(
                name="Future Planning",
                icon="🔮",
                description="Predictive planning and future state analysis",
                log_file=base_logs / "future.log",
                commands=["predict", "plan", "simulate", "forecast", "prepare"],
                integrations=["prediction_engine", "simulation_lab", "planning_system"],
                evolution_stage=1,
            ),
            TerminalType.MAIN: TerminalConfig(
                name="Main Control",
                icon="🏠",
                description="Central command and control interface",
                log_file=base_logs / "main.log",
                commands=["control", "coordinate", "monitor", "command", "evolve"],
                integrations=["central_orchestrator", "system_controller", "master_mind"],
                evolution_stage=5,
            ),
        }

    def _setup_evolution_tracking(self) -> None:
        evolution_file = self.workspace_root / "data" / "terminal_evolution.json"
        if evolution_file.exists():
            with open(evolution_file, encoding="utf-8") as f:
                self.evolution_data = json.load(f)
        else:
            self.evolution_data = {
                "last_updated": datetime.now().isoformat(),
                "terminals": {},
                "global_evolution_stage": 1,
                "capabilities_unlocked": [],
                "evolution_goals": [],
            }

    def start_terminal(self, terminal_type: TerminalType) -> bool:
        if terminal_type in self.terminals:
            self.console.print(
                f"[yellow]⚠️  {terminal_type.value} terminal already running[/yellow]"
            )
            return False
        config = self.terminal_configs[terminal_type]
        session = TerminalSession(terminal_type=terminal_type, config=config, console=self.console)
        self.terminals[terminal_type] = session
        thread = threading.Thread(target=self._run_terminal_session, args=(session,), daemon=True)
        thread.start()
        self.console.print(f"[green]✅ Started {terminal_type.value} terminal[/green]")
        return True

    def _run_terminal_session(self, session: TerminalSession) -> None:
        try:
            with Live(console=session.console, refresh_per_second=4) as live:
                session.live_display = live
                self._render_terminal_interface(session)
                while self.running:
                    if (
                        session.config.auto_refresh
                        and (datetime.now() - session.last_refresh).seconds
                        >= session.config.refresh_interval
                    ):
                        self._refresh_terminal_data(session)
                    self._process_terminal_updates(session)
                    time.sleep(0.1)
        except Exception as exc:
            _module_logger.error(
                "Terminal session error for %s: %s", session.terminal_type.value, exc
            )

    def _render_terminal_interface(self, session: TerminalSession) -> None:
        layout = Layout()
        header = Panel.fit(
            f"{session.config.icon} {session.config.name}\n{session.config.description}",
            title=f"[bold blue]{session.terminal_type.value}[/bold blue]",
            border_style="blue",
        )
        content = self._generate_terminal_content(session)
        command_panel = Panel.fit(
            self._generate_command_interface(session),
            title="[bold green]Commands[/bold green]",
            border_style="green",
        )
        status = self._generate_status_bar(session)
        layout.split_column(
            Layout(header, size=5),
            Layout(content, minimum_size=10),
            Layout(command_panel, size=8),
            Layout(status, size=3),
        )
        if session.live_display:
            session.live_display.update(layout)

    def _generate_terminal_content(self, session: TerminalSession) -> Panel:
        log_content = self._get_recent_log_content(session.config)
        if session.active_filters:
            log_content = self._apply_filters(log_content, session.active_filters)
        content_lines = [
            self._format_log_entry(entry, session.terminal_type)
            for entry in log_content[-session.config.max_lines :]
        ]
        content = "\n".join(content_lines) if content_lines else "[dim]No recent activity[/dim]"
        return Panel.fit(
            content, title="[bold cyan]Activity Feed[/bold cyan]", border_style="cyan", height=20
        )

    def _generate_command_interface(self, session: TerminalSession) -> str:
        commands = session.config.commands
        command_list = []
        for cmd in commands:
            evolution_indicator = ""
            if session.config.evolution_stage >= 3:
                evolution_indicator = " [dim](evolved)[/dim]"
            command_list.append(f"• [bold cyan]{cmd}[/bold cyan]{evolution_indicator}")
        return "\n".join(command_list) + "\n\n[dim]Type command or 'help' for assistance[/dim]"

    def _generate_status_bar(self, session: TerminalSession) -> Panel:
        now = datetime.now()
        uptime = now - session.last_refresh
        parts = [
            f"🕐 {now.strftime('%H:%M:%S')}",
            f"🔄 {uptime.seconds}s ago",
            f"📊 Stage {session.config.evolution_stage}",
            f"🎯 {len(session.active_filters)} filters",
        ]
        status_text = " | ".join(parts)
        return Panel.fit(status_text, border_style="yellow", style="yellow")

    def _get_recent_log_content(self, config: TerminalConfig) -> list[str]:
        if not config.log_file.exists():
            return []
        try:
            with open(config.log_file, encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as exc:
            _module_logger.error("Error reading log file %s: %s", config.log_file, exc)
            return []

    def _apply_filters(self, content: list[str], filters: list[str]) -> list[str]:
        if not filters:
            return content
        return [line for line in content if any(f.lower() in line.lower() for f in filters)]

    def _format_log_entry(self, entry: str, _terminal_type: TerminalType) -> str:
        if "[ERROR]" in entry or "ERROR" in entry:
            return f"[red]{entry}[/red]"
        if "[WARNING]" in entry or "WARNING" in entry:
            return f"[yellow]{entry}[/yellow]"
        if "[INFO]" in entry or "INFO" in entry:
            return f"[blue]{entry}[/blue]"
        return f"[white]{entry}[/white]"

    def _refresh_terminal_data(self, session: TerminalSession) -> None:
        session.last_refresh = datetime.now()
        if session.live_display:
            self._render_terminal_interface(session)

    def _process_terminal_updates(self, session: TerminalSession) -> None:
        try:
            tm = TerminalManager.get_instance()
            # derive the canonical channel name (strip emoji/prefix)
            channel_name = self._channel_name_for_terminal(session.terminal_type)
            if not channel_name:
                return
            recent = tm.recent(channel_name, n=200)
            if not recent:
                return

            # read existing lines to avoid duplicates
            existing = set()
            try:
                if session.config.log_file.exists():
                    with open(session.config.log_file, encoding="utf-8") as f:
                        existing = {line.strip() for line in f if line.strip()}
            except Exception as exc:
                _module_logger.debug(
                    "Could not read existing log file %s: %s", session.config.log_file, exc
                )

            to_append: list[str] = []
            for entry in recent:
                try:
                    line = json.dumps(entry, ensure_ascii=False)
                except Exception:
                    # fallback: stringify minimal fields
                    try:
                        line = json.dumps(
                            {"ts": entry.get("ts"), "message": str(entry.get("message", ""))},
                            ensure_ascii=False,
                        )
                    except Exception:
                        line = str(entry)
                if line not in existing:
                    to_append.append(line)

            if to_append:
                session.config.log_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with open(session.config.log_file, "a", encoding="utf-8") as f:
                        for line in to_append:
                            f.write(line + "\n")
                except Exception as exc:
                    _module_logger.exception(
                        "Failed to append to log file %s: %s", session.config.log_file, exc
                    )
                # refresh view
                if session.live_display:
                    with contextlib.suppress(Exception):
                        self._render_terminal_interface(session)
        except Exception as exc:
            _module_logger.exception(
                "Error processing terminal updates for %s: %s", session.terminal_type.value, exc
            )

    def _channel_name_for_terminal(self, terminal_type: TerminalType) -> str:
        """Resolve the human-friendly channel name used by TerminalManager.

        Attempts a few fallbacks: strips emoji/prefix from the Enum value, then
        tries title-cased enum name variants until a registered channel is found.
        """
        try:
            # strip leading non-word characters (emoji) and whitespace
            pretty = re.sub(r"^[^\w]*", "", terminal_type.value).strip()
        except Exception:
            pretty = terminal_type.name.replace("_", " ").title()

        tm = TerminalManager.get_instance()
        channels = tm.list_channels()
        if pretty in channels:
            return pretty

        alt = terminal_type.name.replace("_", " ").title()
        if alt in channels:
            return alt

        # final fallback: try plain enum name (capitalized)
        cap = terminal_type.name.capitalize()
        if cap in channels:
            return cap

        # last resort: return the stripped pretty name (may not exist in TM)
        return pretty

    def stop_terminal(self, terminal_type: TerminalType) -> bool:
        if terminal_type not in self.terminals:
            self.console.print(f"[yellow]⚠️  {terminal_type.value} terminal not running[/yellow]")
            return False
        session = self.terminals[terminal_type]
        if session.live_display:
            session.live_display.stop()
        del self.terminals[terminal_type]
        self.console.print(f"[red]🛑 Stopped {terminal_type.value} terminal[/red]")
        return True

    def start_all_terminals(self) -> None:
        self.running = True
        count = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Starting terminals...", total=len(TerminalType))
            for terminal_type in TerminalType:
                if self.start_terminal(terminal_type):
                    count += 1
                progress.advance(task)
        self.console.print(f"[green]✅ Started {count}/{len(TerminalType)} terminals[/green]")

    def stop_all_terminals(self) -> None:
        self.running = False
        count = 0
        for terminal_type in list(TerminalType):
            if self.stop_terminal(terminal_type):
                count += 1
        self.console.print(f"[red]🛑 Stopped {count} terminals[/red]")

    def show_terminal_dashboard(self) -> None:
        table = Table(title="🖥️ Terminal Ecosystem Dashboard")
        table.add_column("Terminal", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Evolution", style="yellow")
        table.add_column("Activity", style="blue")
        table.add_column("Commands", style="magenta")
        for terminal_type in TerminalType:
            config = self.terminal_configs[terminal_type]
            status = "🟢 Running" if terminal_type in self.terminals else "🔴 Stopped"
            evolution = f"Stage {config.evolution_stage}"
            activity = f"{len(self._get_recent_log_content(config))} entries"
            commands = ", ".join(config.commands[:3]) + ("..." if len(config.commands) > 3 else "")
            table.add_row(
                f"{config.icon} {terminal_type.value}", status, evolution, activity, commands
            )
        self.console.print(table)

    def get_terminal_command_suggestions(self, terminal_type: TerminalType) -> list[str]:
        if terminal_type not in self.terminal_configs:
            return []
        config = self.terminal_configs[terminal_type]
        suggestions = config.commands.copy()
        if config.evolution_stage >= 2:
            suggestions.extend(["evolve", "upgrade", "optimize"])
        if config.evolution_stage >= 3:
            suggestions.extend(["integrate", "coordinate", "analyze"])
        if config.evolution_stage >= 4:
            suggestions.extend(["predict", "automate", "self_heal"])
        if config.evolution_stage >= 5:
            suggestions.extend(["transcend", "master", "unify"])
        return list(dict.fromkeys(suggestions))


class TerminalEvolutionEngine:
    def __init__(self, ecosystem: EnhancedTerminalEcosystem):
        """Initialize TerminalEvolutionEngine with ecosystem."""
        self.ecosystem = ecosystem

    def _unlock_evolution_stage(self, terminal_type: TerminalType, stage: int) -> None:
        config = self.ecosystem.terminal_configs[terminal_type]
        if config.evolution_stage < stage:
            config.evolution_stage = stage
            self.ecosystem.console.print(
                f"[green]🎉 {terminal_type.value} evolved to Stage {stage}![/green]"
            )


CLI_COMMANDS = {"send", "list", "recent"}


def ecosystem_main(argv: list[str] | None = None) -> int:
    args = argv or []
    workspace_root = Path(__file__).resolve().parents[2]
    ecosystem = EnhancedTerminalEcosystem(workspace_root)
    if not args:
        ecosystem.show_terminal_dashboard()
        return 0
    command = args[0]
    terminal_name = args[1] if len(args) > 1 else None
    if command == "start":
        if terminal_name:
            try:
                terminal_type = TerminalType[terminal_name.upper().replace(" ", "_")]
                ecosystem.start_terminal(terminal_type)
            except KeyError:
                logger.info(f"Unknown terminal: {terminal_name}")
                logger.info("Available terminals:", [t.name for t in TerminalType])
        else:
            ecosystem.start_all_terminals()
    elif command == "stop":
        if terminal_name:
            try:
                terminal_type = TerminalType[terminal_name.upper().replace(" ", "_")]
                ecosystem.stop_terminal(terminal_type)
            except KeyError:
                logger.info(f"Unknown terminal: {terminal_name}")
        else:
            ecosystem.stop_all_terminals()
    elif command in {"dashboard", "status"}:
        ecosystem.show_terminal_dashboard()
    else:
        usage = "Usage: python -m src.system.enhanced_terminal_ecosystem [start|stop|dashboard|status] [terminal_name]"
        logger.info(usage)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if args and args[0] in CLI_COMMANDS:
        return terminal_cli(args)
    return ecosystem_main(args)


if __name__ == "__main__":
    sys.exit(main())

"""extract_commands.py.

Who/What/Where/When/Why/How:
- Who: Developers and automated agents (Copilot/ChatDev) using the repo.
- What: Extracts and summarizes shell/CLI commands found in repository files
    to help build runnable reproductions, documentation, and agent tasks.
- Where: Run from repository root. Output is intended for quick inspection
    and further processing by downstream agents.
- When: Use interactively during code review or as part of analysis pipelines.
- Why: Collects command snippets so agents can propose reproduction steps,
    CI tasks, or remediation guidance.
- How: This module parses files and emits JSON-like summaries which can feed
    into the `logs/` ingestion pipeline or the ChatDev workflows.

Quick start:
    python -m src.tools.extract_commands

Outputs & integration:
- Prints findings to stdout and integrates with `src.LOGGING` if available.
- Designed to be importable by higher-level orchestrators (see
    `src/orchestration/*`) for automated task generation.

Troubleshooting & tips:
- Ensure `requests` or other optional libs are installed when calling
    components that use them; fallback logging is available for lightweight runs.
- Run inside a virtualenv matching the project's `requirements.txt` for
    deterministic behavior.

Dev notes / next steps:
- Consider emitting a `logs/commands_summary_<timestamp>.json` for consumption
    by `log_indexer` and agent ingestion flows.
"""

import json
import os
import re
import subprocess
import sys
import time
# existing imports...
from pathlib import Path
from typing import Any

# Add project src directory to path for robust absolute imports
project_root = Path(__file__).resolve().parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Load configuration for Ollama host

# Modular logging system (tag-aware, subprocess-aware)
try:
    from src.LOGGING.infrastructure.modular_logging_system import (
        log_info, log_subprocess_event, log_tagged_event)

    LOGGING_AVAILABLE = True
except ImportError:
    # Fallback logging if main system unavailable
    def log_info(_tag, _message) -> None:
        pass

    def log_warning(_tag, _message) -> None:
        pass

    def log_error(_tag, _message) -> None:
        pass

    def log_subprocess_event(*_args, **_kwargs) -> None:
        pass

    def log_tagged_event(*_args, **_kwargs) -> None:
        pass

    LOGGING_AVAILABLE = False

COMMANDS_MD = Path("docs/Archive/COMMANDS_LIST.md")
EXECUTED_CMDS_FILE = Path("executed_commands.json")
SUGGESTION_INTERVAL = 10  # seconds


def parse_commands_from_md(md_path: Path) -> list:
    """Extract commands and their order from COMMANDS_LIST.md.

    Args:
        md_path (Path): Path to the markdown file containing commands.

    Returns:
        list: list of extracted commands in order.

    """
    commands: list[Any] = []
    urgency: dict[str, Any] = {}
    if not md_path.exists():
        if LOGGING_AVAILABLE:
            log_info("extract_commands", f"COMMANDS_LIST.md not found at {md_path}")
        return commands, urgency
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
        # Find all code blocks
        blocks = re.findall(r"```(?:powershell|bash|python)?\n(.*?)```", content, re.DOTALL)
        for block in blocks:
            for line in block.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    commands.append(line)
                    if "CRITICAL" in line or "⚠️" in line:
                        urgency[line] = "high"
    if LOGGING_AVAILABLE:
        log_tagged_event(
            "extract_commands",
            f"Parsed {len(commands)} commands from {md_path}",
            omnitag={"purpose": "command_extraction", "source": str(md_path)},
            megatag={"type": "COMMANDS_LIST", "context": "system_startup"},
        )
    return commands, urgency


def load_executed_commands():
    if EXECUTED_CMDS_FILE.exists():
        with open(EXECUTED_CMDS_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_executed_commands(commands) -> None:
    with open(EXECUTED_CMDS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(commands), f, indent=2)


def get_llm_suggestion(context):
    try:
        import requests

        # Resolve Ollama host via config helper > ServiceConfig > env/config file
        try:
            from src.utils.config_helper import get_ollama_host

            ollama_host = get_ollama_host()
        except (ImportError, ModuleNotFoundError, AttributeError):
            try:
                from src.config.service_config import ServiceConfig

                ollama_host = ServiceConfig.get_ollama_url()
            except (ImportError, ModuleNotFoundError, AttributeError):
                repo_root = Path(__file__).parent.parent.parent
                cfg_file = repo_root / "config" / "settings.json"
                cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
                ollama_host = cfg.get("ollama", {}).get(
                    "host",
                    os.getenv("OLLAMA_BASE_URL")
                    or f"{os.getenv('OLLAMA_HOST', 'http://127.0.0.1')}:{os.getenv('OLLAMA_PORT', '11435')}",
                )

        prompt = f"Given the following context, what is the optimal next command?\n{context}"
        resp = requests.post(
            f"{ollama_host}/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=10,
        )
        if resp.status_code == 200:
            suggestion = resp.json().get("response", "").strip()
            if LOGGING_AVAILABLE:
                log_tagged_event(
                    "extract_commands",
                    f"LLM suggested next command: {suggestion}",
                    omnitag={"purpose": "llm_suggestion", "model": "llama3"},
                    megatag={"type": "AI_ASSIST", "context": "command_suggestion"},
                )
            return suggestion
    except Exception as e:
        if LOGGING_AVAILABLE:
            log_info("extract_commands", f"LLM suggestion error: {e}")
    return None


def suggest_next_command(commands, urgency, executed):
    """Suggest next command based on urgency and execution state.

    OmniTag: {
        "purpose": "Command suggestion",
        "context": "Automation, idempotency",
        "evolution_stage": "v2.0"
    }
    MegaTag: {
        "type": "Process",
        "integration_points": ["modular_logging_system.py"],
        "related_tags": ["Automation", "Feedback"]
    }
    RSHTS: ΣΞΣ∞↠ΨΦΩ⟸.
    """
    for cmd in commands:
        if cmd not in executed:
            if urgency.get(cmd) == "high":
                if LOGGING_AVAILABLE:
                    log_tagged_event(
                        "extract_commands",
                        f"Suggesting urgent command: {cmd}",
                        omnitag={"purpose": "urgent_command", "urgency": "high"},
                    )
                return f"⚡ [URGENT] {cmd}"
            if LOGGING_AVAILABLE:
                log_tagged_event(
                    "extract_commands",
                    f"Suggesting next command: {cmd}",
                    omnitag={"purpose": "command_suggestion"},
                )
            return cmd
    if LOGGING_AVAILABLE:
        log_tagged_event(
            "extract_commands",
            "All documented commands executed.",
            omnitag={"purpose": "all_commands_complete"},
        )
    return None


def launch_tool(choice) -> None:
    tool_map = {
        # Use existing ChatDev Party System implementation under src/ai
        "party": "src/ai/ChatDev-Party-System.py",
        "wizard": "src/interface/Enhanced-Wizard-Navigator.py",
        "navigator": "src/interface/Enhanced-Wizard-Navigator.py",
        "adventure": "launch-adventure.py",
        "context": "src/interface/Interactive-Context-Browser.py",
    }
    if choice in tool_map:
        proc = subprocess.Popen([sys.executable, tool_map[choice]])
        if LOGGING_AVAILABLE:
            log_subprocess_event(
                "extract_commands",
                f"Launched tool: {choice}",
                command=tool_map[choice],
                pid=proc.pid,
                tags={"omnitag": {"purpose": "tool_launch", "tool": choice}},
            )
    elif LOGGING_AVAILABLE:
        log_info("extract_commands", f"Unknown tool requested: {choice}")


def command_suggester_loop() -> None:
    """Main loop for smart command suggestion and execution.

    OmniTag: {
        "purpose": "Command suggestion loop",
        "context": "Interactive automation",
        "evolution_stage": "v2.0"
    }
    MegaTag: {
        "type": "Process",
        "integration_points": ["modular_logging_system.py"],
        "related_tags": ["Automation", "Feedback", "UserInteraction"]
    }
    RSHTS: ΣΞΣ∞↠ΨΦΩ⟸.
    """
    commands, urgency = parse_commands_from_md(COMMANDS_MD)
    executed = load_executed_commands()
    shell_type = get_shell_type()
    # Filter commands for the current shell
    commands = filter_commands_for_shell(commands, shell_type)
    last_suggestion = None
    last_llm_suggestion = None
    while True:
        suggestion = suggest_next_command(commands, urgency, executed)
        llm_suggestion = None
        if suggestion:
            if suggestion != last_suggestion:
                last_suggestion = suggestion
            if LOGGING_AVAILABLE:
                log_tagged_event(
                    "extract_commands",
                    f"User prompted with suggestion: {suggestion}",
                    omnitag={"purpose": "user_prompt", "suggestion": suggestion},
                )
            llm_suggestion = get_llm_suggestion(f"Executed: {list(executed)[-5:]}")
            if llm_suggestion and llm_suggestion != last_llm_suggestion:
                last_llm_suggestion = llm_suggestion
        else:
            if last_suggestion != "ALL_DONE":
                last_suggestion = "ALL_DONE"
            if LOGGING_AVAILABLE:
                log_tagged_event(
                    "extract_commands",
                    "User notified: all commands complete.",
                    omnitag={"purpose": "user_prompt", "status": "complete"},
                )
        try:
            user_input = input("> ").strip()
            if user_input.startswith("launch "):
                tool = user_input.split(" ", 1)[1]
                launch_tool(tool)
            elif user_input:
                # Local operator-driven command execution; shell required for interactive UX.
                subprocess.run(user_input, check=False, shell=True)  # nosemgrep
                executed.add(user_input)
                save_executed_commands(executed)
                if LOGGING_AVAILABLE:
                    log_subprocess_event(
                        "extract_commands",
                        f"User executed command: {user_input}",
                        command=user_input,
                        pid=None,
                        tags={
                            "omnitag": {
                                "purpose": "user_command",
                                "command": user_input,
                            }
                        },
                    )
            else:
                time.sleep(SUGGESTION_INTERVAL)
        except KeyboardInterrupt:
            if LOGGING_AVAILABLE:
                log_info("extract_commands", "Smart Command Suggester stopped by user.")
            break


def get_shell_type() -> str:
    if os.name == "nt":
        shell = os.environ.get("SHELL") or os.environ.get("COMSPEC") or ""
        if "powershell" in shell.lower() or "pwsh" in shell.lower():
            return "powershell"
        if "cmd" in shell.lower():
            return "cmd"
        return "unknown"
    shell = os.environ.get("SHELL", "")
    if "bash" in shell:
        return "bash"
    return "unix"


def filter_commands_for_shell(commands, shell_type):
    filtered: list[Any] = []
    for cmd in commands:
        # Always include python and pip commands
        if (
            cmd.strip().startswith("python")
            or cmd.strip().startswith("pip")
            or (
                shell_type == "powershell"
                and (
                    cmd.strip().startswith("$")
                    or "Write-Host" in cmd
                    or "Set-ExecutionPolicy" in cmd
                )
            )
            or (
                shell_type in ("cmd", "bash", "unix")
                and not (
                    cmd.strip().startswith("$")
                    or "Write-Host" in cmd
                    or "Set-ExecutionPolicy" in cmd
                )
            )
        ):
            filtered.append(cmd)
    return filtered


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Smart Command Suggester")
    parser.add_argument("--test", action="store_true", help="Run command extraction test and exit")
    args = parser.parse_args()
    if args.test:
        commands, urgency = parse_commands_from_md(COMMANDS_MD)
        for cmd in commands:
            urgency_mark = " (high)" if urgency.get(cmd) == "high" else ""
    else:
        command_suggester_loop()

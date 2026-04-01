#!/usr/bin/env python3
"""MJOLNIR Protocol CLI — Unified Agent Dispatch for NuSyQ-Hub.

Usage:
    python scripts/nusyq_dispatch.py ask ollama "Analyze this function"
    python scripts/nusyq_dispatch.py council "Best approach?" --agents=ollama,lmstudio
    python scripts/nusyq_dispatch.py status --probes
    python scripts/nusyq_dispatch.py chain "Analyze then fix" --agents=ollama,codex
    python scripts/nusyq_dispatch.py delegate "Refactor auth" --agent=codex --priority=3
    python scripts/nusyq_dispatch.py queue "Generate test suite" --agent=ollama

All output is structured JSON to stdout. Exit code 0 = success, 1 = error.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Load .env.workspace so env-var-based probes (copilot, etc.) work from CLI
_env_workspace = _PROJECT_ROOT / ".env.workspace"
if _env_workspace.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(_env_workspace, override=False)
    except ImportError:
        pass  # dotenv not installed; env vars stay as-is


def _extract_json_payload(raw: str) -> dict[str, object] | None:
    text = (raw or "").strip()
    if not text:
        return None
    decoder = json.JSONDecoder()
    for start in range(len(text)):
        if text[start] != "{":
            continue
        try:
            payload, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and text[start + end :].strip() == "":
            return payload
    return None


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse CLI."""
    parser = argparse.ArgumentParser(
        prog="nusyq_dispatch",
        description="MJOLNIR Protocol — Unified Agent Dispatch",
    )
    sub = parser.add_subparsers(dest="command", help="Dispatch command")

    # ── ask ───────────────────────────────────────────────────────────────
    ask_p = sub.add_parser("ask", help="Route prompt to a single agent")
    ask_p.add_argument("agent", help="Agent name (ollama, codex, claude, lms, etc.)")
    ask_p.add_argument("prompt", help="Natural language prompt")
    ask_p.add_argument("--context-file", help="File path to include as context")
    ask_p.add_argument("--model", help="Specific model to request")
    ask_p.add_argument("--task-type", help="Override task type (analyze/review/generate/debug/...)")
    ask_p.add_argument(
        "--operating-mode",
        "--mode",
        dest="operating_mode",
        choices=["strict", "balanced", "fast"],
        help=(
            "Operating profile (strict=maximum controls, balanced=default, fast=momentum mode). "
            "Use --operating-mode when invoking via start_nusyq.py to avoid global --mode collision."
        ),
    )
    ask_p.add_argument(
        "--risk",
        choices=["low", "medium", "high"],
        help="Risk hint used by operating profile to tune blocking/diagnostics",
    )
    ask_p.add_argument(
        "--signal-budget",
        choices=["minimal", "normal", "full"],
        help="Signal intensity for profile metadata (minimal|normal|full)",
    )
    ask_p.add_argument("--priority", default="NORMAL", help="CRITICAL/HIGH/NORMAL/LOW/BACKGROUND")
    ask_p.add_argument("--timeout", type=float, help="Timeout in seconds")
    ask_p.add_argument(
        "--non-blocking",
        action="store_true",
        help="Return immediately for supported systems (e.g., openclaw/chatdev)",
    )
    ask_p.add_argument(
        "--wait-for-completion",
        action="store_true",
        help="Force blocking completion even if non-blocking defaults are enabled",
    )
    ask_p.add_argument(
        "--retry-attempts",
        type=int,
        help="Retry attempts for timeout-prone systems (openclaw)",
    )
    ask_p.add_argument(
        "--retry-backoff",
        type=float,
        help="Backoff multiplier applied to timeout budget per retry (openclaw)",
    )
    ask_p.add_argument(
        "--openclaw-agent",
        help="OpenClaw agent id override (defaults to NUSYQ_OPENCLAW_AGENT_ID or main)",
    )
    timeout_fallback_group = ask_p.add_mutually_exclusive_group()
    timeout_fallback_group.add_argument(
        "--auto-non-blocking-on-timeout",
        dest="auto_non_blocking_on_timeout",
        action="store_true",
        default=None,
        help="If blocking times out, relaunch supported systems in non-blocking mode",
    )
    timeout_fallback_group.add_argument(
        "--no-auto-non-blocking-on-timeout",
        dest="auto_non_blocking_on_timeout",
        action="store_false",
        help="Disable automatic non-blocking fallback after timeout",
    )
    ask_p.add_argument("--sns", action="store_true", help="Apply SNS-Core compression")
    ask_p.add_argument("--no-guild", action="store_true", help="Skip guild board tracking")
    ask_p.add_argument("--context", help="Context mode override (ecosystem/project/game)")
    ask_p.add_argument(
        "--doctor-gate",
        choices=["off", "warn", "require"],
        default=None,
        help="Triad readiness gate policy when targeting Claude/Codex/Copilot surfaces",
    )

    # ── council ───────────────────────────────────────────────────────────
    council_p = sub.add_parser("council", help="Query multiple agents (consensus)")
    council_p.add_argument("prompt", help="The question for all agents")
    council_p.add_argument("--agents", default="ollama,lmstudio", help="Comma-separated agent list")
    council_p.add_argument("--task-type", help="Override task type")
    council_p.add_argument("--sns", action="store_true", help="Apply SNS-Core compression")
    council_p.add_argument("--no-guild", action="store_true", help="Skip guild board tracking")
    council_p.add_argument(
        "--doctor-gate",
        choices=["off", "warn", "require"],
        default=None,
        help="Triad readiness gate policy when council agents include Claude/Codex/Copilot",
    )

    # ── parallel ──────────────────────────────────────────────────────────
    parallel_p = sub.add_parser("parallel", help="Execute prompt on multiple agents simultaneously")
    parallel_p.add_argument("prompt", help="Prompt for all agents")
    parallel_p.add_argument("--agents", default="ollama,lmstudio", help="Comma-separated agent list")
    parallel_p.add_argument("--task-type", help="Override task type")
    parallel_p.add_argument("--sns", action="store_true", help="Apply SNS-Core compression")
    parallel_p.add_argument(
        "--doctor-gate",
        choices=["off", "warn", "require"],
        default=None,
        help="Triad readiness gate policy when parallel agents include Claude/Codex/Copilot",
    )

    # ── chain ─────────────────────────────────────────────────────────────
    chain_p = sub.add_parser("chain", help="Sequential pipeline: output of A feeds B")
    chain_p.add_argument("prompt", help="Initial prompt")
    chain_p.add_argument("--agents", required=True, help="Comma-separated ordered agent list")
    chain_p.add_argument("--steps", help="Comma-separated step labels (analyze,generate,...)")
    chain_p.add_argument("--sns", action="store_true", help="Apply SNS-Core to initial prompt")
    chain_p.add_argument(
        "--doctor-gate",
        choices=["off", "warn", "require"],
        default=None,
        help="Triad readiness gate policy when chain agents include Claude/Codex/Copilot",
    )

    # ── delegate ──────────────────────────────────────────────────────────
    delegate_p = sub.add_parser("delegate", help="Fire-and-forget to guild board")
    delegate_p.add_argument("prompt", help="Task description")
    delegate_p.add_argument("--agent", default="auto", help="Target agent")
    delegate_p.add_argument("--priority", type=int, default=3, help="Priority 1-5 (1=critical)")
    delegate_p.add_argument("--sns", action="store_true", help="Apply SNS-Core compression")

    # ── queue ─────────────────────────────────────────────────────────────
    queue_p = sub.add_parser("queue", help="Queue task to BackgroundTaskOrchestrator")
    queue_p.add_argument("prompt", help="Task description")
    queue_p.add_argument("--agent", default="auto", help="Target agent")
    queue_p.add_argument("--task-type", help="Override task type")
    queue_p.add_argument("--priority", default="NORMAL", help="CRITICAL/HIGH/NORMAL/LOW/BACKGROUND")
    queue_p.add_argument("--sns", action="store_true", help="Apply SNS-Core compression")

    # ── drain ─────────────────────────────────────────────────────────────
    drain_p = sub.add_parser("drain", help="Execute pending guild board quests")
    drain_p.add_argument("--limit", type=int, default=5, help="Max quests to drain (default: 5)")

    # ── poll ──────────────────────────────────────────────────────────────
    poll_p = sub.add_parser("poll", help="Check status of a queued task or delegated quest")
    poll_p.add_argument("id", help="task_id (from queue) or quest_id (from delegate)")
    poll_p.add_argument(
        "--type",
        choices=["queue", "delegate"],
        default="queue",
        help="Source system to poll (default: queue)",
    )

    # ── recall ────────────────────────────────────────────────────────────
    recall_p = sub.add_parser("recall", help="Query MemoryPalace for past interactions by tag")
    recall_p.add_argument("tag", help="Tag to search (e.g., 'ollama', 'analyze', 'success', 'failed')")
    recall_p.add_argument("--limit", type=int, default=10, help="Max results to return (default: 10)")

    # ── skyclaw ───────────────────────────────────────────────────────────
    skyclaw_p = sub.add_parser("skyclaw", help="SkyClaw gateway lifecycle (status/start/stop)")
    skyclaw_p.add_argument(
        "action",
        choices=["status", "start", "stop"],
        help="Lifecycle action: status (probe), start (spawn daemon), stop (terminate session daemon)",
    )

    # ── status ────────────────────────────────────────────────────────────
    status_p = sub.add_parser("status", help="Report agent availability")
    status_p.add_argument("agent", nargs="?", help="Specific agent to check")
    status_p.add_argument("--probes", action="store_true", help="Probe agents (HTTP/CLI checks)")
    status_p.add_argument(
        "--no-recover",
        action="store_true",
        default=False,
        help="Disable auto-recovery for recoverable agents (e.g. Ollama); "
        "by default, probing Ollama when offline will attempt to start it.",
    )

    return parser


_TRIAD_AGENT_ALIASES = {
    "claude",
    "claude_cli",
    "codex",
    "vscode_codex",
    "copilot",
}


def _doctor_gate_mode(value: str | None) -> str:
    raw = str(value or os.getenv("NUSYQ_TRIAD_DOCTOR_GATE", "warn")).strip().lower()
    return raw if raw in {"off", "warn", "require"} else "warn"


def _uses_triad_agents(agents: list[str]) -> bool:
    return any(str(agent or "").strip().lower() in _TRIAD_AGENT_ALIASES for agent in agents)


def _run_multi_agent_doctor() -> dict[str, object]:
    cmd = [sys.executable, "scripts/start_nusyq.py", "multi_agent_doctor", "--json"]
    proc = subprocess.run(
        cmd,
        cwd=str(_PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        env=os.environ.copy(),
    )
    payload = _extract_json_payload(proc.stdout.strip())
    return {
        "exit_code": proc.returncode,
        "payload": payload if isinstance(payload, dict) else None,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def _check_dispatch_readiness(agents: list[str], gate_mode: str) -> tuple[bool, dict[str, object] | None]:
    mode = _doctor_gate_mode(gate_mode)
    if mode == "off" or not _uses_triad_agents(agents):
        return True, None
    doctor = _run_multi_agent_doctor()
    payload = doctor.get("payload")
    functional = isinstance(payload, dict) and bool(payload.get("functional"))
    if functional:
        return True, payload
    if mode == "warn":
        return True, payload if isinstance(payload, dict) else doctor
    return False, payload if isinstance(payload, dict) else doctor


def _output(envelope) -> int:
    """Print ResponseEnvelope (or plain dict) as JSON and return exit code."""
    if isinstance(envelope, dict):
        print(json.dumps(envelope, indent=2, ensure_ascii=False, default=str))
        return 0 if envelope.get("status") != "error" and "error" not in envelope else 1
    print(json.dumps(envelope.to_dict(), indent=2, ensure_ascii=False, default=str))
    return 0 if envelope.success else 1


async def _run(args: argparse.Namespace) -> int:
    """Execute the dispatch command."""
    from src.dispatch.mjolnir import MjolnirProtocol

    protocol = MjolnirProtocol()

    if args.command == "ask":
        readiness_ok, readiness_payload = _check_dispatch_readiness([args.agent], getattr(args, "doctor_gate", None))
        if not readiness_ok:
            print(
                json.dumps(
                    {
                        "error": "triad_doctor_gate_blocked_dispatch",
                        "doctor_gate": _doctor_gate_mode(getattr(args, "doctor_gate", None)),
                        "readiness": readiness_payload,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 1
        if getattr(args, "non_blocking", False) and getattr(args, "wait_for_completion", False):
            print(
                json.dumps(
                    {
                        "error": "Use either --non-blocking or --wait-for-completion, not both.",
                    },
                    indent=2,
                )
            )
            return 1

        extra_context: dict[str, object] = {}
        if getattr(args, "non_blocking", False):
            extra_context["non_blocking"] = True
            extra_context["openclaw_non_blocking"] = True
        if getattr(args, "wait_for_completion", False):
            extra_context["wait_for_completion"] = True
            extra_context["openclaw_wait_for_completion"] = True
        if getattr(args, "retry_attempts", None) is not None:
            extra_context["openclaw_retry_attempts"] = int(args.retry_attempts)
        if getattr(args, "retry_backoff", None) is not None:
            extra_context["openclaw_retry_backoff"] = float(args.retry_backoff)
        if getattr(args, "openclaw_agent", None):
            extra_context["openclaw_agent_id"] = str(args.openclaw_agent)
        if getattr(args, "operating_mode", None):
            extra_context["operating_mode"] = str(args.operating_mode)
        if getattr(args, "risk", None):
            extra_context["risk_level"] = str(args.risk)
        if getattr(args, "signal_budget", None):
            extra_context["signal_budget"] = str(args.signal_budget)
        if getattr(args, "auto_non_blocking_on_timeout", None) is not None:
            extra_context["openclaw_auto_non_blocking_on_timeout"] = bool(args.auto_non_blocking_on_timeout)

        result = await protocol.ask(
            args.agent,
            args.prompt,
            context=args.context,
            context_file=args.context_file,
            model=args.model,
            task_type=args.task_type,
            priority=args.priority,
            timeout=args.timeout,
            sns=args.sns,
            no_guild=args.no_guild,
            extra_context=extra_context or None,
        )
        if readiness_payload is not None and isinstance(result, object):
            try:
                result.metadata = getattr(result, "metadata", {}) or {}
                result.metadata["triad_readiness"] = readiness_payload
            except Exception:
                pass
        return _output(result)

    elif args.command == "council":
        agents = [a.strip() for a in args.agents.split(",")]
        readiness_ok, readiness_payload = _check_dispatch_readiness(agents, getattr(args, "doctor_gate", None))
        if not readiness_ok:
            print(
                json.dumps(
                    {
                        "error": "triad_doctor_gate_blocked_dispatch",
                        "doctor_gate": _doctor_gate_mode(getattr(args, "doctor_gate", None)),
                        "readiness": readiness_payload,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 1
        result = await protocol.council(
            args.prompt,
            agents=agents,
            task_type=args.task_type,
            sns=args.sns,
            no_guild=args.no_guild,
        )
        if readiness_payload is not None:
            try:
                result.metadata = getattr(result, "metadata", {}) or {}
                result.metadata["triad_readiness"] = readiness_payload
            except Exception:
                pass
        return _output(result)

    elif args.command == "parallel":
        agents = [a.strip() for a in args.agents.split(",")]
        readiness_ok, readiness_payload = _check_dispatch_readiness(agents, getattr(args, "doctor_gate", None))
        if not readiness_ok:
            print(
                json.dumps(
                    {
                        "error": "triad_doctor_gate_blocked_dispatch",
                        "doctor_gate": _doctor_gate_mode(getattr(args, "doctor_gate", None)),
                        "readiness": readiness_payload,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 1
        result = await protocol.parallel(
            args.prompt,
            agents=agents,
            task_type=args.task_type,
            sns=args.sns,
        )
        if readiness_payload is not None:
            try:
                result.metadata = getattr(result, "metadata", {}) or {}
                result.metadata["triad_readiness"] = readiness_payload
            except Exception:
                pass
        return _output(result)

    elif args.command == "chain":
        agents = [a.strip() for a in args.agents.split(",")]
        readiness_ok, readiness_payload = _check_dispatch_readiness(agents, getattr(args, "doctor_gate", None))
        if not readiness_ok:
            print(
                json.dumps(
                    {
                        "error": "triad_doctor_gate_blocked_dispatch",
                        "doctor_gate": _doctor_gate_mode(getattr(args, "doctor_gate", None)),
                        "readiness": readiness_payload,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 1
        steps = [s.strip() for s in args.steps.split(",")] if args.steps else None
        result = await protocol.chain(
            args.prompt,
            agents=agents,
            steps=steps,
            sns=args.sns,
        )
        if readiness_payload is not None:
            try:
                result.metadata = getattr(result, "metadata", {}) or {}
                result.metadata["triad_readiness"] = readiness_payload
            except Exception:
                pass
        return _output(result)

    elif args.command == "delegate":
        result = await protocol.delegate(
            args.prompt,
            agent=args.agent,
            priority=args.priority,
            sns=args.sns,
        )
        return _output(result)

    elif args.command == "queue":
        result = await protocol.queue(
            args.prompt,
            agent=args.agent,
            task_type=args.task_type,
            priority=args.priority,
            sns=args.sns,
        )
        return _output(result)

    elif args.command == "drain":
        result = await protocol.drain(limit=args.limit)
        return _output(result)

    elif args.command == "poll":
        if getattr(args, "type", "queue") == "delegate":
            result = await protocol.poll_delegate(args.id)
        else:
            result = protocol.poll_queue(args.id)
        return _output(result)

    elif args.command == "recall":
        items = protocol.recall(args.tag, limit=args.limit)
        return _output({"tag": args.tag, "count": len(items), "interactions": items})

    elif args.command == "skyclaw":
        action = args.action
        if action == "status":
            result = await protocol.skyclaw_status()
        elif action == "start":
            result = await protocol.skyclaw_start()
        else:  # stop
            result = await protocol.skyclaw_stop()
        return _output(result)

    elif args.command == "status":
        result = await protocol.status(
            args.agent,
            probes=args.probes,
            auto_recover=not getattr(args, "no_recover", False),
        )
        return _output(result)

    else:
        print(json.dumps({"error": "No command specified. Use --help."}, indent=2))
        return 1


def main() -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        print(json.dumps({"error": "Interrupted by user"}, indent=2))
        return 130


if __name__ == "__main__":
    sys.exit(main())

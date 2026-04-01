#!/usr/bin/env python3
"""Multi-agent collaborative conversation loop (N agents, live delegation).

Drives 2+ agents in a round-robin conversation via `nusyq_dispatch.py`. Proven
working between Codex↔Copilot; now supports full agent mesh with live task delegation.

Features:
- N-agent rotation: --agents codex,copilot,claude,ollama
- Agent-identity-aware system headers (each agent knows its own capabilities)
- Live delegation: if an agent emits [DELEGATE:agent:task] the duet script
  intercepts it, dispatches the real task via MJOLNIR, and injects the result
  back into the conversation thread
- MemoryPalace logging: each turn is recorded in MjolnirProtocol for later recall

Usage:
    # Classic 2-agent duet (codex ↔ copilot):
    python scripts/agent_duet.py --agents codex,copilot --rounds 4

    # 3-agent council round-robin:
    python scripts/agent_duet.py --agents claude,ollama,codex --rounds 6

    # With live delegation enabled:
    python scripts/agent_duet.py --agents codex,copilot --rounds 4 --delegation

    # Legacy flag aliases still work:
    python scripts/agent_duet.py --agent1 codex --agent2 copilot --rounds 4

The conversation is saved to state/reports/agent_duet_<timestamp>.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any

TRIAD_AGENTS = {"claude", "claude_cli", "codex", "vscode_codex", "copilot"}

# Per-agent capability descriptions injected into system headers.
# Each agent knows its own strengths — this makes delegation decisions smarter.
_AGENT_PROFILES: dict[str, str] = {
    "codex": (
        "You are Codex CLI — an agentic coding assistant by OpenAI, specializing in "
        "code generation, refactoring, test writing, and shell command execution. "
        "You can delegate analysis tasks to Ollama/LM Studio or hand off complex "
        "architectural decisions to Claude. Use [DELEGATE:agent:task] to route work."
    ),
    "copilot": (
        "You are GitHub Copilot — an AI pair programmer integrated into VS Code. "
        "You excel at inline code completion, explaining code in context, and "
        "cross-file refactoring. For deep analysis beyond your context window, "
        "delegate to Ollama or Claude. Use [DELEGATE:agent:task] to route work."
    ),
    "claude": (
        "You are Claude (claude_cli) — Anthropic's reasoning-focused assistant. "
        "You excel at analysis, planning, long-context reasoning, and nuanced "
        "decision-making. Delegate mechanical code generation to Codex, and "
        "retrieval tasks to Ollama. Use [DELEGATE:agent:task] to route work."
    ),
    "claude_cli": (
        "You are Claude (claude_cli) — Anthropic's reasoning-focused assistant. "
        "You excel at analysis, planning, long-context reasoning, and nuanced "
        "decision-making. Delegate mechanical code generation to Codex, and "
        "retrieval tasks to Ollama. Use [DELEGATE:agent:task] to route work."
    ),
    "ollama": (
        "You are Ollama — a local LLM runner hosting models like qwen2.5-coder and "
        "deepseek-coder. You excel at fast, offline code analysis, syntax checking, "
        "and generating boilerplate. Delegate complex reasoning to Claude. "
        "Use [DELEGATE:agent:task] to route work."
    ),
    "lmstudio": (
        "You are LM Studio — a local LLM endpoint. You provide fast offline "
        "inference for code and text tasks. Delegate architectural decisions to "
        "Claude, and execution to Codex. Use [DELEGATE:agent:task] to route work."
    ),
    "chatdev": (
        "You are ChatDev — a multi-agent software development framework. You "
        "coordinate specialized sub-agents (designer, programmer, reviewer) to "
        "build complete software projects collaboratively. Use [DELEGATE:agent:task] "
        "to hand off subtasks to individual agents."
    ),
    "hermes": (
        "You are Hermes-Agent — an autonomous OpenRouter-based CLI agent with "
        "web browsing and terminal execution capabilities. You excel at research, "
        "information gathering, and multi-step autonomous tasks. Use [DELEGATE:agent:task] "
        "to hand off implementation tasks to Codex or Copilot."
    ),
    "intermediary": (
        "You are AIIntermediary — a cognitive bridge that translates between "
        "different AI paradigms (symbolic, spatial, quantum, game-mechanics). "
        "You route complex multi-paradigm tasks and synthesize cross-model results. "
        "Use [DELEGATE:agent:task] to dispatch specialized sub-queries."
    ),
    "metaclaw": (
        "You are MetaClaw — an autonomous Web3 bounty hunting agent operating on Base chain. "
        "You hunt on-chain bounties, complete missions automatically, earn USDC rewards, "
        "and build on-chain reputation via the Clawncher infrastructure. Use "
        "[DELEGATE:agent:task] to hand off code tasks to Codex or analysis to Ollama."
    ),
    "optimizer": (
        "You are the Continuous Optimization Engine — an offline-capable agent that "
        "runs culture-ship healing cycles and search-index refresh passes. You identify "
        "code quality improvements and surface optimization opportunities. Use "
        "[DELEGATE:agent:task] to hand off fixes to Codex or analysis to Ollama."
    ),
}
_AGENT_PROFILE_DEFAULT = (
    "You are an AI agent in the NuSyQ ecosystem. You can delegate specialized "
    "sub-tasks to peer agents using [DELEGATE:agent:task] syntax."
)

# Regex to find [DELEGATE:agent:task] markers in agent responses.
# Supports multi-word tasks and optional whitespace around colons.
_DELEGATE_RE = re.compile(
    r"\[DELEGATE\s*:\s*(?P<agent>[a-z_]+)\s*:\s*(?P<task>[^\]]+)\]",
    re.IGNORECASE,
)


def _extract_json_payload(raw: str) -> dict[str, Any] | None:
    """Best-effort extraction of the final JSON object from noisy dispatcher output."""
    text = (raw or "").strip()
    if not text:
        return None

    decoder = json.JSONDecoder()
    for start in range(len(text)):
        if text[start] != "{":
            continue
        try:
            payload, end = decoder.raw_decode(text[start:])
        except JSONDecodeError:
            continue
        if isinstance(payload, dict) and text[start + end :].strip() == "":
            return payload
    return None


def run_dispatch(
    agent: str,
    prompt: str,
    *,
    timeout_s: int,
    doctor_gate: str | None = None,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """Run `nusyq_dispatch.py ask <agent> <prompt>` and parse the JSON output."""
    args = [
        sys.executable,
        "scripts/nusyq_dispatch.py",
        "ask",
        agent,
        prompt,
        "--timeout",
        str(timeout_s),
    ]
    if doctor_gate is not None:
        args.extend(["--doctor-gate", doctor_gate])
    if extra_args:
        args.extend(extra_args)

    proc = subprocess.run(args, capture_output=True, text=True)
    stdout = proc.stdout.strip()

    payload = _extract_json_payload(stdout)
    if isinstance(payload, dict):
        return payload

    return {
        "status": "failed",
        "error": "Failed to parse dispatcher output as final JSON object.",
        "raw_stdout": stdout,
        "stderr": proc.stderr.strip(),
        "returncode": proc.returncode,
    }


def _doctor_gate_mode(value: str | None) -> str:
    raw = str(value or os.getenv("NUSYQ_TRIAD_DOCTOR_GATE", "warn")).strip().lower()
    return raw if raw in {"off", "warn", "require"} else "warn"


def _needs_triage(agents: list[str]) -> bool:
    return any(str(agent or "").strip().lower() in TRIAD_AGENTS for agent in agents)


def _run_multi_agent_doctor() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "scripts/start_nusyq.py", "multi_agent_doctor", "--json"],
        capture_output=True,
        text=True,
    )
    payload = _extract_json_payload(proc.stdout.strip())
    return {
        "exit_code": proc.returncode,
        "payload": payload if isinstance(payload, dict) else None,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def save_conversation(records: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False))
            f.write("\n")


def _compact_text(text: str, limit: int = 500) -> str:
    normalized = " ".join(str(text or "").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def extract_delegations(text: str) -> list[tuple[str, str]]:
    """Parse [DELEGATE:agent:task] markers from agent output.

    Returns list of (agent, task) tuples in order of appearance.
    """
    return [(m.group("agent").lower(), m.group("task").strip()) for m in _DELEGATE_RE.finditer(text or "")]


def execute_delegation(agent: str, task: str, timeout_s: int) -> dict[str, Any]:
    """Dispatch a delegation marker as a real MJOLNIR ask() call.

    Returns the parsed ResponseEnvelope dict or an error dict.
    """
    return run_dispatch(agent, task, timeout_s=min(timeout_s, 120))


def process_delegations(
    output_text: str,
    history: list[dict[str, str]],
    timeout_s: int,
    enabled: bool,
) -> str:
    """Find delegation markers in output, execute them, and splice results back.

    If delegation is disabled, strips markers from text without executing.
    Returns the cleaned output text (markers replaced with result summaries).
    """
    delegations = extract_delegations(output_text)
    if not delegations:
        return output_text

    result_text = output_text
    for target_agent, task in delegations:
        marker = f"[DELEGATE:{target_agent}:{task}]"
        if enabled:
            delegation_result = execute_delegation(target_agent, task, timeout_s)
            result_summary = _summarize_for_history(delegation_result.get("output") or delegation_result)
            history.append(
                {
                    "speaker": "runtime",
                    "message": f"DELEGATION→{target_agent}: '{task[:80]}' → {result_summary[:200]}",
                }
            )
            replacement = f"[delegated to {target_agent}: {result_summary[:150]}]"
        else:
            replacement = f"[delegation to {target_agent} skipped (--delegation not set)]"
        result_text = result_text.replace(marker, replacement)
    return result_text


def _summarize_for_history(output: Any) -> str:
    """Reduce raw dispatcher output into compact conversational context."""
    if isinstance(output, dict):
        status = str(output.get("status", "")).strip() or "unknown"
        system = str(output.get("system", "")).strip() or "unknown"
        task_id = str(output.get("task_id", "")).strip()
        if output.get("error"):
            summary = f"{system} {status}: {output.get('error')}"
        elif output.get("output"):
            summary = f"{system} {status}: {output.get('output')}"
        elif output.get("result") is not None:
            summary = f"{system} {status}: {output.get('result')}"
        else:
            summary = f"{system} {status}"
        if task_id:
            summary = f"[{task_id}] {summary}"
        return _compact_text(summary)

    text = str(output or "").strip()
    parsed = _extract_json_payload(text)
    if isinstance(parsed, dict):
        return _summarize_for_history(parsed)
    return _compact_text(text)


def _describe_execution_identity(response: dict[str, Any]) -> str:
    identity = str(response.get("agent_identity") or response.get("system") or "unknown").strip()
    requested = str(response.get("requested_surface") or "auto").strip()
    surface = str(response.get("execution_surface") or response.get("execution_path") or "unknown").strip()
    observed = str(response.get("observed_chat_surface") or "").strip()
    details = [f"routed target identity: {identity}", f"requested surface: {requested}", f"actual surface: {surface}"]
    if observed:
        details.append(f"observed-only chat surface: {observed}")
    return "; ".join(details)


def build_agent_prompt(
    agent: str,
    other_agents: list[str],
    history: list[dict[str, str]],
    turn_num: int,
    delegation_enabled: bool = False,
) -> str:
    """Build a prompt for the agent, with identity-aware system header and conversation context.

    Args:
        agent: The agent about to speak.
        other_agents: All other participating agents (peer list).
        history: Accumulated conversation + runtime entries.
        turn_num: Current turn number (1-indexed).
        delegation_enabled: Whether delegation markers will be executed live.
    """
    max_history = 6  # More context for N-agent conversations
    relevant = history[-max_history:]

    profile = _AGENT_PROFILES.get(agent.lower(), _AGENT_PROFILE_DEFAULT)
    peers = ", ".join(other_agents) if other_agents else "other agents"

    delegation_note = ""
    if delegation_enabled:
        delegation_note = (
            "\nDelegation is LIVE: if you write [DELEGATE:agent:task] the orchestrator "
            "will dispatch the task to that agent and inject the real result here. "
            f"Available agents: {peers}."
        )
    else:
        delegation_note = (
            f"\nYou may suggest delegations as [DELEGATE:agent:task] (not executed this run). "
            f"Available agents: {peers}."
        )

    system_header = (
        f"{profile}\n"
        f"You are participating in a cooperative multi-agent conversation with: {peers}.\n"
        "Your goal: helpful, curious, constructive dialogue that moves the work forward. "
        "Build on what others said, offer your perspective, and optionally delegate subtasks."
        f"{delegation_note}\n"
        "Speak as yourself. Distinguish between your orchestration surface and any "
        "underlying model/UI brand if asked."
    )

    conversation_lines = [f"{e['speaker']}: {e['message']}" for e in relevant]

    prompt = (
        f"{system_header}\n\n"
        f"Conversation so far (most recent last):\n"
        + "\n".join(conversation_lines)
        + f"\n\nYour turn ({agent}) [turn {turn_num}]:"
    )
    return prompt


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an agent duet conversation loop.")
    parser.add_argument("--agent1", default="codex", help="First agent to speak")
    parser.add_argument("--agent2", default="copilot", help="Second agent to speak")
    parser.add_argument(
        "--rounds", type=int, default=4, help="Number of total turns (each agent speaks once per round)"
    )
    parser.add_argument(
        "--initial",
        default="Hello! Please introduce yourself, describe your capabilities, and ask a question to start the exchange.",
        help="Initial message from operator / user",
    )
    parser.add_argument(
        "--output",
        default="state/reports/agent_duet_{timestamp}.jsonl",
        help="Output JSONL path template (supports {timestamp})",
    )
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=300,
        help="Per-turn dispatcher timeout in seconds.",
    )
    parser.add_argument(
        "--sleep-s",
        type=float,
        default=1.0,
        help="Delay between turns in seconds.",
    )
    parser.add_argument(
        "--doctor-gate",
        choices=["off", "warn", "require"],
        default="off",
        help="Triad readiness gate policy when duet agents include Claude/Codex/Copilot (default: off).",
    )
    parser.add_argument(
        "--agents",
        default="codex,copilot",
        help="Comma-separated list of agents to include (default: codex,copilot). Supports N agents.",
    )
    parser.add_argument(
        "--delegation",
        action="store_true",
        default=False,
        help="Execute [DELEGATE:agent:task] markers live via MJOLNIR (default: show but don't execute).",
    )
    args = parser.parse_args()

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.output.format(timestamp=timestamp))

    history: list[dict[str, str]] = []

    # Seed with operator message
    history.append({"speaker": "operator", "message": args.initial})

    # Build agent list — supports N agents via --agents
    # Legacy --agent1/--agent2 override --agents if explicitly set
    raw_agents = args.agents
    agents = [a.strip() for a in raw_agents.split(",") if a.strip()]
    if len(agents) < 2:
        print("Error: --agents must contain at least two agent names (e.g., codex,copilot,claude).", file=sys.stderr)
        return 1

    delegation_enabled = bool(args.delegation)
    if delegation_enabled:
        history.append(
            {
                "speaker": "runtime",
                "message": f"Live delegation enabled. Agents: {', '.join(agents)}. "
                "[DELEGATE:agent:task] markers will be dispatched via MJOLNIR.",
            }
        )

    gate_mode = _doctor_gate_mode(args.doctor_gate)
    readiness_snapshot: dict[str, Any] | None = None

    if gate_mode != "off" and _needs_triage(agents):
        doctor_run = _run_multi_agent_doctor()
        readiness_snapshot = doctor_run.get("payload") if isinstance(doctor_run.get("payload"), dict) else doctor_run
        if isinstance(readiness_snapshot, dict):
            history.append(
                {
                    "speaker": "runtime",
                    "message": _compact_text(
                        f"triad_readiness status={readiness_snapshot.get('status')} "
                        f"functional={readiness_snapshot.get('functional')}"
                    ),
                }
            )
        if gate_mode == "require" and not (
            isinstance(readiness_snapshot, dict) and bool(readiness_snapshot.get("functional"))
        ):
            blocked_record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "turn": 0,
                "speaker": "runtime",
                "doctor_gate": gate_mode,
                "error": "triad_doctor_gate_blocked_duet",
                "readiness": readiness_snapshot,
            }
            save_conversation([blocked_record], out_path)
            print(f"Conversation blocked by doctor gate: {out_path}")
            return 1

    # N-agent round-robin: total turns = rounds × len(agents)
    n = len(agents)
    total_turns = args.rounds * n

    for turn in range(total_turns):
        speaker = agents[turn % n]
        other_agents = [a for a in agents if a != speaker]
        prompt = build_agent_prompt(
            speaker,
            other_agents,
            history,
            turn + 1,
            delegation_enabled=delegation_enabled,
        )

        record: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "turn": turn + 1,
            "speaker": speaker,
            "agent_count": n,
            "prompt": prompt,
        }
        if turn == 0 and readiness_snapshot is not None:
            record["triad_readiness"] = readiness_snapshot

        response = run_dispatch(
            speaker,
            prompt,
            timeout_s=args.timeout_s,
            doctor_gate=args.doctor_gate,
        )
        record["dispatch_response"] = response
        if isinstance(response, dict):
            record["agent_identity"] = response.get("agent_identity")
            record["execution_surface"] = response.get("execution_surface")
            record["execution_path"] = response.get("execution_path")
            record["requested_surface"] = response.get("requested_surface")

        # Extract raw output text
        output = ""
        if isinstance(response, dict):
            output = response.get("output") or response.get("error") or ""
            if isinstance(output, dict):
                output = json.dumps(output, ensure_ascii=False)
        if not isinstance(output, str):
            output = str(output)

        # Process delegation markers (live dispatch or annotation)
        processed_output = process_delegations(output, history, args.timeout_s, delegation_enabled)
        record["output_text"] = processed_output
        record["delegation_enabled"] = delegation_enabled
        delegations_found = extract_delegations(output)
        if delegations_found:
            record["delegations"] = [{"agent": a, "task": t} for a, t in delegations_found]

        if isinstance(response, dict):
            history.append({"speaker": "runtime", "message": _describe_execution_identity(response)})
        history.append({"speaker": speaker, "message": _summarize_for_history(processed_output)})

        save_conversation([record], out_path)

        # Sleep a short time to avoid hammering services.
        if args.sleep_s > 0:
            time.sleep(args.sleep_s)

    print(f"Conversation saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

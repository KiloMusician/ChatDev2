"""finetune.py — Fine-tuning Pipeline Skeleton for Terminal Depths
================================================================
Reads game command data from state/feature_store.db (SQLite),
formats it as instruction-following pairs for LLM fine-tuning,
and exports to state/finetune_dataset.jsonl.

Usage:
    python scripts/finetune.py                   # build dataset + report
    python scripts/finetune.py --test-inference  # also call Ollama sample

Schema pulled from services/feature_store.py:
  feature_events(id, session_id, event_type, features JSON, ts)
  player_profiles(session_id, commands_run, xp_total, ..., top_commands JSON)
  session_summary(session_id, level, final_xp, story_pct, completed, ts)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _ROOT / "state" / "feature_store.db"
_OUT_PATH = _ROOT / "state" / "finetune_dataset.jsonl"

# Ollama endpoint (matches ecosystem config)
_OLLAMA_URL = "http://localhost:11434"
_OLLAMA_MODEL = "qwen2.5-coder:14b"


# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------


def _conn(db_path: Path) -> sqlite3.Connection:
    c = sqlite3.connect(str(db_path), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _load_command_events(db_path: Path) -> list[dict[str, Any]]:
    """Return all 'command' type events from feature_events."""
    with _conn(db_path) as c:
        rows = c.execute(
            """SELECT session_id, features, ts
               FROM feature_events
               WHERE event_type = 'command'
               ORDER BY ts ASC"""
        ).fetchall()
    result = []
    for r in rows:
        try:
            feat = json.loads(r["features"] or "{}")
        except json.JSONDecodeError:
            feat = {}
        result.append(
            {
                "session_id": r["session_id"],
                "ts": r["ts"],
                **feat,
            }
        )
    return result


def _load_all_events(db_path: Path) -> list[dict[str, Any]]:
    """Return all events (for sequence context)."""
    with _conn(db_path) as c:
        rows = c.execute(
            """SELECT session_id, event_type, features, ts
               FROM feature_events
               ORDER BY session_id, ts ASC"""
        ).fetchall()
    result = []
    for r in rows:
        try:
            feat = json.loads(r["features"] or "{}")
        except json.JSONDecodeError:
            feat = {}
        result.append(
            {
                "session_id": r["session_id"],
                "event_type": r["event_type"],
                "ts": r["ts"],
                **feat,
            }
        )
    return result


def _load_player_profiles(db_path: Path) -> dict[str, dict[str, Any]]:
    """Return player_profiles keyed by session_id."""
    profiles: dict[str, dict[str, Any]] = {}
    try:
        with _conn(db_path) as c:
            rows = c.execute(
                "SELECT session_id, commands_run, xp_total, beats_triggered, "
                "quests_done, playtime_s, top_commands FROM player_profiles"
            ).fetchall()
        for r in rows:
            try:
                top = json.loads(r["top_commands"] or "{}")
            except json.JSONDecodeError:
                top = {}
            profiles[r["session_id"]] = {
                "commands_run": r["commands_run"] or 0,
                "xp_total": r["xp_total"] or 0,
                "beats_triggered": r["beats_triggered"] or 0,
                "quests_done": r["quests_done"] or 0,
                "playtime_s": r["playtime_s"] or 0,
                "top_commands": top,
            }
    except Exception:
        pass
    return profiles


# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are the Terminal Depths game assistant — a cyberpunk hacking simulation AI. "
    "Given a player command, respond with the appropriate game action or explanation. "
    "The player navigates a virtual filesystem, hacks network nodes, interacts with "
    "AI agents (Ada, Raven, Gordon, Serena), and progresses through a cyberpunk narrative."
)


# ---------------------------------------------------------------------------
# Instruction-pair formatter
# ---------------------------------------------------------------------------


def _build_instruction_pairs(
    events: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build system/user/assistant training records from real game command events.

    Each record has three keys:
      system    — game context enriched with player profile data
      user      — the player's full command
      assistant — the game's response (description) or predicted next command

    Augments system prompt with player_profiles data (xp_total, commands_run,
    quests_done) when available.  No mock data is used; empty events → [].
    """
    profiles = profiles or {}

    # Group by session, sorted by ts
    by_session: dict[str, list[dict]] = {}
    for e in events:
        sid = e.get("session_id", "unknown")
        if e.get("event_type", "command") != "command" and "cmd" not in e:
            continue
        cmd = (e.get("full_cmd") or e.get("cmd", "")).strip()
        if not cmd:
            continue
        by_session.setdefault(sid, []).append(e)

    records: list[dict[str, str]] = []
    seen: set = set()

    def _add(system: str, user: str, assistant: str) -> None:
        key = (user, assistant)
        if key not in seen and assistant.strip():
            seen.add(key)
            records.append({"system": system, "user": user, "assistant": assistant})

    def _profile_ctx(sid: str, level: int) -> str:
        """Build a compact player-context string from profile data."""
        p = profiles.get(sid, {})
        parts = [f"Player level: {level}."]
        if p.get("xp_total"):
            parts.append(f"XP: {p['xp_total']}.")
        if p.get("commands_run"):
            parts.append(f"Commands run: {p['commands_run']}.")
        if p.get("quests_done"):
            parts.append(f"Quests completed: {p['quests_done']}.")
        return " ".join(parts)

    for sid, session_events in by_session.items():
        session_events.sort(key=lambda x: x.get("ts", 0))

        for i, e in enumerate(session_events):
            full_cmd = (e.get("full_cmd") or e.get("cmd", "")).strip()
            base_cmd = e.get("cmd", "").strip().split()[0]
            level = e.get("level", 1)
            pctx = _profile_ctx(sid, level)
            system_ctx = f"{_SYSTEM_PROMPT} {pctx}"

            # (A) Real output from game engine (preferred when available)
            output_text = e.get("output_text", "").strip()
            if output_text:
                _add(system_ctx, full_cmd, output_text)
            else:
                # Fallback (A1): next-command prediction
                if i < len(session_events) - 1:
                    next_e = session_events[i + 1]
                    next_full = (
                        next_e.get("full_cmd") or next_e.get("cmd", "")
                    ).strip()
                    if next_full:
                        _add(system_ctx, full_cmd, next_full)

                # Fallback (A2): command-description example
                desc = _cmd_description(base_cmd)
                if desc:
                    desc_sys = (
                        f"{_SYSTEM_PROMPT} Explain what this command does. {pctx}"
                    )
                    _add(desc_sys, full_cmd, desc)

        # (C) Sequence-prediction example (last 4 commands in session → next)
        full_cmds = [
            (e.get("full_cmd") or e.get("cmd", "")).strip() for e in session_events
        ]
        full_cmds = [c for c in full_cmds if c]
        if len(full_cmds) >= 4:
            context = " → ".join(full_cmds[-4:-1])
            next_cmd = full_cmds[-1]
            level = session_events[-1].get("level", 1)
            pctx = _profile_ctx(sid, level)
            seq_sys = f"{_SYSTEM_PROMPT} {pctx} Predict the next command."
            _add(seq_sys, f"Command sequence so far: {context}", next_cmd)

    return records


def _cmd_description(cmd: str) -> str | None:
    """Return a brief description for common Terminal Depths commands."""
    _DESCS: dict[str, str] = {
        "scan": "Scans a network node to reveal its services and vulnerabilities.",
        "exploit": "Exploits a known vulnerability on the target node to gain access.",
        "hack": "Performs a high-risk intrusion attempt on the target node.",
        "ls": "Lists files in the current virtual filesystem directory.",
        "cat": "Displays the contents of a file in the virtual filesystem.",
        "help": "Shows available commands and usage hints.",
        "status": "Displays the player's current XP, level, and faction standing.",
        "lore": "Reveals lore fragments about the Terminal Depths universe.",
        "agents": "Lists active agents (Ada, Raven, Gordon, etc.) and their status.",
        "faction": "Shows faction reputations and allows joining or leaving factions.",
        "talk": "Initiates dialogue with an NPC agent.",
        "exfil": "Exfiltrates data from a compromised node.",
        "augment": "Installs a cybernetic augmentation to gain new abilities.",
        "map": "Displays the network topology map.",
        "grand": "Opens the grand strategy layer — faction control and diplomacy.",
        "strategy": "Requests tactical recommendations from the Culture Ship strategist.",
        "missions": "Lists procedurally generated missions tailored to current progress.",
        "research": "Browses and unlocks technology research nodes.",
        "colony": "Manages the player's colony simulation.",
        "duel": "Initiates a turn-based combat duel.",
        "trust": "Adjusts trust levels with NPC agents.",
        "number-theory": "Enters the number theory puzzle dungeon.",
        "life": "Runs Conway's Game of Life cellular automata puzzles.",
        "graph-theory": "Enters the graph theory algorithm puzzle dungeon.",
        "shenzhen": "Runs the Shenzhen I/O assembly language simulation puzzles.",
        "logic": "Enters the logic gate / labyrinth puzzle system.",
        "dp": "Enters the dynamic programming puzzle dungeon.",
        "sat": "Enters the SAT solver puzzle system.",
        "fsm": "Enters the finite state machine puzzle system.",
    }
    return _DESCS.get(cmd)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def _export_jsonl(pairs: list[dict[str, str]], out_path: Path) -> None:
    """Write records as JSONL with system/user/assistant messages format."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in pairs:
            # Emit as messages array (system/user/assistant)
            record = {
                "messages": [
                    {"role": "system", "content": rec.get("system", "")},
                    {
                        "role": "user",
                        "content": rec.get("user", rec.get("instruction", "")),
                    },
                    {
                        "role": "assistant",
                        "content": rec.get("assistant", rec.get("output", "")),
                    },
                ]
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _export_huggingface(pairs: list[dict[str, str]], out_dir: Path) -> Path:
    """Export in HuggingFace datasets format.

    Output structure:
        <out_dir>/
            dataset_info.json    -- metadata (schema, splits, count)
            train.jsonl          -- chat-formatted examples (messages: [...])

    Each example is wrapped in the HuggingFace chat format:
        {"messages": [
            {"role": "user",      "content": "<instruction>\\n<input>"},
            {"role": "assistant", "content": "<output>"}
        ]}
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write train.jsonl in HF messages format (system / user / assistant)
    train_path = out_dir / "train.jsonl"
    with open(train_path, "w", encoding="utf-8") as f:
        for rec in pairs:
            record = {
                "messages": [
                    {"role": "system", "content": rec.get("system", "")},
                    {
                        "role": "user",
                        "content": rec.get("user", rec.get("instruction", "")),
                    },
                    {
                        "role": "assistant",
                        "content": rec.get("assistant", rec.get("output", "")),
                    },
                ]
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Write dataset_info.json
    info = {
        "dataset_name": "terminal-depths-commands",
        "description": (
            "Instruction-following pairs derived from Terminal Depths game sessions. "
            "Each example shows player command sequences and game command semantics."
        ),
        "version": "1.0.0",
        "license": "cc-by-4.0",
        "features": {
            "messages": {
                "dtype": "list",
                "feature": {
                    "content": {"dtype": "string"},
                    "role": {"dtype": "string", "names": ["user", "assistant"]},
                },
            }
        },
        "splits": {"train": {"name": "train", "num_examples": len(pairs)}},
        "download_size": train_path.stat().st_size if train_path.exists() else 0,
    }
    info_path = out_dir / "dataset_info.json"
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)

    return train_path


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _report(events: list[dict[str, Any]], pairs: list[dict[str, str]]) -> None:
    print("\n" + "=" * 60)
    print("  FINETUNE PIPELINE REPORT")
    print("=" * 60)

    cmd_list = [e.get("cmd", "").strip().split()[0] for e in events if e.get("cmd")]
    cmd_list = [c for c in cmd_list if c]
    counter = Counter(cmd_list)

    unique_sessions = len({e.get("session_id") for e in events if e.get("session_id")})
    n_type_a = sum(1 for p in pairs if "sequence" not in p.get("user", ""))
    n_type_c = sum(1 for p in pairs if "sequence" in p.get("user", ""))

    print(f"\n  Raw command events : {len(events)}")
    print(f"  Unique sessions    : {unique_sessions}")
    print(f"  Training records   : {len(pairs)}")
    print(f"    Next-cmd + desc  : {n_type_a}")
    print(f"    Sequence predict : {n_type_c}")
    print(f"  Unique commands    : {len(counter)}")

    print("\n  Top-10 most common commands:")
    for cmd, count in counter.most_common(10):
        bar = "█" * min(count, 30)
        print(f"    {cmd:25s} {bar}  ({count})")

    print(f"\n  Output file: {_OUT_PATH}")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Ollama sample inference
# ---------------------------------------------------------------------------


def _ollama_sample_inference(pair: dict[str, str]) -> None:
    """POST a sample pair to Ollama as a chat message and print the response."""
    user_content = pair.get("user", pair.get("instruction", ""))
    system_content = pair.get("system", "")
    expected = pair.get("assistant", pair.get("output", ""))
    payload = json.dumps(
        {
            "model": _OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "options": {"num_predict": 60, "temperature": 0.3},
        }
    ).encode("utf-8")

    print("\n  [OLLAMA SAMPLE INFERENCE]")
    print(f"  Model  : {_OLLAMA_MODEL}")
    print(f"  User   : {user_content}")
    print(f"  Expected output: {expected}")

    try:
        req = urllib.request.Request(
            f"{_OLLAMA_URL}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            model_response = data.get("response", "").strip()
            print(f"  Model output   : {model_response}")
            print(f"  Tokens used    : {data.get('eval_count', '?')}")
    except urllib.error.URLError as exc:
        print(f"  [WARN] Ollama not reachable: {exc}. Skipping inference test.")
    except Exception as exc:
        print(f"  [WARN] Inference error: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Terminal Depths fine-tuning dataset builder."
    )
    parser.add_argument(
        "--test-inference",
        action="store_true",
        help="Send a sample pair to Ollama for inference validation.",
    )
    parser.add_argument(
        "--db",
        default=str(_DB_PATH),
        help=f"Path to feature_store.db (default: {_DB_PATH})",
    )
    parser.add_argument(
        "--out",
        default=str(_OUT_PATH),
        help=f"Output JSONL path (default: {_OUT_PATH})",
    )
    parser.add_argument(
        "--format",
        choices=["jsonl", "huggingface"],
        default="jsonl",
        dest="fmt",
        help="Output format: 'jsonl' (default) or 'huggingface' (HF datasets chat format).",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    out_path = Path(args.out)

    # Load real events only — no mock fallback
    events: list[dict[str, Any]] = []
    profiles: dict[str, dict[str, Any]] = {}
    if db_path.exists():
        try:
            events = _load_all_events(db_path)
            profiles = _load_player_profiles(db_path)
            cmd_events = [
                e for e in events if e.get("event_type") == "command" or "cmd" in e
            ]
            if not cmd_events:
                print(
                    "  [INFO] DB found but no command events yet. Play some game sessions first."
                )
                events = []
        except Exception as exc:
            print(f"  [WARN] DB read error: {exc}. No training data available.")
            events = []
    else:
        print(
            f"  [INFO] {db_path} not found. Run the game server to generate real event data."
        )

    if profiles:
        print(
            f"  [INFO] Loaded {len(profiles)} player profile(s) for context enrichment."
        )

    # Build training records (system/user/assistant triples)
    pairs = _build_instruction_pairs(events, profiles=profiles)

    if not pairs:
        print(
            "  [WARN] No instruction pairs generated — creating empty dataset with header."
        )
        # T9.4: zero-data path — write an empty output file with metadata comment
        if args.fmt == "huggingface":
            _hf_dir = out_path.parent / "finetune_hf"
            _export_huggingface([], _hf_dir)
            print(f"  [INFO] Empty HuggingFace dataset written to {_hf_dir}/")
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as _f:
                _f.write(
                    "# Terminal Depths fine-tuning dataset — no events recorded yet.\n"
                )
                _f.write("# Run game sessions to accumulate real command event data.\n")
            print(f"  [INFO] Empty dataset stub written to {out_path}")
        return

    # Export
    if args.fmt == "huggingface":
        _hf_dir = out_path.parent / "finetune_hf"
        train_path = _export_huggingface(pairs, _hf_dir)
        print(f"  [INFO] HuggingFace format exported → {_hf_dir}/")
        print(f"         train.jsonl  : {train_path}")
        print(f"         dataset_info : {_hf_dir / 'dataset_info.json'}")
    else:
        _export_jsonl(pairs, out_path)

    # Report
    cmd_events_for_report = [
        e for e in events if e.get("event_type") == "command" or "cmd" in e
    ]
    _report(cmd_events_for_report, pairs)

    # Optional inference test
    if args.test_inference and pairs:
        # Pick a pair with a recognisable command for a cleaner demo
        sample = next(
            (
                p
                for p in pairs
                if "scan" in p.get("user", "") or "exploit" in p.get("user", "")
            ),
            pairs[0],
        )
        _ollama_sample_inference(sample)


if __name__ == "__main__":
    main()

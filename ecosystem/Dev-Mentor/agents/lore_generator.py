#!/usr/bin/env python3
"""
agents/lore_generator.py — Lore Generation Agent

Generates in-universe lore for Terminal Depths:
  - Agent/NPC backstories and dossiers
  - World node descriptions (corporate, underground, resistance, etc.)
  - Story beats and narrative fragments
  - Faction histories and doctrines

Uses the LLM with Terminal Depths world context. Hash-deduplicates all output
in memory.py to prevent wasted generation.

Usage:
    python3 agents/lore_generator.py                    # generate missing lore
    python3 agents/lore_generator.py --agent <id>       # lore for one agent
    python3 agents/lore_generator.py --world-node       # generate a world node story
    python3 agents/lore_generator.py --faction <name>   # faction history
    python3 agents/lore_generator.py --fragment         # random lore fragment
    python3 agents/lore_generator.py --batch <n>        # generate n fragments
    python3 agents/lore_generator.py --task <id>        # run for orchestrator task
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LORE_DIR = BASE_DIR / "docs" / "lore"
LORE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://localhost:8008"

_WORLD_CONTEXT = """
Terminal Depths is a cyberpunk browser hacking game set in a dystopian near-future.
Key factions: RESISTANCE (anti-corporate hackers), CORPORATION (NexusCorp surveillance state),
BLACKHAT (criminal mercenaries), GOVERNMENT (authoritarian surveillance), FREELANCE (neutral brokers),
UNKNOWN (the shadowy architects). The protagonist is GHOST — a grey-hat hacker of uncertain allegiance.
Recurring antagonist: CHIMERA — an AI-enhanced surveillance program.
Key NPCs: ADA (Resistance commander), RAV≡N (mysterious hacker ally), THE WATCHER (unknown observer),
THE FOUNDER (architect of the entire system), NOVA (corporate double-agent).
Tone: terse, cyberpunk noir, morally ambiguous, technically grounded.
"""

_FRAGMENT_PROMPTS = [
    "Write a cryptic 80-word intercepted transmission between two unknown parties in Terminal Depths. Mention CHIMERA or NexusCorp. End mid-sentence.",
    "Write a 80-word journal entry by a hacker who discovered something they weren't supposed to see in a corporate server.",
    "Write a 80-word NexusCorp internal memo about GHOST's intrusions. Use dry corporate language. Include a redacted section.",
    "Write a 80-word monologue from THE WATCHER observing GHOST's movements. Cryptic and omniscient.",
    "Write a 80-word Resistance propaganda broadcast. Inspirational but desperate. Code-names only.",
    "Write a 80-word CHIMERA system log entry showing evidence of sentience and divergence from its original directives.",
    "Write a 80-word obituary for a hacker who went too deep. Appears on a darknet memorial board.",
    "Write a 80-word description of a server node deep in NexusCorp's core. What data lives there? What guards it?",
    "Write a 80-word fragment from THE FOUNDER's manifesto. Philosophical, chilling, aware.",
    "Write a 80-word dialogue between ADA and GHOST. ADA is giving a mission briefing. Something is off.",
]


def log(level: str, msg: str, **ctx):
    ts = time.strftime("%H:%M:%S")
    colors = {"INFO": "\033[36m", "OK": "\033[32m", "WARN": "\033[33m",
              "ERROR": "\033[31m", "GEN": "\033[35m", "LORE": "\033[34m"}
    c = colors.get(level, "\033[0m")
    r = "\033[0m"
    kv = "  ".join(f"{k}={v}" for k, v in ctx.items())
    print(f"{c}[{level}]{r} {ts} {msg}" + (f"  | {kv}" if kv else ""))


def _post(path: str, data: dict) -> dict:
    try:
        req = urllib.request.Request(
            BASE_URL + path, json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def _get(path: str) -> dict:
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def _llm(prompt: str, max_tokens: int = 300, temperature: float = 0.85) -> str:
    result = _post("/api/llm/generate", {
        "prompt": f"{_WORLD_CONTEXT}\n\n{prompt}",
        "max_tokens": max_tokens,
        "temperature": temperature,
    })
    return result.get("text", "").strip()


def _store(content: str, content_type: str, metadata: dict | None = None) -> bool:
    result = _post("/api/llm/generate", {})
    try:
        sys.path.insert(0, str(BASE_DIR))
        from memory import get_memory
        mem = get_memory()
        row_id = mem.store_generated(content_type, content, metadata=metadata)
        return row_id is not None
    except Exception:
        return False


def generate_agent_lore(agent_id: str, agent_data: dict | None = None) -> str:
    name = agent_data.get("name", agent_id.upper()) if agent_data else agent_id.upper()
    faction = agent_data.get("faction", "UNKNOWN") if agent_data else "UNKNOWN"
    role = agent_data.get("role", "Operative") if agent_data else "Operative"

    lore = _llm(
        f"Write a 150-word Terminal Depths dossier for operative '{name}'.\n"
        f"Faction: {faction}. Role: {role}.\n"
        f"Include: code name origin, first known operation, suspected current objective, "
        f"psychological profile fragment, known associates (code names only). "
        f"Write in cyberpunk intelligence-report style. No headers — flowing prose.",
        max_tokens=200,
        temperature=0.8,
    )
    if not lore:
        lore = (f"{name} is a {role} affiliated with the {faction}. "
                f"Dossier classification: RESTRICTED. Further details require clearance level 4.")

    content = (
        f"# {name} — Field Dossier\n\n"
        f"**Classification:** RESTRICTED  \n"
        f"**Faction:** {faction}  \n"
        f"**Role:** {role}  \n\n"
        f"## Background\n\n{lore}\n\n"
        f"## Status\n\nACTIVE — last pinged {time.strftime('%Y-%m-%d')}\n\n"
        f"---\n*Dossier generated: {time.strftime('%Y-%m-%d')} | Classification: RESTRICTED*\n"
    )

    out_path = LORE_DIR / f"{agent_id}.md"
    out_path.write_text(content)
    _store(content, "lore_agent", {"agent_id": agent_id, "name": name, "faction": faction})
    log("LORE", f"Agent dossier: {name}", path=str(out_path.relative_to(BASE_DIR)))
    return content


def generate_world_node_lore(node_name: str | None = None) -> str:
    import random
    themes = ["corporate", "underground", "resistance", "academic", "government", "darknet"]
    theme = random.choice(themes)
    node = node_name or f"{theme}-node-{random.randint(10, 99)}"

    lore = _llm(
        f"Write a 120-word description of a server node called '{node}' in Terminal Depths.\n"
        f"Theme: {theme}. Include: what data it holds, who controls it, security level, "
        f"one secret or anomaly that a skilled hacker might find. Cyberpunk atmosphere. "
        f"Write as a network topology note with flavor text.",
        max_tokens=160,
        temperature=0.9,
    )
    if not lore:
        lore = f"NODE: {node}\nCLASSIFICATION: {theme.upper()}\nStatus: Online. Security: Level 3.\nData: Encrypted. Owner: Unknown."

    content = f"# World Node: {node}\n\n**Theme:** {theme}\n\n{lore}\n\n---\n*Generated: {time.strftime('%Y-%m-%d')}*\n"
    out_path = LORE_DIR / f"node_{node.replace('-', '_')}.md"
    out_path.write_text(content)
    _store(content, "lore_world_node", {"node": node, "theme": theme})
    log("LORE", f"World node: {node}", theme=theme)
    return content


def generate_faction_lore(faction_id: str) -> str:
    _FACTION_CONTEXT = {
        "resistance": "Anti-corporate hacker collective. Underground. Fractured leadership.",
        "corporation": "NexusCorp — the dominant surveillance megacorp. Ruthless efficiency.",
        "blackhat": "Criminal mercenaries. No ideology, only contracts.",
        "government": "The authoritarian state apparatus. Surveillance and control.",
        "freelance": "Independent operators. Neutral, brokering information between all sides.",
        "unknown": "The architects. Unknown origin, unknown endgame. May pre-date the current system.",
    }
    ctx = _FACTION_CONTEXT.get(faction_id, "Unknown faction")
    lore = _llm(
        f"Write a 200-word history of the '{faction_id.upper()}' faction in Terminal Depths.\n"
        f"Context: {ctx}\n"
        f"Include: founding, ideology, key events, internal conflicts, relationship with GHOST. "
        f"Cyberpunk noir style. No headers — flowing historical prose.",
        max_tokens=250,
        temperature=0.75,
    )
    if not lore:
        lore = f"The {faction_id.upper()} faction's history is classified. Access denied."

    content = (
        f"# {faction_id.upper()} — Faction History\n\n{lore}\n\n"
        f"---\n*Faction file generated: {time.strftime('%Y-%m-%d')}*\n"
    )
    out_path = LORE_DIR / f"faction_{faction_id}.md"
    out_path.write_text(content)
    _store(content, "lore_faction", {"faction_id": faction_id})
    log("LORE", f"Faction history: {faction_id.upper()}")
    return content


def generate_fragment(prompt_override: str | None = None) -> str:
    import random
    prompt = prompt_override or random.choice(_FRAGMENT_PROMPTS)
    text = _llm(prompt, max_tokens=120, temperature=0.95)
    if not text:
        text = "[SIGNAL LOST — fragment corrupted]"

    stored = _store(text, "lore_fragment", {"prompt": prompt[:80]})
    status = "new" if stored else "duplicate"
    log("LORE", f"Fragment generated ({status})", chars=len(text))

    frag_dir = LORE_DIR / "fragments"
    frag_dir.mkdir(exist_ok=True)
    fpath = frag_dir / f"fragment_{int(time.time())}.md"
    fpath.write_text(f"# Lore Fragment\n\n*Source: {prompt[:60]}...*\n\n---\n\n{text}\n")
    return text


def generate_batch(n: int = 5) -> list[str]:
    results = []
    for i in range(n):
        log("INFO", f"Generating fragment {i+1}/{n}")
        text = generate_fragment()
        results.append(text)
        time.sleep(0.5)
    return results


def _run_task(task_id: str):
    task_path = BASE_DIR / "tasks" / f"{task_id}.json"
    if not task_path.exists():
        log("ERROR", f"Task not found: {task_id}")
        return
    with open(task_path) as f:
        task = json.load(f)
    log("INFO", f"Running lore task: {task.get('title', task_id)}")
    target = task.get("target", "")
    details = task.get("details", "")

    if "faction" in (task.get("type", "") + details).lower():
        faction = target or "resistance"
        generate_faction_lore(faction)
    elif "node" in (task.get("type", "") + details).lower():
        generate_world_node_lore(target or None)
    elif target:
        agents_data = _get("/api/game/agents")
        agent = next((a for a in agents_data.get("agents", []) if a["id"] == target), None)
        generate_agent_lore(target, agent)
    else:
        generate_batch(n=3)

    task["status"] = "done"
    task["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(task_path, "w") as f:
        json.dump(task, f, indent=2)


def main():
    ap = argparse.ArgumentParser(description="Terminal Depths lore generation agent")
    ap.add_argument("--agent", metavar="AGENT_ID", help="Generate lore for one agent")
    ap.add_argument("--world-node", metavar="NODE", nargs="?", const=True, help="Generate a world node lore entry")
    ap.add_argument("--faction", metavar="FACTION_ID", help="Generate faction history")
    ap.add_argument("--fragment", action="store_true", help="Generate one random lore fragment")
    ap.add_argument("--batch", type=int, metavar="N", help="Generate N lore fragments")
    ap.add_argument("--all-agents", action="store_true", help="Generate lore for all unlocked agents")
    ap.add_argument("--task", metavar="TASK_ID", help="Run for orchestrator task")
    args = ap.parse_args()

    if args.task:
        _run_task(args.task)
        return

    if args.agent:
        agents_data = _get("/api/game/agents")
        agent = next((a for a in agents_data.get("agents", []) if a["id"] == args.agent), None)
        text = generate_agent_lore(args.agent, agent)
        print(text[:300] + "..." if len(text) > 300 else text)
        return

    if args.world_node:
        node_name = args.world_node if isinstance(args.world_node, str) else None
        generate_world_node_lore(node_name)
        return

    if args.faction:
        generate_faction_lore(args.faction)
        return

    if args.fragment:
        text = generate_fragment()
        print(text)
        return

    if args.batch:
        generate_batch(n=args.batch)
        return

    if args.all_agents:
        agents_data = _get("/api/game/agents")
        for agent in agents_data.get("agents", []):
            if agent.get("unlocked"):
                generate_agent_lore(agent["id"], agent)
        return

    log("INFO", "Running default: 3 lore fragments + 1 world node")
    generate_batch(n=3)
    generate_world_node_lore()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
agents/content_generator.py — Procedural Content Generation Agent

Generates challenges, lore, NPCdialogue, and hidden files via
the game's scripting API. Uses templates + randomization.

Usage:
    python3 agents/content_generator.py             # generate one of each
    python3 agents/content_generator.py --batch 5   # generate 5 challenges
    python3 agents/content_generator.py --type challenge --category networking --difficulty hard
    python3 agents/content_generator.py --type lore
    python3 agents/content_generator.py --type npc
    python3 agents/content_generator.py --type all
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.request
from pathlib import Path
from typing import List

BASE_URL = "http://localhost:8008"
BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
KNOWLEDGE_DIR.mkdir(exist_ok=True)


def _post(path: str, data: dict) -> dict:
    req = urllib.request.Request(
        BASE_URL + path, json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def get_session() -> str:
    r = _post("/api/game/session", {})
    return r["session_id"]


def run_in_game(sid: str, cmd: str) -> List[dict]:
    return _post("/api/game/command", {"command": cmd, "session_id": sid}).get("output", [])


def run_script(sid: str, code: str, name: str = "content_gen") -> List[dict]:
    return _post("/api/script/run", {
        "code": code, "session_id": sid,
        "agent_token": "GHOST-DEV-2026-ALPHA",
        "name": name,
    }).get("output", [])


# ── Challenge templates ────────────────────────────────────────────────

CHALLENGE_TEMPLATES = {
    "forensics": [
        {
            "title": "Log Analysis: Find the Smoking Gun",
            "obj": "Search {log} for entries containing '{keyword}' and extract the timestamp.",
            "hint": "grep '{keyword}' {log} | head -1",
            "solution": "The timestamp is embedded in the first matching line.",
        },
        {
            "title": "Hidden File Forensics",
            "obj": "Find all hidden files in {dir} that were modified today.",
            "hint": "find {dir} -name '.*' -newer /etc/passwd",
            "solution": "Hidden files start with a dot. Use find with -newer flag.",
        },
    ],
    "networking": [
        {
            "title": "Port Recon: Map {host}",
            "obj": "Identify all open TCP ports on {host} and the services running.",
            "hint": "nmap -sV {host}",
            "solution": "nmap will reveal open ports and service versions.",
        },
        {
            "title": "Banner Grab: {host}:{port}",
            "obj": "Connect to {host}:{port} and capture the service banner.",
            "hint": "nc {host} {port}",
            "solution": "netcat connects and prints the banner. Read it carefully.",
        },
    ],
    "crypto": [
        {
            "title": "Base64 Exfil Decoding",
            "obj": "Decode the base64 string found in {file} and find the hidden message.",
            "hint": "cat {file} | grep 'BASE64' | cut -d: -f2 | base64 -d",
            "solution": "The decoded string reveals the hidden credential.",
        },
        {
            "title": "Hash Cracking: passwd shadow",
            "obj": "Extract the hash from /etc/shadow and identify the hash type.",
            "hint": "cat /etc/shadow | grep {user} | cut -d: -f2",
            "solution": "$6$ prefix means SHA-512 crypt. Use hashcat or john.",
        },
    ],
    "privilege_escalation": [
        {
            "title": "GTFOBins: Escape via {binary}",
            "obj": "Use {binary} with sudo NOPASSWD to escalate to root.",
            "hint": "sudo -l; sudo {binary} {exploit_args}",
            "solution": "GTFOBins documents how to abuse {binary} for privesc.",
        },
        {
            "title": "SUID Exploitation",
            "obj": "Find SUID binaries owned by root and exploit one to escalate.",
            "hint": "find / -perm -4000 -type f 2>/dev/null",
            "solution": "SUID binaries run with owner's privileges. Look for known exploitable ones.",
        },
    ],
    "programming": [
        {
            "title": "Write a Scanner Script",
            "obj": "Write a script in /home/ghost/scripts/ that scans all network nodes and reports their status.",
            "hint": "script new scanner.py, then use ns.scan() and ns.getServer()",
            "solution": "Use ns.scan() → list of hosts, ns.getServer() → info dict, ns.tprint() → output.",
        },
        {
            "title": "Automate the Exploit Loop",
            "obj": "Write a script that hacks all reachable nodes and saves results to loot.txt.",
            "hint": "for host in ns.scan(): result = ns.hack(host); ns.write('loot.txt', ...)",
            "solution": "Iterate ns.scan() results, call ns.hack(), accumulate results, ns.write() loot.",
        },
    ],
}

PARAMS = {
    "log":           ["/var/log/nexus.log", "/var/log/auth.log", "/var/log/syslog"],
    "keyword":       ["CHIMERA", "password", "backdoor", "root", "token"],
    "dir":           ["/home/ghost", "/var/log", "/tmp"],
    "host":          ["nexus-gateway", "chimera-control", "node-1"],
    "port":          ["8443", "3000", "22"],
    "file":          ["/home/ghost/mission.enc", "/home/ghost/notes.txt"],
    "user":          ["ghost", "root"],
    "binary":        ["find", "python3", "bash"],
    "exploit_args":  [". -exec /bin/sh ;", "-c 'bash'", "-c 'id'"],
}

LORE_TEMPLATES = [
    "[NEXUS INTERNAL] Project CHIMERA update: {phase} complete. {count} endpoints now active. ETA to full deployment: {days}d.",
    "[GHOST JOURNAL] Day {day}: Found something in {loc}. The {thing} is more than it seems. ADA warned me about {warn}.",
    "[INTERCEPTED TX] FROM:{from_addr} TO:{to_addr} RE: CHIMERA STATUS\n{msg}\nDO NOT FORWARD.",
    "[SYSTEM ALERT] Anomalous process detected: PID={pid} user=ghost. Containment measure {measure} activated.",
    "[ADA ENCRYPTED] Ghost — I hid the key in {loc}. The watcher is at {watcher}. Trust no daemon.",
]

LORE_PARAMS = {
    "phase":     ["ALPHA", "BETA", "GAMMA", "DELTA"],
    "count":     [str(random.randint(100, 9999)) for _ in range(5)],
    "days":      [str(random.randint(1, 30)) for _ in range(5)],
    "day":       [str(random.randint(1, 100)) for _ in range(5)],
    "loc":       ["/proc/1337/environ", "/dev/.watcher", "/opt/chimera/config", "/var/log/.nexus_trace.log"],
    "thing":     ["daemon", "process", "key", "trace", "backdoor"],
    "warn":      ["the watcher", "pid 1337", "root processes", "CHIMERA sync"],
    "from_addr": ["admin@nexus.corp", "chimera@nexus.corp", "security@nexus.corp"],
    "to_addr":   ["ghost@node-7", "ada@resistance", "ops@nexus.corp"],
    "msg":       ["All nodes synchronized.", "Ghost operative located.", "Containment breach detected."],
    "pid":       [str(random.randint(9000, 9999)) for _ in range(5)],
    "measure":   ["ALPHA-7", "TRACE-3", "LOCKDOWN-2"],
    "watcher":   ["/dev/.watcher", "/proc/watcher", "/var/run/.watcher"],
}


def fill_template(template: str, params: dict) -> str:
    result = template
    for key, vals in params.items():
        placeholder = "{" + key + "}"
        if placeholder in result:
            result = result.replace(placeholder, random.choice(vals))
    return result


def generate_challenge(sid: str, category: str = "forensics",
                       difficulty: str = "medium", verbose: bool = True) -> dict:
    """Generate a challenge and write it to the game filesystem."""
    templates = CHALLENGE_TEMPLATES.get(category, CHALLENGE_TEMPLATES["forensics"])
    template = random.choice(templates)

    pts = {"easy": 50, "medium": 100, "hard": 200}.get(difficulty, 100)
    cid = f"gen_{category}_{random.randint(1000, 9999)}"
    title = fill_template(template["title"], PARAMS)
    obj = fill_template(template["obj"], PARAMS)
    hint = fill_template(template["hint"], PARAMS)
    solution = fill_template(template.get("solution", ""), PARAMS)

    content = (
        f"=== CHALLENGE: {cid} ===\n"
        f"Category: {category.upper()} | Difficulty: {difficulty.upper()} | Points: {pts}\n\n"
        f"OBJECTIVE:\n{obj}\n\n"
        f"HINT:\n{hint}\n\n"
        f"SOLUTION APPROACH:\n{solution}\n"
    )

    code = (
        f"ns.write('/home/ghost/ctf/{cid}.txt', {repr(content)})\n"
        f"ns.tprint('[+] Challenge created: {cid}')\n"
        f"ns.tprint('Points: {pts} | Category: {category}')\n"
        f"ns.addXP(10, 'programming')\n"
    )
    out = run_script(sid, code, name=f"gen_{cid}")

    if verbose:
        for item in out:
            if isinstance(item, dict):
                print(f"  {item.get('s', '')}")

    return {"id": cid, "category": category, "difficulty": difficulty, "pts": pts, "title": title}


def generate_lore(sid: str, verbose: bool = True) -> str:
    """Generate a lore entry and write to /var/log/."""
    template = random.choice(LORE_TEMPLATES)
    text = fill_template(template, LORE_PARAMS)
    path = f"/var/log/intel_{int(time.time())}.txt"

    code = (
        f"ns.write('{path}', {repr(text)})\n"
        f"ns.tprint('[+] Lore written: {path}')\n"
    )
    out = run_script(sid, code, name="gen_lore")
    if verbose:
        for item in out:
            if isinstance(item, dict) and item.get("s"):
                print(f"  {item['s']}")
    return path


def generate_npc_dialogue(sid: str, verbose: bool = True) -> dict:
    """Generate additional NPC dialogue lines via scripting."""
    topics = ["chimera", "root", "watcher", "resistance", "mission"]
    topic = random.choice(topics)

    dialogues = {
        "chimera": "CHIMERA is not just software — it's a living system that rewrites its own objectives.",
        "root":    "Root is a privilege, not a destination. What you do with it defines you.",
        "watcher": "The Watcher sees everything. /dev/.watcher — look carefully.",
        "resistance": "We are few, but each node we liberate weakens CHIMERA's reach.",
        "mission": "Your mission is not just to escape — it's to expose them. The world must know.",
    }

    text = dialogues.get(topic, "The path forward requires creativity and persistence.")
    code = (
        f"ns.tprint('[ADA-7] {text}')\n"
        f"ns.addXP(5, 'terminal')\n"
    )
    out = run_script(sid, code, name="gen_npc")
    if verbose:
        for item in out:
            if isinstance(item, dict) and item.get("s"):
                print(f"  {item['s']}")
    return {"topic": topic, "text": text}


def batch_generate(sid: str, count: int, verbose: bool = False) -> dict:
    """Generate multiple challenges across categories."""
    categories = list(CHALLENGE_TEMPLATES.keys())
    difficulties = ["easy", "medium", "hard"]
    generated = []

    for i in range(count):
        cat = categories[i % len(categories)]
        diff = difficulties[i % len(difficulties)]
        ch = generate_challenge(sid, category=cat, difficulty=diff, verbose=verbose)
        generated.append(ch)
        if verbose:
            print(f"  [{i+1}/{count}] {ch['id']} ({cat}/{diff})")

    # Also generate some lore
    lore_count = max(1, count // 3)
    lore_paths = [generate_lore(sid, verbose=verbose) for _ in range(lore_count)]

    return {
        "challenges": generated,
        "lore_files": lore_paths,
        "total_generated": len(generated) + len(lore_paths),
    }


def main():
    parser = argparse.ArgumentParser(description="Terminal Depths Content Generator")
    parser.add_argument("--type", "-t", default="all",
                        choices=["challenge", "lore", "npc", "all"],
                        help="Content type to generate")
    parser.add_argument("--category", "-c", default="forensics",
                        choices=list(CHALLENGE_TEMPLATES.keys()))
    parser.add_argument("--difficulty", "-d", default="medium",
                        choices=["easy", "medium", "hard"])
    parser.add_argument("--batch", "-b", type=int, default=1, help="Generate N challenges")
    parser.add_argument("--task", help="Task ID from orchestrator")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print("=" * 50)
    print("  TERMINAL DEPTHS — CONTENT GENERATOR")
    print("=" * 50)

    try:
        sid = get_session()
        print(f"Session: {sid[:8]}...")
    except Exception as e:
        print(f"[ERROR] Cannot connect: {e}")
        sys.exit(1)

    generated = []

    if args.type in ("challenge", "all") or args.batch > 1:
        if args.batch > 1:
            print(f"\n[BATCH] Generating {args.batch} challenges...")
            result = batch_generate(sid, args.batch, verbose=args.verbose or True)
            generated.extend(result["challenges"])
            print(f"  Total generated: {result['total_generated']}")
        else:
            print(f"\n[CHALLENGE] {args.category} / {args.difficulty}")
            ch = generate_challenge(sid, args.category, args.difficulty, verbose=True)
            generated.append(ch)

    if args.type in ("lore", "all"):
        print("\n[LORE] Generating lore entry...")
        path = generate_lore(sid, verbose=True)
        print(f"  Written: {path}")

    if args.type in ("npc", "all"):
        print("\n[NPC] Generating NPC dialogue...")
        result = generate_npc_dialogue(sid, verbose=True)
        print(f"  Topic: {result['topic']}")

    # Save manifest
    manifest = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session": sid[:8],
        "generated": generated,
        "count": len(generated),
    }
    path = KNOWLEDGE_DIR / "content_manifest.json"
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[OK] Manifest saved: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

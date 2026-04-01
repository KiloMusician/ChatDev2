#!/usr/bin/env python3
"""
agents/challenge_generator.py — CTF Challenge Generation Agent

Generates new CTF challenges for Terminal Depths using the LLM.
Specialises in realistic hacking challenges across 8 categories:
  - web, crypto, pwn, forensics, reverse, osint, networking, steganography

Each challenge includes: title, description, category, XP value, flag format,
hints, solution approach, and story integration hooks.

Usage:
    python3 agents/challenge_generator.py                    # generate 3 challenges
    python3 agents/challenge_generator.py --category web     # specific category
    python3 agents/challenge_generator.py --batch <n>        # generate n challenges
    python3 agents/challenge_generator.py --difficulty <1-5> # set difficulty
    python3 agents/challenge_generator.py --audit            # show existing challenge gaps
    python3 agents/challenge_generator.py --validate         # validate all stored challenges
    python3 agents/challenge_generator.py --task <id>        # run for orchestrator task
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent.parent
CHALLENGES_DIR = BASE_DIR / "challenges"
CHALLENGES_DIR.mkdir(exist_ok=True)

BASE_URL = "http://localhost:8008"

CATEGORIES = ["web", "crypto", "pwn", "forensics", "reverse", "osint", "networking", "steganography"]

_WORLD_CONTEXT = """
Terminal Depths is a cyberpunk hacking game. Players are GHOST — a grey-hat operative.
Factions: RESISTANCE vs CORPORATION (NexusCorp) vs GOVERNMENT.
All challenges should feel like real operations in this world — not abstract puzzles.
"""

_CATEGORY_CONTEXT = {
    "web": "Web vulnerabilities: XSS, SQLi, IDOR, SSRF, authentication bypass, JWT manipulation.",
    "crypto": "Cryptography: Caesar cipher, XOR, RSA weak keys, hash cracking, steganographic encoding.",
    "pwn": "Binary exploitation: buffer overflow, format strings, ret2libc. In-game as 'exploiting a running process'.",
    "forensics": "Digital forensics: log analysis, file recovery, metadata extraction, memory dumps.",
    "reverse": "Reverse engineering: binary analysis, obfuscated scripts, bytecode, config files.",
    "osint": "Open-source intelligence: finding info from public data, social engineering, network enumeration.",
    "networking": "Network analysis: pcap files, port scans, protocol analysis, traffic interception.",
    "steganography": "Hidden data: images, audio files, text files with concealed messages.",
}


def log(level: str, msg: str, **ctx):
    ts = time.strftime("%H:%M:%S")
    colors = {"INFO": "\033[36m", "OK": "\033[32m", "WARN": "\033[33m",
              "ERROR": "\033[31m", "GEN": "\033[35m"}
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
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def _get(path: str) -> dict:
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=8) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def _llm(prompt: str, max_tokens: int = 500) -> str:
    result = _post("/api/llm/generate", {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0.75,
    })
    return result.get("text", "").strip()


def _store(content: dict) -> bool:
    try:
        sys.path.insert(0, str(BASE_DIR))
        from memory import get_memory
        mem = get_memory()
        row_id = mem.store_generated("challenge", json.dumps(content), metadata={
            "title": content.get("title", ""), "category": content.get("category", "")
        })
        return row_id is not None
    except Exception:
        return False


def _xp_for_difficulty(difficulty: int) -> int:
    return {1: 25, 2: 50, 3: 100, 4: 200, 5: 350}.get(difficulty, 50)


def _flag_for_category(category: str) -> str:
    codes = {
        "web": "TD{xss_nex_c0rp_0wned}",
        "crypto": "TD{c1ph3r_br0k3n_r3s1st4nc3}",
        "pwn": "TD{buff3r_0vfl0w_r00t3d}",
        "forensics": "TD{f0r3ns1cs_s1l3nt_w1tn3ss}",
        "reverse": "TD{r3v3rs3_3ng1n33r1ng_m4st3r}",
        "osint": "TD{0s1nt_d1g_d33p3r}",
        "networking": "TD{n3tw0rk_sn1ff3d_d4t4}",
        "steganography": "TD{h1dd3n_1n_pl41n_s1ght}",
    }
    return codes.get(category, "TD{flag_here}")


def generate_challenge(
    category: str | None = None,
    difficulty: int = 2,
    story_hook: str | None = None,
) -> dict | None:
    cat = category or random.choice(CATEGORIES)
    cat_ctx = _CATEGORY_CONTEXT.get(cat, "")
    xp = _xp_for_difficulty(difficulty)
    flag = _flag_for_category(cat)

    similar = []
    try:
        sys.path.insert(0, str(BASE_DIR))
        from memory import get_memory
        mem = get_memory()
        similar = mem.query_similar(f"{cat} challenge difficulty {difficulty}", "challenge", limit=3)
    except Exception:
        pass

    dedup_note = ""
    if similar:
        existing_titles = [json.loads(s["metadata"] or "{}").get("title", "?") for s in similar]
        dedup_note = f"\nAvoid similarity to these existing challenges: {', '.join(existing_titles[:3])}"

    hook = story_hook or random.choice([
        "NexusCorp has encrypted a data cache that the Resistance needs.",
        "A ghost operative left a dead drop in a compromised server.",
        "CHIMERA is using this technique to surveil dissidents.",
        "An informant's encrypted message was intercepted.",
        "You need this data to prove the Corporation's crimes.",
    ])

    prompt = f"""{_WORLD_CONTEXT}
Category context: {cat_ctx}

Generate a CTF challenge for Terminal Depths. Difficulty: {difficulty}/5. Category: {cat}.
Story hook: {hook}{dedup_note}

Output a JSON object with these exact fields:
{{
  "title": "Short punchy title (under 8 words)",
  "description": "2-3 sentences: scenario, what to do, Terminal Depths world context",
  "category": "{cat}",
  "difficulty": {difficulty},
  "xp": {xp},
  "flag": "{flag}",
  "hints": ["hint 1 (vague)", "hint 2 (more specific)"],
  "solution_approach": "1-2 sentences on how to solve it (not given to player)",
  "files_needed": ["optional list of files/tools needed, empty if none"],
  "story_tags": ["list of story_beat ids this could trigger, or empty"]
}}

Output ONLY the JSON object. No extra text."""

    text = _llm(prompt, max_tokens=450)

    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        log("WARN", f"LLM returned no JSON for {cat} challenge, using template")
        return _template_challenge(cat, difficulty, xp, flag, hook)

    try:
        challenge = json.loads(json_match.group())
    except json.JSONDecodeError:
        log("WARN", f"JSON parse failed for {cat} challenge, using template")
        return _template_challenge(cat, difficulty, xp, flag, hook)

    challenge.setdefault("category", cat)
    challenge.setdefault("difficulty", difficulty)
    challenge.setdefault("xp", xp)
    challenge.setdefault("flag", flag)

    return challenge


def _template_challenge(cat: str, difficulty: int, xp: int, flag: str, hook: str) -> dict:
    titles = {
        "web": "Inject the Truth",
        "crypto": "Cipher Protocol Alpha",
        "pwn": "Stack Overflow Resistance",
        "forensics": "Silent Witness",
        "reverse": "Black Box Decompile",
        "osint": "Digital Ghost Hunt",
        "networking": "Packet Intercept",
        "steganography": "Hidden in Plain Sight",
    }
    return {
        "title": titles.get(cat, f"{cat.title()} Challenge"),
        "description": f"{hook} Use your {cat} skills to find the flag.",
        "category": cat,
        "difficulty": difficulty,
        "xp": xp,
        "flag": flag,
        "hints": [f"Look for {cat} vulnerabilities.", "The answer is in the data."],
        "solution_approach": f"Standard {cat} exploitation technique.",
        "files_needed": [],
        "story_tags": [],
    }


def save_challenge(challenge: dict) -> Path:
    title_slug = re.sub(r"[^a-z0-9]+", "_", challenge.get("title", "challenge").lower()).strip("_")
    ts = int(time.time())
    fname = f"{title_slug}_{ts}.json"
    path = CHALLENGES_DIR / challenge.get("category", "misc") / fname
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(challenge, indent=2))
    return path


def audit() -> dict:
    existing: dict = {}
    total = 0
    for cat_dir in CHALLENGES_DIR.iterdir():
        if cat_dir.is_dir():
            count = len(list(cat_dir.glob("*.json")))
            existing[cat_dir.name] = count
            total += count

    missing = {cat: 0 for cat in CATEGORIES if cat not in existing or existing.get(cat, 0) == 0}
    light = {cat: existing[cat] for cat in CATEGORIES if 0 < existing.get(cat, 0) < 3}

    return {
        "total": total,
        "by_category": existing,
        "missing_categories": list(missing.keys()),
        "light_categories": light,
        "target_per_category": 10,
    }


def generate_batch(
    n: int = 3,
    category: str | None = None,
    difficulty: int = 2,
) -> list[dict]:
    results = []
    cats = [category] * n if category else [CATEGORIES[i % len(CATEGORIES)] for i in range(n)]

    for i, cat in enumerate(cats):
        log("GEN", f"Generating challenge {i+1}/{n}", category=cat, difficulty=difficulty)
        try:
            challenge = generate_challenge(cat, difficulty)
            if challenge:
                path = save_challenge(challenge)
                stored = _store(challenge)
                status = "new" if stored else "duplicate"
                log("OK", f"Generated: {challenge.get('title', '?')}", path=str(path.relative_to(BASE_DIR)), status=status)
                results.append(challenge)
        except Exception as e:
            log("ERROR", f"Failed to generate {cat} challenge: {e}")
        time.sleep(0.5)

    return results


def _run_task(task_id: str):
    task_path = BASE_DIR / "tasks" / f"{task_id}.json"
    if not task_path.exists():
        log("ERROR", f"Task not found: {task_id}")
        return
    with open(task_path) as f:
        task = json.load(f)
    details = task.get("details", "").lower()
    cat = task.get("target", "")
    for c in CATEGORIES:
        if c in details:
            cat = c
            break

    difficulty = 2
    for d in range(1, 6):
        if f"difficulty {d}" in details or f"level {d}" in details:
            difficulty = d
            break

    results = generate_batch(n=3, category=cat or None, difficulty=difficulty)
    task["status"] = "done"
    task["result"] = f"generated={len(results)} challenges"
    task["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(task_path, "w") as f:
        json.dump(task, f, indent=2)


def main():
    ap = argparse.ArgumentParser(description="CTF challenge generator")
    ap.add_argument("--category", choices=CATEGORIES, help="Challenge category")
    ap.add_argument("--difficulty", type=int, choices=range(1, 6), default=2, metavar="1-5")
    ap.add_argument("--batch", type=int, default=3, metavar="N", help="Number to generate")
    ap.add_argument("--audit", action="store_true", help="Show challenge coverage")
    ap.add_argument("--validate", action="store_true", help="Validate existing challenges")
    ap.add_argument("--task", metavar="TASK_ID", help="Run for orchestrator task")
    args = ap.parse_args()

    if args.task:
        _run_task(args.task)
        return

    if args.audit:
        report = audit()
        print(json.dumps(report, indent=2))
        if report["missing_categories"]:
            log("WARN", f"Missing categories: {report['missing_categories']}")
        return

    if args.validate:
        from agents.validator import Validator
        v = Validator()
        for cat_dir in CHALLENGES_DIR.iterdir():
            if cat_dir.is_dir():
                for jfile in cat_dir.glob("*.json"):
                    v.validate_file(jfile)
        v.print_summary()
        return

    results = generate_batch(n=args.batch, category=args.category, difficulty=args.difficulty)
    log("OK", f"Generated {len(results)} challenge(s)")


if __name__ == "__main__":
    main()

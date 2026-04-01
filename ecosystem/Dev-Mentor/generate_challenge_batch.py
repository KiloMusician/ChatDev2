"""
generate_challenge_batch.py — Procedural CTF challenge batch generator.

Generates challenges using the LLM, validates JSON structure, deduplicates
via memory, and outputs a JSON pool file.

Usage:
    python generate_challenge_batch.py                        # 10 challenges, all categories
    python generate_challenge_batch.py --count 50            # 50 challenges
    python generate_challenge_batch.py --category networking # single category
    python generate_challenge_batch.py --difficulty hard     # specific difficulty
    python generate_challenge_batch.py --pool                # show current pool size
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Optional

from memory import Memory, get_memory
from llm_client import LLMClient, Prompts


POOL_PATH = Path(".devmentor/challenge_pool.json")
POOL_PATH.parent.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    "networking", "linux", "cryptography", "web", "reverse_engineering",
    "forensics", "privilege_escalation", "steganography", "scripting", "misc",
]
DIFFICULTIES = ["easy", "medium", "hard", "expert"]


def _load_pool() -> list[dict]:
    if POOL_PATH.exists():
        try:
            return json.loads(POOL_PATH.read_text())
        except Exception:
            return []
    return []


def _save_pool(pool: list[dict]) -> None:
    POOL_PATH.write_text(json.dumps(pool, indent=2))


def _validate_challenge(ch: dict) -> bool:
    required = {"title", "description", "solution", "hint", "xp"}
    return all(k in ch for k in required) and isinstance(ch.get("xp"), (int, float))


def _generate_one(
    llm: LLMClient,
    category: str,
    difficulty: str,
    mem: Memory,
    existing_titles: set[str],
) -> Optional[dict]:
    prompt = (
        f"Generate a unique cybersecurity CTF challenge for a hacking terminal RPG.\n"
        f"Category: {category}\nDifficulty: {difficulty}\n"
        f"The challenge should be completable via terminal commands in the game world.\n"
        f"Return ONLY valid JSON with these exact keys:\n"
        f"  title (string, unique, creative)\n"
        f"  description (string, 2-3 sentences with context)\n"
        f"  solution (string, the terminal command or answer)\n"
        f"  hint (string, partial clue without giving it away)\n"
        f"  xp (integer, easy=25-50 medium=75-100 hard=150 expert=200-300)\n"
        f"  tags (array of strings)\n"
        f"No markdown, no extra text. Pure JSON only."
    )

    raw = llm.generate(prompt, max_tokens=300, temperature=0.85)

    # Strip markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        ch = json.loads(raw)
    except json.JSONDecodeError:
        # try to extract JSON from text
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                ch = json.loads(m.group())
            except Exception:
                return None
        else:
            return None

    if not _validate_challenge(ch):
        return None

    title = ch.get("title", "")
    if title in existing_titles:
        return None  # duplicate

    ch["category"] = category
    ch["difficulty"] = difficulty
    ch["xp"] = int(ch["xp"])
    ch.setdefault("tags", [category, difficulty])
    return ch


def run_batch(
    count: int = 10,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    quiet: bool = False,
) -> dict:
    mem = get_memory()
    llm = LLMClient()
    pool = _load_pool()
    existing_titles = {ch["title"] for ch in pool}

    generated = 0
    failed = 0
    t0 = time.time()

    cats = [category] if category else CATEGORIES
    diffs = [difficulty] if difficulty else DIFFICULTIES

    if not quiet:
        print(f"[batch] Generating {count} challenges…  pool={len(pool)}")

    import itertools, random
    combos = list(itertools.product(cats, diffs)) * (count // (len(cats) * len(diffs)) + 2)
    random.shuffle(combos)

    for cat, diff in combos:
        if generated >= count:
            break
        ch = _generate_one(llm, cat, diff, mem, existing_titles)
        if ch:
            pool.append(ch)
            existing_titles.add(ch["title"])
            # persist to memory
            mem.store_generated("challenge", json.dumps(ch), metadata={"category": cat, "difficulty": diff})
            generated += 1
            if not quiet:
                print(f"  [{generated}/{count}] {ch['title']} ({cat}/{diff}) +{ch['xp']}xp")
        else:
            failed += 1
            if failed > count * 2:
                break  # abort if too many failures

    _save_pool(pool)
    elapsed = round(time.time() - t0, 1)

    result = {
        "generated": generated,
        "failed": failed,
        "pool_total": len(pool),
        "elapsed_s": elapsed,
        "pool_path": str(POOL_PATH),
    }
    if not quiet:
        print(f"\n[batch] Done — generated={generated} failed={failed} pool={len(pool)} ({elapsed}s)")
    return result


if __name__ == "__main__":
    count = 10
    cat = None
    diff = None
    quiet = "--quiet" in sys.argv

    if "--pool" in sys.argv:
        pool = _load_pool()
        cats = {}
        for ch in pool:
            cats[ch.get("category","?")] = cats.get(ch.get("category","?"), 0) + 1
        print(f"Challenge pool: {len(pool)} total")
        for c, n in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {n:>4}  {c}")
        sys.exit(0)

    for i, arg in enumerate(sys.argv):
        if arg == "--count" and i + 1 < len(sys.argv):
            count = int(sys.argv[i + 1])
        if arg == "--category" and i + 1 < len(sys.argv):
            cat = sys.argv[i + 1]
        if arg == "--difficulty" and i + 1 < len(sys.argv):
            diff = sys.argv[i + 1]

    run_batch(count=count, category=cat, difficulty=diff, quiet=quiet)

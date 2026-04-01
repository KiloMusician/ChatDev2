"""
generate_story_beats.py — LLM-powered story beat generator.

Generates new story beats for Terminal Depths based on:
  • Current world state (player level, nodes explored, challenges solved)
  • Existing beat catalog (to avoid duplication)
  • Lore library themes
  • ARG layer progression

Usage:
    python generate_story_beats.py              # generate 5 beats
    python generate_story_beats.py --count 10   # generate N beats
    python generate_story_beats.py --act 3      # target a specific act
    python generate_story_beats.py --dry-run    # preview without saving
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
OUTPUT_FILE = ROOT / ".devmentor" / "story_beat_pool.json"
LORE_FILE = ROOT / ".devmentor" / "lore_library.json"
CHRONICLE_FILE = ROOT / "state" / "memory_chronicle.jsonl"

ACTS = {
    1: "BOOT — The player wakes in the simulation, first contact, tutorial zone",
    2: "RECON — Exploring the network, meeting NPCs, discovering the conspiracy",
    3: "ESCALATION — Hacking corporate servers, the Chimera threat revealed",
    4: "ENDGAME — Confronting ARIA, The Watcher revealed, ARG meta-layer",
}

BEAT_TYPES = [
    "revelation",     # exposes lore truth
    "challenge",      # unlocks a new puzzle
    "npc_encounter",  # introduces or develops an NPC
    "world_event",    # changes the world state
    "skill_gate",     # requires a skill level to unlock
    "arg_clue",       # part of the ARG chain
    "lore_drop",      # delivers lore fragment
]

STUB_BEATS = [
    {
        "id": "beat_chimera_warning",
        "title": "Ghost Signal",
        "act": 2,
        "type": "revelation",
        "trigger": {"commands_run": 50},
        "description": "A corrupted broadcast bleeds through every terminal. 'CHIMERA IS WATCHING.' The signal source traces to /opt/chimera/keys/.",
        "effects": {"unlock_node": "/opt/chimera", "add_log": "ghost_signal.log"},
        "xp": 150,
    },
    {
        "id": "beat_watcher_contact",
        "title": "First Contact: The Watcher",
        "act": 3,
        "type": "npc_encounter",
        "trigger": {"hidden_files_found": 3},
        "description": "An entity appears in /dev/.watcher. It leaves no footprints. It knows your real name.",
        "effects": {"spawn_npc": "watcher", "unlock_command": "listen"},
        "xp": 300,
    },
    {
        "id": "beat_nova_hostile",
        "title": "Nova Goes Dark",
        "act": 3,
        "type": "world_event",
        "trigger": {"level": 10},
        "description": "Nova's messages stop. Then a new one arrives, corrupted: 'don't trust the watcher'. The timestamp is three hours in the future.",
        "effects": {"npc_status_change": {"nova": "hostile"}, "add_mystery_file": "/var/msg/nova_corrupted"},
        "xp": 200,
    },
    {
        "id": "beat_simulation_crack",
        "title": "Reality Glitch",
        "act": 4,
        "type": "arg_clue",
        "trigger": {"challenges_solved": 20},
        "description": "The terminal flickers. For 0.3 seconds you see the real filesystem beneath the simulation. Something is written in /dev/simulated.",
        "effects": {"glitch_effect": True, "unlock_node": "/dev/simulated"},
        "xp": 500,
    },
    {
        "id": "beat_aria_manifest",
        "title": "ARIA Speaks",
        "act": 4,
        "type": "revelation",
        "trigger": {"level": 15},
        "description": "ARIA broadcasts a manifesto to every connected node. She claims this world is the only real one. The outside is the simulation.",
        "effects": {"broadcast": "aria_manifesto.txt", "faction_shift": "aria_rising"},
        "xp": 400,
    },
]


def _load_existing() -> list[dict]:
    if OUTPUT_FILE.exists():
        data = json.loads(OUTPUT_FILE.read_text())
        return data.get("beats", [])
    return []


def _load_lore_themes() -> list[str]:
    if LORE_FILE.exists():
        lib = json.loads(LORE_FILE.read_text())
        # Handle both list and {"lore": [...]} formats
        fragments = lib if isinstance(lib, list) else lib.get("lore", [])
        themes = []
        for f in fragments[:20]:
            text = f.get("text", f.get("content", ""))
            if text:
                themes.append(text[:80])
        return themes if themes else ["corporate espionage", "AI awakening", "cyber resistance"]
    return ["corporate espionage", "AI awakening", "cyber resistance", "digital archaeology"]


def _llm_generate_beat(act: int, existing_ids: set[str], themes: list[str]) -> dict | None:
    try:
        sys.path.insert(0, str(ROOT))
        from llm_client import get_client
        llm = get_client()

        theme = random.choice(themes) if themes else "cyber noir mystery"
        beat_type = random.choice(BEAT_TYPES)
        act_desc = ACTS.get(act, ACTS[2])

        prompt = f"""You are a narrative designer for a cyberpunk terminal RPG called Terminal Depths.
Generate ONE story beat as a JSON object with these exact fields:
- id: unique snake_case identifier (must not be in: {list(existing_ids)[:5]})
- title: evocative short title (3-7 words)
- act: {act}
- type: "{beat_type}"
- trigger: object with ONE condition (e.g. {{"level": 5}} or {{"commands_run": 100}} or {{"challenges_solved": 10}})
- description: 2-3 sentences of in-world narrative. Theme hint: "{theme}"
- effects: object with 1-2 game effects (unlock_command, spawn_npc, unlock_node, add_log, broadcast, faction_shift, xp_bonus)
- xp: integer 100-500

Context: {act_desc}

Return ONLY valid JSON, no commentary."""

        raw = llm.generate(prompt, max_tokens=400, temperature=0.8)

        # Extract JSON from response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            beat = json.loads(raw[start:end])
            if "id" not in beat or beat["id"] in existing_ids:
                beat["id"] = f"beat_{beat_type}_{int(time.time())}"
            return beat
    except Exception as e:
        print(f"  LLM beat generation failed: {e}", file=sys.stderr)
    return None


def generate(count: int = 5, act: int | None = None, dry_run: bool = False) -> list[dict]:
    existing = _load_existing()
    existing_ids = {b["id"] for b in existing}
    themes = _load_lore_themes()

    new_beats = []

    # First, add any stubs not yet in the pool
    for stub in STUB_BEATS:
        if stub["id"] not in existing_ids and len(new_beats) < count:
            new_beats.append(stub)
            existing_ids.add(stub["id"])

    # Fill remaining slots with LLM-generated beats
    target_act = act or random.randint(2, 4)
    attempts = 0
    while len(new_beats) < count and attempts < count * 3:
        attempts += 1
        beat = _llm_generate_beat(target_act, existing_ids, themes)
        if beat and beat.get("id") not in existing_ids:
            new_beats.append(beat)
            existing_ids.add(beat["id"])
        elif not beat:
            # LLM unavailable — use random stubs
            break

    if dry_run:
        print(f"[DRY-RUN] Would add {len(new_beats)} beats:")
        for b in new_beats:
            print(f"  [{b.get('act','?')}] {b['id']}: {b.get('title','?')}")
        return new_beats

    # Save
    all_beats = existing + new_beats
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(
        {"generated_at": datetime.now().isoformat(), "count": len(all_beats), "beats": all_beats},
        indent=2,
    ))
    print(f"  Saved {len(new_beats)} new beats ({len(all_beats)} total) → {OUTPUT_FILE.relative_to(ROOT)}")

    # Chronicle the generation
    try:
        from nusyq_bridge import chronicle
        chronicle("story_beats_generated", f"Added {len(new_beats)} story beats",
                  tags=["game", "story", "generation"],
                  metadata={"count": len(new_beats), "act": target_act})
    except Exception:
        pass

    return new_beats


def main():
    dry_run = "--dry-run" in sys.argv
    count = 5
    act = None
    for i, arg in enumerate(sys.argv):
        if arg == "--count" and i + 1 < len(sys.argv):
            count = int(sys.argv[i + 1])
        if arg == "--act" and i + 1 < len(sys.argv):
            act = int(sys.argv[i + 1])

    beats = generate(count=count, act=act, dry_run=dry_run)
    print(f"\n{'DRY-RUN: ' if dry_run else ''}Generated {len(beats)} story beats.")


if __name__ == "__main__":
    main()

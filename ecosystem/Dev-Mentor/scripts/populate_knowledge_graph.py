"""scripts/populate_knowledge_graph.py — Knowledge Graph Builder
=============================================================
Phase 1 of the Wisdom Integration Directive.

Reads YAML files from knowledge/games/ and knowledge/concepts/,
builds a unified knowledge_graph.json, and writes it to state/.

The graph has five top-level collections:
  games       — game metadata keyed by game_id
  techniques  — all techniques from all games (list)
  concepts    — all concepts with prerequisites and relationships
  relationships — (from, rel, to) triple store
  index       — inverted index: concept → [technique_id, ...]

Usage:
  python scripts/populate_knowledge_graph.py
  python scripts/populate_knowledge_graph.py --verify
  python scripts/populate_knowledge_graph.py --stats
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).parent.parent

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Loader helpers
# ─────────────────────────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  ⚠  Failed to parse {path.name}: {exc}", file=sys.stderr)
        return None


def _load_all_games() -> dict[str, dict]:
    games_dir = ROOT / "knowledge" / "games"
    games: dict[str, dict] = {}
    if not games_dir.exists():
        return games
    for yf in sorted(games_dir.glob("*.yaml")):
        data = _load_yaml(yf)
        if not data:
            continue
        gid = data.get("game_id") or yf.stem
        games[gid] = data
    return games


def _load_all_concepts() -> list[dict]:
    concepts_dir = ROOT / "knowledge" / "concepts"
    all_concepts: list[dict] = []
    if not concepts_dir.exists():
        return all_concepts
    for yf in sorted(concepts_dir.glob("*.yaml")):
        data = _load_yaml(yf)
        if not data:
            continue
        all_concepts.extend(data.get("concepts", []))
    return all_concepts


# ─────────────────────────────────────────────────────────────────────────────
# Graph builder
# ─────────────────────────────────────────────────────────────────────────────


def build_graph(games: dict[str, dict], concepts_raw: list[dict]) -> dict:
    graph_games: dict[str, dict] = {}
    all_techniques: list[dict] = []
    all_concepts: dict[str, dict] = {}
    relationships: list[dict] = []
    concept_index: dict[str, list[str]] = defaultdict(list)

    # ── Games ────────────────────────────────────────────────────────────────
    for gid, gdata in games.items():
        graph_games[gid] = {
            "id": gid,
            "name": gdata.get("game"),
            "description": str(gdata.get("description", "")).strip(),
            "category": gdata.get("category"),
            "difficulty": gdata.get("difficulty_range"),
            "relevance": gdata.get("terminal_depths_relevance"),
        }

        for tech in gdata.get("techniques", []):
            tid = tech.get("id") or f"{gid}_{len(all_techniques)}"
            technique = {
                "id": tid,
                "game": gid,
                "game_name": gdata.get("game"),
                "name": tech.get("name"),
                "description": str(tech.get("description", "")).strip(),
                "concepts": tech.get("concepts", []),
                "steps": tech.get("steps", []),
                "tips": tech.get("tips", []),
                "principles": tech.get("principles", []),
                "related": tech.get("related_techniques", []),
                "difficulty": tech.get("difficulty", "intermediate"),
                "xp_reward": tech.get("xp_reward", 25),
                "td_mapping": str(tech.get("terminal_depths_mapping", "")).strip(),
            }
            all_techniques.append(technique)

            # Relationships: technique → concepts
            for concept in tech.get("concepts", []):
                relationships.append(
                    {
                        "from": tid,
                        "rel": "APPLIES_TO",
                        "to": concept,
                    }
                )
                concept_index[concept].append(tid)

            # Relationships: game → technique
            relationships.append(
                {
                    "from": gid,
                    "rel": "CONTAINS",
                    "to": tid,
                }
            )

            # Relationships: technique → related techniques
            for related in tech.get("related_techniques", []):
                relationships.append(
                    {
                        "from": tid,
                        "rel": "RELATED_TO",
                        "to": related,
                    }
                )

    # ── Concepts ─────────────────────────────────────────────────────────────
    for c in concepts_raw:
        cid = c.get("id") or c.get("name", "").replace(" ", "_")
        cname = c.get("name", cid)
        all_concepts[cid] = {
            "id": cid,
            "name": cname,
            "description": str(c.get("description", "")).strip(),
            "prerequisites": c.get("prerequisites", []),
            "related": c.get("related", []),
            "difficulty": c.get("difficulty", "beginner"),
            "examples": c.get("examples", []),
        }
        # Prerequisite relationships
        for prereq in c.get("prerequisites", []):
            relationships.append(
                {
                    "from": cid,
                    "rel": "PREREQUISITE",
                    "to": prereq,
                }
            )

    # ── Lore fragments ────────────────────────────────────────────────────────
    lore_entries: list[dict] = []
    for gid, gdata in games.items():
        for fragment in gdata.get("lore", []):
            lore_entries.append(
                {
                    "game": gid,
                    "content": fragment,
                }
            )

    # ── Easter eggs ────────────────────────────────────────────────────────────
    easter_eggs: list[dict] = []
    for gid, gdata in games.items():
        for ee in gdata.get("easter_eggs", []):
            easter_eggs.append({**ee, "game": gid})

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "schema": "wisdom_integration_v1",
        "games": graph_games,
        "techniques": all_techniques,
        "concepts": all_concepts,
        "relationships": relationships,
        "concept_index": dict(concept_index),
        "lore": lore_entries,
        "easter_eggs": easter_eggs,
        "stats": {
            "games": len(graph_games),
            "techniques": len(all_techniques),
            "concepts": len(all_concepts),
            "relationships": len(relationships),
            "lore_fragments": len(lore_entries),
            "easter_eggs": len(easter_eggs),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Query helpers (used by wiki + hint in-game commands)
# ─────────────────────────────────────────────────────────────────────────────


def search_techniques(
    graph: dict,
    query: str,
    game_filter: str | None = None,
    difficulty: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Fuzzy keyword search over techniques. Returns top matches."""
    q = query.lower()
    scored = []
    for tech in graph.get("techniques", []):
        score = 0
        if q in tech.get("name", "").lower():
            score += 10
        if q in tech.get("description", "").lower():
            score += 5
        if any(q in c.lower() for c in tech.get("concepts", [])):
            score += 7
        if any(q in t.lower() for t in tech.get("tips", [])):
            score += 3
        if score > 0:
            if game_filter and tech.get("game") != game_filter:
                continue
            if difficulty and tech.get("difficulty") != difficulty:
                continue
            scored.append((score, tech))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:limit]]


def get_concept(graph: dict, concept_id: str) -> dict | None:
    """Look up a concept by id or name."""
    concepts = graph.get("concepts", {})
    if concept_id in concepts:
        return concepts[concept_id]
    # Fuzzy match by name
    cid_norm = concept_id.lower().replace(" ", "_")
    for cid, c in concepts.items():
        if cid.lower() == cid_norm or c.get("name", "").lower() == concept_id.lower():
            return c
    return None


def techniques_for_concept(graph: dict, concept_id: str) -> list[dict]:
    """Return all techniques that apply to a given concept."""
    idx = graph.get("concept_index", {})
    tid_list = idx.get(concept_id, [])
    tech_by_id = {t["id"]: t for t in graph.get("techniques", [])}
    return [tech_by_id[tid] for tid in tid_list if tid in tech_by_id]


def get_game_techniques(graph: dict, game_id: str) -> list[dict]:
    """Return all techniques for a game."""
    return [t for t in graph.get("techniques", []) if t.get("game") == game_id]


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def print_stats(graph: dict) -> None:
    s = graph["stats"]
    print("\n  Knowledge Graph — Build Report")
    print("  ══════════════════════════════")
    print(f"  Games:         {s['games']}")
    print(f"  Techniques:    {s['techniques']}")
    print(f"  Concepts:      {s['concepts']}")
    print(f"  Relationships: {s['relationships']}")
    print(f"  Lore fragments: {s['lore_fragments']}")
    print(f"  Easter eggs:   {s['easter_eggs']}")
    print()
    for gid, g in graph["games"].items():
        techs = len(get_game_techniques(graph, gid))
        print(f"  [{g['name']}] {techs} techniques — {g['relevance']} relevance")
    print()


def verify_graph(graph: dict) -> bool:
    errors = []
    tech_ids = {t["id"] for t in graph.get("techniques", [])}
    for rel in graph.get("relationships", []):
        from_id = rel["from"]
        to_id = rel["to"]
        # Only validate technique IDs — concepts/games use string keys
        if from_id not in tech_ids and from_id not in graph["games"]:
            if from_id not in graph["concepts"]:
                errors.append(f"  Dangling from: {from_id}")
    if errors:
        print("  Verification FAILED:")
        for e in errors[:10]:
            print(e)
        return False
    print(f"  ✅ Graph verified — {len(graph['relationships'])} relationships valid")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge Graph Builder")
    parser.add_argument("--stats", action="store_true", help="Print stats only")
    parser.add_argument("--verify", action="store_true", help="Verify existing graph")
    parser.add_argument(
        "--out",
        default=str(ROOT / "state" / "knowledge_graph.json"),
        help="Output path",
    )
    args = parser.parse_args()

    out_path = Path(args.out)

    if args.verify and out_path.exists():
        graph = json.loads(out_path.read_text())
        verify_graph(graph)
        return

    print("\n  Building Knowledge Graph...")
    games = _load_all_games()
    concepts = _load_all_concepts()

    print(f"  Loaded {len(games)} games, {len(concepts)} concept entries")

    graph = build_graph(games, concepts)

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False))
    print(f"  ✅ Written to {out_path.relative_to(ROOT)}")

    print_stats(graph)
    verify_graph(graph)


if __name__ == "__main__":
    main()

"""
Player Clustering — k-means in pure Python.

Groups player sessions into behavioural clusters based on:
  - Command frequency distribution
  - XP accumulation rate
  - Story beat density
  - Archetype scores (from feature_store)

No numpy/sklearn required. Pure stdlib math.

Msg⛛ tagging: [ML⛛{cluster}]

API:
  cluster_players(k)              → list of clusters with member sessions
  describe_cluster(cluster_id)    → human-readable cluster description
  get_session_cluster(session_id) → which cluster a session belongs to
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_DB_PATH = _ROOT / "state" / "feature_store.db"


# ── Feature extraction ────────────────────────────────────────────────────────

_EXPLORER_CMDS = {"ls", "cat", "help", "man", "info", "lore", "status", "map", "fragments", "diary"}
_FIGHTER_CMDS = {"attack", "duel", "hack", "exploit", "exfil", "breach", "signal", "scan"}
_SOCIAL_CMDS = {"talk", "trust", "msg", "bribe", "join", "party", "msgx"}
_BUILDER_CMDS = {"augment", "upgrade", "research", "colony", "build", "ml", "serena"}


def _extract_features(session_id: str, profile: Dict) -> List[float]:
    """Convert a player profile into a feature vector for clustering."""
    top_cmds = {cmd: count for cmd, count in profile.get("top_commands", [])}
    total = sum(top_cmds.values()) or 1

    explorer_score = sum(top_cmds.get(c, 0) for c in _EXPLORER_CMDS) / total
    fighter_score = sum(top_cmds.get(c, 0) for c in _FIGHTER_CMDS) / total
    social_score = sum(top_cmds.get(c, 0) for c in _SOCIAL_CMDS) / total
    builder_score = sum(top_cmds.get(c, 0) for c in _BUILDER_CMDS) / total

    cmds_run = min(profile.get("commands_run", 0) / 200, 1.0)
    xp = min(profile.get("xp_total", 0) / 10000, 1.0)
    beats = min(profile.get("beats_triggered", 0) / 50, 1.0)
    quests = min(profile.get("quests_done", 0) / 20, 1.0)

    return [explorer_score, fighter_score, social_score, builder_score,
            cmds_run, xp, beats, quests]


def _load_all_profiles() -> Dict[str, Tuple[Dict, List[float]]]:
    """Load all player profiles from feature_store."""
    if not _DB_PATH.exists():
        return {}
    try:
        con = sqlite3.connect(str(_DB_PATH))
        rows = con.execute("SELECT * FROM player_profiles").fetchall()
        cols = [d[0] for d in con.description] if rows else []
        con.close()
    except Exception:
        return {}

    profiles = {}
    for row in rows:
        p = dict(zip(cols, row))
        sid = p.get("session_id", "")
        if not sid:
            continue
        p["top_commands"] = json.loads(p.get("top_commands") or "[]")
        feats = _extract_features(sid, p)
        profiles[sid] = (p, feats)
    return profiles


# ── Pure Python k-means ───────────────────────────────────────────────────────

def _dist(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _centroid(vectors: List[List[float]]) -> List[float]:
    if not vectors:
        return [0.0] * 8
    n = len(vectors)
    return [sum(v[i] for v in vectors) / n for i in range(len(vectors[0]))]


def kmeans(
    data: Dict[str, List[float]],
    k: int = 4,
    max_iter: int = 50,
    seed: int = 42,
) -> Dict[int, List[str]]:
    """
    Pure Python k-means clustering.
    Returns {cluster_id: [session_ids]}.
    """
    if not data:
        return {}

    session_ids = list(data.keys())
    vectors = [data[s] for s in session_ids]
    dim = len(vectors[0]) if vectors else 8

    if len(vectors) <= k:
        return {i: [sid] for i, sid in enumerate(session_ids)}

    rng = random.Random(seed)
    centroids = [vectors[i] for i in rng.sample(range(len(vectors)), k)]

    assignments = [0] * len(vectors)
    for _ in range(max_iter):
        new_assignments = []
        for vec in vectors:
            dists = [_dist(vec, c) for c in centroids]
            new_assignments.append(dists.index(min(dists)))

        if new_assignments == assignments:
            break
        assignments = new_assignments

        for ci in range(k):
            members = [vectors[j] for j, a in enumerate(assignments) if a == ci]
            if members:
                centroids[ci] = _centroid(members)

    clusters: Dict[int, List[str]] = defaultdict(list)
    for j, cluster_id in enumerate(assignments):
        clusters[cluster_id].append(session_ids[j])
    return dict(clusters)


# ── Public API ─────────────────────────────────────────────────────────────────

def cluster_players(k: int = 4) -> List[Dict]:
    """
    Run k-means on all player profiles in the feature store.
    Returns list of clusters with member info and a description.
    """
    profiles = _load_all_profiles()
    if not profiles:
        return []

    feature_map = {sid: feats for sid, (_, feats) in profiles.items()}
    raw_clusters = kmeans(feature_map, k=min(k, len(feature_map)))

    result = []
    for cluster_id, members in raw_clusters.items():
        member_profiles = [profiles[sid][0] for sid in members if sid in profiles]
        member_feats = [profiles[sid][1] for sid in members if sid in profiles]
        centroid = _centroid(member_feats) if member_feats else [0.0] * 8

        labels = ["explorer", "fighter", "social", "builder",
                  "activity", "xp", "story", "quests"]
        centroid_dict = {labels[i]: round(centroid[i], 3) for i in range(len(labels))}

        dominant = max(centroid_dict.items(), key=lambda x: x[1])

        avg_cmds = sum(p.get("commands_run", 0) for p in member_profiles) / max(len(member_profiles), 1)
        avg_xp = sum(p.get("xp_total", 0) for p in member_profiles) / max(len(member_profiles), 1)

        archetype_labels = {
            "explorer": "Cartographers — prefer discovery over conflict",
            "fighter": "Breach Operators — seek combat and system intrusions",
            "social": "Network Weavers — build trust and alliances",
            "builder": "Architects — construct and optimize systems",
            "activity": "High-Volume Players — commands > depth",
            "xp": "XP Farmers — efficient progression",
            "story": "Lore Seekers — follow the narrative",
            "quests": "Quest Runners — mission-focused",
        }

        result.append({
            "cluster_id": cluster_id,
            "members": len(members),
            "session_ids": members,
            "centroid": centroid_dict,
            "dominant_trait": dominant[0],
            "description": archetype_labels.get(dominant[0], "Mixed playstyle"),
            "avg_commands": round(avg_cmds, 1),
            "avg_xp": round(avg_xp, 1),
        })

    result.sort(key=lambda x: -x["members"])
    return result


def get_session_cluster(session_id: str, k: int = 4) -> Optional[Dict]:
    """Return which cluster a specific session belongs to."""
    clusters = cluster_players(k)
    for c in clusters:
        if session_id in c.get("session_ids", []):
            return c
    return None


def clustering_stats() -> Dict:
    profiles = _load_all_profiles()
    return {
        "sessions_available": len(profiles),
        "msg_tag": "[ML⛛{cluster}]",
    }

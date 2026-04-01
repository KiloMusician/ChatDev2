"""
Terminal Depths — CTF Challenge System
Manages challenge library, presentation, and validation.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

CHALLENGES_DIR = Path(__file__).parent.parent.parent / "challenges" / "ctf"
POOL_PATH = Path(__file__).parent.parent.parent / ".devmentor" / "challenge_pool.json"


def _load_static_challenges() -> List[Dict]:
    """Load hand-authored challenges from challenges/ctf/*.json"""
    challenges = []
    if CHALLENGES_DIR.exists():
        for f in sorted(CHALLENGES_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                if isinstance(data, list):
                    challenges.extend(data)
            except Exception:
                pass
    return challenges


def _load_generated_challenges() -> List[Dict]:
    """Load LLM-generated challenges from the pool file."""
    if POOL_PATH.exists():
        try:
            data = json.loads(POOL_PATH.read_text())
            if isinstance(data, list):
                normalized = []
                for i, ch in enumerate(data):
                    if not ch.get("id"):
                        ch = dict(ch)
                        ch["id"] = f"gen_{i:04d}"
                    if not ch.get("category"):
                        ch["category"] = ch.get("tags", ["misc"])[0].capitalize() if ch.get("tags") else "misc"
                    normalized.append(ch)
                return normalized
        except Exception:
            pass
    return []


class ChallengeEngine:
    """Manages CTF challenges for a player session."""

    CATEGORIES = ["Web", "Crypto", "Forensics", "Reverse Engineering", "Network"]

    def __init__(self):
        self._static = _load_static_challenges()
        self._generated: List[Dict] = []
        self._reload_generated()
        # Rebuild CATEGORIES to include every category present in challenge data
        all_cats: list = []
        seen: set = set()
        for ch in self._static + self._generated:
            cat = ch.get("category", "")
            if cat and cat not in seen:
                all_cats.append(cat)
                seen.add(cat)
        if all_cats:
            self.CATEGORIES = all_cats

    def _reload_generated(self):
        self._generated = _load_generated_challenges()

    @property
    def all_challenges(self) -> List[Dict]:
        return self._static + self._generated

    def get_by_id(self, cid: str) -> Optional[Dict]:
        for ch in self.all_challenges:
            if ch.get("id") == cid:
                return ch
        return None

    def get_by_category(self, category: str) -> List[Dict]:
        cat_lower = category.lower()
        return [
            ch for ch in self.all_challenges
            if ch.get("category", "").lower() == cat_lower
            or ch.get("category", "").lower().replace(" ", "_") == cat_lower.replace(" ", "_")
        ]

    def get_random(self, category: Optional[str] = None, difficulty: Optional[str] = None,
                   exclude: set | None = None) -> Optional[Dict]:
        pool = self.all_challenges
        if category:
            pool = self.get_by_category(category)
        if difficulty:
            diff_lower = difficulty.lower()
            pool = [ch for ch in pool if ch.get("difficulty", "").lower() == diff_lower]
        if exclude:
            pool = [ch for ch in pool if ch.get("id") not in exclude]
        return random.choice(pool) if pool else None

    def validate_answer(self, challenge: Dict, answer: str) -> bool:
        """Check if the player's answer matches the expected solution."""
        def _norm(s: str) -> str:
            # Strip, collapse internal whitespace, lowercase
            return " ".join(s.strip().split()).lower()
        solution = str(challenge.get("solution", ""))
        return _norm(answer) == _norm(solution)

    def summary(self, completed: set) -> Dict[str, Any]:
        """Return challenge stats by category."""
        stats: Dict[str, Dict] = {}
        for ch in self.all_challenges:
            cat = ch.get("category", "misc")
            if cat not in stats:
                stats[cat] = {"total": 0, "completed": 0, "xp_available": 0}
            stats[cat]["total"] += 1
            stats[cat]["xp_available"] += ch.get("xp", 0)
            if ch.get("id") in completed:
                stats[cat]["completed"] += 1
        return stats


# Singleton for reuse across sessions
_engine_instance: Optional[ChallengeEngine] = None


def get_challenge_engine() -> ChallengeEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ChallengeEngine()
    return _engine_instance

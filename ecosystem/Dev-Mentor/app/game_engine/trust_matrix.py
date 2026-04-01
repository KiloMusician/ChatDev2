"""
Terminal Depths — Trust & Influence Matrix
Tracks per-session player-agent and agent-agent relationships.
"""
from __future__ import annotations
from typing import Dict, Tuple

# Default agent-agent relationships (alliance, rivalry, indifference)
# Values: "alliance", "rivalry", "indifference"
_DEFAULT_AGENT_RELATIONS: Dict[str, Dict[str, str]] = {
    "ada": {
        "nova": "rivalry",
        "cypher": "alliance",
        "echo": "alliance",
        "solon": "alliance",
        "raven": "alliance",
        "spartacus": "alliance",
        "mercury": "rivalry",
        "midas": "rivalry",
        "icarus": "alliance",
    },
    "nova": {
        "ada": "rivalry",
        "mercury": "alliance",
        "midas": "alliance",
        "nemesis": "alliance",
        "cypher": "rivalry",
        "croesus": "alliance",
    },
    "cypher": {
        "ada": "alliance",
        "mercury": "rivalry",
        "echo": "alliance",
        "blackhat": "indifference",
        "the_mole": "indifference",
    },
    "echo": {
        "ada": "alliance",
        "cypher": "alliance",
        "echo2": "rivalry",
        "hertz": "alliance",
    },
    "raven": {
        "ada": "alliance",
        "solon": "alliance",
        "whisper": "rivalry",
        "malice": "rivalry",
        "the_mole": "rivalry",
    },
    "solon": {
        "raven": "alliance",
        "ada": "alliance",
        "spartacus": "alliance",
        "mephisto": "rivalry",
    },
    "sparta": {
        "solon": "alliance",
        "ada": "alliance",
        "nemesis": "rivalry",
    },
    "malice": {
        "mercury": "alliance",
        "nemesis": "alliance",
        "ada": "rivalry",
        "raven": "rivalry",
        "lilith": "indifference",
    },
    "mercury": {
        "nova": "alliance",
        "cypher": "alliance",
        "midas": "alliance",
        "ada": "rivalry",
        "echo": "rivalry",
    },
    "midas": {
        "nova": "alliance",
        "mercury": "alliance",
        "croesus": "alliance",
        "ada": "rivalry",
        "the_founder": "rivalry",
    },
    "daedalus": {
        "prometheus": "alliance",
        "oracle": "alliance",
        "kronos": "alliance",
        "kairos": "alliance",
        "hertz": "alliance",
        "morpheus": "alliance",
        "sibyl": "alliance",
    },
    "prometheus": {
        "daedalus": "alliance",
        "ada": "alliance",
        "midas": "rivalry",
        "nova": "rivalry",
    },
    "the_watcher": {
        "scp_079": "alliance",
        "pythia": "alliance",
        "ananke": "alliance",
        "moirae": "alliance",
        "the_founder": "indifference",
    },
    "nemesis": {
        "nova": "alliance",
        "mercury": "alliance",
        "ghost_rival": "alliance",
        "ada": "rivalry",
    },
    "echo2": {
        "echo": "rivalry",
        "mercury": "alliance",
        "nova": "alliance",
    },
    "whisper": {
        "malice": "alliance",
        "nyx": "alliance",
        "raven": "rivalry",
        "ada": "indifference",
    },
    "lilith": {
        "nyx": "alliance",
        "malice": "indifference",
        "raven": "rivalry",
    },
    "hypatia": {
        "the_archivist": "alliance",
        "cipher_sc": "alliance",
        "the_lexicon": "rivalry",
    },
    "the_founder": {
        "raven": "alliance",
        "ada": "alliance",
        "midas": "rivalry",
        "the_watcher": "indifference",
        "the_admin": "alliance",
        "the_sleeper": "alliance",
    },
}


class TrustMatrix:
    """
    Tracks player↔agent trust scores and agent↔agent relationships.

    player_scores: {agent_id: {"trust": 0-100, "respect": 0-100, "fear": 0-100}}
    agent_relations: {agent_id: {agent_id: "alliance"|"rivalry"|"indifference"}}
    """

    def __init__(self, agents_data):
        # agents_data: list of agent dicts (from agents.py)
        self.player_scores: Dict[str, Dict[str, int]] = {}
        self.agent_relations: Dict[str, Dict[str, str]] = {}
        self._init_from_agents(agents_data)
        self._init_relations()

    def _init_from_agents(self, agents_data):
        for agent in agents_data:
            start = agent.get("trust_start", 20)
            self.player_scores[agent["id"]] = {
                "trust": start,
                "respect": max(0, start - 10),
                "fear": 0,
            }

    def _init_relations(self):
        for agent_id, relations in _DEFAULT_AGENT_RELATIONS.items():
            self.agent_relations[agent_id] = dict(relations)
        # Make symmetric where not already defined
        for agent_id, relations in list(self.agent_relations.items()):
            for other_id, rel_type in relations.items():
                if other_id not in self.agent_relations:
                    self.agent_relations[other_id] = {}
                if agent_id not in self.agent_relations[other_id]:
                    # Symmetric default
                    self.agent_relations[other_id][agent_id] = rel_type

    # ── Player score accessors ─────────────────────────────────────────

    def get_player_scores(self, agent_id: str) -> Dict[str, int]:
        if agent_id not in self.player_scores:
            self.player_scores[agent_id] = {"trust": 0, "respect": 0, "fear": 0}
        return self.player_scores[agent_id]

    def get_trust(self, agent_id: str) -> int:
        return self.get_player_scores(agent_id)["trust"]

    def get_respect(self, agent_id: str) -> int:
        return self.get_player_scores(agent_id)["respect"]

    def get_fear(self, agent_id: str) -> int:
        return self.get_player_scores(agent_id)["fear"]

    # ── Score modification ─────────────────────────────────────────────

    def modify_trust(self, agent_id: str, delta: int, reason: str = "") -> Dict[str, int]:
        scores = self.get_player_scores(agent_id)
        old_trust = scores["trust"]
        scores["trust"] = max(0, min(100, scores["trust"] + delta))
        # Respect follows trust directionally but more slowly
        if delta > 0:
            scores["respect"] = min(100, scores["respect"] + max(1, delta // 3))
        elif delta < 0:
            scores["respect"] = max(0, scores["respect"] + delta // 2)
        return {"agent": agent_id, "old_trust": old_trust, "new_trust": scores["trust"],
                "delta": scores["trust"] - old_trust, "reason": reason}

    def modify_respect(self, agent_id: str, delta: int, reason: str = "") -> Dict[str, int]:
        scores = self.get_player_scores(agent_id)
        old = scores["respect"]
        scores["respect"] = max(0, min(100, scores["respect"] + delta))
        return {"agent": agent_id, "old": old, "new": scores["respect"], "reason": reason}

    def modify_fear(self, agent_id: str, delta: int, reason: str = "") -> Dict[str, int]:
        scores = self.get_player_scores(agent_id)
        old = scores["fear"]
        scores["fear"] = max(0, min(100, scores["fear"] + delta))
        return {"agent": agent_id, "old": old, "new": scores["fear"], "reason": reason}

    def apply_action_effect(self, action: str, primary_agent: str | None = None):
        """
        Apply trust/respect/fear changes based on a player action.
        Actions: "talk", "helped_agent", "betrayed_agent", "exposed_mole",
                 "allied_corporation", "attacked_resistance", "completed_challenge",
                 "gained_root", "discovered_chimera"
        """
        changes = []
        if action == "gained_root":
            if primary_agent:
                changes.append(self.modify_respect(primary_agent, +10, "player gained root"))
            # Ada and Cypher respect root exploit
            changes.append(self.modify_trust("ada", +5, "root achieved"))
            changes.append(self.modify_trust("cypher", +5, "root achieved"))
            # Nova increases fear
            changes.append(self.modify_fear("nova", +15, "threat escalation"))

        elif action == "allied_corporation":
            # Resistance agents distrust player
            for aid in ["ada", "cypher", "raven", "solon", "echo", "spartacus"]:
                if aid in self.player_scores:
                    changes.append(self.modify_trust(aid, -10, "player allied with Corporation"))
            # Corporation agents trust player more
            for aid in ["nova", "mercury", "midas", "croesus"]:
                if aid in self.player_scores:
                    changes.append(self.modify_trust(aid, +10, "player allied with Corporation"))

        elif action == "betrayed_agent":
            if primary_agent:
                changes.append(self.modify_trust(primary_agent, -30, "player betrayed agent"))
                changes.append(self.modify_fear(primary_agent, +20, "player betrayed agent"))
                # Allies of the betrayed agent also lose trust
                allies = [k for k, v in self.agent_relations.get(primary_agent, {}).items()
                          if v == "alliance"]
                for ally in allies:
                    if ally in self.player_scores:
                        changes.append(self.modify_trust(ally, -10, f"ally {primary_agent} betrayed"))

        elif action == "helped_agent":
            if primary_agent:
                changes.append(self.modify_trust(primary_agent, +15, "player helped agent"))
                allies = [k for k, v in self.agent_relations.get(primary_agent, {}).items()
                          if v == "alliance"]
                for ally in allies:
                    if ally in self.player_scores:
                        changes.append(self.modify_trust(ally, +5, f"ally {primary_agent} helped"))

        elif action == "completed_challenge":
            for aid in ["ada", "daedalus", "prometheus", "the_critic"]:
                if aid in self.player_scores:
                    changes.append(self.modify_respect(aid, +5, "challenge completed"))

        elif action == "exposed_mole":
            # Resistance applauds, Shadow Council is furious
            for aid in ["ada", "raven", "solon", "echo"]:
                if aid in self.player_scores:
                    changes.append(self.modify_trust(aid, +20, "mole exposed"))
            for aid in ["malice", "whisper", "nyx"]:
                if aid in self.player_scores:
                    changes.append(self.modify_trust(aid, -25, "mole exposed"))
                    changes.append(self.modify_fear(aid, +30, "mole exposed"))

        return changes

    # ── Agent-agent relationships ─────────────────────────────────────

    def get_agent_relation(self, agent_a: str, agent_b: str) -> str:
        return self.agent_relations.get(agent_a, {}).get(agent_b, "indifference")

    def can_player_query_relation(self, agent_a: str, agent_b: str) -> bool:
        """Player can query a relationship only if they have trust >= 40 with both agents."""
        trust_a = self.get_trust(agent_a)
        trust_b = self.get_trust(agent_b)
        return trust_a >= 40 and trust_b >= 40

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "player_scores": {k: dict(v) for k, v in self.player_scores.items()},
            "agent_relations": {k: dict(v) for k, v in self.agent_relations.items()},
        }

    @classmethod
    def from_dict(cls, d: dict, agents_data) -> "TrustMatrix":
        tm = cls.__new__(cls)
        tm.player_scores = {}
        tm.agent_relations = {}
        # First init defaults
        tm._init_from_agents(agents_data)
        tm._init_relations()
        # Then overwrite with saved data
        for agent_id, scores in d.get("player_scores", {}).items():
            tm.player_scores[agent_id] = {
                "trust": int(scores.get("trust", 0)),
                "respect": int(scores.get("respect", 0)),
                "fear": int(scores.get("fear", 0)),
            }
        for agent_id, relations in d.get("agent_relations", {}).items():
            tm.agent_relations[agent_id] = dict(relations)
        return tm

    def summary(self) -> Dict[str, Dict[str, int]]:
        """Return a compact summary of all non-zero player scores."""
        return {
            aid: scores for aid, scores in self.player_scores.items()
            if any(v > 0 for v in scores.values())
        }

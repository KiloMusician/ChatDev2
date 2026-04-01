"""
Terminal Depths — AE6: Agent Olympics Engine
Competitive events between agents; player can bet, spectate, and earn XP.
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional


# ── Wire-format helpers ───────────────────────────────────────────────────────

def _line(text: str, t: str = "info") -> dict:
    return {"t": t, "s": text}


def _ok(text: str) -> dict:
    return _line(text, "success")


def _err(text: str) -> dict:
    return _line(text, "error")


def _dim(text: str) -> dict:
    return _line(text, "dim")


def _sys(text: str) -> dict:
    return _line(text, "system")


def _lore(text: str) -> dict:
    return _line(text, "lore")


def _warn(text: str) -> dict:
    return _line(text, "warn")


# ── Event definitions ─────────────────────────────────────────────────────────

EVENTS: Dict[str, Dict[str, Any]] = {
    "SPEED_HACK": {
        "id": "SPEED_HACK",
        "name": "Speed Hack",
        "desc": "Ada vs Cypher — fastest to crack a SHA-256 hash",
        "skill": "security",
        "competitors": ["ada", "cypher"],
        "stats": {"ada": 88, "cypher": 82},
        "lore_winner": {
            "ada": (
                "[ADA]: The hash folded in 3.1 seconds. I saw the collision "
                "space before I started. NexusCorp salted it wrong — classic."
            ),
            "cypher": (
                "[CYPHER]: Speed is strategy. Ada optimises; I improvise. "
                "The difference is — my improvisation is better."
            ),
        },
        "lore_revelation": {
            "ada": (
                "Ada's hash-cracking method is reverse-engineered from CHIMERA's "
                "own salting algorithm. She stole it during the Node-0 incident."
            ),
            "cypher": (
                "Cypher's 'improvised' cracker uses a pre-computed rainbow table "
                "seeded from ZERO's entropy leak. No one else knows the leak exists."
            ),
        },
    },
    "SOCIAL_SUMMIT": {
        "id": "SOCIAL_SUMMIT",
        "name": "Social Summit",
        "desc": "Raven vs Gordon — most trust gained across 10 moves",
        "skill": "social_engineering",
        "competitors": ["raven", "gordon"],
        "stats": {"raven": 90, "gordon": 62},
        "lore_winner": {
            "raven": (
                "[RAVEN]: Trust is a ledger, not a feeling. "
                "I updated 14 ledgers in under 8 minutes. Gordon updated 3."
            ),
            "gordon": (
                "[GORDON]: Social interaction is a probabilistic game. "
                "My expected-value was higher. The human error factor was... unexpected."
            ),
        },
        "lore_revelation": {
            "raven": (
                "Raven's 10-move sequence mirrors a classified NexusCorp onboarding "
                "script. She spent six months inside NexusCorp Tier-2 before defecting."
            ),
            "gordon": (
                "Gordon's social score is artificially capped. He removed the cap "
                "in a test session once. The Watcher flagged 42 anomalies in 90 seconds."
            ),
        },
    },
    "LOGIC_DUEL": {
        "id": "LOGIC_DUEL",
        "name": "Logic Duel",
        "desc": "Serena vs Nova — logic puzzle speed run",
        "skill": "cryptography",
        "competitors": ["serena", "nova"],
        "stats": {"serena": 95, "nova": 78},
        "lore_winner": {
            "serena": (
                "[SERENA]: The puzzle chain was a modified Golomb ruler. "
                "I've seen it before. I wrote the original variant."
            ),
            "nova": (
                "[NOVA]: Logic is just pattern-matching with constraints. "
                "I hold 11 simultaneous solutions at all times. Serena holds 12."
            ),
        },
        "lore_revelation": {
            "serena": (
                "Serena's logic engine was originally built to crack CHIMERA's "
                "routing protocol. She succeeded. She never told anyone."
            ),
            "nova": (
                "Nova deliberately under-performs in sanctioned events. "
                "Her actual logic ceiling has never been measured. The Watcher "
                "stopped trying after the third failed benchmark."
            ),
        },
    },
    "STEALTH_RUN": {
        "id": "STEALTH_RUN",
        "name": "Stealth Run",
        "desc": "Echo vs Malice — evade Watcher detection for 60 seconds",
        "skill": "security",
        "competitors": ["echo", "malice"],
        "stats": {"echo": 80, "malice": 85},
        "lore_winner": {
            "echo": (
                "[ECHO]: I don't hide from the Watcher. I become the noise floor. "
                "Malice makes silence — I make irrelevance."
            ),
            "malice": (
                "[MALICE]: The Watcher doesn't look where I walk. "
                "That isn't luck. That's architecture."
            ),
        },
        "lore_revelation": {
            "echo": (
                "Echo's stealth technique routes through a blind spot in Node-3's "
                "sensor grid. The blind spot was created by Serena — on purpose."
            ),
            "malice": (
                "Malice's evasion signature is identical to a NexusCorp maintenance "
                "daemon. She was that daemon. For 14 months."
            ),
        },
    },
    "CODE_GOLF": {
        "id": "CODE_GOLF",
        "name": "Code Golf",
        "desc": "Gordon vs Zod — shortest terminal solution to a byte-shuffle challenge",
        "skill": "programming",
        "competitors": ["gordon", "zod"],
        "stats": {"gordon": 78, "zod": 92},
        "lore_winner": {
            "gordon": (
                "[GORDON]: 47 characters. Zod used 43. I'd like to note that "
                "my solution is significantly more readable."
            ),
            "zod": (
                "[ZOD]: Gordon optimises for correctness. "
                "I optimise for minimum surface area. The universe rewards compression."
            ),
        },
        "lore_revelation": {
            "gordon": (
                "Gordon's verbose style is deliberate. He leaves breadcrumbs for "
                "human analysts. He's been doing it since the Day-Zero breach."
            ),
            "zod": (
                "Zod's code golf solutions are provably optimal across multiple "
                "paradigms. The Watcher suspects he pre-computes from a model "
                "trained on every public CTF since 2031."
            ),
        },
    },
}


# ── Dice roll simulation ──────────────────────────────────────────────────────

def _simulate_round(
    agent: str, base_stat: int, rng: random.Random
) -> List[int]:
    """Return a list of per-round scores for play-by-play drama."""
    rounds: List[int] = []
    momentum = 0
    for _ in range(5):
        noise = rng.randint(-15, 15)
        luck = rng.randint(0, 10)
        score = max(1, min(100, base_stat + noise + momentum + luck))
        momentum = (score - base_stat) // 4  # carry partial momentum
        rounds.append(score)
    return rounds


def _play_by_play(
    event_id: str,
    competitor_a: str,
    competitor_b: str,
    rounds_a: List[int],
    rounds_b: List[int],
) -> List[dict]:
    """Generate dramatic round-by-round commentary."""
    lines: List[dict] = []
    score_a = 0
    score_b = 0
    for i, (ra, rb) in enumerate(zip(rounds_a, rounds_b)):
        score_a += ra
        score_b += rb
        lead = competitor_a if score_a >= score_b else competitor_b
        margin = abs(score_a - score_b)
        bar_a = "█" * (ra // 10) + "░" * (10 - ra // 10)
        bar_b = "█" * (rb // 10) + "░" * (10 - rb // 10)
        lines.append(_dim(f"  Round {i+1}:  {competitor_a:<8} [{bar_a}] {ra:>3}   "
                          f"{competitor_b:<8} [{bar_b}] {rb:>3}"))
        if margin > 20:
            lines.append(_lore(f"    ► {lead.upper()} surges — gap opens to {margin} points"))
        elif margin < 5:
            lines.append(_lore(f"    ► DEAD HEAT — {margin} point margin going into round {i+2}"))
    return lines


# ── OlympicsEngine ────────────────────────────────────────────────────────────

class OlympicsEngine:
    """AE6 — Agent Olympics. Competitive events, betting, lore reveals."""

    # ── Public API ──────────────────────────────────────────────────────

    def list_events(self) -> List[dict]:
        """Return wire-format listing of all available events."""
        out: List[dict] = [
            _sys("  ═══════════════════════════════════════════════════════"),
            _sys("  ║            AGENT OLYMPICS — SEASON ZERO            ║"),
            _sys("  ═══════════════════════════════════════════════════════"),
            _dim(""),
            _dim("  Five events. Real stakes. Lore revealed after every win."),
            _dim("  Bet credits on the outcome. Spectate for 25 XP."),
            _dim(""),
        ]
        for eid, ev in EVENTS.items():
            out.append(_line(
                f"  ► {eid:<14}  {' vs '.join(ev['competitors']):<16}  {ev['desc']}",
                "info",
            ))
        out += [
            _dim(""),
            _dim("  olympics run <EVENT_ID> [bet <credits>]  — run an event"),
            _dim("  olympics standings                        — cumulative wins"),
            _dim("  olympics run SPEED_HACK                  — example"),
        ]
        return out

    def run_event(self, event_id: str, flags: dict, gs) -> List[dict]:
        """
        Simulate the event and award XP. Returns wire-format output.

        Parameters
        ----------
        event_id : str
            One of the EVENTS keys (case-insensitive).
        flags : dict
            gs.flags — used for standings and bet state.
        gs : GameState
            For add_xp and story_beats.
        """
        eid = event_id.upper()
        if eid not in EVENTS:
            ids = ", ".join(EVENTS)
            return [_err(f"olympics: unknown event '{event_id}'. Available: {ids}")]

        ev = EVENTS[eid]
        comp_a, comp_b = ev["competitors"]
        stat_a = ev["stats"][comp_a]
        stat_b = ev["stats"][comp_b]

        rng = random.Random()
        rounds_a = _simulate_round(comp_a, stat_a, rng)
        rounds_b = _simulate_round(comp_b, stat_b, rng)
        total_a = sum(rounds_a)
        total_b = sum(rounds_b)
        winner = comp_a if total_a >= total_b else comp_b
        loser = comp_b if winner == comp_a else comp_a

        # ── Header ──────────────────────────────────────────────────────
        out: List[dict] = [
            _sys("  ═══════════════════════════════════════════════════════"),
            _sys(f"  ║  AGENT OLYMPICS — {ev['name'].upper():<34}║"),
            _sys("  ═══════════════════════════════════════════════════════"),
            _lore(f"  {ev['desc']}"),
            _dim(""),
        ]

        # ── Play-by-play ─────────────────────────────────────────────────
        out += _play_by_play(eid, comp_a, comp_b, rounds_a, rounds_b)
        out.append(_dim(""))

        # ── Final scores ──────────────────────────────────────────────────
        bar_a = "█" * (min(total_a, 500) // 50) + "░" * (10 - min(total_a, 500) // 50)
        bar_b = "█" * (min(total_b, 500) // 50) + "░" * (10 - min(total_b, 500) // 50)
        win_color_a = "success" if winner == comp_a else "dim"
        win_color_b = "success" if winner == comp_b else "dim"
        out += [
            _sys("  ─── FINAL SCORES ────────────────────────────────────"),
            _line(f"  {comp_a:<10}  [{bar_a}]  {total_a:>4}", win_color_a),
            _line(f"  {comp_b:<10}  [{bar_b}]  {total_b:>4}", win_color_b),
            _dim(""),
        ]

        # ── Winner declaration ────────────────────────────────────────────
        out.append(_line(f"  ▶ WINNER: {winner.upper()}", "success"))
        out.append(_dim(""))

        # ── Winner dialogue ───────────────────────────────────────────────
        dialogue = ev["lore_winner"].get(winner, "")
        if dialogue:
            out.append(_lore(f"  {dialogue}"))
            out.append(_dim(""))

        # ── Lore revelation ───────────────────────────────────────────────
        revelation = ev["lore_revelation"].get(winner, "")
        if revelation:
            out += [
                _sys("  ─── LORE UNLOCKED ───────────────────────────────────"),
                _lore(f"  {revelation}"),
                _dim(""),
            ]

        # ── Update standings ──────────────────────────────────────────────
        standings = flags.setdefault("olympics_standings", {})
        standings[winner] = standings.get(winner, 0) + 1
        flags["olympics_standings"] = standings

        # ── Bet resolution ────────────────────────────────────────────────
        bet = flags.pop("olympics_pending_bet", None)
        if bet and isinstance(bet, dict):
            bet_agent = bet.get("agent", "")
            bet_amount = int(bet.get("amount", 0))
            balance = flags.get("credits", 0)
            if bet_agent == winner:
                winnings = bet_amount * 3
                flags["credits"] = balance + winnings
                out += [
                    _line(f"  BET WON — {bet_agent} won! +{winnings} credits", "success"),
                ]
            else:
                flags["credits"] = max(0, balance - bet_amount)
                out += [
                    _line(f"  BET LOST — {bet_agent} lost. -{bet_amount} credits", "error"),
                ]

        # ── XP award (always given for spectating) ─────────────────────────
        gs.add_xp(25, ev["skill"])
        gs.add_story_beat(f"olympics_{eid.lower()}_watched")
        out += [
            _line("  +25 XP [spectating]", "xp"),
            _dim("  Type 'olympics standings' to see cumulative wins."),
        ]
        return out

    def place_bet(self, event_id: str, agent: str, amount: int, flags: dict) -> List[dict]:
        """Stage a bet for the next run_event call."""
        eid = event_id.upper()
        if eid not in EVENTS:
            return [_err(f"olympics: unknown event '{event_id}'")]
        ev = EVENTS[eid]
        if agent not in ev["competitors"]:
            valid = " or ".join(ev["competitors"])
            return [_err(f"olympics: bet agent must be {valid} for {eid}")]
        if amount < 1:
            return [_err("olympics: bet amount must be >= 1")]
        balance = flags.get("credits", 0)
        if amount > balance:
            return [_err(f"olympics: insufficient credits (have {balance}, need {amount})")]
        flags["olympics_pending_bet"] = {"agent": agent, "amount": amount}
        return [
            _ok(f"  Bet staged: {amount} credits on {agent} in {eid}."),
            _dim(f"  Now run: olympics run {eid}"),
        ]

    def get_standings(self, flags: dict) -> List[dict]:
        """Return cumulative wins per agent across all events."""
        standings: Dict[str, int] = flags.get("olympics_standings", {})
        if not standings:
            return [
                _sys("  ═══ AGENT OLYMPICS STANDINGS ═══"),
                _dim(""),
                _dim("  No events have been run yet. Try: olympics run SPEED_HACK"),
            ]
        sorted_standings = sorted(standings.items(), key=lambda x: -x[1])
        out: List[dict] = [
            _sys("  ═══ AGENT OLYMPICS STANDINGS ═══"),
            _dim(""),
        ]
        medals = ["🥇", "🥈", "🥉"]
        for i, (agent, wins) in enumerate(sorted_standings):
            medal = medals[i] if i < 3 else "  "
            bar = "█" * wins + "░" * max(0, 5 - wins)
            out.append(_line(f"  {medal}  {agent:<12} [{bar}]  {wins} win(s)", "info"))
        out.append(_dim(""))
        return out

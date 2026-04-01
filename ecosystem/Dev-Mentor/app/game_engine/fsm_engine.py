"""
Finite State Machine (FSM) Puzzle Engine — Terminal Depths
==========================================================
DFA/NFA tracing puzzles for the Boolean Monks and Algorithmic Guild factions.

Commands: fsm list | fsm load <n> | fsm draw <n> | fsm trace <n> <input>
          fsm submit <n> <accept|reject>
"""
from __future__ import annotations
from typing import Dict, List, Set, Optional, Tuple

FSM_PUZZLES: List[Dict] = [
    {
        "id": 1,
        "name": "THE PARITY MACHINE",
        "difficulty": "novice",
        "faction": "Boolean Monks",
        "faction_color": "cyan",
        "description": (
            "A DFA that accepts binary strings containing an EVEN number of 1s.\n"
            "State q0 is the start and accepting state. State q1 is the non-accepting trap.\n"
            "A '0' symbol never changes parity. A '1' symbol flips the state."
        ),
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "transitions": {
            "q0": {"0": "q0", "1": "q1"},
            "q1": {"0": "q1", "1": "q0"},
        },
        "start": "q0",
        "accept": {"q0"},
        "test_input": "110110",
        "test_answer": True,
        "diagram": (
            "  ┌──0──┐   ┌──0──┐\n"
            "  ↓     │   ↓     │\n"
            "→(q0)──1→ q1 ──1→(q0)\n"
            "  ↑        │\n"
            "  └────────┘\n"
            "  (q0) = accept · q1 = reject"
        ),
        "xp": 20,
        "credits": 30,
        "lore": (
            "The Boolean Monks call this the Consensus Machine. "
            "Truth requires even agreement — a lone '1' is heresy."
        ),
    },
    {
        "id": 2,
        "name": "THE BINARY DIVISOR",
        "difficulty": "novice",
        "faction": "Algorithmic Guild",
        "faction_color": "green",
        "description": (
            "A DFA that accepts binary strings whose value is divisible by 3.\n"
            "Three states track (value mod 3). Transitions shift the accumulated\n"
            "remainder: reading 0 doubles; reading 1 doubles and adds 1."
        ),
        "states": ["q0", "q1", "q2"],
        "alphabet": ["0", "1"],
        "transitions": {
            "q0": {"0": "q0", "1": "q1"},
            "q1": {"0": "q2", "1": "q0"},
            "q2": {"0": "q1", "1": "q2"},
        },
        "start": "q0",
        "accept": {"q0"},
        "test_input": "110",
        "test_answer": True,
        "diagram": (
            "       0         0         0\n"
            "  ┌──←──┐   ┌──←──┐   ┌──←──┐\n"
            "→(q0)──1→ q1 ──1→(q0) · q2 ──1→ q2\n"
            "         └──0→ q2 ──1→ q0\n"
            "  (q0) = accept (value ≡ 0 mod 3)"
        ),
        "xp": 25,
        "credits": 35,
        "lore": (
            "Daedalus-7 derived this machine from the Sieve of Eratosthenes. "
            "Every prime > 3 leaves a shadow in the remainder field."
        ),
    },
    {
        "id": 3,
        "name": "THE BALANCED BRACKETS",
        "difficulty": "beginner",
        "faction": "Boolean Monks",
        "faction_color": "cyan",
        "description": (
            "A DFA that accepts strings over {a, b} where every 'a' is eventually\n"
            "followed by a 'b'. States track whether we are 'in debt' (seen an 'a'\n"
            "that hasn't been matched by a 'b' yet). This is a simplified 1-level DFA.\n\n"
            "q0 = balanced (start, accept)\n"
            "q1 = debt: one unmatched 'a'\n"
            "q2 = dead (two unmatched 'a's or malformed)"
        ),
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": {
            "q0": {"a": "q1", "b": "q2"},
            "q1": {"a": "q2", "b": "q0"},
            "q2": {"a": "q2", "b": "q2"},
        },
        "start": "q0",
        "accept": {"q0"},
        "test_input": "abab",
        "test_answer": True,
        "diagram": (
            "        a               b\n"
            "  ┌───────────┐   ┌───────────┐\n"
            "→(q0)────a────→ q1 ────b────→(q0)\n"
            "    ↘b   ↙a    ↑\n"
            "      q2 ──────┘  (dead state)\n"
            "  (q0) = accept · q2 = dead"
        ),
        "xp": 30,
        "credits": 40,
        "lore": (
            "Serena uses balanced bracket detection to validate protocol frames. "
            "An unmatched 'a' is a trust violation — the Consent Gate rejects it."
        ),
    },
    {
        "id": 4,
        "name": "THE VOWEL SENTINEL",
        "difficulty": "beginner",
        "faction": "Serialists",
        "faction_color": "magenta",
        "description": (
            "A DFA over lowercase Latin letters that accepts strings ending in a vowel.\n"
            "Two states: q0 (last char was not a vowel or start), q1 (last char was a vowel).\n"
            "Vowels: a, e, i, o, u. All other characters are consonants."
        ),
        "states": ["q0", "q1"],
        "alphabet": ["(letter)"],
        "transitions": {
            "q0": {"vowel": "q1", "consonant": "q0"},
            "q1": {"vowel": "q1", "consonant": "q0"},
        },
        "start": "q0",
        "accept": {"q1"},
        "test_input": "serena",
        "test_answer": True,
        "diagram": (
            "         vowel             vowel\n"
            "  ┌────────────────┐   ┌──────────┐\n"
            "→ q0 ──vowel─────→(q1) ──consonant→ q0\n"
            "   ↑──consonant──┘\n"
            "  (q1) = accept (ends in vowel)"
        ),
        "xp": 30,
        "credits": 40,
        "lore": (
            "The Serialists encode tone rows using vowel/consonant alternation. "
            "A row ending on a vowel resolves. One ending on a consonant is suspended."
        ),
    },
    {
        "id": 5,
        "name": "THE PREFIX DETECTOR",
        "difficulty": "intermediate",
        "faction": "Algorithmic Guild",
        "faction_color": "green",
        "description": (
            "A DFA that accepts binary strings containing '101' as a substring.\n"
            "Four states track progress through the pattern:\n"
            "q0 = no progress, q1 = seen '1', q2 = seen '10', q3 = seen '101' (accept).\n"
            "Once in q3, stay there (trap accept state)."
        ),
        "states": ["q0", "q1", "q2", "q3"],
        "alphabet": ["0", "1"],
        "transitions": {
            "q0": {"0": "q0", "1": "q1"},
            "q1": {"0": "q2", "1": "q1"},
            "q2": {"0": "q0", "1": "q3"},
            "q3": {"0": "q3", "1": "q3"},
        },
        "start": "q0",
        "accept": {"q3"},
        "test_input": "001010",
        "test_answer": True,
        "diagram": (
            "  → q0 ──1→ q1 ──0→ q2 ──1→(q3)\n"
            "     ↑0     ↑1     ↓0         ↑↓0,1\n"
            "     └──────┘      q0         └────\n"
            "  (q3) = accept (substring '101' found)"
        ),
        "xp": 40,
        "credits": 55,
        "lore": (
            "Gordon uses '101' substring detection to identify exploit handshakes in "
            "packet captures. Daedalus-7 calls it the 'Fisher kernel of trust.'"
        ),
    },
    {
        "id": 6,
        "name": "THE CHIMERA HANDSHAKE",
        "difficulty": "advanced",
        "faction": "Atonal Cult",
        "faction_color": "yellow",
        "description": (
            "An NFA (Non-deterministic Finite Automaton) that accepts strings over {0,1,2}\n"
            "that end with '21' or '012'. Three accepting paths exist simultaneously.\n"
            "The NFA collapses to a DFA via subset construction — trace all active states.\n\n"
            "This is the handshake protocol CHIMERA uses to establish dark sessions.\n"
            "Solve it to unlock the CHIMERA connection manifest."
        ),
        "states": ["q0", "q1", "q2", "q3", "q4"],
        "alphabet": ["0", "1", "2"],
        "transitions": {
            "q0": {"0": ["q0", "q3"], "1": ["q0"], "2": ["q0", "q1"]},
            "q1": {"1": ["q2"]},
            "q2": {},
            "q3": {"1": ["q4"], "2": ["q1"]},
            "q4": {},
        },
        "start": "q0",
        "accept": {"q2", "q4"},
        "test_input": "021",
        "test_answer": True,
        "diagram": (
            "  → q0 ──2→ q1 ──1→(q2)  [path: ends in '21']\n"
            "     ↓0\n"
            "     q3 ──1→(q4)           [path: ends in '01']\n"
            "     q3 ──2→ q1 ──1→(q2)  [path: ends in '021']\n"
            "  (q2, q4) = accept · NFA — track ALL active states"
        ),
        "xp": 60,
        "credits": 80,
        "lore": (
            "CHIMERA's handshake was designed by the Atonal Cult — prime forms of "
            "acceptance, no single path dominant. Ada calls it 'set-theoretic sovereignty.'"
        ),
    },
]


def get_fsm_puzzle(n: int) -> Optional[Dict]:
    for p in FSM_PUZZLES:
        if p["id"] == n:
            return p
    return None


def run_dfa(puzzle: Dict, input_str: str) -> Tuple[bool, List[str]]:
    """Simulate a DFA on input_str. Returns (accepted, state_trace)."""
    state = puzzle["start"]
    transitions = puzzle["transitions"]
    accept_set = puzzle["accept"]
    trace = [state]
    alphabet = puzzle.get("alphabet", [])
    is_vowel_machine = "(letter)" in alphabet

    for ch in input_str:
        t = transitions.get(state, {})
        if is_vowel_machine:
            key = "vowel" if ch.lower() in "aeiou" else "consonant"
        else:
            key = ch
        nxt = t.get(key)
        if nxt is None:
            trace.append(f"DEAD('{ch}')")
            return False, trace
        state = nxt
        trace.append(state)

    accepted = state in accept_set
    return accepted, trace


def trace_string(puzzle: Dict, input_str: str) -> Dict:
    """Return full trace result with state path."""
    accepted, trace = run_dfa(puzzle, input_str)
    return {
        "input": input_str,
        "accepted": accepted,
        "trace": trace,
        "final_state": trace[-1],
    }


def validate_fsm_submission(puzzle: Dict, answer: str) -> Dict:
    """Validate player's accept/reject answer against the test_input."""
    answer = answer.strip().lower()
    if answer not in ("accept", "reject", "yes", "no", "true", "false"):
        return {"ok": False, "error": f"Answer must be 'accept' or 'reject', got: {answer!r}"}

    player_accepts = answer in ("accept", "yes", "true")
    test_input = puzzle["test_input"]
    correct, trace = run_dfa(puzzle, test_input)

    if player_accepts == correct:
        return {
            "ok": True,
            "correct": True,
            "xp": puzzle["xp"],
            "credits": puzzle["credits"],
            "trace": trace,
            "lore": puzzle.get("lore", ""),
        }
    else:
        return {
            "ok": True,
            "correct": False,
            "trace": trace,
            "expected": "accept" if correct else "reject",
            "got": "accept" if player_accepts else "reject",
        }

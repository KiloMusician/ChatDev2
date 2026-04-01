"""
pitch_sets.py — Pitch-Class Set Analysis Engine for Terminal Depths
Atonal music theory: prime form, normal order, interval vector, Forte numbers.
Zero-token — pure music mathematics.
Philosophy: MusicHyperSetAnalysis() generalized into pattern engine.
"""
from __future__ import annotations

from itertools import permutations
from typing import Dict, List, Optional, Tuple


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_ALIASES = {
    "DB": 1, "EB": 3, "GB": 6, "AB": 8, "BB": 10,
    "Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10,
}


def name_to_pc(note: str) -> Optional[int]:
    """Convert note name to pitch class (0-11)."""
    note = note.strip().upper().replace("♭", "b").replace("♯", "#")
    if note in NOTE_ALIASES:
        return NOTE_ALIASES[note]
    for i, n in enumerate(NOTE_NAMES):
        if n.upper() == note:
            return i
    return None


def parse_set(raw: str) -> List[int]:
    """Parse a set string like 'C E G' or '0 4 7' or '{C, Eb, G}' into pitch classes."""
    raw = raw.replace("{", "").replace("}", "").replace(",", " ")
    tokens = raw.split()
    result = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        try:
            pc = int(t) % 12
            result.append(pc)
        except ValueError:
            pc = name_to_pc(t)
            if pc is not None:
                result.append(pc)
    return sorted(set(result))


def normal_order(pcs: List[int]) -> List[int]:
    """Compute normal order (most compact, leftmost packing) of a pitch-class set."""
    if not pcs:
        return []
    pcs = sorted(set(p % 12 for p in pcs))
    n = len(pcs)
    if n == 1:
        return pcs

    rotations = []
    for i in range(n):
        rot = [(pcs[(i + j) % n] - pcs[i]) % 12 for j in range(n)]
        rotations.append((rot, i))

    rotations.sort(key=lambda x: x[0])
    best_start_idx = rotations[0][1]
    best = [(pcs[(best_start_idx + j) % n]) for j in range(n)]
    return best


def prime_form(pcs: List[int]) -> List[int]:
    """Compute prime form: most compact normal order starting from 0."""
    if not pcs:
        return []
    no = normal_order(pcs)
    # Also check inversion
    inv = [(12 - p) % 12 for p in no]
    no_inv = normal_order(inv)

    # Transpose both to start at 0
    t_no = [(p - no[0]) % 12 for p in no]
    t_inv = [(p - no_inv[0]) % 12 for p in no_inv]

    # Pick the more compact (leftmost packed)
    for a, b in zip(t_no, t_inv):
        if a < b:
            return t_no
        if b < a:
            return t_inv
    return t_no


def interval_vector(pcs: List[int]) -> List[int]:
    """
    Compute the interval-class vector (6 entries for ic 1-6).
    Counts occurrences of each interval class in the set.
    """
    pcs = list(set(p % 12 for p in pcs))
    ic = [0] * 6
    for i in range(len(pcs)):
        for j in range(i + 1, len(pcs)):
            diff = abs(pcs[i] - pcs[j])
            ic_val = min(diff, 12 - diff)
            if 1 <= ic_val <= 6:
                ic[ic_val - 1] += 1
    return ic


def complement_set(pcs: List[int]) -> List[int]:
    """Return the complement (all pitch classes NOT in the set)."""
    all_pcs = set(range(12))
    return sorted(all_pcs - set(p % 12 for p in pcs))


def transpose(pcs: List[int], n: int) -> List[int]:
    """Transpose set by n semitones (Tn)."""
    return sorted(set((p + n) % 12 for p in pcs))


def invert(pcs: List[int], n: int = 0) -> List[int]:
    """Invert the set (In: negate each pc mod 12, then transpose by n)."""
    return sorted(set((n - p) % 12 for p in pcs))


def retrograde(row: List[int]) -> List[int]:
    """Return the retrograde (reverse) of a tone row."""
    return list(reversed(row))


def retrograde_inversion(row: List[int], n: int = 0) -> List[int]:
    """Return retrograde-inversion of a tone row."""
    return retrograde(invert(row, n))


# Forte's set-class catalog (subset of most common)
FORTE_CATALOG: Dict[str, Dict] = {
    "(0,1)":      {"forte": "2-1", "ic_vec": [1,0,0,0,0,0]},
    "(0,2)":      {"forte": "2-2", "ic_vec": [0,1,0,0,0,0]},
    "(0,3)":      {"forte": "2-3", "ic_vec": [0,0,1,0,0,0]},
    "(0,4)":      {"forte": "2-4", "ic_vec": [0,0,0,1,0,0]},
    "(0,5)":      {"forte": "2-5", "ic_vec": [0,0,0,0,1,0]},
    "(0,6)":      {"forte": "2-6", "ic_vec": [0,0,0,0,0,1]},
    "(0,1,2)":    {"forte": "3-1", "ic_vec": [2,1,0,0,0,0], "name": "Chromatic trichord"},
    "(0,1,3)":    {"forte": "3-2", "ic_vec": [1,1,1,0,0,0]},
    "(0,1,4)":    {"forte": "3-3", "ic_vec": [1,0,1,1,0,0]},
    "(0,1,5)":    {"forte": "3-4", "ic_vec": [1,0,0,1,1,0]},
    "(0,1,6)":    {"forte": "3-5", "ic_vec": [1,0,0,0,1,1]},
    "(0,2,4)":    {"forte": "3-6", "ic_vec": [0,2,0,1,0,0], "name": "Whole-tone trichord"},
    "(0,2,5)":    {"forte": "3-7", "ic_vec": [0,1,1,0,1,0]},
    "(0,2,6)":    {"forte": "3-8", "ic_vec": [0,1,0,1,0,1]},
    "(0,2,7)":    {"forte": "3-9", "ic_vec": [0,1,0,0,2,0], "name": "Sus4 / suspended"},
    "(0,3,6)":    {"forte": "3-10", "ic_vec": [0,0,2,0,0,1], "name": "Diminished triad"},
    "(0,3,7)":    {"forte": "3-11", "ic_vec": [0,0,1,1,1,0], "name": "Major/minor triad"},
    "(0,4,8)":    {"forte": "3-12", "ic_vec": [0,0,0,3,0,0], "name": "Augmented triad"},
    "(0,1,2,3)":  {"forte": "4-1", "ic_vec": [3,2,1,0,0,0]},
    "(0,1,2,4)":  {"forte": "4-2", "ic_vec": [2,2,1,1,0,0]},
    "(0,1,3,4)":  {"forte": "4-3", "ic_vec": [2,1,2,1,0,0]},
    "(0,1,2,5)":  {"forte": "4-4", "ic_vec": [2,1,1,1,1,0]},
    "(0,1,2,6)":  {"forte": "4-5", "ic_vec": [2,1,0,1,1,1]},
    "(0,1,2,7)":  {"forte": "4-6", "ic_vec": [2,1,0,0,2,1]},
    "(0,1,4,5)":  {"forte": "4-7", "ic_vec": [2,0,1,2,1,0]},
    "(0,1,5,6)":  {"forte": "4-8", "ic_vec": [2,0,0,2,0,2]},
    "(0,1,6,7)":  {"forte": "4-9", "ic_vec": [2,0,0,2,0,2]},
    "(0,2,3,5)":  {"forte": "4-10", "ic_vec": [1,2,2,0,1,0]},
    "(0,1,3,5)":  {"forte": "4-11", "ic_vec": [1,2,1,1,1,0]},
    "(0,2,3,6)":  {"forte": "4-12", "ic_vec": [1,1,2,1,0,1]},
    "(0,1,3,6)":  {"forte": "4-13", "ic_vec": [1,1,2,0,1,1]},
    "(0,2,3,7)":  {"forte": "4-14", "ic_vec": [1,1,1,1,2,0]},
    "(0,1,4,6)":  {"forte": "4-Z15", "ic_vec": [1,1,1,1,1,1]},
    "(0,1,5,7)":  {"forte": "4-16", "ic_vec": [1,1,0,1,2,1]},
    "(0,3,4,7)":  {"forte": "4-17", "ic_vec": [1,0,2,2,1,0]},
    "(0,1,4,7)":  {"forte": "4-18", "ic_vec": [1,0,2,1,1,1]},
    "(0,1,4,8)":  {"forte": "4-19", "ic_vec": [1,0,1,3,1,0]},
    "(0,1,5,8)":  {"forte": "4-20", "ic_vec": [1,0,1,2,0,2], "name": "Major seventh chord"},
    "(0,2,4,6)":  {"forte": "4-21", "ic_vec": [0,3,0,2,0,1], "name": "Whole-tone tetrachord"},
    "(0,2,4,7)":  {"forte": "4-22", "ic_vec": [0,2,1,1,2,0]},
    "(0,2,5,7)":  {"forte": "4-23", "ic_vec": [0,2,1,0,3,0], "name": "Quartal tetrachord"},
    "(0,2,4,8)":  {"forte": "4-24", "ic_vec": [0,2,0,3,0,1]},
    "(0,2,6,8)":  {"forte": "4-25", "ic_vec": [0,2,0,2,0,2]},
    "(0,3,5,8)":  {"forte": "4-26", "ic_vec": [0,1,2,1,2,0]},
    "(0,2,5,8)":  {"forte": "4-27", "ic_vec": [0,1,2,1,1,1], "name": "Half-diminished seventh"},
    "(0,3,6,9)":  {"forte": "4-28", "ic_vec": [0,0,4,0,0,2], "name": "Diminished seventh chord"},
    "(0,1,3,7)":  {"forte": "4-Z29", "ic_vec": [1,1,1,1,1,1]},
}


def forte_number(pcs: List[int]) -> Optional[Dict]:
    """Look up Forte number for a prime form."""
    pf = prime_form(pcs)
    key = "(" + ",".join(str(p) for p in pf) + ")"
    return FORTE_CATALOG.get(key)


# Puzzle definitions for the `set` command
SET_PUZZLES = [
    {
        "id": 1, "title": "PRIME FORM IDENTIFICATION",
        "xp": 20, "credits": 30,
        "description": "Given the set {C, E, G} (a C major triad), find its prime form.",
        "raw_set": "C E G",
        "task": "prime_form",
        "expected_answer": "(0,3,7)",
        "hint": "Transpose the normal order to start at 0. The triad maps to Forte 3-11.",
        "lore": "The Atonal Cult's first lesson: strip away tonality. All major and minor triads share the same prime form.",
    },
    {
        "id": 2, "title": "NORMAL ORDER",
        "xp": 25, "credits": 35,
        "description": "Arrange {E, C#, A} in normal order (most compact packing, ascending).",
        "raw_set": "A C# E",
        "task": "normal_order",
        "expected_answer": "(9,0,4)",
        "hint": "Try all rotations. The most compact span (fewest semitones from first to last) wins.",
        "lore": "Normal order is the canonical form of a set — its most efficient arrangement in pitch space.",
    },
    {
        "id": 3, "title": "INTERVAL VECTOR",
        "xp": 30, "credits": 45,
        "description": "Compute the interval vector of {C, E, G#} (augmented triad).",
        "raw_set": "C E G#",
        "task": "interval_vector",
        "expected_answer": "<0,0,0,3,0,0>",
        "hint": "Count how many times each interval class (1-6) appears. The augmented triad has only ic4.",
        "lore": "Forte 3-12: the augmented triad has the most symmetrical interval structure of any trichord.",
    },
    {
        "id": 4, "title": "COMPLEMENT",
        "xp": 35, "credits": 55,
        "description": "Find the complement of {C, D, E, F, G, A, B} (C major scale).",
        "raw_set": "C D E F G A B",
        "task": "complement",
        "expected_answer": "{C#, D#, F#, G#, A#}",
        "hint": "The complement contains all 12 pitch classes NOT in the set.",
        "lore": "The Serialists use complement as 'the shadow row' — the row that completes the aggregate.",
    },
    {
        "id": 5, "title": "FORTE NUMBER",
        "xp": 40, "credits": 65,
        "description": "Identify the Forte number of {C, Eb, F#, A} (diminished seventh chord).",
        "raw_set": "C Eb F# A",
        "task": "forte",
        "expected_answer": "4-28",
        "hint": "Compute prime form first. Fully diminished seventh = (0,3,6,9) = Forte 4-28.",
        "lore": "4-28 is the most symmetric tetrachord — it divides the octave into four equal parts. The Atonal Cult calls it the 'perfect square.'",
    },
    {
        "id": 6, "title": "TONE ROW — RETROGRADE",
        "xp": 50, "credits": 80,
        "description": "Given the row [C, C#, D, Eb, E, F, F#, G, Ab, A, Bb, B], compute its retrograde.",
        "raw_set": "0 1 2 3 4 5 6 7 8 9 10 11",
        "task": "retrograde",
        "expected_answer": "11 10 9 8 7 6 5 4 3 2 1 0",
        "hint": "Retrograde is simply the row in reverse order.",
        "lore": "The Serialists' prime directive: R(P) reveals the harmonic past as future. The universe is palindromic.",
    },
    {
        "id": 7, "title": "INVERSION",
        "xp": 60, "credits": 95,
        "description": "Invert the trichord {0, 4, 7} around the axis 0 (I₀). What set do you get?",
        "raw_set": "0 4 7",
        "task": "inversion",
        "expected_answer": "(0,5,8)",
        "hint": "I₀(n) = (0 - n) mod 12. So 0→0, 4→8, 7→5. Sort the result.",
        "lore": "Inversion mirrors the set. Major triad inverts to minor triad — same prime form, different quality.",
    },
]


def evaluate_set_answer(puzzle_id: int, player_answer: str) -> Dict:
    """Check a player's answer for a set-theory puzzle."""
    pz = next((p for p in SET_PUZZLES if p["id"] == puzzle_id), None)
    if not pz:
        return {"error": f"No puzzle {puzzle_id}"}

    pcs = parse_set(pz["raw_set"])
    correct: Any = None
    computed_display: str = ""

    task = pz["task"]
    if task == "prime_form":
        pf = prime_form(pcs)
        computed_display = "(" + ",".join(str(p) for p in pf) + ")"
        correct = computed_display
    elif task == "normal_order":
        no = normal_order(pcs)
        computed_display = "(" + ",".join(str(p) for p in no) + ")"
        correct = computed_display
    elif task == "interval_vector":
        iv = interval_vector(pcs)
        computed_display = "<" + ",".join(str(x) for x in iv) + ">"
        correct = computed_display
    elif task == "complement":
        comp = complement_set(pcs)
        names = [NOTE_NAMES[p] for p in comp]
        computed_display = "{" + ", ".join(names) + "}"
        correct = computed_display
    elif task == "forte":
        fn = forte_number(pcs)
        computed_display = fn["forte"] if fn else "unknown"
        correct = computed_display
    elif task == "retrograde":
        ret = retrograde(pcs)
        computed_display = " ".join(str(p) for p in ret)
        correct = computed_display
    elif task == "inversion":
        inv = sorted(set((0 - p) % 12 for p in pcs))
        pf = prime_form(inv)
        computed_display = "(" + ",".join(str(p) for p in pf) + ")"
        correct = computed_display

    # Normalize both for comparison
    def normalize(s: str) -> str:
        return "".join(c for c in s.lower() if c.isdigit() or c == ',')

    passed = normalize(player_answer) == normalize(correct)

    return {
        "passed": passed,
        "puzzle": pz,
        "player_answer": player_answer,
        "correct_answer": correct,
        "computed": computed_display,
        "xp_earned": pz["xp"] if passed else pz["xp"] // 5,
        "credits_earned": pz["credits"] if passed else 0,
        "verdict": "✓ CORRECT — " + pz["lore"] if passed else f"✗ INCORRECT — Expected: {correct}",
    }

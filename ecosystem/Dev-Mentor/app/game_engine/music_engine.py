"""
music_engine.py — Serialist Music Engine for Terminal Depths (P12)
===================================================================
"CHIMERA uses a 12-tone algorithm to coordinate its 847 endpoints.
Every packet is a note. Every protocol is a tone row." — Archivist

5 cyberpunk styles, each with a seed tone row and characteristic rhythm:
  CHIMERA_GOTHIC     — dissonant, angular, machine-like
  RESISTANCE_MARCH   — rhythmic, defiant, coded signal
  ZERO_ELEGY         — slow, sparse, fading into silence
  GHOST_AMBIENT      — drifting, ethereal, processual
  NEXUS_INDUSTRIAL   — dense, relentless, mechanical

Commands (routed from commands.py):
  compose [gothic|march|elegy|ambient|industrial] [--seed <n>]
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Output helpers (mirror commands.py pattern)
# ---------------------------------------------------------------------------

def _sys(s: str) -> Dict:  return {"t": "system",  "s": s}
def _dim(s: str) -> Dict:  return {"t": "dim",     "s": s}
def _ok(s: str)  -> Dict:  return {"t": "success", "s": s}
def _err(s: str) -> Dict:  return {"t": "error",   "s": s}
def _warn(s: str)-> Dict:  return {"t": "warn",    "s": s}
def _info(s: str)-> Dict:  return {"t": "info",    "s": s}
def _lore(s: str)-> Dict:  return {"t": "lore",    "s": s}
def _line(s: str, t: str = "output") -> Dict: return {"t": t, "s": s}


# ---------------------------------------------------------------------------
# Note vocabulary
# ---------------------------------------------------------------------------

NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
DURATIONS = ["Q", "E", "H", "E", "Q", "Q", "E", "H"]     # quarter, eighth, half
DURATION_NAMES = {"Q": "quarter", "E": "eighth", "H": "half"}
DYNAMICS = ["pp", "mp", "mp", "mf", "mf", "ff", "mf", "pp"]


# ---------------------------------------------------------------------------
# Style definitions
# ---------------------------------------------------------------------------

STYLES: Dict[str, Dict[str, Any]] = {
    "gothic": {
        "name": "CHIMERA_GOTHIC",
        "agent": "CHIMERA",
        "seed_row": [0, 11, 3, 4, 8, 7, 9, 6, 1, 5, 2, 10],
        "rhythm":  ["Q", "E", "E", "Q", "H", "E", "E", "Q", "Q", "E", "H", "Q"],
        "dynamics": ["ff", "mf", "mf", "ff", "mf", "mp", "mf", "ff", "mp", "mf", "ff", "mf"],
        "lore": "CHIMERA uses a 12-tone algorithm to coordinate its 847 endpoints. "
                "Every packet is a note. Every protocol is a tone row.",
        "title": "Gothic Protocol",
    },
    "march": {
        "name": "RESISTANCE_MARCH",
        "agent": "Ada",
        "seed_row": [0, 2, 4, 5, 7, 9, 11, 1, 3, 6, 8, 10],
        "rhythm":  ["Q", "Q", "Q", "Q", "E", "E", "Q", "Q", "Q", "Q", "H", "H"],
        "dynamics": ["mf", "mf", "ff", "mf", "mp", "mp", "mf", "ff", "mf", "mf", "ff", "ff"],
        "lore": "The Resistance broadcasts in music — a tone row only Ada can decode. "
                "Each interval encodes a rendezvous coordinate in the Undercroft.",
        "title": "Signal Through the Static",
    },
    "elegy": {
        "name": "ZERO_ELEGY",
        "agent": "ZERO",
        "seed_row": [0, 1, 5, 11, 2, 6, 3, 9, 8, 10, 4, 7],
        "rhythm":  ["H", "Q", "H", "E", "E", "H", "Q", "H", "Q", "E", "H", "H"],
        "dynamics": ["pp", "pp", "mp", "pp", "pp", "mp", "mp", "pp", "pp", "pp", "pp", "pp"],
        "lore": "ZERO wrote this piece in their final hours. The last note is silence. "
                "It is the only composition ever flagged by NexusCorp's sentiment AI as 'grief'.",
        "title": "Last Transmission",
    },
    "ambient": {
        "name": "GHOST_AMBIENT",
        "agent": "Ghost",
        "seed_row": [0, 6, 2, 8, 4, 10, 1, 7, 3, 9, 5, 11],
        "rhythm":  ["H", "H", "Q", "E", "H", "Q", "Q", "H", "E", "E", "H", "Q"],
        "dynamics": ["pp", "mp", "pp", "pp", "mp", "pp", "mp", "mp", "pp", "pp", "mp", "pp"],
        "lore": "Ghost moves through the Grid like a standing wave — present everywhere, "
                "visible nowhere. This piece is Ghost's own heartbeat, rendered in tone.",
        "title": "Ghost Frequency",
    },
    "industrial": {
        "name": "NEXUS_INDUSTRIAL",
        "agent": "Raven",
        "seed_row": [0, 7, 6, 5, 11, 4, 3, 10, 9, 2, 1, 8],
        "rhythm":  ["E", "E", "E", "E", "Q", "E", "E", "E", "E", "Q", "E", "E"],
        "dynamics": ["ff", "ff", "mf", "ff", "ff", "mf", "ff", "ff", "mf", "ff", "ff", "ff"],
        "lore": "NexusCorp's server farms hum at 60 Hz. Raven mapped the harmonic overtones "
                "and found a 12-tone row hidden in the industrial noise. It was intentional.",
        "title": "Machine Hymn",
    },
}

STYLE_ALIASES: Dict[str, str] = {
    "gothic": "gothic", "g": "gothic", "chimera": "gothic",
    "march":  "march",  "m": "march",  "resistance": "march",
    "elegy":  "elegy",  "e": "elegy",  "zero": "elegy",
    "ambient": "ambient", "a": "ambient", "ghost": "ambient",
    "industrial": "industrial", "i": "industrial", "nexus": "industrial",
}


# ---------------------------------------------------------------------------
# 12-tone row operations
# ---------------------------------------------------------------------------

def _transpose_row(row: List[int], semitones: int) -> List[int]:
    """Transpose all pitches by semitones (mod 12)."""
    return [(p + semitones) % 12 for p in row]


def _invert_row(row: List[int]) -> List[int]:
    """Mirror intervals (inversion): I_0."""
    return [(12 - p) % 12 for p in row]


def _retrograde_row(row: List[int]) -> List[int]:
    """Reverse the order of pitches."""
    return list(reversed(row))


def _retrograde_inversion(row: List[int]) -> List[int]:
    """Retrograde of the inversion."""
    return list(reversed(_invert_row(row)))


def _build_matrix(row: List[int]) -> List[List[int]]:
    """Build full 12x12 Babbitt matrix (P0..P11 as rows)."""
    matrix = []
    for t in range(12):
        matrix.append(_transpose_row(row, t))
    return matrix


def _pick_forms(row: List[int], rng: random.Random) -> List[Tuple[str, List[int]]]:
    """Choose a sequence of row forms for the piece (P, I, R, RI with transpositions)."""
    forms = []
    choices = ["P", "I", "R", "RI"]
    for _ in range(4):  # 4 measures, each uses one row form
        form_name = rng.choice(choices)
        transposition = rng.randint(0, 11)
        if form_name == "P":
            built = _transpose_row(row, transposition)
        elif form_name == "I":
            built = _transpose_row(_invert_row(row), transposition)
        elif form_name == "R":
            built = _retrograde_row(_transpose_row(row, transposition))
        else:
            built = _retrograde_inversion(_transpose_row(row, transposition))
        label = f"{form_name}{transposition}"
        forms.append((label, built))
    return forms


# ---------------------------------------------------------------------------
# Piece generation
# ---------------------------------------------------------------------------

def _build_measure(pitch_row: List[int], rhythm: List[str], dynamics: List[str],
                   rng: random.Random, form_label: str) -> Dict[str, Any]:
    """Create a single measure dict from a pitch row + style rhythm/dynamics."""
    notes = []
    for i, pitch in enumerate(pitch_row):
        dur = rhythm[i % len(rhythm)]
        dyn = dynamics[i % len(dynamics)]
        # Small humanization: occasionally accent or soften
        if rng.random() < 0.12:
            dyn_map = {"pp": "pp", "mp": "pp", "mf": "mp", "ff": "mf"}
            dyn = dyn_map.get(dyn, dyn)
        notes.append({
            "pitch": pitch,
            "note": NOTE_NAMES[pitch],
            "duration": dur,
            "duration_name": DURATION_NAMES.get(dur, dur),
            "dynamic": dyn,
        })
    return {"form": form_label, "notes": notes}


def compose(style: str = "gothic", seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate a 12-tone serialist piece.

    Parameters
    ----------
    style : one of gothic / march / elegy / ambient / industrial (or aliases)
    seed  : optional integer seed for reproducibility

    Returns
    -------
    dict with keys: title, composer, style_name, tone_row, matrix_snippet,
                    forms_used, piece (list of measures), ascii_score, lore
    """
    style_key = STYLE_ALIASES.get(style.lower(), "gothic")
    cfg = STYLES[style_key]

    rng = random.Random(seed if seed is not None else random.randint(0, 2**31))

    base_row: List[int] = cfg["seed_row"][:]
    if seed is not None:
        # Deterministic permutation from seed keeps row integrity
        indices = list(range(12))
        rng.shuffle(indices)
        base_row = [cfg["seed_row"][i] for i in indices]
        # Normalize so first element is 0
        offset = base_row[0]
        base_row = [(p - offset) % 12 for p in base_row]

    forms = _pick_forms(base_row, rng)
    rhythm  = cfg["rhythm"]
    dynamics = cfg["dynamics"]

    measures = []
    for form_label, pitch_row in forms:
        measures.append(_build_measure(pitch_row, rhythm, dynamics, rng, form_label))

    # Build ASCII score
    ascii_score = _render_ascii_score(measures, cfg["name"])

    # Matrix snippet (first 4 rows / 4 columns)
    matrix = _build_matrix(base_row)
    matrix_snippet = [[NOTE_NAMES[matrix[r][c]] for c in range(4)] for r in range(4)]

    return {
        "title":          cfg["title"],
        "composer":       cfg["agent"],
        "style_name":     cfg["name"],
        "tone_row":       [NOTE_NAMES[p] for p in base_row],
        "matrix_snippet": matrix_snippet,
        "forms_used":     [f for f, _ in forms],
        "piece":          measures,
        "ascii_score":    ascii_score,
        "lore":           cfg["lore"],
    }


# ---------------------------------------------------------------------------
# ASCII score renderer
# ---------------------------------------------------------------------------

DYN_WIDTH = {"pp": "▁▁", "mp": "▃▃", "mf": "▅▅", "ff": "█▐"}
DUR_SYMBOL = {"Q": "♩", "E": "♪", "H": "𝅗♩"}


def _render_ascii_score(measures: List[Dict], style_name: str) -> str:
    lines = []
    lines.append(f"  ╔══ {style_name} ══╗")
    for m_idx, measure in enumerate(measures):
        lines.append(f"  ║ Measure {m_idx + 1}  [{measure['form']}]")
        note_line = "  ║  "
        dyn_line  = "  ║  "
        for note in measure["notes"]:
            name    = note["note"].ljust(3)
            dur_sym = DUR_SYMBOL.get(note["duration"], note["duration"])
            dyn_sym = DYN_WIDTH.get(note["dynamic"], "  ")
            note_line += f"{name}{dur_sym} "
            dyn_line  += f"{dyn_sym}   "
        lines.append(note_line)
        lines.append(dyn_line)
        lines.append("  ║")
    lines.append("  ╚" + "═" * (len(style_name) + 6) + "╝")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Wire-format render
# ---------------------------------------------------------------------------

def render_score(piece_dict: Dict[str, Any]) -> List[Dict]:
    """Convert a compose() result into terminal wire-format blocks."""
    out: List[Dict] = []
    out.append(_sys(f"  ═══ COMPOSE: {piece_dict['style_name']} ═══"))
    out.append(_dim(""))
    out.append(_info(f"  Title:    {piece_dict['title']}"))
    out.append(_info(f"  Composer: {piece_dict['composer']}"))
    out.append(_dim(""))

    # Tone row
    row_str = "  ".join(piece_dict["tone_row"])
    out.append(_sys("  Tone Row (P0):"))
    out.append(_ok(f"    {row_str}"))
    out.append(_dim(""))

    # Row forms used
    forms_str = "  ".join(piece_dict["forms_used"])
    out.append(_info(f"  Row forms: {forms_str}"))
    out.append(_dim(""))

    # Matrix snippet
    out.append(_sys("  Babbitt Matrix (4×4 excerpt):"))
    for row in piece_dict["matrix_snippet"]:
        out.append(_dim("    " + "  ".join(n.ljust(3) for n in row)))
    out.append(_dim(""))

    # ASCII score
    for line in piece_dict["ascii_score"].split("\n"):
        out.append(_line(line, "output"))
    out.append(_dim(""))

    # Measures detail
    out.append(_sys("  Notation:"))
    for m_idx, measure in enumerate(piece_dict["piece"]):
        out.append(_info(f"  Measure {m_idx + 1}  [{measure['form']}]"))
        for note in measure["notes"]:
            out.append(_dim(
                f"    {note['note']:<3}  {note['duration_name']:<8}  {note['dynamic']}"
            ))
    out.append(_dim(""))

    # Lore
    out.append(_lore(f"  [{piece_dict['composer'].upper()}]: {piece_dict['lore']}"))
    out.append(_dim(""))
    return out


# ---------------------------------------------------------------------------
# Listing helper
# ---------------------------------------------------------------------------

def list_styles() -> List[Dict]:
    out: List[Dict] = []
    out.append(_sys("  ═══ SERIALIST MUSIC ENGINE ═══"))
    out.append(_dim("  5 cyberpunk styles — each a unique tone row and rhythm signature"))
    out.append(_dim(""))
    rows_info = [
        ("gothic",     "CHIMERA_GOTHIC",    "Ada's nightmare — dissonant machine protocol"),
        ("march",      "RESISTANCE_MARCH",  "Encoded signal — only Ada can decode the row"),
        ("elegy",      "ZERO_ELEGY",        "ZERO's final composition — last note is silence"),
        ("ambient",    "GHOST_AMBIENT",     "Ghost's heartbeat — a standing wave in the Grid"),
        ("industrial", "NEXUS_INDUSTRIAL",  "Hidden in NexusCorp's server farm harmonics"),
    ]
    for key, name, desc in rows_info:
        out.append(_info(f"  {key:<12} {name:<22} — {desc}"))
    out.append(_dim(""))
    out.append(_dim("  compose <style>            — generate a piece"))
    out.append(_dim("  compose <style> --seed <n> — reproducible generation"))
    out.append(_dim("  compose all                — play through all 5 styles"))
    return out

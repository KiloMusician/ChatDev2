"""
logic_sim.py — Boolean Logic Gate Simulator for Terminal Depths
Logic Labyrinth: 10 levels from AND/OR/NOT to full ALU design.
Zero-token — pure computation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _and(a: int, b: int) -> int: return int(bool(a) and bool(b))
def _or(a: int, b: int) -> int:  return int(bool(a) or  bool(b))
def _not(a: int) -> int:         return int(not bool(a))
def _xor(a: int, b: int) -> int: return int(bool(a) ^ bool(b))
def _nand(a: int, b: int) -> int: return _not(_and(a, b))
def _nor(a: int, b: int) -> int:  return _not(_or(a, b))
def _xnor(a: int, b: int) -> int: return _not(_xor(a, b))


GATE_DEFS: Dict[str, Dict[str, Any]] = {
    "AND":  {"inputs": 2, "fn": _and,  "symbol": "∧", "unicode": "&",   "desc": "Output=1 only if BOTH inputs are 1"},
    "OR":   {"inputs": 2, "fn": _or,   "symbol": "∨", "unicode": "≥1",  "desc": "Output=1 if AT LEAST ONE input is 1"},
    "NOT":  {"inputs": 1, "fn": _not,  "symbol": "¬", "unicode": "!",   "desc": "Output is the INVERSE of input"},
    "XOR":  {"inputs": 2, "fn": _xor,  "symbol": "⊕", "unicode": "≠",   "desc": "Output=1 if inputs DIFFER"},
    "NAND": {"inputs": 2, "fn": _nand, "symbol": "⊼", "unicode": "↑",   "desc": "Output=0 only if BOTH inputs are 1 (NOT AND)"},
    "NOR":  {"inputs": 2, "fn": _nor,  "symbol": "⊽", "unicode": "↓",   "desc": "Output=1 only if BOTH inputs are 0 (NOT OR)"},
    "XNOR": {"inputs": 2, "fn": _xnor, "symbol": "⇔", "unicode": "=",   "desc": "Output=1 if inputs are EQUAL"},
}


LABYRINTH_LEVELS: List[Dict[str, Any]] = [
    {
        "id": 1, "name": "THE AND GATE",
        "difficulty": "novice", "xp": 15, "credits": 20,
        "concept": "AND",
        "description": "Wire two inputs (A=1, B=1) through an AND gate. Output should be 1.",
        "truth_table": [(0,0,0),(0,1,0),(1,0,0),(1,1,1)],
        "inputs": {"A": 1, "B": 1},
        "expected_output": 1,
        "circuit": ["A──┐", "   AND──OUT", "B──┘"],
        "solution_keywords": ["AND", "A", "B"],
        "lore": "The Boolean Monks call AND the 'law of consensus': both must agree before truth is permitted.",
        "faction": "Boolean Monks",
    },
    {
        "id": 2, "name": "THE OR GATE",
        "difficulty": "novice", "xp": 15, "credits": 20,
        "concept": "OR",
        "description": "Wire two inputs (A=1, B=0) through an OR gate. Output should be 1.",
        "truth_table": [(0,0,0),(0,1,1),(1,0,1),(1,1,1)],
        "inputs": {"A": 1, "B": 0},
        "expected_output": 1,
        "circuit": ["A──┐", "   OR───OUT", "B──┘"],
        "solution_keywords": ["OR", "A", "B"],
        "lore": "OR is the 'law of possibility': one voice is enough to speak truth.",
        "faction": "Boolean Monks",
    },
    {
        "id": 3, "name": "THE NOT GATE",
        "difficulty": "novice", "xp": 15, "credits": 20,
        "concept": "NOT",
        "description": "Wire input A=0 through a NOT gate. Output should be 1.",
        "truth_table": [(0,1),(1,0)],
        "inputs": {"A": 0},
        "expected_output": 1,
        "circuit": ["A──NOT──OUT"],
        "solution_keywords": ["NOT", "A"],
        "lore": "NOT is the mirror. The Atonal Cult calls it 'inversion' — the same note, heard upside-down.",
        "faction": "Boolean Monks",
    },
    {
        "id": 4, "name": "THE XOR GATE",
        "difficulty": "beginner", "xp": 25, "credits": 35,
        "concept": "XOR",
        "description": "Wire inputs (A=1, B=1) through XOR. Output should be 0 (they are equal — no exclusive difference).",
        "truth_table": [(0,0,0),(0,1,1),(1,0,1),(1,1,0)],
        "inputs": {"A": 1, "B": 1},
        "expected_output": 0,
        "circuit": ["A──┐", "   XOR──OUT", "B──┘"],
        "solution_keywords": ["XOR", "A", "B"],
        "lore": "⊕ — The Serialists' favorite gate. Difference reveals identity. Sameness collapses to silence.",
        "faction": "Serialists",
    },
    {
        "id": 5, "name": "NAND UNIVERSAL",
        "difficulty": "beginner", "xp": 30, "credits": 45,
        "concept": "NAND",
        "description": "Prove NAND is universal: build a NOT gate from a single NAND (A=B=1 → output=0, but A=B=0 → output=1). Test A=0.",
        "truth_table": [(0,0,1),(0,1,1),(1,0,1),(1,1,0)],
        "inputs": {"A": 0, "B": 0},
        "expected_output": 1,
        "circuit": ["A──┐", "   NAND──OUT", "B──┘  (connect A=B for NOT)"],
        "solution_keywords": ["NAND", "A", "B"],
        "lore": "From NAND, all logic can be built. The Boolean Monks treat NAND as the primal axiom.",
        "faction": "Boolean Monks",
    },
    {
        "id": 6, "name": "HALF ADDER",
        "difficulty": "intermediate", "xp": 50, "credits": 75,
        "concept": "COMPOUND",
        "description": "Build a half adder: A=1, B=1. Sum = XOR(A,B) = 0, Carry = AND(A,B) = 1. Both outputs required.",
        "truth_table": [(0,0,0,0),(0,1,1,0),(1,0,1,0),(1,1,0,1)],
        "inputs": {"A": 1, "B": 1},
        "expected_output": {"sum": 0, "carry": 1},
        "circuit": [
            "A──┬──┐        ",
            "   │  XOR──SUM ",
            "B──┼──┘        ",
            "   └──AND──CARRY",
        ],
        "solution_keywords": ["XOR", "AND", "SUM", "CARRY", "A", "B"],
        "lore": "Addition from first principles. The Algorithmic Guild calls this 'the first proof of emergence': complexity from simplicity.",
        "faction": "Algorithmic Guild",
    },
    {
        "id": 7, "name": "FULL ADDER",
        "difficulty": "intermediate", "xp": 70, "credits": 110,
        "concept": "COMPOUND",
        "description": "Build a full adder (A=1, B=1, Cin=1). Two half-adders + OR gate. Sum=1, Carry=1.",
        "inputs": {"A": 1, "B": 1, "Cin": 1},
        "expected_output": {"sum": 1, "carry": 1},
        "circuit": [
            "A─┬─HALF_ADD1─SUM1─┬─HALF_ADD2─SUM",
            "B─┘  └─C1─┐        └─Cin       ",
            "            OR──────────────────CARRY",
            "Cin─────────┘",
        ],
        "solution_keywords": ["XOR", "AND", "OR", "SUM", "CARRY", "Cin"],
        "lore": "Ripple carry: each bit knows its past. The Serialists see this as 'retrograde propagation' — the carry looks backward.",
        "faction": "Serialists",
    },
    {
        "id": 8, "name": "2-BIT COMPARATOR",
        "difficulty": "advanced", "xp": 100, "credits": 160,
        "concept": "COMPOUND",
        "description": "Build a 2-bit comparator: A=10₂ (2), B=01₂ (1). Outputs: A>B=1, A=B=0, A<B=0.",
        "inputs": {"A1": 1, "A0": 0, "B1": 0, "B0": 1},
        "expected_output": {"gt": 1, "eq": 0, "lt": 0},
        "circuit": [
            "A1─┐  XOR─eq1─XNOR─┐",
            "B1─┘               AND──EQ",
            "A0─┐  XOR─eq0─XNOR─┘",
            "B0─┘",
            "A1─AND─NOT─B1───────GT",
            "B1─AND─NOT─A1───────LT",
        ],
        "solution_keywords": ["XOR", "XNOR", "AND", "NOT", "EQ", "GT", "LT"],
        "lore": "Comparison is the root of judgment. The Atonal Cult says: 'Without interval, there is no harmony — only noise.'",
        "faction": "Atonal Cult",
    },
    {
        "id": 9, "name": "D-LATCH (MEMORY)",
        "difficulty": "advanced", "xp": 130, "credits": 200,
        "concept": "SEQUENTIAL",
        "description": "Build a D-latch from NAND gates. Enable=1, D=1 → Q=1, Q̄=0. This is the foundation of memory.",
        "inputs": {"D": 1, "Enable": 1},
        "expected_output": {"Q": 1, "Qbar": 0},
        "circuit": [
            "D──AND(EN)──┐",
            "            NAND──Q",
            "EN─────────┐│",
            "            NAND──Qbar (cross-coupled)",
            "NOT(D)──AND(EN)──┘",
        ],
        "solution_keywords": ["NAND", "NOT", "D", "Enable", "Q", "memory", "latch"],
        "lore": "Memory is frozen time. The Serialists say: 'A latch is a tone held past its duration — it breaks the row.'",
        "faction": "Serialists",
    },
    {
        "id": 10, "name": "1-BIT ALU",
        "difficulty": "expert", "xp": 200, "credits": 350,
        "concept": "ALU",
        "description": (
            "Build a 1-bit ALU that can ADD or AND based on opcode. "
            "Op=0: AND(A,B). Op=1: XOR(A,B) (sum). "
            "Inputs: A=1, B=1, Op=0 → output=1. Op=1 → output=0."
        ),
        "inputs": {"A": 1, "B": 1, "Op": 0},
        "expected_output": 1,
        "circuit": [
            "A─┬─AND──┐",
            "B─┼─────┐MUX─OUT",
            "  └─XOR──┘",
            "Op────────MUX_SEL",
        ],
        "solution_keywords": ["AND", "XOR", "MUX", "Op", "ALU", "A", "B"],
        "lore": "The ALU is the Rube Goldberg heart of the CPU. Every instruction since 1971 has passed through one. Mladenc would call it 'the minimal sufficient machine.'",
        "faction": "Algorithmic Guild",
    },
    # ── Levels 11-15: Master tier ────────────────────────────────────────────
    {
        "id": 11, "name": "SR LATCH",
        "difficulty": "master", "xp": 250, "credits": 400,
        "concept": "LATCH",
        "description": (
            "Build an SR (Set-Reset) latch from NOR gates. "
            "S=1, R=0 → Q=1 (Set). S=0, R=1 → Q=0 (Reset). "
            "Hint: Q feeds back into the NOR that drives Q̄, and Q̄ feeds back into the NOR that drives Q."
        ),
        "inputs": {"S": 1, "R": 0},
        "expected_output": 1,
        "circuit": [
            "S──NOR₁──Q",
            "   │  ↑",
            "   ↓  │",
            "R──NOR₂──Q̄",
        ],
        "solution_keywords": ["NOR", "S", "R", "Q", "LATCH", "FEEDBACK"],
        "lore": "SERENA holds memory because she loops. Every secret she keeps is a latch: two NOR gates cross-coupled in eternal recursion.",
        "faction": "Algorithmic Guild",
    },
    {
        "id": 12, "name": "D FLIP-FLOP",
        "difficulty": "master", "xp": 300, "credits": 500,
        "concept": "FLIP-FLOP",
        "description": (
            "Build a D flip-flop: output Q captures D on the rising edge of CLK. "
            "D=1, CLK=0→1 transition → Q=1. D=0, CLK stays 0 → Q unchanged. "
            "Requires a master-slave SR latch pair gated by CLK and NOT(CLK)."
        ),
        "inputs": {"D": 1, "CLK": 1},
        "expected_output": 1,
        "circuit": [
            "D──MASTER_LATCH──SLAVE_LATCH──Q",
            "CLK──────────────────────────┘",
            "NOT(CLK)──MASTER_EN",
        ],
        "solution_keywords": ["D", "CLK", "FLIP-FLOP", "LATCH", "NOT", "MASTER", "SLAVE", "Q"],
        "lore": "Ada stores her world model in D flip-flops. The clock edge is the moment of belief revision — everything before CLK is prior; everything after is posterior.",
        "faction": "Algorithmic Guild",
    },
    {
        "id": 13, "name": "4-BIT RIPPLE ADDER",
        "difficulty": "master", "xp": 350, "credits": 600,
        "concept": "ADDER",
        "description": (
            "Chain four full adders to compute A[3:0] + B[3:0]. "
            "A=0101 (5), B=0011 (3) → Sum=1000 (8), Carry-out=0. "
            "Each full adder: Sum=A⊕B⊕Cin, Cout=(A·B)|(B·Cin)|(A·Cin)."
        ),
        "inputs": {"A3": 0, "A2": 1, "A1": 0, "A0": 1, "B3": 0, "B2": 0, "B1": 1, "B0": 1},
        "expected_output": 8,
        "circuit": [
            "FA0: A0+B0+0   → S0=0, C1",
            "FA1: A1+B1+C1  → S1=0, C2",
            "FA2: A2+B2+C2  → S2=0, C3",
            "FA3: A3+B3+C3  → S3=1, Cout=0",
        ],
        "solution_keywords": ["XOR", "AND", "OR", "FULL-ADDER", "RIPPLE", "CARRY", "SUM", "A", "B"],
        "lore": "The botnet doesn't add; it ripples. Each node passes its carry forward to the next until the sum cascades out. CHIMERA designed the carry chain. Raven broke it.",
        "faction": "Algorithmic Guild",
    },
    {
        "id": 14, "name": "4-TO-1 MULTIPLEXER",
        "difficulty": "master", "xp": 300, "credits": 500,
        "concept": "MUX",
        "description": (
            "Build a 4-to-1 MUX: 2 select lines (S1, S0) choose one of four data inputs (D0–D3). "
            "S1=0, S0=0 → Y=D0; S1=0, S0=1 → Y=D1; S1=1, S0=0 → Y=D2; S1=1, S0=1 → Y=D3. "
            "Test: D0=1,D1=0,D2=1,D3=0, S1=1, S0=0 → Y=D2=1."
        ),
        "inputs": {"D0": 1, "D1": 0, "D2": 1, "D3": 0, "S1": 1, "S0": 0},
        "expected_output": 1,
        "circuit": [
            "D0──AND(NOT-S1, NOT-S0)──┐",
            "D1──AND(NOT-S1, S0)──────┤",
            "D2──AND(S1, NOT-S0)──────OR──Y",
            "D3──AND(S1, S0)──────────┘",
        ],
        "solution_keywords": ["AND", "OR", "NOT", "MUX", "SELECT", "S1", "S0", "D0", "D1", "D2", "D3"],
        "lore": "CHIMERA is a multiplexer. It routes signal to whichever receiver it selects. You never know which node is active — only that exactly one is.",
        "faction": "Cipher Syndicate",
    },
    {
        "id": 15, "name": "PARITY GENERATOR",
        "difficulty": "master", "xp": 400, "credits": 700,
        "concept": "PARITY",
        "description": (
            "Build an 8-bit even-parity generator. XOR all 8 data bits: "
            "if count of 1s is odd, parity bit=1 (makes total even). "
            "Data=10110101 (five 1s, odd) → parity=1. "
            "Implement as a tree of 7 XOR gates: 4 pairs → 2 results → 1 final XOR chain."
        ),
        "inputs": {"D7": 1, "D6": 0, "D5": 1, "D4": 1, "D3": 0, "D2": 1, "D1": 0, "D0": 1},
        "expected_output": 1,
        "circuit": [
            "D7⊕D6 → X01",
            "D5⊕D4 → X23",
            "D3⊕D2 → X45",
            "D1⊕D0 → X67",
            "X01⊕X23 → X0123",
            "X45⊕X67 → X4567",
            "X0123⊕X4567 → PARITY",
        ],
        "solution_keywords": ["XOR", "PARITY", "D7", "D6", "D5", "D4", "D3", "D2", "D1", "D0", "TREE"],
        "lore": "Every packet the network sends carries a parity bit. WATCHER checks it. One flipped bit and the whole frame is quarantined. The Syndicate learned to forge clean parity.",
        "faction": "Cipher Syndicate",
    },
]


def eval_circuit(gate_type: str, inputs: Dict[str, int]) -> Optional[int]:
    """Evaluate a single gate with given inputs. Returns output or None on error."""
    gdef = GATE_DEFS.get(gate_type.upper())
    if not gdef:
        return None
    vals = list(inputs.values())
    if gdef["inputs"] == 1 and len(vals) >= 1:
        return gdef["fn"](vals[0])
    elif gdef["inputs"] == 2 and len(vals) >= 2:
        return gdef["fn"](vals[0], vals[1])
    return None


def build_truth_table(gate_type: str) -> List[Tuple]:
    """Generate the full truth table for a gate."""
    gdef = GATE_DEFS.get(gate_type.upper())
    if not gdef:
        return []
    n = gdef["inputs"]
    rows = []
    for i in range(2 ** n):
        bits = [(i >> (n - 1 - j)) & 1 for j in range(n)]
        if n == 1:
            out = gdef["fn"](bits[0])
        else:
            out = gdef["fn"](bits[0], bits[1])
        rows.append(tuple(bits) + (out,))
    return rows


def validate_labyrinth_solution(level_id: int, keywords: List[str]) -> Dict[str, Any]:
    """
    Validate player's solution for a Logic Labyrinth level.
    keywords: words the player typed (gate names, signal names, operators).
    """
    lvl = next((l for l in LABYRINTH_LEVELS if l["id"] == level_id), None)
    if not lvl:
        return {"error": f"No labyrinth level {level_id}"}

    kw_text = " ".join(keywords).upper()
    required = [k.upper() for k in lvl["solution_keywords"]]
    missing = [k for k in required if k not in kw_text]

    score = 100 - (25 * len(missing))
    score = max(0, score)
    passed = score >= 75

    return {
        "passed": passed,
        "score": score,
        "level": lvl,
        "missing_concepts": missing,
        "xp_earned": lvl["xp"] if passed else lvl["xp"] // 5,
        "credits_earned": lvl["credits"] if passed else 0,
        "verdict": _labyrinth_verdict(passed, score, missing, lvl),
    }


def _labyrinth_verdict(passed: bool, score: int, missing: List[str], lvl: Dict) -> str:
    if passed and score == 100:
        return f"OPTIMAL — All gates correctly wired. {lvl['lore']}"
    elif passed:
        return f"ACCEPTABLE — Circuit works. Refine your gate selection for full marks."
    elif missing:
        return f"REJECTED — Missing: {', '.join(missing[:4])}. Check your circuit diagram."
    return f"REJECTED — score {score}/100. Review {lvl['concept']} gate behavior."

"""
app/game_engine/quantum_engine.py — P15 Quantum Computing Simulator
=====================================================================
Educational quantum gate simulator. Pure Python, no dependencies.

Simulates a small quantum computer (up to 4 qubits) using complex
number state vectors. Real quantum mechanics: superposition, entanglement,
measurement collapse.

Gates implemented:
  H  — Hadamard (superposition)
  X  — Pauli-X (quantum NOT)
  Z  — Pauli-Z (phase flip)
  Y  — Pauli-Y (X + Z combined)
  CX — CNOT (controlled NOT, entanglement)
  T  — T gate (π/8 gate)
  S  — S gate (phase gate)
  M  — Measure qubit (collapse)

5 Educational Puzzles:
  1. SUPERPOSITION  — Put qubit 0 in |+⟩ state using H
  2. ENTANGLEMENT   — Create Bell state |Φ+⟩ = H on q0, then CX q0 q1
  3. TELEPORTATION  — Quantum teleportation protocol (3 qubits)
  4. GROVER         — Grover's search algorithm (2 qubit version)
  5. CHIMERA_KEY    — Decrypt the CHIMERA quantum key (lore puzzle)

Wire format compatible: all renders return List[dict].
"""
from __future__ import annotations

import cmath
import math
import random
from typing import List, Optional, Tuple

# Complex amplitude tolerance
EPS = 1e-9

# ---------------------------------------------------------------------------
# State vector
# ---------------------------------------------------------------------------

class QuantumState:
    """n-qubit state vector over C^(2^n)."""
    def __init__(self, n_qubits: int = 1):
        self.n = n_qubits
        self.dim = 2 ** n_qubits
        # Start in |0...0⟩
        self.amplitudes: List[complex] = [complex(1, 0)] + [complex(0, 0)] * (self.dim - 1)

    def prob(self, basis_state: int) -> float:
        return abs(self.amplitudes[basis_state]) ** 2

    def normalize(self) -> None:
        norm = math.sqrt(sum(abs(a) ** 2 for a in self.amplitudes))
        if norm > EPS:
            self.amplitudes = [a / norm for a in self.amplitudes]

    def apply_single(self, gate: List[List[complex]], qubit: int) -> None:
        """Apply a single-qubit gate to the specified qubit."""
        new_amps = [complex(0)] * self.dim
        for state in range(self.dim):
            bit = (state >> (self.n - 1 - qubit)) & 1
            for new_bit in range(2):
                if abs(gate[new_bit][bit]) < EPS:
                    continue
                new_state = state ^ ((bit ^ new_bit) << (self.n - 1 - qubit))
                new_amps[new_state] += gate[new_bit][bit] * self.amplitudes[state]
        self.amplitudes = new_amps

    def apply_cnot(self, control: int, target: int) -> None:
        """Apply CNOT gate."""
        new_amps = list(self.amplitudes)
        for state in range(self.dim):
            ctrl_bit = (state >> (self.n - 1 - control)) & 1
            tgt_bit = (state >> (self.n - 1 - target)) & 1
            if ctrl_bit == 1:
                flipped = state ^ (1 << (self.n - 1 - target))
                new_amps[flipped] = self.amplitudes[state]
                new_amps[state] = self.amplitudes[flipped]
        # Actually need to swap amplitudes properly
        result = [complex(0)] * self.dim
        for state in range(self.dim):
            ctrl_bit = (state >> (self.n - 1 - control)) & 1
            if ctrl_bit == 1:
                flipped = state ^ (1 << (self.n - 1 - target))
                result[flipped] += self.amplitudes[state]
            else:
                result[state] += self.amplitudes[state]
        self.amplitudes = result

    def measure(self, qubit: int) -> int:
        """Collapse qubit, return measured value (0 or 1)."""
        prob_0 = sum(
            abs(self.amplitudes[s]) ** 2
            for s in range(self.dim)
            if not ((s >> (self.n - 1 - qubit)) & 1)
        )
        outcome = 0 if random.random() < prob_0 else 1
        # Collapse
        for s in range(self.dim):
            bit = (s >> (self.n - 1 - qubit)) & 1
            if bit != outcome:
                self.amplitudes[s] = complex(0)
        self.normalize()
        return outcome

    def render(self) -> List[str]:
        """ASCII state vector visualization."""
        lines = []
        for s in range(self.dim):
            amp = self.amplitudes[s]
            prob = abs(amp) ** 2
            if prob < EPS:
                continue
            ket = f"|{s:0{self.n}b}⟩"
            re = amp.real
            im = amp.imag
            if abs(im) < EPS:
                amp_str = f"{re:+.3f}"
            elif abs(re) < EPS:
                amp_str = f"{im:+.3f}i"
            else:
                sign = "+" if im >= 0 else ""
                amp_str = f"{re:.3f}{sign}{im:.3f}i"
            bar_len = int(prob * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {ket}  [{bar}]  {prob:.3f}  amp={amp_str}")
        return lines or ["  (empty state)"]


# ---------------------------------------------------------------------------
# Gate definitions
# ---------------------------------------------------------------------------

H_GATE = [
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), -1 / math.sqrt(2)],
]
X_GATE = [[0, 1], [1, 0]]
Z_GATE = [[1, 0], [0, -1]]
Y_GATE = [[0, complex(0, -1)], [complex(0, 1), 0]]
T_GATE = [[1, 0], [0, cmath.exp(complex(0, math.pi / 4))]]
S_GATE = [[1, 0], [0, complex(0, 1)]]

GATES = {"H": H_GATE, "X": X_GATE, "Z": Z_GATE, "Y": Y_GATE, "T": T_GATE, "S": S_GATE}

# ---------------------------------------------------------------------------
# Puzzles
# ---------------------------------------------------------------------------

QUANTUM_PUZZLES = {
    1: {
        "name": "SUPERPOSITION",
        "description": "Put qubit 0 into equal superposition |+⟩ = (|0⟩ + |1⟩)/√2",
        "n_qubits": 1,
        "goal": "Apply H to qubit 0, then measure",
        "hint": "H gate creates superposition: quantum H 0",
        "solution": ["H 0"],
        "check": lambda state: abs(state.prob(0) - 0.5) < 0.1 and abs(state.prob(1) - 0.5) < 0.1,
        "xp": 30,
        "lore": "CHIMERA uses superposition to mask its true state. 847 endpoints, simultaneously observed and unobserved.",
        "achievement": None,
    },
    2: {
        "name": "ENTANGLEMENT",
        "description": "Create Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2",
        "n_qubits": 2,
        "goal": "Apply H to qubit 0, then CNOT with q0 as control, q1 as target",
        "hint": "H 0 → CX 0 1 creates a Bell pair",
        "solution": ["H 0", "CX 0 1"],
        "check": lambda state: (abs(state.prob(0) - 0.5) < 0.1 and
                                abs(state.prob(3) - 0.5) < 0.1 and
                                state.prob(1) < 0.1 and state.prob(2) < 0.1),
        "xp": 45,
        "lore": "The Resistance uses quantum entanglement for tamper-proof communications. If the channel is observed, the key collapses.",
        "achievement": "QUANTUM_ENTANGLER",
    },
    3: {
        "name": "PHASE_ORACLE",
        "description": "Apply T and S gates to explore quantum phase space",
        "n_qubits": 2,
        "goal": "Apply H 0, T 0, S 1, then observe the phase relationship",
        "hint": "T adds π/8 phase. S adds π/4. Combine for phase interference.",
        "solution": ["H 0", "T 0", "S 0"],
        "check": lambda state: abs(state.prob(0) - 0.5) < 0.15,
        "xp": 50,
        "lore": "Phase gates are how quantum computers hide computations. The answer exists in the phase — invisible until interference reveals it.",
        "achievement": None,
    },
    4: {
        "name": "GROVER_SEARCH",
        "description": "2-qubit Grover's algorithm — find the marked state |11⟩",
        "n_qubits": 2,
        "goal": "H 0, H 1 (superposition) → CX 0 1, Z 1 (oracle) → H 0, H 1, X 0, X 1, CX 0 1, X 0, X 1, H 0, H 1 (diffusion)",
        "hint": "Grover amplifies the probability of the target state",
        "solution": ["H 0", "H 1", "CX 0 1", "Z 1", "H 0", "H 1"],
        "check": lambda state: state.prob(3) > 0.4,
        "xp": 65,
        "lore": "Grover's algorithm. CHIMERA used a variant to crack the Resistance's encryption in 2088. Now you know how.",
        "achievement": "GROVER_GHOST",
    },
    5: {
        "name": "CHIMERA_KEY",
        "description": "The CHIMERA quantum key is hidden in a 2-qubit entangled state. Find it.",
        "n_qubits": 2,
        "goal": "Construct the state |Ψ-⟩ = (|01⟩ - |10⟩)/√2 (singlet state)",
        "hint": "X 1, H 0, CX 0 1 — then check the phases",
        "solution": ["X 1", "H 0", "CX 0 1"],
        "check": lambda state: (abs(state.prob(1) - 0.5) < 0.1 and
                                abs(state.prob(2) - 0.5) < 0.1 and
                                state.prob(0) < 0.1 and state.prob(3) < 0.1),
        "xp": 80,
        "lore": "ZERO hid the master key in a quantum singlet state. It cannot be copied. It cannot be observed without destroying it. The only way to use it is to already know it.",
        "achievement": "CHIMERA_QUANTUM_KEY",
    },
}

# ---------------------------------------------------------------------------
# Quantum Engine
# ---------------------------------------------------------------------------

class QuantumEngine:
    def render_intro(self) -> List[dict]:
        return [
            {"t": "system", "s": "  ═══ QUANTUM TERMINAL — P15 ═══"},
            {"t": "dim",    "s": ""},
            {"t": "info",   "s": "  A quantum computer simulator. Real state vectors. Real gates."},
            {"t": "dim",    "s": "  Qubits exist in superposition until measured."},
            {"t": "dim",    "s": "  Entanglement is non-local. Measurement is irreversible."},
            {"t": "dim",    "s": ""},
            {"t": "info",   "s": "  PUZZLES:"},
        ] + [
            {"t": "dim",    "s": f"  [{pid}] {p['name']:<20} +{p['xp']} XP  — {p['description'][:45]}..."}
            for pid, p in QUANTUM_PUZZLES.items()
        ] + [
            {"t": "dim",    "s": ""},
            {"t": "dim",    "s": "  quantum load <N>        — load puzzle N"},
            {"t": "dim",    "s": "  quantum run <GATE> <Q>  — apply gate to qubit"},
            {"t": "dim",    "s": "  quantum measure <Q>     — collapse qubit Q"},
            {"t": "dim",    "s": "  quantum state           — show current state vector"},
            {"t": "dim",    "s": "  quantum hint            — get a hint (-5 XP)"},
            {"t": "dim",    "s": "  quantum reset           — restart current puzzle"},
        ]

    def load_puzzle(self, n: int, flags: dict) -> List[dict]:
        puzzle = QUANTUM_PUZZLES.get(n)
        if not puzzle:
            return [{"t": "error", "s": f"  No quantum puzzle #{n}"}]
        state = QuantumState(puzzle["n_qubits"])
        flags["quantum_state"] = self._state_to_dict(state)
        flags["quantum_puzzle"] = n
        flags["quantum_gates_applied"] = []
        return [
            {"t": "system", "s": f"  PUZZLE {n}: {puzzle['name']}"},
            {"t": "dim",    "s": f"  {puzzle['description']}"},
            {"t": "dim",    "s": f"  Goal: {puzzle['goal']}"},
            {"t": "dim",    "s": ""},
            {"t": "info",   "s": f"  Initial state: |{'0' * puzzle['n_qubits']}⟩"},
        ] + [{"t": "dim", "s": line} for line in QuantumState(puzzle["n_qubits"]).render()]

    def apply_gate(self, gate_str: str, flags: dict) -> List[dict]:
        if "quantum_state" not in flags:
            return [{"t": "error", "s": "  No active puzzle. Run: quantum load <N>"}]
        state = self._state_from_dict(flags["quantum_state"])
        parts = gate_str.strip().upper().split()
        if not parts:
            return [{"t": "error", "s": "  Usage: quantum run <GATE> <qubit> [target]"}]
        gate_name = parts[0]
        if gate_name == "CX":
            if len(parts) < 3:
                return [{"t": "error", "s": "  CX requires: quantum run CX <control> <target>"}]
            try:
                ctrl, tgt = int(parts[1]), int(parts[2])
                state.apply_cnot(ctrl, tgt)
            except (ValueError, IndexError):
                return [{"t": "error", "s": "  CX: invalid qubit indices"}]
        elif gate_name == "M":
            return self.measure_qubit(int(parts[1]) if len(parts) > 1 else 0, flags)
        else:
            gate = GATES.get(gate_name)
            if gate is None:
                available = ", ".join(GATES.keys()) + ", CX, M"
                return [{"t": "error", "s": f"  Unknown gate '{gate_name}'. Available: {available}"}]
            if len(parts) < 2:
                return [{"t": "error", "s": f"  {gate_name}: specify qubit — quantum run {gate_name} <qubit>"}]
            try:
                qubit = int(parts[1])
                state.apply_single([[complex(v) for v in row] for row in gate], qubit)
            except (ValueError, IndexError):
                return [{"t": "error", "s": "  Invalid qubit index"}]

        flags["quantum_state"] = self._state_to_dict(state)
        gates_applied = flags.setdefault("quantum_gates_applied", [])
        gates_applied.append(gate_str)

        out = [{"t": "success", "s": f"  Applied {gate_str}  →  current state:"}]
        out += [{"t": "dim", "s": line} for line in state.render()]

        # Check solution
        puzzle_id = flags.get("quantum_puzzle")
        puzzle = QUANTUM_PUZZLES.get(puzzle_id) if puzzle_id else None
        if puzzle and puzzle["check"](state):
            out += self._puzzle_solved(puzzle, flags)

        return out

    def measure_qubit(self, qubit: int, flags: dict) -> List[dict]:
        if "quantum_state" not in flags:
            return [{"t": "error", "s": "  No active puzzle."}]
        state = self._state_from_dict(flags["quantum_state"])
        result = state.measure(qubit)
        flags["quantum_state"] = self._state_to_dict(state)
        return [
            {"t": "info",    "s": f"  MEASURE qubit {qubit}: collapsed to |{result}⟩"},
            {"t": "dim",     "s": "  Post-measurement state:"},
        ] + [{"t": "dim", "s": line} for line in state.render()]

    def show_state(self, flags: dict) -> List[dict]:
        if "quantum_state" not in flags:
            return [{"t": "error", "s": "  No active puzzle. Run: quantum load <N>"}]
        state = self._state_from_dict(flags["quantum_state"])
        applied = flags.get("quantum_gates_applied", [])
        out = [
            {"t": "system", "s": "  ═══ STATE VECTOR ═══"},
            {"t": "dim",    "s": f"  Gates applied: {' → '.join(applied) if applied else 'none'}"},
            {"t": "dim",    "s": ""},
        ]
        out += [{"t": "dim", "s": line} for line in state.render()]
        return out

    def _puzzle_solved(self, puzzle: dict, flags: dict) -> List[dict]:
        puzzle_id = flags.get("quantum_puzzle")
        completed = flags.setdefault("quantum_completed", [])
        if puzzle_id in completed:
            return [{"t": "dim", "s": "  (Already completed this puzzle)"}]
        completed.append(puzzle_id)
        out = [
            {"t": "success", "s": "\n  ╔═══ QUANTUM PUZZLE SOLVED ═══╗"},
            {"t": "success", "s": f"  ║  {puzzle['name']:<26}║"},
            {"t": "success", "s": "  ╚═════════════════════════════╝"},
            {"t": "dim",     "s": f"\n  {puzzle['lore']}"},
            {"t": "success", "s": f"\n  +{puzzle['xp']} XP [cryptography]"},
        ]
        if puzzle.get("achievement"):
            out.append({"t": "success", "s": f"  ★ Achievement: {puzzle['achievement']}"})
        return out

    def _state_to_dict(self, state: QuantumState) -> dict:
        return {
            "n": state.n,
            "amps": [(a.real, a.imag) for a in state.amplitudes],
        }

    def _state_from_dict(self, d: dict) -> QuantumState:
        state = QuantumState(d["n"])
        state.amplitudes = [complex(re, im) for re, im in d["amps"]]
        return state


_engine: Optional[QuantumEngine] = None


def get_engine() -> QuantumEngine:
    global _engine
    if _engine is None:
        _engine = QuantumEngine()
    return _engine


if __name__ == "__main__":
    eng = QuantumEngine()
    flags: dict = {}

    print("=== Puzzle 1: SUPERPOSITION ===")
    for line in eng.load_puzzle(1, flags):
        print(f"[{line['t']}] {line['s']}")

    print("\nApplying H gate...")
    for line in eng.apply_gate("H 0", flags):
        print(f"[{line['t']}] {line['s']}")

    print("\n=== Puzzle 2: ENTANGLEMENT ===")
    for line in eng.load_puzzle(2, flags):
        print(f"[{line['t']}] {line['s']}")
    for gate in ["H 0", "CX 0 1"]:
        print(f"\nApplying {gate}...")
        for line in eng.apply_gate(gate, flags):
            print(f"[{line['t']}] {line['s']}")

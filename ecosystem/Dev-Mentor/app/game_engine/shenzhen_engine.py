"""
shenzhen_engine.py — Shenzhen I/O Puzzle Engine for Terminal Depths

CHIMERA-fabricated microcontrollers recovered from Node-7's hardware layer.
Zod-Prime reverse-engineered the instruction set. Five levels of increasing
difficulty, each requiring assembly programs to satisfy I/O specifications.

Chip types:
  MC4000  — 2 registers, 1 pin, 9 instruction slots
  MC6000  — 4 registers, 2 pins, 14 instruction slots
  MC4000X — 3 registers (includes DX), 1 pin, 9 instruction slots
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Terminal Depths output helpers
# ---------------------------------------------------------------------------

def _sys(s: str) -> dict:
    return {"t": "system", "s": s}


def _dim(s: str) -> dict:
    return {"t": "dim", "s": s}


def _ok(s: str) -> dict:
    return {"t": "success", "s": s}


def _err(s: str) -> dict:
    return {"t": "error", "s": s}


def _warn(s: str) -> dict:
    return {"t": "warn", "s": s}


def _info(s: str) -> dict:
    return {"t": "info", "s": s}


def _lore(s: str) -> dict:
    return {"t": "lore", "s": s}


def _line(s: str, t: str = "output") -> dict:
    return {"t": t, "s": s}


# ---------------------------------------------------------------------------
# Chip register limits by type
# ---------------------------------------------------------------------------

CHIP_SPECS: dict[str, dict] = {
    "MC4000": {
        "regs": ["acc", "dat"],
        "pins": ["p0"],
        "xin": True,
        "xout": True,
        "max_instructions": 9,
        "description": (
            "Simple-I/O microcontroller. "
            "2 registers, 1 pin, 9 instruction slots."
        ),
    },
    "MC6000": {
        "regs": ["acc", "dat", "r0", "r1"],
        "pins": ["p0", "p1"],
        "xin": True,
        "xout": True,
        "max_instructions": 14,
        "description": (
            "Dual-I/O microcontroller. "
            "4 registers, 2 pins, 14 instruction slots."
        ),
    },
    "MC4000X": {
        "regs": ["acc", "dat", "dx"],
        "pins": ["p0"],
        "xin": True,
        "xout": True,
        "max_instructions": 9,
        "description": (
            "Extended MC4000. "
            "3 registers (includes DX), 1 pin, 9 instruction slots."
        ),
    },
}

# ---------------------------------------------------------------------------
# Level definitions
# ---------------------------------------------------------------------------

SHENZHEN_LEVELS: list[dict] = [
    {
        "id": 1,
        "title": "BLINK",
        "chip_type": "MC4000",
        "difficulty": "novice",
        "xp": 30,
        "credit_reward": 50,
        "description": (
            "Make pin p0 pulse high for 1 cycle, then low for 1 cycle, "
            "repeating indefinitely. This is the simplest useful program — "
            "a heartbeat signal for downstream components."
        ),
        "spec": {
            "p0_pattern": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
            "cycles_to_check": 10,
            "inputs": [],
        },
        "solution_hint": (
            "gen p0 1 1  — pulse p0 high for 1 cycle, low for 1 cycle, forever."
        ),
        "reference_solution": "gen p0 1 1",
        "lore": (
            "CHIMERA-SHEN-001: The first program any technician learns. "
            "A pin that blinks is a chip that breathes."
        ),
    },
    {
        "id": 2,
        "title": "ADD FILTER",
        "chip_type": "MC4000",
        "difficulty": "novice",
        "xp": 50,
        "credit_reward": 80,
        "description": (
            "Read values from XIN. If the value is greater than 0, write it "
            "to XOUT unchanged. If the value is 0 or negative, write 0 to "
            "XOUT. This circuit strips negative noise from a sensor feed."
        ),
        "spec": {
            "xin_values": [5, -3, 0, 7, -1, 2, 0, -9, 4, 1],
            "xout_expected": [5, 0, 0, 7, 0, 2, 0, 0, 4, 1],
            "cycles_to_check": 10,
            "inputs": [5, -3, 0, 7, -1, 2, 0, -9, 4, 1],
        },
        "solution_hint": (
            "mov xin acc\n"
            "tgt acc 0\n"
            "+ mov acc xout\n"
            "- mov 0 xout"
        ),
        "reference_solution": (
            "mov xin acc\n"
            "tgt acc 0\n"
            "+ mov acc xout\n"
            "- mov 0 xout"
        ),
        "lore": (
            "CHIMERA-SHEN-002: Sensor feeds from Node-7's outer ring carry "
            "ghost values — negative artefacts from decayed shielding. "
            "Filter them before they corrupt the accumulator chain."
        ),
    },
    {
        "id": 3,
        "title": "COMPARATOR",
        "chip_type": "MC6000",
        "difficulty": "intermediate",
        "xp": 80,
        "credit_reward": 120,
        "description": (
            "Read a value from pin p0 and a value from pin p1 each cycle. "
            "If p0 > p1, write 1 to XOUT. Otherwise write 0. "
            "Used to drive a downstream multiplexer selection line."
        ),
        "spec": {
            "p0_values": [5, 2, 7, 3, 1, 9],
            "p1_values": [3, 4, 7, 1, 8, 9],
            "xout_expected": [1, 0, 0, 1, 0, 0],
            "cycles_to_check": 6,
            "inputs": [],
        },
        "solution_hint": (
            "mov p0 acc\n"
            "mov p1 dat\n"
            "tgt acc dat\n"
            "+ mov 100 xout\n"
            "- mov 0 xout"
        ),
        "reference_solution": (
            "mov p0 acc\n"
            "mov p1 dat\n"
            "tgt acc dat\n"
            "+ mov 100 xout\n"
            "- mov 0 xout"
        ),
        "lore": (
            "CHIMERA-SHEN-003: Every decision reduces to a comparison. "
            "Greater-than, less-than, equal — the three pillars of logic that "
            "Zod-Prime claims predate language itself."
        ),
    },
    {
        "id": 4,
        "title": "COUNTER MOD 5",
        "chip_type": "MC4000X",
        "difficulty": "advanced",
        "xp": 110,
        "credit_reward": 175,
        "description": (
            "Output the sequence 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, ... to XOUT "
            "indefinitely. Each value occupies one cycle. "
            "Used to index into a 5-slot rotating buffer."
        ),
        "spec": {
            "xout_expected": [0, 1, 2, 3, 4, 0, 1, 2, 3, 4],
            "cycles_to_check": 10,
            "inputs": [],
        },
        "solution_hint": (
            "mov 0 acc\n"
            "lp: mov acc xout\n"
            "add 1\n"
            "teq acc 5\n"
            "+ mov 0 acc\n"
            "jmp lp"
        ),
        "reference_solution": (
            "mov 0 acc\n"
            "lp: mov acc xout\n"
            "add 1\n"
            "teq acc 5\n"
            "+ mov 0 acc\n"
            "jmp lp"
        ),
        "lore": (
            "CHIMERA-SHEN-004: Five is not arbitrary. Node-7's rotating cache "
            "was partitioned into exactly 5 slots by whoever built it. "
            "Ada believes the number has symbolic meaning. She's probably right."
        ),
    },
    {
        "id": 5,
        "title": "CROSS-CHIP COMM",
        "chip_type": "MC6000",
        "difficulty": "expert",
        "xp": 200,
        "credit_reward": 300,
        "description": (
            "Two-chip coordination challenge.\n"
            "CHIP-A reads values from XIN and signals CHIP-B via p0 "
            "(high = positive, low = negative).\n"
            "CHIP-B reads the p0 signal and writes |value| to XOUT if "
            "positive, or 0 if negative.\n"
            "Submit solution for CHIP-A and CHIP-B separated by '---'."
        ),
        "spec": {
            "xin_values": [4, -2, 7, 0, -5, 3],
            "xout_expected": [4, 0, 7, 0, 0, 3],
            "cycles_to_check": 6,
            "inputs": [4, -2, 7, 0, -5, 3],
            "multi_chip": True,
        },
        "solution_hint": (
            "# CHIP-A:\n"
            "mov xin acc\n"
            "mov acc dat\n"
            "tgt acc 0\n"
            "+ mov 100 p0\n"
            "- mov 0 p0\n"
            "# --- (separator) ---\n"
            "# CHIP-B:\n"
            "slx p0\n"
            "teq p0 100\n"
            "+ mov dat xout\n"
            "- mov 0 xout"
        ),
        "reference_solution": (
            "mov xin acc\n"
            "mov acc dat\n"
            "tgt acc 0\n"
            "+ mov 100 p0\n"
            "- mov 0 p0\n"
            "---\n"
            "slx p0\n"
            "teq p0 100\n"
            "+ mov dat xout\n"
            "- mov 0 xout"
        ),
        "lore": (
            "CHIMERA-SHEN-005: The hardest part of distributed systems is not "
            "computation — it is communication. Chip A knows the value; Chip B "
            "controls the output. They must speak a shared language in one cycle."
        ),
    },
]


# ---------------------------------------------------------------------------
# VM state for a single chip
# ---------------------------------------------------------------------------

@dataclass
class ChipState:
    """Runtime state for one simulated Shenzhen I/O chip."""

    chip_type: str
    acc: int = 0
    dat: int = 0
    dx: int = 0
    r0: int = 0
    r1: int = 0
    # Pins: int in range 0-100 (Shenzhen's signal range)
    p0: int = 0
    p1: int = 0
    xin_queue: list[int] = field(default_factory=list)
    xout_list: list[int] = field(default_factory=list)
    # Conditional execution: None = no test, True = + branch, False = - branch
    cond: Optional[bool] = None
    ip: int = 0
    labels: dict[str, int] = field(default_factory=dict)
    sleep_cycles: int = 0
    # gen instruction state machine
    gen_pin: str = ""
    gen_high_remaining: int = 0
    gen_low_remaining: int = 0
    halted: bool = False
    error: Optional[str] = None

    def read_reg(self, name: str) -> int:
        name = name.lower()
        if name == "acc":
            return self.acc
        if name == "dat":
            return self.dat
        if name == "dx":
            return self.dx
        if name == "r0":
            return self.r0
        if name == "r1":
            return self.r1
        if name == "p0":
            return self.p0
        if name == "p1":
            return self.p1
        raise ValueError(f"Unknown register: {name}")

    def write_reg(self, name: str, value: int) -> None:
        value = max(-999, min(999, value))
        name = name.lower()
        if name == "acc":
            self.acc = value
        elif name == "dat":
            self.dat = value
        elif name == "dx":
            self.dx = value
        elif name == "r0":
            self.r0 = value
        elif name == "r1":
            self.r1 = value
        elif name == "p0":
            self.p0 = value
        elif name == "p1":
            self.p1 = value
        else:
            raise ValueError(f"Cannot write to: {name}")


# ---------------------------------------------------------------------------
# Instruction parser
# ---------------------------------------------------------------------------

_COMMENT_RE = re.compile(r"#.*$")
_LABEL_RE = re.compile(r"^([A-Za-z_]\w*):\s*(.*)")

# Type alias for a parsed instruction
Instr = tuple[str, list[str], Optional[bool]]


def _parse_program(code: str) -> tuple[list[Instr], dict[str, int]]:
    """
    Parse assembly source into (mnemonic, args, cond_flag) tuples plus a
    label->instruction_index mapping.

    cond_flag: None = unconditional, True = '+' branch, False = '-' branch
    """
    instructions: list[Instr] = []
    labels: dict[str, int] = {}

    for raw_line in code.splitlines():
        line = _COMMENT_RE.sub("", raw_line).strip()
        if not line:
            continue

        cond: Optional[bool] = None
        if line.startswith("+ "):
            cond = True
            line = line[2:].strip()
        elif line.startswith("- "):
            cond = False
            line = line[2:].strip()

        m = _LABEL_RE.match(line)
        if m:
            label_name = m.group(1).lower()
            remainder = m.group(2).strip()
            labels[label_name] = len(instructions)
            if not remainder:
                continue
            line = remainder

        parts = line.split()
        mnemonic = parts[0].lower()
        args = parts[1:]
        instructions.append((mnemonic, args, cond))

    return instructions, labels


def _resolve_value(token: str, state: ChipState) -> int:
    """Resolve a token to an integer (literal or register read)."""
    token = token.lower()
    try:
        return int(token)
    except ValueError:
        pass
    if token == "xin":
        if not state.xin_queue:
            raise RuntimeError("xin: no more input values")
        return state.xin_queue.pop(0)
    return state.read_reg(token)


# ---------------------------------------------------------------------------
# Instruction executor
# ---------------------------------------------------------------------------

def _execute_instruction(
    instr: Instr,
    state: ChipState,
    labels: dict[str, int],
) -> None:
    """Execute one instruction, mutating state in place."""
    mnemonic, args, cond_flag = instr

    # Evaluate conditional branch: skip if condition doesn't match
    if cond_flag is not None:
        if state.cond is None or state.cond != cond_flag:
            state.ip += 1
            return

    def _arg(i: int) -> str:
        if i >= len(args):
            raise RuntimeError(f"{mnemonic}: missing argument {i}")
        return args[i]

    def _val(i: int) -> int:
        return _resolve_value(_arg(i), state)

    def _dst(i: int) -> str:
        return _arg(i).lower()

    def _jump(target: str) -> None:
        tgt = target.lower()
        if tgt in labels:
            state.ip = labels[tgt]
        else:
            state.ip = int(tgt)

    if mnemonic == "nop":
        state.ip += 1
        return

    elif mnemonic == "mov":
        src_val = _val(0)
        dst = _dst(1)
        if dst == "xout":
            state.xout_list.append(src_val)
        else:
            state.write_reg(dst, src_val)

    elif mnemonic == "add":
        state.acc = max(-999, min(999, state.acc + _val(0)))

    elif mnemonic == "sub":
        state.acc = max(-999, min(999, state.acc - _val(0)))

    elif mnemonic == "mul":
        state.acc = max(-999, min(999, state.acc * _val(0)))

    elif mnemonic == "not":
        state.acc = 0 if state.acc != 0 else 100

    elif mnemonic == "dgt":
        n = _val(0)
        state.acc = (abs(state.acc) // (10 ** n)) % 10

    elif mnemonic == "dst":
        n = _val(0)
        v = _val(1)
        place = 10 ** n
        state.acc = state.acc - (state.acc // place % 10) * place + v * place

    # --- Tests ---
    elif mnemonic == "teq":
        state.cond = (_val(0) == _val(1))

    elif mnemonic == "tgt":
        state.cond = (_val(0) > _val(1))

    elif mnemonic == "tlt":
        state.cond = (_val(0) < _val(1))

    elif mnemonic == "tcp":
        a, b = _val(0), _val(1)
        if a > b:
            state.cond = True
        elif a < b:
            state.cond = False
        else:
            state.cond = None

    elif mnemonic == "teg":
        state.cond = (_val(0) >= _val(1))

    # --- Jumps ---
    elif mnemonic == "jmp":
        _jump(_arg(0))
        return

    elif mnemonic in ("jeq", "jne", "jlt", "jgt"):
        a, b = _val(0), _val(1)
        should_jump = (
            (mnemonic == "jeq" and a == b)
            or (mnemonic == "jne" and a != b)
            or (mnemonic == "jlt" and a < b)
            or (mnemonic == "jgt" and a > b)
        )
        if should_jump:
            _jump(_arg(2))
            return

    # --- Sleep / pin wait ---
    elif mnemonic == "slp":
        state.sleep_cycles = max(0, _val(0) - 1)

    elif mnemonic == "slx":
        # The outer loop already drives pin registers from external queues
        # each cycle, so slx just reads the current pin value — no queue pop.
        pass

    # --- gen: generate pulse on pin ---
    elif mnemonic == "gen":
        # Set up the gen state machine; the outer loop drives it cycle-by-cycle.
        # Current cycle counts as the first high cycle.
        pin = _arg(0).lower()
        high_n = _val(1)
        low_n = _val(2)
        state.gen_pin = pin
        state.gen_high_remaining = max(0, high_n - 1)
        state.gen_low_remaining = low_n
        state.write_reg(pin, 100)
        state.ip += 1
        return

    else:
        raise RuntimeError(f"Unknown mnemonic: '{mnemonic}'")

    state.ip += 1


# ---------------------------------------------------------------------------
# Main simulator
# ---------------------------------------------------------------------------

def _simulate_chip(
    code: str,
    chip_type: str,
    xin_values: list[int],
    p0_inputs: Optional[list[int]] = None,
    p1_inputs: Optional[list[int]] = None,
    max_cycles: int = 200,
    target_outputs: int = 0,
) -> dict:
    """
    Simulate a single chip running `code`.

    Returns:
        {cycles, xout, p0_trace, p1_trace, error}
    """
    try:
        program, labels = _parse_program(code)
    except Exception as e:
        return {
            "cycles": 0, "xout": [], "p0_trace": [], "p1_trace": [],
            "error": f"Parse error: {e}",
        }

    if not program:
        return {
            "cycles": 0, "xout": [], "p0_trace": [], "p1_trace": [],
            "error": "No instructions parsed.",
        }

    state = ChipState(chip_type=chip_type, xin_queue=list(xin_values))
    state.labels = labels

    p0_q = list(p0_inputs) if p0_inputs else []
    p1_q = list(p1_inputs) if p1_inputs else []

    p0_trace: list[int] = []
    p1_trace: list[int] = []
    xout_clean: list[int] = []

    cycles = 0
    while cycles < max_cycles:
        cycles += 1

        # gen state machine: drive pin high/low over time
        if state.gen_high_remaining > 0:
            state.write_reg(state.gen_pin, 100)
            state.gen_high_remaining -= 1
            p0_trace.append(state.p0)
            p1_trace.append(state.p1)
            continue

        if state.gen_low_remaining > 0:
            state.write_reg(state.gen_pin, 0)
            state.gen_low_remaining -= 1
            p0_trace.append(state.p0)
            p1_trace.append(state.p1)
            if state.gen_low_remaining == 0:
                state.ip = 0  # restart for infinite loop
            continue

        if state.sleep_cycles > 0:
            state.sleep_cycles -= 1
            p0_trace.append(state.p0)
            p1_trace.append(state.p1)
            continue

        if state.ip >= len(program):
            state.ip = 0  # wrap for infinite-loop chips

        # Drive external pin inputs once per program iteration (at ip == 0),
        # so the value is stable across all instructions of one processing cycle.
        if state.ip == 0:
            if p0_q:
                state.p0 = p0_q.pop(0)
            if p1_q:
                state.p1 = p1_q.pop(0)

        instr = program[state.ip]
        before = len(state.xout_list)
        try:
            _execute_instruction(instr, state, labels)
        except RuntimeError as e:
            return {
                "cycles": cycles,
                "xout": xout_clean,
                "p0_trace": p0_trace,
                "p1_trace": p1_trace,
                "error": f"Cycle {cycles}: {e}",
            }

        for entry in state.xout_list[before:]:
            xout_clean.append(int(entry))  # type: ignore[arg-type]

        p0_trace.append(state.p0)
        p1_trace.append(state.p1)

        if target_outputs > 0 and len(xout_clean) >= target_outputs:
            break

    return {
        "cycles": cycles,
        "xout": xout_clean,
        "p0_trace": p0_trace,
        "p1_trace": p1_trace,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Level 5: two-chip simulation
# ---------------------------------------------------------------------------

def _simulate_two_chips(
    code_a: str,
    code_b: str,
    xin_values: list[int],
    max_cycles: int = 200,
) -> dict:
    """
    Simulate Chip A and Chip B in lockstep.
    Chip A reads XIN, signals p0 to Chip B.
    Chip B reads p0 from Chip A, writes to XOUT.
    """
    try:
        prog_a, labels_a = _parse_program(code_a)
        prog_b, labels_b = _parse_program(code_b)
    except Exception as e:
        return {"cycles": 0, "xout": [], "error": f"Parse error: {e}"}

    state_a = ChipState(chip_type="MC6000", xin_queue=list(xin_values))
    state_a.labels = labels_a
    state_b = ChipState(chip_type="MC6000")
    state_b.labels = labels_b

    xout_result: list[int] = []
    cycles = 0

    while cycles < max_cycles and len(xout_result) < len(xin_values):
        cycles += 1

        if state_a.ip < len(prog_a):
            try:
                _execute_instruction(prog_a[state_a.ip], state_a, labels_a)
            except RuntimeError as e:
                return {
                    "cycles": cycles, "xout": xout_result,
                    "error": f"Chip-A cycle {cycles}: {e}",
                }
        else:
            state_a.ip = 0

        # Transfer p0 and dat bus from Chip A to Chip B
        state_b.p0 = state_a.p0
        state_b.dat = state_a.dat

        if state_b.ip < len(prog_b):
            before_b = len(state_b.xout_list)
            try:
                _execute_instruction(prog_b[state_b.ip], state_b, labels_b)
            except RuntimeError as e:
                return {
                    "cycles": cycles, "xout": xout_result,
                    "error": f"Chip-B cycle {cycles}: {e}",
                }
            for v in state_b.xout_list[before_b:]:
                if not isinstance(v, tuple):
                    xout_result.append(int(v))  # type: ignore[arg-type]
        else:
            state_b.ip = 0

    return {"cycles": cycles, "xout": xout_result, "error": None}


# ---------------------------------------------------------------------------
# ShenzhenEngine public API
# ---------------------------------------------------------------------------

class ShenzhenEngine:
    """Public API for the Shenzhen I/O puzzle system."""

    @staticmethod
    def get_level(n: int) -> dict:
        """Return the raw level dict for level n (1-indexed)."""
        if n < 1 or n > len(SHENZHEN_LEVELS):
            raise ValueError(
                f"Level {n} does not exist (1-{len(SHENZHEN_LEVELS)})"
            )
        return SHENZHEN_LEVELS[n - 1]

    @staticmethod
    def render_level(n: int) -> list[dict]:
        """Return Terminal Depths output format for a level briefing."""
        lvl = ShenzhenEngine.get_level(n)
        chip = CHIP_SPECS.get(lvl["chip_type"], {})
        spec = lvl["spec"]
        out: list[dict] = []

        out.append(_sys(f"╔══ SHENZHEN I/O — LEVEL {n}: {lvl['title']} ══╗"))
        out.append(_dim(
            f"  Chip : {lvl['chip_type']}  "
            f"({chip.get('description', '')})"
        ))
        out.append(_dim(
            f"  Diff : {lvl['difficulty'].upper()}"
            f"   XP: {lvl['xp']}   \u00a2{lvl['credit_reward']}"
        ))
        out.append(_line(""))
        out.append(_info("MISSION:"))
        for line in lvl["description"].splitlines():
            out.append(_line(f"  {line}"))
        out.append(_line(""))

        if spec.get("xin_values"):
            out.append(_dim(f"  XIN  : {spec['xin_values']}"))
        if spec.get("xout_expected"):
            out.append(_dim(f"  XOUT : {spec['xout_expected']}"))
        if spec.get("p0_pattern"):
            out.append(_dim(
                f"  p0   : {spec['p0_pattern']} "
                f"(first {spec['cycles_to_check']} cycles)"
            ))
        if spec.get("p0_values"):
            out.append(_dim(f"  p0\u2191  : {spec['p0_values']}"))
        if spec.get("p1_values"):
            out.append(_dim(f"  p1\u2191  : {spec['p1_values']}"))

        out.append(_line(""))
        out.append(_lore(lvl["lore"]))
        out.append(_line(""))
        out.append(_info("HINT:"))
        for hint_line in lvl["solution_hint"].splitlines():
            out.append(_dim(f"  {hint_line}"))
        out.append(_line(""))
        out.append(_sys("Submit with: shenzhen submit <level>"))
        out.append(_dim("Paste your assembly, then type END on its own line."))

        return out

    @staticmethod
    def simulate(
        code: str,
        chip_type: str,
        inputs: list[int],
        p0_inputs: Optional[list[int]] = None,
        p1_inputs: Optional[list[int]] = None,
        max_cycles: int = 200,
    ) -> dict:
        """
        Run a raw simulation and return results.

        Returns: {cycles, outputs, p0_trace, p1_trace, error}
        """
        result = _simulate_chip(
            code, chip_type, inputs,
            p0_inputs=p0_inputs,
            p1_inputs=p1_inputs,
            max_cycles=max_cycles,
        )
        return {
            "cycles": result["cycles"],
            "outputs": result["xout"],
            "p0_trace": result["p0_trace"],
            "p1_trace": result["p1_trace"],
            "error": result["error"],
        }

    @staticmethod
    def submit_solution(n: int, code: str) -> dict:
        """
        Validate a player's assembly solution for level n.

        Returns: {success, message, output}
        """
        try:
            lvl = ShenzhenEngine.get_level(n)
        except ValueError as e:
            return {"success": False, "message": str(e), "output": [_err(str(e))]}

        spec = lvl["spec"]
        chip = lvl["chip_type"]
        output: list[dict] = []
        output.append(_sys(f"► Running simulation — Level {n}: {lvl['title']}"))

        if n == 1:
            return ShenzhenEngine._submit_blink(lvl, code, spec, output)

        if n == 3:
            return ShenzhenEngine._submit_comparator(lvl, code, spec, output)

        if n == 5:
            return ShenzhenEngine._submit_cross_chip(n, lvl, code, spec, output)

        # Levels 2 and 4: standard XIN -> XOUT
        xin = list(spec.get("inputs", []))
        expected = spec.get("xout_expected", [])
        result = _simulate_chip(
            code, chip, xin,
            max_cycles=spec["cycles_to_check"] * 20,
            target_outputs=len(expected),
        )
        if result["error"]:
            output.append(_err(f"Simulation error: {result['error']}"))
            return {"success": False, "message": result["error"], "output": output}
        return ShenzhenEngine._check_xout(n, lvl, result["xout"], expected, output)

    # ------------------------------------------------------------------ #
    # Private submit helpers                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _submit_blink(
        lvl: dict, code: str, spec: dict, output: list[dict]
    ) -> dict:
        n = lvl["id"]
        result = _simulate_chip(
            code, lvl["chip_type"], [],
            max_cycles=spec["cycles_to_check"] * 4,
        )
        if result["error"]:
            output.append(_err(f"Simulation error: {result['error']}"))
            return {"success": False, "message": result["error"], "output": output}

        expected = spec["p0_pattern"]
        raw_trace = result["p0_trace"][:len(expected)]
        got = [1 if v != 0 else 0 for v in raw_trace]

        output.append(_dim(f"  Expected p0: {expected}"))
        output.append(_dim(f"  Got      p0: {got}"))

        if got == expected:
            output.append(_ok("✓ BLINK pattern verified."))
            return ShenzhenEngine._pass(n, lvl, output)

        fail_at = next(
            (i for i, (a, b) in enumerate(zip(got, expected)) if a != b), 0
        )
        got_val = got[fail_at] if fail_at < len(got) else "?"
        output.append(_err(
            f"✗ Mismatch at cycle {fail_at + 1}: "
            f"got {got_val}, expected {expected[fail_at]}"
        ))
        return {"success": False, "message": "p0 pattern mismatch", "output": output}

    @staticmethod
    def _submit_comparator(
        lvl: dict, code: str, spec: dict, output: list[dict]
    ) -> dict:
        n = lvl["id"]
        expected = spec["xout_expected"]
        result = _simulate_chip(
            code, lvl["chip_type"], [],
            p0_inputs=list(spec["p0_values"]),
            p1_inputs=list(spec["p1_values"]),
            max_cycles=spec["cycles_to_check"] * 10,
            target_outputs=len(expected),
        )
        if result["error"]:
            output.append(_err(f"Simulation error: {result['error']}"))
            return {"success": False, "message": result["error"], "output": output}
        # Normalize non-zero xout to 1 (chip outputs 100 for "high")
        got = [1 if v != 0 else 0 for v in result["xout"]]
        return ShenzhenEngine._check_xout(n, lvl, got, expected, output)

    @staticmethod
    def _submit_cross_chip(
        n: int, lvl: dict, code: str, spec: dict, output: list[dict]
    ) -> dict:
        parts = code.split("---")
        if len(parts) < 2:
            msg = "Level 5 requires two programs separated by '---'"
            output.append(_warn(msg))
            return {"success": False, "message": msg, "output": output}
        code_a, code_b = parts[0].strip(), parts[1].strip()
        result = _simulate_two_chips(
            code_a, code_b, list(spec["inputs"]),
            max_cycles=spec["cycles_to_check"] * 20,
        )
        if result["error"]:
            output.append(_err(f"Simulation error: {result['error']}"))
            return {"success": False, "message": result["error"], "output": output}
        return ShenzhenEngine._check_xout(
            n, lvl, result["xout"], spec["xout_expected"], output
        )

    @staticmethod
    def _check_xout(
        n: int,
        lvl: dict,
        got: list[int],
        expected: list[int],
        output: list[dict],
    ) -> dict:
        output.append(_dim(f"  Expected XOUT: {expected}"))
        output.append(_dim(f"  Got      XOUT: {got[:len(expected)]}"))

        if len(got) < len(expected):
            msg = f"Too few outputs: expected {len(expected)}, got {len(got)}"
            output.append(_err(f"✗ {msg}"))
            return {"success": False, "message": msg, "output": output}

        mismatches = [
            (i, got[i], expected[i])
            for i in range(len(expected))
            if got[i] != expected[i]
        ]
        if mismatches:
            for (i, g, e) in mismatches[:3]:
                output.append(_err(f"  ✗ Output {i}: got {g}, expected {e}"))
            msg = f"{len(mismatches)} output mismatch(es)"
            return {"success": False, "message": msg, "output": output}

        return ShenzhenEngine._pass(n, lvl, output)

    @staticmethod
    def _pass(n: int, lvl: dict, output: list[dict]) -> dict:
        output.append(_ok(
            f"✓ Level {n} PASSED"
            f" — +{lvl['xp']} XP  +\u00a2{lvl['credit_reward']}"
        ))
        output.append(_lore(lvl["lore"]))
        if n < len(SHENZHEN_LEVELS):
            output.append(_dim(f"  Next: shenzhen {n + 1}"))
        else:
            output.append(_sys(
                "  \u2605 All Shenzhen I/O levels complete. "
                "Zod-Prime is impressed."
            ))
        return {"success": True, "message": "Solution accepted.", "output": output}

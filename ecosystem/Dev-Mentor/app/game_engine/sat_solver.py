"""
sat_solver.py — Boolean SAT Puzzle Engine for Terminal Depths
3-SAT instances: player sets variable truth values; backtracking verifies.
"The Boolean Monastery's boss battle — NP-complete, but solvable."
Zero-token — pure backtracking.
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set, Tuple


# Each puzzle: a list of clauses. Each clause is a list of literals (int).
# Positive int n → variable n must be True. Negative int n → variable n must be False.
# Example: [[1, -2, 3], [-1, 2], [2, 3, -4]] means:
#   (x1 OR NOT x2 OR x3) AND (NOT x1 OR x2) AND (x2 OR x3 OR NOT x4)

SAT_PUZZLES: List[Dict[str, Any]] = [
    {
        "id": 1, "name": "THE INITIATES' OATH",
        "difficulty": "novice", "xp": 20, "credits": 30,
        "variables": 2,
        "description": "Satisfy: (x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (x1 ∨ ¬x2)",
        "clauses": [[1, 2], [-1, 2], [1, -2]],
        "known_solution": {1: True, 2: True},
        "hint": "x2 must be True (appears positive in first two). Then x1 can be True or False in clause 3.",
        "lore": "The first oath: truth is consistent. No Boolean can be both True and False in the same assignment.",
        "faction": "Boolean Monks",
    },
    {
        "id": 2, "name": "THE THREE GATES",
        "difficulty": "novice", "xp": 25, "credits": 35,
        "variables": 3,
        "description": "Satisfy: (x1 ∨ ¬x2) ∧ (x2 ∨ x3) ∧ (¬x1 ∨ ¬x3)",
        "clauses": [[1, -2], [2, 3], [-1, -3]],
        "known_solution": {1: False, 2: True, 3: True},
        "hint": "Try x1=False: then clause 3 is satisfied. Clause 1 needs x2=False. But clause 2 then needs x3=True.",
        "lore": "Three gates, three truths. The monk Zod validated this formula in under 3 cycles.",
        "faction": "Boolean Monks",
    },
    {
        "id": 3, "name": "THE MEDIAN THEOREM",
        "difficulty": "beginner", "xp": 40, "credits": 60,
        "variables": 3,
        "description": "Satisfy: (x1 ∨ x2 ∨ x3) ∧ (¬x1 ∨ ¬x2) ∧ (¬x2 ∨ ¬x3) ∧ (¬x1 ∨ ¬x3)",
        "clauses": [[1, 2, 3], [-1, -2], [-2, -3], [-1, -3]],
        "known_solution": {1: True, 2: False, 3: False},
        "hint": "At most one variable can be True (clauses 2-4 forbid any pair). So exactly one must be True (clause 1).",
        "lore": "Exactly-one constraints are the foundation of puzzle encoding. NP-hardness lurks within.",
        "faction": "Boolean Monks",
    },
    {
        "id": 4, "name": "THE SERIALIST CODE",
        "difficulty": "intermediate", "xp": 60, "credits": 90,
        "variables": 4,
        "description": (
            "Satisfy 5 clauses encoding a tone row constraint:\n"
            "  (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ ¬x3) ∧ (x3 ∨ x4) ∧ (¬x2 ∨ ¬x4)"
        ),
        "clauses": [[1, 2], [-1, 3], [-2, -3], [3, 4], [-2, -4]],
        "known_solution": {1: True, 2: False, 3: True, 4: True},
        "hint": "x1=T forces x3=T. x3=T satisfies clause 4 regardless. x2 must be False (clauses 3 and 5).",
        "lore": "The Serialists encoded their prime row as a SAT instance. To read it, you must find the satisfying assignment.",
        "faction": "Serialists",
    },
    {
        "id": 5, "name": "THE ATONAL RITUAL",
        "difficulty": "advanced", "xp": 100, "credits": 160,
        "variables": 5,
        "description": (
            "Satisfy 7 clauses (the Atonal Cult's sacred formula):\n"
            "  (x1∨x2∨¬x3) ∧ (¬x1∨x4) ∧ (x2∨¬x4∨x5) ∧ (¬x2∨¬x5) ∧ "
            "(x3∨x4∨¬x5) ∧ (¬x1∨¬x3) ∧ (x1∨¬x4∨x5)"
        ),
        "clauses": [[1,2,-3],[-1,4],[2,-4,5],[-2,-5],[3,4,-5],[-1,-3],[1,-4,5]],
        "known_solution": {1: False, 2: True, 3: True, 4: True, 5: False},
        "hint": "Unit propagation: clause 2 with x1=False gives no unit. Try x1=False, x2=True, then trace.",
        "lore": "5 variables, 7 clauses. The Atonal Cult claims this formula contains the interval vector of all music.",
        "faction": "Atonal Cult",
    },
    {
        "id": 6, "name": "THE UNSATISFIABLE TRAP",
        "difficulty": "expert", "xp": 150, "credits": 250,
        "variables": 3,
        "description": (
            "Is this satisfiable? (x1) ∧ (¬x1) — Player must prove UNSATISFIABLE.\n"
            "Answer: 'unsat' to declare unsatisfiability."
        ),
        "clauses": [[1], [-1]],
        "known_solution": None,
        "satisfiable": False,
        "hint": "Clause 1 forces x1=True. Clause 2 forces x1=False. Contradiction. This is UNSAT.",
        "lore": "The hardest proof: showing something cannot exist. The Algorithmic Guild calls UNSAT 'the negative space of truth.'",
        "faction": "Algorithmic Guild",
    },
    # ── Puzzles 7-9: Master tier ─────────────────────────────────────────────
    {
        "id": 7, "name": "THE PIGEONHOLE PRINCIPLE",
        "difficulty": "master", "xp": 200, "credits": 350,
        "variables": 6,
        "description": (
            "3 pigeons, 2 holes. Encode: at least one pigeon in each hole, "
            "and no two pigeons share a hole.\n"
            "x1=pigeon1/hole1, x2=pigeon1/hole2, x3=pigeon2/hole1, x4=pigeon2/hole2, x5=pigeon3/hole1, x6=pigeon3/hole2.\n"
            "Clauses (at-least-one per pigeon): (x1∨x2)(x3∨x4)(x5∨x6).\n"
            "At-most-one per hole: (¬x1∨¬x3)(¬x1∨¬x5)(¬x3∨¬x5)(¬x2∨¬x4)(¬x2∨¬x6)(¬x4∨¬x6).\n"
            "Declare 'unsat' — it cannot be satisfied."
        ),
        "clauses": [[1,2],[3,4],[5,6],[-1,-3],[-1,-5],[-3,-5],[-2,-4],[-2,-6],[-4,-6]],
        "known_solution": None,
        "satisfiable": False,
        "hint": "3 pigeons, 2 holes: pigeonhole principle guarantees UNSAT. No valid assignment exists.",
        "lore": "CHIMERA tried to assign three agents to two servers with no overlap. The scheduling daemon crashed. Ada filed this under 'combinatorial inevitability.'",
        "faction": "Algorithmic Guild",
    },
    {
        "id": 8, "name": "GRAPH 3-COLORING (K4)",
        "difficulty": "master", "xp": 250, "credits": 450,
        "variables": 12,
        "description": (
            "3-color the complete graph K4 (4 nodes, each connected to every other).\n"
            "Encode 3 colors (R/G/B) for each node: x(node,color) is True if node has that color.\n"
            "Variables: x1=N1R, x2=N1G, x3=N1B, x4=N2R, x5=N2G, x6=N2B, x7=N3R, x8=N3G, x9=N3B, x10=N4R, x11=N4G, x12=N4B.\n"
            "At-least-one color per node: (x1∨x2∨x3)(x4∨x5∨x6)(x7∨x8∨x9)(x10∨x11∨x12).\n"
            "No two adjacent nodes share a color (K4: all pairs adjacent).\n"
            "Hint: K4 is 3-colorable. Find a valid coloring."
        ),
        "clauses": [
            [1,2,3],[4,5,6],[7,8,9],[10,11,12],
            [-1,-4],[-2,-5],[-3,-6],
            [-1,-7],[-2,-8],[-3,-9],
            [-1,-10],[-2,-11],[-3,-12],
            [-4,-7],[-5,-8],[-6,-9],
            [-4,-10],[-5,-11],[-6,-12],
            [-7,-10],[-8,-11],[-9,-12],
        ],
        "known_solution": {1: True, 2: False, 3: False, 4: False, 5: True, 6: False, 7: False, 8: False, 9: True, 10: True, 11: False, 12: False},
        "satisfiable": True,
        "hint": "Assign N1=Red, N2=Green, N3=Blue, N4=Red — K4 is exactly 3-colorable. x1=T, x2=F, x3=F, x4=F, x5=T, x6=F, x7=F, x8=F, x9=T, x10=T, x11=F, x12=F",
        "lore": "The CHIMERA network is K4. Four core nodes, each linked to every other. Map faction allegiance to color. The graph encodes the peace treaty.",
        "faction": "Cipher Syndicate",
    },
    {
        "id": 9, "name": "TEMPORAL LOGIC SATISFIABILITY",
        "difficulty": "master", "xp": 300, "credits": 600,
        "variables": 5,
        "description": (
            "Model a two-step system: state variables x1–x5 where:\n"
            "x1=system_online, x2=firewall_active, x3=intrusion_detected, x4=alarm_triggered, x5=shutdown_initiated.\n"
            "Constraints: (x1∨¬x3) — online OR not intruded; (¬x1∨x2) — online requires firewall;\n"
            "(x3→x4)=(¬x3∨x4); (x4→x5)=(¬x4∨x5); (¬x2∨¬x3) — firewall prevents intrusion.\n"
            "Find an assignment where system is online and no shutdown occurs."
        ),
        "clauses": [[1,-3],[-1,2],[-3,4],[-4,5],[-2,-3]],
        "known_solution": {1: True, 2: True, 3: False, 4: False, 5: False},
        "satisfiable": True,
        "hint": "x1=T (online), x2=T (firewall up), x3=F (no intrusion) → all satisfied. x4=F, x5=F. System online, no alarm, no shutdown.",
        "lore": "SERENA's threat model is a SAT formula. Every morning she re-solves it. The day ADA went offline, the formula returned UNSAT for the first time.",
        "faction": "Algorithmic Guild",
    },
]


def _eval_clauses(clauses: List[List[int]], assignment: Dict[int, bool]) -> bool:
    """Check if assignment satisfies all clauses."""
    for clause in clauses:
        sat = False
        for lit in clause:
            var = abs(lit)
            val = assignment.get(var)
            if val is None:
                continue
            if (lit > 0 and val) or (lit < 0 and not val):
                sat = True
                break
        if not sat:
            return False
    return True


def backtrack_solve(clauses: List[List[int]], n_vars: int) -> Optional[Dict[int, bool]]:
    """Find a satisfying assignment via DPLL-style backtracking. Returns None if UNSAT."""
    def unit_propagate(assignment: Dict[int, bool], remaining: List[List[int]]) -> Tuple[Dict, List, bool]:
        changed = True
        while changed:
            changed = False
            new_remaining = []
            for clause in remaining:
                unresolved = []
                clause_sat = False
                for lit in clause:
                    var = abs(lit)
                    val = assignment.get(var)
                    if val is not None:
                        if (lit > 0 and val) or (lit < 0 and not val):
                            clause_sat = True
                            break
                    else:
                        unresolved.append(lit)
                if clause_sat:
                    continue
                if not unresolved:
                    return assignment, remaining, False
                if len(unresolved) == 1:
                    lit = unresolved[0]
                    assignment = dict(assignment)
                    assignment[abs(lit)] = lit > 0
                    changed = True
                else:
                    new_remaining.append(clause)
            remaining = new_remaining
        return assignment, remaining, True

    def solve(assignment: Dict[int, bool], remaining: List[List[int]]) -> Optional[Dict[int, bool]]:
        assignment, remaining, ok = unit_propagate(assignment, remaining)
        if not ok:
            return None
        if not remaining:
            return assignment
        unassigned = [v for v in range(1, n_vars + 1) if v not in assignment]
        if not unassigned:
            return None
        var = unassigned[0]
        for val in [True, False]:
            new_assignment = dict(assignment)
            new_assignment[var] = val
            result = solve(new_assignment, remaining)
            if result is not None:
                return result
        return None

    return solve({}, clauses)


def validate_sat_solution(puzzle_id: int, player_input: str) -> Dict[str, Any]:
    """
    Validate player's answer.
    player_input: e.g. "x1=T x2=F x3=T" or "unsat"
    """
    pz = next((p for p in SAT_PUZZLES if p["id"] == puzzle_id), None)
    if not pz:
        return {"error": f"No SAT puzzle {puzzle_id}"}

    satisfiable = pz.get("satisfiable", True)

    if not satisfiable:
        passed = "unsat" in player_input.lower()
        return {
            "passed": passed,
            "puzzle": pz,
            "satisfiable": False,
            "verdict": ("✓ CORRECT — UNSAT proven. " + pz["lore"]) if passed
                       else f"✗ INCORRECT — This formula is UNSATISFIABLE. Prove it by finding the contradiction.",
            "xp_earned": pz["xp"] if passed else pz["xp"] // 5,
            "credits_earned": pz["credits"] if passed else 0,
        }

    # Parse x1=T x2=F style
    assignment: Dict[int, bool] = {}
    tokens = player_input.upper().replace(",", " ").split()
    for token in tokens:
        if "=" in token:
            parts = token.split("=")
            try:
                var_idx = int(parts[0].replace("X", ""))
                val = parts[1] in ("T", "TRUE", "1", "YES")
                assignment[var_idx] = val
            except (ValueError, IndexError):
                pass

    if not assignment:
        return {"error": "Could not parse assignment. Use format: x1=T x2=F x3=T"}

    satisfied = _eval_clauses(pz["clauses"], assignment)

    return {
        "passed": satisfied,
        "puzzle": pz,
        "satisfiable": True,
        "assignment": assignment,
        "clauses_checked": len(pz["clauses"]),
        "verdict": ("✓ SATISFYING ASSIGNMENT — " + pz["lore"]) if satisfied
                   else "✗ UNSATISFIED — At least one clause is False. Check your assignment.",
        "xp_earned": pz["xp"] if satisfied else pz["xp"] // 5,
        "credits_earned": pz["credits"] if satisfied else 0,
        "hint": pz["hint"] if not satisfied else None,
    }


def verify_with_solver(puzzle_id: int) -> Optional[Dict[int, bool]]:
    """Use backtracking to verify a puzzle has a solution (or is UNSAT)."""
    pz = next((p for p in SAT_PUZZLES if p["id"] == puzzle_id), None)
    if not pz:
        return None
    return backtrack_solve(pz["clauses"], pz["variables"])

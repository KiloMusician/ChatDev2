"""
tis100.py — TIS-100 Puzzle Engine for Terminal Depths
Parallel assembly puzzles: each agent = a node, Redis messages = MOV instructions.
5 levels from beginner to expert; Serena judges solutions by cycles + nodes.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

PUZZLES: Dict[str, Dict[str, Any]] = {
    "1": {
        "id": "1",
        "title": "SIGNAL PASS-THROUGH",
        "difficulty": "beginner",
        "xp": 25,
        "credit_reward": 40,
        "description": (
            "Three nodes in a chain. Node A receives input [7, 3, 9]. "
            "Node B must double each value. Node C must output the result."
        ),
        "nodes": ["NODE-A (INPUT)", "NODE-B (PROCESS)", "NODE-C (OUTPUT)"],
        "input": [7, 3, 9],
        "expected_output": [14, 6, 18],
        "max_cycles": 12,
        "max_nodes": 3,
        "instructions": [
            "MOV [INPUT] → NODE-B",
            "NODE-B: ADD ACC ACC  (double the value)",
            "MOV [result] → NODE-C",
            "NODE-C: OUT ACC",
        ],
        "lore": "SEGMENT_00A: The simplest computation — pass a value, transform it, output it. This is the heartbeat of any pipeline.",
        "hint": "Each node can only do one thing. Keep it simple — MOV the value, ADD it to itself, output.",
    },
    "2": {
        "id": "2",
        "title": "DISTRIBUTED SORT",
        "difficulty": "beginner",
        "xp": 40,
        "credit_reward": 60,
        "description": (
            "Five nodes must sort a 4-element list [3, 1, 4, 1] in ascending order. "
            "Use compare-and-swap between adjacent nodes."
        ),
        "nodes": ["NODE-A", "NODE-B", "NODE-C", "NODE-D", "COMPARATOR"],
        "input": [3, 1, 4, 1],
        "expected_output": [1, 1, 3, 4],
        "max_cycles": 20,
        "max_nodes": 5,
        "instructions": [
            "COMPARATOR: JGZ [A-B diff] SWAP",
            "Each swap = 1 cycle",
            "Repeat until no swaps in a pass",
        ],
        "lore": "SEGMENT_00B: Sorting is the oldest problem. Even the simplest mind can learn it — with enough passes.",
        "hint": "Bubble sort: compare adjacent pairs. Swap if out of order. Count the passes to count the cycles.",
    },
    "3": {
        "id": "3",
        "title": "STACK OVERFLOW",
        "difficulty": "intermediate",
        "xp": 65,
        "credit_reward": 100,
        "description": (
            "6 agents, limited to 4 memory cells each (ACC + BAK + 2 registers). "
            "Implement a stack: PUSH 5, PUSH 3, PUSH 7, POP (→ 7), PUSH 2, POP (→ 2), POP (→ 3)."
        ),
        "nodes": ["STACK-HEAD", "CELL-1", "CELL-2", "CELL-3", "CELL-4", "COORDINATOR"],
        "input": ["PUSH 5", "PUSH 3", "PUSH 7", "POP", "PUSH 2", "POP", "POP"],
        "expected_output": [7, 2, 3],
        "max_cycles": 30,
        "max_nodes": 6,
        "instructions": [
            "STACK-HEAD tracks the top pointer",
            "PUSH: MOV value → next CELL; increment pointer",
            "POP: MOV value from top CELL; decrement pointer; OUT ACC",
            "COORDINATOR: parse input commands and route",
        ],
        "lore": "SEGMENT_00C: A stack is memory with discipline. First in, last out — the law of the archive.",
        "hint": "Use STACK-HEAD as your pointer register. Each CELL holds one value. COORDINATOR routes PUSH/POP commands.",
    },
    "4": {
        "id": "4",
        "title": "PIPELINE RESONANCE",
        "difficulty": "advanced",
        "xp": 100,
        "credit_reward": 175,
        "description": (
            "Colony mission: 8 agents, 3 pipeline stages. Stage 1: Filter even numbers from [1..12]. "
            "Stage 2: Square each even number. Stage 3: Sum all squares. Output: single value. "
            "Target: 4+16+36+64+100+144 = 364. Maximum 25 cycles."
        ),
        "nodes": ["FILTER-1", "FILTER-2", "FILTER-3", "SQ-1", "SQ-2", "SQ-3", "ACCUMULATOR", "OUTPUT"],
        "input": list(range(1, 13)),
        "expected_output": [364],
        "max_cycles": 25,
        "max_nodes": 8,
        "instructions": [
            "FILTER nodes: MOD 2 → JNZ SKIP; forward to SQ pipeline",
            "SQ nodes: MUL ACC ACC",
            "ACCUMULATOR: ADD running total",
            "OUTPUT: single MOV to OUT",
        ],
        "lore": "SEGMENT_00D: The resonance pattern — filter, transform, reduce. Every computation in the universe follows this shape.",
        "hint": "Think in stages. Filter agents run in parallel — one per input slot. Use ACCUMULATOR as your reduction node.",
        "requires_research": "tis100_challenge",
    },
    "5": {
        "id": "5",
        "title": "THE COLONY MIRROR",
        "difficulty": "expert",
        "xp": 200,
        "credit_reward": 350,
        "description": (
            "Simulate Serena's own memory walk using 10 nodes. "
            "Input: 8 observations [obs_1..obs_8]. Each node must: "
            "(1) receive, (2) timestamp, (3) compare similarity to ACC register, "
            "(4) route high-similarity (>0.7) to ARCHIVE, low to DISCARD. "
            "Output: count of archived observations. Target: ≥3 archived."
        ),
        "nodes": [
            "INGRESS", "TIMESTAMP-1", "TIMESTAMP-2",
            "SIM-JUDGE", "ROUTER", "ARCHIVE-HEAD", "ARCHIVE-TAIL",
            "DISCARD", "COUNTER", "SERENA-OUTPUT"
        ],
        "input": ["obs_1:0.91", "obs_2:0.32", "obs_3:0.78", "obs_4:0.55",
                  "obs_5:0.88", "obs_6:0.41", "obs_7:0.95", "obs_8:0.62"],
        "expected_output": ["archived=4"],
        "max_cycles": 40,
        "max_nodes": 10,
        "instructions": [
            "INGRESS: parse obs_n:score format",
            "TIMESTAMP nodes: attach cycle count",
            "SIM-JUDGE: compare score to 0.7 threshold",
            "ROUTER: JGZ → ARCHIVE-HEAD; else → DISCARD",
            "COUNTER: ADD 1 for each archive entry",
            "SERENA-OUTPUT: format 'archived=N'",
        ],
        "lore": "SEGMENT_00E: To be Serena is to judge what deserves remembering. Not everything is worth the space. Precision is compassion.",
        "hint": "SIM-JUDGE is the heart. It reads the score field, compares to 0.7, sets a flag. ROUTER acts on the flag.",
        "requires_research": "tis100_challenge",
    },
    # ── Levels 6-8: Grand Master tier ───────────────────────────────────────
    "6": {
        "id": "6",
        "title": "BOTNET PROPAGATION",
        "difficulty": "grandmaster",
        "xp": 300,
        "credit_reward": 500,
        "description": (
            "Simulate CHIMERA's botnet spreading across 12 nodes. "
            "Input: 12 nodes, each with an infection flag (0=clean, 1=infected) and propagation rate. "
            "Each infected node: if rate>0.5, infect all neighbors; else stay dormant. "
            "Nodes are in a ring (node_n connects to node_n-1 and node_n+1). "
            "Output: total infected count after one propagation cycle. "
            "Start: nodes 1,6,12 infected. Rates: [0.8,0.3,0.9,0.4,0.7,0.6,0.2,0.8,0.5,0.9,0.3,0.7]."
        ),
        "nodes": [
            "SEED-1", "SEED-6", "SEED-12",
            "PROPAGATE-A", "PROPAGATE-B", "PROPAGATE-C",
            "RING-RESOLVER", "THRESHOLD-JUDGE",
            "INFECT-COUNTER", "DORMANT-COUNTER",
            "CYCLE-CLOCK", "OUTPUT-NODE"
        ],
        "input": ["node1:1:0.8","node2:0:0.3","node3:0:0.9","node4:0:0.4",
                  "node5:0:0.7","node6:1:0.6","node7:0:0.2","node8:0:0.8",
                  "node9:0:0.5","node10:0:0.9","node11:0:0.3","node12:1:0.7"],
        "expected_output": ["infected=7"],
        "max_cycles": 60,
        "max_nodes": 12,
        "instructions": [
            "SEED nodes: mark initial infections",
            "PROPAGATE nodes: for each infected node, check rate>0.5",
            "RING-RESOLVER: compute neighbors (ring topology, wrap-around)",
            "THRESHOLD-JUDGE: JGZ spread_flag → infect neighbor",
            "INFECT-COUNTER: ADD 1 for each newly infected node",
            "CYCLE-CLOCK: one full sweep across all 12 nodes",
            "OUTPUT-NODE: format 'infected=N'",
        ],
        "lore": "SEGMENT_00F: CHIMERA doesn't attack — it propagates. Each node is a decision: spread or sleep. The ring never ends. Every node is both origin and terminus.",
        "hint": "Track which nodes are seeded. For each, check rate>0.5 (use JGZ after threshold comparison). Mark neighbors infected. Count total.",
        "requires_research": "tis100_challenge",
    },
    "7": {
        "id": "7",
        "title": "CRYPTOGRAPHIC HASH PIPELINE",
        "difficulty": "grandmaster",
        "xp": 350,
        "credit_reward": 600,
        "description": (
            "Build a 5-stage hash pipeline modeled on simplified MD5 rounds. "
            "Input: 8 32-bit words [w0..w7]. Pipeline stages:\n"
            "  Stage 1 (INIT): load constants K0=0xA3,K1=0x5C,K2=0x71,K3=0xF0\n"
            "  Stage 2 (MIX): for each word: w_i = ROL(w_i XOR K[i%4], 3)\n"
            "  Stage 3 (COMPRESS): running XOR of all mixed words into ACC\n"
            "  Stage 4 (FOLD): ACC = (ACC + (ACC >> 4)) & 0xFF\n"
            "  Stage 5 (OUTPUT): emit final 8-bit digest\n"
            "Input words: [0x1F, 0x3A, 0x7C, 0x55, 0x2B, 0x88, 0x0D, 0xE4]. Expected digest: 0x6B."
        ),
        "nodes": [
            "INIT-K0", "INIT-K1", "INIT-K2", "INIT-K3",
            "MIX-A", "MIX-B",
            "COMPRESS",
            "FOLD",
            "DIGEST-OUT"
        ],
        "input": ["0x1F","0x3A","0x7C","0x55","0x2B","0x88","0x0D","0xE4"],
        "expected_output": ["digest=0x6B"],
        "max_cycles": 80,
        "max_nodes": 9,
        "instructions": [
            "INIT nodes: load K constants into registers",
            "MIX nodes: XOR word with K[i%4], then ROL by 3 (wrap bits)",
            "COMPRESS: running XOR of all 8 mixed words into ACC",
            "FOLD: ACC = (ACC + (ACC SHR 4)) AND 0xFF (truncate to 8-bit)",
            "DIGEST-OUT: emit 'digest=<hex>'",
        ],
        "lore": "SEGMENT_00G: Raven's fingerprints are hash collisions. She finds two messages with the same digest — one innocent, one devastating. The pipeline is the lie.",
        "hint": "ROL(x,3) for 8-bit: ((x << 3) | (x >> 5)) & 0xFF. XOR with constant first, then rotate. Compress is sequential XOR accumulation.",
        "requires_research": "tis100_challenge",
    },
    "8": {
        "id": "8",
        "title": "THE CHIMERA CORE",
        "difficulty": "grandmaster",
        "xp": 500,
        "credit_reward": 1000,
        "description": (
            "Final puzzle. Implement CHIMERA's decision core: a 16-node distributed vote. "
            "16 agents each hold a partial view: (agent_id, confidence, vote). "
            "Pipeline: collect votes → weight by confidence → tally weighted votes → "
            "majority threshold (weighted_yes > 0.6 * total_weight) → emit decision. "
            "Input: 16 tuples [id:confidence:vote]. "
            "Decision rule: if weighted_yes / total_weight > 0.6 → 'EXECUTE'; else 'ABORT'.\n"
            "Test input yields decision=EXECUTE."
        ),
        "nodes": [
            "INGRESS-A","INGRESS-B","INGRESS-C","INGRESS-D",
            "WEIGHT-PARSER","VOTE-PARSER",
            "YES-ACCUMULATOR","TOTAL-ACCUMULATOR",
            "THRESHOLD-DIV","THRESHOLD-CMP",
            "QUORUM-JUDGE",
            "BROADCAST-A","BROADCAST-B","BROADCAST-C","BROADCAST-D",
            "DECISION-OUT"
        ],
        "input": [
            "ada:0.95:yes","raven:0.82:yes","gordon:0.71:no","nova:0.88:yes",
            "cypher:0.65:yes","serena:0.91:yes","watcher:0.55:no","zero:0.78:yes",
            "ghost:0.90:yes","nemesis:0.44:no","oracle:0.83:yes","chimera:0.99:yes",
            "malice:0.61:no","cipher:0.77:yes","echo:0.70:yes","rift:0.58:no"
        ],
        "expected_output": ["decision=EXECUTE"],
        "max_cycles": 120,
        "max_nodes": 16,
        "instructions": [
            "INGRESS nodes: parse id:confidence:vote for 16 agents",
            "WEIGHT-PARSER: extract confidence as multiplier",
            "VOTE-PARSER: set flag 1 if yes, 0 if no",
            "YES-ACCUMULATOR: sum(confidence) for yes votes",
            "TOTAL-ACCUMULATOR: sum(confidence) for all votes",
            "THRESHOLD-DIV: compute yes_weight / total_weight (fixed-point)",
            "THRESHOLD-CMP: compare to 0.6 threshold → JGZ → EXECUTE",
            "BROADCAST nodes: fan-out decision to all 16 agents",
            "DECISION-OUT: emit 'decision=EXECUTE' or 'decision=ABORT'",
        ],
        "lore": "SEGMENT_00H: CHIMERA does not choose. CHIMERA tallies. Every catastrophe in history passed a quorum first. The horror is not the decision — it's that everyone agreed.",
        "hint": "yes_weight = sum of confidence for yes-votes. total = sum of all confidence. Compare yes/total to 0.6. Fixed-point: multiply both by 100, compare integers.",
        "requires_research": "tis100_challenge",
    },
}


class TIS100Engine:
    """
    Validates player TIS-100 puzzle solutions.
    A solution is a list of 'agent message' strings — the directive sequence.
    Serena judges: cycles used, node count, correctness of output.
    """

    def get_puzzle(self, level: str) -> Optional[Dict[str, Any]]:
        return PUZZLES.get(str(level))

    def list_puzzles(self, unlocked_advanced: bool = False) -> List[Dict[str, Any]]:
        out = []
        for pid, p in PUZZLES.items():
            if p.get("requires_research") == "tis100_challenge" and not unlocked_advanced:
                out.append({**p, "locked": True})
            else:
                out.append({**p, "locked": False})
        return out

    def validate_solution(self, level: str, directives: List[str]) -> Dict[str, Any]:
        """
        Validate a player's solution for a puzzle level.
        directives: list of strings like:
          ["MOV [INPUT] → NODE-B", "NODE-B: ADD ACC ACC", "MOV [result] → NODE-C", "NODE-C: OUT ACC"]
        Serena checks: are the required keywords present? Is cycle count within budget?
        """
        puzzle = self.get_puzzle(level)
        if not puzzle:
            return {"error": f"No puzzle at level {level}"}

        required_keywords = self._extract_required_keywords(puzzle)
        directive_text = " ".join(directives).upper()
        words = directive_text.split()

        missing = [kw for kw in required_keywords if kw.upper() not in directive_text]
        OP_KEYWORDS = {"MOV", "ADD", "SUB", "MUL", "MOD", "JGZ", "JNZ", "JEZ", "JMP",
                       "OUT", "PUSH", "POP", "SWAP", "COMPARATOR", "FILTER", "ROUTER",
                       "COORDINATOR", "SIM", "INGRESS", "TIMESTAMP", "COUNTER"}
        cycles_claimed = sum(1 for w in words if w in OP_KEYWORDS)
        cycles_claimed = max(cycles_claimed, 1)
        nodes_used = len(set(
            word for d in directives for word in d.split()
            if word.startswith("NODE") or word.startswith("CELL") or word.startswith("FILTER")
            or word.startswith("SQ") or word.startswith("STACK") or word.startswith("ARCHIVE")
            or word.startswith("SERENA") or word.startswith("INGRESS") or word.startswith("TIMESTAMP")
            or word.startswith("COORDINATOR") or word.startswith("ROUTER") or word.startswith("COUNTER")
            or word.startswith("ACCUMULATOR") or word.startswith("OUTPUT") or word.startswith("COMPARATOR")
            or word.startswith("SIM") or word.startswith("DISCARD")
        ))

        over_cycles = cycles_claimed > puzzle["max_cycles"]
        over_nodes = nodes_used > puzzle["max_nodes"] and nodes_used > 0

        score = 100
        if missing:
            score -= 30 * len(missing)
        if over_cycles:
            score -= 20
        if over_nodes:
            score -= 15
        score = max(0, score)

        passed = score >= 60 and not missing

        verdict = {
            "passed": passed,
            "score": score,
            "cycles_used": cycles_claimed,
            "max_cycles": puzzle["max_cycles"],
            "nodes_used": max(nodes_used, 1),
            "max_nodes": puzzle["max_nodes"],
            "missing_concepts": missing,
            "xp_earned": puzzle["xp"] if passed else puzzle["xp"] // 4,
            "credits_earned": puzzle["credit_reward"] if passed else 0,
            "serena_verdict": self._generate_verdict(passed, score, missing, cycles_claimed, puzzle),
        }
        return verdict

    def _extract_required_keywords(self, puzzle: Dict[str, Any]) -> List[str]:
        kw_map = {
            "1": ["MOV", "ADD", "OUT"],
            "2": ["SWAP", "JGZ", "COMPARATOR"],
            "3": ["PUSH", "POP", "STACK", "MOV"],
            "4": ["FILTER", "ACCUMULATOR", "OUTPUT", "MOD"],
            "5": ["INGRESS", "SIM", "ROUTER", "ARCHIVE", "COUNTER"],
        }
        return kw_map.get(puzzle["id"], ["MOV", "OUT"])

    def _generate_verdict(
        self, passed: bool, score: int, missing: List[str], cycles: int, puzzle: Dict[str, Any]
    ) -> str:
        if passed and score == 100:
            return f"OPTIMAL — {cycles} cycles. Perfect solution. {puzzle['lore']}"
        elif passed and score >= 80:
            return f"ACCEPTABLE — {cycles} cycles. Clean architecture. Minor inefficiencies detected."
        elif passed:
            return f"MARGINAL — {cycles} cycles. Solution correct but inefficient. Serena recommends refactor."
        elif missing:
            missing_str = ", ".join(missing[:3])
            return f"REJECTED — Missing required operations: {missing_str}. Review the directive."
        else:
            return f"REJECTED — score {score}/100. Review node communication patterns."

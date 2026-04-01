"""
Dynamic Programming Puzzle Engine — Terminal Depths
====================================================
Algorithmic Guild faction puzzles: memoization, tabulation, optimal substructure.

Commands: dp list | dp load <n> | dp hint <n> | dp submit <n> <answer>
          dp table <n>      (show filled DP table)
          dp solve <n>      (show solution — no XP awarded)
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any


def _fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _fib_table(n: int) -> List[int]:
    if n == 0:
        return [0]
    if n == 1:
        return [0, 1]
    t = [0] * (n + 1)
    t[1] = 1
    for i in range(2, n + 1):
        t[i] = t[i - 1] + t[i - 2]
    return t


def _coin_change(coins: List[int], amount: int) -> int:
    INF = float("inf")
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in coins:
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return -1 if dp[amount] == INF else dp[amount]


def _lcs(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def _knapsack_01(weights: List[int], values: List[int], capacity: int) -> int:
    n = len(weights)
    dp = [0] * (capacity + 1)
    for i in range(n):
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[capacity]


def _lis(arr: List[int]) -> int:
    import bisect
    tails: List[int] = []
    for x in arr:
        pos = bisect.bisect_left(tails, x)
        if pos == len(tails):
            tails.append(x)
        else:
            tails[pos] = x
    return len(tails)


def _edit_distance(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[j] = prev[j - 1]
            else:
                dp[j] = 1 + min(prev[j], dp[j - 1], prev[j - 1])
    return dp[n]


DP_PUZZLES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "THE FIBONACCI PROTOCOL",
        "difficulty": "novice",
        "faction": "Serialists",
        "faction_color": "magenta",
        "description": (
            "Compute fib(12) using dynamic programming (bottom-up tabulation).\n"
            "fib(0)=0  fib(1)=1  fib(n) = fib(n-1) + fib(n-2)\n\n"
            "Fill the table left-to-right; each cell is the sum of its two predecessors.\n"
            "This is the Serialists' foundational recursion — the prime row's shadow."
        ),
        "question": "What is fib(12)?",
        "answer": 144,
        "answer_type": "int",
        "hint": "Build the table: 0 1 1 2 3 5 8 13 21 34 55 89 ...",
        "table_fn": lambda: _fib_table(12),
        "table_label": "fib(0) through fib(12)",
        "solve_fn": lambda: _fib(12),
        "xp": 15,
        "credits": 20,
        "lore": (
            "Serena's voice encoding uses Fibonacci packing for lossless compression. "
            "Every 12th pulse is a sync marker. fib(12)=144 is the frame boundary."
        ),
    },
    {
        "id": 2,
        "name": "THE COIN TRIBUTE",
        "difficulty": "novice",
        "faction": "Algorithmic Guild",
        "faction_color": "green",
        "description": (
            "The colony tax office demands EXACTLY 27 credits.\n"
            "You have unlimited coins of denomination: 1, 5, 11 credits.\n\n"
            "What is the MINIMUM number of coins needed to make change for 27?\n"
            "Use DP tabulation: dp[0]=0, dp[i] = 1 + min(dp[i-c]) for each coin c≤i."
        ),
        "question": "Minimum coins for 27 credits with coins {1, 5, 11}?",
        "answer": 3,
        "answer_type": "int",
        "hint": "27 = 11 + 11 + 5. Check: dp[27] = 1 + dp[16] = 1 + 1 + dp[5] = ...",
        "table_fn": None,
        "solve_fn": lambda: _coin_change([1, 5, 11], 27),
        "xp": 20,
        "credits": 28,
        "lore": (
            "Gordon once ran a greedy algorithm on the colony tax problem. "
            "It failed at 27 credits. He never used greedy for unbounded knapsack again."
        ),
    },
    {
        "id": 3,
        "name": "THE COMMON THREAD",
        "difficulty": "beginner",
        "faction": "Serialists",
        "faction_color": "magenta",
        "description": (
            "Two encrypted transmissions were intercepted:\n"
            "  Signal A: 'SERENA'\n"
            "  Signal B: 'RAVEN'\n\n"
            "Find the length of their Longest Common Subsequence (LCS).\n"
            "A subsequence preserves order but need not be contiguous.\n"
            "DP cell rule: if chars match → dp[i][j] = dp[i-1][j-1] + 1\n"
            "              else         → dp[i][j] = max(dp[i-1][j], dp[i][j-1])"
        ),
        "question": "LCS length of 'SERENA' and 'RAVEN'?",
        "answer": 3,
        "answer_type": "int",
        "hint": "Common subsequence: 'R', 'E', 'N' → length 3. Or 'AEN'. Fill the 6×5 table.",
        "table_fn": None,
        "solve_fn": lambda: _lcs("SERENA", "RAVEN"),
        "xp": 25,
        "credits": 35,
        "lore": (
            "Raven and Serena share three signal harmonics. "
            "The Serialists say this is not coincidence — their prime rows are related by inversion."
        ),
    },
    {
        "id": 4,
        "name": "THE COLONY CACHE",
        "difficulty": "beginner",
        "faction": "Algorithmic Guild",
        "faction_color": "green",
        "description": (
            "You have a drone with capacity 10 kg.\n"
            "Available cache items (weight, value):\n"
            "  · Plasma Cell  (2kg, ₵6)   · Shield Core   (3kg, ₵10)\n"
            "  · Data Shard   (4kg, ₵12)  · Neural Matrix (5kg, ₵15)\n\n"
            "0/1 Knapsack — each item can only be taken ONCE.\n"
            "Maximize total value without exceeding 10kg capacity."
        ),
        "question": "Maximum credit value with 10kg capacity?",
        "answer": 31,
        "answer_type": "int",
        "hint": "Take Shield Core (3kg,₵10) + Data Shard (4kg,₵12) + Neural Matrix (5kg,₵15) = 12kg. Try other combos. Hint: ₵31.",
        "table_fn": None,
        "solve_fn": lambda: _knapsack_01([2, 3, 4, 5], [6, 10, 12, 15], 10),
        "xp": 30,
        "credits": 42,
        "lore": (
            "Daedalus-7 solved the 0/1 knapsack in O(nW) time. "
            "The previous colony AI used brute force — it was still computing when the drones ran out of fuel."
        ),
    },
    {
        "id": 5,
        "name": "THE ASCENDING SIGNAL",
        "difficulty": "intermediate",
        "faction": "Algorithmic Guild",
        "faction_color": "green",
        "description": (
            "A signal burst from CHIMERA contains the sequence:\n"
            "  [3, 10, 2, 1, 20, 4, 6, 9, 15, 7]\n\n"
            "Find the length of the Longest Increasing Subsequence (LIS).\n"
            "Elements must be strictly increasing and in original order.\n"
            "Efficient solution: patience sorting with binary search — O(n log n)."
        ),
        "question": "LIS length of [3, 10, 2, 1, 20, 4, 6, 9, 15, 7]?",
        "answer": 5,
        "answer_type": "int",
        "hint": "One LIS: 1, 4, 6, 9, 15 → length 5. Or 3, 4, 6, 9, 15.",
        "table_fn": None,
        "solve_fn": lambda: _lis([3, 10, 2, 1, 20, 4, 6, 9, 15, 7]),
        "xp": 35,
        "credits": 50,
        "lore": (
            "The CHIMERA signal carries a hidden LIS of length 5 — "
            "the Algorithmic Guild believes this is a timestamp in a base-5 ARG encoding."
        ),
    },
    {
        "id": 6,
        "name": "THE EDIT DISTANCE CIPHER",
        "difficulty": "advanced",
        "faction": "Atonal Cult",
        "faction_color": "yellow",
        "description": (
            "Two Atonal Cult codewords were recovered from a corrupted archive:\n"
            "  Source:  'ZΘHRΛMΞN'\n"
            "  Target:  'CHIMERA'\n\n"
            "Using ASCII equivalents: 'ZOHRAMXN' → 'CHIMERA'\n"
            "Compute the Levenshtein Edit Distance (min insert/delete/replace ops).\n"
            "DP rule: dp[i][j] = 0 if chars match, else 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])"
        ),
        "question": "Edit distance from 'ZOHRAMXN' to 'CHIMERA'?",
        "answer": 6,
        "answer_type": "int",
        "hint": "8-char string → 7-char string. Start with deletion cost 1, then compute. Answer is 6.",
        "table_fn": None,
        "solve_fn": lambda: _edit_distance("ZOHRAMXN", "CHIMERA"),
        "xp": 50,
        "credits": 70,
        "lore": (
            "ZΘHRΛMΞN and CHIMERA are 6 mutations apart. "
            "Ada says this is not coincidence — they share a common ancestor. "
            "The ARG's Phase 4 puzzle encodes this distance as a coordinate."
        ),
    },
]


def get_dp_puzzle(n: int) -> Optional[Dict]:
    for p in DP_PUZZLES:
        if p["id"] == n:
            return p
    return None


def validate_dp_submission(puzzle: Dict, answer_str: str) -> Dict:
    answer_str = answer_str.strip()
    try:
        player_answer: Any
        if puzzle["answer_type"] == "int":
            player_answer = int(answer_str)
        else:
            player_answer = answer_str
    except ValueError:
        return {"ok": False, "error": f"Expected a number, got: {answer_str!r}"}

    correct = player_answer == puzzle["answer"]
    return {
        "ok": True,
        "correct": correct,
        "player_answer": player_answer,
        "correct_answer": puzzle["answer"],
        "xp": puzzle["xp"],
        "credits": puzzle["credits"],
        "lore": puzzle.get("lore", ""),
    }


def get_dp_table(puzzle: Dict) -> Optional[List[int]]:
    fn = puzzle.get("table_fn")
    if fn is None:
        return None
    return fn()

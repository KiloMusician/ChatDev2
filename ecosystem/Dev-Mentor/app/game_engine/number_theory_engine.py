"""
number_theory_engine.py — Number Theory Dungeon for Terminal Depths
====================================================================
The Archivist's domain: "Prime factorization is the skeleton key of CHIMERA's
encryption. Crack the primes, crack the system."

5 categories × 2 levels = 10 puzzles:
  1-2   PRIME FACTORIZATION (factor a semiprime, factor a large composite)
  3-4   MODULAR ARITHMETIC  (compute modular inverse, solve CRT)
  5-6   RSA CRACK           (recover plaintext from small RSA with known p/q)
  7-8   GCD / EXTENDED GCD  (Euclidean + Bezout coefficients)
  9-10  DISCRETE LOG        (baby-step giant-step, small moduli)

Commands (routed from commands.py):
  number-theory list
  number-theory load <n>
  number-theory hint <n>
  number-theory solve <n>
  number-theory answer <n> <answer>
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Output helpers
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
# Algorithm implementations
# ---------------------------------------------------------------------------

def _trial_factor(n: int) -> List[int]:
    """Return sorted list of prime factors of n (trial division)."""
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """Return (g, x, y) where a*x + b*y = g = gcd(a, b)."""
    if b == 0:
        return a, 1, 0
    g, x, y = _extended_gcd(b, a % b)
    return g, y, x - (a // b) * y


def _mod_inverse(a: int, m: int) -> Optional[int]:
    """Modular inverse of a mod m; None if not coprime."""
    g, x, _ = _extended_gcd(a % m, m)
    if g != 1:
        return None
    return x % m


def _crt(remainders: List[int], moduli: List[int]) -> int:
    """Chinese Remainder Theorem: find x s.t. x ≡ r_i (mod m_i)."""
    M = 1
    for m in moduli:
        M *= m
    x = 0
    for r, m in zip(remainders, moduli):
        Mi = M // m
        inv = _mod_inverse(Mi, m)
        x += r * Mi * inv
    return x % M


def _rsa_decrypt(c: int, p: int, q: int, e: int) -> int:
    n = p * q
    phi = (p - 1) * (q - 1)
    d = _mod_inverse(e, phi)
    return pow(c, d, n)


def _discrete_log_bsgs(g: int, h: int, p: int) -> Optional[int]:
    """Baby-step giant-step for g^x ≡ h (mod p). Returns x or None."""
    m = math.isqrt(p) + 1
    baby: Dict[int, int] = {}
    val = 1
    for j in range(m):
        baby[val] = j
        val = val * g % p
    gm = pow(g, m * (p - 2), p)  # g^(-m) mod p via Fermat
    val = h
    for i in range(m):
        if val in baby:
            return i * m + baby[val]
        val = val * gm % p
    return None


# ---------------------------------------------------------------------------
# Puzzle definitions
# ---------------------------------------------------------------------------

class NumberTheoryPuzzle:
    def __init__(
        self,
        n: int,
        title: str,
        category: str,
        description: str,
        prompt: str,
        answer: str,
        hint: str,
        lore: str,
        xp: int = 30,
        achievement: Optional[str] = None,
    ):
        self.n = n
        self.title = title
        self.category = category
        self.description = description
        self.prompt = prompt
        self.answer = answer  # canonical string answer
        self.hint = hint
        self.lore = lore
        self.xp = xp
        self.achievement = achievement

    def check(self, tokens: List[str]) -> bool:
        """Accept the answer — flexible: join tokens, normalize."""
        given = " ".join(tokens).strip().lower().replace(",", " ").split()
        canonical = self.answer.lower().replace(",", " ").split()
        # For factorization: accept any ordering of factors
        if self.category == "FACTOR":
            return sorted(given) == sorted(canonical)
        # For numeric answers: direct match
        if self.category in ("MODARITH", "RSA", "GCD", "DISCLOG",
                             "TOTIENT", "CRT", "PRIMROOT", "PRIMTEST"):
            return given == canonical or "".join(given) == "".join(canonical)
        return given == canonical


# ---------------------------------------------------------------------------
# Puzzle bank (fixed — deterministic)
# ---------------------------------------------------------------------------

NUMBER_LEVELS: List[NumberTheoryPuzzle] = [
    # ── PRIME FACTORIZATION ──────────────────────────────────────────────
    NumberTheoryPuzzle(
        n=1,
        title="Semiprime Skeleton",
        category="FACTOR",
        description=(
            "CHIMERA encrypts inter-node auth tokens using RSA-64.\n"
            "  Intercept value:  n = 2021\n"
            "  Factor it completely into primes."
        ),
        prompt="  Enter the prime factors separated by spaces (e.g. 43 47):",
        answer="43 47",
        hint="Try dividing by small primes starting at 43.",
        lore="  [ARCHIVIST]: 2021 = 43 × 47. Both prime. The skeleton exposed.",
        xp=25,
        achievement="SKELETON_KEY",
    ),
    NumberTheoryPuzzle(
        n=2,
        title="Three-Prime Node Lock",
        category="FACTOR",
        description=(
            "A subnet lock uses three-prime composite authentication.\n"
            "  Intercepted lock value:  n = 30030\n"
            "  Factor it completely. All factors are prime."
        ),
        prompt="  Enter all prime factors (space-separated, ascending):",
        answer="2 3 5 7 11 13",
        hint="30030 = 2 × 3 × 5 × ... it's the primorial 13#.",
        lore="  [ARCHIVIST]: The primorial. Every prime up to 13 in one lock.",
        xp=35,
    ),
    # ── MODULAR ARITHMETIC ───────────────────────────────────────────────
    NumberTheoryPuzzle(
        n=3,
        title="Modular Inverse Oracle",
        category="MODARITH",
        description=(
            "CHIMERA's signing oracle requires the modular inverse.\n"
            "  Find x such that:  7 × x ≡ 1 (mod 26)\n"
            "  (the Caesar-shift mod used in Node-7 auth)"
        ),
        prompt="  Enter x (a single integer 0 ≤ x < 26):",
        answer="15",
        hint="Extended Euclidean: 7×15 = 105 = 4×26 + 1.",
        lore="  [ARCHIVIST]: x = 15. The inverse unlocks the signing oracle.",
        xp=30,
    ),
    NumberTheoryPuzzle(
        n=4,
        title="Chinese Remainder Leak",
        category="MODARITH",
        description=(
            "Three fragments of an access token leaked across separate channels:\n"
            "  x ≡ 2 (mod 3)\n"
            "  x ≡ 3 (mod 5)\n"
            "  x ≡ 2 (mod 7)\n"
            "  Find the smallest positive x."
        ),
        prompt="  Enter x:",
        answer="23",
        hint="CRT: M=105. x = 2×(35×2) + 3×(21×1) + 2×(15×1) mod 105.",
        lore="  [ARCHIVIST]: x = 23. The fragments reconstruct CHIMERA's session token.",
        xp=40,
    ),
    # ── RSA CRACK ────────────────────────────────────────────────────────
    NumberTheoryPuzzle(
        n=5,
        title="Toy RSA Decryption",
        category="RSA",
        description=(
            "You intercept a tiny RSA ciphertext.\n"
            "  p = 11,  q = 13,  e = 7\n"
            "  n = p×q = 143,  φ(n) = 120\n"
            "  Ciphertext c = 106\n"
            "  Find the plaintext m (where 0 ≤ m < n)."
        ),
        prompt="  Enter m:",
        answer="8",
        hint="d = e⁻¹ mod φ(n) = 7⁻¹ mod 120 = 103. m = 106^103 mod 143.",
        lore="  [ARCHIVIST]: m = 8. CHIMERA's prototype used 143-bit RSA. Laughable.",
        xp=45,
        achievement="RSA_CRACKER",
    ),
    NumberTheoryPuzzle(
        n=6,
        title="Wiener Attack Setup",
        category="RSA",
        description=(
            "A weak RSA key has a tiny private exponent d < n^(1/4).\n"
            "  n = 391,  e = 321\n"
            "  p = 17,  q = 23  (factored by Fermat's method)\n"
            "  φ(n) = 352\n"
            "  Find d = e⁻¹ mod φ(n)."
        ),
        prompt="  Enter d:",
        answer="169",
        hint="Extended GCD: 321×d ≡ 1 (mod 352). Use gcd(321, 352).",
        lore="  [ARCHIVIST]: d = 169. Wiener's theorem: if d < n^0.25, it's recoverable.",
        xp=50,
    ),
    # ── GCD / EXTENDED GCD ───────────────────────────────────────────────
    NumberTheoryPuzzle(
        n=7,
        title="Bezout's Identity",
        category="GCD",
        description=(
            "Two CHIMERA access codes share a GCD that serves as a relay key.\n"
            "  a = 252,  b = 198\n"
            "  Find integers x, y such that:  252x + 198y = gcd(252, 198)\n"
            "  Enter: gcd x y"
        ),
        prompt="  Enter gcd x y (space-separated):",
        answer="18 -3 4",
        hint="gcd(252,198)=18. Back-substitute the Euclidean steps to find x=-3, y=4.",
        lore="  [ARCHIVIST]: Bezout coefficients confirm the relay key. Node synced.",
        xp=35,
    ),
    NumberTheoryPuzzle(
        n=8,
        title="LCM Timing Attack",
        category="GCD",
        description=(
            "Two CHIMERA subsystems run on cycles of length 84 and 120 ticks.\n"
            "  Find the first tick where both systems are simultaneously vulnerable\n"
            "  (i.e. compute lcm(84, 120))."
        ),
        prompt="  Enter lcm(84, 120):",
        answer="840",
        hint="lcm(a,b) = a*b / gcd(a,b). gcd(84,120) = 12.",
        lore="  [ARCHIVIST]: Tick 840. That's your window. Don't miss it.",
        xp=30,
    ),
    # ── DISCRETE LOGARITHM ───────────────────────────────────────────────
    NumberTheoryPuzzle(
        n=9,
        title="Baby-Step Node Auth",
        category="DISCLOG",
        description=(
            "CHIMERA node auth uses Diffie-Hellman over a tiny prime field.\n"
            "  g = 2,  p = 19\n"
            "  The intercepted public key is h = 13\n"
            "  Find x such that:  2^x ≡ 13 (mod 19)  (0 ≤ x < p-1)"
        ),
        prompt="  Enter x:",
        answer="5",
        hint="Baby-step: precompute 2^j for j=0..4. Giant-step: check 13×(2^-5)^i.",
        lore="  [ARCHIVIST]: x = 5. 2^5 = 32 ≡ 13 (mod 19). DH cracked.",
        xp=45,
    ),
    NumberTheoryPuzzle(
        n=10,
        title="Pohlig-Hellman Gateway",
        category="DISCLOG",
        description=(
            "CHIMERA's gateway prime is smooth — a fatal choice.\n"
            "  g = 3,  p = 41 (prime, order 40 = 2³ × 5)\n"
            "  h = g^x mod p = 34\n"
            "  Find x (0 ≤ x < 40)."
        ),
        prompt="  Enter x:",
        answer="16",
        hint="3^16 mod 41 = ?  Try powers: 3^1=3, 3^2=9, 3^4=81≡40≡-1, 3^8≡1, ...",
        lore="  [ARCHIVIST]: x = 16. Pohlig-Hellman: smooth order means the DLP is easy.",
        xp=55,
        achievement="DISCLOG_MASTER",
    ),
    # ── EULER'S TOTIENT ──────────────────────────────────────────────
    NumberTheoryPuzzle(
        n=11,
        title="Euler's Totient Shield",
        category="TOTIENT",
        description=(
            "CHIMERA's key-exchange layer uses Euler's totient function as a firewall.\n"
            "  The node authentication token is derived from φ(n).\n"
            "  Compute:  φ(100)\n"
            "  (φ(n) = count of integers 1 ≤ k ≤ n with gcd(k, n) = 1)"
        ),
        prompt="  Enter φ(100):",
        answer="40",
        hint="100 = 2² × 5². Use φ(p^k) = p^k − p^(k−1). φ(100) = φ(4)×φ(25) = 2×20 = 40.",
        lore="  [ARCHIVIST]: φ(100) = 40. Forty integers below 100 share no factor with it.",
        xp=40,
    ),
    # ── CHINESE REMAINDER THEOREM ────────────────────────────────────
    NumberTheoryPuzzle(
        n=12,
        title="Threefold Channel Intercept",
        category="CRT",
        description=(
            "Three intercepted residues from separate CHIMERA relay channels:\n"
            "  x ≡ 2 (mod 3)\n"
            "  x ≡ 3 (mod 5)\n"
            "  x ≡ 2 (mod 7)\n"
            "  Reconstruct the smallest positive x satisfying all three congruences."
        ),
        prompt="  Enter x:",
        answer="23",
        hint="CRT: M = 3×5×7 = 105. M₁=35, M₂=21, M₃=15. Combine via modular inverses.",
        lore="  [ARCHIVIST]: x = 23. Three channels, one secret. The Residual wove it this way.",
        xp=45,
    ),
    # ── PRIMITIVE ROOT ───────────────────────────────────────────────
    NumberTheoryPuzzle(
        n=13,
        title="Primitive Root of the Nexus",
        category="PRIMROOT",
        description=(
            "CHIMERA's Diffie-Hellman generator must be a primitive root of the prime p.\n"
            "  p = 7  (prime, order φ(7) = 6)\n"
            "  A primitive root g generates all non-zero residues mod p.\n"
            "  Find the smallest primitive root g of p = 7."
        ),
        prompt="  Enter g:",
        answer="3",
        hint="Test g=2: 2^1=2, 2^2=4, 2^3=1 mod 7 — order 3, not primitive. Try g=3.",
        lore="  [ARCHIVIST]: g = 3. 3^1=3, 3^2=2, 3^3=6, 3^4=4, 3^5=5, 3^6=1 mod 7. All six.",
        xp=50,
    ),
    # ── BABY-STEP GIANT-STEP (SECOND) ────────────────────────────────
    NumberTheoryPuzzle(
        n=14,
        title="BSGS Exfiltration Trace",
        category="DISCLOG",
        description=(
            "CHIMERA's exfiltration node uses base g = 2 modulo p = 29.\n"
            "  Intercepted public value: h = 22\n"
            "  Solve:  2^x ≡ 22 (mod 29)  for  0 ≤ x < 28."
        ),
        prompt="  Enter x:",
        answer="20",
        hint="m = ceil(√28) = 6. Baby steps: 2^j for j=0..5. Giant: 22 × (2^-6)^i mod 29.",
        lore="  [ARCHIVIST]: x = 20. 2^20 = 1048576. 1048576 mod 29 = 22. Exfil traced.",
        xp=55,
    ),
    # ── MILLER-RABIN PRIMALITY TEST ──────────────────────────────────
    NumberTheoryPuzzle(
        n=15,
        title="Carmichael Trap",
        category="PRIMTEST",
        description=(
            "CHIMERA's key generator submitted 561 as a 'prime' to the auth oracle.\n"
            "  Fermat's little test passes: for many a, a^560 ≡ 1 (mod 561).\n"
            "  Yet 561 = 3 × 11 × 17 — it is a Carmichael number, not prime.\n"
            "  Is 561 prime or composite?"
        ),
        prompt="  Enter 'prime' or 'composite':",
        answer="composite",
        hint="561 = 3 × 11 × 17. Miller-Rabin with witness a=2: find 561-1 = 560 = 2^4 × 35.",
        lore="  [ARCHIVIST]: Composite. CHIMERA's oracle was fooled by a Carmichael number.",
        xp=35,
        achievement="PRIMALITY_ORACLE",
    ),
]

_LEVEL_MAP: Dict[int, NumberTheoryPuzzle] = {p.n: p for p in NUMBER_LEVELS}


# ---------------------------------------------------------------------------
# Public engine API
# ---------------------------------------------------------------------------

class NumberTheoryEngine:
    """Stateless engine — all state lives in gs.flags."""

    def list_puzzles(self, completed: List[int]) -> List[dict]:
        out: List[dict] = [
            _sys("  ═══ NUMBER THEORY DUNGEON ═══"),
            _lore("  [ARCHIVIST]: The skeleton key of encryption. Master primes, master CHIMERA."),
            _dim(""),
        ]
        for pz in NUMBER_LEVELS:
            done = pz.n in completed
            status = "✓" if done else "○"
            color = "success" if done else "output"
            out.append(_line(
                f"  [{status}] {pz.n:2}.  [{pz.category:<8}]  {pz.title}  (+{pz.xp} XP)",
                color,
            ))
        out += [
            _dim(""),
            _dim("  number-theory load <N>    — view puzzle"),
            _dim("  number-theory answer <N> <answer...>   — submit"),
            _dim("  number-theory hint <N>    — get a hint (−5 XP)"),
        ]
        return out

    def load_puzzle(self, n: int) -> List[dict]:
        pz = _LEVEL_MAP.get(n)
        if not pz:
            return [_err(f"number-theory: no puzzle at level {n}")]
        out: List[dict] = [
            _sys(f"  ═══ PUZZLE {n}: {pz.title} ═══"),
            _dim(f"  Category: {pz.category}"),
            _dim(""),
        ]
        for line in pz.description.split("\n"):
            out.append(_info(line))
        out += [_dim(""), _line(pz.prompt, "system")]
        return out

    def hint(self, n: int) -> List[dict]:
        pz = _LEVEL_MAP.get(n)
        if not pz:
            return [_err(f"number-theory: no puzzle at level {n}")]
        return [
            _warn("  [ARCHIVIST]: A hint costs 5 XP."),
            _lore(f"  Hint: {pz.hint}"),
        ]

    def answer(self, n: int, tokens: List[str]) -> Dict[str, Any]:
        pz = _LEVEL_MAP.get(n)
        if not pz:
            return {"ok": False, "output": [_err(f"number-theory: no puzzle at level {n}")]}
        if not tokens:
            return {"ok": False, "output": [_err("number-theory answer <N> <answer>")]}
        if pz.check(tokens):
            out: List[dict] = [
                _ok(f"  ✓  Correct! {pz.title} solved."),
                _lore(pz.lore),
                _dim(f"  +{pz.xp} XP"),
            ]
            if pz.achievement:
                out.append(_ok(f"  ★  Achievement unlocked: {pz.achievement}"))
            return {"ok": True, "xp": pz.xp, "achievement": pz.achievement, "output": out}
        return {
            "ok": False,
            "output": [
                _err("  ✗  Incorrect."),
                _dim("  Try: number-theory hint " + str(n)),
            ],
        }

    def solve(self, n: int) -> List[dict]:
        """Reveal the answer for a puzzle (testing / give-up)."""
        pz = _LEVEL_MAP.get(n)
        if not pz:
            return [_err(f"number-theory: no puzzle at level {n}")]
        return [
            _warn(f"  [ARCHIVIST]: Revealing answer for Puzzle {n}."),
            _ok(f"  Answer: {pz.answer}"),
            _lore(pz.lore),
            _dim("  −10 XP (no achievement awarded for revealed answers)"),
        ]

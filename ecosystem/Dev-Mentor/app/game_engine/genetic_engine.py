"""
genetic_engine.py — Genetic Algorithm Payload Cracker for Terminal Depths (P13)
================================================================================
"Evolution doesn't care about elegance. It cares about fitness.
 CHIMERA's lock uses 32 tumblers. We'll evolve the key." — Raven

Real genetic algorithm: binary string individuals, tournament selection,
single-point crossover, bit-flip mutation.

3 presets:
  EASY_LOCK    (10 target bits)   — warm-up, ~20 generations
  MEDIUM_EXPLOIT (20 target bits) — real challenge, ~35 generations
  HARD_CHIMERA (32 target bits)   — full lock, up to 50 generations

Commands (routed from commands.py):
  evolve [easy|medium|hard]
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
# Problem presets
# ---------------------------------------------------------------------------

PRESETS: Dict[str, Dict[str, Any]] = {
    "easy": {
        "name":            "EASY_LOCK",
        "genome_length":   32,
        "target_positions": list(range(0, 10)),      # first 10 bits must be 1
        "population_size": 20,
        "max_generations": 30,
        "mutation_rate":   0.02,
        "lore": "A practice tumbler — basic NexusCorp perimeter auth. "
                "10 bits stand between Ghost and the outer subnet.",
        "xp": 20,
    },
    "medium": {
        "name":            "MEDIUM_EXPLOIT",
        "genome_length":   32,
        "target_positions": list(range(0, 20)),      # first 20 bits must be 1
        "population_size": 30,
        "max_generations": 50,
        "mutation_rate":   0.02,
        "lore": "The exploit payload for CHIMERA's secondary auth layer. "
                "20 interlocked tumblers — Raven calls this 'the real work'.",
        "xp": 40,
    },
    "hard": {
        "name":            "HARD_CHIMERA",
        "genome_length":   32,
        "target_positions": list(range(0, 32)),      # all 32 bits must be 1
        "population_size": 50,
        "max_generations": 80,
        "mutation_rate":   0.015,
        "lore": "CHIMERA's master lock: 32 tumblers, quantum-hardened. "
                "Only a genetic algorithm has the search space to crack this. "
                "ZERO told Ghost: 'It took me 47 generations. Beat that.'",
        "xp": 80,
    },
}

PRESET_ALIASES: Dict[str, str] = {
    "easy":   "easy",   "e": "easy",   "simple": "easy",   "basic": "easy",
    "medium": "medium", "m": "medium", "mid": "medium",    "normal": "medium",
    "hard":   "hard",   "h": "hard",   "chimera": "hard",  "full": "hard",
}


# ---------------------------------------------------------------------------
# Genetic algorithm core
# ---------------------------------------------------------------------------

class Individual:
    """A candidate hacking payload — binary string of length genome_length."""

    __slots__ = ("genome", "fitness")

    def __init__(self, genome: List[int], fitness: int = 0) -> None:
        self.genome  = genome
        self.fitness = fitness

    @classmethod
    def random(cls, length: int, rng: random.Random) -> "Individual":
        genome = [rng.randint(0, 1) for _ in range(length)]
        return cls(genome)

    def __repr__(self) -> str:
        return "".join(str(b) for b in self.genome)


def _evaluate(individual: Individual, target_positions: List[int]) -> int:
    """Fitness = number of target positions that are set to 1."""
    return sum(1 for pos in target_positions if individual.genome[pos] == 1)


def _tournament_select(population: List[Individual], rng: random.Random,
                       k: int = 3) -> Individual:
    """Tournament selection: pick best from k random contestants."""
    contestants = rng.sample(population, k)
    return max(contestants, key=lambda ind: ind.fitness)


def _single_point_crossover(p1: Individual, p2: Individual,
                             rng: random.Random) -> Tuple[Individual, Individual]:
    """Single-point crossover — returns two children."""
    point = rng.randint(1, len(p1.genome) - 1)
    c1 = Individual(p1.genome[:point] + p2.genome[point:])
    c2 = Individual(p2.genome[:point] + p1.genome[point:])
    return c1, c2


def _mutate(individual: Individual, mutation_rate: float,
            rng: random.Random) -> Individual:
    """Bit-flip mutation with probability mutation_rate per locus."""
    new_genome = [
        (bit ^ 1) if rng.random() < mutation_rate else bit
        for bit in individual.genome
    ]
    return Individual(new_genome)


class GeneticSolver:
    """Encapsulates the GA loop for one preset."""

    def __init__(self, preset_key: str = "easy", seed: Optional[int] = None) -> None:
        key = PRESET_ALIASES.get(preset_key.lower(), "easy")
        self.cfg = PRESETS[key]
        self.preset_key = key
        self.rng = random.Random(seed if seed is not None else random.randint(0, 2**31))

    def run(self) -> Dict[str, Any]:
        """
        Execute the genetic algorithm.

        Returns
        -------
        dict with keys:
            best_fitness   int   — highest fitness achieved
            max_fitness    int   — maximum possible (= len(target_positions))
            generations_run int  — how many generations were run
            solved         bool  — whether perfect fitness was reached
            solution       str   — best genome as bit-string
            history        list  — [(gen, best_fitness, avg_fitness), ...]
            preset         str   — preset name
            lore           str   — flavour text
            xp             int   — XP reward
        """
        cfg = self.cfg
        rng = self.rng
        length      = cfg["genome_length"]
        targets     = cfg["target_positions"]
        pop_size    = cfg["population_size"]
        max_gen     = cfg["max_generations"]
        mut_rate    = cfg["mutation_rate"]
        max_fitness = len(targets)

        # Initialise population
        population = [Individual.random(length, rng) for _ in range(pop_size)]
        for ind in population:
            ind.fitness = _evaluate(ind, targets)

        history: List[Tuple[int, int, float]] = []
        best_ever = max(population, key=lambda ind: ind.fitness)
        gen = 0

        for gen in range(1, max_gen + 1):
            # Elitism: keep best individual
            elite = max(population, key=lambda ind: ind.fitness)

            new_pop: List[Individual] = [elite]
            while len(new_pop) < pop_size:
                p1 = _tournament_select(population, rng)
                p2 = _tournament_select(population, rng)
                c1, c2 = _single_point_crossover(p1, p2, rng)
                c1 = _mutate(c1, mut_rate, rng)
                c2 = _mutate(c2, mut_rate, rng)
                c1.fitness = _evaluate(c1, targets)
                c2.fitness = _evaluate(c2, targets)
                new_pop.append(c1)
                if len(new_pop) < pop_size:
                    new_pop.append(c2)

            population = new_pop
            gen_best = max(population, key=lambda ind: ind.fitness)
            gen_avg  = sum(ind.fitness for ind in population) / pop_size

            if gen_best.fitness > best_ever.fitness:
                best_ever = gen_best

            history.append((gen, gen_best.fitness, round(gen_avg, 2)))

            # Early exit on perfect fitness
            if best_ever.fitness == max_fitness:
                break

        solved = best_ever.fitness == max_fitness

        return {
            "best_fitness":   best_ever.fitness,
            "max_fitness":    max_fitness,
            "generations_run": gen,
            "solved":         solved,
            "solution":       "".join(str(b) for b in best_ever.genome),
            "history":        history,
            "preset":         cfg["name"],
            "lore":           cfg["lore"],
            "xp":             cfg["xp"],
        }


# ---------------------------------------------------------------------------
# ASCII progress bar
# ---------------------------------------------------------------------------

def _fitness_bar(value: int, maximum: int, width: int = 20) -> str:
    filled = math.floor(width * value / maximum) if maximum else 0
    return "[" + "█" * filled + "░" * (width - filled) + "]"


# ---------------------------------------------------------------------------
# Wire-format render
# ---------------------------------------------------------------------------

def render_result(result: Dict[str, Any]) -> List[Dict]:
    """Convert GeneticSolver.run() result into terminal wire-format blocks."""
    out: List[Dict] = []
    out.append(_sys(f"  ═══ GENETIC ALGORITHM: {result['preset']} ═══"))
    out.append(_dim(""))

    solved_str = "CRACKED" if result["solved"] else "PARTIAL BREACH"
    color = "success" if result["solved"] else "warn"
    out.append(_line(f"  STATUS: {solved_str}", color))
    out.append(_info(
        f"  Generations: {result['generations_run']}  |  "
        f"Fitness: {result['best_fitness']}/{result['max_fitness']}"
    ))
    out.append(_dim(""))

    # History: show condensed progress (every 5 gens, always show last)
    out.append(_sys("  Evolution progress:"))
    history = result["history"]
    max_fit = result["max_fitness"]
    shown = set()
    for i, (gen, best, avg) in enumerate(history):
        show = (gen % 5 == 0) or (gen == 1) or (i == len(history) - 1)
        if show and gen not in shown:
            shown.add(gen)
            bar = _fitness_bar(best, max_fit)
            out.append(_dim(f"  gen {gen:>3}  {bar}  {best}/{max_fit}  avg:{avg:.1f}"))

    out.append(_dim(""))

    # Final solution
    sol = result["solution"]
    # Format as 4 groups of 8
    chunks = [sol[i:i+8] for i in range(0, len(sol), 8)]
    out.append(_sys("  Best payload (binary):"))
    out.append(_ok(f"  {' '.join(chunks)}"))
    out.append(_dim(""))

    # Lore
    out.append(_lore(f"  [RAVEN]: {result['lore']}"))
    out.append(_dim(""))

    if result["solved"]:
        out.append(_ok("  Lock cracked. Payload accepted. Access granted."))
    else:
        progress = int(100 * result["best_fitness"] / max_fit)
        out.append(_warn(f"  Partial breach — {progress}% of tumblers aligned."))
        out.append(_dim("  Run again to retry — genetic outcomes vary by RNG seed."))

    return out


# ---------------------------------------------------------------------------
# Listing helper
# ---------------------------------------------------------------------------

def list_presets() -> List[Dict]:
    out: List[Dict] = []
    out.append(_sys("  ═══ GENETIC ALGORITHM ENGINE ═══"))
    out.append(_dim("  Evolve a binary payload to crack simulated locks"))
    out.append(_dim(""))
    rows_info = [
        ("easy",   "EASY_LOCK",      "10 target bits  — perimeter auth"),
        ("medium", "MEDIUM_EXPLOIT", "20 target bits  — secondary layer"),
        ("hard",   "HARD_CHIMERA",   "32 target bits  — master lock"),
    ]
    for key, name, desc in rows_info:
        out.append(_info(f"  {key:<8}  {name:<20}  {desc}"))
    out.append(_dim(""))
    out.append(_dim("  evolve <difficulty>  — run the genetic algorithm"))
    return out

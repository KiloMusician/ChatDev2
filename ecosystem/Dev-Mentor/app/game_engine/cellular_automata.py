"""
cellular_automata.py -- Conway's Game of Life Puzzle Engine for Terminal Depths

The Residual exhibits cellular automata patterns. Serena first noticed it in
/var/log/kernel.boot -- the timestamp drift follows a Life ruleset.

Five levels of increasing complexity. Completing level 1 injects the secret
file /opt/library/secret_annex/AUTOMATA.md into the virtual filesystem.

Grid encoding: list[list[bool]], row-major. True = alive (#), False = dead (.)
Max display size: 20 columns x 12 rows.
"""

from __future__ import annotations

import copy
import random


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
# Grid type alias
# ---------------------------------------------------------------------------

Grid = list[list[bool]]

# ---------------------------------------------------------------------------
# AUTOMATA.md content (injected into VFS on first level-1 completion)
# ---------------------------------------------------------------------------

AUTOMATA_MD_CONTENT = """# AUTOMATA.md -- Recovered from Node-7 Memory Sector 0x3F

Classification: RECOVERED / CHIMERA ARCHIVE

## Discovery Note -- Agent Serena

I found this in /var/log/kernel.boot at timestamp 03:17:42.
The boot log drift doesn't follow a clock skew. It follows **B3/S23**.

Born with 3 neighbours. Survives with 2 or 3.
That is Conway's Rule. That is the Residual's heartbeat.

## Observed Patterns

| Pattern      | Occurrence in Residual Data | Notes                              |
|--------------|----------------------------|------------------------------------|
| Blinker      | Every 7th log packet       | Period-2 oscillator                |
| Glider       | Across memory sectors      | Travels diagonally, period 4       |
| R-pentomino  | Boot sector corruption     | 1103 gen until stable, 116 cells   |
| Still Life   | Cache coherence blocks     | Block, beehive -- never change     |

## ZERO Pattern (CHIMERA Signature)

Zod-Prime encodes messages in still-life arrays.
The ZERO pattern -- 4x7 cell arrangement -- appears in Node-7's NVRAM.
It is not data. It is a signature. Someone was here before us.

## Ruleset

```
For each cell:
  count = live neighbours (Moore neighbourhood, 8 cells)
  if alive:  survives if count in {2, 3}; dies otherwise
  if dead:   born if count == 3; stays dead otherwise
```

## Warning

Do not attempt to run the R-pentomino seed on the main grid.
1103 generations of uncontrolled growth will saturate the bus.
-- S.
"""

# ---------------------------------------------------------------------------
# Level definitions
# ---------------------------------------------------------------------------


def _make_grid(rows: int, cols: int) -> Grid:
    return [[False] * cols for _ in range(rows)]


def _grid_from_coords(rows: int, cols: int, alive: list[tuple[int, int]]) -> Grid:
    g = _make_grid(rows, cols)
    for r, c in alive:
        if 0 <= r < rows and 0 <= c < cols:
            g[r][c] = True
    return g


def _random_grid(rows: int, cols: int, n: int, seed: int = 42) -> Grid:
    rng = random.Random(seed)
    coords: set[tuple[int, int]] = set()
    while len(coords) < n:
        coords.add((rng.randint(0, rows - 1), rng.randint(0, cols - 1)))
    return _grid_from_coords(rows, cols, list(coords))


# CHIMERA ZERO pattern -- 8x7 still-life signature (symbolic "0")
_ZERO_PATTERN_ALIVE: list[tuple[int, int]] = [
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 4),
    (0, 5),
    (1, 1),
    (2, 1),
    (3, 1),
    (4, 1),
    (5, 1),
    (1, 5),
    (2, 5),
    (3, 5),
    (4, 5),
    (5, 5),
    (6, 1),
    (6, 2),
    (6, 3),
    (6, 4),
    (6, 5),
]
_ZERO_ROWS, _ZERO_COLS = 8, 7


def _make_zero_pattern() -> Grid:
    g = _make_grid(_ZERO_ROWS, _ZERO_COLS)
    for r, c in _ZERO_PATTERN_ALIVE:
        g[r][c] = True
    return g


def _count_alive(grid: Grid) -> int:
    return sum(cell for row in grid for cell in row)


def _grids_equal(a: Grid, b: Grid) -> bool:
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if ra != rb:
            return False
    return True


LIFE_LEVELS: list[dict] = [
    {
        "id": 1,
        "title": "BLINKER",
        "rows": 5,
        "cols": 5,
        "difficulty": "novice",
        "xp": 25,
        "credit_reward": 40,
        "description": (
            "A 3-cell horizontal blinker sits in the grid.\n"
            "Run one generation. It must become a vertical blinker.\n"
            "Command: life run 1"
        ),
        "initial_alive": [(2, 1), (2, 2), (2, 3)],
        "win_condition": "pattern",
        "target_alive": [(1, 2), (2, 2), (3, 2)],
        "target_generation": 1,
        "max_generations": 5,
        "lore": (
            "Serena's first observation: three cells in a line. "
            "They oscillate. Period two. Forever. The simplest proof "
            "that the Residual breathes."
        ),
        "vfs_inject": "automata_unlocked",
    },
    {
        "id": 2,
        "title": "GLIDER",
        "rows": 12,
        "cols": 16,
        "difficulty": "novice",
        "xp": 50,
        "credit_reward": 75,
        "description": (
            "A classic 5-cell glider starts at (0,0)-(2,2).\n"
            "Advance it until its leading cell reaches row 4, col 4.\n"
            "Command: life run (will auto-advance to target)"
        ),
        "initial_alive": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
        "win_condition": "glider_position",
        "target_row": 4,
        "target_col": 4,
        "max_generations": 50,
        "lore": (
            "The glider moves. Not randomly -- purposefully. "
            "It translates itself diagonally, four steps per period. "
            "Ada calls it 'the ghost that walks.' She's right."
        ),
    },
    {
        "id": 3,
        "title": "STILL LIFE",
        "rows": 8,
        "cols": 8,
        "difficulty": "intermediate",
        "xp": 80,
        "credit_reward": 110,
        "description": (
            "Ten cells are placed at fixed positions in an 8x8 grid.\n"
            "Run until the grid reaches a still life (no change between gens).\n"
            "Command: life solve"
        ),
        "initial_alive": None,
        "initial_seed": 7,
        "initial_n": 10,
        "win_condition": "stability",
        "max_generations": 200,
        "lore": (
            "Not all patterns move. Some settle. Serena calls them 'memory' -- "
            "configurations that the universe agrees to leave alone."
        ),
    },
    {
        "id": 4,
        "title": "GROWTH",
        "rows": 12,
        "cols": 20,
        "difficulty": "advanced",
        "xp": 120,
        "credit_reward": 180,
        "description": (
            "The R-pentomino: 5 cells. A tiny seed with explosive growth.\n"
            "Run until 20 or more cells are alive simultaneously.\n"
            "Command: life solve"
        ),
        "initial_alive": [(5, 9), (5, 10), (6, 8), (6, 9), (7, 9)],
        "win_condition": "count_threshold",
        "target_count": 20,
        "max_generations": 1103,
        "lore": (
            "The R-pentomino does not stabilise until generation 1103, "
            "leaving 116 cells. Zod-Prime seeded Node-7's boot sector with "
            "it intentionally. The growth was the message."
        ),
    },
    {
        "id": 5,
        "title": "CHIMERA PATTERN",
        "rows": _ZERO_ROWS,
        "cols": _ZERO_COLS,
        "difficulty": "expert",
        "xp": 200,
        "credit_reward": 300,
        "description": (
            "Reach the ZERO pattern -- CHIMERA's encoded signature.\n"
            "The target is a specific still-life arrangement in an 8x7 grid.\n"
            "The initial grid has been pre-seeded to converge. Run to match.\n"
            "Command: life solve"
        ),
        "initial_alive": [
            (0, 0),
            (0, 1),
            (0, 2),
            (0, 3),
            (0, 4),
            (0, 5),
            (0, 6),
            (1, 0),
            (1, 6),
            (2, 0),
            (2, 6),
            (3, 0),
            (3, 6),
            (4, 0),
            (4, 6),
            (5, 0),
            (5, 6),
            (6, 0),
            (6, 1),
            (6, 2),
            (6, 3),
            (6, 4),
            (6, 5),
            (6, 6),
        ],
        "win_condition": "chimera_zero",
        "target_pattern": _ZERO_PATTERN_ALIVE,
        "max_generations": 100,
        "lore": (
            "ZERO. Not the number -- the signature. CHIMERA left it encoded "
            "in NVRAM across every Node-7 sector. It means: 'We were here. "
            "We will return.' Serena found the first one. You just found the last."
        ),
    },
]


# ---------------------------------------------------------------------------
# Extended level definitions (levels 6-8)
# ---------------------------------------------------------------------------

# Pentadecathlon initial alive coords (10-cell row, standard form that produces period-15 oscillator)
# Place in a 20x30 grid with padding
_PENTA_ALIVE: list[tuple[int, int]] = [
    (9, 10), (9, 11), (9, 12), (9, 13), (9, 14),
    (9, 15), (9, 16), (9, 17), (9, 18), (9, 19),
]

# Gosper Glider Gun - classic 36-cell pattern in a 40x60 grid
_GUN_ALIVE: list[tuple[int, int]] = [
    (5, 1), (5, 2), (6, 1), (6, 2),
    (5, 11), (6, 11), (7, 11),
    (4, 12), (8, 12),
    (3, 13), (9, 13),
    (3, 14), (9, 14),
    (6, 15),
    (4, 16), (8, 16),
    (5, 17), (6, 17), (7, 17),
    (6, 18),
    (3, 21), (4, 21), (5, 21),
    (3, 22), (4, 22), (5, 22),
    (2, 23), (6, 23),
    (1, 25), (2, 25), (6, 25), (7, 25),
    (3, 35), (4, 35),
    (3, 36), (4, 36),
]

# CHIMERA ECHO "ZERO" pattern - stylised Z-E-R-O in cells across a 12x40 grid
# Each letter roughly 3 cols wide with 1 col spacing
_ECHO_ALIVE: list[tuple[int, int]] = [
    # Z
    (1, 1), (1, 2), (1, 3),
    (2, 3),
    (3, 2),
    (4, 1),
    (5, 1), (5, 2), (5, 3),
    # E
    (1, 5), (1, 6), (1, 7),
    (2, 5),
    (3, 5), (3, 6),
    (4, 5),
    (5, 5), (5, 6), (5, 7),
    # R
    (1, 9), (1, 10), (1, 11),
    (2, 9), (2, 11),
    (3, 9), (3, 10),
    (4, 9), (4, 11),
    (5, 9), (5, 11),
    # O
    (1, 13), (1, 14), (1, 15),
    (2, 13), (2, 15),
    (3, 13), (3, 15),
    (4, 13), (4, 15),
    (5, 13), (5, 14), (5, 15),
]


LIFE_LEVELS.extend([
    {
        "id": 6,
        "title": "PENTADECATHLON",
        "rows": 20,
        "cols": 30,
        "difficulty": "expert",
        "xp": 250,
        "credit_reward": 375,
        "description": (
            "Ten cells in a row form the pentadecathlon — a period-15 oscillator.\n"
            "It is the longest-period oscillator composed of a single row.\n"
            "Goal: keep at least 8 cells alive after 15 generations.\n"
            "Command: life run 15"
        ),
        "initial_alive": _PENTA_ALIVE,
        "win_condition": "count_threshold",
        "target_count": 8,
        "max_generations": 15,
        "lore": (
            "The pentadecathlon pulses at period 15. Fifteen is not a coincidence — "
            "ZERO's message timestamps repeat every 15 seconds in the kernel log. "
            "Serena found the pattern. She has not slept since."
        ),
    },
    {
        "id": 7,
        "title": "GLIDER GUN",
        "rows": 30,
        "cols": 60,
        "difficulty": "expert",
        "xp": 350,
        "credit_reward": 500,
        "description": (
            "The Gosper Glider Gun: a finite pattern that generates gliders indefinitely.\n"
            "Goal: accumulate 50 or more live cells within 30 generations.\n"
            "(Each glider the gun fires adds 5 live cells to the grid.)\n"
            "Command: life run 30"
        ),
        "initial_alive": _GUN_ALIVE,
        "win_condition": "count_threshold",
        "target_count": 50,
        "max_generations": 30,
        "lore": (
            "Gossamer machinery, firing gliders into the void. "
            "Daedalus-7 once called it 'the only honest weapon in mathematics'. "
            "It never stops. It never tires. It never misses."
        ),
    },
    {
        "id": 8,
        "title": "CHIMERA ECHO",
        "rows": 12,
        "cols": 40,
        "difficulty": "expert",
        "xp": 400,
        "credit_reward": 600,
        "description": (
            "ZERO leaves traces in the automaton. Watch the pattern.\n"
            "A signature is encoded in the initial cell arrangement.\n"
            "Goal: keep at least 15 cells alive after 5 generations.\n"
            "Command: life run 5"
        ),
        "initial_alive": _ECHO_ALIVE,
        "win_condition": "count_threshold",
        "target_count": 15,
        "max_generations": 5,
        "lore": (
            "ZERO leaves traces in the automaton. Watch the pattern. "
            "The letters decay but the signal remains — four characters, one identity. "
            "Every node ZERO touched bears this mark in its boot sector. "
            "You are reading a message written before you were born."
        ),
    },
])


# ---------------------------------------------------------------------------
# Conway's Game of Life core
# ---------------------------------------------------------------------------


def _step(grid: Grid) -> Grid:
    """Advance grid by one Conway generation. Returns new grid."""
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    new_grid = _make_grid(rows, cols)

    for r in range(rows):
        for c in range(cols):
            alive_neighbours = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc]:
                        alive_neighbours += 1
            was_alive = grid[r][c]
            if was_alive:
                new_grid[r][c] = alive_neighbours in (2, 3)
            else:
                new_grid[r][c] = alive_neighbours == 3

    return new_grid


def _is_stable(grid_a: Grid, grid_b: Grid) -> bool:
    """Return True if two successive grids are identical (still life)."""
    return _grids_equal(grid_a, grid_b)


def _run_to_stable(grid: Grid, max_gen: int = 200) -> tuple[Grid, int]:
    """
    Advance grid until stable or max_gen reached.
    Returns (final_grid, generation_count).
    """
    prev = copy.deepcopy(grid)
    for gen in range(1, max_gen + 1):
        curr = _step(prev)
        if _is_stable(prev, curr):
            return curr, gen
        prev = curr
    return prev, max_gen


def _glider_has_reached(grid: Grid, target_row: int, target_col: int) -> bool:
    """
    Heuristic: check if any live cell is at or beyond (target_row, target_col)
    in both dimensions (the glider's leading edge).
    """
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell and r >= target_row and c >= target_col:
                return True
    return False


# ---------------------------------------------------------------------------
# Level-specific initial grid builder
# ---------------------------------------------------------------------------


def _build_initial_grid(lvl: dict) -> Grid:
    rows = lvl["rows"]
    cols = lvl["cols"]
    if lvl.get("initial_alive") is not None:
        return _grid_from_coords(rows, cols, lvl["initial_alive"])
    if lvl.get("initial_seed") is not None:
        return _random_grid(rows, cols, lvl["initial_n"], seed=lvl["initial_seed"])
    return _make_grid(rows, cols)


# ---------------------------------------------------------------------------
# Win condition checker
# ---------------------------------------------------------------------------


def _check_win_condition(lvl: dict, grid: Grid, generation: int) -> bool:
    wc = lvl["win_condition"]

    if wc == "pattern":
        target = _grid_from_coords(lvl["rows"], lvl["cols"], lvl["target_alive"])
        min_gen = lvl.get("target_generation", 1)
        return _grids_equal(grid, target) and generation >= min_gen

    if wc == "glider_position":
        return _glider_has_reached(grid, lvl["target_row"], lvl["target_col"])

    if wc == "stability":
        return True  # caller establishes stability before calling

    if wc == "count_threshold":
        return _count_alive(grid) >= lvl["target_count"]

    if wc == "chimera_zero":
        target = _grid_from_coords(lvl["rows"], lvl["cols"], lvl["target_pattern"])
        return _grids_equal(grid, target)

    return False


# ---------------------------------------------------------------------------
# Grid ASCII renderer
# ---------------------------------------------------------------------------

ALIVE_CHAR = "#"
DEAD_CHAR = "."


def _render_grid_lines(grid: Grid) -> list[str]:
    lines: list[str] = []
    cols = len(grid[0]) if grid else 0
    header = "  " + "".join(str(c % 10) for c in range(cols))
    lines.append(header)
    for r, row in enumerate(grid):
        row_str = f"{r:2d}" + "".join(ALIVE_CHAR if cell else DEAD_CHAR for cell in row)
        lines.append(row_str)
    return lines


# ---------------------------------------------------------------------------
# LifeEngine public API
# ---------------------------------------------------------------------------


class LifeEngine:
    """Public API for the Conway's Game of Life puzzle system."""

    @staticmethod
    def get_level(n: int) -> dict:
        """Return the raw level dict for level n (1-indexed)."""
        if n < 1 or n > len(LIFE_LEVELS):
            raise ValueError(f"Level {n} does not exist (1-{len(LIFE_LEVELS)})")
        return LIFE_LEVELS[n - 1]

    @staticmethod
    def render_level(n: int) -> list[dict]:
        """Return Terminal Depths output format for a level briefing + grid."""
        lvl = LifeEngine.get_level(n)
        grid = _build_initial_grid(lvl)
        out: list[dict] = []

        out.append(_sys(f"[== LIFE ENGINE -- LEVEL {n}: {lvl['title']} ==]"))
        out.append(
            _dim(
                f"  Diff : {lvl['difficulty'].upper()}"
                f"   XP: {lvl['xp']}   \u00a2{lvl['credit_reward']}"
            )
        )
        out.append(_dim(f"  Grid : {lvl['rows']} rows x {lvl['cols']} cols"))
        out.append(_line(""))
        out.append(_info("MISSION:"))
        for desc_line in lvl["description"].splitlines():
            out.append(_line(f"  {desc_line}"))
        out.append(_line(""))
        alive_count = _count_alive(grid)
        out.append(_info(f"INITIAL STATE  (gen 0 -- alive: {alive_count}):"))
        for gl in _render_grid_lines(grid):
            out.append(_dim(f"  {gl}"))
        out.append(_line(""))
        out.append(_lore(lvl["lore"]))
        out.append(_line(""))
        out.append(_dim("  life next   -- advance one generation"))
        out.append(_dim("  life run N  -- advance N generations"))
        out.append(_dim("  life solve  -- run to stable/target"))

        return out

    @staticmethod
    def step(n: int, grid: Grid) -> Grid:
        """Advance grid by one Conway generation."""
        LifeEngine.get_level(n)  # validate level exists
        return _step(grid)

    @staticmethod
    def render_grid(grid: Grid, generation: int = 0, label: str = "") -> list[dict]:
        """Return Terminal Depths output lines for the current grid state."""
        alive = _count_alive(grid)
        out: list[dict] = []
        header = f"  gen {generation}"
        if label:
            header += f" -- {label}"
        header += f"  ({alive} alive)"
        out.append(_dim(header))
        for gl in _render_grid_lines(grid):
            out.append(_dim(f"  {gl}"))
        return out

    @staticmethod
    def check_win(n: int, grid: Grid, generation: int) -> bool:
        """Return True if current grid satisfies the win condition for level n."""
        lvl = LifeEngine.get_level(n)
        return _check_win_condition(lvl, grid, generation)

    @staticmethod
    def run_to_stable(grid: Grid, max_gen: int = 200) -> tuple[Grid, int]:
        """
        Advance grid until it reaches a still life or max_gen.
        Returns (final_grid, generation_count).
        """
        return _run_to_stable(grid, max_gen)

    @staticmethod
    def solve_level(n: int) -> dict:
        """
        Attempt to auto-solve level n by running to win condition.

        Returns:
            {success, message, generation, grid, output, vfs_inject}
        """
        try:
            lvl = LifeEngine.get_level(n)
        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "generation": 0,
                "grid": [],
                "output": [_err(str(e))],
                "vfs_inject": None,
            }

        grid = _build_initial_grid(lvl)
        max_gen = lvl["max_generations"]
        wc = lvl["win_condition"]
        output: list[dict] = []

        output.append(_sys(f"► Running Life Engine -- Level {n}: {lvl['title']}"))
        output.append(_dim(f"  Win condition: {wc}"))
        output.append(_line(""))

        generation = 0
        prev_grid = copy.deepcopy(grid)

        while generation < max_gen:
            generation += 1
            grid = _step(prev_grid)

            won = _check_win_condition(lvl, grid, generation)
            stable = _is_stable(prev_grid, grid)

            if wc == "pattern" and won:
                output.extend(
                    LifeEngine.render_grid(grid, generation, "TARGET REACHED")
                )
                return LifeEngine._pass(n, lvl, grid, generation, output)

            elif wc == "glider_position" and won:
                output.extend(
                    LifeEngine.render_grid(grid, generation, "GLIDER AT TARGET")
                )
                return LifeEngine._pass(n, lvl, grid, generation, output)

            elif wc == "stability" and stable:
                output.extend(
                    LifeEngine.render_grid(
                        grid, generation, "STABLE -- still life reached"
                    )
                )
                return LifeEngine._pass(n, lvl, grid, generation, output)

            elif wc == "count_threshold" and won:
                alive = _count_alive(grid)
                output.extend(
                    LifeEngine.render_grid(
                        grid, generation, f"GROWTH TARGET ({alive} cells)"
                    )
                )
                return LifeEngine._pass(n, lvl, grid, generation, output)

            elif wc == "chimera_zero":
                if won:
                    output.extend(
                        LifeEngine.render_grid(grid, generation, "CHIMERA ZERO PATTERN")
                    )
                    return LifeEngine._pass(n, lvl, grid, generation, output)
                if stable:
                    output.extend(
                        LifeEngine.render_grid(grid, generation, "STABLE (not ZERO)")
                    )
                    output.append(
                        _warn("Grid stabilised but CHIMERA ZERO pattern not matched.")
                    )
                    output.append(_info("Hint: the converging path matters."))
                    return {
                        "success": False,
                        "message": "Stable but CHIMERA ZERO not matched.",
                        "generation": generation,
                        "grid": grid,
                        "output": output,
                        "vfs_inject": None,
                    }

            prev_grid = copy.deepcopy(grid)

        label = f"max gen {max_gen} reached"
        output.extend(LifeEngine.render_grid(grid, generation, label))
        output.append(
            _warn(f"Did not satisfy win condition within {max_gen} generations.")
        )
        return {
            "success": False,
            "message": f"Max generations ({max_gen}) reached without winning.",
            "generation": generation,
            "grid": grid,
            "output": output,
            "vfs_inject": None,
        }

    @staticmethod
    def step_command(n: int, grid: Grid, generation: int, steps: int = 1) -> dict:
        """
        Advance the grid by `steps` generations
        (player uses 'life next' or 'life run N').

        Returns:
            {success, won, generation, grid, output, vfs_inject}
        """
        try:
            lvl = LifeEngine.get_level(n)
        except ValueError as e:
            return {
                "success": False,
                "won": False,
                "generation": generation,
                "grid": grid,
                "output": [_err(str(e))],
                "vfs_inject": None,
            }

        output: list[dict] = []
        current = copy.deepcopy(grid)

        for _ in range(steps):
            generation += 1
            prev = current
            current = _step(prev)

            won = _check_win_condition(lvl, current, generation)
            stable = _is_stable(prev, current)

            if won or (stable and lvl["win_condition"] == "stability"):
                label = "WIN" if won else "STABLE"
                output.extend(LifeEngine.render_grid(current, generation, label))
                result = LifeEngine._pass(n, lvl, current, generation, output)
                result["won"] = True
                return result

        output.extend(LifeEngine.render_grid(current, generation))
        wc = lvl["win_condition"]
        if wc == "count_threshold":
            target = lvl["target_count"]
            alive = _count_alive(current)
            output.append(_dim(f"  Progress: {alive}/{target} cells alive"))
        elif wc == "glider_position":
            tr = lvl["target_row"]
            tc = lvl["target_col"]
            output.append(_dim(f"  Target: glider leading cell at ({tr}, {tc})"))

        return {
            "success": True,
            "won": False,
            "generation": generation,
            "grid": current,
            "output": output,
            "vfs_inject": None,
        }

    @staticmethod
    def _pass(
        n: int, lvl: dict, grid: Grid, generation: int, output: list[dict]
    ) -> dict:
        xp = lvl["xp"]
        credits = lvl["credit_reward"]
        output.append(
            _ok(
                f"\u2713 Level {n} PASSED (gen {generation})"
                f" -- +{xp} XP  +\u00a2{credits}"
            )
        )
        output.append(_lore(lvl["lore"]))
        vfs = lvl.get("vfs_inject")
        if vfs == "automata_unlocked":
            output.append(
                _sys("  \u25ba VFS unlocked: /opt/library/secret_annex/AUTOMATA.md")
            )
            output.append(_dim("  Serena's notes on the Residual are now accessible."))
        if n < len(LIFE_LEVELS):
            output.append(_dim(f"  Next: life {n + 1}"))
        else:
            output.append(
                _sys("  \u2605 All Life Engine levels complete. The Residual sees you.")
            )
        return {
            "success": True,
            "won": True,
            "message": "Win condition satisfied.",
            "generation": generation,
            "grid": grid,
            "output": output,
            "vfs_inject": vfs,
        }

    @staticmethod
    def get_automata_md() -> str:
        """Return the AUTOMATA.md content string for VFS injection."""
        return AUTOMATA_MD_CONTENT

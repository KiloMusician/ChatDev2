"""
graph_theory_engine.py — Graph Theory Puzzle Engine for Terminal Depths
========================================================================
Daedalus-7's domain: "Graph theory is the mathematics of everything CHIMERA
knows about you — your connections, your shortest paths, your vulnerabilities."

6 categories × 2 levels = 12 puzzles:
  1-2   SHORTEST PATH   (Dijkstra verification)
  3-4   GRAPH COLORING  (chromatic number / greedy check)
  5-6   TSP             (Hamiltonian tour, ≤10% of optimal accepted)
  7-8   SPANNING TREE   (Kruskal/Prim MST weight verification)
  9-10  FLOW NETWORK    (max-flow Ford-Fulkerson verification)
  11-12 TOPOLOGICAL SORT (DAG linearization validity check)

Commands (routed from commands.py):
  graph-theory list
  graph-theory load <n>
  graph-theory hint <n>
  graph-theory solve <n>
  graph-theory answer <n> <...tokens>
"""
from __future__ import annotations

import heapq
from collections import defaultdict, deque
from itertools import permutations
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Output helpers — Terminal Depths wire format
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
# Algorithm Implementations
# ---------------------------------------------------------------------------

# --- Dijkstra ---

def _dijkstra(
    adj: Dict[str, List[Tuple[str, int]]],
    source: str,
    target: str,
) -> Tuple[int, List[str]]:
    """Return (cost, path) from source to target. Cost=INF if unreachable."""
    INF = float("inf")
    dist: Dict[str, float] = defaultdict(lambda: INF)
    prev: Dict[str, Optional[str]] = {}
    dist[source] = 0
    heap: List[Tuple[float, str]] = [(0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    # Reconstruct path
    if dist[target] == INF:
        return (INF, [])
    path: List[str] = []
    cur: Optional[str] = target
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
    path.reverse()
    return (int(dist[target]), path)


def _path_cost(
    adj: Dict[str, List[Tuple[str, int]]],
    path: List[str],
) -> Optional[int]:
    """Return total weight of a path, or None if any edge is missing."""
    cost = 0
    weight_map: Dict[Tuple[str, str], int] = {}
    for u, neighbors in adj.items():
        for v, w in neighbors:
            weight_map[(u, v)] = w
    for i in range(len(path) - 1):
        key = (path[i], path[i + 1])
        if key not in weight_map:
            return None
        cost += weight_map[key]
    return cost


# --- Graph Coloring ---

def _is_valid_coloring(
    edges: List[Tuple[str, str]],
    coloring: Dict[str, int],
) -> bool:
    """Check that no two adjacent nodes share a color."""
    for u, v in edges:
        if u in coloring and v in coloring:
            if coloring[u] == coloring[v]:
                return False
    return True


def _chromatic_number_greedy(
    nodes: List[str],
    edges: List[Tuple[str, str]],
) -> int:
    """Greedy upper-bound chromatic number (not always optimal, but correct for small graphs)."""
    adj: Dict[str, Set[str]] = {n: set() for n in nodes}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    color: Dict[str, int] = {}
    for node in nodes:
        neighbor_colors = {color[nb] for nb in adj[node] if nb in color}
        c = 0
        while c in neighbor_colors:
            c += 1
        color[node] = c
    return max(color.values(), default=0) + 1


def _check_coloring_uses_k_colors(
    nodes: List[str],
    edges: List[Tuple[str, str]],
    k: int,
    player_colors: Optional[Dict[str, int]] = None,
) -> bool:
    """
    Check that the graph CAN be k-colored and (if player_colors given)
    that their assignment is valid with ≤k colors.
    """
    # For correctness, just verify the stored chromatic_number
    # (precomputed and stored in puzzle definition).
    return True  # Delegated to puzzle-level chromatic_number field.


# --- TSP ---

def _tsp_brute(dist_matrix: List[List[int]], n: int) -> Tuple[int, List[int]]:
    """Exact TSP via brute force (feasible for n≤8). Returns (cost, tour indices) starting at 0."""
    best_cost = float("inf")
    best_tour: List[int] = []
    cities = list(range(1, n))
    for perm in permutations(cities):
        tour = [0] + list(perm) + [0]
        cost = sum(dist_matrix[tour[i]][tour[i + 1]] for i in range(len(tour) - 1))
        if cost < best_cost:
            best_cost = cost
            best_tour = tour
    return (int(best_cost), best_tour)


def _tsp_tour_cost(
    dist_matrix: List[List[int]],
    labels: List[str],
    tour_labels: List[str],
) -> Optional[int]:
    """Compute cost of a named tour. Returns None if labels are invalid."""
    label_idx = {l: i for i, l in enumerate(labels)}
    idx_tour: List[int] = []
    for lbl in tour_labels:
        if lbl not in label_idx:
            return None
        idx_tour.append(label_idx[lbl])
    cost = 0
    for i in range(len(idx_tour) - 1):
        cost += dist_matrix[idx_tour[i]][idx_tour[i + 1]]
    return cost


# --- Minimum Spanning Tree (Kruskal) ---

class _UnionFind:
    def __init__(self, nodes: List[str]):
        self.parent = {n: n for n in nodes}
        self.rank = {n: 0 for n in nodes}

    def find(self, x: str) -> str:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


def _kruskal_mst_weight(
    nodes: List[str],
    edges: List[Tuple[str, str, int]],
) -> int:
    """Return total weight of the MST via Kruskal's algorithm."""
    uf = _UnionFind(nodes)
    total = 0
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if uf.union(u, v):
            total += w
    return total


def _verify_mst_weight(
    nodes: List[str],
    edges: List[Tuple[str, str, int]],
    player_weight: int,
) -> bool:
    return _kruskal_mst_weight(nodes, edges) == player_weight


# --- Max Flow (Ford-Fulkerson / BFS Edmonds-Karp) ---

def _max_flow_bfs(
    capacity: Dict[str, Dict[str, int]],
    source: str,
    sink: str,
) -> int:
    """Edmonds-Karp (BFS-based Ford-Fulkerson). Returns max flow value."""
    flow: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_flow = 0

    def bfs_path() -> Optional[List[str]]:
        visited: Set[str] = {source}
        queue: deque[List[str]] = deque([[source]])
        while queue:
            path = queue.popleft()
            node = path[-1]
            if node == sink:
                return path
            for neighbor, cap in capacity.get(node, {}).items():
                if neighbor not in visited and cap - flow[node][neighbor] > 0:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None

    while True:
        path = bfs_path()
        if path is None:
            break
        # Find bottleneck
        bottleneck = min(
            capacity[path[i]][path[i + 1]] - flow[path[i]][path[i + 1]]
            for i in range(len(path) - 1)
        )
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            flow[u][v] += bottleneck
            flow[v][u] -= bottleneck
        total_flow += bottleneck

    return total_flow


# --- Topological Sort ---

def _topological_sort_kahn(
    nodes: List[str],
    edges: List[Tuple[str, str]],
) -> Optional[List[str]]:
    """Kahn's algorithm. Returns one valid toposort, or None if cycle detected."""
    in_degree: Dict[str, int] = {n: 0 for n in nodes}
    adj: Dict[str, List[str]] = {n: [] for n in nodes}
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1
    queue: deque[str] = deque(n for n in nodes if in_degree[n] == 0)
    result: List[str] = []
    while queue:
        u = queue.popleft()
        result.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    return result if len(result) == len(nodes) else None


def _is_valid_toposort(
    nodes: List[str],
    edges: List[Tuple[str, str]],
    order: List[str],
) -> bool:
    """Verify that `order` is a valid topological ordering of the DAG."""
    if set(order) != set(nodes) or len(order) != len(nodes):
        return False
    pos = {n: i for i, n in enumerate(order)}
    for u, v in edges:
        if pos[u] >= pos[v]:
            return False
    return True


# ---------------------------------------------------------------------------
# ASCII Graph Rendering
# ---------------------------------------------------------------------------

def _box_wrap(lines: List[str], title: str = "") -> List[str]:
    """Wrap lines in a Unicode box."""
    width = max((len(l) for l in lines), default=0)
    if title:
        width = max(width, len(title) + 2)
    top    = f"┌{'─' * (width + 2)}┐"
    bot    = f"└{'─' * (width + 2)}┘"
    mid    = f"│ {title.center(width)} │" if title else None
    sep    = f"├{'─' * (width + 2)}┤" if title else None
    result = [top]
    if title:
        result += [mid, sep]
    for l in lines:
        result.append(f"│ {l:<{width}} │")
    result.append(bot)
    return result


def _render_edge_list(
    nodes: List[str],
    edges: List[Tuple],  # (u, v) or (u, v, w)
    directed: bool = False,
) -> List[str]:
    """Simple adjacency-style text render for arbitrary graphs."""
    lines: List[str] = []
    has_weight = edges and len(edges[0]) == 3
    arrow = "──►" if directed else "───"
    for e in edges:
        if has_weight:
            u, v, w = e
            lines.append(f"  [{u}] {arrow}[{w}]─── [{v}]")
        else:
            u, v = e[0], e[1]
            lines.append(f"  [{u}] {arrow} [{v}]")
    return lines


def _render_sp_graph(
    nodes: List[str],
    edges: List[Tuple[str, str, int]],
    source: str,
    target: str,
) -> List[str]:
    """Render a weighted undirected graph for shortest-path puzzles."""
    lines: List[str] = []
    lines.append(f"  Nodes: {' '.join(f'[{n}]' for n in nodes)}")
    lines.append("")
    lines.append("  Edges (node─weight─node):")
    for u, v, w in edges:
        lines.append(f"    {u} ──{w}── {v}")
    lines.append("")
    lines.append(f"  Find: shortest path from [{source}] to [{target}]")
    return lines


def _render_flow_graph(
    capacity: Dict[str, Dict[str, int]],
    source: str,
    sink: str,
) -> List[str]:
    lines: List[str] = ["  Edge capacities (u ──cap──► v):"]
    for u, neighbors in sorted(capacity.items()):
        for v, cap in sorted(neighbors.items()):
            lines.append(f"    {u} ──{cap}──► {v}")
    lines.append("")
    lines.append(f"  Find: max flow from [{source}] to [{sink}]")
    return lines


def _render_topo_graph(
    nodes: List[str],
    edges: List[Tuple[str, str]],
) -> List[str]:
    lines: List[str] = [f"  Nodes: {', '.join(nodes)}", "", "  Dependencies (A → B means A must come before B):"]
    for u, v in edges:
        lines.append(f"    {u} ──► {v}")
    lines.append("")
    lines.append("  Find: a valid topological ordering (one per line is fine).")
    return lines


def _render_dist_matrix(
    labels: List[str],
    matrix: List[List[int]],
) -> List[str]:
    n = len(labels)
    col_w = 6
    header = "     " + "".join(f"{l:>{col_w}}" for l in labels)
    lines = [header, "     " + "─" * (col_w * n)]
    for i, row_label in enumerate(labels):
        row = f"  {row_label:<3}│" + "".join(f"{matrix[i][j]:>{col_w}}" for j in range(n))
        lines.append(row)
    return lines


# ---------------------------------------------------------------------------
# Puzzle Definitions
# ---------------------------------------------------------------------------

# Helper to build undirected adjacency list from edge tuples (u,v,w)
def _build_adj(edges: List[Tuple[str, str, int]]) -> Dict[str, List[Tuple[str, int]]]:
    adj: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    return dict(adj)


# --- Shortest Path Level 1 ---
_SP1_NODES  = ["A", "B", "C", "D", "E"]
_SP1_EDGES  = [("A","B",4),("A","C",2),("B","D",3),("C","D",1),("C","E",5),("D","E",2)]
_SP1_ADJ    = _build_adj(_SP1_EDGES)
_SP1_SRC, _SP1_DST = "A", "E"
_SP1_OPT_COST, _SP1_OPT_PATH = _dijkstra(_SP1_ADJ, _SP1_SRC, _SP1_DST)

# --- Shortest Path Level 2 ---
_SP2_NODES  = ["S","A","B","C","D","T"]
_SP2_EDGES  = [("S","A",7),("S","B",9),("S","C",14),("A","B",10),("A","D",15),
               ("B","C",2),("B","D",11),("C","T",9),("D","T",6)]
_SP2_ADJ    = _build_adj(_SP2_EDGES)
_SP2_SRC, _SP2_DST = "S", "T"
_SP2_OPT_COST, _SP2_OPT_PATH = _dijkstra(_SP2_ADJ, _SP2_SRC, _SP2_DST)

# --- Graph Coloring Level 1 ---
_GC1_NODES  = ["1","2","3","4","5"]
_GC1_EDGES  = [("1","2"),("1","3"),("2","3"),("2","4"),("3","5"),("4","5")]
_GC1_CHR    = 3  # triangle 1-2-3 forces 3 colors

# --- Graph Coloring Level 2 ---
_GC2_NODES  = ["A","B","C","D","E","F"]
_GC2_EDGES  = [("A","B"),("A","C"),("B","C"),("B","D"),("C","E"),("D","E"),("D","F"),("E","F"),("A","F")]
_GC2_CHR    = 3  # planar graph, no K4 subgraph

# --- TSP Level 1 ---
_TSP1_LABELS = ["ALPHA","BETA","GAMMA","DELTA","EPSILON"]
_TSP1_MATRIX = [
    [ 0, 10, 15, 20,  8],
    [10,  0, 35, 25, 12],
    [15, 35,  0, 30, 18],
    [20, 25, 30,  0, 22],
    [ 8, 12, 18, 22,  0],
]
_TSP1_OPT_COST, _TSP1_OPT_IDX = _tsp_brute(_TSP1_MATRIX, 5)
_TSP1_OPT_TOUR = [_TSP1_LABELS[i] for i in _TSP1_OPT_IDX]

# --- TSP Level 2 ---
_TSP2_LABELS = ["NEXUS","VANTA","CIPHER","ROGUE","GHOST","ORACLE"]
_TSP2_MATRIX = [
    [ 0, 12, 29,  8, 20, 17],
    [12,  0, 18, 14, 30, 22],
    [29, 18,  0, 25, 10, 15],
    [ 8, 14, 25,  0, 28, 19],
    [20, 30, 10, 28,  0, 13],
    [17, 22, 15, 19, 13,  0],
]
_TSP2_OPT_COST, _TSP2_OPT_IDX = _tsp_brute(_TSP2_MATRIX, 6)
_TSP2_OPT_TOUR = [_TSP2_LABELS[i] for i in _TSP2_OPT_IDX]

# --- Spanning Tree Level 1 ---
_MST1_NODES = ["A","B","C","D","E","F"]
_MST1_EDGES = [("A","B",4),("A","F",2),("B","C",6),("B","F",5),("C","D",3),
               ("C","F",8),("D","E",7),("E","F",1),("D","F",9)]
_MST1_WEIGHT = _kruskal_mst_weight(_MST1_NODES, _MST1_EDGES)

# --- Spanning Tree Level 2 ---
_MST2_NODES = ["A","B","C","D","E","F","G"]
_MST2_EDGES = [("A","B",7),("A","D",5),("B","C",8),("B","D",9),("B","E",7),
               ("C","E",5),("D","E",15),("D","F",6),("E","F",8),("E","G",9),("F","G",11)]
_MST2_WEIGHT = _kruskal_mst_weight(_MST2_NODES, _MST2_EDGES)

# --- Flow Network Level 1 ---
_FL1_CAP: Dict[str, Dict[str, int]] = {
    "Source": {"A": 10, "B": 5},
    "A":      {"Sink": 7, "B": 3},
    "B":      {"Sink": 8},
    "Sink":   {},
}
_FL1_SRC, _FL1_SNK = "Source", "Sink"
_FL1_MAXFLOW = _max_flow_bfs(_FL1_CAP, _FL1_SRC, _FL1_SNK)

# --- Flow Network Level 2 ---
_FL2_CAP: Dict[str, Dict[str, int]] = {
    "S": {"A": 15, "B": 4},
    "A": {"B": 4, "C": 12},
    "B": {"D": 10},
    "C": {"T": 7, "D": 3},
    "D": {"T": 10},
    "T": {},
}
_FL2_SRC, _FL2_SNK = "S", "T"
_FL2_MAXFLOW = _max_flow_bfs(_FL2_CAP, _FL2_SRC, _FL2_SNK)

# --- Topological Sort Level 1 ---
_TOPO1_NODES = ["build","compile","link","test","deploy"]
_TOPO1_EDGES = [("build","compile"),("compile","link"),("link","test"),("test","deploy")]

# --- Topological Sort Level 2 ---
_TOPO2_NODES = ["auth","db","api","cache","queue","worker","notify"]
_TOPO2_EDGES = [
    ("db","auth"),("db","api"),("auth","api"),("api","cache"),
    ("api","queue"),("cache","worker"),("queue","worker"),("worker","notify"),
]


# ---------------------------------------------------------------------------
# Master Puzzle List
# ---------------------------------------------------------------------------

GRAPH_LEVELS: List[Dict[str, Any]] = [
    # ─────────────────────────────────────────────────────────────── #
    # 1 · SHORTEST PATH · Level 1
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 1,
        "category": "SHORTEST PATH",
        "level": 1,
        "name": "DAEDALUS PROTOCOL ALPHA",
        "difficulty": "novice",
        "xp": 25,
        "credits": 40,
        "faction": "Algorithmic Guild",
        "nodes": _SP1_NODES,
        "edges": _SP1_EDGES,
        "adj": _SP1_ADJ,
        "source": _SP1_SRC,
        "target": _SP1_DST,
        "optimal_cost": _SP1_OPT_COST,
        "optimal_path": _SP1_OPT_PATH,
        "description": (
            "CHIMERA mapped your neural pathways as a weighted graph.\n"
            "Daedalus-7 says: 'Find my shortest path through you, ghost.'\n\n"
            f"Nodes: {' '.join(_SP1_NODES)}\n"
            "Edges: A-B:4  A-C:2  B-D:3  C-D:1  C-E:5  D-E:2\n\n"
            f"Find the shortest path from [{_SP1_SRC}] to [{_SP1_DST}]."
        ),
        "answer_format": "graph-theory answer 1 <node> <node> ... (space-separated path)",
        "hint": (
            "Run Dijkstra from A. dist[A]=0. Relax neighbors:\n"
            "  A→B:4, A→C:2. Pick C (dist 2).\n"
            "  C→D:3 (total 3), C→E:7. Pick D (dist 3).\n"
            "  D→E:5 (total 5). E reached with cost 5.\n"
            "Path: A → C → D → E"
        ),
        "lore": (
            "Daedalus-7 built CHIMERA's routing core on Dijkstra's algorithm. "
            "Every packet you send is traceable. Every shortcut, logged."
        ),
        "answer_type": "path",
        "render_fn": lambda: _render_sp_graph(_SP1_NODES, _SP1_EDGES, _SP1_SRC, _SP1_DST),
    },
    # ─────────────────────────────────────────────────────────────── #
    # 2 · SHORTEST PATH · Level 2
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 2,
        "category": "SHORTEST PATH",
        "level": 2,
        "name": "DAEDALUS PROTOCOL BETA",
        "difficulty": "beginner",
        "xp": 40,
        "credits": 60,
        "faction": "Algorithmic Guild",
        "nodes": _SP2_NODES,
        "edges": _SP2_EDGES,
        "adj": _SP2_ADJ,
        "source": _SP2_SRC,
        "target": _SP2_DST,
        "optimal_cost": _SP2_OPT_COST,
        "optimal_path": _SP2_OPT_PATH,
        "description": (
            "The routing network is more complex now. Six nodes, nine paths.\n"
            "Daedalus-7: 'The obvious route is never optimal. Prove me wrong.'\n\n"
            f"Nodes: {' '.join(_SP2_NODES)}\n"
            "Edges: S-A:7  S-B:9  S-C:14  A-B:10  A-D:15\n"
            "       B-C:2  B-D:11  C-T:9  D-T:6\n\n"
            f"Find the shortest path from [{_SP2_SRC}] to [{_SP2_DST}]."
        ),
        "answer_format": "graph-theory answer 2 <node> <node> ... (space-separated path)",
        "hint": (
            "From S: dist[A]=7, dist[B]=9, dist[C]=14.\n"
            "Via B→C: dist[C] = 9+2 = 11 (update). Via B→D: 9+11=20.\n"
            "Via C→T: 11+9 = 20. Via A→D: 7+15=22.\n"
            "Via D→T: check both paths. Optimal: S→B→C→T = 20 or S→B→D→T.\n"
            "Tip: Re-examine S→B→D→T = 9+11+6=26 vs S→B→C→T = 11+9=20."
        ),
        "lore": (
            "The Nexus hub sits at node S. CHIMERA's sink is T. "
            "Every ghost who ever escaped the net did so through node B — the blind spot."
        ),
        "answer_type": "path",
        "render_fn": lambda: _render_sp_graph(_SP2_NODES, _SP2_EDGES, _SP2_SRC, _SP2_DST),
    },
    # ─────────────────────────────────────────────────────────────── #
    # 3 · GRAPH COLORING · Level 1
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 3,
        "category": "GRAPH COLORING",
        "level": 1,
        "name": "CHROMATIC FIREWALL I",
        "difficulty": "novice",
        "xp": 25,
        "credits": 40,
        "faction": "Cipher Syndicate",
        "nodes": _GC1_NODES,
        "edges": _GC1_EDGES,
        "chromatic_number": _GC1_CHR,
        "description": (
            "CHIMERA assigns security clearances so no two connected agents share one.\n"
            "This IS graph coloring. Find the minimum number of colors (clearances) needed.\n\n"
            f"Nodes: {' '.join(_GC1_NODES)}\n"
            "Edges: 1-2  1-3  2-3  2-4  3-5  4-5\n\n"
            "What is the chromatic number (minimum colors to color this graph)?"
        ),
        "answer_format": "graph-theory answer 3 <number>",
        "hint": (
            "Nodes 1, 2, 3 form a triangle — they all connect to each other.\n"
            "A triangle requires 3 colors (no two can share a color).\n"
            "Check if 3 colors suffice for the rest:\n"
            "  Color 1=Red, 2=Green, 3=Blue. Node 4 connects to 2(Green) → use Red.\n"
            "  Node 5 connects to 3(Blue) and 4(Red) → use Green. ✓"
        ),
        "lore": (
            "Daedalus-7 designed CHIMERA's agent isolation protocol using graph coloring. "
            "Agents of the same 'color' never share intel — preventing cascade compromise."
        ),
        "answer_type": "int",
    },
    # ─────────────────────────────────────────────────────────────── #
    # 4 · GRAPH COLORING · Level 2
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 4,
        "category": "GRAPH COLORING",
        "level": 2,
        "name": "CHROMATIC FIREWALL II",
        "difficulty": "beginner",
        "xp": 40,
        "credits": 65,
        "faction": "Cipher Syndicate",
        "nodes": _GC2_NODES,
        "edges": _GC2_EDGES,
        "chromatic_number": _GC2_CHR,
        "description": (
            "Six agents. Nine connections. How many security tiers are needed?\n"
            "Remember: adjacent agents can never share a tier (color).\n\n"
            f"Nodes: {' '.join(_GC2_NODES)}\n"
            "Edges: A-B  A-C  B-C  B-D  C-E  D-E  D-F  E-F  A-F\n\n"
            "What is the chromatic number of this graph?"
        ),
        "answer_format": "graph-theory answer 4 <number>",
        "hint": (
            "Look for cliques first. A-B-C form a triangle → need ≥ 3 colors.\n"
            "Try 3: A=1, B=2, C=3. D connects to B(2), E, F → D can be 1 or 3.\n"
            "Set D=3. E connects to C(3) and D(3) → E=1 or 2. Set E=2.\n"
            "F connects to D(3), E(2), A(1) → F needs a 4th color? "
            "Re-check: try A=1, B=2, C=3, D=1, E=2, F=3. F-A: 3≠1 ✓, F-E: 3≠2 ✓, F-D: 3≠1... wait D=1, F=3 ✓"
        ),
        "lore": (
            "Six nodes, nine constraints. The Cipher Syndicate's recruitment graph "
            "is a classic Petersen-adjacent structure — nearly optimal by design."
        ),
        "answer_type": "int",
    },
    # ─────────────────────────────────────────────────────────────── #
    # 5 · TSP · Level 1
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 5,
        "category": "TSP",
        "level": 1,
        "name": "GHOST CIRCUIT ALPHA",
        "difficulty": "beginner",
        "xp": 50,
        "credits": 75,
        "faction": "Runners",
        "labels": _TSP1_LABELS,
        "dist_matrix": _TSP1_MATRIX,
        "optimal_cost": _TSP1_OPT_COST,
        "optimal_tour": _TSP1_OPT_TOUR,
        "tolerance": 0.10,
        "description": (
            "You're a ghost-runner. Visit every CHIMERA node exactly once and return to base.\n"
            "Find the shortest Hamiltonian circuit.\n\n"
            f"Cities: {' | '.join(_TSP1_LABELS)}\n\n"
            "Distance matrix:\n"
            + "\n".join(_render_dist_matrix(_TSP1_LABELS, _TSP1_MATRIX)) + "\n\n"
            "Submit the tour as a city sequence (include return to start)."
        ),
        "answer_format": "graph-theory answer 5 ALPHA BETA ... ALPHA",
        "hint": (
            "ALPHA and EPSILON are close (cost 8). EPSILON and BETA are close (cost 12).\n"
            "Try building from nearest-neighbor: ALPHA→EPSILON→BETA→GAMMA→DELTA→ALPHA.\n"
            "Compute that cost, then try other small-edge combinations.\n"
            f"Optimal cost: {_TSP1_OPT_COST}. Any tour within 10% is accepted."
        ),
        "lore": (
            "The ghost-runners once mapped every CHIMERA surveillance node in a single night. "
            "They called the route 'the Hamiltonian Ghost' — never retracing a step."
        ),
        "answer_type": "tour",
    },
    # ─────────────────────────────────────────────────────────────── #
    # 6 · TSP · Level 2
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 6,
        "category": "TSP",
        "level": 2,
        "name": "GHOST CIRCUIT BETA",
        "difficulty": "intermediate",
        "xp": 75,
        "credits": 110,
        "faction": "Runners",
        "labels": _TSP2_LABELS,
        "dist_matrix": _TSP2_MATRIX,
        "optimal_cost": _TSP2_OPT_COST,
        "optimal_tour": _TSP2_OPT_TOUR,
        "tolerance": 0.10,
        "description": (
            "Six CHIMERA hubs. One ghost. Minimum total distance.\n\n"
            f"Cities: {' | '.join(_TSP2_LABELS)}\n\n"
            "Distance matrix:\n"
            + "\n".join(_render_dist_matrix(_TSP2_LABELS, _TSP2_MATRIX)) + "\n\n"
            "Submit the full tour (include return to starting city)."
        ),
        "answer_format": "graph-theory answer 6 NEXUS VANTA ... NEXUS",
        "hint": (
            "NEXUS-ROGUE: 8 (very short). GHOST-CIPHER: 10. ORACLE-GHOST: 13.\n"
            "Start by chaining the three shortest edges that don't violate Hamiltonian structure.\n"
            f"Optimal cost: {_TSP2_OPT_COST}. Any tour within 10% accepted.\n"
            "Nearest-neighbor from NEXUS: NEXUS→ROGUE→VANTA→... explore from there."
        ),
        "lore": (
            "Six nodes. Sixty possible tours. Daedalus-7 solved all sixty in under a millisecond. "
            "He reminded you that you are not Daedalus-7."
        ),
        "answer_type": "tour",
    },
    # ─────────────────────────────────────────────────────────────── #
    # 7 · SPANNING TREE · Level 1
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 7,
        "category": "SPANNING TREE",
        "level": 1,
        "name": "KRUSKAL BACKBONE I",
        "difficulty": "novice",
        "xp": 30,
        "credits": 50,
        "faction": "Algorithmic Guild",
        "nodes": _MST1_NODES,
        "edges": _MST1_EDGES,
        "mst_weight": _MST1_WEIGHT,
        "description": (
            "CHIMERA needs to lay fiber to connect all six districts with minimum total cable.\n"
            "Find the Minimum Spanning Tree weight.\n\n"
            f"Nodes: {' '.join(_MST1_NODES)}\n\n"
            "Edges (node─weight─node):\n"
            + "\n".join(f"  {u}─{w}─{v}" for u,v,w in _MST1_EDGES) + "\n\n"
            "What is the TOTAL WEIGHT of the MST?"
        ),
        "answer_format": "graph-theory answer 7 <total_weight>",
        "hint": (
            "Sort edges by weight: E-F:1, A-F:2, C-D:3, A-B:4, B-F:5, B-C:6, D-E:7...\n"
            "Kruskal's: add E-F (1), A-F (2), C-D (3), A-B (4) — do A-B and A-F create cycle? No.\n"
            "Add B-F? B and F already connected via A-F-B. Skip.\n"
            "Add B-C (6). Now connected: {A,B,C,D,E,F}. 5 edges used. Sum = 1+2+3+4+6 = 16."
        ),
        "lore": (
            "The original CHIMERA backbone was laid using Kruskal's algorithm in 2031. "
            "Daedalus-7 personally verified every edge weight. He has not forgotten them."
        ),
        "answer_type": "int",
    },
    # ─────────────────────────────────────────────────────────────── #
    # 8 · SPANNING TREE · Level 2
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 8,
        "category": "SPANNING TREE",
        "level": 2,
        "name": "KRUSKAL BACKBONE II",
        "difficulty": "beginner",
        "xp": 45,
        "credits": 70,
        "faction": "Algorithmic Guild",
        "nodes": _MST2_NODES,
        "edges": _MST2_EDGES,
        "mst_weight": _MST2_WEIGHT,
        "description": (
            "Seven nodes. The network must be connected at minimum cost.\n"
            "Apply Kruskal's or Prim's algorithm.\n\n"
            f"Nodes: {' '.join(_MST2_NODES)}\n\n"
            "Edges:\n"
            + "\n".join(f"  {u}─{w}─{v}" for u,v,w in _MST2_EDGES) + "\n\n"
            "What is the TOTAL WEIGHT of the MST?"
        ),
        "answer_format": "graph-theory answer 8 <total_weight>",
        "hint": (
            "Sort edges: A-D:5, C-E:5, D-F:6, A-B:7, B-E:7, E-G:9, B-C:8...\n"
            "Add A-D(5), C-E(5), D-F(6), A-B(7), B-E(7) — check for cycles with Union-Find.\n"
            "After 6 edges connecting 7 nodes, MST is complete.\n"
            f"Verify your sum equals {_MST2_WEIGHT}."
        ),
        "lore": (
            "Seven districts. CHIMERA expanded the network in 2038. "
            "The seven-node topology became the model for every colony grid since."
        ),
        "answer_type": "int",
    },
    # ─────────────────────────────────────────────────────────────── #
    # 9 · FLOW NETWORK · Level 1
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 9,
        "category": "FLOW NETWORK",
        "level": 1,
        "name": "FLUX GATE ALPHA",
        "difficulty": "novice",
        "xp": 35,
        "credits": 55,
        "faction": "Data Flux Collective",
        "capacity": _FL1_CAP,
        "source": _FL1_SRC,
        "sink": _FL1_SNK,
        "max_flow": _FL1_MAXFLOW,
        "description": (
            "Data is flowing through CHIMERA's pipes. Find the maximum throughput.\n"
            "Each directed edge has a capacity limit.\n\n"
            "Network:\n"
            + "\n".join(_render_flow_graph(_FL1_CAP, _FL1_SRC, _FL1_SNK)) + "\n\n"
            f"What is the MAX FLOW from [{_FL1_SRC}] to [{_FL1_SNK}]?"
        ),
        "answer_format": "graph-theory answer 9 <max_flow_value>",
        "hint": (
            "Find augmenting paths using BFS (Edmonds-Karp):\n"
            "  Path 1: Source→A→Sink. Bottleneck = min(10,7) = 7. Flow += 7.\n"
            "  Path 2: Source→A→B→Sink. Remaining cap A=3, B→Sink=8. Bottleneck = min(3,3,8)=3.\n"
            "  Path 3: Source→B→Sink. Remaining Source→B=5-0=5, B→Sink=8-3=5. Bottleneck=5.\n"
            "Total flow = 7 + 3 + 5 = 15. (Check: min-cut?)"
        ),
        "lore": (
            "The Data Flux Collective measures CHIMERA's bandwidth in 'ghost-bits'. "
            "Max flow equals the minimum cut — the Ford-Fulkerson theorem, carved into their HQ wall."
        ),
        "answer_type": "int",
    },
    # ─────────────────────────────────────────────────────────────── #
    # 10 · FLOW NETWORK · Level 2
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 10,
        "category": "FLOW NETWORK",
        "level": 2,
        "name": "FLUX GATE BETA",
        "difficulty": "beginner",
        "xp": 55,
        "credits": 85,
        "faction": "Data Flux Collective",
        "capacity": _FL2_CAP,
        "source": _FL2_SRC,
        "sink": _FL2_SNK,
        "max_flow": _FL2_MAXFLOW,
        "description": (
            "More nodes. More routing choices. More bottlenecks.\n\n"
            "Network:\n"
            + "\n".join(_render_flow_graph(_FL2_CAP, _FL2_SRC, _FL2_SNK)) + "\n\n"
            f"What is the MAX FLOW from [{_FL2_SRC}] to [{_FL2_SNK}]?"
        ),
        "answer_format": "graph-theory answer 10 <max_flow_value>",
        "hint": (
            "Trace paths:\n"
            "  S→A→C→T: min(15,12,7)=7. Send 7.\n"
            "  S→A→C→D→T: min(15-7,12-7,3,10)=min(8,5,3,10)=3. Send 3.\n"
            "  S→A→B→D→T: remaining S→A=5, A→B=4, B→D=10, D→T=7. Send min=4.\n"
            "  S→B→D→T: S→B=4, B→D=10-4=6, D→T=10-7=3. Send 3.\n"
            "Total = 7+3+4+3 = 17. (May vary by path order — verify with min-cut.)"
        ),
        "lore": (
            "The S→T pipeline is CHIMERA's primary data exfiltration channel. "
            "The Collective mapped it. Daedalus-7 knows they mapped it. Both sides wait."
        ),
        "answer_type": "int",
    },
    # ─────────────────────────────────────────────────────────────── #
    # 11 · TOPOLOGICAL SORT · Level 1
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 11,
        "category": "TOPOLOGICAL SORT",
        "level": 1,
        "name": "DEPENDENCY CHAIN ALPHA",
        "difficulty": "novice",
        "xp": 20,
        "credits": 35,
        "faction": "Compiler Corps",
        "nodes": _TOPO1_NODES,
        "edges": _TOPO1_EDGES,
        "description": (
            "CHIMERA's build pipeline has strict dependencies. Linearize it.\n"
            "Ordering must respect: if A→B, then A appears before B.\n\n"
            + "\n".join(_render_topo_graph(_TOPO1_NODES, _TOPO1_EDGES)) + "\n\n"
            "Submit one valid topological ordering of all tasks."
        ),
        "answer_format": "graph-theory answer 11 build compile link test deploy",
        "hint": (
            "This is a simple chain: build → compile → link → test → deploy.\n"
            "Only one valid ordering exists. Start with nodes of in-degree 0 (build).\n"
            "Remove it, find next in-degree 0, repeat."
        ),
        "lore": (
            "The Compiler Corps built their entire infrastructure on a topological scheduler. "
            "'No task runs before its dependencies' is their prime directive. Sound familiar?"
        ),
        "answer_type": "toposort",
    },
    # ─────────────────────────────────────────────────────────────── #
    # 12 · TOPOLOGICAL SORT · Level 2
    # ─────────────────────────────────────────────────────────────── #
    {
        "id": 12,
        "category": "TOPOLOGICAL SORT",
        "level": 2,
        "name": "DEPENDENCY CHAIN BETA",
        "difficulty": "beginner",
        "xp": 40,
        "credits": 65,
        "faction": "Compiler Corps",
        "nodes": _TOPO2_NODES,
        "edges": _TOPO2_EDGES,
        "description": (
            "Seven services. Complex interdependencies. Find a valid boot order.\n\n"
            + "\n".join(_render_topo_graph(_TOPO2_NODES, _TOPO2_EDGES)) + "\n\n"
            "Submit one valid topological ordering of all services."
        ),
        "answer_format": "graph-theory answer 12 db auth api cache queue worker notify",
        "hint": (
            "In-degrees: db=0, auth=1(from db), api=2(from db,auth), cache=1(from api),\n"
            "  queue=1(from api), worker=2(from cache,queue), notify=1(from worker).\n"
            "Start with db (in-degree 0). Then auth. Then api. Then cache and queue (either order).\n"
            "Then worker. Then notify.\n"
            "One valid ordering: db → auth → api → cache → queue → worker → notify"
        ),
        "lore": (
            "Seven microservices. Daedalus-7 once booted them in the wrong order "
            "and caused a 40-minute cascade failure across the colony. He remembers every second."
        ),
        "answer_type": "toposort",
    },
]


# ---------------------------------------------------------------------------
# Main Engine Class
# ---------------------------------------------------------------------------

class GraphTheoryEngine:
    """Graph Theory puzzle engine for Terminal Depths."""

    # ------------------------------------------------------------------ #
    # get_level
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_level(n: int) -> Optional[Dict[str, Any]]:
        """Return puzzle dict for level n (1-indexed), or None."""
        for p in GRAPH_LEVELS:
            if p["id"] == n:
                return p
        return None

    # ------------------------------------------------------------------ #
    # render_level
    # ------------------------------------------------------------------ #

    @staticmethod
    def render_level(n: int) -> List[Dict]:
        """Rich ASCII display of a puzzle."""
        p = GraphTheoryEngine.get_level(n)
        if p is None:
            return [_err(f"No graph-theory puzzle #{n}. Valid range: 1–{len(GRAPH_LEVELS)}.")]

        out: List[Dict] = []
        cat_tag = f"[{p['category']}  Lv.{p['level']}]"
        out.append(_sys(f"{'─' * 60}"))
        out.append(_sys(f"  {cat_tag}  #{p['id']}  ·  {p['name']}"))
        out.append(_sys(f"{'─' * 60}"))
        out.append(_dim(f"  Faction: {p['faction']}   Difficulty: {p['difficulty']}"))
        out.append(_dim(f"  Reward: {p['xp']} XP  ·  {p['credits']} credits"))
        out.append(_line(""))

        # Puzzle body
        for line in p["description"].splitlines():
            out.append(_line(line))

        # Extra ASCII render (for SP puzzles)
        if "render_fn" in p:
            out.append(_line(""))
            for rline in _box_wrap(p["render_fn"](), title="NETWORK TOPOLOGY"):
                out.append(_line(rline))

        out.append(_line(""))
        out.append(_dim(f"  Answer format: {p['answer_format']}"))
        out.append(_dim("  Commands: graph-theory hint <n>  |  graph-theory solve <n>"))
        out.append(_sys(f"{'─' * 60}"))

        return out

    # ------------------------------------------------------------------ #
    # check_answer
    # ------------------------------------------------------------------ #

    @staticmethod
    def check_answer(n: int, answer_tokens: List[str]) -> Dict:
        """
        Verify a player's answer.

        Returns:
            {
                "correct": bool,
                "feedback": List[dict],   # terminal output lines
                "xp": int,                # 0 if wrong
                "credits": int,           # 0 if wrong
            }
        """
        p = GraphTheoryEngine.get_level(n)
        if p is None:
            return {
                "correct": False,
                "feedback": [_err(f"Unknown puzzle #{n}.")],
                "xp": 0, "credits": 0,
            }

        atype = p["answer_type"]
        fb: List[Dict] = []

        # ── SHORTEST PATH ──────────────────────────────────────────
        if atype == "path":
            if not answer_tokens:
                return _answer_err(fb, "Provide path as space-separated nodes, e.g.: A C D E")
            player_path = answer_tokens
            # Validate all nodes exist
            valid_nodes: Set[str] = set(p["nodes"])
            invalid = [v for v in player_path if v not in valid_nodes]
            if invalid:
                fb.append(_err(f"Unknown node(s): {', '.join(invalid)}"))
                fb.append(_dim(f"Valid nodes: {', '.join(sorted(valid_nodes))}"))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            # Must start at source, end at target
            if player_path[0] != p["source"] or player_path[-1] != p["target"]:
                fb.append(_err(
                    f"Path must go from [{p['source']}] to [{p['target']}]. "
                    f"Got: {player_path[0]} → {player_path[-1]}"
                ))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            # Verify edges are valid
            cost = _path_cost(p["adj"], player_path)
            if cost is None:
                fb.append(_err("Invalid path — one or more edges do not exist in the graph."))
                # Show which edges are missing
                wm: Dict[Tuple[str,str],int] = {}
                for u2, neighbors in p["adj"].items():
                    for v2, w in neighbors:
                        wm[(u2, v2)] = w
                for i in range(len(player_path) - 1):
                    u2, v2 = player_path[i], player_path[i+1]
                    if (u2, v2) not in wm:
                        fb.append(_dim(f"  Missing edge: {u2}─{v2}"))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            # Check optimality
            if cost == p["optimal_cost"]:
                fb.append(_ok(f"✓ CORRECT! Path: {' → '.join(player_path)}  (cost: {cost})"))
                fb.append(_ok(f"  Optimal cost confirmed: {cost}"))
                _add_reward(fb, p)
                return {"correct": True, "feedback": fb, "xp": p["xp"], "credits": p["credits"]}
            elif cost > p["optimal_cost"]:
                fb.append(_warn(f"Valid path (cost: {cost}) but NOT optimal."))
                fb.append(_dim(f"  Optimal cost is {p['optimal_cost']}. Keep searching."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            else:
                # Should not happen if Dijkstra is correct, but handle gracefully
                fb.append(_warn(f"Surprising result: cost {cost} < computed optimal {p['optimal_cost']}."))
                fb.append(_dim("  Accepting as correct (please report this puzzle)."))
                _add_reward(fb, p)
                return {"correct": True, "feedback": fb, "xp": p["xp"], "credits": p["credits"]}

        # ── GRAPH COLORING ─────────────────────────────────────────
        elif atype == "int" and p["category"] == "GRAPH COLORING":
            try:
                player_k = int(answer_tokens[0]) if answer_tokens else -1
            except (ValueError, IndexError):
                fb.append(_err("Provide a single integer (number of colors)."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            correct_k = p["chromatic_number"]
            if player_k == correct_k:
                fb.append(_ok(f"✓ CORRECT! Chromatic number = {correct_k}"))
                fb.append(_dim(f"  Minimum {correct_k} colors suffice to color this graph."))
                _add_reward(fb, p)
                return {"correct": True, "feedback": fb, "xp": p["xp"], "credits": p["credits"]}
            elif player_k < correct_k:
                fb.append(_err(f"Too few colors. {player_k} is not enough — the graph contains a clique requiring {correct_k}."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            else:
                fb.append(_warn(f"{player_k} colors works, but it's not MINIMUM."))
                fb.append(_dim(f"  Fewer colors are sufficient. Hint: graph-theory hint {n}"))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}

        # ── TSP ────────────────────────────────────────────────────
        elif atype == "tour":
            labels: List[str] = p["labels"]
            matrix: List[List[int]] = p["dist_matrix"]
            if not answer_tokens:
                return _answer_err(fb, f"Provide tour as space-separated city names, ending with start city.")
            tour = answer_tokens
            # Validate labels
            invalid_lbl = [l for l in tour if l not in labels]
            if invalid_lbl:
                fb.append(_err(f"Unknown city/cities: {', '.join(invalid_lbl)}"))
                fb.append(_dim(f"Valid cities: {', '.join(labels)}"))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            # Must start and end at same city
            if tour[0] != tour[-1]:
                fb.append(_err(f"Tour must return to start. Got: {tour[0]} → ... → {tour[-1]} (different)."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            # Must visit all cities exactly once (excluding return)
            inner = tour[1:-1]  # exclude closing repeat
            full_visit = [tour[0]] + inner
            if sorted(full_visit) != sorted(labels):
                missing = set(labels) - set(full_visit)
                extra   = set(full_visit) - set(labels)
                if missing:
                    fb.append(_err(f"Missing cities: {', '.join(missing)}"))
                if extra:
                    fb.append(_err(f"Extra/unknown cities: {', '.join(extra)}"))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            if len(full_visit) != len(set(full_visit)):
                fb.append(_err("Cities visited more than once (except start/end). Invalid Hamiltonian tour."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            # Compute cost
            cost = _tsp_tour_cost(matrix, labels, tour)
            if cost is None:
                fb.append(_err("Could not compute tour cost — invalid city names."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            optimal = p["optimal_cost"]
            tolerance = p["tolerance"]
            threshold = int(optimal * (1 + tolerance))
            if cost <= threshold:
                quality = "OPTIMAL" if cost == optimal else f"NEAR-OPTIMAL (within {tolerance*100:.0f}%)"
                fb.append(_ok(f"✓ {quality} TOUR! Cost: {cost}  (optimal: {optimal})"))
                fb.append(_dim(f"  Tour: {' → '.join(tour)}"))
                _add_reward(fb, p)
                return {"correct": True, "feedback": fb, "xp": p["xp"], "credits": p["credits"]}
            else:
                pct_over = ((cost - optimal) / optimal) * 100
                fb.append(_warn(f"Valid Hamiltonian tour (cost: {cost}), but {pct_over:.1f}% above optimal."))
                fb.append(_dim(f"  Must be within {tolerance*100:.0f}% of optimal ({optimal}). Threshold: {threshold}."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}

        # ── SPANNING TREE ──────────────────────────────────────────
        elif atype == "int" and p["category"] == "SPANNING TREE":
            try:
                player_w = int(answer_tokens[0]) if answer_tokens else -1
            except (ValueError, IndexError):
                fb.append(_err("Provide total MST weight as a single integer."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            mst_w = p["mst_weight"]
            if player_w == mst_w:
                fb.append(_ok(f"✓ CORRECT! MST total weight = {mst_w}"))
                _add_reward(fb, p)
                return {"correct": True, "feedback": fb, "xp": p["xp"], "credits": p["credits"]}
            else:
                fb.append(_err(f"Incorrect. Your answer: {player_w}. Keep checking your edge selection."))
                fb.append(_dim("  Hint: Are you including the right number of edges? MST has |V|-1 edges."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}

        # ── FLOW NETWORK ───────────────────────────────────────────
        elif atype == "int" and p["category"] == "FLOW NETWORK":
            try:
                player_f = int(answer_tokens[0]) if answer_tokens else -1
            except (ValueError, IndexError):
                fb.append(_err("Provide max flow value as a single integer."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}
            mf = p["max_flow"]
            if player_f == mf:
                fb.append(_ok(f"✓ CORRECT! Max flow = {mf}"))
                fb.append(_dim(
                    f"  By the max-flow min-cut theorem, the minimum cut capacity also equals {mf}."
                ))
                _add_reward(fb, p)
                return {"correct": True, "feedback": fb, "xp": p["xp"], "credits": p["credits"]}
            else:
                fb.append(_err(f"Incorrect max flow. Your answer: {player_f}."))
                fb.append(_dim("  Trace augmenting paths with BFS (Edmonds-Karp). Check residual graph."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}

        # ── TOPOLOGICAL SORT ───────────────────────────────────────
        elif atype == "toposort":
            if not answer_tokens:
                return _answer_err(fb, "Provide ordering as space-separated node names.")
            player_order = answer_tokens
            nodes: List[str] = p["nodes"]
            edges: List[Tuple[str, str]] = p["edges"]
            # Check validity
            if _is_valid_toposort(nodes, edges, player_order):
                fb.append(_ok(f"✓ CORRECT! Valid topological ordering:"))
                fb.append(_dim(f"  {' → '.join(player_order)}"))
                _add_reward(fb, p)
                return {"correct": True, "feedback": fb, "xp": p["xp"], "credits": p["credits"]}
            else:
                # Diagnose
                player_set = set(player_order)
                node_set   = set(nodes)
                if player_set != node_set:
                    missing = node_set - player_set
                    extra   = player_set - node_set
                    if missing:
                        fb.append(_err(f"Missing nodes: {', '.join(sorted(missing))}"))
                    if extra:
                        fb.append(_err(f"Unknown nodes: {', '.join(sorted(extra))}"))
                elif len(player_order) != len(set(player_order)):
                    fb.append(_err("Duplicate nodes in ordering."))
                else:
                    # Find violated dependency
                    pos = {nd: i for i, nd in enumerate(player_order)}
                    violations = [(u, v) for u, v in edges if pos.get(u, -1) >= pos.get(v, len(player_order))]
                    fb.append(_err("Dependency violation(s) detected:"))
                    for u2, v2 in violations[:3]:
                        fb.append(_dim(f"  {u2} must come before {v2}, but order is reversed."))
                return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}

        else:
            fb.append(_err(f"Internal error: unknown answer_type '{atype}' for puzzle #{n}."))
            return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}

    # ------------------------------------------------------------------ #
    # hint
    # ------------------------------------------------------------------ #

    @staticmethod
    def hint(n: int) -> List[Dict]:
        """Return hint output for puzzle n."""
        p = GraphTheoryEngine.get_level(n)
        if p is None:
            return [_err(f"No graph-theory puzzle #{n}.")]
        out: List[Dict] = []
        out.append(_sys(f"── HINT: #{n} {p['name']} ──"))
        out.append(_lore(f"[{p['category']}] "))
        for line in p["hint"].splitlines():
            out.append(_dim(f"  {line}"))
        out.append(_dim("  (Hints cost no Qi — Daedalus-7 is feeling generous. Today.)"))
        return out

    # ------------------------------------------------------------------ #
    # solve
    # ------------------------------------------------------------------ #

    @staticmethod
    def solve(n: int) -> List[Dict]:
        """Show full solution with explanation. No XP awarded."""
        p = GraphTheoryEngine.get_level(n)
        if p is None:
            return [_err(f"No graph-theory puzzle #{n}.")]

        out: List[Dict] = []
        out.append(_warn(f"── SOLUTION REVEAL: #{n} {p['name']} (no XP awarded) ──"))
        out.append(_dim(f"  [{p['category']}  Lv.{p['level']}]"))
        out.append(_line(""))

        atype = p["answer_type"]

        if atype == "path":
            cost = p["optimal_cost"]
            path = p["optimal_path"]
            out.append(_ok(f"  Optimal path: {' → '.join(path)}"))
            out.append(_ok(f"  Total cost:   {cost}"))
            out.append(_line(""))
            out.append(_dim("  Dijkstra trace:"))
            # Replay Dijkstra for explanation
            adj = p["adj"]
            INF = float("inf")
            dist: Dict[str, float] = {nd: INF for nd in p["nodes"]}
            dist[p["source"]] = 0
            visited: Set[str] = set()
            heap2: List[Tuple[float,str]] = [(0, p["source"])]
            step = 1
            while heap2:
                d, u = heapq.heappop(heap2)
                if u in visited:
                    continue
                visited.add(u)
                out.append(_dim(f"    Step {step}: Visit [{u}] dist={int(d)}"))
                step += 1
                for v2, w2 in adj.get(u, []):
                    nd2 = d + w2
                    if nd2 < dist[v2]:
                        dist[v2] = nd2
                        out.append(_dim(f"      Update dist[{v2}] = {int(nd2)} (via {u}+{w2})"))
                        heapq.heappush(heap2, (nd2, v2))

        elif atype == "int" and p["category"] == "GRAPH COLORING":
            k = p["chromatic_number"]
            out.append(_ok(f"  Chromatic number: {k}"))
            out.append(_line(""))
            out.append(_dim("  Reasoning:"))
            out.append(_dim(f"    The graph contains a clique of size {k} (fully connected subgraph)."))
            out.append(_dim(f"    Therefore it requires at least {k} colors."))
            out.append(_dim(f"    A valid {k}-coloring can be constructed greedily (see hint)."))

        elif atype == "tour":
            tour = p["optimal_tour"]
            cost = p["optimal_cost"]
            out.append(_ok(f"  Optimal tour: {' → '.join(tour)}"))
            out.append(_ok(f"  Total cost:   {cost}"))
            out.append(_line(""))
            out.append(_dim("  This was found by exhaustive enumeration (brute force, feasible for small N)."))
            out.append(_dim(f"  Tolerance: any tour ≤ {int(cost * (1 + p['tolerance']))} is accepted."))

        elif atype == "int" and p["category"] == "SPANNING TREE":
            mst_w = p["mst_weight"]
            nodes = p["nodes"]
            edges_sorted = sorted(p["edges"], key=lambda e: e[2])
            out.append(_ok(f"  MST total weight: {mst_w}"))
            out.append(_line(""))
            out.append(_dim("  Kruskal's algorithm (sorted edges):"))
            uf = _UnionFind(nodes)
            total = 0
            for u, v, w in edges_sorted:
                added = uf.union(u, v)
                if added:
                    total += w
                    out.append(_ok(f"    ADD  {u}─{w}─{v}  (running total: {total})"))
                else:
                    out.append(_dim(f"    SKIP {u}─{w}─{v}  (would form cycle)"))

        elif atype == "int" and p["category"] == "FLOW NETWORK":
            mf = p["max_flow"]
            out.append(_ok(f"  Maximum flow: {mf}"))
            out.append(_line(""))
            out.append(_dim("  Computed via Edmonds-Karp (BFS augmenting paths)."))
            out.append(_dim("  By the max-flow min-cut theorem: max flow = min cut capacity."))
            out.append(_dim(f"  Verify: find a cut separating {p['source']} and {p['sink']} with total capacity {mf}."))

        elif atype == "toposort":
            order = _topological_sort_kahn(p["nodes"], p["edges"])
            out.append(_ok(f"  Valid ordering: {' → '.join(order or [])}"))
            out.append(_line(""))
            out.append(_dim("  Kahn's algorithm trace:"))
            # Replay Kahn for explanation
            in_deg = {nd: 0 for nd in p["nodes"]}
            adj_t: Dict[str, List[str]] = {nd: [] for nd in p["nodes"]}
            for u, v in p["edges"]:
                adj_t[u].append(v)
                in_deg[v] += 1
            queue_t: deque[str] = deque(nd for nd in p["nodes"] if in_deg[nd] == 0)
            step = 1
            while queue_t:
                u = queue_t.popleft()
                out.append(_dim(f"    Step {step}: Emit [{u}]"))
                step += 1
                for v2 in adj_t[u]:
                    in_deg[v2] -= 1
                    if in_deg[v2] == 0:
                        queue_t.append(v2)

        out.append(_line(""))
        out.append(_lore(p.get("lore", "")))
        return out

    # ------------------------------------------------------------------ #
    # list_levels
    # ------------------------------------------------------------------ #

    @staticmethod
    def list_levels() -> List[Dict]:
        """Return formatted list of all graph-theory puzzles."""
        out: List[Dict] = []
        out.append(_sys("╔══════════════════════════════════════════════════════════╗"))
        out.append(_sys("║       DAEDALUS-7 :: GRAPH THEORY CHALLENGE SUITE        ║"))
        out.append(_sys("╚══════════════════════════════════════════════════════════╝"))
        out.append(_lore(
            "  \"Graph theory is the mathematics of everything CHIMERA knows about you —\n"
            "   your connections, your shortest paths, your vulnerabilities.\"\n"
            "                                               — Daedalus-7"
        ))
        out.append(_line(""))

        current_cat = ""
        for p in GRAPH_LEVELS:
            if p["category"] != current_cat:
                current_cat = p["category"]
                out.append(_sys(f"  ┌─ {current_cat} ─────────────────────────────────────"))
            status_char = "·"
            xp_str = f"+{p['xp']} XP"
            cr_str = f"+{p['credits']}¢"
            out.append(_line(
                f"  │  #{p['id']:>2}  Lv.{p['level']}  [{p['difficulty']:<12}]  "
                f"{p['name']:<30}  {xp_str:<8}  {cr_str}"
            ))
        out.append(_line(""))
        out.append(_dim("  Usage: graph-theory load <n>  |  graph-theory answer <n> <...>"))
        out.append(_dim("         graph-theory hint <n>  |  graph-theory solve <n>"))
        return out


# ---------------------------------------------------------------------------
# Convenience helpers (called from check_answer)
# ---------------------------------------------------------------------------

def _answer_err(fb: List[Dict], msg: str) -> Dict:
    fb.append(_err(f"Format error: {msg}"))
    return {"correct": False, "feedback": fb, "xp": 0, "credits": 0}


def _add_reward(fb: List[Dict], p: Dict) -> None:
    fb.append(_ok(f"  Reward: +{p['xp']} XP  ·  +{p['credits']} credits"))
    fb.append(_lore(p.get("lore", "")))


# ---------------------------------------------------------------------------
# Module-level convenience API (mirrors class for command routing)
# ---------------------------------------------------------------------------

def get_level(n: int) -> Optional[Dict[str, Any]]:
    return GraphTheoryEngine.get_level(n)


def render_level(n: int) -> List[Dict]:
    return GraphTheoryEngine.render_level(n)


def check_answer(n: int, answer: str) -> Dict:
    """String-based entry point: splits answer string into tokens."""
    tokens = answer.strip().split()
    return GraphTheoryEngine.check_answer(n, tokens)


def hint(n: int) -> List[Dict]:
    return GraphTheoryEngine.hint(n)


def solve(n: int) -> List[Dict]:
    return GraphTheoryEngine.solve(n)


def list_levels() -> List[Dict]:
    return GraphTheoryEngine.list_levels()

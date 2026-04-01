"""
services/mod_audit/graph.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Dependency graph builder + topological sort for RimWorld mod load order.

Rules:
  - loadAfter  [A]   → A must appear BEFORE the current mod
  - loadBefore [B]   → B must appear AFTER the current mod
  - dependencies     → like loadAfter but hard-required

The topo sort uses Kahn's algorithm; detected cycles are reported
without crashing — we emit a partial order and flag the cycle members.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


# ── Graph construction ────────────────────────────────────────────────────────

def build_dep_graph(mods: list[dict[str, Any]]) -> dict[str, list[str]]:
    """
    Build an adjacency list: edge A → B means "A must load before B".
    Collected from loadAfter, loadBefore, and dependencies fields.
    Only edges where both endpoints exist in the mod list are retained.
    """
    known = {m["package_id"] for m in mods}
    adj: dict[str, list[str]] = {m["package_id"]: [] for m in mods}

    for mod in mods:
        pid = mod["package_id"]

        # loadAfter X  ⟹  X → pid
        for dep in mod.get("load_after", []) + mod.get("dependencies", []):
            if dep in known and dep != pid:
                adj.setdefault(dep, [])
                if pid not in adj[dep]:
                    adj[dep].append(pid)

        # loadBefore X  ⟹  pid → X
        for succ in mod.get("load_before", []):
            if succ in known and succ != pid:
                if succ not in adj[pid]:
                    adj[pid].append(succ)

    return adj


# ── Topological sort ──────────────────────────────────────────────────────────

def topo_sort(adj: dict[str, list[str]],
              mods: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Kahn's algorithm topological sort.

    Returns:
      {
        "order":        [pkg_id, ...],      # correct load order
        "violations":   [{before, after}],  # pairs that are currently wrong
        "cycles":       [[pkg_id, ...]],    # detected dependency cycles
        "has_changes":  bool,               # True if order differs from input
      }
    """
    all_ids = [m["package_id"] for m in mods]
    nodes = set(all_ids)

    # Build in-degree map
    in_degree: dict[str, int] = {n: 0 for n in nodes}
    for src, targets in adj.items():
        for tgt in targets:
            if tgt in in_degree:
                in_degree[tgt] += 1

    queue: deque[str] = deque(
        n for n in all_ids if in_degree.get(n, 0) == 0
    )
    order: list[str] = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbour in adj.get(node, []):
            if neighbour not in in_degree:
                continue
            in_degree[neighbour] -= 1
            if in_degree[neighbour] == 0:
                queue.append(neighbour)

    # Nodes remaining with in_degree > 0 are in a cycle
    cycle_nodes = [n for n in nodes if in_degree.get(n, 0) > 0]
    cycles: list[list[str]] = []
    if cycle_nodes:
        cycles = [_trace_cycle(adj, cycle_nodes)]
        # Append them at the end in original order so we emit a complete list
        for n in all_ids:
            if n not in order:
                order.append(n)

    # Detect violations: pairs where A must precede B but B comes first
    pos_map = {pid: i for i, pid in enumerate(order)}
    violations = []
    for src, targets in adj.items():
        for tgt in targets:
            if tgt in pos_map and src in pos_map:
                if pos_map[src] > pos_map[tgt]:
                    violations.append({"before": src, "after": tgt})

    return {
        "order":       order,
        "violations":  violations,
        "cycles":      cycles,
        "has_changes": order != all_ids,
    }


def _trace_cycle(adj: dict[str, list[str]], candidates: list[str]) -> list[str]:
    """DFS to trace one cycle among the candidate nodes."""
    cand_set = set(candidates)
    visited: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> bool:
        if node in path:
            idx = path.index(node)
            path[:] = path[idx:]
            return True
        if node in visited:
            return False
        visited.add(node)
        path.append(node)
        for nb in adj.get(node, []):
            if nb in cand_set and dfs(nb):
                return True
        path.pop()
        return False

    for start in candidates:
        if dfs(start):
            break

    return path or candidates[:5]


# ── Current-order violation checker ─────────────────────────────────────────

def check_load_order_violations(
    mods: list[dict[str, Any]],
    adj: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """
    Given the *current* mod order (index = load position) and the dep graph,
    return a list of ordering violations the user currently has.
    """
    pos = {m["package_id"]: m["load_position"] for m in mods}
    violations = []

    for src, targets in adj.items():
        for tgt in targets:
            if src in pos and tgt in pos:
                if pos[src] > pos[tgt]:
                    violations.append({
                        "rule":   "load_after",
                        "before": src,
                        "after":  tgt,
                        "current_before_pos": pos[src],
                        "current_after_pos":  pos[tgt],
                        "message": (
                            f"'{src}' must load BEFORE '{tgt}', "
                            f"but is currently at position {pos[src]} "
                            f"(after {tgt} at {pos[tgt]})"
                        ),
                    })

    return violations

"""
services/mod_audit/recommendation_engine.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Top-level entry point for the mod audit pipeline.

  result = analyze(mod_ids, about_xmls)

Returns a ModAuditReport dict ready to serialise directly as the API response.
"""
from __future__ import annotations

import time
from typing import Any

from .scanner import build_mod_list, detect_duplicates
from .graph import build_dep_graph, topo_sort, check_load_order_violations
from .conflict_rules import check_conflicts, detect_ai_surface_mods


def analyze(
    mod_ids:    list[str],
    about_xmls: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Run the full mod audit pipeline.

    Parameters
    ----------
    mod_ids:    Ordered list of packageIds as they appear in ModsConfig.xml.
    about_xmls: Mapping packageId → raw About.xml text (optional but recommended).

    Returns
    -------
    A ModAuditReport dict with keys:
      timestamp, mod_count, duplicates, conflicts, load_order, ai_surfaces, summary
    """
    t0 = time.time()

    # 1. Parse + normalise
    mods     = build_mod_list(mod_ids, about_xmls)
    dupes    = detect_duplicates(mod_ids)

    # 2. Conflict detection
    conflicts = check_conflicts(mods)

    # 3. Dependency graph + topological sort
    adj       = build_dep_graph(mods)
    topo      = topo_sort(adj, mods)
    violations = check_load_order_violations(mods, adj)

    # 4. AI/LLM surface detection
    ai_surfaces = detect_ai_surface_mods(mods)

    # 5. Health score (0–100)
    n_critical = sum(1 for c in conflicts if c["severity"] == "critical")
    n_warning  = sum(1 for c in conflicts if c["severity"] == "warning")
    n_dupes    = len(dupes)
    n_viol     = len(violations)
    health     = max(0, 100 - (n_critical * 20) - (n_warning * 5)
                         - (n_dupes * 3) - (n_viol * 2))

    # 6. Human-readable summary
    summary_lines: list[str] = [
        f"{len(mod_ids)} mods loaded | health={health}%",
    ]
    if n_critical:
        summary_lines.append(f"⛔ {n_critical} critical conflict(s) — fix before loading saves")
    if n_warning:
        summary_lines.append(f"⚠ {n_warning} warning(s)")
    if n_dupes:
        summary_lines.append(f"⚠ {n_dupes} duplicate packageId(s)")
    if n_viol:
        summary_lines.append(f"⚠ {n_viol} load-order violation(s)")
    if topo["has_changes"]:
        summary_lines.append("ℹ Optimal load order differs from current order")
    if not (n_critical or n_warning or n_dupes or n_viol):
        summary_lines.append("✓ No issues detected")
    if ai_surfaces:
        summary_lines.append(
            f"🤖 {len(ai_surfaces)} AI/LLM surface mod(s) detected — "
            "TerminalKeeper integration opportunities available"
        )

    elapsed = round((time.time() - t0) * 1000)

    return {
        "timestamp":      time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_ms":     elapsed,
        "mod_count":      len(mod_ids),
        "health_score":   health,
        "summary":        "\n".join(summary_lines),
        "duplicates":     dupes,
        "conflicts":      conflicts,
        "load_order": {
            "current":     mod_ids,
            "optimal":     topo["order"],
            "violations":  violations,
            "cycles":      topo["cycles"],
            "has_changes": topo["has_changes"],
        },
        "ai_surfaces":   ai_surfaces,
    }

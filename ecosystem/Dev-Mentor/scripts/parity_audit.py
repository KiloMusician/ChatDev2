#!/usr/bin/env python3
"""parity_audit.py — NuSyQ-Hub dual-interface parity gap detector.
Reads state/parity_matrix.json and reports gaps between terminal and graphical UIs.
The terminal must always be a complete, authoritative play surface.
The graphical UI must always be a richer projection, not a different truth.

Run: python3 scripts/parity_audit.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
MATRIX = ROOT / "state/parity_matrix.json"

STATUS_ICON = {"done": "✓", "partial": "◐", "planned": "○", "gap": "✗"}
STATUS_COLOR = {
    "done": "\033[92m",
    "partial": "\033[93m",
    "planned": "\033[94m",
    "gap": "\033[91m",
    "": "\033[0m",
}
RESET = "\033[0m"


def color(s, status):
    return f"{STATUS_COLOR.get(status,'')}{s}{RESET}"


def main():
    if not MATRIX.exists():
        print("parity_matrix.json not found. Run: python3 scripts/size_audit.py first.")
        sys.exit(1)

    data = json.loads(MATRIX.read_text())
    features = data["features"]
    meta = data.get("_meta", {})

    print(f"\n{'═'*70}")
    print("  NuSyQ-Hub — DUAL INTERFACE PARITY AUDIT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Law: {meta.get('compression_law','')[:60]}")
    print(f"{'═'*70}\n")

    # Tally
    t_done = sum(1 for f in features if f["terminal_status"] == "done")
    g_done = sum(1 for f in features if f["graphical_status"] == "done")
    gaps = [f for f in features if f["graphical_status"] == "gap"]
    planned = [f for f in features if f["graphical_status"] in ("planned",)]
    partials = [
        f
        for f in features
        if f["terminal_status"] == "partial" or f["graphical_status"] == "partial"
    ]

    print(f"  Total features:      {len(features)}")
    print(
        f"  Terminal done:       {t_done}/{len(features)} ({t_done*100//len(features)}%)"
    )
    print(
        f"  Graphical done:      {g_done}/{len(features)} ({g_done*100//len(features)}%)"
    )
    print(f"  Graphical gaps:      {len(gaps)}")
    print(f"  Partially complete:  {len(partials)}")

    print(f"\n  {'Feature':<26} {'Terminal':^10} {'Graphical':^12} {'Unlock'}")
    print("  " + "─" * 65)

    for f in features:
        ts = STATUS_ICON.get(f["terminal_status"], "?")
        gs = STATUS_ICON.get(f["graphical_status"], "?")
        ts_c = color(f"{ts} {f['terminal_status']:<6}", f["terminal_status"])
        gs_c = color(f"{gs} {f['graphical_status']:<8}", f["graphical_status"])
        unlock = f["unlock_condition"][:25]
        print(f"  {f['label']:<26} {ts_c}  {gs_c}  {unlock}")

    if gaps:
        print(f"\n  {'─'*65}")
        print("  GRAPHICAL GAPS (no panel yet):")
        for f in gaps:
            print(f"    ✗ {f['label']:<24}  planned form: {f['graphical_form'][:45]}")

    if planned:
        print("\n  GRAPHICAL PLANNED (implementation queued):")
        for f in planned:
            print(f"    ○ {f['label']:<24}  {f['graphical_form'][:45]}")

    # Feature pipeline gate check
    print("\n  FEATURE PIPELINE GATE CHECK:")
    print(f"  {'─'*65}")
    gate_fails = []
    for f in features:
        issues = []
        if not f.get("backend_model"):
            issues.append("Gate 2: no backend model")
        if not f.get("terminal_form"):
            issues.append("Gate 3a: no terminal form")
        if not f.get("graphical_form"):
            issues.append("Gate 3b: no graphical form")
        if not f.get("compression_note"):
            issues.append("Gate 4: no compression note")
        if issues:
            gate_fails.append((f["label"], issues))

    if gate_fails:
        for label, issues in gate_fails:
            print(f"  ⚠ {label}: {', '.join(issues)}")
    else:
        print(f"  ✓ All {len(features)} features pass all pipeline gates")

    # Compression score
    procedural = sum(
        1
        for f in features
        if "procedural" in f.get("compression_note", "").lower()
        or "zero asset" in f.get("compression_note", "").lower()
        or "text-native" in f.get("compression_note", "").lower()
    )
    print(
        f"\n  COMPRESSION SCORE: {procedural}/{len(features)} features are procedural-first ({procedural*100//len(features)}%)"
    )

    # Budget status
    budgets = data.get("domain_budgets_mb", {})
    print("\n  DOMAIN BUDGETS:")
    for domain, limits in budgets.items():
        if isinstance(limits, dict):
            print(
                f"  {domain:<20} target={limits['target']} MB  ceiling={limits['ceiling']} MB"
            )

    # Write report
    report = {
        "timestamp": datetime.now().isoformat(),
        "terminal_pct": t_done * 100 // len(features),
        "graphical_pct": g_done * 100 // len(features),
        "gaps": len(gaps),
        "procedural_pct": procedural * 100 // len(features),
    }
    (ROOT / "state" / "parity_report.json").write_text(json.dumps(report, indent=2))
    print("\n  Report saved: state/parity_report.json")
    print(f"{'═'*70}\n")


if __name__ == "__main__":
    main()

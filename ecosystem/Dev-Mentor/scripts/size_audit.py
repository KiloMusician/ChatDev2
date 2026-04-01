#!/usr/bin/env python3
"""size_audit.py — Repo density health monitor.
Nudges the project toward osmium-level compression without imposing law.
Run: python3 scripts/size_audit.py
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

SOFT_LIMIT_MB = 1_000  # 1 GB — comfortable GitHub zone
WARN_LIMIT_MB = 3_000  # 3 GB — start nudging
HARD_LIMIT_MB = 5_000  # 5 GB — GitHub gets upset

BUDGET = {
    "app": {"soft": 300, "hard": 750, "note": "code + VFS; prefer procedural"},
    "scripts": {"soft": 50, "hard": 150, "note": "tooling; keep lean"},
    "bootstrap": {
        "soft": 5,
        "hard": 20,
        "note": "one-file wonders; exempt from pressure",
    },
    ".devmentor": {"soft": 10, "hard": 50, "note": "state + config"},
    "state": {"soft": 20, "hard": 100, "note": "game state; auto-rotated"},
    "docs": {"soft": 50, "hard": 200, "note": "text only; no binary docs"},
    "sessions": {"soft": 100, "hard": 500, "note": "player sessions; auto-pruned"},
}

STELLAR_STAGES = [
    (0, 10, "🌫  Nebula", "formless — good starting point"),
    (10, 100, "☀  Hydrogen", "main sequence — building blocks"),
    (100, 500, "⚡  Helium", "fusing complexity — healthy growth"),
    (500, 1500, "💎  Carbon", "rich structure — monitor carefully"),
    (1500, 3000, "⚙  Iron Core", "peak efficiency — no more fusion gains"),
    (3000, 5000, "🌀  Neutron", "degenerate matter — extreme density warning"),
    (5000, None, "⚫  Black Hole", "GitHub event horizon — push refused"),
]


def get_dir_size_mb(path: Path) -> float:
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / (1024 * 1024)


def get_git_size_mb() -> float:
    try:
        r = subprocess.run(
            ["git", "count-objects", "-vH"], capture_output=True, text=True, cwd=ROOT
        )
        for line in r.stdout.splitlines():
            if line.startswith("size-pack"):
                val = line.split()[-1]
                mult = {"KiB": 1 / 1024, "MiB": 1, "GiB": 1024}.get(val[-3:], 0)
                return float(val[:-3]) * mult if mult else 0
    except Exception:
        pass
    return 0


def stellar_stage(mb: float):
    for lo, hi, name, desc in STELLAR_STAGES:
        if hi is None or mb < hi:
            return name, desc
    return STELLAR_STAGES[-1][2], STELLAR_STAGES[-1][3]


def density_score(mb: float) -> str:
    pct = min(100, (mb / SOFT_LIMIT_MB) * 100)
    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
    return f"[{bar}] {pct:.1f}% of soft limit ({SOFT_LIMIT_MB} MB)"


def main():
    print("\n" + "═" * 64)
    print("  TERMINAL DEPTHS — DENSITY AUDIT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print("═" * 64 + "\n")

    total_mb = get_dir_size_mb(ROOT)
    git_mb = get_git_size_mb()
    stage, stage_desc = stellar_stage(total_mb)

    print(f"  Working tree:  {total_mb:>8.1f} MB")
    print(f"  Git objects:   {git_mb:>8.1f} MB  (history)")
    print(f"  Total est:     {total_mb + git_mb:>8.1f} MB")
    print(f"\n  {density_score(total_mb + git_mb)}")
    print(f"\n  Stellar stage: {stage}")
    print(f"  {stage_desc}\n")

    # Per-directory audit
    print("  DIRECTORY BUDGETS:")
    print(f"  {'Directory':<20} {'Size MB':>8}  {'Budget':>8}  Status")
    print("  " + "─" * 55)
    warnings = []
    for dir_name, limits in BUDGET.items():
        d = ROOT / dir_name
        if not d.exists():
            continue
        mb = get_dir_size_mb(d)
        soft, hard = limits["soft"], limits["hard"]
        if mb > hard:
            status = "⚫ OVER HARD LIMIT"
            warnings.append(
                f"  {dir_name}: {mb:.1f} MB exceeds hard limit {hard} MB — {limits['note']}"
            )
        elif mb > soft:
            status = "🌀 approaching limit"
            warnings.append(
                f"  {dir_name}: {mb:.1f} MB > soft limit {soft} MB — nudge: {limits['note']}"
            )
        else:
            pct = mb / soft * 100
            status = f"✓ {pct:.0f}% of soft limit"
        print(f"  {dir_name:<20} {mb:>8.1f}  {soft:>6} MB  {status}")

    # Largest files
    print("\n  LARGEST FILES (top 10):")
    files = sorted(
        ROOT.rglob("*"),
        key=lambda f: f.stat().st_size if f.is_file() else 0,
        reverse=True,
    )
    files = [f for f in files if f.is_file() and ".git" not in str(f)][:10]
    for f in files:
        mb = f.stat().st_size / (1024 * 1024)
        rel = f.relative_to(ROOT)
        note = ""
        if mb > 10:
            note = "  ← consider: compress / procedural / LFS"
        elif f.suffix in (".log", ".jsonl") and mb > 5:
            note = "  ← consider: rotate / prune"
        print(f"  {mb:>8.2f} MB  {rel}{note}")

    # Recommendations
    print("\n  DENSITY RECOMMENDATIONS:")
    if total_mb < 100:
        print("  ✦ IRIDIUM DENSITY — continue building freely")
    elif total_mb < 500:
        print("  ✦ OSMIUM DENSITY — healthy; prefer procedural content over files")
    elif total_mb < 1000:
        print("  ✦ CARBON STAGE — good; audit any binary assets added this sprint")
    elif total_mb < 3000:
        print("  ⚡ IRON CORE — meaningful size; run: git gc --aggressive")
        print("     Consider: .gitignore *.log, rotate sessions/, compress VFS text")
    else:
        print("  🌀 NEUTRON WARNING — approaching GitHub soft limit")
        print("     Actions: git-sizer, BFG repo cleaner, or split repository")

    if warnings:
        print("\n  NUDGES:")
        for w in warnings:
            print(w)

    # Write audit to state
    audit = {
        "timestamp": datetime.now().isoformat(),
        "working_mb": round(total_mb, 2),
        "git_mb": round(git_mb, 2),
        "stage": stage,
    }
    (ROOT / "state").mkdir(exist_ok=True)
    (ROOT / "state" / "size_audit.json").write_text(json.dumps(audit, indent=2))
    print("\n  Audit saved: state/size_audit.json")
    print("═" * 64 + "\n")


if __name__ == "__main__":
    main()

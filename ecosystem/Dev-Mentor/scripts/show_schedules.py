#!/usr/bin/env python3
"""show_schedules.py — Print Grey Hack-style agent schedule summary."""
from pathlib import Path

import yaml

data = yaml.safe_load(
    (Path(__file__).parent.parent / "agents" / "schedules.yaml").read_text()
)
agents = data.get("agents", {})

print("")
print("  ── COLONY AGENT SCHEDULES ──")
print(f"  {'Agent':<22} {'Active':<13} {'Faction':<22} {'₵/cycle'}")
print(f"  {'─'*22} {'─'*13} {'─'*22} {'─'*7}")
for aid, a in agents.items():
    active = len(a.get("active_hours", []))
    rest = "always on" if not a.get("rest_hours") else f"{active}h/day"
    faction = a.get("faction", "—")
    cpc = a.get("credits_per_cycle", "?")
    print(f"  {aid:<22} {rest:<13} {faction:<22} +{cpc}")
print("")

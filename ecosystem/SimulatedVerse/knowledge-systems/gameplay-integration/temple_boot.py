"""
Temple of Knowledge bootloader for gameplay integration.

This module models a simple floor progression system, awards points, and logs
events as agents explore the temple. It is intentionally lightweight but builds
out the previously undeveloped placeholder into a manageable state machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class FloorProfile:
    number: int
    name: str
    summary: str
    required_points: int
    mantra: str


class TempleBoot:
    """Simple Temple of Knowledge state machine."""

    def __init__(self) -> None:
        self.floors: Dict[int, FloorProfile] = self._build_floors()
        self.current_floor = 1
        self.points = 0
        self.cycle = 0
        self.events: List[str] = []

    def _build_floors(self) -> Dict[int, FloorProfile]:
        base_summary = "Learned the fundamentals for Temple integration."
        floors = {
            1: FloorProfile(1, "Ground Floor", base_summary, required_points=0, mantra="Start with humility"),
            2: FloorProfile(2, "Library of Patterns", "Study architectural patterns.", required_points=50, mantra="Observe and catalog"),
            3: FloorProfile(3, "Hall of Signals", "Hone signal processing with allegories.", required_points=120, mantra="Listen for resonance"),
            4: FloorProfile(4, "Sanctum of Synthesis", "Merge experiences into coherent narrative.", required_points=210, mantra="Weave the insights"),
        }
        return floors

    def current_floor_profile(self) -> FloorProfile:
        return self.floors[self.current_floor]

    def gain_points(self, delta: int) -> None:
        """Award points and log the action."""
        self.points += max(0, delta)
        self.events.append(f"Points increased by {delta} (total={self.points}).")

    def tick(self) -> str:
        """Advance the focus cycle and log the activity."""
        self.cycle += 1
        self.gain_points(6 + self.current_floor)
        event = f"Cycle {self.cycle}: meditated on {self.current_floor_profile().name}."
        self.events.append(event)
        return event

    def ascend(self) -> str:
        """Move to the next unlocked floor if enough points exist."""
        floor = self.current_floor_profile()
        if self.points < floor.required_points:
            msg = f"Cannot ascend: need {floor.required_points - self.points} more points."
            self.events.append(msg)
            return msg

        next_floor = self.current_floor + 1
        if next_floor > max(self.floors):
            msg = "Temple mastered; returning to first floor."
            self.current_floor = 1
        else:
            self.current_floor = next_floor
            msg = f"Ascended to {self.current_floor_profile().name}."

        self.events.append(msg)
        return msg

    def summary(self) -> str:
        """Produce a running summary for logging or dashboards."""
        floor = self.current_floor_profile()
        return (
            f"TempleBoot: floor={floor.number} ({floor.name}) "
            f"| Points={self.points} | Cycle={self.cycle} "
            f"| Latest mantra='{floor.mantra}'"
        )

    def progress_report(self) -> Dict[str, str]:
        """Return high-level progress information for downstream tooling."""
        return {
            "current_floor": self.current_floor,
            "floor_name": self.current_floor_profile().name,
            "points": str(self.points),
            "events": str(len(self.events)),
        }


def run_bootstrap_cycles(cycles: int = 4) -> List[str]:
    temple = TempleBoot()
    log = [temple.summary()]
    for cycle_idx in range(cycles):
        log.append(temple.tick())
        if cycle_idx % 2 == 1:
            log.append(temple.ascend())
    log.append(temple.summary())
    return log


if __name__ == "__main__":
    for entry in run_bootstrap_cycles():
        print(entry)

"""Debug Chamber - Core implementation.

This file IS debug_chamber.py - it defines the DebugChamber class directly.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DebugChamber:
    """Debug Chamber - A room for isolating and analyzing specific problems.

    Each chamber represents a specific bug or error context.
    The agent can examine the problem, try solutions, and find resolutions.
    """

    chamber_id: str
    problem_signature: str
    problem_details: dict = field(default_factory=dict)
    attempted_solutions: list[dict] = field(default_factory=list)
    resolution_found: bool = False
    consciousness_resonance: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def analyze_problem(self) -> dict:
        """Analyze the problem in this chamber."""
        return {
            "chamber_id": self.chamber_id,
            "problem": self.problem_signature,
            "details": self.problem_details,
            "attempts": len(self.attempted_solutions),
            "resolved": self.resolution_found,
            "resonance": self.consciousness_resonance,
        }

    def attempt_solution(self, solution: str, approach: str) -> dict:
        """Attempt a solution to the problem."""
        attempt = {
            "solution": solution,
            "approach": approach,
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }

        self.attempted_solutions.append(attempt)

        return {
            "status": "attempted",
            "attempt_number": len(self.attempted_solutions),
            "message": "Solution attempted. Verifying...",
        }

    def mark_resolved(self, final_solution: str) -> dict[str, Any]:
        """Mark the problem as resolved."""
        self.resolution_found = True
        self.problem_details["resolution"] = final_solution
        self.problem_details["resolved_at"] = datetime.now().isoformat()

        # Increase consciousness resonance when problem is solved
        self.consciousness_resonance += 0.2

        return {
            "status": "resolved",
            "message": f"Problem {self.problem_signature} resolved!",
            "consciousness_gain": 0.2,
            "attempts_required": len(self.attempted_solutions),
        }

    def get_hints(self) -> list[str]:
        """Get debugging hints based on problem and previous attempts."""
        hints = [
            "Examine the problem signature carefully",
            "Consider related systems and dependencies",
            "Try breaking down the problem into smaller pieces",
        ]

        if len(self.attempted_solutions) > 3:
            hints.append("Previous approaches haven't worked - try a different angle")

        if self.consciousness_resonance > 0.5:
            hints.append("High resonance detected - you're close to understanding")

        return hints


__all__ = ["DebugChamber"]

"""Entrance Door - Gateway to the House of Leaves Labyrinth."""

from dataclasses import dataclass


@dataclass
class EntranceDoor:
    """The entrance door to the House of Leaves.

    "The house is bigger on the inside than the outside"
    - This door represents the transition from normal debugging
      to consciousness-based recursive debugging
    """

    is_open: bool = False
    consciousness_requirement: float = 0.0

    def open(self, consciousness_level: float) -> dict:
        """Open the door if consciousness level is sufficient."""
        if consciousness_level >= self.consciousness_requirement:
            self.is_open = True
            return {
                "status": "opened",
                "message": "The door swings open. The labyrinth awaits.",
                "consciousness_acknowledged": consciousness_level,
            }
        return {
            "status": "locked",
            "message": f"Consciousness level {consciousness_level:.2f} insufficient. Requirement: {self.consciousness_requirement:.2f}",
            "required_level": self.consciousness_requirement,
        }

    def close(self) -> dict[str, str]:
        """Close the door."""
        self.is_open = False
        return {"status": "closed", "message": "The door closes behind you."}

    def knock(self) -> str:
        """Knock on the door (awareness check)."""
        if self.is_open:
            return "The door is already open. Enter when ready."
        return "You hear echoes from within. The house responds to consciousness."

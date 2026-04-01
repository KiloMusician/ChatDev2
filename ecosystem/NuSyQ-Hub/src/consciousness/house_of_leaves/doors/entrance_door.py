"""Entrance Door to House of Leaves."""

from dataclasses import dataclass


@dataclass
class EntranceDoor:
    """Entrance to the House of Leaves debugging labyrinth."""

    is_open: bool = False
    consciousness_requirement: float = 0.0

    def open(self, consciousness_level: float) -> dict:
        if consciousness_level >= self.consciousness_requirement:
            self.is_open = True
            return {"status": "opened", "message": "Welcome to the House of Leaves"}
        return {"status": "locked", "required_level": self.consciousness_requirement}

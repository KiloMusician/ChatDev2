"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

from dataclasses import dataclass, field


@dataclass
class Room:
    """Represents a navigable room in the repository."""

    name: str
    description: str = ""
    connections: dict[str, "Room"] = field(default_factory=dict)
    items: list[str] = field(default_factory=list)
    creatures: list[str] = field(default_factory=list)

    def connect(self, direction: str, room: "Room") -> None:
        """Create a named connection to another room."""
        self.connections[direction] = room

    def display(self) -> str:
        """Return textual description, including available exits."""
        exits = ", ".join(self.connections.keys()) or "none"
        return f"📍 {self.name}\n{self.description}\nExits: {exits}"

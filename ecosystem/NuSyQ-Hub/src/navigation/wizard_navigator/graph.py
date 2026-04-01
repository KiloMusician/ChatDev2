"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

from pathlib import Path

from .room import Room


class Navigator:
    """Builds and traverses a room graph based on filesystem structure."""

    def __init__(self, start_path: Path) -> None:
        """Initialize Navigator with start_path."""
        self.rooms: dict[str, Room] = {}
        # Build room graph recursively
        self._build_rooms(start_path, None)
        # Initialize current room to start path
        self.current_room: Room = self.rooms[str(start_path)]

    def _build_rooms(self, path: Path, parent: Room | None) -> None:
        room = Room(name=path.name or str(path), description=str(path))
        self.rooms[str(path)] = room
        if parent:
            parent.connect(path.name, room)
            room.connect("back", parent)
        # Only traverse directories, limit depth if needed
        for child in path.iterdir():
            if child.is_dir():
                self._build_rooms(child, room)

    def move(self, direction: str) -> str:
        target = self.current_room.connections.get(direction)
        if not target:
            return f"❌ No exit '{direction}' from {self.current_room.name}."
        self.current_room = target
        return self.current_room.display()

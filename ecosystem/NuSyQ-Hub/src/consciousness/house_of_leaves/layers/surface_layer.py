"""Surface Layer - Entry level of the debugging labyrinth."""

from dataclasses import dataclass


@dataclass
class SurfaceLayer:
    """Surface Layer - The shallowest layer of the House of Leaves."""

    layer_id: int = 0
    name: str = "Surface"
    depth_threshold: float = 0.0
    accessible: bool = True

    def describe(self) -> str:
        return f"Layer {self.layer_id}: {self.name} - Entry level debugging"

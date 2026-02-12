"""Lightweight entity definitions for pvz_THUNLPDemo_2024 placeholder modules."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

class PlantType(Enum):
    PEASHOOTER = "peashooter"
    SUNFLOWER = "sunflower"
    CHOMPER = "chomper"

class ZombieType(Enum):
    NORMAL = "normal"
    NEWSPAPER = "newspaper"
    DANCING = "dancing"

@dataclass
class Plant:
    id: int
    type: PlantType
    health: int
    position: Tuple[int, int]

    def is_healthy(self) -> bool:
        return self.health > 0

    def take_damage(self, amount: int) -> None:
        self.health = max(0, self.health - amount)

@dataclass
class Zombie:
    id: int
    type: ZombieType
    health: int
    position: Tuple[int, int]

    def is_alive(self) -> bool:
        return self.health > 0

    def heal(self, amount: int) -> None:
        self.health += amount

@dataclass
class Projectile:
    origin: Tuple[int, int]
    destination: Tuple[int, int]
    damage: int = 20
    speed: float = 5.0

    def travel(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        return self.origin, self.destination

__all__ = ["PlantType", "ZombieType", "Plant", "Zombie", "Projectile"]

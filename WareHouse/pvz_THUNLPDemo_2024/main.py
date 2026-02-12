"""Simplified entry point for the pvz_THUNLPDemo_2024 placeholder demo."""

from dataclasses import dataclass
from enum import Enum
from typing import List

from entities import Plant, PlantType, Projectile, Zombie, ZombieType

class GameState(Enum):
    MENU = "menu"
    RUNNING = "running"
    COMPLETE = "complete"

@dataclass
class GameStats:
    waves_completed: int = 0
    suns_collected: int = 0
    actions_taken: int = 0

class Game:
    def __init__(self):
        self.state = GameState.MENU
        self.stats = GameStats()
        self.plants: List[Plant] = [
            Plant(id=1, type=PlantType.SUNFLOWER, health=100, position=(0, 0))
        ]
        self.zombies: List[Zombie] = []

    def start(self) -> None:
        self.state = GameState.RUNNING
        self.stats.actions_taken += 1
        print("Placeholder: Game started")

    def cycle(self) -> None:
        self.stats.waves_completed += 1
        self.stats.suns_collected += 5
        self.stats.actions_taken += 1
        self.zombies.append(
            Zombie(id=self.stats.waves_completed, type=ZombieType.NORMAL, health=80, position=(1, 0))
        )
        self.state = GameState.COMPLETE

    def report(self) -> str:
        return (
            f"State: {self.state.value}, "
            f"Waves: {self.stats.waves_completed}, "
            f"Suns: {self.stats.suns_collected}, "
            f"Actions: {self.stats.actions_taken}"
        )


def run_demo() -> Game:
    game = Game()
    game.start()
    game.cycle()
    print("Placeholder demo completed the cycle:", game.report())
    return game


if __name__ == "__main__":
    run_demo()

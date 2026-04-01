"""Simple turn-based combat system for prototyping."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Character:
    name: str
    max_hp: int = 100
    attack: int = 10
    defense: int = 5
    hp: int = 100
    guard: int = 0

    def __post_init__(self) -> None:
        """Implement __post_init__."""
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        mitigated = max(0, amount - self.guard)
        self.guard = 0
        self.hp = max(0, self.hp - mitigated)
        return mitigated


class Action(ABC):
    """Base combat action — subclass and implement execute()."""

    @abstractmethod
    def execute(self, actor: Character, target: Character) -> str:
        """Execute this action against a target. Returns a description string."""


@dataclass
class AttackAction(Action):
    bonus_damage: int = 0

    def execute(self, actor: Character, target: Character) -> str:
        raw = max(0, actor.attack + self.bonus_damage)
        dealt = target.take_damage(raw)
        return f"{actor.name} attacks {target.name} for {dealt} damage."


class DefendAction(Action):
    def execute(self, actor: Character, _target: Character) -> str:
        actor.guard = actor.defense
        return f"{actor.name} braces for impact."


@dataclass
class SkillAction(Action):
    multiplier: float = 1.5
    critical_chance: float = 0.1

    def execute(self, actor: Character, target: Character) -> str:
        base = actor.attack * self.multiplier
        crit = random.random() < self.critical_chance
        damage = int(base * (2 if crit else 1))
        dealt = target.take_damage(damage)
        tag = " (critical)" if crit else ""
        return f"{actor.name} uses a skill on {target.name} for {dealt} damage{tag}."


@dataclass
class CombatSystem:
    participants: list[Character] = field(default_factory=list)
    turn_index: int = 0

    def add_participant(self, character: Character) -> None:
        self.participants.append(character)

    def next_actor(self) -> Character:
        if not self.participants:
            raise ValueError("No participants available")
        actor = self.participants[self.turn_index % len(self.participants)]
        self.turn_index += 1
        return actor

    def resolve_turn(self, actor: Character, target: Character, action: Action) -> str:
        if not actor.is_alive() or not target.is_alive():
            return "Combatant is already down."
        return action.execute(actor, target)

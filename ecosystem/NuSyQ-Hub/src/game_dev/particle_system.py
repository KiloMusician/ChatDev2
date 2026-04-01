"""Lightweight particle system for prototyping effects."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class Particle:
    position: list[float]
    velocity: list[float]
    lifespan: float
    start_color: tuple[int, int, int] = (255, 255, 255)
    end_color: tuple[int, int, int] = (0, 0, 0)
    age: float = 0.0

    def update(self, dt: float) -> None:
        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt
        self.age += dt

    @property
    def alive(self) -> bool:
        return self.age < self.lifespan


@dataclass
class ParticleEmitter:
    position: tuple[float, float] = (0.0, 0.0)
    emission_rate: int = 5
    speed: float = 1.0
    spread_radians: float = math.pi / 4
    lifespan_range: tuple[float, float] = (0.5, 1.5)
    start_color: tuple[int, int, int] = (255, 255, 255)
    end_color: tuple[int, int, int] = (0, 0, 0)
    particles: list[Particle] = field(default_factory=list)

    def emit(self, count: int | None = None) -> list[Particle]:
        created: list[Particle] = []
        emit_count = count if count is not None else self.emission_rate
        for _ in range(emit_count):
            angle = random.uniform(-self.spread_radians, self.spread_radians)
            vx = math.cos(angle) * self.speed
            vy = math.sin(angle) * self.speed
            lifespan = random.uniform(*self.lifespan_range)
            particle = Particle(
                position=[self.position[0], self.position[1]],
                velocity=[vx, vy],
                lifespan=lifespan,
                start_color=self.start_color,
                end_color=self.end_color,
            )
            self.particles.append(particle)
            created.append(particle)
        return created

    def update(self, dt: float) -> None:
        expired: list[Particle] = []
        for particle in self.particles:
            particle.update(dt)
            if not particle.alive:
                expired.append(particle)
        for particle in expired:
            self.particles.remove(particle)

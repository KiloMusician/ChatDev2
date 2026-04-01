from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")

Gate = Callable[[Any], bool]


@dataclass
class Shadow:
    audit: bool = False
    pii: bool = False
    ttl: int | None = None


def merge_shadow(a: Shadow, b: Shadow) -> Shadow:
    return Shadow(
        audit=(a.audit or b.audit),
        pii=(a.pii or b.pii),
        ttl=(a.ttl if a.ttl is not None else b.ttl),
    )


@dataclass
class Step:
    """A composable pipeline step.

    Fields:
      - run: callable A -> B
      - gate: predicate on input to allow transition
      - shade: Shadow metadata
      - seal: predicate on output to ensure closure
    """

    run: Callable[[Any], Any]
    gate: Gate
    shade: Shadow
    seal: Callable[[Any], bool]

    def __rshift__(self, other: Step) -> Step:
        """Compose two steps with '>>' semantics.

        The left step is executed first. Its output is sealed, then the
        right step's gate is checked against that output and, if allowed,
        the right step is executed. The composed step merges shadows and
        carries forward the right step's seal.
        """

        def run(x: Any) -> Any:
            y = self.run(x)
            if not self.seal(y):
                msg = "Seal failed in left step"
                raise RuntimeError(msg)
            if not other.gate(y):
                msg = "Gate blocked transition"
                raise RuntimeError(msg)
            return other.run(y)

        def gate_fn(x: Any) -> bool:
            return self.gate(x)

        shade = merge_shadow(self.shade, other.shade)

        def seal_res(z: Any) -> bool:
            return other.seal(z)

        return Step(run=run, gate=gate_fn, shade=shade, seal=seal_res)


def make_step(
    run: Callable[[Any], Any],
    *,
    gate: Gate | None = None,
    shade: Shadow | None = None,
    seal: Callable[[Any], bool] | None = None,
) -> Step:
    """Helper to create a step with sensible defaults.

    Defaults:
      - gate: allow everything
      - shade: no shadow
      - seal: always True
    """
    gate_fn = gate if gate is not None else lambda _x: True
    shade_val = shade if shade is not None else Shadow()
    seal_fn = seal if seal is not None else lambda _y: True

    return Step(run=run, gate=gate_fn, shade=shade_val, seal=seal_fn)


# Convenience: pipeline builder (left-to-right composition)
def pipeline(*steps: Step) -> Step:
    if not steps:
        msg = "At least one step required"
        raise ValueError(msg)
    composed = steps[0]
    for s in steps[1:]:
        composed = composed >> s
    return composed


# Simple Pipeline class for tests expecting an importable symbol
@dataclass
class Pipeline:
    """Lightweight pipeline wrapper providing a test-friendly interface.

    Usage:
        p = Pipeline.from_steps(step1, step2)
        result = p.run(input)
    """

    steps: list[Step]

    def run(self, x: Any) -> Any:
        """Execute the composed pipeline over input x."""
        return pipeline(*self.steps).run(x)

    def add(self, step: Step) -> None:
        """Append a step to the pipeline."""
        self.steps.append(step)

    @classmethod
    def from_steps(cls, *steps: Step) -> Pipeline:
        return cls(list(steps))

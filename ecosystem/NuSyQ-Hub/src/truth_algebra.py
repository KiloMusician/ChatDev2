"""Replacement clean implementation of Truth algebra."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class Truth:
    """A lightweight multi-truth representation for orchestration and agents.

    Fields:
      value: Optional[bool]  # True/False/Unknown(None)
      confidence: float      # 0.0..1.0
      source: str            # 'inference'|'sensor'|'cache'|'user' etc.
      freshness: str         # 'fresh'|'stale'|'deferred' etc.
      scope: str             # 'local'|'global'|'session' etc.
      narrative_fit: float   # 0.0..1.0 how well it fits current story
    """

    value: bool | None
    confidence: float = 1.0
    source: str = "unknown"
    freshness: str = "fresh"
    scope: str = "local"
    narrative_fit: float = 1.0

    def to_dict(self):
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(s: str) -> Truth:
        d = json.loads(s)
        return Truth(
            d.get("value"),
            d.get("confidence", 1.0),
            d.get("source", "unknown"),
            d.get("freshness", "fresh"),
            d.get("scope", "local"),
            d.get("narrative_fit", 1.0),
        )

    def __repr__(self) -> str:  # concise human-friendly representation
        return (
            f"Truth(value={self.value}, conf={self.confidence:.2f}, src={self.source}, "
            f"fresh={self.freshness}, scope={self.scope}, narr={self.narrative_fit:.2f})"
        )


def freshness_most(a: Truth, b: Truth) -> str:
    # prefer the freshest
    order = {"fresh": 2, "stale": 1, "deferred": 0}
    return a.freshness if order.get(a.freshness, 0) >= order.get(b.freshness, 0) else b.freshness


def not_op(t: Truth) -> Truth:
    if t.value is None:
        return Truth(None, t.confidence, t.source, t.freshness, t.scope, t.narrative_fit)
    return Truth(
        not t.value,
        t.confidence,
        f"not({t.source})",
        t.freshness,
        t.scope,
        1 - t.narrative_fit,
    )


def and_op(a: Truth, b: Truth) -> Truth:
    """Combine two Truths using a conservative t-norm (min for confidence).
    If either is explicitly False with high confidence, result tends to False.
    """
    if a.value is False or b.value is False:
        # take the stronger disconfirming signal
        conf = min(
            a.confidence if a.value is False else 1.0, b.confidence if b.value is False else 1.0
        )
        return Truth(
            False,
            conf,
            f"({a.source}&{b.source})",
            freshness_most(a, b),
            "merged",
            min(a.narrative_fit, b.narrative_fit),
        )
    if a.value is None or b.value is None:
        # unknown => unknown but combine confidence
        return Truth(
            None,
            min(a.confidence, b.confidence),
            f"({a.source}&{b.source})",
            freshness_most(a, b),
            "merged",
            min(a.narrative_fit, b.narrative_fit),
        )
    # both True
    return Truth(
        True,
        min(a.confidence, b.confidence),
        f"({a.source}&{b.source})",
        freshness_most(a, b),
        "merged",
        min(a.narrative_fit, b.narrative_fit),
    )


def or_op(a: Truth, b: Truth) -> Truth:
    # optimistic disjunction using max confidence
    if a.value is True or b.value is True:
        return Truth(
            True,
            max(a.confidence if a.value else 0.0, b.confidence if b.value else 0.0),
            f"({a.source}|{b.source})",
            freshness_most(a, b),
            "merged",
            max(a.narrative_fit, b.narrative_fit),
        )
    if a.value is None or b.value is None:
        return Truth(
            None,
            max(a.confidence, b.confidence),
            f"({a.source}|{b.source})",
            freshness_most(a, b),
            "merged",
            max(a.narrative_fit, b.narrative_fit),
        )
    return Truth(
        False,
        max(a.confidence, b.confidence),
        f"({a.source}|{b.source})",
        freshness_most(a, b),
        "merged",
        max(a.narrative_fit, b.narrative_fit),
    )


def implies(a: Truth, b: Truth) -> Truth:
    # Simple probabilistic implication: P(b|a) approximated as conf(b) when a True
    if a.value is False:
        return Truth(
            True,
            1.0,
            f"(imp:{a.source}->{b.source})",
            freshness_most(a, b),
            "merged",
            b.narrative_fit,
        )
    if a.value is None:
        return Truth(
            None,
            min(a.confidence, b.confidence),
            f"(imp:{a.source}->{b.source})",
            freshness_most(a, b),
            "merged",
            b.narrative_fit,
        )
    # a is True
    return Truth(
        b.value,
        b.confidence * a.confidence,
        f"(imp:{a.source}->{b.source})",
        freshness_most(a, b),
        "merged",
        b.narrative_fit,
    )


def xor_op(a: Truth, b: Truth) -> Truth:
    # approximate: true when confidences disagree for true values
    if a.value is None or b.value is None:
        return Truth(
            None,
            abs(a.confidence - b.confidence),
            f"xor({a.source},{b.source})",
            freshness_most(a, b),
            "merged",
            abs(a.narrative_fit - b.narrative_fit),
        )
    return Truth(
        bool(a.value) ^ bool(b.value),
        abs(a.confidence - b.confidence),
        f"xor({a.source},{b.source})",
        freshness_most(a, b),
        "merged",
        abs(a.narrative_fit - b.narrative_fit),
    )


def evaluate(preds: Iterable[Truth], operator: str = "AND") -> Truth:
    """Combine a sequence of Truths using the chosen operator. Operator in {AND,OR,XOR,IMPLIES}.

    This is a small orchestration-ready evaluator; it keeps provenance and combines confidences conservatively.
    """
    preds = list(preds)
    if not preds:
        return Truth(None, 0.0, "none", "deferred", "merged", 0.0)

    op = operator.upper()
    if op == "AND":
        acc = preds[0]
        for p in preds[1:]:
            acc = and_op(acc, p)
        return acc
    if op == "OR":
        acc = preds[0]
        for p in preds[1:]:
            acc = or_op(acc, p)
        return acc
    if op == "XOR":
        acc = preds[0]
        for p in preds[1:]:
            acc = xor_op(acc, p)
        return acc
    if op == "IMPLIES":
        # implies chain: (p1 -> p2) and (p2 -> p3) ... approximated by folding
        acc = preds[0]
        for p in preds[1:]:
            acc = implies(acc, p)
        return acc

    raise ValueError(f"Unsupported operator: {operator}")


def necessarily(t: Truth, threshold: float = 0.95) -> Truth:
    """Modal 'necessarily' operator: high-confidence truth required."""
    if t.value is None:
        return Truth(None, t.confidence, t.source, t.freshness, t.scope, t.narrative_fit)
    if t.confidence >= threshold:
        return Truth(
            t.value, t.confidence, f"necessarily({t.source})", t.freshness, t.scope, t.narrative_fit
        )
    return Truth(
        None, t.confidence, f"necessarily({t.source})", t.freshness, t.scope, t.narrative_fit
    )


def possibly(t: Truth, threshold: float = 0.2) -> Truth:
    """Modal 'possibly' operator: low-confidence threshold for possibility."""
    if t.value is None:
        return Truth(None, t.confidence, t.source, t.freshness, t.scope, t.narrative_fit)
    if t.confidence >= threshold:
        return Truth(
            True, t.confidence, f"possibly({t.source})", t.freshness, t.scope, t.narrative_fit
        )
    return Truth(
        False, t.confidence, f"possibly({t.source})", t.freshness, t.scope, t.narrative_fit
    )


def map_to_omnitag(t: Truth) -> list:
    """Map a Truth to a simple OmniTag-like list: [purpose, dependencies, context, evolution_stage]

    purpose <- source
    dependencies <- empty list (placeholder)
    context <- scope
    evolution_stage <- 'mature'|'staged'|'experimental' based on confidence
    """
    if t.confidence >= 0.9:
        stage = "mature"
    elif t.confidence >= 0.6:
        stage = "staged"
    else:
        stage = "experimental"
    return [t.source, [], t.scope, stage]

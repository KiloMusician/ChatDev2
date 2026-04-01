"""Unit tests for src.orchestration.ecosystem_efficiency_engine."""

from __future__ import annotations

from src.orchestration.ecosystem_efficiency_engine import suggest_routing


def test_suggest_routing_generate_targets_chatdev():
    result = suggest_routing("generate", "Create feature", {"b": 2, "a": 1})
    assert result["target_system"] == "chatdev"
    assert result["confidence"] == 0.4
    assert result["context_keys"] == ["a", "b"]


def test_suggest_routing_analyze_and_review_target_ollama():
    analyze = suggest_routing("analyze", "Inspect code", {"ctx": True})
    review = suggest_routing("review", "Review code", {"ctx": True})
    assert analyze["target_system"] == "ollama"
    assert review["target_system"] == "ollama"


def test_suggest_routing_debug_targets_quantum_resolver():
    result = suggest_routing("debug", "Fix crash", {"run": "1"})
    assert result["target_system"] == "quantum_resolver"
    assert result["confidence"] == 0.4


def test_suggest_routing_unknown_has_no_target_and_zero_confidence():
    result = suggest_routing("plan", "Roadmap", None)
    assert result["target_system"] is None
    assert result["confidence"] == 0.0
    assert result["context_keys"] == []


def test_suggest_routing_context_keys_limited_to_eight():
    context = {f"k{i}": i for i in range(20)}
    result = suggest_routing("generate", "Any", context)
    assert len(result["context_keys"]) == 8

"""Lightweight coverage for QuantumProblemResolver high-level APIs.

These tests focus on deterministic, best-effort helpers to raise coverage on the
healing layer without invoking heavy quantum backends.
"""

from pathlib import Path

from src.healing.quantum_problem_resolver import QuantumProblemResolver


def test_detect_problems_empty(tmp_path: Path):
    resolver = QuantumProblemResolver(root_path=tmp_path)
    problems = resolver.detect_problems()
    assert problems == []


def test_detect_problems_finds_import_issue(tmp_path: Path):
    bad = tmp_path / "bad.py"
    bad.write_text("import nonexistent_module\n", encoding="utf-8")

    resolver = QuantumProblemResolver(root_path=tmp_path)
    problems = resolver.detect_problems()

    assert problems and problems[0]["type"] == "import_error"


def test_heal_problems_returns_summary():
    resolver = QuantumProblemResolver()
    summary = resolver.heal_problems([{"type": "import_error"}])

    assert summary["healed"] == 1
    assert summary["success"] is True


def test_heal_problems_handles_none():
    resolver = QuantumProblemResolver()
    summary = resolver.heal_problems(None)

    assert summary["healed"] == 0
    assert summary["success"] is True


def test_select_strategy_mapping():
    resolver = QuantumProblemResolver()

    assert resolver.select_strategy({"type": "import_error"}) == "import_fix"
    assert resolver.select_strategy({"type": "path_issue"}).startswith("path")
    assert resolver.select_strategy({"severity": "high"}) == "escalated_healing"
    assert resolver.select_strategy(None) == "general_healing"


def test_get_compute_resolver_best_effort_returns_none(monkeypatch):
    # Force compute backend to remain unavailable to avoid heavy imports
    import src.healing.quantum_problem_resolver as qpr

    monkeypatch.setattr(qpr, "_load_compute_backend", lambda: None, raising=False)
    monkeypatch.setattr(qpr, "QUANTUM_COMPUTE_AVAILABLE", False, raising=False)
    monkeypatch.setattr(qpr, "QuantumComputeResolver", None, raising=False)

    # Use qpr.QuantumProblemResolver (not top-level import) so the class's __globals__
    # references the same module object we just patched, even if the module was
    # previously evicted from sys.modules by another test's sys.modules.pop() cleanup.
    resolver = qpr.QuantumProblemResolver()

    backend = resolver._get_compute_resolver()  # pyright: ignore[reportPrivateUsage]

    assert backend is None


def test_get_algorithm_info_when_unavailable(monkeypatch):
    import src.healing.quantum_problem_resolver as qpr

    monkeypatch.setattr(qpr, "_load_compute_backend", lambda: None, raising=False)
    monkeypatch.setattr(qpr, "QUANTUM_COMPUTE_AVAILABLE", False, raising=False)
    monkeypatch.setattr(qpr, "QuantumComputeResolver", None, raising=False)

    resolver = QuantumProblemResolver()
    # Also patch the instance method directly to guard against cached compute resolver
    # from earlier tests that called _load_compute_backend successfully.
    monkeypatch.setattr(resolver, "_get_compute_resolver", lambda: None)

    info = resolver.get_algorithm_info("qaoa")

    assert info["status"] == "unavailable"
    assert info["algorithm"] == "qaoa"


def test_start_interactive_mode_graceful_when_unavailable(monkeypatch):
    import src.healing.quantum_problem_resolver as qpr

    monkeypatch.setattr(qpr, "_load_compute_backend", lambda: None, raising=False)
    monkeypatch.setattr(qpr, "QUANTUM_COMPUTE_AVAILABLE", False, raising=False)
    monkeypatch.setattr(qpr, "QuantumComputeResolver", None, raising=False)

    resolver = QuantumProblemResolver()

    # Should no-op without raising
    resolver.start_interactive_mode()

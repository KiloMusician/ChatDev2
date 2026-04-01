"""Tests for xi_nusyq Pipeline (Step-composition architecture)."""

from src.xi_nusyq.pipeline import Pipeline, Step, Shadow, make_step


def _identity_step() -> Step:
    """Create a simple pass-through step for testing."""
    return make_step(run=lambda x: x)


def test_pipeline_from_steps_creates_pipeline():
    """Pipeline.from_steps returns a Pipeline with steps list."""
    step = _identity_step()
    p = Pipeline.from_steps(step)
    assert isinstance(p, Pipeline)
    assert len(p.steps) == 1


def test_pipeline_run_returns_value():
    """Pipeline.run passes input through steps and returns output."""
    step = _identity_step()
    p = Pipeline.from_steps(step)
    result = p.run(42)
    assert result == 42


def test_pipeline_add_appends_step():
    """Pipeline.add appends a step to the steps list."""
    step1 = _identity_step()
    step2 = _identity_step()
    p = Pipeline.from_steps(step1)
    p.add(step2)
    assert len(p.steps) == 2


def test_pipeline_transform_step():
    """Pipeline with a transform step applies the function."""
    double_step = make_step(run=lambda x: x * 2)
    p = Pipeline.from_steps(double_step)
    assert p.run(5) == 10


def test_make_step_creates_valid_step():
    """make_step factory creates a Step with correct fields."""
    step = make_step(run=lambda x: x + 1)
    assert isinstance(step, Step)
    assert step.run(3) == 4


def test_shadow_default_fields():
    """Shadow dataclass has expected default boolean fields."""
    s = Shadow()
    assert s.audit is False
    assert s.pii is False
    assert s.ttl is None


def test_step_compose_operator():
    """>> operator chains two steps (covers Step.__rshift__)."""
    step_add = make_step(run=lambda x: x + 10)
    step_mul = make_step(run=lambda x: x * 2)
    composed = step_add >> step_mul
    # (5 + 10) * 2 = 30
    assert composed.run(5) == 30


def test_step_compose_seal_failure_raises():
    """>> raises RuntimeError if left step seal fails."""
    import pytest
    bad_seal = make_step(run=lambda x: x, seal=lambda x: False)
    next_step = make_step(run=lambda x: x)
    composed = bad_seal >> next_step
    with pytest.raises(RuntimeError, match="Seal failed"):
        composed.run(1)


def test_pipeline_function_single_step():
    """pipeline() with a single step returns that step."""
    from src.xi_nusyq.pipeline import pipeline
    step = make_step(run=lambda x: x * 3)
    result_step = pipeline(step)
    assert result_step.run(4) == 12


def test_pipeline_function_empty_raises():
    """pipeline() with no args raises ValueError."""
    import pytest
    from src.xi_nusyq.pipeline import pipeline
    with pytest.raises(ValueError, match="At least one step"):
        pipeline()

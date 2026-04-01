import pytest
from src.xi_nusyq.pipeline import Pipeline, Shadow, make_step, pipeline


def test_pipeline_success():
    # ingest: returns dict with x
    ingest = make_step(lambda _: {"x": 1}, shade=Shadow(audit=True))

    def validate(d):
        if "x" not in d:
            raise RuntimeError("missing x")
        return d

    validate_step = make_step(validate, seal=lambda d: True)

    def transform(d):
        d2 = dict(d)
        d2["y"] = d2["x"] + 1
        return d2

    transform_step = make_step(transform, shade=Shadow(pii=False), seal=lambda d: True)

    p = pipeline(ingest, validate_step, transform_step)
    out = p.run(None)
    assert out["y"] == 2


def test_gate_blocked():
    s1 = make_step(lambda _: {"ok": True})

    # gate that only allows inputs with 'ok' == False (so blocks)
    s2 = make_step(lambda d: d, gate=lambda d: False)

    p = pipeline(s1, s2)
    with pytest.raises(RuntimeError):
        p.run(None)


def test_shadow_merge():
    s1 = make_step(lambda _: 1, shade=Shadow(audit=True, pii=False))
    s2 = make_step(lambda v: v, shade=Shadow(audit=False, pii=True))
    p = pipeline(s1, s2)
    merged = p.shade
    assert merged.audit is True
    assert merged.pii is True


def test_pipeline_class_from_steps():
    """Test Pipeline class instantiation via from_steps."""
    step1 = make_step(lambda _: {"x": 10})
    step2 = make_step(lambda d: {**d, "y": d["x"] * 2})

    pipe = Pipeline.from_steps(step1, step2)
    result = pipe.run(None)
    assert result["x"] == 10
    assert result["y"] == 20


def test_pipeline_class_direct_init():
    """Test Pipeline class direct initialization."""
    step1 = make_step(lambda _: 5)
    step2 = make_step(lambda v: v + 3)

    pipe = Pipeline(steps=[step1, step2])
    result = pipe.run(None)
    assert result == 8


def test_pipeline_class_add_step():
    """Test Pipeline.add() method to append steps."""
    step1 = make_step(lambda _: {"val": 1})
    step2 = make_step(lambda d: {**d, "val": d["val"] + 1})
    step3 = make_step(lambda d: {**d, "val": d["val"] * 2})

    pipe = Pipeline(steps=[step1, step2])
    pipe.add(step3)

    assert len(pipe.steps) == 3
    result = pipe.run(None)
    assert result["val"] == 4  # (1 + 1) * 2


def test_pipeline_class_empty_steps_error():
    """Test that empty Pipeline raises error on run."""
    pipe = Pipeline(steps=[])
    with pytest.raises(ValueError, match="At least one step required"):
        pipe.run(None)


def test_pipeline_class_gate_blocks():
    """Test that Pipeline respects step gates."""
    step1 = make_step(lambda _: {"x": 100})
    step2 = make_step(lambda d: d, gate=lambda d: d["x"] > 50)  # gate allows
    step3 = make_step(lambda d: {**d, "blocked": True}, gate=lambda d: False)  # blocks

    pipe = Pipeline.from_steps(step1, step2)
    result = pipe.run(None)
    assert result["x"] == 100

    pipe_blocked = Pipeline.from_steps(step1, step3)
    with pytest.raises(RuntimeError):
        pipe_blocked.run(None)

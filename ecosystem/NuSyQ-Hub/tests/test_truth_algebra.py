from src.truth_algebra import Truth, and_op, evaluate, not_op, or_op


def test_basic_and_or_not():
    a = Truth(True, 0.9, "sensorA")
    b = Truth(False, 0.8, "sensorB")

    a_and_b = and_op(a, b)
    assert a_and_b.value is False

    a_or_b = or_op(a, b)
    assert a_or_b.value is True

    n = not_op(a)
    assert n.value is False


def test_evaluate_and_chain():
    p1 = Truth(True, 0.8, "p1")
    p2 = Truth(True, 0.6, "p2")
    res = evaluate([p1, p2], operator="AND")
    assert res.value is True
    assert abs(res.confidence - 0.6) < 1e-6

from src.tools.maze_solver import TREASURE_RE


def test_bug_word_boundary_does_not_match_debugging():
    assert TREASURE_RE.search("DEBUGGING") is None
    assert TREASURE_RE.search("bug-tracking") is None
    assert TREASURE_RE.search("BUG") is not None


def test_todo_and_fixme_detected():
    assert TREASURE_RE.search("# TODO: implement") is not None
    assert TREASURE_RE.search("# FIXME handle None") is not None

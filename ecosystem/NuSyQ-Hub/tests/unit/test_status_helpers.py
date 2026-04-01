from src.utils.status_helpers import is_completed, normalize_status


def test_normalize_various_statuses():
    assert normalize_status("complete") == "completed"
    assert normalize_status("COMPLETE") == "completed"
    assert normalize_status("Completed") == "completed"
    assert normalize_status(None) == "pending"


def test_is_completed_true_false():
    assert is_completed("complete")
    assert is_completed("completed")
    assert not is_completed("pending")

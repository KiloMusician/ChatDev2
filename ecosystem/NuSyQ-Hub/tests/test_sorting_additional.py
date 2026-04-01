from src.utils.sorting import quicksort


def test_quicksort_empty():
    assert quicksort([]) == []


def test_quicksort_singleton():
    assert quicksort([42]) == [42]


def test_quicksort_duplicates_and_negatives():
    data = [3, -1, 3, 2, -1, 0]
    assert quicksort(data) == sorted(data)

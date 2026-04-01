"""Unit tests for the quicksort algorithm.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing", "#TEST_SUITE", "#UNIT_TEST"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

from src.utils.sorting import quicksort


def test_quicksort_basic():
    assert quicksort([3, 1, 2]) == [1, 2, 3]


def test_quicksort_strings():
    assert quicksort(["b", "a", "c"]) == ["a", "b", "c"]

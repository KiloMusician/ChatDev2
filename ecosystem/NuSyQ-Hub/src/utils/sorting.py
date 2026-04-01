"""Utility sorting algorithms."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar


class _Comparable(Protocol):
    def __lt__(self, other: _Comparable, /) -> bool: ...

    def __gt__(self, other: _Comparable, /) -> bool: ...

    def __le__(self, other: _Comparable, /) -> bool: ...

    def __ge__(self, other: _Comparable, /) -> bool: ...


T = TypeVar("T", bound=_Comparable)


def quicksort(items: Sequence[T]) -> list[T]:
    """Return a new list containing *items* sorted using the quicksort algorithm.

    The implementation is a functional variant that does not mutate the input
    sequence. It selects the last element as pivot and recursively sorts the
    partitions.
    """
    items_list = list(items)
    if len(items_list) <= 1:
        return items_list

    pivot: T = items_list[-1]
    less = [x for x in items_list[:-1] if x <= pivot]
    greater = [x for x in items_list[:-1] if x > pivot]
    return [*quicksort(less), pivot, *quicksort(greater)]

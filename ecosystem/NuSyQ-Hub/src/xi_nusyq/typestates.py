from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class Frame(Generic[T]):
    value: T


@dataclass
class Bound(Generic[T]):
    value: T


@dataclass
class Walked(Generic[T]):
    value: T


@dataclass
class Closed(Generic[T]):
    value: T


def bind(frame: Frame[Any]) -> Bound[Any]:
    return Bound(frame.value)


def walk(bound: Bound[Any]) -> Walked[Any]:
    return Walked(bound.value)


def seal(walked: Walked[Any]) -> Closed[Any]:
    return Closed(walked.value)


def reopen(closed: Closed[Any]) -> Bound[Any]:
    return Bound(closed.value)

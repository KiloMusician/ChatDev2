# server/normalizers.py
from typing import Any, Iterable, List

def ensure_array(m: Any) -> List[Any]:
    if m is None:
        return []
    if isinstance(m, list):
        return m
    if isinstance(m, dict):
        return list(m.values())
    if isinstance(m, (tuple, set)):
        return list(m)
    return [m]

def safe_iter(m: Any) -> Iterable[Any]:
    for x in ensure_array(m):
        yield x
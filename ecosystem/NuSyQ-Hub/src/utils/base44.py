"""Base44 encoding and decoding helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-_.~!*@$"
BASE = len(ALPHABET)


def _count_leading_zeros(data: Iterable[int]) -> int:
    count = 0
    for b in data:
        if b == 0:
            count += 1
        else:
            break
    return count


def encode(data: bytes) -> str:
    """Encode bytes into a base44 string."""
    if not data:
        return ""
    num = int.from_bytes(data, "big")
    zeros = _count_leading_zeros(data)
    chars: list[Any] = []
    while num > 0:
        num, rem = divmod(num, BASE)
        chars.append(ALPHABET[rem])
    encoded = "".join(reversed(chars))
    return ALPHABET[0] * zeros + encoded


def decode(text: str) -> bytes:
    """Decode a base44 string back into bytes."""
    if not text:
        return b""
    zeros = len(text) - len(text.lstrip(ALPHABET[0]))
    num = 0
    for ch in text:
        num = num * BASE + ALPHABET.index(ch)
    byte_length = (num.bit_length() + 7) // 8
    decoded = num.to_bytes(byte_length, "big")
    return b"\x00" * zeros + decoded


__all__ = ["ALPHABET", "decode", "encode"]

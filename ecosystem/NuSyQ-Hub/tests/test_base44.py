"""Tests for src/utils/base44.py - Base44 encoding/decoding."""

import pytest
from src.utils.base44 import ALPHABET, BASE, _count_leading_zeros, decode, encode


class TestConstants:
    """Test module constants."""

    def test_alphabet_length(self):
        """Test ALPHABET has 44 characters."""
        assert len(ALPHABET) == 44

    def test_base_equals_alphabet_length(self):
        """Test BASE equals len(ALPHABET)."""
        assert BASE == len(ALPHABET)
        assert BASE == 44

    def test_alphabet_characters(self):
        """Test ALPHABET contains expected character types."""
        # Digits
        assert "0" in ALPHABET
        assert "9" in ALPHABET
        # Uppercase letters
        assert "A" in ALPHABET
        assert "Z" in ALPHABET
        # Special characters
        for ch in "-_.~!*@$":
            assert ch in ALPHABET

    def test_alphabet_is_unique(self):
        """Test all ALPHABET characters are unique."""
        assert len(ALPHABET) == len(set(ALPHABET))


class TestCountLeadingZeros:
    """Test _count_leading_zeros helper."""

    def test_no_zeros(self):
        """Test data with no leading zeros."""
        assert _count_leading_zeros([1, 2, 3]) == 0

    def test_one_leading_zero(self):
        """Test data with one leading zero."""
        assert _count_leading_zeros([0, 1, 2]) == 1

    def test_multiple_leading_zeros(self):
        """Test data with multiple leading zeros."""
        assert _count_leading_zeros([0, 0, 0, 1]) == 3

    def test_all_zeros(self):
        """Test data that is all zeros."""
        assert _count_leading_zeros([0, 0, 0, 0]) == 4

    def test_empty_data(self):
        """Test empty data."""
        assert _count_leading_zeros([]) == 0

    def test_bytes_input(self):
        """Test with bytes input (which is iterable of int)."""
        assert _count_leading_zeros(b"\x00\x00\x01\x02") == 2


class TestEncode:
    """Test encode function."""

    def test_empty_bytes(self):
        """Test encoding empty bytes returns empty string."""
        assert encode(b"") == ""

    def test_single_byte(self):
        """Test encoding single byte."""
        result = encode(b"\x01")
        assert result == "1"  # 1 in base44 is "1"

    def test_larger_number(self):
        """Test encoding larger number."""
        result = encode(b"\xff")  # 255
        assert len(result) > 0
        # 255 in base44 should decode back to same value
        decoded = decode(result)
        assert decoded == b"\xff"

    def test_leading_zeros_preserved(self):
        """Test leading zeros are preserved in encoding."""
        result = encode(b"\x00\x01")
        assert result.startswith(ALPHABET[0])  # Leading zero preserved

    def test_multiple_leading_zeros(self):
        """Test multiple leading zeros preserved."""
        result = encode(b"\x00\x00\x00\x01")
        assert result.startswith(ALPHABET[0] * 3)

    def test_all_zeros(self):
        """Test all-zero bytes."""
        result = encode(b"\x00\x00\x00")
        assert result == ALPHABET[0] * 3

    def test_ascii_text(self):
        """Test encoding ASCII text."""
        result = encode(b"hello")
        assert len(result) > 0
        # Should round-trip
        assert decode(result) == b"hello"


class TestDecode:
    """Test decode function."""

    def test_empty_string(self):
        """Test decoding empty string returns empty bytes."""
        assert decode("") == b""

    def test_single_char(self):
        """Test decoding single character."""
        encoded = encode(b"\x01")
        assert decode(encoded) == b"\x01"

    def test_leading_zeros_preserved(self):
        """Test leading zeros are preserved in decoding."""
        original = b"\x00\x00\x05"
        encoded = encode(original)
        decoded = decode(encoded)
        assert decoded == original

    def test_invalid_char_raises(self):
        """Test invalid character raises ValueError."""
        with pytest.raises(ValueError):
            decode("#")  # '#' not in ALPHABET


class TestRoundTrip:
    """Test encode/decode round-trip for various inputs."""

    @pytest.mark.parametrize(
        "data",
        [
            b"",
            b"\x00",
            b"\x01",
            b"\xff",
            b"\x00\x00\x00",
            b"hello",
            b"Hello, World!",
            b"\x00\x00hello",
            bytes(range(256)),  # All possible byte values
        ],
    )
    def test_round_trip(self, data):
        """Test encoding then decoding returns original data."""
        encoded = encode(data)
        decoded = decode(encoded)
        assert decoded == data

    def test_round_trip_unicode_bytes(self):
        """Test round-trip with UTF-8 encoded Unicode."""
        original = "日本語".encode()
        encoded = encode(original)
        decoded = decode(encoded)
        assert decoded == original

    def test_round_trip_binary_data(self):
        """Test round-trip with random binary data."""
        import os

        original = os.urandom(100)
        encoded = encode(original)
        decoded = decode(encoded)
        assert decoded == original


class TestEdgeCases:
    """Edge case tests."""

    def test_encode_produces_valid_alphabet_chars(self):
        """Test encode only produces characters from ALPHABET."""
        data = b"test data with various bytes \x00\xff\x7f"
        encoded = encode(data)
        for ch in encoded:
            assert ch in ALPHABET, f"Character '{ch}' not in ALPHABET"

    def test_decode_all_alphabet_chars(self):
        """Test decoding a string with all ALPHABET characters."""
        # Just verify it doesn't raise
        result = decode(ALPHABET)
        assert isinstance(result, bytes)

    def test_single_zero_byte(self):
        """Test single zero byte encodes to single ALPHABET[0]."""
        result = encode(b"\x00")
        assert result == ALPHABET[0]

    def test_single_max_byte(self):
        """Test single 0xff byte."""
        result = encode(b"\xff")
        decoded = decode(result)
        assert decoded == b"\xff"

    def test_large_data(self):
        """Test with larger data to ensure no overflow issues."""
        data = b"x" * 1000
        encoded = encode(data)
        decoded = decode(encoded)
        assert decoded == data

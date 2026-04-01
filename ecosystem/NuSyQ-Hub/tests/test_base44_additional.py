from src.utils.base44 import decode, encode


def test_encode_decode_roundtrip_empty():
    assert encode(b"") == ""
    assert decode("") == b""


def test_encode_decode_roundtrip_basic():
    data = b"hello world"
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data


def test_encode_preserves_leading_zeros():
    data = b"\x00\x00abc"
    encoded = encode(data)
    # Leading zeros must be preserved after decode
    decoded = decode(encoded)
    assert decoded == data


def test_decode_handles_all_alphabet_chars():
    # Ensure decode can process a string composed of all alphabet symbols
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-_.~!*@$"
    # This may not correspond to valid encoded data but should not raise ValueError
    decoded = decode(alphabet)
    assert isinstance(decoded, (bytes, bytearray))

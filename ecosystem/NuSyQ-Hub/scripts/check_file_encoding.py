#!/usr/bin/env python3
"""Check file bytes and UTF-8 decode for a given file path.

Usage:
    python scripts/check_file_encoding.py <path>
"""

import sys
from pathlib import Path


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("Usage: check_file_encoding.py <path>")
        return 2
    p = Path(argv[0])
    if not p.exists():
        print(f"File not found: {p}")
        return 2
    data = p.read_bytes()
    print(f"Path: {p}")
    print(f"Length (bytes): {len(data)}")
    contains_null = "yes" if b"\x00" in data else "no"
    print(f"Contains null bytes: {contains_null}")
    try:
        text = data.decode("utf-8")
        print("Decoded as UTF-8: yes")
        # show first 20 lines safely
        lines = text.splitlines()
        print(f"First {min(20, len(lines))} lines:")
        for i, ln in enumerate(lines[:20], 1):
            print(f"{i:3}: {ln}")
    except Exception as e:
        print("Decoded as UTF-8: no")
        print("Decode error:", e)
        # show a hexdump sample
        sample = data[:256]
        print("First 256 bytes (hex):")
        print(sample.hex())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

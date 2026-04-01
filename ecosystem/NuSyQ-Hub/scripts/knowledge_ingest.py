#!/usr/bin/env python3
"""Ingest artifacts into knowledge index and show Three-Before-New suggestions."""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

from src.system.knowledge import ingest_artifacts, three_before_new


def main() -> None:
    count = ingest_artifacts()
    print(f"Ingested {count} manifests into knowledge index.")
    suggestion = three_before_new("chatdev")
    if suggestion:
        print("Three-Before-New suggestions for 'chatdev':")
        for s in suggestion:
            print(" -", s)
    else:
        print("No matching patterns found.")


if __name__ == "__main__":
    main()

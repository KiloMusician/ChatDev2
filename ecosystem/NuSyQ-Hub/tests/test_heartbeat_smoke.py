#!/usr/bin/env python3
"""Quick heartbeat smoke test."""

import time

from src.tools.operator_heartbeat import heartbeat

print("🧪 Heartbeat Smoke Test")
print("=" * 50)
print("Running 6-second operation with 1-second heartbeat interval...")
print()

with heartbeat("Processing 20 items", interval=1.0):
    for i in range(20):
        print(f"  Processing item {i + 1}/20")
        time.sleep(0.3)

print()
print("✅ Smoke test complete!")

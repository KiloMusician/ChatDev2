#!/usr/bin/env python3
"""Quick test of TREASURE_RE fix"""

from src.tools.maze_solver import TREASURE_RE

test_cases = [
    ("BUG", True, "Match BUG"),
    ("bug", True, "Match bug (case-insensitive)"),
    ("DEBUGGING", False, "NOT match inside DEBUGGING"),
    ("bug-tracking", False, "NOT match inside bug-tracking"),
    ("TODO: fix", True, "Match TODO"),
    ("FIXME issue", True, "Match FIXME"),
    ("buggy", False, "NOT match inside buggy"),
]

print("Testing TREASURE_RE patterns:")
all_pass = True
for text, should_match, description in test_cases:
    matches = TREASURE_RE.search(text) is not None
    status = "✓" if matches == should_match else "✗"
    result = "PASS" if matches == should_match else "FAIL"
    print(f"{status} {result}: {description}")
    if matches != should_match:
        all_pass = False
        print(f"    Expected: {should_match}, Got: {matches}")

if all_pass:
    print("\n✅ All TREASURE_RE pattern tests pass!")
else:
    print("\n❌ Some tests failed!")
    exit(1)

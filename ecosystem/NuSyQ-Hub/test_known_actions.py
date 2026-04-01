#!/usr/bin/env python3
"""Test script to verify KNOWN_ACTIONS parsing."""

import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import the module
from scripts import start_nusyq

print(f"KNOWN_ACTIONS type: {type(start_nusyq.KNOWN_ACTIONS)}")
print(f"KNOWN_ACTIONS length: {len(start_nusyq.KNOWN_ACTIONS)}")
print(f"\nContains 'ai_status': {'ai_status' in start_nusyq.KNOWN_ACTIONS}")
print(f"Contains 'ai_work_gate': {'ai_work_gate' in start_nusyq.KNOWN_ACTIONS}")
print(f"Contains 'brief': {'brief' in start_nusyq.KNOWN_ACTIONS}")

# Show all actions with 'ai' in the name
ai_actions = [a for a in start_nusyq.KNOWN_ACTIONS if "ai" in a.lower()]
print(f"\nAI-related actions ({len(ai_actions)}):")
for action in sorted(ai_actions):
    print(f"  - {action}")

# Show first 20 actions
print("\nFirst 20 actions:")
for action in sorted(start_nusyq.KNOWN_ACTIONS)[:20]:
    print(f"  - {action}")

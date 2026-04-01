"""DevMentor validator (v0)

This script demonstrates how to surface feedback in VS Code's Problems panel
via a problemMatcher in tasks.json.

Output format:
ERROR path:line:col - message
WARN  path:line:col - message
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".devmentor" / "state.json"


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def main():
    state = load_state()
    active = state.get("active_challenge")

    # v0: if no challenge set, validate the first challenge by convention
    if not active:
        active = "challenges/git-challenges/01-first-commit"
        state["active_challenge"] = active
        (ROOT / ".devmentor").mkdir(exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

    # Basic checks
    readme = ROOT / active / "README.md"
    if not readme.exists():
        print(f"ERROR {active}/README.md:1:1 - Missing challenge README.md")
        return

    # Challenge-specific check: for "first commit", require a learner note
    note = ROOT / ".devmentor" / "notes" / "first_commit.md"
    if not note.exists():
        print(
            "WARN .devmentor/notes/first_commit.md:1:1 - Create this note file after completing the challenge."
        )
        print(
            "WARN .devmentor/notes/first_commit.md:1:1 - Tip: write what you staged vs committed and why."
        )
    else:
        # Simple content check
        content = note.read_text(encoding="utf-8").strip()
        if len(content) < 40:
            print(
                "WARN .devmentor/notes/first_commit.md:1:1 - Add a bit more detail (aim for 2–5 sentences)."
            )
        else:
            print("✅ Challenge note present. (v0 validation passed)")


if __name__ == "__main__":
    main()

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".devmentor"
STATE_PATH = STATE_DIR / "state.json"

REQUIRED_FILES = [
    "START_HERE.md",
    "README.md",
    ".vscode/tasks.json",
    ".vscode/settings.json",
    ".vscode/extensions.json",
    "scripts/devmentor_bootstrap.py",
    "scripts/devmentor_portable.py",
    "scripts/devmentor_validate.py",
]


def main():
    missing = 0
    for f in REQUIRED_FILES:
        if not (ROOT / f).exists():
            missing += 1
            print(f"ERROR {f}:1:1 - Missing required file")

    STATE_DIR.mkdir(exist_ok=True)
    if not STATE_PATH.exists():
        STATE_PATH.write_text(
            json.dumps(
                {
                    "schema_version": "2.0",
                    "first_open_completed": False,
                    "active_track": "vscode",
                    "active_tutorial": "tutorials/00-vscode-basics/01-command-palette.md",
                    "active_challenge": None,
                    "skill_xp": {
                        "vscode": 0,
                        "git": 0,
                        "ai": 0,
                        "debugging": 0,
                        "godot": 0,
                    },
                    "achievements": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print("WARN .devmentor/state.json:1:1 - Created missing state.json")

    (ROOT / "exports").mkdir(exist_ok=True)
    (ROOT / "docs").mkdir(exist_ok=True)

    if missing == 0:
        print("✅ Improve completed: workspace healthy.")
    else:
        print("⚠️ Improve completed with missing files. Fix ERRORs above.")


if __name__ == "__main__":
    main()

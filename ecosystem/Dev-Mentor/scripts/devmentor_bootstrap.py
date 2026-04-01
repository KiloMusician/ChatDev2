import json
import shutil
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".devmentor"
STATE_PATH = STATE_DIR / "state.json"

DEFAULT_STATE = {
    "schema_version": "1.0",
    "first_open_completed": False,
    "active_track": "vscode",
    "active_tutorial": "tutorials/00-vscode-basics/01-command-palette.md",
    "active_challenge": None,
    "skill_xp": {"vscode": 0, "git": 0, "ai": 0, "debugging": 0, "godot": 0},
    "achievements": [],
    "last_platform": "vscode",
    "last_updated": None,
}

TUTORIAL_SEQUENCE = [
    "tutorials/00-vscode-basics/01-command-palette.md",
    "tutorials/00-vscode-basics/02-keyboard-shortcuts.md",
    "tutorials/01-git-in-vscode/01-clone-and-scm.md",
    "tutorials/01-git-in-vscode/02-first-commit.md",
    "tutorials/02-ai-tools-in-vscode/01-ai-workflow-basics.md",
]


def load_state():
    STATE_DIR.mkdir(exist_ok=True)
    if not STATE_PATH.exists():
        save_state(DEFAULT_STATE)
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state):
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _next_in_sequence(current: str) -> str:
    try:
        i = TUTORIAL_SEQUENCE.index(current)
        if i < len(TUTORIAL_SEQUENCE) - 1:
            return TUTORIAL_SEQUENCE[i + 1]
    except ValueError:
        pass
    return current


def _check_cmd(name: str, cmd: str) -> tuple[bool, str]:
    path = shutil.which(cmd)
    if path:
        return True, f"{name}: found at {path}"
    return False, f"{name}: not found (install and add to PATH)"


def _check_url(name: str, url: str, timeout: float = 1.0) -> tuple[bool, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if 200 <= resp.status < 400 or resp.status == 404:
                return True, f"{name}: reachable ({resp.status})"
            return False, f"{name}: unreachable ({resp.status})"
    except Exception as e:
        return False, f"{name}: error ({e})"


def diagnose():
    print("DevMentor Diagnose")
    print(f"- Workspace: {ROOT}")
    print("- State:")
    print(f"  {STATE_PATH} ({'exists' if STATE_PATH.exists() else 'missing'})")
    print(f"- Python: {sys.executable} (v{sys.version.split()[0]})")
    print("- Tip: Run 'DevMentor: Start/Resume'")


def health_check():
    print("DevMentor Health Check")
    print(f"- Workspace: {ROOT}")

    print("\nChecking core tools:")
    for ok, msg in [
        _check_cmd("python", "python"),
        _check_cmd("git", "git"),
        _check_cmd("node", "node"),
        _check_cmd("npm", "npm"),
    ]:
        print(f"{'✅' if ok else '❌'} {msg}")

    print("\nChecking common services (HTTP endpoints):")
    services = [
        ("DevMentor server", "http://127.0.0.1:7337/"),
        ("SimulatedVerse", "http://127.0.0.1:5000/"),
        ("NuSyQ MCP", "http://127.0.0.1:8081/"),
        ("Ollama", "http://127.0.0.1:11434/"),
        ("LM Studio", "http://127.0.0.1:1234/"),
    ]
    for name, url in services:
        ok, msg = _check_url(name, url)
        print(f"{'✅' if ok else '❌'} {msg}")

    print("\nTip: Start any missing service.")
    print("Use the relevant start script or Docker compose.")


def start():
    state = load_state()
    print("🧠 DevMentor Runtime: Start/Resume")
    print(f"➡️ Next tutorial: {state['active_tutorial']}")
    print("✅ What to do now (inside VS Code):")
    print("1) Open the tutorial in Explorer")
    print("2) Follow the steps")
    print("3) Run: DevMentor: Next Step")
    if not state.get("first_open_completed", False):
        print("\nTip: Open START_HERE.md if you haven't yet.")


def next_step():
    state = load_state()
    current = state["active_tutorial"]
    nxt = _next_in_sequence(current)
    if nxt == current:
        print("🏁 You're at the end of the current v0 tutorial chain.")
        print("Next: pick a challenge in challenges/")
        print("then run the validation task.")
        return

    # Award small XP for completing a step (v0 simplistic)
    if current.startswith("tutorials/00-vscode-basics"):
        state["skill_xp"]["vscode"] += 25
    elif current.startswith("tutorials/01-git-in-vscode"):
        state["skill_xp"]["git"] += 25
    elif current.startswith("tutorials/02-ai-tools-in-vscode"):
        state["skill_xp"]["ai"] += 25

    state["active_tutorial"] = nxt
    if not state.get("first_open_completed"):
        state["first_open_completed"] = True
    save_state(state)

    print("⏭ DevMentor: Next Step")
    print(f"✅ Saved progress. New next tutorial: {nxt}")
    print("Open it in VS Code, complete it, then run Next Step again.")


if __name__ == "__main__":
    cmd = (sys.argv[1:] or ["start"])[0]
    if cmd == "start":
        start()
    elif cmd == "next":
        next_step()
    elif cmd == "diagnose":
        diagnose()
    elif cmd == "health":
        health_check()
    else:
        print("Usage: python scripts/devmentor_bootstrap.py <cmd>")
        print("Commands: start, next, diagnose, health")

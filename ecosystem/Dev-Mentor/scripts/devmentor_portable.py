import json
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".devmentor"
STATE_PATH = STATE_DIR / "state.json"
EXPORTS = ROOT / "exports"

INCLUDE_PATHS = [
    "README.md",
    "START_HERE.md",
    "docs",
    "tutorials",
    "challenges",
    "scripts/devmentor_bootstrap.py",
    "scripts/devmentor_portable.py",
    "scripts/devmentor_validate.py",
    ".vscode",
]


def load_state():
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state):
    STATE_DIR.mkdir(exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def export_zip():
    EXPORTS.mkdir(exist_ok=True)
    state = load_state()
    manifest = {
        "schema_version": "1.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "state": state,
        "resume_hint": state.get("active_tutorial"),
        "instructions": "Unzip, open in VS Code, run task: DevMentor: Start/Resume",
    }
    zip_path = EXPORTS / "devmentor-portable.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2))
        for rel in INCLUDE_PATHS:
            p = ROOT / rel
            if p.is_dir():
                for fp in p.rglob("*"):
                    if fp.is_file():
                        z.write(fp, arcname=str(fp.relative_to(ROOT)))
            elif p.exists():
                z.write(p, arcname=str(p.relative_to(ROOT)))
    print(f"✅ Exported portable ZIP: {zip_path}")


def import_zip():
    zip_path = EXPORTS / "devmentor-portable.zip"
    if not zip_path.exists():
        print("❌ No exports/devmentor-portable.zip found.")
        return
    with zipfile.ZipFile(zip_path, "r") as z:
        manifest = json.loads(z.read("manifest.json"))
        state = manifest.get("state", {})
        save_state(state)
    print("✅ Imported progress into .devmentor/state.json")
    print(f"➡️ Resume from: {state.get('active_tutorial')}")


if __name__ == "__main__":
    import sys

    cmd = (sys.argv[1:] or ["export"])[0]
    if cmd == "export":
        export_zip()
    elif cmd == "import":
        import_zip()
    else:
        print("Usage: python scripts/devmentor_portable.py [export|import]")

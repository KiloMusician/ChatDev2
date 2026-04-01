import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".devmentor" / "state.json"
DOCS = ROOT / "docs"


def _read_json(p: Path, default):
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default


def _cmd_ok(cmd):
    try:
        r = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )  # nosec B603
        return r.returncode == 0, (r.stdout.strip() or r.stderr.strip())
    except Exception as e:
        return False, str(e)


def main():
    DOCS.mkdir(exist_ok=True)
    state = _read_json(STATE_PATH, {})
    has_git, git_ver = _cmd_ok(["git", "--version"])
    has_code_cli, code_ver = _cmd_ok(["code", "--version"])

    status = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "workspace": str(ROOT),
        "progress": {
            "active_tutorial": state.get("active_tutorial"),
            "active_track": state.get("active_track"),
            "skill_xp": state.get("skill_xp", {}),
            "achievements": state.get("achievements", []),
        },
        "environment": {
            "git_available": has_git,
            "git_version": git_ver if has_git else None,
            "code_cli_available": has_code_cli,
            "code_cli_version_or_hint": (
                code_ver if has_code_cli else "Optional: ensure `code` is on PATH."
            ),
            "python": "ok",
        },
    }

    md = []
    md.append("# DevMentor Status Dashboard")
    md.append("")
    md.append(f"- Generated: `{status['generated_at']}`")
    md.append(f"- Workspace: `{status['workspace']}`")
    md.append("")
    md.append("## Progress")
    md.append(f"- Active tutorial: `{status['progress']['active_tutorial']}`")
    md.append(f"- Active track: `{status['progress']['active_track']}`")
    md.append(f"- XP: `{json.dumps(status['progress']['skill_xp'])}`")
    md.append(
        f"- Achievements: `{', '.join(status['progress']['achievements']) or 'none yet'}`"
    )
    md.append("")
    md.append("## Environment")
    md.append(f"- Git: `{status['environment']['git_available']}`")
    md.append(
        f"- Git version/hint: `{status['environment']['git_version'] or 'not found'}`"
    )
    md.append(
        f"- VS Code CLI (`code`): `{status['environment']['code_cli_available']}`"
    )
    md.append(
        f"- VS Code CLI version/hint: `{status['environment']['code_cli_version_or_hint']}`"
    )
    md.append("")
    md.append("## Next actions")
    md.append("1. Run task: **DevMentor: Start/Resume**")
    md.append("2. Complete the active tutorial file")
    md.append("3. Run task: **DevMentor: Next Step**")
    md.append("4. Export often: **DevMentor: Export Portable ZIP**")
    md.append("")
    (DOCS / "STATUS.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    nxt = []
    nxt.append("# DevMentor Next Actions")
    nxt.append("")
    nxt.append("- Open `START_HERE.md`")
    nxt.append("- Run: **DevMentor: Start/Resume**")
    nxt.append("- Or launch the console: **DevMentor: Launch DevMentor Console (Web)**")
    nxt.append("")
    (DOCS / "NEXT_ACTIONS.md").write_text("\n".join(nxt) + "\n", encoding="utf-8")

    print("✅ Wrote docs/STATUS.md and docs/NEXT_ACTIONS.md")


if __name__ == "__main__":
    main()

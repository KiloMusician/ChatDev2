from pathlib import Path

files = [
    Path("tests/test_ai_coordinator_generated.py"),
    Path("src/copilot/__init__.py"),
    Path("src/copilot/bridge_cli.py"),
    Path("tests/test_orchestrator_sns.py"),
]
root = Path("c:/Users/keath/Desktop/Legacy/NuSyQ-Hub")
for f in files:
    p = root / f
    if not p.exists():
        print("missing", p)
        continue
    s = p.read_text(encoding="utf-8")
    if s.strip().startswith("```"):
        lines = s.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s2 = "\n".join(lines).lstrip("\n")
        p.write_text(s2, encoding="utf-8")
        print("fixed", p)
    else:
        print("no change", p)

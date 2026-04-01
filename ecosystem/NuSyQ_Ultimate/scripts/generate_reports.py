import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
MANIFEST = ROOT / "nusyq.manifest.yaml"
REPORTS = ROOT / "Reports"
REPORTS.mkdir(exist_ok=True)

# Load manifest and normalize model list
m = yaml.safe_load(open(MANIFEST, "r", encoding="utf-8").read())
models = m.get("ollama_models", [])
manifest_models = []
for mm in models:
    if isinstance(mm, str):
        manifest_models.append(mm.strip())
    elif isinstance(mm, dict):
        manifest_models.extend(list(mm.keys()))

# call ollama
installed = None
try:
    r = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode == 0:
        installed = []
        for line in r.stdout.splitlines():
            parts = line.split()
            if parts and ":" in parts[0]:
                installed.append(parts[0])
    else:
        installed = None
except FileNotFoundError:
    installed = None

out = REPORTS / "ollama_model_sync.md"
with open(out, "w", encoding="utf-8") as f:
    f.write("# Ollama Model Sync Report\n\n")
    f.write("## Manifest models\n")
    for mm in manifest_models:
        f.write(f"- {mm}\n")

    f.write("\n## Installed models\n")
    if installed is None:
        f.write("_ollama CLI not found or failed to list models_\n")
    else:
        for im in installed:
            f.write(f"- {im}\n")

    f.write("\n## Status\n")
    if installed is None:
        f.write("Cannot determine installed models.\n")
    else:
        missing = [mm for mm in manifest_models if mm not in installed]
        extra = [im for im in installed if im not in manifest_models]
        if not missing:
            f.write("- All manifest models are present locally.\n")
        else:
            f.write("- Missing models:\n")
            for mm in missing:
                f.write(f"  - {mm}\n")
        if extra:
            f.write("- Extra local models not in manifest:\n")
            for im in extra:
                f.write(f"  - {im}\n")

print("WROTE", out)

# TODO report
todos = []
for p in ROOT.rglob("*.py"):
    try:
        txt = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue
    for i, line in enumerate(txt.splitlines(), 1):
        if "TODO" in line or "FIXME" in line or "HACK" in line:
            todos.append(f"{p}:{i}: {line.strip()}")

out2 = REPORTS / "TODO_REPORT.md"
with open(out2, "w", encoding="utf-8") as f:
    f.write("# TODO Report\n\n")
    if todos:
        for t in todos:
            f.write(f"- {t}\n")
    else:
        f.write("No TODOs found.\n")

print("WROTE", out2)

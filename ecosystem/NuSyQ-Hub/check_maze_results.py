import json
from pathlib import Path

latest = max(Path("logs").glob("maze_summary_*.json"), key=lambda p: p.stat().st_mtime)
data = json.loads(latest.read_text(encoding="utf-8"))

print(f"Latest: {latest.name}")
print(f"Total treasures found: {data['total']}")
print(f"Files scanned: {len(data['files'])}")

venv_files = [item for item in data["files"] if ".venv.old" in item.lower()]
print(f"Files in .venv.old: {len(venv_files)}")

if venv_files:
    print("ERROR: .venv.old files STILL found!")
    print(f"Sample .venv.old paths: {venv_files[:3]}")
else:
    print("✅ SUCCESS: NO .venv.old files found! Exclusion working!")

sample_paths = (
    list(data["files"].values())[:5] if isinstance(data["files"], dict) else data["files"][:5]
)
print(f"Sample paths in scan: {sample_paths}")

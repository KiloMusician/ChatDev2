import json
import os

p = "src/Rosetta_Quest_System/quests.json"
print("Path exists:", os.path.exists(p))
print("Size:", os.path.getsize(p))
with open(p, "rb") as f:
    data = f.read()
    head = data[:200]
    print("First 200 bytes:", head)
try:
    with open(p, encoding="utf-8") as f:
        obj = json.load(f)
    print("JSON loaded, elements:", len(obj))
except Exception as e:
    print("JSON load error:", repr(e))

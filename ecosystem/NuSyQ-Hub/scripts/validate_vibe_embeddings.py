import json
import pathlib
import sys

p = pathlib.Path("lattices/vibe.embeddings.jsonl")
if not p.exists():
    print("ERROR: embeddings file missing:", p)
    sys.exit(2)
bad = 0
dims = set()
n = 0
with p.open("r", encoding="utf-8") as fh:
    for n, line in enumerate(fh, 1):
        try:
            obj = json.loads(line)
        except Exception as e:
            print(f"LINE {n} JSON ERROR: {e}")
            bad += 1
            continue
        emb = obj.get("embedding") or (obj.get("embeddings") or [None])[0]
        if not emb:
            bad += 1
        else:
            dims.add(len(emb))
print("lines:", n, "empty_vectors:", bad, "dims:", sorted(dims))
if bad:
    sys.exit(1)
sys.exit(0)

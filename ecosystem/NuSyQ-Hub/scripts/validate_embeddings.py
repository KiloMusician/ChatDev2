import json
import sys

p = "lattices/vibe.embeddings.jsonl"
count = 0
dims = set()
with open(p, encoding="utf-8") as fh:
    for line in fh:
        count += 1
        obj = json.loads(line)
        emb = obj.get("embedding")
        if emb is None:
            print("MISSING embedding at line", count)
            sys.exit(2)
        if len(emb) == 0:
            print("EMPTY embedding at line", count)
            sys.exit(3)
        dims.add(len(emb))
print("entries=", count, "dims=", sorted(dims))
if len(dims) > 1:
    print("WARNING: inconsistent embedding dims")
    sys.exit(4)
print("OK")

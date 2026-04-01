import hashlib
import json
import pathlib
from datetime import datetime

p = pathlib.Path("lattices/vibe.embeddings.jsonl")
if not p.exists():
    print("MISSING")
    raise SystemExit(2)
sha = hashlib.sha256(p.read_bytes()).hexdigest()
size = p.stat().st_size
ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
print(sha, size, ts)
# also write small metadata file for later use
meta = {"sha256": sha, "size": size, "created": ts, "path": str(p)}
path = pathlib.Path(".hub")
path.mkdir(exist_ok=True)
(path / "vibe.emb.meta.json").write_text(json.dumps(meta, indent=2))
print("wrote .hub/vibe.emb.meta.json")

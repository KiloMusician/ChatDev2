import json
import pathlib
import sys

meta_p = pathlib.Path(".hub") / "vibe.emb.meta.json"
if not meta_p.exists():
    print("meta missing", meta_p)
    sys.exit(2)

meta = json.loads(meta_p.read_text(encoding="utf-8"))
sha = meta["sha256"]
size = meta["size"]
ts = meta["created"]

# update .hub/index.json
idxp = pathlib.Path(".hub") / "index.json"
if not idxp.exists():
    idxp.parent.mkdir(parents=True, exist_ok=True)
    idxp.write_text(json.dumps({"lattices": []}, indent=2), encoding="utf-8")
idx = json.loads(idxp.read_text(encoding="utf-8"))
# upsert vibe entry
found = False
for lattice in idx.get("lattices", []):
    if lattice.get("id") == "vibe":
        lattice["path"] = "lattices\\vibe.json"
        artifacts = lattice.get("artifacts", [])
        # remove old embeddings artifact
        artifacts = [
            a
            for a in artifacts
            if not (a.get("type") == "embeddings" and a.get("path", "").endswith("vibe.embeddings.jsonl"))
        ]
        artifacts.append(
            {
                "type": "embeddings",
                "path": "lattices\\vibe.embeddings.jsonl",
                "sha256": sha,
                "size": size,
                "created": ts,
            }
        )
        lattice["artifacts"] = artifacts
        found = True
        break
if not found:
    idx.setdefault("lattices", []).append(
        {
            "id": "vibe",
            "path": "lattices\\vibe.json",
            "artifacts": [
                {
                    "type": "embeddings",
                    "path": "lattices\\vibe.embeddings.jsonl",
                    "sha256": sha,
                    "size": size,
                    "created": ts,
                }
            ],
        }
    )
idxp.write_text(json.dumps(idx, indent=2), encoding="utf-8")
print("updated", idxp)

# update docs/Vault/lattices_index.json
vault = pathlib.Path("docs") / "Vault" / "lattices_index.json"
vault.parent.mkdir(parents=True, exist_ok=True)
if not vault.exists():
    vault.write_text("[]", encoding="utf-8")
raw = vault.read_text(encoding="utf-8")
try:
    arr = json.loads(raw)
except (json.JSONDecodeError, ValueError):
    # if file is malformed, start fresh
    arr = {}

if isinstance(arr, dict):
    # update dict-style registry
    arr["vibe"] = {
        "id": "vibe",
        "name": "vibe-coding",
        "lattice": "lattices\\vibe.json",
        "embeddings": "lattices\\vibe.embeddings.jsonl",
        "sha256": sha,
        "size": size,
        "registered_at": ts,
    }
    vault.write_text(json.dumps(arr, indent=2), encoding="utf-8")
elif isinstance(arr, list):
    arr = [x for x in arr if x.get("id") != "vibe"]
    arr.append(
        {
            "id": "vibe",
            "name": "vibe-coding",
            "lattice": "lattices\\vibe.json",
            "embeddings": "lattices\\vibe.embeddings.jsonl",
            "sha256": sha,
            "size": size,
            "registered_at": ts,
        }
    )
    vault.write_text(json.dumps(arr, indent=2), encoding="utf-8")
else:
    # unknown shape: overwrite with dict
    new = {
        "vibe": {
            "id": "vibe",
            "name": "vibe-coding",
            "lattice": "lattices\\vibe.json",
            "embeddings": "lattices\\vibe.embeddings.jsonl",
            "sha256": sha,
            "size": size,
            "registered_at": ts,
        }
    }
    vault.write_text(json.dumps(new, indent=2), encoding="utf-8")
print("updated", vault)

from __future__ import annotations
import json
import os
import hashlib
import argparse
import pathlib
from sentence_transformers import SentenceTransformer

def iter_files(root: str):
    ex = {".git", "node_modules", ".venv", ".cache", ".attic", ".quarantine", "models"}
    for dp, dn, fn in os.walk(root):
        if any(part in ex for part in pathlib.Path(dp).parts): continue
        for f in fn:
            p = pathlib.Path(dp)/f
            if p.is_file() and p.stat().st_size < 2_000_000:  # 2MB cap
                yield p

def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as r:
        for chunk in iter(lambda: r.read(8192), b""): h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default=".reports/index.json")
    args = ap.parse_args()

    model = SentenceTransformer("all-MiniLM-L6-v2")  # CPU ok
    records = []
    texts = []
    paths = []

    for p in iter_files(args.root):
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        paths.append(str(p))
        texts.append(text[:4000])  # sample
        records.append({"path": str(p), "hash": sha256(p), "size": p.stat().st_size})

    if texts:
        embs = model.encode(texts, show_progress_bar=False).tolist()
        for rec, emb in zip(records, embs): rec["emb"] = emb

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as w: json.dump(records, w)
    print(f"indexed: {len(records)} → {args.out}")

if __name__ == "__main__":
    main()
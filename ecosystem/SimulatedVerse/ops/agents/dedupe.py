import argparse
import json
import os
import hashlib
import pathlib
import shutil

def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--write", default=".reports/dupes.json")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    ex = {".git","node_modules",".venv",".cache",".attic",".quarantine"}
    map_hash = {}
    for dp, dn, fn in os.walk(args.root):
        if any(part in ex for part in pathlib.Path(dp).parts): continue
        for f in fn:
            p = pathlib.Path(dp)/f
            if not p.is_file(): continue
            try: h = sha256(p)
            except Exception: continue
            map_hash.setdefault(h, []).append(str(p))

    dupes = {h:paths for h,paths in map_hash.items() if len(paths)>1}
    os.makedirs(os.path.dirname(args.write), exist_ok=True)
    with open(args.write,"w") as w: json.dump(dupes, w, indent=2)
    print(f"dupes: {sum(len(v)-1 for v in dupes.values())} → {args.write}")

    if args.apply:
        attic = pathlib.Path(".attic/dupes"); attic.mkdir(parents=True, exist_ok=True)
        for _, paths in dupes.items():
            # keep first as canonical; move others to attic
            for p in paths[1:]:
                src = pathlib.Path(p)
                dst = attic / src.name
                try: shutil.move(str(src), str(dst))
                except Exception: pass

if __name__ == "__main__":
    main()
# /ops/tools/history_indexer.py
import argparse
import json
import re
from pathlib import Path

def index_docs(root: Path):
    entries = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md",".mdx",".txt",".rst"}:
            title = p.stem.replace("_"," ").replace("-"," ").title()
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                m = re.search(r"^#\s+(.+)$", txt, re.M)
                if m: title = m.group(1).strip()
                entries.append({"path": str(p), "title": title})
            except: pass
    return {"count": len(entries), "items": entries[:500]}

def index_quests(qbook: Path):
    try:
        import yaml
    except:
        import subprocess
        import sys
        subprocess.run([sys.executable,"-m","pip","install","pyyaml","--quiet"], check=False)
        import yaml
    data = yaml.safe_load(qbook.read_text(encoding="utf-8"))
    qs = data.get("quests",[])
    out = []
    for q in qs:
        out.append({"id": q.get("id"), "title": q.get("title"), "tier": q.get("tier"), "tags": q.get("tags",[])})
    return {"count": len(out), "items": out[:500]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=str)
    ap.add_argument("--quests", type=str)
    ap.add_argument("--out", type=str, required=True)
    args = ap.parse_args()

    res = {}
    if args.docs:
        res["docs"] = index_docs(Path(args.docs))
    if args.quests:
        res["quests"] = index_quests(Path(args.quests))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"indexed -> {args.out}")

if __name__ == "__main__":
    main()
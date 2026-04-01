#!/usr/bin/env python3
"""Simple curator/inspector for src/Rosetta_Quest_System/quests.json

Usage:
  python scripts/curate_quests.py [--dedupe] [--out deduped.json]

This script prints basic stats and reports duplicate quest ids/titles.
If --dedupe is provided the script will write a deduplicated file (keeping
the first occurrence of each quest id).
"""

import argparse
import json
from collections import Counter
from pathlib import Path

QUESTS_PATH = Path("src/Rosetta_Quest_System/quests.json")


def load_quests(path: Path):
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    # common shapes: list of quests, or dict with key 'quests'
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # try common keys
        for key in ("quests", "items", "questlines", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # fallback: try to find first list value
        for v in data.values():
            if isinstance(v, list):
                return v
    raise SystemExit(f"Unrecognized JSON structure in {path}")


def analyze(quests):
    total = len(quests)
    ids = [q.get("id") for q in quests]
    titles = [q.get("title") for q in quests if q.get("title")]
    id_counts = Counter(ids)
    title_counts = Counter(titles)
    dup_ids = [i for i, c in id_counts.items() if i is not None and c > 1]
    return {
        "total": total,
        "unique_ids": len([i for i in ids if i is not None]),
        "duplicate_ids_count": len(dup_ids),
        "duplicate_ids_sample": dup_ids[:20],
        "top_titles": title_counts.most_common(20),
    }


def dedupe(quests):
    seen = set()
    out = []
    for q in quests:
        qid = q.get("id")
        if qid is None:
            # keep quests without id (avoid data loss)
            out.append(q)
            continue
        if qid in seen:
            continue
        seen.add(qid)
        out.append(q)
    return out


def main():
    p = QUESTS_PATH
    if not p.exists():
        raise SystemExit(f"File not found: {p}")
    parser = argparse.ArgumentParser()
    parser.add_argument("--dedupe", action="store_true", help="Write deduplicated file by id")
    parser.add_argument(
        "--dedupe-title",
        action="store_true",
        help="Write deduplicated file by title (keep first occurrence)",
    )
    parser.add_argument(
        "--out",
        default="src/Rosetta_Quest_System/quests.deduped.json",
        help="Output file when --dedupe",
    )
    args = parser.parse_args()

    quests = load_quests(p)
    info = analyze(quests)
    print(f"Total quests loaded: {info['total']}")
    print(f"Unique id fields present: {info['unique_ids']}")
    print(f"Duplicate ids count: {info['duplicate_ids_count']}")
    if info["duplicate_ids_count"]:
        print("Sample duplicate ids:")
        for qid in info["duplicate_ids_sample"]:
            print(" -", qid)
    print("Top titles (most common):")
    for t, c in info["top_titles"]:
        print(f"  {c:4d}  {t}")

    if args.dedupe or args.dedupe_title:
        if args.dedupe_title:
            # dedupe by normalized title
            seen_titles = set()
            out_list = []
            for q in quests:
                title = q.get("title")
                key = None if title is None else title.strip().lower()
                if key is None:
                    out_list.append(q)
                    continue
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                out_list.append(q)
        else:
            out_list = dedupe(quests)

        out_path = Path(args.out)
        out_path.write_text(json.dumps(out_list, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote deduplicated file: {out_path} (entries: {len(out_list)})")


if __name__ == "__main__":
    main()

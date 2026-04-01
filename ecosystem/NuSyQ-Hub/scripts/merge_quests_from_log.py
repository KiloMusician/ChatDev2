#!/usr/bin/env python3
"""Merge quests from `quest_log.jsonl` into `quests.json` without duplicates.

Safe merge: preserves existing quests in `quests.json`, adds any quests found
in `quest_log.jsonl` `add_quest` events that are not already present. Also
applies latest status updates from `update_quest_status` events.
"""

import json
from pathlib import Path

ROOT = Path(".")
QUESTS_P = ROOT / "src" / "Rosetta_Quest_System" / "quests.json"
LOG_P = ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"


def load_json(p: Path):
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    quests = {q["id"]: q for q in load_json(QUESTS_P)}

    if not LOG_P.exists():
        print("No quest log found; nothing to merge.")
        return

    # process log sequentially to capture updates
    with LOG_P.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            event = entry.get("event")
            details = entry.get("details", {})
            if event == "add_quest":
                qid = details.get("id")
                if not qid:
                    continue
                if qid in quests:
                    # merge fields: prefer existing, but fill missing
                    existing = quests[qid]
                    for k, v in details.items():
                        if k not in existing or existing.get(k) in (None, "", []):
                            existing[k] = v
                else:
                    quests[qid] = details
            elif event == "update_quest_status":
                qid = details.get("id")
                if not qid:
                    continue
                if qid in quests:
                    quests[qid]["status"] = details.get("status", quests[qid].get("status"))
                    quests[qid]["updated_at"] = details.get("updated_at", quests[qid].get("updated_at"))
                    if "history" in details:
                        quests[qid]["history"] = details.get("history")

    merged = list(quests.values())
    # sort by created_at if available
    try:
        merged.sort(key=lambda q: q.get("created_at", ""))
    except Exception:
        pass

    with QUESTS_P.open("w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"Merged {len(merged)} quests into {QUESTS_P}")


if __name__ == "__main__":
    main()

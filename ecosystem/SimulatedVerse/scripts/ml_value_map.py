#!/usr/bin/env python3
import json


def load_inventory(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []


def score(entry):
    s = 0
    p = entry["path"].lower()
    if "pipeline" in p:
        s += 3
    if "features" in p:
        s += 2
    if "notebook" in p:
        s += 1
    if "model" in p and not entry["placeholder"]:
        s += 2
    if "train" in p:
        s += 2
    if entry["placeholder"]:
        s -= 2
    if entry["size"] > 0:
        s += 1
    if entry["size"] > 1000:
        s += 1
    return s


def main():
    cur = load_inventory("ml/data/snapshots/ml_inventory.json")
    leg = load_inventory("ml/data/snapshots/legacy_ml_inventory.json")

    cur_s = sorted(cur, key=score, reverse=True)
    leg_s = sorted(leg, key=score, reverse=True)

    out = {
        "current_top10": cur_s[:10],
        "legacy_top10": leg_s[:10],
        "summary": {
            "current_ml_files": len(cur),
            "legacy_ml_files": len(leg),
            "high_value_current": len([x for x in cur if score(x) >= 3]),
            "high_value_legacy": len([x for x in leg if score(x) >= 3])
        }
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

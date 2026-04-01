from __future__ import annotations
import json
import time
import os
from typing import Dict, Any, List

class History:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.index_path = os.path.join(log_dir, "index.jsonl")

    def log_decision(self, entry: Dict[str, Any]):
        entry["ts"] = time.time()
        with open(self.index_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def recent_scores(self, task_id: str, limit=20) -> List[float]:
        scores = []
        if not os.path.exists(self.index_path): return scores
        with open(self.index_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    if item.get("task_id") == task_id and "score" in item:
                        scores.append(item["score"])
                except: pass
        return scores[-limit:]
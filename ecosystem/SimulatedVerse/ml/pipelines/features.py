import re
from typing import Any, Dict

# Very cheap, non-LLM features
TOK=re.compile(r"[a-zA-Z_]+")
def featurize_pu(pu: Dict[str,Any]) -> Dict[str,float]:
    t = (pu.get("title") or "") + " " + (pu.get("desc") or "")
    words = TOK.findall(t.lower())
    L=len(words)
    feats = {
        "len_words": float(L),
        "priority_hi": 1.0 if pu.get("priority","").lower() in ("critical","high") else 0.0,
        "is_test": 1.0 if "test" in words else 0.0,
        "is_perf": 1.0 if "perf" in words or "optimiz" in words else 0.0,
        "is_doc": 1.0 if "doc" in words or "readme" in words else 0.0,
    }
    return feats
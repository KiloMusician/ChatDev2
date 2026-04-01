"""Challenge Generator Plugin — wraps generate_challenge_batch for plugin API."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def plugin(input_data: str, config: dict) -> str:
    try:
        cfg = json.loads(input_data) if input_data.strip().startswith("{") else {}
        cfg.update(config)
    except Exception:
        cfg = config.copy()

    category = cfg.get("category", None)
    difficulty = cfg.get("difficulty", None)
    count = int(cfg.get("count", 1))

    from generate_challenge_batch import run_batch
    result = run_batch(count=count, category=category, difficulty=difficulty, quiet=True)
    return json.dumps(result, indent=2)

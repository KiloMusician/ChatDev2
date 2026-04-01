"""
Next-Command Predictor — heuristic LSTM substitute using feature_store history.

Uses Markov chain (bigram/trigram) statistics over recorded command sequences
to predict the most likely next command. No heavy ML library needed.

When sufficient telemetry accumulates (Phase 3), this module can be upgraded
to a real LSTM or Transformer via the fine-tuning pipeline.

Msg⛛ tagging: [ML⛛{predict}]

API:
  predict_next(session_id, n)      → top-n predicted commands
  build_markov_model(sessions)     → bigram transition matrix from all sessions
  suggest_from_history(cmd_list)   → predict from a raw sequence
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_DB_PATH = _ROOT / "state" / "feature_store.db"


# ── Markov chain (bigram) ─────────────────────────────────────────────────────

def _load_command_sequences(limit_sessions: int = 100) -> List[List[str]]:
    """Load command sequences from feature_store grouped by session."""
    if not _DB_PATH.exists():
        return []
    try:
        con = sqlite3.connect(str(_DB_PATH))
        rows = con.execute(
            """SELECT session_id, features FROM feature_events
               WHERE event_type='command'
               ORDER BY session_id, ts
               LIMIT ?""",
            (limit_sessions * 50,),
        ).fetchall()
        con.close()
    except Exception:
        return []

    sessions: Dict[str, List[str]] = defaultdict(list)
    for sid, feat_json in rows:
        try:
            feat = json.loads(feat_json or "{}")
            cmd = feat.get("cmd", "").strip()
            if cmd:
                sessions[sid].append(cmd)
        except Exception:
            continue
    return list(sessions.values())


def build_markov_model(
    sequences: Optional[List[List[str]]] = None,
    order: int = 2,
) -> Dict[Tuple, Counter]:
    """
    Build an n-gram Markov model from command sequences.
    Returns {(prev_cmd, ...): Counter({next_cmd: count})}
    """
    if sequences is None:
        sequences = _load_command_sequences()

    model: Dict[Tuple, Counter] = defaultdict(Counter)
    for seq in sequences:
        for i in range(len(seq) - order):
            context = tuple(seq[i:i + order])
            next_cmd = seq[i + order]
            model[context][next_cmd] += 1
    return model


def predict_next(
    session_id: Optional[str] = None,
    n: int = 5,
    order: int = 2,
) -> List[Dict]:
    """
    Predict the top-n next commands for a session.
    Uses bigram Markov model trained on all recorded sessions.
    """
    sequences = _load_command_sequences()
    if not sequences:
        return [{"cmd": c, "prob": 1 / 5, "source": "default"}
                for c in ["help", "status", "ls", "consciousness", "ml"]]

    model = build_markov_model(sequences, order=order)

    # Get current session's last N commands
    current_seq: List[str] = []
    if session_id and _DB_PATH.exists():
        try:
            con = sqlite3.connect(str(_DB_PATH))
            rows = con.execute(
                """SELECT features FROM feature_events
                   WHERE event_type='command' AND session_id=?
                   ORDER BY ts DESC LIMIT ?""",
                (session_id, order),
            ).fetchall()
            con.close()
            for (feat_json,) in reversed(rows):
                feat = json.loads(feat_json or "{}")
                cmd = feat.get("cmd", "")
                if cmd:
                    current_seq.append(cmd)
        except Exception:
            pass

    # Try to look up context in model
    if len(current_seq) >= order:
        context = tuple(current_seq[-order:])
        counter = model.get(context, Counter())
        if not counter:
            # Fall back to order-1 context
            context = tuple(current_seq[-1:])
            counter = model.get(context, Counter())
    elif current_seq:
        context = tuple(current_seq[-1:])
        counter = model.get(context, Counter())
    else:
        counter = Counter()

    if not counter:
        # Global frequency fallback
        all_cmds: Counter = Counter()
        for ctx_counter in model.values():
            all_cmds.update(ctx_counter)
        counter = all_cmds

    total = sum(counter.values()) or 1
    top = counter.most_common(n)
    return [{"cmd": cmd, "prob": round(count / total, 3), "source": "markov"}
            for cmd, count in top]


def suggest_from_history(cmd_list: List[str], n: int = 3) -> List[str]:
    """
    Given a list of recent commands, predict next n.
    Convenience wrapper for quick in-game hints.
    """
    model = build_markov_model()
    context = tuple(cmd_list[-2:]) if len(cmd_list) >= 2 else tuple(cmd_list[-1:]) if cmd_list else ()
    counter = model.get(context, Counter())
    if not counter:
        return ["help", "status", "consciousness"]
    return [cmd for cmd, _ in counter.most_common(n)]


def predictor_stats() -> Dict:
    sequences = _load_command_sequences()
    model = build_markov_model(sequences)
    return {
        "sessions_in_training_set": len(sequences),
        "total_transitions": sum(sum(c.values()) for c in model.values()),
        "unique_contexts": len(model),
        "msg_tag": "[ML⛛{predict}]",
    }

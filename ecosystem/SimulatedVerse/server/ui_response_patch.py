# server/ui_response_patch.py
from typing import Any, Dict
from .normalizers import ensure_array

def normalize_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(resp or {})
    # Typical fields the HUD tries to render with `.map`
    for k in ("menu", "windows", "panes", "cascades", "achievements", "tasks", "rows", "agents", "effects", "recentGains"):
        if k in out:
            out[k] = ensure_array(out.get(k))
    
    # Nested patterns
    if "metrics" in out and isinstance(out["metrics"], dict):
        for mk in ("history", "series", "motif"):
            if mk in out["metrics"]:
                out["metrics"][mk] = ensure_array(out["metrics"][mk])
    
    # Game state specific normalizations
    if "richState" in out and isinstance(out["richState"], dict):
        rich = out["richState"]
        if "effects" in rich and isinstance(rich["effects"], dict):
            for ek in ("recentGains", "achievements"):
                if ek in rich["effects"]:
                    rich["effects"][ek] = ensure_array(rich["effects"][ek])
    
    return out
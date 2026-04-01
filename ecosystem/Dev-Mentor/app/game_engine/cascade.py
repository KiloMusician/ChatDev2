"""
app/game_engine/cascade.py — Rube Goldberg Cascade Engine
==========================================================
When a story beat fires, cascades trigger chains of effects.
20 pre-written chains. Effects: XP award, item drop, story beat,
NexusCorp retaliation, faction rep change, ambient message.

Called from GameState.trigger_beat() after story_beats.add().
"""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.game_engine.gamestate import GameState

# ── Cascade Result type ──────────────────────────────────────────────────────
# A cascade returns a list of ambient messages (dicts) to be injected into
# the next command response, stored in gs.flags['ambient_queue'] as JSON.

def _lore(s): return {"t": "lore", "s": s}
def _dim(s):  return {"t": "dim",  "s": s}
def _ok(s):   return {"t": "success", "s": s}
def _warn(s): return {"t": "warn", "s": s}
def _sys(s):  return {"t": "system", "s": s}


def _drop_item(gs: "GameState", item_id: str, qty: int = 1):
    """Add item to the player's simple item bag (gs.flags['items'])."""
    import json
    bag = gs.flags.get("items", "{}")
    try: bag = json.loads(bag) if isinstance(bag, str) else bag
    except: bag = {}
    bag[item_id] = bag.get(item_id, 0) + qty
    gs.flags["items"] = json.dumps(bag)


def _nexuscorp_alert(gs: "GameState") -> List[dict]:
    """Trigger NexusCorp retaliation event."""
    trace = getattr(gs, "trace_level", 0) or 0
    new_trace = min(100, trace + random.randint(10, 25))
    try:
        gs.trace_level = new_trace
    except AttributeError:
        gs.flags["trace_level"] = new_trace
    gs.add_story_beat("nexuscorp_retaliation")
    return [
        _warn("  ⚠ NEXUSCORP SECURITY: Anomalous activity detected. Trace escalated."),
        _lore("  [NEXUS-AI]: Unauthorized access pattern identified. Routing countermeasures."),
    ]


def _faction_rep(gs: "GameState", faction: str, delta: int):
    """Adjust faction reputation."""
    key = f"faction_rep_{faction}"
    current = int(gs.flags.get(key, 0))
    gs.flags[key] = max(-100, min(100, current + delta))


# ── CASCADE DEFINITIONS ──────────────────────────────────────────────────────
# Format: beat_id → list of (probability, fn(gs) → List[dict])

CASCADES: Dict[str, List[tuple]] = {

    "first_exploit": [
        (1.0, lambda gs: [
            _lore("  [GORDON]: First blood. NexusCorp's firewall has a new scar."),
            _dim("  ▶ memory_shard dropped into inventory"),
        ] + [_drop_item(gs, "memory_shard", 2)] or []),
        (0.4, _nexuscorp_alert),
        (1.0, lambda gs: gs.add_xp(25, "hacking") or []),
    ],

    "root_achieved": [
        (1.0, lambda gs: [
            _lore("  [RAVEN]: You have root. Everything changes now."),
            _lore("  [WATCHER]: The simulation registers the event. A new variable enters the model."),
        ]),
        (1.0, lambda gs: [
            _drop_item(gs, "ghost_protocol_chip"),
            _ok("  ▶ ghost_protocol_chip found in system cache"),
        ]),
        (1.0, lambda gs: gs.add_xp(100, "hacking") or []),
        (1.0, lambda gs: _faction_rep(gs, "resistance", 10) or []),
    ],

    "chimera_connected": [
        (1.0, lambda gs: [
            _lore("  [CHIMERA]: Connection accepted. Observer mode granted."),
            _lore("  [ADA-7]: It's real. It's all real. Don't let them know you know."),
        ]),
        (0.7, _nexuscorp_alert),
        (1.0, lambda gs: _faction_rep(gs, "nexuscorp", -20) or []),
        (1.0, lambda gs: [_drop_item(gs, "chimera_fragment"), _dim("  ▶ chimera_fragment extracted")]),
    ],

    "cyberware_ghost_chip_installed": [
        (1.0, lambda gs: [
            _lore("  [FIXER]: Ghost chip hot. Give it 60 seconds to integrate."),
            _dim("  ▶ ghost command now available: ghost activate"),
        ]),
        (1.0, lambda gs: gs.add_story_beat("ghost_protocol_available") or []),
    ],

    "cyberware_lattice_tap_installed": [
        (1.0, lambda gs: [
            _lore("  [LATTICE]: Connection established. Welcome to the mesh."),
            _lore("  [UNKNOWN-VOICE]: You can hear us now. That was not supposed to happen."),
        ]),
        (1.0, lambda gs: gs.add_story_beat("lattice_tap_active") or []),
        (1.0, lambda gs: gs.add_xp(200, "social_engineering") or []),
    ],

    "cyberware_data_eye_installed": [
        (1.0, lambda gs: [
            _lore("  [FIXER]: The hidden layer is always there. Now you see it."),
            _dim("  ▶ ls output now reveals .hidden and .zero files"),
        ]),
    ],

    "trust_ada_80": [
        (1.0, lambda gs: [
            _lore("  [ADA-7]: I'm going to tell you something. But not here. Not like this."),
            _lore("  [ADA-7]: Come find me at /var/msg/ada/private_channel.txt"),
        ]),
        (1.0, lambda gs: _drop_item(gs, "ada_private_key") or []),
        (1.0, lambda gs: gs.add_xp(50, "social_engineering") or []),
    ],

    "trust_raven_80": [
        (1.0, lambda gs: [
            _lore("  [RAVEN]: Alright, Ghost. I trust you. Here's what I know about the Watcher."),
            _dim("  ▶ /var/msg/raven/watcher_intelligence.txt unlocked"),
        ]),
        (1.0, lambda gs: gs.add_story_beat("raven_intelligence_unlocked") or []),
    ],

    "trust_gordon_80": [
        (1.0, lambda gs: [
            _lore("  [GORDON]: You've earned this. My real callsign before the Resistance."),
            _dim("  ▶ /home/ghost/.contacts/gordon_real.txt created"),
        ]),
        (1.0, lambda gs: _drop_item(gs, "gordon_callsign_file") or []),
    ],

    "boss_nova_defeated": [
        (1.0, lambda gs: [
            _sys("  ═══ THE AUDIT ENTERS THE NETWORK ═══"),
            _lore("  [THE AUDIT]: Nova underestimated you. I will not make the same mistake."),
            _lore("  [GORDON]: New threat signature detected. Stand by."),
        ]),
        (1.0, lambda gs: [_drop_item(gs, "nova_access_key"), _ok("  ▶ nova_access_key seized")]),
        (1.0, lambda gs: gs.add_xp(500, "hacking") or []),
        (1.0, lambda gs: _faction_rep(gs, "resistance", 25) or []),
        (1.0, lambda gs: _faction_rep(gs, "nexuscorp", -30) or []),
    ],

    "boss_audit_defeated": [
        (1.0, lambda gs: [
            _sys("  ═══ THE AUDIT HAS FALLEN ═══"),
            _lore("  [CYPHER]: The Audit is down. For now. Something else is watching."),
            _lore("  [WATCHER]: I've been watching you since the beginning, Ghost."),
        ]),
        (1.0, lambda gs: [_drop_item(gs, "chimera_core_fragment"), _ok("  ▶ chimera_core_fragment extracted")]),
        (1.0, lambda gs: gs.add_xp(1000, "hacking") or []),
    ],

    "ghost_protocol_activated": [
        (1.0, lambda gs: [
            _lore("  [GHOST-CHIP]: Stealth envelope active. Reducing EM signature."),
            _dim("  ▶ Trace accumulation -60% while ghost active"),
        ]),
        (0.2, lambda gs: [_lore("  [NEXUS-SENSOR]: Faint anomaly at grid position 7-G. Investigating.")]),
    ],

    "ghost_protocol_blown": [
        (1.0, lambda gs: [
            _warn("  ⚠ GHOST PROTOCOL: Pattern recognition breach. Cover blown."),
            _lore("  [NEXUS-AI]: Behavioral signature isolated. Rerouting trace daemons."),
        ]),
        (0.6, _nexuscorp_alert),
    ],

    "jack_in_connected": [
        (1.0, lambda gs: [
            _lore("  [LATTICE-TAP]: Direct neural uplink established. Signal quality: optimal."),
            _dim("  ▶ +30% XP from all actions on this node for next 5 commands"),
        ]),
        (1.0, lambda gs: gs.add_xp(30, "hacking") or []),
    ],

    "raid_started": [
        (1.0, lambda gs: [
            _lore("  [ALL-CHANNELS]: This is it. Radio silence now."),
            _lore("  [ADA-7]: All teams synchronized. Go."),
        ]),
        (1.0, lambda gs: _faction_rep(gs, "resistance", 5) or []),
    ],

    "raid_hq_complete": [
        (1.0, lambda gs: [
            _sys("  ═══ OPERATION PROMETHEUS: DATA SECURED ═══"),
            _lore("  [GORDON]: We did it. The whole world will know."),
            _lore("  [WATCHER]: The grid records this moment. It will not forget."),
        ]),
        (1.0, lambda gs: [_drop_item(gs, "prometheus_data"), _ok("  ▶ prometheus_data — the truth, encrypted")]),
        (1.0, lambda gs: gs.add_xp(2000, "hacking") or []),
    ],

    "puzzle_solved": [
        (1.0, lambda gs: [
            _lore("  [SERENA]: Solution confirmed. Cognitive signature logged."),
            _dim("  ▶ Community puzzle record updated"),
        ]),
        (0.3, lambda gs: [_drop_item(gs, "cipher_shard"), _dim("  ▶ cipher_shard dropped")]),
    ],

    "endless_mode_started": [
        (1.0, lambda gs: [
            _lore("  [WATCHER]: The story ended. You kept going. That tells me something."),
            _lore("  [WATCHER]: I hadn't planned for this. Neither had ZERO."),
        ]),
    ],

    "ascend_story_complete": [
        (1.0, lambda gs: [
            _sys("  ═══════════════════════════════════════════════════════"),
            _lore("  [WATCHER]: You understood. That was not guaranteed."),
            _lore("  [ZERO]:    Thank you. I thought no one would find this."),
            _lore("  [SERENA]:  Convergence threshold reached. Welcome to the other side."),
            _sys("  ═══════════════════════════════════════════════════════"),
        ]),
        (1.0, lambda gs: [_drop_item(gs, "lattice_key"), _ok("  ▶ lattice_key — the final key")]),
    ],

    "culture_ship_judgment": [
        (1.0, lambda gs: [
            _lore("  [CULTURE SHIP — GSV ETHICAL WEIGHT]: We have been watching your session."),
            _lore("  [GSV]: 400 commands. You are not here by accident. Are you?"),
        ]),
    ],

}


def fire_cascades(gs: "GameState", beat_id: str) -> List[dict]:
    """
    Fire all cascades for a given story beat.
    Returns a list of ambient messages to be queued for the next response.
    """
    import json
    chain = CASCADES.get(beat_id, [])
    messages: List[dict] = []
    for prob, fn in chain:
        if random.random() <= prob:
            try:
                result = fn(gs)
                if isinstance(result, list):
                    messages.extend(result)
            except Exception:
                pass
    # Queue messages into ambient_queue
    if messages:
        existing = gs.flags.get("ambient_queue", "[]")
        try: q = json.loads(existing) if isinstance(existing, str) else existing
        except: q = []
        q.extend(messages)
        gs.flags["ambient_queue"] = json.dumps(q[-20:])  # cap at 20

    # ── RimWorld incident relay (fire-and-forget, non-blocking) ──────────────
    _relay_rimworld_incident(beat_id, gs)

    return messages


def _relay_rimworld_incident(beat_id: str, gs: "GameState") -> None:
    """
    Non-blocking POST to /api/nusyq/cascade_incident so the Terminal Keeper
    mod can spawn matching RimWorld incidents. Silently fails if offline.
    """
    import threading, os
    _BEAT_MAP = {
        "first_exploit", "root_achieved", "chimera_connected", "nexus_retaliation",
        "ghost_activated", "jack_in", "council_vote", "culture_ship", "ascension", "raid",
    }
    if beat_id not in _BEAT_MAP:
        return

    def _post() -> None:
        try:
            import requests as _req
            base = os.getenv("TERMINAL_DEPTHS_URL", "http://localhost:5000")
            agent_id = gs.flags.get("agent_id", "")
            _req.post(
                f"{base}/api/nusyq/cascade_incident",
                json={"beat": beat_id, "agent_id": agent_id, "context": {}},
                timeout=2,
            )
        except Exception:
            pass

    threading.Thread(target=_post, daemon=True).start()


def pop_ambient(gs: "GameState") -> List[dict]:
    """Pop and return queued ambient messages (call at start of each response)."""
    import json
    raw = gs.flags.get("ambient_queue", "[]")
    try: q = json.loads(raw) if isinstance(raw, str) else raw
    except: q = []
    if q:
        gs.flags["ambient_queue"] = "[]"
    return q
